"""CFB play-by-play -- reusable knowledge relationships (Knowledge
Expansion Batch 3).

Built entirely on the EXISTING `cfb_plays` table (3,718,552 real rows,
2002-2025, real `drive_id`) -- no new table, no duplicated rows.

--- SCORING-PLAY CLASSIFICATION: play_type IS the real, structured signal ---
Unlike NFL's `nfl_plays`, CFB's source `play_type` is ALREADY a granular,
purpose-built category (confirmed by direct inspection of the real
distinct values: "Rushing Touchdown", "Passing Touchdown", "Interception
Return Touchdown", "Fumble Return Touchdown", "Kickoff/Punt/Blocked Punt
Return Touchdown", "Field Goal Good/Missed", "Extra Point Good/Missed",
"2pt Conversion"/"Two Point Pass", "Safety") -- classification here is a
direct mapping from that field, not text-guessing.

A real, disclosed source disagreement was found and is preserved, not
hidden: the separate `scoring` boolean column agrees with the play_type-
implied made/missed result ~97-99% of the time but not always (e.g. 957
of 45,567 "Field Goal Good" rows have `scoring=0`; 16 of 14,693 "Field
Goal Missed" rows have `scoring=1`). `play_type` is used as the primary
classification (it is the more specific, purpose-built field); every
classified row also carries `scoring_flag_agrees` so a caller can see
and handle the real minority disagreement rather than have it hidden.

--- PLAYER IDENTITY: NAME-PARSED FROM play_text, RESOLVED PER-QUERY ---
`cfb_plays` has NO player-ID columns at all. Player identity for a
scoring play is resolved here, on demand, by regex-extracting the
leading player name out of `play_text` (real, standardized CFBD
boilerplate -- confirmed patterns below) and matching it against
`cfb_roster_seasons_real` + `canonical_cfb_players` for the play's own
real `season` + offense/defense `school_id` -- a name is only ever
considered RESOLVED when that join yields exactly one real canonical
player; 0 or 2+ matches are UNRESOLVED/AMBIGUOUS, never guessed. This is
NOT run over all 3.7M rows -- only over the (much smaller) real scoring-
play subset a caller actually asks about, which is the honest, bounded
scope this batch commits to (see `identity_coverage()`).
"""
from __future__ import annotations

import re

_RUSH_TD_RE = re.compile(r"^(?P<name>.+?) run for \d+ yds? for a TD")
_PASS_TD_RE = re.compile(r"^(?P<passer>.+?) pass complete to (?P<receiver>.+?) for \d+ yds? for a TD")
_RETURN_TD_RE = re.compile(r"^(?P<name>.+?) \d+ Yds? (?:Interception|Kickoff|Punt) Return", re.IGNORECASE)
_SACK_RE = re.compile(r"^(?P<passer>.+?) sacked by (?P<defender>.+?) for a loss")

# --- Knowledge Expansion Batch 4: broader, non-scoring-only event parsing ---
# Real, confirmed modern-era (~2013+) CFBD play_text patterns for events
# beyond touchdowns. Each pattern was verified against real sample rows
# before being adopted (see cfb_pbp_facts identity-coverage measurement);
# older-era text (pre-~2013) uses different phrasing and is NOT covered by
# these patterns -- those rows are honestly unresolved, never guessed.
_RUSH_RE = re.compile(r"^(?P<rusher>.+?) run for")
_PASS_RE = re.compile(r"^(?P<passer>.+?) pass complete to (?P<receiver>.+?) for")
# Sack text has three real, distinct shapes: passer+defender named, passer
# only (no defender identified), or defender only (passer name omitted
# from this particular row) -- each is a real, distinct partial-identity
# case, never force-filled from the other.
_SACK_WITH_DEFENDER_RE = re.compile(r"^(?P<passer>.+?) sacked by (?P<defender>.+?)(?: and (?P<defender2>.+?))? for a loss")
_SACK_NO_DEFENDER_RE = re.compile(r"^(?P<passer>.+?) sacked for a loss")
_SACK_DEFENDER_ONLY_RE = re.compile(r"^sacked by (?P<defender>.+?)(?: and (?P<defender2>.+?))? for a loss")
_INTERCEPTION_RE = re.compile(r"^(?P<passer>.+?) pass intercepted(?: by)? (?P<defender>.+?) return for")
_FG_KICKER_RE = re.compile(r"^(?P<kicker>.+?) \d+ yd FG (?:GOOD|MISSED)")
_XP_KICKER_RE = re.compile(r"^Extra point by (?P<kicker>.+?)(?:\s*\(|\s+is)")
_KICKOFF_RETURN_RE = re.compile(r"^(?P<kicker>.+?) kickoff for \d+ yds\s*,\s*(?P<returner>\S.*?) return for")

