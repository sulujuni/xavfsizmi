"""
Xavfsizmi? Bot — Main Entry Point
All handler logic is split into the handlers/ package.
"""
import logging
from telegram import MenuButtonCommands, BotCommand, BotCommandScopeChat, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ConversationHandler,
    BusinessConnectionHandler,
    TypeHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import BOT_TOKEN, ADMIN_ID, USE_WEBHOOK, WEBHOOK_URL, WEBHOOK_PORT
from admin import admin_command, admin_callback, broadcast_command, ratelimit_command
from error_handler import error_handler
from rate_tracker import send_limit_warnings

from handlers import (
    # Command handlers
    start_command,
    help_command,
    language_command,
    language_callback,
    group_language_callback,
    history_command,
    stats_command,
    referral_command,
    phish_command,
    # Conversation commands (2-step)
    scammer_command, scammer_receive,
    report_command, report_receive,
    feedback_command, feedback_receive,
    cancel_conversation,
    WAITING_SCAMMER_INPUT,
    WAITING_REPORT_INPUT, WAITING_FEEDBACK_INPUT,
    # Premium & payment handlers
    premium_command,
    add_promo_command,
    promo_command,
    payment_gateway_callback,
    admin_payment_callback,
    pre_checkout,
    payment_success,
    paynet_receipt_command,
    paynet_receipt_receive,
    paynet_receipt_cancel,
    WAITING_PAYNET_RECEIPT,
    # Breach conversation
    breach_command,
    breach_receive_input,
    breach_cancel,
    WAITING_BREACH_INPUT,
    # Private message handlers
    check_subscription_callback,
    handle_private_message,
    handle_apk,
    handle_photo,
    # Group message handlers
    handle_group_message,
    handle_group_apk,
    handle_group_photo,
    # Secretary mode (Business Connection)
    handle_business_connection,
    handle_business_message,
    # Daily tips & leaderboard
    tips_command,
    send_daily_tips,
    top_command,
    reward_top_referrers,
)

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ─── BOT MENU SETUP (post_init) ──────────────────────────────────────────────

async def setup_menu(application: Application):
    """Configure bot menu buttons and commands on startup."""
    public_commands = [
        BotCommand("start", "🚀 Botni ishga tushirish"),
        BotCommand("help", "📖 Barcha buyruqlar ro'yxati"),
        BotCommand("language", "🌐 Tilni o'zgartirish"),
        BotCommand("breach", "🔐 Email/Parol tekshiruvi"),
        BotCommand("scammer", "👤 Skammer tekshiruvi"),
        BotCommand("phish", "🎣 Fishing simulyatori"),
        BotCommand("referral", "👥 Do'stlarni taklif qilish"),
        BotCommand("top", "🏆 Liderlar jadvali"),
        BotCommand("tips", "💡 Kunlik maslahatlar"),
        BotCommand("premium", "⭐ Premium xarid qilish"),
        BotCommand("history", "🕒 Tekshiruvlar tarixi"),
        BotCommand("feedback", "📩 Taklif va shikoyatlar"),
        BotCommand("report", "🚨 Xavfli link xabar berish"),
    ]
    await application.bot.set_my_commands(public_commands)

    try:
        await application.bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        print(f"⚠️ Menu button: {e}")

    # Admin gets extra commands
    admin_commands = public_commands + [
        BotCommand("stats", "📊 Bot statistikasi"),
        BotCommand("broadcast", "📢 Hammaga xabar yuborish"),
        BotCommand("admin", "🔐 Admin panel"),
        BotCommand("addpromo", "🔑 Promokod yaratish"),
        BotCommand("ratelimit", "📉 API limit dashboard"),
    ]
    try:
        await application.bot.set_my_commands(
            commands=admin_commands,
            scope=BotCommandScopeChat(chat_id=ADMIN_ID),
        )
        print("✅ Bot menyulari muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Menyu sozlashda xatolik: {e}")


# ─── SCHEDULER SETUP ──────────────────────────────────────────────────────────

