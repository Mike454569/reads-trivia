"""Clue intelligence for progressive, non-giveaway football trivia."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import log2

RELATION_BASE_WEIGHT={
 "DRAFTED_BY":0.72,"ROSTERED_BY":0.55,"ALL_PRO":0.82,"PRO_BOWL":0.76,
 "HOF":0.94,"GAME_APPEARANCE":0.60,"TRANSFER":0.66,"RANKED":0.58,
 "COACHED_BY":0.52,"CHAMPIONSHIP":0.84,
}
GIVEAWAY_RELATIONS={"HOF","CHAMPIONSHIP"}
SEMANTIC_FAMILY={
 "DRAFTED_BY":"draft","ROSTERED_BY":"career","ALL_PRO":"honors","PRO_BOWL":"honors",
 "HOF":"honors","GAME_APPEARANCE":"game","TRANSFER":"career","RANKED":"ranking",
 "COACHED_BY":"coaching","CHAMPIONSHIP":"team_success",
}

@dataclass(frozen=True)
class ScoredClue:
    relation:str
    object_id:str
    season:int|None
    source_id:str
    verification_status:str
    semantic_family:str
    information_gain:float
    giveaway_risk:float
    clue_score:float

def _population_gain(population:int|None,matching:int|None)->float:
    if not population or not matching or population<=0 or matching<=0 or matching>population:
        return 0.0
    return max(0.0,log2(population/matching))

def score_hop(hop,*,population=None,matching=None,current_season=None):
    family=SEMANTIC_FAMILY.get(hop.relation,"other")
    base=RELATION_BASE_WEIGHT.get(hop.relation,0.5)
    gain=_population_gain(population,matching)
    recency=0.0
    if current_season and hop.season:
        age=max(0,current_season-int(hop.season))
        recency=max(0.0,1.0-min(age,30)/30)
    giveaway=(0.72 if hop.relation in GIVEAWAY_RELATIONS else 0.18)
    if gain>7: giveaway=min(1.0,giveaway+.12)
    score=base*45 + min(gain,10)*4 + recency*10 - giveaway*22
    return ScoredClue(
      hop.relation,hop.object_id,hop.season,hop.source_id,hop.verification_status,
      family,round(gain,3),round(giveaway,3),round(score,3)
    )

def order_progressive_clues(chain,*,stats=None,current_season=None,max_clues=3):
    """Hardest useful clue first; strongest giveaway allowed later."""
    stats=stats or {}
    scored=[]
    for h in chain.hops:
        s=stats.get((h.relation,h.object_id,h.season),{})
        scored.append(score_hop(h,population=s.get("population"),matching=s.get("matching"),
                                current_season=current_season))
    if not scored:return []
    # semantic variety first: keep the best clue from each family, then backfill.
    best={}
    for c in scored:
        if c.semantic_family not in best or c.clue_score>best[c.semantic_family].clue_score:
            best[c.semantic_family]=c
    pool=list(best.values())
    leftovers=[c for c in scored if c not in pool]
    pool.sort(key=lambda c:(c.giveaway_risk,-c.clue_score,c.information_gain))
    ordered=[]
    if pool:
        # Opening clue: lowest giveaway among useful clues.
        opening=max(pool,key=lambda c:(c.clue_score-c.giveaway_risk*30,c.information_gain))
        ordered.append(opening); pool.remove(opening)
    # Middle: maximize info without repeating semantic family.
    while pool and len(ordered)<max_clues:
        used={x.semantic_family for x in ordered}
        candidates=[c for c in pool if c.semantic_family not in used] or pool
        pick=max(candidates,key=lambda c:(c.information_gain+c.clue_score/20-c.giveaway_risk*8))
        ordered.append(pick); pool.remove(pick)
    if len(ordered)<max_clues:
        leftovers.sort(key=lambda c:c.clue_score,reverse=True)
        for c in leftovers:
            if c not in ordered:
                ordered.append(c)
                if len(ordered)>=max_clues:break
    # Final clue may be most revealing; sort final two accordingly.
    if len(ordered)>=2:
        head=ordered[:-1]
        tail=max(ordered[-2:],key=lambda c:(c.giveaway_risk,c.information_gain,c.clue_score))
        other=ordered[-2] if tail==ordered[-1] else ordered[-1]
        ordered=head[:-1]+[other,tail] if len(head)>=1 else [other,tail]
    return [asdict(c) for c in ordered[:max_clues]]
