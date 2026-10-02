"""Read-only bridge from legacy Engine tables to normalized v0.5 facts.

Adapters are deliberately declarative: no table is exposed unless its
verification/source columns and identity keys are known.
"""
from __future__ import annotations
import hashlib

ADAPTERS={
 "nfl_games":{
  "table":"games","kind":"GAME_RESULT","id":"game_id",
  "columns":("game_id","season","week","game_type","game_date","away_team","away_score","home_team","home_score","source_id"),
  "where":"home_score IS NOT NULL AND away_score IS NOT NULL","verification":None,
 },
 "cfb_games":{
  "table":"cfb_games_canonical","kind":"GAME_RESULT","id":"game_id",
  "columns":("game_id","season","week","game_date","away_school_id","away_score","home_school_id","home_score","source_id","verification_status"),
  "where":"home_score IS NOT NULL AND away_score IS NOT NULL","verification":"SOURCE_BACKED",
 },
 "cfb_rankings":{
  "table":"cfb_rankings","kind":"RANKING","id":"record_id",
  "columns":("record_id","season","week","season_type","poll","rank","school_id","school_name_raw","source_id","verification_status"),
  "where":"1=1","verification":"SOURCE_BACKED",
 },
 "nfl_draft":{
  "table":"draft_facts","kind":"DRAFT","id":"player_key",
  "columns":("player_key","player_name","draft_season","draft_round","draft_pick_overall","draft_team","source_id","verification_status"),
  "where":"1=1","verification":"SOURCE_BACKED",
 },
 "nfl_all_pro":{
  "table":"nfl_all_pro_selections","kind":"AWARD","id":"selection_id",
  "columns":("selection_id","season","position_raw","player_id","player_name_raw","honor_level","source_id","verification_status"),
  "where":"is_ap=1","verification":"WIKIPEDIA_STRUCTURED_SECONDARY",
 },
 "nfl_pro_bowl":{
  "table":"nfl_pro_bowl_selections","kind":"AWARD","id":"selection_id",
  "columns":("selection_id","season","position_raw","player_name_raw","tier","source_id","verification_status"),
  "where":"1=1","verification":"WIKIPEDIA_STRUCTURED_SECONDARY",
 },
 "nfl_hof":{
  "table":"nfl_hof_inductees","kind":"AWARD","id":"hof_id",
  "columns":("hof_id","class_year","position_raw","inductee_name_raw","source_id","verification_status"),
  "where":"is_player=1","verification":"WIKIPEDIA_STRUCTURED_SECONDARY",
 },
 "nfl_championships":{
  "table":"season_standings","kind":"CHAMPIONSHIP","id":None,
  "columns":("season","team_code","wins","losses","ties","playoff_result","source_id","verification_status"),
  "where":"playoff_result IS NOT NULL","verification":"SOURCE_BACKED",
 },
 "nfl_coaching":{
  "table":"coach_team_seasons","kind":"COACHING","id":None,
  "columns":("season","team_code","coach_id","coach_name","games_observed","source_id","verification_status"),
  "where":"1=1","verification":"SOURCE_BACKED",
 },
 "nfl_pbp":{
  "table":"nfl_plays","kind":"PLAY","id":"play_id",
  "columns":("game_id","play_id","season","week","qtr","down","ydstogo","yardline_100","play_type","play_desc","yards_gained","touchdown","posteam","defteam","passer_player_key","receiver_player_key","rusher_player_key"),
  "where":"1=1","verification":None,
 },
 "cfb_pbp":{
  "table":"cfb_plays","kind":"PLAY","id":"play_id",
  "columns":("game_id","play_id","season","week","drive_id","offense_school_id","defense_school_id","play_type","play_text","yards_gained","scoring"),
  "where":"1=1","verification":None,
 },
 "cfb_rivalries":{
  "table":"cfb_rivalries","kind":"RIVALRY","id":"rivalry_id",
  "columns":("rivalry_id","matchup","school_a_id","school_a","school_b_id","school_b","nickname","trophy","series_record","fun_fact"),
  "where":"school_a_id IS NOT NULL AND school_b_id IS NOT NULL","verification":None,
 },
 "nfl_roster":{
  "table":"canonical_roster_seasons","kind":"ROSTER","id":None,
  "columns":("player_id","season","team_code","source_id","verification_status"),
  "where":"1=1","verification":"SOURCE_BACKED",
 },
}

def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def available(conn):
    tables=_tables(conn)
    return {name:(spec["table"] in tables) for name,spec in ADAPTERS.items()}

def _stable_id(adapter,spec,row):
    if spec["id"] and row[spec["id"]] is not None:
        raw=str(row[spec["id"]])
    else:
        raw="|".join(str(row[c]) for c in spec["columns"])
    return "legacy_"+hashlib.sha256((adapter+"|"+raw).encode()).hexdigest()[:24]

def iter_facts(conn,adapter,*,limit=None):
    if adapter not in ADAPTERS: raise ValueError("unknown legacy adapter")
    spec=ADAPTERS[adapter]
    if spec["table"] not in _tables(conn): return
    cols=spec["columns"]
    sql="SELECT "+",".join(cols)+" FROM "+spec["table"]+" WHERE "+spec["where"]
    args=[]
    if spec["verification"] and "verification_status" in cols:
        sql+=" AND verification_status=?"; args.append(spec["verification"])
    sql+=" ORDER BY "+(spec["id"] or ",".join(cols[:2]))
    if limit is not None:
        sql+=" LIMIT ?"; args.append(max(1,min(int(limit),100000)))
    cur=conn.execute(sql,args)
    keys=[d[0] for d in cur.description]
    for raw in cur:
        row=dict(zip(keys,raw))
        yield {
          "fact_id":_stable_id(adapter,spec,row),"kind":spec["kind"],
          "legacy_adapter":adapter,"legacy_table":spec["table"],
          "source_id":row.get("source_id"),"verification_status":row.get("verification_status"),
          "data":row,
        }

def bridge_report(conn):
    report={}
    tables=_tables(conn)
    for name,spec in ADAPTERS.items():
        if spec["table"] not in tables:
            report[name]={"status":"MISSING_TABLE","count":0}; continue
        q="SELECT COUNT(*) FROM "+spec["table"]+" WHERE "+spec["where"]
        args=[]
        if spec["verification"] and "verification_status" in spec["columns"]:
            q+=" AND verification_status=?";args.append(spec["verification"])
        count=conn.execute(q,args).fetchone()[0]
        report[name]={"status":"READY" if count else "EMPTY","count":count,"kind":spec["kind"],"table":spec["table"]}
    return report
