"""Reusable, mode-aware distractor selection.

Real bug found by actually playing every live generated mode, not assumed
from reading QA code alone: `cfb_heisman.py`'s distractor pool was ALL 805
real schools in the `schools` table, sampled uniformly at random. A famous
Heisman winner (Ohio State, Notre Dame, LSU...) ended up surrounded by
random Division-III/NAIA names ("Presentation", "Mars Hill", "Nichols
College") that no realistic distractor for that question would ever be --
the correct answer was trivially obvious by elimination, without the player
needing to know anything about football. Draft/Championship/Lineup do NOT
have this problem: their distractor pools (`teams_active_in_season()`, the
closed 5-outcome playoff vocabulary) are already inherently plausible --
every option is a real NFL team that was genuinely active that season, or a
real possible playoff outcome, so there is no "obviously wrong" tier to
begin with.

`sample_plausible()` is the one shared mechanism every adapter's distractor
selection should go through: prefer a curated, genuinely-similar-category
pool (e.g. "other real Heisman-winning schools") and only fall back to a
wider universe if that pool doesn't have enough real, distinct options --
never the other way around, and never a fabricated entity either way.
"""
from __future__ import annotations

import random


def sample_plausible(rng: random.Random, correct_id, plausible_pool: dict, full_pool: dict, k: int = 3):
    """Returns {id: label} for k distractors, or None if fewer than k real,
    distinct options exist across BOTH pools combined (never pads with a
    fabricated entity).

    `plausible_pool` and `full_pool` are both {id: label} dicts of REAL
    entities -- `plausible_pool` should be a genuine subset of `full_pool`
    representing "things in the same meaningful category as the correct
    answer" (e.g. other schools that have produced a Heisman winner, other
    teams active the same season). Distractors are drawn from
    `plausible_pool` first; only if it has fewer than k eligible entries
    (excluding the correct answer) does this top up from the rest of
    `full_pool` -- so a plausible option is never skipped in favor of a
    less plausible one just because of sampling order.
    """
    plausible = dict(plausible_pool)
    plausible.pop(correct_id, None)

    if len(plausible) >= k:
        chosen_ids = rng.sample(sorted(plausible.keys()), k)
        return {cid: plausible[cid] for cid in chosen_ids}

    chosen_ids = sorted(plausible.keys())
    remaining_pool = dict(full_pool)
    remaining_pool.pop(correct_id, None)
    for cid in chosen_ids:
        remaining_pool.pop(cid, None)
    needed = k - len(chosen_ids)
    if len(remaining_pool) < needed:
        return None
    chosen_ids += rng.sample(sorted(remaining_pool.keys()), needed)
    return {cid: (plausible_pool.get(cid) or full_pool.get(cid)) for cid in chosen_ids}
