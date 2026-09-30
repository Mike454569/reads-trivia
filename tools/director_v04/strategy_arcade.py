"""Strategy Arcade -- 100-format expansion, formats 48-62.

Fifteen genuinely different state machines over Reads' already-certified real
mixed trivia pool. The shared question source is deliberate: a FORMAT is the
player interaction/state contract, not a second copy of the knowledge layer.

Every answer remains server-authoritative. Private answer ids/notes stay in the
immutable package; client_view() exposes only the current playable state.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from tools.director_v04 import category_roulette

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "STRATEGY_ARCADE"

FORMAT_SPECS = {
    "BINGO_BLITZ": {
        "title": "Bingo Blitz", "goal": "Claim a three-cell line on the 3x3 board.",
        "interaction": "Choose any open board cell, then answer its real question. Correct claims it; wrong burns it.",
    },
    "TERRITORY_TAKEOVER": {
        "title": "Territory Takeover", "goal": "Own more territory points than the opponent after six zones.",
        "interaction": "Choose an open 1-3 point zone. Correct claims it; wrong gives that zone to the opponent.",
    },
    "EXACT_TEN": {
        "title": "Exact Ten", "goal": "Reach exactly 10 points without going over.",
        "interaction": "Choose a 1, 2, or 3 point play before seeing the question. Correct adds it; going over 10 busts.",
    },
    "PYRAMID_CLIMB": {
        "title": "Pyramid Climb", "goal": "Reach level five before the question supply runs out.",
        "interaction": "Choose one of three lanes each level. Correct climbs one level; wrong drops one.",
    },
    "LOCKBOX": {
        "title": "Lockbox", "goal": "Open three locks, then solve the vault question.",
        "interaction": "Choose which lock to attack in any order. Three correct locks unlock a final boss question.",
    },
    "COMBO_METER": {
        "title": "Combo Meter", "goal": "Build the biggest scoring combo across eight real questions.",
        "interaction": "Every correct answer increases the multiplier; a miss resets the multiplier to x1.",
    },
    "CHECKPOINT_RALLY": {
        "title": "Checkpoint Rally", "goal": "Reach progress eight before 12 questions expire.",
        "interaction": "Correct answers advance. Every second step saves a checkpoint; a miss drops you back to it.",
    },
    "ESCALATOR": {
        "title": "Escalator", "goal": "Reach step 10 before falling back to zero.",
        "interaction": "Choose to risk one or two steps before the question. Correct climbs that many; wrong falls that many.",
    },
    "POWER_UP": {
        "title": "Power Up", "goal": "Score as much as possible while managing earned energy.",
        "interaction": "Correct answers earn energy. Spend two energy before a question for a server-safe 50/50.",
    },
    "CATEGORY_CONQUEST": {
        "title": "Category Conquest", "goal": "Capture all three real trivia categories.",
        "interaction": "Choose which uncaptured category to attack. A correct answer captures it; a miss leaves it open.",
    },
    "SCOREBOARD_SWING": {
        "title": "Scoreboard Swing", "goal": "Reach 21 before the opponent.",
        "interaction": "Correct answers score seven for you; misses give the opponent three. First to 21 wins.",
    },
    "MOMENTUM_BAR": {
        "title": "Momentum Bar", "goal": "Push momentum to +8 before it falls to -4.",
        "interaction": "Correct answers push +2, misses -1, and a three-answer streak adds a bonus momentum point.",
    },
    "TIMEOUT_TOKENS": {
        "title": "Timeout Tokens", "goal": "Maximize score using two skips and one double-score token.",
        "interaction": "Before each question choose normal play, spend a skip, or spend your one double-score token.",
    },
    "PERFECT_SET": {
        "title": "Perfect Set", "goal": "Win two of three three-question sets.",
        "interaction": "Each set is best-of-three questions. Win at least two questions to take the set.",
    },
    "TRIPLE_OR_TAKE": {
        "title": "Triple or Take", "goal": "Bank points across three self-selected series.",
        "interaction": "Choose a 1, 2, or 3-question series. Clear every question to bank 1, 3, or 6 points; one miss loses the series.",
    },
}
VARIANTS = frozenset(FORMAT_SPECS)

_BINGO_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)
_TERRITORY_VALUES = (1, 2, 3, 2, 3, 1)


def build_package(seed: str, variant: str, round_count: int = 24) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    source = category_roulette.build_package(
        f"{seed}-strategy-{variant}", "CATEGORY_ROULETTE_MIXED", round_count=max(24, round_count)
    )
    rounds = source.get("rounds") or []
    package_id = "GGP38:" + hashlib.sha256(
        f"{MECHANIC}|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id,
        "package_version": PACKAGE_SCHEMA_VERSION,
        "mechanic": MECHANIC,
        "domain_variant": variant,
        "format_id": variant,
        "game_title": FORMAT_SPECS[variant]["title"],
        "game_instructions": FORMAT_SPECS[variant]["interaction"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(rounds) >= 12 else "FAILED",
        "rounds": rounds,
        "round_count": len(rounds),
        "production_safety": source.get("production_safety"),
        "shortfall_reason": None if len(rounds) >= 12 else (
            f"Only {len(rounds)} real mixed-trivia questions were available; Strategy Arcade requires at least 12."
        ),
        "review_status": "UNREVIEWED",
        "_diagnostics": {"seed": seed, "source_package_id": source.get("package_id")},
    }


def _base_state(progress: dict) -> dict:
    state = dict(progress)
    state.setdefault("cursor", 0)
    state.setdefault("score", 0)
    state.setdefault("completed", False)
    state.setdefault("ended", False)
    state.setdefault("phase", "SELECT")
    state.setdefault("correct_total", 0)
    state.setdefault("wrong_total", 0)
    return state


def _round(package: dict, index: int) -> dict:
    rounds = package["rounds"]
    if not rounds:
        raise ValueError("strategy package has no real rounds")
    return rounds[index % len(rounds)]


def _options(r: dict, *, fifty_fifty: bool = False) -> list[dict]:
    opts = [{"item_id": it["item_id"], "label": it["label"]} for it in r["options"]]
    if not fifty_fifty:
        return opts
    correct = r["_answer_item_id"]
    decoy = next(it for it in opts if it["item_id"] != correct)
    return [it for it in opts if it["item_id"] == correct or it["item_id"] == decoy]


def _question_view(package: dict, state: dict, *, fifty_fifty: bool = False) -> dict:
    r = _round(package, state["cursor"])
    return {
        "phase": "QUESTION",
        "round_index": state["cursor"],
        "round_count": len(package["rounds"]),
        "category": r["category"],
        "prompt": r["prompt"],
        "options": _options(r, fifty_fifty=fifty_fifty),
    }


def _grade(package: dict, state: dict, submission: dict) -> dict:
    r = _round(package, state["cursor"])
    choice = str(submission.get("choice_item_id", "")).strip().upper()
    canonical = r["_answer_item_id"]
    correct = bool(choice) and choice == canonical
    canonical_label = next(it["label"] for it in r["options"] if it["item_id"] == canonical)
    return {"correct": correct, "canonical_answer": canonical_label, "notes": r["_notes"]}


def _advance_question(state: dict, correct: bool) -> None:
    state["cursor"] += 1
    if correct:
        state["correct_total"] += 1
    else:
        state["wrong_total"] += 1


def _common_view(package: dict, state: dict) -> dict:
    variant = package["domain_variant"]
    spec = FORMAT_SPECS[variant]
    return {
        "format_id": variant,
        "title": spec["title"],
        "goal_text": spec["goal"],
        "interaction_text": spec["interaction"],
        "score": state.get("score", 0),
        "correct_total": state.get("correct_total", 0),
        "wrong_total": state.get("wrong_total", 0),
        "completed": bool(state.get("completed")),
        "ended": bool(state.get("ended")),
    }


def client_view(package: dict, progress: dict) -> dict:
    state = _base_state(progress)
    variant = package["domain_variant"]
    out = _common_view(package, state)
    if state["completed"] or state["ended"]:
        out.update({"phase": "COMPLETE", "result_label": state.get("result_label", "Complete")})
        return out

    if variant == "BINGO_BLITZ":
        claimed = set(state.get("claimed", [])); missed = set(state.get("missed", []))
        out["board"] = [{"id": str(i), "label": f"CELL {i+1}", "value": "CLAIMED" if i in claimed else ("BURNT" if i in missed else "OPEN")}
                        for i in range(9)]
        if state.get("pending_cell") is None:
            out.update({"phase": "SELECT", "actions": [{"id": str(i), "label": f"Play Cell {i+1}"} for i in range(9) if i not in claimed | missed]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = f"Cell {state['pending_cell']+1}"
        return out

    if variant == "TERRITORY_TAKEOVER":
        owners = state.get("owners", {})
        out["board"] = [{"id": str(i), "label": f"ZONE {i+1}", "value": owners.get(str(i), f"{_TERRITORY_VALUES[i]} PTS")}
                        for i in range(6)]
        out["status_items"] = [{"label": "YOU", "value": state.get("player_points", 0)}, {"label": "THEM", "value": state.get("opponent_points", 0)}]
        if state.get("pending_zone") is None:
            out.update({"phase": "SELECT", "actions": [{"id": str(i), "label": f"Zone {i+1} · {_TERRITORY_VALUES[i]} pts"} for i in range(6) if str(i) not in owners]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = f"Zone {state['pending_zone']+1}"
        return out

    if variant == "EXACT_TEN":
        out["status_items"] = [{"label": "TOTAL", "value": state.get("total", 0)}, {"label": "TARGET", "value": 10}]
        if state.get("stake") is None:
            out.update({"phase": "SELECT", "actions": [{"id": str(n), "label": f"Risk {n} point{'s' if n>1 else ''}"} for n in (1,2,3)]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = f"{state['stake']} point play"
        return out

    if variant == "PYRAMID_CLIMB":
        level = state.get("level", 0)
        out["status_items"] = [{"label": "LEVEL", "value": level}, {"label": "TOP", "value": 5}]
        if state.get("lane") is None:
            out.update({"phase": "SELECT", "actions": [{"id": lane, "label": f"{lane.title()} Lane"} for lane in ("left","middle","right")]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = f"{state['lane'].title()} lane"
        return out

    if variant == "LOCKBOX":
        opened = set(state.get("opened_locks", [])); attempted = set(state.get("attempted_locks", []))
        vault = len(opened) >= 3
        out["board"] = [{"id": str(i), "label": f"LOCK {i+1}", "value": "OPEN" if i in opened else ("MISSED" if i in attempted else "LOCKED")} for i in range(4)]
        if state.get("pending_lock") is None and not state.get("vault_question"):
            if vault:
                out.update({"phase": "SELECT", "actions": [{"id": "vault", "label": "Open the Vault"}]})
            else:
                out.update({"phase": "SELECT", "actions": [{"id": str(i), "label": f"Attack Lock {i+1}"} for i in range(4) if i not in attempted]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = "VAULT" if state.get("vault_question") else f"Lock {state['pending_lock']+1}"
        return out

    if variant == "COMBO_METER":
        out.update(_question_view(package, state))
        out["status_items"] = [{"label": "COMBO", "value": f"x{state.get('multiplier',1)}"}, {"label": "SCORE", "value": state.get("score",0)}]
        return out

    if variant == "CHECKPOINT_RALLY":
        out.update(_question_view(package, state))
        out["status_items"] = [{"label": "PROGRESS", "value": state.get("distance",0)}, {"label": "CHECKPOINT", "value": state.get("checkpoint",0)}, {"label": "GOAL", "value": 8}]
        return out

    if variant == "ESCALATOR":
        out["status_items"] = [{"label": "STEP", "value": state.get("step",0)}, {"label": "TOP", "value": 10}]
        if state.get("step_risk") is None:
            out.update({"phase": "SELECT", "actions": [{"id": "1", "label": "Take 1 Step"}, {"id": "2", "label": "Risk 2 Steps"}]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = f"{state['step_risk']} step play"
        return out

    if variant == "POWER_UP":
        energy = state.get("energy",0)
        out["status_items"] = [{"label": "ENERGY", "value": energy}, {"label": "SCORE", "value": state.get("score",0)}]
        if state.get("question_ready") is not True:
            actions = [{"id":"normal","label":"Play Normal"}]
            if energy >= 2: actions.append({"id":"fifty","label":"Spend 2 Energy · 50/50"})
            out.update({"phase":"SELECT","actions":actions})
        else:
            out.update(_question_view(package, state, fifty_fifty=bool(state.get("fifty_fifty"))))
        return out

    if variant == "CATEGORY_CONQUEST":
        captured = set(state.get("captured", []))
        out["board"] = [{"id": c, "label": c, "value": "CAPTURED" if c in captured else "OPEN"} for c in ("NFL Team Records","Heisman Winners","Super Bowl Champions")]
        if state.get("target_category") is None:
            out.update({"phase":"SELECT","actions":[{"id":c,"label":f"Attack {c}"} for c in ("NFL Team Records","Heisman Winners","Super Bowl Champions") if c not in captured]})
        else:
            out.update(_question_view(package, state)); out["selected_label"] = state["target_category"]
        return out

    if variant == "SCOREBOARD_SWING":
        out.update(_question_view(package, state))
        out["status_items"] = [{"label":"YOU","value":state.get("player_score",0)},{"label":"THEM","value":state.get("opponent_score",0)},{"label":"TARGET","value":21}]
        return out

    if variant == "MOMENTUM_BAR":
        out.update(_question_view(package, state))
        out["status_items"] = [{"label":"MOMENTUM","value":state.get("momentum",0)},{"label":"STREAK","value":state.get("streak",0)},{"label":"WIN","value":"+8"}]
        return out

    if variant == "TIMEOUT_TOKENS":
        out["status_items"] = [{"label":"SKIPS","value":state.get("skips",2)},{"label":"DOUBLE","value":"READY" if state.get("double",1) else "USED"},{"label":"SCORE","value":state.get("score",0)}]
        if state.get("play_type") is None:
            actions=[{"id":"normal","label":"Run the Play"}]
            if state.get("skips",2)>0: actions.append({"id":"skip","label":"Use Timeout · Skip"})
            if state.get("double",1)>0: actions.append({"id":"double","label":"Use Double Score"})
            out.update({"phase":"SELECT","actions":actions})
        else:
            out.update(_question_view(package,state)); out["selected_label"]=state["play_type"].replace("_"," ").title()
        return out

    if variant == "PERFECT_SET":
        out.update(_question_view(package,state))
        out["status_items"]=[{"label":"SETS","value":state.get("sets_won",0)},{"label":"SET W-L","value":f"{state.get('set_correct',0)}-{state.get('set_wrong',0)}"},{"label":"TARGET","value":"2 sets"}]
        return out

    if variant == "TRIPLE_OR_TAKE":
        out["status_items"]=[{"label":"BANK","value":state.get("score",0)},{"label":"SERIES","value":state.get("series_done",0)+1},{"label":"TARGET","value":"3 series"}]
        if state.get("series_size") is None:
            out.update({"phase":"SELECT","actions":[{"id":"1","label":"Take 1 · 1 pt"},{"id":"2","label":"Take 2 · 3 pts"},{"id":"3","label":"Take 3 · 6 pts"}]})
        else:
            out.update(_question_view(package,state)); out["selected_label"]=f"{state.get('series_hits',0)+1} of {state['series_size']}"
        return out

    raise ValueError(f"unknown strategy variant {variant!r}")


def _finish_if_out(state: dict, package: dict) -> None:
    if state["cursor"] >= len(package["rounds"]):
        state["completed"] = True
        state.setdefault("result_label", "Question pool complete")


def evaluate(package: dict, progress: dict, submission: dict) -> tuple[dict, dict]:
    state = _base_state(progress)
    variant = package["domain_variant"]
    if state["completed"] or state["ended"]:
        raise ValueError("this strategy round has already ended")
    action = str(submission.get("action", "")).strip()
    result: dict = {"action": action or "answer"}

    if variant == "BINGO_BLITZ":
        if state.get("pending_cell") is None:
            cell=int(action)
            unavailable=set(state.get("claimed",[]))|set(state.get("missed",[]))
            if cell<0 or cell>8 or cell in unavailable: raise ValueError("cell is not open")
            state["pending_cell"]=cell; state["phase"]="QUESTION"
            return {"action":"select","selected":cell},state
        result.update(_grade(package,state,submission)); cell=state.pop("pending_cell")
        key="claimed" if result["correct"] else "missed"; vals=list(state.get(key,[])); vals.append(cell); state[key]=vals
        _advance_question(state,result["correct"]); claimed=set(state.get("claimed",[]))
        if any(set(line)<=claimed for line in _BINGO_LINES):
            state["completed"]=True; state["result_label"]="BINGO!"
        elif len(claimed|set(state.get("missed",[])))>=9:
            state["completed"]=True; state["result_label"]="Board exhausted"
        return result,state

    if variant == "TERRITORY_TAKEOVER":
        owners=dict(state.get("owners",{}))
        if state.get("pending_zone") is None:
            z=int(action)
            if z<0 or z>=6 or str(z) in owners: raise ValueError("zone is not open")
            state["pending_zone"]=z; return {"action":"select","selected":z},state
        result.update(_grade(package,state,submission)); z=state.pop("pending_zone"); value=_TERRITORY_VALUES[z]
        if result["correct"]:
            owners[str(z)]="YOU"; state["player_points"]=state.get("player_points",0)+value
        else:
            owners[str(z)]="THEM"; state["opponent_points"]=state.get("opponent_points",0)+value
        state["owners"]=owners; _advance_question(state,result["correct"])
        if len(owners)>=6:
            state["completed"]=True; p=state.get("player_points",0); o=state.get("opponent_points",0)
            state["result_label"]="Territory won" if p>o else ("Draw" if p==o else "Opponent won")
        return result,state

    if variant == "EXACT_TEN":
        if state.get("stake") is None:
            stake=int(action)
            if stake not in (1,2,3): raise ValueError("stake must be 1, 2, or 3")
            state["stake"]=stake; return {"action":"select","stake":stake},state
        result.update(_grade(package,state,submission)); stake=state.pop("stake")
        if result["correct"]: state["total"]=state.get("total",0)+stake
        else: state["total"]=max(0,state.get("total",0)-1)
        state["score"]=state["total"]; _advance_question(state,result["correct"])
        if state["total"]==10: state["completed"]=True; state["result_label"]="Exact 10!"
        elif state["total"]>10: state["completed"]=True; state["result_label"]="Bust"
        _finish_if_out(state,package); return result,state

    if variant == "PYRAMID_CLIMB":
        if state.get("lane") is None:
            if action not in ("left","middle","right"): raise ValueError("invalid lane")
            state["lane"]=action; return {"action":"select","lane":action},state
        result.update(_grade(package,state,submission)); state.pop("lane",None)
        level=state.get("level",0)+(1 if result["correct"] else -1); state["level"]=max(0,level)
        _advance_question(state,result["correct"])
        if state["level"]>=5: state["completed"]=True; state["result_label"]="Pyramid conquered"
        _finish_if_out(state,package); return result,state

    if variant == "LOCKBOX":
        opened=set(state.get("opened_locks",[])); attempted=set(state.get("attempted_locks",[]))
        if state.get("pending_lock") is None and not state.get("vault_question"):
            if action=="vault":
                if len(opened)<3: raise ValueError("vault is still locked")
                state["vault_question"]=True; return {"action":"vault"},state
            lock=int(action)
            if lock<0 or lock>3 or lock in attempted: raise ValueError("lock unavailable")
            state["pending_lock"]=lock; return {"action":"select","lock":lock},state
        result.update(_grade(package,state,submission))
        if state.get("vault_question"):
            state["vault_question"]=False; _advance_question(state,result["correct"]); state["completed"]=True
            state["result_label"]="Vault cracked" if result["correct"] else "Vault held"
            return result,state
        lock=state.pop("pending_lock"); attempted.add(lock)
        if result["correct"]: opened.add(lock)
        state["opened_locks"]=sorted(opened); state["attempted_locks"]=sorted(attempted); _advance_question(state,result["correct"])
        if len(attempted)>=4 and len(opened)<3: state["completed"]=True; state["result_label"]="Not enough locks opened"
        return result,state

    if variant == "COMBO_METER":
        result.update(_grade(package,state,submission)); mult=state.get("multiplier",1)
        if result["correct"]:
            state["score"]=state.get("score",0)+100*mult; state["multiplier"]=min(5,mult+1)
        else: state["multiplier"]=1
        _advance_question(state,result["correct"])
        if state["cursor"]>=8: state["completed"]=True; state["result_label"]=f"{state['score']} points"
        return result,state

    if variant == "CHECKPOINT_RALLY":
        result.update(_grade(package,state,submission)); distance=state.get("distance",0); checkpoint=state.get("checkpoint",0)
        if result["correct"]:
            distance+=1
            if distance%2==0: checkpoint=distance
        else: distance=checkpoint
        state["distance"]=distance; state["checkpoint"]=checkpoint; _advance_question(state,result["correct"])
        if distance>=8: state["completed"]=True; state["result_label"]="Finish line reached"
        elif state["cursor"]>=12: state["completed"]=True; state["result_label"]="Rally ended"
        return result,state

    if variant == "ESCALATOR":
        if state.get("step_risk") is None:
            n=int(action)
            if n not in (1,2): raise ValueError("step risk must be 1 or 2")
            state["step_risk"]=n; return {"action":"select","steps":n},state
        result.update(_grade(package,state,submission)); n=state.pop("step_risk"); step=state.get("step",0)
        step=step+n if result["correct"] else max(0,step-n); state["step"]=step; _advance_question(state,result["correct"])
        if step>=10: state["completed"]=True; state["result_label"]="Top floor reached"
        _finish_if_out(state,package); return result,state

    if variant == "POWER_UP":
        if state.get("question_ready") is not True:
            if action=="fifty":
                if state.get("energy",0)<2: raise ValueError("not enough energy")
                state["energy"]-=2; state["fifty_fifty"]=True
            elif action=="normal": state["fifty_fifty"]=False
            else: raise ValueError("invalid power-up action")
            state["question_ready"]=True; return {"action":"select","power":action},state
        result.update(_grade(package,state,submission))
        if result["correct"]: state["energy"]=state.get("energy",0)+1; state["score"]=state.get("score",0)+100
        state["question_ready"]=False; state["fifty_fifty"]=False; _advance_question(state,result["correct"])
        if state["cursor"]>=8: state["completed"]=True; state["result_label"]=f"{state['score']} points"
        return result,state

    if variant == "CATEGORY_CONQUEST":
        categories=("NFL Team Records","Heisman Winners","Super Bowl Champions")
        if state.get("target_category") is None:
            if action not in categories or action in set(state.get("captured",[])): raise ValueError("category unavailable")
            start=state["cursor"]; rounds=package["rounds"]; found=None
            for off in range(len(rounds)):
                idx=(start+off)%len(rounds)
                if rounds[idx]["category"]==action: found=idx; break
            if found is None: raise ValueError("no real question for category")
            state["cursor"]=found; state["target_category"]=action; return {"action":"select","category":action},state
        result.update(_grade(package,state,submission)); target=state.pop("target_category")
        if result["correct"]:
            cap=set(state.get("captured",[])); cap.add(target); state["captured"]=sorted(cap)
        _advance_question(state,result["correct"])
        if len(state.get("captured",[]))>=3: state["completed"]=True; state["result_label"]="All categories conquered"
        return result,state

    if variant == "SCOREBOARD_SWING":
        result.update(_grade(package,state,submission))
        if result["correct"]: state["player_score"]=state.get("player_score",0)+7
        else: state["opponent_score"]=state.get("opponent_score",0)+3
        _advance_question(state,result["correct"])
        if state.get("player_score",0)>=21 or state.get("opponent_score",0)>=21:
            state["completed"]=True; state["result_label"]="You win" if state.get("player_score",0)>=21 else "Opponent wins"
        _finish_if_out(state,package); return result,state

    if variant == "MOMENTUM_BAR":
        result.update(_grade(package,state,submission)); streak=state.get("streak",0)
        if result["correct"]:
            streak+=1; state["momentum"]=state.get("momentum",0)+2+(1 if streak%3==0 else 0)
        else:
            streak=0; state["momentum"]=state.get("momentum",0)-1
        state["streak"]=streak; _advance_question(state,result["correct"])
        if state.get("momentum",0)>=8: state["completed"]=True; state["result_label"]="Momentum maxed"
        elif state.get("momentum",0)<=-4: state["completed"]=True; state["result_label"]="Momentum lost"
        _finish_if_out(state,package); return result,state

    if variant == "TIMEOUT_TOKENS":
        if state.get("skips") is None: state["skips"]=2
        if state.get("double") is None: state["double"]=1
        if state.get("play_type") is None:
            if action=="skip":
                if state["skips"]<=0: raise ValueError("no skips left")
                state["skips"]-=1; state["cursor"]+=1
                if state["cursor"]>=8: state["completed"]=True; state["result_label"]=f"{state.get('score',0)} points"
                return {"action":"skip"},state
            if action=="double":
                if state["double"]<=0: raise ValueError("double already used")
                state["double"]=0; state["play_type"]="double"
            elif action=="normal": state["play_type"]="normal"
            else: raise ValueError("invalid token action")
            return {"action":"select","play_type":state["play_type"]},state
        result.update(_grade(package,state,submission)); play=state.pop("play_type")
        if result["correct"]: state["score"]=state.get("score",0)+(200 if play=="double" else 100)
        _advance_question(state,result["correct"])
        if state["cursor"]>=8: state["completed"]=True; state["result_label"]=f"{state.get('score',0)} points"
        return result,state

    if variant == "PERFECT_SET":
        result.update(_grade(package,state,submission))
        if result["correct"]: state["set_correct"]=state.get("set_correct",0)+1
        else: state["set_wrong"]=state.get("set_wrong",0)+1
        _advance_question(state,result["correct"])
        played=state.get("set_correct",0)+state.get("set_wrong",0)
        if state.get("set_correct",0)>=2 or state.get("set_wrong",0)>=2 or played>=3:
            if state.get("set_correct",0)>state.get("set_wrong",0): state["sets_won"]=state.get("sets_won",0)+1
            else: state["sets_lost"]=state.get("sets_lost",0)+1
            state["set_correct"]=0; state["set_wrong"]=0
        if state.get("sets_won",0)>=2 or state.get("sets_lost",0)>=2:
            state["completed"]=True; state["result_label"]="Set match won" if state.get("sets_won",0)>=2 else "Set match lost"
        _finish_if_out(state,package); return result,state

    if variant == "TRIPLE_OR_TAKE":
        if state.get("series_size") is None:
            n=int(action)
            if n not in (1,2,3): raise ValueError("series size must be 1, 2, or 3")
            state["series_size"]=n; state["series_hits"]=0; state["series_failed"]=False
            return {"action":"select","series_size":n},state
        result.update(_grade(package,state,submission)); n=state["series_size"]
        if result["correct"]: state["series_hits"]=state.get("series_hits",0)+1
        else: state["series_failed"]=True
        _advance_question(state,result["correct"])
        if state.get("series_failed") or state.get("series_hits",0)>=n:
            if not state.get("series_failed"):
                state["score"]=state.get("score",0)+{1:1,2:3,3:6}[n]
            state["series_done"]=state.get("series_done",0)+1
            state["series_size"]=None; state["series_hits"]=0; state["series_failed"]=False
            if state["series_done"]>=3:
                state["completed"]=True; state["result_label"]=f"{state.get('score',0)} points banked"
        _finish_if_out(state,package); return result,state

    raise ValueError(f"unknown strategy variant {variant!r}")
