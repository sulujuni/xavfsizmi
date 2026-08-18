"""
Breach, Password & Dark Web Check — unified /breach command.

User sends email → checks breaches + dark web mentions
User sends password → checks HaveIBeenPwned (k-anonymity, safe)
"""
import hashlib
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler
import aiohttp

from bot.core.database import (
    get_user_lang, is_premium, get_referral_credits, consume_referral_credit,
)
from bot.i18n import t
from bot.core.trust import check_dark_web_mentions

# Conversation states
WAITING_BREACH_INPUT = 1


async def breach_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 — check access, then ask for email or password."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    has_premium = is_premium(user.id)
    free_credits = get_referral_credits(user.id)

    if not has_premium and free_credits < 1:
        keyboard = [[InlineKeyboardButton("⭐ Premium olish", callback_data="pay_p1m_stars")]]
        await update.message.reply_text(
            t(lang, "breach_premium_required", credits=0),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END

    note = ""
    if not has_premium:
        note = f"\n💳 {t(lang, 'breach_credits_left', credits=free_credits)}"

    await update.message.reply_text(
        t(lang, "breach_ask_input") + note,
        parse_mode="Markdown",
    )
    return WAITING_BREACH_INPUT


async def breach_receive_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 — detect if input is email or password, check accordingly."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    user_input = update.message.text.strip()

    has_premium = is_premium(user.id)

    # Detect if it's an email or a password
    is_email = "@" in user_input and "." in user_input.split("@")[-1]

    # If it's a password, delete the user's message immediately for safety
    if not is_email:
        try:
            await update.message.delete()
        except Exception:
            pass

    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=t(lang, "breach_checking"),
    )

    try:
        if is_email:
            result = await _check_email_full(user_input, lang)
        else:
            result = await _check_password_breach(user_input, lang)

        await status_msg.edit_text(result, parse_mode="Markdown")

        # Deduct credit if not premium
        if not has_premium:
            consume_referral_credit(user.id)
    except Exception as e:
        logging.error(f"Breach check failed: {e}", exc_info=True)
        await status_msg.edit_text(t(lang, "api_error"))

    return ConversationHandler.END


# ─── Combined email check: breaches + dark web ────────────────────────────────

async def _check_email_full(email: str, lang: str) -> str:
    """Check email in both breach databases AND dark web sources."""
    import asyncio

    # Run both checks in parallel
    breach_result, darkweb_result = await asyncio.gather(
        _get_breach_data(email),
        check_dark_web_mentions(email),
    )

    # Build combined report
    breaches_list = breach_result.get("breaches", [])
    darkweb_mentions = darkweb_result.get("total_mentions", 0)
    darkweb_sources = darkweb_result.get("found_in", [])

    # Determine overall status
    is_compromised = bool(breaches_list) or darkweb_mentions > 0

    if is_compromised:
        report = f"🚨 *{t(lang, 'breach_result_danger')}*\n\n"
        report += f"📧 `{email}`\n\n"

        # Breach section
        if breaches_list:
            breaches_text = "\n".join([f"  • *{b}*" for b in breaches_list[:5]])
            if len(breaches_list) > 5:
                breaches_text += f"\n  ... +{len(breaches_list) - 5} {t(lang, 'more_breaches')}"
            report += f"🔓 *{t(lang, 'breach_section')}:* {len(breaches_list)}\n{breaches_text}\n\n"

        # Dark web section
        if darkweb_mentions > 0:
            sources_text = ", ".join(darkweb_sources)
            report += f"🕸 *{t(lang, 'darkweb_section')}:* {darkweb_mentions}\n"
            report += f"  📋 {sources_text}\n\n"

        report += f"⚠️ {t(lang, 'breach_action_required')}"
    else:
        report = f"✅ *{t(lang, 'breach_result_safe')}*\n\n"
        report += f"📧 `{email}`\n\n"
        report += f"🔓 {t(lang, 'breach_section')}: 0\n"
        report += f"🕸 {t(lang, 'darkweb_section')}: 0\n\n"
        report += f"✅ {t(lang, 'breach_all_clear')}"

    return report


async def _get_breach_data(email: str) -> dict:
    """Get breach list for an email. Returns {breaches: [list]}."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.xposedornot.com/v1/check-email/{email}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw = data.get("breaches", [])
                    breaches_list = raw[0] if raw and isinstance(raw[0], list) else raw
                    return {"breaches": breaches_list if breaches_list else []}
    except Exception:
        pass
    return {"breaches": []}


# ─── Password breach check (HaveIBeenPwned k-anonymity) ──────────────────────

async def _check_password_breach(password: str, lang: str) -> str:
    """
    Check if password has been leaked using k-anonymity.
    Only sends first 5 chars of SHA1 hash — password NEVER leaves the device.
    """
    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return t(lang, "password_check_error")
            text = await resp.text()

    times_found = 0
    for line in text.splitlines():
        parts = line.strip().split(":")
        if len(parts) == 2 and parts[0] == suffix:
            times_found = int(parts[1])
            break

    if times_found > 0:
        return t(lang, "password_compromised", count=times_found)
    else:
        return t(lang, "password_safe")


# ─── Cancel ───────────────────────────────────────────────────────────────────

async def breach_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "breach_cancel"))
    return ConversationHandler.END



# ═══════════════════════════════════════════════════════════════════════════════
# /darkweb conversation (merged from handlers/conversations.py)
# ═══════════════════════════════════════════════════════════════════════════════

WAITING_DARKWEB_INPUT = 14


async def darkweb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for email/username to check."""
    from bot.handlers.scan import react_to_message, require_subscription
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "darkweb_ask"), parse_mode="Markdown")
    return WAITING_DARKWEB_INPUT


