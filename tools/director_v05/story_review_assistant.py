"""Deterministic review assistant for story candidates.

Produces structured suggestions for human review. Suggestions never mutate
universal lore and never approve sensitive/legal/discipline candidates.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .story_article_extract import fetch_article
from .story_subject_match import build_subject_index, match_subjects, primary_identity_match
from .story_to_trivia_factory import AUTO_FAMILIES, FAMILY_TERMS, _infer_league

MONTHS = {
    "january":1, "february":2, "march":3, "april":4, "may":5, "june":6,
    "july":7, "august":8, "september":9, "october":10, "november":11, "december":12,
}

LEGAL_STAGE_TERMS = {
    "ARREST": ("arrested", "arrest"),
    "CHARGE": ("charged", "charge", "indicted", "indictment"),
    "INVESTIGATION": ("investigation", "investigating", "under investigation"),
    "SUSPENSION": ("suspended", "suspension"),
    "FINE": ("fined", "fine"),
    "DISMISSAL": ("dismissed", "charges dismissed", "case dismissed"),
    "ACQUITTAL": ("acquitted", "not guilty"),
    "CONVICTION": ("convicted", "guilty plea", "pleaded guilty", "pled guilty"),
}


def _ensure_schema(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS story_review_suggestions (
            candidate_id TEXT PRIMARY KEY,
            source_url TEXT NOT NULL,
            family_hint TEXT,
            suggested_event_type TEXT,
            suggested_league TEXT,
            suggested_subject_type TEXT,
            suggested_subject_id TEXT,
            suggested_subject_label TEXT,
            suggested_event_date TEXT,
            date_basis TEXT,
            publication_date TEXT,
            suggested_legal_stage TEXT,
            evidence_terms_json TEXT NOT NULL,
            risk_flags_json TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'SUGGESTED_ONLY',
            generated_at TEXT NOT NULL
        )
    """)
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_story_review_suggestions_status "
        "ON story_review_suggestions(status,family_hint)"
    )
    c.commit()


def _family_terms(family, article):
    copy = (
        str(article.get("headline") or "") + " "
        + str(article.get("description") or "") + " "
        + str(article.get("text") or "")
    ).casefold()
    return [term for term in FAMILY_TERMS.get(str(family), ()) if term in copy]


def _date_candidates(text):
    text = str(text or "")
    found = set()

    for y, m, d in re.findall(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text):
        try:
            found.add(dt.date(int(y), int(m), int(d)).isoformat())
        except ValueError:
            pass

    month_names = "|".join(MONTHS)
    pattern = re.compile(
        rf"\b({month_names})\s+(\d{{1,2}}),\s+(20\d{{2}})\b",
        re.I,
    )
    for month, day, year in pattern.findall(text):
        try:
            found.add(
                dt.date(int(year), MONTHS[month.casefold()], int(day)).isoformat()
            )
        except ValueError:
            pass
    return sorted(found)


def _publication_date(article):
    raw = str(article.get("published") or "")
    match = re.match(r"(20\d{2})[-/]?(\d{2})?[-/]?(\d{2})?", raw)
    if not match:
        return None
    y = int(match.group(1))
    m = int(match.group(2) or 1)
    d = int(match.group(3) or 1)
    try:
        return dt.date(y, m, d).isoformat()
    except ValueError:
        return None


def _suggest_event_date(article):
    publication = _publication_date(article)
    dates = _date_candidates(
        str(article.get("headline") or "") + " "
        + str(article.get("description") or "") + " "
        + str(article.get("text") or "")
    )
    # Never blindly reuse publication date. Only suggest one distinct body date
    # when it differs from publication, otherwise leave chronology unresolved.
    distinct = [d for d in dates if d != publication]
    if len(distinct) == 1:
        return distinct[0], "SINGLE_EXPLICIT_ARTICLE_DATE"
    return None, None


def _legal_stage(article):
    copy = (
        str(article.get("headline") or "") + " "
        + str(article.get("description") or "") + " "
        + str(article.get("text") or "")
    ).casefold()
    hits = []
    for stage, terms in LEGAL_STAGE_TERMS.items():
        if any(term in copy for term in terms):
            hits.append(stage)
    return hits[0] if len(hits) == 1 else None


def _confidence(subject, evidence_terms, event_date, league, sensitive):
    score = 0
    if subject:
        score += 40 if subject.get("in_title") else 25
        score += 20 if subject.get("in_text") else 0
    score += min(15, 5 * len(evidence_terms))
    if league:
        score += 10
    if event_date:
        score += 5
    if sensitive:
        score = min(score, 75)
    return min(score, 100)


