"""Reads v3.0 AI Game Director.
Natural-language game request -> conservative parse -> knowledge/data plan ->
feasibility -> Game Factory candidates -> QA -> optional publication.
"""
from pathlib import Path
import sqlite3,json,hashlib,re,datetime as dt
import game_factory as F
import quality_intelligence as Q

ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"
def conn():
 c=sqlite3.connect(DB,timeout=60); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def hid(prefix,*parts): return prefix+":"+hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]

def graph_plan(spec):
 pred=spec.get("relationship_predicate")
 plans={
  "AWARD_DRAFT_SEQUENCE":{"path":["CFB_PLAYER","SAME_PERSON","NFL_PLAYER"],"support":["cross_league_identity_bridge","cfb_award_facts","draft_facts"]},
  "CFB_TRANSFER_COUNT":{"path":["CFB_PLAYER","TRANSFERRED_TO","SCHOOL"],"support":["cfb_transfer_summary"]},
  "CFB_SAME_SCHOOL_POSITION":{"path":["CFB_PLAYER","PLAYED_FOR","SCHOOL"],"support":["cfb_roster_seasons_real"]},
  "CFB_SCHOOL_POSITION_CONTRAST":{"path":["CFB_PLAYER","PLAYED_FOR","SCHOOL"],"support":["cfb_roster_seasons_real"]},
  "NFL_SAME_DRAFT_TEAM_POSITION":{"path":["NFL_PLAYER","DRAFTED_BY","NFL_TEAM"],"support":["draft_facts"]},
  "NFL_DRAFT_TEAM_POSITION_CONTRAST":{"path":["NFL_PLAYER","DRAFTED_BY","NFL_TEAM"],"support":["draft_facts"]},
  "NFL_TEAMMATE_TIME":{"path":["NFL_PLAYER","PLAYED_FOR","NFL_TEAM"],"support":["canonical_roster_seasons"]},
  "CFB_TEAMMATE_TIME":{"path":["CFB_PLAYER","PLAYED_FOR","SCHOOL"],"support":["cfb_roster_seasons_real"]},
 }
 if pred in plans:return plans[pred]
 # Generic plan is intentionally descriptive, not permission to invent unsupported joins.
 return {"path":[],"support":[],"note":"Use Game Factory feasibility gate; unsupported relationships remain blocked."}

def interpret(text):
 spec=F.compile_description(text)
 plan=graph_plan(spec)
 feas=F.feasibility(spec)
 status="READY" if feas.get("status")=="SUPPORTED" else "BLOCKED"
 rid=hid("GDR",text,json.dumps(spec,sort_keys=True))
 c=conn()
 c.execute("""INSERT OR REPLACE INTO game_director_requests
  (request_id,request_text,parsed_spec_json,graph_plan_json,feasibility_json,status)
  VALUES(?,?,?,?,?,?)""",(rid,text,json.dumps(spec),json.dumps(plan),json.dumps(feas),status))
 c.commit();c.close()
 return {"request_id":rid,"request":text,"spec":spec,"graph_plan":plan,"feasibility":feas,"status":status}

def _candidate_qa(payload):
 reasons=[]
 if not isinstance(payload,dict): reasons.append("INVALID_PAYLOAD")
 if not payload.get("prompt"): reasons.append("MISSING_PROMPT")
 if not payload.get("answer"): reasons.append("MISSING_ANSWER")
 items=payload.get("items",[])
 labels=[str(x.get("label","")).strip().lower() for x in items if isinstance(x,dict)]
 if len(labels)!=len(set(labels)): reasons.append("DUPLICATE_ITEM_LABEL")
 if payload.get("answer_id") and payload["answer_id"] not in {x.get("id") for x in items if isinstance(x,dict)}:
  reasons.append("ANSWER_NOT_IN_ITEMS")
 return {"status":"PASS" if not reasons else "FAIL","reasons":reasons}

def preview(text,limit=20,seed="director"):
 r=interpret(text)
 if r["status"]!="READY": return {**r,"candidates":[],"qa":{"pass":0,"fail":0}}
 candidates,feas=F.generate_candidates(r["spec"],limit=limit,seed=seed)
 out=[];passed=0
 for payload,difficulty,ambiguity,sources in candidates:
  qa=_candidate_qa(payload)
  if qa["status"]=="PASS":passed+=1
  out.append({"payload":payload,"difficulty":difficulty,"ambiguity":ambiguity,"sources":sources,"qa":qa})
 pid=hid("GDP",r["request_id"],seed,limit)
 c=conn();c.execute("""INSERT OR REPLACE INTO game_director_previews
  VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)""",(pid,r["request_id"],len(out),passed,json.dumps(out)));c.commit();c.close()
 return {**r,"preview_id":pid,"candidates":out,"qa":{"pass":passed,"fail":len(out)-passed}}

def publish(text,mode_id,limit=50,seed="publish"):
 """Publish only Game Factory candidates that pass director QA.
 Existing Game Factory owns canonical puzzle insertion semantics.
 """
 p=preview(text,limit,seed)
 if p["status"]!="READY": return {"status":"BLOCKED","reason":p["feasibility"]}
 good=[x for x in p["candidates"] if x["qa"]["status"]=="PASS"]
 if not good:return {"status":"HOLD","reason":"No QA-passing candidates"}
 # Game Factory is the sole publishing layer; director never bypasses it.
 result=F.build_mode(text,mode_id=mode_id,limit=limit,seed=seed,publish=True)
 pub=hid("GDPUB",p["request_id"],mode_id,seed)
 c=conn();c.execute("""INSERT OR REPLACE INTO game_director_publications
  VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)""",(pub,p["request_id"],mode_id,int(result.get("published",0) or 0),
  "PASS" if result.get("published",0) else "HOLD",json.dumps(result)));c.commit();c.close()
 return {"status":"PUBLISHED" if result.get("published",0) else "HOLD","publication_id":pub,"result":result}

def examples():
 return [
  "Make a Connections game with college players who went to the same school and played the same position.",
  "Make an odd-one-out game where four college players shared a school and position but the fifth played another position.",
  "Make a game about NFL players drafted by the same team at the same position.",
  "Make a game about college players who transferred exactly once.",
  "Make a timeline game where a college award happened before the player's NFL draft."
 ]
