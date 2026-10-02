"""Compile knowledge concepts independently from game mechanics."""
from __future__ import annotations
from .creator_concepts import CONCEPTS, COMPATIBLE_MECHANICS

ORDERED_METRICS={"bust_score","steal_score","comeback_magnitude","upset_magnitude","career_journey","rarity"}
ORDER_MECHANICS={"HIGHER_LOWER","SORTING","BRACKET","ELIMINATION","LEADERBOARD"}
CLUE_MECHANICS={"MULTIPLE_CHOICE","TRUE_FALSE","WHO_AM_I","THREE_CLUES","COMMON_LINK","SURVIVAL","DAILY","ENDLESS"}

def compile_recipe(concept,mechanic,*,league=None,limit=20):
    concept=concept.upper(); mechanic=mechanic.upper()
    if concept not in CONCEPTS: raise ValueError("unknown concept")
    if mechanic not in COMPATIBLE_MECHANICS: raise ValueError("unsupported mechanic")
    spec=CONCEPTS[concept]
    metric=spec.get("metric")
    source="derived" if metric else "events"
    if mechanic in ORDER_MECHANICS and not metric:
        raise ValueError("ordered mechanic requires a numeric derived metric")
    return {
      "recipe_version":"1.0.0","concept":concept,"mechanic":mechanic,
      "source":source,"metric":metric,"tags":tuple(spec.get("tags",())),
      "league":league,"limit":max(2,min(int(limit),100)),
      "sensitive":bool(spec.get("sensitive")),
      "requires_verified_evidence":bool(spec.get("sensitive")) or source=="events",
      "answer_provenance_required":True,
    }

def supported_pairs():
    out=[]
    for concept,spec in CONCEPTS.items():
        for mechanic in COMPATIBLE_MECHANICS:
            try: out.append(compile_recipe(concept,mechanic))
            except ValueError: pass
    return out
