"""
Command handlers for basic bot commands:
/start, /language, /history, /feedback, /report, /stats, /referral, /phish
Plus new advanced commands:
/expand, /ssl, /redirect, /typo, /scammer, /privacy
"""
import random
from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import ADMIN_ID, DAILY_FREE_LIMIT, CHANNEL_INVITE_LINK
from database import (
    get_user_lang, set_user_lang, get_group_lang, set_group_lang,
    get_history, add_referral, get_referral_count, add_report,
)
from languages import t, gt
from admin import is_admin
from handlers.tools import (
    expand_short_url, check_ssl_certificate, get_redirect_chain,
    check_typosquatting, check_social_account, check_privacy_score,
)

REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡", "👏", "🤩", "💯"]


async def react_to_message(message):
    """Give a random reaction to any user message."""
    try:
        await message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass


# ─── Subscription helper (imported in other modules too) ──────────────────────

async def _require_sub(update, context):
    """Lazy import to avoid circular dependency."""
    from handlers.private_messages import require_subscription
    return await require_subscription(update, context)


# ─── /start ──────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)

    await react_to_message(update.message)

    # Start arguments (Referral or Phishing test)
    if context.args:
        args_text = context.args[0]

        # Phishing simulation click
        if args_text.startswith("phish_"):
            try:
                creator_id = int(args_text.split("_")[1])
            except (IndexError, ValueError):
                pass
            else:
                if creator_id == user.id:
                    await update.message.reply_text(
                        "🎣 Bu sizning shaxsiy fishing testingiz. Uni do'stlaringizga yuboring!"
                    )
                    return

                warning_text = (
                    "🚨 *DIQQAT! Siz fishing tuzog'iga tushdingiz!*\n\n"
                    "Xavotir olmang, bu shunchaki do'stingiz tomonidan yuborilgan "
                    "*Xavfsizmi? Bot* xavfsizlik testi edi. "
                    "Lekin real hayotda bu haqiqiy skamer bo'lishi va barcha "
                    "parollaringizni o'g'irlashi mumkin edi!\n\n"
                    "🛡 *Qanday himoyalanish kerak:*\n"
                    "• Notanish havolalarni hech qachon bosmang\n"
                    "• Shubhali linkni avval @XavfsizmiBot orqali tekshiring\n"
                    "• 2-bosqichli autentifikatsiyani yoqing\n"
                    "• Parollarni har 3 oyda yangilang\n\n"
                    "💡 Siz ham do'stlaringizni sinab ko'ring: /phish"
                )
                await update.message.reply_text(warning_text, parse_mode="Markdown")

                try:
                    creator_lang = get_user_lang(creator_id)
                    await context.bot.send_message(
                        chat_id=creator_id,
                        text=t(creator_lang, "phish_alert", name=user.first_name),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
                return

        # Referral link
        elif args_text.startswith("ref_") or args_text.isdigit():
            try:
                referrer_id = int(args_text.replace("ref_", ""))
                if referrer_id != user.id:
                    success = add_referral(user.id, referrer_id)
                    if success:
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text="🎉 Yangi do'st taklif qildingiz! "
                                     "Sizga 1 ta bepul /breach tekshiruv balansi qo'shildi."
                            )
                        except Exception:
                            pass
            except (ValueError, Exception):
                pass

    welcome_text = t(lang, "start", name=user.full_name, limit=DAILY_FREE_LIMIT)
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─── /language ────────────────────────────────────────────────────────────────

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)

    is_group = update.effective_chat.type in ["group", "supergroup"]
    if is_group:
        user_id = update.effective_user.id
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❗ Faqat guruh adminlari tilni o'zgartira oladi.")
            return
        prefix = "glang_"
    else:
        prefix = "lang_"

    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data=f"{prefix}uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data=f"{prefix}ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data=f"{prefix}en"),
        ]
    ]
    text = (
        t(get_user_lang(update.effective_user.id), "choose_language")
        if not is_group
        else "🌐 Guruh tilini tanlang / Выберите язык группы:"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    set_user_lang(query.from_user.id, lang)
    await query.edit_message_text(t(lang, "language_set"), parse_mode="Markdown")


async def group_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("glang_", "")
    set_group_lang(query.message.chat_id, lang)
    await query.edit_message_text(gt(lang, "language_set"), parse_mode="Markdown")


# ─── /history ─────────────────────────────────────────────────────────────────

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    history = get_history(user_id)

    if not history:
        await update.message.reply_text(t(lang, "history_empty"))
        return

    text = t(lang, "history_title") + "\n"
    for item in history[:10]:
        text += f"• `{item.get('url', '')[:40]}` — {item.get('status', '')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /feedback ────────────────────────────────────────────────────────────────

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "feedback_usage"), parse_mode="Markdown")
        return

    feedback_text = " ".join(context.args).strip()
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 *Yangi taklif/shikoyat:*\n"
                 f"Kimdan: {user.full_name} (`{user.id}`)\n"
                 f"Matn: {feedback_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text(t(lang, "feedback_received"))
    except Exception:
        await update.message.reply_text("❌ Xabarni adminlarga yuborib bo'lmadi.")


