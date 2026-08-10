"""Reads v3.1 Autonomous Game Expansion + Director Memory."""
from pathlib import Path
import sqlite3,json,hashlib,re,math
import game_director as D
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():
 c=sqlite3.connect(DB,timeout=60);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]

def parse_advanced(text):
 c=db();ops=[]
 for r in c.execute("SELECT * FROM director_capabilities WHERE active=1"):
  m=re.search(r["phrase_pattern"],text,re.I)
  if m: ops.append({"operator":r["operator_type"],"normalized":r["normalized_form"],"groups":list(m.groups())})
 c.close()
 base=D.interpret(text)
 base["advanced_operators"]=ops
 return base

def remember_template(name,description,mechanic,spec,graph_plan,source="USER_APPROVED"):
 tid=hid("DMT",name,mechanic,json.dumps(spec,sort_keys=True))
 c=db();c.execute("""INSERT OR REPLACE INTO director_mode_templates
 (template_id,template_name,description,mechanic,spec_json,graph_plan_json,source,approval_status,use_count,last_used_at)
 VALUES(?,?,?,?,?,?,?,'APPROVED',COALESCE((SELECT use_count FROM director_mode_templates WHERE template_id=?),0),CURRENT_TIMESTAMP)""",
 (tid,name,description,mechanic,json.dumps(spec),json.dumps(graph_plan),source,tid));c.commit();c.close()
 return {"template_id":tid,"status":"APPROVED"}

def recall_templates(query,limit=10):
 q=query.lower();c=db();rows=[]
 for r in c.execute("SELECT * FROM director_mode_templates WHERE approval_status='APPROVED'"):
  hay=(r["template_name"]+" "+r["description"]+" "+r["mechanic"]).lower()
  score=sum(1 for w in set(re.findall(r"[a-z0-9]+",q)) if len(w)>2 and w in hay)
  if score:rows.append((score,dict(r)))
 rows=sorted(rows,key=lambda x:(-x[0],-x[1]["use_count"]))[:limit]
 for _,r in rows:
  c.execute("UPDATE director_mode_templates SET use_count=use_count+1,last_used_at=CURRENT_TIMESTAMP WHERE template_id=?",(r["template_id"],))
 c.commit();c.close();return [r for _,r in rows]

def _surface(n):
 if n>=500:return "ENDLESS"
 if n>=100:return "STANDARD_MODE"
 if n>=24:return "ROTATING_PACK"
 if n>=6:return "DAILY_OR_EVENT"
 return "INSUFFICIENT"

