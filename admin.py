"""
Phase 2 Admin Module — async database + metrics integration.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from config import ADMIN_ID
from database import get_stats, get_all_user_ids, get_url_cache_size, clear_url_cache, get_recent_reports
from logger import get_logger, metrics, health
from cache_manager import cache

logger = get_logger("admin")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ─── ADMIN PANEL ─────────────────────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun.")
        return

    stats = await get_stats()
    cache_size = await get_url_cache_size()
    cache_stats = cache.get_stats()

    text = (
        "🔐 *ADMIN PANEL*\n\n"
        f"👥 Jami foydalanuvchi: `{stats['total_users']}`\n"
        f"⭐ Premium: `{stats['total_premium']}`\n"
        f"🚨 Hisobotlar: `{stats['total_reports']}`\n"
        f"🗄 URL Cache (DB): `{cache_size}`\n"
        f"💾 Cache Backend: `{cache_stats['backend']}` (hit rate: {cache_stats['hit_rate_percent']}%)\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )

    keyboard = [
        [InlineKeyboardButton("🚨 So'nggi hisobotlar", callback_data="admin_reports")],
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Metrics & Health", callback_data="admin_metrics")],
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

    action = query.data

    if action == "admin_reports":
        reports = await get_recent_reports(limit=10)
        if not reports:
            await query.edit_message_text("📭 Hech qanday hisobot yo'q.")
            return
        text = "🚨 *So'nggi hisobotlar:*\n\n"
        for r in reports:
            text += f"• `{r['url']}`\n  📅 {r['date']} | 👤 {r['user_id']}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_users":
        stats = await get_stats()
        text = (
            f"👥 *Foydalanuvchilar:*\n\n"
            f"Jami: `{stats['total_users']}`\n"
            f"Premium: `{stats['total_premium']}`\n"
            f"Bepul: `{stats['total_users'] - stats['total_premium']}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_metrics":
        # Show metrics and health report
        metrics_text = await metrics.get_formatted_report()
        health_text = health.get_formatted_status()
        cache_stats = cache.get_stats()

        text = f"{metrics_text}\n\n{health_text}\n"
        text += f"\n💾 *Cache Stats:*\n"
        text += f"• Backend: `{cache_stats['backend']}`\n"
        text += f"• Hit Rate: `{cache_stats['hit_rate_percent']}%`\n"
        text += f"• Hits: `{cache_stats['hits']}` | Misses: `{cache_stats['misses']}`\n"
        text += f"• Errors: `{cache_stats['errors']}`\n"

        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_clear_cache":
        await clear_url_cache()
        await cache.clear_all()
        await query.edit_message_text("✅ URL cache (DB + Redis/Memory) tozalandi!")
        logger.info("Admin cleared all caches")


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

    all_users = await get_all_user_ids()
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
            failed += 1

        # Update progress every 10 users
        if (success + failed) % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"📤 Yuborilmoqda... {success + failed}/{len(all_users)}"
                )
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ *Broadcast yakunlandi!*\n\n"
        f"✔️ Muvaffaqiyatli: `{success}`\n"
        f"❌ Muvaffaqiyatsiz: `{failed}` (bot bloklangan yoki o'chirilgan)",
        parse_mode="Markdown"
    )
    logger.info("Broadcast completed: %d success, %d failed", success, failed)
    await metrics.record_event("broadcast", count=1)
