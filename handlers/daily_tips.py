"""
Daily Security Tips system powered by Groq AI (free llama3).
- Generates fresh cybersecurity tips daily using AI.
- Falls back to pre-written tips if API fails.
- Users toggle with /tips on or /tips off.
"""
from telegram import Update
from telegram.ext import ContextTypes, Application
from telegram.error import TelegramError
import random
import logging
import aiohttp

from config import GROQ_API_KEY
from database import get_user_lang, load_db, save_db
from languages import t
from handlers.private_messages import require_subscription, react_to_message


# ─── FALLBACK TIPS (used if AI API fails) ─────────────────────────────────────

FALLBACK_TIPS = [
    {
        "uz": "🔐 Parollaringizni har 90 kunda yangilang va har bir sayt uchun alohida parol ishlating.",
        "ru": "🔐 Меняйте пароли каждые 90 дней и используйте уникальный пароль для каждого сайта.",
        "en": "🔐 Change your passwords every 90 days and use a unique password for each site.",
    },
    {
        "uz": "📱 Ilovalani faqat rasmiy do'konlardan (Google Play, App Store) yuklab oling.",
        "ru": "📱 Скачивайте приложения только из официальных магазинов (Google Play, App Store).",
        "en": "📱 Only download apps from official stores (Google Play, App Store).",
    },
    {
        "uz": "🔗 Qisqa havolalarga (bit.ly, tinyurl) ishonmang — avval /expand orqali tekshiring.",
        "ru": "🔗 Не доверяйте коротким ссылкам (bit.ly, tinyurl) — проверьте через /expand.",
        "en": "🔗 Don't trust short links (bit.ly, tinyurl) — check them first with /expand.",
    },
    {
        "uz": "🛡 Ikki bosqichli autentifikatsiyani (2FA) barcha akkauntlaringizda yoqing.",
        "ru": "🛡 Включите двухфакторную аутентификацию (2FA) на всех аккаунтах.",
        "en": "🛡 Enable two-factor authentication (2FA) on all your accounts.",
    },
    {
        "uz": "📧 Notanish emaillardan kelgan fayllarni HECH QACHON ochmang.",
        "ru": "📧 НИКОГДА не открывайте файлы из писем незнакомых отправителей.",
        "en": "📧 NEVER open files from emails sent by unknown senders.",
    },
    {
        "uz": "🏦 Bankingiz HECH QACHON parol yoki PIN kod so'ramaydi. Bu 100% fishing!",
        "ru": "🏦 Ваш банк НИКОГДА не просит пароль или ПИН-код. Это 100% фишинг!",
        "en": "🏦 Your bank NEVER asks for passwords or PINs. It's 100% phishing!",
    },
    {
        "uz": "📶 Ochiq Wi-Fi tarmoqlarida (kafe, metro) bank ilovalaringizni ISHLATMANG.",
        "ru": "📶 НЕ используйте банковские приложения в открытых Wi-Fi сетях (кафе, метро).",
        "en": "📶 DON'T use banking apps on public Wi-Fi networks (cafes, metro).",
    },
    {
        "uz": "🔍 Saytga parol kiritishdan oldin URL manzilini diqqat bilan tekshiring — https borligini aniqlang.",
        "ru": "🔍 Перед вводом пароля внимательно проверьте URL — убедитесь что есть https.",
        "en": "🔍 Before entering passwords, check the URL carefully — make sure it has https.",
    },
    {
        "uz": "💾 Muhim fayllaringizni kamida 2 ta joyda saqlang (bulut + tashqi disk).",
        "ru": "💾 Храните важные файлы минимум в 2 местах (облако + внешний диск).",
        "en": "💾 Keep important files in at least 2 places (cloud + external drive).",
    },
    {
        "uz": "🚫 'Siz yutdingiz!' xabarlariga ISHONMANG. Hech kim bepulga pul bermaydi.",
        "ru": "🚫 НЕ верьте сообщениям 'Вы выиграли!' Никто не дарит деньги просто так.",
        "en": "🚫 DON'T believe 'You won!' messages. Nobody gives away money for free.",
    },
    {
        "uz": "🔄 Telefon va kompyuteringiz dasturlarini doim yangilab turing — xavfsizlik tuzatishlari muhim!",
        "ru": "🔄 Всегда обновляйте программы на телефоне и компьютере — патчи безопасности важны!",
        "en": "🔄 Always update your phone and computer software — security patches matter!",
    },
    {
        "uz": "👁 Ijtimoiy tarmoqlarda juda ko'p shaxsiy ma'lumot qoldirmang — firibgarlar foydalanadi.",
        "ru": "👁 Не оставляйте слишком много личной информации в соцсетях — мошенники используют её.",
        "en": "👁 Don't share too much personal info on social media — scammers use it.",
    },
    {
        "uz": "📲 QR-kodni skanerlaganingizda avtomatik ochilgan saytga shaxsiy ma'lumot BERMANG.",
        "ru": "📲 Не вводите личные данные на сайтах, открывшихся после сканирования QR-кода.",
        "en": "📲 Don't enter personal info on sites opened after scanning a QR code.",
    },
    {
        "uz": "🔑 Parol menejeri ishlating (Bitwarden — bepul va xavfsiz). Bitta parolni eslab qolasiz.",
        "ru": "🔑 Используйте менеджер паролей (Bitwarden — бесплатный и безопасный). Запомните один пароль.",
        "en": "🔑 Use a password manager (Bitwarden — free and secure). Remember just one password.",
    },
    {
        "uz": "⚠️ Telegram'da 'Admin' yoki 'Support' yozgan odamga parolingizni BERMANG — bu firibgar.",
        "ru": "⚠️ НЕ давайте пароль людям с ником 'Admin' или 'Support' в Telegram — это мошенники.",
        "en": "⚠️ NEVER give your password to people named 'Admin' or 'Support' in Telegram — they're scammers.",
    },
]


