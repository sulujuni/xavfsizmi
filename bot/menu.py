"""
Bot command menus — reduced public list (~8 commands).
Other commands still work but are discoverable via /help.
"""
from telegram import BotCommand, BotCommandScopeChat, MenuButtonCommands

SUPPORTED_LANGS = ("uz", "ru", "en")

PUBLIC_MENU_COMMANDS = {
    "uz": [
        ("start", "🚀 Boshlash"),
        ("help", "📖 Yordam"),
        ("check", "🔍 Havola tekshirish"),
        ("breach", "🔐 Email/Parol tekshiruvi"),
        ("ask", "🤖 AI yordamchi"),
        ("premium", "⭐ Premium"),
        ("referral", "👥 Taklif qilish"),
        ("language", "🌐 Til"),
    ],
    "ru": [
        ("start", "🚀 Старт"),
        ("help", "📖 Помощь"),
        ("check", "🔍 Проверка ссылки"),
        ("breach", "🔐 Проверка email/пароля"),
        ("ask", "🤖 AI помощник"),
        ("premium", "⭐ Премиум"),
        ("referral", "👥 Пригласить"),
        ("language", "🌐 Язык"),
    ],
    "en": [
        ("start", "🚀 Start"),
        ("help", "📖 Help"),
        ("check", "🔍 Check a link"),
        ("breach", "🔐 Email/Password check"),
        ("ask", "🤖 AI assistant"),
        ("premium", "⭐ Premium"),
        ("referral", "👥 Invite friends"),
        ("language", "🌐 Language"),
    ],
}

ADMIN_MENU_COMMANDS = {
    "uz": [
        ("stats", "📊 Bot statistikasi"),
        ("broadcast", "📢 Hammaga xabar yuborish"),
        ("admin", "🔐 Admin panel"),
        ("addpromo", "🔑 Promokod yaratish"),
        ("ratelimit", "📉 API limit dashboard"),
        ("dbinfo", "🗄 Database va cache holati"),
        ("restart", "🔄 Botni qayta ishga tushirish"),
    ],
    "ru": [
        ("stats", "📊 Статистика бота"),
        ("broadcast", "📢 Рассылка всем"),
        ("admin", "🔐 Админ панель"),
        ("addpromo", "🔑 Создать промокод"),
        ("ratelimit", "📉 Лимиты API"),
        ("dbinfo", "🗄 Статус БД и кеша"),
        ("restart", "🔄 Перезапустить бота"),
    ],
    "en": [
        ("stats", "📊 Bot statistics"),
        ("broadcast", "📢 Broadcast to all"),
        ("admin", "🔐 Admin panel"),
        ("addpromo", "🔑 Create promo code"),
        ("ratelimit", "📉 API rate limits"),
        ("dbinfo", "🗄 Database & cache status"),
        ("restart", "🔄 Restart the bot"),
    ],
}

# Legacy alias used by bot/app.py if present
ADMIN_EXTRA_COMMANDS = ADMIN_MENU_COMMANDS["uz"]


def build_menu_commands(lang: str, include_admin: bool = False) -> list:
    """Return a list of telegram.BotCommand for the given language."""
    public = PUBLIC_MENU_COMMANDS.get(lang, PUBLIC_MENU_COMMANDS["en"])
    pairs = list(public)
    if include_admin:
        admin_extras = ADMIN_MENU_COMMANDS.get(lang, ADMIN_MENU_COMMANDS["en"])
        pairs.extend(admin_extras)
    return [BotCommand(cmd, desc) for cmd, desc in pairs]


async def apply_startup_menus(bot, admin_id: int, default_lang: str = "uz"):
    """Configure the default command menu and the admin's per-chat menu on startup."""
    await bot.set_my_commands(build_menu_commands(default_lang, include_admin=False))
    try:
        await bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception:
        pass
    if admin_id:
        try:
            await bot.set_my_commands(
                commands=build_menu_commands(default_lang, include_admin=True),
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception:
            pass


async def set_user_menu(bot, user_id: int, lang: str, is_admin_user: bool = False):
    """Set the per-chat command menu for a single user in their language."""
    try:
        await bot.set_my_commands(
            commands=build_menu_commands(lang, include_admin=is_admin_user),
            scope=BotCommandScopeChat(chat_id=user_id),
        )
    except Exception:
        pass
