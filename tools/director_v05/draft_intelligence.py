"""Derived draft intelligence built only from objective, versioned inputs."""
from __future__ import annotations
from collections import defaultdict
from .derivations import draft_value,bust_score,steal_score,store

def _table(conn,name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def derive_nfl_draft_intelligence(conn,*,min_draft_season=1980,max_draft_season=None,commit=True):
    if not _table(conn,"draft_facts"): return {"players":0,"stored":0}
    sql="""SELECT player_key,player_name,draft_season,draft_round,draft_pick_overall
           FROM draft_facts WHERE verification_status='SOURCE_BACKED'
             AND player_key IS NOT NULL AND draft_pick_overall IS NOT NULL
             AND draft_season>=?"""
    args=[min_draft_season]
    if max_draft_season is not None: sql+=" AND draft_season<=?";args.append(max_draft_season)
    rows=conn.execute(sql,args).fetchall()
    stored=0
    for d in rows:
        pid=str(d["player_key"])
        games=starts=0
        if _table(conn,"player_game_stats"):
            g=conn.execute("""SELECT COUNT(DISTINCT game_id) games,
              SUM(CASE WHEN passing_attempts>0 OR carries>0 OR targets>0 OR tackles_combined>0 THEN 1 ELSE 0 END) active_games
              FROM player_game_stats WHERE player_key=?""",(pid,)).fetchone()
            games=int((g["games"] if g else 0) or 0); starts=int((g["active_games"] if g else 0) or 0)
        pb=ap=0; hof=False; inputs=[f"draft:{pid}:{d['draft_season']}:{d['draft_pick_overall']}"]
        if _table(conn,"nfl_pro_bowl_selections"):
            pb=conn.execute("SELECT COUNT(*) n FROM nfl_pro_bowl_selections WHERE player_id=?",(pid,)).fetchone()["n"]
            if pb: inputs.append(f"pro_bowl:{pid}:{pb}")
        if _table(conn,"nfl_all_pro_selections"):
            ap=conn.execute("SELECT COUNT(*) n FROM nfl_all_pro_selections WHERE player_id=?",(pid,)).fetchone()["n"]
            if ap: inputs.append(f"all_pro:{pid}:{ap}")
        if _table(conn,"nfl_hof_inductees"):
            hof=bool(conn.execute("SELECT 1 FROM nfl_hof_inductees WHERE player_id=? LIMIT 1",(pid,)).fetchone())
            if hof: inputs.append(f"hof:{pid}")
        inputs.append(f"game_stats:{pid}:{games}:{starts}")
        kw=dict(pick=d["draft_pick_overall"],career_starts=starts,games=games,pro_bowls=pb,all_pro=ap,hof=hof)
        dv=draft_value(**kw)
        store(conn,"draft_value","NFL_PLAYER",pid,dv,inputs,value_text=d["player_name"],eligible=True)
        store(conn,"bust_score","NFL_PLAYER",pid,bust_score(**kw),inputs,value_text=d["player_name"],eligible=True)
        store(conn,"steal_score","NFL_PLAYER",pid,steal_score(**kw),inputs,value_text=d["player_name"],eligible=True)
        stored+=3
    if commit: conn.commit()
    return {"players":len(rows),"stored":stored}
