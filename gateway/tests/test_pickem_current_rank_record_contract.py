import sqlite3
from datetime import datetime, timedelta, timezone

from tools.director_v04 import weekly_pickem


def _rank_conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("""
        CREATE TABLE cfb_rankings(
            season INTEGER, week INTEGER, season_type TEXT, poll TEXT,
            rank INTEGER, school_id INTEGER
        )
    """)
    return c


def test_current_cfb_pickem_is_date_driven_not_week_resolver():
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    assert weekly_pickem._is_live_current_cfb_slate(
        datetime.now(timezone.utc).year, "regular", [future]
    )


def test_old_cfb_pickem_week_stays_historical():
    past = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    assert not weekly_pickem._is_live_current_cfb_slate(
        datetime.now(timezone.utc).year, "regular", [past]
    )


def test_current_cfb_pickem_uses_latest_complete_ap_poll_even_if_week_numbers_drift():
    c = _rank_conn()
    season = datetime.now(timezone.utc).year
    for rank in range(1, 26):
        c.execute(
            "INSERT INTO cfb_rankings VALUES (?,?,?,?,?,?)",
            (season, 4, "regular", "AP Top 25", rank, 1000 + rank),
        )
    # A partial newer refresh must never become the Pick'em poll.
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


def test_historical_cfb_pickem_never_uses_future_poll():
    c = _rank_conn()
    season = datetime.now(timezone.utc).year
    for poll_week in (2, 4):
        for rank in range(1, 26):
            c.execute(
                "INSERT INTO cfb_rankings VALUES (?,?,?,?,?,?)",
                (season, poll_week, "regular", "AP Top 25", rank, poll_week * 1000 + rank),
            )
    c.commit()

    ranks = weekly_pickem._ap_top25(
        c, season, 2, "regular", live_current=False
    )
    assert len(ranks) == 25
    assert 2001 in ranks
    assert 4001 not in ranks
