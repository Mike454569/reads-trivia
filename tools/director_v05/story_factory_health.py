"""Health metrics for the automatic story-to-trivia factory."""
from __future__ import annotations


def story_factory_health(conn):
    tables = {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    out = {
        "candidate_total": 0,
        "candidate_status": {},
        "enriched_total": 0,
        "promotion_decisions": {},
        "promoted_events": 0,
        "generated_question_total": 0,
        "ready_for_bank": 0,
        "questions_by_mechanic": {},
        "questions_by_status": {},
        "ready_for_format_bank": 0,
        "promotion_rate": 0.0,
        "questions_per_promoted_event": 0.0,
    }

    if "football_story_candidates" in tables:
        rows = conn.execute(
            """SELECT status,COUNT(*) n
               FROM football_story_candidates
               GROUP BY status"""
        ).fetchall()
        out["candidate_status"] = {str(r["status"]): int(r["n"]) for r in rows}
        out["candidate_total"] = sum(out["candidate_status"].values())

    if "football_story_enrichment" in tables:
        rows = conn.execute(
            """SELECT decision,COUNT(*) n
               FROM football_story_enrichment
               GROUP BY decision"""
        ).fetchall()
        out["promotion_decisions"] = {str(r["decision"]): int(r["n"]) for r in rows}
        out["enriched_total"] = sum(out["promotion_decisions"].values())
        out["promoted_events"] = int(
            out["promotion_decisions"].get("AUTO_PROMOTED", 0)
        )

    if "story_generated_questions" in tables:
        rows = conn.execute(
            """SELECT mechanic,status,COUNT(*) n
               FROM story_generated_questions
               GROUP BY mechanic,status"""
        ).fetchall()
        by_mechanic = {}
        by_status = {}
        total = 0
        ready = 0
        ready_format = 0
        for r in rows:
            n = int(r["n"])
            total += n
            mechanic = str(r["mechanic"])
            status = str(r["status"])
            by_mechanic[mechanic] = by_mechanic.get(mechanic, 0) + n
            by_status[status] = by_status.get(status, 0) + n
            if status == "READY_FOR_BANK":
                ready += n
            if status == "READY_FOR_FORMAT_BANK":
                ready_format += n
        out["generated_question_total"] = total
        out["ready_for_bank"] = ready
        out["ready_for_format_bank"] = ready_format
        out["questions_by_mechanic"] = by_mechanic
        out["questions_by_status"] = by_status

    if out["enriched_total"]:
        out["promotion_rate"] = round(
            out["promoted_events"] / out["enriched_total"], 4
        )
    if out["promoted_events"]:
        out["questions_per_promoted_event"] = round(
            out["generated_question_total"] / out["promoted_events"], 4
        )
    return out
