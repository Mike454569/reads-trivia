from pathlib import Path

import pytest

from gateway.errors import GatewayError
from gateway.services import game_state, public_formats, public_game, public_mechanics

ROOT = Path(__file__).resolve().parents[2]


def test_unified_question_start_delegates_and_normalizes(monkeypatch):
    monkeypatch.setitem(public_game.PUBLIC_MODES, "_test_question", {
        "competition": "NFL",
        "title": "Test Question",
        "instructions": "Pick one.",
        "kind": "multiple_choice",
    })
    monkeypatch.setattr(public_game, "get_public_game", lambda **kwargs: {
        "game_id": "GGPTESTQUESTION",
        "mode": "_test_question",
        "competition": "NFL",
        "difficulty": "medium",
        "title": "Test Question",
        "instructions": "Pick one.",
        "payload": {
            "prompt": "Which one?",
            "options": ["A", "B"],
            "visual_template": "DEFAULT_MULTIPLE_CHOICE",
            "visual_payload": None,
        },
        "metadata": {"contract_version": 1},
    })

    result = public_formats.start_public_format(mode="_test_question")

    assert result["round_id"] == "GGPTESTQUESTION"
    assert result["engine_kind"] == "question"
    assert result["view"]["prompt"] == "Which one?"
    assert result["view"]["options"] == ["A", "B"]


def test_unified_mechanic_start_delegates_and_normalizes(monkeypatch):
    monkeypatch.setitem(public_mechanics.PUBLIC_MECHANIC_MODES, "_test_mechanic", {
        "competition": "NFL",
        "title": "Test Mechanic",
        "instructions": "Do the thing.",
        "kind": "matching",
    })
    monkeypatch.setattr(public_mechanics, "start_public_round", lambda **kwargs: {
        "round_id": "GGPTESTMECHANIC",
        "mode": "_test_mechanic",
        "title": "Test Mechanic",
        "kind": "matching",
        "instructions": "Do the thing.",
        "metadata": {"contract_version": 1},
        "view": {"completed": False, "left_items": [], "right_items": []},
    })

    result = public_formats.start_public_format(mode="_test_mechanic")

    assert result["round_id"] == "GGPTESTMECHANIC"
    assert result["engine_kind"] == "mechanic"
    assert result["kind"] == "matching"
    assert result["view"]["completed"] is False


def test_unified_submit_routes_mechanic_from_server_owned_state(monkeypatch):
    monkeypatch.setattr(game_state, "load_state", lambda round_id: {
        "public_mode": "_test_mechanic",
        "taxonomy_id": "MATCHING",
    })
    monkeypatch.setattr(public_mechanics, "submit_public_round", lambda **kwargs: {
        "round_id": kwargs["round_id"],
        "mode": "_test_mechanic",
        "result": {"correct": True},
        "view": {"completed": True},
    })

    result = public_formats.submit_public_format(
        round_id="GGPTESTMECHANIC",
        submission={"mapping": {"L0": "R0"}},
    )

    assert result["engine_kind"] == "mechanic"
    assert result["result"]["correct"] is True


def test_unified_submit_routes_question_without_client_backend_hint(monkeypatch):
    monkeypatch.setattr(game_state, "load_state", lambda round_id: None)
    monkeypatch.setattr(public_game, "validate_public_answer", lambda **kwargs: {
        "correct": kwargs["answer"] == "A",
        "canonical_answer": "A",
        "notes": None,
    })

    result = public_formats.submit_public_format(
        round_id="GGPTESTQUESTION",
        submission={"answer": "A"},
    )

    assert result["engine_kind"] == "question"
    assert result["result"]["correct"] is True


def test_question_submit_requires_answer(monkeypatch):
    monkeypatch.setattr(game_state, "load_state", lambda round_id: None)
    with pytest.raises(GatewayError) as exc:
        public_formats.submit_public_format(round_id="GGPTESTQUESTION", submission={})
    assert exc.value.code == "INVALID_REQUEST"


def test_engine_ui_uses_only_unified_format_network_contract():
    source = (ROOT / "engine-game-ui.js").read_text(encoding="utf-8")
    assert "/v1/public/formats/round" in source
    assert "enginePilotFetchJson('/v1/public/game" not in source
    assert "enginePilotFetchJson('/v1/public/mechanics/round" not in source
