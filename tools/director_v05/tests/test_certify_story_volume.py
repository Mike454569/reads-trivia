from tools.director_v05.certify_story_volume import evaluate_volume_result


def test_volume_cert_passes_clean_terminal_batch():
    result = evaluate_volume_result(
        before_ledger={"PENDING": 100, "PROCESSING": 0},
        after_ledger={"PENDING": 75, "DONE": 5, "REVIEW_REQUIRED": 20, "PROCESSING": 0},
        before_generated=10,
        after_generated=16,
        drain={"claimed_total": 25, "stop_reason": "MAX_BATCHES", "micro_batches_run": 5},
        processed_rows=[
            {"candidate_id": f"c{i}", "state": "DONE" if i < 5 else "REVIEW_REQUIRED", "attempts": 1}
            for i in range(25)
        ],
        min_claimed=25,
    )
    assert result["promotion_ready"] is True
    assert result["generated_delta"] == 6


def test_volume_cert_rejects_stranded_duplicate_and_attempt_overflow():
    result = evaluate_volume_result(
        before_ledger={"PENDING": 100, "PROCESSING": 0},
        after_ledger={"PENDING": 98, "PROCESSING": 1},
        before_generated=10,
        after_generated=9,
        drain={"claimed_total": 2, "stop_reason": "NO_PROMOTION_STREAK", "micro_batches_run": 1},
        processed_rows=[
            {"candidate_id": "same", "state": "PROCESSING", "attempts": 4},
            {"candidate_id": "same", "state": "REVIEW_REQUIRED", "attempts": 1},
        ],
        min_claimed=25,
    )
    assert result["promotion_ready"] is False
    joined = "|".join(result["errors"])
    assert "INSUFFICIENT_CLAIMED" in joined
    assert "GENERATED_COUNT_REGRESSED" in joined
    assert "STRANDED_PROCESSING_ROWS" in joined
    assert "DUPLICATE_CANDIDATE" in joined
    assert "NON_TERMINAL_STATE" in joined
    assert "ATTEMPT_BOUNDS" in joined


def test_story_factory_and_harvesters_share_neutral_write_helpers():
    from tools.director_v05 import story_candidate_harvest as mixed
    from tools.director_v05 import cfb_story_candidate_harvest as cfb
    from tools.director_v05 import story_to_trivia_factory as factory
    from tools.director_v05 import story_write_utils as write_utils

    assert mixed._commit_with_retry is write_utils._commit_with_retry
    assert cfb._commit_with_retry is write_utils._commit_with_retry
    assert factory._commit_with_retry is write_utils._commit_with_retry
    assert mixed._prepare_write_connection is write_utils._prepare_write_connection
    assert cfb._prepare_write_connection is write_utils._prepare_write_connection
    assert factory._prepare_write_connection is write_utils._prepare_write_connection
