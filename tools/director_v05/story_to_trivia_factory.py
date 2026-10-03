"""Story candidate -> verified lore -> generated trivia factory.

Safe automation rules:
- never auto-promote sensitive/legal/discipline candidates;
- require readable article text from an approved domain after redirects;
- require one clear canonical person subject;
- require family-specific evidence in article text;
- require a high confidence score;
- create universal_event only after all gates pass;
- immediately attempt Progressive Clue and deep-chain question compilation;
- persist generated question JSON for inspection/reuse.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .event_ingest import upsert_event
from .lore_chains import discover_lore_chains, compile_lore_chain_question
from .lore_distractors import attach_deep_lore_options
from .lore_mechanics import compile_progressive_identity
from .story_article_extract import fetch_article
from .story_subject_match import build_subject_index, match_subjects, primary_identity_match

AUTO_FAMILIES = {
    "PRESS_CONFERENCE": "PRESS_CONFERENCE",
    "OFF_FIELD_ODDITY": "OFF_FIELD_ODDITY",
    "CELEBRATION_FAN": "CELEBRATION",
}

FAMILY_TERMS = {
    "PRESS_CONFERENCE": (
        "press conference", "news conference", "postgame", "media availability",
        "reporters", "asked", "said", "media session", "locker room",
    ),
    "OFF_FIELD_ODDITY": (
        "hard knocks", "off-field", "training camp", "bizarre", "weird",
        "unusual", "funny", "viral", "prank", "costume", "outside football",
    ),
    "CELEBRATION_FAN": (
        "celebration", "celebrated", "dance", "taunt", "mascot", "fan",
        "crowd", "sideline",
    ),
}

PRIMARY_DOMAINS = {"nfl.com", "ncaa.org"}

MIN_PRIMARY_SCORE = 80
MIN_REPUTABLE_SCORE = 90
MAX_ARTICLE_FETCHES_DEFAULT = 100


def _ensure_schema(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS football_story_enrichment (
            candidate_id TEXT PRIMARY KEY,
            final_url TEXT,
            article_text_sha256 TEXT,
            article_text_chars INTEGER,
            extracted_headline TEXT,
            extracted_description TEXT,
            published_at TEXT,
            subject_type TEXT,
            subject_id TEXT,
            subject_label TEXT,
            family TEXT,
            confidence_score INTEGER,
            evidence_terms_json TEXT,
            decision TEXT NOT NULL,
            decision_reason TEXT,
            promoted_event_id TEXT,
            generated_question_count INTEGER NOT NULL DEFAULT 0,
            processed_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS story_generated_questions (
            question_id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            mechanic TEXT NOT NULL,
            difficulty_band TEXT,
            question_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'READY_FOR_BANK',
            created_at TEXT NOT NULL
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS ix_story_generated_candidate ON story_generated_questions(candidate_id,status)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_story_enrichment_decision ON football_story_enrichment(decision,family)")
    c.commit()


def _norm(text):
    return " ".join(re.sub(r"\s+", " ", str(text or "")).split())


def _family_evidence(family, article):
    combined = (str(article.get("headline") or "") + " "
                + str(article.get("description") or "") + " "
                + str(article.get("text") or "")).casefold()
    hits = [term for term in FAMILY_TERMS.get(family, ()) if term in combined]
    return hits


def _confidence(candidate, article, subject, evidence_terms):
    score = 0
    if subject.get("in_title"):
        score += 35
    if subject.get("in_text"):
        score += 25
    score += min(20, 6 * len(evidence_terms))
    if candidate["domain"] in PRIMARY_DOMAINS:
        score += 10
    else:
        score += 3
    if article.get("description"):
        score += 4
    if article.get("published"):
        score += 3
    if int(article.get("text_chars") or 0) >= 1500:
        score += 3
    return min(100, score)


def _topic_from_headline(headline, subject_label):
    headline = _norm(headline)
    label = str(subject_label or "").strip()
    if label:
        headline = re.sub(re.escape(label), "", headline, flags=re.I)
    headline = re.sub(r"^[\s:|—–-]+|[\s:|—–-]+$", "", headline)
    headline = re.sub(r"\s+", " ", headline).strip()
    return headline[:180]


def _neutral_summary(candidate, article, subject_label):
    family = str(candidate["family_hint"])
    topic = _topic_from_headline(article.get("headline") or candidate["title"], subject_label)
    family_label = {
        "PRESS_CONFERENCE": "media appearance",
        "OFF_FIELD_ODDITY": "off-field football story",
        "CELEBRATION_FAN": "football celebration or fan story",
    }.get(family, "football story")
    if topic:
        return f"{subject_label} was the subject of a documented {family_label} concerning {topic}."
    return f"{subject_label} was the subject of a documented {family_label}."


def _event_date(candidate, article):
    published = str(article.get("published") or "").strip()
    if published:
        m = re.match(r"(\d{4})[-/]?(\d{2})?[-/]?(\d{2})?", published)
        if m:
            y = m.group(1)
            mo = m.group(2) or "01"
            day = m.group(3) or "01"
            return f"{y}-{mo}-{day}"
    seen = str(candidate["seen_date"] or "")
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", seen)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def _publisher(domain):
    return {
        "nfl.com": "NFL.com",
        "ncaa.org": "NCAA",
        "espn.com": "ESPN",
        "cbssports.com": "CBS Sports",
        "foxsports.com": "FOX Sports",
        "si.com": "Sports Illustrated",
        "sports.yahoo.com": "Yahoo Sports",
        "usatoday.com": "USA Today",
    }.get(str(domain), str(domain))


def _evidence_tier(domain):
    return "PRIMARY" if str(domain) in PRIMARY_DOMAINS else "REPUTABLE_MEDIA"


def _build_event(candidate, article, subject, evidence_terms):
    family = str(candidate["family_hint"])
    event_type = AUTO_FAMILIES[family]
    eid = "evt_story_" + hashlib.sha256(
        (str(candidate["candidate_id"]) + "|" + str(article["final_url"])).encode()
    ).hexdigest()[:24]
    return {
        "event_id": eid,
        "event_type": event_type,
        "league": "CFB" if subject["entity_type"] == "CFB_PLAYER" else "NFL",
        "event_date": _event_date(candidate, article),
        "title": _norm(article.get("headline") or candidate["title"])[:240],
        "neutral_summary": _neutral_summary(candidate, article, subject["label"]),
        "source_url": article["final_url"],
        "source_publisher": _publisher(article["domain"]),
        "source_date": _event_date(candidate, article),
        "evidence_tier": _evidence_tier(article["domain"]),
        "verification_status": "VERIFIED",
        "subjects": [{
            "subject_type": subject["entity_type"],
            "subject_id": subject["entity_id"],
            "role": "speaker" if family == "PRESS_CONFERENCE" else "subject",
        }],
        "tags": [
            "story_factory",
            family.casefold(),
            *[term.replace(" ", "_") for term in evidence_terms[:5]],
        ],
        "sensitive": False,
    }


def _store_enrichment(c, candidate, *, article=None, subject=None, family=None,
                      score=None, evidence_terms=(), decision, reason=None,
                      event_id=None, generated=0):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    text_value = str((article or {}).get("text") or "")
    c.execute(
        """INSERT OR REPLACE INTO football_story_enrichment(
           candidate_id,final_url,article_text_sha256,article_text_chars,
           extracted_headline,extracted_description,published_at,
           subject_type,subject_id,subject_label,family,confidence_score,
           evidence_terms_json,decision,decision_reason,promoted_event_id,
           generated_question_count,processed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            str(candidate["candidate_id"]),
            (article or {}).get("final_url"),
            hashlib.sha256(text_value.encode()).hexdigest() if text_value else None,
            (article or {}).get("text_chars"),
            (article or {}).get("headline"),
            (article or {}).get("description"),
            (article or {}).get("published"),
            (subject or {}).get("entity_type"),
            (subject or {}).get("entity_id"),
            (subject or {}).get("label"),
            family,
            score,
            json.dumps(list(evidence_terms), sort_keys=True),
            decision,
            reason,
            event_id,
            int(generated),
            now,
        ),
    )
    c.execute(
        "UPDATE football_story_candidates SET status=?,promoted_event_id=? WHERE candidate_id=?",
        (
            "PROMOTED" if decision == "AUTO_PROMOTED" else decision,
            event_id,
            str(candidate["candidate_id"]),
        ),
    )
    c.commit()


