"""Engine bootstrap, in one place instead of triplicated per exporter script.

Director v0.7, Part D: ENGINE_DIR is now overridable via the
`READS_ENGINE_DIR` environment variable, defaulting to the exact same
hardcoded local path every prior milestone used -- so every existing local
call site (every test, every prior generated package's determinism check)
is byte-for-byte unaffected when the env var is unset, which is every local
run to date. Only a staging/container environment that explicitly sets
`READS_ENGINE_DIR` takes a different path. `game_factory.py` itself (Engine
code, never modified by this project) resolves its own DB file as
`Path(__file__).parent / 'reads_football_v4.0.sqlite'` -- i.e. the sqlite
file MUST live alongside the Engine's own .py modules, so this module
overrides the whole Engine directory (modules + database together), not a
database file path independent of it. See
READS_ENGINE_STAGING_GAP_ANALYSIS.md for why a separate, independently-settable
DB-path env var was considered and rejected as architecturally dishonest
given that constraint.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("READS_ENGINE_DIR", "/Users/micahnichols/Downloads/Reads_Football_Data_Engine_v4.0"))
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
import game_factory as gf  # noqa: E402  Engine's own connect/seeded/band/generate_candidates/qa_candidate

REPO_ROOT = Path(__file__).resolve().parents[2]  # tools/quiz_export/engine.py -> .../nfl-trivia
DATA_DIR = REPO_ROOT / "data"
TOOLS_DIR = REPO_ROOT / "tools"
BACKUPS_DIR = TOOLS_DIR / "backups"

DB_FILENAME = "reads_football_v4.0.sqlite"


def db_path() -> Path:
    return ENGINE_DIR / DB_FILENAME


def connect():
    """Director v0.7, Part E: sets a busy timeout on every connection this
    project opens (via a PRAGMA on the connection `game_factory.connect()`
    -- Engine code, never modified -- already returns, not by changing that
    function). Without it, SQLite's default behavior on lock contention is
    to raise `database is locked` immediately; 5s gives a transient
    external writer (one of the 8 legacy servers audited in
    READS_ENGINE_GATEWAY_AUDIT.md, or Engine's own tooling) a chance to
    finish without every Gateway request needing its own retry logic.
    Does not affect any existing single-writer local test/generation run,
    where no contention ever occurs.

    Read/write finding (Part E): empirically verified this milestone that
    the ENTIRE Gateway generation path (tools.director_v02.pipeline.run(),
    every registered capability's generate_fn, every adapter's
    fetch_ordered_candidates()/evaluate()) performs ZERO writes to the
    Engine database -- confirmed by comparing `game_director_requests` row
    counts before/after a real generation call (unchanged). This is because
    the v0.2+ translator/validator/pipeline layer never calls
    `game_director.interpret()` (the one function in this Engine that does
    write, for its own request-logging -- and only reachable through the
    OLD, unused-by-the-Gateway v0.1 regex path,
    `game_director_v01.interpret_and_gate()`). A dedicated read-only
    connection mode was considered and not built: every real call site is
    already read-only in practice, and `game_factory.connect()` (Engine
    code) does not expose a way to request one without wrapping/duplicating
    its connection logic, which this project avoids per its standing
    discipline against copying Engine internals."""
    c = gf.connect()
    c.execute("PRAGMA busy_timeout = 5000")
    return c


def seeded(seed):
    return gf.seeded(seed)


def band(score):
    return gf.band(score)


def check_engine_readiness() -> dict:
    """Part D/L: the fail-closed check `sqlite3.connect()` alone does NOT
    give you -- connecting to a MISSING path silently creates an empty file
    (confirmed empirically, see READS_ENGINE_STAGING_GAP_ANALYSIS.md) rather
    than raising. Never raises itself; always returns a structured result so
    a readiness endpoint can report exactly what's wrong rather than 500ing.
    Deliberately lightweight (a handful of indexed lookups), NOT a full data
    audit -- Part L is explicit that readiness must stay cheap enough to
    call on every health check, not run a generation-scale scan."""
    path = db_path()
    if not ENGINE_DIR.is_dir():
        return {"ready": False, "reason": f"READS_ENGINE_DIR does not exist or is not a directory: {ENGINE_DIR}"}
    if not path.exists():
        return {"ready": False, "reason": f"Engine database file not found at {path} -- refusing to auto-create one."}
    if path.stat().st_size == 0:
        return {"ready": False, "reason": f"Engine database file at {path} is empty (0 bytes)."}
    try:
        # sqlite3.connect() on an existing-but-garbage file still succeeds --
        # PRAGMA integrity_check plus one real known-table query is what
        # actually proves this is a readable, structurally valid database.
        #
        # NOT opened via the `mode=ro` read-only URI: a real backup/restore
        # drill this milestone caught that failing on a freshly-restored
        # WAL-mode database that has never been opened before (no -shm file
        # exists yet, and a strictly read-only connection cannot create one
        # -- a genuine, documented SQLite limitation, not a bug in this
        # code). A plain connection (identical in spirit to how
        # game_factory.connect() already opens the database everywhere
        # else in this project) reads this exact same data just as safely
        # -- this function never executes a single write -- without that
        # failure mode. See READS_ENGINE_BACKUP_AND_RESTORE.md's drill.
        conn = sqlite3.connect(str(path), timeout=5)
        try:
            integrity = conn.execute("PRAGMA quick_check").fetchone()
            if not integrity or integrity[0] != "ok":
                return {"ready": False, "reason": f"PRAGMA quick_check did not report 'ok': {integrity}"}
            draft_facts_rows = conn.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0]
            db_version_row = conn.execute("SELECT value FROM meta WHERE key='database_version'").fetchone()
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {"ready": False, "reason": f"Engine database at {path} is not readable: {e}"}
    return {
        "ready": True,
        "db_path": str(path),
        "db_size_bytes": path.stat().st_size,
        "database_version": db_version_row[0] if db_version_row else None,
        "draft_facts_row_count": draft_facts_rows,
    }
