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
        "candidate_families": {},
        "candidate_domains": {},
        "promoted_by_family": {},
        "league_balance": {},
        "review_backlog": 0,
        "sensitive_backlog": 0,
        "processing_ledger": {},
        "checkpointed_generated": 0,
    }

    if "football_story_candidates" in tables:
        rows = conn.execute(
            """SELECT status,COUNT(*) n
               FROM football_story_candidates
               GROUP BY status"""
        ).fetchall()
        out["candidate_status"] = {str(r["status"]): int(r["n"]) for r in rows}
        out["candidate_total"] = sum(out["candidate_status"].values())
        fam = conn.execute(
            """SELECT family_hint,COUNT(*) n
               FROM football_story_candidates
               GROUP BY family_hint ORDER BY n DESC"""
        ).fetchall()
        dom = conn.execute(
            """SELECT domain,COUNT(*) n
               FROM football_story_candidates
               GROUP BY domain ORDER BY n DESC"""
        ).fetchall()
        out["candidate_families"] = {str(r["family_hint"]): int(r["n"]) for r in fam}
        out["candidate_domains"] = {str(r["domain"]): int(r["n"]) for r in dom}
        out["review_backlog"] = int(out["candidate_status"].get("REVIEW_REQUIRED", 0))
        out["sensitive_backlog"] = int(out["candidate_status"].get("REVIEW_REQUIRED_SENSITIVE", 0))

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
        promoted = conn.execute(
            """SELECT c.family_hint,COUNT(*) n
               FROM football_story_enrichment e
               JOIN football_story_candidates c ON c.candidate_id=e.candidate_id
               WHERE e.decision='AUTO_PROMOTED'
               GROUP BY c.family_hint ORDER BY n DESC"""
        ).fetchall()
        leagues = conn.execute(
            """SELECT u.league,COUNT(DISTINCT e.promoted_event_id) n
               FROM football_story_enrichment e
               JOIN universal_event u ON u.event_id=e.promoted_event_id
               WHERE e.decision='AUTO_PROMOTED'
               GROUP BY u.league ORDER BY n DESC"""
        ).fetchall()
        out["promoted_by_family"] = {str(r["family_hint"]): int(r["n"]) for r in promoted}
        out["league_balance"] = {str(r["league"]): int(r["n"]) for r in leagues}

    if "story_candidate_processing" in tables:
        rows = conn.execute(
            """SELECT state,COUNT(*) n
               FROM story_candidate_processing
               GROUP BY state"""
        ).fetchall()
        out["processing_ledger"] = {
            str(r["state"]): int(r["n"]) for r in rows
        }
        out["checkpointed_generated"] = int(
            conn.execute(
                "SELECT COALESCE(SUM(generated_question_count),0) "
                "FROM story_candidate_processing"
            ).fetchone()[0]
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
