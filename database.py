"""
SafeLink Bot database layer (Phase 2).

Backed by SQLite (a single key/value table holding JSON documents) instead of
a single users.json file. All public functions keep their original signatures
and remain synchronous, so no handler code needs to change.

A Redis write-through cache (see cache.py) sits in front of single-document
reads/writes. When REDIS_URL is unset it transparently uses an in-memory cache.

Document model (unchanged from the old JSON file):
  - key str(user_id)      -> user dict
  - key "group_<chat_id>" -> group dict
  - key "reports"         -> list of report dicts
  - key "promocodes"      -> dict of code -> promo dict
URL scan results are cached via the cache layer with a TTL.
"""

import os
import json
import sqlite3
import logging
import threading
from datetime import date, datetime, timedelta

from cache import cache, URL_CACHE_TTL

logger = logging.getLogger("safelink.database")

# Persistent volume on Railway, else local file. DB_PATH env overrides both.
DB_PATH = os.getenv("DB_PATH") or ("/data/safelink.db" if os.path.exists("/data") else "safelink.db")
# Backward-compatible alias (old code referenced DB_FILE)
DB_FILE = DB_PATH

RATE_LIMIT_SECONDS = 30
CACHE_EXPIRE_HOURS = 24
GROUP_DAILY_FREE_LIMIT = 20  # Groups get 20 free checks per day

_rate_limit_cache = {}
_conn = None
_lock = threading.RLock()



# ─── STORAGE ENGINE (SQLite key/value document store) ────────────────────────

def _connect() -> sqlite3.Connection:
    """Lazily open the SQLite connection, create schema, and auto-migrate."""
    global _conn
    if _conn is not None:
        return _conn
    with _lock:
        if _conn is not None:
            return _conn
        dir_name = os.path.dirname(DB_PATH)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.commit()
        _conn = conn
        _auto_migrate_json()
        return _conn


def init_db():
    """Explicit initialization hook (safe to call at startup)."""
    cache.connect()
    _connect()


def _get_doc(key: str):
    """Return the JSON document for a key (dict/list) or None. Cache-first."""
    cached = cache.get(f"doc:{key}")
    if cached is not None:
        try:
            return json.loads(cached)
        except (ValueError, TypeError):
            pass
    with _lock:
        cur = _connect().execute("SELECT value FROM kv WHERE key = ?", (key,))
        row = cur.fetchone()
    if row is None:
        return None
    cache.set(f"doc:{key}", row[0])
    try:
        return json.loads(row[0])
    except (ValueError, TypeError):
        return None


def _set_doc(key: str, value):
    """Upsert a JSON document for a key and refresh the cache (write-through)."""
    raw = json.dumps(value)
    with _lock:
        conn = _connect()
        conn.execute(
            "INSERT INTO kv (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, raw),
        )
        conn.commit()
    cache.set(f"doc:{key}", raw)


def _del_doc(key: str):
    with _lock:
        conn = _connect()
        conn.execute("DELETE FROM kv WHERE key = ?", (key,))
        conn.commit()
    cache.delete(f"doc:{key}")


def _all_docs() -> dict:
    """Return the entire store as a dict (used by scans / load_db)."""
    with _lock:
        cur = _connect().execute("SELECT key, value FROM kv")
        rows = cur.fetchall()
    out = {}
    for k, v in rows:
        try:
            out[k] = json.loads(v)
        except (ValueError, TypeError):
            continue
    return out



