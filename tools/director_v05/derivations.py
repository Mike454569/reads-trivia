"""Versioned derivation framework for Reads Engine v0.5."""
from __future__ import annotations
import hashlib, json, math
from .universal_schema import install

FORMULAS={
 "draft_value":"1.0.0","bust_score":"1.0.0","steal_score":"1.0.0",
 "comeback_magnitude":"1.0.0","upset_magnitude":"1.0.0",
 "career_journey":"1.0.0","rarity":"1.0.0",
}

def _clamp(x,lo=0.0,hi=100.0): return max(lo,min(hi,float(x)))

def draft_value(*,pick,career_starts=0,games=0,pro_bowls=0,all_pro=0,hof=False):
    """Career return vs draft capital. Objective inputs only."""
    pick=max(1,int(pick)); expected=_clamp(101-(pick-1)*100/261)
    output=_clamp(career_starts*.45+games*.08+pro_bowls*8+all_pro*13+(25 if hof else 0))
    return round(output-expected,2)

def bust_score(**kw): return round(_clamp(-draft_value(**kw)),2)
def steal_score(**kw): return round(_clamp(draft_value(**kw)),2)

def comeback_magnitude(*,largest_deficit,won):
    return float(max(0,largest_deficit)) if won else 0.0

def upset_magnitude(*,winner_rank,loser_rank=None,loser_ranked=True):
    """Higher means larger ranking shock; unranked winner is represented as 26."""
    w=26 if winner_rank is None else int(winner_rank)
    l=26 if (loser_rank is None and not loser_ranked) else int(loser_rank or 26)
    return float(max(0,w-l))

def career_journey(*,team_stops=0,college_stops=0,transfers=0,transactions=0):
    return round(team_stops+college_stops+1.5*transfers+.35*transactions,2)

def rarity(*,population,matching):
    if population<=0 or matching<=0 or matching>population: raise ValueError("invalid rarity population")
    return round(-math.log10(matching/population),4)

def store(conn,metric,subject_type,subject_id,value,input_fact_ids,*,value_text=None,eligible=True):
    if metric not in FORMULAS: raise ValueError("unknown metric")
    ids=sorted(set(str(x) for x in input_fact_ids if str(x)))
    if not ids: raise ValueError("derived facts require input fact IDs")
    install(conn)
    version=FORMULAS[metric]
    seed="|".join((metric,subject_type,str(subject_id),version,*ids))
    did="drv_"+hashlib.sha256(seed.encode()).hexdigest()[:24]
    conn.execute(
      """INSERT INTO universal_derived_fact
      (derived_id,metric,subject_type,subject_id,value_num,value_text,formula_version,input_fact_ids_json,eligible_for_gameplay)
      VALUES(?,?,?,?,?,?,?,?,?)
      ON CONFLICT(derived_id) DO UPDATE SET value_num=excluded.value_num,value_text=excluded.value_text,
      input_fact_ids_json=excluded.input_fact_ids_json,eligible_for_gameplay=excluded.eligible_for_gameplay,
      computed_at=CURRENT_TIMESTAMP""",
      (did,metric,subject_type,str(subject_id),float(value),value_text,version,json.dumps(ids),1 if eligible else 0))
    conn.commit()
    return did
