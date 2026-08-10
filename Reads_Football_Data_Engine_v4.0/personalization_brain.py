from pathlib import Path
import sqlite3,json,hashlib
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]
def rebuild_profile(user_id):
 c=db();a=c.execute("SELECT COUNT(*),COALESCE(SUM(correct),0) FROM puzzle_attempts WHERE user_id=?",(user_id,)).fetchone();n=a[0];skill=.5 if n<5 else max(.05,min(.95,a[1]/max(1,n)));modes=[r[0] for r in c.execute("SELECT p.mode_id FROM puzzle_attempts a JOIN puzzle_catalog p USING(puzzle_id) WHERE a.user_id=? GROUP BY p.mode_id ORDER BY COUNT(*) DESC LIMIT 8",(user_id,))];c.execute("INSERT OR REPLACE INTO personalization_profiles(user_id,skill_score,preferred_modes_json,updated_at) VALUES(?,?,?,CURRENT_TIMESTAMP)",(user_id,skill,json.dumps(modes)));c.commit();c.close();return {'user_id':user_id,'attempts':n,'skill_score':skill,'preferred_modes':modes}
def recommend(user_id,limit=12):
 prof=rebuild_profile(user_id);c=db();rows=[]
 for r in c.execute("SELECT puzzle_id,mode_id,difficulty_band FROM puzzle_catalog WHERE eligible=1 ORDER BY RANDOM() LIMIT 500"):
  d={'EASY':.2,'MEDIUM':.45,'HARD':.7,'EXPERT':.9}.get(str(r['difficulty_band']).upper(),.5);score=1-abs(d-prof['skill_score'])+(.15 if r['mode_id'] in prof['preferred_modes'] else 0);rows.append((score,dict(r)))
 out=[]
 for score,r in sorted(rows,key=lambda x:-x[0])[:limit]:out.append({'puzzle_id':r['puzzle_id'],'mode_id':r['mode_id'],'score':round(score,3)})
 c.close();return out