# ─── /report ──────────────────────────────────────────────────────────────────

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "report_usage"), parse_mode="Markdown")
        return

    url_to_report = context.args[0].strip()
    try:
        add_report(user.id, url_to_report)
    except Exception:
        pass
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 *Xavfli havola haqida xabar:*\nUser: {user.id}\nLink: {url_to_report}",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    await update.message.reply_text(t(lang, "report_sent"))


# ─── /stats ───────────────────────────────────────────────────────────────────

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if update.effective_user.id != ADMIN_ID:
        return
    from database import get_stats
    try:
        stats_data = get_stats()
        text = (
            f"📊 *Bot statistikasi:*\n"
            f"Jami foydalanuvchilar: {stats_data['total_users']}\n"
            f"Premium: {stats_data['total_premium']}\n"
            f"Hisobotlar: {stats_data['total_reports']}"
        )
    except Exception:
        text = "📊 *Bot statistikasi:* Ma'lumotlarni olishda xatolik."
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── /referral ────────────────────────────────────────────────────────────────

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(
        text=t(lang, "referral_link", ref_code=user.id, count=count),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ─── /phish (Upgraded — realistic phishing simulation) ───────────────────────

PHISH_TEMPLATES = [
    {
        "type": "bank",
        "uz": "🏦 Diqqat! Sizning kartangizdan 1,500,000 so'm yechilmoqda. Bekor qilish uchun bosing:",
        "ru": "🏦 Внимание! С вашей карты списывается 1,500,000 сум. Для отмены нажмите:",
        "en": "🏦 Alert! $150 is being withdrawn from your card. Cancel here:",
    },
    {
        "type": "prize",
        "uz": "🎁 Tabriklaymiz! Siz 5,000,000 so'm yutdingiz! Sovg'angizni olish uchun:",
        "ru": "🎁 Поздравляем! Вы выиграли 5,000,000 сум! Получить приз:",
        "en": "🎁 Congratulations! You won $500! Claim your prize:",
    },
    {
        "type": "account",
        "uz": "⚠️ Sizning Telegram akkauntingiz bloklanmoqda! Tasdiqlash:",
        "ru": "⚠️ Ваш аккаунт Telegram будет заблокирован! Подтвердите:",
        "en": "⚠️ Your Telegram account is being suspended! Verify now:",
    },
    {
        "type": "delivery",
        "uz": "📦 Sizga jo'natma keldi! Kuzatish raqami: UZ7839. Ma'lumot:",
        "ru": "📦 У вас посылка! Номер отслеживания: RU7839. Подробнее:",
        "en": "📦 You have a package! Tracking: EN7839. Details:",
    },
    {
        "type": "password",
        "uz": "🔒 Kimdir akkauntingizga kirmoqchi! Parolni tiklash:",
        "ru": "🔒 Кто-то пытается войти в ваш аккаунт! Сбросить пароль:",
        "en": "🔒 Someone is trying to access your account! Reset password:",
    },
]


async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)
    bot_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"

    template = random.choice(PHISH_TEMPLATES)
    phish_text = template.get(lang, template["uz"])

    response = (
        f"🎣 Fishing Simulyatsiya Yaratildi!\n\n"
        f"Quyidagi xabarni do'stingizga yuboring:\n\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{phish_text}\n"
        f"{bot_link}\n\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"📋 Yuqoridagi matnni nusxalab, do'stingizga yuboring.\n"
        f"Agar u havolani bossa — ogohlantirish oladi, siz esa xabar.\n\n"
        f"🔄 Boshqa shablon: /phish"
    )

    await update.message.reply_text(response, disable_web_page_preview=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NEW ADVANCED COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════


# ─── /expand — Short URL Expander ─────────────────────────────────────────────

async def expand_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "expand_usage"), parse_mode="Markdown")
        return

    url = context.args[0].strip()
    status_msg = await update.message.reply_text(t(lang, "checking"))

    result = await expand_short_url(url)

    if result["redirect_count"] == 0:
        text = t(lang, "expand_no_redirect", url=url)
    else:
        hops_text = ""
        for i, hop in enumerate(result["hops"]):
            prefix = "  → " if i > 0 else "🔗 "
            hops_text += f"{prefix}`{hop}`\n"

        text = (
            f"🔀 *URL Kengaytirish Natijasi:*\n\n"
            f"{hops_text}\n"
            f"📍 *Yakuniy manzil:* `{result['final_url']}`\n"
            f"🔢 *Yo'naltirish soni:* {result['redirect_count']}"
        )

    await status_msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── /ssl — SSL Certificate Checker ──────────────────────────────────────────

