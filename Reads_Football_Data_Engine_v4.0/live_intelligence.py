"""Reads v2.0 Live Football Intelligence orchestrator."""
from pathlib import Path
import sqlite3,json,hashlib,datetime as dt,subprocess,sys,random

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"

def db():
    c=sqlite3.connect(DB,timeout=60);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
def hid(prefix,*parts):
    return prefix+":"+hashlib.sha1("|".join(map(str,parts)).encode()).hexdigest()[:22]
def utcnow(): return dt.datetime.now(dt.timezone.utc)

def begin_run(feed_id):
    c=db()
    rid=hid("LIVE",feed_id,utcnow().isoformat())
    c.execute("INSERT INTO live_ingest_runs(run_id,feed_id,status) VALUES(?,?,'RUNNING')",(rid,feed_id))
    c.execute("UPDATE live_data_feeds SET last_attempt_at=CURRENT_TIMESTAMP,last_status='RUNNING' WHERE feed_id=?",(feed_id,))
    c.commit();c.close();return rid

def finish_run(run_id,status,rows_seen=0,rows_inserted=0,rows_updated=0,rows_rejected=0,qa=0,log=None,source_version=None,sha=None):
    c=db()
    c.execute("""UPDATE live_ingest_runs SET finished_at=CURRENT_TIMESTAMP,status=?,source_version=?,source_sha256=?,
                 rows_seen=?,rows_inserted=?,rows_updated=?,rows_rejected=?,qa_issues=?,log_json=? WHERE run_id=?""",
              (status,source_version,sha,rows_seen,rows_inserted,rows_updated,rows_rejected,qa,json.dumps(log or {}),run_id))
    feed=c.execute("SELECT feed_id FROM live_ingest_runs WHERE run_id=?",(run_id,)).fetchone()[0]
    if status=="SUCCESS":
        c.execute("UPDATE live_data_feeds SET last_success_at=CURRENT_TIMESTAMP,last_status='SUCCESS' WHERE feed_id=?",(feed,))
        c.execute("UPDATE freshness_registry SET last_verified_at=CURRENT_TIMESTAMP,stale=0 WHERE domain_id=?",(feed,))
    else:
        c.execute("UPDATE live_data_feeds SET last_status=? WHERE feed_id=?",(status,feed))
    c.commit();c.close()

def detect_staleness():
    c=db();now=utcnow();alerts=[]
    for r in c.execute("SELECT * FROM freshness_registry"):
        lv=r["last_verified_at"]
        stale=0
        if lv:
            try:
                t=dt.datetime.fromisoformat(lv.replace("Z","+00:00"))
                if t.tzinfo is None:t=t.replace(tzinfo=dt.timezone.utc)
                stale=int((now-t).total_seconds()/60 > r["stale_after_minutes"])
            except: stale=1
        else:
            # No live run yet: respect packaged historical data, but mark as needing first refresh rather than breaking production.
            stale=0
        c.execute("UPDATE freshness_registry SET stale=? WHERE domain_id=?",(stale,r["domain_id"]))
        if stale:
            aid=hid("ALERT","STALE",r["domain_id"])
            c.execute("""INSERT OR IGNORE INTO admin_alerts(alert_id,severity,category,title,detail,object_type,object_id)
                         VALUES(?,'WARN','FRESHNESS',?,?, 'DOMAIN',?)""",
                      (aid,f"{r['domain_id']} data is stale",f"Exceeded {r['stale_after_minutes']} minute freshness window.",r["domain_id"]))
            alerts.append(r["domain_id"])
    c.commit();c.close();return alerts

def register_change(run_id,entity_type,entity_id,field,old,new,source_id=None):
    if str(old)==str(new): return None
    cid=hid("CHG",run_id,entity_type,entity_id,field,str(new))
    c=db()
    c.execute("""INSERT OR IGNORE INTO live_fact_changes(
      change_id,run_id,entity_type,entity_id,field_name,old_value,new_value,change_type,source_id)
      VALUES(?,?,?,?,?,?,?,?,?)""",
      (cid,run_id,entity_type,entity_id,field,None if old is None else str(old),None if new is None else str(new),
       "INSERT" if old is None else "UPDATE",source_id))
    c.execute("""INSERT OR IGNORE INTO live_publish_queue(queue_id,object_type,object_id,reason,priority)
                 VALUES(?, 'FACT_CHANGE', ?, 'New live football fact awaiting QA', 60)""",(hid("QUEUE",cid),cid))
    c.commit();c.close();return cid

