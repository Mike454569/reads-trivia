"""Mine verified game tables for story-worthy universal events."""
from __future__ import annotations
from .event_ingest import upsert_event

def _tables(c):
    return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def mine_nfl_games(c,limit=None):
    if "nfl_games" not in _tables(c): return {"inserted":0}
    cols={r[1] for r in c.execute("PRAGMA table_info(nfl_games)")}
    need={"game_id","season","home_team","away_team","home_score","away_score"}
    if not need<=cols: return {"inserted":0,"reason":"schema"}
    sql="SELECT game_id,season,home_team,away_team,home_score,away_score FROM nfl_games WHERE home_score IS NOT NULL AND away_score IS NOT NULL"
    if limit: sql+=" LIMIT "+str(int(limit))
    n=0
    for r in c.execute(sql):
        hs=int(r["home_score"]); aw=int(r["away_score"]); total=hs+aw; margin=abs(hs-aw)
        tags=[]; typ=None
        if total>=80: typ="RECORD_EVENT"; tags=["high_scoring","rare_score"]
        elif margin>=35: typ="RECORD_EVENT"; tags=["blowout","rare_margin"]
        elif hs==aw: typ="ON_FIELD_ODDITY"; tags=["tie","rare_result"]
        elif min(hs,aw)==0: typ="RECORD_EVENT"; tags=["shutout"]
        if not typ: continue
        upsert_event(c,{"event_type":typ,"league":"NFL","event_date":str(r["season"])+"-01-01",
          "title":str(r["away_team"])+" vs "+str(r["home_team"])+" unusual game result",
          "neutral_summary":"Final score "+str(aw)+"-"+str(hs)+", a verified game result selected by rarity rules.",
          "source_url":"https://github.com/nflverse/nfldata/blob/master/data/games.csv",
          "source_publisher":"nflverse game data","evidence_tier":"AUTHORITATIVE","verification_status":"VERIFIED",
          "subjects":[{"subject_type":"NFL_TEAM","subject_id":r["away_team"],"role":"away"},
                      {"subject_type":"NFL_TEAM","subject_id":r["home_team"],"role":"home"},
                      {"subject_type":"GAME","subject_id":r["game_id"],"role":"game"}],
          "tags":tags,"sensitive":False})
        n+=1
    return {"inserted":n}
