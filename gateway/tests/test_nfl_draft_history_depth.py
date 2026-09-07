"""Absolute Final Closeout: NFL Draft History's real depth fix.

Two real, compounding bugs found by direct measurement, not assumed:

1. resolve_franchise()/teams_active_in_season() both queried team_aliases
   with no fallback -- that table's own real coverage floor is 2002 (a
   data-collection start date, not evidence a team_code first existed
   then). 6,526 of 12,927 real draft_facts rows (50.5%) predate 2002, and
   32 of the 37 real distinct pre-2002 draft_team codes already appear in
   team_aliases under a LATER season_start -- every one of those was
   rejected as TEAM_UNRESOLVED (or its distractor pool came back empty)
   purely from this resolver gap, not a real data gap.
2. CANDIDATE_LIMIT=500 was an arbitrary historical default against a real
   12,927-row universe, not a measured performance ceiling.
3. The vendored Engine's own difficulty score (never modified) structurally
   never produces EASY for this domain (0 of 3,340 real generated
   questions banded EASY) -- a real, adapter-level override using round/
   pick/recency (legitimate proxies for "recognizable", never fabricated)
   fixes this without touching vendored code.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters import draft  # noqa: E402
from tools import game_director_v01 as v01  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)


def _generate(seed: str, target_count: int = 5000):
    return v01.generate_package_from_spec(
        dict(draft._SPEC), draft, request_text="pytest", director_request_id="pytest",
        seed=seed, target_count=target_count, id_start=1,
    )


def test_a_real_pre_2002_pick_now_resolves():
    """Jeff George, real 1990 #1 overall pick by the Indianapolis Colts --
    used to be rejected TEAM_UNRESOLVED purely because team_aliases' own
    earliest 'IND' row starts in 2002, 12 years after this real pick."""
    c = engine_bootstrap.connect()
    try:
        correct, err = draft._resolve_franchise_with_legacy_codes(c, "IND", 1990)
    finally:
        c.close()
    assert err is None
    assert correct["full_name"] == "Indianapolis Colts"


def test_pre_2002_seasons_have_a_real_full_distractor_pool():
    c = engine_bootstrap.connect()
    try:
        pool = draft.teams_active_in_season(c, 1985)
    finally:
        c.close()
    assert len(pool) >= 28, "a real historical season must have a real, near-complete distractor pool"


def test_legacy_codes_resolve_to_their_real_modern_franchise():
    c = engine_bootstrap.connect()
    try:
        for code, expected_name in [
            ("PHO", "Arizona Cardinals"), ("TAM", "Tampa Bay Buccaneers"),
            ("LARD", "Oakland Raiders"), ("LARM", "Los Angeles Rams"), ("BAL1", "Indianapolis Colts"),
        ]:
            correct, err = draft._resolve_franchise_with_legacy_codes(c, code, 1988)
            assert err is None, f"{code} should resolve via the real legacy-code map"
            assert correct["full_name"] == expected_name
    finally:
        c.close()


def test_effective_playable_universe_is_dramatically_larger_than_the_old_ceiling():
    """Real, measured before/after: the old CANDIDATE_LIMIT=500 with the
    unfixed resolver produced ~204 effective real questions. The fix
    (resolver + CANDIDATE_LIMIT=5000) must produce a materially larger
    real pool -- checked generously (>1500) rather than pinned to today's
    exact measured 3,325, since real data volume grows over time."""
    pkg = _generate("pytest-draft-universe-check")
    assert pkg["qa_status"] == "PASSED"
    assert len(pkg["questions"]) > 1500


def test_team_unresolved_rejection_rate_is_now_a_small_minority():
    pkg = _generate("pytest-draft-rejection-rate")
    rejected = pkg["funnel"]["rejected_counts"]
    considered = pkg["funnel"]["considered"]
    team_unresolved = rejected.get("TEAM_UNRESOLVED", 0)
    assert team_unresolved / considered < 0.20, (
        f"TEAM_UNRESOLVED is {team_unresolved}/{considered} ({team_unresolved/considered:.1%}) -- "
        f"still a majority-rejection rate, the exact bug this fix closes"
    )


def test_real_easy_content_now_exists():
    pkg = _generate("pytest-draft-easy-check")
    easy = [q for q in pkg["questions"] if q["difficulty"] == "Easy"]
    assert len(easy) > 50, "NFL Draft History must reliably produce real Easy questions"
    medium = [q for q in pkg["questions"] if q["difficulty"] == "Medium"]
    hard = [q for q in pkg["questions"] if q["difficulty"] == "Hard"]
    assert medium and hard, "Medium/Hard depth must not regress while adding Easy"


def test_easy_questions_are_real_top_picks_or_recent_first_rounders():
    """The override must be grounded in real signals, never arbitrary --
    every Easy question's underlying pick must genuinely be a top-10
    overall pick or a real round-1 pick from a recent draft. The exported
    package strips _audit, so this looks the player back up by name
    (parsed from the question text) directly against draft_facts."""
    pkg = _generate("pytest-draft-easy-grounding")
    c = engine_bootstrap.connect()
    try:
        checked = 0
        for q in pkg["questions"]:
            if q["difficulty"] != "Easy":
                continue
            player_name = q["question"].removeprefix("Which NFL team drafted ").rstrip("?")
            correct_team = q["options"][q["correctIndex"]]
            rows = c.execute(
                "SELECT draft_round, draft_pick_overall, draft_season FROM draft_facts "
                "WHERE player_name=? AND draft_round=1", (player_name,),
            ).fetchall()
            assert rows, f"{player_name!r} (Easy) has no real round-1 draft_facts row at all"
            assert any(
                (r["draft_pick_overall"] or 999) <= 10 or r["draft_season"] >= draft._RECENT_SEASON_FLOOR
                for r in rows
            ), f"{player_name!r} (Easy) has no real row matching the top-10-pick or recent-round-1 criteria"
            checked += 1
        assert checked > 50
    finally:
        c.close()


def test_difficulty_override_never_downgrades_a_real_deep_cut_to_easy():
    assert draft._real_difficulty_override(7, 250, 1985) is None
    assert draft._real_difficulty_override(3, 90, 2020) is None
    assert draft._real_difficulty_override(1, 5, 1985) == "Easy"
    assert draft._real_difficulty_override(1, 32, 2024) == "Easy"