def setup_scheduler(application: Application):
    """Configure APScheduler for daily tips, monthly rewards, and rate limit warnings."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        send_daily_tips, CronTrigger(hour=9, minute=0),
        args=[application], id="daily_tips", replace_existing=True,
    )
    scheduler.add_job(
        reward_top_referrers, CronTrigger(day=1, hour=0, minute=0),
        args=[application], id="monthly_reward", replace_existing=True,
    )
    scheduler.add_job(
        send_limit_warnings, CronTrigger(hour="*/4", minute=0),
        args=[application], id="rate_limit_check", replace_existing=True,
    )

    scheduler.start()
    print("⏰ Scheduler ishga tushdi")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(setup_menu).build()

    # ── Command Handlers ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("promo", promo_command))
    app.add_handler(CommandHandler("addpromo", add_promo_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("premium", premium_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("phish", phish_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("ratelimit", ratelimit_command))
    app.add_handler(CommandHandler("tips", tips_command))
    app.add_handler(CommandHandler("top", top_command))

    # ── Breach Conversation Handler ───────────────────────────────────────────
    breach_conv = ConversationHandler(
        entry_points=[CommandHandler("breach", breach_command)],
        states={
            WAITING_BREACH_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, breach_receive_input)
            ]
        },
        fallbacks=[CommandHandler("cancel", breach_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(breach_conv)

    # ── Paynet Receipt Conversation Handler ───────────────────────────────────
    receipt_conv = ConversationHandler(
        entry_points=[CommandHandler("receipt", paynet_receipt_command)],
        states={WAITING_PAYNET_RECEIPT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, paynet_receipt_receive),
            MessageHandler(filters.PHOTO, paynet_receipt_receive),
        ]},
        fallbacks=[CommandHandler("cancel", paynet_receipt_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(receipt_conv)

    # ── Scammer Conversation Handler ──────────────────────────────────────────
    scammer_conv = ConversationHandler(
        entry_points=[CommandHandler("scammer", scammer_command)],
        states={WAITING_SCAMMER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, scammer_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(scammer_conv)

    # ── Report Conversation Handler ───────────────────────────────────────────
    report_conv = ConversationHandler(
        entry_points=[CommandHandler("report", report_command)],
        states={WAITING_REPORT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(report_conv)

    # ── Feedback Conversation Handler ─────────────────────────────────────────
    feedback_conv = ConversationHandler(
        entry_points=[CommandHandler("feedback", feedback_command)],
        states={WAITING_FEEDBACK_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(feedback_conv)

    # ── Callback Query Handlers ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_payment_callback, pattern="^(approve_|reject_)"))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(group_language_callback, pattern="^glang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(payment_gateway_callback, pattern="^pay_|^paynet_"))

    # ── Payment Handlers ──────────────────────────────────────────────────────
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    # ── Secretary Mode (Business Connection) ──────────────────────────────────
    app.add_handler(BusinessConnectionHandler(handle_business_connection))
    app.add_handler(TypeHandler(type=Update, callback=handle_business_message), group=-1)

    # ── Private Message Handlers ──────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_apk))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private_message))

    # ── Group Message Handlers ────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.Document.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), handle_group_apk))
    app.add_handler(MessageHandler(filters.PHOTO & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), handle_group_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), handle_group_message))

    # ── Scheduler + Error Handler ─────────────────────────────────────────────
    setup_scheduler(app)
    app.add_error_handler(error_handler)

    # ── Start Bot ─────────────────────────────────────────────────────────────
    if USE_WEBHOOK and WEBHOOK_URL:
        print(f"🌐 Webhook mode: {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0", port=WEBHOOK_PORT, url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=["message", "callback_query", "pre_checkout_query", "business_connection", "business_message", "edited_business_message"],
        )
    else:
        print("🚀 Xavfsizmi? Bot ishga tushdi!")
        app.run_polling(allowed_updates=["message", "callback_query", "pre_checkout_query", "business_connection", "business_message", "edited_business_message"])


if __name__ == "__main__":
    main()
