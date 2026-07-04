"""
Group message handlers:
- handle_group_message (auto-scan URLs posted in groups)
- handle_group_apk (scan APK files in groups)
- handle_group_photo (scan QR codes in group photos)

Free tier groups: 20 checks/day. Premium groups: unlimited.
"""
import re
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_group_lang, increment_group_blocked,
    is_group_limit_reached, increment_group_checks,
)
from languages import gt, at
from checker import check_virustotal, check_google_safe_browsing
from apk_checker import scan_apk
from qr_checker import extract_qr_url

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')


# ─── Helper: check group limit ───────────────────────────────────────────────

def _check_group_limit(chat_id: int) -> bool:
    """
    Returns True if the group can proceed.
    Returns False if the daily limit is reached.
    Increments counter if allowed.
    """
    if is_group_limit_reached(chat_id):
        return False
    increment_group_checks(chat_id)
    return True


# ─── Group URL auto-scan ─────────────────────────────────────────────────────

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    urls = URL_REGEX.findall(message.text)
    if not urls:
        return

    chat_id = message.chat_id
    lang = get_group_lang(chat_id)

    # Check group daily limit
    if not _check_group_limit(chat_id):
        # Silently skip if limit reached (don't spam the group)
        return

    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    for url in urls:
        vt = await check_virustotal(url)
        gsb = await check_google_safe_browsing(url)

        if gsb.get("dangerous") or vt.get("malicious", 0) > 0:
            # Always alert on dangerous links (even if limit reached)
            await message.reply_text(
                gt(lang, "dangerous_no_permission", mention=mention, url=url),
                parse_mode="Markdown",
            )
            increment_group_blocked(chat_id)
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

    chat_id = message.chat_id
    lang = get_group_lang(chat_id)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    # Check group daily limit
    if not _check_group_limit(chat_id):
        return

    if doc.file_size > 32 * 1024 * 1024:
        await message.reply_text(at(lang, "too_large"))
        return

    status_msg = await message.reply_text(at(lang, "scanning"), parse_mode="Markdown")

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await scan_apk(bytes(file_bytes), file_name)
    except Exception:
        await status_msg.edit_text(at(lang, "error"))
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
        await context.bot.send_message(
            chat_id=chat_id,
            text=gt(lang, "group_apk_dangerous", mention=mention, name=file_name, mal=mal, total=total),
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

    chat_id = message.chat_id
    lang = get_group_lang(chat_id)

    # Check group daily limit
    if not _check_group_limit(chat_id):
        return

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
        gt(lang, "checking"),
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
            await context.bot.send_message(
                chat_id=chat_id,
                text=gt(lang, "group_qr_dangerous", mention=mention, url=url),
                parse_mode="Markdown",
            )
        else:
            await status_msg.edit_text(
                f"📸 QR: `{url}`\n\n✅ {gt(lang, 'clean')}",
                parse_mode="Markdown",
            )
    except Exception:
        await status_msg.edit_text(at(lang, "error"))
