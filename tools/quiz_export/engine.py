"""Engine bootstrap, in one place instead of triplicated per exporter script.

Director v0.7, Part D: ENGINE_DIR is overridable via the `READS_ENGINE_DIR`
environment variable. `game_factory.py` itself (Engine code, never modified
by this project) resolves its own DB file as `Path(__file__).parent /
'reads_football_v4.0.sqlite'` -- i.e. the sqlite file MUST live alongside
the Engine's own .py modules, so this module overrides the whole Engine
directory (modules + database together), not a database file path
independent of it. See READS_ENGINE_STAGING_GAP_ANALYSIS.md for why a
separate, independently-settable DB-path env var was considered and
rejected as architecturally dishonest given that constraint.

v1.4, Part 2: the original v0.7 default here was a hardcoded path on one
specific developer's machine (`/Users/<name>/Downloads/...`) -- acceptable
at the time as a "every existing local call site stays byte-for-byte
unaffected" convenience, but a real liability once this module is audited
as part of production deployment: it's not even this project's current
maintainer's path anymore, and "production must resolve its engine
location through deployment-safe configuration, never a guessed personal
directory" is explicit. `READS_ENGINE_DIR` is required now -- every real
call site (every test, every Gateway process, local or staging) already
sets it explicitly (confirmed: no test file in gateway/tests/ omits it).
An unset var resolves to a sentinel that is obviously not a real path
(rather than silently pointing at a stranger's Downloads folder), so
`check_engine_readiness()`'s existing `ENGINE_DIR.is_dir()` check still
fails closed with an honest, honestly-labeled reason -- no new failure
mode, just no misleading value in it.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import threading
import time
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("READS_ENGINE_DIR") or "/READS_ENGINE_DIR-not-set")
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


_READINESS_CACHE: dict = {"result": None, "checked_at": 0.0}
_READINESS_CACHE_TTL_READY_SECONDS = 300.0   # 5 min -- steady-state healthy result
_READINESS_CACHE_TTL_NOT_READY_SECONDS = 15.0  # re-check a real problem promptly
_readiness_lock = threading.Lock()


def check_engine_readiness() -> dict:
    """Part D/L, cached + de-duplicated as of the Final Go-Live Operation's
    real production deployment (Mission E) -- and, as of the readiness-
    latency incident below, no longer runs `PRAGMA quick_check` on this hot
    path at all.

    Real root cause, found on live production, not assumed: `PRAGMA
    quick_check` measured ~10s locally but 166s against the real production
    Fly.io volume for this 1.65GB database (Fly's block storage has
    meaningfully worse random-I/O throughput than a local dev SSD for the
    scattered page-walk quick_check performs). The caching/locking added
    during the Final Go-Live Operation (below) correctly de-duplicates
    concurrent callers so only one quick_check runs at a time -- but it does
    nothing for the FIRST call after a cold start or cache-expiry, which is
    exactly when Fly's health checker is polling and exactly when a 166s
    stall reads as `context deadline exceeded` and pulls the machine out of
    rotation. A readiness probe that can independently take almost three
    minutes is a latency bug regardless of how well it's deduplicated.

    Fix: `PRAGMA quick_check` is no longer part of what "ready" means for a
    live-traffic health probe. Readiness now answers only "can this process
    actually serve gameplay right now" -- file exists, database opens, a
    real lightweight query against a real table succeeds, the schema-version
    marker is present. Each of those is a fast, indexed, small-I/O operation
    (confirmed fast even against the same slow Fly volume, since none of
    them walk the whole file the way quick_check does). Full structural
    integrity verification still exists -- see `check_engine_readiness_deep()`
    below -- just no longer on the polled hot path.

    Reliability pass (Pass 2.6): this function is also what gateway/app.py's
    lifespan handler now calls at startup (it used to call the DEEP check
    there instead -- a real, measured 6-8 minute outage on every deploy,
    since nothing could be served while that ran). The deep check still
    runs, just as a background task (gateway/app.py's
    _run_periodic_deep_integrity_check()) started right after this fast
    check passes, off the request-serving critical path -- see that
    function's docstring, and the admin-gated deep-diagnostic route, for
    where it actually runs now.

    The cache/lock machinery below is kept (harmless, still avoids redundant
    concurrent work for the now-fast check, and needed no behavior change to
    stay correct) -- TTLs unchanged: 5 min when healthy, 15s when not."""
    cached = _READINESS_CACHE["result"]
    if cached is not None:
        ttl = _READINESS_CACHE_TTL_READY_SECONDS if cached["ready"] else _READINESS_CACHE_TTL_NOT_READY_SECONDS
        if time.monotonic() - _READINESS_CACHE["checked_at"] < ttl:
            return cached
    with _readiness_lock:
        # Re-check inside the lock: another thread may have just refreshed
        # the cache while this caller was waiting for the lock.
        cached = _READINESS_CACHE["result"]
        if cached is not None:
            ttl = _READINESS_CACHE_TTL_READY_SECONDS if cached["ready"] else _READINESS_CACHE_TTL_NOT_READY_SECONDS
            if time.monotonic() - _READINESS_CACHE["checked_at"] < ttl:
                return cached
        result = _check_engine_readiness_uncached(deep=False)
        _READINESS_CACHE["result"] = result
        _READINESS_CACHE["checked_at"] = time.monotonic()
        return result


def check_engine_readiness_deep() -> dict:
    """The full structural integrity certification (`PRAGMA quick_check`
    included) -- deliberately NEVER cached, NEVER on the polled `/v1/ready`
    hot path, and never invoked automatically per-request. Real, current
    uses only: gateway/app.py's `_run_periodic_deep_integrity_check()`
    background task (started once per process boot, after a short initial
    delay, then on a fixed interval for the life of the process -- see that
    function's own docstring) and the admin-gated
    `/v1/admin/diagnostics/db-integrity?force=true` route for on-demand
    deep verification.

    Reliability pass (Pass 2.6): this used to also run synchronously,
    once, inside gateway/app.py's lifespan startup handler -- "a real
    ~166s cost against the production volume is acceptable exactly once at
    startup" turned out to be wrong in practice: nothing could be served
    (including Fly's own health checks) while that ran, so it was a real,
    measured 6-8 minute total outage on every single deploy, not a one-time
    cost paid quietly in the background. See check_engine_readiness()'s own
    docstring for the incident this split originally fixed, and
    gateway/app.py's _run_periodic_deep_integrity_check() for the incident
    THIS pass fixed."""
    return _check_engine_readiness_uncached(deep=True)


def _check_engine_readiness_uncached(*, deep: bool) -> dict:
    """Part D/L: the fail-closed check `sqlite3.connect()` alone does NOT
    give you -- connecting to a MISSING path silently creates an empty file
    (confirmed empirically, see READS_ENGINE_STAGING_GAP_ANALYSIS.md) rather
    than raising. Never raises itself; always returns a structured result so
    a readiness endpoint can report exactly what's wrong rather than 500ing.

    `deep=False` (the hot path, via check_engine_readiness()): file
    exists/non-empty, database opens, one real lightweight query against a
    real table succeeds (`draft_facts` count), the schema-version marker
    (`meta`) is present -- every one of these is small, indexed I/O, fast
    even against a slow disk. `deep=True` (check_engine_readiness_deep()
    only) additionally runs `PRAGMA quick_check` -- see that function's
    docstring for why this is no longer unconditional.

    v1.4, Part 6: every failure branch also returns a stable `reason_code`
    (e.g. "DB_FILE_MISSING") alongside the detailed `reason` string. The
    detailed string embeds a real filesystem path -- fine for the startup
    log (gateway/app.py's lifespan handler, an operator-only stderr
    stream) but not for GET /v1/ready's PUBLIC, unauthenticated JSON body,
    which exposes `reason_code` only (see app.py's ready() route) -- a
    public health endpoint must not reveal server filesystem paths."""
    path = db_path()
    if not ENGINE_DIR.is_dir():
        return {"ready": False, "reason_code": "DIR_MISSING",
                "reason": f"READS_ENGINE_DIR does not exist or is not a directory: {ENGINE_DIR}"}
    if not path.exists():
        return {"ready": False, "reason_code": "DB_FILE_MISSING",
                "reason": f"Engine database file not found at {path} -- refusing to auto-create one."}
    if path.stat().st_size == 0:
        return {"ready": False, "reason_code": "DB_FILE_EMPTY",
                "reason": f"Engine database file at {path} is empty (0 bytes)."}
    try:
        # sqlite3.connect() on an existing-but-garbage file still succeeds --
        # a real query against a real table is what actually proves this is
        # a readable, structurally usable database, not just a file that
        # opens.
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
            if deep:
                integrity = conn.execute("PRAGMA quick_check").fetchone()
                if not integrity or integrity[0] != "ok":
                    return {"ready": False, "reason_code": "INTEGRITY_CHECK_FAILED",
                            "reason": f"PRAGMA quick_check did not report 'ok': {integrity}"}
            draft_facts_rows = conn.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0]
            db_version_row = conn.execute("SELECT value FROM meta WHERE key='database_version'").fetchone()
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {"ready": False, "reason_code": "DB_NOT_READABLE",
                "reason": f"Engine database at {path} is not readable: {e}"}
    return {
        "ready": True,
        "db_path": str(path),
        "db_size_bytes": path.stat().st_size,
        "database_version": db_version_row[0] if db_version_row else None,
        "draft_facts_row_count": draft_facts_rows,
        "deep_integrity_checked": deep,
    }
