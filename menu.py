"""
Single source of truth for the bot's command menu.

Both the startup menu setup (main.setup_menu) and the per-user language
switcher (handlers.commands) build their command lists from here, so the menu
never drifts between code paths.

Includes:
- PUBLIC_MENU_COMMANDS: shown to everyone, per language
- ADMIN_MENU_COMMANDS:  extra commands appended only for the admin
"""
from telegram import BotCommand, BotCommandScopeChat, MenuButtonCommands

# Languages we ship translated menus for.
SUPPORTED_LANGS = ("uz", "ru", "en")

PUBLIC_MENU_COMMANDS = {
    "uz": [
        ("start", "🚀 Botni ishga tushirish"),
        ("help", "📖 Barcha buyruqlar"),
        ("language", "🌐 Tilni o'zgartirish"),
        ("breach", "🔐 Email/Parol tekshiruvi"),
        ("monitor", "📡 Email monitoring (Premium)"),
        ("ask", "🤖 AI yordamchidan so'rash"),
        ("analyze", "🔍 Shubhali xabarni tahlil qilish"),
        ("scammer", "👤 Skammer tekshiruvi"),
        ("darkweb", "🕸 Dark web tekshiruvi"),
        ("phish", "🎣 Fishing simulyatori"),
        ("referral", "👥 Do'stlarni taklif qilish"),
        ("top", "🏆 Liderlar jadvali"),
        ("tips", "💡 Kunlik maslahatlar"),
        ("premium", "⭐ Premium xarid qilish"),
        ("history", "🕒 Tekshiruvlar tarixi"),
        ("feedback", "📩 Taklif va shikoyatlar"),
        ("report", "🚨 Xavfli link xabar berish"),
    ],
    "ru": [
        ("start", "🚀 Запустить бота"),
        ("help", "📖 Все команды"),
        ("language", "🌐 Сменить язык"),
        ("breach", "🔐 Проверка email/пароля"),
        ("monitor", "📡 Мониторинг email (Premium)"),
        ("ask", "🤖 Спросить AI-помощника"),
        ("analyze", "🔍 Анализ подозрительного сообщения"),
        ("scammer", "👤 Проверка скаммера"),
        ("darkweb", "🕸 Проверка dark web"),
        ("phish", "🎣 Симулятор фишинга"),
        ("referral", "👥 Пригласить друзей"),
        ("top", "🏆 Таблица лидеров"),
        ("tips", "💡 Ежедневные советы"),
        ("premium", "⭐ Купить Premium"),
        ("history", "🕒 История проверок"),
        ("feedback", "📩 Обратная связь"),
        ("report", "🚨 Сообщить о ссылке"),
    ],
    "en": [
        ("start", "🚀 Start the bot"),
        ("help", "📖 All commands"),
        ("language", "🌐 Change language"),
        ("breach", "🔐 Email/Password check"),
        ("monitor", "📡 Email monitoring (Premium)"),
        ("ask", "🤖 Ask the AI assistant"),
        ("analyze", "🔍 Analyze a suspicious message"),
        ("scammer", "👤 Scammer check"),
        ("darkweb", "🕸 Dark web check"),
        ("phish", "🎣 Phishing simulator"),
        ("referral", "👥 Invite friends"),
        ("top", "🏆 Leaderboard"),
        ("tips", "💡 Daily tips"),
        ("premium", "⭐ Buy Premium"),
        ("history", "🕒 Check history"),
        ("feedback", "📩 Send feedback"),
        ("report", "🚨 Report link"),
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
    ],
    "ru": [
        ("stats", "📊 Статистика бота"),
        ("broadcast", "📢 Рассылка всем"),
        ("admin", "🔐 Админ панель"),
        ("addpromo", "🔑 Создать промокод"),
        ("ratelimit", "📉 Лимиты API"),
        ("dbinfo", "🗄 Статус БД и кеша"),
    ],
    "en": [
        ("stats", "📊 Bot statistics"),
        ("broadcast", "📢 Broadcast to all"),
        ("admin", "🔐 Admin panel"),
        ("addpromo", "🔑 Create promo code"),
        ("ratelimit", "📉 API rate limits"),
        ("dbinfo", "🗄 Database & cache status"),
    ],
}


def build_menu_commands(lang: str, include_admin: bool = False) -> list:
    """Return a list of telegram.BotCommand for the given language.

    When include_admin is True, the admin-only commands are appended.
    """
    public = PUBLIC_MENU_COMMANDS.get(lang, PUBLIC_MENU_COMMANDS["en"])
    pairs = list(public)
    if include_admin:
        admin_extras = ADMIN_MENU_COMMANDS.get(lang, ADMIN_MENU_COMMANDS["en"])
        pairs.extend(admin_extras)
    return [BotCommand(cmd, desc) for cmd, desc in pairs]


async def apply_startup_menus(bot, admin_id: int, default_lang: str = "uz"):
    """Configure the default command menu, the menu button, and the admin's
    per-chat menu. Called once from main.setup_menu on startup."""
    # Default menu (public commands) shown to all users.
    await bot.set_my_commands(build_menu_commands(default_lang, include_admin=False))

    # Menu button (best effort).
    try:
        await bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception:
        pass

    # Admin gets the extra commands scoped to their own chat.
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
