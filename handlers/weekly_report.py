"""
Weekly Personal Report.
Sends each active user a summary of their week's activity:
- total checks, dangerous found, breaches monitored, etc.
Scheduler job runs once a week (Monday morning).
"""
import logging
from telegram.ext import Application
from telegram.error import TelegramError

from database import (
    get_user_lang, get_all_active_users,
    get_weekly_stats, reset_weekly_stats,
)
from languages import t


async def send_weekly_reports(application: Application):
    """
    Sends a weekly activity summary to all users who had activity,
    then resets the weekly counters. Called by APScheduler.
    """
    users = get_all_active_users()
    sent = 0

    for user_id in users:
        stats = get_weekly_stats(user_id)
        total = stats.get("checks", 0)

        # Skip users with no activity this week
        if total == 0:
            continue

        lang = get_user_lang(user_id)
        dangerous = stats.get("dangerous", 0)
        safe = total - dangerous

        message = t(
            lang, "weekly_report",
            total=total, safe=safe, dangerous=dangerous,
        )

        try:
            await application.bot.send_message(
                chat_id=user_id, text=message, parse_mode="Markdown"
            )
            sent += 1
        except TelegramError:
            pass

        if sent % 25 == 0:
            import asyncio
            await asyncio.sleep(1)

    # Reset all weekly counters for the new week
    reset_weekly_stats()
    logging.info(f"Weekly reports sent to {sent} users")
