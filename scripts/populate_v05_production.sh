#!/usr/bin/env bash
set -euo pipefail
APP=reads-football-gateway
MACHINE=$(flyctl machines list -a "$APP" --json | python3 scripts/select_prod_machine.py)
flyctl ssh console -a "$APP" --machine "$MACHINE" -C "cd /app && READS_ENGINE_DIR=/data/engine python3 -m tools.director_v05.populate_knowledge"
