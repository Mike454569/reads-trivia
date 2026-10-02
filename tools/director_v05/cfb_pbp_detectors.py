"""High-signal CFB play-by-play story detectors."""
from __future__ import annotations


def _text(play):
    return (" ".join([
        str(play.get("play_type") or ""),
        str(play.get("play_text") or ""),
    ])).casefold()


def _truthy(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in {"", "0", "false", "no", "none", "nan"}
    return bool(value)


def classify_cfb_play(play):
    """Return only concrete, text-supported unusual CFB play events."""
    out = []
    pid = str(play.get("play_id") or "")
    text = _text(play)
    yards = int(play.get("yards_gained") or 0)
    scoring = _truthy(play.get("scoring"))
    down = int(play.get("down") or 0)

    if scoring and yards >= 50:
        out.append((
            "CFB_EXPLOSIVE_SCORE:" + pid,
            "ICONIC_PLAY",
            ["cfb", "explosive_play", "scoring_play"],
            f"{yards}-yard scoring play",
        ))

    if down == 4 and yards >= 20:
        out.append((
            "CFB_FOURTH_DOWN:" + pid,
            "ON_FIELD_ODDITY",
            ["cfb", "fourth_down", "explosive_play"],
            f"{yards} yards gained on fourth down",
        ))

    turnover_words = ("interception", "fumble recovery", "fumble recovered")
    if scoring and any(word in text for word in turnover_words):
        out.append((
            "CFB_TURNOVER_SCORE:" + pid,
            "ICONIC_PLAY",
            ["cfb", "turnover", "defensive_score"],
            "A turnover play produced a score",
        ))

    if "safety" in text:
        out.append((
            "CFB_SAFETY:" + pid,
            "ON_FIELD_ODDITY",
            ["cfb", "safety", "rare_score"],
            "The play resulted in a safety",
        ))

    if scoring and "blocked" in text and any(word in text for word in ("kick", "punt", "field goal")):
        out.append((
            "CFB_BLOCKED_KICK_SCORE:" + pid,
            "ON_FIELD_ODDITY",
            ["cfb", "special_teams", "blocked_kick", "scoring_play"],
            "A blocked-kick play produced a score",
        ))

    if scoring and any(word in text for word in ("kickoff return", "punt return")) and yards >= 70:
        out.append((
            "CFB_RETURN_SCORE:" + pid,
            "ICONIC_PLAY",
            ["cfb", "special_teams", "return_touchdown"],
            f"{yards}-yard return score",
        ))

    return out


def classify_cfb_game(plays):
    """Aggregate concrete chaos patterns from one verified CFB game."""
    turnovers = 0
    explosive_scores = 0
    fourth_down_explosives = 0
    safeties = 0
    special_teams_scores = 0
    turnover_scores = 0

    for play in plays:
        text = _text(play)
        yards = int(play.get("yards_gained") or 0)
        scoring = _truthy(play.get("scoring"))
        down = int(play.get("down") or 0)

        if "interception" in text or "fumble recovery (opponent)" in text or "fumble recovered by" in text:
            turnovers += 1
        if scoring and yards >= 40:
            explosive_scores += 1
        if down == 4 and yards >= 15:
            fourth_down_explosives += 1
        if "safety" in text:
            safeties += 1
        if scoring and any(word in text for word in ("kickoff return", "punt return", "blocked kick", "blocked punt", "blocked field goal")):
            special_teams_scores += 1
        if scoring and ("interception" in text or "fumble recovery" in text or "fumble recovered by" in text):
            turnover_scores += 1

    out = []
    if turnovers >= 6:
        out.append((
            "CFB_TURNOVER_AVALANCHE",
            "ON_FIELD_ODDITY",
            ["cfb", "turnover_avalanche", "chaos_game"],
            f"{turnovers} turnover plays",
        ))
    if turnover_scores >= 2:
        out.append((
            "CFB_DEFENSIVE_SCORE_FRENZY",
            "ON_FIELD_ODDITY",
            ["cfb", "defensive_score", "chaos_game"],
            f"{turnover_scores} turnover plays that produced scores",
        ))
    if explosive_scores >= 4:
        out.append((
            "CFB_EXPLOSIVE_SCORE_CLUSTER",
            "ICONIC_PLAY",
            ["cfb", "explosive_play", "chaos_game"],
            f"{explosive_scores} scoring plays of at least 40 yards",
        ))
    if fourth_down_explosives >= 3:
        out.append((
            "CFB_FOURTH_DOWN_MADNESS",
            "ON_FIELD_ODDITY",
            ["cfb", "fourth_down", "chaos_game"],
            f"{fourth_down_explosives} fourth-down gains of at least 15 yards",
        ))
    if safeties >= 2:
        out.append((
            "CFB_SAFETY_CHAOS",
            "ON_FIELD_ODDITY",
            ["cfb", "safety", "rare_score", "chaos_game"],
            f"{safeties} safeties",
        ))
    if special_teams_scores >= 2:
        out.append((
            "CFB_SPECIAL_TEAMS_CHAOS",
            "ON_FIELD_ODDITY",
            ["cfb", "special_teams", "chaos_game"],
            f"{special_teams_scores} special-teams scoring plays",
        ))
    return out
