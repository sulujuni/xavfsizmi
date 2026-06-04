import json
import os
from datetime import date, datetime, timedelta

# Saves to /data on Railway (persistent volume), or locally when testing
DB_FILE = "/data/users.json" if os.path.exists("/data") else "users.json"

RATE_LIMIT_SECONDS = 30
CACHE_EXPIRE_HOURS = 24

_rate_limit_cache = {}


def load_db() -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data: dict):
    dir_name = os.path.dirname(DB_FILE)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ─── USER CHECKS ─────────────────────────────────────────────────────────────

def get_user_checks(user_id: int) -> int:
    db = load_db()
    today = str(date.today())
    user_key = str(user_id)
    if user_key not in db:
        return 0
    if db[user_key].get("date") != today:
        return 0
    return db[user_key].get("checks", 0)


def increment_user_checks(user_id: int):
    db = load_db()
    today = str(date.today())
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": today, "checks": 0, "lang": "uz"}
    elif db[user_key].get("date") != today:
        db[user_key]["date"] = today
        db[user_key]["checks"] = 0
    db[user_key]["checks"] += 1
    save_db(db)


# ─── LANGUAGE ─────────────────────────────────────────────────────────────────

def get_user_lang(user_id: int) -> str:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return "uz"
    return db[user_key].get("lang", "uz")


def set_user_lang(user_id: int, lang: str):
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": str(date.today()), "checks": 0, "lang": lang}
    else:
        db[user_key]["lang"] = lang
    save_db(db)


def get_group_lang(chat_id: int) -> str:
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        return "uz"
    return db[key].get("lang", "uz")


def set_group_lang(chat_id: int, lang: str):
    db = load_db()
    key = f"group_{chat_id}"
    db[key] = db.get(key, {})
    db[key]["lang"] = lang
    save_db(db)


# ─── PREMIUM (single implementation with expiry support) ─────────────────────

def is_premium(user_id: int) -> bool:
    """Checks if a user has active premium status (or is the Admin)."""
    from config import ADMIN_ID
    if user_id == ADMIN_ID:
        return True

    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return False

    # Support both old boolean format and new expiry format
    expiry_str = db[user_key].get("premium_until")
    if expiry_str:
        try:
            expiry_date = datetime.fromisoformat(expiry_str)
            return datetime.now() < expiry_date
        except ValueError:
            return False

    # Fallback: old boolean field
    return db[user_key].get("premium", False)


def set_premium(user_id: int, days: int = 30):
    """Gives a user premium for a specified number of days."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"lang": "uz", "checks": 0, "date": str(date.today())}

    current_expiry = db[user_key].get("premium_until")
    base_date = datetime.now()

    # If already premium, extend it
    if current_expiry:
        try:
            parsed_expiry = datetime.fromisoformat(current_expiry)
            if parsed_expiry > base_date:
                base_date = parsed_expiry
        except ValueError:
            pass

    new_expiry = base_date + timedelta(days=days)
    db[user_key]["premium_until"] = new_expiry.isoformat()
    db[user_key]["premium"] = True
    save_db(db)


def get_premium_expiry(user_id: int) -> str:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return None
    return db[user_key].get("premium_until")


# ─── HISTORY ──────────────────────────────────────────────────────────────────

def add_to_history(user_id: int, url: str, status: str):
    """Add a URL check to user history. status is a string like '🟢 Clean' or '🔴 Malicious'."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    if "history" not in db[user_key]:
        db[user_key]["history"] = []
    history = db[user_key]["history"]
    history.insert(0, {"url": url, "status": status, "date": str(date.today())})
    db[user_key]["history"] = history[:10]
    save_db(db)


def get_history(user_id: int) -> list:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return []
    return db[user_key].get("history", [])


# ─── REPORTS ──────────────────────────────────────────────────────────────────

def add_report(user_id: int, url: str, reason: str = ""):
    """Add a malicious URL report."""
    db = load_db()
    if "reports" not in db:
        db["reports"] = []
    db["reports"].append({
        "user_id": user_id,
        "url": url,
        "reason": reason,
        "date": str(date.today())
    })
    save_db(db)


