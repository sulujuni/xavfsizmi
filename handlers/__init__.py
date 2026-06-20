"""
Handlers package — all bot handler functions organized by responsibility.
"""

from .commands import (
    start_command,
    help_command,
    language_command,
    language_callback,
    group_language_callback,
    history_command,
    stats_command,
    referral_command,
    phish_command,
)

from .conversations import (
    scammer_command,
    scammer_receive,
    report_command,
    report_receive,
    feedback_command,
    feedback_receive,
    darkweb_command,
    darkweb_receive,
    cancel_conversation,
    WAITING_SCAMMER_INPUT,
    WAITING_REPORT_INPUT,
    WAITING_FEEDBACK_INPUT,
    WAITING_DARKWEB_INPUT,
)

from .premium import (
    premium_command,
    add_promo_command,
    promo_command,
    payment_gateway_callback,
    admin_payment_callback,
    pre_checkout,
    payment_success,
    paynet_receipt_command,
    paynet_receipt_receive,
    paynet_receipt_cancel,
    WAITING_PAYNET_RECEIPT,
)

from .breach import (
    breach_command,
    breach_receive_input,
    breach_cancel,
    WAITING_BREACH_INPUT,
)

from .private_messages import (
    is_user_subscribed,
    require_subscription,
    check_subscription_callback,
    handle_private_message,
    handle_apk,
    handle_photo,
)

from .group_messages import (
    handle_group_message,
    handle_group_apk,
    handle_group_photo,
)

from .secretary import (
    handle_business_connection,
    handle_business_message,
)

from .daily_tips import tips_command, send_daily_tips
from .leaderboard import top_command, reward_top_referrers

from .ai import (
    ask_command,
    ask_receive,
    analyze_command,
    analyze_receive,
    ai_cancel,
    WAITING_ASK_INPUT,
    WAITING_ANALYZE_INPUT,
)

from .monitor import (
    monitor_command,
    monitor_receive_email,
    monitor_remove_callback,
    check_monitored_emails,
    WAITING_MONITOR_EMAIL,
)

from .weekly_report import send_weekly_reports
