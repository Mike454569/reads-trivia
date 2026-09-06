"""CFB Rivalry domain adapter (Creator-gap-audit operation).

Built on `cfb_rivalries` (48 real, named rivalries, e.g. Alabama-Auburn/
"Iron Bowl", Texas-Oklahoma/"Red River Rivalry", Michigan-Ohio State/
"The Game") -- fully populated with real school_id links on both sides,
zero Creator capabilities built on it before this. "Which school is [team]'s
rival in [named rivalry]" -- entity is one side of a real rivalry, answer is
the other side. Each of the 48 rivalry rows produces TWO real candidates
(A asked about B, and B asked about A), since a rivalry is symmetric.

Distractor schools use the same "other real rivalry-pool schools" plausible-
distractor pattern cfb_heisman.py/cfb_championship.py already established
(every option here is a school famous enough to be in a real, named
rivalry -- never an obscure program that would make the answer obvious by
elimination alone).
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None
CATEGORY = "CFB Rivalries"
REQUIRED_SOURCE = "READS_CFB_MASTER"
TRACK_ENTITY = True  # one question per real (school, rivalry) direction


def safety_check(c) -> dict:
    src = c.execute(
        "SELECT approved_for_import FROM sources WHERE source_id=?", (REQUIRED_SOURCE,)
    ).fetchone()
    if not src or not src["approved_for_import"]:
        return {"safe": False, "reason": f"source {REQUIRED_SOURCE} not registered/approved"}
    total = c.execute("SELECT COUNT(*) FROM cfb_rivalries").fetchone()[0]
    with_both_ids = c.execute(
        "SELECT COUNT(*) FROM cfb_rivalries WHERE school_a_id IS NOT NULL AND school_b_id IS NOT NULL"
    ).fetchone()[0]
    return {
        "safe": total > 0 and with_both_ids == total,
        "total_rows": total, "rows_with_both_school_ids_resolved": with_both_ids,
    }


def fetch_ordered_candidates(c, seed: str):
    rows = c.execute(
        "SELECT rivalry_id, matchup, school_a_id, school_a, school_b_id, school_b, nickname, "
        "trophy, series_record, fun_fact FROM cfb_rivalries "
        "WHERE school_a_id IS NOT NULL AND school_b_id IS NOT NULL"
    ).fetchall()
    candidates = []
    for r in rows:
        candidates.append({"rivalry_id": r["rivalry_id"], "nickname": r["nickname"], "trophy": r["trophy"],
                            "series_record": r["series_record"], "fun_fact": r["fun_fact"],
                            "ask_id": r["school_a_id"], "ask_name": r["school_a"],
                            "answer_id": r["school_b_id"], "answer_name": r["school_b"]})
        candidates.append({"rivalry_id": r["rivalry_id"], "nickname": r["nickname"], "trophy": r["trophy"],
                            "series_record": r["series_record"], "fun_fact": r["fun_fact"],
                            "ask_id": r["school_b_id"], "ask_name": r["school_b"],
                            "answer_id": r["school_a_id"], "answer_name": r["school_a"]})
    rng_order = engine.seeded(seed)
    rng_order.shuffle(candidates)
    return candidates


def _rivalry_schools_pool(c) -> dict:
    rows = c.execute(
        "SELECT school_a_id, school_a FROM cfb_rivalries WHERE school_a_id IS NOT NULL "
        "UNION SELECT school_b_id, school_b FROM cfb_rivalries WHERE school_b_id IS NOT NULL"
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def _all_real_schools(c) -> dict:
    rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def evaluate(c, row, rng, guard):
    if not row["ask_id"] or not row["answer_id"] or not row["ask_name"] or not row["answer_name"]:
        return "SCHOOL_UNRESOLVED"

    plausible = _rivalry_schools_pool(c)
    full = _all_real_schools(c)
    distractor_map = distractors_mod.sample_plausible(rng, row["answer_id"], plausible, full, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [row["answer_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    # Public Mode Wiring pass: real bug found while making this capability
    # public -- 32 of 96 real rows have a literal "-" placeholder nickname
    # (no real nickname exists for that rivalry), which the original
    # `if row["nickname"]` check didn't catch (a non-empty "-" string is
    # still truthy), producing 'in the game known as ("-")' for a full
    # third of all real questions. Treat a dash/whitespace-only placeholder
    # the same as no nickname at all -- matches this line's own clear
    # intent, doesn't change any real, meaningful nickname.
    real_nickname = (row["nickname"] or "").strip()
    if real_nickname == "-":
        real_nickname = ""
    rivalry_phrase = f' ("{real_nickname}")' if real_nickname else ""
    question = f"Which school is {row['ask_name']}’s rival in the game known as{rivalry_phrase}?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_rivalry:{row['rivalry_id']}:{row['ask_id']}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_DIRECTION"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["answer_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["answer_name"]:
        return "INVALID_CORRECT_INDEX"

    # No real season/recency axis for a standing rivalry -- difficulty is a
    # flat "medium" rather than a fabricated recency score.
    diff_label = "Medium"

    extra = row["series_record"] or row["fun_fact"] or ""
    notes = f"{row['ask_name']} and {row['answer_name']} play in {real_nickname or 'a rivalry game'}. {extra}".strip()

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "rivalry_id": row["rivalry_id"], "ask_id": row["ask_id"], "answer_id": row["answer_id"],
            "correct_answer_text": row["answer_name"],
            "difficulty_score": 0.5, "difficulty_band": "MEDIUM", "entity_key": entity_key,
            "verification_status": "SOURCE_BACKED_FROM_CFB_MASTER", "source_id": REQUIRED_SOURCE,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} real rivalry-direction pairs on record (48 rivalries x 2 directions); "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    return {"unique_rivalries": len(set(q["_audit"]["rivalry_id"] for q in exported))}


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_rivalry.py -- CFB Rivalries.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Rivalry:** `{a['rivalry_id']}`",
        f"- **Asked about:** `{a['ask_id']}` -> **Answer:** `{a['answer_id']}` "
        f"(\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_rivalries`, verification_status `{a['verification_status']}`, "
        f"source_id `{a['source_id']}`",
    ]
