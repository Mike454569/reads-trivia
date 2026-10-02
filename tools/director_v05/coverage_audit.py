"""Executable coverage audit for Reads Engine v0.5.

Usage:
  python -m tools.director_v05.coverage_audit /data/reads_football_v4.0.sqlite
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
from .audit_spec import AUDIT_FAMILIES

TOKENS={
 "core_identity":("player","team","school","franchise","person"),
 "roster_career":("roster","played_for","affiliation","transfer","transaction"),
 "games":("game","box","play","drive","schedule"),
 "situational":("play","drive","pbp","down","distance"),
 "season_stats":("season","stat","leader"),
 "postseason":("playoff","bowl","championship","super_bowl","cfp"),
 "rankings":("ranking","rank","poll"),
 "honors":("award","honor","all_pro","pro_bowl","all_america","hof"),
 "draft":("draft","combine"),
 "recruiting":("recruit","commit","portal","transfer"),
 "coaching":("coach","coordinator","staff"),
 "money":("contract","salary","cap"),
 "availability":("injury","inactive","suspension","ir_"),
 "venues":("venue","stadium","weather","attendance"),
 "records":("record","streak","milestone"),
 "rules":("rule","era"),
 "off_field":("legal","arrest","discipline","suspension","investigation"),
 "culture_story":("story","event","quote","moment","oddity","controvers"),
 "derived":("derived","metric","score","index"),
}

def _tables(c):
    return [r[0] for r in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")]

def _count(c,t):
    try:return int(c.execute('select count(*) from "'+t.replace('"','""')+'"').fetchone()[0])
    except sqlite3.Error:return -1

def audit(db):
    c=sqlite3.connect(str(db))
    tables=_tables(c); low={t:t.lower() for t in tables}
    out={}
    for fam, concepts in AUDIT_FAMILIES.items():
        hits=[t for t,v in low.items() if any(tok in v for tok in TOKENS.get(fam,()))]
        counts={t:_count(c,t) for t in hits}
        nonempty=[t for t,n in counts.items() if n>0]
        # PRESENT means schema candidates exist and at least one is populated.
        # PARTIAL deliberately remains conservative until concept-level checks
        # are added for era/entity completeness.
        status="PRESENT" if nonempty else ("PARTIAL" if hits else "MISSING")
        out[fam]={"status":status,"concepts":concepts,"tables":hits,"row_counts":counts}
    c.close()
    return out

def main(argv=None):
    argv=argv or sys.argv[1:]
    if not argv: raise SystemExit("database path required")
    p=Path(argv[0]); result=audit(p)
    print(json.dumps({"database":str(p),"families":result},indent=2,sort_keys=True))

if __name__=="__main__": main()
