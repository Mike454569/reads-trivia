"""Verified SQLite backup + restore helper for Reads v2.1."""
from pathlib import Path
import sqlite3,hashlib,datetime as dt,shutil,json,sys
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite";DIR=ROOT/"backups"
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
 return h.hexdigest()
def create():
 DIR.mkdir(exist_ok=True);stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ");out=DIR/f"reads_v2.1_{stamp}.sqlite"
 src=sqlite3.connect(DB);dst=sqlite3.connect(out);src.backup(dst);dst.close();src.close()
 test=sqlite3.connect(out);integrity=test.execute("PRAGMA integrity_check").fetchone()[0];test.close()
 if integrity!="ok":out.unlink();raise RuntimeError(integrity)
 digest=sha(out);bid="BKP:"+digest[:24];c=sqlite3.connect(DB);c.execute("INSERT OR REPLACE INTO backup_registry VALUES(?,?,?,CURRENT_TIMESTAMP,?,?,?,'VERIFIED',?)",(bid,"FULL","2.1.0",str(out),digest,out.stat().st_size,"SQLite online backup + integrity check"));c.commit();c.close()
 return {"backup_id":bid,"path":str(out),"sha256":digest,"size_bytes":out.stat().st_size}
def verify(path):
 p=Path(path);test=sqlite3.connect(p);i=test.execute("PRAGMA integrity_check").fetchone()[0];test.close();return {"integrity":i,"sha256":sha(p)}
if __name__=="__main__":print(json.dumps(create(),indent=2))
