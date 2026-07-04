"""
Shared pytest fixtures and test isolation.

The database is pointed at a throwaway SQLite file (set before importing the
app modules), and the autouse reset_state fixture truncates the table and
cache before every test, so tests are deterministic and offline.
"""
import os
import sys
import tempfile

# Make the repo root importable regardless of where pytest is invoked from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

# Isolated DB path (must be set before importing database, which reads it at import).
_TMP_DIR = tempfile.mkdtemp(prefix="xavf_tests_")
os.environ["DB_PATH"] = os.path.join(_TMP_DIR, "test.db")

import pytest  # noqa: E402

from bot.core import database as db  # noqa: E402
from bot.core.cache import cache  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state():
    """Wipe the kv table and cache before every test for isolation."""
    db.init_db()
    with db._lock:
        conn = db._connect()
        conn.execute("DELETE FROM kv")
        conn.commit()
    cache._mem.clear()
    cache._stats = {"hits": 0, "misses": 0, "errors": 0}
    yield
