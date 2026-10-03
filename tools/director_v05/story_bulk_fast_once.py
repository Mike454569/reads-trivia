"""One-off fast bulk promotion worker for production Story Factory.

Purpose: turn already-harvested, non-sensitive primary-source candidates into
verified lore + immediately playable story questions without the expensive
multi-hop chain crawl. Candidates with no clear title identity are left in the
queue for slower review rather than discarded.
"""
from __future__ import annotations
import datetime as dt
import json
import sqlite3
import time
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.event_ingest import upsert_event
from tools.director_v05.lore_mechanics import compile_progressive_identity
from tools.director_v05.lore_distractors import attach_deep_lore_options
from tools.director_v05.story_article_extract import fetch_article
from tools.director_v05.story_subject_match import build_subject_index, match_subjects, primary_identity_match
from tools.director_v05.story_to_trivia_factory import (
    AUTO_FAMILIES,
    PRIMARY_DOMAINS,
    MIN_PRIMARY_SCORE,
    _ensure_schema,
    _family_evidence,
    _confidence,
    _build_event,
)

BATCH_TARGET=40
SCAN_LIMIT=1500
BUSY_MS=120000

def commit_retry(c, attempts=8):
    for attempt in range(1, attempts+1):
        try:
            c.commit()
            return
        except sqlite3.OperationalError as exc:
            msg=str(exc).casefold()
            if "locked" not in msg and "busy" not in msg:
                raise
            if attempt==attempts:
                raise
            time.sleep(2*attempt)

def store_review(c, candidate_id, decision, reason):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    c.execute(
        """INSERT OR REPLACE INTO football_story_enrichment(
           candidate_id,decision,decision_reason,processed_at,
           generated_question_count)
           VALUES(?,?,?,?,0)""",
        (candidate_id,decision,reason,now),
    )
    c.execute(
        "UPDATE football_story_candidates SET status=? WHERE candidate_id=?",
        (decision,candidate_id),
    )
    commit_retry(c)

def persist_question(c,candidate_id,event_id,subject,q,status):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    c.execute(
        """INSERT OR REPLACE INTO story_generated_questions(
           question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
           difficulty_band,question_json,status,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            str(q["question_id"]),candidate_id,event_id,
            str(subject["entity_type"]),str(subject["entity_id"]),
            str(q.get("mechanic") or ""),
            str(q.get("difficulty_band") or "HARD"),
            json.dumps(q,sort_keys=True,ensure_ascii=False),
            status,now,
        ),
    )

def store_promoted(c,candidate,article,subject,family,score,evidence,event_id,generated):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    text_value=str(article.get("text") or "")
    import hashlib
    c.execute(
        """INSERT OR REPLACE INTO football_story_enrichment(
           candidate_id,final_url,article_text_sha256,article_text_chars,
           extracted_headline,extracted_description,published_at,
           subject_type,subject_id,subject_label,family,confidence_score,
           evidence_terms_json,decision,decision_reason,promoted_event_id,
           generated_question_count,processed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            str(candidate["candidate_id"]),article.get("final_url"),
            hashlib.sha256(text_value.encode()).hexdigest() if text_value else None,
            article.get("text_chars"),article.get("headline"),
            article.get("description"),article.get("published"),
            subject.get("entity_type"),subject.get("entity_id"),subject.get("label"),
            family,score,json.dumps(list(evidence),sort_keys=True),
            "AUTO_PROMOTED_FAST",None,event_id,int(generated),now,
        ),
    )
    c.execute(
        "UPDATE football_story_candidates SET status='PROMOTED',promoted_event_id=? WHERE candidate_id=?",
        (event_id,str(candidate["candidate_id"])),
    )
    commit_retry(c)

