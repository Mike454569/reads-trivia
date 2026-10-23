"""Story queue drain accounting tests; no network or production database."""
from unittest.mock import patch

from tools.director_v05 import story_batch_drain


def test_drain_keeps_batch_selection_diagnostics():
    outputs = iter([
        {
            "claimed": 1, "generated_from_checkpointed_batches": 2,
            "counts": {"DONE": 1}, "ledger": {"DONE": 1},
            "selection_diagnostics": {
                "eligible_ledger_rows": 2, "priority_matches": 1,
                "fallback_matches": 1, "selected": 1,
            },
        },
        {
            "claimed": 0, "generated_from_checkpointed_batches": 2,
            "counts": {}, "ledger": {"DONE": 1},
            "selection_diagnostics": {
                "eligible_ledger_rows": 0, "priority_matches": 0,
                "fallback_matches": 0, "selected": 0,
            },
        },
    ])
    with patch.object(story_batch_drain, "process_story_batch", side_effect=lambda **kwargs: next(outputs)):
        with patch.object(story_batch_drain, "build_subject_index", return_value={}):
            with patch.object(story_batch_drain.engine_bootstrap, "connect") as connect:
                connect.return_value.close.return_value = None
                with patch.object(story_batch_drain, "_prepare_write_connection", side_effect=lambda c: c):
                    result = story_batch_drain.drain_story_queue(batch_size=1, max_batches=3)
    assert result["claimed_total"] == 1
    assert result["stop_reason"] == "QUEUE_EMPTY_OR_UNCLAIMABLE"
    assert len(result["selection_diagnostics"]) == 2
    assert result["selection_diagnostics"][0]["priority_matches"] == 1
    assert result["selection_diagnostics"][1]["selected"] == 0
    assert result["runs"][0]["selection_diagnostics"]["fallback_matches"] == 1
