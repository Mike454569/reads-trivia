"""Reliability Design Phase 7B -- LIVE_WEEKLY_FANTASY_DRAFT.

Real single-drafter weekly fantasy roster construction: generator-level
pool correctness (both the GAME_PARTICIPATION_CONFIRMED and
SEASON_ROSTER_MEMBERSHIP reliability tiers, NFL + CFB), no-duplicate-pick
enforcement, position/slot-eligibility validation, stale-state rejection
(the one genuinely new safety property this mechanic needs that no other
one does), completion, deterministic repeat generation, and the
admin-gated Gateway routes end to end. Same real-DB, no-mocking discipline
every other mechanic test in this suite already follows.
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

# Real, confirmed-live fixtures.
NFL_CONFIRMED_SEASON, NFL_CONFIRMED_WEEK = 2025, "1"   # real player_game_stats exist -- GAME_PARTICIPATION_CONFIRMED
NFL_ROSTER_TIER_SEASON, NFL_ROSTER_TIER_WEEK = 2026, "1"  # not yet played -- SEASON_ROSTER_MEMBERSHIP fallback
CFB_SEASON, CFB_WEEK = 2025, 1


# --- generator-level: real NFL + CFB pools, both reliability tiers -------

def test_nfl_confirmed_week_uses_game_participation_tier():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    pkg = lwfd.build_package("t-nfl-confirmed", "NFL_WEEKLY_FANTASY_DRAFT", NFL_CONFIRMED_SEASON, NFL_CONFIRMED_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["pool_source"] == "GAME_PARTICIPATION_CONFIRMED"
    assert pkg["player_count"] > 0
    for pos in ("QB", "RB", "WR", "TE"):
        assert pkg["by_position"].get(pos, 0) > 0, f"no real {pos}s in the confirmed-tier pool"


def test_nfl_future_week_falls_back_to_roster_tier_honestly_disclosed():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    pkg = lwfd.build_package("t-nfl-future", "NFL_WEEKLY_FANTASY_DRAFT", NFL_ROSTER_TIER_SEASON, NFL_ROSTER_TIER_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["pool_source"] == "SEASON_ROSTER_MEMBERSHIP"
    assert pkg["player_count"] > 0


def test_cfb_pool_is_always_season_roster_tier():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    pkg = lwfd.build_package("t-cfb", "CFB_WEEKLY_FANTASY_DRAFT", CFB_SEASON, CFB_WEEK)
    assert pkg["qa_status"] == "PASSED"
    assert pkg["pool_source"] == "SEASON_ROSTER_MEMBERSHIP"
    assert pkg["player_count"] > 0
    for p in pkg["players"][:5]:
        assert p["display_name"] and p["team_display"]


def test_repeat_generation_is_deterministic():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    p1 = lwfd.build_package("same-seed", "NFL_WEEKLY_FANTASY_DRAFT", NFL_CONFIRMED_SEASON, NFL_CONFIRMED_WEEK)
    p2 = lwfd.build_package("same-seed", "NFL_WEEKLY_FANTASY_DRAFT", NFL_CONFIRMED_SEASON, NFL_CONFIRMED_WEEK)
    assert p1["package_id"] == p2["package_id"]
    assert [p["player_id"] for p in p1["players"]] == [p["player_id"] for p in p2["players"]]


# --- feasibility ------------------------------------------------------------

def test_feasibility_supported_for_a_real_week():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    result = lwfd.check_slate_feasibility("NFL_WEEKLY_FANTASY_DRAFT", NFL_CONFIRMED_SEASON, NFL_CONFIRMED_WEEK)
    assert result["support_status"] == "SUPPORTED"
    assert result["real_player_count"] > 0


def test_feasibility_missing_data_never_fabricates_a_pool():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    result = lwfd.check_slate_feasibility("NFL_WEEKLY_FANTASY_DRAFT", NFL_CONFIRMED_SEASON, "99")
    assert result["support_status"] == "MISSING_DATA"
    assert result["real_player_count"] == 0


def test_feasibility_unknown_for_bad_variant():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    result = lwfd.check_slate_feasibility("XFL_WEEKLY_FANTASY_DRAFT", 2025, "1")
    assert result["support_status"] == "UNKNOWN"


# --- mechanic_engine: draft state, duplicate/invalid picks, completion ----

def _fresh_round(seed: str):
    """Every call site passes its OWN unique seed. package_id is a pure
    deterministic hash of (variant, season, week, seed), and game_state.py
    persists to a real, shared-on-disk store keyed by that same id -- two
    tests reusing the same seed would silently share (and, thanks to the
    stale-state guard this phase adds, correctly but confusingly REJECT
    picks against) the exact same on-disk draft state. Real production
    callers avoid this the same way (a genuinely unique seed per session);
    this is a test-isolation requirement, not a mechanic bug."""
    from tools.director_v02 import mechanic_engine
    pkg = mechanic_engine.generate_fantasy_draft_round(
        variant="NFL_WEEKLY_FANTASY_DRAFT", season=NFL_CONFIRMED_SEASON, week=NFL_CONFIRMED_WEEK, seed=seed)
    progress = mechanic_engine.initial_progress("LIVE_WEEKLY_FANTASY_DRAFT")
    return pkg, progress


def test_client_view_exposes_current_slot_and_remaining_pool_no_leakage():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-client-view-exposes-current-slot-and-rem')
    view = mechanic_engine.client_safe_view("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress)
    assert view["current_slot"] == pkg["draft_slots"][0] == "QB"
    assert view["completed"] is False
    assert view["picks_made"] == 0
    assert all(p["position"] == "QB" for p in view["remaining_pool"])
    assert len(view["remaining_pool"]) == view["remaining_pool_size"] > 0
    for marker in ("_audit", "_diagnostics", "production_safety"):
        assert marker not in view


def test_evaluate_rejects_player_not_in_pool():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-evaluate-rejects-player-not-in-pool')
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": "not-a-real-player"})


def test_evaluate_rejects_position_ineligible_for_current_slot():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-evaluate-rejects-position-ineligible-for')
    wr = next(p for p in pkg["players"] if p["position"] == "WR")
    with pytest.raises(mechanic_engine.MechanicError):
        # current slot is QB (slot 0) -- a real WR is not eligible for it
        mechanic_engine.evaluate_submission("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": wr["player_id"]})


def test_evaluate_accepts_a_valid_pick_and_advances_slot():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-evaluate-accepts-a-valid-pick-and-advanc')
    qb = next(p for p in pkg["players"] if p["position"] == "QB")
    result, progress = mechanic_engine.evaluate_submission(
        "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": qb["player_id"]})
    assert result["slot"] == "QB"
    assert result["player_id"] == qb["player_id"]
    assert progress["current_slot_index"] == 1
    assert progress["drafted_player_ids"] == [qb["player_id"]]
    assert progress["state_version"] == 1


def test_no_player_can_be_drafted_twice():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-no-player-can-be-drafted-twice')
    qb = next(p for p in pkg["players"] if p["position"] == "QB")
    _, progress = mechanic_engine.evaluate_submission(
        "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": qb["player_id"]})
    # current slot is now RB -- but even if this same QB somehow matched a
    # later slot, drafting the exact same player again must be rejected.
    rb_slot_but_same_player = qb["player_id"]
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission(
            "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": rb_slot_but_same_player})


def test_flex_slot_accepts_rb_wr_or_te():
    from tools.director_v04 import live_weekly_fantasy_draft as lwfd
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-flex-slot-accepts-rb-wr-or-te')
    # Fill QB, RB, RB, WR, WR, TE (slots 0-5) with real, distinct players so
    # slot 6 (FLEX) is reached, then confirm a real WR is accepted there.
    filled_positions = ["QB", "RB", "RB", "WR", "WR", "TE"]
    used_ids = set()
    for pos in filled_positions:
        player = next(p for p in pkg["players"] if p["position"] == pos and p["player_id"] not in used_ids)
        used_ids.add(player["player_id"])
        _, progress = mechanic_engine.evaluate_submission(
            "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": player["player_id"]})
    assert progress["current_slot_index"] == 6
    assert pkg["draft_slots"][6] == "FLEX"
    flex_pick = next(p for p in pkg["players"] if p["position"] in lwfd.FLEX_ELIGIBLE_POSITIONS
                      and p["player_id"] not in used_ids)
    result, progress = mechanic_engine.evaluate_submission(
        "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": flex_pick["player_id"]})
    assert result["slot"] == "FLEX"
    assert progress["completed"] is True
    assert progress["current_slot_index"] == 7
    view = mechanic_engine.client_safe_view("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress)
    assert view["completed"] is True
    assert view["current_slot"] is None
    assert view["picks_made"] == 7


def test_evaluate_rejects_a_pick_once_the_draft_is_complete():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-evaluate-rejects-a-pick-once-the-draft-i')
    for pos in ["QB", "RB", "RB", "WR", "WR", "TE", "RB"]:  # 7th (extra RB) fills FLEX too
        player = next(p for p in pkg["players"]
                       if p["position"] == pos and p["player_id"] not in progress.get("drafted_player_ids", []))
        _, progress = mechanic_engine.evaluate_submission(
            "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": player["player_id"]})
    assert progress["completed"] is True
    extra = next(p for p in pkg["players"] if p["player_id"] not in progress["drafted_player_ids"])
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": extra["player_id"]})


def test_stale_draft_state_is_rejected_not_silently_overwritten():
    """The one real, new safety property this mechanic needs: a submit
    call built from an OLD progress snapshot (someone else's pick already
    landed on disk since) must fail loudly, never silently clobber the
    newer real state."""
    from tools.director_v02 import mechanic_engine
    from gateway.services import game_state

    pkg, progress = _fresh_round('t-stale-draft-state-is-rejected-not-silent')
    round_id = pkg["package_id"]
    game_state.create_state(round_id, progress)

    qb = next(p for p in pkg["players"] if p["position"] == "QB")
    result, newer_progress = mechanic_engine.evaluate_submission(
        "LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": qb["player_id"]})
    game_state.save_state(round_id, newer_progress)  # a real newer write already landed

    # A second caller still holding the OLD (pre-pick) progress snapshot
    # tries to submit against it -- must be rejected as stale, not applied.
    rb = next(p for p in pkg["players"] if p["position"] == "QB" and p["player_id"] != qb["player_id"])
    with pytest.raises(mechanic_engine.MechanicError, match="stale"):
        mechanic_engine.evaluate_submission("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": rb["player_id"]})

    # The real, on-disk state must be exactly the newer one -- untouched.
    on_disk = game_state.load_state(round_id)
    assert on_disk["drafted_player_ids"] == [qb["player_id"]]


def test_malformed_submission_fails_safely():
    from tools.director_v02 import mechanic_engine
    pkg, progress = _fresh_round('t-malformed-submission-fails-safely')
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {})
    with pytest.raises(mechanic_engine.MechanicError):
        mechanic_engine.evaluate_submission("LIVE_WEEKLY_FANTASY_DRAFT", pkg, progress, {"player_id": None})


# --- Gateway routes, admin-gated, end to end -------------------------------

def test_mechanics_round_requires_admin_for_fantasy_draft(client):
    r = client.post("/v1/creator/mechanics/round", json={
        "taxonomy_id": "LIVE_WEEKLY_FANTASY_DRAFT", "variant": "NFL_WEEKLY_FANTASY_DRAFT",
        "season": NFL_CONFIRMED_SEASON, "week": NFL_CONFIRMED_WEEK,
    })
    assert r.status_code == 401


def test_mechanics_round_rejects_missing_season_or_week(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "LIVE_WEEKLY_FANTASY_DRAFT", "variant": "NFL_WEEKLY_FANTASY_DRAFT"},
                     headers=auth_headers)
    assert r.status_code == 400


def test_mechanics_round_rejects_unknown_variant(client, auth_headers):
    r = client.post("/v1/creator/mechanics/round",
                     json={"taxonomy_id": "LIVE_WEEKLY_FANTASY_DRAFT", "variant": "XFL_WEEKLY_FANTASY_DRAFT",
                           "season": 2025, "week": "1"},
                     headers=auth_headers)
    assert r.status_code == 400


def test_fantasy_draft_full_round_trip_generate_pick_resume(client, auth_headers):
    gen = client.post("/v1/creator/mechanics/round", json={
        "taxonomy_id": "LIVE_WEEKLY_FANTASY_DRAFT", "variant": "NFL_WEEKLY_FANTASY_DRAFT",
        "season": NFL_CONFIRMED_SEASON, "week": NFL_CONFIRMED_WEEK, "seed": "route-draft-e2e",
    }, headers=auth_headers)
    assert gen.status_code == 200
    body = gen.json()
    round_id = body["round_id"]
    assert body["view"]["current_slot"] == "QB"
    qb_id = body["view"]["remaining_pool"][0]["player_id"]

    sub = client.post(f"/v1/creator/mechanics/round/{round_id}/submit",
                       json={"submission": {"player_id": qb_id}}, headers=auth_headers)
    assert sub.status_code == 200
    assert sub.json()["result"]["slot"] == "QB"
    assert sub.json()["view"]["current_slot"] == "RB"

    resumed = client.get(f"/v1/creator/mechanics/round/{round_id}", headers=auth_headers)
    assert resumed.status_code == 200
    assert resumed.json()["view"]["picks_made"] == 1
    assert resumed.json()["view"]["current_slot"] == "RB"

    # Deterministic restoration of an existing draft state -- a second
    # fetch reproduces the exact same view, not a re-randomized one.
    resumed_again = client.get(f"/v1/creator/mechanics/round/{round_id}", headers=auth_headers)
    assert resumed_again.json()["view"] == resumed.json()["view"]
