"""P0 Accuracy + Reliability Hardening pass (Section 5): current-season
roster-fact drift detection.

Historical data (a 1994 Super Bowl roster, a 2018 starting lineup) never
changes -- once verified, it's permanently correct. CURRENT-season data is
fundamentally different: `curated_nfl_offense_college_board`'s
CURRENT_TEAM_2026 boards are an explicit, disclosed snapshot ("Projected
2026 starters as of early Aug 2026 (curated workbook); re-verify O-line
before live play" -- every board's own `notes` field says this), not a
live roster feed. Camp battles, trades, and injuries make that snapshot
progressively less trustworthy the longer it goes un-refreshed, and
nothing in this codebase measured that staleness before this pass -- a
capability could keep confidently serving a increasingly-wrong current
roster indefinitely.

This module does NOT add a new data source, table, or capability (P0
scope: no new engine, no new data) -- it's a small, honest freshness
calculation over the ALREADY-DISCLOSED snapshot date already embedded in
every CURRENT_TEAM_2026 board's own `notes` text, exposed as a real,
checkable signal any caller (an operator audit script, a future admin
dashboard, or a safety_check()) can act on.
"""
from __future__ import annotations

import datetime as _dt

# The curated Gold Standard workbook's own disclosed snapshot date for
# CURRENT_TEAM_2026 boards (every board's `notes` field says "as of early
# Aug 2026" verbatim -- also cross-confirmed by the workbook's own
# "9. Site Mode Audit" sheet, dated "Site checked August 7, 2026"). Not
# derived from any live source -- update this constant by hand the next
# time the curated workbook is actually refreshed, matching the discipline
# every other curated-data staleness check in this codebase already uses
# (e.g. lineup_college.py's own disclosed real-coverage-ceiling comments).
CURRENT_TEAM_SNAPSHOT_DATE = _dt.date(2026, 8, 7)

# Two-tier threshold, not a single hard cutoff: NFL rosters churn fastest
# around final cuts (late Aug), the trade deadline (early Nov), and in-
# season injuries -- a flat "N days = broken" number would either nag
# constantly right after a fresh snapshot or stay silent long after the
# data has clearly gone stale. WARN is a soft signal (worth a human
# re-check); STALE is the real "this should not keep serving unqualified"
# threshold -- roughly half an NFL season, long enough that real roster
# movement (trades, injuries, depth-chart changes) has almost certainly
# invalidated at least some of the 32 real boards.
WARN_AFTER_DAYS = 45
STALE_AFTER_DAYS = 120


def days_since_snapshot(*, today: _dt.date | None = None) -> int:
    today = today or _dt.date.today()
    return (today - CURRENT_TEAM_SNAPSHOT_DATE).days


def freshness_report(*, today: _dt.date | None = None) -> dict:
    """Returns a real, checkable freshness verdict for the curated
    CURRENT_TEAM_2026 board data. `status` is one of FRESH / WARN / STALE
    -- STALE is the "quarantine until refreshed" signal Section 5 asks
    for; a caller wiring this into a safety_check() or a public-mode gate
    should treat STALE as "do not keep serving this current-team data
    unqualified.\""""
    age_days = days_since_snapshot(today=today)
    if age_days >= STALE_AFTER_DAYS:
        status = "STALE"
    elif age_days >= WARN_AFTER_DAYS:
        status = "WARN"
    else:
        status = "FRESH"
    return {
        "snapshot_date": CURRENT_TEAM_SNAPSHOT_DATE.isoformat(),
        "age_days": age_days,
        "status": status,
        "warn_after_days": WARN_AFTER_DAYS,
        "stale_after_days": STALE_AFTER_DAYS,
        "message": (
            f"Current-team roster snapshot is {age_days} days old (as of "
            f"{(today or _dt.date.today()).isoformat()}) -- status {status}. "
            f"Real roster movement (trades/injuries/depth-chart changes) becomes "
            f"increasingly likely to have invalidated some of the 32 real boards "
            f"the longer this goes un-refreshed."
        ),
    }
