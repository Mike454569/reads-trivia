"""Isolated regression tests: never serve a rejected trivia question again.

All generation is mocked. These tests use no real Engine database, network,
Fly.io resources, or paid services.
"""
import pytest

from gateway.errors import GatewayError
from gateway.services import public_game


def _mock_generator(monkeypatch, *, entity_key="board:repeat"):
    calls = []
    def generate(**kwargs):
        calls.append(kwargs)
        return {
            "package_id": "GGP:" + "a" * 24,
            "qa_status": "PASSED",
            "questions": [{"entity_key": entity_key}],
        }
    monkeypatch.setattr(public_game.generation, "generate_public", generate)
    monkeypatch.setattr(public_game, "MAX_GAME_FETCH_ATTEMPTS", 2)
    monkeypatch.setattr(public_game.oplog, "record_event", lambda *args, **kwargs: None)
    return calls


def test_excluded_game_never_returns_as_fallback(monkeypatch):
    calls = _mock_generator(monkeypatch)
    with pytest.raises(GatewayError) as exc:
        public_game.get_public_game(
            mode="draft_guess", difficulty=None, seed=None,
            exclude_game_ids=["GGP:" + "a" * 24],
        )
    assert exc.value.code == "NO_ELIGIBLE_GAME"
    assert len(calls) == 2


def test_recent_entity_never_returns_as_fallback(monkeypatch):
    calls = _mock_generator(monkeypatch)
    client_id = "test-repeat-guard-unique-client"
    public_game._recent_entities_for(client_id).append("board:repeat")
    with pytest.raises(GatewayError) as exc:
        public_game.get_public_game(
            mode="draft_guess", difficulty=None, seed=None,
            exclude_game_ids=[], client_id=client_id,
        )
    assert exc.value.code == "NO_ELIGIBLE_GAME"
    assert len(calls) == 2
