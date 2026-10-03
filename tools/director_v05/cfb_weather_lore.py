"""Mine source-backed CFB weather facts into universal lore events."""
from __future__ import annotations

from collections import defaultdict

from .event_ingest import upsert_event

SOURCE_URL = "https://api.collegefootballdata.com/games/weather"
SOURCE_PUBLISHER = "CollegeFootballData.com game weather"


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _extreme_weather(row):
    events = []
    temp = row["temperature"]
    wind = row["wind_speed"]
    snow = row["snowfall"]
    precip = row["precipitation"]
    condition = str(row["weather_condition"] or "").strip()

    if temp is not None and float(temp) <= 32:
        events.append((
            "FREEZING_GAME",
            ["weather", "cold", "freezing"],
            f"Game-time temperature was {float(temp):g}°F",
        ))
    if temp is not None and float(temp) >= 95:
        events.append((
            "EXTREME_HEAT_GAME",
            ["weather", "heat"],
            f"Game-time temperature was {float(temp):g}°F",
        ))
    if wind is not None and float(wind) >= 25:
        events.append((
            "HIGH_WIND_GAME",
            ["weather", "wind"],
            f"Game-time wind speed reached {float(wind):g} mph",
        ))
    if snow is not None and float(snow) > 0:
        events.append((
            "SNOW_GAME",
            ["weather", "snow"],
            f"Recorded snowfall was {float(snow):g}",
        ))
    if precip is not None and float(precip) >= 0.25:
        events.append((
            "HEAVY_PRECIPITATION_GAME",
            ["weather", "rain", "precipitation"],
            f"Recorded precipitation was {float(precip):g}",
        ))
    if condition and any(x in condition.casefold() for x in ("snow", "storm", "thunder", "heavy rain", "blizzard")):
        events.append((
            "SEVERE_CONDITION_GAME",
            ["weather", "severe_conditions"],
            f"Recorded weather condition: {condition}",
        ))
    return events


def mine_cfb_weather_lore(conn, *, limit_games=None):
    if "cfb_games_canonical" not in _tables(conn):
        return {"events": 0, "reason": "missing_table"}

    cols = {r[1] for r in conn.execute("PRAGMA table_info(cfb_games_canonical)")}
    required = {
        "game_id", "season", "home_school_id", "away_school_id",
        "temperature", "wind_speed", "snowfall", "precipitation",
        "weather_condition", "weather_source_id", "weather_verification_status",
    }
    if not required <= cols:
        return {"events": 0, "reason": "schema", "missing": sorted(required - cols)}

    rows = conn.execute(
        """SELECT game_id,season,home_school_id,away_school_id,temperature,
                  wind_speed,snowfall,precipitation,weather_condition
           FROM cfb_games_canonical
           WHERE weather_source_id='CFBD_API_LIVE'
             AND weather_verification_status='SOURCE_BACKED'
             AND COALESCE(game_indoors,0)=0
           ORDER BY season,game_id"""
    ).fetchall()

    inserted = 0
    kinds = defaultdict(int)
    for index, row in enumerate(rows):
        if limit_games and index >= int(limit_games):
            break
        subjects = [{"subject_type":"GAME","subject_id":str(row["game_id"]),"role":"game"}]
        if row["home_school_id"] is not None:
            subjects.append({"subject_type":"SCHOOL","subject_id":str(row["home_school_id"]),"role":"home"})
        if row["away_school_id"] is not None:
            subjects.append({"subject_type":"SCHOOL","subject_id":str(row["away_school_id"]),"role":"away"})

        for rule, tags, summary in _extreme_weather(row):
            upsert_event(conn, {
                "event_type": "WEATHER_CHAOS",
                "league": "CFB",
                "event_date": str(row["season"]) + "-01-01" if row["season"] is not None else None,
                "title": rule.replace("_", " ").title() + " in " + str(row["game_id"]),
                "neutral_summary": summary + " for CFB game " + str(row["game_id"]) + ".",
                "source_url": SOURCE_URL,
                "source_publisher": SOURCE_PUBLISHER,
                "evidence_tier": "AUTHORITATIVE",
                "verification_status": "VERIFIED",
                "subjects": subjects,
                "tags": tags + [rule.casefold()],
                "sensitive": False,
            })
            inserted += 1
            kinds[rule] += 1

    conn.commit()
    return {
        "games_scanned": min(len(rows), int(limit_games) if limit_games else len(rows)),
        "events": inserted,
        "kinds": dict(kinds),
    }