# ─── GROQ AI TIP GENERATOR ───────────────────────────────────────────────────

async def generate_ai_tip(lang: str = "uz") -> str:
    """
    Generates a fresh cybersecurity tip using Groq AI (free llama3).
    Returns the tip text or empty string if fails.
    """
    if not GROQ_API_KEY:
        return ""

    lang_map = {
        "uz": "O'zbek tilida",
        "ru": "на русском языке",
        "en": "in English",
    }
    lang_instruction = lang_map.get(lang, "in English")

    prompt = (
        f"Generate ONE short, practical cybersecurity tip or lifehack for regular internet users "
        f"{lang_instruction}. It should be:\n"
        f"- Maximum 2-3 sentences\n"
        f"- Actionable and specific (not generic)\n"
        f"- Include a relevant emoji at the start\n"
        f"- About a DIFFERENT topic each time (phishing, passwords, malware, privacy, "
        f"social engineering, Wi-Fi security, mobile security, data backups, etc.)\n"
        f"- Written in a friendly, informative tone\n\n"
        f"Just output the tip itself, nothing else. No quotation marks."
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "You are a cybersecurity expert giving daily tips to regular users."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 200,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tip = data["choices"][0]["message"]["content"].strip()
                    # Clean up any quotes the model might add
                    tip = tip.strip('"').strip("'")
                    return tip
                else:
                    logging.warning(f"Groq API returned status {resp.status}")
                    return ""
    except Exception as e:
        logging.error(f"Groq AI tip generation error: {e}")
        return ""


# ─── Tips toggle (database helpers) ──────────────────────────────────────────

def get_tips_enabled(user_id: int) -> bool:
    """Check if user has tips enabled (default: True)."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return True
    return db[user_key].get("tips_enabled", True)


def set_tips_enabled(user_id: int, enabled: bool):
    """Toggle tips on/off for a user."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"lang": "uz", "checks": 0}
    db[user_key]["tips_enabled"] = enabled
    save_db(db)


def get_all_tips_subscribers() -> list:
    """Returns list of user IDs who have tips enabled."""
    db = load_db()
    subscribers = []
    for key in db.keys():
        if key.isdigit():
            if db[key].get("tips_enabled", True):
                subscribers.append(int(key))
    return subscribers


# ─── /tips command ────────────────────────────────────────────────────────────

async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle daily tips on/off. Usage: /tips on or /tips off"""
    user = update.effective_user
    lang = get_user_lang(user.id)

    await react_to_message(update.message)

    if not await require_subscription(update, context):
        return

    if context.args and context.args[0].lower() in ("off", "0", "no", "yoq"):
        set_tips_enabled(user.id, False)
        await update.message.reply_text(t(lang, "tips_disabled"))
    elif context.args and context.args[0].lower() in ("on", "1", "yes", "ha"):
        set_tips_enabled(user.id, True)
        await update.message.reply_text(t(lang, "tips_enabled"))
    else:
        # Show current status and generate a tip
        enabled = get_tips_enabled(user.id)
        status = "✅" if enabled else "❌"

        # Try AI tip first, fallback to pre-written
        status_msg = await update.message.reply_text(t(lang, "ai_generating"))
        ai_tip = await generate_ai_tip(lang)

        if ai_tip:
            tip_text = ai_tip
            source = "🤖 AI"
        else:
            tip = random.choice(FALLBACK_TIPS)
            tip_text = tip.get(lang, tip["uz"])
            source = "📝"

        await status_msg.edit_text(
            f"{t(lang, 'tips_header', status=status)}\n\n"
            f"{source} *Bugungi maslahat:*\n{tip_text}\n\n"
            f"O'chirish: `/tips off`\nYoqish: `/tips on`",
            parse_mode="Markdown",
        )


# ─── Daily tips sender (called by scheduler) ─────────────────────────────────

async def send_daily_tips(application: Application):
    """
    Sends an AI-generated tip to all subscribed users.
    Generates one tip per language, then broadcasts.
    Called daily by APScheduler.
    """
    subscribers = get_all_tips_subscribers()
    if not subscribers:
        return

    # Generate tips for each language using AI
    tips_by_lang = {}
    for lang in ["uz", "ru", "en"]:
        ai_tip = await generate_ai_tip(lang)
        if ai_tip:
            tips_by_lang[lang] = ai_tip
        else:
            # Fallback to pre-written
            fallback = random.choice(FALLBACK_TIPS)
            tips_by_lang[lang] = fallback.get(lang, fallback["uz"])

    sent = 0
    failed = 0

    for user_id in subscribers:
        lang = get_user_lang(user_id)
        tip_text = tips_by_lang.get(lang, tips_by_lang.get("uz", ""))
        message = f"{t(lang, 'tip_of_day')}\n\n{tip_text}"

        try:
            await application.bot.send_message(
                chat_id=user_id, text=message, parse_mode="Markdown"
            )
            sent += 1
        except TelegramError:
            failed += 1

        # Rate limit: don't spam Telegram API
        if (sent + failed) % 25 == 0:
            import asyncio
            await asyncio.sleep(1)

    logging.info(f"Daily AI tips sent: {sent} success, {failed} failed")
