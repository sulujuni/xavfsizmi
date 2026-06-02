"""
Premium & Payment handlers:
/premium, /promo, /addpromo, payment callbacks, pre-checkout, success
"""
from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import DAILY_FREE_LIMIT, CHANNEL_INVITE_LINK
from database import (
    get_user_lang, is_premium, set_premium,
    create_promocode, redeem_promocode,
)
from languages import t
from admin import is_admin

# Import UZS provider token safely
try:
    from config import UZS_PROVIDER_TOKEN
except ImportError:
    UZS_PROVIDER_TOKEN = "PROVIDER_TOKEN_NOT_SET"


# ─── /premium ─────────────────────────────────────────────────────────────────

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if is_premium(user_id):
        await update.message.reply_text(t(lang, "premium_already_active"))
        return

    keyboard = [
        [InlineKeyboardButton("⭐ Telegram Stars (75 XTR)", callback_data="pay_stars")],
        [InlineKeyboardButton("💳 Payme / Click (29,990 So'm)", callback_data="pay_som")],
    ]
    await update.message.reply_text(
        t(lang, "premium_info"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    # Send promo code info as a follow-up
    await update.message.reply_text(
        t(lang, "premium_promo_hint"),
        parse_mode="Markdown",
    )


# ─── /addpromo (Admin) ────────────────────────────────────────────────────────

async def add_promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌")
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "🔑 *Syntax:* `/addpromo [kod_nomi] [kunlar] [once/multi]`",
            parse_mode="Markdown",
        )
        return

    code = context.args[0].strip().upper()
    try:
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Days must be an integer.")
        return

    usage_type = context.args[2].strip().lower()
    create_promocode(code, days, usage_type)
    await update.message.reply_text(
        f"✅ Promo created: `{code}` ({days} days, type: {usage_type})",
        parse_mode="Markdown",
    )


# ─── /promo ───────────────────────────────────────────────────────────────────

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(text=t(lang, "promo_usage"), parse_mode="Markdown")
        return

    input_code = context.args[0].strip()
    success, msg_key = redeem_promocode(user.id, input_code)

    if success:
        await update.message.reply_text(text=t(lang, "promo_success_msg", days=30))
    else:
        await update.message.reply_text(text=t(lang, msg_key))


# ─── Payment gateway callback (Stars / So'm) ─────────────────────────────────

async def payment_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "pay_stars":
        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Premium - 30 days (Stars)",
            description="30-day Premium subscription via Telegram Stars",
            payload="premium_stars_30",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Premium Stars", 75)],
        )
    elif query.data == "pay_som":
        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Premium - 30 days (So'm)",
            description="30-day Premium subscription via payment provider",
            payload="premium_som_30",
            provider_token=UZS_PROVIDER_TOKEN,
            currency="UZS",
            prices=[LabeledPrice("Premium UZS", 2999000)],
        )


# ─── Pre-checkout & payment success ──────────────────────────────────────────

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    set_premium(user_id, days=30)
    try:
        await update.message.set_reaction([ReactionTypeEmoji(emoji="🎉")])
    except TelegramError:
        pass
    await update.message.reply_text(t(lang, "premium_success"), parse_mode="Markdown")
