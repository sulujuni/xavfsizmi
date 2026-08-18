"""
Social handlers — merged from:
- handlers/conversations.py (scammer, report, feedback)
- handlers/commands.py (referral, phish)
- handlers/daily_tips.py (tips command)
- handlers/leaderboard.py (top command)
"""
import random
import logging
import aiohttp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, Application
from telegram.error import TelegramError

from bot.config import ADMIN_ID, GROQ_API_KEY, DAILY_FREE_LIMIT
from bot.core.database import (
    get_user_lang, add_report, load_db, save_db,
    set_premium, get_referral_count,
)
from bot.i18n import t
from bot.core.trust import check_social_account

# Conversation states
WAITING_SCAMMER_INPUT = 10
WAITING_REPORT_INPUT = 12
WAITING_FEEDBACK_INPUT = 13


# ═══════════════════════════════════════════════════════════════════════════════
# /scammer conversation
# ═══════════════════════════════════════════════════════════════════════════════

async def scammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Ask for username."""
    from bot.handlers.scan import react_to_message, require_subscription
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
    from bot.handlers.scan import react_to_message, require_subscription
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
    from bot.handlers.scan import react_to_message, require_subscription
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
# /referral (from commands.py)
# ═══════════════════════════════════════════════════════════════════════════════

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.scan import react_to_message, require_subscription
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(
        text=t(lang, "referral_link", ref_code=user.id, count=count),
        parse_mode="Markdown", disable_web_page_preview=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /phish (from commands.py)
# ═══════════════════════════════════════════════════════════════════════════════

PHISH_TEMPLATES = [
    {"uz": "🏦 Diqqat! Kartangizdan 1,500,000 so'm yechilmoqda. Bekor qilish:", "ru": "🏦 Внимание! Списание 1,500,000 сум. Отменить:", "en": "🏦 Alert! $150 withdrawal from your card. Cancel:"},
    {"uz": "🎁 Tabriklaymiz! 5,000,000 so'm yutdingiz! Olish:", "ru": "🎁 Поздравляем! Выигрыш 5,000,000 сум! Получить:", "en": "🎁 You won $500! Claim:"},
    {"uz": "⚠️ Telegram akkauntingiz bloklanmoqda! Tasdiqlash:", "ru": "⚠️ Ваш Telegram будет заблокирован! Подтвердить:", "en": "⚠️ Your Telegram is being suspended! Verify:"},
    {"uz": "📦 Sizga jo'natma keldi! Kuzatish: UZ7839. Batafsil:", "ru": "📦 Посылка! Трек: RU7839. Подробнее:", "en": "📦 Package! Track: EN7839. Details:"},
    {"uz": "🔒 Kimdir akkauntingizga kirmoqchi! Parolni tiklash:", "ru": "🔒 Попытка входа! Сбросить пароль:", "en": "🔒 Login attempt! Reset password:"},
]


async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.scan import react_to_message, require_subscription
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    bot_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"

    template = random.choice(PHISH_TEMPLATES)
    phish_text = template.get(lang, template["uz"])

    # The copyable phishing message
    copy_text = f"{phish_text}\n{bot_link}"

    # First send the explanation
    await update.message.reply_text(t(lang, "phish_intro"))

    # Then send the phishing message separately (easy to copy/forward)
    keyboard = [
        [InlineKeyboardButton(t(lang, "phish_copy_btn"), switch_inline_query=copy_text[:64])],
    ]
    await update.message.reply_text(
        copy_text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# /tips (from daily_tips.py)
# ═══════════════════════════════════════════════════════════════════════════════

FALLBACK_TIPS = [
    {"uz": "🔐 Parollaringizni har 90 kunda yangilang va har bir sayt uchun alohida parol ishlating.", "ru": "🔐 Меняйте пароли каждые 90 дней и используйте уникальный пароль для каждого сайта.", "en": "🔐 Change your passwords every 90 days and use a unique password for each site."},
    {"uz": "📱 Ilovalani faqat rasmiy do'konlardan (Google Play, App Store) yuklab oling.", "ru": "📱 Скачивайте приложения только из официальных магазинов (Google Play, App Store).", "en": "📱 Only download apps from official stores (Google Play, App Store)."},
    {"uz": "🔗 Qisqa havolalarga (bit.ly, tinyurl) ishonmang — avval /expand orqali tekshiring.", "ru": "🔗 Не доверяйте коротким ссылкам (bit.ly, tinyurl) — проверьте через /expand.", "en": "🔗 Don't trust short links (bit.ly, tinyurl) — check them first with /expand."},
    {"uz": "🛡 Ikki bosqichli autentifikatsiyani (2FA) barcha akkauntlaringizda yoqing.", "ru": "🛡 Включите двухфакторную аутентификацию (2FA) на всех аккаунтах.", "en": "🛡 Enable two-factor authentication (2FA) on all your accounts."},
    {"uz": "📧 Notanish emaillardan kelgan fayllarni HECH QACHON ochmang.", "ru": "📧 НИКОГДА не открывайте файлы из писем незнакомых отправителей.", "en": "📧 NEVER open files from emails sent by unknown senders."},
    {"uz": "🏦 Bankingiz HECH QACHON parol yoki PIN kod so'ramaydi. Bu 100% fishing!", "ru": "🏦 Ваш банк НИКОГДА не просит пароль или ПИН-код. Это 100% фишинг!", "en": "🏦 Your bank NEVER asks for passwords or PINs. It's 100% phishing!"},
]


async def generate_ai_tip(lang: str = "uz") -> str:
    """Generates a fresh cybersecurity tip using Groq AI."""
    if not GROQ_API_KEY:
        return ""
    lang_map = {"uz": "O'zbek tilida", "ru": "на русском языке", "en": "in English"}
    lang_instruction = lang_map.get(lang, "in English")
    prompt = (
        f"Generate ONE short, practical cybersecurity tip or lifehack for regular internet users "
        f"{lang_instruction}. It should be:\n- Maximum 2-3 sentences\n- Actionable and specific\n"
        f"- Include a relevant emoji at the start\n- Written in a friendly tone\n\n"
        f"Just output the tip itself, nothing else. No quotation marks."
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant", "messages": [
                    {"role": "system", "content": "You are a cybersecurity expert giving daily tips to regular users."},
                    {"role": "user", "content": prompt},
                ], "temperature": 0.9, "max_tokens": 200},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tip = data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
                    return tip
    except Exception as e:
        logging.error(f"Groq AI tip generation error: {e}")
    return ""


def get_tips_enabled(user_id: int) -> bool:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return True
    return db[user_key].get("tips_enabled", True)


def set_tips_enabled(user_id: int, enabled: bool):
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"lang": "uz", "checks": 0}
    db[user_key]["tips_enabled"] = enabled
    save_db(db)


def get_all_tips_subscribers() -> list:
    db = load_db()
    subscribers = []
    for key in db.keys():
        if key.isdigit():
            if db[key].get("tips_enabled", True):
                subscribers.append(int(key))
    return subscribers


async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle daily tips on/off with inline buttons."""
    from bot.handlers.scan import react_to_message, require_subscription
    user = update.effective_user
    lang = get_user_lang(user.id)
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return

    if context.args and context.args[0].lower() in ("off", "0", "no", "yoq"):
        set_tips_enabled(user.id, False)
        keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_on_btn"), callback_data="tips_on")]]
        await update.message.reply_text(t(lang, "tips_disabled"), reply_markup=InlineKeyboardMarkup(keyboard))
    elif context.args and context.args[0].lower() in ("on", "1", "yes", "ha"):
        set_tips_enabled(user.id, True)
        keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_off_btn"), callback_data="tips_off")]]
        await update.message.reply_text(t(lang, "tips_enabled"), reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        enabled = get_tips_enabled(user.id)
        status = "✅" if enabled else "❌"
        status_msg = await update.message.reply_text(t(lang, "ai_generating"))
        ai_tip = await generate_ai_tip(lang)
        if ai_tip:
            tip_text = ai_tip
            source = "🤖 AI"
        else:
            tip = random.choice(FALLBACK_TIPS)
            tip_text = tip.get(lang, tip["uz"])
            source = "📝"
        if enabled:
            keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_off_btn"), callback_data="tips_off")]]
        else:
            keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_on_btn"), callback_data="tips_on")]]
        await status_msg.edit_text(
            f"{t(lang, 'tips_header', status=status)}\n\n{source} {t(lang, 'tips_today')}:\n{tip_text}",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def tips_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tips_on / tips_off inline button press."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id)
    if query.data == "tips_on":
        set_tips_enabled(user.id, True)
        keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_off_btn"), callback_data="tips_off")]]
        await query.edit_message_text(t(lang, "tips_enabled"), reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "tips_off":
        set_tips_enabled(user.id, False)
        keyboard = [[InlineKeyboardButton(t(lang, "tips_turn_on_btn"), callback_data="tips_on")]]
        await query.edit_message_text(t(lang, "tips_disabled"), reply_markup=InlineKeyboardMarkup(keyboard))


# ═══════════════════════════════════════════════════════════════════════════════
# /top — leaderboard (from leaderboard.py)
# ═══════════════════════════════════════════════════════════════════════════════

def get_monthly_referral_leaderboard() -> list:
    db = load_db()
    referral_counts = {}
    for key in db.keys():
        if key.isdigit():
            referred_by = db[key].get("referred_by")
            if referred_by:
                referrer_id = int(referred_by) if isinstance(referred_by, str) else referred_by
                if referrer_id == ADMIN_ID:
                    continue
                referral_counts[referrer_id] = referral_counts.get(referrer_id, 0) + 1
    sorted_board = sorted(referral_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_board[:10]


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows top 10 referrers leaderboard."""
    from bot.handlers.scan import react_to_message, require_subscription
    user = update.effective_user
    lang = get_user_lang(user.id)
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return

    leaderboard = get_monthly_referral_leaderboard()
    if not leaderboard:
        await update.message.reply_text(t(lang, "leaderboard_empty"))
        return

    medals = ["🥇", "🥈", "🥉"]
    text = t(lang, "leaderboard_title") + "\n\n"
    for i, (uid, count) in enumerate(leaderboard):
        medal = medals[i] if i < 3 else f"#{i+1}"
        try:
            chat = await context.bot.get_chat(uid)
            name = chat.first_name or f"User {uid}"
        except Exception:
            name = f"User {uid}"
        prize = " ⭐" if i < 3 else ""
        text += f"{medal} *{name}* — {count} {t(lang, 'referrals_count')}{prize}\n"

    text += f"\n{'─' * 20}\n"
    text += t(lang, "leaderboard_footer")
    if user.id != ADMIN_ID:
        user_count = get_referral_count(user.id)
        text += f"\n\n👤 *{t(lang, 'your_position')}:* {user_count} {t(lang, 'referrals_count')}"
    await update.message.reply_text(text, parse_mode="Markdown")


async def reward_top_referrers(application: Application):
    """Awards top 3 referrers with 30 days free premium."""
    leaderboard = get_monthly_referral_leaderboard()
    for i, (uid, count) in enumerate(leaderboard[:3]):
        if count < 1:
            continue
        set_premium(uid, days=30)
        lang = get_user_lang(uid)
        try:
            await application.bot.send_message(
                chat_id=uid, text=t(lang, "leaderboard_reward", count=count), parse_mode="Markdown",
            )
        except TelegramError:
            pass
    logging.info(f"Monthly rewards: top {min(3, len(leaderboard))} rewarded")


# ─── Daily tips sender (called by scheduler) ─────────────────────────────────

async def send_daily_tips(application: Application):
    """Sends an AI-generated tip to all subscribed users."""
    subscribers = get_all_tips_subscribers()
    if not subscribers:
        return
    import asyncio
    tips_by_lang = {}
    for lang in ["uz", "ru", "en"]:
        ai_tip = await generate_ai_tip(lang)
        if ai_tip:
            tips_by_lang[lang] = ai_tip
        else:
            fallback = random.choice(FALLBACK_TIPS)
            tips_by_lang[lang] = fallback.get(lang, fallback["uz"])
    sent = 0
    failed = 0
    for user_id in subscribers:
        lang = get_user_lang(user_id)
        tip_text = tips_by_lang.get(lang, tips_by_lang.get("uz", ""))
        message = f"{t(lang, 'tip_of_day')}\n\n{tip_text}"
        try:
            await application.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
            sent += 1
        except TelegramError:
            failed += 1
        if (sent + failed) % 25 == 0:
            await asyncio.sleep(1)
    logging.info(f"Daily AI tips sent: {sent} success, {failed} failed")
