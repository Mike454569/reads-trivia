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
