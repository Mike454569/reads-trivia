"""All-American -> NFL Pro Bowl cross-league composition. See
_cross_league_honors_common.py for the real, shared logic. Real pool: 11
players.
"""
from __future__ import annotations

from . import _cross_league_honors_common as common

OUT_PATH = None
CATEGORY = "All-American to NFL Pro Bowl"
TRACK_ENTITY = True
HONOR_TABLE = "nfl_pro_bowl_selections"
HONOR_LABEL = "Pro Bowler"


def safety_check(c) -> dict:
    return {"honor_table": HONOR_TABLE, "note": "composed via cfb_all_america_certified + nfl_cfb_player_links (AUTO_HIGH) + nfl_pro_bowl_selections"}


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, honor_table=HONOR_TABLE)


def evaluate(c, row, rng, guard):
    return common.evaluate(c, row, rng, guard, honor_table=HONOR_TABLE, honor_label=HONOR_LABEL, category=CATEGORY, entity_prefix="aa_to_pb")


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, honor_label=HONOR_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/cfb_all_american_to_pro_bowl.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, honor_label=HONOR_LABEL, honor_table=HONOR_TABLE)
