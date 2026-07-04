"""
Command handlers:
/start, /help, /language, /history, /feedback, /report, /stats,
/referral, /phish, /scammer, /privacy
"""
import random
from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from bot.config import ADMIN_ID, DAILY_FREE_LIMIT, CHANNEL_INVITE_LINK
from bot.core.database import (
    get_user_lang, set_user_lang, get_group_lang, set_group_lang,
    get_history, add_referral, get_referral_count, ensure_user_exists,
)
from bot.i18n import t, gt
from bot.handlers.admin import is_admin

REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡", "👏", "🤩", "💯"]


async def react_to_message(message):
    """Give a random reaction to any user message."""
    try:
        await message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass


async def _require_sub(update, context):
    """Lazy import to avoid circular dependency."""
    from bot.handlers.scan import require_subscription
    return await require_subscription(update, context)


# ─── Translated menu commands per user language ───────────────────────────────

MENU_COMMANDS = {
    "uz": [
        ("start", "🚀 Botni ishga tushirish"),
        ("help", "📖 Barcha buyruqlar"),
        ("language", "🌐 Tilni o'zgartirish"),
        ("breach", "🔐 Email/Parol tekshiruvi"),
        ("scammer", "👤 Skammer tekshiruvi"),
        ("phish", "🎣 Fishing simulyatori"),
        ("referral", "👥 Do'stlarni taklif qilish"),
        ("top", "🏆 Liderlar jadvali"),
        ("tips", "💡 Kunlik maslahatlar"),
        ("premium", "⭐ Premium xarid"),
        ("history", "🕒 Tekshiruvlar tarixi"),
        ("feedback", "📩 Taklif/shikoyat"),
        ("report", "🚨 Xavfli link xabar"),
    ],
    "ru": [
        ("start", "🚀 Запустить бота"),
        ("help", "📖 Все команды"),
        ("language", "🌐 Сменить язык"),
        ("breach", "🔐 Проверка email/пароля"),
        ("scammer", "👤 Проверка скаммера"),
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
        ("scammer", "👤 Scammer check"),
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


async def _set_user_menu_commands(context, user_id: int, lang: str):
    """Set translated menu commands for a specific user."""
    from telegram import BotCommand, BotCommandScopeChat
    commands_list = MENU_COMMANDS.get(lang, MENU_COMMANDS["en"])
    try:
        await context.bot.set_my_commands(
            commands=[BotCommand(cmd, desc) for cmd, desc in commands_list],
            scope=BotCommandScopeChat(chat_id=user_id),
        )
    except Exception:
        pass


# ─── /start (short welcome) ──────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    # Register user in database for accurate stats
    ensure_user_exists(user.id)

    await react_to_message(update.message)

    # Handle start arguments (Referral / Phish)
    if context.args:
        args_text = context.args[0]

        if args_text.startswith("phish_"):
            try:
                creator_id = int(args_text.split("_")[1])
            except (IndexError, ValueError):
                pass
            else:
                if creator_id == user.id:
                    await update.message.reply_text(t(lang, "phish_self_click"))
                    return

                await update.message.reply_text(
                    t(lang, "phish_victim_warning"), parse_mode="Markdown"
                )
                try:
                    creator_lang = get_user_lang(creator_id)
                    await context.bot.send_message(
                        chat_id=creator_id,
                        text=t(creator_lang, "phish_alert", name=user.first_name),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                return

        elif args_text.startswith("ref_") or args_text.isdigit():
            try:
                referrer_id = int(args_text.replace("ref_", ""))
                if referrer_id != user.id:
                    success = add_referral(user.id, referrer_id)
                    if success:
                        try:
                            referrer_lang = get_user_lang(referrer_id)
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=t(referrer_lang, "referral_success_notify"),
                            )
                        except Exception:
                            pass
            except (ValueError, Exception):
                pass

    welcome_text = t(lang, "start", name=user.full_name, limit=DAILY_FREE_LIMIT)
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ],
        [InlineKeyboardButton(t(lang, "add_to_group_btn"), url=f"https://t.me/{context.bot.username}?startgroup=true")],
    ]
    await update.message.reply_text(
        welcome_text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Ask new users to subscribe to the required channel (private chat only)
    if update.effective_chat.type == "private":
        from bot.handlers.scan import is_user_subscribed
        if not await is_user_subscribed(context.application, user.id):
            sub_keyboard = [
                [InlineKeyboardButton(t(lang, "sub_button"), url=CHANNEL_INVITE_LINK)],
                [InlineKeyboardButton(t(lang, "sub_check_btn"), callback_data="check_subscription")],
            ]
            await update.message.reply_text(
                text=t(lang, "sub_required"),
                reply_markup=InlineKeyboardMarkup(sub_keyboard),
                parse_mode="Markdown",
            )


# ─── /help (detailed command list) ───────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    user = update.effective_user
    lang = get_user_lang(user.id)

    help_text = t(lang, "help_message")
    await update.message.reply_text(help_text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── /language ────────────────────────────────────────────────────────────────

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    is_group = update.effective_chat.type in ["group", "supergroup"]
    if is_group:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text(t(get_user_lang(update.effective_user.id), "group_admin_only"))
            return
        prefix = "glang_"
    else:
        prefix = "lang_"

    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data=f"{prefix}uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data=f"{prefix}ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data=f"{prefix}en"),
        ]
    ]
    await update.message.reply_text(
        text=t(get_user_lang(update.effective_user.id), "choose_language") if not is_group else "🌐 Guruh tilini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    set_user_lang(query.from_user.id, lang)

    # Delete old message and send fresh start in new language
    try:
        await query.message.delete()
    except TelegramError:
        pass

    user = query.from_user
    welcome_text = t(lang, "start", name=user.full_name, limit=DAILY_FREE_LIMIT)
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ],
        [InlineKeyboardButton(t(lang, "add_to_group_btn"), url=f"https://t.me/{context.bot.username}?startgroup=true")],
    ]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # Update menu commands in user's language
    await _set_user_menu_commands(context, query.from_user.id, lang)


