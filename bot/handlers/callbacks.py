"""
Consolidated CallbackQueryHandler routing.
Re-exports all callback handlers from their respective modules.
"""
from bot.handlers.start import language_callback, group_language_callback
from bot.handlers.scan import check_subscription_callback
from bot.handlers.social import tips_toggle_callback
from bot.handlers.breach import monitor_remove_callback
from bot.handlers.premium import payment_gateway_callback, admin_payment_callback
from bot.handlers.admin import admin_callback
