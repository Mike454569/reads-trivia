"""Starting-offense-lineup domain adapter -- NFL Starting Lineups (v1.8, Part F).

--- WHY THIS IS A "NAMES" PUZZLE, NOT THE "COLLEGES" PUZZLE THE SPEC ASKED FOR ---
The v1.8 spec's primary acceptance test asks for "guess the NFL team from the
colleges attended by the players on its offense, displayed by position." That
EXACT concept was audited directly against the real database before any code
here was written, and is NOT viably supported:
  - `canonical_roster_seasons.school_id` is NULL for 100% of rows (0/60,246).
  - `canonical_players.primary_school_id` is NULL for 100% of rows (0/17,113).
  - `nfl_cfb_player_links` (the only NFL<->CFB player bridge) has 124 total
    rows, and only 39 correspond to a player with any recorded `starts`.
39 real players is nowhere near enough to build a real starting offense for
any real team-season. Building this with any other data (guessing colleges,
inferring from partial matches, etc.) would mean fabricating college
attendance for players the database does not actually document one -- exactly
what this milestone's own instructions forbid.

This adapter instead builds the truthful, data-backed variant of the same
IDEA: a real starting offense, laid out by position, guessed from real
player NAMES instead of colleges. Same mechanic (`guess`, 4-option
multiple choice of team names), same visual idea (a position-lineup board,
not a sentence) -- `visual_template=POSITION_LINEUP` (see
tools/director_v02/visual_templates.py). Every player shown, every team,
every season is real and SOURCE_BACKED; nothing here is invented.

--- WHY "starts" IS THE STARTER SIGNAL (not a depth-chart table) ---
There is no explicit "who started this game" table in this database. Reusing
the reasoning already established for other Reads Engine surfaces: `starts`
(real, source-backed games-started count) is a defensible, honest proxy for
"this is who actually started at this position that season" -- not a guess,
a genuine count of games the player started, sourced from NFLVERSE_DATA /
NFLVERSE_ROSTERS. Selecting the single HIGHEST-`starts` player per bucket for
a given (season, team_code) is the natural, non-invented reading of that
column.

--- WHY THE OFFENSIVE LINE IS ONE GENERIC "OL" GROUP, NOT 5 NAMED SLOTS ---
Audited directly: `position` values for offensive linemen are genuinely
inconsistent across rows -- some rows say `LT`/`RT` (specific side), many
say the generic `T`, and `LG`/`RG`/`C`/`G` show up too, with no reliable way
to know which convention a given team-season used. Claiming "this specific
player was your LEFT tackle" when the underlying row only says `T` would be
fabricating precision the data doesn't have. This adapter instead buckets
every offensive-line-family position (`LT`,`RT`,`T`,`LG`,`RG`,`G`,`C`) into
one honest "OL" group and takes the top 5 by `starts` -- five real starting
offensive linemen, labeled as a group, not five falsely-specific slots.

--- REAL COVERAGE (audited before writing this file) ---
415 of 416 real (season, team_code) pairs with any `starts>0` data satisfy
this shape (>=1 QB, >=1 RB, >=2 WR, >=1 TE, >=5 OL-family), spanning real
seasons 2006-2018.

--- DIFFICULTY: A NEW, HONEST HEURISTIC (no puzzle_catalog row exists yet) ---
Draft/Championship look up a pre-computed difficulty score from Engine's own
`puzzle_catalog` table. No such row exists for this brand-new domain (Part D:
adding a domain is the sanctioned way to extend the registry -- this is a
genuinely new domain, not a rename of an old one). Rather than fabricate a
"difficulty" claim, this uses one real, disclosed, deterministic signal:
season recency (`(max_season - season) / (max_season - min_season)`,
mapped through the Engine's own `band()`/`map_band()` -- the same bucketing
Draft/Championship use). More recent lineups are treated as easier to
recognize than older ones. This is a stated, defensible heuristic, not a
claim of empirical validation -- documented here so nobody mistakes it for
one.
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .draft import resolve_franchise, teams_active_in_season

OUT_PATH = None  # not exported to a static .js file -- Director-pipeline-only, like player_from_clues
CATEGORY = "NFL Starting Lineups"
REQUIRED_SOURCES = ("NFLVERSE_DATA", "NFLVERSE_ROSTERS")  # canonical_roster_seasons' two legitimate provenances
TRACK_ENTITY = False  # each (season, team_code) is already unique by construction -- same call as championship.py

MIN_SEASON = 2006
MAX_SEASON = 2018

QB_POSITIONS = frozenset({"QB"})
RB_POSITIONS = frozenset({"RB"})
WR_POSITIONS = frozenset({"WR"})
TE_POSITIONS = frozenset({"TE"})
OL_POSITIONS = frozenset({"LT", "RT", "T", "LG", "RG", "G", "C"})


def safety_check(c) -> dict:
    return safety.check_table_wide_safety(
        c, "canonical_roster_seasons", REQUIRED_SOURCES, where_extra="starts > 0"
    )


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT crs.season, crs.team_code, crs.player_id, cp.display_name, crs.position, crs.starts "
        "FROM canonical_roster_seasons crs JOIN canonical_players cp ON cp.player_id = crs.player_id "
        "WHERE crs.starts > 0 AND crs.position IS NOT NULL "
        "AND crs.verification_status = 'SOURCE_BACKED' AND crs.source_id IN (?, ?) "
        "ORDER BY crs.season, crs.team_code, crs.starts DESC, crs.player_id",
        REQUIRED_SOURCES,
    ).fetchall()

    groups: dict[tuple[int, str], list] = {}
    for r in rows:
        groups.setdefault((r["season"], r["team_code"]), []).append(r)

    candidates = []
    for (season, team_code), players in groups.items():
        qbs = [p for p in players if p["position"] in QB_POSITIONS]
        rbs = [p for p in players if p["position"] in RB_POSITIONS]
        wrs = [p for p in players if p["position"] in WR_POSITIONS]
        tes = [p for p in players if p["position"] in TE_POSITIONS]
        ols = [p for p in players if p["position"] in OL_POSITIONS]
        if not (len(qbs) >= 1 and len(rbs) >= 1 and len(wrs) >= 2 and len(tes) >= 1 and len(ols) >= 5):
            continue
        # Each list is already sorted by starts DESC, player_id (deterministic tie-break) from the
        # ORDER BY clause above -- taking a fixed-size prefix is a stable, non-random selection.
        lineup = {
            "QB": [qbs[0]],
            "RB": [rbs[0]],
            "WR": wrs[:2],
            "TE": [tes[0]],
            "OL": ols[:5],
        }
        candidates.append((season, team_code, lineup))

    rng_order = engine.seeded(seed)
    candidates.sort(key=lambda x: (x[0], x[1]))  # deterministic base order before shuffle
    rng_order.shuffle(candidates)
    return candidates


def evaluate(c, raw, rng, guard):
    season, team_code, lineup = raw
    if not (MIN_SEASON <= season <= MAX_SEASON):
        return "SEASON_OUT_OF_HEURISTIC_RANGE"

    correct, err = resolve_franchise(c, team_code, season)
    if err:
        return err

    pool = teams_active_in_season(c, season)
    pool.pop(correct["franchise_id"], None)
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[fid] for fid in distractor_ids]

    options = [correct["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    # The prompt must embed something that makes it unique per (season, team) --
    # same requirement Draft (player name) and Championship (team+season) already
    # meet -- WITHOUT naming the team itself, which is the answer being guessed.
    # The starting QB's name is safe to embed: it is already shown on the lineup
    # board itself (visual_payload), so this adds no new information a player
    # doesn't already see, it just also makes the guard's duplicate-question
    # check meaningful (plain "its {season} starting offense" collides across
    # every team sharing a season, which a bare season number cannot avoid).
    qb_name = lineup["QB"][0]["display_name"]
    question = f"Guess the NFL team from its {season} starting offense (led by {qb_name} at QB), by position."
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct["full_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / (MAX_SEASON - MIN_SEASON)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    positions_payload = []
    all_players = []
    for slot in ("QB", "RB", "WR", "TE", "OL"):
        for p in lineup[slot]:
            positions_payload.append({"position": slot, "name": p["display_name"], "starts": p["starts"]})
            all_players.append(p["display_name"])

    notes = (
        f"The {correct['full_name']}'s {season} starting offense (by real games-started). "
        f"Offensive-line positions are grouped as \"OL\" because this database does not reliably "
        f"distinguish left/right tackle and guard assignments across every season."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP",
        "visual_payload": {"positions": positions_payload, "season": season},
        "_audit": {
            "team_code": team_code, "season": season,
            "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "lineup_player_names": all_players,
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCES[0],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real (season, team_code) pairs with a qualifying starting offense; "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    franchises = sorted(set(q["_audit"]["franchise_id"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_franchises": len(franchises),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/lineup.py -- NFL Starting Lineups (v1.8, Part F).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    names = ", ".join(a["lineup_player_names"])
    return [
        f"- **Season/team:** {a['season']}, franchise `{a['franchise_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\"), raw team code `{a['team_code']}`",
        f"- **Starting offense (by real games-started):** {names}",
        f"- **Underlying Engine source:** `canonical_roster_seasons`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
