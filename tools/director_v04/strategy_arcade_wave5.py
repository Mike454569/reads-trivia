"""Strategy Arcade Wave 5 -- final formats 93-100.

Eight final distinct interaction/state contracts to reach an honest 100:
choice elimination, route tree, accumulating yardage with turnovers,
category lockout, last-play rescue, rolling target, draft-order gauntlet,
and a final four-stage championship run.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from tools.director_v04 import category_roulette
from tools.director_v04 import strategy_arcade as core

PACKAGE_SCHEMA_VERSION="2.0"
MECHANIC="STRATEGY_ARCADE"
_CATEGORIES=("Game Day","Season & Legacy","College Chaos")

FORMAT_SPECS={
"OPTION_ERASER":{"title":"Option Eraser","goal":"Clear six questions while managing three eraser tokens.","interaction":"Before a question, play normal or spend one eraser to remove one server-selected wrong option."},
"ROUTE_TREE":{"title":"Route Tree","goal":"Complete a three-branch route tree by winning one question on each route.","interaction":"Choose slant, post, or go route in any order; each route carries a different point value."},
"TURNOVER_BATTLE":{"title":"Turnover Battle","goal":"Reach 50 yards before three turnovers.","interaction":"Correct answers gain 10 yards; misses are turnovers that reset the current drive's yardage."},
"CATEGORY_LOCKOUT":{"title":"Category Lockout","goal":"Score in all three categories before any category is locked by two misses.","interaction":"Choose a category to attack; two misses in that category lock it permanently."},
"HAIL_MARY":{"title":"Hail Mary","goal":"Survive five regulation questions, then use one final rescue question if needed.","interaction":"Score four of five to win outright; at exactly three correct, unlock a final Hail Mary question."},
"MOVING_TARGET":{"title":"Moving Target","goal":"Hit a target score that changes after every answer.","interaction":"Choose a 1-3 point shot; after each answer the target moves deterministically between 7 and 12."},
"DRAFT_ORDER":{"title":"Draft Order","goal":"Climb from pick 10 to pick one before five misses.","interaction":"Choose safe, medium, or aggressive trade-up attempts worth one, two, or three draft slots."},
"CHAMPIONSHIP_RUN":{"title":"Championship Run","goal":"Win Wild Card, Divisional, Conference, and Championship stages.","interaction":"Each stage needs a different number of correct answers before its miss limit is reached."},
}
VARIANTS=frozenset(FORMAT_SPECS)

def build_package(seed:str,variant:str,round_count:int=36)->dict:
    if variant not in VARIANTS: raise ValueError(f"unknown Wave 5 variant {variant!r}")
    src=category_roulette.build_package(f"{seed}-strategy-wave5-{variant}","CATEGORY_ROULETTE_MIXED",round_count=max(18, round_count), launch_fast=True)
    rounds=src.get("rounds") or []
    pid="GGP41:"+hashlib.sha256(f"{MECHANIC}|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()).hexdigest()[:24]
    return {"package_id":pid,"package_version":PACKAGE_SCHEMA_VERSION,"mechanic":MECHANIC,
      "domain_variant":variant,"format_id":variant,"game_title":FORMAT_SPECS[variant]["title"],
      "game_instructions":FORMAT_SPECS[variant]["interaction"],"generated_at":datetime.now(timezone.utc).isoformat(),
      "qa_status":"PASSED" if len(rounds)>=18 else "FAILED","rounds":rounds,"round_count":len(rounds),
      "production_safety":src.get("production_safety"),
      "shortfall_reason":None if len(rounds)>=18 else f"Only {len(rounds)} real mixed questions available; Wave 5 needs 18.",
      "review_status":"UNREVIEWED","_diagnostics":{"seed":seed,"source_package_id":src.get("package_id")}}

def _s(progress):
    s=core._base_state(progress); s.setdefault("score",0); return s
def _common(package,s):
    spec=FORMAT_SPECS[package["domain_variant"]]
    return {"format_id":package["domain_variant"],"title":spec["title"],"goal_text":spec["goal"],
      "interaction_text":spec["interaction"],"score":s.get("score",0),"correct_total":s.get("correct_total",0),
      "wrong_total":s.get("wrong_total",0),"completed":bool(s.get("completed")),"ended":bool(s.get("ended"))}
def _q(package,s,remove_one=False):
    r=core._round(package,s["cursor"]); opts=core._options(r)
    if remove_one:
        correct=r["_answer_item_id"]; decoy=next(o["item_id"] for o in opts if o["item_id"]!=correct)
        opts=[o for o in opts if o["item_id"]!=decoy]
    return {"phase":"QUESTION","round_index":s["cursor"],"round_count":len(package["rounds"]),
      "category":r["category"],"prompt":r["prompt"],"options":opts}
def _adv(s,correct):
    s["cursor"]+=1
    if correct:s["correct_total"]+=1
    else:s["wrong_total"]+=1

def client_view(package,progress):
    s=_s(progress); v=package["domain_variant"]; out=_common(package,s)
    if s.get("completed") or s.get("ended"):
        out.update({"phase":"COMPLETE","result_label":s.get("result_label","Complete")}); return out
    if v=="OPTION_ERASER":
        out["status_items"]=[{"label":"ERASERS","value":s.get("erasers",3)},{"label":"CLEARED","value":s.get("cleared",0)}]
        if s.get("question_ready"): out.update(_q(package,s,remove_one=bool(s.get("erased"))))
        else:
            acts=[{"id":"normal","label":"Play Normal"}]
            if s.get("erasers",3)>0: acts.append({"id":"erase","label":"Spend Eraser"})
            out.update({"phase":"SELECT","actions":acts})
        return out
    if v=="ROUTE_TREE":
        done=set(s.get("routes_done",[])); out["status_items"]=[{"label":"POINTS","value":s.get("score",0)},{"label":"ROUTES","value":f"{len(done)}/3"}]
        if s.get("route") is None: out.update({"phase":"SELECT","actions":[{"id":r,"label":r.title()} for r in ("slant","post","go") if r not in done]})
        else: out.update(_q(package,s)); out["selected_label"]=s["route"].upper()
        return out
    if v=="TURNOVER_BATTLE":
        out.update(_q(package,s)); out["status_items"]=[{"label":"TOTAL YARDS","value":s.get("total_yards",0)},{"label":"DRIVE YARDS","value":s.get("drive_yards",0)},{"label":"TURNOVERS","value":f"{s.get('turnovers',0)}/3"}]; return out
    if v=="CATEGORY_LOCKOUT":
        locks=set(s.get("locked",[])); misses=dict(s.get("category_misses",{})); scored=set(s.get("scored_categories",[]))
        out["status_items"]=[{"label":c.upper(),"value":"LOCKED" if c in locks else ("SCORED" if c in scored else f"{misses.get(c,0)}/2 MISSES")} for c in _CATEGORIES]
        if s.get("category") is None: out.update({"phase":"SELECT","actions":[{"id":c,"label":c} for c in _CATEGORIES if c not in locks]})
        else:
            idx=next(i for i,r in enumerate(package["rounds"]) if r.get("bucket")==s["category"])
            tmp=dict(s); tmp["cursor"]=idx; out.update(_q(package,tmp)); out["selected_label"]=s["category"]
        return out
    if v=="HAIL_MARY":
        out.update(_q(package,s)); out["status_items"]=[{"label":"CORRECT","value":s.get("correct_total",0)},{"label":"REGULATION","value":f"{min(s.get('cursor',0),5)}/5"}]
        if s.get("hail_mary"): out["selected_label"]="HAIL MARY"
        return out
    if v=="MOVING_TARGET":
        out["status_items"]=[{"label":"SCORE","value":s.get("score",0)},{"label":"TARGET","value":s.get("target",9)}]
        if s.get("shot") is None: out.update({"phase":"SELECT","actions":[{"id":str(n),"label":f"{n}-Point Shot"} for n in (1,2,3)]})
        else: out.update(_q(package,s)); out["selected_label"]=f"{s['shot']}-POINT SHOT"
        return out
    if v=="DRAFT_ORDER":
        out["status_items"]=[{"label":"PICK","value":s.get("pick",10)},{"label":"MISSES","value":f"{s.get('misses',0)}/5"}]
        if s.get("trade") is None: out.update({"phase":"SELECT","actions":[{"id":"safe","label":"Safe · +1"},{"id":"medium","label":"Medium · +2"},{"id":"aggressive","label":"Aggressive · +3"}]})
        else: out.update(_q(package,s)); out["selected_label"]=s["trade"].upper()
        return out
    if v=="CHAMPIONSHIP_RUN":
        stages=("Wild Card","Divisional","Conference","Championship"); stage=s.get("stage",0)
        out.update(_q(package,s)); out["selected_label"]=stages[stage]
        out["status_items"]=[{"label":"STAGE","value":f"{stage+1}/4"},{"label":"WINS","value":s.get("stage_correct",0)},{"label":"MISSES","value":s.get("stage_wrong",0)}]; return out
    raise ValueError(f"unknown Wave 5 variant {v!r}")

def evaluate(package,progress,submission):
    s=_s(progress); v=package["domain_variant"]; action=str(submission.get("action","")).strip()
    if s.get("completed") or s.get("ended"): raise ValueError("round ended")

    if v=="OPTION_ERASER":
        s.setdefault("erasers",3)
        if not s.get("question_ready"):
            if action=="erase":
                if s["erasers"]<=0: raise ValueError("no erasers left")
                s["erasers"]-=1; s["erased"]=True
            elif action=="normal": s["erased"]=False
            else: raise ValueError("invalid eraser action")
            s["question_ready"]=True; return {"action":"select"},s
        r=core._grade(package,s,submission)
        if r["correct"]: s["cleared"]=s.get("cleared",0)+1
        s["question_ready"]=False; s["erased"]=False; _adv(s,r["correct"])
        if s.get("cleared",0)>=6: s["completed"]=True; s["result_label"]="Six cleared"
        elif s["cursor"]>=9: s["completed"]=True; s["result_label"]=f"{s.get('cleared',0)} cleared"
        return r,s
    if v=="ROUTE_TREE":
        done=set(s.get("routes_done",[]))
        if s.get("route") is None:
            if action not in ("slant","post","go") or action in done: raise ValueError("route unavailable")
            s["route"]=action; return {"action":"select"},s
        route=s.pop("route"); r=core._grade(package,s,submission)
        done.add(route); s["routes_done"]=sorted(done)
        if r["correct"]: s["score"]=s.get("score",0)+{"slant":1,"post":2,"go":3}[route]
        _adv(s,r["correct"])
        if len(done)>=3: s["completed"]=True; s["result_label"]=f"{s['score']} route points"
        return r,s
    if v=="TURNOVER_BATTLE":
        r=core._grade(package,s,submission)
        if r["correct"]:
            s["drive_yards"]=s.get("drive_yards",0)+10; s["total_yards"]=s.get("total_yards",0)+10
        else:
            s["turnovers"]=s.get("turnovers",0)+1; s["drive_yards"]=0
        _adv(s,r["correct"])
        if s.get("total_yards",0)>=50: s["completed"]=True; s["result_label"]="50 yards reached"
        elif s.get("turnovers",0)>=3: s["completed"]=True; s["result_label"]="Turnover battle lost"
        return r,s
    if v=="CATEGORY_LOCKOUT":
        locks=set(s.get("locked",[])); misses=dict(s.get("category_misses",{})); scored=set(s.get("scored_categories",[]))
        if s.get("category") is None:
            if action not in _CATEGORIES or action in locks: raise ValueError("category unavailable")
            s["category"]=action; return {"action":"select"},s
        cat=s.pop("category")
        idx=next(i for i,r in enumerate(package["rounds"]) if r.get("bucket")==cat)
        r=core._grade(package,{"cursor":idx},submission)
        if r["correct"]: scored.add(cat)
        else:
            misses[cat]=misses.get(cat,0)+1
            if misses[cat]>=2: locks.add(cat)
        s["category_misses"]=misses; s["scored_categories"]=sorted(scored); s["locked"]=sorted(locks); _adv(s,r["correct"])
        if len(scored)>=3: s["completed"]=True; s["result_label"]="All categories scored"
        elif len(locks)>=1 and len(scored|locks)>=3: s["completed"]=True; s["result_label"]="Category locked out"
        return r,s
    if v=="HAIL_MARY":
        r=core._grade(package,s,submission); _adv(s,r["correct"])
        if s.get("hail_mary"):
            s["completed"]=True; s["result_label"]="Hail Mary complete" if r["correct"] else "Hail Mary incomplete"; return r,s
        if s["cursor"]>=5:
            if s.get("correct_total",0)>=4: s["completed"]=True; s["result_label"]="Regulation win"
            elif s.get("correct_total",0)==3: s["hail_mary"]=True
            else: s["completed"]=True; s["result_label"]="Regulation loss"
        return r,s
    if v=="MOVING_TARGET":
        s.setdefault("target",9)
        if s.get("shot") is None:
            n=int(action)
            if n not in (1,2,3): raise ValueError("invalid shot")
            s["shot"]=n; return {"action":"select"},s
        n=s.pop("shot"); r=core._grade(package,s,submission)
        if r["correct"]: s["score"]=s.get("score",0)+n
        else: s["score"]=max(0,s.get("score",0)-1)
        _adv(s,r["correct"]); s["target"]=7+((s["cursor"]*4+1)%6)
        if s["score"]==s["target"]: s["completed"]=True; s["result_label"]="Target hit exactly"
        elif s["cursor"]>=10: s["completed"]=True; s["result_label"]=f"Finished on {s['score']} vs {s['target']}"
        return r,s
    if v=="DRAFT_ORDER":
        s.setdefault("pick",10); s.setdefault("misses",0)
        if s.get("trade") is None:
            if action not in ("safe","medium","aggressive"): raise ValueError("invalid trade")
            s["trade"]=action; return {"action":"select"},s
        trade=s.pop("trade"); r=core._grade(package,s,submission); move={"safe":1,"medium":2,"aggressive":3}[trade]
        if r["correct"]: s["pick"]=max(1,s["pick"]-move)
        else: s["misses"]+=1
        _adv(s,r["correct"])
        if s["pick"]<=1: s["completed"]=True; s["result_label"]="No. 1 pick reached"
        elif s["misses"]>=5: s["completed"]=True; s["result_label"]=f"Finished at pick {s['pick']}"
        return r,s
    if v=="CHAMPIONSHIP_RUN":
        req=(1,2,2,3); miss_limit=(2,2,2,2); stage=s.get("stage",0)
        r=core._grade(package,s,submission)
        if r["correct"]: s["stage_correct"]=s.get("stage_correct",0)+1
        else: s["stage_wrong"]=s.get("stage_wrong",0)+1
        _adv(s,r["correct"])
        if s["stage_correct"]>=req[stage]:
            s["stage"]=stage+1; s["stage_correct"]=0; s["stage_wrong"]=0
            if s["stage"]>=4: s["completed"]=True; s["result_label"]="Champion"
        elif s["stage_wrong"]>=miss_limit[stage]:
            s["completed"]=True; s["result_label"]=f"Eliminated in stage {stage+1}"
        return r,s
    raise ValueError(f"unknown Wave 5 variant {v!r}")
