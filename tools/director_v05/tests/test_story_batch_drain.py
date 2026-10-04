import sys
import types

fake_engine = types.ModuleType("tools.quiz_export.engine")
fake_engine.connect = lambda: None
fake_engine.ENGINE_DIR = None
sys.modules.setdefault("tools.quiz_export.engine", fake_engine)

from tools.director_v05 import story_batch_drain as drain


def test_drain_runs_checkpointed_micro_batches_until_empty(monkeypatch):
    results = iter([
        {
            "claimed": 5,
            "counts": {"DONE": 2, "REVIEW_REQUIRED": 3},
            "reclaimed_stale": 1,
            "ledger": {"PENDING": 10, "DONE": 2, "REVIEW_REQUIRED": 3},
            "generated_from_checkpointed_batches": 6,
        },
        {
            "claimed": 3,
            "counts": {"DONE": 1, "REVIEW_REQUIRED": 2},
            "reclaimed_stale": 0,
            "ledger": {"PENDING": 7, "DONE": 3, "REVIEW_REQUIRED": 5},
            "generated_from_checkpointed_batches": 9,
        },
        {
            "claimed": 0,
            "counts": {},
            "reclaimed_stale": 0,
            "ledger": {"DONE": 3, "REVIEW_REQUIRED": 5},
            "generated_from_checkpointed_batches": 9,
        },
    ])
    calls = []

    def fake_process(**kwargs):
        calls.append(kwargs)
        return next(results)

    monkeypatch.setattr(drain, "process_story_batch", fake_process)

    out = drain.drain_story_queue(
        batch_size=5,
        max_batches=10,
        time_budget_seconds=900,
        include_deep_chains=False,
    )
    assert out["micro_batches_run"] == 3
    assert out["claimed_total"] == 8
    assert out["counts"] == {"DONE": 3, "REVIEW_REQUIRED": 5}
    assert out["generated_from_checkpointed_batches"] == 9
    assert out["final_ledger"] == {"DONE": 3, "REVIEW_REQUIRED": 5}
    assert len(calls) == 3
    assert all(call["batch_size"] == 5 for call in calls)
    assert all(call["include_deep_chains"] is False for call in calls)


def test_drain_respects_max_batches(monkeypatch):
    def fake_process(**kwargs):
        return {
            "claimed": 5,
            "counts": {"DONE": 5},
            "reclaimed_stale": 0,
            "ledger": {"PENDING": 100},
            "generated_from_checkpointed_batches": 5,
        }

    monkeypatch.setattr(drain, "process_story_batch", fake_process)

    out = drain.drain_story_queue(
        batch_size=5,
        max_batches=2,
        time_budget_seconds=900,
    )
    assert out["micro_batches_run"] == 2
    assert out["claimed_total"] == 10



def test_drain_stops_after_three_batches_without_promotions(monkeypatch):
    calls = []

    def fake_process(**kwargs):
        calls.append(kwargs)
        return {
            "claimed": 5,
            "counts": {"REVIEW_REQUIRED": 5},
            "reclaimed_stale": 0,
            "ledger": {"PENDING": 100, "REVIEW_REQUIRED": len(calls) * 5},
            "generated_from_checkpointed_batches": 0,
        }

    monkeypatch.setattr(drain, "process_story_batch", fake_process)

    out = drain.drain_story_queue(
        batch_size=5,
        max_batches=10,
        time_budget_seconds=900,
    )
    assert out["micro_batches_run"] == 3
    assert out["claimed_total"] == 15
    assert out["stop_reason"] == "NO_PROMOTION_STREAK"
    assert out["no_promotion_streak"] == 3
    assert out["ledger"] == out["final_ledger"]


def test_drain_resets_no_promotion_streak_after_done(monkeypatch):
    results = iter([
        {
            "claimed": 5,
            "counts": {"REVIEW_REQUIRED": 5},
            "reclaimed_stale": 0,
            "ledger": {"PENDING": 20},
            "generated_from_checkpointed_batches": 0,
        },
        {
            "claimed": 5,
            "counts": {"DONE": 1, "REVIEW_REQUIRED": 4},
            "reclaimed_stale": 0,
            "ledger": {"PENDING": 15, "DONE": 1},
            "generated_from_checkpointed_batches": 3,
        },
        {
            "claimed": 0,
            "counts": {},
            "reclaimed_stale": 0,
            "ledger": {"DONE": 1, "REVIEW_REQUIRED": 4},
            "generated_from_checkpointed_batches": 3,
        },
    ])
    monkeypatch.setattr(drain, "process_story_batch", lambda **kwargs: next(results))

    out = drain.drain_story_queue(max_batches=10)
    assert out["micro_batches_run"] == 3
    assert out["stop_reason"] == "QUEUE_EMPTY_OR_UNCLAIMABLE"
    assert out["no_promotion_streak"] == 0
