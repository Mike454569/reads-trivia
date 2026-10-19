"""Regression tests for story queue diagnostics (offline SQLite only)."""
import sqlite3
from unittest.mock import patch

from tools.director_v05 import story_batch_processor as queue


def connection():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE football_story_candidates (candidate_id TEXT PRIMARY KEY, status TEXT, sensitive_hint INTEGER, family_hint TEXT, title TEXT, domain TEXT, first_harvested_at TEXT, evidence_tier_hint TEXT, seen_date TEXT)")
    db.execute("CREATE TABLE story_candidate_processing (candidate_id TEXT PRIMARY KEY, state TEXT, attempts INTEGER, claimed_at TEXT, heartbeat_at TEXT, updated_at TEXT, last_error TEXT)")
    return db


def test_no_eligible_story_reports_zero():
    db = connection()
    with patch.object(queue, "_commit_with_retry", side_effect=lambda c: c.commit()):
        chosen, stats = queue._claim_batch(db, batch_size=3, max_attempts=3)
    assert chosen == []
    assert stats["eligible_ledger_rows"] == 0
    assert stats["priority_matches"] == 0
    assert stats["fallback_matches"] == 0
    assert stats["selected"] == 0
    db.close()


def test_priority_and_fallback_counts_are_not_mixed():
    db = connection()
    for cid in ("priority", "fallback"):
        db.execute(
            "INSERT INTO football_story_candidates VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, "REVIEW_PRIORITY", 0, "BIZARRE_MOMENT",
             "Strange NFL touchdown sparks surprise", "nfl.com",
             "2026-10-19", "PRIMARY", "2026-10-19"),
        )
        db.execute(
            "INSERT INTO story_candidate_processing(candidate_id,state,attempts) VALUES (?,'PENDING',0)",
            (cid,),
        )
    with patch.object(queue, "_story_candidate_priority", side_effect=lambda r: (10, 0, 0, 0) if r["candidate_id"] == "priority" else None):
        with patch.object(queue, "_commit_with_retry", side_effect=lambda c: c.commit()):
            chosen, stats = queue._claim_batch(db, batch_size=2, max_attempts=3)
    assert len(chosen) == 2
    assert stats["eligible_ledger_rows"] == 2
    assert stats["priority_matches"] == 1
    assert stats["fallback_matches"] == 1
    assert stats["selected"] == 2
    db.close()
