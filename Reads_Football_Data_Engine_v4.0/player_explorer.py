
from pathlib import Path
import sqlite3,json,sys
DB=Path(__file__).with_name("reads_football_v4.0.sqlite")
def search(q,limit=20):
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    rows=[dict(r) for r in c.execute("""SELECT player_type,player_id,display_name,primary_team_or_school,
      first_year,last_year,graph_degree FROM player_profiles
      WHERE lower(display_name) LIKE ? ORDER BY graph_degree DESC,display_name LIMIT ?""",(f"%{q.lower()}%",limit))]
    c.close();return rows
def profile(pt,pid):
    c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
    r=c.execute("SELECT * FROM player_profiles WHERE player_type=? AND player_id=?",(pt,pid)).fetchone()
    c.close()
    if not r:return None
    x=dict(r);x["profile"]=json.loads(x.pop("profile_json"));return x
if __name__=="__main__":
    if len(sys.argv)>=4 and sys.argv[1]=="profile": print(json.dumps(profile(sys.argv[2],sys.argv[3]),indent=2))
    else: print(json.dumps(search(" ".join(sys.argv[1:]) or "Brady"),indent=2))
