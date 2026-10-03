"""Admin-only story review queue and factory diagnostics."""
from __future__ import annotations

import json

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_factory_health import story_factory_health
from tools.director_v05.story_multiformat import generate_story_formats_for_event
from tools.director_v05.certify_story_question_quality import certify_story_question_quality
from tools.director_v05.story_subject_match import build_subject_index
from tools.director_v05.story_to_trivia_factory import process_candidate, _ensure_schema as ensure_story_factory_schema


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def review_queue(*, limit=200, include_sensitive=True):
    c = engine_bootstrap.connect()
    try:
        tables = _tables(c)
        if "football_story_candidates" not in tables:
            return {"items": [], "count": 0, "reason": "STORY_CANDIDATE_TABLE_MISSING"}

        suggestion_join = ""
        suggestion_cols = """
            NULL suggested_event_type,NULL suggested_league,NULL suggested_subject_type,
            NULL suggested_subject_id,NULL suggested_subject_label,NULL suggested_event_date,
            NULL date_basis,NULL publication_date,NULL suggested_legal_stage,
            NULL suggestion_confidence,NULL risk_flags_json,NULL evidence_terms_json
        """
        if "story_review_suggestions" in tables:
            suggestion_join = (
                " LEFT JOIN story_review_suggestions s"
                " ON s.candidate_id=c.candidate_id "
            )
            suggestion_cols = """
                s.suggested_event_type,s.suggested_league,s.suggested_subject_type,
                s.suggested_subject_id,s.suggested_subject_label,s.suggested_event_date,
                s.date_basis,s.publication_date,s.suggested_legal_stage,
                s.confidence suggestion_confidence,s.risk_flags_json,s.evidence_terms_json
            """

        # Include promoted stories too: they may be fully verified for normal
        # trivia but still need a human-confirmed event date before chronology
        # formats can unlock.
        statuses = ["REVIEW_REQUIRED", "PROMOTED"]
        if include_sensitive:
            statuses.append("REVIEW_REQUIRED_SENSITIVE")
        placeholders = ",".join("?" for _ in statuses)

        rows = c.execute(
            f"""SELECT c.candidate_id,c.source_url,c.title,c.domain,c.seen_date,
                       c.family_hint,c.evidence_tier_hint,c.sensitive_hint,c.status,
                       c.review_notes,{suggestion_cols}
                FROM football_story_candidates c
                {suggestion_join}
                WHERE c.status IN ({placeholders})
                ORDER BY
                  c.sensitive_hint DESC,
                  CASE c.evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
                  COALESCE(suggestion_confidence,0) DESC,
                  c.seen_date DESC,c.candidate_id
                LIMIT ?""",
            (*statuses, max(1, min(int(limit), 2000))),
        ).fetchall()

        items = []
        for row in rows:
            item = dict(row)
            for key in ("risk_flags_json", "evidence_terms_json"):
                raw = item.pop(key, None)
                try:
                    item[key.removesuffix("_json")] = json.loads(raw) if raw else []
                except Exception:
                    item[key.removesuffix("_json")] = []
            items.append(item)
        return {
            "items": items,
            "count": len(items),
            "include_sensitive": bool(include_sensitive),
        }
    finally:
        c.close()


def factory_health():
    c = engine_bootstrap.connect()
    try:
        health = story_factory_health(c)
        if "story_review_suggestions" in _tables(c):
            rows = c.execute(
                """SELECT status,COUNT(*) n
                   FROM story_review_suggestions
                   GROUP BY status"""
            ).fetchall()
            health["review_suggestions"] = {
                str(r["status"]): int(r["n"]) for r in rows
            }
        else:
            health["review_suggestions"] = {}
        health["question_quality"] = certify_story_question_quality(c)
        return health
    finally:
        c.close()



