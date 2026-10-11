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
import sqlite3
import time
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .event_ingest import upsert_event
from .lore_chains import discover_lore_chains, compile_lore_chain_question
from .lore_distractors import attach_deep_lore_options
from .lore_mechanics import compile_progressive_identity
from .story_article_extract import fetch_article
from .story_subject_match import build_subject_index, match_subjects, primary_identity_match
from .story_multiformat import generate_story_formats_for_event, generate_story_matching_round
from .story_factory_v2 import prepare_story_question
from .story_sqlite import (
    prepare_write_connection as _prepare_write_connection,
    commit_with_retry as _commit_with_retry,
)


AUTO_FAMILIES = {
    # Exact v3 taxonomy. The publisher headline is not proof: every one of
    # these still has to pass article-text, identity, evidence and confidence
    # gates before a verified event can be created.
    "BIZARRE_MOMENT": "ON_FIELD_ODDITY",
    "DRAFT_BUST": "HISTORICAL_MILESTONE",
    "TRADE_ODDITY": "TRADE",
    "SIDELINE_INCIDENT": "ON_FIELD_ODDITY",
    "COACHING_MELTDOWN": "COACHING_MOVE",
    "CELEBRATION_CONTROVERSY": "CELEBRATION",
    "RECRUITING_CHAOS": "HISTORICAL_MILESTONE",
    "RECORD_ODDITY": "HISTORICAL_MILESTONE",
    "INFAMOUS_MISTAKE": "ON_FIELD_ODDITY",
    "RIVALRY_INCIDENT": "ON_FIELD_ODDITY",
    "TRANSFER_NIL_CHAOS": "HISTORICAL_MILESTONE",
    "PLAYOFF_FORGOTTEN": "ON_FIELD_ODDITY",
    "PRESS_CONFERENCE": "PRESS_CONFERENCE",
    "OFF_FIELD_ODDITY": "OFF_FIELD_ODDITY",
    "CELEBRATION_FAN": "CELEBRATION",
    "DRAFT_CHAOS": "HISTORICAL_MILESTONE",
    "COMEBACK_RETURN": "COMEBACK",
    "TRADE_CHAOS": "TRADE",
    "BUST_REDEMPTION": "HISTORICAL_MILESTONE",
    "GAME_ODDITY": "ON_FIELD_ODDITY",
    "COACHING_ODDITY": "COACHING_MOVE",
    "RIVALRY_ODDITY": "ON_FIELD_ODDITY",
    "RULE_ODDITY": "RULE_ODDITY",
}

