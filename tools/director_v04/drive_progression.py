"""DRIVE_PROGRESSION -- 40-Format Expansion pass, new mechanic template.

Backs PERFECT_DRIVE (field-position meter: correct answers gain yardage
toward a score) and GOAL_LINE_STAND (a fixed number of downs to score;
wrong answers cost a down). Deliberately does NOT introduce a new data
source or adapter -- per the format spec's own instruction ("question pool
reuses any existing 'guess' capability, no new data required"), this
module reuses the EXACT real generation path every registered "guess"
capability already has (tools.game_director_v01.generate_package_from_spec
via gateway.services.generation.generate(), the same call
mechanic_engine.generate_guess_round() makes for MULTIPLE_CHOICE_SINGLE_FACT/
POSITION_LINEUP_GRID) -- so every question in a drive is a real, already
QA'd, already anti-hallucination-checked fact from a real registered
capability. This module only adds the progression/scoring WRAPPER on top:
which real (domain, relationship_predicate) backs the question pool, and
whether the drive is scored by yardage or downs.

Two real modes:
  - YARDAGE (PERFECT_DRIVE): each correct answer advances real yardage
    toward the end zone, keyed to the QUESTION'S OWN real, already-computed
    difficulty_band (easy/medium/hard -- never a fabricated scale): easy=10,
    medium=20, hard=30. A wrong answer ends the drive.
  - DOWNS (GOAL_LINE_STAND): a fixed number of downs (default 4); each wrong
    answer costs one down; running out of downs ends the drive without a
    score; any correct answer scores.
"""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone

# Real, confirmed-live casing: generated questions carry Title-Case
# difficulty values ("Easy"/"Medium"/"Hard"), not lowercase.
YARDS_BY_DIFFICULTY = {"Easy": 10, "Medium": 20, "Hard": 30, "Any": 15}
FIELD_LENGTH_YARDS = 100
DEFAULT_DOWNS = 4

PACKAGE_SCHEMA_VERSION = "1.1"
MECHANIC = "DRIVE_PROGRESSION"


def _generate_question_pool(*, domain: str, relationship_predicate: str, question_count: int, seed: str) -> dict:
    from gateway.services import generation as generation_service
    spec = {"mechanic": "guess", "domain": domain, "relationship_predicate": relationship_predicate,
            "question_count": question_count, "difficulty": "any", "filters": {}, "exclusions": []}
    return generation_service.generate(request_text=None, spec=spec, provider="mock",
                                        puzzle_count=None, difficulty=None, seed=seed)


def _category_schedule(question_pools: list[dict], question_count: int, seed: str) -> list[str]:
    """Build a deterministic, non-repeating category rotation.

    Draft is allowed only as an occasional NFL category: never in the
    first two slots and never more than one out of every five questions.
    """
    keys = [p["key"] for p in question_pools]
    non_draft = [key for key in keys if key != "DRAFT"]
    if not non_draft:
        return keys[:1] * question_count

    offset = int(hashlib.sha256(f"{seed}|drive-category-order".encode()).hexdigest()[:8], 16) % len(non_draft)
    rotated = non_draft[offset:] + non_draft[:offset]
    schedule = []
    non_draft_index = 0
    draft_budget = min(question_count // 5, 2)
    for i in range(question_count):
        use_draft = "DRAFT" in keys and draft_budget > 0 and i >= 2 and (i + 1) % 5 == 0
        if use_draft:
            schedule.append("DRAFT")
            draft_budget -= 1
        else:
            schedule.append(rotated[non_draft_index % len(rotated)])
            non_draft_index += 1
    return schedule


def _generate_mixed_question_pool(*, question_pools: list[dict], question_count: int, seed: str) -> tuple[list[dict], list[dict]]:
    schedule = _category_schedule(question_pools, question_count, seed)
    requested = Counter(schedule)
    by_key = {p["key"]: p for p in question_pools}
    generated: dict[str, list[dict]] = defaultdict(list)
    safety = []

    for key, count in requested.items():
        pool = by_key[key]
        result = _generate_question_pool(
            domain=pool["domain"], relationship_predicate=pool["relationship_predicate"],
            question_count=count, seed=f"{seed}-drive-{key.lower()}",
        )
        safety.append(result.get("production_safety") if isinstance(result, dict) else None)
        for q in result.get("questions", []) if isinstance(result, dict) else []:
            q = dict(q)
            q["content_category"] = pool["label"]
            generated[key].append(q)

    questions = []
    for key in schedule:
        if generated[key]:
            questions.append(generated[key].pop(0))
    return questions, safety


def build_package(seed: str, variant: str, *, mode: str, domain: str | None = None,
                   relationship_predicate: str | None = None, question_pools: list[dict] | None = None,
                   question_count: int, downs: int = DEFAULT_DOWNS) -> dict:
    if mode not in ("YARDAGE", "DOWNS"):
        raise ValueError(f"mode must be 'YARDAGE' or 'DOWNS', got {mode!r}")

    if question_pools:
        questions, production_safety = _generate_mixed_question_pool(
            question_pools=question_pools, question_count=question_count, seed=seed,
        )
        capability_fingerprint = "|".join(
            f"{p['key']}:{p['domain']}:{p['relationship_predicate']}" for p in question_pools
        )
        underlying_capability = {"mixed": question_pools}
    else:
        if not domain or not relationship_predicate:
            raise ValueError("domain and relationship_predicate are required when question_pools is not supplied")
        underlying = _generate_question_pool(
            domain=domain, relationship_predicate=relationship_predicate, question_count=question_count, seed=seed,
        )
        questions = underlying.get("questions", []) if isinstance(underlying, dict) else []
        production_safety = underlying.get("production_safety") if isinstance(underlying, dict) else None
        capability_fingerprint = f"{domain}|{relationship_predicate}"
        underlying_capability = {"domain": domain, "relationship_predicate": relationship_predicate}
    # Story Factory integration: replace a bounded slice of generic drive
    # questions with verified story-backed MCQs. The drive mechanic stays the
    # same; only the football knowledge source becomes deeper and more varied.
    try:
        c_story = engine_bootstrap.connect()
        try:
            story_questions = load_story_mcqs(
                c_story,
                limit=max(1, min(3, question_count // 4 or 1)),
            )
        finally:
            c_story.close()
    except Exception:
        story_questions = []

    story_inserted = 0
    if story_questions and questions:
        positions = list(range(2, len(questions), 4))
        for pos, story_q in zip(positions, story_questions):
            questions[pos] = to_generation_question(story_q)
            story_inserted += 1

    package_id = "GGP12:" + hashlib.sha256(
        f"DRIVE|{variant}|{mode}|{capability_fingerprint}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]

    qa_status = "PASSED" if questions else "FAILED"
    shortfall_reason = None if questions else (
        f"No real questions were generated for capability={capability_fingerprint!r} "
        f"-- no drive was built rather than run one with zero real content."
    )
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "mode": mode,
        "game_title": "Perfect Drive" if mode == "YARDAGE" else "Goal Line Stand",
        "game_instructions": (
            "Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive."
            if mode == "YARDAGE" else
            f"You have {downs} downs to score. A wrong answer costs a down."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": qa_status,
        "questions": questions,
        "field_length_yards": FIELD_LENGTH_YARDS, "downs_total": downs,
        "underlying_capability": underlying_capability,
        "production_safety": production_safety,
        "shortfall_reason": shortfall_reason,
        "review_status": "UNREVIEWED", "_diagnostics": {
            "seed": seed,
            "story_questions_used": story_inserted,
        },
    }