async def ssl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "ssl_usage"), parse_mode="Markdown")
        return

    url = context.args[0].strip()
    status_msg = await update.message.reply_text(t(lang, "checking"))

    result = await check_ssl_certificate(url)

    if not result.get("valid"):
        text = (
            f"🔓 *SSL Sertifikat Tekshiruvi:*\n\n"
            f"🔗 `{url}`\n\n"
            f"❌ *Holat:* Xavfsiz emas!\n"
            f"⚠️ *Xatolik:* {result.get('error', 'Noma`lum')}\n\n"
            f"🚨 Bu saytga shaxsiy ma'lumot BERMANG!"
        )
    else:
        days = result["days_remaining"]
        if days < 0:
            status_emoji = "🔴 MUDDATI O'TGAN"
        elif days < 30:
            status_emoji = f"🟡 {days} kun qoldi (tez tugaydi!)"
        else:
            status_emoji = f"🟢 {days} kun qoldi"

        text = (
            f"🔒 *SSL Sertifikat Tekshiruvi:*\n\n"
            f"🔗 `{url}`\n\n"
            f"✅ *Holat:* Xavfsiz\n"
            f"🏢 *Beruvchi:* {result['issuer']}\n"
            f"📛 *Domen:* {result['common_name']}\n"
            f"📅 *Muddati:* {result['expiry']}\n"
            f"⏳ *Qoldi:* {status_emoji}"
        )

    await status_msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── /redirect — Redirect Chain Tracker ──────────────────────────────────────

async def redirect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "redirect_usage"), parse_mode="Markdown")
        return

    url = context.args[0].strip()
    status_msg = await update.message.reply_text(t(lang, "checking"))

    result = await get_redirect_chain(url)

    if result["redirect_count"] == 0:
        text = f"🔗 *Redirect Zanjiri:*\n\n`{url}`\n\n✅ Hech qanday yo'naltirish yo'q. To'g'ridan-to'g'ri ochiladi."
    else:
        text = f"🔗 *Redirect Zanjiri ({result['redirect_count']} qadam):*\n\n"
        for i, hop in enumerate(result["hops"]):
            if i == 0:
                text += f"1️⃣ `{hop}`\n"
            elif i == len(result["hops"]) - 1:
                text += f"🏁 `{hop}` (yakuniy)\n"
            else:
                text += f"  ↓ `{hop}`\n"

        text += f"\n⚠️ Ko'p yo'naltirish = shubhali bo'lishi mumkin!" if result["redirect_count"] > 3 else ""

    await status_msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── /typo — Typosquatting Detector ──────────────────────────────────────────

