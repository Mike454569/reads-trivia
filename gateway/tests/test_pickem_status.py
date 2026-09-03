"""Dynamic Weekly Pick'em pass -- unit coverage for tools/data_refresh/
_pickem_status.py's pure functions (real kickoff derivation, real
FINAL/SCHEDULED/IN_PROGRESS/UNKNOWN/POSTPONED/CANCELED decision logic).
No DB/network needed -- these are pure functions over explicit inputs."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.data_refresh import _pickem_status  # noqa: E402


def test_nfl_kickoff_combines_date_and_time_as_real_eastern_then_utc():
    # A real 2025 Week 1 Sunday 1pm ET game -- EDT (UTC-4) in September.
    kickoff = _pickem_status.nfl_kickoff_utc("2025-09-07", "13:00")
    assert kickoff == datetime(2025, 9, 7, 17, 0, tzinfo=timezone.utc)


def test_nfl_kickoff_respects_real_standard_time_boundary():
    # A real January game -- EST (UTC-5), not EDT -- must NOT reuse the
    # same fixed UTC offset as the September case above.
    kickoff = _pickem_status.nfl_kickoff_utc("2026-01-04", "13:00")
    assert kickoff == datetime(2026, 1, 4, 18, 0, tzinfo=timezone.utc)


def test_nfl_kickoff_falls_back_to_date_only_when_time_is_blank():
    kickoff = _pickem_status.nfl_kickoff_utc("2025-09-07", None)
    assert kickoff == datetime(2025, 9, 7, 0, 0, tzinfo=timezone.utc)


def test_derive_pending_status_future_kickoff_is_scheduled():
    now = datetime(2026, 9, 1, tzinfo=timezone.utc)
    kickoff = datetime(2026, 9, 7, 17, 0, tzinfo=timezone.utc)
    assert _pickem_status.derive_pending_status(kickoff, now=now) == "SCHEDULED"


def test_derive_pending_status_within_window_is_in_progress():
    kickoff = datetime(2026, 9, 7, 17, 0, tzinfo=timezone.utc)
    now = datetime(2026, 9, 7, 19, 0, tzinfo=timezone.utc)  # 2h after kickoff
    assert _pickem_status.derive_pending_status(kickoff, now=now) == "IN_PROGRESS"


def test_derive_pending_status_long_past_kickoff_no_score_is_unknown():
    kickoff = datetime(2026, 9, 7, 17, 0, tzinfo=timezone.utc)
    now = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)  # ~19h later, real data lag or undetected gap
    assert _pickem_status.derive_pending_status(kickoff, now=now) == "UNKNOWN"


def test_compute_status_and_winner_real_score_always_wins_final():
    status, winner = _pickem_status.compute_status_and_winner(
        existing_status=None, existing_kickoff=None, new_kickoff=None,
        home_score=24, away_score=17, home_code="KC", away_code="BUF",
    )
    assert status == "FINAL"
    assert winner == "KC"


def test_compute_status_and_winner_tie():
    status, winner = _pickem_status.compute_status_and_winner(
        existing_status=None, existing_kickoff=None, new_kickoff=None,
        home_score=20, away_score=20, home_code="ATL", away_code="PIT",
    )
    assert status == "FINAL"
    assert winner == "TIE"


def test_compute_status_and_winner_never_clobbers_admin_postponed_without_real_evidence():
    kickoff = datetime(2026, 9, 7, tzinfo=timezone.utc)
    status, winner = _pickem_status.compute_status_and_winner(
        existing_status="POSTPONED", existing_kickoff=kickoff, new_kickoff=kickoff,
        home_score=None, away_score=None, home_code="KC", away_code="BUF",
    )
    assert status == "POSTPONED"
    assert winner is None


def test_compute_status_and_winner_real_reschedule_clears_postponed():
    old_kickoff = datetime(2026, 9, 7, tzinfo=timezone.utc)
    new_kickoff = datetime(2026, 9, 14, tzinfo=timezone.utc)  # source now reports a real, different kickoff
    status, winner = _pickem_status.compute_status_and_winner(
        existing_status="POSTPONED", existing_kickoff=old_kickoff, new_kickoff=new_kickoff,
        home_score=None, away_score=None, home_code="KC", away_code="BUF",
        now=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    assert status == "SCHEDULED"  # real, disclosed heuristic re-applied to the NEW real kickoff
    assert winner is None


def test_compute_status_and_winner_real_score_overrides_even_a_canceled_flag():
    # Real evidence (a score exists) always wins -- an admin mistakenly
    # marking a game CANCELED before a real result was known must not
    # permanently hide the real outcome once one exists.
    status, winner = _pickem_status.compute_status_and_winner(
        existing_status="CANCELED", existing_kickoff=None, new_kickoff=None,
        home_score=10, away_score=7, home_code="DAL", away_code="NYG",
    )
    assert status == "FINAL"
    assert winner == "DAL"
