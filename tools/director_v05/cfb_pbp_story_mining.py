"""Mine verified CFB play-by-play into universal lore events."""
from __future__ import annotations

from collections import defaultdict

from .cfb_pbp_detectors import classify_cfb_play, classify_cfb_game
from .event_ingest import upsert_event

SOURCE_URL = "https://api.collegefootballdata.com/"
SOURCE_PUBLISHER = "CollegeFootballData.com plays API"


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def mine_cfb_pbp(conn, limit_games=None):
    if "cfb_plays" not in _tables(conn):
        return {"events": 0, "reason": "missing_table"}

    cols = {r[1] for r in conn.execute("PRAGMA table_info(cfb_plays)")}
    required = {
        "game_id", "play_id", "season", "offense_school_id", "defense_school_id",
        "down", "yards_gained", "play_type", "play_text", "scoring",
        "verification_status", "source_id",
    }
    if not required <= cols:
        return {"events": 0, "reason": "schema", "missing": sorted(required - cols)}

    selected = sorted(required | ({"ppa"} if "ppa" in cols else set()))
    games = defaultdict(list)
    sql = (
        "SELECT " + ",".join(selected) + " FROM cfb_plays "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='CFBD_API_LIVE' "
        "ORDER BY game_id,play_id"
    )
    for raw in conn.execute(sql):
        games[str(raw["game_id"])].append(dict(raw))

    events = 0
    kinds = defaultdict(int)

    for index, (game_id, plays) in enumerate(games.items()):
        if limit_games and index >= limit_games:
            break
        if not plays:
            continue

        season = plays[0].get("season")
        team_ids = []
        for p in plays:
            for key in ("offense_school_id", "defense_school_id"):
                sid = p.get(key)
                if sid is not None and str(sid) not in team_ids:
                    team_ids.append(str(sid))

        base_subjects = [{"subject_type": "GAME", "subject_id": game_id, "role": "game"}]
        base_subjects.extend(
            {"subject_type": "SCHOOL", "subject_id": sid, "role": "participant"}
            for sid in team_ids[:2]
        )

        seen = set()
        for play in plays:
            for key, event_type, tags, summary in classify_cfb_play(play):
                if key in seen:
                    continue
                seen.add(key)
                subjects = list(base_subjects)
                if play.get("offense_school_id") is not None:
                    subjects.append({
                        "subject_type": "SCHOOL",
                        "subject_id": str(play["offense_school_id"]),
                        "role": "offense",
                    })
                if play.get("defense_school_id") is not None:
                    subjects.append({
                        "subject_type": "SCHOOL",
                        "subject_id": str(play["defense_school_id"]),
                        "role": "defense",
                    })
                upsert_event(conn, {
                    "event_type": event_type,
                    "league": "CFB",
                    "event_date": str(season) + "-01-01" if season is not None else None,
                    "title": summary + " in " + game_id,
                    "neutral_summary": summary + " in CollegeFootballData.com play-by-play for game " + game_id + ".",
                    "source_url": SOURCE_URL,
                    "source_publisher": SOURCE_PUBLISHER,
                    "evidence_tier": "AUTHORITATIVE",
                    "verification_status": "VERIFIED",
                    "subjects": subjects,
                    "tags": tags,
                    "sensitive": False,
                })
                events += 1
                kinds[key.split(":")[0]] += 1

        for rule, event_type, tags, summary in classify_cfb_game(plays):
            upsert_event(conn, {
                "event_type": event_type,
                "league": "CFB",
                "event_date": str(season) + "-01-01" if season is not None else None,
                "title": rule.replace("_", " ").title() + " in " + game_id,
                "neutral_summary": summary + " in CollegeFootballData.com play-by-play for game " + game_id + ".",
                "source_url": SOURCE_URL,
                "source_publisher": SOURCE_PUBLISHER,
                "evidence_tier": "AUTHORITATIVE",
                "verification_status": "VERIFIED",
                "subjects": base_subjects,
                "tags": tags + [rule.lower()],
                "sensitive": False,
            })
            events += 1
            kinds[rule] += 1

    conn.commit()
    return {
        "games_scanned": min(len(games), limit_games or len(games)),
        "events": events,
        "kinds": dict(kinds),
    }
