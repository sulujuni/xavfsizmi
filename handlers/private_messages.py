"""
Private message handlers:
- handle_private_message (URL scanning)
- handle_apk (APK file scanning)
- handle_photo (QR code scanning)

All checks (URL, APK, QR) share the same daily limit for non-premium users.
Bot reacts to every message with a random emoji.
"""
import re
import logging
import asyncio
import random

from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, Application
from telegram.error import TelegramError
from telegram.constants import ChatMemberStatus

from config import REQUIRED_CHANNEL_ID, CHANNEL_INVITE_LINK, DAILY_FREE_LIMIT
from database import (
    get_user_lang, is_premium, get_user_checks, increment_user_checks,
    add_to_history, is_rate_limited, update_rate_limit,
)
from languages import t
from checker import (
    check_virustotal, check_google_safe_browsing,
    check_alienvault, check_urlscan, check_url_with_domain_age,
)
from apk_checker import scan_apk
from qr_checker import extract_qr_url

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡", "👏", "🤩", "💯"]


# ─── Helper: react to every message ──────────────────────────────────────────

async def react_to_message(message):
    """Give a random reaction to any user message."""
    try:
        await message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass


# ─── Helper: check daily limit (shared for URL, APK, QR) ─────────────────────

def check_and_consume_limit(user_id: int) -> bool:
    """
    Returns True if the user can proceed (premium or under limit).
    Returns False if limit is reached.
    Automatically increments the counter if allowed.
    """
    if is_premium(user_id):
        return True
    checks = get_user_checks(user_id)
    if checks >= DAILY_FREE_LIMIT:
        return False
    increment_user_checks(user_id)
    return True


# ─── Subscription check helper ───────────────────────────────────────────────

async def is_user_subscribed(application: Application, user_id: int) -> bool:
    """Check if user is subscribed to the required channel."""
    try:
        member = await application.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL_ID, user_id=user_id
        )
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]
    except TelegramError:
        return False


async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback when user clicks 'Check subscription' button."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id)

    if await is_user_subscribed(context.application, user.id):
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user.id,
            text=t(lang, "start", name=user.first_name, limit=DAILY_FREE_LIMIT),
            parse_mode="Markdown",
        )
    else:
        await context.bot.send_message(chat_id=user.id, text=t(lang, "sub_failed"))


