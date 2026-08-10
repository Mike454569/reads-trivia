from pathlib import Path
import sqlite3,json,hashlib,datetime as dt
import content_studio as S
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]
def gate(object_type,object_id,truth='PASS',qa='PASS',freshness='PASS',release='PASS'):
 reasons=[k for k,v in {'truth':truth,'qa':qa,'freshness':freshness,'release':release}.items() if v!='PASS'];decision='PUBLISH' if not reasons else 'HOLD';gid=hid('GATE',object_type,object_id);c=db();c.execute("INSERT OR REPLACE INTO publication_gate VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",(gid,object_type,object_id,truth,qa,freshness,release,decision,json.dumps(reasons)));c.commit();c.close();return {'decision':decision,'reasons':reasons}
def run_daily(date=None):
 date=date or dt.date.today().isoformat();steps=[];blockers=[]
 try:steps.append({'content':S.build_day(date)})
 except Exception as e:blockers.append('CONTENT:'+str(e))
 status='PASS' if not blockers else 'HOLD';rid=hid('APR','AUTO_DAILY',date);c=db();c.execute("INSERT OR REPLACE INTO autopilot_runs(run_id,job_id,finished_at,status,steps_json,blockers_json) VALUES(?,?,CURRENT_TIMESTAMP,?,?,?)",(rid,'AUTO_DAILY',status,json.dumps(steps),json.dumps(blockers)));c.commit();c.close();return {'run_id':rid,'status':status,'steps':steps,'blockers':blockers}
