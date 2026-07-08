"""
Admin Panel — comprehensive bot management:
- Dashboard with stats, active users, revenue
- User management: lookup, give/remove premium, ban/unban
- Pending Paynet payments
- Group management
- Export data
- Broadcast
- Rate limit dashboard
"""
import json
from datetime import datetime, date, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import ADMIN_ID
from database import (
    get_stats, load_db, save_db, set_premium,
    get_premium_expiry, is_premium, get_user_lang,
    get_history, get_referral_count,
)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def get_all_user_ids() -> list:
    """Get all real user IDs from the database."""
    db = load_db()
    return [
        int(k) for k in db.keys()
        if not k.startswith("group_")
        and k not in ("reports", "url_cache", "promocodes")
        and k.isdigit()
    ]


def get_active_users_count(hours: int = 24) -> int:
    """Count users active in the last N hours."""
    db = load_db()
    today = str(date.today())
    count = 0
    for k in db.keys():
        if k.isdigit():
            if db[k].get("date") == today:
                count += 1
    return count


def get_banned_users() -> list:
    """Get list of banned user IDs."""
    db = load_db()
    return [int(k) for k in db.keys() if k.isdigit() and db[k].get("banned")]


def ban_user(user_id: int):
    db = load_db()
    key = str(user_id)
    if key not in db:
        db[key] = {"lang": "uz", "checks": 0}
    db[key]["banned"] = True
    save_db(db)


def unban_user(user_id: int):
    db = load_db()
    key = str(user_id)
    if key in db:
        db[key].pop("banned", None)
        save_db(db)


def is_banned(user_id: int) -> bool:
    db = load_db()
    key = str(user_id)
    if key not in db:
        return False
    return db[key].get("banned", False)


