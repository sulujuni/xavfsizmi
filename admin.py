from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from config import ADMIN_ID
from database import get_stats, load_db

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_all_user_ids() -> list:
    """Get all real user IDs from the database"""
    db = load_db()
    return [
        int(k) for k in db.keys()
        if not k.startswith("group_")
        and k not in ("reports", "url_cache")
        and k.isdigit()
    ]

# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    stats = get_stats()
    db = load_db()
    reports = db.get("reports", [])
    all_users = get_all_user_ids()

    text = (
        "🔐 *ADMIN PANEL*\n\n"
        f"👥 Jami foydalanuvchi: `{stats['total_users']}`\n"
        f"⭐ Premium: `{stats['total_premium']}`\n"
        f"🚨 Hisobotlar: `{stats['total_reports']}`\n"
        f"🔗 URL Cache: `{len(db.get('url_cache', {}))}`\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )

    keyboard = [
        [InlineKeyboardButton("🚨 So'nggi hisobotlar", callback_data="admin_reports")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("🗑 Cache'ni tozalash", callback_data="admin_clear_cache")],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    db = load_db()
    action = query.data

    if action == "admin_reports":
        reports = db.get("reports", [])
        if not reports:
            await query.edit_message_text("📭 Hech qanday hisobot yo'q.")
            return
        # Show last 10 reports
        text = "🚨 *So'nggi hisobotlar:*\n\n"
        for r in reports[-10:][::-1]:
            text += f"• `{r['url']}`\n  📅 {r['date']} | 👤 {r['user_id']}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_users":
        users = get_all_user_ids()
        premium_users = [k for k in db.keys() if k.isdigit() and db[k].get("premium")]
        text = (
            f"👥 *Foydalanuvchilar:*\n\n"
            f"Jami: `{len(users)}`\n"
            f"Premium: `{len(premium_users)}`\n"
            f"Bepul: `{len(users) - len(premium_users)}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_clear_cache":
        db["url_cache"] = {}
        from database import save_db
        save_db(db)
        await query.edit_message_text("✅ URL cache tozalandi!")

# ─── BROADCAST ───────────────────────────────────────────────────────────────

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    if not context.args:
        await update.message.reply_text(
            "📢 *Broadcast yuborish:*\n\n"
            "Foydalanish: `/broadcast Xabar matni`\n\n"
            "Misol: `/broadcast Yangi funksiya qo'shildi! Endi QR kodlarni tekshirishingiz mumkin.`",
            parse_mode="Markdown"
        )
        return

    message_text = " ".join(context.args)
    broadcast_msg = f"📢 *SafeLink Bot xabari:*\n\n{message_text}"

    all_users = get_all_user_ids()
    status_msg = await update.message.reply_text(
        f"📤 Yuborilmoqda... 0/{len(all_users)}"
    )

    success = 0
    failed = 0

    for uid in all_users:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=broadcast_msg,
                parse_mode="Markdown"
            )
            success += 1
        except TelegramError:
            failed += 1  # User blocked the bot or account deleted

        # Update progress every 10 users
        if (success + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"📤 Yuborilmoqda... {success + failed}/{len(all_users)}"
                )
            except:
                pass

    await status_msg.edit_text(
        f"✅ *Broadcast yakunlandi!*\n\n"
        f"✔️ Muvaffaqiyatli: `{success}`\n"
        f"❌ Muvaffaqiyatsiz: `{failed}` (bot bloklangan yoki o'chirilgan)",
        parse_mode="Markdown"
    )
