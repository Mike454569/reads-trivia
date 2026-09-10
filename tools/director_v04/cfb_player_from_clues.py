"""CFB Player From Clues -- the CFB parity capability for
`tools/director_v04/player_from_clues.py` (Creator Semantic Routing +
Who Am I pass). Same real `identify_player_from_clues` mechanic contract
(progressive, narrowing, server-authoritative clue sequence -- see that
module's own docstring for the shared mechanic-level rules this reuses
verbatim: broadest-still-narrowing-clue-first selection, name-leakage
rejection, independent QA re-verification, duplicate-target/duplicate-
sequence guards), built on real CFB identity tables instead of NFL ones.

Real universe: `cfb_roster_seasons_real` (282,124 rows, 2004-2025,
verification_status='SOURCE_BACKED', source_id='SPORTSDATAVERSE_CFB') joined
to `canonical_cfb_players` on `cfb_player_id` -- the SAME real, per-season-
verified identity foundation `cfb_player_season_school.py`'s own module
docstring already establishes (zero unjoined rows, confirmed there). Never
joined on name -- `cfb_player_id` is the identity key throughout; every
real, dramatic same-name-collision case that adapter's docstring documents
(five distinct real "Caleb Williams" players active in 2023 alone) applies
equally here and is avoided the same way, by construction.

Clue types, each backed by a real, disclosed source:
  school               -- the one real school this player's roster rows most
                           commonly name (cfb_roster_seasons_real.school_id
                           -> schools.school_name). Always shown first when
                           real (see FORCED_OPENING_CLUE_TYPES/build_puzzle()
                           -- a basic identifying fact every fan expects,
                           not left to compete on narrowing power alone).
  position             -- the position from this player's most recent real
                           roster row with a non-null position. Always shown
                           second when real, same forced-opening reasoning.
  career_span          -- MIN/MAX(season) across this player's real roster
                           rows.
  all_america          -- True if certified in cfb_all_america_certified
                           (real, cfb_player_id-keyed) -- a real, rare,
                           strongly-narrowing honor. See DIFFICULTY_BANDS's
                           own is_consensus split for why "certified" alone
                           is no longer treated as automatically Easy.
  transfer_school_count -- this player's real school_count from
                           cfb_transfer_summary_v17 (cfb_player_id-keyed,
                           covers the full roster universe, not just
                           multi-school players -- school_count=1 is a real,
                           valid value too).
  stat_highlight       -- this player's single most notable real college
                           season in whichever stat category they clear
                           STAT_THRESHOLDS by the largest real margin
                           (cfb_player_season_stats_real, 2014-2025
                           coverage only) -- see _attach_stat_highlights().

Does not build a `college` clue (that word means something different here
than it does for the NFL module -- there is no cross-league bridge to name)
and does not use Heisman as a clue type: cfb_award_facts' Heisman winners
are matched to a school via WIKIPEDIA_STRUCTURED text, not to a
canonical_cfb_players cfb_player_id, so there is no safe, direct join to
this module's identity key without a separate, unverified name-matching
step -- exactly the kind of "join on name" this module (and the whole
Engine) does not do.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import duplicates, engine, safety  # noqa: E402

PACKAGE_SCHEMA_VERSION = "0.4"
MECHANIC = "identify_player_from_clues"
CATEGORY = "CFB Player From Clues"
ID_START = 890000
MIN_CLUES = 3
MAX_CLUES = 5
MIN_SEASON = 2004
MAX_SEASON = 2025
REQUIRED_SOURCE_ID = "SPORTSDATAVERSE_CFB"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED"

STAT_CLUE_LABELS = {
    "passing_yards": lambda v: f"This player passed for {v:,} yards in a single college season.",
    "rushing_yards": lambda v: f"This player rushed for {v:,} yards in a single college season.",
    "receiving_yards": lambda v: f"This player caught passes for {v:,} yards in a single college season.",
    "defensive_interceptions": lambda v: f"This player recorded {v} interception{'s' if v != 1 else ''} in a single college season.",
    "sacks": lambda v: f"This player recorded {v:g} sack{'s' if v != 1 else ''} in a single college season.",
    "field_goals_made": lambda v: f"This player made {v} field goals in a single college season.",
}

CLUE_TEMPLATES = {
    "school": lambda v: f"This player played college football for {v}.",
    "position": lambda v: f"This player's college position was {v}.",
    "career_span": lambda v: f"This player's college career (by recorded roster seasons) spanned {v[0]} to {v[1]}.",
    "all_america": lambda v: "This player was a certified College Football All-American.",
    "transfer_school_count": lambda v: (
        f"This player played for {v} different real school{'s' if v != 1 else ''} across his college career."
    ),
    # Player Experience pass (user request: "add stats into the clues if we
    # can"): `v` is a (stat_column, value) pair -- see _attach_stat_highlights()
    # for how a player's single most notable real season is chosen among the
    # categories that clear STAT_THRESHOLDS.
    "stat_highlight": lambda v: STAT_CLUE_LABELS[v[0]](v[1]),
}

CLUE_SOURCE_META = {
    "school": {"table": "cfb_roster_seasons_real+schools", "field": "school_id (most seasons)", "source_id": REQUIRED_SOURCE_ID, "verification_status": REQUIRED_VERIFICATION_STATUS},
    "position": {"table": "cfb_roster_seasons_real", "field": "position (most recent real row)", "source_id": REQUIRED_SOURCE_ID, "verification_status": REQUIRED_VERIFICATION_STATUS},
    "career_span": {"table": "cfb_roster_seasons_real", "field": "MIN/MAX(season)", "source_id": REQUIRED_SOURCE_ID, "verification_status": REQUIRED_VERIFICATION_STATUS},
    # cfb_all_america_certified/cfb_transfer_summary_v17 are both derived,
    # identity-resolved tables (joined on cfb_player_id, never on name) with
    # no per-row source_id/verification_status column of their own -- unlike
    # the NFLVERSE-sourced tables above, confirmed directly against their
    # real schema before writing this (same real distinction
    # cfb_all_america_facts.py's own module docstring already makes: "the
    # identity-resolved layer, never the raw table directly"). Their real
    # provenance signal is resolution_method + confidence (0.85-0.98 for
    # All-America) and derivation from cfb_roster_seasons_real (for the
    # transfer summary) respectively -- described honestly here rather than
    # inventing a source_id/verification_status value neither table has.
    "all_america": {"table": "cfb_all_america_certified", "field": "cfb_player_id membership (resolution_method + confidence 0.85-0.98)", "source_id": None, "verification_status": "IDENTITY_RESOLVED_CERTIFIED"},
    "transfer_school_count": {"table": "cfb_transfer_summary_v17", "field": "school_count (derived from cfb_roster_seasons_real)", "source_id": None, "verification_status": "DERIVED_FROM_SOURCE_BACKED_ROSTER"},
    # cfb_player_season_stats_real carries a real, uniform verification_status/
    # source_id of its own (confirmed directly: 100% SOURCE_BACKED_DERIVED /
    # SPORTSDATAVERSE_CFB), unlike the two derived tables above.
    "stat_highlight": {"table": "cfb_player_season_stats_real", "field": "single-season stat value (best qualifying category)", "source_id": "SPORTSDATAVERSE_CFB", "verification_status": "SOURCE_BACKED_DERIVED"},
}

QA_CHECKS_PERFORMED = [
    "target player resolved through the real cfb_roster_seasons_real/canonical_cfb_players universe, joined "
    "on cfb_player_id only, never on name",
    "every clue value independently re-derived from its index and re-checked to contain the target cfb_player_id",
    "every clue's source/verification_status checked against the constant per-type provenance table",
    "name-leakage check: no clue's display_text contains the target's display_name (case-insensitive substring)",
    "no duplicate clue_type within one puzzle",
    "candidate-narrowing chain independently recomputed and checked for monotonic non-increase and contiguity",
    "clue[0].candidates_before == full universe size",
    "final candidate set independently recomputed and checked to equal exactly {target_player_id}",
    "clue count within [3, 5]",
    "duplicate-puzzle-target guard (no player targeted twice in one export)",
    "duplicate-clue-sequence guard (no two puzzles share an identical ordered (clue_type, value) sequence)",
    "production safety: cfb_roster_seasons_real/canonical_cfb_players/cfb_all_america_certified/"
    "cfb_transfer_summary_v17 table-wide or verification_status checks, all independently verified before generation",
]


def safety_check(c) -> dict:
    # MASTER WORKBOOK ingestion pass: cfb_roster_seasons_real/
    # canonical_cfb_players gained a second, independently-approved
    # provenance (READS_MASTER_KNOWLEDGE_FEED_2026_09, real 2026 roster
    # rows the automated SPORTSDATAVERSE_CFB feed has never had) -- the
    # exhaustive table-wide check must allow-list BOTH real sources rather
    # than abort on the table no longer being single-provenance. This
    # adapter's own build_universe() query below still filters to
    # REQUIRED_SOURCE_ID alone, so its actual real candidate pool/behavior
    # is unchanged -- this only stops a false ABORT.
    return {
        "cfb_roster_seasons_real": safety.check_table_wide_safety(
            c, "cfb_roster_seasons_real", [REQUIRED_SOURCE_ID, "READS_MASTER_KNOWLEDGE_FEED_2026_09"],
        ),
        "canonical_cfb_players": safety.check_table_wide_safety(
            c, "canonical_cfb_players", [REQUIRED_SOURCE_ID, "READS_MASTER_KNOWLEDGE_FEED_2026_09"],
        ),
    }


def build_universe(c):
    """Same real shape as player_from_clues.py's own build_universe(): pure
    function of Engine data, no randomness. Returns (facts, indexes,
    universe_ids)."""
    roster_rows = c.execute(
        "SELECT season, school_id, cfb_player_id, position FROM cfb_roster_seasons_real "
        "WHERE verification_status=? AND source_id=? AND season BETWEEN ? AND ?",
        (REQUIRED_VERIFICATION_STATUS, REQUIRED_SOURCE_ID, MIN_SEASON, MAX_SEASON),
    ).fetchall()

    by_player: dict = {}
    for r in roster_rows:
        by_player.setdefault(r["cfb_player_id"], []).append((r["season"], r["school_id"], r["position"]))

    name_rows = c.execute(
        "SELECT cfb_player_id, display_name FROM canonical_cfb_players "
        f"WHERE cfb_player_id IN ({','.join('?' * len(by_player))})",
        tuple(by_player.keys()),
    ).fetchall() if by_player else []
    display_names = {r["cfb_player_id"]: r["display_name"] for r in name_rows}

    school_names = {r["school_id"]: r["school_name"] for r in c.execute("SELECT school_id, school_name FROM schools")}

    facts: dict = {}
    for pid, rows in by_player.items():
        display_name = display_names.get(pid)
        if not display_name:
            continue  # no resolved identity row -- excluded, never guessed at
        rows_sorted = sorted(rows, key=lambda x: x[0])
        seasons = [r[0] for r in rows_sorted]

        school_counts = Counter(r[1] for r in rows_sorted if r[1])
        primary_school_id = None
        if school_counts:
            max_count = max(school_counts.values())
            primary_school_id = sorted(sid for sid, cnt in school_counts.items() if cnt == max_count)[0]
        primary_school = school_names.get(primary_school_id) if primary_school_id else None

        # 'NA'/'?' are real but non-positions -- source placeholder values
        # (1,161 and 2,155 real rows respectively, confirmed by direct
        # query), not an actual football position a clue could honestly
        # name. Skipped exactly like a NULL position, never surfaced as
        # "this player's position was NA."
        latest_position = None
        for season, _sid, pos in reversed(rows_sorted):
            if pos and pos not in ("NA", "?"):
                latest_position = pos
                break

        facts[pid] = {
            "player_id": pid, "display_name": display_name,
            "school": primary_school,
            "position": latest_position,
            "career_span": (seasons[0], seasons[-1]) if seasons else None,
            "n_real_seasons": len(set(seasons)),
        }

    # Same real fix as player_from_clues.py's own build_universe() (found
    # during production validation): a single real recorded season
    # produces a degenerate "spanned 2019 to 2019" career_span clue, and
    # correlates with genuinely obscure one-year-blip roster appearances
    # (35% of this real universe -- 38,254 of 109,221 -- have exactly one
    # real season). Scoped to 3+ real distinct seasons here rather than
    # NFL's 5+ -- real college eligibility rarely exceeds 4-5 years, so a
    # proportionally lower bar. 50,632 real candidates remain, far more
    # than this capability's own max_question_count ever needs.
    MIN_REAL_SEASONS = 3
    facts = {pid: f for pid, f in facts.items() if f["n_real_seasons"] >= MIN_REAL_SEASONS}

    universe_ids = frozenset(facts.keys())

    if universe_ids:
        placeholders = ",".join("?" * len(universe_ids))
        # Player Experience pass: is_consensus tracked separately from plain
        # AA certification -- see _attach_difficulty_bands()'s own comment
        # for why "Easy" now requires the real consensus tier, not any
        # certified AA honor (many certified honors are single-selector/
        # non-consensus recognitions a casual fan would not know).
        aa_rows = c.execute(
            f"SELECT cfb_player_id, MAX(is_consensus) AS any_consensus FROM cfb_all_america_certified "
            f"WHERE cfb_player_id IN ({placeholders}) GROUP BY cfb_player_id",
            tuple(universe_ids),
        ).fetchall()
        for r in aa_rows:
            facts[r["cfb_player_id"]]["all_america"] = True
            facts[r["cfb_player_id"]]["all_america_consensus"] = bool(r["any_consensus"])

        transfer_rows = c.execute(
            f"SELECT cfb_player_id, school_count FROM cfb_transfer_summary_v17 WHERE cfb_player_id IN ({placeholders})",
            tuple(universe_ids),
        ).fetchall()
        for r in transfer_rows:
            facts[r["cfb_player_id"]]["transfer_school_count"] = r["school_count"]

    _attach_difficulty_bands(c, facts, universe_ids)
    _attach_stat_highlights(c, facts, universe_ids)

    indexes: dict = {ct: {} for ct in CLUE_TEMPLATES}
    for pid, f in facts.items():
        for ct in ("school", "position"):
            v = f.get(ct)
            if v is not None:
                indexes[ct].setdefault(v, set()).add(pid)
        cs = f.get("career_span")
        if cs is not None:
            indexes["career_span"].setdefault(cs, set()).add(pid)
        if f.get("all_america"):
            indexes["all_america"].setdefault(True, set()).add(pid)
        tsc = f.get("transfer_school_count")
        if tsc is not None:
            indexes["transfer_school_count"].setdefault(tsc, set()).add(pid)
        sh = f.get("stat_highlight")
        if sh is not None:
            indexes["stat_highlight"].setdefault(sh, set()).add(pid)

    return facts, indexes, universe_ids



# Player Experience pass, real fix: this capability's only eligibility bar
# was "3+ real recorded roster seasons" -- no requirement of ever having
# been a real, meaningful on-field contributor, so the ~50,632-player
# universe is overwhelmingly walk-ons, backups, and deep-bench players a
# normal CFB fan would never recognize. Confirmed directly against the
# shipped 3,300-puzzle pack before this fix: 2,843/3,300 (86%) landed in
# "Hard" purely because the only prior difficulty signals (All-America,
# NFL draft) are each real but rare (939 / a few thousand players
# respectively) -- "Hard" was really "everyone else," not "a real
# recognizable player who's just tough to place."
#
# Real, non-fabricated "was a real contributor" signal added here:
# cfb_player_season_stats_real (2014-2025 coverage only -- a real,
# disclosed gap for 2004-2013 players, who fall back to the All-America/
# draft signal alone). STAT_THRESHOLDS are round, defensible single-
# season starter-level marks (a real season passing/rushing/receiving
# leader-caliber year, or a real meaningful defensive/kicking season) --
# 5,600 real distinct players clear at least one of them, out of 39,817
# total players with any stat row at all (measured directly).
STAT_THRESHOLDS = {
    "passing_yards": 1500, "rushing_yards": 600, "receiving_yards": 600,
    "defensive_interceptions": 3, "sacks": 5, "field_goals_made": 10,
}
DIFFICULTY_BANDS = ("Easy", "Medium", "Hard", "Sicko")


def _attach_difficulty_bands(c, facts: dict, universe_ids: frozenset) -> None:
    """Stamps facts[pid]['difficulty_band'] for every real player in the
    universe -- Easy/Medium/Hard together are this mode's real "a normal
    CFB fan could plausibly know this player" pool; Sicko is the real,
    explicit deep-cut tier (no recognizability signal found at all),
    never silently mixed into the other three. See module comment above
    for the real signals and thresholds used."""
    if not universe_ids:
        return
    placeholders = ",".join("?" * len(universe_ids))

    bridge: dict[str, int | None] = {}
    for row in c.execute(
        f"""
        SELECT b.cfb_player_id, d.draft_round
        FROM cfb_nfl_identity_bridge_certified b
        LEFT JOIN draft_facts d ON b.nfl_player_key = d.player_key
        WHERE b.cfb_player_id IN ({placeholders})
        """,
        tuple(universe_ids),
    ).fetchall():
        pid, draft_round = row["cfb_player_id"], row["draft_round"]
        # A player can have multiple bridge/draft rows (rare data overlap);
        # keep the best (lowest) real draft round seen for this player.
        if pid not in bridge or (draft_round is not None and (bridge[pid] is None or draft_round < bridge[pid])):
            bridge[pid] = draft_round

    stat_conditions = " OR ".join(f"{col} >= {threshold}" for col, threshold in STAT_THRESHOLDS.items())
    notable_stat_ids = {
        row["cfb_player_id"] for row in c.execute(
            f"SELECT DISTINCT cfb_player_id FROM cfb_player_season_stats_real "
            f"WHERE cfb_player_id IN ({placeholders}) AND ({stat_conditions})",
            tuple(universe_ids),
        ).fetchall()
    }

    for pid, f in facts.items():
        # Player Experience pass, real fix: "Easy" originally meant "any
        # certified All-America honor OR round 1-2 NFL draft pick" -- but
        # only 299/916 real 2004+ certified AA honorees are CONSENSUS (the
        # real "essentially every major selector agreed" tier; the other
        # 617 are single-selector/lower-profile honors a casual fan is far
        # less likely to know), and a round-2 pick is a real NFL player but
        # not the same recognizability tier as a round-1 pick. Tightened to
        # consensus AA OR round-1 specifically -- non-consensus AA and
        # round-2/3 picks now land in the real "still notable, one tier
        # down" Medium band instead.
        if f.get("all_america_consensus") or (pid in bridge and bridge[pid] == 1):
            f["difficulty_band"] = "Easy"
        elif f.get("all_america") or pid in bridge:
            f["difficulty_band"] = "Medium"
        elif pid in notable_stat_ids:
            f["difficulty_band"] = "Hard"
        else:
            f["difficulty_band"] = "Sicko"


def _attach_stat_highlights(c, facts: dict, universe_ids: frozenset) -> None:
    """Stamps facts[pid]['stat_highlight'] = (stat_column, value) for every
    real player with at least one real single-season stat clearing
    STAT_THRESHOLDS -- the same real notability signal _attach_difficulty_bands()
    uses, now surfaced as an actual clue (user request: "add stats into the
    clues if we can") rather than only a hidden banding input. When a
    player clears more than one category, picks whichever they clear by
    the largest real MARGIN over its threshold (their most standout real
    category), not an arbitrary fixed priority order."""
    if not universe_ids:
        return
    placeholders = ",".join("?" * len(universe_ids))
    cols = ", ".join(f"MAX({col}) AS {col}" for col in STAT_THRESHOLDS)
    rows = c.execute(
        f"SELECT cfb_player_id, {cols} FROM cfb_player_season_stats_real "
        f"WHERE cfb_player_id IN ({placeholders}) GROUP BY cfb_player_id",
        tuple(universe_ids),
    ).fetchall()
    for row in rows:
        best_col, best_value, best_margin = None, None, 0.0
        for col, threshold in STAT_THRESHOLDS.items():
            v = row[col]
            if v is None or v < threshold:
                continue
            margin = v / threshold
            if margin > best_margin:
                best_col, best_value, best_margin = col, v, margin
        if best_col is not None:
            facts[row["cfb_player_id"]]["stat_highlight"] = (best_col, best_value)


def _candidate_clues_for_player(pid: str, facts: dict, indexes: dict) -> list:
    f = facts[pid]
    out = []
    for ct, value_index in indexes.items():
        v = f.get(ct)
        if ct == "all_america":
            if not v:
                continue
            v = True
        if v is None:
            continue
        cset = value_index.get(v)
        if not cset or pid not in cset:
            continue  # defensive -- should be unreachable given how indexes are built
        out.append((ct, v, cset))
    return out


# Product Growth + Real User Testing pass: same real repetition defect
# found in player_from_clues.py's own build_puzzle() (see that module's
# OPENING_CLUE_VARIETY_EXCLUDE docstring) -- transfer_school_count is a
# near-binary (1 vs 2 real schools) split across most of the real player
# universe, so it dominated as the OPENING clue for the large majority of
# a real local sample. Same fix: excluded from the opening slot only,
# with a safe fallback to allow it there if it's genuinely the only real
# clue this player has.
OPENING_CLUE_VARIETY_EXCLUDE = frozenset({"transfer_school_count"})


# Player Experience pass (user request: "always include the team they
# played for and position"): forced ahead of the greedy narrowing loop
# below, in this order, rather than left to compete on narrowing power --
# school/position are real basic identifying facts every CFB fan expects
# up front, even though they're rarely the MOST narrowing clue available
# (a school/position combo is shared by many real players). Only forced
# when the clue actually narrows the running candidate set at all (the
# same real monotonic-decrease requirement validate_puzzle_qa() enforces
# for every clue) -- skipped, never fabricated, on the rare real player
# missing one of these two facts entirely.
FORCED_OPENING_CLUE_TYPES = ("school", "position")


def _force_clue(ct: str, pool: list, running: frozenset, f: dict) -> tuple[dict | None, frozenset]:
    match = next((o for o in pool if o[0] == ct), None)
    if match is None:
        return None, running
    _ct, v, cset = match
    new_set = running & cset
    if len(new_set) >= len(running):
        return None, running  # would not narrow -- never included as a no-op clue
    display_text = CLUE_TEMPLATES[ct](v)
    if f["display_name"] and f["display_name"].lower() in display_text.lower():
        return None, running
    return {"clue_type": ct, "value": v, "display_text": display_text, "source": CLUE_SOURCE_META[ct],
            "candidates_before": len(running), "candidates_after": len(new_set)}, new_set


def build_puzzle(pid: str, facts: dict, indexes: dict, universe_ids: frozenset):
    """Same real narrowing algorithm as player_from_clues.py's own
    build_puzzle() -- see that module's docstring for the rationale
    (broadest-still-narrowing clue first, deterministic tie-break, no RNG,
    name-leakage rejection). FORCED_OPENING_CLUE_TYPES above are attempted
    first, unconditionally; the remaining MAX_CLUES budget still runs the
    original greedy-narrowing selection over every other real clue type."""
    f = facts[pid]
    running = universe_ids
    pool = _candidate_clues_for_player(pid, facts, indexes)
    selected: list = []
    used_types: set = set()

    for ct in FORCED_OPENING_CLUE_TYPES:
        if len(selected) >= MAX_CLUES or len(running) == 1:
            break
        clue, new_running = _force_clue(ct, pool, running, f)
        if clue is None:
            continue
        clue["clue_index"] = len(selected)
        selected.append(clue)
        used_types.add(ct)
        running = new_running

    while len(selected) < MAX_CLUES:
        step_options = []
        for ct, v, cset in pool:
            if ct in used_types:
                continue
            new_set = running & cset
            if len(new_set) < len(running):
                step_options.append((ct, v, cset, new_set))
        if not step_options:
            break
        if len(selected) == 0:
            varied = [o for o in step_options if o[0] not in OPENING_CLUE_VARIETY_EXCLUDE]
            if varied:
                step_options = varied
        step_options.sort(key=lambda x: (-len(x[3]), x[0]))
        ct, v, _cset, new_set = step_options[0]
        display_text = CLUE_TEMPLATES[ct](v)
        if f["display_name"] and f["display_name"].lower() in display_text.lower():
            pool = [c for c in pool if c[0] != ct]
            continue
        selected.append({
            "clue_index": len(selected), "clue_type": ct, "value": v, "display_text": display_text,
            "source": CLUE_SOURCE_META[ct],
            "candidates_before": len(running), "candidates_after": len(new_set),
        })
        used_types.add(ct)
        running = new_set
        if len(running) == 1:
            break

    if len(selected) < MIN_CLUES:
        return None, "INSUFFICIENT_NARROWING_CLUES"
    if len(running) != 1:
        return None, f"AMBIGUOUS_FINAL_SET_SIZE_{len(running)}"
    if next(iter(running)) != pid:
        return None, "UNIQUENESS_MISMATCH"

    puzzle = {
        "answer": {"answer_type": "player", "player_id": pid, "display_name": f["display_name"]},
        "clues": selected,
        "final_candidate_count": len(running),
    }
    return puzzle, None


def validate_puzzle_qa(puzzle: dict, universe_ids: frozenset, indexes: dict) -> list:
    """Same independent re-verification pass as player_from_clues.py's own
    validate_puzzle_qa() -- does not trust build_puzzle()'s own bookkeeping."""
    issues = []
    target = puzzle["answer"]["player_id"]
    if target not in universe_ids:
        issues.append("TARGET_NOT_IN_UNIVERSE")
        return issues

    clues = puzzle["clues"]
    if not (MIN_CLUES <= len(clues) <= MAX_CLUES):
        issues.append(f"CLUE_COUNT_OUT_OF_BOUNDS_{len(clues)}")

    seen_types = set()
    running = universe_ids
    for i, clue in enumerate(clues):
        ct, v = clue["clue_type"], clue["value"]
        if ct in seen_types:
            issues.append(f"DUPLICATE_CLUE_TYPE_{ct}")
        seen_types.add(ct)

        expected_source = CLUE_SOURCE_META.get(ct)
        if expected_source != clue.get("source"):
            issues.append(f"SOURCE_METADATA_MISMATCH_{ct}")

        display_name = puzzle["answer"]["display_name"]
        if display_name and display_name.lower() in clue["display_text"].lower():
            issues.append(f"NAME_LEAKAGE_{ct}")

        cset = indexes.get(ct, {}).get(v)
        if not cset or target not in cset:
            issues.append(f"CLUE_NOT_TRUE_FOR_TARGET_{ct}")
            continue

        if clue["candidates_before"] != len(running):
            issues.append(f"NON_CONTIGUOUS_CHAIN_AT_{i}")
        new_running = running & cset
        if len(new_running) != clue["candidates_after"]:
            issues.append(f"CANDIDATES_AFTER_MISMATCH_AT_{i}")
        if len(new_running) > len(running):
            issues.append(f"NON_MONOTONIC_NARROWING_AT_{i}")
        running = new_running

    if clues and clues[0]["candidates_before"] != len(universe_ids):
        issues.append("FIRST_CLUE_DOES_NOT_START_FROM_FULL_UNIVERSE")

    if len(running) != 1 or (running and next(iter(running)) != target):
        issues.append("FINAL_SET_NOT_UNIQUE_TARGET")

    return issues


# Player Experience pass: generation is now stratified by exact band
# (rather than one shuffled "notable" draw across Easy+Medium+Hard
# together) so a real, sufficient number of genuinely Easy puzzles can be
# guaranteed -- Easy is real but the smallest of the 3 recognizable bands
# (593 real players universe-wide vs. 6,074 Medium / 3,003 Hard), and a
# single unstratified draw would under-represent it by construction (a
# uniform random sample would only pull ~6% Easy, matching what was
# actually measured before this fix).
POOL_TO_BANDS = {
    "Easy": frozenset({"Easy"}), "Medium": frozenset({"Medium"}), "Hard": frozenset({"Hard"}),
    "Sicko": frozenset({"Sicko"}), "notable": frozenset({"Easy", "Medium", "Hard"}),
}


def generate_pack(seed: str, target_count: int = 25, id_start: int = ID_START, pool: str = "notable") -> dict:
    """`pool`: one of POOL_TO_BANDS's keys. "Easy"/"Medium"/"Hard" each
    draw puzzle TARGETS only from that exact real difficulty band (see
    _attach_difficulty_bands) -- this is the real fix for "use players
    that casual and normal cfb fans would know," now with real control
    over each band's own real representation. "notable" draws from all
    three combined (Easy+Medium+Hard mixed by shuffle order) for a caller
    that doesn't need per-band stratification. "Sicko" draws targets only
    from the real complement (no recognizability signal found at all) --
    an explicit, opt-in deep-cut tier, never silently mixed into any of
    the other four. Either way, clue narrowing/uniqueness math still runs
    against the FULL real universe (universe_ids unrestricted) -- only
    which players are eligible to be a puzzle's ANSWER changes."""
    if pool not in POOL_TO_BANDS:
        raise ValueError(f"pool must be one of {sorted(POOL_TO_BANDS)}, got {pool!r}")
    c = engine.connect()
    safety_result = safety_check(c)
    facts, indexes, universe_ids = build_universe(c)
    c.close()

    bands = POOL_TO_BANDS[pool]
    target_pids = {pid for pid in universe_ids if facts[pid]["difficulty_band"] in bands}

    order = sorted(target_pids)
    rng = engine.seeded(seed)
    rng.shuffle(order)

    rejected_counts: Counter = Counter()
    accepted: list = []
    guard = duplicates.DuplicateGuard(track_entity=True)
    qa_failed: list = []
    # Real, measured performance guard, same discipline
    # cfb_player_season_school.py's own max_fetched_candidates uses (that
    # capability's own docstring: a real, measured 116s full-pool call
    # before its cap): a full unbounded scan of this 109,221-player universe
    # was directly timed at 3+ minutes -- the per-player candidate-narrowing
    # work here is real set-intersection work against index buckets that can
    # be large (e.g. a big program's "school" bucket), not free. Stops once
    # comfortably past what any real target_count needs; `scanned_count`
    # (not the full universe size) is what funnel["attempted"] reports below,
    # so this cap is never misreported as "the whole universe was checked."
    # Absolute ceiling, not just a target_count multiple -- a caller that
    # requests a very large target_count (e.g. health_probe.py's real
    # Tier-2 certification, which deliberately requests up to 1,000,000 to
    # then cycle through the real accepted set with wraparound -- see that
    # module's own docstring) must not turn this into the same 3+ minute
    # unbounded scan this cap exists to prevent.
    scan_cap = min(max(target_count * 20, 2000), 20000)
    scanned_count = 0

    for pid in order:
        scanned_count += 1
        puzzle, reason = build_puzzle(pid, facts, indexes, universe_ids)
        if puzzle is None:
            rejected_counts[reason] += 1
        elif guard.entity_seen(pid):
            rejected_counts["DUPLICATE_PUZZLE_TARGET"] += 1
        else:
            sequence_signature = "|".join(f"{cl['clue_type']}={cl['value']}" for cl in puzzle["clues"])
            if guard.question_seen(sequence_signature):
                rejected_counts["DUPLICATE_CLUE_SEQUENCE"] += 1
            else:
                issues = validate_puzzle_qa(puzzle, universe_ids, indexes)
                if issues:
                    qa_failed.append({"player_id": pid, "issues": issues})
                    rejected_counts["QA_FAILED"] += 1
                else:
                    puzzle["puzzle_id"] = id_start + len(accepted)
                    puzzle["mechanic"] = MECHANIC
                    puzzle["qa_status"] = "PASSED"
                    puzzle["difficulty_band"] = facts[pid]["difficulty_band"]
                    accepted.append(puzzle)
                    guard.record(sequence_signature, pid)

        if len(accepted) >= target_count or scanned_count >= scan_cap:
            break

    exported = accepted[:target_count]
    shortfall_reason = None
    if len(exported) < target_count:
        shortfall_reason = (
            f"Only {len(accepted)} of {len(target_pids)} real CFB roster players in the {pool!r} pool "
            f"produced a puzzle passing every rule, out of {scanned_count} scanned (in this seeded "
            f"order, up to a real performance cap); exported the maximum available ({len(accepted)}) "
            f"rather than loosen the minimum-clue-count or uniqueness requirements to reach {target_count}."
        )

    clue_type_counts: Counter = Counter()
    clue_counts_per_puzzle: list = []
    for p in exported:
        clue_counts_per_puzzle.append(len(p["clues"]))
        for cl in p["clues"]:
            clue_type_counts[cl["clue_type"]] += 1

    funnel = {
        "pool": pool,
        "pool_size": len(target_pids),
        "universe_size": len(universe_ids),
        "attempted": scanned_count,
        "rejected_counts": dict(rejected_counts),
        "accepted_total": len(accepted),
        "exported_count": len(exported),
        "target_count": target_count,
        "shortfall_reason": shortfall_reason,
        "qa_failures_detail": qa_failed,
        "clue_type_distribution": dict(clue_type_counts),
        "average_clue_count": (sum(clue_counts_per_puzzle) / len(clue_counts_per_puzzle)) if clue_counts_per_puzzle else None,
    }

    return {
        "mechanic": MECHANIC, "category": CATEGORY, "safety": safety_result,
        "puzzles": exported, "funnel": funnel,
        "qa_checks_performed": QA_CHECKS_PERFORMED, "seed": seed,
    }


def _engine_version_fingerprint(c) -> dict:
    database_version = c.execute("SELECT value FROM meta WHERE key = 'database_version'").fetchone()
    return {
        "database_version": database_version[0] if database_version else None,
        "cfb_roster_seasons_real_row_count": c.execute("SELECT COUNT(*) FROM cfb_roster_seasons_real").fetchone()[0],
        "canonical_cfb_players_row_count": c.execute("SELECT COUNT(*) FROM canonical_cfb_players").fetchone()[0],
        "cfb_all_america_certified_row_count": c.execute("SELECT COUNT(*) FROM cfb_all_america_certified").fetchone()[0],
        "cfb_transfer_summary_v17_row_count": c.execute("SELECT COUNT(*) FROM cfb_transfer_summary_v17").fetchone()[0],
    }


def build_package(seed: str, target_count: int = 25, id_start: int = ID_START, pool: str = "notable",
                   requested_description: str | None = None, freeze_timestamp: str | None = None) -> dict:
    pack = generate_pack(seed, target_count=target_count, id_start=id_start, pool=pool)

    c = engine.connect()
    engine_version_fingerprint = _engine_version_fingerprint(c)
    c.close()

    description = requested_description or (
        "Identify the college football player from a progressive sequence of source-backed clues."
    )
    package_id = "GGP4:" + hashlib.sha256(
        f"{description}|{seed}|{MECHANIC}|CFB|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]

    return {
        "package_id": package_id,
        "package_version": PACKAGE_SCHEMA_VERSION,
        "mechanic": MECHANIC,
        "requested_description": description,
        "game_title": "CFB Player From Clues",
        "game_instructions": (
            "You'll see a sequence of verified clues about one college football player, revealed one at a "
            "time and narrowing from broad to specific. Identify the player."
        ),
        "generated_at": freeze_timestamp or datetime.now(timezone.utc).isoformat(),
        "engine_version": {
            "db_path": str(engine.ENGINE_DIR / "reads_football_v4.0.sqlite"),
            **engine_version_fingerprint,
        },
        "source_domains": ["CFB_PLAYER_IDENTITY"],
        "production_safety": pack["safety"],
        "qa_status": "PASSED" if not pack["funnel"]["qa_failures_detail"] and pack["puzzles"] else "FAILED",
        "qa_checks_performed": pack["qa_checks_performed"],
        "difficulty_distribution": None,
        "puzzle_count": len(pack["puzzles"]),
        "puzzles": pack["puzzles"],
        "funnel": pack["funnel"],
        "review_status": "UNREVIEWED",
        "_diagnostics": {"seed": seed},
    }


def write_package(path: Path, package: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