# ─── /admin COMMAND (main panel) ──────────────────────────────────────────────

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    # Handle subcommands: /admin user 123, /admin ban 123, etc.
    if context.args:
        subcmd = context.args[0].lower()

        # /admin user <id> — lookup a user
        if subcmd == "user" and len(context.args) > 1:
            await _admin_user_lookup(update, context, context.args[1])
            return

        # /admin ban <id>
        elif subcmd == "ban" and len(context.args) > 1:
            try:
                uid = int(context.args[1])
                ban_user(uid)
                await update.message.reply_text(f"🚫 User `{uid}` banned.", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID.")
            return

        # /admin unban <id>
        elif subcmd == "unban" and len(context.args) > 1:
            try:
                uid = int(context.args[1])
                unban_user(uid)
                await update.message.reply_text(f"✅ User `{uid}` unbanned.", parse_mode="Markdown")
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID.")
            return

        # /admin premium <id> <days>
        elif subcmd == "premium" and len(context.args) > 2:
            try:
                uid = int(context.args[1])
                days = int(context.args[2])
                set_premium(uid, days=days)
                await update.message.reply_text(
                    f"⭐ User `{uid}` → {days} days Premium.", parse_mode="Markdown"
                )
            except ValueError:
                await update.message.reply_text("❌ Usage: `/admin premium <user_id> <days>`", parse_mode="Markdown")
            return

        # /admin export — send database file
        elif subcmd == "export":
            await _admin_export(update, context)
            return

    # Main panel with buttons
    stats = get_stats()
    db = load_db()
    active_24h = get_active_users_count(24)
    banned_count = len(get_banned_users())
    groups_count = sum(1 for k in db.keys() if k.startswith("group_"))
    pending_payments = db.get("pending_payments", [])

    text = (
        "🔐 *ADMIN PANEL*\n\n"
        "━━━ *Statistika* ━━━\n"
        f"👥 Jami users: `{stats['total_users']}`\n"
        f"🟢 Faol (24h): `{active_24h}`\n"
        f"⭐ Premium: `{stats['total_premium']}`\n"
        f"🚫 Banned: `{banned_count}`\n"
        f"👥 Guruhlar: `{groups_count}`\n"
        f"🚨 Hisobotlar: `{stats['total_reports']}`\n"
        f"🔗 URL Cache: `{len(db.get('url_cache', {}))}`\n"
        f"💳 Pending payments: `{len(pending_payments)}`\n\n"
        "━━━ *Buyruqlar* ━━━\n"
        "`/admin user <id>` — User ma'lumotlari\n"
        "`/admin ban <id>` — Bloklash\n"
        "`/admin unban <id>` — Blokdan chiqarish\n"
        "`/admin premium <id> <days>` — Premium berish\n"
        "`/admin export` — Bazani yuklab olish\n"
        "`/ratelimit` — API limitlar\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("🚨 Hisobotlar", callback_data="admin_reports"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("💳 Pending Payments", callback_data="admin_payments"),
            InlineKeyboardButton("👥 Guruhlar", callback_data="admin_groups"),
        ],
        [
            InlineKeyboardButton("🚫 Banned list", callback_data="admin_banned"),
            InlineKeyboardButton("🗑 Cache clear", callback_data="admin_clear_cache"),
        ],
        [InlineKeyboardButton("📊 Revenue", callback_data="admin_revenue")],
    ]

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── Admin Callbacks ──────────────────────────────────────────────────────────

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    db = load_db()
    action = query.data

    if action == "admin_reports":
        reports = db.get("reports", [])
        if not reports:
            await query.edit_message_text("📭 Hech qanday hisobot yo'q.")
            return
        text = "🚨 *So'nggi hisobotlar:*\n\n"
        for r in reports[-10:][::-1]:
            text += f"• `{r.get('url', '?')}`\n  📅 {r.get('date', '?')} | 👤 {r.get('user_id', '?')}\n\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_users":
        users = get_all_user_ids()
        active = get_active_users_count(24)
        premium_count = sum(1 for k in db.keys() if k.isdigit() and is_premium(int(k)))
        text = (
            f"👥 *Foydalanuvchilar:*\n\n"
            f"📊 Jami: `{len(users)}`\n"
            f"🟢 Faol (bugun): `{active}`\n"
            f"⭐ Premium: `{premium_count}`\n"
            f"🆓 Bepul: `{len(users) - premium_count}`\n"
            f"🚫 Banned: `{len(get_banned_users())}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_groups":
        groups = {k: v for k, v in db.items() if k.startswith("group_")}
        if not groups:
            await query.edit_message_text("📭 Guruhlar yo'q.")
            return
        text = f"👥 *Guruhlar ({len(groups)}):*\n\n"
        for gid, gdata in list(groups.items())[:10]:
            chat_id = gid.replace("group_", "")
            premium_status = "⭐" if gdata.get("premium_until") else "🆓"
            blocked = gdata.get("blocked", 0)
            text += f"{premium_status} `{chat_id}` — blocked: {blocked}\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_payments":
        # Show pending Paynet payments (stored by premium.py)
        pending = db.get("pending_payments", [])
        if not pending:
            await query.edit_message_text("💳 Kutilayotgan to'lovlar yo'q.")
            return
        text = "💳 *Pending Paynet Payments:*\n\n"
        for p in pending[-10:][::-1]:
            text += (
                f"👤 `{p.get('user_id', '?')}` | 💰 {p.get('price', '?')}\n"
                f"🧾 `{p.get('receipt', '?')}` | 📅 {p.get('date', '?')}\n\n"
            )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_banned":
        banned = get_banned_users()
        if not banned:
            await query.edit_message_text("✅ Bloklangan userlar yo'q.")
            return
        text = "🚫 *Banned Users:*\n\n"
        for uid in banned[:20]:
            text += f"• `{uid}`\n"
        text += f"\nUnban: `/admin unban <id>`"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_revenue":
        # Count successful payments from database
        total_stars = 0
        total_paynet = 0
        premium_users = []
        for k in db.keys():
            if k.isdigit() and db[k].get("premium_until"):
                premium_users.append(k)
        # Estimate revenue from premium count
        text = (
            f"💰 *Revenue Dashboard:*\n\n"
            f"⭐ Premium users: `{len(premium_users)}`\n"
            f"💳 Pending Paynet: `{len(db.get('pending_payments', []))}`\n\n"
            f"📊 *Estimated:*\n"
            f"• If all paid Stars (25): ~`{len(premium_users) * 25}` Stars\n"
            f"• Monthly potential: ~`{get_active_users_count(24) * 30 * 0.05:.0f}` Stars\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "admin_clear_cache":
        db["url_cache"] = {}
        save_db(db)
        await query.edit_message_text("✅ URL cache tozalandi!")

    elif action.startswith("admin_give_prem_"):
        uid = int(action.replace("admin_give_prem_", ""))
        set_premium(uid, days=30)
        await query.edit_message_text(f"⭐ User `{uid}` → +30 days Premium.", parse_mode="Markdown")
        try:
            user_lang = get_user_lang(uid)
            from languages import t
            await context.bot.send_message(
                chat_id=uid,
                text=t(user_lang, "premium_success_with_days", days=30),
                parse_mode="Markdown"
            )
        except Exception:
            pass

    elif action.startswith("admin_ban_"):
        uid = int(action.replace("admin_ban_", ""))
        ban_user(uid)
        await query.edit_message_text(f"🚫 User `{uid}` banned.", parse_mode="Markdown")


# ─── User Lookup ──────────────────────────────────────────────────────────────

async def _admin_user_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id_str: str):
    """Show detailed info about a specific user."""
    try:
        uid = int(user_id_str)
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    db = load_db()
    key = str(uid)

    if key not in db:
        await update.message.reply_text(f"❌ User `{uid}` not found in database.", parse_mode="Markdown")
        return

    user_data = db[key]

    # Try to get user name from Telegram
    try:
        chat = await context.bot.get_chat(uid)
        name = chat.full_name or f"User {uid}"
        username = f"@{chat.username}" if chat.username else "—"
    except Exception:
        name = f"User {uid}"
        username = "—"

    premium_status = "⭐ Active" if is_premium(uid) else "🆓 Free"
    expiry = get_premium_expiry(uid)
    expiry_text = expiry[:10] if expiry else "—"
    banned_status = "🚫 BANNED" if user_data.get("banned") else "✅ Normal"
    lang = user_data.get("lang", "uz")
    referrals = get_referral_count(uid)
    checks_today = user_data.get("checks", 0)
    history = get_history(uid)
    monitored = len(user_data.get("monitored_emails", []))
    tips = "✅" if user_data.get("tips_enabled", True) else "❌"

    text = (
        f"👤 *User Info:*\n\n"
        f"🆔 ID: `{uid}`\n"
        f"📛 Name: {name}\n"
        f"👤 Username: {username}\n"
        f"🌐 Lang: `{lang}`\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ Premium: {premium_status}\n"
        f"📅 Expiry: `{expiry_text}`\n"
        f"🚫 Status: {banned_status}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🔍 Checks today: `{checks_today}`\n"
        f"📋 History: `{len(history)}` items\n"
        f"👥 Referrals: `{referrals}`\n"
        f"📡 Monitored emails: `{monitored}`\n"
        f"💡 Tips: {tips}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("⭐ +30 Premium", callback_data=f"admin_give_prem_{uid}"),
            InlineKeyboardButton("🚫 Ban", callback_data=f"admin_ban_{uid}"),
        ],
    ]

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ─── Export Database ──────────────────────────────────────────────────────────

