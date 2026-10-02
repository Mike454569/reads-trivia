"""Ambiguity/uniqueness gates for multi-hop trivia."""
from __future__ import annotations

def player_signature(chain):
    sig=[]
    for c in chain.get("clues",()):
        if c["type"]=="draft": sig.append(("draft",c["text"]))
        elif c["type"]=="journey": sig.append(("journey",c["text"]))
        elif c["type"]=="honor": sig.append(("honor",c["text"]))
        elif c["type"]=="peak_game": sig.append(("peak_game",c["text"]))
    return tuple(sig)

def uniqueness_check(target_chain,candidate_chains,*,min_clues=2):
    target=player_signature(target_chain)
    if len(target)<min_clues:
        return {"unique":False,"reason":"INSUFFICIENT_CLUES","collisions":[]}
    collisions=[]
    t=set(target)
    for other in candidate_chains:
        if other.get("subject_id")==target_chain.get("subject_id"): continue
        o=set(player_signature(other))
        # A candidate is ambiguous when it satisfies every disclosed target clue.
        if t.issubset(o): collisions.append(other.get("subject_id"))
    return {"unique":not collisions,"reason":"UNIQUE" if not collisions else "AMBIGUOUS_ANSWER",
            "collisions":collisions}

def certify_payload(payload,uniqueness):
    if not payload.get("input_fact_ids"): raise ValueError("missing provenance")
    if payload.get("requires_unique_answer") and not uniqueness.get("unique"):
        raise ValueError("ambiguous answer")
    out=dict(payload); out["certified"]=True; out["uniqueness"]=uniqueness
    return out
