"""
Premium & Payment handlers:
/premium, /promo, /addpromo, payment callbacks, pre-checkout, success

Plans:
- 1 month: 25 Stars / 9,990 UZS
- 3 months: 65 Stars / 24,990 UZS (save 17%)
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

from config import (
    PERSONAL_1M_STARS, PERSONAL_3M_STARS,
    PERSONAL_1M_UZS, PERSONAL_3M_UZS,
    UZS_PROVIDER_TOKEN,
)
from database import (
    get_user_lang, is_premium, set_premium,
    create_promocode, redeem_promocode, get_premium_expiry,
)
from languages import t
from admin import is_admin


# ─── /premium ─────────────────────────────────────────────────────────────────

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if is_premium(user_id):
        expiry = get_premium_expiry(user_id)
        expiry_text = expiry[:10] if expiry else "?"
        await update.message.reply_text(
            t(lang, "premium_already_active_with_expiry", expiry=expiry_text),
            parse_mode="Markdown",
        )
        return

    # Price display (convert tiyin to so'm for display)
    uzs_1m = PERSONAL_1M_UZS // 100  # 9990
    uzs_3m = PERSONAL_3M_UZS // 100  # 24990

    keyboard = [
        [
            InlineKeyboardButton(
                f"⭐ 1 {t(lang, 'month')} — {PERSONAL_1M_STARS} Stars",
                callback_data="pay_p1m_stars"
            ),
        ],
        [
            InlineKeyboardButton(
                f"⭐ 3 {t(lang, 'months')} — {PERSONAL_3M_STARS} Stars 🔥",
                callback_data="pay_p3m_stars"
            ),
        ],
        [
            InlineKeyboardButton(
                f"💳 1 {t(lang, 'month')} — {uzs_1m:,} so'm",
                callback_data="pay_p1m_uzs"
            ),
        ],
        [
            InlineKeyboardButton(
                f"💳 3 {t(lang, 'months')} — {uzs_3m:,} so'm 🔥",
                callback_data="pay_p3m_uzs"
            ),
        ],
    ]
    await update.message.reply_text(
        t(lang, "premium_info"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    # Promo code hint
    await update.message.reply_text(
        t(lang, "premium_promo_hint"),
        parse_mode="Markdown",
    )


# ─── /addpromo (Admin) ────────────────────────────────────────────────────────

async def add_promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 3:
        await update.message.reply_text(
            "🔑 *Syntax:* `/addpromo [code] [days] [once/multi]`",
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


# ─── Payment gateway callback ─────────────────────────────────────────────────

# Map callback_data to (currency, amount, days, title)
PAYMENT_PLANS = {
    "pay_p1m_stars": ("XTR", PERSONAL_1M_STARS, 30, "Premium 1 month (Stars)"),
    "pay_p3m_stars": ("XTR", PERSONAL_3M_STARS, 90, "Premium 3 months (Stars)"),
    "pay_p1m_uzs": ("UZS", PERSONAL_1M_UZS, 30, "Premium 1 month (So'm)"),
    "pay_p3m_uzs": ("UZS", PERSONAL_3M_UZS, 90, "Premium 3 months (So'm)"),
}


async def payment_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    plan = PAYMENT_PLANS.get(query.data)
    if not plan:
        return

    currency, amount, days, title = plan
    provider_token = "" if currency == "XTR" else UZS_PROVIDER_TOKEN
    payload = f"premium_{days}d"

    await context.bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=f"{days}-day Premium subscription",
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=[LabeledPrice(title, amount)],
    )


# ─── Pre-checkout & payment success ──────────────────────────────────────────

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    # Determine days from payload
    payload = update.message.successful_payment.invoice_payload
    if "90" in payload:
        days = 90
    else:
        days = 30

    set_premium(user_id, days=days)
    try:
        await update.message.set_reaction([ReactionTypeEmoji(emoji="🎉")])
    except TelegramError:
        pass
    await update.message.reply_text(
        t(lang, "premium_success_with_days", days=days),
        parse_mode="Markdown",
    )