async def _admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the database file to admin."""
    import os
    from database import DB_FILE

    if os.path.exists(DB_FILE):
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(DB_FILE, "rb"),
            filename=f"xavfsizmi_backup_{date.today()}.json",
            caption="📦 Database export",
        )
    else:
        await update.message.reply_text("❌ Database file not found.")


# ─── Rate Limit Dashboard ─────────────────────────────────────────────────────

async def ratelimit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows API rate limit dashboard to admin."""
    if not is_admin(update.effective_user.id):
        return

    from rate_tracker import get_usage_dashboard
    text = get_usage_dashboard()
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── Broadcast ────────────────────────────────────────────────────────────────

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text(
            "📢 *Broadcast:*\n`/broadcast Xabar matni`",
            parse_mode="Markdown"
        )
        return

    message_text = " ".join(context.args)
    broadcast_msg = f"📢 *Xavfsizmi? Bot:*\n\n{message_text}"

    all_users = get_all_user_ids()
    status_msg = await update.message.reply_text(f"📤 0/{len(all_users)}")

    success = 0
    failed = 0

    for uid in all_users:
        if is_banned(uid):
            continue
        try:
            await context.bot.send_message(chat_id=uid, text=broadcast_msg, parse_mode="Markdown")
            success += 1
        except TelegramError:
            failed += 1

        if (success + failed) % 10 == 0:
            try:
                await status_msg.edit_text(f"📤 {success + failed}/{len(all_users)}")
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ *Broadcast done!*\n✔️ Sent: `{success}`\n❌ Failed: `{failed}`",
        parse_mode="Markdown"
    )