def qa_changes(run_id=None):
    c=db()
    q="SELECT * FROM live_fact_changes WHERE qa_status='PENDING'"
    args=()
    if run_id:q+=" AND run_id=?";args=(run_id,)
    passed=held=0
    for r in c.execute(q,args):
        # Conservative generic QA: source required and new value nonblank.
        ok=bool(r["source_id"]) and r["new_value"] not in (None,"")
        c.execute("UPDATE live_fact_changes SET qa_status=?,publish_status=? WHERE change_id=?",
                  ("PASSED" if ok else "FAILED","READY" if ok else "HELD",r["change_id"]))
        if ok:passed+=1
        else:held+=1
    c.commit();c.close();return {"passed":passed,"held":held}

def register_event(competition,event_type,event_date,title,payload,source_id,entity_type=None,entity_id=None,verified=True):
    eid=hid("EVENT",competition,event_type,event_date,title)
    c=db()
    c.execute("""INSERT OR REPLACE INTO live_event_catalog(
      event_id,competition_id,event_type,event_date,entity_type,entity_id,title,payload_json,source_id,verification_status,freshness_status)
      VALUES(?,?,?,?,?,?,?,?,?,?, 'FRESH')""",
      (eid,competition,event_type,event_date,entity_type,entity_id,title,json.dumps(payload,sort_keys=True),source_id,
       "VERIFIED" if verified else "PENDING"))
    c.commit();c.close();return eid

def generate_from_event(event_id):
    c=db();ev=c.execute("SELECT * FROM live_event_catalog WHERE event_id=?",(event_id,)).fetchone()
    if not ev:c.close();raise KeyError(event_id)
    payload=json.loads(ev["payload_json"])
    out=[]

    # Live results should not depend on the language parser: the event itself is already verified structured data.
    if ev["event_type"]=="GAME_FINAL" and ev["verification_status"]=="VERIFIED":
        if ev["competition_id"]=="CFB":
            home=payload.get("home_school_id"); away=payload.get("away_school_id")
            hs=payload.get("home_score"); aw=payload.get("away_score")
        else:
            home=payload.get("home_team"); away=payload.get("away_team")
            hs=payload.get("home_score"); aw=payload.get("away_score")
        if home and away and hs is not None and aw is not None:
            winner=home if hs>aw else away if aw>hs else "TIE"
            candidates=[
              ("live_game_winner",f"Who won: {away} at {home}? ",str(winner),
               {"home":home,"away":away,"home_score":hs,"away_score":aw}),
              ("live_home_score",f"How many points did {home} score against {away}?",str(hs),
               {"home":home,"away":away,"home_score":hs,"away_score":aw}),
              ("live_away_score",f"How many points did {away} score at {home}?",str(aw),
               {"home":home,"away":away,"home_score":hs,"away_score":aw})
            ]
            c.execute("DELETE FROM live_event_puzzles WHERE event_id=?",(event_id,))
            for mode,prompt,answer,extra in candidates:
                lid=hid("LIVEPZ",event_id,mode)
                pld={"event_id":event_id,"competition_id":ev["competition_id"],"event_title":ev["title"],**extra}
                c.execute("""INSERT INTO live_event_puzzles(live_puzzle_id,event_id,mode_id,prompt,answer,payload_json,verification_status,publish_status)
                             VALUES(?,?,?,?,?,?,'VERIFIED_EVENT','PREVIEW')""",
                          (lid,event_id,mode,prompt,answer,json.dumps(pld,sort_keys=True)))
                out.append({"mode_id":mode,"status":"PREVIEW_READY","live_puzzle_id":lid})
            qid=hid("QUEUE",event_id,"DIRECT_GAME_FINAL")
            c.execute("""INSERT OR IGNORE INTO live_publish_queue(queue_id,object_type,object_id,reason,priority)
                         VALUES(?,'LIVE_EVENT_PUZZLES',?,'Verified game final generated direct live trivia',90)""",(qid,event_id))
            c.commit();c.close();return out

    # Non-game events still use the Game Factory when a matching rule is available.
    rules=list(c.execute("""SELECT * FROM event_game_rules WHERE event_type=? AND auto_generate=1
                           AND (competition_id IS NULL OR competition_id=?)""",(ev["event_type"],ev["competition_id"])))
    c.close()
    if not rules:return out
    import game_factory
    for rule in rules:
        pv=game_factory.preview(rule["game_factory_description"],limit=12,seed=event_id)
        status="PREVIEW_READY" if pv["feasibility"]["status"]=="SUPPORTED" else "NEEDS_DATA"
        c=db()
        c.execute("""INSERT OR REPLACE INTO event_generated_games(
          event_id,rule_id,factory_spec_id,mode_id,generated_count,qa_excluded,publish_status)
          VALUES(?,?,?,?,?,?,?)""",
          (event_id,rule["rule_id"],pv.get("spec_id"),None,len(pv.get("preview",[])),pv.get("excluded_by_qa",0),status))
        if status=="PREVIEW_READY":
            c.execute("""INSERT OR IGNORE INTO live_publish_queue(queue_id,object_type,object_id,reason,priority)
                         VALUES(?,'EVENT_GAME',?,'Verified football event generated a new Factory preview',80)""",
                      (hid("QUEUE",event_id,rule["rule_id"]),event_id+"|"+rule["rule_id"]))
        c.commit();c.close()
        out.append({"rule_id":rule["rule_id"],"status":status,"preview_count":len(pv.get("preview",[])),
                    "feasibility":pv["feasibility"]})
    return out

