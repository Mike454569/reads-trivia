"""Verified SQLite backup + restore helper for Reads v2.1."""
from pathlib import Path
import sqlite3,hashlib,datetime as dt,shutil,json,sys,os
ROOT=Path(__file__).parent;DB=ROOT/"reads_football_v4.0.sqlite";DIR=ROOT/"backups"
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
 return h.hexdigest()
def create():
 # Real incident, fixed here: this used to connect() DIRECTLY to the final
 # `reads_v2.1_<stamp>.sqlite` path and stream src.backup(dst) into it in
 # place. sqlite3.connect() creates that file immediately, before a single
 # page is copied -- so a process kill mid-backup (this machine runs with
 # 1GB RAM copying a multi-GB live DB; confirmed twice in production, Sep 23
 # and Sep 27, both times leaving a 0-byte file sitting at the real backup
 # path instead of the `if integrity!="ok":out.unlink()` cleanup ever
 # running) left a corrupt-but-present file that both looked like a real
 # backup AND was never caught by the integrity check, since the process
 # died before reaching it. Now backs up into a `.tmp` path that can never
 # collide with the `reads_v2.1_*.sqlite` glob _prune_old_backups()/any
 # registry code matches, verifies THAT file's integrity, and only then
 # atomically renames it into the real path with os.replace -- same
 # verify-before-atomic-swap shape safety.py's restore_from_backup()
 # already uses for the live DB. A crash mid-copy now leaves only an
 # orphaned `.tmp` file (harmless, never referenced by anything) and no
 # backup at the real path -- an honest, detectable absence instead of a
 # silent landmine.
 DIR.mkdir(exist_ok=True);stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ");out=DIR/f"reads_v2.1_{stamp}.sqlite";tmp=DIR/f"reads_v2.1_{stamp}.sqlite.tmp"
 tmp.unlink(missing_ok=True)
 src=sqlite3.connect(DB);dst=sqlite3.connect(tmp);src.backup(dst);dst.close();src.close()
 test=sqlite3.connect(tmp);integrity=test.execute("PRAGMA integrity_check").fetchone()[0];test.close()
 if integrity!="ok":tmp.unlink(missing_ok=True);raise RuntimeError(integrity)
 os.replace(tmp,out)
 digest=sha(out);bid="BKP:"+digest[:24];c=sqlite3.connect(DB);c.execute("INSERT OR REPLACE INTO backup_registry VALUES(?,?,?,CURRENT_TIMESTAMP,?,?,?,'VERIFIED',?)",(bid,"FULL","2.1.0",str(out),digest,out.stat().st_size,"SQLite online backup + integrity check"));c.commit();c.close()
 return {"backup_id":bid,"path":str(out),"sha256":digest,"size_bytes":out.stat().st_size}
def verify(path):
 p=Path(path);test=sqlite3.connect(p);i=test.execute("PRAGMA integrity_check").fetchone()[0];test.close();return {"integrity":i,"sha256":sha(p)}
if __name__=="__main__":print(json.dumps(create(),indent=2))
