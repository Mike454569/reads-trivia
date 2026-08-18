"""Public-readiness punch-list, item 6 -- natural-language Creator
reachability for MATCHING/SORTING_TIMELINE/HIGHER_LOWER_STREAK/
ELIMINATION_SURVIVAL/POSITION_LINEUP_GRID.
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


@pytest.mark.parametrize("text,expected_taxonomy,expected_league", [
    ("Make me a matching game.", "MATCHING", "NFL"),
    ("Match these players to their teams.", "MATCHING", "NFL"),
    ("Give me a football matching game.", "MATCHING", "NFL"),
    ("Give me a CFB matching game.", "MATCHING", "CFB"),
    ("Make me sort these players in order.", "SORTING_TIMELINE", "NFL"),
    ("Put these draft picks in order.", "SORTING_TIMELINE", "NFL"),
    ("Give me a football sorting game.", "SORTING_TIMELINE", "NFL"),
    ("Give me a college football sorting game.", "SORTING_TIMELINE", "CFB"),
    ("Give me a higher or lower game.", "HIGHER_LOWER_STREAK", "NFL"),
    ("Make me choose who had more yards.", "HIGHER_LOWER_STREAK", "NFL"),
    ("Higher or lower with NFL stats.", "HIGHER_LOWER_STREAK", "NFL"),
    ("Make me an elimination game.", "ELIMINATION_SURVIVAL", "NFL"),
    ("Give me an odd-one-out football game.", "ELIMINATION_SURVIVAL", "NFL"),
    ("Keep eliminating the one that doesn't belong.", "ELIMINATION_SURVIVAL", "NFL"),
    ("Make me guess the team from the lineup.", "POSITION_LINEUP_GRID", None),
    ("Give me a lineup grid.", "POSITION_LINEUP_GRID", None),
    ("Guess the NFL team from its offensive players.", "POSITION_LINEUP_GRID", None),
])
def test_recognized_phrases_route_to_the_real_mechanic(text, expected_taxonomy, expected_league):
    from tools.director_v04 import nl_mechanic_bridge

    result = nl_mechanic_bridge.detect(text)
    assert result is not None, f"expected a match for {text!r}"
    assert result["taxonomy_id"] == expected_taxonomy
    from tools.director_v02 import mechanic_engine
    assert result["variant"] in mechanic_engine.VARIANTS[expected_taxonomy]
    if expected_league:
        assert expected_league in result["variant"] or (expected_league == "NFL" and "NFL" in result["variant"])


@pytest.mark.parametrize("text", [
    "Guess the CFB team from its lineup.",  # no real CFB lineup variant -- must never false-route to NFL
    "Guess the winner of a game.",
    "Who drafted this player?",
    "Tell me about your favorite pizza toppings.",
])
def test_unrecognized_or_unsupported_phrases_never_match(text):
    from tools.director_v04 import nl_mechanic_bridge

    assert nl_mechanic_bridge.detect(text) is None


def test_cfb_lineup_request_is_never_silently_routed_to_nfl():
    """The specific, explicit acceptance criterion: a CFB lineup ask must
    never receive an NFL lineup game."""
    from tools.director_v04 import nl_mechanic_bridge

    for text in ["Guess the CFB team from its lineup.", "Give me a college football lineup grid.",
                 "Guess the college football team from its offensive players."]:
        assert nl_mechanic_bridge.detect(text) is None, f"{text!r} must not match (no real CFB lineup variant)"


# --- End-to-end through the real Creator routes -----------------------------

def test_creator_feasibility_reports_supported_for_bridged_mechanics(client, auth_headers):
    r = client.post("/v1/creator/feasibility", json={"request_text": "Make me a matching game."}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["support_status"] == "SUPPORTED"
    assert body["taxonomy_id"] == "MATCHING"


@pytest.mark.parametrize("text", [
    "Make me a matching game.",
    "Give me a higher or lower game.",
    "Give me a lineup grid.",
    "Make me an elimination game.",
    "Make me sort these players in order.",
])
def test_creator_generate_produces_a_real_playable_round_for_bridged_mechanics(text, client, auth_headers):
    r = client.post("/v1/creator/generate", json={"request_text": text}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body.get("round_id"), f"no round_id in response for {text!r}: {body}"
    assert body.get("view") is not None
