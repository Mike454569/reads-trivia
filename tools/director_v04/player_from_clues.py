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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import duplicates, engine, safety  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402

PACKAGE_SCHEMA_VERSION = "0.4"
MECHANIC = "identify_player_from_clues"
CATEGORY = "Player From Clues"
ID_START = 620000
MIN_CLUES = 3
MAX_CLUES = 5

# Deterministic, fact-preserving templates -- NEVER LLM-generated (Part D).
# Each lambda only ever inserts an already-verified `value`; it cannot
# introduce any fact not already present in that value.
CLUE_TEMPLATES = {
    "draft_year": lambda v: f"This player was drafted in {v}.",
    "draft_round": lambda v: f"This player was drafted in round {v}.",
    "draft_pick_overall": lambda v: f"This player was selected with the #{v} overall pick.",
    "position": lambda v: f"This player's position at the time of the draft was {v}.",
    "drafting_franchise": lambda v: f"This player was drafted by the {v}.",
    "team_history": lambda v: f"At another point in his career, this player played for the {v}.",
    "career_span": lambda v: f"This player's NFL career (by recorded roster seasons) spanned {v[0]} to {v[1]}.",
    "college": lambda v: f"This player attended {v} before entering the NFL draft.",
    "postseason_participation": lambda v: (
        "This player was on an NFL team's active roster during a playoff run at some point in his career."
    ),
    "won_super_bowl": lambda v: (
        "This player was on the active roster of a team that won the Super Bowl at some point in his career."
    ),
}

# Provenance metadata per clue type -- constant per type, attached to every
# clue instance of that type (see PLAYER_FROM_CLUES_MECHANIC_SPEC.md).
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

QA_CHECKS_PERFORMED = [
    "target player resolved through the fixed 4,506-player safe universe (DIRECTOR_V04_IDENTITY_POLICY.md)",
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
        "canonical_players": safety.check_table_wide_safety(c, "canonical_players", "NFLVERSE_DATA"),
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


def _candidate_clues_for_player(pid: str, facts: dict, indexes: dict) -> list:
    f = facts[pid]
    out = []
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
            continue  # defensive -- should be unreachable given how indexes are built
        out.append((ct, v, cset))
    return out


def build_puzzle(pid: str, facts: dict, indexes: dict, universe_ids: frozenset):
    """Returns (puzzle_dict, None) or (None, rejection_reason_str). Never
    raises for an ordinary player who simply doesn't have enough safe,
    narrowing clue data -- that's a normal, counted rejection."""
    f = facts[pid]
    running = universe_ids
    pool = _candidate_clues_for_player(pid, facts, indexes)
    selected: list = []
    used_types: set = set()

    while len(selected) < MAX_CLUES:
        step_options = []
        for ct, v, cset in pool:
            if ct in used_types:
                continue
            new_set = running & cset
            if len(new_set) < len(running):  # must actually narrow -- rejects "true but useless" clues (Part E)
                step_options.append((ct, v, cset, new_set))
        if not step_options:
            break
        # Broadest still-narrowing clue first; deterministic alphabetical tie-break, no RNG.
        step_options.sort(key=lambda x: (-len(x[3]), x[0]))
        ct, v, _cset, new_set = step_options[0]
        display_text = CLUE_TEMPLATES[ct](v)
        if f["display_name"] and f["display_name"].lower() in display_text.lower():
            pool = [c for c in pool if c[0] != ct]  # name-leakage -- drop this clue type, try the next best
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
        return None, "UNIQUENESS_MISMATCH"  # should be unreachable; a real bug if ever hit

    puzzle = {
        "answer": {"answer_type": "player", "player_id": pid, "display_name": f["display_name"]},
        "clues": selected,
        "final_candidate_count": len(running),
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


def generate_pack(seed: str, target_count: int = 25, id_start: int = ID_START) -> dict:
    c = engine.connect()
    safety_result = safety_check(c)
    facts, indexes, universe_ids = build_universe(c)
    c.close()

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
                   requested_description: str | None = None, freeze_timestamp: str | None = None) -> dict:
    """Wraps generate_pack()'s raw output in the full GeneratedGamePackage
    shape used by every other capability in this project, adapted for this
    mechanic's answer/clue model (no options/correctIndex -- see
    PLAYER_FROM_CLUES_MECHANIC_SPEC.md, Part G)."""
    pack = generate_pack(seed, target_count=target_count, id_start=id_start)

    c = engine.connect()
    engine_version_fingerprint = _engine_version_fingerprint(c)
    c.close()

    description = requested_description or (
        "Identify the NFL player from a progressive sequence of source-backed clues."
    )
    package_id = "GGP4:" + hashlib.sha256(f"{description}|{seed}|{MECHANIC}".encode()).hexdigest()[:24]

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
