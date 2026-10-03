"""Admin-only story review queue and factory diagnostics."""
from __future__ import annotations

import json

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.story_factory_health import story_factory_health


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

        statuses = ["REVIEW_REQUIRED"]
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
        return health
    finally:
        c.close()
