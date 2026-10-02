"""Context-aware distractor intelligence for Reads Engine v0.5."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Candidate:
    entity_id:str
    label:str
    era:int|None=None
    position:str|None=None
    team_or_school:str|None=None
    tier:str|None=None
    numeric_value:float|None=None
    verified:bool=True

@dataclass(frozen=True)
class ScoredDistractor:
    entity_id:str
    label:str
    score:float
    reasons:tuple[str,...]

def _era_score(a,b):
    if a is None or b is None:return 0.0
    d=abs(int(a)-int(b))
    return max(0.0,22.0-min(d,20)*1.1)

def _numeric_score(a,b):
    if a is None or b is None:return 0.0
    scale=max(abs(float(a)),abs(float(b)),1.0)
    rel=abs(float(a)-float(b))/scale
    return max(0.0,24.0-rel*24.0)

def score_candidate(correct,candidate,*,forbidden_ids=(),forbidden_labels=()):
    if not candidate.verified:return None
    if candidate.entity_id==correct.entity_id:return None
    if candidate.entity_id in {str(x) for x in forbidden_ids}:return None
    if candidate.label.casefold()==correct.label.casefold():return None
    if candidate.label.casefold() in {str(x).casefold() for x in forbidden_labels}:return None
    score=10.0; reasons=[]
    if correct.position and candidate.position and correct.position==candidate.position:
        score+=24;reasons.append("same_position")
    if correct.team_or_school and candidate.team_or_school and correct.team_or_school==candidate.team_or_school:
        score+=18;reasons.append("same_team_or_school")
    if correct.tier and candidate.tier and correct.tier==candidate.tier:
        score+=16;reasons.append("same_tier")
    e=_era_score(correct.era,candidate.era)
    if e: score+=e;reasons.append("similar_era")
    n=_numeric_score(correct.numeric_value,candidate.numeric_value)
    if n: score+=n;reasons.append("similar_value")
    return ScoredDistractor(candidate.entity_id,candidate.label,round(score,3),tuple(reasons))

def select_distractors(correct,candidates,*,k=3,forbidden_ids=(),forbidden_labels=(),recent_ids=()):
    """Deterministic plausibility ranking; never invents or pads candidates."""
    recent={str(x) for x in recent_ids}
    scored=[]
    for c in candidates:
        s=score_candidate(correct,c,forbidden_ids=forbidden_ids,forbidden_labels=forbidden_labels)
        if s is None:continue
        penalty=14.0 if c.entity_id in recent else 0.0
        scored.append(ScoredDistractor(s.entity_id,s.label,round(s.score-penalty,3),
                                       s.reasons+(("recent_penalty",) if penalty else ())))
    # Stable tie-breaking keeps generation reproducible without RNG luck.
    scored.sort(key=lambda x:(-x.score,x.label.casefold(),x.entity_id))
    out=[];seen=set()
    for s in scored:
        key=s.label.casefold()
        if key in seen:continue
        seen.add(key);out.append(s)
        if len(out)>=k:break
    return [asdict(x) for x in out]

def validate_distractors(correct,selected,*,all_correct_ids=()):
    if len(selected)!=len({x["entity_id"] for x in selected}):return "DUPLICATE_DISTRACTOR_ID"
    if len(selected)!=len({x["label"].casefold() for x in selected}):return "DUPLICATE_DISTRACTOR_LABEL"
    bad={str(x) for x in all_correct_ids}
    if any(x["entity_id"]==correct.entity_id or x["entity_id"] in bad for x in selected):
        return "ACCIDENTALLY_CORRECT_DISTRACTOR"
    return None