def _persist_question(c, candidate_id, event_id, subject, question):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    c.execute(
        """INSERT OR REPLACE INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            str(question["question_id"]),
            str(candidate_id),
            str(event_id),
            str(subject["entity_type"]),
            str(subject["entity_id"]),
            str(question.get("mechanic") or ""),
            str(question.get("difficulty_band") or "") or None,
            json.dumps(question, sort_keys=True, ensure_ascii=False),
            "READY_FOR_BANK",
            now,
        ),
    )


def generate_questions_for_event(c, candidate_id, event_id, subject, *, max_questions=4):
    generated = []

    # Story-first question. This is valuable even when the graph is still too
    # thin for a deep multi-hop question.
    try:
        q = compile_progressive_identity(c, event_id)
        if q["answer"]["label"] and q["answer"]["label"] != q["answer"]["id"]:
            generated.append(q)
    except ValueError:
        pass

    # Deep mixed-source questions when the rest of the Engine provides enough
    # surrounding history. Add real distractors before storage.
    try:
        chains = discover_lore_chains(
            c,
            subject["entity_type"],
            subject["entity_id"],
            max_depth=6,
            max_chains=12,
        )
        for chain in chains:
            if len(generated) >= int(max_questions):
                break
            try:
                q = compile_lore_chain_question(c, chain, difficulty_band="HARD", variant=0)
                q = attach_deep_lore_options(c, q, difficulty_band="HARD")
                generated.append(q)
            except ValueError:
                continue
    except ValueError:
        pass

    unique = {}
    for q in generated:
        unique[str(q["question_id"])] = q
    generated = list(unique.values())[:max(1, int(max_questions))]

    for q in generated:
        _persist_question(c, candidate_id, event_id, subject, q)
    c.commit()
    return generated


def process_candidate(c, candidate, subject_index):
    family = str(candidate["family_hint"])
    if int(candidate["sensitive_hint"] or 0):
        _store_enrichment(
            c, candidate, family=family,
            decision="REVIEW_REQUIRED_SENSITIVE",
            reason="SENSITIVE_STORIES_NEVER_AUTO_PROMOTE",
        )
        return {"decision":"REVIEW_REQUIRED_SENSITIVE","generated":0}

    if family not in AUTO_FAMILIES:
        _store_enrichment(
            c, candidate, family=family,
            decision="REVIEW_REQUIRED",
            reason="FAMILY_NOT_AUTO_PROMOTABLE",
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}

    try:
        article = fetch_article(candidate["source_url"])
    except Exception as exc:
        _store_enrichment(
            c, candidate, family=family,
            decision="REVIEW_REQUIRED",
            reason="ARTICLE_FETCH:" + type(exc).__name__ + ":" + str(exc),
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}

    matches = match_subjects(
        subject_index,
        title=article.get("headline") or candidate["title"],
        text=article["text"],
    )
    subject = primary_identity_match(matches)
    if not subject:
        _store_enrichment(
            c, candidate, article=article, family=family,
            decision="REVIEW_REQUIRED",
            reason="NO_SINGLE_CANONICAL_PERSON_SUBJECT",
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}

    evidence_terms = _family_evidence(family, article)
    if not evidence_terms:
        _store_enrichment(
            c, candidate, article=article, subject=subject, family=family,
            decision="REVIEW_REQUIRED",
            reason="NO_FAMILY_SPECIFIC_EVIDENCE",
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}

    score = _confidence(candidate, article, subject, evidence_terms)
    threshold = (
        MIN_PRIMARY_SCORE
        if candidate["domain"] in PRIMARY_DOMAINS
        else MIN_REPUTABLE_SCORE
    )
    if score < threshold:
        _store_enrichment(
            c, candidate, article=article, subject=subject, family=family,
            score=score, evidence_terms=evidence_terms,
            decision="REVIEW_REQUIRED",
            reason=f"CONFIDENCE_BELOW_THRESHOLD:{score}<{threshold}",
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}

    event = _build_event(candidate, article, subject, evidence_terms)
    event_id = upsert_event(c, event)
    questions = generate_questions_for_event(
        c,
        candidate["candidate_id"],
        event_id,
        subject,
    )
    _store_enrichment(
        c, candidate, article=article, subject=subject, family=family,
        score=score, evidence_terms=evidence_terms,
        decision="AUTO_PROMOTED",
        event_id=event_id,
        generated=len(questions),
    )
    return {
        "decision":"AUTO_PROMOTED",
        "event_id":event_id,
        "generated":len(questions),
        "score":score,
    }


def run_story_to_trivia_factory(*, limit=MAX_ARTICLE_FETCHES_DEFAULT):
    c = engine_bootstrap.connect()
    _ensure_schema(c)
    subject_index = build_subject_index(c)

    rows = c.execute(
        """SELECT * FROM football_story_candidates
           WHERE status='REVIEW_PRIORITY'
           ORDER BY
             CASE evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
             seen_date DESC,
             candidate_id
           LIMIT ?""",
        (max(1, min(int(limit), 1000)),),
    ).fetchall()

    counts = Counter()
    generated_questions = 0
    examples = []

    for row in rows:
        result = process_candidate(c, row, subject_index)
        counts[result["decision"]] += 1
        generated_questions += int(result.get("generated") or 0)
        if result["decision"] == "AUTO_PROMOTED" and len(examples) < 10:
            examples.append({
                "candidate_id": row["candidate_id"],
                "title": row["title"],
                "event_id": result.get("event_id"),
                "generated": result.get("generated"),
                "confidence": result.get("score"),
            })

    queue = c.execute(
        """SELECT status,COUNT(*) n FROM football_story_candidates
           GROUP BY status ORDER BY status"""
    ).fetchall()
    ready = c.execute(
        """SELECT COUNT(*) FROM story_generated_questions
           WHERE status='READY_FOR_BANK'"""
    ).fetchone()[0]
    c.close()

    return {
        "processed_candidates": len(rows),
        "decisions": dict(counts),
        "generated_questions_this_run": generated_questions,
        "ready_question_total": int(ready),
        "queue_status": {str(r["status"]): int(r["n"]) for r in queue},
        "examples": examples,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=MAX_ARTICLE_FETCHES_DEFAULT)
    args = ap.parse_args()
    print(json.dumps(
        run_story_to_trivia_factory(limit=args.limit),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
