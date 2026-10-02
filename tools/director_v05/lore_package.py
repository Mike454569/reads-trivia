"""Standard package adapter for deep-lore gameplay.

Builds the same questions/options/correctIndex package shape used by public guess
modes, but is deliberately not public-allowlisted until real-DB certification.
"""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone

from tools.quiz_export import engine as engine_bootstrap

from .lore_question_bank import build_lore_question_bank

DIFFICULTY_MAP = {
    "easy": "CASUAL",
    "medium": "HARD",
    "hard": "SICKO",
    "any": "HARD",
    "CASUAL": "CASUAL",
    "HARD": "HARD",
    "SICKO": "SICKO",
}


def _anchors(conn):
    rows = conn.execute(
        """SELECT subject_type,subject_id,COUNT(DISTINCT event_id) n
           FROM universal_event_subject
           WHERE subject_type IN ('NFL_PLAYER','CFB_PLAYER','COACH')
           GROUP BY subject_type,subject_id
           HAVING n>=1
           ORDER BY n DESC,subject_type,subject_id"""
    ).fetchall()
    return [(str(r["subject_type"]), str(r["subject_id"])) for r in rows]


def _stable_package_id(payload):
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return "GGP39:" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def _question_contract(q, *, index, delivery_difficulty):
    options = list(q.get("options") or [])
    answer_label = str((q.get("answer") or {}).get("label") or "")
    if not options or not answer_label:
        raise ValueError("LORE_DELIVERY_MISSING_OPTIONS")
    try:
        correct_index = options.index(answer_label)
    except ValueError as exc:
        raise ValueError("LORE_DELIVERY_ANSWER_NOT_IN_OPTIONS") from exc

    clue_text = [str(c.get("text") or "").strip() for c in q.get("clues") or [] if str(c.get("text") or "").strip()]
    if len(clue_text) < 2:
        raise ValueError("LORE_DELIVERY_TOO_FEW_CLUES")

    return {
        "id": q["question_id"],
        "question": q["question"],
        "clues": clue_text,
        "options": options,
        "correctIndex": correct_index,
        "answer": answer_label,
        "difficulty": str(delivery_difficulty).lower(),
        "notes": " ".join(clue_text),
        "visual_template": "DEEP_LORE_THREE_CLUES",
        "visual_payload": {
            "clues": clue_text,
            "reveal_order": [
                {
                    "step": int(c.get("reveal_step") or i + 1),
                    "text": str(c.get("text") or ""),
                }
                for i, c in enumerate(q.get("clues") or [])
            ],
        },
        "entity_key": str((q.get("answer") or {}).get("type") or "") + ":" + str((q.get("answer") or {}).get("id") or ""),
        "internal_lore": {
            "chain_id": q.get("chain_id"),
            "question_family": q.get("question_family"),
            "rarity_score": q.get("rarity_score"),
            "difficulty_score": q.get("difficulty_score"),
            "provenance": q.get("provenance"),
            "distractors": q.get("distractors"),
        },
    }


def build_package(
    *,
    seed,
    target_count=1,
    difficulty="medium",
    recent_question_ids=(),
    recent_answer_ids=(),
    recent_chain_ids=(),
    recent_distractor_ids=(),
    recent_families=(),
):
    band = DIFFICULTY_MAP.get(str(difficulty), DIFFICULTY_MAP.get(str(difficulty).lower()))
    if not band:
        raise ValueError("UNKNOWN_LORE_DELIVERY_DIFFICULTY")

    conn = engine_bootstrap.connect()
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        anchors = _anchors(conn)
        rng = random.Random(str(seed))
        rng.shuffle(anchors)

        bank = build_lore_question_bank(
            conn,
            anchors,
            difficulty_band=band,
            target=max(1, int(target_count)),
            recent_question_ids=recent_question_ids,
            recent_answer_ids=recent_answer_ids,
            recent_chain_ids=recent_chain_ids,
            recent_distractor_ids=recent_distractor_ids,
            recent_families=recent_families,
            with_options=True,
        )
        questions = [
            _question_contract(q, index=i, delivery_difficulty=difficulty)
            for i, q in enumerate(bank["selected"])
        ]
    finally:
        conn.close()

    qa_status = "PASSED" if questions else "FAILED"
    shortfall = None if len(questions) >= int(target_count) else (
        f"Requested {int(target_count)} deep-lore question(s); generated {len(questions)} "
        "without weakening provenance, uniqueness, or distractor quality."
    )

    identity = {
        "mode": "deep_lore_guess",
        "seed": str(seed),
        "difficulty": str(difficulty).lower(),
        "question_ids": [q["id"] for q in questions],
    }
    package_id = _stable_package_id(identity)
    return {
        "package_id": package_id,
        "package_version": "5.0-deep-lore",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": qa_status,
        "review_status": "UNREVIEWED",
        "game_title": "Deep Football Lore",
        "game_instructions": "Use three real clues to identify the football player or coach.",
        "question_count": len(questions),
        "questions": questions,
        "parsed_spec": {
            "mechanic": "guess",
            "domain": "UNIVERSAL_DEEP_LORE",
            "relationship_predicate": "IDENTIFY_FROM_DEEP_LORE",
            "question_count": int(target_count),
            "difficulty": str(difficulty).lower(),
            "filters": {},
            "exclusions": [],
        },
        "_diagnostics": {
            "seed": str(seed),
            "difficulty_band": band,
            "candidate_count": bank["candidate_count"],
            "selected_count": bank["selected_count"],
            "unique_answers": bank["unique_answers"],
            "unique_events": bank["unique_events"],
            "family_counts": bank.get("family_counts", {}),
            "league_counts": bank.get("league_counts", {}),
            "sensitive_count": bank.get("sensitive_count", 0),
            "available_family_counts": bank.get("available_family_counts", {}),
            "mix_counts": bank.get("mix_counts", {}),
            "draft_fraction": bank.get("draft_fraction", 0.0),
            "story_fraction": bank.get("story_fraction", 0.0),
            "recent_families": [str(x) for x in recent_families],
            "shortfall_reason": shortfall,
        },
        "shortfall_reason": shortfall,
    }
