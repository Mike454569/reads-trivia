"""Mine game-level chaos patterns from verified NFL play-by-play."""
from __future__ import annotations
from collections import defaultdict

from .event_ingest import upsert_event

SOURCE_URL = "https://github.com/nflverse/nflverse-data/releases"
SOURCE_PUBLISHER = "nflverse play-by-play"

def _truthy(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "none", "nan"}
    return bool(value)

def classify_game(plays):
    """Return high-signal, game-level story patterns for one game."""
    turnovers = 0
    defensive_scores = 0
    explosive_tds = 0
    fourth_down_explosives = 0
    wpa_swings = 0
    onside_recoveries = 0

    for play in plays:
        yards = int(play.get("yards_gained") or 0)
        interception = _truthy(play.get("interception"))
        fumble_lost = _truthy(play.get("fumble_lost"))
        touchdown = _truthy(play.get("touchdown"))

        if interception:
            turnovers += 1
        if fumble_lost:
            turnovers += 1
        if touchdown and (interception or fumble_lost):
            defensive_scores += 1
        if touchdown and yards >= 40:
            explosive_tds += 1
        if int(play.get("down") or 0) == 4 and yards >= 15:
            fourth_down_explosives += 1
        if _truthy(play.get("own_kickoff_recovery")):
            onside_recoveries += 1
        if play.get("wpa") is not None:
            try:
                if abs(float(play["wpa"])) >= 0.25:
                    wpa_swings += 1
            except (TypeError, ValueError):
                pass

    out = []
    if turnovers >= 6:
        out.append(("TURNOVER_AVALANCHE", "ON_FIELD_ODDITY",
                    ["turnover_avalanche", "chaos_game", "turnovers"],
                    f"{turnovers} combined turnovers"))
    if defensive_scores >= 2:
        out.append(("DEFENSIVE_SCORE_FRENZY", "ON_FIELD_ODDITY",
                    ["defensive_touchdown", "chaos_game", "multiple_defensive_scores"],
                    f"{defensive_scores} defensive touchdowns"))
    if explosive_tds >= 4:
        out.append(("EXPLOSIVE_TD_CLUSTER", "ICONIC_PLAY",
                    ["explosive_play", "chaos_game", "touchdown"],
                    f"{explosive_tds} touchdowns of at least 40 yards"))
    if fourth_down_explosives >= 3:
        out.append(("FOURTH_DOWN_MADNESS", "ON_FIELD_ODDITY",
                    ["fourth_down", "chaos_game", "explosive_play"],
                    f"{fourth_down_explosives} fourth-down gains of at least 15 yards"))
    if wpa_swings >= 3:
        out.append(("WIN_PROBABILITY_WHIPLASH", "COMEBACK",
                    ["wpa", "chaos_game", "game_swing"],
                    f"{wpa_swings} plays with at least a 25-point win-probability swing"))
    if onside_recoveries >= 2:
        out.append(("ONSIDE_CHAOS", "ON_FIELD_ODDITY",
                    ["onside_kick", "chaos_game", "special_teams"],
                    f"{onside_recoveries} kicking-team kickoff recoveries"))
    return out

def mine_nfl_game_chaos(conn, limit_games=None):
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "nfl_plays" not in tables:
        return {"events": 0, "reason": "missing_table"}

    cols = {r[1] for r in conn.execute("PRAGMA table_info(nfl_plays)")}
    required = {"game_id", "season", "play_id", "yards_gained", "touchdown", "posteam", "defteam"}
    if not required <= cols:
        return {"events": 0, "reason": "schema", "missing": sorted(required - cols)}

    optional = ["down", "interception", "fumble_lost", "own_kickoff_recovery", "wpa"]
    selected = sorted(required) + [name for name in optional if name in cols]
    games = defaultdict(list)
    for raw in conn.execute("SELECT " + ",".join(selected) + " FROM nfl_plays ORDER BY game_id,play_id"):
        games[str(raw["game_id"])].append(dict(raw))

    inserted = 0
    kinds = defaultdict(int)
    for index, (game_id, plays) in enumerate(games.items()):
        if limit_games and index >= limit_games:
            break
        if not plays:
            continue

        teams = []
        for play in plays:
            for key in ("posteam", "defteam"):
                team = play.get(key)
                if team and team not in teams:
                    teams.append(team)

        subjects = [{"subject_type": "GAME", "subject_id": game_id, "role": "game"}]
        subjects.extend(
            {"subject_type": "NFL_TEAM", "subject_id": team, "role": "participant"}
            for team in teams[:2]
        )
        season = plays[0].get("season")

        for rule, event_type, tags, summary in classify_game(plays):
            upsert_event(conn, {
                "event_type": event_type,
                "league": "NFL",
                "event_date": str(season) + "-01-01" if season is not None else None,
                "title": rule.replace("_", " ").title() + " in " + game_id,
                "neutral_summary": summary + " in verified play-by-play for " + game_id + ".",
                "source_url": SOURCE_URL,
                "source_publisher": SOURCE_PUBLISHER,
                "evidence_tier": "AUTHORITATIVE",
                "verification_status": "VERIFIED",
                "subjects": subjects,
                "tags": tags + [rule.lower()],
                "sensitive": False,
            })
            inserted += 1
            kinds[rule] += 1

    conn.commit()
    return {
        "games_scanned": min(len(games), limit_games or len(games)),
        "events": inserted,
        "kinds": dict(kinds),
    }
