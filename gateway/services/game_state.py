"""Reads Engine Gateway -- mutable per-game-session state.

packages.py is deliberately content-addressed and immutable: save_package()
raises PackageCollision if you try to persist different content under the
same package_id (Part E's duplicate-ID integrity guarantee). That is the
right contract for generated puzzle DEFINITIONS, but Coach Connections v2's
progressive-reveal mechanic needs something packages.py explicitly refuses
to be: a record that legitimately changes after creation (the discovered
path grows one real, server-validated node at a time).

Six Degrees v1 (public_six_degrees.py) avoided ever needing this by keeping
the puzzle package immutable and round-tripping progress (step_index)
through the CLIENT instead -- safe there because the "correct" answer for
step N is fixed and looked up server-side purely by index, so a client can't
forge progress. Coach Connections v2 can't reuse that trick: paths are
open-ended and multi-route (Part 7 of the rebuild spec explicitly requires
accepting more than one canonical path), so the server must know the
player's TRUE last-validated node to check the next move against -- trusting
a client-supplied "current position" would let a client claim to already be
standing next to the target without ever having walked a real, validated
chain there. So this state has to live server-side and really change.

Same on-disk safety technique packages.py already uses (id allowlist regex
before any path join, atomic write-tmp-then-replace) -- just without the
content-collision restriction, since mutation is the entire point here.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from .. import config

STATE_ID_RE = re.compile(r"^GGP4?:[0-9a-f]{24}$")  # same shape as packages.PACKAGE_ID_RE -- state is always keyed by a real game_id

_write_lock = threading.Lock()


class StateIdInvalid(ValueError):
    pass


def _safe_path_for_id(state_id: str) -> Path:
    if not isinstance(state_id, str) or not STATE_ID_RE.match(state_id):
        raise StateIdInvalid(f"invalid game_id format: {state_id!r}")
    safe_name = state_id.replace(":", "_") + ".json"
    path = (config.GAME_STATE_DIR / safe_name).resolve()
    if path.parent != config.GAME_STATE_DIR.resolve():
        raise StateIdInvalid("resolved game_state path escaped the game_state directory")
    return path


def create_state(state_id: str, state: dict) -> dict:
    """First write for a given game_id. Unlike save_package(), a second
    create_state() call for the same id is just an overwrite -- generation
    already guarantees game_id uniqueness (content hash of a fresh random
    seed), so collision here would only mean a genuine retry, not corrupt
    state."""
    return save_state(state_id, state)


def save_state(state_id: str, state: dict) -> dict:
    path = _safe_path_for_id(state_id)
    config.GAME_STATE_DIR.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(state, ensure_ascii=False, default=str), encoding="utf-8")
        tmp_path.replace(path)  # atomic on POSIX
    return state


def load_state(state_id: str) -> dict | None:
    path = _safe_path_for_id(state_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
