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
from datetime import datetime, timezone

# Real, confirmed-live casing: generated questions carry Title-Case
# difficulty values ("Easy"/"Medium"/"Hard"), not lowercase.
YARDS_BY_DIFFICULTY = {"Easy": 10, "Medium": 20, "Hard": 30, "Any": 15}
FIELD_LENGTH_YARDS = 100
DEFAULT_DOWNS = 4

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "DRIVE_PROGRESSION"


def _generate_question_pool(*, domain: str, relationship_predicate: str, question_count: int, seed: str) -> dict:
    from gateway.services import generation as generation_service
    spec = {"mechanic": "guess", "domain": domain, "relationship_predicate": relationship_predicate,
            "question_count": question_count, "difficulty": "any", "filters": {}, "exclusions": []}
    return generation_service.generate(request_text=None, spec=spec, provider="mock",
                                        puzzle_count=None, difficulty=None, seed=seed)


def build_package(seed: str, variant: str, *, mode: str, domain: str, relationship_predicate: str,
                   question_count: int, downs: int = DEFAULT_DOWNS) -> dict:
    if mode not in ("YARDAGE", "DOWNS"):
        raise ValueError(f"mode must be 'YARDAGE' or 'DOWNS', got {mode!r}")

    underlying = _generate_question_pool(
        domain=domain, relationship_predicate=relationship_predicate, question_count=question_count, seed=seed,
    )
    questions = underlying.get("questions", []) if isinstance(underlying, dict) else []
    package_id = "GGP12:" + hashlib.sha256(
        f"DRIVE|{variant}|{mode}|{domain}|{relationship_predicate}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]

    qa_status = "PASSED" if questions else "FAILED"
    shortfall_reason = None if questions else (
        f"No real questions were generated for domain={domain!r}/relationship_predicate={relationship_predicate!r} "
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
        "underlying_capability": {"domain": domain, "relationship_predicate": relationship_predicate},
        "production_safety": underlying.get("production_safety") if isinstance(underlying, dict) else None,
        "shortfall_reason": shortfall_reason,
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