def _mode_candidates(c,slot):
    q="""SELECT p.puzzle_id,p.mode_id,p.difficulty_band,p.season
         FROM puzzle_catalog p WHERE p.eligible=1"""
    args=[]
    if slot.get("mode_prefix"):
        q+=" AND p.mode_id LIKE ?";args.append(slot["mode_prefix"]+"%")
    diff=slot.get("difficulty")
    if diff:q+=" AND p.difficulty_band=?";args.append(diff)
    if slot.get("historical"):q+=" AND (p.season IS NULL OR p.season<=2019)"
    # Competition selection through mode naming/known bindings.
    comp=slot.get("competition")
    if comp=="CFB":q+=" AND p.mode_id LIKE 'cfb_%'"
    elif comp=="NFL":q+=" AND p.mode_id NOT LIKE 'cfb_%' AND p.mode_id NOT LIKE 'cross_%'"
    if slot.get("mode_family")=="connections":
        q+=" AND (p.mode_id LIKE '%connection%' OR p.mode_id LIKE '%connections%' OR p.mode_id='cross_school_pipeline')"
    q+=" ORDER BY p.puzzle_id"
    return list(c.execute(q,args))

def build_daily_slate(date=None,template_id="READS_DAILY"):
    date=date or dt.date.today().isoformat()
    c=db();t=c.execute("SELECT * FROM daily_slate_templates WHERE slate_template_id=? AND active=1",(template_id,)).fetchone()
    if not t:c.close();raise KeyError(template_id)
    slots=json.loads(t["slots_json"])
    c.execute("DELETE FROM daily_slates WHERE slate_date=? AND slate_template_id=?",(date,template_id))
    used=set();out=[]
    for slot in slots:
        pool=[r for r in _mode_candidates(c,slot) if r["puzzle_id"] not in used]
        seed=hid("SEED",date,template_id,slot["slot"])
        if pool:
            idx=int(hashlib.sha256(seed.encode()).hexdigest()[:12],16)%len(pool);r=pool[idx]
            used.add(r["puzzle_id"])
            c.execute("INSERT INTO daily_slates VALUES(?,?,?,?,?,?,?,?)",
                      (date,template_id,slot["slot"],r["mode_id"],r["puzzle_id"],seed,"READY","Deterministic daily selection"))
            out.append({"slot":slot["slot"],"mode_id":r["mode_id"],"puzzle_id":r["puzzle_id"]})
        else:
            c.execute("INSERT INTO daily_slates VALUES(?,?,?,?,?,?,?,?)",
                      (date,template_id,slot["slot"],"UNAVAILABLE",None,seed,"HELD","No eligible puzzle matched slot constraints"))
            out.append({"slot":slot["slot"],"status":"HELD"})
    c.commit();c.close();return out

