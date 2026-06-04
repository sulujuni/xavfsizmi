"""
Global error handler — catches all unhandled exceptions and reports them to admin.
Also tracks API rate limit usage.
"""
import logging
import traceback
from datetime import date, datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler. Logs the error and sends details to the admin.
    Registered via app.add_error_handler(error_handler).
    """
    # Log the error
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Build error message for admin
    error_text = f"🚨 *BOT ERROR REPORT*\n\n"
    error_text += f"⏰ *Vaqt:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"

    # Add update info if available
    if isinstance(update, Update):
        if update.effective_user:
            error_text += f"👤 *User:* {update.effective_user.full_name} (`{update.effective_user.id}`)\n"
        if update.effective_chat:
            error_text += f"💬 *Chat:* `{update.effective_chat.id}` ({update.effective_chat.type})\n"
        if update.effective_message and update.effective_message.text:
            msg_preview = update.effective_message.text[:100]
            error_text += f"📝 *Xabar:* `{msg_preview}`\n"

    # Add error details
    if context.error:
        error_name = type(context.error).__name__
        error_msg = str(context.error)[:300]
        error_text += f"\n❌ *Xatolik:* `{error_name}`\n"
        error_text += f"📋 *Tafsilot:* `{error_msg}`\n"

        # Get traceback (last 5 lines)
        tb = traceback.format_exception(type(context.error), context.error, context.error.__traceback__)
        tb_short = "".join(tb[-5:])[:500]
        error_text += f"\n```\n{tb_short}\n```"

    # Send to admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=error_text,
            parse_mode="Markdown",
        )
    except TelegramError:
        # If markdown fails, send without formatting
        try:
            plain_text = error_text.replace("*", "").replace("`", "").replace("```", "")
            await context.bot.send_message(chat_id=ADMIN_ID, text=plain_text)
        except Exception:
            logger.error("Could not send error report to admin!")
