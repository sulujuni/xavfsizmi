"""
Referral Leaderboard:
/top shows top 10 referrers this month.
Top 3 get a free premium month automatically.
"""
from telegram import Update
from telegram.ext import ContextTypes, Application
from telegram.error import TelegramError
import logging
from datetime import datetime, date

from database import (
    get_user_lang, load_db, save_db, set_premium,
    get_referral_count,
)
from languages import t
from handlers.private_messages import require_subscription, react_to_message


# ─── Leaderboard helpers ──────────────────────────────────────────────────────

def get_monthly_referral_leaderboard() -> list:
    """
    Returns top referrers sorted by count.
    Returns list of (user_id, count) tuples.
    """
    db = load_db()
    referral_counts = {}

    for key in db.keys():
        if key.isdigit():
            referred_by = db[key].get("referred_by")
            if referred_by:
                referrer_id = int(referred_by) if isinstance(referred_by, str) else referred_by
                referral_counts[referrer_id] = referral_counts.get(referrer_id, 0) + 1

    # Sort by count descending
    sorted_board = sorted(referral_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_board[:10]


# ─── /top command ─────────────────────────────────────────────────────────────

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows top 10 referrers leaderboard."""
    user = update.effective_user
    lang = get_user_lang(user.id)

    await react_to_message(update.message)

    if not await require_subscription(update, context):
        return

    leaderboard = get_monthly_referral_leaderboard()

    if not leaderboard:
        await update.message.reply_text(t(lang, "leaderboard_empty"))
        return

    # Build leaderboard text
    medals = ["🥇", "🥈", "🥉"]
    text = t(lang, "leaderboard_title") + "\n\n"

    for i, (uid, count) in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"#{i+1}"
        # Try to get user name
        try:
            chat = await context.bot.get_chat(uid)
            name = chat.first_name or f"User {uid}"
        except Exception:
            name = f"User {uid}"

        prize = " ⭐" if i < 3 else ""
        text += f"{medal} *{name}* — {count} ta taklif{prize}\n"

    text += f"\n{'─' * 20}\n"
    text += t(lang, "leaderboard_footer")

    # Check user's own position
    user_count = get_referral_count(user.id)
    text += f"\n\n👤 *Sizning o'rningiz:* {user_count} ta taklif"

    await update.message.reply_text(text, parse_mode="Markdown")


# ─── Monthly auto-reward (called by scheduler) ───────────────────────────────

async def reward_top_referrers(application: Application):
    """
    Awards top 3 referrers with 30 days free premium.
    Should be called once per month by the scheduler.
    """
    leaderboard = get_monthly_referral_leaderboard()

    for i, (uid, count) in enumerate(leaderboard[:3]):
        if count < 1:
            continue
        # Give 30 days premium
        set_premium(uid, days=30)
        try:
            await application.bot.send_message(
                chat_id=uid,
                text=(
                    f"🏆 *Tabriklaymiz!* Siz bu oyning eng faol taklif qiluvchisi bo'ldingiz!\n\n"
                    f"🎁 Sizga 30 kunlik bepul Premium taqdim etildi.\n"
                    f"📊 Sizning taklif sonatingiz: {count} ta"
                ),
                parse_mode="Markdown",
            )
        except TelegramError:
            pass

    logging.info(f"Monthly rewards: top {min(3, len(leaderboard))} rewarded")
