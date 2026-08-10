"""Reads v2.3 Launch Intelligence, QA certification and Knowledge Graph."""
from pathlib import Path
import sqlite3,json,hashlib,math,datetime as dt,time,collections,re,os
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():
 c=sqlite3.connect(DB,timeout=90);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]

def build_knowledge_graph():
 c=db();c.execute("DELETE FROM knowledge_edges");c.execute("DELETE FROM knowledge_nodes")
 nodes=0;edges=0
 # Existing verified graph nodes become formal knowledge nodes.
 for r in c.execute("SELECT * FROM graph_nodes WHERE verification_status IN ('SOURCE_BACKED','VERIFIED','VERIFIED_STABLE_ID')"):
  nid=hid("KN",r["node_type"],r["node_id"])
  comp="CFB" if r["node_type"] in ("CFB_PLAYER","SCHOOL") else "NFL" if r["node_type"] in ("NFL_PLAYER","NFL_TEAM","FRANCHISE") else None
  c.execute("INSERT OR IGNORE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?)",(nid,r["node_type"],r["node_id"],r["display_name"] or r["node_id"],comp,json.dumps({"popularity":r["popularity_score"]}),r["verification_status"]));nodes+=c.execute("SELECT changes()").fetchone()[0]
 # Add edge endpoint nodes even when the legacy graph_nodes table omitted them.
 for r in c.execute("""SELECT subject_type,subject_id,object_type,object_id FROM graph_edges
                       WHERE verification_status IN ('SOURCE_BACKED','VERIFIED','VERIFIED_STABLE_ID')"""):
  for typ,key in [(r["subject_type"],r["subject_id"]),(r["object_type"],r["object_id"])]:
   nid=hid("KN",typ,key);comp="CFB" if typ in ("CFB_PLAYER","SCHOOL") else "NFL" if typ in ("NFL_PLAYER","NFL_TEAM","FRANCHISE") else None
   c.execute("INSERT OR IGNORE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?)",(nid,typ,key,key,comp,"{}", "SOURCE_BACKED"));nodes+=c.execute("SELECT changes()").fetchone()[0]
 # Mirror only verified/source-backed graph edges.
 for r in c.execute("""SELECT * FROM graph_edges WHERE verification_status IN ('SOURCE_BACKED','VERIFIED','VERIFIED_STABLE_ID')"""):
  a=hid("KN",r["subject_type"],r["subject_id"]);b=hid("KN",r["object_type"],r["object_id"])
  eid=hid("KE",a,r["predicate"],b,r["season_start"],r["season_end"],r["source_id"])
  c.execute("""INSERT OR IGNORE INTO knowledge_edges(edge_id,source_node_id,predicate,target_node_id,season_start,season_end,source_id,verification_status,confidence)
               VALUES(?,?,?,?,?,?,?,?,?)""",(eid,a,r["predicate"],b,r["season_start"],r["season_end"],r["source_id"],r["verification_status"],1.0));edges+=c.execute("SELECT changes()").fetchone()[0]
 # Explicit CFB↔NFL identities.
 for r in c.execute("SELECT cfb_player_id,nfl_player_key,confidence,verification_status FROM cross_league_identity_bridge WHERE production_safe=1"):
  a=hid("KN","CFB_PLAYER",r["cfb_player_id"]);b=hid("KN","NFL_PLAYER",r["nfl_player_key"])
  for typ,key,nid in [("CFB_PLAYER",r["cfb_player_id"],a),("NFL_PLAYER",r["nfl_player_key"],b)]:
   c.execute("INSERT OR IGNORE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?)",(nid,typ,key,key,"CFB" if typ=="CFB_PLAYER" else "NFL","{}",r["verification_status"]))
  c.execute("""INSERT OR IGNORE INTO knowledge_edges VALUES(?,?,?,?,NULL,NULL,'IDENTITY_BRIDGE',?,?,?)""",
   (hid("KE",a,"SAME_PERSON",b),a,"SAME_PERSON",b,r["verification_status"],float(r["confidence"] or 1),json.dumps({"production_safe":True})));edges+=c.execute("SELECT changes()").fetchone()[0]
 c.commit();c.close();return {"nodes":nodes,"edges":edges}

