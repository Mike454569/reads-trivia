import sqlite3
from datetime import datetime, timedelta, timezone

from tools.director_v04 import weekly_pickem


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""
        CREATE TABLE cfb_rankings(
            season INTEGER, week INTEGER, season_type TEXT, poll TEXT,
            rank INTEGER, school_id INTEGER
        )
    """)
    return c


def test_live_current_slate_is_date_driven_not_week_resolver():
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    assert weekly_pickem._is_live_current_cfb_slate(
        datetime.now(timezone.utc).year, "regular", [future]
    )


def test_historical_slate_stays_historical():
    past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    assert not weekly_pickem._is_live_current_cfb_slate(
        datetime.now(timezone.utc).year, "regular", [past]
    )


def test_live_pickem_uses_latest_complete_ap_poll_even_if_schedule_week_is_behind():
    c = _conn()
    season = datetime.now(timezone.utc).year
    # Week 4 complete poll.
    for rank in range(1, 26):
        c.execute(
            "INSERT INTO cfb_rankings VALUES (?,?,?,?,?,?)",
            (season, 4, "regular", "AP Top 25", rank, 1000 + rank),
        )
    # Week 5 partial refresh must NOT replace the complete poll.
    for rank in range(1, 6):
        c.execute(
            "INSERT INTO cfb_rankings VALUES (?,?,?,?,?,?)",
            (season, 5, "regular", "AP Top 25", rank, 2000 + rank),
        )
    c.commit()

    ranks = weekly_pickem._ap_top25(
        c, season, 3, "regular", live_current=True
    )
    assert len(ranks) == 25
    assert ranks[1001] == 1
    assert 2001 not in ranks


def test_historical_pickem_never_uses_future_poll():
    c = _conn()
    season = datetime.now(timezone.utc).year
    for week in (2, 4):
        for rank in range(1, 26):
            c.execute(
                "INSERT INTO cfb_rankings VALUES (?,?,?,?,?,?)",
                (season, week, "regular", "AP Top 25", rank, week * 1000 + rank),
            )
    c.commit()

    ranks = weekly_pickem._ap_top25(
        c, season, 2, "regular", live_current=False
    )
    assert len(ranks) == 25
    assert 2001 in ranks
    assert 4001 not in ranks
