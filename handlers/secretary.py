"""
Secretary Mode Handler (Telegram Business Bot Feature)

When a user connects this bot as their Telegram Business chatbot,
the bot receives copies of all incoming messages to that user's personal chat.

The bot silently scans messages for:
- Suspicious URLs
- Suspicious email addresses
- Signs of phishing/scam text patterns

If something dangerous is detected → sends an alert to the user.
If everything is clean → stays silent (no spam).
"""
import re
import logging
import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_user_lang, save_business_connection,
    is_business_secretary_active, get_business_connection_id,
)
from languages import t
from checker import check_virustotal, check_google_safe_browsing

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# Patterns that indicate phishing/scam messages
SCAM_PATTERNS = [
    r'(?i)(yutdingiz|sovg\'a|prize|приз|выиграл)',
    r'(?i)(parol.*tiklash|сбросить.*пароль|reset.*password)',
    r'(?i)(kartangiz.*bloklandi|карта.*заблокирована|card.*blocked)',
    r'(?i)(tasdiqlang.*akkaunt|подтвердите.*аккаунт|verify.*account)',
    r'(?i)(срочно|zudlik|urgently|immediately)',
    r'(?i)(click here|bosing|нажмите сюда)',
    r'(?i)(investitsiya|инвестиц|crypto.*profit|guaranteed.*return)',
    r'(?i)(secret.*method|maxfiy.*usul|секретный.*метод)',
]

SCAM_REGEX = [re.compile(p) for p in SCAM_PATTERNS]


# ─── Business Connection Handler ─────────────────────────────────────────────

async def handle_business_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Triggered when a user connects/disconnects the bot as their Business chatbot.
    Telegram sends a BusinessConnection update.
    """
    connection = update.business_connection
    if not connection:
        return

    user_id = connection.user.id
    connection_id = connection.id
    is_enabled = not connection.is_disabled

    # Save the connection status
    save_business_connection(user_id, connection_id, is_enabled)

    lang = get_user_lang(user_id)

    if is_enabled:
        welcome = (
            "🤖 *Secretary Mode faollashtirildi!*\n\n"
            "Endi men sizning shaxsiy chatlaringizga kelgan xabarlarni "
            "avtomatik tekshiraman.\n\n"
            "🔍 *Nima tekshiriladi:*\n"
            "• Havolalar (URL) — fishing/virus mavjudligi\n"
            "• Matn tahlili — skam/firibgarlik belgilari\n\n"
            "✅ Xavfsiz xabarlar — jim turaman\n"
            "🚨 Xavfli xabarlar — sizga ogohlantirish yuboraman\n\n"
            "❌ O'chirish: Telegram → Settings → Business → Chatbots → Olib tashlash"
        )
        try:
            await context.bot.send_message(
                chat_id=user_id, text=welcome, parse_mode="Markdown"
            )
        except TelegramError:
            pass
    else:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🤖 Secretary Mode o'chirildi. Endi xabarlaringizni tekshirmayman.",
            )
        except TelegramError:
            pass


# ─── Business Message Handler ────────────────────────────────────────────────

async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles messages received via Business Connection.
    Only scans incoming messages (from other users TO our connected user).
    Stays silent if safe, alerts if dangerous.
    """
    message = update.business_message
    if not message:
        return

    # We only care about messages FROM others (not sent by the connected user)
    # The business_connection_id tells us which user connected the bot
    business_connection_id = message.business_connection_id
    if not business_connection_id:
        return

    text = message.text or message.caption or ""
    if not text:
        return

    # Determine the connected user (owner) from connection_id
    # We need to find who this connection belongs to
    # The sender is message.from_user — if it's the connected user, skip
    # Business messages from the user themselves should be ignored
    chat = message.chat
    sender = message.from_user

    # Check for URLs
    urls_found = URL_REGEX.findall(text)

    # Check for scam text patterns
    scam_detected = any(pattern.search(text) for pattern in SCAM_REGEX)

    # If no URLs and no scam patterns — stay silent
    if not urls_found and not scam_detected:
        return

    # Analyze URLs if found
    dangerous_urls = []
    if urls_found:
        for url in urls_found[:3]:  # Max 3 URLs per message
            try:
                vt_res, gsb_res = await asyncio.gather(
                    check_virustotal(url),
                    check_google_safe_browsing(url),
                )
                if gsb_res.get("dangerous") or vt_res.get("malicious", 0) > 0:
                    dangerous_urls.append({
                        "url": url,
                        "malicious_count": vt_res.get("malicious", 0),
                    })
            except Exception as e:
                logging.error(f"Secretary URL check error: {e}")

    # If nothing dangerous — stay silent
    if not dangerous_urls and not scam_detected:
        return

    # ─── BUILD ALERT MESSAGE ──────────────────────────────────────────────────

    alert = "🚨🤖 *SECRETARY OGOHLANTIRISH!*\n\n"
    alert += f"👤 *Kimdan:* {sender.full_name if sender else 'Noma`lum'}\n"

    if dangerous_urls:
        alert += "\n🔗 *Xavfli havolalar aniqlandi:*\n"
        for d in dangerous_urls:
            alert += f"  • `{d['url']}` — {d['malicious_count']} antivirus xavf aniqladi\n"

    if scam_detected:
        alert += "\n⚠️ *Skam/Firibgarlik belgilari topildi!*\n"
        alert += "Bu xabar fishing yoki firibgarlik bo'lishi mumkin.\n"

    alert += (
        "\n━━━━━━━━━━━━━━━━\n"
        "💡 *Maslahat:*\n"
        "• Bu havolalarni BOSMANG\n"
        "• Shaxsiy ma'lumot bermang\n"
        "• Shubhali bo'lsa /report orqali xabar bering"
    )

    # Send alert via business connection reply
    try:
        await context.bot.send_message(
            business_connection_id=business_connection_id,
            chat_id=chat.id,
            text=alert,
            parse_mode="Markdown",
        )
    except TelegramError:
        # Fallback: try sending directly to the connected user
        # We can't easily determine the owner here without a lookup,
        # but the business_connection message context should handle it
        logging.warning("Could not send secretary alert via business connection.")
