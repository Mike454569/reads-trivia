"""Public-readiness punch-list -- capability_catalog.public_availability
must never drift from the real routing truth (gateway/config.py's
PUBLIC_MODE_ALLOWLIST, via public_game.py's PUBLIC_MODES). A real, found
mismatch (14 rows claimed PUBLIC_ENABLED while unreachable) was corrected
by tools.director_v02.catalog.recompute_public_availability() -- this test
file is what keeps it from silently drifting again.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_public_availability_matches_real_public_mode_allowlist():
    """The real invariant: a capability_catalog row's public_availability
    is PUBLIC_ENABLED if and only if its (domain, relationship_predicate)
    is the spec of a real entry in public_game.PUBLIC_MODES (the table
    /v1/public/game actually routes through) -- never a separately
    hand-maintained claim that can go stale."""
    from gateway.services import public_game

    public_predicates = {
        (entry["spec"]["domain"], entry["spec"]["relationship_predicate"])
        for entry in public_game.PUBLIC_MODES.values()
    }

    c = engine_bootstrap.connect()
    try:
        rows = c.execute(
            "SELECT capability_id, domain, relationship_predicate, public_availability FROM capability_catalog"
        ).fetchall()
    finally:
        c.close()

    assert rows
    mismatches = []
    for row in rows:
        really_public = (row["domain"], row["relationship_predicate"]) in public_predicates
        claims_public = row["public_availability"] == "PUBLIC_ENABLED"
        if really_public != claims_public:
            mismatches.append(dict(row))
    assert not mismatches, f"public_availability drifted from PUBLIC_MODE_ALLOWLIST truth: {mismatches}"


def test_recompute_public_availability_is_idempotent_and_matches_allowlist():
    from tools.director_v02 import catalog
    from gateway.services import public_game

    c = engine_bootstrap.connect()
    try:
        result = catalog.recompute_public_availability(c)
        assert result["rows_corrected"] == 0, "recompute should be a no-op when already correct"

        public_predicates = {
            (entry["spec"]["domain"], entry["spec"]["relationship_predicate"])
            for entry in public_game.PUBLIC_MODES.values()
        }
        rows = c.execute("SELECT domain, relationship_predicate, public_availability FROM capability_catalog").fetchall()
    finally:
        c.close()

    for row in rows:
        expected = "PUBLIC_ENABLED" if (row["domain"], row["relationship_predicate"]) in public_predicates else "PRIVATE"
        assert row["public_availability"] == expected


def test_lineup_college_guess_is_a_real_public_mode():
    """The one real, deliberate exposure decision this pass made: the
    lineup-college variant, only after its starvation fix was verified."""
    from gateway.services import public_game
    from gateway import config as gateway_config

    assert "lineup_college_guess" in public_game.PUBLIC_MODES
    assert "lineup_college_guess" in gateway_config.PUBLIC_MODE_ALLOWLIST
    entry = public_game.PUBLIC_MODES["lineup_college_guess"]
    assert entry["spec"]["domain"] == "NFL_OFFENSE_LINEUP_COLLEGE"