def query_graph(start_type,start_id,predicates,max_results=100):
 c=db();front=[hid("KN",start_type,start_id)];paths=[[front[0]]]
 for pred in predicates:
  nxt=[];npaths=[]
  for node,path in zip(front,paths):
   for e in c.execute("SELECT target_node_id FROM knowledge_edges WHERE source_node_id=? AND predicate=? AND confidence>=.9",(node,pred)):
    nxt.append(e[0]);npaths.append(path+[pred,e[0]])
  front,paths=nxt,npaths
  if not front:break
 rows=[]
 for node,path in list(zip(front,paths))[:max_results]:
  n=c.execute("SELECT * FROM knowledge_nodes WHERE node_id=?",(node,)).fetchone()
  if n:rows.append({"node":dict(n),"path":path})
 c.close();return rows

def audit_truth_claims():
 c=db();c.execute("DELETE FROM qa_truth_claims");c.execute("DELETE FROM qa_contradictions")
 # Use graph edges as claims; contradiction rules apply only to predicates expected to be singular in a season.
 for r in c.execute("""SELECT subject_type,subject_id,predicate,object_id,season_start,season_end,source_id,verification_status
                       FROM graph_edges WHERE verification_status IN ('SOURCE_BACKED','VERIFIED','VERIFIED_STABLE_ID')"""):
  season=r["season_start"] if r["season_start"]==r["season_end"] else None
  ch=hashlib.sha256(f"{r['subject_type']}|{r['subject_id']}|{r['predicate']}|{r['object_id']}|{season}|{r['source_id']}".encode()).hexdigest()
  c.execute("""INSERT OR IGNORE INTO qa_truth_claims(claim_id,subject_type,subject_id,predicate,object_value,season,source_id,verification_status,confidence,claim_hash)
               VALUES(?,?,?,?,?,?,?,?,1,?)""",(hid("CL",ch),r["subject_type"],r["subject_id"],r["predicate"],r["object_id"],season,r["source_id"],r["verification_status"],ch))
 singular={"POSITION","DRAFTED_BY","DRAFT_ROUND","DRAFT_PICK","HOME_STADIUM"}
 contradictions=0
 for pred in singular:
  groups=c.execute("""SELECT subject_type,subject_id,predicate,season,COUNT(DISTINCT object_value) n,
                      GROUP_CONCAT(DISTINCT object_value),GROUP_CONCAT(DISTINCT source_id)
                      FROM qa_truth_claims WHERE predicate=? GROUP BY subject_type,subject_id,predicate,season HAVING n>1""",(pred,)).fetchall()
  for g in groups:
   sev="BLOCKER" if g[3] is not None else "HIGH"
   c.execute("INSERT INTO qa_contradictions VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,NULL)",
    (hid("CON",g[0],g[1],g[2],g[3]),g[0],g[1],g[2],g[3],json.dumps((g[5] or "").split(",")),json.dumps((g[6] or "").split(",")),sev,"OPEN"));contradictions+=1
 c.commit();claims=c.execute("SELECT COUNT(*) FROM qa_truth_claims").fetchone()[0];c.close()
 return {"claims":claims,"contradictions":contradictions}

