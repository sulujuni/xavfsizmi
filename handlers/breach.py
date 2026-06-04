"""
Breach conversation handler:
/breach → asks for email → checks breach API → returns result
"""
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler

from database import (
    get_user_lang, is_premium, get_referral_credits, consume_referral_credit,
)
from languages import t

# Conversation state
WAITING_BREACH_EMAIL = 1


async def breach_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 — check access, then ask for email."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    has_premium = is_premium(user.id)
    free_credits = get_referral_credits(user.id)

    if not has_premium and free_credits < 1:
        keyboard = [[InlineKeyboardButton("⭐ Premium olish", callback_data="pay_stars")]]
        await update.message.reply_text(
            t(lang, "breach_premium_required", credits=0),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END

    note = f"\n💳 Sizda {free_credits} ta bepul tekshiruv bor." if not has_premium else ""
    await update.message.reply_text(
        f"🔐 *Email Breach Tekshiruvi*{note}\n\n📧 Emailingizni yuboring:",
        parse_mode="Markdown",
    )
    return WAITING_BREACH_EMAIL


async def breach_receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 — receive email, validate, check API."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    email = update.message.text.strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text(
            "❌ Noto'g'ri email format.\nMasalan: `user@gmail.com`\n\nQayta yuboring:",
            parse_mode="Markdown",
        )
        return WAITING_BREACH_EMAIL

    has_premium = is_premium(user.id)
    status_msg = await update.message.reply_text(t(lang, "breach_checking"))

    try:
        import aiohttp
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
                        result = t(
                            lang, "breach_compromised",
                            email=email, count=len(breaches_list), breaches=breaches_text,
                        )
                    else:
                        result = t(lang, "breach_safe", email=email)
                else:
                    result = t(lang, "breach_safe", email=email)

        await status_msg.edit_text(result, parse_mode="Markdown")

        # Deduct credit if not premium
        if not has_premium:
            consume_referral_credit(user.id)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ API xatoligi: {str(e)}")

    return ConversationHandler.END


async def breach_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "breach_cancel"))
    return ConversationHandler.END
