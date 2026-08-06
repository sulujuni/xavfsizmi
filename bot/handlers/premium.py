"""
Premium & Payment handlers:
/premium, /promo, /addpromo, payment callbacks, pre-checkout, success

Payment methods:
- Telegram Stars (instant, recommended)
- Paynet QR (manual admin approval)
"""
from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import TelegramError

from bot.config import (
    ADMIN_ID,
    PERSONAL_1M_STARS, PERSONAL_3M_STARS,
    GROUP_1M_STARS, GROUP_3M_STARS,
)
from bot.core.database import (
    get_user_lang, is_premium, set_premium, get_premium_expiry,
    is_group_premium, set_group_premium, get_group_premium_expiry,
    create_promocode, redeem_promocode, load_db, save_db, log_event,
)
from bot.i18n import t
from bot.handlers.admin import is_admin

# Paynet QR link
PAYNET_QR_LINK = "https://app.paynet.uz/qr-online/00020101021140440012qr-online.uz01186r10poerJSNZJzxWmP0202115204531153038605802UZ5910AO'PAYNET'6008Tashkent610610002164280002uz0106PAYNET0208Toshkent80520012qr-online.uz03097120207070419marketing@paynet.uz63040D46"

# Paynet prices for display
PAYNET_PRICES = {
    "1m": "9,990",
    "3m": "24,990",
    "g1m": "19,990",
    "g3m": "49,990",
}

# Conversation state for Paynet receipt
WAITING_PAYNET_RECEIPT = 20


# ─── /premium ─────────────────────────────────────────────────────────────────

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    is_group_chat = update.effective_chat.type in ["group", "supergroup"]

    # Admin toggle: /premium off or /premium on (not a real "view" — skip logging)
    if is_admin(user_id) and context.args:
        arg = context.args[0].lower()
        if arg == "off":
            db = load_db()
            key = str(user_id)
            if key in db:
                db[key].pop("premium_until", None)
                db[key].pop("premium", None)
                save_db(db)
            await update.message.reply_text(t(lang, "admin_premium_off"))
            return
        elif arg == "on":
            set_premium(user_id, days=9999)
            await update.message.reply_text(t(lang, "admin_premium_on"))
            return

    log_event(user_id, "premium_viewed", {"chat_type": "group" if is_group_chat else "private"})

    if is_group_chat:
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
            [InlineKeyboardButton(f"💳 Paynet 1 {t(lang, 'month')} — {PAYNET_PRICES['g1m']} so'm", callback_data="paynet_g1m")],
            [InlineKeyboardButton(f"💳 Paynet 3 {t(lang, 'months')} — {PAYNET_PRICES['g3m']} so'm", callback_data="paynet_g3m")],
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
            [InlineKeyboardButton(f"⭐ 1 {t(lang, 'month')} — {PERSONAL_1M_STARS} Stars ⚡", callback_data="pay_p1m_stars")],
            [InlineKeyboardButton(f"⭐ 3 {t(lang, 'months')} — {PERSONAL_3M_STARS} Stars 🔥", callback_data="pay_p3m_stars")],
            [InlineKeyboardButton(f"💳 Paynet 1 {t(lang, 'month')} — {PAYNET_PRICES['1m']} so'm", callback_data="paynet_p1m")],
            [InlineKeyboardButton(f"💳 Paynet 3 {t(lang, 'months')} — {PAYNET_PRICES['3m']} so'm", callback_data="paynet_p3m")],
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
        await update.message.reply_text("❌")
        return
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

# Stars payment plans
STARS_PLANS = {
    "pay_p1m_stars": (PERSONAL_1M_STARS, 30, "Personal Premium 1 month", "personal"),
    "pay_p3m_stars": (PERSONAL_3M_STARS, 90, "Personal Premium 3 months", "personal"),
    "pay_g1m_stars": (GROUP_1M_STARS, 30, "Group Premium 1 month", "group"),
    "pay_g3m_stars": (GROUP_3M_STARS, 90, "Group Premium 3 months", "group"),
}

# Paynet plan details (for admin notification)
PAYNET_PLANS = {
    "paynet_p1m": (30, "personal", "9,990 so'm", "1 oy"),
    "paynet_p3m": (90, "personal", "24,990 so'm", "3 oy"),
    "paynet_g1m": (30, "group", "19,990 so'm", "1 oy"),
    "paynet_g3m": (90, "group", "49,990 so'm", "3 oy"),
}


async def payment_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user = query.from_user
    lang = get_user_lang(user.id)

    # ── Stars Payment ─────────────────────────────────────────────────────────
    if query.data in STARS_PLANS:
        amount, days, title, plan_type = STARS_PLANS[query.data]
        payload = f"{plan_type}_{days}d_{chat_id}"

        await context.bot.send_invoice(
            chat_id=user.id if plan_type == "group" else chat_id,
            title=title,
            description=f"{days}-day Premium subscription",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(title, amount)],
        )

    # ── Paynet Payment (show QR + instructions) ───────────────────────────────
    elif query.data in PAYNET_PLANS:
        days, plan_type, price, duration = PAYNET_PLANS[query.data]

        # Store pending payment info in context
        context.user_data["paynet_pending"] = {
            "days": days,
            "plan_type": plan_type,
            "price": price,
            "duration": duration,
            "chat_id": chat_id,
            "user_id": user.id,
        }

        keyboard = [
            [InlineKeyboardButton(f"💳 {t(lang, 'open_paynet')}", url=PAYNET_QR_LINK)],
        ]

        await context.bot.send_message(
            chat_id=user.id,
            text=t(lang, "paynet_instructions", price=price, duration=duration),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )


