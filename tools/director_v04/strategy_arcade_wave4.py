"""Strategy Arcade Wave 4 -- formats 78-92.

Fifteen more distinct play/state contracts over the certified mixed NFL/CFB
question source. This wave focuses on football decision structure: red-zone
progression, play sequencing, hot-hand switching, overtime possessions,
first-down conversion, blitz risk, zone control, play calling, alternating
possession, sudden death, bank-or-multiply scoring, audibles, fourth-down
choices, best-of-series sweeps, and a race to 100 points.
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
"RED_ZONE_LADDER":{"title":"Red Zone Ladder","goal":"Climb from the 20 to the end zone before three misses.","interaction":"Each correct answer advances five yards; every miss costs a life."},
"DRIVE_BUILDER":{"title":"Drive Builder","goal":"Assemble a touchdown drive by completing short, medium, and deep plays in order.","interaction":"Choose your next play depth; correct adds its yardage, but you must use all three play types before scoring."},
"HOT_HAND_SWITCH":{"title":"Hot Hand Switch","goal":"Build the best score by deciding whether to stay with or switch categories after each answer.","interaction":"Correct answers grow a category multiplier; switching resets the multiplier but changes the category."},
"OVERTIME_SHOOTOUT":{"title":"Overtime Shootout","goal":"Beat the opponent across alternating overtime possessions.","interaction":"Each possession is one question; correct scores seven, then the opponent gets a deterministic answer result."},
"FIRST_DOWN_CHAIN":{"title":"First Down Chain","goal":"Earn four first downs before turning it over.","interaction":"You have four downs to earn two correct answers; convert to reset downs, fail and the game ends."},
"BLITZ_PACKAGE":{"title":"Blitz Package","goal":"Record five sacks before giving up three touchdowns.","interaction":"Choose light, standard, or all-out blitz. Higher risk earns more sack credit on a correct answer but punishes misses harder."},
"ZONE_CONTROL":{"title":"Zone Control","goal":"Fill all nine field zones with control points.","interaction":"Choose any zone; each correct answer adds one control point there, and every zone needs one point."},
"PLAY_CALLER":{"title":"Play Caller","goal":"Score as many points as possible across eight called plays.","interaction":"Call run, pass, or play-action before the question; each call has a different scoring reward and miss penalty."},
"POSSESSION_ARROW":{"title":"Possession Arrow","goal":"Reach 21 while possession alternates after every miss.","interaction":"Correct answers score for whoever owns possession; misses flip possession without scoring."},
"SUDDEN_DEATH":{"title":"Sudden Death","goal":"Survive until the opponent misses after you answer correctly.","interaction":"Your answer is followed by an opponent result; if you miss you lose, if you score and the opponent misses you win."},
"SCORE_BANK":{"title":"Score Bank","goal":"Bank as many points as possible before three misses.","interaction":"Correct answers grow an unbanked pot. Between questions, bank it safely or risk it for a larger multiplier."},
"AUDIBLE":{"title":"Audible","goal":"Use two audibles wisely across eight questions.","interaction":"Before answering, you may keep the current category or spend an audible to swap to a different real category."},
"FOURTH_DOWN_DECISION":{"title":"Fourth Down Decision","goal":"Maximize points across four drives by choosing whether to go for it on fourth down.","interaction":"After three questions, choose to bank a field goal or risk the drive on one fourth-down question for a touchdown."},
"SERIES_SWEEP":{"title":"Series Sweep","goal":"Win a best-of-five series, with bonus credit for a sweep.","interaction":"Each game is one question; first to three wins the series, 3-0 earns a sweep bonus."},
"ROAD_TO_100":{"title":"Road to 100","goal":"Reach 100 points before 12 questions expire.","interaction":"Choose a 10-, 20-, or 30-point shot before each question; correct adds it, miss subtracts half its value."},
}
VARIANTS=frozenset(FORMAT_SPECS)

def build_package(seed:str,variant:str,round_count:int=36)->dict:
    if variant not in VARIANTS: raise ValueError(f"unknown Wave 4 variant {variant!r}")
    rounds=core.build_fast_round_pool(f"{seed}-strategy-wave4-{variant}", round_count)
    pid="GGP40:"+hashlib.sha256(f"{MECHANIC}|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()).hexdigest()[:24]
    return {"package_id":pid,"package_version":PACKAGE_SCHEMA_VERSION,"mechanic":MECHANIC,
            "domain_variant":variant,"format_id":variant,"game_title":FORMAT_SPECS[variant]["title"],
            "game_instructions":FORMAT_SPECS[variant]["interaction"],"generated_at":datetime.now(timezone.utc).isoformat(),
            "qa_status":"PASSED" if len(rounds)>=round_count else "FAILED","rounds":rounds,"round_count":len(rounds),
            "production_safety":{"launch_pool":"verified_direct_sql"},
            "shortfall_reason":None if len(rounds)>=round_count else f"Only {len(rounds)} real mixed questions available; Wave 4 requested {round_count}.",
            "review_status":"UNREVIEWED","_diagnostics":{"seed":seed,"launch_pool":"verified_direct_sql"}}

def _s(progress):
    s=core._base_state(progress); s.setdefault("score",0); return s

def _common(package,s):
    spec=FORMAT_SPECS[package["domain_variant"]]
    return {"format_id":package["domain_variant"],"title":spec["title"],"goal_text":spec["goal"],
            "interaction_text":spec["interaction"],"score":s.get("score",0),
            "correct_total":s.get("correct_total",0),"wrong_total":s.get("wrong_total",0),
            "completed":bool(s.get("completed")),"ended":bool(s.get("ended"))}

def _q(package,s,index=None):
    idx=s["cursor"] if index is None else index
    r=core._round(package,idx)
    return {"phase":"QUESTION","round_index":idx,"round_count":len(package["rounds"]),
            "category":r["category"],"prompt":r["prompt"],"options":core._options(r)}

def _grade_at(package,idx,submission):
    return core._grade(package,{"cursor":idx},submission)

def _adv(s,correct,n=1):
    s["cursor"]+=n
    if correct:s["correct_total"]+=1
    else:s["wrong_total"]+=1

def _find(package,start,category):
    for off in range(len(package["rounds"])):
        idx=(start+off)%len(package["rounds"])
        if package["rounds"][idx].get("bucket")==category:return idx
    raise ValueError("category unavailable")

def client_view(package,progress):
    s=_s(progress); v=package["domain_variant"]; out=_common(package,s)
    if s.get("completed") or s.get("ended"):
        out.update({"phase":"COMPLETE","result_label":s.get("result_label","Complete")}); return out

    if v=="RED_ZONE_LADDER":
        out.update(_q(package,s)); out["status_items"]=[{"label":"YARD LINE","value":max(0,20-s.get("yards",0))},{"label":"MISSES","value":f"{s.get('misses',0)}/3"}]; return out
    if v=="DRIVE_BUILDER":
        if s.get("play_call") is None:
            used=set(s.get("used_play_types",[])); acts=[{"id":x,"label":x.title()} for x in ("short","medium","deep") if x not in used]
            out.update({"phase":"SELECT","actions":acts})
        else: out.update(_q(package,s)); out["selected_label"]=s["play_call"].title()
        out["status_items"]=[{"label":"YARDS","value":s.get("yards",0)},{"label":"USED","value":", ".join(s.get("used_play_types",[])) or "None"}]; return out
    if v=="HOT_HAND_SWITCH":
        current=s.get("current_category",_CATEGORIES[0]); out["status_items"]=[{"label":"CATEGORY","value":current},{"label":"MULTIPLIER","value":f"x{s.get('multiplier',1)}"},{"label":"SCORE","value":s.get("score",0)}]
        if s.get("category_locked"):
            out.update(_q(package,s,index=s["question_index"]))
        else:
            out.update({"phase":"SELECT","actions":[{"id":c,"label":("Stay: " if c==current else "Switch: ")+c} for c in _CATEGORIES]})
        return out
    if v=="OVERTIME_SHOOTOUT":
        out.update(_q(package,s)); out["status_items"]=[{"label":"YOU","value":s.get("player_score",0)},{"label":"THEM","value":s.get("opponent_score",0)},{"label":"OT","value":s.get("possession",0)+1}]; return out
    if v=="FIRST_DOWN_CHAIN":
        out.update(_q(package,s)); out["status_items"]=[{"label":"FIRST DOWNS","value":f"{s.get('first_downs',0)}/4"},{"label":"DOWN","value":s.get("down",1)},{"label":"CORRECT THIS SET","value":f"{s.get('set_correct',0)}/2"}]; return out
    if v=="BLITZ_PACKAGE":
        if s.get("blitz") is None: out.update({"phase":"SELECT","actions":[{"id":"light","label":"Light Blitz"},{"id":"standard","label":"Standard Blitz"},{"id":"allout","label":"All-Out Blitz"}]})
        else: out.update(_q(package,s)); out["selected_label"]=s["blitz"].upper()
        out["status_items"]=[{"label":"SACKS","value":s.get("sacks",0)},{"label":"TDS ALLOWED","value":s.get("tds_allowed",0)}]; return out
    if v=="ZONE_CONTROL":
        zones=dict(s.get("zones",{})); out["board"]=[{"id":str(i),"label":f"ZONE {i+1}","value":"CONTROLLED" if zones.get(str(i)) else "OPEN"} for i in range(9)]
        if s.get("zone") is None: out.update({"phase":"SELECT","actions":[{"id":str(i),"label":f"Zone {i+1}"} for i in range(9) if not zones.get(str(i))]})
        else: out.update(_q(package,s)); out["selected_label"]=f"Zone {int(s['zone'])+1}"
        return out
    if v=="PLAY_CALLER":
        if s.get("play_call") is None: out.update({"phase":"SELECT","actions":[{"id":"run","label":"Run"},{"id":"pass","label":"Pass"},{"id":"play_action","label":"Play Action"}]})
        else: out.update(_q(package,s)); out["selected_label"]=s["play_call"].replace("_"," ").title()
        out["status_items"]=[{"label":"SCORE","value":s.get("score",0)},{"label":"PLAYS","value":f"{s.get('plays',0)}/8"}]; return out
    if v=="POSSESSION_ARROW":
        out.update(_q(package,s)); out["selected_label"]="YOUR BALL" if s.get("possession","YOU")=="YOU" else "THEIR BALL"; out["status_items"]=[{"label":"YOU","value":s.get("player_score",0)},{"label":"THEM","value":s.get("opponent_score",0)}]; return out
    if v=="SUDDEN_DEATH":
        out.update(_q(package,s)); out["status_items"]=[{"label":"ROUND","value":s.get("round_no",1)},{"label":"STATE","value":"Sudden Death"}]; return out
    if v=="SCORE_BANK":
        out["status_items"]=[{"label":"BANK","value":s.get("bank",0)},{"label":"POT","value":s.get("pot",0)},{"label":"MISSES","value":f"{s.get('misses',0)}/3"}]
        if s.get("decision_pending",True): out.update({"phase":"SELECT","actions":[{"id":"risk","label":"Risk It"},{"id":"bank","label":"Bank Pot"}]})
        else: out.update(_q(package,s))
        return out
    if v=="AUDIBLE":
        current=core._round(package,s["cursor"]).get("bucket") or _CATEGORIES[0]; out["status_items"]=[{"label":"AUDIBLES","value":s.get("audibles",2)},{"label":"CURRENT","value":current}]
        if s.get("question_index") is None:
            acts=[{"id":"keep","label":"Keep Call"}]
            if s.get("audibles",2)>0: acts += [{"id":c,"label":"Audible to "+c} for c in _CATEGORIES if c!=current]
            out.update({"phase":"SELECT","actions":acts})
        else: out.update(_q(package,s,index=s["question_index"]))
        return out
    if v=="FOURTH_DOWN_DECISION":
        if s.get("decision_pending"):
            out.update({"phase":"SELECT","actions":[{"id":"field_goal","label":"Take 3"},{"id":"go","label":"Go For 7"}]})
        else: out.update(_q(package,s)); out["selected_label"]="FOURTH DOWN" if s.get("fourth_down") else f"Drive {s.get('drive',0)+1}"
        out["status_items"]=[{"label":"SCORE","value":s.get("score",0)},{"label":"DRIVE","value":f"{s.get('drive',0)+1}/4"},{"label":"PLAYS","value":s.get("drive_plays",0)}]; return out
    if v=="SERIES_SWEEP":
        out.update(_q(package,s)); out["status_items"]=[{"label":"YOU","value":s.get("wins",0)},{"label":"THEM","value":s.get("losses",0)},{"label":"SERIES","value":"Best of 5"}]; return out
    if v=="ROAD_TO_100":
        if s.get("shot") is None: out.update({"phase":"SELECT","actions":[{"id":str(n),"label":f"{n}-Point Shot"} for n in (10,20,30)]})
        else: out.update(_q(package,s)); out["selected_label"]=f"{s['shot']}-POINT SHOT"
        out["status_items"]=[{"label":"SCORE","value":s.get("score",0)},{"label":"TARGET","value":100},{"label":"ATTEMPTS","value":f"{s.get('attempts',0)}/12"}]; return out
    raise ValueError(f"unknown Wave 4 variant {v!r}")

def evaluate(package,progress,submission):
    s=_s(progress); v=package["domain_variant"]; action=str(submission.get("action","")).strip()
    if s.get("completed") or s.get("ended"): raise ValueError("round ended")

    if v=="RED_ZONE_LADDER":
        r=core._grade(package,s,submission)
        if r["correct"]: s["yards"]=s.get("yards",0)+5
        else: s["misses"]=s.get("misses",0)+1
        _adv(s,r["correct"])
        if s.get("yards",0)>=20: s["completed"]=True; s["result_label"]="Touchdown"
        elif s.get("misses",0)>=3: s["completed"]=True; s["result_label"]="Red-zone trip ended"
        return r,s
    if v=="DRIVE_BUILDER":
        if s.get("play_call") is None:
            if action not in ("short","medium","deep") or action in set(s.get("used_play_types",[])): raise ValueError("play type unavailable")
            s["play_call"]=action; return {"action":"select"},s
        call=s.pop("play_call"); r=core._grade(package,s,submission); used=list(s.get("used_play_types",[])); used.append(call); s["used_play_types"]=used
        if r["correct"]: s["yards"]=s.get("yards",0)+{"short":5,"medium":12,"deep":25}[call]
        _adv(s,r["correct"])
        if len(used)>=3: s["completed"]=True; s["result_label"]="Touchdown drive built" if s.get("yards",0)>=30 else f"{s.get('yards',0)}-yard drive"
        return r,s
    if v=="HOT_HAND_SWITCH":
        if not s.get("category_locked"):
            current=s.get("current_category",_CATEGORIES[0])
            if action not in _CATEGORIES: raise ValueError("invalid category")
            if action!=current: s["multiplier"]=1
            s["current_category"]=action; s["question_index"]=_find(package,s["cursor"],action); s["category_locked"]=True
            return {"action":"select"},s
        idx=s.pop("question_index"); s["category_locked"]=False; r=_grade_at(package,idx,submission)
        if r["correct"]: s["score"]=s.get("score",0)+100*s.get("multiplier",1); s["multiplier"]=min(5,s.get("multiplier",1)+1)
        else: s["multiplier"]=1
        _adv(s,r["correct"])
        if s["cursor"]>=8: s["completed"]=True; s["result_label"]=f"{s['score']} points"
        return r,s
    if v=="OVERTIME_SHOOTOUT":
        r=core._grade(package,s,submission); pos=s.get("possession",0)
        if r["correct"]: s["player_score"]=s.get("player_score",0)+7
        opp_correct=(pos%3)!=1
        if opp_correct: s["opponent_score"]=s.get("opponent_score",0)+7
        s["possession"]=pos+1; _adv(s,r["correct"])
        if s["possession"]>=2 and s["possession"]%2==0 and s.get("player_score",0)!=s.get("opponent_score",0):
            s["completed"]=True; s["result_label"]="OT win" if s.get("player_score",0)>s.get("opponent_score",0) else "OT loss"
        elif s["possession"]>=6:
            s["completed"]=True; s["result_label"]="OT shootout complete"
        return r,s
    if v=="FIRST_DOWN_CHAIN":
        r=core._grade(package,s,submission); s["down"]=s.get("down",1)+1
        if r["correct"]: s["set_correct"]=s.get("set_correct",0)+1
        _adv(s,r["correct"])
        if s.get("set_correct",0)>=2:
            s["first_downs"]=s.get("first_downs",0)+1; s["down"]=1; s["set_correct"]=0
        elif s["down"]>4:
            s["completed"]=True; s["result_label"]="Turnover on downs"
        if s.get("first_downs",0)>=4: s["completed"]=True; s["result_label"]="Four first downs"
        return r,s
    if v=="BLITZ_PACKAGE":
        if s.get("blitz") is None:
            if action not in ("light","standard","allout"): raise ValueError("invalid blitz")
            s["blitz"]=action; return {"action":"select"},s
        call=s.pop("blitz"); r=core._grade(package,s,submission); sack={"light":1,"standard":2,"allout":3}[call]; punish={"light":0,"standard":1,"allout":2}[call]
        if r["correct"]: s["sacks"]=s.get("sacks",0)+sack
        else: s["tds_allowed"]=s.get("tds_allowed",0)+max(1,punish)
        _adv(s,r["correct"])
        if s.get("sacks",0)>=5: s["completed"]=True; s["result_label"]="Pressure package won"
        elif s.get("tds_allowed",0)>=3: s["completed"]=True; s["result_label"]="Blitz burned"
        return r,s
    if v=="ZONE_CONTROL":
        zones=dict(s.get("zones",{}))
        if s.get("zone") is None:
            if action not in {str(i) for i in range(9)} or zones.get(action): raise ValueError("zone unavailable")
            s["zone"]=action; return {"action":"select"},s
        zone=s.pop("zone"); r=core._grade(package,s,submission)
        if r["correct"]: zones[zone]=1
        s["zones"]=zones; _adv(s,r["correct"])
        if len(zones)>=9: s["completed"]=True; s["result_label"]="All zones controlled"
        elif s["cursor"]>=15: s["completed"]=True; s["result_label"]=f"{len(zones)} of 9 zones"
        return r,s
    if v=="PLAY_CALLER":
        if s.get("play_call") is None:
            if action not in ("run","pass","play_action"): raise ValueError("invalid play call")
            s["play_call"]=action; return {"action":"select"},s
        call=s.pop("play_call"); r=core._grade(package,s,submission); reward={"run":1,"pass":2,"play_action":3}[call]; penalty={"run":0,"pass":1,"play_action":2}[call]
        s["score"]=max(0,s.get("score",0)+(reward if r["correct"] else -penalty)); s["plays"]=s.get("plays",0)+1; _adv(s,r["correct"])
        if s["plays"]>=8: s["completed"]=True; s["result_label"]=f"{s['score']} points"
        return r,s
    if v=="POSSESSION_ARROW":
        r=core._grade(package,s,submission); poss=s.get("possession","YOU")
        if r["correct"]:
            if poss=="YOU": s["player_score"]=s.get("player_score",0)+7
            else: s["opponent_score"]=s.get("opponent_score",0)+7
        else: s["possession"]="THEM" if poss=="YOU" else "YOU"
        _adv(s,r["correct"])
        if s.get("player_score",0)>=21 or s.get("opponent_score",0)>=21:
            s["completed"]=True; s["result_label"]="You win" if s.get("player_score",0)>=21 else "Opponent wins"
        elif s["cursor"]>=12: s["completed"]=True; s["result_label"]="Possession game ended"
        return r,s
    if v=="SUDDEN_DEATH":
        r=core._grade(package,s,submission)
        if not r["correct"]:
            s["completed"]=True; s["result_label"]="Sudden-death loss"; _adv(s,False); return r,s
        opp_correct=(s.get("round_no",1)%2)==0
        s["round_no"]=s.get("round_no",1)+1; _adv(s,True)
        if not opp_correct: s["completed"]=True; s["result_label"]="Sudden-death win"
        elif s["round_no"]>8: s["completed"]=True; s["result_label"]="Sudden-death draw"
        return r,s
    if v=="SCORE_BANK":
        s.setdefault("bank",0); s.setdefault("pot",0); s.setdefault("misses",0)
        if s.get("decision_pending",True):
            if action=="bank":
                s["bank"]+=s["pot"]; s["pot"]=0; return {"action":"select","decision":"bank"},s
            if action=="risk":
                s["decision_pending"]=False; return {"action":"select","decision":"risk"},s
            raise ValueError("invalid bank decision")
        r=core._grade(package,s,submission)
        if r["correct"]: s["pot"]=max(100,s["pot"]*2 if s["pot"] else 100)
        else: s["pot"]=0; s["misses"]+=1
        s["decision_pending"]=True; _adv(s,r["correct"])
        if s["misses"]>=3 or s["cursor"]>=10:
            s["bank"]+=s["pot"]; s["pot"]=0; s["completed"]=True; s["score"]=s["bank"]; s["result_label"]=f"{s['bank']} banked"
        return r,s
    if v=="AUDIBLE":
        s.setdefault("audibles",2)
        if s.get("question_index") is None:
            current=core._round(package,s["cursor"]).get("bucket") or _CATEGORIES[0]
            if action=="keep": idx=s["cursor"]
            elif action in _CATEGORIES and action!=current and s["audibles"]>0:
                s["audibles"]-=1; idx=_find(package,s["cursor"],action)
            else: raise ValueError("invalid audible")
            s["question_index"]=idx; return {"action":"select"},s
        idx=s.pop("question_index"); r=_grade_at(package,idx,submission); _adv(s,r["correct"])
        if s["cursor"]>=8: s["completed"]=True; s["result_label"]=f"{s['correct_total']} of 8 correct"
        return r,s
    if v=="FOURTH_DOWN_DECISION":
        s.setdefault("drive",0); s.setdefault("drive_plays",0)
        if s.get("decision_pending"):
            if action=="field_goal":
                s["score"]=s.get("score",0)+3; s["drive"]+=1; s["drive_plays"]=0; s["decision_pending"]=False
                if s["drive"]>=4: s["completed"]=True; s["result_label"]=f"{s['score']} points"
                return {"action":"select","decision":"field_goal"},s
            if action=="go": s["decision_pending"]=False; s["fourth_down"]=True; return {"action":"select","decision":"go"},s
            raise ValueError("invalid fourth-down decision")
        r=core._grade(package,s,submission); s["drive_plays"]+=1
        if s.get("fourth_down"):
            if r["correct"]: s["score"]=s.get("score",0)+7
            s["drive"]+=1; s["drive_plays"]=0; s["fourth_down"]=False
        elif s["drive_plays"]>=3: s["decision_pending"]=True
        _adv(s,r["correct"])
        if s["drive"]>=4: s["completed"]=True; s["result_label"]=f"{s['score']} points"
        return r,s
    if v=="SERIES_SWEEP":
        r=core._grade(package,s,submission)
        if r["correct"]: s["wins"]=s.get("wins",0)+1
        else: s["losses"]=s.get("losses",0)+1
        _adv(s,r["correct"])
        if s.get("wins",0)>=3 or s.get("losses",0)>=3:
            sweep=s.get("wins",0)==3 and s.get("losses",0)==0
            s["score"]=4 if sweep else s.get("wins",0); s["completed"]=True; s["result_label"]="Series sweep" if sweep else ("Series won" if s.get("wins",0)>=3 else "Series lost")
        return r,s
    if v=="ROAD_TO_100":
        if s.get("shot") is None:
            n=int(action)
            if n not in (10,20,30): raise ValueError("invalid shot")
            s["shot"]=n; return {"action":"select"},s
        n=s.pop("shot"); r=core._grade(package,s,submission); s["attempts"]=s.get("attempts",0)+1
        s["score"]=max(0,s.get("score",0)+(n if r["correct"] else -(n//2))); _adv(s,r["correct"])
        if s["score"]>=100: s["completed"]=True; s["result_label"]="100 reached"
        elif s["attempts"]>=12: s["completed"]=True; s["result_label"]=f"{s['score']} points"
        return r,s
    raise ValueError(f"unknown Wave 4 variant {v!r}")
