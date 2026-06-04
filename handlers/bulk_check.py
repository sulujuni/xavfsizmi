"""
Bulk URL Check handler.
User sends multiple links separated by newlines → bot checks them all.
"""
import re
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import get_user_lang, is_premium, get_user_checks, increment_user_checks
from config import DAILY_FREE_LIMIT
from languages import t
from checker import check_virustotal, check_google_safe_browsing
from handlers.tools import calculate_trust_score, trust_score_emoji
from handlers.private_messages import require_subscription, react_to_message

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')


async def handle_bulk_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /bulk command. User sends multiple URLs (one per line) after the command.
    Usage: /bulk
    https://example1.com
    https://example2.com
    """
    user = update.effective_user
    lang = get_user_lang(user.id)

    await react_to_message(update.message)

    # Subscription check
    if not await require_subscription(update, context):
        return

    # Get text after the command
    text = update.message.text or ""
    # Remove /bulk command itself
    text = re.sub(r'^/bulk\s*', '', text, flags=re.IGNORECASE).strip()

    # Find all URLs
    urls = URL_REGEX.findall(text)

    if not urls:
        await update.message.reply_text(
            t(lang, "bulk_usage"),
            parse_mode="Markdown",
        )
        return

    # Limit: max 5 URLs for free, 10 for premium
    max_urls = 10 if is_premium(user.id) else 5
    if len(urls) > max_urls:
        urls = urls[:max_urls]

    # Check daily limit
    if not is_premium(user.id):
        checks = get_user_checks(user.id)
        remaining = DAILY_FREE_LIMIT - checks
        if remaining <= 0:
            await update.message.reply_text(t(lang, "limit_reached", limit=DAILY_FREE_LIMIT))
            return
        # Only check as many as remaining allows
        urls = urls[:remaining]
        for _ in urls:
            increment_user_checks(user.id)

    status_msg = await update.message.reply_text(
        f"🔄 {len(urls)} ta havola tekshirilmoqda..."
    )

    results = []
    for url in urls:
        try:
            vt_res, gsb_res = await asyncio.gather(
                check_virustotal(url),
                check_google_safe_browsing(url),
            )
            score = calculate_trust_score(
                vt_res, gsb_res,
                {"pulses_count": 0, "dangerous": False},
                {"verdict": "unknown", "score": 0},
                365
            )
            results.append({"url": url, "score": score})
        except Exception as e:
            logging.error(f"Bulk check error for {url}: {e}")
            results.append({"url": url, "score": -1})

    # Format report
    report = f"📋 *Bulk Tekshiruv Natijalari ({len(results)} ta):*\n\n"
    for r in results:
        if r["score"] < 0:
            emoji = "⚪"
            label = "Xatolik"
        elif r["score"] >= 80:
            emoji = "🟢"
            label = f"{r['score']}/100"
        elif r["score"] >= 50:
            emoji = "🟡"
            label = f"{r['score']}/100"
        else:
            emoji = "🔴"
            label = f"{r['score']}/100"

        # Truncate long URLs
        display_url = r["url"][:50] + "..." if len(r["url"]) > 50 else r["url"]
        report += f"{emoji} `{display_url}` — {label}\n"

    report += f"\n📊 *Jami:* {len(results)} ta havola tekshirildi"

    try:
        await status_msg.edit_text(report, parse_mode="Markdown", disable_web_page_preview=True)
    except TelegramError:
        await status_msg.edit_text(report, disable_web_page_preview=True)
