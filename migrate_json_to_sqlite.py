"""
Migration Script: JSON (users.json) → SQLite (safelink.db)

Run this ONCE to migrate existing data from the old JSON database
to the new Phase 2 SQLite database.

Usage:
    python migrate_json_to_sqlite.py

Options:
    --json-path PATH   Path to users.json (default: users.json or /data/users.json)
    --db-path PATH     Path to SQLite DB (default: safelink.db or /data/safelink.db)
    --dry-run          Show what would be migrated without writing
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime, date

# Add parent dir to path so we can import database module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def migrate(json_path: str, db_path: str, dry_run: bool = False):
    """Main migration logic."""
    import aiosqlite

    # Load JSON data
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        print("   Nothing to migrate. The bot will start with a fresh database.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    print(f"📂 Loaded JSON: {json_path} ({len(data)} keys)")

    # Count entities
    users = {}
    groups = {}
    reports = []
    url_cache = {}
    promocodes = {}

    for key, value in data.items():
        if key == "reports":
            reports = value if isinstance(value, list) else []
        elif key == "url_cache":
            url_cache = value if isinstance(value, dict) else {}
        elif key == "promocodes":
            promocodes = value if isinstance(value, dict) else {}
        elif key.startswith("group_"):
            chat_id = key.replace("group_", "")
            try:
                groups[int(chat_id)] = value
            except ValueError:
                pass
        elif key.isdigit():
            users[int(key)] = value

    print(f"\n📊 Migration Summary:")
    print(f"   👥 Users: {len(users)}")
    print(f"   🏘 Groups: {len(groups)}")
    print(f"   🚨 Reports: {len(reports)}")
    print(f"   🗄 URL Cache entries: {len(url_cache)}")
    print(f"   🎟 Promo codes: {len(promocodes)}")

    if dry_run:
        print("\n🔍 DRY RUN — no changes written.")
        _preview_users(users)
        return

    # Initialize database
    print(f"\n💾 Creating SQLite database: {db_path}")

    # Set env so database.py uses correct path
    os.environ["DB_PATH"] = db_path

    from database import init_db, DB_PATH
    await init_db()
    print("   ✅ Tables created")

    # Migrate data
    async with aiosqlite.connect(db_path) as db:
        # Make migration idempotent: history & reports use autoincrement IDs and would
        # duplicate on re-run. Clear them first since they're fully repopulated from JSON.
        # (users/groups/url_cache/promocodes use INSERT OR REPLACE and are already safe.)
        await db.execute("DELETE FROM history")
        await db.execute("DELETE FROM reports")
        await db.commit()

        # --- USERS ---
        print(f"\n👥 Migrating {len(users)} users...")
        user_count = 0
        for user_id, user_data in users.items():
            lang = user_data.get("lang", "uz")
            checks = user_data.get("checks", 0)
            checks_date = user_data.get("date", str(date.today()))
            premium_until = user_data.get("premium_until")
            referred_by = user_data.get("referred_by")
            referral_credits = user_data.get("referral_credits", 0)
            secretary_mode = int(user_data.get("secretary_mode", False))
            business_connection_id = user_data.get("business_connection_id")
            business_secretary = int(user_data.get("business_secretary", False))

            # Handle old-style boolean premium (convert to 30 days from now)
            if not premium_until and user_data.get("premium", False):
                premium_until = (datetime.now()).isoformat()  # Already expired

            await db.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, lang, checks_today, checks_date, premium_until, referred_by, 
                 referral_credits, secretary_mode, business_connection_id, business_secretary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, lang, checks, checks_date, premium_until,
                referred_by, referral_credits, secretary_mode,
                business_connection_id, business_secretary
            ))

            # Migrate history
            history = user_data.get("history", [])
            for item in history:
                url = item.get("url", "")
                is_safe = item.get("safe", True)
                checked_date = item.get("date", str(date.today()))
                status = "🟢 Clean" if is_safe else "🔴 Malicious"
                if isinstance(is_safe, str):
                    status = is_safe

                await db.execute(
                    "INSERT INTO history (user_id, url, status, checked_at) VALUES (?, ?, ?, ?)",
                    (user_id, url, status, checked_date)
                )

            user_count += 1
            if user_count % 100 == 0:
                print(f"   ... {user_count}/{len(users)} users migrated")

        print(f"   ✅ {user_count} users migrated")

        # --- GROUPS ---
        print(f"\n🏘 Migrating {len(groups)} groups...")
        for chat_id, group_data in groups.items():
            lang = group_data.get("lang", "uz")
            blocked = group_data.get("blocked", 0)
            warned = group_data.get("warned", 0)
            premium_until = group_data.get("premium_until")
            premium_buyer = group_data.get("premium_buyer")

            await db.execute("""
                INSERT OR REPLACE INTO groups 
                (chat_id, lang, blocked, warned, premium_until, premium_buyer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, lang, blocked, warned, premium_until, premium_buyer))

        print(f"   ✅ {len(groups)} groups migrated")

        # --- REPORTS ---
        print(f"\n🚨 Migrating {len(reports)} reports...")
        for report in reports:
            user_id = report.get("user_id", 0)
            url = report.get("url", "")
            reason = report.get("reason", "")
            reported_at = report.get("date", str(date.today()))

            await db.execute(
                "INSERT INTO reports (user_id, url, reason, reported_at) VALUES (?, ?, ?, ?)",
                (user_id, url, reason, reported_at)
            )
        print(f"   ✅ {len(reports)} reports migrated")

        # --- URL CACHE ---
        print(f"\n🗄 Migrating {len(url_cache)} cached URLs...")
        cache_count = 0
        for url, entry in url_cache.items():
            result = json.dumps(entry.get("result", {}))
            timestamp = entry.get("timestamp", datetime.now().isoformat())

            await db.execute(
                "INSERT OR REPLACE INTO url_cache (url, result, cached_at) VALUES (?, ?, ?)",
                (url, result, timestamp)
            )
            cache_count += 1

        print(f"   ✅ {cache_count} cache entries migrated")

        # --- PROMOCODES ---
        print(f"\n🎟 Migrating {len(promocodes)} promo codes...")
        for code, promo_data in promocodes.items():
            days = promo_data.get("days", 30)
            usage_type = promo_data.get("type", "once")
            used_by = promo_data.get("used_by", [])

            await db.execute(
                "INSERT OR REPLACE INTO promocodes (code, days, usage_type) VALUES (?, ?, ?)",
                (code, days, usage_type)
            )

            # Migrate redemption records
            for uid_str in used_by:
                try:
                    uid = int(uid_str)
                    await db.execute(
                        "INSERT OR IGNORE INTO promo_redemptions (code, user_id) VALUES (?, ?)",
                        (code, uid)
                    )
                except (ValueError, TypeError):
                    pass

        print(f"   ✅ {len(promocodes)} promo codes migrated")

        # Commit all changes
        await db.commit()

    print(f"\n{'='*50}")
    print(f"✅ MIGRATION COMPLETE!")
    print(f"   Database: {db_path}")
    print(f"   Size: {os.path.getsize(db_path) / 1024:.1f} KB")
    print(f"\n💡 Tip: Keep '{json_path}' as backup. You can safely delete it")
    print(f"   after verifying the bot works correctly with the new database.")


