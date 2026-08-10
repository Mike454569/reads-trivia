
from __future__ import annotations
from pathlib import Path
import sqlite3, json, hashlib, random

DB=Path(__file__).with_name("reads_football_v4.0.sqlite")

def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def seeded_index(seed,n):
    return int(hashlib.sha256(str(seed).encode()).hexdigest()[:16],16)%n

def list_templates():
    c=con()
    rows=[dict(r) for r in c.execute("""
      SELECT template_id,display_name,mechanic,nfl_status,cfb_status,notes
      FROM game_mode_templates ORDER BY display_name
    """)]
    c.close(); return rows

def list_bindings(competition):
    c=con()
    rows=[dict(r) for r in c.execute("""
      SELECT b.template_id,t.display_name,t.mechanic,b.concrete_mode_id,b.status,
             b.source_view,b.eligibility_rule
      FROM league_mode_bindings b
      JOIN game_mode_templates t ON t.template_id=b.template_id
      WHERE b.competition_id=? ORDER BY t.display_name
    """,(competition.upper(),))]
    c.close(); return rows

def generated_pack(competition,mode,seed="daily:1"):
    c=con()
    r=c.execute("""
      SELECT pack_id,competition_id,mode_id,seed_text,difficulty_band,payload_json,verification_status
      FROM generated_game_packs WHERE competition_id=? AND mode_id=? AND seed_text=?
    """,(competition.upper(),mode,seed)).fetchone()
    if not r:
        rows=list(c.execute("""
          SELECT pack_id,competition_id,mode_id,seed_text,difficulty_band,payload_json,verification_status
          FROM generated_game_packs WHERE competition_id=? AND mode_id=? ORDER BY seed_text
        """,(competition.upper(),mode)))
        if not rows:
            c.close(); return None
        r=rows[seeded_index(f"{competition}|{mode}|{seed}",len(rows))]
    out=dict(r);out["payload"]=json.loads(out.pop("payload_json"));c.close();return out

def single_puzzle(mode,seed="daily",difficulty=None):
    c=con()
    sql="SELECT * FROM puzzle_catalog WHERE mode_id=? AND eligible=1";params=[mode]
    if difficulty:
        sql+=" AND difficulty_band=?";params.append(difficulty.upper())
    sql+=" ORDER BY puzzle_id"
    rows=list(c.execute(sql,params))
    if not rows:
        c.close();return None
    r=rows[seeded_index(f"{mode}|{seed}|{difficulty}",len(rows))]
    out=dict(r);out["payload"]=json.loads(out.pop("payload_json"));c.close();return out

def cfb_daily(seed="daily:1"):
    modes=["cfb_matching","cfb_ordering","cfb_connections","cfb_odd_one_out"]
    packs=[generated_pack("CFB",m,seed) for m in modes]
    singles=[
      single_puzzle("college_of_player",seed),
      single_puzzle("award_winner",seed),
      single_puzzle("award_school",seed),
      single_puzzle("cfb_champion_by_year",seed),
      single_puzzle("cfb_coach_school",seed)
    ]
    return {"competition":"CFB","seed":seed,"generated_packs":[x for x in packs if x],
            "single_puzzles":[x for x in singles if x]}

def nfl_daily(seed="daily:1"):
    modes=["nfl_matching","nfl_ordering","nfl_connections","nfl_odd_one_out"]
    packs=[generated_pack("NFL",m,seed) for m in modes]
    singles=[
      single_puzzle("draft_team",seed),
      single_puzzle("draft_pick",seed),
      single_puzzle("draft_round",seed),
      single_puzzle("season_record",seed),
      single_puzzle("playoff_seed",seed),
      single_puzzle("coach_from_team_season",seed),
      single_puzzle("stadium_from_game",seed)
    ]
    return {"competition":"NFL","seed":seed,"generated_packs":[x for x in packs if x],
            "single_puzzles":[x for x in singles if x]}

if __name__=="__main__":
    print(json.dumps({"NFL":nfl_daily("daily:1"),"CFB":cfb_daily("daily:1")},indent=2))
