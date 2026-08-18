"""Reads Engine Gateway -- generated-package repository (Part E).

Local filesystem storage, exactly as the milestone allows for v0.6. Every
requirement from Part E is implemented here and only here -- no route
handler touches the filesystem directly.

Package ID format is fixed and pre-existing (not invented by the Gateway):
`GGP:<24 hex chars>` (v0.1-v0.3, guess-mechanic packages, reused as-is by
POSITION_LINEUP_GRID -- same mechanic="guess" contract), `GGP4:<24 hex
chars>` (v0.4+, Player From Clues / PROGRESSIVE_CLUE_IDENTIFY), and, added
in Reliability Design Phase 6 for the four genuinely new mechanic
templates, `GGP5:` (MATCHING), `GGP6:` (SORTING_TIMELINE), `GGP7:`
(ELIMINATION_SURVIVAL), `GGP8:` (HIGHER_LOWER_STREAK), and, added in Phase
7A, `GGP9:` (WEEKLY_PICKEM) -- all are `"GGP" + optional single version
digit + ":" + sha256(...)[:24]`, the same extension pattern GGP4 already
established (a new mechanic gets the next digit, never a new ID scheme).
Produced by `game_director_v01.
generate_package_from_spec()` / `player_from_clues.build_package()` /
`tools/director_v04/{matching,sorting,elimination,higher_lower,weekly_pickem}.py`'s own
`build_package()` functions. `_safe_filename_for_id()` is the ONLY place a
package_id ever touches a filesystem path, and it does so through a strict
allowlist regex first -- never through direct string interpolation into a
path.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from .. import config

PACKAGE_ID_RE = re.compile(r"^GGP[4-9]?:[0-9a-f]{24}$")

_write_lock = threading.Lock()


class PackageIdInvalid(ValueError):
    pass


class PackageCollision(ValueError):
    """A package with this ID already exists with DIFFERENT content -- since
    package_id is a deterministic hash of (request/spec, seed, predicate),
    this should be mathematically unreachable in practice; treated as a hard
    integrity error rather than silently overwritten if it ever happens."""
    pass


def _safe_filename_for_id(package_id: str) -> Path:
    """The only function in this module allowed to build a filesystem path
    from a package_id. Validates against a strict allowlist regex BEFORE
    any path construction -- `../`, absolute paths, null bytes, or any
    character outside the fixed GGP(4)?:[0-9a-f]{24} shape is rejected
    outright, never sanitized-and-used."""
    if not isinstance(package_id, str) or not PACKAGE_ID_RE.match(package_id):
        raise PackageIdInvalid(f"invalid package_id format: {package_id!r}")
    safe_name = package_id.replace(":", "_") + ".json"
    path = (config.PACKAGES_DIR / safe_name).resolve()
    if path.parent != config.PACKAGES_DIR.resolve():
        # Defense in depth -- should be unreachable given the regex above,
        # since a matching package_id cannot contain "/" or "..", but the
        # resolved-parent check is cheap insurance against a future regex
        # change accidentally widening what's allowed.
        raise PackageIdInvalid("resolved package path escaped the packages directory")
    return path


def _content_fingerprint(package: dict) -> str:
    """Hash of everything except wall-clock/storage timestamps -- used only
    to detect a genuine content collision under the same package_id (Part E:
    duplicate-ID protection), not for any security purpose."""
    comparable = {k: v for k, v in package.items() if k not in ("generated_at", "gateway_stored_at")}
    return hashlib.sha256(json.dumps(comparable, sort_keys=True, default=str).encode()).hexdigest()


def save_package(package: dict, *, review_status: str = "GENERATED") -> dict:
    """Validates minimally (package_id present and well-formed, qa_status
    PASSED -- Part E: "schema validation before persistence"), then writes
    atomically (write to a temp file, then os.replace -- POSIX-atomic
    rename, never a partially-written file visible under the real name).
    Returns the stored record (including the fields this function adds)."""
    package_id = package.get("package_id")
    if not package_id:
        raise ValueError("package has no package_id -- refusing to persist")
    if package.get("qa_status") != "PASSED":
        raise ValueError(f"package qa_status is {package.get('qa_status')!r}, not PASSED -- refusing to persist")

    path = _safe_filename_for_id(package_id)
    config.PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    record = dict(package)
    # Part E's review-status vocabulary (GENERATED/REVIEWED/APPROVED/REJECTED)
    # is deliberately DIFFERENT from the "UNREVIEWED" every Director v0.1-v0.5
    # generate_fn already stamps onto every package -- an explicit assignment
    # here (not setdefault) so the Gateway's own contract always wins, never
    # silently inherits the older per-package convention.
    record["review_status"] = review_status
    record["gateway_stored_at"] = datetime.now(timezone.utc).isoformat()

    with _write_lock:
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if _content_fingerprint(existing) == _content_fingerprint(record):
                return existing  # identical content under the same deterministic ID -- idempotent, not an error
            raise PackageCollision(
                f"package_id {package_id} already exists with different content -- "
                f"this should be unreachable given package_id is a content hash"
            )
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        tmp_path.replace(path)  # atomic on POSIX
    return record


def load_package(package_id: str) -> dict | None:
    """Returns the stored record, or None if not found. Raises
    PackageIdInvalid for a malformed ID -- callers map that to the same
    PACKAGE_NOT_FOUND response a real missing package gets (never
    distinguishing "malformed" from "missing" to a client, which would leak
    information about the validation rule for free)."""
    path = _safe_filename_for_id(package_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


REVIEW_STATUSES = frozenset({"GENERATED", "REVIEWED", "APPROVED", "REJECTED"})
# Part E's own vocabulary (module docstring) -- GENERATED is the only status
# save_package() itself ever writes; the other three are set later, by a
# human decision, via set_review_status() below.
MUTABLE_REVIEW_STATUSES = REVIEW_STATUSES - {"GENERATED"}


def set_review_status(package_id: str, review_status: str) -> dict:
    """v1.8, Part G/H -- the Game Creator's approve/reject step. Deliberately
    NOT implemented as save_package(dict(record, review_status=...)): that
    function's collision check (Part E) treats ANY content difference under
    the same package_id as a hard integrity error, and review_status is
    genuinely mutable human-review metadata layered on top of an otherwise
    content-addressed, immutable package -- not a content collision. This is
    a separate, narrow, explicit code path instead: load, validate, mutate
    exactly one field (+ a `reviewed_at` timestamp), atomic overwrite.

    Approving a package here does NOT make it publicly servable -- see
    gateway/services/public_game.py's PUBLIC_MODE_ALLOWLIST module docstring:
    public exposure is always a separate, deliberate code-level certification
    decision, never a side effect of an admin review action. See
    READS_ENGINE_V18_FINAL_BUILD_AND_LAUNCH_REPORT.md, Game Creator section,
    for why that boundary is deliberate, not a missing feature."""
    if review_status not in MUTABLE_REVIEW_STATUSES:
        raise ValueError(f"review_status must be one of {sorted(MUTABLE_REVIEW_STATUSES)}, got {review_status!r}")
    path = _safe_filename_for_id(package_id)
    with _write_lock:
        if not path.exists():
            raise FileNotFoundError(f"no such package: {package_id}")
        record = json.loads(path.read_text(encoding="utf-8"))
        record["review_status"] = review_status
        record["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
        tmp_path.replace(path)
    return record


def list_packages(*, review_status: str | None = None, limit: int = 100) -> list[dict]:
    """v1.8, Part G -- lightweight summaries (not full package bodies, which
    can each be tens of KB with every question) for the Creator's review
    queue. A real directory scan, not a database query -- packages.py has no
    index beyond the filesystem itself, and this is admin-only, low-traffic
    content-ops tooling (Part G explicitly does not need database-scale
    performance)."""
    config.PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    for path in sorted(config.PACKAGES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue  # a stray/corrupt file must never break the whole listing
        if review_status is not None and record.get("review_status") != review_status:
            continue
        summaries.append({
            "package_id": record.get("package_id"),
            "game_title": record.get("game_title"),
            "review_status": record.get("review_status"),
            "qa_status": record.get("qa_status"),
            "question_count": record.get("question_count"),
            "requested_description": record.get("requested_description"),
            "gateway_stored_at": record.get("gateway_stored_at"),
            "reviewed_at": record.get("reviewed_at"),
            "capability": {
                "mechanic": (record.get("parsed_spec") or {}).get("mechanic"),
                "relationship_predicate": (record.get("parsed_spec") or {}).get("relationship_predicate"),
            },
        })
        if len(summaries) >= limit:
            break
    return summaries
