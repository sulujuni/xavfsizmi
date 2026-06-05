"""
Breach & Password Check conversation handler:
/breach → asks for email OR password → checks against leak databases

Email: uses XposedOrNot API (free)
Password: uses HaveIBeenPwned k-anonymity API (free, safe — only sends
           first 5 chars of SHA1 hash, never the full password)
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
            result = await _check_email_breach(user_input, lang)
        else:
            result = await _check_password_breach(user_input, lang)

        await status_msg.edit_text(result, parse_mode="Markdown")

        # Deduct credit if not premium
        if not has_premium:
            consume_referral_credit(user.id)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ API xatoligi: {str(e)}")

    return ConversationHandler.END


# ─── Email breach check (XposedOrNot API) ────────────────────────────────────

async def _check_email_breach(email: str, lang: str) -> str:
    """Check if email has been in data breaches."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.xposedornot.com/v1/check-email/{email}",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                raw = data.get("breaches", [])
                breaches_list = raw[0] if raw and isinstance(raw[0], list) else raw
                if breaches_list:
                    breaches_text = "\n".join([f"• *{b}*" for b in breaches_list[:5]])
                    extra = ""
                    if len(breaches_list) > 5:
                        extra = f"\n... +{len(breaches_list) - 5} {t(lang, 'more_breaches')}"
                    return t(
                        lang, "breach_compromised",
                        email=email, count=len(breaches_list),
                        breaches=breaches_text + extra,
                    )
                else:
                    return t(lang, "breach_safe", email=email)
            else:
                return t(lang, "breach_safe", email=email)


# ─── Password breach check (HaveIBeenPwned k-anonymity) ──────────────────────

async def _check_password_breach(password: str, lang: str) -> str:
    """
    Check if password has been leaked using k-anonymity.
    Only sends first 5 chars of SHA1 hash — password NEVER leaves the device.
    """
    # Hash the password
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

    # Search for our suffix in the response
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
