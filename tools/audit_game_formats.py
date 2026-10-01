#!/usr/bin/env python3
"""Print the Reads game-format audit as JSON.

Exit code 0 means the registry/public-mode integrity gate passed. Reaching the
100-distinct-format product target is reported separately and does not make CI
fail while the remaining genuinely new formats are still being built.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.director_v02.format_audit import audit_snapshot  # noqa: E402


def main() -> int:
    snapshot = audit_snapshot()
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0 if snapshot["passes_integrity_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
