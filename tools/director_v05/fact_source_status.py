"""Classify remaining lore gaps by whether Reads already has a usable source."""
from __future__ import annotations


FAMILY_SOURCES = {
    "CONTRACT": {
        "status": "AUTO_SOURCE_READY",
        "source": "nfl_player_contracts / NFLVERSE_DATA",
        "refresh": "nfl_contracts",
    },
    "WEATHER_CHAOS": {
        "status": "AUTO_SOURCE_READY",
        "source": "cfb_games_canonical weather enrichment / CFBD_API_LIVE",
        "refresh": "cfb_weather",
    },
    "ON_FIELD_ODDITY": {
        "status": "AUTO_SOURCE_READY",
        "source": "nfl_plays + cfb_plays",
        "refresh": "nfl_pbp + cfb_pbp",
    },
    "ICONIC_PLAY": {
        "status": "AUTO_SOURCE_READY",
        "source": "nfl_plays + cfb_plays",
        "refresh": "nfl_pbp + cfb_pbp",
    },
    "COMEBACK": {
        "status": "PARTIAL_SOURCE",
        "source": "NFL PBP WPA + canonical games; CFB PBP lacks equivalent full WPA coverage",
        "refresh": "nfl_pbp + cfb_pbp",
    },
    "TRANSFER": {
        "status": "PARTIAL_SOURCE",
        "source": "verified CFB game/player logs infer school changes",
        "refresh": "cfb_player_stats",
    },
    "COACHING_MOVE": {
        "status": "PARTIAL_SOURCE",
        "source": "coach_team_seasons provides team/season history but not every transaction date/reason",
        "refresh": None,
    },
    "HISTORICAL_MILESTONE": {
        "status": "PARTIAL_SOURCE",
        "source": "games, records, rankings, draft and award tables",
        "refresh": None,
    },
    "RECORD_EVENT": {
        "status": "PARTIAL_SOURCE",
        "source": "player/team stats and historical records",
        "refresh": None,
    },
    "RECRUITING": {
        "status": "AUTO_SOURCE_READY",
        "source": "cfb_recruits / CFBD_API_LIVE",
        "refresh": "cfb_recruiting",
    },
    "PRESS_CONFERENCE": {
        "status": "PARTIAL_SOURCE",
        "source": "reviewed-media ingestion lane; requires reviewed primary/reputable-media URLs",
        "refresh": None,
    },
    "OFF_FIELD_ODDITY": {
        "status": "PARTIAL_SOURCE",
        "source": "reviewed-media ingestion lane; requires reviewed primary/reputable-media URLs",
        "refresh": None,
    },
    "RULE_ODDITY": {
        "status": "AUTO_SOURCE_READY",
        "source": "official NFL Football Operations + NCAA rule-change corpus",
        "refresh": None,
    },
    "MASCOT_FAN_MOMENT": {
        "status": "NEW_SOURCE_NEEDED",
        "source": None,
        "refresh": None,
    },
    "CELEBRATION": {
        "status": "PARTIAL_SOURCE",
        "source": "play-by-play text can identify some celebration/penalty events",
        "refresh": "nfl_pbp + cfb_pbp",
    },
    "LEAGUE_DISCIPLINE": {
        "status": "NEW_SOURCE_NEEDED",
        "source": None,
        "refresh": None,
    },
    "LEGAL_EVENT": {
        "status": "NEW_SOURCE_NEEDED",
        "source": None,
        "refresh": None,
    },
    "CONTROVERSY": {
        "status": "NEW_SOURCE_NEEDED",
        "source": None,
        "refresh": None,
    },
    "INJURY": {
        "status": "AUTO_SOURCE_READY",
        "source": "NFL injury refresh",
        "refresh": "nfl_injuries",
    },
}


def source_status_for_family(family):
    return dict(FAMILY_SOURCES.get(str(family), {
        "status": "NEW_SOURCE_NEEDED",
        "source": None,
        "refresh": None,
    }))


def source_status_report():
    counts = {}
    for value in FAMILY_SOURCES.values():
        counts[value["status"]] = counts.get(value["status"], 0) + 1
    return {
        "families": {k: dict(v) for k, v in FAMILY_SOURCES.items()},
        "counts": counts,
    }
