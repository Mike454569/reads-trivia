"""Insert at most ten genuinely certified Who Am I questions from verified lore.

Use through a single-writer controlled run only. Never fabricate clues.
"""
import json,sqlite3
from datetime import datetime,timezone
from tools.director_v05.lore_mechanics import compile_progressive_identity
from tools.director_v05.story_quality_certification import certify_question

def fill(db,limit=10):
    before=db.execute("SELECT COUNT(*) FROM story_generated_questions WHERE mechanic='PROGRESSIVE_CLUE' AND status='READY_FOR_BANK'").fetchone()[0]
    rows=db.execute("""SELECT e.event_id, f.candidate_id, s.subject_type, s.subject_id
      FROM universal_event e
      JOIN football_story_enrichment f ON f.promoted_event_id=e.event_id
      JOIN universal_event_subject s ON s.event_id=e.event_id
      WHERE e.verification_status='VERIFIED' AND COALESCE(e.sensitive,0)=0
        AND e.league='NFL' AND s.subject_type IN ('NFL_PLAYER','PLAYER')
        AND f.decision='AUTO_PROMOTED'
      GROUP BY e.event_id ORDER BY e.event_id LIMIT 100""").fetchall()
    report={"tested":0,"certified":0,"inserted":0,"rejected":0,"before":before}
    for row in rows:
        if report["inserted"]>=limit: break
        eid=row["event_id"]
        if db.execute("SELECT 1 FROM story_generated_questions WHERE event_id=? AND mechanic='PROGRESSIVE_CLUE' AND status='READY_FOR_BANK' LIMIT 1",(eid,)).fetchone():continue
        report["tested"]+=1
        try:
            q=compile_progressive_identity(db,eid)
            defects=certify_question(q,expected_event_id=eid)
            if defects:
                report["rejected"]+=1
                continue
            report["certified"]+=1
            db.execute("""INSERT OR IGNORE INTO story_generated_questions
              (question_id,candidate_id,event_id,subject_type,subject_id,mechanic,difficulty_band,question_json,status,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?)""",
              (q["question_id"],row["candidate_id"],eid,row["subject_type"],row["subject_id"],
              "PROGRESSIVE_CLUE",None,json.dumps(q,sort_keys=True),"READY_FOR_BANK",datetime.now(timezone.utc).isoformat()))
            report["inserted"]+=db.execute("SELECT changes()").fetchone()[0]
            db.commit()
        except (ValueError,KeyError,TypeError,sqlite3.Error):
            db.rollback()
            report["rejected"]+=1
    report["after"]=db.execute("SELECT COUNT(*) FROM story_generated_questions WHERE mechanic='PROGRESSIVE_CLUE' AND status='READY_FOR_BANK'").fetchone()[0]
    report["delta"]=report["after"]-before
    return report
