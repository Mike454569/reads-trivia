"""MISSING_PIECE -- 15-Format Expansion Part 2, format #7.

The inverse of PICK_THE_IMPOSTOR (tools/director_v04/pick_the_impostor.py):
3 real players from the same real group are shown as given context, and
the player picks which of 4 candidates was ALSO genuinely part of that
same real group -- 1 real correct completion plus 3 real decoys who
genuinely were not.

Real data, 2 variants:
  - NFL_TEAM_ROSTER_MISSING_PIECE: 3 real players shown from the same real
    NFL team's real roster in a real season (canonical_roster_seasons,
    NFLVERSE_DATA, SOURCE_BACKED); the correct answer is a 4th real player
    really on that same roster, and the 3 decoys really played for
    DIFFERENT real teams that same season.
  - CFB_SCHOOL_ROSTER_MISSING_PIECE: same idea using
    cfb_player_season_stats_real (SPORTSDATAVERSE_CFB,
    SOURCE_BACKED_DERIVED -- the same real stat-appearance roster-
    membership proxy pick_the_impostor.py already discloses).

Both the correct completion and every decoy are drawn from a real,
already-fetched pool for that exact real season -- no decoy is ever
assumed absent from the real group; it is only included once confirmed
not already among the 4 real group members (context + correct answer).

Answer format: the item_id ('A'-'D') of the real correct completion, in a
real position shuffled per round -- never sent to the client before
evaluate() runs.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "MISSING_PIECE"
VARIANTS = frozenset({"NFL_TEAM_ROSTER_MISSING_PIECE", "CFB_SCHOOL_ROSTER_MISSING_PIECE"})


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    # Same real scoping fix pick_the_impostor.py's own safety_check
    # already established: canonical_roster_seasons carries more than one
    # real source/provenance, so this is scoped to the exact
    # source_id='NFLVERSE_DATA' subset the real query below uses.
    return {
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
    }


def _nfl_team_roster_missing_piece_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT rs.season, rs.team_code, rs.player_id, p.display_name FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA'"
    ).fetchall()
    by_team_season: dict[tuple, list] = {}
    for r in rows:
        by_team_season.setdefault((r["season"], r["team_code"]), []).append(r)
    by_season: dict[int, dict[str, list]] = {}
    for (season, team), players in by_team_season.items():
        by_season.setdefault(season, {})[team] = players

    rng = engine_bootstrap.seeded(seed)
    keys = list(by_team_season.keys())
    rng.shuffle(keys)

    rounds = []
    for season, team in keys:
        if len(rounds) >= round_count:
            break
        group = by_team_season[(season, team)]
        if len(group) < 4:
            continue  # need 3 shown + 1 real correct completion, all genuinely distinct
        chosen4 = rng.sample(group, 4)
        shown, correct = chosen4[:3], chosen4[3]
        chosen_ids = {p["player_id"] for p in chosen4}
        other_pool = [p for t, plist in by_season[season].items() if t != team for p in plist
                      if p["player_id"] not in chosen_ids]
        if len(other_pool) < 3:
            continue
        decoys = rng.sample(other_pool, 3)
        rounds.append({
            "prompt": f"3 of the real {season} {team} roster are shown above. Which of these 4 was ALSO really on that roster?",
            "group_members": [p["display_name"] for p in shown],
            "correct": {"label": correct["display_name"], "_audit": {"player_id": correct["player_id"]}},
            "decoys": [{"label": d["display_name"], "_audit": {"player_id": d["player_id"]}} for d in decoys],
            "notes": f"Real {season} {team} roster (NFLVERSE_DATA, SOURCE_BACKED); every decoy really "
                     f"played for a different real team that season.",
        })
    return rounds


def _cfb_school_roster_missing_piece_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.season, s.school_id, sc.school_name, s.cfb_player_id, s.player_name "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED'"
    ).fetchall()
    by_school_season: dict[tuple, list] = {}
    for r in rows:
        by_school_season.setdefault((r["season"], r["school_id"]), []).append(r)
    by_season: dict[int, dict[str, list]] = {}
    for (season, school_id), players in by_school_season.items():
        by_season.setdefault(season, {})[school_id] = players

    rng = engine_bootstrap.seeded(seed)
    keys = list(by_school_season.keys())
    rng.shuffle(keys)

    rounds = []
    for season, school_id in keys:
        if len(rounds) >= round_count:
            break
        group = by_school_season[(season, school_id)]
        if len(group) < 4:
            continue
        chosen4 = rng.sample(group, 4)
        shown, correct = chosen4[:3], chosen4[3]
        chosen_ids = {p["cfb_player_id"] for p in chosen4}
        other_pool = [p for sid, plist in by_season[season].items() if sid != school_id for p in plist
                      if p["cfb_player_id"] not in chosen_ids]
        if len(other_pool) < 3:
            continue
        decoys = rng.sample(other_pool, 3)
        school_name = group[0]["school_name"]
        rounds.append({
            "prompt": f"3 of the real {season} {school_name} roster are shown above. Which of these 4 also really played for {school_name} that season?",
            "group_members": [p["player_name"] for p in shown],
            "correct": {"label": correct["player_name"], "_audit": {"cfb_player_id": correct["cfb_player_id"]}},
            "decoys": [{"label": d["player_name"], "_audit": {"cfb_player_id": d["cfb_player_id"]}} for d in decoys],
            "notes": f"Real {season} {school_name} players (by real recorded stats, SPORTSDATAVERSE_CFB, "
                     f"SOURCE_BACKED_DERIVED); every decoy really recorded stats for a different real school.",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_TEAM_ROSTER_MISSING_PIECE":
            raw_rounds = _nfl_team_roster_missing_piece_rounds(c, seed, round_count)
        else:  # CFB_SCHOOL_ROSTER_MISSING_PIECE
            raw_rounds = _cfb_school_roster_missing_piece_rounds(c, seed, round_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(raw_rounds) < round_count:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {round_count} requested real MISSING_PIECE rounds could be built "
            f"for variant={variant!r} with a genuine real completion plus 3 genuinely absent decoys each "
            f"time; exported the maximum available rather than include a fabricated or ambiguous option."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_TEAM_ROSTER_MISSING_PIECE": "Missing Piece", "CFB_SCHOOL_ROSTER_MISSING_PIECE": "Missing Piece"}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP20:" + hashlib.sha256(
        f"MISSING_PIECE|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct"]] + list(r["decoys"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        items = [{"item_id": item_ids[pos], "label": candidates[src]["label"]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "prompt": r["prompt"], "group_members": r["group_members"], "items": items,
            # Server-private (_prefixed) until evaluate() runs -- same
            # discipline every other mechanic's package uses.
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "3 real group members are shown -- tap whichever of these 4 real players "
                              "really belongs with them too.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
