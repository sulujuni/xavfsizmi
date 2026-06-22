"""
Phase 2 Database Layer — SQLite with async support (aiosqlite).
Drop-in replacement for the old JSON-based database.
All public function signatures are preserved for backward compatibility.
"""

import os
import asyncio
import aiosqlite
from datetime import date, datetime, timedelta
from typing import Optional

# ─── CONFIG ───────────────────────────────────────────────────────────────────

DB_PATH = os.getenv("DB_PATH", "/data/safelink.db") if os.path.exists("/data") else "safelink.db"
RATE_LIMIT_SECONDS = 30
CACHE_EXPIRE_HOURS = 24

_rate_limit_cache: dict[int, float] = {}
_db_lock = asyncio.Lock()


# ─── DATABASE INITIALIZATION ──────────────────────────────────────────────────

async def init_db():
    """Create tables if they don't exist. Call once at startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz',
                checks_today INTEGER DEFAULT 0,
                checks_date TEXT,
                premium_until TEXT,
                referred_by INTEGER,
                referral_credits INTEGER DEFAULT 0,
                secretary_mode INTEGER DEFAULT 0,
                business_connection_id TEXT,
                business_secretary INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                checked_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                reason TEXT,
                reported_at TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'uz',
                blocked INTEGER DEFAULT 0,
                warned INTEGER DEFAULT 0,
                premium_until TEXT,
                premium_buyer INTEGER
            );

            CREATE TABLE IF NOT EXISTS url_cache (
                url TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                cached_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                days INTEGER NOT NULL,
                usage_type TEXT NOT NULL DEFAULT 'once',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS promo_redemptions (
                code TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                redeemed_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (code, user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id);
            CREATE INDEX IF NOT EXISTS idx_url_cache_time ON url_cache(cached_at);
        """)
        await db.commit()


async def _ensure_user(db: aiosqlite.Connection, user_id: int):
    """Insert user row if not exists."""
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id, lang, checks_today, checks_date) VALUES (?, 'uz', 0, ?)",
        (user_id, str(date.today()))
    )


# ─── USER CHECKS ─────────────────────────────────────────────────────────────

