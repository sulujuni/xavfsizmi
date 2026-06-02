"""
Command handlers for basic bot commands:
/start, /language, /history, /feedback, /report, /stats, /referral, /phish
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

from config import ADMIN_ID, DAILY_FREE_LIMIT, CHANNEL_INVITE_LINK
from database import (
    get_user_lang, set_user_lang, get_group_lang, set_group_lang,
    get_history, add_referral, get_referral_count, add_report,
)
from languages import t, gt
from admin import is_admin

REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡", "👏", "🤩", "💯"]


async def react_to_message(message):
    """Give a random reaction to any user message."""
    try:
        await message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass


# ─── /start ──────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    await react_to_message(update.message)

    # Start arguments (Referral or Phishing test)
    if context.args:
        args_text = context.args[0]

        # Phishing simulation click
        if args_text.startswith("phish_"):
            try:
                creator_id = int(args_text.split("_")[1])
            except (IndexError, ValueError):
                pass
            else:
                if creator_id == user.id:
                    await update.message.reply_text(
                        "🎣 Bu sizning shaxsiy fishing testingiz. Uni do'stlaringizga yuboring!"
                    )
                    return

                warning_text = (
                    "🚨 *DIQQAT! Siz fishing tuzog'iga tushdingiz!*\n\n"
                    "Xavotir olmang, bu shunchaki do'stingiz tomonidan yuborilgan "
                    "*Xavfsizmi? Bot* xavfsizlik testi edi. "
                    "Lekin real hayotda bu haqiqiy skamer bo'lishi va barcha "
                    "parollaringizni o'g'irlashi mumkin edi!\n\n"
                    "🛡 *Qanday himoyalanish kerak:*\n"
                    "• Notanish havolalarni hech qachon bosmang\n"
                    "• Shubhali linkni avval @XavfsizmiBot orqali tekshiring\n"
                    "• 2-bosqichli autentifikatsiyani yoqing\n"
                    "• Parollarni har 3 oyda yangilang\n\n"
                    "💡 Siz ham do'stlaringizni sinab ko'ring: /phish"
                )
                await update.message.reply_text(warning_text, parse_mode="Markdown")

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

        # Referral link
        elif args_text.startswith("ref_") or args_text.isdigit():
            try:
                referrer_id = int(args_text.replace("ref_", ""))
                if referrer_id != user.id:
                    success = add_referral(user.id, referrer_id)
                    if success:
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text="🎉 Yangi do'st taklif qildingiz! "
                                     "Sizga 1 ta bepul /breach tekshiruv balansi qo'shildi."
                            )
                        except Exception:
                            pass
            except (ValueError, Exception):
                pass

    welcome_text = t(lang, "start", name=user.full_name, limit=DAILY_FREE_LIMIT)
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


# ─── /language ────────────────────────────────────────────────────────────────

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    is_group = update.effective_chat.type in ["group", "supergroup"]
    if is_group:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❗ Faqat guruh adminlari tilni o'zgartira oladi.")
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
    text = (
        t(get_user_lang(update.effective_user.id), "choose_language")
        if not is_group
        else "🌐 Guruh tilini tanlang / Выберите язык группы:"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    set_user_lang(query.from_user.id, lang)
    await query.edit_message_text(t(lang, "language_set"), parse_mode="Markdown")


async def group_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("glang_", "")
    set_group_lang(query.message.chat_id, lang)
    await query.edit_message_text(gt(lang, "language_set"), parse_mode="Markdown")


# ─── /history ─────────────────────────────────────────────────────────────────

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    history = get_history(user_id)

    if not history:
        await update.message.reply_text("🕒 Tekshiruvlar tarixingiz hozircha bo'sh.")
        return

    text = "🕒 *Sizning oxirgi 10 ta tekshiruv tarixingiz:*\n\n"
    for item in history[:10]:
        text += f"• `{item.get('url', '')}` ➔ {item.get('status', '')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /feedback ────────────────────────────────────────────────────────────────

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "feedback_usage"), parse_mode="Markdown")
        return

    feedback_text = " ".join(context.args).strip()
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 *Yangi taklif/shikoyat:*\n"
                 f"Kimdan: {user.full_name} (`{user.id}`)\n"
                 f"Matn: {feedback_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(t(lang, "feedback_received"))
    except Exception:
        await update.message.reply_text("❌ Xabarni adminlarga yuborib bo'lmadi.")


# ─── /report ──────────────────────────────────────────────────────────────────

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "report_usage"), parse_mode="Markdown")
        return

    url_to_report = context.args[0].strip()
    try:
        add_report(user.id, url_to_report)
    except Exception:
        pass
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 *Xavfli havola haqida xabar:*\nUser: {user.id}\nLink: {url_to_report}",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await update.message.reply_text(t(lang, "report_sent"))


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
            f"Jami foydalanuvchilar: {stats_data['total_users']}\n"
            f"Premium: {stats_data['total_premium']}\n"
            f"Hisobotlar: {stats_data['total_reports']}"
        )
    except Exception:
        text = "📊 *Bot statistikasi:* Ma'lumotlarni olishda xatolik."
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /referral ────────────────────────────────────────────────────────────────

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(
        text=t(lang, "referral_link", ref_code=user.id, count=count),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── /phish (UPGRADED — realistic phishing simulation) ───────────────────────

PHISH_TEMPLATES = [
    {
        "type": "bank",
        "uz": "🏦 *Diqqat!* Sizning kartangizdan 1,500,000 so'm yechilmoqda. Bekor qilish uchun bosing: {link}",
        "ru": "🏦 *Внимание!* С вашей карты списывается 1,500,000 сум. Для отмены нажмите: {link}",
        "en": "🏦 *Alert!* $150 is being withdrawn from your card. Cancel here: {link}",
    },
    {
        "type": "prize",
        "uz": "🎁 *Tabriklaymiz!* Siz 5,000,000 so'm yutdingiz! Sovg'angizni olish uchun: {link}",
        "ru": "🎁 *Поздравляем!* Вы выиграли 5,000,000 сум! Получить приз: {link}",
        "en": "🎁 *Congratulations!* You won $500! Claim your prize: {link}",
    },
    {
        "type": "account",
        "uz": "⚠️ Sizning Telegram akkauntingiz bloklanmoqda! Tasdiqlash: {link}",
        "ru": "⚠️ Ваш аккаунт Telegram будет заблокирован! Подтвердите: {link}",
        "en": "⚠️ Your Telegram account is being suspended! Verify now: {link}",
    },
    {
        "type": "delivery",
        "uz": "📦 Sizga jo'natma keldi! Kuzatish raqami: #UZ7839. Ma'lumot: {link}",
        "ru": "📦 У вас посылка! Номер отслеживания: #RU7839. Подробнее: {link}",
        "en": "📦 You have a package! Tracking: #EN7839. Details: {link}",
    },
    {
        "type": "password",
        "uz": "🔒 Kimdir akkauntingizga kirmoqchi! Parolni tiklash: {link}",
        "ru": "🔒 Кто-то пытается войти в ваш аккаунт! Сбросить пароль: {link}",
        "en": "🔒 Someone is trying to access your account! Reset password: {link}",
    },
]


async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Upgraded /phish — generates a realistic-looking phishing message template
    that the user can forward to friends to test their awareness.
    """
    await react_to_message(update.message)

    user = update.effective_user
    lang = get_user_lang(user.id)
    bot_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"

    # Pick a random phishing template
    template = random.choice(PHISH_TEMPLATES)
    phish_message = template.get(lang, template["uz"]).format(link=bot_link)

    response = (
        "🎣 *Fishing Simulyatsiya Yaratildi!*\n\n"
        "Quyidagi xabarni do'stingizga yuboring (nusxa oling):\n\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{phish_message}\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "📋 Yuqoridagi matnni nusxalab, do'stingizga yuboring.\n"
        "Agar u havolani bossa — ogohlantirish oladi, siz esa xabar.\n\n"
        "🔄 Boshqa shablon olish uchun yana /phish bosing."
    )

    await update.message.reply_text(
        response, parse_mode="Markdown", disable_web_page_preview=True
    )
