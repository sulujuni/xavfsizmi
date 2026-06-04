"""
Private message handlers:
- handle_private_message (URL scanning with Trust Score)
- handle_apk (APK file scanning)
- handle_photo (QR code scanning)

All checks (URL, APK, QR) share the same daily limit for non-premium users.
Bot reacts to every message with a random emoji.
Mandatory channel subscription enforced on all handlers.
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
from handlers.tools import (
    calculate_trust_score, trust_score_emoji,
    get_website_screenshot, check_typosquatting,
    is_short_url, expand_short_url,
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
    if not REQUIRED_CHANNEL_ID or REQUIRED_CHANNEL_ID == 0:
        return True
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


async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks subscription. If not subscribed, sends subscription prompt and returns False.
    Returns True if user is subscribed.
    """
    user = update.effective_user
    lang = get_user_lang(user.id)

    if await is_user_subscribed(context.application, user.id):
        return True

    keyboard = [
        [InlineKeyboardButton(t(lang, "sub_button"), url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton(t(lang, "sub_check_btn"), callback_data="check_subscription")],
    ]
    await update.message.reply_text(
        text=t(lang, "sub_required"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
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


# ─── Private text/URL handler (with Trust Score + Typosquatting) ──────────────

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    text = update.message.text or ""

    # React to every message
    await react_to_message(update.message)

    # Check mandatory subscription
    if not await require_subscription(update, context):
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

    # If it's a short URL, expand it first
    expanded_info = ""
    if is_short_url(url):
        expand_result = await expand_short_url(url)
        if expand_result["redirect_count"] > 0:
            url = expand_result["final_url"]
            expanded_info = f"🔀 *{t(lang, 'short_url_expanded')}:* `{expand_result['original']}` → `{url}`\n\n"

    # Deep multi-API scan
    try:
        vt_res, gsb_res, alien_res, uscan_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
            check_alienvault(url),
            check_urlscan(url),
        )
        domain_res = await check_url_with_domain_age(url)
        domain_age = domain_res.get("age_days", 365) if domain_res else 365

        # Calculate Trust Score
        trust_score = calculate_trust_score(vt_res, gsb_res, alien_res, uscan_res, domain_age)
        score_display = trust_score_emoji(trust_score, lang)

        is_dangerous = trust_score < 50
        status_str = f"{'🔴' if is_dangerous else '🟢'} {trust_score}/100"
        add_to_history(user.id, url, status_str)

        # Check typosquatting
        typo_result = check_typosquatting(url)
        typo_warning = ""
        if typo_result.get("is_typosquat"):
            match = typo_result["matches"][0]
            typo_warning = f"\n⚠️ *TYPOSQUATTING:* {t(lang, 'typo_warning', domain=match['similar_to'])}\n"

        # Build report
        report = expanded_info
        report += t(lang, "scan_header") + "\n\n"
        report += f"🔗 *URL:* `{url}`\n"
        report += f"🎯 *{t(lang, 'trust_score_label')}:* {score_display}\n"
        report += typo_warning
        report += f"\n"
        report += f"🔍 *VirusTotal:* `{vt_res.get('malicious', 0)}/{vt_res.get('total', 0)}` {t(lang, 'threats')}\n"
        report += f"🌐 *Google Safe Browsing:* {'❌ ' + t(lang, 'dangerous') if gsb_res.get('dangerous') else '✅ ' + t(lang, 'clean')}\n"
        report += f"👽 *AlienVault OTX:* `{alien_res.get('pulses_count', 0)}` {t(lang, 'threat_groups')}\n"
        report += f"📸 *URLScan.io:* `{str(uscan_res.get('verdict', 'unknown')).upper()}` ({t(lang, 'score')}: {uscan_res.get('score', 0)}/100)\n"

        if domain_res and "age_days" in domain_res:
            age = domain_res.get("age_days", 0)
            report += f"📅 *{t(lang, 'domain_age_label')}:* `{age} {t(lang, 'days')}` ({domain_res.get('created', 'N/A')})\n"
            if age < 30:
                report += f"⚠️ *{t(lang, 'new_domain_warning')}*\n"

        # Try to get screenshot (non-blocking, don't wait too long)
        try:
            screenshot_url = await asyncio.wait_for(
                get_website_screenshot(url), timeout=5
            )
            if screenshot_url:
                report += f"\n📸 [{t(lang, 'screenshot_link')}]({screenshot_url})"
        except (asyncio.TimeoutError, Exception):
            pass

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

    # Check mandatory subscription
    if not await require_subscription(update, context):
        return

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
        await update.message.reply_text(t(lang, "too_large"))
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

            report = f"📱 *APK Tahlil Hisoboti:*\n\n"
            report += f"📦 *Fayl:* `{doc.file_name}`\n"

            if mal > 0:
                report += f"🚨 *Holat:* ZARARLI (Virus)\n"
                report += f"🔍 *Aniqlovchilar:* `{mal}/{total}`\n"
            elif sus > 0:
                report += f"⚠️ *Holat:* SHUBHALI\n"
                report += f"🔍 *Shubhali:* `{sus}/{total}`\n"
            else:
                report += f"✅ *Holat:* XAVFSIZ\n"
                report += f"🔍 *Tekshiruvchilar:* `{total}` ta dvigatel\n"

            # Behavioral analysis (permissions, network)
            if result.get("permissions"):
                perms = result["permissions"][:8]
                report += f"\n📋 *Ruxsatlar ({len(result['permissions'])} ta):*\n"
                for p in perms:
                    emoji = "🔴" if "DANGEROUS" in p.get("level", "") else "🟢"
                    report += f"  {emoji} `{p.get('name', '')}`\n"

            if result.get("network_calls"):
                report += f"\n🌐 *Tarmoq so'rovlari:* {len(result['network_calls'])} ta\n"

            await status_msg.edit_text(report, parse_mode="Markdown")
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

    # Check mandatory subscription
    if not await require_subscription(update, context):
        return

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
        vt_res, gsb_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
        )
        domain_res = await check_url_with_domain_age(url)
        domain_age = domain_res.get("age_days", 365) if domain_res else 365

        # Trust score for QR URLs too
        trust_score = calculate_trust_score(
            vt_res, gsb_res, {"pulses_count": 0, "dangerous": False},
            {"verdict": "unknown", "score": 0}, domain_age
        )
        score_display = trust_score_emoji(trust_score)
        is_dangerous = trust_score < 50

        status_str = f"{'🔴' if is_dangerous else '🟢'} {trust_score}/100"
        add_to_history(user_id, url, status_str)

        report = f"🛡 *QR-kod ichidagi havola hisoboti:*\n\n"
        report += f"🔗 `{url}`\n\n"
        report += f"🎯 *Ishonch Darajasi:* {score_display}\n"
        report += f"🔍 *VirusTotal:* {vt_res.get('malicious', 0)} ta dvigatel xavf aniqladi\n"
        report += f"🌐 *Google Safe Browsing:* {'❌ Xavfli' if gsb_res.get('dangerous') else '✅ Toza'}"

        await status_msg.edit_text(report, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"QR error: {e}")
        await update.message.reply_text("❌ QR-kodni tahlil qilib o'qishda xatolik yuz berdi.")