async def get_user_checks(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.commit()
        cursor = await db.execute(
            "SELECT checks_today, checks_date FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return 0
        checks, checks_date = row
        if checks_date != str(date.today()):
            return 0
        return checks or 0


async def increment_user_checks(user_id: int):
    today = str(date.today())
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        # Reset if new day
        await db.execute(
            """UPDATE users SET 
                checks_today = CASE WHEN checks_date = ? THEN checks_today + 1 ELSE 1 END,
                checks_date = ?
            WHERE user_id = ?""",
            (today, today, user_id)
        )
        await db.commit()


# ─── LANGUAGE ─────────────────────────────────────────────────────────────────

async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.commit()
        cursor = await db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else "uz"


async def set_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        await db.commit()


async def get_group_lang(chat_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT lang FROM groups WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return row[0] if row else "uz"


async def set_group_lang(chat_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO groups (chat_id, lang) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang",
            (chat_id, lang)
        )
        await db.commit()


# ─── PREMIUM ──────────────────────────────────────────────────────────────────

async def is_premium(user_id: int) -> bool:
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        return True

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or not row[0]:
            return False
        try:
            expiry = datetime.fromisoformat(row[0])
            return datetime.now() < expiry
        except (ValueError, TypeError):
            return False


async def set_premium(user_id: int, days: int = 30):
    """Give a user premium for N days. Extends if already active."""
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        cursor = await db.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

        base_date = datetime.now()
        if row and row[0]:
            try:
                parsed = datetime.fromisoformat(row[0])
                if parsed > base_date:
                    base_date = parsed
            except (ValueError, TypeError):
                pass

        new_expiry = base_date + timedelta(days=days)
        await db.execute(
            "UPDATE users SET premium_until = ? WHERE user_id = ?",
            (new_expiry.isoformat(), user_id)
        )
        await db.commit()


async def get_premium_expiry(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


# ─── HISTORY ──────────────────────────────────────────────────────────────────

async def add_to_history(user_id: int, url: str, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.execute(
            "INSERT INTO history (user_id, url, status) VALUES (?, ?, ?)",
            (user_id, url, status)
        )
        # Keep only last 50 entries per user
        await db.execute("""
            DELETE FROM history WHERE id NOT IN (
                SELECT id FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 50
            ) AND user_id = ?
        """, (user_id, user_id))
        await db.commit()


async def get_history(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT url, status, checked_at FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 10",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [{"url": r[0], "status": r[1], "date": r[2]} for r in rows]


# ─── REPORTS ──────────────────────────────────────────────────────────────────

async def add_report(user_id: int, url: str, reason: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reports (user_id, url, reason) VALUES (?, ?, ?)",
            (user_id, url, reason)
        )
        await db.commit()


# ─── STATS ────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE premium_until IS NOT NULL AND premium_until > ?",
            (datetime.now().isoformat(),)
        )
        total_premium = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM reports")
        total_reports = (await cursor.fetchone())[0]

        return {"total_users": total_users, "total_premium": total_premium, "total_reports": total_reports}


# ─── REFERRAL ─────────────────────────────────────────────────────────────────

async def add_referral(user_id: int, referred_by: int) -> bool:
    """Add referral. Returns True if newly added, False if already existed."""
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        # Check if already referred
        cursor = await db.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row and row[0]:
            return False  # Already has a referrer

        await db.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referred_by, user_id))
        # Give the referrer a credit
        await _ensure_user(db, referred_by)
        await db.execute(
            "UPDATE users SET referral_credits = referral_credits + 1 WHERE user_id = ?",
            (referred_by,)
        )
        await db.commit()
        return True


async def get_referral_count(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_referral_credits(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.commit()
        cursor = await db.execute("SELECT referral_credits FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def consume_referral_credit(user_id: int):
    """Decrement referral credits by 1."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET referral_credits = MAX(0, referral_credits - 1) WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


# ─── GROUP STATS ──────────────────────────────────────────────────────────────

async def get_group_stats(chat_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT blocked, warned FROM groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return {"blocked": 0, "warned": 0}
        return {"blocked": row[0] or 0, "warned": row[1] or 0}


async def increment_group_blocked(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO groups (chat_id, blocked) VALUES (?, 1) ON CONFLICT(chat_id) DO UPDATE SET blocked = blocked + 1",
            (chat_id,)
        )
        await db.commit()


async def increment_group_warned(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO groups (chat_id, warned) VALUES (?, 1) ON CONFLICT(chat_id) DO UPDATE SET warned = warned + 1",
            (chat_id,)
        )
        await db.commit()


# ─── URL CACHE ────────────────────────────────────────────────────────────────

async def cache_url_result(url: str, result: str):
    """Store a URL scan result as JSON string in cache."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO url_cache (url, result, cached_at) VALUES (?, ?, ?)",
            (url, result, datetime.now().isoformat())
        )
        # Evict old entries (keep max 5000)
        await db.execute("""
            DELETE FROM url_cache WHERE url NOT IN (
                SELECT url FROM url_cache ORDER BY cached_at DESC LIMIT 5000
            )
        """)
        await db.commit()


async def get_cached_url(url: str) -> Optional[str]:
    """Get cached result. Returns None if expired or not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT result, cached_at FROM url_cache WHERE url = ?", (url,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        try:
            cached_time = datetime.fromisoformat(row[1])
            if (datetime.now() - cached_time).total_seconds() / 3600 > CACHE_EXPIRE_HOURS:
                # Expired — delete it
                await db.execute("DELETE FROM url_cache WHERE url = ?", (url,))
                await db.commit()
                return None
        except (ValueError, TypeError):
            return None
        return row[0]


# ─── RATE LIMITING (in-memory for speed) ──────────────────────────────────────

def is_rate_limited(user_id: int) -> tuple:
    now = datetime.now().timestamp()
    last = _rate_limit_cache.get(user_id, 0)
    elapsed = now - last
    if elapsed < RATE_LIMIT_SECONDS:
        return True, int(RATE_LIMIT_SECONDS - elapsed)
    return False, 0


def update_rate_limit(user_id: int):
    _rate_limit_cache[user_id] = datetime.now().timestamp()


# ─── PROMOCODE SYSTEM ─────────────────────────────────────────────────────────

async def create_promocode(code: str, days: int, usage_type: str):
    """Creates a promo code. usage_type: 'once' or 'multi'."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO promocodes (code, days, usage_type) VALUES (?, ?, ?)",
            (code.upper(), days, usage_type)
        )
        await db.commit()


async def redeem_promocode(user_id: int, code: str) -> tuple:
    """Attempt to redeem a promo code. Returns (success, message_key)."""
    code_upper = code.upper()

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if promo exists
        cursor = await db.execute(
            "SELECT days, usage_type FROM promocodes WHERE code = ?", (code_upper,)
        )
        promo = await cursor.fetchone()
        if not promo:
            return False, "promo_invalid"

        days, usage_type = promo

        # Check if user already used this code
        cursor = await db.execute(
            "SELECT 1 FROM promo_redemptions WHERE code = ? AND user_id = ?",
            (code_upper, user_id)
        )
        if await cursor.fetchone():
            return False, "promo_already_used"

        # Check if single-use code was already taken
        if usage_type == "once":
            cursor = await db.execute(
                "SELECT COUNT(*) FROM promo_redemptions WHERE code = ?", (code_upper,)
            )
            count = (await cursor.fetchone())[0]
            if count > 0:
                return False, "promo_expired"

        # Redeem it
        await db.execute(
            "INSERT INTO promo_redemptions (code, user_id) VALUES (?, ?)",
            (code_upper, user_id)
        )
        await db.commit()

    # Apply premium days (outside the transaction)
    await set_premium(user_id, days)
    return True, "promo_success"


# ─── GROUP PREMIUM ────────────────────────────────────────────────────────────

async def is_group_premium(chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT premium_until FROM groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        if not row or not row[0]:
            return False
        try:
            return datetime.now() < datetime.fromisoformat(row[0])
        except (ValueError, TypeError):
            return False


async def set_group_premium(chat_id: int, days: int = 30):
    """Give a group premium for N days. Extends if already active."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT premium_until FROM groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()

        base_date = datetime.now()
        if row and row[0]:
            try:
                parsed = datetime.fromisoformat(row[0])
                if parsed > base_date:
                    base_date = parsed
            except (ValueError, TypeError):
                pass

        new_expiry = (base_date + timedelta(days=days)).isoformat()
        await db.execute(
            """INSERT INTO groups (chat_id, premium_until) VALUES (?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET premium_until = excluded.premium_until""",
            (chat_id, new_expiry)
        )
        await db.commit()


async def get_group_premium_expiry(chat_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT premium_until FROM groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_group_premium_buyer(chat_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT premium_buyer FROM groups WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_group_premium_buyer(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO groups (chat_id, premium_buyer) VALUES (?, ?)
               ON CONFLICT(chat_id) DO UPDATE SET premium_buyer = excluded.premium_buyer""",
            (chat_id, user_id)
        )
        await db.commit()


# ─── BUSINESS CONNECTION ─────────────────────────────────────────────────────

async def save_business_connection(user_id: int, connection_id: str, is_active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET business_connection_id = ?, business_secretary = ? WHERE user_id = ?",
            (connection_id if is_active else None, int(is_active), user_id)
        )
        await db.commit()


async def get_business_connection_id(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT business_connection_id FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def is_business_secretary_active(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT business_secretary FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row[0]) if row else False


# ─── SECRETARY MODE ───────────────────────────────────────────────────────────

async def get_secretary_mode(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT secretary_mode FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row[0]) if row else False


async def set_secretary_mode(user_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_user(db, user_id)
        await db.execute(
            "UPDATE users SET secretary_mode = ? WHERE user_id = ?",
            (int(enabled), user_id)
        )
        await db.commit()


# ─── ADMIN HELPERS ────────────────────────────────────────────────────────────

async def get_all_user_ids() -> list:
    """Get all user IDs."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_url_cache_size() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM url_cache")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def clear_url_cache():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM url_cache")
        await db.commit()


async def get_recent_reports(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, url, reason, reported_at FROM reports ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [{"user_id": r[0], "url": r[1], "reason": r[2], "date": r[3]} for r in rows]


# ─── BACKWARD COMPATIBILITY (sync wrappers for non-async contexts) ───────────
# These should NOT be used in production — only during migration or testing.

def load_db() -> dict:
    """Legacy compatibility — returns empty dict. Use async functions instead."""
    return {}
