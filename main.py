"""
Xavfsizmi? Bot — Main Entry Point
All handler logic is split into the handlers/ package.
"""
import logging
from telegram import MenuButtonCommands, BotCommand, BotCommandScopeChat
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID
from admin import admin_command, admin_callback, broadcast_command

from handlers import (
    # Command handlers
    start_command,
    language_command,
    language_callback,
    group_language_callback,
    history_command,
    feedback_command,
    report_command,
    stats_command,
    referral_command,
    phish_command,
    # Premium & payment handlers
    premium_command,
    add_promo_command,
    promo_command,
    payment_gateway_callback,
    pre_checkout,
    payment_success,
    # Breach conversation
    breach_command,
    breach_receive_email,
    breach_cancel,
    WAITING_BREACH_EMAIL,
    # Private message handlers
    check_subscription_callback,
    handle_private_message,
    handle_apk,
    handle_photo,
    # Group message handlers
    handle_group_message,
    handle_group_apk,
    handle_group_photo,
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
        BotCommand("language", "🌐 Tilni o'zgartirish (Language)"),
        BotCommand("breach", "🔐 Email leak check (Premium)"),
        BotCommand("referral", "👥 Do'stlarni taklif qilish"),
        BotCommand("phish", "🎣 Fishing simulyatori (Xavfsizlik testi)"),
        BotCommand("premium", "⭐ Premium xarid qilish / Promokod"),
        BotCommand("feedback", "📩 Taklif va shikoyatlar"),
        BotCommand("report", "🚨 Xavfli link haqida xabar berish"),
        BotCommand("history", "🕒 Tekshiruvlar tarixi"),
    ]
    await application.bot.set_my_commands(public_commands)

    try:
        await application.bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        print(f"⚠️ Menu button: {e}")

    # Admin gets extra commands
    admin_commands = public_commands + [
        BotCommand("stats", "📊 Bot statistikasi (Admin Only)"),
        BotCommand("broadcast", "📢 Hammaga xabar yuborish"),
        BotCommand("admin", "🔐 Admin panel"),
        BotCommand("addpromo", "🔑 Promokod yaratish"),
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

    # ── Command Handlers ──────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
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
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("history", history_command))

    # ── Breach Conversation Handler ───────────────────────────────────────────
    breach_conv = ConversationHandler(
        entry_points=[CommandHandler("breach", breach_command)],
        states={
            WAITING_BREACH_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, breach_receive_email)
            ]
        },
        fallbacks=[CommandHandler("cancel", breach_cancel)],
        per_user=True,
        per_chat=True,
    )
    app.add_handler(breach_conv)

    # ── Callback Query Handlers ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(group_language_callback, pattern="^glang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(payment_gateway_callback, pattern="^pay_"))

    # ── Payment Handlers ──────────────────────────────────────────────────────
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    # ── Private Message Handlers (Documents, Photos, Text) ────────────────────
    app.add_handler(MessageHandler(
        filters.Document.ALL & filters.ChatType.PRIVATE, handle_apk
    ))
    app.add_handler(MessageHandler(
        filters.PHOTO & filters.ChatType.PRIVATE, handle_photo
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private_message
    ))

    # ── Group Message Handlers (Documents, Photos, Text) ──────────────────────
    app.add_handler(MessageHandler(
        filters.Document.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_group_apk,
    ))
    app.add_handler(MessageHandler(
        filters.PHOTO & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_group_photo,
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_group_message,
    ))

    print("🚀 Xavfsizmi? Bot muvaffaqiyatli ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