async def typo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "typo_usage"), parse_mode="Markdown")
        return

    url = context.args[0].strip()
    result = check_typosquatting(url)

    if result.get("exact_match"):
        text = f"✅ *Typosquatting Tekshiruvi:*\n\n`{url}`\n\nBu rasmiy domen: `{result['exact_match']}`"
    elif result.get("is_typosquat"):
        matches_text = ""
        for m in result["matches"]:
            matches_text += f"  • `{m['similar_to']}` (farq: {m['distance']} belgi)\n"
        text = (
            f"🚨 *TYPOSQUATTING ANIQLANDI!*\n\n"
            f"🔗 Tekshirilgan: `{result['domain']}`\n\n"
            f"⚠️ Bu domen quyidagilarga juda o'xshash:\n{matches_text}\n"
            f"🎯 Bu fishing sayt bo'lishi mumkin!\n"
            f"❌ Shaxsiy ma'lumot BERMANG!"
        )
    else:
        text = f"✅ *Typosquatting Tekshiruvi:*\n\n`{result.get('domain', url)}`\n\nHech qanday mashhur domenga o'xshamasligi aniqlandi."

    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── /scammer — Social Media Account Checker ─────────────────────────────────

async def scammer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "scammer_usage"), parse_mode="Markdown")
        return

    username = context.args[0].strip()
    status_msg = await update.message.reply_text(t(lang, "checking"))

    result = await check_social_account(username)

    if result["reports_found"] > 0:
        warnings_text = "\n".join([f"  🚨 {w}" for w in result["warnings"]])
        text = (
            f"⚠️ *Skammer Tekshiruvi:*\n\n"
            f"👤 `@{result['username']}`\n\n"
            f"🚨 *OGOHLANTIRISH topildi!*\n{warnings_text}\n\n"
            f"📊 Tekshirilgan bazalar: {result['sources_checked']}\n"
            f"⚠️ Bu akkaunt bilan ehtiyot bo'ling!"
        )
    else:
        text = (
            f"✅ *Skammer Tekshiruvi:*\n\n"
            f"👤 `@{result['username']}`\n\n"
            f"✅ Hech qanday ogohlantirish topilmadi.\n"
            f"📊 Tekshirilgan bazalar: {result['sources_checked']}\n\n"
            f"⚠️ Eslatma: bu 100% kafolat bermaydi. Doim ehtiyot bo'ling!"
        )

    await status_msg.edit_text(text, parse_mode="Markdown")


# ─── /privacy — Privacy Score ─────────────────────────────────────────────────

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await react_to_message(update.message)
    if not await _require_sub(update, context):
        return

    user = update.effective_user
    lang = get_user_lang(user.id)

    if not context.args:
        await update.message.reply_text(t(lang, "privacy_usage"), parse_mode="Markdown")
        return

    profile_url = context.args[0].strip()
    if not profile_url.startswith("http"):
        profile_url = f"https://{profile_url}"

    status_msg = await update.message.reply_text(t(lang, "checking"))

    result = await check_privacy_score(profile_url)

    if result.get("score", -1) < 0:
        text = f"❌ Profilni tekshirib bo'lmadi: {result.get('error', 'Noma`lum xatolik')}"
    else:
        score = result["score"]
        if score >= 80:
            score_emoji = f"🟢 {score}/100 (Yaxshi himoyalangan)"
        elif score >= 50:
            score_emoji = f"🟡 {score}/100 (O'rtacha)"
        else:
            score_emoji = f"🔴 {score}/100 (Xavfli darajada ochiq!)"

        findings_text = "\n".join([f"  • {f}" for f in result["findings"]])
        recs_text = "\n".join([f"  💡 {r}" for r in result["recommendations"]])

        text = (
            f"🔏 *Maxfiylik Tahlili:*\n\n"
            f"🔗 `{profile_url}`\n\n"
            f"🎯 *Maxfiylik Bali:* {score_emoji}\n\n"
            f"📋 *Topilmalar:*\n{findings_text}\n\n"
            f"💡 *Tavsiyalar:*\n{recs_text}"
        )

    await status_msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)