# Event-type -> (regex, roles) used by `extract_event_participants`.
_EVENT_PATTERNS = {
    "Rush": (_RUSH_RE, ("rusher",)),
    "Rushing Touchdown": (_RUSH_RE, ("rusher",)),
    "Pass Reception": (_PASS_RE, ("passer", "receiver")),
    "Pass Completion": (_PASS_RE, ("passer", "receiver")),
    "Passing Touchdown": (_PASS_RE, ("passer", "receiver")),
    "Field Goal Good": (_FG_KICKER_RE, ("kicker",)),
    "Field Goal Missed": (_FG_KICKER_RE, ("kicker",)),
    "Extra Point Good": (_XP_KICKER_RE, ("kicker",)),
    "Extra Point Missed": (_XP_KICKER_RE, ("kicker",)),
    "Kickoff Return (Offense)": (_KICKOFF_RETURN_RE, ("kicker", "returner")),
}


def extract_event_participants(row: dict) -> dict:
    """PLAY -> raw participant name(s) for the play's real event type.
    Sack and interception get dedicated handling (multiple real text
    shapes); everything else uses the `_EVENT_PATTERNS` table. Returns an
    empty dict for a play type/text this module doesn't have a confirmed
    pattern for -- never guesses a shape it hasn't verified."""
    text = row.get("play_text") or ""
    pt = row.get("play_type")

    if pt == "Sack":
        m = _SACK_WITH_DEFENDER_RE.match(text)
        if m:
            out = {"passer_name_raw": m.group("passer"), "defender_name_raw": m.group("defender")}
            if m.group("defender2"):
                out["defender2_name_raw"] = m.group("defender2")
            return out
        m = _SACK_NO_DEFENDER_RE.match(text)
        if m:
            return {"passer_name_raw": m.group("passer")}
        m = _SACK_DEFENDER_ONLY_RE.match(text)
        if m:
            out = {"defender_name_raw": m.group("defender")}
            if m.group("defender2"):
                out["defender2_name_raw"] = m.group("defender2")
            return out
        return {}

    if pt in ("Pass Interception", "Pass Interception Return", "Interception"):
        m = _INTERCEPTION_RE.match(text)
        return {"passer_name_raw": m.group("passer"), "defender_name_raw": m.group("defender")} if m else {}

    if pt == "Interception Return Touchdown":
        m = _RETURN_TD_RE.match(text)
        return {"defender_name_raw": m.group("name")} if m else {}

    entry = _EVENT_PATTERNS.get(pt)
    if not entry:
        return {}
    pattern, roles = entry
    m = pattern.match(text)
    if not m:
        return {}
    return {f"{role}_name_raw": m.group(role) for role in roles}

SCORING_PLAY_TYPE_MAP = {
    "Rushing Touchdown": "RUSHING_TOUCHDOWN",
    "Passing Touchdown": "PASSING_TOUCHDOWN",
    "Interception Return Touchdown": "INTERCEPTION_RETURN_TOUCHDOWN",
    "Fumble Return Touchdown": "FUMBLE_RETURN_TOUCHDOWN",
    "Kickoff Return Touchdown": "KICKOFF_RETURN_TOUCHDOWN",
    "Punt Return Touchdown": "PUNT_RETURN_TOUCHDOWN",
    "Blocked Punt Touchdown": "BLOCKED_PUNT_RETURN_TOUCHDOWN",
    "Field Goal Good": "FIELD_GOAL",
    "Extra Point Good": "EXTRA_POINT",
    "2pt Conversion": "TWO_POINT_CONVERSION",
    "Safety": "SAFETY",
}
# Made vs. missed CANNOT be assumed by type alone for "2pt Conversion" /
# "Two Point Pass" (both label successes AND failures under similar
# names in the raw type) -- for those two, the real `scoring` column is
# the only reliable made/missed signal and is used directly.
_AMBIGUOUS_RESULT_TYPES = {"2pt Conversion", "Two Point Pass"}
TURNOVER_PLAY_TYPES = {
    "Interception Return Touchdown": "INTERCEPTION", "Pass Interception Return": "INTERCEPTION",
    "Interception": "INTERCEPTION", "Pass Interception": "INTERCEPTION",
    "Fumble Return Touchdown": "FUMBLE_LOST", "Fumble Recovery (Opponent)": "FUMBLE_LOST",
}