# ─── Paynet receipt handler (user sends receipt after paying) ─────────────────

async def paynet_receipt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User sends /receipt after paying via Paynet."""
    user = update.effective_user
    lang = get_user_lang(user.id)

    await update.message.reply_text(t(lang, "paynet_send_receipt"), parse_mode="Markdown")
    return WAITING_PAYNET_RECEIPT


async def paynet_receipt_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive receipt number/screenshot and notify admin."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    receipt = update.message.text.strip() if update.message.text else "📸 Screenshot"

    # Get pending payment info
    pending = context.user_data.get("paynet_pending", {})
    price = pending.get("price", "?")
    duration = pending.get("duration", "?")
    plan_type = pending.get("plan_type", "personal")
    days = pending.get("days", 30)

    # Notify admin with approve/reject buttons
    admin_text = (
        f"🧾 *YANGI PAYNET TO'LOV!*\n\n"
        f"👤 *User:* {user.full_name} (`{user.id}`)\n"
        f"💰 *Narx:* {price}\n"
        f"📅 *Reja:* {duration} ({plan_type})\n"
        f"🧾 *Kvitansiya:* `{receipt}`\n\n"
        f"⚠️ Paynet ilovangizda ushbu to'lovni tekshiring!"
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user.id}_{days}_{plan_type}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user.id}"),
        ]
    ]

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except TelegramError:
        pass

    # Also forward screenshot if it's a photo
    if update.message.photo:
        try:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"🧾 Receipt from {user.full_name} ({user.id})",
            )
        except TelegramError:
            pass

    await update.message.reply_text(t(lang, "paynet_receipt_sent"))
    return ConversationHandler.END


async def paynet_receipt_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "breach_cancel"))
    return ConversationHandler.END


# ─── Admin approve/reject callback ───────────────────────────────────────────

async def admin_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin approves or rejects Paynet payment."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    data = query.data

    if data.startswith("approve_"):
        parts = data.split("_")
        # approve_USERID_DAYS_PLANTYPE
        try:
            user_id = int(parts[1])
            days = int(parts[2])
            plan_type = parts[3] if len(parts) > 3 else "personal"
        except (IndexError, ValueError):
            await query.edit_message_text("❌ Xatolik: noto'g'ri ma'lumot.")
            return

        if plan_type == "group":
            # For group, we'd need chat_id — for now give personal premium
            set_premium(user_id, days=days)
        else:
            set_premium(user_id, days=days)
        log_event(user_id, "premium_purchased", {"method": "paynet", "plan": plan_type, "days": days})

        # Notify user
        user_lang = get_user_lang(user_id)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=t(user_lang, "premium_success_with_days", days=days),
                parse_mode="Markdown",
            )
        except TelegramError:
            pass

        await query.edit_message_text(
            f"✅ *TASDIQLANDI!*\n\nUser `{user_id}` ga {days} kunlik Premium berildi.",
            parse_mode="Markdown",
        )

    elif data.startswith("reject_"):
        parts = data.split("_")
        try:
            user_id = int(parts[1])
        except (IndexError, ValueError):
            await query.edit_message_text("❌ Xatolik.")
            return

        # Notify user
        user_lang = get_user_lang(user_id)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=t(user_lang, "paynet_rejected"),
                parse_mode="Markdown",
            )
        except TelegramError:
            pass

        await query.edit_message_text("❌ *RAD ETILDI.* Foydalanuvchiga xabar yuborildi.")


# ─── Pre-checkout & payment success (Stars) ──────────────────────────────────

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

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
            log_event(user_id, "premium_purchased", {"method": "stars", "plan": "group", "days": days})
            await update.message.reply_text(
                t(lang, "group_premium_success", days=days),
                parse_mode="Markdown",
            )
        except (ValueError, IndexError):
            set_premium(user_id, days=days)
            log_event(user_id, "premium_purchased", {"method": "stars", "plan": "personal", "days": days})
            await update.message.reply_text(
                t(lang, "premium_success_with_days", days=days),
                parse_mode="Markdown",
            )
    else:
        set_premium(user_id, days=days)
        log_event(user_id, "premium_purchased", {"method": "stars", "plan": "personal", "days": days})
        try:
            await update.message.set_reaction([ReactionTypeEmoji(emoji="🎉")])
        except TelegramError:
            pass
        await update.message.reply_text(
            t(lang, "premium_success_with_days", days=days),
            parse_mode="Markdown",
        )
