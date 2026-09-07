"""Franchise Marathon (Closeout Part 3 rebuild) -- a real franchise's history
across 8 different real dimensions, not a Super Bowl roster quiz with extra
steps.

--- THE REAL PROBLEM THIS REPLACES ---
The previous "franchise_marathon_guess" mode was a thin filter over
sb_champion_offense_college.py's 60-board SB_CHAMPION table: given a
franchise_name, it returned every one of that franchise's real Super Bowl
championship boards, in order, and asked the SAME "guess team+season from
starting-offense colleges" question for each one. A franchise with 1 title
got a 1-question "marathon"; a franchise with 0 titles got NONE at all
(shortfall to empty). Either way, 100% of the content was Super Bowl roster
trivia -- exactly the "recycling the same Super Bowl roster questions"
pattern this closeout pass exists to end.

--- THE REBUILD ---
A fixed 8-stage progression, each stage pulling from a DIFFERENT real table
this Engine already has, verified directly before writing this file:
    0. IDENTITY       -- team_seasons (relocation history, or conference/
                          division if the franchise never moved)
    1. SEASON_RECORD  -- season_standings (real win-loss record + playoff
                          finish for one real season)
    2. COACH          -- coach_team_seasons (real head coach for one season)
    3. DRAFT          -- draft_facts (a real player this franchise drafted)
    4. AWARD          -- nfl_all_pro_selections / nfl_pro_bowl_selections
                          (a real honoree while playing for this franchise)
    5. PLAYOFFS       -- season_standings.playoff_result, a DIFFERENT real
                          season than stage 1, framed as a playoff-run
                          question rather than a record question
    6. ROSTER         -- canonical_roster_seasons + canonical_players (a
                          real roster member for a real season)
    7. DEEP_CUT       -- reuses curated_nfl_offense_college_board's real
                          SB_CHAMPION data (the ONLY stage that touches
                          Super Bowl content) IF this franchise has a real
                          title; otherwise a second, harder ROSTER pick
                          fills the slot instead of fabricating anything.

Every stage is independently sourced and independently query-verified (see
the exploratory queries run before writing this file) -- this is not one
big roster table wearing 8 different question templates. A franchise that
has never won a Super Bowl still gets a full, real 8-stage marathon; a
dynasty's Super Bowl history appears as exactly ONE stage, not the whole
mode.

--- TEAM IDENTITY RESOLUTION ---
`franchises`/`team_aliases` only carry ONE current team_code per franchise
(2002-2026 coverage, confirmed by direct query) -- useless for a relocated
franchise's pre-move history. `team_seasons` is season-grained and DOES
carry every historical team_code+full_name a franchise has ever used
(confirmed: Raiders show OAK 1999-2019 and LV 2020-2026, Rams show STL/LA)
-- so franchise identity here is resolved the same way
sb_champion_offense_college.py already resolves it for its own franchise_name
filter: a case-insensitive substring match on team_seasons.full_name,
collecting every real team_code that name has ever mapped to. This
correctly reunites a moved franchise's full real history across every
stage, not just the SB one.

--- REAL COVERAGE WINDOWS (disclosed, not hidden) ---
team_seasons/season_standings: 2002-2026. coach_team_seasons/
canonical_roster_seasons: 1999-2026. draft_facts: 1980-2026. nfl_all_pro/
nfl_pro_bowl_selections: 1932-2026 (but team_code only reliably populated in
the modern era -- see _award_candidate's own real, measured season floor).
DEEP_CUT (SB_CHAMPION boards): 1966-2025, the one stage with pre-2002 reach.
A franchise whose whole real history predates 2002 (extremely rare -- every
current NFL franchise has played since at least 2002) would only be
missing IDENTITY/SEASON_RECORD/PLAYOFFS depth for its earliest years, never
a total blackout.
"""
from __future__ import annotations

from collections import Counter

from .. import serializer
from . import _college_offense_curated_common as sb_common

CATEGORY = "Franchise Marathon"
OUT_PATH = None  # Director-pipeline-only
TRACK_ENTITY = True
SUPPORTS_FILTERS = True
REQUIRED_SOURCE_ID = "NFLVERSE_DATA"

