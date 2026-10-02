"""Evidence-first multi-hop intelligence for deep Creator questions."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib

@dataclass(frozen=True)
class Hop:
    relation:str
    subject_id:str
    object_id:str
    season:int|None=None
    source_id:str|None=None
    verification_status:str|None=None

@dataclass(frozen=True)
class Chain:
    chain_id:str
    anchor_type:str
    anchor_id:str
    hops:tuple[Hop,...]
    depth:int
    rarity_score:float
    difficulty_score:float
    provenance_complete:bool

_VERIFIED={"SOURCE_BACKED","SOURCE_BACKED_DERIVED","WIKIPEDIA_STRUCTURED_SECONDARY","SOURCE_BACKED_INHERITED"}

def _hop(relation,row):
    return Hop(relation,str(row["subject_id"]),str(row["object_id"]),row.get("season"),
               row.get("source_id"),row.get("verification_status"))

def _quality(hops):
    complete=all(h.source_id and (h.verification_status in _VERIFIED) for h in hops)
    unique_objects=len({(h.relation,h.object_id) for h in hops})
    rarity=round(min(10.0, unique_objects/max(len(hops),1)*4 + len(hops)*.6),3)
    difficulty=round(min(100.0, 18+len(hops)*13+rarity*3),2)
    return complete,rarity,difficulty

def build_chain(anchor_type,anchor_id,hops):
    hops=tuple(hops)
    if len(hops)<2: raise ValueError("deep chain requires at least two hops")
    complete,rarity,difficulty=_quality(hops)
    if not complete: raise ValueError("chain contains unverified or unsourced hop")
    seed="|".join([anchor_type,str(anchor_id)]+[f"{h.relation}:{h.subject_id}:{h.object_id}:{h.season}" for h in hops])
    return Chain("chain_"+hashlib.sha256(seed.encode()).hexdigest()[:24],
                 anchor_type,str(anchor_id),hops,len(hops),rarity,difficulty,complete)

def player_nfl_chains(conn,player_id):
    """Discover independently sourced player career chains; no name joins."""
    from .relationships import traverse
    groups=[]
    roster=traverse(conn,"PLAYER_ROSTER_TEAM",player_id)
    draft=traverse(conn,"PLAYER_DRAFT",player_id)
    allpro=traverse(conn,"PLAYER_ALL_PRO",player_id)
    games=traverse(conn,"PLAYER_GAME_LOG",player_id,limit=5000)
    if draft and roster:
        groups.append([_hop("DRAFTED_BY",draft[0]),_hop("ROSTERED_BY",roster[-1])])
    if draft and allpro:
        groups.append([_hop("DRAFTED_BY",draft[0]),_hop("ALL_PRO",allpro[-1])])
    if draft and games:
        best=max(games,key=lambda x:(x.get("pass_yards") or 0)+(x.get("rush_yards") or 0)+(x.get("receiving_yards") or 0))
        groups.append([_hop("DRAFTED_BY",draft[0]),_hop("GAME_APPEARANCE",best)])
    if roster and allpro and games:
        groups.append([_hop("ROSTERED_BY",roster[-1]),_hop("ALL_PRO",allpro[-1]),_hop("GAME_APPEARANCE",games[-1])])
    out=[]
    for hops in groups:
        try: out.append(build_chain("NFL_PLAYER",player_id,hops))
        except ValueError: pass
    return sorted(out,key=lambda c:(c.difficulty_score,c.depth),reverse=True)

def chain_payload(chain):
    d=asdict(chain)
    d["hops"]=[asdict(h) for h in chain.hops]
    d["answer_provenance_required"]=True
    return d
