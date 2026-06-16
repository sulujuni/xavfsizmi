"""
Data Breach Monitor (Premium feature).
Premium users can save multiple emails. A scheduler job periodically
re-checks them and alerts the user if a NEW breach is detected.

Commands:
/monitor          — show list + add/remove buttons
/monitor add x@y  — add an email
/monitor          — manage saved emails
"""
import logging
import aiohttp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, Application
from telegram.error import TelegramError

from database import (
    get_user_lang, is_premium,
    get_monitored_emails, add_monitored_email,
    remove_monitored_email, update_monitored_email_count,
    get_all_monitoring_users,
)
from languages import t
from handlers.private_messages import require_subscription, react_to_message

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
        logging.error(f"Monitor breach check error: {e}")
    return -1


# ─── /monitor command ─────────────────────────────────────────────────────────

async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

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

    logging.info(f"Breach monitor: checked {checked} emails, {alerts} alerts sent")