_STAGE_ORDER = ("IDENTITY", "SEASON_RECORD", "COACH", "DRAFT", "AWARD", "PLAYOFFS", "ROSTER", "DEEP_CUT")
_STAGE_DIFFICULTY = {
    "IDENTITY": "Easy", "SEASON_RECORD": "Easy", "COACH": "Medium", "DRAFT": "Medium",
    "AWARD": "Medium", "PLAYOFFS": "Medium", "ROSTER": "Hard", "DEEP_CUT": "Hard",
}
_PLAYOFF_RESULT_TEXT = {
    "WonSB": "Won the Super Bowl",
    "LostSB": "Lost the Super Bowl",
    "LostCC": "Lost in the Conference Championship",
    "LostDV": "Lost in the Divisional round",
    "LostWC": "Lost in the Wild Card round",
}
_ALL_PLAYOFF_RESULT_TEXTS = list(_PLAYOFF_RESULT_TEXT.values()) + ["Missed the playoffs"]


def safety_check(c) -> dict:
    src = c.execute("SELECT approved_for_import FROM sources WHERE source_id=?", (REQUIRED_SOURCE_ID,)).fetchone()
    return {"safe": bool(src and src["approved_for_import"])}


def _team_codes_for_franchise(c, franchise_name: str) -> list[dict]:
    """Every real (team_code, full_name, first_season, last_season) this
    franchise nickname has ever mapped to, oldest first -- see module
    docstring for why team_seasons (not franchises/team_aliases) is the
    real source for this."""
    needle = f"%{franchise_name.strip()}%"
    rows = c.execute(
        "SELECT team_code, full_name, MIN(season) AS first_season, MAX(season) AS last_season "
        "FROM team_seasons WHERE full_name LIKE ? COLLATE NOCASE GROUP BY team_code, full_name "
        "ORDER BY first_season",
        (needle,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_ordered_candidates(c, seed: str, filters: dict | None = None):
    from .. import engine

    filters = filters or {}
    # Real capability-health-probe / any generic (no-filter) caller needs
    # SOME real output to prove this capability actually generates -- unlike
    # sb_champion_offense_college.py, where "no filter" sensibly means "all
    # 60 boards" (its unit of content IS one board), Franchise Marathon's
    # unit of content is one franchise's whole 8-stage run, so "no filter"
    # can't mean "every franchise's marathon at once" without changing the
    # mode's shape. Defaults to a fixed, well-covered real franchise
    # (confirmed to reach all 8 stages including deep-cut) rather than
    # returning nothing -- every real public request always supplies
    # franchise_name via caller_filter_key, so this default is only ever
    # exercised by generic/probe-style callers, never a real player.
    franchise_name = filters.get("franchise_name") or "Cowboys"

    identities = _team_codes_for_franchise(c, franchise_name)
    if not identities:
        return []
    team_codes = [i["team_code"] for i in identities]
    current = identities[-1]
    # Deliberately NOT derived from `seed`: get_public_game() re-derives this
    # entire list once per stage_index request, each with a DIFFERENT
    # gen_seed (f"{real_seed}:stage{stage_index}") -- so which real
    # season/player/coach occupies stage N must be a stable function of
    # franchise_name alone, exactly like the pre-existing sb_champion_
    # offense_college.py franchise_name branch (real season sort, no RNG at
    # all). Only evaluate()'s own rng (seeded from f"{seed}:distractors" by
    # game_director_v01, called once per real generation) may vary with the
    # request seed -- that's distractor shuffling only, never which real
    # fact this stage is about.
    rng = engine.seeded(f"franchise_marathon:{franchise_name.lower()}")

    used_seasons: set[int] = set()
    used_players: set = set()
    candidates: list[dict] = []

    builders = {
        "IDENTITY": lambda: _identity_candidate(c, identities, current, rng),
        "SEASON_RECORD": lambda: _season_record_candidate(c, team_codes, rng, used_seasons),
        "COACH": lambda: _coach_candidate(c, team_codes, rng, used_seasons),
        "DRAFT": lambda: _draft_candidate(c, team_codes, rng, used_players),
        "AWARD": lambda: _award_candidate(c, team_codes, rng, used_players),
        "PLAYOFFS": lambda: _playoffs_candidate(c, team_codes, rng, used_seasons),
        "ROSTER": lambda: _roster_candidate(c, team_codes, rng, used_seasons, used_players, hard=False),
    }
    for family in ("IDENTITY", "SEASON_RECORD", "COACH", "DRAFT", "AWARD", "PLAYOFFS", "ROSTER"):
        cand = builders[family]()
        if cand is not None:
            cand["family"] = family
            cand["franchise_display_name"] = current["full_name"]
            candidates.append(cand)
            if cand.get("season") is not None:
                used_seasons.add(cand["season"])
            if cand.get("player_key") is not None:
                used_players.add(cand["player_key"])

    deep_cut = _deep_cut_candidate(c, franchise_name, rng)
    if deep_cut is not None:
        deep_cut["family"] = "DEEP_CUT"
        deep_cut["franchise_display_name"] = current["full_name"]
        candidates.append(deep_cut)
    else:
        # No real title for this franchise -- a second, harder roster pick
        # fills the final-boss slot instead of fabricating a championship,
        # per the module docstring's explicit "never fabricate" rule.
        second_roster = _roster_candidate(c, team_codes, rng, used_seasons, used_players, hard=True)
        if second_roster is not None:
            second_roster["family"] = "ROSTER"
            second_roster["franchise_display_name"] = current["full_name"]
            candidates.append(second_roster)

    return candidates


# --- IDENTITY --------------------------------------------------------------

def _identity_candidate(c, identities: list[dict], current: dict, rng) -> dict | None:
    if len(identities) >= 2:
        former = identities[0]
        if former["full_name"] == current["full_name"]:
            return _division_candidate(c, current, rng)
        other_names = [
            r["full_name"] for r in c.execute(
                "SELECT DISTINCT full_name FROM team_seasons WHERE full_name != ? AND full_name != ?",
                (former["full_name"], current["full_name"]),
            ).fetchall()
        ]
        if len(other_names) < 3:
            return _division_candidate(c, current, rng)
        distractors = rng.sample(other_names, 3)
        return {
            "subtype": "RELOCATION", "correct_text": former["full_name"],
            "current_name": current["full_name"], "distractors": distractors,
            "season": None, "player_key": None,
        }
    return _division_candidate(c, current, rng)


def _division_candidate(c, current: dict, rng) -> dict | None:
    row = c.execute(
        "SELECT conference, division FROM team_seasons WHERE team_code=? ORDER BY season DESC LIMIT 1",
        (current["team_code"],),
    ).fetchone()
    if not row or not row["division"]:
        return None
    correct = row["division"]
    other_divisions = [
        r[0] for r in c.execute("SELECT DISTINCT division FROM team_seasons WHERE division != ?", (correct,)).fetchall()
    ]
    if len(other_divisions) < 3:
        return None
    distractors = rng.sample(other_divisions, 3)
    return {
        "subtype": "DIVISION", "correct_text": correct, "current_name": current["full_name"],
        "distractors": distractors, "season": None, "player_key": None,
    }


def _identity_eval(row, rng, guard):
    correct_text = row["correct_text"]
    if row["subtype"] == "RELOCATION":
        question = (
            f"Before becoming the {row['current_name']}, this real NFL franchise was known as the "
            f"{correct_text}. Which of these is that real former identity?"
        )
        notes = f"The {row['current_name']} were previously the {correct_text} -- a real franchise relocation/rename."
    else:
        question = f"Which real NFL division do the {row['current_name']} currently play in?"
        notes = f"The {row['current_name']} currently play in the {correct_text}."
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:IDENTITY:{row['current_name']}:{row['subtype']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- SEASON_RECORD -----------------------------------------------------------

def _season_record_candidate(c, team_codes, rng, used_seasons: set) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    rows = c.execute(
        f"SELECT season, team_code, wins, losses, ties FROM season_standings "
        f"WHERE team_code IN ({placeholders}) AND wins IS NOT NULL AND losses IS NOT NULL",
        team_codes,
    ).fetchall()
    rows = [r for r in rows if r["season"] not in used_seasons]
    if not rows:
        return None
    row = rows[rng.randrange(len(rows))]
    ties = row["ties"] or 0
    correct = f"{row['wins']}-{row['losses']}" + (f"-{ties}" if ties else "")

    other_rows = c.execute(
        "SELECT wins, losses, ties FROM season_standings WHERE wins IS NOT NULL AND losses IS NOT NULL "
        "AND ABS(season - ?) <= 10 AND team_code NOT IN (%s)" % placeholders,
        [row["season"], *team_codes],
    ).fetchall()
    pool = set()
    for r in other_rows:
        t = r["ties"] or 0
        pool.add(f"{r['wins']}-{r['losses']}" + (f"-{t}" if t else ""))
    pool.discard(correct)
    if len(pool) < 3:
        return None
    distractors = rng.sample(sorted(pool), 3)
    return {
        "subtype": "RECORD", "season": row["season"], "team_code": row["team_code"],
        "correct_text": correct, "distractors": distractors, "player_key": None,
    }


def _season_record_eval(row, rng, guard):
    correct_text = row["correct_text"]
    question = f"What was the {row['franchise_display_name']}' real regular-season record in {row['season']}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:SEASON_RECORD:{row['team_code']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"The {row['franchise_display_name']} went {correct_text} in the real {row['season']} season."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- COACH -------------------------------------------------------------------

def _coach_candidate(c, team_codes, rng, used_seasons: set) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    rows = c.execute(
        f"SELECT season, team_code, coach_name FROM coach_team_seasons WHERE team_code IN ({placeholders})",
        team_codes,
    ).fetchall()
    rows = [r for r in rows if r["season"] not in used_seasons and r["coach_name"]]
    if not rows:
        return None
    row = rows[rng.randrange(len(rows))]
    correct = row["coach_name"]

    other = c.execute(
        "SELECT DISTINCT coach_name FROM coach_team_seasons WHERE coach_name != ? "
        "AND ABS(season - ?) <= 10 AND team_code NOT IN (%s)" % placeholders,
        [correct, row["season"], *team_codes],
    ).fetchall()
    names = [r[0] for r in other if r[0]]
    if len(names) < 3:
        return None
    distractors = rng.sample(names, 3)
    return {
        "subtype": "COACH", "season": row["season"], "team_code": row["team_code"],
        "correct_text": correct, "distractors": distractors, "player_key": None,
    }


def _coach_eval(row, rng, guard):
    correct_text = row["correct_text"]
    question = f"Who was the {row['franchise_display_name']}' real head coach in the {row['season']} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:COACH:{row['team_code']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"{correct_text} was the {row['franchise_display_name']}' real head coach in {row['season']}."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- DRAFT ---------------------------------------------------------------

def _draft_candidate(c, team_codes, rng, used_players: set) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    rows = c.execute(
        f"SELECT player_key, player_name, draft_season, draft_round, draft_pick_overall, position, college "
        f"FROM draft_facts WHERE draft_team IN ({placeholders}) AND player_name IS NOT NULL",
        team_codes,
    ).fetchall()
    rows = [r for r in rows if r["player_key"] not in used_players]
    if not rows:
        return None
    row = rows[rng.randrange(len(rows))]
    correct = row["player_name"]

    other = c.execute(
        "SELECT DISTINCT player_name FROM draft_facts WHERE draft_season=? AND player_name != ? "
        "AND draft_team NOT IN (%s)" % placeholders,
        [row["draft_season"], correct, *team_codes],
    ).fetchall()
    names = [r[0] for r in other if r[0]]
    if len(names) < 3:
        return None
    distractors = rng.sample(names, 3)
    return {
        "subtype": "DRAFT", "season": row["draft_season"], "team_code": None,
        "correct_text": correct, "distractors": distractors, "player_key": row["player_key"],
        "round": row["draft_round"], "pick": row["draft_pick_overall"], "position": row["position"],
        "college": row["college"],
    }


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _draft_eval(row, rng, guard):
    correct_text = row["correct_text"]
    pick_phrase = f"the {_ordinal(row['pick'])} overall pick" if row["pick"] else f"a round {row['round']} pick"
    question = (
        f"The {row['franchise_display_name']} used {pick_phrase} of the real {row['season']} NFL Draft on a "
        f"{row['position']} from {row['college']}. Who was it?"
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:DRAFT:{row['player_key']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"The {row['franchise_display_name']} drafted {correct_text} ({row['position']}, {row['college']}) in {row['season']}."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- AWARD -----------------------------------------------------------------

def _award_candidate(c, team_codes, rng, used_players: set) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    all_pro = c.execute(
        f"SELECT season, player_name_raw AS name, position_raw AS position, player_id "
        f"FROM nfl_all_pro_selections WHERE team_code IN ({placeholders}) AND honor_level='FIRST_TEAM' "
        f"AND season >= 1970",
        team_codes,
    ).fetchall()
    pro_bowl = c.execute(
        f"SELECT season, player_name_raw AS name, position_raw AS position, player_id "
        f"FROM nfl_pro_bowl_selections WHERE team_code IN ({placeholders}) AND season >= 1970",
        team_codes,
    ).fetchall()
    pool = [dict(r, honor="First-Team All-Pro") for r in all_pro] + [dict(r, honor="Pro Bowl") for r in pro_bowl]
    pool = [r for r in pool if r["player_id"] not in used_players and r["name"]]
    if not pool:
        return None
    row = pool[rng.randrange(len(pool))]
    correct = row["name"]

    if row["honor"] == "First-Team All-Pro":
        other = c.execute(
            "SELECT DISTINCT player_name_raw FROM nfl_all_pro_selections WHERE season=? AND honor_level='FIRST_TEAM' "
            "AND player_name_raw != ? AND team_code NOT IN (%s)" % placeholders,
            [row["season"], correct, *team_codes],
        ).fetchall()
    else:
        other = c.execute(
            "SELECT DISTINCT player_name_raw FROM nfl_pro_bowl_selections WHERE season=? "
            "AND player_name_raw != ? AND team_code NOT IN (%s)" % placeholders,
            [row["season"], correct, *team_codes],
        ).fetchall()
    names = [r[0] for r in other if r[0]]
    if len(names) < 3:
        return None
    distractors = rng.sample(names, 3)
    return {
        "subtype": "AWARD", "season": row["season"], "team_code": None,
        "correct_text": correct, "distractors": distractors, "player_key": row["player_id"],
        "honor": row["honor"],
    }


def _award_eval(row, rng, guard):
    correct_text = row["correct_text"]
    question = f"Which of these players earned real {row['honor']} honors on the {row['franchise_display_name']} in {row['season']}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:AWARD:{row['player_key']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"{correct_text} was a real {row['honor']} selection on the {row['franchise_display_name']} in {row['season']}."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- PLAYOFFS ----------------------------------------------------------------

def _playoffs_candidate(c, team_codes, rng, used_seasons: set) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    rows = c.execute(
        f"SELECT season, team_code, playoff_result FROM season_standings WHERE team_code IN ({placeholders})",
        team_codes,
    ).fetchall()
    rows = [r for r in rows if r["season"] not in used_seasons]
    if not rows:
        return None
    row = rows[rng.randrange(len(rows))]
    correct = _PLAYOFF_RESULT_TEXT.get(row["playoff_result"], "Missed the playoffs")
    other_texts = [t for t in _ALL_PLAYOFF_RESULT_TEXTS if t != correct]
    if len(other_texts) < 3:
        return None
    distractors = rng.sample(other_texts, 3)
    return {
        "subtype": "PLAYOFFS", "season": row["season"], "team_code": row["team_code"],
        "correct_text": correct, "distractors": distractors, "player_key": None,
    }


def _playoffs_eval(row, rng, guard):
    correct_text = row["correct_text"]
    question = f"How did the {row['franchise_display_name']}' real playoff run end in the {row['season']} season?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:PLAYOFFS:{row['team_code']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"In {row['season']}, the {row['franchise_display_name']}' real result: {correct_text.lower()}."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- ROSTER ------------------------------------------------------------------

def _roster_candidate(c, team_codes, rng, used_seasons: set, used_players: set, *, hard: bool) -> dict | None:
    placeholders = ",".join("?" for _ in team_codes)
    av_filter = "AND crs.av IS NOT NULL AND crs.av <= 8" if hard else "AND crs.av IS NOT NULL AND crs.av >= 8"
    rows = c.execute(
        f"SELECT crs.season, crs.team_code, crs.position, crs.player_id, cp.display_name AS name "
        f"FROM canonical_roster_seasons crs JOIN canonical_players cp ON cp.player_id = crs.player_id "
        f"WHERE crs.team_code IN ({placeholders}) {av_filter} AND cp.display_name IS NOT NULL",
        team_codes,
    ).fetchall()
    rows = [r for r in rows if r["player_id"] not in used_players]
    if not rows:
        return None
    row = rows[rng.randrange(len(rows))]
    correct = row["name"]

    other = c.execute(
        "SELECT DISTINCT cp.display_name FROM canonical_roster_seasons crs "
        "JOIN canonical_players cp ON cp.player_id = crs.player_id "
        "WHERE crs.season=? AND crs.position=? AND cp.display_name != ? "
        "AND crs.team_code NOT IN (%s)" % placeholders,
        [row["season"], row["position"], correct, *team_codes],
    ).fetchall()
    names = [r[0] for r in other if r[0]]
    if len(names) < 3:
        return None
    distractors = rng.sample(names, 3)
    return {
        "subtype": "ROSTER", "season": row["season"], "team_code": row["team_code"],
        "correct_text": correct, "distractors": distractors, "player_key": row["player_id"],
        "position": row["position"], "hard": hard,
    }


def _roster_eval(row, rng, guard):
    correct_text = row["correct_text"]
    question = f"Which of these players was a real {row['position']} on the {row['franchise_display_name']}' {row['season']} roster?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:ROSTER:{row['player_key']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"{correct_text} ({row['position']}) was really on the {row['franchise_display_name']}' {row['season']} roster."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


# --- DEEP_CUT (the ONLY stage touching Super Bowl content) -------------------

def _deep_cut_candidate(c, franchise_name: str, rng) -> dict | None:
    boards = sb_common.fetch_boards(c, "SB_CHAMPION")
    needle = franchise_name.strip().lower()
    matched = [b for b in boards if needle in b["team_display_name"].lower()]
    if not matched:
        return None
    board = matched[rng.randrange(len(matched))]
    all_seasons = sorted({b["season"] for b in boards} - {board["season"]})
    if len(all_seasons) < 3:
        return None
    distractor_seasons = [str(s) for s in rng.sample(all_seasons, 3)]
    return {
        "subtype": "DEEP_CUT", "season": board["season"], "team_code": board["team_code"],
        "correct_text": str(board["season"]), "distractors": distractor_seasons, "player_key": None,
        "positions": board["positions"], "team_display_name": board["team_display_name"],
    }


def _deep_cut_eval(row, rng, guard):
    correct_text = row["correct_text"]
    positions = row["positions"]
    question = (
        f"Final boss: the {row['franchise_display_name']} won the Super Bowl with a starting offense of "
        f"QB from {positions['QB']}, LT from {positions['LT']}, RB from {positions['RB']}, "
        f"WR1 from {positions['WR1']} (player names hidden). Guess the real season."
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"franchise_marathon:DEEP_CUT:{row['team_display_name']}:{row['season']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_ENTITY"
    options = [correct_text] + row["distractors"]
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"
    notes = f"The {row['team_display_name']} won that Super Bowl in {row['season']} with this real starting offense."
    shuffled, idx = serializer.finalize_options(rng, correct_text, row["distractors"])
    return question, notes, shuffled, idx, entity_key


_EVALUATORS = {
    "IDENTITY": _identity_eval, "SEASON_RECORD": _season_record_eval, "COACH": _coach_eval,
    "DRAFT": _draft_eval, "AWARD": _award_eval, "PLAYOFFS": _playoffs_eval,
    "ROSTER": _roster_eval, "DEEP_CUT": _deep_cut_eval,
}


def evaluate(c, row, rng, guard):
    family = row["family"]
    result = _EVALUATORS[family](row, rng, guard)
    if isinstance(result, str):
        return result
    question, notes, shuffled_options, correct_index, entity_key = result
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["correct_text"]:
        return "INVALID_CORRECT_INDEX"
    diff_label = _STAGE_DIFFICULTY[family]
    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "family": family, "season": row.get("season"), "correct_answer_text": row["correct_text"],
            "difficulty_band": diff_label.upper(), "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED_FROM_NFLVERSE_DATA", "source_id": REQUIRED_SOURCE_ID,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} of this franchise's {considered_count} real marathon stages "
        f"(identity/season-record/coach/draft/award/playoffs/roster/deep-cut) passed every validation "
        f"rule; exported the maximum available ({accepted_count}) rather than fabricate a stage."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_family = Counter(q["_audit"]["family"] for q in exported)
    sb_count = by_family.get("DEEP_CUT", 0)
    return {
        "family_distribution": dict(by_family),
        "super_bowl_share": round(sb_count / len(exported), 3) if exported else 0.0,
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/franchise_marathon.py -- Franchise Marathon (Closeout Part 3 rebuild).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Stage family:** `{a['family']}`",
        f"- **Season:** `{a.get('season')}`",
        f"- **Answer:** \"{record['options'][record['correctIndex']]}\"",
        f"- **Underlying Engine source:** verification_status `{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
