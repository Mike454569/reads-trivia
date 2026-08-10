from pathlib import Path
import sqlite3,json,hashlib,datetime as dt
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]
def build_day(date=None,slots=6):
 date=date or dt.date.today().isoformat();c=db();modes=[r[0] for r in c.execute("SELECT mode_id FROM mode_health WHERE eligible_puzzles>0 ORDER BY eligible_puzzles DESC")];out=[];used=set()
 for m in modes:
  if len(out)>=slots:break
  n=c.execute("SELECT COUNT(*) FROM puzzle_catalog WHERE mode_id=? AND eligible=1",(m,)).fetchone()[0]
  if not n:continue
  off=int(hashlib.sha256((date+'|'+m).encode()).hexdigest()[:8],16)%n
  p=c.execute("SELECT puzzle_id FROM puzzle_catalog WHERE mode_id=? AND eligible=1 ORDER BY puzzle_id LIMIT 1 OFFSET ?",(m,off)).fetchone()
  if not p or p[0] in used:continue
  slot=f"SLOT_{len(out)+1}";sid=hid('CS',date,slot,m,p[0])
  c.execute("INSERT OR REPLACE INTO content_schedule(schedule_id,publish_date,slot_key,content_type,mode_id,puzzle_id,headline,payload_json,qa_status,status) VALUES(?,?,?,?,?,?,?,?,?,?)",(sid,date,slot,'DAILY_GAME',m,p[0],f"Today's {m.replace('_',' ').title()}",json.dumps({'source':'AUTO_STUDIO'}),'PASS','SCHEDULED'))
  used.add(p[0]);out.append({'slot':slot,'mode_id':m,'puzzle_id':p[0]})
 rid=hid('CSR','DAILY',date);c.execute("INSERT OR REPLACE INTO content_studio_runs(run_id,run_type,target_date,generated_count,held_count,details_json) VALUES(?,?,?,?,?,?)",(rid,'DAILY',date,len(out),max(0,slots-len(out)),json.dumps(out)));c.commit();c.close();return {'date':date,'generated':len(out),'slots':out}
def themed_pack(title,keyword,limit=20):
 c=db();cid=hid('CMP',title,keyword);c.execute("INSERT OR REPLACE INTO content_campaigns(campaign_id,campaign_type,title,theme_json,status) VALUES(?,?,?,?,?)",(cid,'THEMED_PACK',title,json.dumps({'keyword':keyword}),'DRAFT'));rows=[dict(r) for r in c.execute("SELECT puzzle_id,mode_id FROM puzzle_catalog WHERE eligible=1 AND (mode_id LIKE ? OR payload_json LIKE ?) LIMIT ?",(f'%{keyword.lower()}%',f'%{keyword}%',limit))];c.commit();c.close();return {'campaign_id':cid,'candidates':rows}
