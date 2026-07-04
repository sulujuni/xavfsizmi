"""
Bot command menus — reduced public list (~8 commands).
Other commands still work but are discoverable via /help.
"""

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

ADMIN_EXTRA_COMMANDS = [
    ("stats", "📊 Bot statistikasi"),
    ("broadcast", "📢 Hammaga xabar yuborish"),
    ("admin", "🔐 Admin panel"),
    ("addpromo", "🔑 Promokod yaratish"),
    ("ratelimit", "📉 API limit dashboard"),
    ("dbinfo", "🗄 Database va cache holati"),
]
