"""MYSTERY_ROSTER -- 75-Format Expansion (Wave 1), format #33 overall.

Real progressive team-season identification: each round targets one real
NFL team-season (e.g. "2007 New England Patriots") and reveals up to 4
real clues about it, one at a time, on request -- the real season record,
the real starting QB, the real top skill/defensive player by AV
(approximate value), and that player's real years of NFL experience
entering that season (canonical_roster_seasons.jersey_number is present
in the schema but entirely unpopulated in this Engine's real data --
confirmed live before shipping -- so years_experience is used instead,
never a field this Engine cannot actually back with real values). At any point
the player may instead submit a guess (4 real candidate team-seasons,
the correct one plus 3 real decoys). Fewer real reveals before a correct
guess earns more points (4 points at 1 clue down to 1 point at 4 clues);
an incorrect guess ends the round with 0 points.

Reuses tools.quiz_export.adapters.draft.resolve_franchise (already
proven across HIGHER_LOWER_STREAK and other capabilities) for real
franchise full names, season_standings for the real record, and
canonical_roster_seasons/canonical_players for the real roster clues.

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also").
Added CFB_TEAM_SEASON_MYSTERY_ROSTER on cfb_standings (FBS only, same
real classification='fbs' filter higher_lower.py's own _cfb_items already
certified) + cfb_player_season_stats_real + cfb_roster_seasons_real.
Two real, disclosed substitutions -- CFB has no starts/AV-equivalent
columns at all: the "starting QB" clue uses the real season passing-
yards LEADER at that school (rs.position='QB'), and the "top player"
clue uses the real season-leading rusher+receiver by combined real
scrimmage yards (never invented, never claiming to BE approximate
value). The 4th clue uses real roster class_year (1-6, mapped to
Freshman..6th-year Senior) as the real substitute for years_experience
-- rows with a null or out-of-range class_year (a real, disclosed data
quality gap for a small number of rows) are excluded rather than guessed.

Two variants: NFL_TEAM_SEASON_MYSTERY_ROSTER, CFB_TEAM_SEASON_MYSTERY_ROSTER.
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
MECHANIC = "MYSTERY_ROSTER"
VARIANTS = frozenset({"NFL_TEAM_SEASON_MYSTERY_ROSTER", "CFB_TEAM_SEASON_MYSTERY_ROSTER"})
MAX_CLUES = 4
_CLUE_POINTS = {1: 4, 2: 3, 3: 2, 4: 1}
_CFB_CLASS_YEAR_LABELS = {
    "1": "Freshman", "2": "Sophomore", "3": "Junior", "4": "Senior",
    "5": "5th-year Senior", "6": "6th-year Senior",
}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'",
        ),
        "cfb_standings": safety.check_table_wide_safety(c, "cfb_standings", "CFBD_API_LIVE"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
        "cfb_roster_seasons_real": safety.check_table_wide_safety(
            c, "cfb_roster_seasons_real", ["SPORTSDATAVERSE_CFB", "READS_MASTER_KNOWLEDGE_FEED_2026_09"]),
    }


def _fetch_team_seasons(c) -> list[dict]:
    rows = c.execute(
        "SELECT season, team_code, wins, losses, ties FROM season_standings "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' "
        "AND wins IS NOT NULL AND losses IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_qb(c, season: int, team_code: str) -> dict | None:
    row = c.execute(
        "SELECT p.display_name, rs.starts FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA' "
        "AND rs.season=? AND rs.team_code=? AND rs.position='QB' AND rs.starts IS NOT NULL "
        "ORDER BY rs.starts DESC LIMIT 1",
        (season, team_code),
    ).fetchone()
    return dict(row) if row else None


def _fetch_top_player(c, season: int, team_code: str, exclude_name: str | None) -> dict | None:
    row = c.execute(
        "SELECT p.display_name, rs.position, rs.years_experience, rs.av FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA' "
        "AND rs.season=? AND rs.team_code=? AND rs.av IS NOT NULL AND rs.years_experience IS NOT NULL "
        "AND p.display_name != ? "
        "ORDER BY rs.av DESC LIMIT 1",
        (season, team_code, exclude_name or ""),
    ).fetchone()
    return dict(row) if row else None


def _record_str(row: dict) -> str:
    if row.get("ties"):
        return f"{row['wins']}-{row['losses']}-{row['ties']}"
    return f"{row['wins']}-{row['losses']}"


def _build_round(c, rng, pool: list[dict]) -> dict | None:
    candidates = list(pool)
    rng.shuffle(candidates)
    for row in candidates:
        season, team_code = row["season"], row["team_code"]
        fr, err = resolve_franchise(c, team_code, season)
        if err or fr is None:
            continue
        qb = _fetch_qb(c, season, team_code)
        if qb is None:
            continue
        top = _fetch_top_player(c, season, team_code, qb["display_name"])
        if top is None:
            continue
        label = f"{season} {fr['full_name']}"
        clues = [
            f"This real team went {_record_str(row)} that season.",
            f"Their real starting QB was {qb['display_name']}.",
            f"Their real top player by AV (approximate value) was {top['display_name']} ({top['position']}).",
            f"That player had {top['years_experience']} real years of NFL experience that season.",
        ]
        decoy_pool = [r for r in pool if (r["season"], r["team_code"]) != (season, team_code)]
        if len(decoy_pool) < 3:
            continue
        decoys = []
        seen_labels = {label}
        for d in rng.sample(decoy_pool, min(len(decoy_pool), 12)):
            dfr, derr = resolve_franchise(c, d["team_code"], d["season"])
            if derr or dfr is None:
                continue
            dlabel = f"{d['season']} {dfr['full_name']}"
            if dlabel in seen_labels:
                continue
            seen_labels.add(dlabel)
            decoys.append(dlabel)
            if len(decoys) >= 3:
                break
        if len(decoys) < 3:
            continue
        return {"label": label, "clues": clues, "decoy_labels": decoys,
                "notes": f"This was really the {label} ({_record_str(row)}), real starting QB "
                         f"{qb['display_name']}, real top player {top['display_name']} "
                         f"(NFLVERSE_DATA, SOURCE_BACKED)."}
    return None


def _fetch_team_seasons_cfb(c) -> list[dict]:
    rows = c.execute(
        "SELECT season, school_id, school_name_raw, total_wins AS wins, total_losses AS losses, "
        "total_ties AS ties FROM cfb_standings WHERE verification_status='SOURCE_BACKED' "
        "AND classification='fbs' AND total_wins IS NOT NULL AND school_id IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _fetch_qb_cfb(c, season: int, school_id: str) -> dict | None:
    row = c.execute(
        "SELECT s.player_name, s.passing_yards FROM cfb_player_season_stats_real s "
        "JOIN cfb_roster_seasons_real rs ON rs.season=s.season AND rs.school_id=s.school_id "
        "AND rs.cfb_player_id=s.cfb_player_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.source_id='SPORTSDATAVERSE_CFB' "
        "AND s.season=? AND s.school_id=? AND rs.position='QB' AND s.passing_yards IS NOT NULL "
        "ORDER BY s.passing_yards DESC LIMIT 1",
        (season, school_id),
    ).fetchone()
    return dict(row) if row else None


def _fetch_top_player_cfb(c, season: int, school_id: str, exclude_name: str | None) -> dict | None:
    row = c.execute(
        "SELECT s.player_name, rs.position, rs.class_year, (s.rushing_yards + s.receiving_yards) AS scrim_yards "
        "FROM cfb_player_season_stats_real s "
        "JOIN cfb_roster_seasons_real rs ON rs.season=s.season AND rs.school_id=s.school_id "
        "AND rs.cfb_player_id=s.cfb_player_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.source_id='SPORTSDATAVERSE_CFB' "
        "AND s.season=? AND s.school_id=? AND s.player_name != ? "
        "AND rs.class_year IN ('1','2','3','4','5','6') AND (s.rushing_yards + s.receiving_yards) > 0 "
        "ORDER BY scrim_yards DESC LIMIT 1",
        (season, school_id, exclude_name or ""),
    ).fetchone()
    return dict(row) if row else None


def _build_round_cfb(c, rng, pool: list[dict]) -> dict | None:
    candidates = list(pool)
    rng.shuffle(candidates)
    for row in candidates:
        season, school_id = row["season"], row["school_id"]
        qb = _fetch_qb_cfb(c, season, school_id)
        if qb is None:
            continue
        top = _fetch_top_player_cfb(c, season, school_id, qb["player_name"])
        if top is None:
            continue
        label = f"{season} {row['school_name_raw']}"
        clues = [
            f"This real team went {_record_str(row)} that season.",
            f"Their real leading passer was {qb['player_name']} ({qb['passing_yards']} passing yards).",
            f"Their real leading rusher+receiver by combined yards was {top['player_name']} "
            f"({top['position']}, {top['scrim_yards']} yards).",
            f"That player was really a real {_CFB_CLASS_YEAR_LABELS[top['class_year']]} that season.",
        ]
        decoy_pool = [r for r in pool if (r["season"], r["school_id"]) != (season, school_id)]
        if len(decoy_pool) < 3:
            continue
        decoys = []
        seen_labels = {label}
        for d in rng.sample(decoy_pool, min(len(decoy_pool), 12)):
            dlabel = f"{d['season']} {d['school_name_raw']}"
            if dlabel in seen_labels:
                continue
            seen_labels.add(dlabel)
            decoys.append(dlabel)
            if len(decoys) >= 3:
                break
        if len(decoys) < 3:
            continue
        return {"label": label, "clues": clues, "decoy_labels": decoys,
                "notes": f"This was really the {label} ({_record_str(row)}), real leading passer "
                         f"{qb['player_name']}, real leading rusher+receiver {top['player_name']} "
                         f"(SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED)."}
    return None


def generate_rounds(seed: str, variant: str, round_count: int = 6) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    is_cfb = variant == "CFB_TEAM_SEASON_MYSTERY_ROSTER"
    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        pool = _fetch_team_seasons_cfb(c) if is_cfb else _fetch_team_seasons(c)
        rounds = []
        for i in range(round_count):
            rng = engine_bootstrap.seeded(f"{seed}-mr-r{i}")
            r = _build_round_cfb(c, rng, pool) if is_cfb else _build_round(c, rng, pool)
            if r is None:
                continue
            rounds.append(r)
    finally:
        c.close()

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real MYSTERY_ROSTER rounds could be built with "
            f"a real, decoy-complete clue set (real QB + real top AV player both required); exported the "
            f"maximum available rather than include a fabricated clue."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_TEAM_SEASON_MYSTERY_ROSTER": "Mystery Roster", "CFB_TEAM_SEASON_MYSTERY_ROSTER": "Mystery Roster (CFB)"}


def build_package(seed: str, variant: str, round_count: int = 6) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP35:" + hashlib.sha256(
        f"MYSTERY_ROSTER|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["label"]] + list(r["decoy_labels"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-mr-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "clues": r["clues"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "Reveal real clues about a mystery real NFL team-season one at a time, or "
                              "guess at any point -- fewer reveals before a correct guess earns more points.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds), "max_clues": MAX_CLUES,
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
