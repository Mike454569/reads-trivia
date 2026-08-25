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

This module does NOT add a new data source, table, or capability (P0/P1
scope: no new engine, no new data) -- it's a small, honest freshness
calculation over the ALREADY-DISCLOSED snapshot date already embedded in
every CURRENT_TEAM_2026 board's own `notes` text, exposed as a real,
checkable signal any caller (an operator audit script, a future admin
dashboard, or a safety_check()) can act on.

P1 Release Readiness pass: STALE is now actually enforced, not just
reported. tools/quiz_export/adapters/nfl_offense_college_curated.py's
`fetch_ordered_candidates()` returns zero candidates when STALE -- the
capability quarantines itself through the exact same "0 candidates ->
qa_status FAILED -> package_contract rejects -> NO_ELIGIBLE_GAME" pipeline
the P0 pass already built for every other empty-pool case, with a specific
(not generic) shortfall_reason explaining why (see game_director_v01.py's
shortfall_reason computation). WARN deliberately stays non-blocking: it is
a softer, "worth a human re-check" signal, not yet a "stop serving this"
verdict -- only historical SB_CHAMPION board data (which never goes stale)
and the 8 sibling capabilities built on it are guaranteed unaffected, since
none of them read CURRENT_TEAM_2026 boards at all (verified directly: every
one of their fetch_boards() calls is hardcoded to board_type='SB_CHAMPION').
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
