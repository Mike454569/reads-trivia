import sqlite3
import datetime as dt

from tools.director_v05 import story_batch_processor as batch
from tools.director_v05.story_candidate_harvest import _ensure_schema as ensure_candidates
from tools.director_v05.story_to_trivia_factory import _ensure_schema as ensure_factory


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    ensure_candidates(c)
    ensure_factory(c)
    batch._ensure_schema(c)
    return c


def _candidate(c, cid, *, status="REVIEW_PRIORITY", sensitive=0, tier="PRIMARY"):
    now = "2026-10-03T00:00:00+00:00"
    c.execute(
        """INSERT INTO football_story_candidates(
           candidate_id,source_url,title,domain,seen_date,language,source_country,
           family_hint,query_text,evidence_tier_hint,sensitive_hint,status,
           first_harvested_at,last_seen_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            cid, f"https://www.nfl.com/{cid}", f"Player {cid} postgame",
            "nfl.com", "20261003", "English", "US", "PRESS_CONFERENCE",
            "postgame", tier, sensitive, status, now, now,
        ),
    )
    c.commit()


def test_sync_queue_excludes_sensitive_and_nonpriority_candidates():
    c = _conn()
    _candidate(c, "safe")
    _candidate(c, "sensitive", sensitive=1)
    _candidate(c, "review", status="REVIEW_REQUIRED")

    batch.sync_queue(c)
    ids = {
        r["candidate_id"]
        for r in c.execute("SELECT candidate_id FROM story_candidate_processing")
    }
    assert ids == {"safe"}


def test_claim_batch_is_checkpointed_and_not_claimed_twice():
    c = _conn()
    for cid in ("c1", "c2", "c3"):
        _candidate(c, cid)
    batch.sync_queue(c)

    first = batch._claim_batch(c, batch_size=2, max_attempts=3)
    first_ids = {r["candidate_id"] for r in first}
    assert len(first_ids) == 2

    second = batch._claim_batch(c, batch_size=2, max_attempts=3)
    second_ids = {r["candidate_id"] for r in second}
    assert len(second_ids) == 1
    assert not first_ids & second_ids

    states = {
        r["candidate_id"]: r["state"]
        for r in c.execute("SELECT candidate_id,state FROM story_candidate_processing")
    }
    assert list(states.values()).count("PROCESSING") == 3


def test_stale_processing_is_reclaimed_for_retry():
    c = _conn()
    _candidate(c, "c1")
    batch.sync_queue(c)
    old = (
        dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
    ).isoformat()
    c.execute(
        """UPDATE story_candidate_processing
           SET state='PROCESSING',claimed_at=?,heartbeat_at=?,updated_at=?
           WHERE candidate_id='c1'""",
        (old, old, old),
    )
    c.commit()

    assert batch.reclaim_stale(c, stale_minutes=30) == 1
    row = c.execute(
        "SELECT state,last_error FROM story_candidate_processing WHERE candidate_id='c1'"
    ).fetchone()
    assert row["state"] == "FAILED_RETRYABLE"
    assert row["last_error"] == "STALE_PROCESSING_RECLAIMED"


def test_finish_preserves_completed_checkpoint():
    c = _conn()
    _candidate(c, "c1")
    batch.sync_queue(c)
    batch._claim_batch(c, batch_size=1, max_attempts=3)
    batch._finish(
        c, "c1", state="DONE", decision="AUTO_PROMOTED", generated=2
    )

    row = c.execute(
        """SELECT state,last_decision,generated_question_count
           FROM story_candidate_processing WHERE candidate_id='c1'"""
    ).fetchone()
    assert row["state"] == "DONE"
    assert row["last_decision"] == "AUTO_PROMOTED"
    assert row["generated_question_count"] == 2

    assert batch._claim_batch(c, batch_size=1, max_attempts=3) == []


def test_retryable_candidate_stops_after_max_attempts():
    c = _conn()
    _candidate(c, "c1")
    batch.sync_queue(c)

    for _ in range(3):
        rows = batch._claim_batch(c, batch_size=1, max_attempts=3)
        assert len(rows) == 1
        attempt = c.execute(
            "SELECT attempts FROM story_candidate_processing WHERE candidate_id='c1'"
        ).fetchone()["attempts"]
        state = "FAILED_FINAL" if attempt >= 3 else "FAILED_RETRYABLE"
        batch._finish(c, "c1", state=state, error="boom")

    assert batch._claim_batch(c, batch_size=1, max_attempts=3) == []
    row = c.execute(
        "SELECT state,attempts FROM story_candidate_processing WHERE candidate_id='c1'"
    ).fetchone()
    assert row["state"] == "FAILED_FINAL"
    assert row["attempts"] == 3
