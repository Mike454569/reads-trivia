"""REVERSE_TRIVIA -- 75-Format Expansion (Wave 1), format #31 overall.

Real inverted-trivia: a real player's NAME is shown first, then 4
candidate "fact" statements about their real NFL Draft outcome -- only
ONE is genuinely true for that named player (their own real team/season/
pick); the other 3 are real draft facts that genuinely belong to OTHER
real players, phrased as if describing the named subject. The player
taps whichever statement is really true for the named player.

Deliberately distinct from FACT_OR_FAKE (75-Format Expansion, Wave 1):
that format shows one ALREADY-COMPLETE statement (subject baked in) and
asks a binary TRUE/FAKE judgment. REVERSE_TRIVIA separates the subject
from the candidate facts entirely -- the player sees WHO first, then
chooses WHICH of 4 real candidate facts is really theirs, a genuinely
different recall shape (recognize the one true fact among plausible real
alternates, matching the user's own spec example: "Answer: Derrick
Henry. Which statement correctly describes him?").

Reuses draft_facts (NFLVERSE_DATA, SOURCE_BACKED) directly -- same real,
already-certified table RISK_IT/WAGER_MODE/FACT_OR_FAKE already use.

CFB retrofit pass (user request: "I want all these formats to be NFL and
CFB based not just nfl... for the formats already on the app also", and
separately: "can every new format mode not be strictly about the draft").
Added CFB_SEASON_PASSING_REVERSE_TRIVIA -- deliberately NOT draft-
flavored (CFB players aren't drafted): the candidate facts are real
single-season passing stat lines ("Threw for <yards> yards and <TDs>
TDs at <School> in <season>.") from cfb_player_season_stats_real +
schools, the same shape (name shown, pick the 1 of 4 real facts that's
really theirs) with a genuinely different real domain.

Category variety pass (user feedback: "we don't need game modes based on
draft picks" -- every round of the NFL variant used to be a draft
candidate fact). NFL_DRAFT_REVERSE_TRIVIA now picks, per round, one of 3
real independent categories for BOTH the subject's true fact and all 3
decoys (kept same-category within a round so the 4 candidates stay
internally consistent/plausible as parallel facts):
  - DRAFT: unchanged, the original draft-pick fact.
  - SEASON_PASSING: a real single-season passing stat line
    (player_season_stats + canonical_players).
  - TEAM_RECORD_SEASON: a real "played for a team that went W-L that
    season" fact (canonical_roster_seasons + season_standings).
Which category a given round uses is itself seeded/deterministic.

Two variants: NFL_DRAFT_REVERSE_TRIVIA, CFB_SEASON_PASSING_REVERSE_TRIVIA.
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
MECHANIC = "REVERSE_TRIVIA"
VARIANTS = frozenset({"NFL_DRAFT_REVERSE_TRIVIA", "CFB_SEASON_PASSING_REVERSE_TRIVIA"})
_NFL_CATEGORIES = ("DRAFT", "SEASON_PASSING", "TEAM_RECORD_SEASON")


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "draft_facts": safety.check_table_wide_safety(c, "draft_facts", "NFLVERSE_DATA"),
        "cfb_player_season_stats_real": safety.check_verification_status_safety(
            c, "cfb_player_season_stats_real", "SPORTSDATAVERSE_CFB", "SOURCE_BACKED_DERIVED"),
        "player_season_stats": safety.check_table_wide_safety(c, "player_season_stats", "NFLVERSE_DATA"),
        "canonical_roster_seasons": safety.check_verification_status_safety(
            c, "canonical_roster_seasons", "NFLVERSE_DATA", "SOURCE_BACKED",
            where_extra="source_id = 'NFLVERSE_DATA'"),
        "season_standings": safety.check_table_wide_safety(c, "season_standings", "NFLVERSE_DATA"),
    }


def _fetch_pool(c) -> list[dict]:
    rows = c.execute(
        "SELECT player_key, player_name, draft_season, draft_team, draft_pick_overall FROM draft_facts "
        "WHERE verification_status='SOURCE_BACKED' AND source_id='NFLVERSE_DATA' AND draft_team IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _statement_for(row: dict) -> str:
    return f"Drafted by {row['draft_team']} in the {row['draft_season']} NFL Draft, pick #{row['draft_pick_overall']}."


def _build_round(rng, pool: list[dict]) -> dict | None:
    if len(pool) < 4:
        return None
    subject = rng.choice(pool)
    subject_key = (subject["draft_team"], subject["draft_season"], subject["draft_pick_overall"])
    decoy_pool = [r for r in pool if r["player_key"] != subject["player_key"]
                  and (r["draft_team"], r["draft_season"], r["draft_pick_overall"]) != subject_key]
    if len(decoy_pool) < 3:
        return None
    decoys = rng.sample(decoy_pool, 3)
    return {"subject_name": subject["player_name"], "correct_statement": _statement_for(subject),
            "decoy_statements": [_statement_for(d) for d in decoys],
            "notes": f"{subject['player_name']} was really drafted by {subject['draft_team']} in the "
                     f"{subject['draft_season']} NFL Draft (pick #{subject['draft_pick_overall']}) "
                     f"(NFLVERSE_DATA, SOURCE_BACKED); the other 3 real facts genuinely belong to other "
                     f"real players."}


def _fetch_pool_season_passing(c) -> list[dict]:
    rows = c.execute(
        "SELECT s.player_key, p.display_name AS player_name, s.season, s.team_code, s.pass_yards, s.pass_td "
        "FROM player_season_stats s JOIN canonical_players p ON p.player_id = s.player_key "
        "WHERE s.verification_status='SOURCE_BACKED' AND s.source_id='NFLVERSE_DATA' AND s.pass_yards > 500"
    ).fetchall()
    return [dict(r) for r in rows]


def _statement_season_passing(row: dict) -> str:
    return f"Threw for {row['pass_yards']} yards and {row['pass_td']} TDs for {row['team_code']} in {row['season']}."


def _build_round_season_passing(rng, pool: list[dict]) -> dict | None:
    if len(pool) < 4:
        return None
    subject = rng.choice(pool)
    subject_key = (subject["team_code"], subject["season"], subject["pass_yards"], subject["pass_td"])
    decoy_pool = [r for r in pool if r["player_key"] != subject["player_key"]
                  and (r["team_code"], r["season"], r["pass_yards"], r["pass_td"]) != subject_key]
    if len(decoy_pool) < 3:
        return None
    decoys = rng.sample(decoy_pool, 3)
    return {"subject_name": subject["player_name"], "correct_statement": _statement_season_passing(subject),
            "decoy_statements": [_statement_season_passing(d) for d in decoys],
            "notes": f"{subject['player_name']} really threw for {subject['pass_yards']} yards and "
                     f"{subject['pass_td']} TDs for {subject['team_code']} in {subject['season']} "
                     f"(NFLVERSE_DATA, SOURCE_BACKED); the other 3 real facts genuinely belong to other "
                     f"real players."}


def _fetch_pool_team_record(c) -> list[dict]:
    rows = c.execute(
        "SELECT rs.player_id AS player_key, p.display_name AS player_name, rs.season, rs.team_code, "
        "ss.wins, ss.losses, ss.ties FROM canonical_roster_seasons rs "
        "JOIN canonical_players p ON p.player_id = rs.player_id "
        "JOIN season_standings ss ON ss.season = rs.season AND ss.team_code = rs.team_code "
        "WHERE rs.verification_status='SOURCE_BACKED' AND rs.source_id='NFLVERSE_DATA' "
        "AND ss.verification_status='SOURCE_BACKED' AND ss.source_id='NFLVERSE_DATA' AND ss.wins IS NOT NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def _record_str_rt(row: dict) -> str:
    if row.get("ties"):
        return f"{row['wins']}-{row['losses']}-{row['ties']}"
    return f"{row['wins']}-{row['losses']}"


def _statement_team_record(row: dict) -> str:
    return f"Played for a real team that went {_record_str_rt(row)} in the {row['season']} season."


def _build_round_team_record(rng, pool: list[dict]) -> dict | None:
    if len(pool) < 4:
        return None
    subject = rng.choice(pool)
    subject_combo = (subject["team_code"], subject["season"])
    # Many teammates share one team-season -- dedupe decoys by the real
    # (team, season) COMBO, not by player, or 2+ decoys could silently
    # show the exact same real record as if they were distinct options.
    by_combo: dict = {}
    for r in pool:
        combo = (r["team_code"], r["season"])
        if combo == subject_combo:
            continue
        by_combo.setdefault(combo, r)
    if len(by_combo) < 3:
        return None
    decoy_combos = rng.sample(list(by_combo.keys()), 3)
    decoys = [by_combo[combo] for combo in decoy_combos]
    return {"subject_name": subject["player_name"], "correct_statement": _statement_team_record(subject),
            "decoy_statements": [_statement_team_record(d) for d in decoys],
            "notes": f"{subject['player_name']} really played for a team that went {_record_str_rt(subject)} "
                     f"in the {subject['season']} season (NFLVERSE_DATA, SOURCE_BACKED); the other 3 real "
                     f"facts genuinely belong to other real players."}


def _fetch_pool_cfb(c) -> list[dict]:
    rows = c.execute(
        "SELECT s.cfb_player_id, s.player_name, s.season, sc.school_name, s.passing_yards, s.passing_tds "
        "FROM cfb_player_season_stats_real s JOIN schools sc ON sc.school_id = s.school_id "
        "WHERE s.verification_status='SOURCE_BACKED_DERIVED' AND s.source_id='SPORTSDATAVERSE_CFB' "
        "AND s.passing_yards > 500"
    ).fetchall()
    return [dict(r) for r in rows]


def _statement_for_cfb(row: dict) -> str:
    return (f"Threw for {row['passing_yards']} yards and {row['passing_tds']} TDs at {row['school_name']} "
            f"in {row['season']}.")


def _build_round_cfb(rng, pool: list[dict]) -> dict | None:
    if len(pool) < 4:
        return None
    subject = rng.choice(pool)
    subject_key = (subject["school_name"], subject["season"], subject["passing_yards"], subject["passing_tds"])
    decoy_pool = [r for r in pool if r["cfb_player_id"] != subject["cfb_player_id"]
                  and (r["school_name"], r["season"], r["passing_yards"], r["passing_tds"]) != subject_key]
    if len(decoy_pool) < 3:
        return None
    decoys = rng.sample(decoy_pool, 3)
    return {"subject_name": subject["player_name"], "correct_statement": _statement_for_cfb(subject),
            "decoy_statements": [_statement_for_cfb(d) for d in decoys],
            "notes": f"{subject['player_name']} really threw for {subject['passing_yards']} yards and "
                     f"{subject['passing_tds']} TDs at {subject['school_name']} in {subject['season']} "
                     f"(SPORTSDATAVERSE_CFB, SOURCE_BACKED_DERIVED); the other 3 real facts genuinely belong "
                     f"to other real players."}


def generate_rounds(seed: str, variant: str, round_count: int = 8) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    is_cfb = variant == "CFB_SEASON_PASSING_REVERSE_TRIVIA"
    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        if is_cfb:
            pool = _fetch_pool_cfb(c)
        else:
            draft_pool = _fetch_pool(c)
            passing_pool = _fetch_pool_season_passing(c)
            record_pool = _fetch_pool_team_record(c)
    finally:
        c.close()

    rounds = []
    for i in range(round_count):
        if is_cfb:
            rng = engine_bootstrap.seeded(f"{seed}-rt-r{i}")
            r = _build_round_cfb(rng, pool)
        else:
            # Category variety pass: which real, independent category a
            # round draws from (subject + all 3 decoys, kept same-category
            # for internal consistency) is itself seeded/deterministic,
            # tried in a real fallback order if the chosen category can't
            # build a round rather than silently dropping it.
            cat_rng = engine_bootstrap.seeded(f"{seed}-rt-cat-{i}")
            categories = list(_NFL_CATEGORIES)
            cat_rng.shuffle(categories)
            r = None
            for category in categories:
                rng = engine_bootstrap.seeded(f"{seed}-rt-r{i}-{category}")
                if category == "DRAFT":
                    r = _build_round(rng, draft_pool)
                elif category == "SEASON_PASSING":
                    r = _build_round_season_passing(rng, passing_pool)
                else:
                    r = _build_round_team_record(rng, record_pool)
                if r is not None:
                    break
        if r is None:
            continue
        rounds.append(r)

    shortfall_reason = None
    if len(rounds) < round_count:
        shortfall_reason = (
            f"Only {len(rounds)} of {round_count} requested real REVERSE_TRIVIA rounds could be built with "
            f"a real, decoy-complete candidate set; exported the maximum available rather than include a "
            f"fabricated statement."
        )
    return {"rounds": rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_DRAFT_REVERSE_TRIVIA": "Reverse Trivia", "CFB_SEASON_PASSING_REVERSE_TRIVIA": "Reverse Trivia (CFB)"}


def build_package(seed: str, variant: str, round_count: int = 8) -> dict:
    result = generate_rounds(seed, variant, round_count=round_count)
    package_id = "GGP33:" + hashlib.sha256(
        f"REVERSE_TRIVIA|{variant}|{seed}|{round_count}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"])

    rounds = []
    for i, r in enumerate(result["rounds"]):
        candidates = [r["correct_statement"]] + list(r["decoy_statements"])
        order = list(range(4))
        engine_bootstrap.seeded(f"{seed}-rt-shuffle-{i}").shuffle(order)
        item_ids = ["A", "B", "C", "D"]
        options = [{"item_id": item_ids[pos], "label": candidates[src]} for pos, src in enumerate(order)]
        correct_pos = order.index(0)
        rounds.append({
            "round_index": i, "subject_name": r["subject_name"], "options": options,
            "_answer_item_id": item_ids[correct_pos], "_notes": r["notes"],
        })

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "game_title": _GAME_TITLES[variant],
        "game_instructions": "A real player is named -- tap the 1 of 4 real statements that's actually "
                              "true about them.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
