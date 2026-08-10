"""Generate PostgreSQL production schema from Reads v2.1 SQLite."""
from pathlib import Path
import sqlite3,re,json
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite"
TYPE={"INTEGER":"BIGINT","REAL":"DOUBLE PRECISION","TEXT":"TEXT","BLOB":"BYTEA","NUMERIC":"NUMERIC"}
def q(n):return '"'+n.replace('"','""')+'"'
def generate(out=None):
 c=sqlite3.connect(DB);tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
 lines=["-- Reads Football v2.1 PostgreSQL production schema","BEGIN;"]
 for t in tables:
  cols=c.execute(f"PRAGMA table_info({q(t)})").fetchall();defs=[]
  pks=[x for x in cols if x[5]]
  for _,name,typ,notnull,dflt,pk in cols:
   base=(typ or "TEXT").upper().split("(")[0];sqlt=TYPE.get(base,"TEXT");s=f"{q(name)} {sqlt}"
   if notnull:s+=" NOT NULL"
   if dflt is not None:
    d=str(dflt)
    if "CURRENT_TIMESTAMP" in d.upper():d="CURRENT_TIMESTAMP"
    s+=" DEFAULT "+d
   defs.append(s)
  if pks:defs.append("PRIMARY KEY ("+", ".join(q(x[1]) for x in sorted(pks,key=lambda x:x[5]))+")")
  lines.append(f"CREATE TABLE IF NOT EXISTS {q(t)} (\n  "+",\n  ".join(defs)+"\n);")
 lines+=["COMMIT;"]
 c.close();text="\n\n".join(lines);out=Path(out or ROOT/"postgres_v2_1_schema.sql");out.write_text(text,encoding="utf-8");return {"tables":len(tables),"path":str(out)}
if __name__=="__main__":print(json.dumps(generate(),indent=2))
