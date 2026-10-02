"""Quality gates for universal chain-backed questions."""
from __future__ import annotations
from collections import Counter

def signature(chain):
    return tuple((h.relation,h.object_id,h.season) for h in chain.hops)

def uniqueness_report(chains):
    sigs=Counter(signature(c) for c in chains)
    return {c.chain_id:{"unique":sigs[signature(c)]==1,"collision_count":sigs[signature(c)]}
            for c in chains}

def eligible_chains(chains,*,recent_anchor_ids=(),min_depth=2,min_difficulty=0,max_difficulty=100):
    recent={str(x) for x in recent_anchor_ids}
    report=uniqueness_report(chains)
    out=[]
    for c in chains:
        if not c.provenance_complete: continue
        if c.anchor_id in recent: continue
        if c.depth<min_depth: continue
        if not min_difficulty<=c.difficulty_score<=max_difficulty: continue
        if not report[c.chain_id]["unique"]: continue
        out.append(c)
    return out

def explain_rejection(chain,chains,*,recent_anchor_ids=(),min_depth=2):
    if not chain.provenance_complete:return "INCOMPLETE_PROVENANCE"
    if chain.anchor_id in {str(x) for x in recent_anchor_ids}:return "RECENT_REPEAT"
    if chain.depth<min_depth:return "TOO_SHALLOW"
    if not uniqueness_report(chains)[chain.chain_id]["unique"]:return "AMBIGUOUS_CHAIN"
    return None
