"""
Group message handlers:
- handle_group_message (auto-scan URLs posted in groups)
- handle_group_apk (scan APK files in groups)
- handle_group_photo (scan QR codes in group photos)
"""
import re
import logging
import asyncio

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_group_lang, increment_group_blocked,
)
from languages import gt, at
from checker import check_virustotal, check_google_safe_browsing
from apk_checker import scan_apk
from qr_checker import extract_qr_url

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')


# ─── Group URL auto-scan ─────────────────────────────────────────────────────

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    urls = URL_REGEX.findall(message.text)
    if not urls:
        return

    lang = get_group_lang(message.chat_id)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    for url in urls:
        vt = await check_virustotal(url)
        gsb = await check_google_safe_browsing(url)

        if gsb.get("dangerous") or vt.get("malicious", 0) > 0:
            try:
                await message.delete()
                await context.bot.send_message(
                    chat_id=message.chat_id,
                    text=gt(lang, "dangerous_deleted", mention=mention, url=url, engines=vt.get("malicious", 0)),
                    parse_mode="Markdown",
                )
                increment_group_blocked(message.chat_id)
            except TelegramError:
                await message.reply_text(
                    gt(lang, "dangerous_no_permission", mention=mention, url=url),
                    parse_mode="Markdown",
                )
            break


# ─── Group APK handler ───────────────────────────────────────────────────────

async def handle_group_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scans APK files sent in groups."""
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    file_name = doc.file_name or "file.apk"
    mime_type = doc.mime_type or ""
    is_apk = (
        file_name.lower().endswith(".apk")
        or mime_type == "application/vnd.android.package-archive"
    )
    if not is_apk:
        return

    lang = get_group_lang(message.chat_id)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    if doc.file_size > 32 * 1024 * 1024:
        await message.reply_text(at(lang, "too_large"))
        return

    status_msg = await message.reply_text(at(lang, "scanning"), parse_mode="Markdown")

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await scan_apk(bytes(file_bytes), file_name)
    except Exception:
        await status_msg.edit_text("❌ APK tekshirishda xatolik.")
        return

    if not result.get("success"):
        if result.get("timeout"):
            await status_msg.edit_text(at(lang, "timeout"))
        else:
            await status_msg.edit_text(at(lang, "error"))
        return

    mal = result["malicious"]
    sus = result["suspicious"]
    total = result["total"]

    if mal > 0:
        try:
            await message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=(
                f"🚨 *XAVFLI APK BLOKLANDI!*\n\n"
                f"👤 {mention}\n"
                f"📱 Fayl: `{file_name}`\n"
                f"{mal}/{total} antivirus xavfli deb topdi!\n"
                f"❌ Bu ilovani O'RNATMANG!"
            ),
            parse_mode="Markdown",
        )
    elif sus > 0:
        await status_msg.edit_text(
            at(lang, "suspicious", sus=sus, total=total, name=file_name),
            parse_mode="Markdown",
        )
    else:
        await status_msg.edit_text(
            at(lang, "safe", total=total, name=file_name),
            parse_mode="Markdown",
        )


# ─── Group QR/Photo handler ──────────────────────────────────────────────────

async def handle_group_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scans QR codes sent as photos in groups."""
    message = update.message
    if not message or not message.photo:
        return

    lang = get_group_lang(message.chat_id)
    photo = message.photo[-1]

    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        url = extract_qr_url(bytes(photo_bytes))
    except Exception:
        return

    if not url:
        return  # Not a QR code, ignore silently

    status_msg = await message.reply_text(
        "📸 QR kod aniqlandi, tekshirilmoqda...",
        parse_mode="Markdown",
    )

    try:
        vt_res, gsb_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
        )
        is_dangerous = gsb_res.get("dangerous") or vt_res.get("malicious", 0) > 0
        mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

        if is_dangerous:
            try:
                await message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=(
                    f"🚨 *XAVFLI QR KOD BLOKLANDI!*\n\n"
                    f"👤 {mention}\n"
                    f"🔗 URL: `{url}`\n"
                    f"Bu QR kodga ishonmang!"
                ),
                parse_mode="Markdown",
            )
        else:
            await status_msg.edit_text(
                f"📸 QR kod URL: `{url}`\n\n✅ Xavfsiz ko'rinadi.",
                parse_mode="Markdown",
            )
    except Exception:
        await status_msg.edit_text("❌ QR kod tekshirishda xatolik.")
