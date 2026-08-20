"""CFB game rushing leader -- objective "top offensive performer" (rushing
category). See _game_leader_common.py for the real, shared logic.
"""
from __future__ import annotations

from .. import safety as safety_mod
from . import _game_leader_common as common

OUT_PATH = None
CATEGORY = "CFB Game Rushing Leader"
TRACK_ENTITY = True
TABLE = "cfb_player_game_stats_real"
SOURCE_ID = "SPORTSDATAVERSE_CFB"
VERIFICATION_STATUS = "SOURCE_BACKED_DERIVED"
GAME_ID_COLUMN = "game_id"
TEAM_COLUMN = "school_id"
NAME_COLUMN = "player_name"
STAT_COLUMN = "rushing_yards"
ATTEMPT_COLUMN = "rush_attempts"
STAT_LABEL = "rushing yards"
MIN_SEASON = 2014
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return common.safety_check(c, safety_mod=safety_mod, table=TABLE, source_id=SOURCE_ID,
                                verification_status=VERIFICATION_STATUS, attempt_column=ATTEMPT_COLUMN)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(
        c, seed, table=TABLE, game_id_column=GAME_ID_COLUMN, team_column=TEAM_COLUMN,
        name_column=NAME_COLUMN, stat_column=STAT_COLUMN, attempt_column=ATTEMPT_COLUMN,
        source_id=SOURCE_ID, verification_status=VERIFICATION_STATUS,
    )


def evaluate(c, row, rng, guard):
    return common.evaluate(
        c, row, rng, guard, table=TABLE, game_id_column=GAME_ID_COLUMN, team_column=TEAM_COLUMN,
        name_column=NAME_COLUMN, stat_column=STAT_COLUMN, source_id=SOURCE_ID,
        verification_status=VERIFICATION_STATUS, stat_label=STAT_LABEL, category=CATEGORY,
        entity_prefix="cfb_rush_ldr", min_season=MIN_SEASON, max_season=MAX_SEASON,
    )


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, stat_label=STAT_LABEL, min_season=MIN_SEASON, max_season=MAX_SEASON)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/cfb_rushing_leader.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, stat_label=STAT_LABEL, table=TABLE)
