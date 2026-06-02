import logging
import re
import random
import requests
from telegram import (
    MenuButtonCommands,
    Update, 
    BotCommand, 
    BotCommandScopeChat, 
    ReactionTypeEmoji, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    Application,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ConversationHandler,
    TypeHandler,
    filters
)
from telegram.error import TelegramError
from telegram.constants import ChatMemberStatus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time
import pytz

# --- CONFIG & DATABASE IMPORTS ---
from config import (
    BOT_TOKEN, ADMIN_ID, REQUIRED_CHANNEL_ID, CHANNEL_INVITE_LINK,
    DAILY_FREE_LIMIT
)

# Config faylingizdan UZS provayder tokenini import qilamiz
try:
    from config import UZS_PROVIDER_TOKEN
except ImportError:
    UZS_PROVIDER_TOKEN = "PROVIDER_TOKEN_NOT_SET"

from database import (
    get_user_lang, set_user_lang, get_group_lang, set_group_lang,
    is_premium, set_premium, get_user_checks, increment_user_checks,
    add_to_history, get_history, add_report, get_stats,
    add_referral, get_referral_count, consume_referral_credit,
    get_group_stats, increment_group_blocked, increment_group_warned,
    is_rate_limited, update_rate_limit, redeem_promocode, create_promocode, load_db
)
from languages import t, gt
try:
    from languages import pt
except ImportError:
    pt = t

from admin import admin_command, admin_callback, broadcast_command, is_admin

# --- CHECKER FRAMEWORK IMPORTS ---
from checker import (check_url, check_url_with_domain_age, check_url_complete,
    check_virustotal, check_google_safe_browsing, check_alienvault, check_urlscan)
from apk_checker import scan_apk
from email_checker import check_email_breach
from qr_checker import extract_qr_url

# --- INITIAL SETUP & LOGGING ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

URL_REGEX = re.compile(r'https?://\S+|www\.\S+')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
REACTIONS = ["❤", "👍", "🔥", "🎉", "⚡"]

# --- SCHEDULER FOR DAILY TIPS & WEEKLY REPORTS ---
scheduler = AsyncIOScheduler()

async def send_daily_tips(app: Application):
    """Foydalanuvchilarga har kuni xavfsizlik bo'yicha maslahatlar yuborish"""
    pass

async def send_weekly_reports(app: Application):
    """Guruhlarga haftalik hisobotlarni yuborish"""
    pass

# --- SUBSCRIPTION CHECKER ---
async def is_user_subscribed(application: Application, user_id: int) -> bool:
    """Foydalanuvchi majburiy kanalga a'zo ekanligini tekshirish"""
    try:
        member = await application.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]
    except TelegramError:
        return False

# --- MENU TRANSLATION HOOK ---
async def setup_menu(application: Application):
    """Bot menyu tugmalarini va buyruqlarini sozlash"""
    public_commands = [
        BotCommand("start", "🚀 Botni ishga tushirish"),
        BotCommand("language", "🌐 Tilni o'zgartirish (Language)"),
        BotCommand("breach", "🔐 Email leak check (Premium)"),
        BotCommand("referral", "👥 Do'stlarni taklif qilish"),
        BotCommand("phish", "🎣 Fishing simulyatori (Xavfsizlik testi)"),
        BotCommand("premium", "⭐ Premium xarid qilish / Promokod"),
        BotCommand("feedback", "📩 Taklif va shikoyatlar"),
        BotCommand("report", "🚨 Xavfli link haqida xabar berish"),
        BotCommand("history", "🕒 Tekshiruvlar tarixi")
    ]
    await application.bot.set_my_commands(public_commands)
    try:
        await application.bot.set_my_default_menu_button(menu_button=MenuButtonCommands())
    except Exception as e:
        print(f"⚠️ Menu button: {e}")
    
    admin_commands = public_commands + [
        BotCommand("stats", "📊 Bot statistikasi (Admin Only)"),
        BotCommand("broadcast", "📢 Hammaga xabar yuborish")
    ]
    try:
        await application.bot.set_my_commands(commands=admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_ID))
        print("✅ Bot menyulari muvaffaqiyatli yuklandi!")
    except Exception as e:
        print(f"⚠️ Menyu sozlashda xatolik: {e}")