# ─── STATS ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    db = load_db()
    total_users = sum(1 for k in db.keys() if k.isdigit())
    total_premium = sum(1 for k in db.keys() if k.isdigit() and is_premium(int(k)))
    total_reports = len(db.get("reports", []))
    return {"total_users": total_users, "total_premium": total_premium, "total_reports": total_reports}


# ─── REFERRAL ─────────────────────────────────────────────────────────────────

def add_referral(user_id: int, referred_by: int) -> bool:
    """Records that user_id was referred by referred_by. Returns True if new referral."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": str(date.today()), "checks": 0, "lang": "uz"}

    # Don't allow re-referral
    if db[user_key].get("referred_by"):
        return False

    db[user_key]["referred_by"] = referred_by

    # Give the referrer 1 free breach credit
    referrer_key = str(referred_by)
    if referrer_key not in db:
        db[referrer_key] = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    db[referrer_key]["referral_credits"] = db[referrer_key].get("referral_credits", 0) + 1

    save_db(db)
    return True


def get_referral_count(user_id: int) -> int:
    db = load_db()
    return sum(1 for k in db.keys() if k.isdigit() and db[k].get("referred_by") == user_id)


def get_referral_credits(user_id: int) -> int:
    """Returns the number of free breach scan tokens from referrals."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return 0
    return db[user_key].get("referral_credits", 0)


def consume_referral_credit(user_id: int):
    """Deducts 1 referral credit from a user (for free breach check)."""
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return
    credits = db[user_key].get("referral_credits", 0)
    if credits > 0:
        db[user_key]["referral_credits"] = credits - 1
        save_db(db)


# ─── GROUP STATS ──────────────────────────────────────────────────────────────

def get_group_stats(chat_id: int) -> dict:
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        return {"blocked": 0, "warned": 0}
    return {"blocked": db[key].get("blocked", 0), "warned": db[key].get("warned", 0)}


def increment_group_blocked(chat_id: int):
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        db[key] = {"lang": "uz", "blocked": 0, "warned": 0}
    db[key]["blocked"] = db[key].get("blocked", 0) + 1
    save_db(db)


def increment_group_warned(chat_id: int):
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        db[key] = {"lang": "uz", "blocked": 0, "warned": 0}
    db[key]["warned"] = db[key].get("warned", 0) + 1
    save_db(db)


# ─── URL CACHE ────────────────────────────────────────────────────────────────

def cache_url_result(url: str, result: dict):
    db = load_db()
    if "url_cache" not in db:
        db["url_cache"] = {}
    db["url_cache"][url] = {"result": result, "timestamp": str(datetime.now())}
    if len(db["url_cache"]) > 1000:
        oldest = list(db["url_cache"].keys())[0]
        del db["url_cache"][oldest]
    save_db(db)


def get_cached_url(url: str):
    db = load_db()
    cache = db.get("url_cache", {})
    if url not in cache:
        return None
    entry = cache[url]
    cached_time = datetime.fromisoformat(entry["timestamp"])
    if (datetime.now() - cached_time).total_seconds() / 3600 > CACHE_EXPIRE_HOURS:
        return None
    return entry["result"]


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
    db = load_db()
    if "promocodes" not in db:
        db["promocodes"] = {}

    db["promocodes"][code.upper()] = {
        "days": days,
        "type": usage_type,
        "used_by": []
    }
    save_db(db)


def redeem_promocode(user_id: int, code: str) -> tuple:
    """Attempts to redeem a code for a user. Returns (success_bool, message_key)"""
    db = load_db()
    promocodes = db.get("promocodes", {})
    code_upper = code.upper()

    if code_upper not in promocodes:
        return False, "promo_invalid"

    promo = promocodes[code_upper]
    uid_str = str(user_id)

    # Check if this user has already used this specific code
    if uid_str in promo["used_by"]:
        return False, "promo_already_used"

    # Check if a single-use code was already taken by someone else
    if promo["type"] == "once" and len(promo["used_by"]) > 0:
        return False, "promo_expired"

    # Code is valid! Apply premium days
    set_premium(user_id, promo["days"])

    # Mark as used
    promo["used_by"].append(uid_str)
    db["promocodes"][code_upper] = promo
    save_db(db)

    return True, "promo_success"


