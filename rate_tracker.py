"""
API Rate Limit Tracker.
Tracks daily API usage for each service and provides dashboard for admins.
Warns when approaching limits.
"""
import json
import os
from datetime import date

TRACKER_FILE = "/data/rate_tracker.json" if os.path.exists("/data") else "rate_tracker.json"


def _load_tracker() -> dict:
    """Load rate tracker data from file."""
    if not os.path.exists(TRACKER_FILE):
        return {}
    try:
        with open(TRACKER_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_tracker(data: dict):
    """Save rate tracker data to file."""
    dir_name = os.path.dirname(TRACKER_FILE)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)


def track_api_call(api_name: str):
    """
    Record one API call for the given service.
    Call this every time you make a request to an external API.
    """
    data = _load_tracker()
    today = str(date.today())

    if "daily" not in data:
        data["daily"] = {}
    if today not in data["daily"]:
        data["daily"] = {today: {}}  # Reset old days
    if api_name not in data["daily"][today]:
        data["daily"][today][api_name] = 0

    data["daily"][today][api_name] += 1
    _save_tracker(data)


def get_daily_usage() -> dict:
    """
    Returns today's API usage for all services.
    Format: {api_name: count, ...}
    """
    data = _load_tracker()
    today = str(date.today())
    return data.get("daily", {}).get(today, {})


def get_usage_dashboard() -> str:
    """
    Generates a formatted dashboard string showing API usage vs limits.
    Used by admin /ratelimit command.
    """
    from config import API_LIMITS

    usage = get_daily_usage()
    today = str(date.today())

    text = "📊 *API Rate Limit Dashboard*\n"
    text += f"📅 Sana: `{today}`\n\n"

    for api_name, limit in API_LIMITS.items():
        used = usage.get(api_name, 0)
        percentage = (used / limit * 100) if limit > 0 else 0

        # Progress bar
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)

        # Warning emoji based on usage
        if percentage >= 90:
            emoji = "🔴"
        elif percentage >= 70:
            emoji = "🟡"
        else:
            emoji = "🟢"

        text += f"{emoji} *{api_name}*\n"
        text += f"   `[{bar}]` {used}/{limit} ({percentage:.0f}%)\n\n"

    # Total calls today
    total = sum(usage.values())
    text += "━━━━━━━━━━━━━━━━\n"
    text += f"📈 *Jami bugungi so'rovlar:* `{total}`"

    return text


def check_limit_warning(api_name: str) -> str:
    """
    Check if an API is approaching its limit.
    Returns warning message or empty string.
    """
    from config import API_LIMITS

    usage = get_daily_usage()
    used = usage.get(api_name, 0)
    limit = API_LIMITS.get(api_name, 0)

    if limit == 0:
        return ""

    percentage = used / limit * 100

    if percentage >= 95:
        return f"🚨 *KRITIK:* `{api_name}` limiti tugamoqda! ({used}/{limit} = {percentage:.0f}%)"
    elif percentage >= 80:
        return f"⚠️ *Ogohlantirish:* `{api_name}` limiti yaqinlashmoqda ({used}/{limit} = {percentage:.0f}%)"

    return ""


async def send_limit_warnings(application):
    """
    Check all APIs and send warnings to admin if any are near limit.
    Called periodically by the scheduler.
    """
    from config import API_LIMITS, ADMIN_ID
    from telegram.error import TelegramError

    warnings = []
    for api_name in API_LIMITS:
        warning = check_limit_warning(api_name)
        if warning:
            warnings.append(warning)

    if warnings:
        text = "⚠️ *API LIMIT OGOHLANTIRISH:*\n\n" + "\n".join(warnings)
        try:
            await application.bot.send_message(
                chat_id=ADMIN_ID, text=text, parse_mode="Markdown"
            )
        except TelegramError:
            pass
