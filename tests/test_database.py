"""Tests for core database logic: promo codes, premium expiry, rate limiting,
referrals, stats, and the DAU analytics trend."""
from datetime import datetime, timedelta

import database as db


# ─── Promo codes ─────────────────────────────────────────────────────────────

def test_promo_redeem_success_grants_premium():
    db.create_promocode("WELCOME", days=30, usage_type="multi")
    ok, key = db.redeem_promocode(1001, "welcome")  # case-insensitive
    assert ok is True
    assert key == "promo_success"
    assert db.is_premium(1001) is True


def test_promo_invalid_code():
    ok, key = db.redeem_promocode(1002, "NOPE")
    assert ok is False
    assert key == "promo_invalid"


def test_promo_cannot_be_used_twice_by_same_user():
    db.create_promocode("ONCEUSER", days=10, usage_type="multi")
    db.redeem_promocode(1003, "ONCEUSER")
    ok, key = db.redeem_promocode(1003, "ONCEUSER")
    assert ok is False
    assert key == "promo_already_used"


def test_promo_once_type_expires_after_first_use():
    db.create_promocode("SINGLE", days=10, usage_type="once")
    ok1, _ = db.redeem_promocode(1004, "SINGLE")
    ok2, key2 = db.redeem_promocode(1005, "SINGLE")
    assert ok1 is True
    assert ok2 is False
    assert key2 == "promo_expired"


# ─── Premium expiry ──────────────────────────────────────────────────────────

def test_premium_active_and_expired():
    db.set_premium(2001, days=5)
    assert db.is_premium(2001) is True

    # Force an expired timestamp directly in the doc.
    doc = db._get_doc("2002") or {}
    doc["premium_until"] = (datetime.now() - timedelta(days=1)).isoformat()
    doc["premium"] = True
    db._set_doc("2002", doc)
    assert db.is_premium(2002) is False


def test_set_premium_extends_existing():
    db.set_premium(2003, days=10)
    first = datetime.fromisoformat(db.get_premium_expiry(2003))
    db.set_premium(2003, days=10)
    second = datetime.fromisoformat(db.get_premium_expiry(2003))
    assert second > first


# ─── Rate limiting (cache-backed) ────────────────────────────────────────────

def test_rate_limit_flow():
    limited, _ = db.is_rate_limited(3001)
    assert limited is False
    db.update_rate_limit(3001)
    limited, remaining = db.is_rate_limited(3001)
    assert limited is True
    assert 0 < remaining <= db.RATE_LIMIT_SECONDS


# ─── Referrals + stats (SQL-backed counts) ───────────────────────────────────

def test_referral_count_and_credits():
    db.ensure_user_exists(4001)
    assert db.add_referral(4002, 4001) is True
    assert db.add_referral(4003, 4001) is True
    # A user can't be referred twice.
    assert db.add_referral(4002, 4001) is False
    assert db.get_referral_count(4001) == 2
    assert db.get_referral_credits(4001) == 2


def test_stats_counts():
    db.ensure_user_exists(5001)
    db.ensure_user_exists(5002)
    db.set_premium(5003, days=5)
    db.add_report(5001, "http://bad.example", "phishing")
    stats = db.get_stats()
    assert stats["total_users"] == 3
    assert stats["total_premium"] == 1
    assert stats["total_reports"] == 1


# ─── DAU analytics ───────────────────────────────────────────────────────────

def test_dau_dedupes_per_user_per_day():
    db.record_daily_active(6001)
    db.record_daily_active(6001)  # same user again -> not double counted
    db.record_daily_active(6002)
    trend = db.get_dau_trend(7)
    assert len(trend) == 7
    # Today's bucket is the last entry.
    assert trend[-1][1] == 2
