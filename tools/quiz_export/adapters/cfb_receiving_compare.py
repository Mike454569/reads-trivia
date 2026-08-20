"""CFB same-week receiving yards comparison. See
_cfb_stat_compare_common.py for the real, shared logic this file
parameterizes with receiving_yards/receptions.
"""
from __future__ import annotations

from . import _cfb_stat_compare_common as common

OUT_PATH = None
CATEGORY = "CFB Receiving Comparisons"
REQUIRED_SOURCE_ID = common.REQUIRED_SOURCE_ID
TRACK_ENTITY = True
STAT_COLUMN = "receiving_yards"
ATTEMPT_COLUMN = "receptions"
STAT_LABEL = "receiving yardage"


def safety_check(c) -> dict:
    return common.safety_check(c, stat_column=STAT_COLUMN, attempt_column=ATTEMPT_COLUMN)


def fetch_ordered_candidates(c, seed: str):
    return common.fetch_ordered_candidates(c, seed, stat_column=STAT_COLUMN, attempt_column=ATTEMPT_COLUMN)


def evaluate(c, row, rng, guard):
    return common.evaluate(
        c, row, rng, guard, stat_column=STAT_COLUMN, attempt_column=ATTEMPT_COLUMN, stat_label=STAT_LABEL,
        category=CATEGORY, entity_prefix="cfb_rec_cmp",
    )


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return common.shortfall_reason(accepted_count, considered_count, target_count, stat_label=STAT_LABEL)


def extra_funnel_fields(accepted, exported) -> dict:
    return common.extra_funnel_fields(accepted, exported)


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_receiving_compare.py -- CFB Receiving Comparisons.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    return common.human_review_context(record, stat_label=STAT_LABEL)