FAMILY_TERMS = {
    "BIZARRE_MOMENT": ("bizarre", "weird play", "strange play", "unusual touchdown", "crazy ending", "rare play"),
    "DRAFT_BUST": ("draft bust", "first-round bust", "draft failure", "draft disappointment"),
    "TRADE_ODDITY": ("traded", "trade", "trade request", "trade deal", "blockbuster"),
    "SIDELINE_INCIDENT": ("sideline incident", "sideline altercation", "sideline fight", "sideline confrontation"),
    "COACHING_MELTDOWN": ("coach rant", "meltdown", "postgame rant", "press conference"),
    "CELEBRATION_CONTROVERSY": ("taunting", "celebration penalty", "celebration fine", "controversial celebration"),
    "RECRUITING_CHAOS": ("recruiting flip", "commitment flip", "recruiting controversy", "decommitment"),
    "RECORD_ODDITY": ("strange record", "bizarre record", "record-breaking", "unusual record"),
    "INFAMOUS_MISTAKE": ("botched play", "costly mistake", "blunder", "wrong way", "forgot the rules"),
    "RIVALRY_INCIDENT": ("rivalry prank", "rivalry incident", "rivalry fight", "rivalry trophy"),
    "TRANSFER_NIL_CHAOS": ("transfer portal", "nil controversy", "nil dispute", "transfer flip"),
    "PLAYOFF_FORGOTTEN": ("playoff upset", "forgotten playoff", "postseason upset", "forgotten bowl"),
    "PRESS_CONFERENCE": (
        "press conference", "news conference", "media availability",
        "spoke to reporters", "told reporters", "addressed reporters",
        "speaking to reporters", "speaking with reporters",
        "postgame press conference", "postgame media session",
        "during his press conference", "during the press conference",
    ),
    "OFF_FIELD_ODDITY": (
        "hard knocks", "off-field", "training camp", "bizarre", "weird",
        "unusual", "funny", "viral", "prank", "costume", "outside football",
    ),
    "CELEBRATION_FAN": (
        "celebration", "celebrated", "dance", "taunt", "mascot", "fan",
        "crowd", "sideline", "end zone",
    ),
    "DRAFT_CHAOS": (
        "draft", "trade up", "trade down", "draft-day", "draft day", "slide",
        "surprise pick", "unexpected pick", "mr. irrelevant", "mr irrelevant",
    ),
    "COMEBACK_RETURN": (
        "comeback", "retirement", "came out of retirement", "returned",
        "unretired", "career comeback", "return to football",
    ),
    "TRADE_CHAOS": (
        "trade", "traded", "blockbuster", "trade request", "trade deadline",
    ),
    "BUST_REDEMPTION": (
        "draft bust", "bust", "career turnaround", "late bloomer", "revival",
        "breakout", "redeemed", "redemption",
    ),
    "GAME_ODDITY": (
        "weird play", "bizarre play", "strange play", "unusual touchdown",
        "rare play", "crazy ending", "accidental touchdown", "odd play",
    ),
    "COACHING_ODDITY": (
        "coach", "rant", "fired", "sideline", "celebration", "prank", "quote",
    ),
    "RIVALRY_ODDITY": (
        "rivalry", "prank", "trophy", "tradition", "crazy ending",
    ),
    "RULE_ODDITY": (
        "rule", "penalty", "targeting", "kickoff", "loophole", "officiating",
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
    _commit_with_retry(c)


def _norm(text):
    return " ".join(re.sub(r"\s+", " ", str(text or "")).split())


def _family_evidence(family, article):
    """Require family-defining evidence, not generic football vocabulary.

    An injury article that says someone 'said' something is not proof of a
    press conference. Likewise, an ordinary trade isn't a trade oddity.
    """
    combined = (str(article.get("headline") or "") + " "
                + str(article.get("description") or "") + " "
                + str(article.get("text") or "")).casefold()
    if family == "TRADE_ODDITY":
        if not any(term in combined for term in (
            "unusual trade", "bizarre trade", "shocking trade",
            "surprise trade", "unexpected trade", "trade controversy",
            "trade request", "historic trade", "strange trade",
        )):
            return []
    return [term for term in FAMILY_TERMS.get(family, ()) if term in combined]


def _event_evidence(article, subject, family):
    """Ground one concrete, subject-linked occurrence in the fetched article.

    This deliberately rejects broad topic mentions and opinions. The selected
    passage must state the event and name the *same canonical subject*.
    Headlines, index snippets and publication dates are insufficient alone.
    """
    body = _norm(article.get("text"))
    person = _norm(subject.get("label"))
    if len(body) < 250 or len(person) < 5:
        return None
    # Prefer complete sentences over arbitrary sliding-word coincidence.
    fragments = [
        passage.strip()
        for passage in re.split(r"(?<=[.!?])\s+|\n+", body)
        if passage.strip()
    ]
    triggers = {
        "PRESS_CONFERENCE": (
            r"\b(?:said|told|addressed|spoke to)\s+(?:the\s+)?reporters\b",
            r"\b(?:held|spoke at|addressed)\s+(?:a|the|his|her)\s+press conference\b",
            r"\b(?:postgame|pregame)\s+(?:press conference|media availability)\b",
        ),
        "TRADE_ODDITY": (
            r"\b(?:shocking|unexpected|surprise|bizarre|unusual|historic)\s+trade\b",
            r"\btrade request\b",
        ),
        "TRADE_CHAOS": (r"\b(?:was|were|has been|had been) traded\b", r"\btrade request\b"),
        "COMEBACK_RETURN": (
            r"\b(?:returned|came back|unretired)\s+(?:to|from|after)\b",
            r"\bcame out of retirement\b",
        ),
        "OFF_FIELD_ODDITY": (r"\b(?:prank|costume|bizarre|unusual|strange|viral|funny)\b",),
        "BIZARRE_MOMENT": (r"\b(?:bizarre|unusual|strange|rare)\s+(?:play|touchdown|ending)\b",),
    }
    patterns = triggers.get(family)
    if not patterns:
        # All other families remain review-only until a specific
        # event-relation extractor has been implemented and tested.
        return None
    person_key = person.casefold()
    for passage in fragments:
        low = passage.casefold()
        # Exact person boundaries avoid identifying an unrelated name fragment.
        if not re.search(r"(?<![a-z0-9])" + re.escape(person_key) + r"(?![a-z0-9])", low):
            continue
        for trigger in patterns:
            if re.search(trigger, low):
                # Named speaker plus literal event assertion: provenance is
                # retained as a SHA, not an unlicensed full-article archive.
                return {
                    "passage_sha256": hashlib.sha256(passage.encode()).hexdigest(),
                    "matched_trigger": trigger,
                    "passage_chars": len(passage),
                }
    return None

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
        "DRAFT_CHAOS": "draft-day football story",
        "COMEBACK_RETURN": "football comeback or return story",
        "TRADE_CHAOS": "football trade story",
        "BUST_REDEMPTION": "career arc or draft-outcome story",
        "GAME_ODDITY": "unusual on-field football story",
        "COACHING_ODDITY": "coaching story",
        "RIVALRY_ODDITY": "rivalry football story",
        "RULE_ODDITY": "football rules story",
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


def _infer_league(article, subject):
    if subject["entity_type"] == "NFL_PLAYER":
        return "NFL"
    if subject["entity_type"] == "CFB_PLAYER":
        return "CFB"
    copy = (
        str(article.get("headline") or "") + " "
        + str(article.get("description") or "") + " "
        + str(article.get("text") or "")
    ).casefold()
    nfl_hits = sum(term in copy for term in (" nfl ", "super bowl", "national football league"))
    cfb_hits = sum(term in copy for term in ("college football", " ncaa ", "fbs", "cfp", "bowl game"))
    if nfl_hits > cfb_hits and nfl_hits > 0:
        return "NFL"
    if cfb_hits > nfl_hits and cfb_hits > 0:
        return "CFB"
    return None


def _build_event(candidate, article, subject, evidence_terms):
    family = str(candidate["family_hint"])
    event_type = AUTO_FAMILIES[family]
    league = _infer_league(article, subject)
    if not league:
        raise ValueError("AMBIGUOUS_STORY_LEAGUE")
    eid = "evt_story_" + hashlib.sha256(
        (str(candidate["candidate_id"]) + "|" + str(article["final_url"])).encode()
    ).hexdigest()[:24]
    return {
        "event_id": eid,
        "event_type": event_type,
        "league": league,
        # Article publication time is provenance, not automatically the date
        # the described football event happened. Never fabricate chronology.
        "event_date": None,
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
    _commit_with_retry(c)


def _persist_question(c, candidate_id, event_id, subject, question):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    mechanic = str(question.get("mechanic") or "")
    options = list(question.get("options") or [])
    status = (
        "READY_FOR_BANK"
        if mechanic == "MULTIPLE_CHOICE"
        and len(options) == 4
        and len({str(x).casefold().strip() for x in options}) == 4
        else "READY_FOR_FORMAT_BANK"
    )
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
            mechanic,
            str(question.get("difficulty_band") or "") or None,
            json.dumps(question, sort_keys=True, ensure_ascii=False),
            status,
            now,
        ),
    )


def generate_questions_for_event(
    c, candidate_id, event_id, subject, *, max_questions=4,
    include_deep_chains=True,
):
    generated = []

    # Story-first question. This is valuable even when the graph is still too
    # thin for a deep multi-hop question.
    try:
        q = compile_progressive_identity(c, event_id)
        if q["answer"]["label"] and q["answer"]["label"] != q["answer"]["id"]:
            try:
                q = attach_deep_lore_options(
                    c,
                    q,
                    difficulty_band="HARD",
                )
            except ValueError:
                # Keep the progressive artifact for a future Progressive Clue
                # renderer even when a safe four-choice set is unavailable.
                pass
            generated.append(q)
    except ValueError:
        pass

    # Deep mixed-source questions are an enrichment layer, not a prerequisite
    # for making a verified story playable. Bulk production can disable this
    # expensive graph crawl and backfill it later.
    if include_deep_chains:
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
        try:
            q = prepare_story_question(q)
        except ValueError:
            continue
        unique[str(q["question_id"])] = q
    generated = list(unique.values())[:max(1, int(max_questions))]

    for q in generated:
        _persist_question(c, candidate_id, event_id, subject, q)
    _commit_with_retry(c)
    return generated


def process_candidate(c, candidate, subject_index, *, include_deep_chains=True):
    family = str(candidate["family_hint"])
    if int(candidate["sensitive_hint"] or 0):
        _store_enrichment(
            c, candidate, family=family,
            decision="REVIEW_REQUIRED_SENSITIVE",
            reason="SENSITIVE_STORIES_NEVER_AUTO_PROMOTE",
        )
        return {"decision":"REVIEW_REQUIRED_SENSITIVE","generated":0}

    # Sensitive/legal stories are never automatically promoted even when the
    # original harvest mislabeled sensitive_hint=0.
    if family == "DISCIPLINE_LEGAL":
        _store_enrichment(
            c, candidate, family=family,
            decision="REVIEW_REQUIRED_SENSITIVE",
            reason="SENSITIVE_STORIES_NEVER_AUTO_PROMOTE",
        )
        return {"decision": "REVIEW_REQUIRED_SENSITIVE", "generated": 0}

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

    # The publisher's extracted og:title can differ from the headline stored
    # by the article index (e.g. SEO rewrites). Both are grounded source
    # metadata. Preserve both for headline-identity matching, while still
    # requiring the exact canonical name to occur in the fetched article body.
    source_headlines = " ".join(dict.fromkeys(
        str(x).strip() for x in (candidate["title"], article.get("headline"))
        if str(x or "").strip()
    ))
    matches = match_subjects(
        subject_index,
        title=source_headlines,
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

    event_evidence = _event_evidence(article, subject, family)
    if event_evidence is None:
        _store_enrichment(
            c, candidate, article=article, subject=subject, family=family,
            evidence_terms=evidence_terms, decision="REVIEW_REQUIRED",
            reason="NO_SUBJECT_LINKED_EVENT_PASSAGE",
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

    try:
        event = _build_event(candidate, article, subject, evidence_terms)
    except ValueError as exc:
        _store_enrichment(
            c, candidate, article=article, subject=subject, family=family,
            score=score, evidence_terms=evidence_terms,
            decision="REVIEW_REQUIRED",
            reason=str(exc),
        )
        return {"decision":"REVIEW_REQUIRED","generated":0}
    # Record the checkable passage fingerprint with the sourced event.
    # Do not equate a generic headline or commentary with a verified fact.
    event["tags"].append("passage_sha256_" + event_evidence["passage_sha256"][:16])
    event_id = upsert_event(c, event)
    questions = generate_questions_for_event(
        c,
        candidate["candidate_id"],
        event_id,
        subject,
        include_deep_chains=include_deep_chains,
    )
    formats = generate_story_formats_for_event(
        c,
        candidate_id=candidate["candidate_id"],
        event_id=event_id,
        subject_type=subject["entity_type"],
        subject_id=subject["entity_id"],
    )
    _store_enrichment(
        c, candidate, article=article, subject=subject, family=family,
        score=score, evidence_terms=evidence_terms,
        decision="AUTO_PROMOTED",
        event_id=event_id,
        generated=len(questions) + int(formats.get("generated_count") or 0),
    )
    return {
        "decision":"AUTO_PROMOTED",
        "event_id":event_id,
        "generated":len(questions) + int(formats.get("generated_count") or 0),
        "identity_questions":len(questions),
        "format_questions":int(formats.get("generated_count") or 0),
        "format_rejections":formats.get("rejected", []),
        "score":score,
    }


# Queue priority is discovery order only. It does not make a candidate
# VERIFIED: the article parser, canonical identity, family and event passage
# gates still run after selection.
EVENT_DISCOVERY_HEADLINES = {
    "PRESS_CONFERENCE": (
        "press conference", "news conference", "speaks to reporters",
        "spoke to reporters", "told reporters", "addressed reporters",
        "media availability", "postgame comments",
    ),
    "TRADE_ODDITY": (
        "shocking trade", "surprise trade", "unexpected trade",
        "bizarre trade", "unusual trade", "trade request",
    ),
    "TRADE_CHAOS": ("traded to", "traded for", "trade request", "blockbuster trade"),
    "COMEBACK_RETURN": (
        "came out of retirement", "returns from retirement",
        "unretires", "returns to football", "comeback after",
    ),
    "OFF_FIELD_ODDITY": (
        "bizarre", "strange", "prank", "costume", "weird", "funny",
    ),
    "BIZARRE_MOMENT": (
        "bizarre play", "unusual touchdown", "strange play",
        "rare play", "bizarre ending",
    ),
}
DISCOVERY_LOW_SIGNAL = (
    "mock draft", "power rankings", "fantasy football",
    "betting odds", "prediction", "weekly picks",
)


def _story_candidate_priority(row):
    """Pure discovery ranking; fail closed on unimplemented story families."""
    family = str(row["family_hint"])
    terms = EVENT_DISCOVERY_HEADLINES.get(family)
    if not terms or family not in AUTO_FAMILIES:
        return None
    if int(row["sensitive_hint"] or 0):
        return None
    if str(row["status"]) != "REVIEW_PRIORITY":
        return None
    headline = re.sub(r"\\s+", " ", str(row["title"] or "").casefold()).strip()
    if len(headline) < 16 or any(term in headline for term in DISCOVERY_LOW_SIGNAL):
        return None
    matched = [term for term in terms if term in headline]
    if not matched:
        return None
    # Longer concrete phrases outrank generic press mentions. Primary
    # publisher stories break ties ahead of secondary syndicated coverage.
    primary = int(str(row["domain"]) in PRIMARY_DOMAINS)
    return (max(map(len, matched)), len(matched), primary)


def _select_event_rich_candidates(c, *, limit, scan_limit=5000):
    """Select bounded distinct URLs from approved review-priority queue.

    Existing production candidates retain their status until the independent
    article-level review makes an explicit decision.
    """
    allowed = (
        "nfl.com", "ncaa.org", "espn.com", "cbssports.com",
        "foxsports.com", "si.com", "sports.yahoo.com", "usatoday.com",
    )
    marks = ",".join("?" for _ in allowed)
    rows = c.execute(
        f"""SELECT * FROM football_story_candidates
            WHERE status='REVIEW_PRIORITY'
              AND COALESCE(sensitive_hint, 0)=0
              AND domain IN ({marks})
            ORDER BY first_harvested_at DESC,candidate_id
            LIMIT ?""",
        (*allowed, max(1, min(int(scan_limit), 10000))),
    ).fetchall()
    ranked = []
    seen_urls = set()
    for row in rows:
        priority = _story_candidate_priority(row)
        if priority is None:
            continue
        url = str(row["source_url"] or "").strip().casefold()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        ranked.append((priority, row))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in ranked[:max(1, min(int(limit), 100))]]


def run_story_to_trivia_factory(
    *, limit=MAX_ARTICLE_FETCHES_DEFAULT, include_deep_chains=True
):
    c = _prepare_write_connection(engine_bootstrap.connect())
    _ensure_schema(c)
    subject_index = build_subject_index(c)

    rows = _select_event_rich_candidates(c, limit=limit)

    counts = Counter()
    generated_questions = 0
    examples = []

    for row in rows:
        result = process_candidate(
            c,
            row,
            subject_index,
            include_deep_chains=include_deep_chains,
        )
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

    matching = generate_story_matching_round(c, limit=4)

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
        "matching_round_generated": bool(matching.get("generated")),
        "matching_round_reason": matching.get("reason"),
        "include_deep_chains": bool(include_deep_chains),
        "examples": examples,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=MAX_ARTICLE_FETCHES_DEFAULT)
    ap.add_argument("--fast", action="store_true",
                    help="skip expensive deep-chain enrichment; keep story-first questions")
    args = ap.parse_args()
    print(json.dumps(
        run_story_to_trivia_factory(
            limit=args.limit,
            include_deep_chains=not args.fast,
        ),
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
