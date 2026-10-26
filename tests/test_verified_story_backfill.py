"""Bounded verified-story backfill never harvests or writes during dry run."""
from unittest.mock import MagicMock, patch

from tools.director_v05.backfill_verified_story_questions import backfill


def test_backfill_dry_run_does_not_generate():
    conn = MagicMock()
    with patch("tools.director_v05.backfill_verified_story_questions.candidates",
               return_value=[{"event_id": "one"}, {"event_id": "two"}]), patch(
               "tools.director_v05.backfill_verified_story_questions.generate_story_formats_for_event"
               ) as generate:
        report = backfill(conn, limit=2)
    assert report["dry_run"] is True
    assert report["counts"]["eligible_events"] == 2
    generate.assert_not_called()


def test_backfill_counts_only_certified_artifacts():
    conn = MagicMock()
    row = {"event_id": "evt", "candidate_id": "candidate",
           "subject_type": "PLAYER", "subject_id": "p1"}
    with patch("tools.director_v05.backfill_verified_story_questions.candidates",
               return_value=[row]), patch(
               "tools.director_v05.backfill_verified_story_questions.generate_story_formats_for_event",
               return_value={"generated_count": 3}), patch(
               "tools.director_v05.backfill_verified_story_questions.certify_event_questions",
               return_value={"passed": 1, "rejected": 2}):
        result = backfill(conn, apply=True)
    assert result["counts"]["questions_generated"] == 3
    assert result["counts"]["questions_certified"] == 1
    assert result["counts"]["questions_rejected"] == 2