def discover():
 c=db();c.execute("DELETE FROM autonomous_mode_discoveries");c.execute("DELETE FROM director_mode_recommendations")
 patterns=[]
 # Use actual shipped puzzle/graph counts rather than imagined coverage.
 queries=[
 ("CFB_SCHOOL_POSITION","connections","Players linked by school + position",["CFB_PLAYER","PLAYED_FOR","SCHOOL"],["cfb_roster_seasons_real"],
  "SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id='cfb_same_school_position_connections' AND eligible=1"),
 ("CFB_POSITION_CONTRAST","odd_one_out","Four players share school/position; one differs",["CFB_PLAYER","PLAYED_FOR","SCHOOL"],["cfb_roster_seasons_real"],
  "SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id='cfb_school_position_odd_one_out' AND eligible=1"),
 ("NFL_DRAFT_POSITION","connections","NFL players grouped by drafting team + position",["NFL_PLAYER","DRAFTED_BY","NFL_TEAM"],["draft_facts"],
  "SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id='nfl_same_draft_team_position_connections' AND eligible=1"),
 ("CFB_TRANSFER","count_filter","College transfer-count challenges",["CFB_PLAYER","TRANSFERRED_TO","SCHOOL"],["cfb_transfer_summary"],
  "SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id='cfb_transfer_count' AND eligible=1"),
 ("CROSS_IDENTITY","sequence","College-to-NFL identity sequence challenges",["CFB_PLAYER","SAME_PERSON","NFL_PLAYER"],["cross_league_identity_bridge"],
  "SELECT COUNT(*) FROM cross_league_identity_bridge WHERE production_safe=1")
 ]
 for key,mech,desc,path,tables,sql in queries:
  n=c.execute(sql).fetchone()[0]
  cov=min(1,n/100);truth=1.0;amb=.05 if n else 1.0;nov=.9 if key=="CROSS_IDENTITY" else .75
  surf=_surface(n);reasons=[]
  if n<6:reasons.append("TOO_FEW_CANDIDATES")
  if truth<.95:reasons.append("TRUTH_SCORE_LOW")
  if amb>.35:reasons.append("AMBIGUITY_HIGH")
  cert="PASS" if not reasons else "HOLD"
  did=hid("AMD",key,mech);mode="auto_"+key.lower()
  c.execute("""INSERT INTO autonomous_mode_discoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
   (did,key,mech,desc,json.dumps(path),json.dumps(tables),n,cov,truth,amb,nov,surf,cert,json.dumps(reasons),mode,"PROPOSED"))
  rationale=f"{n:,} verified/eligible candidates; recommended as {surf}."
  rid=hid("DMR",did,surf);c.execute("INSERT INTO director_mode_recommendations VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",
   (rid,did,surf,rationale,6,None))
  patterns.append({"pattern":key,"candidates":n,"surface":surf,"certification":cert})
 c.commit();c.close();return patterns

def auto_certify(discovery_id):
 c=db();r=c.execute("SELECT * FROM autonomous_mode_discoveries WHERE discovery_id=?",(discovery_id,)).fetchone()
 if not r:c.close();return {"status":"NOT_FOUND"}
 reasons=[]
 if r["estimated_candidate_count"]<6:reasons.append("TOO_FEW_CANDIDATES")
 if r["coverage_score"]<.5:reasons.append("LOW_COVERAGE")
 if r["truth_score"]<.95:reasons.append("LOW_TRUTH")
 if r["ambiguity_score"]>.35:reasons.append("HIGH_AMBIGUITY")
 status="PASS" if not reasons else "HOLD"
 c.execute("UPDATE autonomous_mode_discoveries SET certification_status=?,certification_reasons_json=? WHERE discovery_id=?",(status,json.dumps(reasons),discovery_id))
 c.commit();c.close();return {"status":status,"reasons":reasons}

def propose_new_games(limit=20):
 discover();c=db()
 rows=[dict(r) for r in c.execute("""SELECT * FROM autonomous_mode_discoveries
 WHERE certification_status='PASS' ORDER BY novelty_score DESC,estimated_candidate_count DESC LIMIT ?""",(limit,))]
 c.close();return rows

def seed_memory():
 examples=[
 ("School Position Connections","Players from the same college who played the same position","connections",
  {"relationship_predicate":"CFB_SAME_SCHOOL_POSITION"},{"path":["CFB_PLAYER","PLAYED_FOR","SCHOOL"]}),
 ("Draft Room Connections","NFL players drafted by the same team at the same position","connections",
  {"relationship_predicate":"NFL_SAME_DRAFT_TEAM_POSITION"},{"path":["NFL_PLAYER","DRAFTED_BY","NFL_TEAM"]}),
 ("Transfer Count","Guess/filter college players by number of transfers","count_filter",
  {"relationship_predicate":"CFB_TRANSFER_COUNT"},{"path":["CFB_PLAYER","TRANSFERRED_TO","SCHOOL"]}),
 ("Career Sequence","Order verified college/NFL career events","sequence",
  {"relationship_predicate":"AWARD_DRAFT_SEQUENCE"},{"path":["CFB_PLAYER","SAME_PERSON","NFL_PLAYER"]})
 ]
 return [remember_template(*x,source="SYSTEM_SEED") for x in examples]

def director_plus(text):
 memories=recall_templates(text,5)
 parsed=parse_advanced(text)
 return {"director":parsed,"matching_memory":memories,"recommendation":
  "Use approved memory template" if memories else "Use parsed Game Director plan"}
