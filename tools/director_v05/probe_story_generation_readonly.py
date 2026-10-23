"""Read-only production compiler probe; no INSERT, UPDATE, or transaction writes."""
import json, sqlite3, sys
from collections import Counter
# The running Fly image may lag this branch. Load the changed clue compiler
# first so the probe tests candidate code instead of the deployed old module.
import importlib.util
_lore_name="tools.director_v05.lore_trivia"
_lore_spec=importlib.util.spec_from_file_location(_lore_name,"/tmp/reads_story_lore_checked.py")
_lore_mod=importlib.util.module_from_spec(_lore_spec)
sys.modules[_lore_name]=_lore_mod
_lore_spec.loader.exec_module(_lore_mod)
from tools.director_v05.lore_mechanics import compile_fact_or_fake, compile_progressive_identity
from tools.director_v05.lore_formats import compile_common_link_mcq
import importlib.util
_cert_name="tools.director_v05.story_quality_certification"
_spec=importlib.util.spec_from_file_location(_cert_name,"/tmp/reads_story_quality_checked.py")
_mod=importlib.util.module_from_spec(_spec)
sys.modules[_cert_name]=_mod
_spec.loader.exec_module(_mod)
certify_question=_mod.certify_question

def run(db):
    db.execute("PRAGMA query_only=ON")
    rows=db.execute("""SELECT e.event_id,s.subject_type,s.subject_id
      FROM universal_event e JOIN universal_event_subject s ON s.event_id=e.event_id
      JOIN football_story_enrichment f ON f.promoted_event_id=e.event_id
      WHERE e.verification_status='VERIFIED' AND COALESCE(e.sensitive,0)=0
      ORDER BY e.event_id LIMIT 20""").fetchall()
    stats=Counter()
    examples=[]
    for r in rows:
        event_id,subject_type,subject_id=r
        for name,compiler in (
            ("fact",lambda:compile_fact_or_fake(db,event_id,fake=False)),
            ("fake",lambda:compile_fact_or_fake(db,event_id,fake=True)),
            ("identity",lambda:compile_progressive_identity(db,event_id)),
            ("common_link",lambda:compile_common_link_mcq(db,subject_type,subject_id))):
            try:
                q=compiler()
                failures=certify_question(q,expected_event_id=event_id)
                stats[name+"_passed" if not failures else name+"_rejected"]+=1
                for reason in failures:stats["reason:"+reason]+=1
                if failures and len(examples)<12: examples.append({"mechanic":name,"reasons":failures})
            except (ValueError,TypeError,KeyError,sqlite3.Error) as exc:
                stats[name+"_cannot_compile"]+=1
                stats["compiler_error:"+str(exc)[:80]]+=1
    return {"events_checked":len(rows),"stats":dict(stats),"examples":examples}

if __name__=="__main__":
    connection=sqlite3.connect("file:"+sys.argv[1]+"?mode=ro",uri=True,timeout=10)
    connection.row_factory=sqlite3.Row
    try: print(json.dumps(run(connection),sort_keys=True))
    finally:connection.close()