# ─── GROUP PREMIUM ────────────────────────────────────────────────────────────

def is_group_premium(chat_id: int) -> bool:
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        return False
    expiry_str = db[key].get("premium_until")
    if not expiry_str:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(expiry_str)
    except ValueError:
        return False


def set_group_premium(chat_id: int, days: int = 30):
    """Give a group premium for N days. Extends if already active."""
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        db[key] = {"lang": "uz", "blocked": 0, "warned": 0}
    base_date = datetime.now()
    current_expiry = db[key].get("premium_until")
    if current_expiry:
        try:
            parsed = datetime.fromisoformat(current_expiry)
            if parsed > base_date:
                base_date = parsed
        except ValueError:
            pass
    db[key]["premium_until"] = (base_date + timedelta(days=days)).isoformat()
    db[key]["premium"] = True
    save_db(db)


def get_group_premium_expiry(chat_id: int) -> str:
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        return None
    return db[key].get("premium_until")


def get_group_premium_buyer(chat_id: int) -> int:
    """Returns the user_id who activated group premium."""
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        return None
    return db[key].get("premium_buyer")


def set_group_premium_buyer(chat_id: int, user_id: int):
    db = load_db()
    key = f"group_{chat_id}"
    if key not in db:
        db[key] = {"lang": "uz", "blocked": 0, "warned": 0}
    db[key]["premium_buyer"] = user_id
    save_db(db)


# ─── BUSINESS CONNECTION (Secretary Mode) ────────────────────────────────────

def save_business_connection(user_id: int, connection_id: str, is_active: bool):
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    db[user_key]["business_connection_id"] = connection_id if is_active else None
    db[user_key]["business_secretary"] = is_active
    save_db(db)


def get_business_connection_id(user_id: int) -> str:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return None
    return db[user_key].get("business_connection_id")


def is_business_secretary_active(user_id: int) -> bool:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return False
    return db[user_key].get("business_secretary", False)


def get_secretary_mode(user_id: int) -> bool:
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        return False
    return db[user_key].get("secretary_mode", False)


def set_secretary_mode(user_id: int, enabled: bool):
    db = load_db()
    user_key = str(user_id)
    if user_key not in db:
        db[user_key] = {"date": str(date.today()), "checks": 0, "lang": "uz"}
    db[user_key]["secretary_mode"] = enabled
    save_db(db)



# ─── GROUP DAILY CHECKS (free tier limit) ─────────────────────────────────────

GROUP_DAILY_FREE_LIMIT = 20  # Groups get 20 free checks per day


def get_group_checks(chat_id: int) -> int:
    """Get how many checks the group has used today."""
    db = load_db()
    today = str(date.today())
    key = f"group_{chat_id}"
    if key not in db:
        return 0
    if db[key].get("check_date") != today:
        return 0
    return db[key].get("checks", 0)


def increment_group_checks(chat_id: int):
    """Increment the group's daily check counter."""
    db = load_db()
    today = str(date.today())
    key = f"group_{chat_id}"
    if key not in db:
        db[key] = {"lang": "uz", "blocked": 0, "warned": 0}
    if db[key].get("check_date") != today:
        db[key]["check_date"] = today
        db[key]["checks"] = 0
    db[key]["checks"] = db[key].get("checks", 0) + 1
    save_db(db)


def is_group_limit_reached(chat_id: int) -> bool:
    """Check if a group has reached its daily free limit."""
    if is_group_premium(chat_id):
        return False
    return get_group_checks(chat_id) >= GROUP_DAILY_FREE_LIMIT
