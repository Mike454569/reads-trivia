"""Assemble v0.5 knowledge into finished, mechanic-ready questions."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass

RELATION_TEXT={
 "DRAFTED_BY":lambda c:f"I was drafted by {c['object_label']}" + (f" in {c['season']}" if c.get("season") else ""),
 "ROSTERED_BY":lambda c:f"I was on {c['object_label']}'s roster" + (f" in {c['season']}" if c.get("season") else ""),
 "ALL_PRO":lambda c:f"I earned {c['object_label']} All-Pro honors" + (f" in {c['season']}" if c.get("season") else ""),
 "PRO_BOWL":lambda c:f"I was selected to the Pro Bowl" + (f" in {c['season']}" if c.get("season") else ""),
 "HOF":lambda c:f"I was inducted into the Hall of Fame" + (f" in {c['season']}" if c.get("season") else ""),
 "GAME_APPEARANCE":lambda c:f"One of my notable games was {c['object_label']}" + (f" in {c['season']}" if c.get("season") else ""),
 "TRANSFER":lambda c:f"My college path included {c['object_label']}" + (f" in {c['season']}" if c.get("season") else ""),
 "RANKED":lambda c:f"My team held the No. {c['object_label']} ranking" + (f" in {c['season']}" if c.get("season") else ""),
 "COACHED_BY":lambda c:f"I played for coach {c['object_label']}" + (f" in {c['season']}" if c.get("season") else ""),
 "CHAMPIONSHIP":lambda c:f"I was part of {c['object_label']}" + (f" in {c['season']}" if c.get("season") else ""),
}

def _render_clue(clue,labels):
    relation=clue["relation"]
    object_id=str(clue["object_id"])
    object_label=labels.get(object_id,object_id)
    payload={**clue,"object_label":object_label}
    fn=RELATION_TEXT.get(relation)
    if not fn:return f"{relation.replace('_',' ').title()}: {object_label}"
    return fn(payload)+"."

def _question_id(chain_id,mechanic,answer_id,clues):
    seed="|".join([chain_id,mechanic,str(answer_id)]+clues)
    return "qv5_"+hashlib.sha256(seed.encode()).hexdigest()[:24]

def assemble(compiled,*,answer_label,labels=None,as_of_season=None,retrospective=True):
    labels=labels or {}
    raw_clues=compiled.get("clues") or []
    if not raw_clues: raise ValueError("NO_CLUES")
    if not retrospective and as_of_season is not None:
        future=[c for c in raw_clues if c.get("season") is not None and int(c["season"])>int(as_of_season)]
        if future: raise ValueError("TEMPORAL_LEAKAGE")
    clues=[_render_clue(c,labels) for c in raw_clues]
    mechanic=compiled["mechanic"]
    if mechanic in {"WHO_AM_I","THREE_CLUES","DAILY","ENDLESS","SURVIVAL","ELIMINATION"}:
        question="Who am I?"
    elif mechanic=="COMMON_LINK":
        question="What football figure connects these clues?"
    else:
        question="Which answer best matches these verified football clues?"
    options=[answer_label]+[d["label"] for d in compiled.get("distractors",[])]
    explanation=" ".join(clues)
    qid=_question_id(compiled["chain_id"],mechanic,compiled["answer"]["id"],clues)
    return {
      "contract_version":"1.0.0","question_id":qid,"mechanic":mechanic,
      "question":question,"clues":clues,
      "answer":{"id":compiled["answer"]["id"],"label":answer_label,"type":compiled["answer"]["type"]},
      "options":options,"explanation":explanation,
      "difficulty_score":compiled["difficulty_score"],
      "difficulty_band":(compiled.get("clue_plan") or {}).get("difficulty_band"),
      "chain_id":compiled["chain_id"],"provenance":compiled["provenance"],
    }
