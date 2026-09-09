"""COMPARISON_BRACKET -- Reusable Game Format System pass, real mechanic
template #6 (the "comparison" mechanic the format-system spec calls for,
built to back the new BRACKET_TREE format -- see
tools/director_v02/visual_templates.py's own module comment for the
format/mechanic separation this fits into).

A real single-elimination bracket built entirely from a genuine, tie-free
comparable attribute: real team-season win totals -- the SAME real,
already-certified data source tools/director_v04/higher_lower.py already
uses (season_standings.wins / cfb_standings.total_wins), reused here
rather than re-derived, so this format is proven against real data on day
one rather than a fabricated one-off dataset.

Real design decision (documented, not incidental): every real matchup's
winner is FULLY DETERMINED by the two real win totals at generation
time -- there is no player-choice branching that changes which teams meet
in a later round (unlike a fantasy bracket pool). The player's job is to
correctly PREDICT every real matchup, round by round, exactly the same
"guess the real outcome" shape Weekly Pick'em already established for a
real schedule of games -- this keeps Reads' whole identity (test real
football knowledge, never invent an outcome) intact for a genuinely new
presentation shape. All matchups across all rounds are exposed up front
(the real bracket structure, not the results) and graded together --
Pick a full bracket, or a partial one that's graded on it. Simpler and
more honest than round-by-round server-gated advancement while directly
matching the format spec's own "or the player fills it in" allowance.

Two real, disclosed variants (mirrors higher_lower.py's exact two):
  - NFL_TEAM_SEASON_WINS_BRACKET: 8 real NFL team-seasons
    (season_standings.wins, NFLVERSE_DATA, SOURCE_BACKED).
  - CFB_TEAM_SEASON_WINS_BRACKET: 8 real FBS team-seasons
    (cfb_standings.total_wins, CFBD_API_LIVE, SOURCE_BACKED).
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "COMPARISON_BRACKET"
BRACKET_SIZE = 8  # 8 real entries -> 3 real rounds (quarterfinal/semifinal/final)

VARIANTS = frozenset({"NFL_TEAM_SEASON_WINS_BRACKET", "CFB_TEAM_SEASON_WINS_BRACKET"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
        "cfb_standings": safety.check_table_wide_safety(c, "cfb_standings", "CFBD_API_LIVE"),
    }


def _nfl_entrants(c, seed: str) -> list[dict]:
    rows = c.execute(
        "SELECT season, team_code, wins FROM season_standings "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND wins IS NOT NULL"
    ).fetchall()
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    entrants, seen_values = [], set()
    for r in order:
        if len(entrants) >= BRACKET_SIZE:
            break
        if r["wins"] in seen_values:
            continue  # tie-exclusion: every real matchup this pass must have a real, unambiguous winner
        fr, err = resolve_franchise(c, r["team_code"], r["season"])
        if err or fr is None:
            continue
        seen_values.add(r["wins"])
        entrants.append({
            "label": f"{fr['full_name']} ({r['season']})", "_private_value": r["wins"],
            "_audit": {"season": r["season"], "team_code": r["team_code"], "franchise_id": fr["franchise_id"]},
        })
    return entrants


def _cfb_entrants(c, seed: str) -> list[dict]:
    rows = c.execute(
        "SELECT season, school_id, school_name_raw, total_wins FROM cfb_standings "
        "WHERE verification_status='SOURCE_BACKED' AND classification='fbs' AND total_wins IS NOT NULL"
    ).fetchall()
    school_names = {r["school_id"]: r["school_name"] for r in c.execute("SELECT school_id, school_name FROM schools")}
    rng = engine_bootstrap.seeded(seed)
    order = list(rows)
    rng.shuffle(order)

    entrants, seen_values = [], set()
    for r in order:
        if len(entrants) >= BRACKET_SIZE:
            break
        if r["total_wins"] in seen_values:
            continue
        name = school_names.get(r["school_id"]) or r["school_name_raw"]
        seen_values.add(r["total_wins"])
        entrants.append({
            "label": f"{name} ({r['season']})", "_private_value": r["total_wins"],
            "_audit": {"season": r["season"], "school_id": r["school_id"]},
        })
    return entrants


def _build_bracket(entrants: list[dict]) -> list[list[dict]]:
    """Real, fully-determined single-elimination bracket over `entrants`
    (already real, tie-free, real-valued). Round 0 = quarterfinals (4 real
    matchups from the 8 entrants, seeded 1v8/4v5/3v6/2v7 -- the standard
    real tournament-seeding pairing, never a fabricated pairing rule).
    Each later round's matchups are built from the REAL winners of the
    previous round -- nothing here is a player choice, only real
    comparison outcomes."""
    seeding_pairs = [(0, 7), (3, 4), (2, 5), (1, 6)]
    rounds: list[list[dict]] = []
    current = [
        {"match_id": f"R0M{i}", "entrant_a": entrants[a]["label"], "entrant_b": entrants[b]["label"],
         "value_a": entrants[a]["_private_value"], "value_b": entrants[b]["_private_value"]}
        for i, (a, b) in enumerate(seeding_pairs)
    ]
    round_index = 0
    while True:
        winners = []
        for m in current:
            winner_label = m["entrant_a"] if m["value_a"] > m["value_b"] else m["entrant_b"]
            winner_value = max(m["value_a"], m["value_b"])
            m["real_winner"] = winner_label
            winners.append({"label": winner_label, "value": winner_value})
        rounds.append(current)
        if len(winners) == 1:
            break
        round_index += 1
        current = [
            {"match_id": f"R{round_index}M{i}", "entrant_a": winners[2 * i]["label"], "entrant_b": winners[2 * i + 1]["label"],
             "value_a": winners[2 * i]["value"], "value_b": winners[2 * i + 1]["value"]}
            for i in range(len(winners) // 2)
        ]
    return rounds


def generate_bracket(seed: str, variant: str) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        entrants = _nfl_entrants(c, seed) if variant == "NFL_TEAM_SEASON_WINS_BRACKET" else _cfb_entrants(c, seed)
    finally:
        c.close()

    shortfall_reason = None
    rounds: list[list[dict]] = []
    if len(entrants) < BRACKET_SIZE:
        shortfall_reason = (
            f"Only {len(entrants)} of {BRACKET_SIZE} real entrants with a genuinely distinct real win "
            f"total each (tie-exclusion) could be found for variant={variant!r}; a real single-elimination "
            f"bracket needs exactly {BRACKET_SIZE} tie-free entrants, so no bracket was built rather than "
            f"pad it with a duplicate or fabricated entrant."
        )
    else:
        rounds = _build_bracket(entrants)

    return {
        "entrants": entrants, "rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason,
        "comparison_attribute": "real regular-season win total",
    }


def build_package(seed: str, variant: str) -> dict:
    result = generate_bracket(seed, variant)
    package_id = "GGP9:" + hashlib.sha256(
        f"COMPARISON|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    round_labels = ["Quarterfinals", "Semifinals", "Final"]
    rounds_public = [
        {
            "round_index": i, "round_label": round_labels[i] if i < len(round_labels) else f"Round {i + 1}",
            "matchups": [
                {"match_id": m["match_id"], "entrant_a": m["entrant_a"], "entrant_b": m["entrant_b"]}
                for m in round_matches
            ],
        }
        for i, round_matches in enumerate(result["rounds"])
    ]
    # Real winners are kept out of the public package entirely -- only
    # evaluate_submission() (server-side, mechanic_engine.py) ever reads
    # result["rounds"][i][j]["real_winner"]/["value_a"]/["value_b"].
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant,
        "game_title": "NFL Wins Bracket" if variant == "NFL_TEAM_SEASON_WINS_BRACKET" else "CFB Wins Bracket",
        "game_instructions": f"Predict the real winner of every matchup in this real {BRACKET_SIZE}-team "
                              f"bracket, based on {result['comparison_attribute']}. Grade the whole bracket "
                              f"whenever you're ready.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if result["rounds"] else "FAILED",
        "rounds": rounds_public,
        "_private_rounds": result["rounds"],
        "bracket_size": BRACKET_SIZE,
        "comparison_attribute": result["comparison_attribute"],
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
