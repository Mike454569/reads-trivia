"""Compile a verified knowledge chain into mechanic-neutral question material."""
from __future__ import annotations
from .chain_engine import chain_payload
from .difficulty_planner import plan as plan_difficulty
from .distractor_intelligence import select_distractors, validate_distractors

MECHANICS={"WHO_AM_I","THREE_CLUES","MULTIPLE_CHOICE","MATCHING","COMMON_LINK","ELIMINATION","SURVIVAL","DAILY","ENDLESS"}

def compile_chain(chain,mechanic,*,difficulty=None,difficulty_band=None,clue_stats=None,current_season=None,
                  correct_candidate=None,distractor_candidates=(),all_correct_ids=(),recent_distractor_ids=()):
    mechanic=mechanic.upper()
    if mechanic not in MECHANICS:raise ValueError("mechanic cannot consume a relationship chain")
    if not chain.provenance_complete:raise ValueError("unverified chain")
    hops=[{"relation":h.relation,"object_id":h.object_id,"season":h.season,
           "source_id":h.source_id,"verification_status":h.verification_status} for h in chain.hops]
    clue_plan=None
    if difficulty_band:
        clue_plan=plan_difficulty(chain,difficulty_band,stats=clue_stats,current_season=current_season)
        hops=clue_plan["clues"]
    distractors=[]
    if correct_candidate is not None and mechanic in {"MULTIPLE_CHOICE","MATCHING","ELIMINATION","SURVIVAL","DAILY","ENDLESS"}:
        distractors=select_distractors(
            correct_candidate,distractor_candidates,k=3,
            forbidden_ids=all_correct_ids,recent_ids=recent_distractor_ids)
        problem=validate_distractors(correct_candidate,distractors,all_correct_ids=all_correct_ids)
        if problem: raise ValueError(problem)
        if len(distractors)<3: raise ValueError("INSUFFICIENT_PLAUSIBLE_DISTRACTORS")
    return {
      "compiler_version":"1.2.0","mechanic":mechanic,
      "answer":{"type":chain.anchor_type,"id":chain.anchor_id},
      "clues":hops,"clue_plan":clue_plan,"distractors":distractors,"chain_id":chain.chain_id,"depth":chain.depth,
      "rarity_score":chain.rarity_score,
      "difficulty_score":chain.difficulty_score if difficulty is None else difficulty,
      "provenance":chain_payload(chain),
      "answer_provenance_required":True,
    }