async def group_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("glang_", "")
    set_group_lang(query.message.chat_id, lang)
    await query.edit_message_text(gt(lang, "language_set"), parse_mode="Markdown")


# ─── /history ─────────────────────────────────────────────────────────────────

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    history = get_history(user_id)

    if not history:
        await update.message.reply_text(t(lang, "history_empty"))
        return

    text = t(lang, "history_title") + "\n"
    for item in history[:10]:
        text += f"• `{item.get('url', '')[:40]}` — {item.get('status', '')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /stats ───────────────────────────────────────────────────────────────────

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if update.effective_user.id != ADMIN_ID:
        return
    from database import get_stats
    try:
        stats_data = get_stats()
        text = (
            f"📊 *Bot statistikasi:*\n"
            f"Jami: {stats_data['total_users']}\n"
            f"Premium: {stats_data['total_premium']}\n"
            f"Hisobotlar: {stats_data['total_reports']}"
        )
    except Exception:
        text = "📊 Ma'lumotlarni olishda xatolik."
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /referral ────────────────────────────────────────────────────────────────

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(
        text=t(lang, "referral_link", ref_code=user.id, count=count),
        parse_mode="Markdown", disable_web_page_preview=True,
    )


# ─── /phish ───────────────────────────────────────────────────────────────────

PHISH_TEMPLATES = [
    {"uz": "🏦 Diqqat! Kartangizdan 1,500,000 so'm yechilmoqda. Bekor qilish:", "ru": "🏦 Внимание! Списание 1,500,000 сум. Отменить:", "en": "🏦 Alert! $150 withdrawal from your card. Cancel:"},
    {"uz": "🎁 Tabriklaymiz! 5,000,000 so'm yutdingiz! Olish:", "ru": "🎁 Поздравляем! Выигрыш 5,000,000 сум! Получить:", "en": "🎁 You won $500! Claim:"},
    {"uz": "⚠️ Telegram akkauntingiz bloklanmoqda! Tasdiqlash:", "ru": "⚠️ Ваш Telegram будет заблокирован! Подтвердить:", "en": "⚠️ Your Telegram is being suspended! Verify:"},
    {"uz": "📦 Sizga jo'natma keldi! Kuzatish: UZ7839. Batafsil:", "ru": "📦 Посылка! Трек: RU7839. Подробнее:", "en": "📦 Package! Track: EN7839. Details:"},
    {"uz": "🔒 Kimdir akkauntingizga kirmoqchi! Parolni tiklash:", "ru": "🔒 Попытка входа! Сбросить пароль:", "en": "🔒 Login attempt! Reset password:"},
]


async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    bot_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"

    template = random.choice(PHISH_TEMPLATES)
    phish_text = template.get(lang, template["uz"])

    # The copyable phishing message
    copy_text = f"{phish_text}\n{bot_link}"

    # First send the explanation
    await update.message.reply_text(t(lang, "phish_intro"))

    # Then send the phishing message separately (easy to copy/forward)
    keyboard = [
        [InlineKeyboardButton(t(lang, "phish_copy_btn"), switch_inline_query=copy_text[:64])],
    ]
    await update.message.reply_text(
        copy_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
