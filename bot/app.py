"""
Xavfsizmi? Bot — Application builder + ALL handler registration.
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

from bot.config import BOT_TOKEN, ADMIN_ID, USE_WEBHOOK, WEBHOOK_URL, WEBHOOK_PORT
from bot.core.database import init_db
from bot.error_handler import error_handler
from bot.menu import PUBLIC_MENU_COMMANDS, ADMIN_EXTRA_COMMANDS
from bot.scheduler import setup_scheduler

from bot.handlers.start import (
    start_command, help_command, language_command,
    language_callback, group_language_callback,
    history_command, stats_command,
)
from bot.handlers.scan import (
    check_subscription_callback,
    handle_private_message, handle_apk, handle_photo,
)
from bot.handlers.group import (
    handle_group_message, handle_group_apk, handle_group_photo,
)
from bot.handlers.secretary import (
    handle_business_connection, handle_business_message,
)
from bot.handlers.premium import (
    premium_command, add_promo_command, promo_command,
    payment_gateway_callback, admin_payment_callback,
    pre_checkout, payment_success,
    paynet_receipt_command, paynet_receipt_receive, paynet_receipt_cancel,
    WAITING_PAYNET_RECEIPT,
)
from bot.handlers.breach import (
    breach_command, breach_receive_input, breach_cancel,
    WAITING_BREACH_INPUT,
    darkweb_command, darkweb_receive, WAITING_DARKWEB_INPUT,
    monitor_command, monitor_receive_email, monitor_remove_callback,
    WAITING_MONITOR_EMAIL,
)
from bot.handlers.social import (
    scammer_command, scammer_receive, WAITING_SCAMMER_INPUT,
    report_command, report_receive, WAITING_REPORT_INPUT,
    feedback_command, feedback_receive, WAITING_FEEDBACK_INPUT,
    cancel_conversation,
    referral_command, phish_command,
    tips_command, tips_toggle_callback,
    top_command,
)
from bot.handlers.ai import (
    ask_command, ask_receive, analyze_command, analyze_receive,
    ai_cancel, WAITING_ASK_INPUT, WAITING_ANALYZE_INPUT,
)
from bot.handlers.admin import (
    admin_command, admin_callback, broadcast_command,
    ratelimit_command, dbinfo_command,
)

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ─── BOT MENU SETUP (post_init) ──────────────────────────────────────────────

async def setup_menu(application: Application):
    """Configure bot menu buttons and commands on startup."""
    init_db()

    public_commands = [
        BotCommand(cmd, desc)
        for cmd, desc in PUBLIC_MENU_COMMANDS["uz"]
    ]
    await application.bot.set_my_commands(public_commands)

    try:
        await application.bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        print(f"⚠️ Menu button: {e}")

    # Admin gets extra commands
    admin_commands = public_commands + [
        BotCommand(cmd, desc) for cmd, desc in ADMIN_EXTRA_COMMANDS
    ]
    try:
        await application.bot.set_my_commands(
            commands=admin_commands,
            scope=BotCommandScopeChat(chat_id=ADMIN_ID),
        )
        print("✅ Bot menyulari muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Menyu sozlashda xatolik: {e}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(setup_menu).build()

    # ── Command Handlers (work everywhere) ───────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("premium", premium_command))

    # ── Command Handlers (private chat only) ──────────────────────────────────
    app.add_handler(CommandHandler("promo", promo_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("addpromo", add_promo_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("report", report_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("referral", referral_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("admin", admin_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("broadcast", broadcast_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("phish", phish_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("history", history_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("ratelimit", ratelimit_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("dbinfo", dbinfo_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("tips", tips_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("top", top_command, filters=filters.ChatType.PRIVATE))

    # ── Breach Conversation Handler (private only) ──────────────────────────────
    # All conversation state handlers use filters.UpdateType.MESSAGE to avoid
    # matching business_message updates (where update.message is None).
    _msg_text = filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE
    _msg_photo = filters.PHOTO & filters.UpdateType.MESSAGE

    breach_conv = ConversationHandler(
        entry_points=[CommandHandler("breach", breach_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_BREACH_INPUT: [MessageHandler(_msg_text, breach_receive_input)]},
        fallbacks=[CommandHandler("cancel", breach_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(breach_conv)

    # ── Paynet Receipt Conversation Handler (private only) ────────────────────
    receipt_conv = ConversationHandler(
        entry_points=[CommandHandler("receipt", paynet_receipt_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_PAYNET_RECEIPT: [
            MessageHandler(_msg_text, paynet_receipt_receive),
            MessageHandler(_msg_photo, paynet_receipt_receive),
        ]},
        fallbacks=[CommandHandler("cancel", paynet_receipt_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(receipt_conv)

    # ── Scammer Conversation Handler (private only) ───────────────────────────
    scammer_conv = ConversationHandler(
        entry_points=[CommandHandler("scammer", scammer_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_SCAMMER_INPUT: [MessageHandler(_msg_text, scammer_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(scammer_conv)

    # ── Report Conversation Handler (private only) ──────────────────────────────
    report_conv = ConversationHandler(
        entry_points=[CommandHandler("report", report_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_REPORT_INPUT: [MessageHandler(_msg_text, report_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(report_conv)

    # ── Feedback Conversation Handler (private only) ──────────────────────────
    feedback_conv = ConversationHandler(
        entry_points=[CommandHandler("feedback", feedback_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_FEEDBACK_INPUT: [MessageHandler(_msg_text, feedback_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(feedback_conv)

    # ── Dark Web Check Conversation Handler (private only) ────────────────────
    darkweb_conv = ConversationHandler(
        entry_points=[CommandHandler("darkweb", darkweb_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_DARKWEB_INPUT: [MessageHandler(_msg_text, darkweb_receive)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(darkweb_conv)

    # ── AI Ask Conversation Handler (private only) ────────────────────────────
    ask_conv = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_ASK_INPUT: [MessageHandler(_msg_text, ask_receive)]},
        fallbacks=[CommandHandler("cancel", ai_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(ask_conv)

    # ── AI Analyze Conversation Handler (private only) ────────────────────────
    analyze_conv = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_ANALYZE_INPUT: [MessageHandler(_msg_text, analyze_receive)]},
        fallbacks=[CommandHandler("cancel", ai_cancel)],
        per_user=True, per_chat=True,
    )
    app.add_handler(analyze_conv)

    # ── Breach Monitor Conversation Handler (private only) ────────────────────
    monitor_conv = ConversationHandler(
        entry_points=[CommandHandler("monitor", monitor_command, filters=filters.ChatType.PRIVATE)],
        states={WAITING_MONITOR_EMAIL: [MessageHandler(_msg_text, monitor_receive_email)]},
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_user=True, per_chat=True,
    )
    app.add_handler(monitor_conv)

    # ── Callback Query Handlers ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_payment_callback, pattern="^(approve_|reject_)"))
    app.add_handler(CallbackQueryHandler(monitor_remove_callback, pattern="^monrm_"))
    app.add_handler(CallbackQueryHandler(tips_toggle_callback, pattern="^tips_"))
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
