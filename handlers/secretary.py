"""
Secretary Mode Handler (Telegram Business Bot Feature)

When a user connects this bot as their Telegram Business chatbot,
the bot receives copies of all incoming messages to that user's personal chat.

Scans:
- URLs → checks with VirusTotal + Google Safe Browsing
- APK files → scans with VirusTotal (shows progress)
- QR code photos → extracts and checks URL
- Text patterns → detects scam/phishing language

Behavior:
- Dangerous → sends alert
- APK files → always shows scanning status + result
- Clean text → stays silent
"""
import re
import logging
import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_user_lang, save_business_connection,
)
from languages import t
from checker import check_virustotal, check_google_safe_browsing
from apk_checker import scan_apk
from qr_checker import extract_qr_url

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')

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
    """
    connection = update.business_connection
    if not connection:
        return

    user_id = connection.user.id
    connection_id = connection.id
    is_enabled = connection.is_enabled

    save_business_connection(user_id, connection_id, is_enabled)
    lang = get_user_lang(user_id)

    if is_enabled:
        await _send_to_user(context, user_id, t(lang, "secretary_enabled"))
    else:
        await _send_to_user(context, user_id, t(lang, "secretary_disabled"))


# ─── Business Message Handler ────────────────────────────────────────────────

async def handle_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles messages received via Business Connection.
    Scans URLs, APK files, QR photos, and scam text patterns.
    """
    # TypeHandler receives ALL updates — only process business messages
    if not hasattr(update, 'business_message') or not update.business_message:
        return

    message = update.business_message
    business_connection_id = message.business_connection_id
    if not business_connection_id:
        return

    chat = message.chat
    sender = message.from_user
    sender_name = sender.full_name if sender else "?"

    # ── Check for APK files ───────────────────────────────────────────────────
    if message.document:
        doc = message.document
        file_name = doc.file_name or ""
        mime_type = doc.mime_type or ""
        is_apk = (
            file_name.lower().endswith(".apk")
            or mime_type == "application/vnd.android.package-archive"
        )
        if is_apk:
            await _handle_secretary_apk(context, message, business_connection_id, chat, sender_name, doc)
            return

    # ── Check for QR code photos ──────────────────────────────────────────────
    if message.photo:
        await _handle_secretary_photo(context, message, business_connection_id, chat, sender_name)
        return

    # ── Check text messages ───────────────────────────────────────────────────
    text = message.text or message.caption or ""
    if not text:
        return

    # Check for URLs
    urls_found = URL_REGEX.findall(text)

    # Check for scam text patterns
    scam_detected = any(pattern.search(text) for pattern in SCAM_REGEX)

    # If no URLs and no scam patterns — stay silent
    if not urls_found and not scam_detected:
        return

    # Analyze URLs
    dangerous_urls = []
    if urls_found:
        for url in urls_found[:3]:
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

    # Build alert
    alert = f"🚨🤖 *SECRETARY OGOHLANTIRISH!*\n\n"
    alert += f"👤 *Kimdan:* {sender_name}\n"

    if dangerous_urls:
        alert += "\n🔗 *Xavfli havolalar:*\n"
        for d in dangerous_urls:
            alert += f"  • `{d['url']}` — {d['malicious_count']} antivirus xavf aniqladi\n"

    if scam_detected:
        alert += "\n⚠️ *Skam/Firibgarlik belgilari topildi!*\n"

    alert += "\n💡 Bu havolalarni BOSMANG va shaxsiy ma'lumot bermang."

    await _send_via_business(context, business_connection_id, chat.id, alert)


# ─── Secretary APK Handler ────────────────────────────────────────────────────

async def _handle_secretary_apk(context, message, business_connection_id, chat, sender_name, doc):
    """Scan APK files received in secretary mode. Always shows status."""
    file_name = doc.file_name or "file.apk"

    # Send "scanning" status so user sees the bot is working
    status_text = f"🤖🔍 *Secretary:* `{file_name}` tekshirilmoqda..."
    await _send_via_business(context, business_connection_id, chat.id, status_text)

    if doc.file_size > 32 * 1024 * 1024:
        await _send_via_business(
            context, business_connection_id, chat.id,
            f"🤖❌ *Secretary:* `{file_name}` — hajmi juda katta (max 32 MB)"
        )
        return

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await scan_apk(bytes(file_bytes), file_name)

        if result.get("success"):
            mal = result.get("malicious", 0)
            sus = result.get("suspicious", 0)
            total = result.get("total", 0)

            if mal > 0:
                alert = (
                    f"🤖🚨 *SECRETARY: ZARARLI APK!*\n\n"
                    f"👤 *Kimdan:* {sender_name}\n"
                    f"📱 *Fayl:* `{file_name}`\n"
                    f"🔴 *Natija:* {mal}/{total} antivirus xavf aniqladi!\n\n"
                    f"⚠️ Bu faylni OCHMANG va O'RNATMANG!"
                )
            elif sus > 0:
                alert = (
                    f"🤖⚠️ *SECRETARY: Shubhali APK*\n\n"
                    f"👤 *Kimdan:* {sender_name}\n"
                    f"📱 *Fayl:* `{file_name}`\n"
                    f"🟡 *Natija:* {sus}/{total} shubhali\n\n"
                    f"⚠️ Ehtiyot bo'ling!"
                )
            else:
                alert = (
                    f"🤖✅ *SECRETARY: APK xavfsiz*\n\n"
                    f"👤 *Kimdan:* {sender_name}\n"
                    f"📱 *Fayl:* `{file_name}`\n"
                    f"🟢 *Natija:* {total} dvigatel tekshirdi — xavf topilmadi"
                )
        else:
            alert = f"🤖❌ *Secretary:* `{file_name}` — tekshirib bo'lmadi (API xatolik)"

        await _send_via_business(context, business_connection_id, chat.id, alert)
    except Exception as e:
        logging.error(f"Secretary APK error: {e}")
        await _send_via_business(
            context, business_connection_id, chat.id,
            f"🤖❌ *Secretary:* `{file_name}` — tekshirishda xatolik"
        )


# ─── Secretary Photo/QR Handler ──────────────────────────────────────────────

async def _handle_secretary_photo(context, message, business_connection_id, chat, sender_name):
    """Scan QR codes in photos received in secretary mode."""
    photo = message.photo[-1] if message.photo else None
    if not photo:
        return

    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        url = extract_qr_url(bytes(photo_bytes))
    except Exception:
        return

    if not url:
        return  # Not a QR code, stay silent

    # QR found — check the URL
    try:
        vt_res, gsb_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
        )
        is_dangerous = gsb_res.get("dangerous") or vt_res.get("malicious", 0) > 0

        if is_dangerous:
            alert = (
                f"🤖🚨 *SECRETARY: Xavfli QR kod!*\n\n"
                f"👤 *Kimdan:* {sender_name}\n"
                f"🔗 *URL:* `{url}`\n"
                f"🔴 *Natija:* Xavfli havola aniqlandi!\n\n"
                f"⚠️ Bu QR kodga ISHONMANG!"
            )
            await _send_via_business(context, business_connection_id, chat.id, alert)
        # If safe — stay silent (don't spam for every photo)
    except Exception as e:
        logging.error(f"Secretary QR error: {e}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _send_via_business(context, business_connection_id: str, chat_id: int, text: str):
    """Send a message via business connection."""
    try:
        await context.bot.send_message(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
        )
    except TelegramError as e:
        logging.warning(f"Secretary send failed: {e}")


async def _send_to_user(context, user_id: int, text: str):
    """Send a direct message to the connected user."""
    try:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
    except TelegramError:
        pass
