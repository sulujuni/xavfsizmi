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

REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡"]


# ─── /start ──────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    try:
        await update.message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass

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
                    "*SafeLink Bot* xavfsizlik testi edi. "
                    "Lekin real hayotda bu haqiqiy skamer bo'lishi va barcha "
                    "parollaringizni o'g'irlashi mumkin edi!\n\n"
                    "🛡 Internetda doim hushyor bo'ling va shubhali havolalarni "
                    "doim bizning bot orqali tekshiring."
                )
                await update.message.reply_text(warning_text, parse_mode="Markdown")

                try:
                    creator_lang = get_user_lang(creator_id)
                    await context.bot.send_message(
                        chat_id=creator_id,
                        text=t(creator_lang, "phish_alert"),
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
    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(
        text=t(lang, "referral_link", ref_code=user.id, count=count),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── /phish ───────────────────────────────────────────────────────────────────

async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    test_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"
    await update.message.reply_text(
        text=t(lang, "phish_created", link=test_link),
        parse_mode="Markdown",
    )