# --- COMMAND HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    
    try:
        await update.message.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])
    except TelegramError:
        pass

    # Start argumentlarini tekshirish (Referral yoki Fishing)
    if context.args:
        args_text = context.args[0]
        
        # Fishing Simulyatsiyasi Bosilganda
        if args_text.startswith("phish_"):
            creator_id = int(args_text.split("_")[1])
            if creator_id == user.id:
                await update.message.reply_text("🎣 Bu sizning shaxsiy fishing testingiz. Uni do'stlaringizga yuboring!")
                return

            warning_text = (
                "🚨 *DIQQAT! Siz fishing tuzog'iga tushdingiz!*\n\n"
                "Xavotir olmang, bu shunchaki do'stingiz tomonidan yuborilgan *SafeLink Bot* xavfsizlik testi edi. "
                "Lekin real hayotda bu haqiqiy skamer bo'lishi va barcha parollaringizni o'g'irlashi mumkin edi!\n\n"
                "🛡 Internetda doim hushyor bo'ling va shubhali havolalarni doim bizning bot orqali tekshiring."
            )
            await update.message.reply_text(warning_text, parse_mode="Markdown")
            
            try:
                creator_lang = get_user_lang(creator_id)
                await context.bot.send_message(
                    chat_id=creator_id, 
                    text=t(creator_lang, "phish_alert"), 
                    parse_mode="Markdown"
                )
            except Exception: 
                pass
            return

        # Referral Havola orqali kirilganda
        elif args_text.startswith("ref_") or args_text.isdigit():
            try:
                referrer_id = int(args_text.replace("ref_", ""))
                if referrer_id != user.id:
                    success = add_referral(user.id, referrer_id)
                    if success:
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_id, 
                                text="🎉 Yangi do'st taklif qildingiz! Sizga 1 ta bepul dynamic /breach balansi qo'shildi."
                            )
                        except Exception: 
                            pass
            except Exception: 
                pass

    welcome_text = t(lang, "start", name=user.full_name, limit=DAILY_FREE_LIMIT)
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            InlineKeyboardButton("🇺🇸 English", callback_data=f"{prefix}en")
        ]
    ]
    await update.message.reply_text(
        text=t(get_user_lang(update.effective_user.id), "choose_language") if not is_group else "🌐 Guruh tilini tanlang / Выберите язык группы:",
        reply_markup=InlineKeyboardMarkup(keyboard)
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

async def add_promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bu buyruq faqat bot adminlari uchun.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("🔑 *Syntax:* `/addpromo [kod_nomi] [kunlar] [once/multi]`", parse_mode="Markdown")
        return
    code = context.args[0].strip().upper()
    try: 
        days = int(context.args[1])
    except ValueError: 
        await update.message.reply_text("❌ Kun miqdori butun son bo'lishi kerak.")
        return
    usage_type = context.args[2].strip().lower()
    create_promocode(code, days, usage_type)
    await update.message.reply_text(f"✅ Promokod muvaffaqiyatli yaratildi: `{code}` ({days} kun, turi: {usage_type})", parse_mode="Markdown")

async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    if not context.args:
        await update.message.reply_text(text=t(lang, "promo_usage"), parse_mode="Markdown")
        return
    input_code = context.args[0].strip()
    success, msg_key = redeem_promocode(user.id, input_code)
    if success:
        await update.message.reply_text(text=t(lang, "promo_success_msg", days=30))
    else:
        await update.message.reply_text(text=t(lang, msg_key))

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    history = get_history(user_id)
    if not history:
        await update.message.reply_text("🕒 Tekshiruvlar tariqingiz hozircha bo'sh.")
        return
    text = "🕒 *Sizning oxirgi 10 ta tekshiruv tariqingiz:*\n\n"
    for item in history[:10]:
        text += f"• `{item.get('url', '')}` ➔ {item.get('status', '')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# Conversation state for breach
WAITING_BREACH_EMAIL = 1

async def breach_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1 — check access, then ask for email."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    has_premium = is_premium(user.id)
    free_credits = get_referral_credits(user.id)

    if not has_premium and free_credits < 1:
        keyboard = [[InlineKeyboardButton("⭐ Premium olish", callback_data="pay_p1m_stars")]]
        await update.message.reply_text(
            t(lang, "breach_premium_required", credits=0),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    note = f"\n💳 Sizda {free_credits} ta bepul tekshiruv bor." if not has_premium else ""
    await update.message.reply_text(
        f"🔐 *Email Breach Tekshiruvi*{note}\n\n📧 Emailingizni yuboring:",
        parse_mode="Markdown"
    )
    return WAITING_BREACH_EMAIL


async def breach_receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2 — receive email, validate, check API."""
    user = update.effective_user
    lang = get_user_lang(user.id)
    email = update.message.text.strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        await update.message.reply_text(
            f"❌ Noto\'g\'ri email format.\nMasalan: `user@gmail.com`\n\nQayta yuboring:",
            parse_mode="Markdown"
        )
        return WAITING_BREACH_EMAIL

    has_premium = is_premium(user.id)
    status_msg = await update.message.reply_text(t(lang, "breach_checking"))

    try:
        import aiohttp as _aiohttp
        async with _aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.xposedornot.com/v1/check-email/{email}",
                timeout=_aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw = data.get("breaches", [])
                    breaches_list = raw[0] if raw and isinstance(raw[0], list) else raw
                    if breaches_list:
                        breaches_text = "\n".join([f"• *{b}*" for b in breaches_list[:5]])
                        result = t(lang, "breach_compromised",
                                   email=email, count=len(breaches_list), breaches=breaches_text)
                    else:
                        result = t(lang, "breach_safe", email=email)
                else:
                    result = t(lang, "breach_safe", email=email)

        await status_msg.edit_text(result, parse_mode="Markdown")
        if not has_premium:
            consume_referral_credit(user.id)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ API xatoligi: {str(e)}")

    return ConversationHandler.END


async def breach_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.")
    return ConversationHandler.END

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    if not context.args:
        await update.message.reply_text(t(lang, "feedback_usage"), parse_mode="Markdown")
        return
    feedback_text = " ".join(context.args).strip()
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"📩 *Yangi taklif/shikoyat:*\nKimdan: {user.full_name} (`{user.id}`)\nMatn: {feedback_text}", 
            parse_mode="Markdown"
        )
        await update.message.reply_text(t(lang, "feedback_received"))
    except Exception: 
        await update.message.reply_text("❌ Xabarni adminlarga yuborib bo'lmadi.")
        
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚨 *Xavfli havola haqida xabar:* \nUser: {user.id}\nLink: {url_to_report}", parse_mode="Markdown")
    except Exception: 
        pass
    await update.message.reply_text(t(lang, "report_sent"))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    try:
        stats_data = get_stats()
        users_count = stats_data[0] if isinstance(stats_data, (tuple, list)) else "X"
    except Exception: 
        users_count = "X"
    await update.message.reply_text(f"📊 *Bot statistikasi:*\nJami foydalanuvchilar: {users_count}", parse_mode="Markdown")

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    count = get_referral_count(user.id)
    await update.message.reply_text(text=t(lang, "referral_link", ref_code=user.id, count=count), parse_mode="Markdown", disable_web_page_preview=True)

async def phish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    test_link = f"https://t.me/{context.bot.username}?start=phish_{user.id}"
    await update.message.reply_text(text=t(lang, "phish_created", link=test_link), parse_mode="Markdown")

# --- MULTI-PROVIDER PREMIUM PAYMENT SYSTEM (STARS + SO'M) ---
async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if is_premium(user_id):
        await update.message.reply_text("⭐ Sizda allaqachon Premium status faol!")
        return

    keyboard = [
        [InlineKeyboardButton("⭐ Telegram Stars (75 XTR)", callback_data="pay_stars")],
        [InlineKeyboardButton("💳 Payme / Click (29,990 So'm)", callback_data="pay_som")]
    ]
    await update.message.reply_text(
        "⚡ *SafeLink Premium obunasi!*\n\n"
        "Premium afzalliklari:\n"
        "• Cheksiz havolalarni tekshirish\n"
        "• To'liq /breach leak ma'lumotlar bazasidan foydalanish\n"
        "• Reklamasiz va yuqori tezlikdagi tahlil\n\n"
        "To'lov usulini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def payment_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "pay_stars":
        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Premium - 30 kunlik (Stars)",
            description="Telegram Stars orqali 30 kunlik Premium obuna",
            payload="premium_stars_30",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("Premium Stars", 75)]
        )
    elif query.data == "pay_som":
        # 29,990 UZS ni tiyin ko'rinishida yozamiz (29990 * 100)
        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Premium - 30 kunlik (So'm)",
            description="To'lov provayderi orqali 30 kunlik Premium obuna",
            payload="premium_som_30",
            provider_token=UZS_PROVIDER_TOKEN,
            currency="UZS",
            prices=[LabeledPrice("Premium UZS", 2999000)]
        )

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def payment_success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    set_premium(user_id)
    try: 
        await update.message.set_reaction([ReactionTypeEmoji(emoji="🎉")])
    except TelegramError: 
        pass
    await update.message.reply_text("🎉 *To'lov muvaffaqiyatli yakunlandi!* Sizga 30 kunlik Premium status taqdim etildi.", parse_mode="Markdown")

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = get_user_lang(user.id)
    
    if await is_user_subscribed(context.application, user.id):
        await query.message.delete()
        await context.bot.send_message(chat_id=user.id, text=t(lang, "start", name=user.first_name, limit=DAILY_FREE_LIMIT), parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=user.id, text=t(lang, "sub_failed"))
        
# --- ORIGINAL 800-LINE FULL MESSAGE PROCESSING LOGIC ---
async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_user_lang(user.id)
    text = update.message.text or ""
    
    # Majburiy obunani tekshirish
    if not await is_user_subscribed(context.application, user.id):
        keyboard = [
            [InlineKeyboardButton(t(lang, "sub_button"), url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton(t(lang, "sub_check_btn"), callback_data="check_subscription")]
        ]
        await update.message.reply_text(text=t(lang, "sub_required"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # Matn ichidan linklarni qidirish
    url_match = URL_REGEX.search(text)
    if not url_match:
        await update.message.reply_text(t(lang, "start", name=user.first_name, limit=DAILY_FREE_LIMIT), parse_mode="Markdown")
        return

    url = url_match.group(0)

    # Premium bo'lmagan foydalanuvchilar uchun kunlik limitni tekshirish
    if not is_premium(user.id):
        checks = get_user_checks(user.id)
        if checks >= DAILY_FREE_LIMIT:
            await update.message.reply_text(t(lang, "limit_reached", limit=DAILY_FREE_LIMIT))
            return
        increment_user_checks(user.id)

    status_msg = await update.message.reply_text(t(lang, "checking"))

    # Barcha 4 ta API orqali chuqur tekshiruv
    try:
        import asyncio
        vt_res, gsb_res, alien_res, uscan_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url),
            check_alienvault(url),
            check_urlscan(url),
        )
        domain_res = await check_url_with_domain_age(url)

        is_dangerous = (
            gsb_res.get("dangerous", False) or
            vt_res.get("malicious", 0) > 0 or
            alien_res.get("dangerous", False) or
            uscan_res.get("verdict") == "malicious"
        )
        status_str = "🔴 Malicious" if is_dangerous else "🟢 Clean"
        add_to_history(user.id, url, status_str)

        report  = f"🛡 *SafeLink Ko\'p Qatlamli Tahlil:*\n\n"
        report += f"🔗 *URL:* `{url}`\n"
        report += f"📊 *Xulosa:* {'🚨 XAVFLI' if is_dangerous else '✅ XAVFSIZ'}\n\n"
        report += f"🔍 *VirusTotal:* `{vt_res.get('malicious', 0)}/{vt_res.get('total', 0)}` tahdid\n"
        report += f"🌐 *Google Safe Browsing:* {'❌ Xavfli' if gsb_res.get('dangerous') else '✅ Toza'}\n"
        report += f"👽 *AlienVault OTX:* `{alien_res.get('pulses_count', 0)}` tahdid guruhi\n"
        report += f"📸 *URLScan.io:* `{str(uscan_res.get('verdict', 'unknown')).upper()}` (skor: {uscan_res.get('score', 0)}/100)\n"

        if domain_res and "age_days" in domain_res:
            age = domain_res.get("age_days", 0)
            report += f"📅 *Domen yoshi:* `{age} kun` ({domain_res.get('created', 'N/A')})\n"
            if age < 30:
                report += f"⚠️ *Juda yangi domen! Fishing bo\'lishi mumkin!*\n"

        await status_msg.edit_text(text=report, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Havolani tekshirishda xatolik: {e}")
        await status_msg.edit_text("❌ Havolani tahlil qilish jarayonida xatolik yuz berdi.")
        
async def handle_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    doc = update.message.document

    # Tezlik cheklovini (Rate limiting) tekshirish
    limited, seconds = is_rate_limited(user_id)
    if limited:
        await update.message.reply_text(t(lang, "rate_limited", seconds=seconds))
        return
    update_rate_limit(user_id)

    if not (doc.file_name or "").lower().endswith(".apk"): 
        return

    # Maksimal hajm tekshiruvi (32 MB)
    if doc.file_size > 32 * 1024 * 1024:
        await update.message.reply_text("❌ APK fayl hajmi juda katta. Maksimal limit 32 MB.")
        return

    status_msg = await update.message.reply_text("🔍 *APK fayl tahlil qilinmoqda, kuting...*", parse_mode="Markdown")
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        result = await scan_apk(bytes(file_bytes), doc.file_name)
        
        if result.get("success"):
            mal = result.get("malicious", 0)
            sus = result.get("suspicious", 0)
            total = result.get("total", 0)
            
            if mal > 0:
                await status_msg.edit_text(f"🚨 *Zararli APK aniqlandi!* (Virus)\n📦 Nomi: `{doc.file_name}`\nAniqlovchi dvigatellar: `{mal}/{total}`", parse_mode="Markdown")
            elif sus > 0:
                await status_msg.edit_text(f"⚠️ *Shubhali APK activity!* \n📦 Nomi: `{doc.file_name}`\nShubhali qismlar: `{sus}/{total}`", parse_mode="Markdown")
            else:
                await status_msg.edit_text(f"✅ *Xavfsiz APK!* Zararli kodlar aniqlanmadi.\n📦 Nomi: `{doc.file_name}`", parse_mode="Markdown")
        else:
            await status_msg.edit_text("❌ VirusTotal API orqali APK faylni tekshirib bo'lmadi.")
    except Exception as e: 
        logging.error(f"APK error: {e}")
        await status_msg.edit_text("❌ APK tahlili jarayonida xatolik yuz berdi.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    limited, seconds = is_rate_limited(user_id)
    if limited:
        await update.message.reply_text(t(lang, "rate_limited", seconds=seconds))
        return
    update_rate_limit(user_id)

    photo = update.message.photo[-1]
    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        url = extract_qr_url(bytes(photo_bytes))
        
        if not url:
            await update.message.reply_text("🔍 Ushbu rasmdan hech qanday QR-kod yoki havola topilmadi.")
            return
            
        status_msg = await update.message.reply_text(f"🔗 *QR-kod ichidan havola topildi:* `{url}`\nUni tahlil qilmoqdaman...", parse_mode="Markdown")
        
        # QR ichidagi linkni chuqur tekshirish
        vt_res = await check_virustotal(url)
        gsb_res = await check_google_safe_browsing(url)
        is_dangerous = gsb_res.get("dangerous", False) or vt_res.get("malicious", 0) > 0
        
        report = f"🛡 *QR-kod ichidagi havola hisoboti:*\n\n`{url}`\n\n"
        report += f"Holati: {'🚨 ZARARLI/FISHING' if is_dangerous else '✅ TOZA'}\n"
        report += f"VirusTotal tahlili: {vt_res.get('malicious', 0)} ta dvigatel xavf aniqladi."
        
        await status_msg.edit_text(report, parse_mode="Markdown")
    except Exception as e: 
        logging.error(f"QR error: {e}")
        await update.message.reply_text("❌ QR-kodni tahlil qilib o'qishda xatolik yuz berdi.")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text: 
        return
    urls = URL_REGEX.findall(message.text)
    if not urls: 
        return
        
    lang = get_group_lang(message.chat_id)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    for url in urls:
        vt = await check_virustotal(url)
        gsb = await check_google_safe_browsing(url)
        
        if gsb.get("dangerous") or vt.get("malicious", 0) > 0:
            try:
                await message.delete()
                await context.bot.send_message(
                    chat_id=message.chat_id, 
                    text=gt(lang, "dangerous_deleted", mention=mention, url=url, engines=vt.get("malicious", 0)), 
                    parse_mode="Markdown"
                )
                increment_group_blocked(message.chat_id)
            except TelegramError: 
                await message.reply_text(gt(lang, "dangerous_no_permission", mention=mention, url=url), parse_mode="Markdown")
            break

# --- BOT MAIN START ---

# ─── GROUP APK & QR HANDLERS ─────────────────────────────────────────────────

async def handle_group_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scans APK files sent in groups."""
    message = update.message
    if not message or not message.document:
        return

    doc = message.document
    file_name = doc.file_name or "file.apk"
    mime_type = doc.mime_type or ""
    is_apk = (file_name.lower().endswith(".apk") or
              mime_type == "application/vnd.android.package-archive")
    if not is_apk:
        return

    lang = get_group_lang(message.chat_id)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    if doc.file_size > 32 * 1024 * 1024:
        await message.reply_text(at(lang, "too_large"))
        return

    status_msg = await message.reply_text(at(lang, "scanning"), parse_mode="Markdown")

    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        from apk_checker import scan_apk
        result = await scan_apk(bytes(file_bytes), file_name)
    except Exception:
        await status_msg.edit_text("❌ APK tekshirishda xatolik.")
        return

    if not result.get("success"):
        await status_msg.edit_text(at(lang, "timeout") if result.get("timeout") else at(lang, "error"))
        return

    mal = result["malicious"]
    sus = result["suspicious"]
    total = result["total"]

    if mal > 0:
        try:
            await message.delete()
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=f"🚨 *XAVFLI APK BLOKLANDI!*\n\n"
                 f"👤 {mention}\n"
                 f"📱 Fayl: `{file_name}`\n"
                 f"{mal}/{total} antivirus xavfli deb topdi!\n"
                 f"❌ Bu ilovani O'RNATMANG!",
            parse_mode="Markdown"
        )
    elif sus > 0:
        await status_msg.edit_text(
            at(lang, "suspicious", sus=sus, total=total, name=file_name),
            parse_mode="Markdown"
        )
    else:
        await status_msg.edit_text(
            at(lang, "safe", total=total, name=file_name),
            parse_mode="Markdown"
        )


async def handle_group_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scans QR codes sent as photos in groups."""
    message = update.message
    if not message or not message.photo:
        return

    lang = get_group_lang(message.chat_id)
    photo = message.photo[-1]

    try:
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        from qr_checker import extract_qr_url
        url = extract_qr_url(bytes(photo_bytes))
    except Exception:
        return

    if not url:
        return  # Not a QR code, ignore

    status_msg = await message.reply_text(
        f"📸 QR kod aniqlandi, tekshirilmoqda...",
        parse_mode="Markdown"
    )

    try:
        import asyncio
        vt_res, gsb_res = await asyncio.gather(
            check_virustotal(url),
            check_google_safe_browsing(url)
        )
        is_dangerous = gsb_res.get("dangerous") or vt_res.get("malicious", 0) > 0
        mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

        if is_dangerous:
            try:
                await message.delete()
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"🚨 *XAVFLI QR KOD BLOKLANDI!*\n\n"
                     f"👤 {mention}\n"
                     f"🔗 URL: `{url}`\n"
                     f"Bu QR kodga ishonmang!",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(
                f"📸 QR kod URL: `{url}`\n\n✅ Xavfsiz ko'rinadi.",
                parse_mode="Markdown"
            )
    except Exception:
        await status_msg.edit_text("❌ QR kod tekshirishda xatolik.")


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(setup_menu).build()

    # --- COMMAND HANDLERS ---
    app.add_handler(CommandHandler("start",    start_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("promo",    promo_command))
    app.add_handler(CommandHandler("addpromo", add_promo_command))
    breach_conv = ConversationHandler(
        entry_points=[CommandHandler("breach", breach_command)],
        states={
            WAITING_BREACH_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, breach_receive_email)
            ]
        },
        fallbacks=[CommandHandler("cancel", breach_cancel)],
        per_user=True,
        per_chat=True,
    )
    app.add_handler(breach_conv)
    app.add_handler(CommandHandler("report",   report_command))
    app.add_handler(CommandHandler("stats",    stats_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("premium",  premium_command))
    app.add_handler(CommandHandler("admin",    admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("phish",    phish_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("history",  history_command))
    
    # --- CALLBACK QUERY HANDLERS ---
    app.add_handler(CallbackQueryHandler(admin_callback,              pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(language_callback,           pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(group_language_callback,     pattern="^glang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(payment_gateway_callback,    pattern="^pay_"))
    
    # --- PRE-CHECKOUT & SUCCESSFUL PAYMENTS ---
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    # --- MULTIMEDIA & TEXT PROCESSING HANDLERS ---
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, handle_apk))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    # Group APK and QR scanning
    app.add_handler(MessageHandler(
        filters.Document.ALL & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_group_apk
    ))
    app.add_handler(MessageHandler(
        filters.PHOTO & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
        handle_group_photo
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP), handle_group_message))

    print("🚀 SafeLink Bot barcha mantiqiy funksiyalari bilan muvaffaqiyatli ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
