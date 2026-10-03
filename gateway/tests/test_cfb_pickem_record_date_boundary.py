from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tools.director_v04 import weekly_pickem


def test_current_cfb_slate_stays_current_for_entire_game_date():
    now = datetime.now(ZoneInfo("America/Chicago"))
    today = now.date().isoformat()
    assert weekly_pickem._is_live_current_cfb_slate(
        now.year, "regular", [today]
    ) is True


def test_future_cfb_game_date_is_current_slate():
    now = datetime.now(ZoneInfo("America/Chicago"))
    future = (now.date() + timedelta(days=1)).isoformat()
    assert weekly_pickem._is_live_current_cfb_slate(
        now.year, "regular", [future]
    ) is True


def test_past_cfb_game_date_is_historical():
    now = datetime.now(ZoneInfo("America/Chicago"))
    past = (now.date() - timedelta(days=1)).isoformat()
    assert weekly_pickem._is_live_current_cfb_slate(
        now.year, "regular", [past]
    ) is False
