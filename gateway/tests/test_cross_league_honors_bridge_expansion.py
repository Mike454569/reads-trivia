"""Absolute Final Closeout: CROSS_LEAGUE_HONORS bridge expansion.

Both All-American -> NFL All-Pro and All-American -> NFL Pro Bowl used to
resolve identity via a fragile double-DISPLAY-NAME join against
nfl_cfb_player_links (124 total rows, match_status='AUTO_HIGH' only) --
real pools of just 4 and 11 players, "too thin to sustain a mode" per the
audit that flagged them. Rebuilt on cfb_nfl_identity_bridge_certified
(7,745 rows, real cfb_player_id -> nfl_player_key ID join, already
certified and already used elsewhere in this codebase for CFB Who Am I) --
real, measured pools grew to 117 and 137 players. A legitimate expansion
(a real, already-verified, better bridge existed and was simply unused),
never a fabricated one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools import game_director_v01 as v01  # noqa: E402
from tools.quiz_export.adapters import cfb_all_american_to_all_pro as aa2ap  # noqa: E402
from tools.quiz_export.adapters import cfb_all_american_to_pro_bowl as aa2pb  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _generate(adapter, predicate: str, seed: str, target_count: int = 200):
    spec = {
        "competition_id": "NFL", "mechanic": "guess", "entity_type": "cross_league_player",
        "relationship_predicate": predicate, "object_type": "player", "answer_type": "player",
        "group_size": 4, "filters": {},
    }
    return v01.generate_package_from_spec(
        spec, adapter, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


def test_all_american_to_all_pro_pool_is_no_longer_near_empty():
    pkg = _generate(aa2ap, "ALL_AMERICAN_TO_ALL_PRO", "pytest-aa2ap-pool")
    assert len(pkg["questions"]) > 50, "the old 4-candidate pool is the exact bug this fix closes"


def test_all_american_to_pro_bowl_pool_is_no_longer_near_empty():
    pkg = _generate(aa2pb, "ALL_AMERICAN_TO_PRO_BOWL", "pytest-aa2pb-pool")
    assert len(pkg["questions"]) > 50


def test_cross_league_honors_uses_the_certified_id_bridge_not_a_name_join():
    """Structural guard: the fetch query must join on cfb_player_id (a real
    ID), never a display-name column, which is what made the old bridge
    fragile."""
    import inspect
    from tools.quiz_export.adapters import _cross_league_honors_common as common

    src = inspect.getsource(common.fetch_ordered_candidates)
    assert "cfb_nfl_identity_bridge_certified" in src
    assert "nfl_cfb_player_links" not in src


def test_a_real_known_cross_league_honoree_is_reachable():
    """Jamal Adams: real 2016 college football All-American DB (LSU), real
    NFL All-Pro -- a concrete, verifiable example the expanded bridge must
    surface, not just a raw count."""
    pkg = _generate(aa2ap, "ALL_AMERICAN_TO_ALL_PRO", "pytest-aa2ap-jamal", target_count=500)
    answers = {q["options"][q["correctIndex"]] for q in pkg["questions"]}
    assert "Jamal Adams" in answers


def test_distractors_are_always_other_real_cross_league_honorees():
    """Every option (correct answer or distractor) must be a real player
    somewhere in the FULL underlying eligible pool -- checked against the
    real pool directly, not just against whichever subset happened to
    become a "correct answer" within one generated sample (a real name can
    legitimately appear only as a distractor across an entire run if
    duplicate-question collisions keep it from ever being drawn as the
    correct answer itself)."""
    c = engine_bootstrap.connect()
    try:
        full_pool = {
            r[0] for r in c.execute(
                "SELECT DISTINCT cp.display_name FROM cfb_all_america_certified aa "
                "JOIN cfb_nfl_identity_bridge_certified br ON br.cfb_player_id = aa.cfb_player_id "
                "JOIN nfl_all_pro_selections h ON h.player_id = br.nfl_player_key "
                "JOIN canonical_players cp ON cp.player_id = br.nfl_player_key"
            )
        }
    finally:
        c.close()
    pkg = _generate(aa2ap, "ALL_AMERICAN_TO_ALL_PRO", "pytest-aa2ap-distractors")
    for q in pkg["questions"]:
        for opt in q["options"]:
            assert opt in full_pool, f"{opt!r} is not a real player in the full eligible pool"
