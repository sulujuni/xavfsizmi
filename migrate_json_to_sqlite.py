"""
Migrate a legacy users.json into the Phase 2 SQLite store.

The bot ALSO auto-migrates on first startup (see database._auto_migrate_json),
so running this manually is optional — useful for verifying the result or
migrating ahead of deployment.

Usage:
    python migrate_json_to_sqlite.py
    python migrate_json_to_sqlite.py --json-path users.json --db-path safelink.db
    python migrate_json_to_sqlite.py --dry-run
"""

import os
import sys
import json
import argparse


def _resolve(json_path, db_path):
    if not json_path:
        json_path = "/data/users.json" if os.path.exists("/data/users.json") else "users.json"
    if not db_path:
        db_path = "/data/safelink.db" if os.path.exists("/data") else "safelink.db"
    return json_path, db_path


def migrate(json_path: str, db_path: str, dry_run: bool = False):
    if not os.path.exists(json_path):
        print(f"  No JSON file at {json_path} - nothing to migrate (bot will start fresh).")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    users = {k: v for k, v in data.items() if k.isdigit()}
    groups = {k: v for k, v in data.items() if k.startswith("group_")}
    reports = data.get("reports", [])
    promocodes = data.get("promocodes", {})
    url_cache = data.get("url_cache", {})

    print("Migration summary:")
    print(f"  Users:       {len(users)}")
    print(f"  Groups:      {len(groups)}")
    print(f"  Reports:     {len(reports)}")
    print(f"  Promo codes: {len(promocodes)}")
    print(f"  URL cache:   {len(url_cache)} (loaded into cache layer with TTL)")

    if dry_run:
        print("\nDRY RUN - nothing written.")
        return

    # Point the database layer at the chosen DB and import via its kv store.
    os.environ["DB_PATH"] = db_path
    # Ensure a clean, idempotent import: write each top-level doc directly.
    import sqlite3
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    rows = []
    for k, v in users.items():
        rows.append((k, json.dumps(v)))
    for k, v in groups.items():
        rows.append((k, json.dumps(v)))
    if reports:
        rows.append(("reports", json.dumps(reports)))
    if promocodes:
        rows.append(("promocodes", json.dumps(promocodes)))

    conn.executemany(
        "INSERT INTO kv (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        rows,
    )
    conn.commit()
    conn.close()

    # Load URL cache entries into the cache layer (Redis/memory) with TTL.
    if url_cache:
        from cache import cache, URL_CACHE_TTL
        cache.connect()
        for url, entry in url_cache.items():
            try:
                cache.set(f"url:{url}", json.dumps(entry.get("result", {})), ttl=URL_CACHE_TTL)
            except Exception:
                pass

    size_kb = os.path.getsize(db_path) / 1024
    print(f"\nMigration complete -> {db_path} ({size_kb:.1f} KB)")
    print("Tip: keep users.json as a backup until you've verified the bot works.")


def main():
    p = argparse.ArgumentParser(description="Migrate users.json to SQLite")
    p.add_argument("--json-path", default=None)
    p.add_argument("--db-path", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    json_path, db_path = _resolve(args.json_path, args.db_path)
    print("SafeLink Bot - JSON -> SQLite migration")
    print(f"  Source: {json_path}")
    print(f"  Target: {db_path}")
    print(f"  Mode:   {'DRY RUN' if args.dry_run else 'LIVE'}\n")
    migrate(json_path, db_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