def confirm_event_date(*, candidate_id, event_date):
    import datetime as dt

    try:
        parsed = dt.date.fromisoformat(str(event_date))
    except ValueError as exc:
        raise ValueError("INVALID_EVENT_DATE") from exc

    c = engine_bootstrap.connect()
    try:
        tables = _tables(c)
        required = {
            "football_story_enrichment",
            "universal_event",
            "story_generated_questions",
        }
        if not required <= tables:
            raise ValueError("STORY_REVIEW_TABLES_MISSING")

        row = c.execute(
            """SELECT candidate_id,decision,promoted_event_id,subject_type,subject_id
               FROM football_story_enrichment
               WHERE candidate_id=?""",
            (str(candidate_id),),
        ).fetchone()
        if not row:
            raise ValueError("UNKNOWN_STORY_CANDIDATE")
        if str(row["decision"]) != "AUTO_PROMOTED":
            raise ValueError("STORY_NOT_AUTO_PROMOTED")
        if not row["promoted_event_id"]:
            raise ValueError("STORY_HAS_NO_PROMOTED_EVENT")

        event = c.execute(
            """SELECT event_id,event_date,sensitive
               FROM universal_event
               WHERE event_id=?""",
            (str(row["promoted_event_id"]),),
        ).fetchone()
        if not event:
            raise ValueError("PROMOTED_EVENT_MISSING")
        if int(event["sensitive"] or 0):
            raise ValueError("SENSITIVE_EVENT_DATE_REVIEW_REQUIRES_SEPARATE_WORKFLOW")

        existing = str(event["event_date"] or "").strip()
        if existing and existing != parsed.isoformat():
            raise ValueError("EVENT_DATE_ALREADY_CONFIRMED_DIFFERENTLY")

        c.execute(
            """UPDATE universal_event
               SET event_date=?,updated_at=datetime('now')
               WHERE event_id=?""",
            (parsed.isoformat(), str(row["promoted_event_id"])),
        )

        if "story_review_suggestions" in tables:
            c.execute(
                """UPDATE story_review_suggestions
                   SET status='DATE_CONFIRMED'
                   WHERE candidate_id=?""",
                (str(candidate_id),),
            )
        c.commit()

        formats = generate_story_formats_for_event(
            c,
            candidate_id=str(candidate_id),
            event_id=str(row["promoted_event_id"]),
            subject_type=str(row["subject_type"]),
            subject_id=str(row["subject_id"]),
        )
        return {
            "candidate_id": str(candidate_id),
            "event_id": str(row["promoted_event_id"]),
            "event_date": parsed.isoformat(),
            "format_questions_generated": int(formats.get("generated_count") or 0),
            "format_rejections": formats.get("rejected", []),
        }
    finally:
        c.close()



def game_reach_certification():
    from tools.director_v05.certify_story_production import certify_story_production
    return certify_story_production()



def retry_safe_promotions(*, limit=50):
    """Re-run strict auto-promotion gates for non-sensitive review backlog.

    This is not a manual override. It cannot lower confidence thresholds,
    bypass canonical identity matching, or promote sensitive/legal candidates.
    """
    c = engine_bootstrap.connect()
    try:
        ensure_story_factory_schema(c)
        rows = c.execute(
            """SELECT * FROM football_story_candidates
               WHERE status='REVIEW_REQUIRED'
                 AND COALESCE(sensitive_hint,0)=0
               ORDER BY
                 CASE evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
                 seen_date DESC,candidate_id
               LIMIT ?""",
            (max(1, min(int(limit), 250)),),
        ).fetchall()
        subject_index = build_subject_index(c)
        counts = {}
        promoted = []
        for row in rows:
            result = process_candidate(c, row, subject_index)
            decision = str(result.get("decision") or "UNKNOWN")
            counts[decision] = counts.get(decision, 0) + 1
            if decision == "AUTO_PROMOTED":
                promoted.append({
                    "candidate_id": str(row["candidate_id"]),
                    "event_id": result.get("event_id"),
                    "generated_questions": int(result.get("generated") or 0),
                })
        return {
            "processed": len(rows),
            "decisions": counts,
            "promoted": promoted,
            "promoted_count": len(promoted),
        }
    finally:
        c.close()
