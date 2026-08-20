"""NFL All-Pro + College composition -- "which NFL All-Pro attended this
college". See _honor_college_common.py for the real, shared logic.
Answers the real manual-failure prompt directly.
"""
from __future__ import annotations

from . import _honor_college_common as common

OUT_PATH = None
CATEGORY = "NFL All-Pro + College"
TRACK_ENTITY = True
HONOR_TABLE = "nfl_all_pro_selections"
HONOR_WHERE = "is_ap = 1"
HONOR_LABEL = "All-Pro"


def safety_check(c) -> dict:
    return {"honor_table": HONOR_TABLE, "note": "composed from already-verified NFL_ALL_PRO + ATTENDED_COLLEGE capabilities"}


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, honor_table=HONOR_TABLE, honor_where=HONOR_WHERE)


def evaluate(c, row, rng, guard):
    return common.evaluate(c, row, rng, guard, honor_table=HONOR_TABLE, honor_label=HONOR_LABEL, category=CATEGORY, entity_prefix="nfl_ap_college")


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, honor_label=HONOR_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/nfl_all_pro_college.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, honor_label=HONOR_LABEL, honor_table=HONOR_TABLE)
