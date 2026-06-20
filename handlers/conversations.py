"""
Conversation handlers for commands that need a 2-step flow:
1. User sends command → bot asks for input
2. User sends input → bot processes

Commands: /scammer, /report, /feedback, /darkweb
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_ID
from database import get_user_lang, add_report
from languages import t
from handlers.tools import check_social_account, check_dark_web_mentions
from handlers.private_messages import require_subscription, react_to_message

# Conversation states
WAITING_SCAMMER_INPUT = 10
WAITING_REPORT_INPUT = 12
WAITING_FEEDBACK_INPUT = 13
WAITING_DARKWEB_INPUT = 14


# ═══════════════════════════════════════════════════════════════════════════════
# /scammer conversation
# ═══════════════════════════════════════════════════════════════════════════════

async def scammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for username."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "scammer_ask"), parse_mode="Markdown")
    return WAITING_SCAMMER_INPUT


async def scammer_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Receive username and check."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    username = update.message.text.strip()

    status_msg = await update.message.reply_text(t(lang, "checking"))
    result = await check_social_account(username)

    if result["reports_found"] > 0:
        warnings_text = "\n".join([f"  🚨 {w}" for w in result["warnings"]])
        text = (
            f"⚠️ *{t(lang, 'scammer_result_title')}:*\n\n"
            f"👤 `@{result['username']}`\n\n"
            f"🚨 *{t(lang, 'warning_found')}!*\n{warnings_text}\n\n"
            f"📊 {t(lang, 'sources_checked')}: {result['sources_checked']}"
        )
    else:
        text = (
            f"✅ *{t(lang, 'scammer_result_title')}:*\n\n"
            f"👤 `@{result['username']}`\n\n"
            f"✅ {t(lang, 'no_warnings')}\n"
            f"📊 {t(lang, 'sources_checked')}: {result['sources_checked']}\n"
            f"⚠️ {t(lang, 'no_guarantee')}"
        )
    await status_msg.edit_text(text, parse_mode="Markdown")
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
# /report conversation
# ═══════════════════════════════════════════════════════════════════════════════

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for URL to report."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "report_ask"), parse_mode="Markdown")
    return WAITING_REPORT_INPUT


async def report_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Receive URL and submit report."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    url_to_report = update.message.text.strip()

    try:
        add_report(user.id, url_to_report)
    except Exception:
        pass
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 *Report:*\n👤 {user.full_name} (`{user.id}`)\n🔗 {url_to_report}",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await update.message.reply_text(t(lang, "report_sent"))
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
# /feedback conversation
# ═══════════════════════════════════════════════════════════════════════════════

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for feedback text."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "feedback_ask"), parse_mode="Markdown")
    return WAITING_FEEDBACK_INPUT


async def feedback_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Receive feedback and forward to admin."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    feedback_text = update.message.text.strip()

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 *Feedback:*\n👤 {user.full_name} (`{user.id}`)\n💬 {feedback_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(t(lang, "feedback_received"))
    except Exception:
        await update.message.reply_text(t(lang, "error_send_failed"))
    return ConversationHandler.END


# ─── Cancel handler (shared) ─────────────────────────────────────────────────

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "breach_cancel"))
    return ConversationHandler.END



# ═══════════════════════════════════════════════════════════════════════════════
# /darkweb conversation
# ═══════════════════════════════════════════════════════════════════════════════

async def darkweb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for email/username to check."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "darkweb_ask"), parse_mode="Markdown")
    return WAITING_DARKWEB_INPUT


async def darkweb_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Check dark web mentions."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    query = update.message.text.strip()

    status_msg = await update.message.reply_text(t(lang, "checking"))
    result = await check_dark_web_mentions(query)

    if result["total_mentions"] > 0:
        sources_text = "\n".join([f"  🔴 {s}" for s in result["found_in"]])
        text = t(lang, "darkweb_found",
                 query=query, count=result["total_mentions"],
                 sources=sources_text)
    else:
        text = t(lang, "darkweb_safe", query=query,
                 checked=result["sources_checked"])

    await status_msg.edit_text(text, parse_mode="Markdown")
    return ConversationHandler.END
