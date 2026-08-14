"""NFL Game Box Score -- Sacks. "Which team's defense recorded more sacks in
this real game" -- genuinely distinct from HAD_MORE_YARDS (nfl_game_boxscore.py)
and from WON_GAME (a team can record more sacks and still lose). Built on the
same team_game_stats table, `def_sacks` column (the team's own defense's sack
total, not sacks its offense allowed -- see team_game_stats' column docs).

Shares its real candidate-fetch/evaluate machinery with
nfl_game_boxscore_turnovers.py/nfl_game_boxscore_penalties.py via
_boxscore_stat_common.py (see that module's docstring for why this is
extracted rather than duplicated three times).
"""
from __future__ import annotations

from collections import Counter

from . import _boxscore_stat_common as common

OUT_PATH = None
CATEGORY = "NFL Game Box Scores -- Sacks"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
MIN_SEASON = common.MIN_SEASON
MAX_SEASON = common.MAX_SEASON
STAT_COLUMN = "def_sacks"

_cache = common.make_cache()


def safety_check(c) -> dict:
    from .. import safety
    return safety.check_source_id_only_safety(
        c, "team_game_stats", REQUIRED_SOURCE_ID, where_extra=f"{STAT_COLUMN} IS NOT NULL",
    )


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, stat_column=STAT_COLUMN, cache=_cache)


def _question(franchise_a, franchise_b, season, week_label):
    return (
        f"In {week_label}, {season}, in the game between the {franchise_a['full_name']} and the "
        f"{franchise_b['full_name']}, which team's defense recorded more sacks?"
    )


def _notes(winner, loser, winner_stat, loser_stat):
    loser_possessive = loser["full_name"] + ("'" if loser["full_name"].endswith("s") else "'s")
    return f"The {winner['full_name']} recorded {winner_stat} sacks to the {loser_possessive} {loser_stat}."


def evaluate(c, row, rng, guard):
    result = common.evaluate_stat_comparison(
        c, row, rng, guard, prefer_lower=False, question_fn=_question, notes_fn=_notes,
        entity_prefix="nfl_boxscore_sacks",
    )
    if isinstance(result, str):
        return result
    result["category"] = CATEGORY
    return result


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count}-game pool ({MIN_SEASON}-{MAX_SEASON}, ties in sacks excluded); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// NFL Game Box Scores -- Sacks -- served live via the Gateway (team_game_stats.def_sacks),",
        "// not a static export.",
        f'// Deterministic seed: "{seed}".',
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, stat_label="sacks")
