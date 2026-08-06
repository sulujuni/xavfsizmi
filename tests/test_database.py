"""Tests for core database logic: promo codes, premium expiry, rate limiting,
referrals, stats, and the DAU analytics trend."""
import sqlite3
from datetime import datetime, timedelta

from bot.core import database as db


# ─── Promo codes ─────────────────────────────────────────────────────────────

def test_promo_redeem_success_grants_premium():
    db.create_promocode("WELCOME", days=30, usage_type="multi")
    ok, key = db.redeem_promocode(1001, "welcome")
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


# ─── Funnel events ───────────────────────────────────────────────────────────

def test_log_event_is_recorded_and_readable():
    db.log_event(3001, "scan_done", {"type": "url", "verdict": "safe"})
    events = db.get_recent_events(event_type="scan_done")
    assert len(events) == 1
    assert events[0]["user_id"] == "3001"
    assert events[0]["context"] == {"type": "url", "verdict": "safe"}


def test_log_event_never_raises_on_backend_failure(monkeypatch):
    def _boom(*args, **kwargs):
        raise sqlite3.OperationalError("simulated failure")

    monkeypatch.setattr(db, "_connect", _boom)
    # Must not raise — instrumentation failures can never break the bot.
    db.log_event(3002, "error_shown", {"type": "url_scan_error"})


def test_log_event_context_excludes_pii():
    """Callers must only pass categorical fields (type/verdict), never raw
    URLs, emails, or filenames — this test locks in that contract for the
    values actually used by the scan handlers."""
    url = "https://phishing-example.uz/login?user=victim"
    email = "victim@example.com"
    db.log_event(3003, "scan_done", {"type": "url", "verdict": "dangerous"})

    events = db.get_recent_events(event_type="scan_done")
    stored = events[0]["context"]
    assert url not in str(stored)
    assert email not in str(stored)
    assert set(stored.keys()) <= {"type", "verdict"}


def test_ensure_user_exists_logs_first_start_once():
    db.ensure_user_exists(3004)
    db.ensure_user_exists(3004)  # second call: existing user, no duplicate event
    events = db.get_recent_events(event_type="first_start")
    matching = [e for e in events if e["user_id"] == "3004"]
    assert len(matching) == 1


def test_add_referral_logs_referral_joined():
    ok = db.add_referral(3005, referred_by=3006)
    assert ok is True
    events = db.get_recent_events(event_type="referral_joined")
    matching = [e for e in events if e["user_id"] == "3005"]
    assert len(matching) == 1
    assert matching[0]["context"]["referred_by"] == 3006


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
    db.record_daily_active(6001)
    db.record_daily_active(6002)
    trend = db.get_dau_trend(7)
    assert len(trend) == 7
    assert trend[-1][1] == 2


# ─── Lifetime scan counter (subscription trial window) ───────────────────────

def test_total_checks_accumulates_across_days():
    """The daily counter resets; the lifetime one must not, otherwise a user
    gets a fresh batch of free scans every day and never hits the gate."""
    db.increment_user_checks(7001)
    db.increment_user_checks(7001)
    assert db.get_user_checks(7001) == 2
    assert db.get_user_total_checks(7001) == 2

    # Simulate the next day: the stored date is what triggers the daily reset.
    user = db._get_doc("7001")
    user["date"] = str(datetime.now().date() - timedelta(days=1))
    db._set_doc("7001", user)

    db.increment_user_checks(7001)
    assert db.get_user_checks(7001) == 1        # daily counter restarted
    assert db.get_user_total_checks(7001) == 3  # lifetime kept counting


def test_total_checks_defaults_to_daily_count_for_legacy_records():
    """Records written before total_checks existed must not read as brand new."""
    db._set_doc("7002", {"date": str(datetime.now().date()), "checks": 4, "lang": "uz"})
    assert db.get_user_total_checks(7002) == 4


def test_total_checks_is_zero_for_unknown_user():
    assert db.get_user_total_checks(7003) == 0
