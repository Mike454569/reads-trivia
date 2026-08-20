"""NFL Hall of Fame + College composition -- "which Hall of Famer attended
this college". See _honor_college_common.py for the real, shared logic.
Real pool measured directly before building: 104 real HOF players with a
resolved draft college.
"""
from __future__ import annotations

from . import _honor_college_common as common

OUT_PATH = None
CATEGORY = "NFL Hall of Fame + College"
TRACK_ENTITY = True
HONOR_TABLE = "nfl_hof_inductees"
HONOR_LABEL = "Hall of Famer"


def safety_check(c) -> dict:
    return {"honor_table": HONOR_TABLE, "note": "composed from already-verified NFL_HALL_OF_FAME + ATTENDED_COLLEGE capabilities"}


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, honor_table=HONOR_TABLE)


def evaluate(c, row, rng, guard):
    return common.evaluate(c, row, rng, guard, honor_table=HONOR_TABLE, honor_label=HONOR_LABEL, category=CATEGORY, entity_prefix="nfl_hof_college")


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, honor_label=HONOR_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return ["// Director-pipeline-only domain.", "// tools/quiz_export/adapters/nfl_hof_college.py.", f"// Deterministic seed: \"{seed}\"."]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, honor_label=HONOR_LABEL, honor_table=HONOR_TABLE)
