"""Difficulty-aware clue plans for universal chain trivia."""
from __future__ import annotations
from .clue_intelligence import order_progressive_clues

BANDS={
 "CASUAL":{"max_clues":3,"min_gain":0.0,"max_giveaway_first":0.65,"target":35},
 "HARD":{"max_clues":3,"min_gain":1.0,"max_giveaway_first":0.40,"target":65},
 "SICKO":{"max_clues":3,"min_gain":2.0,"max_giveaway_first":0.28,"target":88},
}

def plan(chain,band,*,stats=None,current_season=None):
    band=band.upper()
    if band not in BANDS: raise ValueError("unknown difficulty band")
    cfg=BANDS[band]
    clues=order_progressive_clues(chain,stats=stats,current_season=current_season,max_clues=cfg["max_clues"])
    useful=[c for c in clues if c["information_gain"]>=cfg["min_gain"]]
    if len(useful)>=2: clues=useful
    if clues and clues[0]["giveaway_risk"]>cfg["max_giveaway_first"]:
        safer=sorted(clues,key=lambda c:(c["giveaway_risk"],-c["clue_score"]))
        clues=safer
    return {
      "difficulty_band":band,"target_difficulty":cfg["target"],
      "chain_difficulty":chain.difficulty_score,
      "clues":clues,
      "progressive":True,
      "reveal_order":"hard-to-easy",
    }
