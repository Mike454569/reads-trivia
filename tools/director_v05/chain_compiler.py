"""Compile a verified knowledge chain into mechanic-neutral question material."""
from __future__ import annotations
from .chain_engine import chain_payload

MECHANICS={"WHO_AM_I","THREE_CLUES","MULTIPLE_CHOICE","MATCHING","COMMON_LINK","ELIMINATION","SURVIVAL","DAILY","ENDLESS"}

def compile_chain(chain,mechanic,*,difficulty=None):
    mechanic=mechanic.upper()
    if mechanic not in MECHANICS:raise ValueError("mechanic cannot consume a relationship chain")
    if not chain.provenance_complete:raise ValueError("unverified chain")
    hops=[{"relation":h.relation,"object_id":h.object_id,"season":h.season,
           "source_id":h.source_id,"verification_status":h.verification_status} for h in chain.hops]
    return {
      "compiler_version":"1.0.0","mechanic":mechanic,
      "answer":{"type":chain.anchor_type,"id":chain.anchor_id},
      "clues":hops,"chain_id":chain.chain_id,"depth":chain.depth,
      "rarity_score":chain.rarity_score,
      "difficulty_score":chain.difficulty_score if difficulty is None else difficulty,
      "provenance":chain_payload(chain),
      "answer_provenance_required":True,
    }
