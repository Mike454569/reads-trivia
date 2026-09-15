"""Reusable Game Format System pass -- real, end-to-end tests for FORMAT
selection through the actual Game Creator surfaces: the natural-language
bridge (tools/director_v04/nl_mechanic_bridge.py), the admin
/v1/creator/* routes, and the admin /v1/creator/mechanics/round route
(gateway/app.py). Covers the exact scenarios the format-system spec names:
auto-selection, honoring an explicit compatible request, and a clean
FORMAT_INCOMPATIBLE rejection (never a silent substitution) for an
explicit incompatible one.
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


# --- nl_mechanic_bridge.detect_format() / detect() ---------------------

def test_detect_format_recognizes_timeline_and_bracket_keywords():
    from tools.director_v04 import nl_mechanic_bridge as bridge

    assert bridge.detect_format("give me a sorting game as a timeline") == "TIMELINE_RIBBON"
    assert bridge.detect_format("give me a sorting game with a ribbon") == "TIMELINE_RIBBON"
    assert bridge.detect_format("make me a bracket game") == "BRACKET_TREE"
    assert bridge.detect_format("give me a plain sorting game") is None


def test_detect_returns_bracket_taxonomy_with_the_named_format():
    from tools.director_v04 import nl_mechanic_bridge as bridge

    result = bridge.detect("make me a bracket game about NFL teams")
    assert result == {"taxonomy_id": "COMPARISON_BRACKET", "variant": "NFL_TEAM_SEASON_WINS_BRACKET", "format": "BRACKET_TREE"}

    cfb_result = bridge.detect("make a bracket game for college football")
    assert cfb_result["variant"] == "CFB_TEAM_SEASON_WINS_BRACKET"


def test_detect_stat_ladder_picks_the_right_real_variant():
    from tools.director_v04 import nl_mechanic_bridge as bridge

    assert bridge.detect_format("make a stat ladder with running backs") == "STAT_LADDER"

    running_backs = bridge.detect("make a stat ladder with running backs")
    assert running_backs == {"taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_SEASON_RUSHING_YARDS_LADDER",
                              "format": "STAT_LADDER"}

    quarterbacks = bridge.detect("give me a stat ladder game with quarterbacks")
    assert quarterbacks["variant"] == "NFL_CAREER_PASSING_TD_LADDER"
    assert quarterbacks["format"] == "STAT_LADDER"

    cfb = bridge.detect("make a college football stat ladder")
    assert cfb["variant"] == "CFB_CAREER_RUSHING_YARDS_LADDER"

    casual = bridge.detect("put these stats in order")
    assert casual["taxonomy_id"] == "SORTING_TIMELINE"
    assert casual["format"] == "STAT_LADDER"

    # A plain chronological sorting request must be completely unaffected.
    plain = bridge.detect("put these NFL draft picks in order")
    assert plain == {"taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_DRAFT_PICK_ORDER", "format": None}


def test_detect_stat_ladder_matches_real_stat_phrasing_not_just_the_format_name():
    """Regression guard: the cleanup pass's own required example --
    "Rank these quarterbacks by career passing yards." -- never says "stat
    ladder" at all. Real requests describe the STAT, not the format name;
    the original pattern only recognized the latter."""
    from tools.director_v04 import nl_mechanic_bridge as bridge

    r = bridge.detect("Rank these quarterbacks by career passing yards.")
    assert r is not None
    assert r["taxonomy_id"] == "SORTING_TIMELINE"
    assert r["format"] == "STAT_LADDER"

    r2 = bridge.detect("Order these players by rushing yards.")
    assert r2 is not None and r2["format"] == "STAT_LADDER"
    assert r2["variant"] == "NFL_SEASON_RUSHING_YARDS_LADDER"

    r3 = bridge.detect("Rank these running backs by rushing yards, most to least.")
    assert r3 is not None and r3["format"] == "STAT_LADDER"

    # Must not widen into matching a bare "rank"/"order" with no real stat
    # keyword nearby -- "year" isn't one, so this must NOT be pulled into
    # STAT_LADDER (it also doesn't match the generic _SORTING_RE's own
    # narrower phrasing, so the honest, correct result is no match at all,
    # not a false-positive STAT_LADDER format).
    assert bridge.detect("Order these Heisman winners by year.") is None


def test_detect_map_the_career_real_phrasing_and_league_routing():
    """15-Format Expansion Part 2, format #9: checked BEFORE the generic
    _SORTING_RE fallback -- same real reason STAT_LADDER is -- so a
    career-team-order request resolves to the real MAP_THE_CAREER variant
    instead of the chronological NFL_DRAFT_PICK_ORDER default."""
    from tools.director_v04 import nl_mechanic_bridge as bridge

    r = bridge.detect("map the career game")
    assert r is not None
    assert r["taxonomy_id"] == "SORTING_TIMELINE"
    assert r["format"] == "MAP_THE_CAREER"
    assert r["variant"] == "NFL_PLAYER_CAREER_TEAM_ORDER"

    r2 = bridge.detect("order the teams this player played for")
    assert r2 is not None and r2["format"] == "MAP_THE_CAREER"

    r3 = bridge.detect("college football, map the career game")
    assert r3["variant"] == "CFB_PLAYER_CAREER_SCHOOL_ORDER"

    # A plain chronological sorting request must be completely unaffected.
    plain = bridge.detect("put these NFL draft picks in order")
    assert plain == {"taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_DRAFT_PICK_ORDER", "format": None}


def test_detect_never_matches_an_unrelated_request():
    from tools.director_v04 import nl_mechanic_bridge as bridge

    assert bridge.detect("give me a rivalry game") is None
    assert bridge.detect("who won the Heisman in 1985") is None


# --- gateway/services/creator.py's _resolve_format() --------------------

def test_resolve_format_auto_selects_the_real_documented_default():
    from gateway.services.creator import _resolve_format

    assert _resolve_format("COMPARISON_BRACKET", None) == "BRACKET_TREE"
    assert _resolve_format("SORTING_TIMELINE", None) == "SORT_LIST_DEFAULT"


def test_resolve_format_honors_an_explicit_compatible_request():
    from gateway.services.creator import _resolve_format

    assert _resolve_format("SORTING_TIMELINE", "TIMELINE_RIBBON") == "TIMELINE_RIBBON"
    assert _resolve_format("COMPARISON_BRACKET", "BRACKET_TREE") == "BRACKET_TREE"


def test_resolve_format_rejects_an_explicit_incompatible_request():
    from gateway.errors import GatewayError
    from gateway.services.creator import _resolve_format

    with pytest.raises(GatewayError) as exc_info:
        _resolve_format("SORTING_TIMELINE", "BRACKET_TREE")
    assert exc_info.value.code == "FORMAT_INCOMPATIBLE"
    assert "TIMELINE_RIBBON" in exc_info.value.message or "SORT_LIST_DEFAULT" in exc_info.value.message


# --- Real end-to-end through the actual admin Gateway routes ------------

def test_admin_mechanics_route_generates_a_comparison_bracket_round(client, auth_headers):
    r = client.post(
        "/v1/creator/mechanics/round",
        json={"taxonomy_id": "COMPARISON_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_BRACKET", "seed": "pytest-admin-bracket"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["format_id"] == "BRACKET_TREE"
    assert body["taxonomy_id"] == "COMPARISON_BRACKET"
    assert len(body["view"]["rounds"]) == 3


def test_admin_mechanics_route_rejects_an_incompatible_explicit_format(client, auth_headers):
    r = client.post(
        "/v1/creator/mechanics/round",
        json={"taxonomy_id": "COMPARISON_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_BRACKET",
              "seed": "pytest-admin-bad-format", "format": "TIMELINE_RIBBON"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "FORMAT_INCOMPATIBLE"


def test_creator_nl_generate_resolves_bracket_request_end_to_end(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": "make me an NFL bracket game", "seed": "pytest-nl-bracket"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.json()
    body = r.json()
    assert body["taxonomy_id"] == "COMPARISON_BRACKET"
    assert body["format_id"] == "BRACKET_TREE"


def test_creator_nl_generate_rejects_an_incompatible_nl_format_request(client, auth_headers):
    r = client.post(
        "/v1/creator/generate",
        json={"request_text": "give me a sorting game in a bracket format", "seed": "pytest-nl-bad-format"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "FORMAT_INCOMPATIBLE"


# --- Real end-to-end through the public mechanics route -----------------

def test_public_comparison_bracket_modes_are_discoverable_and_playable(client):
    r = client.get("/v1/public/mechanics/modes")
    assert r.status_code == 200
    modes = {m["mode"] for m in r.json()["modes"]} if isinstance(r.json(), dict) else {m["mode"] for m in r.json()}
    assert "comparison_nfl_wins" in modes
    assert "comparison_cfb_wins" in modes

    r2 = client.get("/v1/public/mechanics/round", params={"mode": "comparison_cfb_wins"})
    assert r2.status_code == 200, r2.json()
    round_id = r2.json()["round_id"]
    m0 = r2.json()["view"]["rounds"][0]["matchups"][0]
    r3 = client.post(f"/v1/public/mechanics/round/{round_id}/submit",
                      json={"submission": {"match_id": m0["match_id"], "predicted_winner": m0["entrant_a"]}})
    assert r3.status_code == 200, r3.json()
    assert "correct" in r3.json()["result"]