def game_plays(c, *, game_id: str) -> list[dict]:
    """PLAY -> GAME (+ PERIOD/CLOCK/DOWN/DISTANCE/YARDS_TO_GOAL/OFFENSE/
    DEFENSE/PLAY_TYPE/YARDS_GAINED/RESULT), raw play text preserved."""
    rows = c.execute(
        "SELECT game_id, play_id, season, week, drive_id, offense_school_id, defense_school_id, "
        "period, clock_minutes, clock_seconds, down, distance, yards_to_goal, yards_gained, "
        "play_type, play_text, scoring FROM cfb_plays WHERE game_id=? ORDER BY CAST(play_id AS INTEGER)",
        (game_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def classify_scoring_play(row: dict) -> tuple[str | None, bool | None]:
    """PLAY -> (scoring type, scoring_flag_agrees). Returns (None, None)
    for a non-scoring play."""
    pt = row.get("play_type")
    if pt not in SCORING_PLAY_TYPE_MAP:
        return None, None
    if pt in _AMBIGUOUS_RESULT_TYPES:
        if not row.get("scoring"):
            return None, None  # a real, failed conversion attempt -- not a scoring play
        return "TWO_POINT_CONVERSION", True
    scoring_type = SCORING_PLAY_TYPE_MAP[pt]
    agrees = bool(row.get("scoring")) == True
    return scoring_type, agrees


def classify_turnover(row: dict) -> str | None:
    """PLAY -> TURNOVER_TYPE, from the real structured play_type only."""
    return TURNOVER_PLAY_TYPES.get(row.get("play_type"))


def _extract_scoring_names(row: dict) -> dict:
    """Regex-extracts the leading player name(s) from real, standardized
    CFBD play_text for the scoring subtypes where a pattern is confirmed.
    Returns raw names only -- NOT yet resolved to a canonical identity."""
    text = row.get("play_text") or ""
    pt = row.get("play_type")
    if pt == "Rushing Touchdown":
        m = _RUSH_TD_RE.match(text)
        return {"rusher_name_raw": m.group("name")} if m else {}
    if pt == "Passing Touchdown":
        m = _PASS_TD_RE.match(text)
        return {"passer_name_raw": m.group("passer"), "receiver_name_raw": m.group("receiver")} if m else {}
    if pt in ("Interception Return Touchdown", "Kickoff Return Touchdown", "Punt Return Touchdown"):
        m = _RETURN_TD_RE.match(text)
        return {"returner_name_raw": m.group("name")} if m else {}
    return {}


def _resolve_cfb_player_name(c, *, name: str, school_id: str | None, season: int) -> dict:
    """NAME (+ SCHOOL + SEASON) -> canonical cfb_player_id. Only ever
    resolves on a real, unique roster match -- never guesses across
    multiple same-named candidates."""
    if not name or not school_id:
        return {"name_raw": name, "cfb_player_id": None, "resolution": "MISSING_INPUT"}
    rows = c.execute(
        "SELECT p.cfb_player_id FROM cfb_roster_seasons_real rs "
        "JOIN canonical_cfb_players p ON p.cfb_player_id = rs.cfb_player_id "
        "WHERE rs.season=? AND rs.school_id=? AND p.display_name=?",
        (season, school_id, name),
    ).fetchall()
    if len(rows) == 1:
        return {"name_raw": name, "cfb_player_id": rows[0]["cfb_player_id"], "resolution": "UNIQUE_ROSTER_MATCH"}
    if len(rows) == 0:
        return {"name_raw": name, "cfb_player_id": None, "resolution": "NO_ROSTER_MATCH"}
    return {"name_raw": name, "cfb_player_id": None, "resolution": f"AMBIGUOUS_{len(rows)}_CANDIDATES"}


def game_scoring_plays(c, *, game_id: str, resolve_identity: bool = True) -> list[dict]:
    """GAME -> SCORING_PLAYS (+ QUARTER, YARDS, player identity where
    resolvable)."""
    out = []
    for row in game_plays(c, game_id=game_id):
        scoring_type, agrees = classify_scoring_play(row)
        if scoring_type is None:
            continue
        entry = {
            "play_id": row["play_id"], "scoring_type": scoring_type, "period": row["period"],
            "yards": row["yards_gained"], "offense_school_id": row["offense_school_id"],
            "defense_school_id": row["defense_school_id"], "scoring_flag_agrees": agrees,
            "play_text": row["play_text"],
        }
        if resolve_identity:
            names = _extract_scoring_names(row)
            resolved = {}
            for role, name in names.items():
                school_for_role = row["defense_school_id"] if role == "returner_name_raw" else row["offense_school_id"]
                resolved[role.replace("_name_raw", "")] = _resolve_cfb_player_name(
                    c, name=name, school_id=school_for_role, season=row["season"])
            entry["identity"] = resolved
        out.append(entry)
    return out


# Roles resolved against the DEFENSE school (the play's tackler/defender
# side); every other role resolves against the OFFENSE school. Kickoff
# returns are a real exception -- see module docstring's kickoff-return
# offense/defense-convention note: the kicking team is `offense_school_id`.
_DEFENSE_SIDE_ROLES = frozenset({"defender", "defender2", "returner"})


def game_play_events(c, *, game_id: str, event_types: tuple[str, ...] | None = None,
                      resolve_identity: bool = True) -> list[dict]:
    """GAME -> PLAY_EVENTS -- broader-than-scoring player-event coverage
    (Knowledge Expansion Batch 4): rush/pass/sack/interception/kicker/
    kickoff-return participants, resolved on demand for the plays a
    caller actually asks about (never precomputed across all 3.7M rows --
    see module docstring)."""
    out = []
    for row in game_plays(c, game_id=game_id):
        pt = row["play_type"]
        if event_types and pt not in event_types:
            continue
        participants = extract_event_participants(row)
        if not participants:
            continue
        entry = {
            "play_id": row["play_id"], "play_type": pt, "period": row["period"],
            "yards": row["yards_gained"], "offense_school_id": row["offense_school_id"],
            "defense_school_id": row["defense_school_id"], "play_text": row["play_text"],
        }
        if resolve_identity:
            resolved = {}
            for role_key, name in participants.items():
                role = role_key.replace("_name_raw", "")
                school_for_role = row["defense_school_id"] if role in _DEFENSE_SIDE_ROLES else row["offense_school_id"]
                resolved[role] = _resolve_cfb_player_name(c, name=name, school_id=school_for_role, season=row["season"])
            entry["identity"] = resolved
        out.append(entry)
    return out


def broader_identity_coverage(c, *, game_id: str) -> dict:
    """Measured, honest player-identity coverage across the BROADER event
    set (rush/pass/sack/interception/kicker/kickoff-return), not just
    scoring plays -- the real, expanded scope Batch 4 adds on top of
    Batch 3's scoring-only measurement."""
    events = game_play_events(c, game_id=game_id, resolve_identity=True)
    by_event_type: dict[str, dict] = {}
    total = resolved = unresolved = ambiguous = 0
    for e in events:
        et = e["play_type"]
        stats = by_event_type.setdefault(et, {"slots": 0, "resolved": 0, "unresolved": 0, "ambiguous": 0})
        for role, info in e.get("identity", {}).items():
            total += 1
            stats["slots"] += 1
            if info["resolution"] == "UNIQUE_ROSTER_MATCH":
                resolved += 1
                stats["resolved"] += 1
            elif info["resolution"].startswith("AMBIGUOUS"):
                ambiguous += 1
                stats["ambiguous"] += 1
            else:
                unresolved += 1
                stats["unresolved"] += 1
    return {
        "game_id": game_id, "events_with_a_pattern_match": len(events),
        "name_slots_found": total, "resolved": resolved, "unresolved": unresolved, "ambiguous": ambiguous,
        "resolution_pct": round(100.0 * resolved / total, 1) if total else 0.0,
        "by_event_type": by_event_type,
    }


def game_turnovers(c, *, game_id: str) -> list[dict]:
    """GAME -> TURNOVERS (+ TURNOVER_TYPE)."""
    out = []
    for row in game_plays(c, game_id=game_id):
        t = classify_turnover(row)
        if t is None:
            continue
        out.append({"play_id": row["play_id"], "turnover_type": t, "period": row["period"],
                     "offense_school_id": row["offense_school_id"], "defense_school_id": row["defense_school_id"],
                     "play_text": row["play_text"]})
    return out


def game_drives(c, *, game_id: str) -> list[dict]:
    """GAME -> DRIVES (+ OFFENSE, START/END, PLAY_COUNT, YARDS, RESULT,
    POINTS, SCORING, TURNOVER) -- uses the real, existing `drive_id`."""
    plays = game_plays(c, game_id=game_id)
    drives: dict[str, list[dict]] = {}
    order: list[str] = []
    for p in plays:
        did = p["drive_id"]
        if did not in drives:
            drives[did] = []
            order.append(did)
        drives[did].append(p)

    out = []
    for did in order:
        dplays = drives[did]
        first, last = dplays[0], dplays[-1]
        total_yards = sum(p["yards_gained"] or 0 for p in dplays)
        scoring_plays_in_drive = [classify_scoring_play(p) for p in dplays]
        scoring_types = [s for s, _ in scoring_plays_in_drive if s]
        turnover_types = [classify_turnover(p) for p in dplays]
        turnover_types = [t for t in turnover_types if t]
        points = 6 * sum(1 for s in scoring_types if "TOUCHDOWN" in s) + \
            3 * scoring_types.count("FIELD_GOAL") + 1 * scoring_types.count("EXTRA_POINT") + \
            2 * scoring_types.count("TWO_POINT_CONVERSION") + 2 * scoring_types.count("SAFETY")
        out.append({
            "drive_id": did, "offense_school_id": first["offense_school_id"],
            "defense_school_id": first["defense_school_id"],
            "start_yards_to_goal": first["yards_to_goal"], "end_yards_to_goal": last["yards_to_goal"],
            "play_count": len(dplays), "yards": total_yards,
            "result": scoring_types[-1] if scoring_types else (turnover_types[-1] if turnover_types else last["play_type"]),
            "points": points, "is_scoring": bool(scoring_types), "is_turnover": bool(turnover_types),
        })
    return out


def explosive_plays(c, *, game_id: str | None = None, season: int | None = None,
                     rush_threshold: int = 10, pass_threshold: int = 20, any_play_threshold: int = 40) -> list[dict]:
    """TEAM/GAME -> EXPLOSIVE_PLAYS -- caller-chosen threshold, exact
    yards preserved (same reusable-threshold design as the NFL module)."""
    where = []
    params: list = []
    if game_id:
        where.append("game_id=?")
        params.append(game_id)
    if season:
        where.append("season=?")
        params.append(season)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = c.execute(
        f"SELECT game_id, play_id, play_type, yards_gained, offense_school_id, defense_school_id, play_text "
        f"FROM cfb_plays {where_sql}{' AND' if where_sql else 'WHERE'} play_type IN ('Rush','Pass Reception','Pass Completion')",
        params,
    ).fetchall()
    out = []
    for row in rows:
        yards = row["yards_gained"] or 0
        threshold = rush_threshold if row["play_type"] == "Rush" else pass_threshold
        if yards >= threshold or yards >= any_play_threshold:
            out.append(dict(row))
    return out


def game_derived_facts(c, *, game_id: str) -> dict:
    """GAME -> derived PBP facts (longest play/TD, first/final TD, first
    turnover, totals, scoring by quarter)."""
    plays = game_plays(c, game_id=game_id)
    if not plays:
        return {"game_id": game_id, "found": False}

    scoring = [(p, *classify_scoring_play(p)) for p in plays]
    scoring = [(p, t, a) for p, t, a in scoring if t]
    turnovers = [(p, classify_turnover(p)) for p in plays]
    turnovers = [(p, t) for p, t in turnovers if t]
    real_plays = [p for p in plays if p["play_type"] in ("Rush", "Pass Reception", "Pass Completion") and p["yards_gained"] is not None]

    longest_play = max(real_plays, key=lambda p: p["yards_gained"], default=None)
    tds = [p for p, t, _a in scoring if "TOUCHDOWN" in t]
    longest_td = max(tds, key=lambda p: p["yards_gained"] or 0, default=None)

    by_period: dict[int, int] = {}
    for p, _t, _a in scoring:
        by_period[p["period"]] = by_period.get(p["period"], 0) + 1

    sacks = [p for p in plays if p["play_type"] == "Sack"]

    return {
        "game_id": game_id, "found": True,
        "longest_play": {"play_id": longest_play["play_id"], "yards": longest_play["yards_gained"],
                          "play_text": longest_play["play_text"]} if longest_play else None,
        "longest_touchdown": {"play_id": longest_td["play_id"], "yards": longest_td["yards_gained"],
                               "play_text": longest_td["play_text"]} if longest_td else None,
        "first_touchdown": {"play_id": tds[0]["play_id"], "period": tds[0]["period"], "play_text": tds[0]["play_text"]} if tds else None,
        "final_scoring_play": {"play_id": scoring[-1][0]["play_id"], "type": scoring[-1][1],
                                "play_text": scoring[-1][0]["play_text"]} if scoring else None,
        "first_turnover": {"play_id": turnovers[0][0]["play_id"], "type": turnovers[0][1]} if turnovers else None,
        "total_turnovers": len(turnovers), "total_sacks": len(sacks),
        "scoring_play_count": len(scoring), "scoring_by_period": by_period,
    }


def identity_coverage(c, *, game_id: str) -> dict:
    """Measured, honest player-identity coverage for CFB scoring plays IN
    ONE GAME -- the real, bounded scope this batch resolves at query time
    (not precomputed across all 3.7M rows; see module docstring)."""
    # Scoring types this module knows a real, extractable name pattern
    # for -- a play of one of these types with zero extracted name slots
    # is a real regex-extraction miss, and counts as unresolved too, not
    # silently excluded from the denominator.
    _EXPECTED_NAME_TYPES = {
        "RUSHING_TOUCHDOWN": 1, "PASSING_TOUCHDOWN": 2,
        "INTERCEPTION_RETURN_TOUCHDOWN": 1, "KICKOFF_RETURN_TOUCHDOWN": 1, "PUNT_RETURN_TOUCHDOWN": 1,
    }
    scoring = game_scoring_plays(c, game_id=game_id, resolve_identity=True)
    total_name_slots = resolved = unresolved = ambiguous = 0
    for s in scoring:
        identity = s.get("identity", {})
        expected = _EXPECTED_NAME_TYPES.get(s["scoring_type"], 0)
        total_name_slots += max(expected, len(identity))
        if expected and not identity:
            unresolved += expected  # regex found no name at all on a type that should have one
            continue
        for role, info in identity.items():
            if info["resolution"] == "UNIQUE_ROSTER_MATCH":
                resolved += 1
            elif info["resolution"].startswith("AMBIGUOUS"):
                ambiguous += 1
            else:
                unresolved += 1
    return {
        "game_id": game_id, "scoring_plays": len(scoring), "name_slots_found": total_name_slots,
        "resolved": resolved, "unresolved": unresolved, "ambiguous": ambiguous,
        "resolution_pct": round(100.0 * resolved / total_name_slots, 1) if total_name_slots else 0.0,
    }


def eligibility_report(c) -> dict:
    total = c.execute("SELECT COUNT(*) FROM cfb_plays").fetchone()[0]
    seasons = c.execute("SELECT MIN(season), MAX(season) FROM cfb_plays").fetchone()
    games = c.execute("SELECT COUNT(DISTINCT game_id) FROM cfb_plays").fetchone()[0]
    drives = c.execute("SELECT COUNT(DISTINCT drive_id) FROM cfb_plays WHERE drive_id IS NOT NULL").fetchone()[0]
    scoring_agree = c.execute(
        "SELECT COUNT(*) FROM cfb_plays WHERE play_type IN ('Field Goal Good','Extra Point Good') AND scoring=1"
    ).fetchone()[0]
    scoring_disagree = c.execute(
        "SELECT COUNT(*) FROM cfb_plays WHERE play_type IN ('Field Goal Good','Extra Point Good') AND scoring=0"
    ).fetchone()[0]
    return {
        "total_rows": total, "season_range": [seasons[0], seasons[1]], "distinct_games": games,
        "distinct_drives": drives,
        "scoring_flag_vs_play_type_agreement": {"agree": scoring_agree, "disagree": scoring_disagree},
    }
