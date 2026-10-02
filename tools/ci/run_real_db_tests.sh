#!/bin/sh
set -eu

cd /tmp/reads-ci
rm -rf /tmp/ci-python /tmp/ci-packages /tmp/ci-game-state /tmp/ci-logs
mkdir -p /tmp/ci-packages /tmp/ci-game-state /tmp/ci-logs

python -m pip install --no-cache-dir --target /tmp/ci-python -r gateway/requirements-dev.txt

export PYTHONPATH=/tmp/ci-python:/tmp/reads-ci
export READS_ENGINE_DIR=/data/engine
export READS_ENGINE_PACKAGES_DIR=/tmp/ci-packages
export READS_ENGINE_GAME_STATE_DIR=/tmp/ci-game-state
export READS_ENGINE_LOG_DIR=/tmp/ci-logs
export CI_ONLY_DB_TESTS=1

python - <<'PY'
import os
import sqlite3

path = "/data/engine/reads_football_v4.0.sqlite"
size = os.path.getsize(path)
if size <= 100 * 1024 * 1024:
    raise SystemExit(f"Real DB is unexpectedly small: {size} bytes")

con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
try:
    row = con.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='games'"
    ).fetchone()
    if not row or row[0] != 1:
        raise SystemExit("Forked DB is missing the games table")
    game_count = con.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    if game_count <= 0:
        raise SystemExit("Forked Reads DB has an empty games table")
    print(f"Validated forked real DB: {size} bytes, games={game_count}")
finally:
    con.close()
PY

# Heavy integrity/stress work belongs on this disposable production-volume
# fork, never on the live serving volume.
python - <<'PY'
from tools.quiz_export import engine as e
result = e.check_engine_readiness_deep()
print("Isolated deep Engine integrity:", result)
if not result.get("ready"):
    raise SystemExit("Deep Engine integrity failed on production-volume fork")
PY

python - <<'PY'
from tools.quiz_export import engine as e
from tools.director_v05.performance_indexes import install
c=e.connect()
try:
    print("Fork performance indexes:", install(c))
finally:
    c.close()
PY

python -m tools.director_v05.stress_harness \
  --max-facts-per-adapter 5000 --max-players 1000 --out /tmp/v05-stress.json
python - <<'PY'
import json
from tools.director_v05.stress_certification import assert_certified
result=json.load(open("/tmp/v05-stress.json"))
print("Fork v0.5 stress certification:", assert_certified(result))
PY

python - <<'PY'
from tools.data_refresh.repair_capability_catalog_drift import repair_missing_catalog_rows
print("Catalog drift repair:", repair_missing_catalog_rows())
PY

python - <<'PY'
from tools.director_v02.generate_schema_and_prompt import verify_anthropic_prompt
print("Anthropic prompt/catalog diff:", verify_anthropic_prompt())
PY

# The sibling pytest job already covers every DB-independent test. Here we
# select only node IDs empirically proven to need the real warehouse, which
# removes duplicate work and lets Fly surface real integration regressions.
# Fail fast while this gate is being stabilized so the first failing node is
# visible instead of being hidden behind a remote-session timeout.
python -m pytest gateway/tests -x -vv --tb=short