def _auto_migrate_json():
    """One-time import of a legacy users.json into the kv store if empty."""
    try:
        cur = _conn.execute("SELECT COUNT(*) FROM kv")
        if cur.fetchone()[0] > 0:
            return  # already populated
    except sqlite3.Error:
        return

    legacy = "/data/users.json" if os.path.exists("/data/users.json") else "users.json"
    if not os.path.exists(legacy):
        return

    try:
        with open(legacy, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    url_cache = data.pop("url_cache", {})
    rows = [(k, json.dumps(v)) for k, v in data.items()]
    with _lock:
        _conn.executemany(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", rows
        )
        _conn.commit()

    # Move any cached URL results into the cache layer (with TTL semantics).
    for url, entry in url_cache.items():
        try:
            cache.set(f"url:{url}", json.dumps(entry.get("result", {})), ttl=URL_CACHE_TTL)
        except Exception:
            pass

    logger.info("Auto-migrated %d records from %s into %s", len(rows), legacy, DB_PATH)


# ─── BACKWARD-COMPATIBLE DOCUMENT API (used directly by some handlers) ───────

def load_db() -> dict:
    """Return the full store as a dict (parity with the old JSON loader)."""
    return _all_docs()


def save_db(data: dict):
    """Reconcile the store to exactly match `data` (parity with JSON saver)."""
    with _lock:
        conn = _connect()
        existing = {r[0] for r in conn.execute("SELECT key FROM kv").fetchall()}
        for k, v in data.items():
            raw = json.dumps(v)
            conn.execute(
                "INSERT INTO kv (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (k, raw),
            )
            cache.set(f"doc:{k}", raw)
        for k in existing - set(data.keys()):
            conn.execute("DELETE FROM kv WHERE key = ?", (k,))
            cache.delete(f"doc:{k}")
        conn.commit()


def ensure_user_exists(user_id: int):
    """Make sure user is registered in the database (for accurate stats)."""
    user_key = str(user_id)
    if _get_doc(user_key) is None:
        _set_doc(user_key, {"date": str(date.today()), "checks": 0, "lang": "uz"})



# ─── USER CHECKS ─────────────────────────────────────────────────────────────

def get_user_checks(user_id: int) -> int:
    user = _get_doc(str(user_id))
    if user is None:
        return 0
    if user.get("date") != str(date.today()):
        return 0
    return user.get("checks", 0)


def increment_user_checks(user_id: int):
    today = str(date.today())
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        user = {"date": today, "checks": 0, "lang": "uz"}
    elif user.get("date") != today:
        user["date"] = today
        user["checks"] = 0
    user["checks"] = user.get("checks", 0) + 1
    _set_doc(user_key, user)


# ─── LANGUAGE ─────────────────────────────────────────────────────────────────

def get_user_lang(user_id: int) -> str:
    user = _get_doc(str(user_id))
    if user is None:
        return "uz"
    return user.get("lang", "uz")


def set_user_lang(user_id: int, lang: str):
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        user = {"date": str(date.today()), "checks": 0, "lang": lang}
    else:
        user["lang"] = lang
    _set_doc(user_key, user)


def get_group_lang(chat_id: int) -> str:
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return "uz"
    return grp.get("lang", "uz")


def set_group_lang(chat_id: int, lang: str):
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {}
    grp["lang"] = lang
    _set_doc(key, grp)



# ─── PREMIUM (single implementation with expiry support) ─────────────────────

def is_premium(user_id: int) -> bool:
    """Checks if a user has active premium status."""
    from config import ADMIN_ID

    user = _get_doc(str(user_id))

    # Admin: if premium was explicitly removed, respect that; else default True
    if user_id == ADMIN_ID:
        if user is not None and "premium_until" not in user and not user.get("premium"):
            return False
        if user is None:
            return True
        if "premium_until" not in user:
            return True

    if user is None:
        return False

    expiry_str = user.get("premium_until")
    if expiry_str:
        try:
            return datetime.now() < datetime.fromisoformat(expiry_str)
        except ValueError:
            return False
    return user.get("premium", False)


def set_premium(user_id: int, days: int = 30):
    """Gives a user premium for a specified number of days (extends if active)."""
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        user = {"lang": "uz", "checks": 0, "date": str(date.today())}

    base_date = datetime.now()
    current_expiry = user.get("premium_until")
    if current_expiry:
        try:
            parsed = datetime.fromisoformat(current_expiry)
            if parsed > base_date:
                base_date = parsed
        except ValueError:
            pass

    user["premium_until"] = (base_date + timedelta(days=days)).isoformat()
    user["premium"] = True
    _set_doc(user_key, user)


def get_premium_expiry(user_id: int) -> str:
    user = _get_doc(str(user_id))
    if user is None:
        return None
    return user.get("premium_until")



# ─── HISTORY ──────────────────────────────────────────────────────────────────

def add_to_history(user_id: int, url: str, status: str):
    """Add a URL check to user history. status is a string like '🟢 Clean'."""
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        user = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    history = user.get("history", [])
    history.insert(0, {"url": url, "status": status, "date": str(date.today())})
    user["history"] = history[:10]
    _set_doc(user_key, user)


def get_history(user_id: int) -> list:
    user = _get_doc(str(user_id))
    if user is None:
        return []
    return user.get("history", [])


# ─── REPORTS ──────────────────────────────────────────────────────────────────

def add_report(user_id: int, url: str, reason: str = ""):
    """Add a malicious URL report."""
    reports = _get_doc("reports") or []
    reports.append({
        "user_id": user_id,
        "url": url,
        "reason": reason,
        "date": str(date.today()),
    })
    _set_doc("reports", reports)


# ─── STATS ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    db = _all_docs()
    total_users = sum(1 for k in db.keys() if k.isdigit())
    total_premium = 0
    for k in db.keys():
        if not k.isdigit():
            continue
        user = db[k]
        expiry = user.get("premium_until")
        if expiry:
            try:
                if datetime.now() < datetime.fromisoformat(expiry):
                    total_premium += 1
                    continue
            except ValueError:
                pass
        if user.get("premium"):
            total_premium += 1
    total_reports = len(db.get("reports", []))
    return {"total_users": total_users, "total_premium": total_premium, "total_reports": total_reports}



# ─── REFERRAL ─────────────────────────────────────────────────────────────────

def add_referral(user_id: int, referred_by: int) -> bool:
    """Records that user_id was referred by referred_by. Returns True if new."""
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        user = {"date": str(date.today()), "checks": 0, "lang": "uz"}

    if user.get("referred_by"):
        return False

    user["referred_by"] = referred_by
    _set_doc(user_key, user)

    # Give the referrer 1 free breach credit
    referrer_key = str(referred_by)
    referrer = _get_doc(referrer_key)
    if referrer is None:
        referrer = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    referrer["referral_credits"] = referrer.get("referral_credits", 0) + 1
    _set_doc(referrer_key, referrer)
    return True


def get_referral_count(user_id: int) -> int:
    db = _all_docs()
    return sum(1 for k in db.keys() if k.isdigit() and db[k].get("referred_by") == user_id)


def get_referral_credits(user_id: int) -> int:
    """Returns the number of free breach scan tokens from referrals."""
    user = _get_doc(str(user_id))
    if user is None:
        return 0
    return user.get("referral_credits", 0)


def consume_referral_credit(user_id: int):
    """Deducts 1 referral credit from a user (for free breach check)."""
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        return
    credits = user.get("referral_credits", 0)
    if credits > 0:
        user["referral_credits"] = credits - 1
        _set_doc(user_key, user)



# ─── GROUP STATS ──────────────────────────────────────────────────────────────

def get_group_stats(chat_id: int) -> dict:
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return {"blocked": 0, "warned": 0}
    return {"blocked": grp.get("blocked", 0), "warned": grp.get("warned", 0)}


def increment_group_blocked(chat_id: int):
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {"lang": "uz", "blocked": 0, "warned": 0}
    grp["blocked"] = grp.get("blocked", 0) + 1
    _set_doc(key, grp)


def increment_group_warned(chat_id: int):
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {"lang": "uz", "blocked": 0, "warned": 0}
    grp["warned"] = grp.get("warned", 0) + 1
    _set_doc(key, grp)


# ─── URL CACHE (routed through the Redis/memory cache layer) ─────────────────

def cache_url_result(url: str, result: dict):
    try:
        cache.set(f"url:{url}", json.dumps(result), ttl=URL_CACHE_TTL)
    except Exception:
        pass


def get_cached_url(url: str):
    raw = cache.get(f"url:{url}")
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


# ─── RATE LIMITING ────────────────────────────────────────────────────────────

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

def create_promocode(code: str, days: int, usage_type: str):
    """Creates a promo code. usage_type can be 'once' or 'multi'."""
    promocodes = _get_doc("promocodes") or {}
    promocodes[code.upper()] = {"days": days, "type": usage_type, "used_by": []}
    _set_doc("promocodes", promocodes)


def redeem_promocode(user_id: int, code: str) -> tuple:
    """Attempts to redeem a code for a user. Returns (success_bool, message_key)."""
    promocodes = _get_doc("promocodes") or {}
    code_upper = code.upper()

    if code_upper not in promocodes:
        return False, "promo_invalid"

    promo = promocodes[code_upper]
    uid_str = str(user_id)

    if uid_str in promo["used_by"]:
        return False, "promo_already_used"

    if promo["type"] == "once" and len(promo["used_by"]) > 0:
        return False, "promo_expired"

    # Code is valid! Apply premium days
    set_premium(user_id, promo["days"])

    promo["used_by"].append(uid_str)
    promocodes[code_upper] = promo
    _set_doc("promocodes", promocodes)
    return True, "promo_success"


# ─── GROUP PREMIUM ────────────────────────────────────────────────────────────

def is_group_premium(chat_id: int) -> bool:
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return False
    expiry_str = grp.get("premium_until")
    if not expiry_str:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(expiry_str)
    except ValueError:
        return False


def set_group_premium(chat_id: int, days: int = 30):
    """Give a group premium for N days. Extends if already active."""
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {"lang": "uz", "blocked": 0, "warned": 0}
    base_date = datetime.now()
    current_expiry = grp.get("premium_until")
    if current_expiry:
        try:
            parsed = datetime.fromisoformat(current_expiry)
            if parsed > base_date:
                base_date = parsed
        except ValueError:
            pass
    grp["premium_until"] = (base_date + timedelta(days=days)).isoformat()
    grp["premium"] = True
    _set_doc(key, grp)


def get_group_premium_expiry(chat_id: int) -> str:
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return None
    return grp.get("premium_until")


def get_group_premium_buyer(chat_id: int) -> int:
    """Returns the user_id who activated group premium."""
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return None
    return grp.get("premium_buyer")


def set_group_premium_buyer(chat_id: int, user_id: int):
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {"lang": "uz", "blocked": 0, "warned": 0}
    grp["premium_buyer"] = user_id
    _set_doc(key, grp)



# ─── BUSINESS CONNECTION (Secretary Mode) ────────────────────────────────────

def save_business_connection(user_id: int, connection_id: str, is_active: bool):
    user_key = str(user_id)
    user = _get_doc(user_key) or {"date": str(date.today()), "checks": 0, "lang": "uz"}
    user["business_connection_id"] = connection_id if is_active else None
    user["business_secretary"] = is_active
    _set_doc(user_key, user)


def get_business_connection_id(user_id: int) -> str:
    user = _get_doc(str(user_id))
    if user is None:
        return None
    return user.get("business_connection_id")


def is_business_secretary_active(user_id: int) -> bool:
    user = _get_doc(str(user_id))
    if user is None:
        return False
    return user.get("business_secretary", False)


def get_secretary_mode(user_id: int) -> bool:
    user = _get_doc(str(user_id))
    if user is None:
        return False
    return user.get("secretary_mode", False)


def set_secretary_mode(user_id: int, enabled: bool):
    user_key = str(user_id)
    user = _get_doc(user_key) or {"date": str(date.today()), "checks": 0, "lang": "uz"}
    user["secretary_mode"] = enabled
    _set_doc(user_key, user)


# ─── GROUP DAILY CHECKS (free tier limit) ─────────────────────────────────────

def get_group_checks(chat_id: int) -> int:
    """Get how many checks the group has used today."""
    grp = _get_doc(f"group_{chat_id}")
    if grp is None:
        return 0
    if grp.get("check_date") != str(date.today()):
        return 0
    return grp.get("checks", 0)


def increment_group_checks(chat_id: int):
    """Increment the group's daily check counter."""
    today = str(date.today())
    key = f"group_{chat_id}"
    grp = _get_doc(key) or {"lang": "uz", "blocked": 0, "warned": 0}
    if grp.get("check_date") != today:
        grp["check_date"] = today
        grp["checks"] = 0
    grp["checks"] = grp.get("checks", 0) + 1
    _set_doc(key, grp)


def is_group_limit_reached(chat_id: int) -> bool:
    """Check if a group has reached its daily free limit."""
    if is_group_premium(chat_id):
        return False
    return get_group_checks(chat_id) >= GROUP_DAILY_FREE_LIMIT



# ─── DATA BREACH MONITOR (premium multi-email) ───────────────────────────────

def get_monitored_emails(user_id: int) -> list:
    """Returns list of {email, last_breach_count} dicts for a user."""
    user = _get_doc(str(user_id))
    if user is None:
        return []
    return user.get("monitored_emails", [])


def add_monitored_email(user_id: int, email: str, breach_count: int = 0):
    user_key = str(user_id)
    user = _get_doc(user_key) or {"date": str(date.today()), "checks": 0, "lang": "uz"}
    monitored = user.get("monitored_emails", [])
    if not any(e.get("email") == email for e in monitored):
        monitored.append({"email": email, "last_breach_count": breach_count})
    user["monitored_emails"] = monitored
    _set_doc(user_key, user)


def remove_monitored_email(user_id: int, email: str):
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        return
    monitored = [e for e in user.get("monitored_emails", []) if e.get("email") != email]
    user["monitored_emails"] = monitored
    _set_doc(user_key, user)


def update_monitored_email_count(user_id: int, email: str, new_count: int):
    user_key = str(user_id)
    user = _get_doc(user_key)
    if user is None:
        return
    monitored = user.get("monitored_emails", [])
    for e in monitored:
        if e.get("email") == email:
            e["last_breach_count"] = new_count
            break
    user["monitored_emails"] = monitored
    _set_doc(user_key, user)


def get_all_monitoring_users() -> list:
    """Returns user IDs who have at least one monitored email."""
    db = _all_docs()
    return [int(k) for k in db.keys() if k.isdigit() and db[k].get("monitored_emails")]



# ─── WEEKLY STATS (for weekly personal report) ───────────────────────────────

def record_check(user_id: int, is_dangerous: bool):
    """Increment weekly check counters for a user."""
    user_key = str(user_id)
    user = _get_doc(user_key) or {"date": str(date.today()), "checks": 0, "lang": "uz"}
    week = user.get("week_stats", {"checks": 0, "dangerous": 0})
    week["checks"] = week.get("checks", 0) + 1
    if is_dangerous:
        week["dangerous"] = week.get("dangerous", 0) + 1
    user["week_stats"] = week
    _set_doc(user_key, user)


def get_weekly_stats(user_id: int) -> dict:
    user = _get_doc(str(user_id))
    if user is None:
        return {"checks": 0, "dangerous": 0}
    return user.get("week_stats", {"checks": 0, "dangerous": 0})


def reset_weekly_stats():
    """Reset all users' weekly counters (called after weekly report sent)."""
    db = _all_docs()
    for k in db.keys():
        if k.isdigit() and "week_stats" in db[k]:
            doc = db[k]
            doc["week_stats"] = {"checks": 0, "dangerous": 0}
            _set_doc(k, doc)


def get_all_active_users() -> list:
    """Returns all real user IDs (for weekly reports)."""
    db = _all_docs()
    return [int(k) for k in db.keys() if k.isdigit()]
