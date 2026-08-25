"""Final Technical Risk Cleanup pass: regression tests for the package_id
collision risk found during the prior phase's own production verification.

Real incident this guards against: every director_v04 build_package()
(and game_director_v01.generate_package_from_spec()) hashed only the
GENERATION PARAMETERS (mechanic, variant, seed, counts...) into package_id,
never a generator/schema version. tools/director_v04/elimination.py's
generation logic changed (excluding unresolved-season candidates) without
changing package_id's inputs at all -- so re-generating with the exact
same (variant, seed, sequence_length) used before the fix produced
DIFFERENT real content under the SAME package_id, and
gateway/services/packages.py's save_package() correctly rejected it as a
PackageCollision (verified live on production: package_id
GGP7:180cfb0ff04041f7111ab062, seed="mechanics-round", sequence_length=10).

The fix: every one of these package_id hashes now includes that module's
PACKAGE_SCHEMA_VERSION (already a real, pre-existing field on every
package -- just never part of the hash). Old already-stored package files
are untouched and still load by their original id (package_id's hash
FORMULA changing doesn't touch anything already on disk); a version bump
after a real logic change now guarantees a fresh, non-colliding id for the
same seed/params, without inventing any new ID scheme or resorting to
randomness.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.director_v04 import (  # noqa: E402
    elimination, higher_lower, matching, sorting, weekly_pickem, live_weekly_fantasy_draft,
    player_from_clues, cfb_player_from_clues,
)

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def test_elimination_same_seed_across_the_real_pre_fix_version_does_not_collide(monkeypatch):
    """The literal real-world incident: seed='mechanics-round',
    variant=NFL_SUPER_BOWL_CHAMPION_SURVIVAL, sequence_length=10, generated
    once under PACKAGE_SCHEMA_VERSION='1.0' (the pre-fix logic) and again
    under '1.1' (the fixed logic) -- must never produce the same
    package_id, precisely because that's what a real save_package() call
    would reject as a PackageCollision if they matched."""
    monkeypatch.setattr(elimination, "PACKAGE_SCHEMA_VERSION", "1.0")
    pkg_v1 = elimination.build_package("mechanics-round", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    monkeypatch.setattr(elimination, "PACKAGE_SCHEMA_VERSION", "1.1")
    pkg_v2 = elimination.build_package("mechanics-round", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    assert pkg_v1["package_id"] != pkg_v2["package_id"]
    assert pkg_v1["package_version"] == "1.0"
    assert pkg_v2["package_version"] == "1.1"


@pytest.mark.parametrize("build_fn, args, kwargs", [
    (elimination.build_package, ("collision-test-seed", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL"), {"sequence_length": 10}),
    (higher_lower.build_package, ("collision-test-seed", "NFL_TEAM_SEASON_WINS"), {"sequence_length": 10}),
    (matching.build_package, ("collision-test-seed", "NFL_DRAFT_CLASS_MATCH"), {"round_count": 5, "pair_count": 4}),
    (sorting.build_package, ("collision-test-seed", "NFL_DRAFT_PICK_ORDER"), {"round_count": 5, "item_count": 4}),
])
def test_same_seed_different_schema_version_never_collides(monkeypatch, build_fn, args, kwargs):
    """Generic guard across every director_v04 mechanic sharing this exact
    package_id-hash pattern: bumping PACKAGE_SCHEMA_VERSION with identical
    seed/params must always change package_id, never reuse it."""
    module = sys.modules[build_fn.__module__]
    original_version = module.PACKAGE_SCHEMA_VERSION
    try:
        monkeypatch.setattr(module, "PACKAGE_SCHEMA_VERSION", "test-version-a")
        pkg_a = build_fn(*args, **kwargs)
        monkeypatch.setattr(module, "PACKAGE_SCHEMA_VERSION", "test-version-b")
        pkg_b = build_fn(*args, **kwargs)
    finally:
        monkeypatch.setattr(module, "PACKAGE_SCHEMA_VERSION", original_version)
    assert pkg_a["package_id"] != pkg_b["package_id"], (
        f"{build_fn.__module__}.build_package produced the same package_id under two different "
        f"PACKAGE_SCHEMA_VERSION values for identical seed/params -- the version fix isn't wired into the hash"
    )


def test_elimination_same_seed_same_version_is_still_fully_deterministic():
    """The fix must not break the pre-existing determinism guarantee --
    identical inputs (including version) must always produce the identical
    package_id, so idempotent re-generation still works."""
    pkg_1 = elimination.build_package("determinism-check", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    pkg_2 = elimination.build_package("determinism-check", "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", sequence_length=10)
    assert pkg_1["package_id"] == pkg_2["package_id"]


def test_player_from_clues_nfl_and_cfb_schema_version_in_hash(monkeypatch):
    """NFL/CFB Who Am I (GGP4) share the same hash pattern -- explicitly
    covered since these are the two capabilities named in this pass's own
    regression list."""
    monkeypatch.setattr(player_from_clues, "PACKAGE_SCHEMA_VERSION", "test-version-a")
    pkg_a = player_from_clues.build_package("who-am-i-collision-test", target_count=3)
    monkeypatch.setattr(player_from_clues, "PACKAGE_SCHEMA_VERSION", "test-version-b")
    pkg_b = player_from_clues.build_package("who-am-i-collision-test", target_count=3)
    assert pkg_a["package_id"] != pkg_b["package_id"]

    monkeypatch.setattr(cfb_player_from_clues, "PACKAGE_SCHEMA_VERSION", "test-version-a")
    cfb_pkg_a = cfb_player_from_clues.build_package("cfb-who-am-i-collision-test", target_count=3)
    monkeypatch.setattr(cfb_player_from_clues, "PACKAGE_SCHEMA_VERSION", "test-version-b")
    cfb_pkg_b = cfb_player_from_clues.build_package("cfb-who-am-i-collision-test", target_count=3)
    assert cfb_pkg_a["package_id"] != cfb_pkg_b["package_id"]


def test_game_director_guess_packages_include_package_version_in_hash():
    """GGP: (mechanic='guess', the highest-traffic capability family) uses a
    `package_version` call-time parameter (registry.py's own
    PACKAGE_SCHEMA_VERSION, passed through by every real caller) rather
    than a bare game_director_v01 module constant -- confirm the hash
    still varies with whatever value is actually passed, using the real
    registered NFL Draft ("guess", "NFL_DRAFT", "DRAFTED_BY") capability."""
    from tools import game_director_v01
    from tools.director_v02.registry import CAPABILITY_REGISTRY

    capability = CAPABILITY_REGISTRY[("guess", "NFL_DRAFT", "DRAFTED_BY")]
    adapter = capability["adapter"]
    factory_spec = {
        "competition_id": capability["competition_id"], "mechanic": "guess",
        "entity_type": capability["entity_type"], "relationship_predicate": "DRAFTED_BY",
        "object_type": capability["object_type"], "answer_type": capability["answer_type"],
        "group_size": capability["group_size"], "filters": {},
    }
    pkg_a = game_director_v01.generate_package_from_spec(
        factory_spec, adapter, request_text="package-id version test", director_request_id="test-req-a",
        seed="version-collision-test", target_count=3, package_version="test-version-a",
    )
    pkg_b = game_director_v01.generate_package_from_spec(
        factory_spec, adapter, request_text="package-id version test", director_request_id="test-req-b",
        seed="version-collision-test", target_count=3, package_version="test-version-b",
    )
    assert pkg_a["package_id"] != pkg_b["package_id"]
