"""All-American -> NFL All-Pro cross-league composition. See
_cross_league_honors_common.py for the real, shared logic. Answers the
real manual-failure prompt directly. Real pool: 4 players.
"""
from __future__ import annotations

from . import _cross_league_honors_common as common

OUT_PATH = None
CATEGORY = "All-American to NFL All-Pro"
TRACK_ENTITY = True
HONOR_TABLE = "nfl_all_pro_selections"
HONOR_LABEL = "All-Pro"


def safety_check(c) -> dict:
    return {"honor_table": HONOR_TABLE, "note": "composed via cfb_all_america_certified + nfl_cfb_player_links (AUTO_HIGH) + nfl_all_pro_selections"}


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, honor_table=HONOR_TABLE)


def evaluate(c, row, rng, guard):
    return common.evaluate(c, row, rng, guard, honor_table=HONOR_TABLE, honor_label=HONOR_LABEL, category=CATEGORY, entity_prefix="aa_to_ap")


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, honor_label=HONOR_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/cfb_all_american_to_all_pro.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, honor_label=HONOR_LABEL, honor_table=HONOR_TABLE)