def main():
    c=engine_bootstrap.connect()
    c.row_factory=sqlite3.Row
    c.execute(f"PRAGMA busy_timeout={BUSY_MS}")
    _ensure_schema(c)
    subject_index=build_subject_index(c)

    rows=c.execute(
        """SELECT * FROM football_story_candidates
           WHERE status='REVIEW_PRIORITY'
             AND sensitive_hint=0
             AND evidence_tier_hint='PRIMARY'
             AND family_hint IN ('PRESS_CONFERENCE','OFF_FIELD_ODDITY','CELEBRATION_FAN')
           ORDER BY seen_date DESC,candidate_id
           LIMIT ?""",
        (SCAN_LIMIT,),
    ).fetchall()

    selected=[]
    for row in rows:
        title=str(row["title"] or "")
        matches=match_subjects(subject_index,title=title,text="")
        subject=primary_identity_match(matches)
        if subject:
            selected.append(row)
        if len(selected)>=BATCH_TARGET:
            break

    counts=Counter()
    examples=[]
    for idx,row in enumerate(selected,1):
        cid=str(row["candidate_id"])
        family=str(row["family_hint"])
        try:
            article=fetch_article(row["source_url"])
        except Exception as exc:
            store_review(c,cid,"REVIEW_REQUIRED","ARTICLE_FETCH:"+type(exc).__name__+":"+str(exc))
            counts["FETCH_REVIEW"]+=1
            continue

        matches=match_subjects(
            subject_index,
            title=article.get("headline") or row["title"],
            text=article.get("text") or "",
        )
        subject=primary_identity_match(matches)
        if not subject:
            store_review(c,cid,"REVIEW_REQUIRED","NO_SINGLE_CANONICAL_PERSON_SUBJECT")
            counts["SUBJECT_REVIEW"]+=1
            continue

        evidence=_family_evidence(family,article)
        if not evidence:
            store_review(c,cid,"REVIEW_REQUIRED","NO_FAMILY_SPECIFIC_EVIDENCE")
            counts["EVIDENCE_REVIEW"]+=1
            continue

        score=_confidence(row,article,subject,evidence)
        if score<MIN_PRIMARY_SCORE:
            store_review(c,cid,"REVIEW_REQUIRED",f"CONFIDENCE_BELOW_THRESHOLD:{score}<{MIN_PRIMARY_SCORE}")
            counts["CONFIDENCE_REVIEW"]+=1
            continue

        try:
            event=_build_event(row,article,subject,evidence)
            event_id=upsert_event(c,event)
            commit_retry(c)
        except Exception as exc:
            store_review(c,cid,"REVIEW_REQUIRED","EVENT_BUILD:"+type(exc).__name__+":"+str(exc))
            counts["EVENT_REVIEW"]+=1
            continue

        try:
            q=compile_progressive_identity(c,event_id)
            status="READY_FOR_FORMAT_BANK"
            try:
                q=attach_deep_lore_options(c,q,difficulty_band="HARD")
                status="READY_FOR_BANK"
                counts["MCQ"]+=1
            except Exception:
                counts["PROGRESSIVE"]+=1
            persist_question(c,cid,event_id,subject,q,status)
            commit_retry(c)
            store_promoted(c,row,article,subject,family,score,evidence,event_id,1)
            counts["PROMOTED"]+=1
            if len(examples)<12:
                examples.append({
                    "candidate_id":cid,
                    "event_id":event_id,
                    "title":str(row["title"]),
                    "subject":subject.get("label"),
                    "mechanic":q.get("mechanic"),
                    "status":status,
                    "score":score,
                })
        except Exception as exc:
            store_review(c,cid,"REVIEW_REQUIRED","QUESTION_BUILD:"+type(exc).__name__+":"+str(exc))
            counts["QUESTION_REVIEW"]+=1

    queue={
        str(r["status"]):int(r["n"])
        for r in c.execute("SELECT status,COUNT(*) n FROM football_story_candidates GROUP BY status").fetchall()
    }
    qstats={
        str(r["status"]):int(r["n"])
        for r in c.execute("SELECT status,COUNT(*) n FROM story_generated_questions GROUP BY status").fetchall()
    }
    c.close()
    print(json.dumps({
        "scanned":len(rows),
        "selected":len(selected),
        "processed":sum(counts.values())-counts["MCQ"]-counts["PROGRESSIVE"],
        "counts":dict(counts),
        "queue":queue,
        "question_status":qstats,
        "examples":examples,
    },sort_keys=True))

if __name__=="__main__":
    main()