def publish_live_event(event_id,actor="ADMIN",notify=True):
    c=db()
    ev=c.execute("SELECT * FROM live_event_catalog WHERE event_id=? AND verification_status='VERIFIED'",(event_id,)).fetchone()
    if not ev:c.close();return {"status":"BLOCKED","reason":"EVENT_NOT_VERIFIED"}
    live=list(c.execute("SELECT * FROM live_event_puzzles WHERE event_id=? AND publish_status='PREVIEW'",(event_id,)))
    published=[]
    for r in live:
        pid=hid("PZLIVE",r["live_puzzle_id"])
        payload=json.loads(r["payload_json"]);payload.update({"prompt":r["prompt"],"answer":r["answer"],"live_event_id":event_id})
        mode=r["mode_id"]
        c.execute("""INSERT OR REPLACE INTO puzzle_catalog(
          puzzle_id,mode_id,source_entity_type,source_entity_id,season,difficulty_score,difficulty_band,
          ambiguity_score,popularity_proxy,eligible,exclusion_reason,verification_status,source_id,payload_json)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (pid,mode,"live_event",event_id,None,.42,"MEDIUM",0,.8,1,None,"VERIFIED_EVENT",ev["source_id"],json.dumps(payload,sort_keys=True)))
        c.execute("UPDATE live_event_puzzles SET publish_status='PUBLISHED' WHERE live_puzzle_id=?",(r["live_puzzle_id"],))
        c.execute("""INSERT INTO live_publication_audit(publication_id,event_id,live_puzzle_id,puzzle_id,mode_id,action,actor)
                     VALUES(?,?,?,?,?,'PUBLISH',?)""",(hid("PUB",event_id,r["live_puzzle_id"]),event_id,r["live_puzzle_id"],pid,mode,actor))
        published.append(pid)
    if published:
        # refresh mode health for live modes
        for mode in sorted({r["mode_id"] for r in live}):
            n=c.execute("SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id=? AND eligible=1",(mode,)).fetchone()[0]
            c.execute("""INSERT OR REPLACE INTO mode_health(mode_id,eligible_puzzles,easy_count,medium_count,hard_count,expert_count,
                         min_difficulty,max_difficulty,notes)
                         VALUES(?, ?,0,?,0,0,.42,.42,'Verified live-event puzzles')""",(mode,n,n))
        if notify:
            nid=hid("NOTIFY",event_id)
            c.execute("""INSERT OR IGNORE INTO notification_outbox(
              notification_id,audience_type,notification_type,title,body,deep_link,payload_json)
              VALUES(?,'ALL','LIVE_GAME',?,?,?,?)""",
              (nid,f"New {ev['competition_id']} challenge",ev["title"],f"/live/{event_id}",
               json.dumps({"event_id":event_id,"puzzle_ids":published})))
    # resolve publish queue items for the event
    c.execute("""UPDATE live_publish_queue SET qa_status='PASSED',decision='PUBLISHED',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=?
                 WHERE object_id=? OR object_id LIKE ?""",(actor,event_id,event_id+"|%"))
    c.commit();c.close()
    return {"status":"PUBLISHED","event_id":event_id,"puzzle_ids":published}

def reject_live_event(event_id,actor="ADMIN",reason="Rejected by admin"):
    c=db()
    c.execute("UPDATE live_event_puzzles SET publish_status='REJECTED' WHERE event_id=? AND publish_status='PREVIEW'",(event_id,))
    c.execute("""UPDATE live_publish_queue SET qa_status='FAILED',decision='REJECTED',reviewed_at=CURRENT_TIMESTAMP,reviewed_by=?
                 WHERE object_id=? OR object_id LIKE ?""",(actor,event_id,event_id+"|%"))
    c.execute("""INSERT OR IGNORE INTO admin_alerts(alert_id,severity,category,title,detail,object_type,object_id,status)
                 VALUES(?,'INFO','MODERATION','Live event rejected',?,'EVENT',?,'RESOLVED')""",
              (hid("ALERT","REJECT",event_id),reason,event_id))
    c.commit();c.close();return {"status":"REJECTED","event_id":event_id}

def scan_game_events(season_min=None):
    season_min=season_min or dt.date.today().year
    c=db();created=[]
    # CFB completed games.
    for r in c.execute("""SELECT game_id,season,game_date,home_school_id,away_school_id,home_score,away_score
                          FROM cfb_games_canonical WHERE season>=? AND home_score IS NOT NULL AND away_score IS NOT NULL""",(season_min,)):
        title=f"CFB final {r['away_school_id']} at {r['home_school_id']}"
        eid=hid("EVENT","CFB","GAME_FINAL",r["game_id"])
        if not c.execute("SELECT 1 FROM live_event_catalog WHERE event_id=?",(eid,)).fetchone():
            payload=dict(r)
            c.execute("""INSERT INTO live_event_catalog VALUES(?,?,?,?,?,?,?,?,?,'VERIFIED','FRESH',CURRENT_TIMESTAMP)""",
                      (eid,"CFB","GAME_FINAL",str(r["game_date"] or r["season"]),"cfb_game",r["game_id"],title,json.dumps(payload,sort_keys=True),"SPORTSDATAVERSE_CFB"))
            created.append(eid)
    # NFL completed games from canonical games table.
    cols={x[1] for x in c.execute("PRAGMA table_info(games)")}
    if {"game_id","season","home_team","away_team","home_score","away_score"}.issubset(cols):
        datecol="gameday" if "gameday" in cols else "season"
        for r in c.execute(f"""SELECT game_id,season,{datecol} event_date,home_team,away_team,home_score,away_score
                              FROM games WHERE season>=? AND home_score IS NOT NULL AND away_score IS NOT NULL""",(season_min,)):
            eid=hid("EVENT","NFL","GAME_FINAL",r["game_id"])
            if not c.execute("SELECT 1 FROM live_event_catalog WHERE event_id=?",(eid,)).fetchone():
                c.execute("""INSERT INTO live_event_catalog VALUES(?,?,?,?,?,?,?,?,?,'VERIFIED','FRESH',CURRENT_TIMESTAMP)""",
                          (eid,"NFL","GAME_FINAL",str(r["event_date"]),"nfl_game",r["game_id"],
                           f"NFL final {r['away_team']} at {r['home_team']}",json.dumps(dict(r),sort_keys=True),"NFLVERSE_DATA"))
                created.append(eid)
    c.commit();c.close();return created

def pipeline(run_updates=False):
    result={"updates":[]}
    if run_updates:
        r=subprocess.run([sys.executable,str(ROOT/"update_everything.py")],cwd=ROOT,capture_output=True,text=True)
        result["updates"].append({"code":r.returncode,"stdout":r.stdout[-5000:],"stderr":r.stderr[-1000:]})
    result["stale_domains"]=detect_staleness()
    events=scan_game_events()
    result["new_events"]=len(events)
    generated=[]
    # Keep automatic generation bounded to avoid a huge rebuild on first installation.
    for eid in events[-20:]:
        try: generated.extend(generate_from_event(eid))
        except Exception as e: generated.append({"event_id":eid,"error":repr(e)})
    result["event_generation"]=generated
    result["daily_slate"]=build_daily_slate()
    return result

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--update",action="store_true");ap.add_argument("--slate-date")
    a=ap.parse_args()
    out=pipeline(a.update)
    if a.slate_date:out["requested_slate"]=build_daily_slate(a.slate_date)
    print(json.dumps(out,indent=2))