def suggest_candidate(c, candidate, subject_index):
    sensitive = bool(int(candidate["sensitive_hint"] or 0))
    family = str(candidate["family_hint"])
    risk_flags = []
    try:
        article = fetch_article(candidate["source_url"])
    except Exception as exc:
        return {
            "candidate_id": str(candidate["candidate_id"]),
            "status": "FETCH_FAILED",
            "reason": type(exc).__name__ + ":" + str(exc),
        }

    matches = match_subjects(
        subject_index,
        title=article.get("headline") or candidate["title"],
        text=article.get("text") or "",
    )
    subject = primary_identity_match(matches)
    if not subject:
        risk_flags.append("NO_SINGLE_CANONICAL_PERSON_SUBJECT")
    if len([
        m for m in matches
        if m["entity_type"] in {"NFL_PLAYER","CFB_PLAYER","COACH"}
    ]) > 1:
        risk_flags.append("MULTIPLE_PERSON_IDENTITIES_MENTIONED")

    evidence_terms = _family_terms(family, article)
    if not evidence_terms and family in AUTO_FAMILIES:
        risk_flags.append("NO_FAMILY_SPECIFIC_EVIDENCE")

    league = _infer_league(article, subject) if subject else None
    if not league:
        risk_flags.append("LEAGUE_UNRESOLVED")

    event_date, date_basis = _suggest_event_date(article)
    if not event_date:
        risk_flags.append("EVENT_DATE_REQUIRES_REVIEW")

    legal_stage = _legal_stage(article) if sensitive else None
    if sensitive:
        risk_flags.append("SENSITIVE_MANUAL_REVIEW_REQUIRED")
        if not legal_stage:
            risk_flags.append("LEGAL_OR_DISCIPLINE_STAGE_UNRESOLVED")

    event_type = AUTO_FAMILIES.get(family)
    if sensitive:
        event_type = "LEGAL_EVENT" if legal_stage in {
            "ARREST","CHARGE","INVESTIGATION","DISMISSAL","ACQUITTAL","CONVICTION"
        } else "LEAGUE_DISCIPLINE"

    confidence = _confidence(
        subject, evidence_terms, event_date, league, sensitive
    )
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    row = {
        "candidate_id": str(candidate["candidate_id"]),
        "source_url": article["final_url"],
        "family_hint": family,
        "suggested_event_type": event_type,
        "suggested_league": league,
        "suggested_subject_type": (subject or {}).get("entity_type"),
        "suggested_subject_id": (subject or {}).get("entity_id"),
        "suggested_subject_label": (subject or {}).get("label"),
        "suggested_event_date": event_date,
        "date_basis": date_basis,
        "publication_date": _publication_date(article),
        "suggested_legal_stage": legal_stage,
        "evidence_terms": evidence_terms,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "status": "SUGGESTED_ONLY",
        "generated_at": now,
    }

    c.execute(
        """INSERT OR REPLACE INTO story_review_suggestions(
           candidate_id,source_url,family_hint,suggested_event_type,
           suggested_league,suggested_subject_type,suggested_subject_id,
           suggested_subject_label,suggested_event_date,date_basis,
           publication_date,suggested_legal_stage,evidence_terms_json,
           risk_flags_json,confidence,status,generated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["candidate_id"], row["source_url"], row["family_hint"],
            row["suggested_event_type"], row["suggested_league"],
            row["suggested_subject_type"], row["suggested_subject_id"],
            row["suggested_subject_label"], row["suggested_event_date"],
            row["date_basis"], row["publication_date"],
            row["suggested_legal_stage"],
            json.dumps(row["evidence_terms"], sort_keys=True),
            json.dumps(row["risk_flags"], sort_keys=True),
            row["confidence"], row["status"], row["generated_at"],
        ),
    )
    c.commit()
    return row


def run_review_assistant(*, limit=250, include_sensitive=True):
    c = engine_bootstrap.connect()
    _ensure_schema(c)
    subject_index = build_subject_index(c)

    # Promoted non-sensitive stories are included so the assistant can
    # suggest a real event date for chronology review after auto-promotion.
    statuses = ["REVIEW_REQUIRED", "PROMOTED"]
    if include_sensitive:
        statuses.append("REVIEW_REQUIRED_SENSITIVE")
    placeholders = ",".join("?" for _ in statuses)
    rows = c.execute(
        f"""SELECT * FROM football_story_candidates
            WHERE status IN ({placeholders})
            ORDER BY
              CASE status WHEN 'PROMOTED' THEN 0 WHEN 'REVIEW_REQUIRED' THEN 1 ELSE 2 END,
              CASE evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
              seen_date DESC,candidate_id
            LIMIT ?""",
        (*statuses, max(1, min(int(limit), 2000))),
    ).fetchall()

    counts = Counter()
    examples = []
    for row in rows:
        suggestion = suggest_candidate(c, row, subject_index)
        counts[suggestion.get("status") or "UNKNOWN"] += 1
        if suggestion.get("status") == "SUGGESTED_ONLY" and len(examples) < 10:
            examples.append({
                "candidate_id": suggestion["candidate_id"],
                "subject": suggestion["suggested_subject_label"],
                "event_type": suggestion["suggested_event_type"],
                "event_date": suggestion["suggested_event_date"],
                "legal_stage": suggestion["suggested_legal_stage"],
                "confidence": suggestion["confidence"],
                "risk_flags": suggestion["risk_flags"],
            })

    total = c.execute(
        "SELECT COUNT(*) FROM story_review_suggestions WHERE status='SUGGESTED_ONLY'"
    ).fetchone()[0]
    c.close()
    return {
        "processed": len(rows),
        "status_counts": dict(counts),
        "suggestion_total": int(total),
        "examples": examples,
    }
