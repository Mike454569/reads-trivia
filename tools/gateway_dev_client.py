#!/usr/bin/env python3
"""Director v0.6, Part O -- local dev harness proving:

    Reads local browser -> Gateway -> Director -> Warehouse -> QA
    -> GeneratedGamePackage -> Reads renderer

This is a Python script, deliberately NOT browser JavaScript, because doing
this from the browser would require putting READS_ENGINE_ADMIN_TOKEN into
client-side code -- explicitly forbidden by Part R. This script stands in
for "a trusted local admin tool" -- it reads the admin token from the same
environment variable the Gateway itself uses, calls the real running
Gateway over HTTP, and writes the result to a file the Reads frontend can
load like any other static data file.

Usage:
    READS_ENGINE_ADMIN_TOKEN=... python3 tools/gateway_dev_client.py \\
        --gateway-url http://127.0.0.1:8850 \\
        --request "Make me a game where you give me clues about an NFL player and I have to identify him." \\
        --puzzle-count 5 --seed gateway-dev-loop

Writes data/player-from-clues-gateway-dev.js (window.PLAYER_FROM_CLUES_GATEWAY_DEV),
a file completely separate from the existing static baseline
(data/player-from-clues-v01.js / window.PLAYER_FROM_CLUES_V01), which this
script never touches. The Reads frontend only reads from the gateway-dev
file when a SEPARATE, default-off flag
(ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01 in app.js) is explicitly turned
on -- see PLAYER_FROM_CLUES_FRONTEND_INTEGRATION_PLAN.md and
READS_ENGINE_GATEWAY_V01_REPORT.md, Part O, for why.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.export_player_from_clues_frontend import convert  # noqa: E402  reused, not duplicated

OUTPUT_JS = REPO_ROOT / "data" / "player-from-clues-gateway-dev.js"
ADMIN_TOKEN_ENV_VAR = "READS_ENGINE_ADMIN_TOKEN"


def call_gateway(gateway_url: str, token: str, *, request_text: str, puzzle_count: int, seed: str) -> dict:
    body = json.dumps({"request_text": request_text, "puzzle_count": puzzle_count, "seed": seed}).encode()
    req = urllib.request.Request(
        f"{gateway_url}/v1/games/generate", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        payload = json.loads(e.read().decode())
        raise SystemExit(f"ABORT: Gateway returned {e.code}: {payload}")


def write_browser_file(package: dict) -> None:
    browser_data = convert(package)
    lines = [
        "// AUTO-GENERATED -- do not hand-edit.",
        "// Produced by tools/gateway_dev_client.py via a LIVE call to the local Reads Engine",
        f"// Gateway (package_id {browser_data['packageId']}) -- NOT the static baseline",
        "// (data/player-from-clues-v01.js). Only loaded by the Reads frontend when",
        "// ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01 is explicitly turned on in app.js --",
        "// see READS_ENGINE_GATEWAY_V01_REPORT.md, Part O.",
        "window.PLAYER_FROM_CLUES_GATEWAY_DEV = " + json.dumps(browser_data, indent=2, ensure_ascii=False) + ";",
    ]
    OUTPUT_JS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_JS.relative_to(REPO_ROOT)} -- {browser_data['puzzleCount']} puzzles from package {browser_data['packageId']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gateway-url", default="http://127.0.0.1:8850")
    ap.add_argument("--request", required=True)
    ap.add_argument("--puzzle-count", type=int, default=5)
    ap.add_argument("--seed", default="gateway-dev-loop")
    args = ap.parse_args()

    token = os.environ.get(ADMIN_TOKEN_ENV_VAR)
    if not token:
        raise SystemExit(f"ABORT: {ADMIN_TOKEN_ENV_VAR} is not set -- this script never hard-codes it.")

    package = call_gateway(args.gateway_url, token, request_text=args.request,
                            puzzle_count=args.puzzle_count, seed=args.seed)
    if not package.get("package_id"):
        raise SystemExit(f"ABORT: Gateway did not return a package: {package}")
    write_browser_file(package)


if __name__ == "__main__":
    main()