def audit_puzzles():
 c=db();c.execute("DELETE FROM puzzle_quality_audits");c.execute("DELETE FROM puzzle_similarity")
 total=0;blocked=0;ambiguous=0
 # Cheap deterministic audits over all puzzles.
 for r in c.execute("SELECT puzzle_id,mode_id,eligible,verification_status,source_id,ambiguity_score,payload_json FROM puzzle_catalog"):
  reasons=[]
  if r["verification_status"] not in ("SOURCE_BACKED","VERIFIED","VERIFIED_STABLE_ID","VERIFIED_EVENT"):reasons.append("UNVERIFIED")
  if not r["source_id"]:reasons.append("MISSING_SOURCE")
  if r["ambiguity_score"]>=.5:reasons.append("HIGH_AMBIGUITY");ambiguous+=1
  try:
   payload=json.loads(r["payload_json"])
   if not payload:reasons.append("EMPTY_PAYLOAD")
  except:reasons.append("INVALID_PAYLOAD")
  status="FAIL" if reasons else "PASS"
  c.execute("INSERT INTO puzzle_quality_audits VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (hid("PQA",r["puzzle_id"],"BASE"),r["puzzle_id"],"BASELINE",1.0 if not reasons else 0.0,status,";".join(reasons) if reasons else None,json.dumps({"mode":r["mode_id"]})))
  total+=1;blocked+=bool(reasons)
 # Exact semantic duplicates by normalized payload within mode, capped to duplicate groups.
 for g in c.execute("""SELECT mode_id,payload_json,COUNT(*) n FROM puzzle_catalog WHERE eligible=1
                       GROUP BY mode_id,payload_json HAVING n>1 LIMIT 50000"""):
  ids=[x[0] for x in c.execute("SELECT puzzle_id FROM puzzle_catalog WHERE mode_id=? AND payload_json=? ORDER BY puzzle_id LIMIT 25",(g["mode_id"],g["payload_json"]))]
  for i in range(1,len(ids)):
   a,b=ids[0],ids[i]
   c.execute("INSERT OR IGNORE INTO puzzle_similarity VALUES(?,?,1,'EXACT_PAYLOAD',CURRENT_TIMESTAMP)",(a,b))
 c.commit();dups=c.execute("SELECT COUNT(*) FROM puzzle_similarity").fetchone()[0];c.close()
 return {"audited":total,"failed":blocked,"high_ambiguity":ambiguous,"duplicate_pairs":dups}

def calibrate_difficulty():
 c=db()
 rows=c.execute("""SELECT puzzle_id,COUNT(*) attempts,SUM(correct) correct,SUM(abandoned) skips,AVG(solve_ms) avg_ms
                   FROM puzzle_attempts GROUP BY puzzle_id""").fetchall()
 for r in rows:
  rate=(r["correct"] or 0)/max(1,r["attempts"]);d=1-rate
  band="EASY" if d<.3 else "MEDIUM" if d<.55 else "HARD" if d<.78 else "EXPERT"
  c.execute("""INSERT OR REPLACE INTO player_answer_stats(puzzle_id,attempts,correct,skips,avg_answer_ms,calibrated_difficulty,calibrated_band,updated_at)
               VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",(r["puzzle_id"],r["attempts"],r["correct"] or 0,r["skips"] or 0,r["avg_ms"],d,band))
 c.commit();c.close();return {"calibrated":len(rows)}

def rebuild_mode_quality():
 c=db();c.execute("DELETE FROM mode_quality_metrics")
 base={r["mode_id"]:r for r in c.execute("""SELECT mode_id,COUNT(*) total,SUM(eligible) eligible,AVG(ambiguity_score) amb
                                           FROM puzzle_catalog GROUP BY mode_id""")}
 attempt_count=c.execute("SELECT COUNT(*) FROM puzzle_attempts").fetchone()[0]
 attempts={}
 if attempt_count:
  attempts={r["mode_id"]:r for r in c.execute("""SELECT p.mode_id,COUNT(*) attempts,SUM(a.correct) correct,SUM(a.abandoned) skips
       FROM puzzle_attempts a JOIN puzzle_catalog p USING(puzzle_id) GROUP BY p.mode_id""")}
 dup_count=c.execute("SELECT COUNT(*) FROM puzzle_similarity").fetchone()[0]
 dups={}
 if dup_count:
  dups={r["mode_id"]:r["n"] for r in c.execute("""SELECT p.mode_id,COUNT(*) n FROM puzzle_similarity s
       JOIN puzzle_catalog p ON p.puzzle_id=s.puzzle_id_a GROUP BY p.mode_id""")}
 for mode,b in base.items():
  a=attempts.get(mode);att=a["attempts"] if a else 0;correct=(a["correct"] or 0)/max(1,att) if a else 0;skip=(a["skips"] or 0)/max(1,att) if a else 0
  dupr=dups.get(mode,0)/max(1,b["total"]);amb=b["amb"] or 0
  quality=max(0,100-(amb*45)-(dupr*35)-(skip*20));status="HEALTHY" if quality>=85 else "WATCH" if quality>=70 else "HOLD"
  c.execute("INSERT INTO mode_quality_metrics VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (mode,b["eligible"] or 0,att,None if not att else 1-skip,None if not att else correct,None if not att else skip,0,dupr,amb,quality,status))
 c.commit();n=len(base);c.close();return {"modes":n}

def build_coverage_map():
 c=db();c.execute("DELETE FROM coverage_dimensions")
 # Canonical coverage declarations.
 for r in c.execute("SELECT * FROM data_coverage"):
  score=1.0 if r["production_safe"] and r["completeness"]=="COMPLETE" else .75 if r["production_safe"] else .35
  gap="NONE" if score>=.9 else "LOW" if score>=.7 else "HIGH"
  cid=hid("COV",r["competition_id"],"DATASET",r["domain_id"],r["coverage_start"],r["coverage_end"])
  c.execute("INSERT INTO coverage_dimensions VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (cid,r["competition_id"],"DATASET",r["domain_id"],r["coverage_start"],r["coverage_end"],0,0,0,score,gap))
 # Puzzle coverage by mode.
 for r in c.execute("""SELECT CASE WHEN mode_id LIKE 'cfb_%' THEN 'CFB' ELSE 'NFL' END comp,mode_id,COUNT(*) n,SUM(eligible) e
                       FROM puzzle_catalog GROUP BY mode_id"""):
  score=(r["e"] or 0)/max(1,r["n"]);gap="NONE" if score>=.95 else "LOW" if score>=.8 else "HIGH"
  c.execute("INSERT INTO coverage_dimensions VALUES(?,?,?,?,NULL,NULL,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (hid("COV",r["comp"],"MODE",r["mode_id"]),r["comp"],"MODE",r["mode_id"],r["n"],r["n"],r["e"] or 0,score,gap))
 c.commit();n=c.execute("SELECT COUNT(*) FROM coverage_dimensions").fetchone()[0];c.close();return {"dimensions":n}

def discover_factory_opportunities():
 c=db();c.execute("DELETE FROM factory_opportunities");ops=[]
 candidates=[
 ("GRAPH_TWO_HOP","Verified two-hop knowledge graph paths",["knowledge_nodes","knowledge_edges"],["PLAYER","ATTENDED","SCHOOL"],"graph_two_hop"),
 ("CROSS_LEAGUE","Verified CFB-to-NFL identity traversal",["cross_league_identity_bridge","knowledge_edges"],["CFB_PLAYER","SAME_PERSON","NFL_PLAYER"],"cross_identity"),
 ("CAREER_CHAIN","Player school/team relationship chains",["knowledge_edges"],["PLAYER","ATTENDED","SCHOOL","PLAYED_FOR","NFL_TEAM"],"career_chain")
 ]
 for typ,desc,tables,path,mode in candidates:
  est=c.execute("SELECT COUNT(*) FROM knowledge_edges").fetchone()[0]
  oid=hid("OPP",typ,mode);c.execute("INSERT INTO factory_opportunities VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (oid,typ,desc,json.dumps(tables),json.dumps(path),est,1.0,.85,"SUPPORTED",mode,"CANDIDATE"));ops.append(oid)
 c.commit();c.close();return {"opportunities":len(ops)}

def certify_daily(date):
 c=db();rows=list(c.execute("SELECT * FROM daily_slates WHERE slate_date=?",(date,)));out=[]
 for r in rows:
  p=c.execute("SELECT * FROM puzzle_catalog WHERE puzzle_id=?",(r["puzzle_id"],)).fetchone();reasons=[]
  if not p:reasons.append("PUZZLE_MISSING")
  else:
   if not p["eligible"]:reasons.append("INELIGIBLE")
   if p["verification_status"] not in ("SOURCE_BACKED","VERIFIED","VERIFIED_STABLE_ID","VERIFIED_EVENT"):reasons.append("UNVERIFIED")
   if not p["source_id"]:reasons.append("MISSING_SOURCE")
   if p["ambiguity_score"]>=.5:reasons.append("AMBIGUOUS")
   fail=c.execute("SELECT 1 FROM puzzle_quality_audits WHERE puzzle_id=? AND status='FAIL' LIMIT 1",(p["puzzle_id"],)).fetchone()
   if fail:reasons.append("QA_FAIL")
  final="PASS" if not reasons else "HOLD"
  c.execute("INSERT OR REPLACE INTO daily_qa_certifications VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (date,r["slot_key"],r["puzzle_id"],"PASS" if p else "FAIL","PASS","PASS" if p and p["ambiguity_score"]<.5 else "FAIL","PASS" if p and p["source_id"] else "FAIL",final,json.dumps(reasons)))
  out.append({"slot":r["slot_key"],"status":final,"reasons":reasons})
 c.commit();c.close();return out

def health_snapshot():
 c=db()
 integrity=100 if c.execute("PRAGMA integrity_check").fetchone()[0]=="ok" else 0
 fk=100 if not c.execute("PRAGMA foreign_key_check").fetchall() else 0
 contradictions=c.execute("SELECT COUNT(*) FROM qa_contradictions WHERE status='OPEN' AND severity='BLOCKER'").fetchone()[0]
 data=max(0,100-contradictions*.5)
 q=c.execute("SELECT AVG(quality_score) FROM mode_quality_metrics").fetchone()[0] or 0
 cov=(c.execute("SELECT AVG(coverage_score) FROM coverage_dimensions").fetchone()[0] or 0)*100
 stale=c.execute("SELECT COUNT(*) FROM freshness_registry WHERE stale=1").fetchone()[0]
 live=max(0,100-stale*15)
 growth=100 if c.execute("SELECT COUNT(*) FROM seo_entities WHERE indexable=1").fetchone()[0]>100000 else 75
 infra=(integrity+fk)/2
 overall=data*.3+q*.25+cov*.15+live*.1+growth*.1+infra*.1
 details={"blocker_contradictions":contradictions,"stale_domains":stale}
 sid=hid("HEALTH",dt.datetime.now().isoformat())
 c.execute("INSERT INTO reads_health_snapshots VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",(sid,overall,data,q,cov,live,growth,infra,json.dumps(details)))
 c.commit();c.close();return {"overall":round(overall,2),"data_truth":round(data,2),"puzzle_quality":round(q,2),"coverage":round(cov,2),"live":round(live,2),"growth":growth,"infrastructure":infra,"details":details}

def release_certify(version="2.3.0",compile_ok=True):
 c=db();h=health_snapshot()
 integrity=c.execute("PRAGMA integrity_check").fetchone()[0];fk=c.execute("PRAGMA foreign_key_check").fetchall()
 blockers=[]
 if integrity!="ok":blockers.append("INTEGRITY")
 if fk:blockers.append("FOREIGN_KEYS")
 if not compile_ok:blockers.append("COMPILE")
 if c.execute("SELECT COUNT(*) FROM qa_contradictions WHERE status='OPEN' AND severity='BLOCKER'").fetchone()[0]:blockers.append("TRUTH_CONTRADICTIONS")
 decision="PASS" if not blockers and h["overall"]>=80 else "HOLD" if h["overall"]>=65 else "FAIL"
 cid=hid("CERT",version,dt.datetime.now().isoformat())
 c.execute("""INSERT INTO release_certifications(certification_id,release_version,database_sha256,truth_score,puzzle_quality_score,coverage_score,
  integrity_status,foreign_key_status,compile_status,overall_score,decision,blockers_json)
  VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
  (cid,version,None,h["data_truth"],h["puzzle_quality"],h["coverage"],integrity,"PASS" if not fk else "FAIL","PASS" if compile_ok else "FAIL",h["overall"],decision,json.dumps(blockers)))
 c.commit();c.close();return {"certification_id":cid,"decision":decision,"score":h["overall"],"blockers":blockers}

def run_all():
 return {"graph":build_knowledge_graph(),"truth":audit_truth_claims(),"puzzles":audit_puzzles(),
         "difficulty":calibrate_difficulty(),"modes":rebuild_mode_quality(),"coverage":build_coverage_map(),
         "factory":discover_factory_opportunities(),"health":health_snapshot()}
