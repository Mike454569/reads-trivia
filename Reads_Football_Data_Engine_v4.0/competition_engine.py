from pathlib import Path
import sqlite3,json,hashlib
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
def db():c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def hid(p,*x):return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]
def create_season(name,kind='RANKED'):
 sid=hid('SEA',name,kind);c=db();c.execute("INSERT OR IGNORE INTO competition_seasons(season_id,name,competition_type,status) VALUES(?,?,?,'ACTIVE')",(sid,name,kind));c.commit();c.close();return sid
def join(sid,user):c=db();c.execute("INSERT OR IGNORE INTO competition_entries(season_id,user_id) VALUES(?,?)",(sid,user));c.commit();c.close()
def create_match(sid,a,b,count=5):
 c=db();p=[r[0] for r in c.execute("SELECT puzzle_id FROM puzzle_catalog WHERE eligible=1 ORDER BY RANDOM() LIMIT ?",(count,))];mid=hid('MAT',sid,a,b,*p);c.execute("INSERT INTO competition_matches(match_id,season_id,player_a,player_b,puzzle_ids_json) VALUES(?,?,?,?,?)",(mid,sid,a,b,json.dumps(p)));c.commit();c.close();return {'match_id':mid,'puzzles':p}
def report(mid,score_a,score_b):
 c=db();m=c.execute("SELECT * FROM competition_matches WHERE match_id=?",(mid,)).fetchone();
 if not m:c.close();return {'status':'NOT_FOUND'}
 winner=m['player_a'] if score_a>score_b else m['player_b'] if score_b>score_a else None;c.execute("UPDATE competition_matches SET status='FINAL',score_a=?,score_b=?,winner_user_id=? WHERE match_id=?",(score_a,score_b,winner,mid));c.commit();c.close();return {'winner':winner}