# ─── Private text/URL handler ────────────────────────────────────────────────

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    text = update.message.text or ""

    # React to every message
    await react_to_message(update.message)

    # Check mandatory subscription
    if not await is_user_subscribed(context.application, user.id):
        keyboard = [
            [InlineKeyboardButton(t(lang, "sub_button"), url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton(t(lang, "sub_check_btn"), callback_data="check_subscription")],
        ]
        await update.message.reply_text(
            text=t(lang, "sub_required"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # Search for URLs in the message
    url_match = URL_REGEX.search(text)
    if not url_match:
        await update.message.reply_text(
            t(lang, "start", name=user.first_name, limit=DAILY_FREE_LIMIT),
            parse_mode="Markdown",
        )
        return

    url = url_match.group(0)

    # Daily limit check (shared across URL/APK/QR)
    if not check_and_consume_limit(user.id):
        await update.message.reply_text(t(lang, "limit_reached", limit=DAILY_FREE_LIMIT))
        return

    status_msg = await update.message.reply_text(t(lang, "checking"))

    # Deep multi-API scan
    try:
        vt_res, gsb_res, alien_res, uscan_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
            check_alienvault(url),
            check_urlscan(url),
        )
        domain_res = await check_url_with_domain_age(url)

        is_dangerous = (
            gsb_res.get("dangerous", False)
            or vt_res.get("malicious", 0) > 0
            or alien_res.get("dangerous", False)
            or uscan_res.get("verdict") == "malicious"
        )
        status_str = "🔴 Malicious" if is_dangerous else "🟢 Clean"
        add_to_history(user.id, url, status_str)

        report = f"🛡 *SafeLink Ko'p Qatlamli Tahlil:*\n\n"
        report += f"🔗 *URL:* `{url}`\n"
        report += f"📊 *Xulosa:* {'🚨 XAVFLI' if is_dangerous else '✅ XAVFSIZ'}\n\n"
        report += f"🔍 *VirusTotal:* `{vt_res.get('malicious', 0)}/{vt_res.get('total', 0)}` tahdid\n"
        report += f"🌐 *Google Safe Browsing:* {'❌ Xavfli' if gsb_res.get('dangerous') else '✅ Toza'}\n"
        report += f"👽 *AlienVault OTX:* `{alien_res.get('pulses_count', 0)}` tahdid guruhi\n"
        report += f"📸 *URLScan.io:* `{str(uscan_res.get('verdict', 'unknown')).upper()}` (skor: {uscan_res.get('score', 0)}/100)\n"

        if domain_res and "age_days" in domain_res:
            age = domain_res.get("age_days", 0)
            report += f"📅 *Domen yoshi:* `{age} kun` ({domain_res.get('created', 'N/A')})\n"
            if age < 30:
                report += f"⚠️ *Juda yangi domen! Fishing bo'lishi mumkin!*\n"

        await status_msg.edit_text(text=report, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Havolani tekshirishda xatolik: {e}")
        await status_msg.edit_text("❌ Havolani tahlil qilish jarayonida xatolik yuz berdi.")


# ─── APK file handler (private) ──────────────────────────────────────────────

async def handle_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    doc = update.message.document

    if not (doc.file_name or "").lower().endswith(".apk"):
        return

    # React to every message
    await react_to_message(update.message)

    # Rate limiting
    limited, seconds = is_rate_limited(user_id)
    if limited:
        await update.message.reply_text(t(lang, "rate_limited", seconds=seconds))
        return
    update_rate_limit(user_id)

    # Daily limit check (shared across URL/APK/QR)
    if not check_and_consume_limit(user_id):
        await update.message.reply_text(t(lang, "limit_reached", limit=DAILY_FREE_LIMIT))
        return

    # Max size check (32 MB)
    if doc.file_size > 32 * 1024 * 1024:
        await update.message.reply_text("❌ APK fayl hajmi juda katta. Maksimal limit 32 MB.")
        return

    status_msg = await update.message.reply_text(
        "🔍 *APK fayl tahlil qilinmoqda, kuting...*", parse_mode="Markdown"
    )
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await scan_apk(bytes(file_bytes), doc.file_name)

        if result.get("success"):
            mal = result.get("malicious", 0)
            sus = result.get("suspicious", 0)
            total = result.get("total", 0)

            if mal > 0:
                await status_msg.edit_text(
                    f"🚨 *Zararli APK aniqlandi!* (Virus)\n"
                    f"📦 Nomi: `{doc.file_name}`\n"
                    f"Aniqlovchi dvigatellar: `{mal}/{total}`",
                    parse_mode="Markdown",
                )
            elif sus > 0:
                await status_msg.edit_text(
                    f"⚠️ *Shubhali APK activity!*\n"
                    f"📦 Nomi: `{doc.file_name}`\n"
                    f"Shubhali qismlar: `{sus}/{total}`",
                    parse_mode="Markdown",
                )
            else:
                await status_msg.edit_text(
                    f"✅ *Xavfsiz APK!* Zararli kodlar aniqlanmadi.\n"
                    f"📦 Nomi: `{doc.file_name}`",
                    parse_mode="Markdown",
                )
        else:
            await status_msg.edit_text("❌ VirusTotal API orqali APK faylni tekshirib bo'lmadi.")
    except Exception as e:
        logging.error(f"APK error: {e}")
        await status_msg.edit_text("❌ APK tahlili jarayonida xatolik yuz berdi.")


# ─── Photo/QR handler (private) ──────────────────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    # React to every message
    await react_to_message(update.message)

    # Rate limiting
    limited, seconds = is_rate_limited(user_id)
    if limited:
        await update.message.reply_text(t(lang, "rate_limited", seconds=seconds))
        return
    update_rate_limit(user_id)

    # Daily limit check (shared across URL/APK/QR)
    if not check_and_consume_limit(user_id):
        await update.message.reply_text(t(lang, "limit_reached", limit=DAILY_FREE_LIMIT))
        return

    photo = update.message.photo[-1]
    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        url = extract_qr_url(bytes(photo_bytes))

        if not url:
            await update.message.reply_text(
                "🔍 Ushbu rasmdan hech qanday QR-kod yoki havola topilmadi."
            )
            return

        status_msg = await update.message.reply_text(
            f"🔗 *QR-kod ichidan havola topildi:* `{url}`\nUni tahlil qilmoqdaman...",
            parse_mode="Markdown",
        )

        # Deep check the URL from QR
        vt_res = await check_virustotal(url)
        gsb_res = await check_google_safe_browsing(url)
        is_dangerous = gsb_res.get("dangerous", False) or vt_res.get("malicious", 0) > 0

        status_str = "🔴 Malicious" if is_dangerous else "🟢 Clean"
        add_to_history(user_id, url, status_str)

        report = f"🛡 *QR-kod ichidagi havola hisoboti:*\n\n`{url}`\n\n"
        report += f"Holati: {'🚨 ZARARLI/FISHING' if is_dangerous else '✅ TOZA'}\n"
        report += f"VirusTotal tahlili: {vt_res.get('malicious', 0)} ta dvigatel xavf aniqladi."

        await status_msg.edit_text(report, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"QR error: {e}")
        await update.message.reply_text("❌ QR-kodni tahlil qilib o'qishda xatolik yuz berdi.")
