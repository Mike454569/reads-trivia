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
export CI_REAL_DB_ONLY=1

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

python -m pytest gateway/tests -q --maxfail=20
