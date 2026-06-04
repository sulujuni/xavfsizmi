"""
Premium & Payment handlers:
/premium, /promo, /addpromo, payment callbacks, pre-checkout, success

Payment methods:
- Telegram Stars (in-app)
- Paynet QR link (external)
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
    GROUP_1M_STARS, GROUP_3M_STARS,
)
from database import (
    get_user_lang, is_premium, set_premium, get_premium_expiry,
    is_group_premium, set_group_premium, get_group_premium_expiry,
    create_promocode, redeem_promocode,
)
from languages import t
from admin import is_admin

# Paynet QR link
PAYNET_QR_LINK = "https://app.paynet.uz/qr-online/00020101021140440012qr-online.uz01186r10poerJSNZJzxWmP0202115204531153038605802UZ5910AO'PAYNET'6008Tashkent610610002164280002uz0106PAYNET0208Toshkent80520012qr-online.uz03097120207070419marketing@paynet.uz63040D46"


# ─── /premium ─────────────────────────────────────────────────────────────────

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    is_group = update.effective_chat.type in ["group", "supergroup"]

    # Admin toggle: /premium off to test as free user, /premium on to restore
    if is_admin(user_id) and context.args:
        arg = context.args[0].lower()
        if arg == "off":
            from database import load_db, save_db
            db = load_db()
            key = str(user_id)
            if key in db:
                db[key].pop("premium_until", None)
                db[key].pop("premium", None)
                save_db(db)
            await update.message.reply_text("🔓 Admin Premium o'chirildi. Endi oddiy user sifatida test qilishingiz mumkin.")
            return
        elif arg == "on":
            set_premium(user_id, days=9999)
            await update.message.reply_text("🔒 Admin Premium qayta yoqildi.")
            return

    if is_group:
        # Group premium — only admins can buy
        chat_id = update.effective_chat.id
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ["administrator", "creator"]:
                await update.message.reply_text(t(lang, "group_premium_admin_only"))
                return
        except Exception:
            return

        if is_group_premium(chat_id):
            expiry = get_group_premium_expiry(chat_id)
            expiry_text = expiry[:10] if expiry else "?"
            await update.message.reply_text(
                t(lang, "group_premium_active", expiry=expiry_text),
                parse_mode="Markdown",
            )
            return

        keyboard = [
            [InlineKeyboardButton(f"⭐ 1 {t(lang, 'month')} — {GROUP_1M_STARS} Stars", callback_data="pay_g1m_stars")],
            [InlineKeyboardButton(f"⭐ 3 {t(lang, 'months')} — {GROUP_3M_STARS} Stars 🔥", callback_data="pay_g3m_stars")],
            [InlineKeyboardButton(f"💳 Paynet ({t(lang, 'pay_via_qr')})", url=PAYNET_QR_LINK)],
        ]
        await update.message.reply_text(
            t(lang, "group_premium_info"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    else:
        # Personal premium
        if is_premium(user_id):
            expiry = get_premium_expiry(user_id)
            expiry_text = expiry[:10] if expiry else "?"
            await update.message.reply_text(
                t(lang, "premium_already_active_with_expiry", expiry=expiry_text),
                parse_mode="Markdown",
            )
            return

        keyboard = [
            [InlineKeyboardButton(f"⭐ 1 {t(lang, 'month')} — {PERSONAL_1M_STARS} Stars", callback_data="pay_p1m_stars")],
            [InlineKeyboardButton(f"⭐ 3 {t(lang, 'months')} — {PERSONAL_3M_STARS} Stars 🔥", callback_data="pay_p3m_stars")],
            [InlineKeyboardButton(f"💳 Paynet ({t(lang, 'pay_via_qr')})", url=PAYNET_QR_LINK)],
        ]
        await update.message.reply_text(
            t(lang, "premium_info"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
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


# ─── Payment gateway callback (Stars only now) ───────────────────────────────

PAYMENT_PLANS = {
    "pay_p1m_stars": (PERSONAL_1M_STARS, 30, "Personal Premium 1 month", "personal"),
    "pay_p3m_stars": (PERSONAL_3M_STARS, 90, "Personal Premium 3 months", "personal"),
    "pay_g1m_stars": (GROUP_1M_STARS, 30, "Group Premium 1 month", "group"),
    "pay_g3m_stars": (GROUP_3M_STARS, 90, "Group Premium 3 months", "group"),
}


async def payment_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    plan = PAYMENT_PLANS.get(query.data)
    if not plan:
        return

    amount, days, title, plan_type = plan
    payload = f"{plan_type}_{days}d_{chat_id}"

    await context.bot.send_invoice(
        chat_id=query.from_user.id if plan_type == "group" else chat_id,
        title=title,
        description=f"{days}-day Premium subscription",
        payload=payload,
        provider_token="",  # Empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice(title, amount)],
    )


# ─── Pre-checkout & payment success ──────────────────────────────────────────

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    # Parse payload to determine plan type and days
    payload = update.message.successful_payment.invoice_payload
    parts = payload.split("_")
    plan_type = parts[0] if parts else "personal"

    if "90" in payload:
        days = 90
    else:
        days = 30

    if plan_type == "group" and len(parts) >= 3:
        try:
            group_chat_id = int(parts[2])
            set_group_premium(group_chat_id, days=days)
            await update.message.reply_text(
                t(lang, "group_premium_success", days=days),
                parse_mode="Markdown",
            )
        except (ValueError, IndexError):
            set_premium(user_id, days=days)
            await update.message.reply_text(
                t(lang, "premium_success_with_days", days=days),
                parse_mode="Markdown",
            )
    else:
        set_premium(user_id, days=days)
        try:
            await update.message.set_reaction([ReactionTypeEmoji(emoji="🎉")])
        except TelegramError:
            pass
        await update.message.reply_text(
            t(lang, "premium_success_with_days", days=days),
            parse_mode="Markdown",
        )
