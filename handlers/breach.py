"""
Breach, Password & Dark Web Check — unified /breach command.

User sends email → checks breaches + dark web mentions
User sends password → checks HaveIBeenPwned (k-anonymity, safe)
"""
import hashlib
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler
import aiohttp

from database import (
    get_user_lang, is_premium, get_referral_credits, consume_referral_credit,
)
from languages import t
from handlers.tools import check_dark_web_mentions

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
        await status_msg.edit_text(t(lang, "api_error", error=str(e)[:100]))

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
