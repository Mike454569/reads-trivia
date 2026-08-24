"""NFL Defensive Coordinator -- "given a real team and season, guess who
coordinated the defense". See nfl_offensive_coordinator.py's own module
docstring for the real direction-bug fix this mirrors (same shared
_coordinator_common.py, role='DEFENSIVE_COORDINATOR').
"""
from __future__ import annotations

from . import _coordinator_common as common

OUT_PATH = None
CATEGORY = "NFL Defensive Coordinators"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
ROLE = "DEFENSIVE_COORDINATOR"
SIDE_LABEL = "Defensive"


def safety_check(c) -> dict:
    return common.safety_check(c, role=ROLE)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, role=ROLE)


def evaluate(c, row, rng, guard):
    result = common.evaluate(
        c, row, rng, guard, role=ROLE, side_label=SIDE_LABEL, category=CATEGORY,
        entity_prefix="nfl_dc", direction="TEAM_TO_COACH",
    )
    return result


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, side_label=SIDE_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/nfl_defensive_coordinator.py -- NFL Defensive Coordinators.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, table_name="nfl_coordinators")
