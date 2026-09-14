"""GUESS_THE_SEASON -- 40-Format Expansion Part 2.

Reveals several real clues about one real NFL season -- the Super Bowl
champion plus real season awards (AP MVP/OPOY/DPOY/OROY/DROY, Super Bowl
MVP) -- and the player guesses the real season/year they all describe.

Real data, both from `nfl_championship_events` (60 rows, 1966-2025) and
`nfl_season_awards` (369 rows): both tables are WIKIPEDIA_STRUCTURED_
SECONDARY tier, not NFLVERSE_DATA-primary -- honestly labeled as a real
secondary source rather than silently treated as equivalent to the
primary-tier tables elsewhere in this Engine (same discipline
cfb_player_season_stats_real's own SOURCE_BACKED_DERIVED status already
established for a different real secondary-tier table).

Restricted to seasons where BOTH a resolved (team-identified) Super Bowl
champion AND at least 2 real season awards exist (24 of 60 real seasons,
confirmed live) -- a season missing either is skipped entirely, never
padded with an invented or unresolved clue. The champion clue is always
the base clue (real regardless of how many teams have won multiple times,
since it's still a real, true fact about that season); award clues layer
on top in a fixed, non-randomized priority order (see _AWARD_PRIORITY)
so a given season's EASY round is always a superset of its own MEDIUM/HARD
clues, never a differently-selected set -- difficulty is genuinely "how
much of the same real evidence you get," not "different evidence."

Answer format: the real season year as a 4-digit string (e.g. "2019"),
matching how a real player would naturally type a year guess -- compared
case-/whitespace-insensitively, same normalization style
tools.director_v04.player_from_clues already uses for its own guesses.
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
MECHANIC = "GUESS_THE_SEASON"
VARIANTS = frozenset({"NFL_SUPER_BOWL_SEASON"})

_AWARD_LABELS = {
    "SB_MVP": "the Super Bowl MVP",
    "AP_MVP": "the AP Most Valuable Player",
    "AP_OPOY": "the AP Offensive Player of the Year",
    "AP_DPOY": "the AP Defensive Player of the Year",
    "AP_OROY": "the AP Offensive Rookie of the Year",
    "AP_DROY": "the AP Defensive Rookie of the Year",
}
# Fixed reveal order (never randomized) so a season's EASY clue set is
# always a strict superset of its own MEDIUM/HARD sets -- see module
# docstring. Not an ambiguity ranking (a champion clue alone can still be
# ambiguous for a team that's won multiple times) -- difficulty here means
# "how much real corroborating evidence," which is still a fair, real
# operationalization of "harder clues" even without per-team ambiguity
# scoring.
_AWARD_PRIORITY = ["SB_MVP", "AP_MVP", "AP_OPOY", "AP_DPOY", "AP_OROY", "AP_DROY"]
_DIFFICULTY_CLUE_COUNTS = {"EASY": 4, "MEDIUM": 3, "HARD": 2}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "nfl_championship_events": safety.check_verification_status_safety(
            c, "nfl_championship_events", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
        ),
        "nfl_season_awards": safety.check_verification_status_safety(
            c, "nfl_season_awards", "WIKIPEDIA_STRUCTURED", "WIKIPEDIA_STRUCTURED_SECONDARY",
        ),
    }


def _nfl_super_bowl_season_rounds(c, seed: str, round_count: int, difficulty: str) -> list[dict]:
    clue_n = _DIFFICULTY_CLUE_COUNTS[difficulty]
    champ_rows = c.execute(
        "SELECT season, winner_name_raw FROM nfl_championship_events WHERE winner_team_code IS NOT NULL"
    ).fetchall()

    eligible = []
    for r in champ_rows:
        season = r["season"]
        award_rows = c.execute(
            "SELECT award_type, player_name_raw FROM nfl_season_awards "
            "WHERE season = ? AND player_name_raw IS NOT NULL", (season,),
        ).fetchall()
        # SB_MVP excluded here on purpose -- an unshifted row for this same
        # season would be the WRONG player (see the shifted lookup below,
        # which is the only correct source for SB_MVP). Never let the
        # general query's coincidentally-matching row silently win.
        award_map = {a["award_type"]: a["player_name_raw"]
                     for a in award_rows if a["award_type"] in _AWARD_LABELS and a["award_type"] != "SB_MVP"}
        # Confirmed real off-by-one, SB_MVP only: nfl_season_awards stores
        # every OTHER award type under the season it represents (AP_MVP for
        # season=2007 really is Tom Brady's 2007 MVP season -- matches
        # nfl_championship_events' own convention), but SB_MVP rows are
        # stored under season+1 -- the calendar year the Super Bowl game was
        # actually PLAYED, not the season it caps. Verified against real
        # history before writing this fix (not assumed): season=2020 in the
        # raw table holds Patrick Mahomes (real SB LIV MVP, Feb 2020, capping
        # the 2019 season) and season=2021 holds Tom Brady (real SB LV MVP,
        # Feb 2021, capping the 2020 season) -- both one year later than the
        # season they actually belong to. Corrected here rather than in the
        # shared table itself, which is out of scope for adding one new
        # game format; every OTHER award type is unaffected and queried
        # normally above.
        sb_mvp_row = c.execute(
            "SELECT player_name_raw FROM nfl_season_awards "
            "WHERE season = ? AND award_type = 'SB_MVP' AND player_name_raw IS NOT NULL", (season + 1,),
        ).fetchone()
        if sb_mvp_row:
            award_map["SB_MVP"] = sb_mvp_row["player_name_raw"]
        if len(award_map) < 2:
            continue  # not enough real corroborating evidence for this season -- skip, never pad
        clue_texts = ["The Super Bowl champion that season was the " + r["winner_name_raw"] + "."]
        for award_type in _AWARD_PRIORITY:
            if award_type in award_map:
                clue_texts.append(f"{_AWARD_LABELS[award_type]} was {award_map[award_type]}.")
        eligible.append({"season": r["season"], "clue_texts": clue_texts})

    rng = engine_bootstrap.seeded(seed)
    eligible.sort(key=lambda e: e["season"])
    rng.shuffle(eligible)

    rounds = []
    for item in eligible:
        if len(rounds) >= round_count:
            break
        revealed = item["clue_texts"][:clue_n]
        if len(revealed) < 2:
            continue  # this season doesn't honestly have enough clues at this difficulty -- skip
        rounds.append({
            "season": item["season"],
            "clues": [{"clue_index": i, "display_text": t} for i, t in enumerate(revealed)],
        })
    return rounds


def generate_rounds(seed: str, variant: str, round_count: int = 5, difficulty: str = "MEDIUM") -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    if difficulty not in _DIFFICULTY_CLUE_COUNTS:
        raise ValueError(f"difficulty must be one of {sorted(_DIFFICULTY_CLUE_COUNTS)}, got {difficulty!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        raw_rounds = _nfl_super_bowl_season_rounds(c, seed, round_count, difficulty)
    finally:
        c.close()

    shortfall_reason = None
    if not raw_rounds:
        shortfall_reason = f"No real NFL seasons have enough real, resolved clues at difficulty={difficulty!r}."
    return {"rounds": raw_rounds, "safety": safety_result, "shortfall_reason": shortfall_reason}


_GAME_TITLES = {"NFL_SUPER_BOWL_SEASON": "Guess the Season"}


def build_package(seed: str, variant: str, round_count: int = 5, difficulty: str = "MEDIUM") -> dict:
    result = generate_rounds(seed, variant, round_count=round_count, difficulty=difficulty)
    package_id = "GGP17:" + hashlib.sha256(
        f"GUESS_THE_SEASON|{variant}|{seed}|{round_count}|{difficulty}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    valid = bool(result["rounds"]) and not result["shortfall_reason"]

    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "difficulty": difficulty,
        "game_title": _GAME_TITLES[variant],
        "game_instructions": "Read the real clues, then guess the real NFL season (e.g. 2019) they all describe.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if valid else "FAILED",
        # Each round's real answer (the season year) is kept server-private
        # under _answer -- never sent to the client until evaluate() runs,
        # same discipline every other mechanic's package uses.
        "rounds": [{"round_index": i, "clues": r["clues"], "_answer": str(r["season"])}
                   for i, r in enumerate(result["rounds"])],
        "round_count": len(result["rounds"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