def _preview_users(users: dict):
    """Show a preview of first 5 users."""
    print("\n   First 5 users:")
    for i, (uid, data) in enumerate(list(users.items())[:5]):
        premium = "⭐" if data.get("premium") or data.get("premium_until") else "  "
        lang = data.get("lang", "uz")
        checks = data.get("checks", 0)
        history_count = len(data.get("history", []))
        print(f"   {premium} User {uid}: lang={lang}, checks={checks}, history={history_count}")


def main():
    parser = argparse.ArgumentParser(description="Migrate SafeLink Bot from JSON to SQLite")
    parser.add_argument("--json-path", default=None, help="Path to users.json")
    parser.add_argument("--db-path", default=None, help="Path to output SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    # Determine paths
    json_path = args.json_path
    if not json_path:
        if os.path.exists("/data/users.json"):
            json_path = "/data/users.json"
        else:
            json_path = "users.json"

    db_path = args.db_path
    if not db_path:
        if os.path.exists("/data"):
            db_path = "/data/safelink.db"
        else:
            db_path = "safelink.db"

    print("🔄 SafeLink Bot — JSON → SQLite Migration")
    print(f"{'='*50}")
    print(f"   Source: {json_path}")
    print(f"   Target: {db_path}")
    print(f"   Mode:   {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"{'='*50}")

    asyncio.run(migrate(json_path, db_path, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
