"""CAREER_PATH -- 15-Format Expansion Part 2, format #10.

The inverse of MAP_THE_CAREER (tools/director_v04/sorting.py's
NFL_PLAYER_CAREER_TEAM_ORDER / CFB_PLAYER_CAREER_SCHOOL_ORDER variants):
that format shows a player's name and asks the player to order their real
teams/schools; this format shows the already-ordered real path of
teams/schools and asks the player to identify WHICH real player it
belongs to, from 4 real multiple-choice options.

Real data, 2 variants:
  - NFL_PLAYER_CAREER_PATH_IDENTIFY: the real first N teams (by real
    debut season) of one real NFL player's real career
    (canonical_roster_seasons, NFLVERSE_DATA, SOURCE_BACKED), plus 3 real
    decoy players.
  - CFB_PLAYER_CAREER_PATH_IDENTIFY: same real idea using
    cfb_player_season_stats_real (SPORTSDATAVERSE_CFB,
    SOURCE_BACKED_DERIVED).

Every decoy's OWN real path (their own first N real teams/schools by
debut season) is checked against the correct player's real shown path
and rejected if it matches -- a decoy whose real path is identical to
the correct answer's would itself be a second valid real answer, which
this never risks presenting as if it were simply wrong.

Answer format: the item_id ('A'-'D') of the real correct player, in a
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
MECHANIC = "CAREER_PATH"
VARIANTS = frozenset({"NFL_PLAYER_CAREER_PATH_IDENTIFY", "CFB_PLAYER_CAREER_PATH_IDENTIFY"})
PATH_LENGTH = 3


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED",
        ),
    }


def _nfl_career_path_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT rs.player_id, p.display_name, rs.season, rs.team_code FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["player_id"], []).append(r)

    def _path_for(pid: str):
        earliest_by_team: dict[str, int] = {}
        for h in by_player[pid]:
            if h["team_code"] not in earliest_by_team or h["season"] < earliest_by_team[h["team_code"]]:
                earliest_by_team[h["team_code"]] = h["season"]
        if len(earliest_by_team) < PATH_LENGTH:
            return None
        ordered_teams = sorted(earliest_by_team, key=lambda t: earliest_by_team[t])
        return tuple(ordered_teams[:PATH_LENGTH])

    rng = engine_bootstrap.seeded(seed)
    eligible_ids = [pid for pid, hist in by_player.items() if len({h["team_code"] for h in hist}) >= PATH_LENGTH]
    rng.shuffle(eligible_ids)

    rounds = []
    for pid in eligible_ids:
        if len(rounds) >= round_count:
            break
        path = _path_for(pid)
        if path is None:
            continue
        display_name = by_player[pid][0]["display_name"]
        decoy_pool = [d for d in eligible_ids if d != pid]
        rng.shuffle(decoy_pool)
        decoys = []
        for d in decoy_pool:
            if len(decoys) >= 3:
                break
            dpath = _path_for(d)
            if dpath is None or dpath == path:
                continue  # a real decoy sharing the exact same real path would be a 2nd valid answer -- skip
            decoys.append(by_player[d][0]["display_name"])
        if len(decoys) < 3:
            continue
        rounds.append({
            "path": list(path), "correct_label": display_name, "decoy_labels": decoys,
            "notes": f"Real career path (first {PATH_LENGTH} real teams by debut season) for "
                     f"{display_name} (NFLVERSE_DATA, SOURCE_BACKED).",
        })
    return rounds


def _cfb_career_path_rounds(c, seed: str, round_count: int) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, s.player_name, s.season, s.school_id, sc.school_name "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED'"
    ).fetchall()
    by_player: dict[str, list] = {}
    for r in rows:
        by_player.setdefault(r["cfb_player_id"], []).append(r)

    def _path_for(pid: str):
        earliest_by_school: dict[str, tuple] = {}
        for h in by_player[pid]:
            if h["school_id"] not in earliest_by_school or h["season"] < earliest_by_school[h["school_id"]][0]:
                earliest_by_school[h["school_id"]] = (h["season"], h["school_name"])
        if len(earliest_by_school) < PATH_LENGTH:
            return None
        ordered = sorted(earliest_by_school, key=lambda s: earliest_by_school[s][0])[:PATH_LENGTH]
        return tuple(ordered)

    rng = engine_bootstrap.seeded(seed)
    eligible_ids = [pid for pid, hist in by_player.items() if len({h["school_id"] for h in hist}) >= PATH_LENGTH]
    rng.shuffle(eligible_ids)

    rounds = []
    for pid in eligible_ids:
        if len(rounds) >= round_count:
            break
        path_ids = _path_for(pid)
        if path_ids is None:
            continue
        school_names_by_id = {h["school_id"]: h["school_name"] for h in by_player[pid]}
        path_names = [school_names_by_id[sid] for sid in path_ids]
        player_name = by_player[pid][0]["player_name"]
        decoy_pool = [d for d in eligible_ids if d != pid]
        rng.shuffle(decoy_pool)
        decoys = []
        for d in decoy_pool:
            if len(decoys) >= 3:
                break
            dpath = _path_for(d)
            if dpath is None or dpath == path_ids:
                continue
            decoys.append(by_player[d][0]["player_name"])
        if len(decoys) < 3:
            continue
        rounds.append({
            "path": path_names, "correct_label": player_name, "decoy_labels": decoys,
            "notes": f"Real career path (first {PATH_LENGTH} real schools by debut season) for "
                     f"{player_name} (SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED).",
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if variant == "NFL_PLAYER_CAREER_PATH_IDENTIFY":
            raw_rounds = _nfl_career_path_rounds(c, seed, round_count)
        else:  # CFB_PLAYER_CAREER_PATH_IDENTIFY
            raw_rounds = _cfb_career_path_rounds(c, seed, round_count)
    finally:
        c.close()

    shortfall_reason = None
    if len(raw_rounds) < round_count:
        shortfall_reason = (
            f"Only {len(raw_rounds)} of {round_count} requested real CAREER_PATH rounds could be built for "
            f"variant={variant!r} with 3 genuinely non-matching real decoy paths each time; exported the "
            f"maximum available rather than include an ambiguous or fabricated decoy."
        )
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_PLAYER_CAREER_PATH_IDENTIFY": "Career Path", "CFB_PLAYER_CAREER_PATH_IDENTIFY": "Career Path"}


def build_package(seed: str, variant: str, round_count: int = 5) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP22:" + hashlib.sha256(
        f"CAREER_PATH|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_label"]] + list(r["decoy_labels"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "path": r["path"], "options": options,
            # Server-private (_prefixed) until evaluate() runs -- same
            # discipline every other mechanic's package uses.
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Read the real career path, then tap whichever real player it belongs to.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
