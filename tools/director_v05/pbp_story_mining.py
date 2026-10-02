"""Mine verified NFL PBP into universal story events."""
from __future__ import annotations
from collections import defaultdict
from .event_ingest import upsert_event
from .pbp_detectors import classify

def mine_nfl_pbp(c,limit_games=None):
    tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "nfl_plays" not in tables:return {"events":0,"reason":"missing_table"}
    cols={r[1] for r in c.execute("PRAGMA table_info(nfl_plays)")}
    required={"game_id","play_id","season","play_desc","yards_gained","touchdown","posteam","defteam"}
    if not required<=cols:return {"events":0,"reason":"schema","missing":sorted(required-cols)}
    optional=["down","interception","fumble_lost","own_kickoff_recovery","wpa"]
    selected=sorted(required)+[x for x in optional if x in cols]
    by=defaultdict(list)
    for raw in c.execute("SELECT "+",".join(selected)+" FROM nfl_plays ORDER BY game_id,play_id"):
        d=dict(raw);by[str(d["game_id"])].append(d)
    events=0;kinds=defaultdict(int)
    for index,(gid,plays) in enumerate(by.items()):
        if limit_games and index>=limit_games:break
        seen=set()
        for p in plays:
            for key,typ,tags,summary in classify(p):
                if key in seen:continue
                seen.add(key)
                subjects=[{"subject_type":"GAME","subject_id":gid,"role":"game"}]
                if p.get("posteam"):subjects.append({"subject_type":"NFL_TEAM","subject_id":p["posteam"],"role":"possession"})
                if p.get("defteam"):subjects.append({"subject_type":"NFL_TEAM","subject_id":p["defteam"],"role":"defense"})
                upsert_event(c,{"event_type":typ,"league":"NFL","event_date":str(p["season"])+"-01-01",
                  "title":summary+" in "+gid,"neutral_summary":summary+" in verified play-by-play for "+gid+".",
                  "source_url":"https://github.com/nflverse/nflverse-data/releases","source_publisher":"nflverse play-by-play",
                  "evidence_tier":"AUTHORITATIVE","verification_status":"VERIFIED","subjects":subjects,
                  "tags":tags,"sensitive":False})
                events+=1;kinds[key.split(":")[0]]+=1
    c.commit()
    return {"games_scanned":min(len(by),limit_games or len(by)),"events":events,"kinds":dict(kinds)}
