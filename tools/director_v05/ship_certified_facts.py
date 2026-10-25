"""Controlled insertion of genuinely certified Fact trivia for already sourced events.

The live runner loads the tested lore/quality modules before importing this.
Maximum 20 events; INSERT OR IGNORE, never overwrite existing content.
"""
import json
import sqlite3
from datetime import datetime, timezone
from tools.director_v05.lore_mechanics import compile_fact_or_fake
from tools.director_v05.story_quality_certification import certify_question

def fill(db, limit=20):
    limit=max(1,min(int(limit),20))
    before=db.execute("SELECT COUNT(*) FROM story_generated_questions WHERE status IN ('READY_FOR_BANK','READY_FOR_FORMAT_BANK')").fetchone()[0]
    rows=db.execute("""
        SELECT e.event_id,f.candidate_id,s.subject_type,s.subject_id
        FROM universal_event e
        JOIN football_story_enrichment f ON f.promoted_event_id=e.event_id
        JOIN universal_event_subject s ON s.event_id=e.event_id
        WHERE e.verification_status='VERIFIED' AND COALESCE(e.sensitive,0)=0
          AND UPPER(e.league) IN ('NFL','CFB') AND f.decision='AUTO_PROMOTED'
        GROUP BY e.event_id ORDER BY e.event_id LIMIT 160
    """).fetchall()
    output={"scanned":0,"certified_candidates":0,"inserted":0,"rejected":0,"before_ready":before}
    for row in rows:
        if output["scanned"]>=limit: break
        event_id=str(row["event_id"])
        # Preserve existing certified variants. Re-run only where missing.
        qid_row=db.execute("SELECT COUNT(*) FROM story_generated_questions WHERE event_id=? AND mechanic='FACT_OR_FAKE' AND status='READY_FOR_FORMAT_BANK'",(event_id,)).fetchone()
        if qid_row[0]: continue
        output["scanned"]+=1
        try:
            q=compile_fact_or_fake(db,event_id,fake=False)
            defects=certify_question(q,expected_event_id=event_id)
            if defects:
                output["rejected"]+=1
                continue
            output["certified_candidates"]+=1
            # Only a real, complete fact may be stored. No fake claims, no reclassification.
            assert q["answer"]["id"]=="FACT" and q["mechanic"]=="FACT_OR_FAKE"
            db.execute("""INSERT OR IGNORE INTO story_generated_questions
                (question_id,candidate_id,event_id,subject_type,subject_id,mechanic,
                 difficulty_band,question_json,status,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",(
                str(q["question_id"]),str(row["candidate_id"]),event_id,
                str(row["subject_type"]),str(row["subject_id"]),"FACT_OR_FAKE",
                None,json.dumps(q,ensure_ascii=False,sort_keys=True),"READY_FOR_FORMAT_BANK",
                datetime.now(timezone.utc).isoformat()))
            output["inserted"]+=db.execute("SELECT changes()").fetchone()[0]
            db.commit()
        except (ValueError,TypeError,KeyError,AssertionError,sqlite3.Error):
            db.rollback()
            output["rejected"]+=1
    output["after_ready"]=db.execute("SELECT COUNT(*) FROM story_generated_questions WHERE status IN ('READY_FOR_BANK','READY_FOR_FORMAT_BANK')").fetchone()[0]
    output["delta"]=output["after_ready"]-before
    return output

if __name__=="__main__":
    import sys
    c=sqlite3.connect("/data/engine/reads_football_v4.0.sqlite",timeout=15)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA busy_timeout=15000")
    try:
        result=fill(c)
        print("CERTIFIED_FACT_BATCH",json.dumps(result,sort_keys=True),flush=True)
        if result["delta"]<=0: sys.exit(3)
    finally:c.close()
