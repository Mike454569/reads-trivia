"""NFL Offensive Coordinator -- "which team did this coach coordinate the
offense for". See _coordinator_common.py for the real, shared logic this
file just parameterizes with role='OFFENSIVE_COORDINATOR'.
"""
from __future__ import annotations

from . import _coordinator_common as common

OUT_PATH = None
CATEGORY = "NFL Offensive Coordinators"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
ROLE = "OFFENSIVE_COORDINATOR"
SIDE_LABEL = "Offensive"


def safety_check(c) -> dict:
    return common.safety_check(c, role=ROLE)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, role=ROLE)


def evaluate(c, row, rng, guard):
    result = common.evaluate(
        c, row, rng, guard, role=ROLE, side_label=SIDE_LABEL, category=CATEGORY,
        entity_prefix="nfl_oc",
    )
    return result


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, side_label=SIDE_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_offensive_coordinator.py -- NFL Offensive Coordinators.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, table_name="nfl_coordinators")
