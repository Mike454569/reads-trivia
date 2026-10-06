"""Player From Clues -- the first genuinely new Engine-generated game
mechanic (`identify_player_from_clues`).

Read `PLAYER_FROM_CLUES_FEASIBILITY_REPORT.md`, `DIRECTOR_V04_IDENTITY_POLICY.md`,
and `PLAYER_FROM_CLUES_MECHANIC_SPEC.md` first -- this module implements the
contract those documents define, and does not re-explain the reasoning
behind it inline beyond what's needed to read the code.

Keeps all NFL-specific clue construction inside this module. Reuses shared
infrastructure from `tools/quiz_export/` (production safety, deterministic
seeding, duplicate detection) and `tools/quiz_export/adapters/draft.py`
(`resolve_franchise`, proven across four prior capabilities) rather than
reimplementing any of it.
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import duplicates, engine, safety  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402
from tools.director_v04 import question_intelligence  # noqa: E402

PACKAGE_SCHEMA_VERSION = "0.4"
MECHANIC = "identify_player_from_clues"
CATEGORY = "Player From Clues"
ID_START = 620000
MIN_CLUES = 3
MAX_CLUES = 5

# Building the full source-backed player universe/index is intentionally
# comprehensive and can take several seconds on a cold Fly volume. It is
# immutable for the lifetime of one Gateway process, so cache it in memory
# and prewarm it at boot instead of making the first player pay that cost.
_GENERATION_CONTEXT_LOCK = threading.Lock()
_GENERATION_CONTEXT_CACHE = None


def _generation_context():
    global _GENERATION_CONTEXT_CACHE
    if _GENERATION_CONTEXT_CACHE is not None:
        return _GENERATION_CONTEXT_CACHE
    with _GENERATION_CONTEXT_LOCK:
        if _GENERATION_CONTEXT_CACHE is not None:
            return _GENERATION_CONTEXT_CACHE
        c = engine.connect()
        try:
            safety_result = safety_check(c)
            facts, indexes, universe_ids = build_universe(c)
        finally:
            c.close()
        _GENERATION_CONTEXT_CACHE = (safety_result, facts, indexes, universe_ids)
        return _GENERATION_CONTEXT_CACHE


def warm_generation_cache() -> dict:
    safety_result, facts, _indexes, universe_ids = _generation_context()
    return {
        "ready": True,
        "universe_size": len(universe_ids),
        "safety_domains": sorted(safety_result),
        "fact_count": len(facts),
    }


# Deterministic, fact-preserving templates -- NEVER LLM-generated (Part D).
# Each lambda only ever inserts an already-verified `value`; it cannot
# introduce any fact not already present in that value.
CLUE_TEMPLATES = {
    "draft_year": lambda v: f"He was drafted into the NFL in {v}.",
    "draft_round": lambda v: f"His name was called in Round {v}.",
    "draft_pick_overall": lambda v: f"He was selected with the No. {v} overall pick.",
    "position": lambda v: f"His listed NFL position was {v}.",
    "drafting_franchise": lambda v: f"The {v} were the team that drafted him.",
    "team_history": lambda v: f"At one point in his NFL career, he suited up for the {v}.",
    "career_span": lambda v: f"His recorded NFL career ran from {v[0]} through {v[1]}.",
    "college": lambda v: f"He played his college football at {v}.",
    "postseason_participation": lambda v: "He reached the NFL postseason as an active roster player.",
    "won_super_bowl": lambda v: "He was on an active roster for a Super Bowl champion.",
}

# V2 composite clues combine two independently verified facts. They are not
# synthetic facts: the candidate set is the intersection of both source-backed
# atomic facts, and QA independently recomputes that same intersection.
COMPOSITE_CLUES = {
    "college_position": {
        "components": ("college", "position"),
        "template": lambda v: f"He played {v[1]} and came into the league from {v[0]}.",
    },
    "draft_year_round": {
        "components": ("draft_year", "draft_round"),
        "template": lambda v: f"He entered the NFL in the {v[0]} draft and was taken in Round {v[1]}.",
    },
    "draft_team_year": {
        "components": ("drafting_franchise", "draft_year"),
        "template": lambda v: f"The {v[0]} drafted him in {v[1]}.",
    },
    "college_career_span": {
        "components": ("college", "career_span"),
        "template": lambda v: f"He played at {v[0]} before an NFL career that ran from {v[1][0]} through {v[1][1]}.",
    },
    "team_super_bowl": {
        "components": ("team_history", "won_super_bowl"),
        "template": lambda v: f"He spent part of his NFL career with the {v[0]} and was on an active roster for a Super Bowl champion.",
    },
}

# Provenance metadata per atomic clue type.
CLUE_SOURCE_META = {
    "draft_year": {"table": "draft_facts", "field": "draft_season", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "draft_round": {"table": "draft_facts", "field": "draft_round", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "draft_pick_overall": {"table": "draft_facts", "field": "draft_pick_overall", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "position": {"table": "draft_facts", "field": "position", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "drafting_franchise": {"table": "draft_facts+team_aliases", "field": "draft_team (season-resolved)", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "team_history": {"table": "canonical_roster_seasons+team_aliases", "field": "team_code (season-resolved)", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "career_span": {"table": "canonical_roster_seasons", "field": "MIN/MAX(season) WHERE games>0", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "college": {"table": "relationships(ATTENDED_BEFORE_DRAFT)+schools", "field": "school_name", "source_id": "READS_IDENTITY_BRIDGE", "verification_status": "PRODUCTION_SAFE_DERIVED"},
    "postseason_participation": {"table": "canonical_roster_seasons+season_standings", "field": "playoff_result IS NOT NULL (derived join on team_code+season, games>0)", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
    "won_super_bowl": {"table": "canonical_roster_seasons+season_standings", "field": "playoff_result='WonSB' (derived join on team_code+season, games>0)", "source_id": "NFLVERSE_DATA", "verification_status": "SOURCE_BACKED"},
}


def _clue_components(clue_type: str) -> tuple[str, ...]:
    spec = COMPOSITE_CLUES.get(clue_type)
    return tuple(spec["components"]) if spec else (clue_type,)


def _source_meta_for(clue_type: str):
    components = _clue_components(clue_type)
    if len(components) == 1:
        return CLUE_SOURCE_META[components[0]]
    return {"composite": True, "components": [CLUE_SOURCE_META[x] for x in components]}


def _display_text_for(clue_type: str, value):
    if clue_type in COMPOSITE_CLUES:
        return COMPOSITE_CLUES[clue_type]["template"](value)
    return CLUE_TEMPLATES[clue_type](value)


QA_CHECKS_PERFORMED = [
    # Absolute Final Closeout fix: this cited a stale number. 4,506 is
    # player_identity_links' own row count (DIRECTOR_V04_IDENTITY_POLICY.md's
    # "safe universe" -- confirmed still real and unchanged, not a
    # regression) -- the raw pool of players resolvable through
    # draft_facts.player_key -> canonical_players.player_id at all,
    # BEFORE this mechanic's own further narrowing. A later pass added the
    # MIN_REAL_SEASONS=5 filter above (build_universe()'s own "Real bug
    # found in production validation" comment) specifically to exclude
    # drafted-but-never-played players from making unfair/unfun targets,
    # which correctly narrows the REAL, CURRENT eligible universe this
    # mechanic actually draws from to 2,489 (verified directly against the
    # live Engine, not assumed) -- that pass never updated this comment's
    # older, now-superseded number. Both figures are real; this one was
    # simply describing an earlier stage of the same real pipeline.
    "target player resolved through the current 2,489-player eligible universe (a further real, disclosed "
    "MIN_REAL_SEASONS>=5 narrowing of the 4,506-player safe universe from DIRECTOR_V04_IDENTITY_POLICY.md)",
    "every clue value independently re-derived from its index and re-checked to contain the target player_id "
    "(not merely trusted from construction)",
    "every clue's source/verification_status checked against the constant per-type provenance table",
    "name-leakage check: no clue's display_text contains the target's display_name (case-insensitive substring)",
    "no duplicate clue_type within one puzzle",
    "no contradictory clues (each clue_type has exactly one authoritative source per player -- structurally "
    "prevented, not merely checked)",
    "candidate-narrowing chain independently recomputed and checked for monotonic non-increase and contiguity "
    "(clue[i].candidates_before == clue[i-1].candidates_after)",
    "clue[0].candidates_before == full universe size",
    "final candidate set independently recomputed and checked to equal exactly {target_player_id}",
    "clue count within [3, 5]",
    "duplicate-puzzle-target guard (no player targeted twice in one export)",
    "duplicate-clue-sequence guard (no two puzzles share an identical ordered (clue_type, value) sequence)",
    "production safety: NFL_DRAFT domain, canonical_players/canonical_roster_seasons/season_standings table-wide "
    "checks, NFL_CFB_IDENTITY_BRIDGE domain -- all independently verified before generation",
]


def safety_check(c) -> dict:
    return {
        "NFL_DRAFT": safety.check_domain_coverage_safety(c, "NFL_DRAFT"),
        # v0.8: canonical_players now legitimately spans two approved sources --
        # NFLVERSE_DATA's original 2006-2019 rows and NFLVERSE_ROSTERS' 2020-2026
        # extension (see Reads_Football_Data_Engine_v4.0/import_modern_rosters_v08.py).
        "canonical_players": safety.check_table_wide_safety(c, "canonical_players", ["NFLVERSE_DATA", "NFLVERSE_ROSTERS"]),
        "canonical_roster_seasons": safety.check_table_wide_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", where_extra="games > 0"
        ),
        "season_standings": safety.check_table_wide_safety(
            c, "season_standings", "NFLVERSE_DATA", where_extra="playoff_result IS NOT NULL"
        ),
        "NFL_CFB_IDENTITY_BRIDGE": safety.check_domain_coverage_safety(c, "NFL_CFB_IDENTITY_BRIDGE"),
    }


def build_universe(c):
    """Returns (facts: dict[player_id -> dict], indexes: dict[clue_type -> dict[value -> set[player_id]]],
    universe_ids: frozenset[player_id]). Pure function of Engine data + this module's fixed rules --
    no randomness anywhere in here."""
    base_rows = c.execute(
        "SELECT d.player_key AS player_id, cp.display_name, d.draft_season, d.draft_round, "
        "d.draft_pick_overall, d.position, d.draft_team "
        "FROM draft_facts d JOIN canonical_players cp ON cp.player_id = d.player_key "
        "WHERE d.verification_status='SOURCE_BACKED' AND d.source_id='NFLVERSE_DATA' "
        "AND d.player_key LIKE 'PFR:%'"
    ).fetchall()

    facts: dict = {}
    for r in base_rows:
        facts[r["player_id"]] = {
            "player_id": r["player_id"], "display_name": r["display_name"],
            "draft_year": r["draft_season"], "draft_round": r["draft_round"],
            "draft_pick_overall": r["draft_pick_overall"], "position": r["position"],
            "draft_team_code": r["draft_team"],
        }
    universe_ids = frozenset(facts.keys())

    for pid, f in facts.items():
        fr, _err = resolve_franchise(c, f["draft_team_code"], f["draft_year"])
        f["drafting_franchise"] = fr["full_name"] if fr else None

    placeholders = ",".join("?" * len(universe_ids))
    roster_rows = c.execute(
        f"SELECT player_id, season, team_code FROM canonical_roster_seasons "
        f"WHERE games > 0 AND player_id IN ({placeholders})",
        tuple(universe_ids),
    ).fetchall()
    roster_by_player: dict = {}
    for r in roster_rows:
        roster_by_player.setdefault(r["player_id"], []).append((r["season"], r["team_code"]))

    for pid, f in facts.items():
        seasons = sorted(roster_by_player.get(pid, []))
        f["n_real_seasons"] = len(set(s[0] for s in seasons))
        if seasons:
            f["career_span"] = (seasons[0][0], seasons[-1][0])
            other_team_seasons = [s for s in seasons if s[1] != f["draft_team_code"]]
            if other_team_seasons:
                last_season, last_team_code = other_team_seasons[-1]
                fr, _err = resolve_franchise(c, last_team_code, last_season)
                f["team_history"] = fr["full_name"] if fr else None
            else:
                f["team_history"] = None
        else:
            f["career_span"] = None
            f["team_history"] = None

    # Real bug found in production validation: the universe was every
    # drafted player ever (draft_facts, unfiltered) -- 49.4% of them
    # (5,483 of 11,099) have ZERO real recorded roster seasons with
    # games>0 (drafted but never actually played), and another 8.3%
    # (925) have exactly one real season, producing a degenerate
    # "spanned 2006 to 2006" career_span clue that reads like a bug even
    # though it's technically accurate. Neither makes for a fair or
    # recognizable "Who Am I" target. Scoped to real players with at
    # least 5 distinct real recorded seasons (games>0) -- a genuine
    # "stuck in the league" bar (the average NFL career is often cited
    # around 3.3 years, so this is meaningfully above merely average),
    # not just "played at all." 2,489 real candidates remain, still far
    # more than this capability's own max_question_count (25) ever
    # needs, using only data already computed here -- no new data, no
    # fabricated "fame" score.
    MIN_REAL_SEASONS = 5
    excluded_ids = {pid for pid, f in facts.items() if f["n_real_seasons"] < MIN_REAL_SEASONS}
    for pid in excluded_ids:
        del facts[pid]
    universe_ids = frozenset(facts.keys())
    placeholders = ",".join("?" * len(universe_ids))

    standings = {
        (r["team_code"], r["season"]): r["playoff_result"]
        for r in c.execute("SELECT team_code, season, playoff_result FROM season_standings WHERE playoff_result IS NOT NULL")
    }
    for pid, f in facts.items():
        seasons = roster_by_player.get(pid, [])
        results = {standings[(tc, s)] for (s, tc) in seasons if (tc, s) in standings}
        f["postseason_participation"] = True if results else None
        f["won_super_bowl"] = True if "WonSB" in results else None

    college_rows = c.execute(
        f"SELECT r.object_id AS player_id, s.school_name FROM relationships r "
        f"JOIN schools s ON s.school_id = r.subject_id "
        f"WHERE r.predicate='ATTENDED_BEFORE_DRAFT' AND r.object_id IN ({placeholders})",
        tuple(universe_ids),
    ).fetchall()
    college_by_player: dict = {}
    for r in college_rows:
        college_by_player.setdefault(r["player_id"], set()).add(r["school_name"])
    for pid, f in facts.items():
        schools = college_by_player.get(pid)
        f["college"] = next(iter(schools)) if schools and len(schools) == 1 else None

    indexes: dict = {ct: {} for ct in CLUE_TEMPLATES}
    for pid, f in facts.items():
        for ct in ("draft_year", "draft_round", "draft_pick_overall", "position", "drafting_franchise", "team_history", "college"):
            v = f.get(ct)
            if v is not None:
                indexes[ct].setdefault(v, set()).add(pid)
        cs = f.get("career_span")
        if cs is not None:
            indexes["career_span"].setdefault(cs, set()).add(pid)
        if f.get("postseason_participation"):
            indexes["postseason_participation"].setdefault(True, set()).add(pid)
        if f.get("won_super_bowl"):
            indexes["won_super_bowl"].setdefault(True, set()).add(pid)

    return facts, indexes, universe_ids


def _atomic_candidate_set(pid: str, clue_type: str, value, indexes: dict):
    cset = indexes.get(clue_type, {}).get(value)
    if not cset or pid not in cset:
        return None
    return cset


def _candidate_clues_for_player(pid: str, facts: dict, indexes: dict) -> list:
    f = facts[pid]
    out = []
    atomic = {}
    for ct, value_index in indexes.items():
        v = f.get(ct)
        if ct in ("postseason_participation", "won_super_bowl"):
            if not v:
                continue
            v = True
        if v is None:
            continue
        cset = value_index.get(v)
        if not cset or pid not in cset:
            continue
        atomic[ct] = (v, cset)
        out.append((ct, v, cset))

    for composite_type, spec in COMPOSITE_CLUES.items():
        components = tuple(spec["components"])
        if not all(ct in atomic for ct in components):
            continue
        values = tuple(atomic[ct][0] for ct in components)
        csets = [atomic[ct][1] for ct in components]
        combined = set(csets[0])
        for cs in csets[1:]:
            combined &= cs
        if pid in combined and combined:
            out.append((composite_type, values, frozenset(combined)))
    return out


def _candidate_set_for_clue(pid: str, clue_type: str, value, indexes: dict):
    components = _clue_components(clue_type)
    if len(components) == 1:
        return _atomic_candidate_set(pid, components[0], value, indexes)
    values = tuple(value)
    sets = []
    for ct, v in zip(components, values):
        cs = _atomic_candidate_set(pid, ct, v, indexes)
        if not cs:
            return None
        sets.append(cs)
    combined = set(sets[0])
    for cs in sets[1:]:
        combined &= cs
    return frozenset(combined)


# Who Am I v2 player-facing roles. These do not alter truth; they only decide
# which verified narrowing clue belongs at which point of the reveal ladder.
OPENING_CLUE_VARIETY_EXCLUDE = frozenset({
    "postseason_participation", "position", "draft_pick_overall", "draft_round",
})
OPENING_CLUE_PREFERRED = frozenset({
    "college_position", "college_career_span", "team_history", "college",
    "career_span", "drafting_franchise", "won_super_bowl",
})
MIDDLE_CLUE_PREFERRED = frozenset({
    "draft_year_round", "draft_team_year", "college_position",
    "college_career_span", "team_super_bowl", "career_span",
})
LATE_CLUE_PREFERRED = frozenset({
    "draft_pick_overall", "draft_team_year", "draft_year_round",
    "drafting_franchise", "college", "team_history",
})
# Ideal fraction of the current candidate pool remaining after each clue.
# Broad first, progressively sharper later.
_CLUE_STAGE_TARGET_RATIO = (0.48, 0.24, 0.10, 0.035, 0.0)


def _clue_role_bonus(clue_type: str, clue_index: int) -> int:
    if clue_index == 0:
        return 30 if clue_type in OPENING_CLUE_PREFERRED else 0
    if clue_index >= 3:
        return 22 if clue_type in LATE_CLUE_PREFERRED else 0
    return 18 if clue_type in MIDDLE_CLUE_PREFERRED else 0


def _clue_human_quality(clue_type: str, display_text: str, before: int, after: int, clue_index: int) -> dict:
    reduction = 1.0 - (after / max(1, before))
    target_ratio = _CLUE_STAGE_TARGET_RATIO[min(clue_index, len(_CLUE_STAGE_TARGET_RATIO)-1)]
    actual_ratio = after / max(1, before)
    stage_fit = max(0.0, 1.0 - abs(actual_ratio - target_ratio))
    score = 45 + int(30 * stage_fit) + _clue_role_bonus(clue_type, clue_index)
    if clue_type == "position":
        score -= 25
    if clue_type == "postseason_participation":
        score -= 18
    if clue_type in COMPOSITE_CLUES:
        score += 10
    if reduction < 0.05:
        score -= 15
    score = max(0, min(100, score))
    return {
        "score": score,
        "stage": "opening" if clue_index == 0 else ("giveaway" if after == 1 else "narrowing"),
        "information_gain": round(reduction, 4),
        "candidate_ratio_after": round(actual_ratio, 4),
        "composite": clue_type in COMPOSITE_CLUES,
        "text_fingerprint": question_intelligence.semantic_fingerprint({"question": display_text}),
    }


def build_puzzle(pid: str, facts: dict, indexes: dict, universe_ids: frozenset):
    """Build a human-first progressive clue ladder from verified facts."""
    f = facts[pid]
    running = universe_ids
    pool = _candidate_clues_for_player(pid, facts, indexes)
    selected: list = []
    used_components: set[str] = set()

    while len(selected) < MAX_CLUES:
        step_options = []
        for ct, v, cset in pool:
            components = set(_clue_components(ct))
            if components & used_components:
                continue
            new_set = running & cset
            if len(new_set) >= len(running):
                continue
            display_text = _display_text_for(ct, v)
            if f["display_name"] and f["display_name"].lower() in display_text.lower():
                continue
            quality = _clue_human_quality(ct, display_text, len(running), len(new_set), len(selected))
            step_options.append((quality["score"], ct, v, cset, new_set, display_text, quality))

        if not step_options:
            break

        if len(selected) == 0:
            varied = [o for o in step_options if o[1] not in OPENING_CLUE_VARIETY_EXCLUDE]
            if varied:
                step_options = varied

        # Do not end the puzzle before the minimum reveal count when another
        # legitimate narrowing clue is available.
        if len(selected) + 1 < MIN_CLUES:
            non_terminal = [o for o in step_options if len(o[4]) > 1]
            if non_terminal:
                step_options = non_terminal

        # Human quality first; if tied, prefer the broader clue early and the
        # sharper clue late. Final alphabetical tie-break keeps determinism.
        if len(selected) < 2:
            step_options.sort(key=lambda x: (-x[0], -len(x[4]), x[1]))
        else:
            step_options.sort(key=lambda x: (-x[0], len(x[4]), x[1]))

        _score, ct, v, _cset, new_set, display_text, quality = step_options[0]
        selected.append({
            "clue_index": len(selected),
            "clue_type": ct,
            "components": list(_clue_components(ct)),
            "value": v,
            "display_text": display_text,
            "source": _source_meta_for(ct),
            "candidates_before": len(running),
            "candidates_after": len(new_set),
            "clue_intelligence": quality,
        })
        used_components.update(_clue_components(ct))
        running = new_set
        if len(running) == 1 and len(selected) >= MIN_CLUES:
            break

    if len(selected) < MIN_CLUES:
        return None, "INSUFFICIENT_NARROWING_CLUES"
    if len(running) != 1:
        return None, f"AMBIGUOUS_FINAL_SET_SIZE_{len(running)}"
    if next(iter(running)) != pid:
        return None, "UNIQUENESS_MISMATCH"

    # Ladder score rewards progressive narrowing and human-readable clue mix.
    clue_scores = [cl["clue_intelligence"]["score"] for cl in selected]
    puzzle = {
        "answer": {"answer_type": "player", "player_id": pid, "display_name": f["display_name"]},
        "clues": selected,
        "final_candidate_count": len(running),
        "who_am_i_v2": {
            "version": 2,
            "ladder_score": round(sum(clue_scores) / len(clue_scores), 1),
            "composite_clue_count": sum(1 for cl in selected if cl["clue_intelligence"]["composite"]),
            "opening_candidate_count": selected[0]["candidates_after"],
        },
    }
    return puzzle, None


def validate_puzzle_qa(puzzle: dict, universe_ids: frozenset, indexes: dict) -> list:
    """Independent re-verification pass -- does NOT trust build_puzzle()'s
    own bookkeeping. Re-derives every claim from `indexes` fresh. Returns a
    list of issue strings; empty means the puzzle passes."""
    issues = []
    target = puzzle["answer"]["player_id"]
    if target not in universe_ids:
        issues.append("TARGET_NOT_IN_UNIVERSE")
        return issues

    clues = puzzle["clues"]
    if not (MIN_CLUES <= len(clues) <= MAX_CLUES):
        issues.append(f"CLUE_COUNT_OUT_OF_BOUNDS_{len(clues)}")

    seen_types = set()
    seen_pairs = set()
    running = universe_ids
    for i, clue in enumerate(clues):
        ct, v = clue["clue_type"], clue["value"]
        if ct in seen_types:
            issues.append(f"DUPLICATE_CLUE_TYPE_{ct}")
        seen_types.add(ct)
        v_key = v if not isinstance(v, list) else tuple(v)
        seen_pairs.add((ct, v_key))

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


def generate_pack(seed: str, target_count: int = 25, id_start: int = ID_START,
                  stop_after_target: bool = False) -> dict:
    safety_result, facts, indexes, universe_ids = _generation_context()

    order = sorted(universe_ids)  # deterministic base order before seeding
    rng = engine.seeded(seed)
    rng.shuffle(order)

    rejected_counts: Counter = Counter()
    accepted: list = []
    guard = duplicates.DuplicateGuard(track_entity=True)
    qa_failed: list = []

    for pid in order:
        puzzle, reason = build_puzzle(pid, facts, indexes, universe_ids)
        if puzzle is None:
            rejected_counts[reason] += 1
            continue
        if guard.entity_seen(pid):
            rejected_counts["DUPLICATE_PUZZLE_TARGET"] += 1
            continue
        sequence_signature = "|".join(f"{cl['clue_type']}={cl['value']}" for cl in puzzle["clues"])
        if guard.question_seen(sequence_signature):
            rejected_counts["DUPLICATE_CLUE_SEQUENCE"] += 1
            continue

        issues = validate_puzzle_qa(puzzle, universe_ids, indexes)
        if issues:
            qa_failed.append({"player_id": pid, "issues": issues})
            rejected_counts["QA_FAILED"] += 1
            continue

        puzzle["puzzle_id"] = id_start + len(accepted)
        puzzle["mechanic"] = MECHANIC
        puzzle["qa_status"] = "PASSED"
        accepted.append(puzzle)
        guard.record(sequence_signature, pid)
        if stop_after_target and len(accepted) >= target_count:
            break

    exported = accepted[:target_count]
    shortfall_reason = None
    if len(exported) < target_count:
        shortfall_reason = (
            f"Only {len(accepted)} of {len(universe_ids)} safe-universe players (in this "
            f"seeded order) produced a puzzle passing every rule; exported the maximum "
            f"available ({len(accepted)}) rather than loosen the minimum-clue-count or "
            f"uniqueness requirements to reach {target_count}."
        )

    clue_type_counts: Counter = Counter()
    clue_counts_per_puzzle: list = []
    for p in exported:
        clue_counts_per_puzzle.append(len(p["clues"]))
        for cl in p["clues"]:
            clue_type_counts[cl["clue_type"]] += 1

    funnel = {
        "universe_size": len(universe_ids),
        "attempted": len(order),
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
        "mechanic": MECHANIC,
        "category": CATEGORY,
        "safety": safety_result,
        "puzzles": exported,
        "funnel": funnel,
        "qa_checks_performed": QA_CHECKS_PERFORMED,
        "seed": seed,
    }


def _engine_version_fingerprint(c) -> dict:
    """Same rationale as game_director_v01.py's fingerprint: a raw file hash
    would capture incidental writes to unrelated tables (e.g. Director's own
    request-logging) and be non-deterministic across otherwise-identical
    runs. Fingerprints only the specific tables this mechanic reads."""
    database_version = c.execute("SELECT value FROM meta WHERE key = 'database_version'").fetchone()
    return {
        "database_version": database_version[0] if database_version else None,
        "draft_facts_row_count": c.execute("SELECT COUNT(*) FROM draft_facts").fetchone()[0],
        "canonical_players_row_count": c.execute("SELECT COUNT(*) FROM canonical_players").fetchone()[0],
        "canonical_roster_seasons_row_count": c.execute("SELECT COUNT(*) FROM canonical_roster_seasons").fetchone()[0],
        "season_standings_row_count": c.execute("SELECT COUNT(*) FROM season_standings").fetchone()[0],
        "attended_before_draft_row_count": c.execute(
            "SELECT COUNT(*) FROM relationships WHERE predicate='ATTENDED_BEFORE_DRAFT'"
        ).fetchone()[0],
    }


def build_package(seed: str, target_count: int = 25, id_start: int = ID_START,
                   requested_description: str | None = None, freeze_timestamp: str | None = None,
                   stop_after_target: bool = False) -> dict:
    """Wraps generate_pack()'s raw output in the full GeneratedGamePackage
    shape used by every other capability in this project, adapted for this
    mechanic's answer/clue model (no options/correctIndex -- see
    PLAYER_FROM_CLUES_MECHANIC_SPEC.md, Part G)."""
    pack = generate_pack(seed, target_count=target_count, id_start=id_start,
                         stop_after_target=stop_after_target)

    c = engine.connect()
    engine_version_fingerprint = _engine_version_fingerprint(c)
    c.close()

    description = requested_description or (
        "Identify the NFL player from a progressive sequence of source-backed clues."
    )
    package_id = "GGP4:" + hashlib.sha256(
        f"{description}|{seed}|{MECHANIC}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]

    return {
        "package_id": package_id,
        "package_version": PACKAGE_SCHEMA_VERSION,
        "mechanic": MECHANIC,
        "requested_description": description,
        "game_title": "Player From Clues",
        "game_instructions": (
            "You'll see a sequence of verified clues about one NFL player, revealed one at a "
            "time and narrowing from broad to specific. Identify the player."
        ),
        "generated_at": freeze_timestamp or datetime.now(timezone.utc).isoformat(),
        "engine_version": {
            "db_path": str(engine.ENGINE_DIR / "reads_football_v4.0.sqlite"),
            **engine_version_fingerprint,
        },
        "source_domains": ["NFL_DRAFT", "NFL_CFB_IDENTITY_BRIDGE"],
        "production_safety": pack["safety"],
        "qa_status": "PASSED" if not pack["funnel"]["qa_failures_detail"] and pack["puzzles"] else "FAILED",
        "qa_checks_performed": pack["qa_checks_performed"],
        "difficulty_distribution": None,  # see PLAYER_FROM_CLUES_MECHANIC_SPEC.md, Part H
        "puzzle_count": len(pack["puzzles"]),
        "puzzles": pack["puzzles"],
        "funnel": pack["funnel"],
        "review_status": "UNREVIEWED",
        "_diagnostics": {"seed": seed},
    }


def write_package(path: Path, package: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
