"""Fast one-off compiler from already-reviewed production lore events."""
from __future__ import annotations
import datetime as dt
import json
import sqlite3
import time

from tools.quiz_export import engine as engine_bootstrap
from tools.director_v05.lore_mechanics import compile_progressive_identity
from tools.director_v05.lore_distractors import attach_deep_lore_options

def commit_retry(c, attempts=8):
    for i in range(attempts):
        try:
            c.commit()
            return
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).casefold() and "busy" not in str(exc).casefold():
                raise
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))

def main():
    c=engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=120000")
    c.execute("""
        CREATE TABLE IF NOT EXISTS story_generated_questions(
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
    commit_retry(c)

    rows=c.execute("""
        SELECT e.event_id,s.subject_type,s.subject_id
        FROM universal_event e
        JOIN universal_event_subject s ON s.event_id=e.event_id
        WHERE e.event_id LIKE 'reviewed_%'
          AND e.verification_status='VERIFIED'
          AND e.sensitive=0
        GROUP BY e.event_id,s.subject_type,s.subject_id
        ORDER BY e.event_id
    """).fetchall()

    out={"attempted_events":0,"mcq":0,"progressive":0,"failed":0,"events":[]}
    for row in rows:
        eid=str(row["event_id"]); st=str(row["subject_type"]); sid=str(row["subject_id"])
        out["attempted_events"]+=1
        try:
            q=compile_progressive_identity(c,eid)
            status="READY_FOR_FORMAT_BANK"
            try:
                q=attach_deep_lore_options(c,q,difficulty_band="HARD")
                status="READY_FOR_BANK"
                out["mcq"]+=1
            except Exception as option_exc:
                out["progressive"]+=1
                q.setdefault("generation_notes",{})["options_error"]=type(option_exc).__name__+":"+str(option_exc)

            c.execute("""
                INSERT OR REPLACE INTO story_generated_questions(
                    question_id,candidate_id,event_id,subject_type,subject_id,
                    mechanic,difficulty_band,question_json,status,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
            """,(
                str(q["question_id"]),
                "reviewed-seed:"+eid,
                eid,st,sid,
                str(q.get("mechanic") or ""),
                str(q.get("difficulty_band") or "HARD"),
                json.dumps(q,sort_keys=True,ensure_ascii=False),
                status,
                dt.datetime.now(dt.timezone.utc).isoformat(),
            ))
            commit_retry(c)
            out["events"].append({"event_id":eid,"status":status,"mechanic":q.get("mechanic")})
        except Exception as exc:
            out["failed"]+=1
            out["events"].append({"event_id":eid,"status":"FAILED","reason":type(exc).__name__+":"+str(exc)})

    out["total_story_questions"]=int(c.execute("select count(*) from story_generated_questions").fetchone()[0])
    out["ready_for_bank"]=int(c.execute("select count(*) from story_generated_questions where status='READY_FOR_BANK'").fetchone()[0])
    out["ready_for_format_bank"]=int(c.execute("select count(*) from story_generated_questions where status='READY_FOR_FORMAT_BANK'").fetchone()[0])
    c.close()
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__":
    main()
