"""Starting-offense-lineup domain adapter -- NFL Starting Lineups by
POSITION + COLLEGE, names hidden.

--- THIS IS THE ORIGINAL v1.8 PROOF-GAME REQUEST, NOW GENUINELY DATA-BACKED ---
`adapters/lineup.py`'s own module docstring explains why THAT capability
ships real player NAMES instead of colleges: at the time it was built, the
only NFL<->CFB identity bridge had 124 rows, nowhere near enough. That has
since changed -- a real, disclosed identity-bridge expansion
(`tools/data_refresh/nfl_college_identity_bridge.py`, using ONLY
already-present Engine data: a completed unique-normalized-name +
NFL-chronology matching pass, plus the pre-existing but previously-unused
`ATTENDED_BEFORE_DRAFT` relationship) grew real, certified NFL-player-to-
college coverage from 2,542 to 7,745+ entries. Measured against this
adapter's own real candidate pool (see `lineup.lineup_college_coverage()`):
68 of 412 real, actually-generatable team-seasons (2006-2018) now have a
certified college for every one of the 5 shown SKILL positions -- well past
the 20-team-season floor this registry treats as "a real, repeatable public
mode" (see `lineup.py`'s `MIN_FULL_LINEUP_COLLEGE_COVERAGE`).

--- WHY THE OFFENSIVE LINE IS NOT SHOWN AT ALL (not grouped, not guessed) ---
Real, measured, and NOT fixable by better matching: per-OL-player certified
college coverage is ~10% (211/2,060 shown OL slots, post-expansion). Needing
all 5 OL players on one team-season to ALL be covered simultaneously is a
combinatorially hard bar that -- honestly measured, not assumed -- zero real
team-seasons clear (0/412, even after the same expansion that got skill
positions to 68/412). This is a real, structural ceiling: offensive linemen
are simply far less documented in CFB participation data than skill-position
players, not a bug in this adapter or the identity bridge. Rather than show
a fabricated or degraded OL row (guessing, silently substituting a name,
or claiming a false college), this capability drops OL from the shown board
entirely and says so plainly in every generated question's own `notes` field
-- the same "expose the truth rather than fabricate precision" discipline
`lineup.py` already applies to its own OL-grouping decision.

--- REUSES lineup.py'S OWN REAL STARTER SELECTION, NOT A REIMPLEMENTATION ---
`fetch_ordered_candidates()` below is `lineup.fetch_ordered_candidates()`
verbatim -- the exact same real, `starts`-based starting-offense selection,
same real seasons, same real teams. This adapter's ONLY new logic is: (a)
requiring a certified college for every skill-position player (rejecting a
candidate outright -- never guessing -- if even one is unresolved), and (b)
hiding names and showing colleges instead in both the question text and the
visual payload.

--- A DISTINCT, SEPARATE CAPABILITY FROM TEAM_OF_STARTING_LINEUP ---
This is NOT a variant/config flag on the existing names-based lineup
capability -- it is its own registered (mechanic, domain, relationship_
predicate) triple (`registry.py`), because the two capabilities have a
genuinely different, non-overlapping candidate pool (68 team-seasons here
vs. 412 there) and a different answer-support contract (a team-season that
fails here because of an unresolved college may still succeed on the
names-based capability, and vice versa is never true since every candidate
here is a subset of that adapter's own pool). Creator routing (translator.py
providers) must never silently substitute one for the other -- see
providers/mock.py and providers/anthropic_provider.py's own "names hidden"
handling.
"""
from __future__ import annotations

from .. import difficulty as difficulty_mod
from .. import engine, serializer
from . import lineup as lineup_adapter
from .draft import resolve_franchise, teams_active_in_season

CATEGORY = "NFL Starting Lineups by College"
OUT_PATH = None  # Director-pipeline-only, like lineup.py
REQUIRED_SOURCES = lineup_adapter.REQUIRED_SOURCES
TRACK_ENTITY = False  # (season, team_code) is already unique by construction, same as lineup.py
MIN_SEASON = lineup_adapter.MIN_SEASON
MAX_SEASON = lineup_adapter.MAX_SEASON
SKILL_SLOTS = ("QB", "RB", "WR", "TE")


def safety_check(c) -> dict:
    return lineup_adapter.safety_check(c)


