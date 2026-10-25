"""Regression coverage for unified public mechanic launches."""
from unittest.mock import patch

import pytest

from gateway.errors import GatewayError
from gateway.services import public_formats


def test_mechanic_accepts_shared_launch_hints():
    payload = {
        "round_id": "round-test", "mode": "matching_nfl_draft",
        "kind": "matching", "title": "Draft match",
        "instructions": "Match", "view": {"items": []}, "metadata": {},
    }
    with patch.object(public_formats.public_mechanics, "start_public_round", return_value=payload) as starter:
        result = public_formats.start_public_format(
            mode="matching_nfl_draft", difficulty="medium", seed="abc123",
            exclude_game_ids=["previous"], client_id="client123",
        )
    assert result["round_id"] == "round-test"
    assert result["engine_kind"] == "mechanic"
    starter.assert_called_once_with(mode="matching_nfl_draft")


def test_mechanic_still_rejects_sequential_stage():
    with pytest.raises(GatewayError):
        public_formats.start_public_format(mode="matching_nfl_draft", stage_index=2)



def test_unified_mechanic_launch_then_submit_full_roundtrip():
    """Shared launch hints must not stop a playable mode from reaching submit."""
    started_payload = {
        "round_id": "GGP4:0123456789abcdef01234567",
        "mode": "matching_nfl_draft", "kind": "matching",
        "title": "Draft matching", "instructions": "Match the pairs",
        "view": {"items": ["A", "B"], "completed": False}, "metadata": {},
    }
    progress = {"public_mode": "matching_nfl_draft", "taxonomy_id": "MATCHING"}
    submitted_payload = {
        "mode": "matching_nfl_draft",
        "result": {"correct": True},
        "view": {"completed": True},
    }
    with patch.object(public_formats.public_mechanics, "start_public_round", return_value=started_payload), \
         patch.object(public_formats.game_state, "load_state", return_value=progress), \
         patch.object(public_formats.public_mechanics, "submit_public_round", return_value=submitted_payload):
        started = public_formats.start_public_format(
            mode="matching_nfl_draft", difficulty="medium", seed="daily-round",
            exclude_game_ids=["GGP4:old"], client_id="reader-123",
        )
        assert started["round_id"] == started_payload["round_id"]
        assert started["view"]["completed"] is False
        submitted = public_formats.submit_public_format(
            round_id=started["round_id"], submission={"pairs": [0, 1]},
        )
    assert submitted["result"]["correct"] is True
    assert submitted["view"]["completed"] is True
