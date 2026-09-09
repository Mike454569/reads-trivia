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
