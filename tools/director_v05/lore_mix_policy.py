"""Content-mix policy for Deep Lore banks.

Prevents structurally rich domains (especially draft) from dominating mixed trivia.
"""
from __future__ import annotations

from collections import Counter
import math

DRAFT_RELATIONS = {"DRAFTED_BY", "DERIVED_DRAFT VALUE", "DERIVED_BUST SCORE", "DERIVED_STEAL SCORE"}
CAREER_RELATIONS = {"ROSTERED_BY", "COACHED", "STARTED_AT", "TRANSFERRED_TO"}
HONOR_RELATIONS = {"ALL_PRO", "PRO_BOWL", "RANKED"}


def question_mix_tags(question):
    relations = {
        str(c.get("relation") or "").upper()
        for c in (question.get("clues") or [])
    }
    tags = set()
    if relations & DRAFT_RELATIONS:
        tags.add("DRAFT")
    if relations & CAREER_RELATIONS:
        tags.add("CAREER")
    if relations & HONOR_RELATIONS:
        tags.add("HONORS")
    if "SUBJECT_OF_EVENT" in relations:
        tags.add("STORY")
    if not tags:
        tags.add("OTHER")
    return tags


def enforce_mix_policy(
    questions,
    *,
    target,
    max_draft_fraction=0.25,
    min_story_fraction=0.40,
):
    """Greedily retain quality order while enforcing mixed-trivia composition."""
    target = max(1, int(target))
    # Fraction caps/floors must remain mathematically true even for tiny
    # packages. Example: target=3 with a 25% draft cap permits 0 draft
    # questions; allowing 1 would actually be 33.3% and fail certification.
    max_draft = max(0, int(math.floor(target * float(max_draft_fraction))))
    min_story = min(target, max(1, int(math.ceil(target * float(min_story_fraction)))))

    selected = []
    draft_count = 0
    story_count = 0
    deferred = []

    for q in questions:
        tags = question_mix_tags(q)
        if "DRAFT" in tags and draft_count >= max_draft:
            deferred.append(q)
            continue
        selected.append(q)
        draft_count += int("DRAFT" in tags)
        story_count += int("STORY" in tags)
        if len(selected) >= target:
            break

    # If the first pass did not reach the story floor, replace lowest-priority
    # non-story items with deferred/remaining story questions.
    if story_count < min_story:
        story_pool = [
            q for q in questions
            if "STORY" in question_mix_tags(q) and q not in selected
        ]
        replaceable = [
            i for i in range(len(selected) - 1, -1, -1)
            if "STORY" not in question_mix_tags(selected[i])
        ]
        for q, idx in zip(story_pool, replaceable):
            old_tags = question_mix_tags(selected[idx])
            new_tags = question_mix_tags(q)
            draft_count -= int("DRAFT" in old_tags)
            draft_count += int("DRAFT" in new_tags)
            if draft_count > max_draft:
                draft_count -= int("DRAFT" in new_tags)
                draft_count += int("DRAFT" in old_tags)
                continue
            selected[idx] = q
            story_count += 1
            if story_count >= min_story:
                break

    # Fill any remaining slots without violating the draft cap.
    if len(selected) < target:
        for q in deferred:
            if q in selected:
                continue
            tags = question_mix_tags(q)
            if "DRAFT" in tags and draft_count >= max_draft:
                continue
            selected.append(q)
            draft_count += int("DRAFT" in tags)
            story_count += int("STORY" in tags)
            if len(selected) >= target:
                break

    counts = Counter()
    for q in selected:
        counts.update(question_mix_tags(q))

    return {
        "selected": selected[:target],
        "mix_counts": dict(counts),
        "max_draft": max_draft,
        "min_story": min_story,
        "draft_fraction": round(counts.get("DRAFT", 0) / max(1, len(selected[:target])), 4),
        "story_fraction": round(counts.get("STORY", 0) / max(1, len(selected[:target])), 4),
    }