async def darkweb_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Check dark web mentions."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    query = update.message.text.strip()

    status_msg = await update.message.reply_text(t(lang, "checking"))
    result = await check_dark_web_mentions(query)

    if result["total_mentions"] > 0:
        sources_text = "\n".join([f"  🔴 {s}" for s in result["found_in"]])
        text = t(lang, "darkweb_found",
                 query=query, count=result["total_mentions"],
                 sources=sources_text)
    else:
        text = t(lang, "darkweb_safe", query=query,
                 checked=result["sources_checked"])

    await status_msg.edit_text(text, parse_mode="Markdown")
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
# /monitor conversation (merged from handlers/monitor.py)
# ═══════════════════════════════════════════════════════════════════════════════

import logging as _logging

from bot.core.database import (
    get_monitored_emails, add_monitored_email,
    remove_monitored_email, update_monitored_email_count,
    get_all_monitoring_users,
)
from telegram.ext import Application
from telegram.error import TelegramError

WAITING_MONITOR_EMAIL = 40
MAX_MONITORED_EMAILS = 10


# ─── Breach count helper ──────────────────────────────────────────────────────

async def _get_breach_count(email: str) -> int:
    """Returns the number of breaches an email appears in, or -1 on error."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.xposedornot.com/v1/check-email/{email}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw = data.get("breaches", [])
                    breaches_list = raw[0] if raw and isinstance(raw[0], list) else raw
                    return len(breaches_list) if breaches_list else 0
                elif resp.status == 404:
                    return 0
    except Exception as e:
        _logging.error(f"Monitor breach check error: {e}")
    return -1


# ─── /monitor command ─────────────────────────────────────────────────────────

async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    from bot.handlers.scan import react_to_message, require_subscription
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    # Premium only
    if not is_premium(user.id):
        keyboard = [[InlineKeyboardButton("⭐ Premium", callback_data="pay_p1m_stars")]]
        await update.message.reply_text(
            t(lang, "monitor_premium_required"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END

    # Inline add: /monitor add email@example.com
    if context.args and context.args[0].lower() == "add" and len(context.args) > 1:
        await _add_email(update, context, context.args[1].strip(), lang)
        return ConversationHandler.END

    # Show list
    emails = get_monitored_emails(user.id)
    if not emails:
        await update.message.reply_text(t(lang, "monitor_empty"), parse_mode="Markdown")
        return WAITING_MONITOR_EMAIL

    text = t(lang, "monitor_list_title") + "\n\n"
    keyboard = []
    for item in emails:
        email = item.get("email", "")
        count = item.get("last_breach_count", 0)
        status = "🔴" if count > 0 else "🟢"
        text += f"{status} `{email}` — {count} {t(lang, 'breaches_word')}\n"
        keyboard.append([InlineKeyboardButton(f"🗑 {email}", callback_data=f"monrm_{email}")])

    text += f"\n{t(lang, 'monitor_add_hint')}"
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
    )
    return WAITING_MONITOR_EMAIL


async def monitor_receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive an email to add to monitoring."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    email = update.message.text.strip()
    await _add_email(update, context, email, lang)
    return ConversationHandler.END


async def _add_email(update, context, email: str, lang: str):
    user = update.effective_user

    # Validate
    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text(t(lang, "monitor_invalid_email"))
        return

    emails = get_monitored_emails(user.id)
    if len(emails) >= MAX_MONITORED_EMAILS:
        await update.message.reply_text(t(lang, "monitor_limit", limit=MAX_MONITORED_EMAILS))
        return

    if any(e.get("email") == email for e in emails):
        await update.message.reply_text(t(lang, "monitor_already_added"))
        return

    status_msg = await update.message.reply_text(t(lang, "breach_checking"))
    count = await _get_breach_count(email)
    if count < 0:
        count = 0

    add_monitored_email(user.id, email, count)

    if count > 0:
        await status_msg.edit_text(
            t(lang, "monitor_added_breached", email=email, count=count),
            parse_mode="Markdown",
        )
    else:
        await status_msg.edit_text(
            t(lang, "monitor_added_safe", email=email),
            parse_mode="Markdown",
        )


# ─── Remove email callback ────────────────────────────────────────────────────

async def monitor_remove_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id)

    email = query.data.replace("monrm_", "")
    remove_monitored_email(user.id, email)
    await query.edit_message_text(t(lang, "monitor_removed", email=email), parse_mode="Markdown")


# ─── Scheduler job: re-check all monitored emails ────────────────────────────

async def check_monitored_emails(application: Application):
    """
    Periodically checks all monitored emails. Alerts users if a NEW breach
    appeared since the last check. Called by APScheduler (e.g. daily).
    """
    users = get_all_monitoring_users()
    checked = 0
    alerts = 0

    for user_id in users:
        # Skip if user lost premium
        if not is_premium(user_id):
            continue

        lang = get_user_lang(user_id)
        emails = get_monitored_emails(user_id)

        for item in emails:
            email = item.get("email", "")
            old_count = item.get("last_breach_count", 0)
            new_count = await _get_breach_count(email)
            checked += 1

            if new_count < 0:
                continue  # API error, skip

            if new_count > old_count:
                # New breach detected!
                update_monitored_email_count(user_id, email, new_count)
                try:
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=t(lang, "monitor_new_breach_alert",
                               email=email, new=new_count - old_count, total=new_count),
                        parse_mode="Markdown",
                    )
                    alerts += 1
                except TelegramError:
                    pass
            elif new_count != old_count:
                update_monitored_email_count(user_id, email, new_count)

    _logging.info(f"Breach monitor: checked {checked} emails, {alerts} alerts sent")