def fetch_ordered_candidates(c, seed: str):
    """Verbatim reuse of lineup.py's own real starter-selection query --
    see that module's docstring for the full audit trail on why `starts`
    is the honest starter signal and how ties are broken deterministically.
    This adapter only differs in what it does with the result (evaluate()).

    Public-readiness punch-list fix: also warms the certified-college
    lookup cache HERE, exactly once per real generation call (this function
    is called exactly once per run, before the per-candidate evaluate()
    loop below runs once per candidate) -- see
    lineup.refresh_college_lookup_cache()'s own docstring for the full
    root-cause story on why doing this per-candidate inside evaluate() was
    the real cause of the reproduced generation-timeout defect."""
    candidates = lineup_adapter.fetch_ordered_candidates(c, seed)
    lineup_adapter.refresh_college_lookup_cache(c)
    return candidates


def evaluate(c, raw, rng, guard):
    season, team_code, lineup_players = raw
    if not (MIN_SEASON <= season <= MAX_SEASON):
        return "SEASON_OUT_OF_HEURISTIC_RANGE"

    correct, err = resolve_franchise(c, team_code, season)
    if err:
        return err

    bridge = lineup_adapter.certified_college_lookup(c)
    skill_payload = []
    for slot in SKILL_SLOTS:
        for p in lineup_players[slot]:
            college = bridge.get(p["player_id"])
            if college is None:
                # Never guessed, never substituted -- an unresolved college
                # for even one shown player means this candidate is not
                # honestly playable in this shape, full stop.
                return "COLLEGE_UNRESOLVED"
            skill_payload.append({"position": slot, "college": college})

    pool = teams_active_in_season(c, season)
    pool.pop(correct["franchise_id"], None)
    if len(pool) < 3:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_ids = rng.sample(sorted(pool.keys()), 3)
    distractor_names = [pool[fid] for fid in distractor_ids]

    options = [correct["full_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    # Names are hidden entirely (the whole point of this capability) -- the
    # QB's real COLLEGE is what makes the question TEXT unique per (season,
    # team), mirroring lineup.py's own use of the QB's NAME for the exact
    # same structural reason (a bare "its {season} starting offense"
    # collides across every team sharing that season). This adds no new
    # information a player doesn't already see on the board itself.
    qb_college = skill_payload[0]["college"]
    question = (
        f"Guess the NFL team from its {season} starting offense (QB from {qb_college}), "
        f"shown by position and college only -- player names hidden."
    )
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, correct["full_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != correct["full_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / (MAX_SEASON - MIN_SEASON)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    notes = (
        f"The {correct['full_name']}'s {season} starting offense, shown by position and real college "
        f"(names hidden). Offensive line is not shown at all: certified college identity coverage for "
        f"offensive linemen is too sparse (~10% per player) for any real team-season's full offensive "
        f"line to be honestly covered -- see tools/quiz_export/adapters/lineup.lineup_college_coverage()."
    )

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "visual_template": "POSITION_LINEUP_COLLEGE",
        "visual_payload": {"positions": skill_payload, "season": season},
        "_audit": {
            "team_code": team_code, "season": season,
            "franchise_id": correct["franchise_id"], "correct_answer_text": correct["full_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band,
            "lineup_colleges": [p["college"] for p in skill_payload],
            "verification_status": "SOURCE_BACKED", "source_id": REQUIRED_SOURCES[0],
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates have a certified college for every shown skill position, out of "
        f"{considered_count} real (season, team_code) pairs with a qualifying starting offense; exported the "
        f"maximum available ({accepted_count}) rather than guess or substitute an unresolved player's college "
        f"to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    from collections import Counter
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
        "// tools/quiz_export/adapters/lineup_college.py -- NFL Starting Lineups by College (names hidden).",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    colleges = ", ".join(a["lineup_colleges"])
    return [
        f"- **Season/team:** {a['season']}, franchise `{a['franchise_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\"), raw team code `{a['team_code']}`",
        f"- **Starting offense colleges shown (by real games-started, names hidden):** {colleges}",
        f"- **Underlying Engine source:** certified NFL<->CFB identity bridge "
        f"(`cfb_nfl_identity_bridge_certified` + `ATTENDED_BEFORE_DRAFT`) + `canonical_roster_seasons`",
    ]
