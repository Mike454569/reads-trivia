"""Natural-language Creator reachability for WEEKLY_PICKEM and
LIVE_WEEKLY_FANTASY_DRAFT (post Phase 7 Creator audit). Both mechanics were
already fully playable through POST /v1/creator/mechanics/round, but a
plain-English request through POST /v1/creator/generate never reached
either one -- neither has a (mechanic, domain, relationship_predicate)
triple, so the normal translator/registry pipeline could never resolve to
them. This file exercises the real Gateway HTTP routes (not the bridge
module in isolation) for exactly the phrasing this reachability fix targets.
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


def _resolve_real_future_nfl_week() -> tuple[int, str]:
    """Same real, dynamic resolver test_weekly_pickem.py's own
    _resolve_real_future_nfl_week() established -- a hardcoded week number
    (this file's own previous `2026, "1"`) is real and future when written,
    but goes stale the moment the real calendar catches up to it (confirmed
    live this pass: by the time this suite ran again, every week-1 game had
    already kicked off, so the app's own real "picks close at kickoff"
    logic correctly rejected it -- the test broke, not the app). Picks the
    earliest NFL week, in the latest season the Engine has real schedule
    data for, whose games all start after today's real date."""
    from datetime import datetime, timezone
    c = engine_bootstrap.connect()
    try:
        season = c.execute("SELECT MAX(season) FROM games WHERE game_type='REG'").fetchone()[0]
        today = datetime.now(timezone.utc).date().isoformat()
        row = c.execute(
            "SELECT week FROM games WHERE season = ? AND game_type = 'REG' "
            "GROUP BY week HAVING MIN(game_date) > ? ORDER BY CAST(week AS INTEGER) LIMIT 1",
            (season, today),
        ).fetchone()
        if row is None:
            raise RuntimeError(
                f"No fully-future NFL week found for season {season} as of {today} -- "
                f"the real Engine schedule may need a refresh."
            )
        return season, str(row["week"])
    finally:
        c.close()


# Real, confirmed-live schedule windows (same fixtures test_weekly_pickem.py
# and test_live_weekly_fantasy_draft.py already use) -- used only for the
# full generate->submit playthroughs below, never for the pure routing
# assertions (those must pass regardless of what real data happens to exist
# for the auto-resolved current week). NFL_SEASON/NFL_WEEK are resolved
# dynamically (see above) rather than hardcoded, since the whole point of
# this fixture is to always name a genuinely still-open real week.
#
# Guarded the same way test_weekly_pickem.py's own module-level resolution
# is: pytest's skipif marker only skips test FUNCTIONS, not module-level
# code run at collection time -- without this guard, an environment with
# no READS_ENGINE_DIR would crash collection instead of cleanly skipping
# every test in this file (the placeholder is never actually used, since
# every test that depends on it is skipped in that case).
if engine_bootstrap.ENGINE_DIR.is_dir():
    NFL_SEASON, NFL_WEEK = _resolve_real_future_nfl_week()
else:
    NFL_SEASON, NFL_WEEK = 1900, "1"
CFB_SEASON, CFB_WEEK = 2025, 1             # real CFB schedule + rosters, confirmed live


def _feasibility(client, auth_headers, text):
    r = client.post("/v1/creator/feasibility", json={"request_text": text}, headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


# --- Required routing tests (1-7) -------------------------------------------
# Routing is asserted via /v1/creator/feasibility, which always returns 200
# and reports taxonomy_id/variant whenever the natural-language bridge
# matched -- independent of whether a real slate/pool happens to exist for
# the auto-resolved current week, so these are pure classification checks.

def test_weekly_nfl_pickem_phrase_routes_to_weekly_pickem_nfl(client, auth_headers):
    f = _feasibility(client, auth_headers, "Make me a weekly NFL pick’em for week 1.")
    assert f["taxonomy_id"] == "WEEKLY_PICKEM"
    assert f["variant"] == "NFL_WEEKLY_PICKEM"
    assert f["week"] == "1"


def test_college_football_pickem_phrase_routes_to_weekly_pickem_cfb(client, auth_headers):
    f = _feasibility(client, auth_headers, "Give me a college football pick’em for week 1.")
    assert f["taxonomy_id"] == "WEEKLY_PICKEM"
    assert f["variant"] == "CFB_WEEKLY_PICKEM"
    assert f["week"] == "1"


def test_nfl_fantasy_draft_phrase_routes_to_fantasy_draft_nfl(client, auth_headers):
    f = _feasibility(client, auth_headers, "Start an NFL weekly fantasy draft.")
    assert f["taxonomy_id"] == "LIVE_WEEKLY_FANTASY_DRAFT"
    assert f["variant"] == "NFL_WEEKLY_FANTASY_DRAFT"


def test_college_football_fantasy_draft_phrase_routes_to_fantasy_draft_cfb(client, auth_headers):
    f = _feasibility(client, auth_headers, "Make me a college football fantasy draft.")
    assert f["taxonomy_id"] == "LIVE_WEEKLY_FANTASY_DRAFT"
    assert f["variant"] == "CFB_WEEKLY_FANTASY_DRAFT"


def test_historical_game_result_question_does_not_route_to_pickem(client, auth_headers):
    f = _feasibility(client, auth_headers, "Who won the Alabama game?")
    assert "taxonomy_id" not in f
    assert f["support_status"] in feasibility_statuses()


def test_who_drafted_question_does_not_route_to_fantasy_draft(client, auth_headers):
    f = _feasibility(client, auth_headers, "Who drafted this player?")
    assert "taxonomy_id" not in f


def test_draft_round_question_does_not_route_to_fantasy_draft(client, auth_headers):
    f = _feasibility(client, auth_headers, "What round was this player drafted in?")
    assert "taxonomy_id" not in f


def feasibility_statuses():
    from tools.director_v02 import feasibility as feasibility_mod
    return feasibility_mod.SUPPORT_STATUSES


# --- Additional phrasing coverage (spec's "recognize variations" list) -----

@pytest.mark.parametrize("text,expected_taxonomy", [
    ("pick the winners of each game", "WEEKLY_PICKEM"),
    ("choose the winner of each game", "WEEKLY_PICKEM"),
    ("NFL picks this week", "WEEKLY_PICKEM"),
    ("college football picks", "WEEKLY_PICKEM"),
    ("pick every game this week", "WEEKLY_PICKEM"),
    ("weekly football predictions", "WEEKLY_PICKEM"),
    ("fantasy draft", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("draft a fantasy team", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("NFL fantasy draft this week", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("college football fantasy draft", "LIVE_WEEKLY_FANTASY_DRAFT"),
    ("build a fantasy lineup from this week's players", "LIVE_WEEKLY_FANTASY_DRAFT"),
])
def test_additional_phrasing_variations_route_correctly(client, auth_headers, text, expected_taxonomy):
    f = _feasibility(client, auth_headers, text)
    assert f["taxonomy_id"] == expected_taxonomy, (text, f)


@pytest.mark.parametrize("text", [
    "Guess which team drafted this NFL player.",
    "Who won the Super Bowl in 2023?",
    "Guess the winner of a real NFL game.",
    "How many draft picks does this team have this year?",
])
def test_unrelated_or_draft_trivia_phrasing_never_routes_to_bridge(client, auth_headers, text):
    f = _feasibility(client, auth_headers, text)
    assert "taxonomy_id" not in f, (text, f)


# --- Required test 8 / Acceptance test: real end-to-end playthroughs -------
# Not enough to classify correctly -- the resulting Creator response must
# actually be playable: a real generated slate/pool, a real valid
# submission, and a real resulting state/view.

def test_pickem_natural_language_playthrough_is_actually_playable(client, auth_headers):
    text = f"Make me a weekly NFL pick’em for week {NFL_WEEK}."
    gen = client.post("/v1/creator/generate", json={"request_text": text}, headers=auth_headers)
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["taxonomy_id"] == "WEEKLY_PICKEM"
    round_id = body["round_id"]
    view = body["view"]
    assert view["season"] == NFL_SEASON and view["week"] == NFL_WEEK
    assert view["game_count"] >= 1

    # Pick the first genuinely still-open game, not just games[0] -- NFL_WEEK
    # names a real, identifiable week, but doesn't promise every game in it
    # is still unplayed (mid-week, the earlier slate has already kicked off
    # even though the week overall is still real/current). A real player
    # picking games for "this week" would skip the ones already locked too.
    open_games = [g for g in view["games"] if g["status"] == "SCHEDULED"]
    assert open_games, f"no still-open game in {NFL_SEASON} week {NFL_WEEK} -- pick a later real week"
    first_game = open_games[0]
    sub = client.post(
        f"/v1/creator/mechanics/round/{round_id}/submit",
        json={"submission": {"game_id": first_game["game_id"], "predicted_winner": first_game["home_team_code"]}},
        headers=auth_headers,
    )
    assert sub.status_code == 200, sub.text
    result = sub.json()
    assert result["result"]["status"] == "PENDING"
    assert result["view"]["picks_made"] == 1

    resumed = client.get(f"/v1/creator/mechanics/round/{round_id}", headers=auth_headers)
    assert resumed.status_code == 200
    assert resumed.json()["view"]["picks_made"] == 1


def test_fantasy_draft_natural_language_playthrough_is_actually_playable(client, auth_headers):
    text = f"Start an NFL weekly fantasy draft for {NFL_SEASON} week {NFL_WEEK}."
    gen = client.post("/v1/creator/generate", json={"request_text": text}, headers=auth_headers)
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["taxonomy_id"] == "LIVE_WEEKLY_FANTASY_DRAFT"
    round_id = body["round_id"]
    view = body["view"]
    assert view["remaining_pool_size"] >= 1
    assert view["picks_made"] == 0

    first_pick = view["remaining_pool"][0]
    sub = client.post(
        f"/v1/creator/mechanics/round/{round_id}/submit",
        json={"submission": {"player_id": first_pick["player_id"]}},
        headers=auth_headers,
    )
    assert sub.status_code == 200, sub.text
    result = sub.json()
    assert result["view"]["picks_made"] == 1
    assert result["view"]["roster"][0]["player_id"] == first_pick["player_id"]


def test_cfb_fantasy_draft_natural_language_playthrough_with_explicit_season_is_playable(client, auth_headers):
    text = f"Make me a college football fantasy draft for {CFB_SEASON}, week {CFB_WEEK}."
    gen = client.post("/v1/creator/generate", json={"request_text": text}, headers=auth_headers)
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["taxonomy_id"] == "LIVE_WEEKLY_FANTASY_DRAFT"
    assert body["view"]["remaining_pool_size"] >= 1

    first_pick = body["view"]["remaining_pool"][0]
    sub = client.post(
        f"/v1/creator/mechanics/round/{body['round_id']}/submit",
        json={"submission": {"player_id": first_pick["player_id"]}},
        headers=auth_headers,
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["view"]["picks_made"] == 1


# --- Missing-current-week honesty: current CFB pick'em/fantasy requests with
# no real schedule data yet must fail honestly (NO_ELIGIBLE_GAME), never
# fabricate a slate/pool. -----------------------------------------------------

def test_cfb_pickem_with_no_resolvable_current_week_fails_honestly_not_silently(client, auth_headers):
    from tools.director_v04 import nl_schedule_bridge

    bridged = nl_schedule_bridge.detect("Give me a college football pick’em for this week.")
    assert bridged["taxonomy_id"] == "WEEKLY_PICKEM"
    if bridged["week"] is not None:
        pytest.skip("Real current-season CFB schedule data now exists -- honest-failure path not reachable.")

    gen = client.post(
        "/v1/creator/generate", json={"request_text": "Give me a college football pick’em for this week."},
        headers=auth_headers,
    )
    assert gen.status_code != 200
    assert gen.json()["error"]["code"] == "NO_ELIGIBLE_GAME"
