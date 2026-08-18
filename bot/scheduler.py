"""
APScheduler setup — consolidates all scheduled jobs:
- send_daily_tips
- reward_top_referrers
- send_limit_warnings
- check_monitored_emails
- send_weekly_reports
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application

from bot.handlers.social import send_daily_tips, reward_top_referrers
from bot.handlers.breach import check_monitored_emails
from bot.core.rate_limiter import send_limit_warnings


# ─── Weekly report (from handlers/weekly_report.py) ───────────────────────────

from bot.core.database import (
    get_user_lang, get_all_active_users,
    get_weekly_stats, reset_weekly_stats,
)
from bot.i18n import t
from telegram.error import TelegramError


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

    reset_weekly_stats()
    logging.info(f"Weekly reports sent to {sent} users")


# ─── Scheduler setup ──────────────────────────────────────────────────────────

def setup_scheduler(application: Application):
    """Configure APScheduler for daily tips, monthly rewards, and rate limit warnings."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        send_daily_tips, CronTrigger(hour=9, minute=0),
        args=[application], id="daily_tips", replace_existing=True,
    )
    scheduler.add_job(
        reward_top_referrers, CronTrigger(day=1, hour=0, minute=0),
        args=[application], id="monthly_reward", replace_existing=True,
    )
    scheduler.add_job(
        send_limit_warnings, CronTrigger(hour="*/4", minute=0),
        args=[application], id="rate_limit_check", replace_existing=True,
    )
    scheduler.add_job(
        check_monitored_emails, CronTrigger(hour=10, minute=0),
        args=[application], id="breach_monitor", replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_reports, CronTrigger(day_of_week="mon", hour=10, minute=0),
        args=[application], id="weekly_report", replace_existing=True,
    )

    scheduler.start()
    print("⏰ Scheduler ishga tushdi")
