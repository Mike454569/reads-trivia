"""Strategy Arcade Wave 3 -- 100-format expansion, formats 63-77.

Fifteen additional interaction/state contracts. They deliberately reuse the
same certified mixed NFL/CFB question source as Wave 2 while changing what the
player controls: board gravity, opponent occupation, retry/review state,
post-touchdown conversion decisions, deficit recovery, category drafting,
three-play survival, visible category choice, deferred second chances, zone
coverage, alternating offense/defense, field-goal banking, clock management,
per-category streaks, and four-drive quarter scoring.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from tools.director_v04 import category_roulette
from tools.director_v04 import strategy_arcade as core

PACKAGE_SCHEMA_VERSION = "2.0"
MECHANIC = "STRATEGY_ARCADE"

FORMAT_SPECS = {
    "CONNECT_FOUR": {
        "title": "Connect Four",
        "goal": "Drop four of your discs in a row before the opponent does.",
        "interaction": "Choose a non-full column. Correct drops your disc; a miss drops the opponent's disc into that same column.",
    },
    "TIC_TAC_TOE": {
        "title": "Tic-Tac-Toe",
        "goal": "Claim a three-cell line before the opponent.",
        "interaction": "Choose an open square. Correct claims it for you; a miss gives that square to the opponent.",
    },
    "CHALLENGE_FLAG": {
        "title": "Challenge Flag",
        "goal": "Maximize your score across eight questions with two replay challenges.",
        "interaction": "After a miss, spend a challenge to replay the same question with the chosen wrong answer removed, or accept the ruling.",
    },
    "EXTRA_POINT": {
        "title": "Extra Point",
        "goal": "Turn correct answers into touchdowns, then decide between one safe point or a two-point trivia try.",
        "interaction": "A correct base question scores six and opens a conversion decision: take one point or answer one bonus question for two.",
    },
    "COMEBACK_MODE": {
        "title": "Comeback Mode",
        "goal": "Erase a 21-point deficit in six possessions.",
        "interaction": "Each correct possession scores seven. Misses burn possessions. Finish tied or ahead.",
    },
    "CATEGORY_DRAFT": {
        "title": "Category Draft",
        "goal": "Score across six picks while managing a two-use limit for each category.",
        "interaction": "Draft the category for each question. Every real category can be used only twice.",
    },
    "THREE_AND_OUT": {
        "title": "Three & Out",
        "goal": "Survive four drives by getting at least one correct answer on each three-play drive.",
        "interaction": "Each drive lasts up to three questions. One correct converts the drive; three misses ends the run.",
    },
    "PICK_YOUR_POISON": {
        "title": "Pick Your Poison",
        "goal": "Win six rounds by choosing which of two visible categories you want to answer.",
        "interaction": "Before every question, choose one of two real categories. The engine serves the next real question from that category.",
    },
    "SECOND_CHANCE_QUEUE": {
        "title": "Second Chance Queue",
        "goal": "Finish eight questions with one chance to defer a miss and replay that exact question at the end.",
        "interaction": "Your first miss can be sent to the back of the queue. The replay must be answered correctly to recover the point.",
    },
    "COVERAGE_SHELL": {
        "title": "Coverage Shell",
        "goal": "Record two stops in each of three zones before allowing three completions.",
        "interaction": "Choose a zone to defend, then answer. Correct adds a stop to that zone; a miss adds an opponent completion.",
    },
    "OFFENSE_DEFENSE": {
        "title": "Offense / Defense",
        "goal": "Outscore the opponent across eight alternating snaps.",
        "interaction": "On offense, correct scores seven. On defense, correct forces a stop while a miss gives the opponent seven.",
    },
    "FIELD_GOAL_RANGE": {
        "title": "Field Goal Range",
        "goal": "Build field position, then choose when to attempt one final field-goal trivia question.",
        "interaction": "Correct answers gain 10 yards. Between snaps, keep driving or kick; a made kick scores more the farther you advanced.",
    },
    "TWO_MINUTE_DRILL": {
        "title": "Two-Minute Drill",
        "goal": "Reach 60 yards before 120 seconds of game clock expire.",
        "interaction": "Choose hurry-up or normal tempo before each snap. Hurry-up costs 15 seconds for 8 yards; normal costs 30 for 15 yards when correct.",
    },
    "CATEGORY_STREAK": {
        "title": "Category Streak",
        "goal": "Build a two-answer streak in all three real categories.",
        "interaction": "Choose the category to attack. Correct grows only that category's streak; a miss resets that category to zero.",
    },
    "PERFECT_QUARTER": {
        "title": "Perfect Quarter",
        "goal": "Score on at least three of four drives.",
        "interaction": "Every drive is two questions. Going 2-for-2 scores a touchdown; anything less is a stop.",
    },
}
VARIANTS = frozenset(FORMAT_SPECS)
_CATEGORIES=("Game Day","Season & Legacy","College Chaos")
_TTT_LINES = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))


def build_package(seed: str, variant: str, round_count: int = 30) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")
    # Startup latency matters more than pre-generating a full theoretical
    # Connect Four board. Wave 3's own QA contract requires 18 real questions;
    # every state machine can safely cycle the immutable pool via core._round.
    # Building 42 Deep Ball questions synchronously made live rounds exceed
    # the frontend's 10s timeout on production.
    rounds = core.build_fast_round_pool(
        f"{seed}-strategy-wave3-{variant}", round_count
    )
    package_id = "GGP39:" + hashlib.sha256(
        f"{MECHANIC}|{variant}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION,
        "mechanic": MECHANIC, "domain_variant": variant, "format_id": variant,
        "game_title": FORMAT_SPECS[variant]["title"],
        "game_instructions": FORMAT_SPECS[variant]["interaction"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(rounds) >= round_count else "FAILED",
        "rounds": rounds, "round_count": len(rounds),
        "production_safety": {"launch_pool": "verified_direct_sql"},
        "shortfall_reason": None if len(rounds) >= round_count else
            f"Only {len(rounds)} real mixed-trivia questions were available; Wave 3 requested {round_count}.",
        "review_status": "UNREVIEWED",
        "_diagnostics": {"seed": seed, "launch_pool": "verified_direct_sql"},
    }


def _state(progress: dict) -> dict:
    s = core._base_state(progress)
    s.setdefault("score", 0)
    return s


def _common(package: dict, s: dict) -> dict:
    spec = FORMAT_SPECS[package["domain_variant"]]
    return {
        "format_id": package["domain_variant"], "title": spec["title"],
        "goal_text": spec["goal"], "interaction_text": spec["interaction"],
        "score": s.get("score", 0), "correct_total": s.get("correct_total", 0),
        "wrong_total": s.get("wrong_total", 0),
        "completed": bool(s.get("completed")), "ended": bool(s.get("ended")),
    }


def _find_category_index(package: dict, start: int, category: str, excluded: set[int] | None = None) -> int:
    excluded = excluded or set()
    for off in range(len(package["rounds"])):
        idx = (start + off) % len(package["rounds"])
        if idx not in excluded and package["rounds"][idx].get("bucket")==category:
            return idx
    raise ValueError(f"no real question available for category {category!r}")


def _question(package: dict, s: dict, index: int | None = None, remove_ids: set[str] | None = None) -> dict:
    idx = s["cursor"] if index is None else index
    r = core._round(package, idx)
    options = core._options(r)
    if remove_ids:
        options = [o for o in options if o["item_id"] not in remove_ids]
    return {
        "phase": "QUESTION", "round_index": idx, "round_count": len(package["rounds"]),
        "category": r["category"], "prompt": r["prompt"], "options": options,
    }


def _grade_at(package: dict, idx: int, submission: dict) -> dict:
    temp = {"cursor": idx}
    return core._grade(package, temp, submission)


def _advance(s: dict, correct: bool, amount: int = 1) -> None:
    s["cursor"] += amount
    if correct: s["correct_total"] += 1
    else: s["wrong_total"] += 1


def _line_winner(cells: dict[str, str]) -> str | None:
    for line in _TTT_LINES:
        vals = [cells.get(str(i)) for i in line]
        if vals[0] and vals[0] == vals[1] == vals[2]:
            return vals[0]
    return None


def _connect_winner(board: list[list[str | None]]) -> str | None:
    rows, cols = 6, 7
    for r in range(rows):
        for c in range(cols):
            who = board[r][c]
            if not who: continue
            for dr, dc in ((0,1),(1,0),(1,1),(1,-1)):
                pts = [(r + dr*k, c + dc*k) for k in range(4)]
                if all(0 <= rr < rows and 0 <= cc < cols and board[rr][cc] == who for rr, cc in pts):
                    return who
    return None


def client_view(package: dict, progress: dict) -> dict:
    s = _state(progress); variant = package["domain_variant"]; out = _common(package, s)
    if s.get("completed") or s.get("ended"):
        out.update({"phase":"COMPLETE","result_label":s.get("result_label","Complete")})
        return out

    if variant == "CONNECT_FOUR":
        board = s.get("connect_board") or [[None]*7 for _ in range(6)]
        out["board_columns"] = 7
        out["board"] = [{"id":f"{r}:{c}","label":f"R{r+1} C{c+1}","value":board[r][c] or "OPEN"} for r in range(6) for c in range(7)]
        if s.get("pending_column") is None:
            actions=[{"id":str(c),"label":f"Column {c+1}"} for c in range(7) if board[0][c] is None]
            out.update({"phase":"SELECT","actions":actions})
        else:
            out.update(_question(package,s)); out["selected_label"]=f"Column {s['pending_column']+1}"
        return out

    if variant == "TIC_TAC_TOE":
        cells=dict(s.get("ttt_cells",{}))
        out["board"]=[{"id":str(i),"label":f"SQUARE {i+1}","value":cells.get(str(i),"OPEN")} for i in range(9)]
        if s.get("pending_square") is None:
            out.update({"phase":"SELECT","actions":[{"id":str(i),"label":f"Square {i+1}"} for i in range(9) if str(i) not in cells]})
        else:
            out.update(_question(package,s)); out["selected_label"]=f"Square {s['pending_square']+1}"
        return out

    if variant == "CHALLENGE_FLAG":
        out["status_items"]=[{"label":"CHALLENGES","value":s.get("challenges",2)},{"label":"SCORE","value":s.get("score",0)}]
        if s.get("review_pending"):
            out.update({"phase":"SELECT","actions":[{"id":"challenge","label":"Throw Challenge Flag"},{"id":"accept","label":"Accept Ruling"}]})
        else:
            out.update(_question(package,s, index=s.get("question_index"), remove_ids=set(s.get("removed_option_ids",[]))))
        return out

    if variant == "EXTRA_POINT":
        out["status_items"]=[{"label":"POINTS","value":s.get("score",0)},{"label":"TDS","value":s.get("touchdowns",0)}]
        if s.get("conversion_pending"):
            out.update({"phase":"SELECT","actions":[{"id":"kick","label":"Kick · +1"},{"id":"two","label":"Go for 2"}]})
        elif s.get("two_point_question"):
            out.update(_question(package,s)); out["selected_label"]="2-POINT TRY"
        else:
            out.update(_question(package,s))
        return out

    if variant == "COMEBACK_MODE":
        out.update(_question(package,s))
        out["status_items"]=[{"label":"YOU","value":s.get("score",0)},{"label":"THEM","value":21},{"label":"POSSESSIONS","value":f"{s.get('possessions',0)}/6"}]
        return out

    if variant == "CATEGORY_DRAFT":
        uses=dict(s.get("category_uses",{}))
        out["status_items"]=[{"label":c.upper(),"value":f"{uses.get(c,0)}/2"} for c in _CATEGORIES]
        if s.get("target_category") is None:
            out.update({"phase":"SELECT","actions":[{"id":c,"label":c} for c in _CATEGORIES if uses.get(c,0)<2]})
        else:
            out.update(_question(package,s,index=s["question_index"])); out["selected_label"]=s["target_category"]
        return out

    if variant == "THREE_AND_OUT":
        out.update(_question(package,s))
        out["status_items"]=[{"label":"DRIVE","value":f"{s.get('drives_won',0)+s.get('drives_lost',0)+1}/4"},
                             {"label":"PLAY","value":f"{s.get('drive_plays',0)+1}/3"},
                             {"label":"CONVERTED","value":"YES" if s.get("drive_hit") else "NO"}]
        return out

    if variant == "PICK_YOUR_POISON":
        if s.get("target_category") is None:
            pair = list(s.get("category_pair") or _CATEGORIES[:2])
            out.update({"phase":"SELECT","actions":[{"id":c,"label":c} for c in pair]})
        else:
            out.update(_question(package,s,index=s["question_index"])); out["selected_label"]=s["target_category"]
        out["status_items"]=[{"label":"WINS","value":s.get("score",0)},{"label":"ROUNDS","value":s.get("rounds_played",0)}]
        return out

    if variant == "SECOND_CHANCE_QUEUE":
        replay_idx=s.get("active_replay_index")
        idx=replay_idx if replay_idx is not None else s["cursor"]
        out.update(_question(package,s,index=idx))
        out["status_items"]=[{"label":"SECOND CHANCE","value":"USED" if s.get("deferred_index") is not None else "READY"},
                             {"label":"SCORE","value":s.get("score",0)}]
        if replay_idx is not None: out["selected_label"]="SECOND CHANCE"
        return out

    if variant == "COVERAGE_SHELL":
        stops=dict(s.get("zone_stops",{}))
        out["status_items"]=[{"label":"COMPLETIONS","value":s.get("completions_allowed",0)}]+[
            {"label":z.upper(),"value":f"{stops.get(z,0)}/2"} for z in ("short","middle","deep")]
        if s.get("target_zone") is None:
            out.update({"phase":"SELECT","actions":[{"id":z,"label":f"Defend {z.title()}"} for z in ("short","middle","deep") if stops.get(z,0)<2]})
        else:
            out.update(_question(package,s)); out["selected_label"]=s["target_zone"].title()
        return out

    if variant == "OFFENSE_DEFENSE":
        out.update(_question(package,s))
        role="OFFENSE" if s.get("snap",0)%2==0 else "DEFENSE"
        out["selected_label"]=role
        out["status_items"]=[{"label":"YOU","value":s.get("player_score",0)},{"label":"THEM","value":s.get("opponent_score",0)},{"label":"SNAP","value":f"{s.get('snap',0)+1}/8"}]
        return out

    if variant == "FIELD_GOAL_RANGE":
        yards=s.get("yards",0)
        out["status_items"]=[{"label":"FIELD POS","value":f"{yards} YDS"},{"label":"KICK VALUE","value":1+yards//20}]
        if s.get("kick_question"):
            out.update(_question(package,s)); out["selected_label"]="FIELD GOAL"
        elif s.get("decision_pending",True):
            actions=[{"id":"drive","label":"Run Another Play"}]
            if yards>=20: actions.append({"id":"kick","label":f"Kick Now · {1+yards//20} pts"})
            out.update({"phase":"SELECT","actions":actions})
        else:
            out.update(_question(package,s))
        return out

    if variant == "TWO_MINUTE_DRILL":
        out["status_items"]=[{"label":"CLOCK","value":s.get("clock",120)},{"label":"YARDS","value":s.get("yards",0)},{"label":"TARGET","value":60}]
        if s.get("tempo") is None:
            out.update({"phase":"SELECT","actions":[{"id":"hurry","label":"Hurry-Up · 15 sec / 8 yds"},{"id":"normal","label":"Normal · 30 sec / 15 yds"}]})
        else:
            out.update(_question(package,s)); out["selected_label"]=s["tempo"].replace("_"," ").upper()
        return out

    if variant == "CATEGORY_STREAK":
        streaks=dict(s.get("category_streaks",{}))
        out["status_items"]=[{"label":c.upper(),"value":f"{streaks.get(c,0)}/2"} for c in _CATEGORIES]
        if s.get("target_category") is None:
            out.update({"phase":"SELECT","actions":[{"id":c,"label":c} for c in _CATEGORIES if streaks.get(c,0)<2]})
        else:
            out.update(_question(package,s,index=s["question_index"])); out["selected_label"]=s["target_category"]
        return out

    if variant == "PERFECT_QUARTER":
        out.update(_question(package,s))
        out["status_items"]=[{"label":"DRIVE","value":f"{s.get('drive_index',0)+1}/4"},
                             {"label":"PLAY","value":f"{s.get('drive_play',0)+1}/2"},
                             {"label":"TDS","value":s.get("touchdowns",0)}]
        return out

    raise ValueError(f"unknown Wave 3 strategy variant {variant!r}")


def evaluate(package: dict, progress: dict, submission: dict) -> tuple[dict, dict]:
    s=_state(progress); variant=package["domain_variant"]; action=str(submission.get("action","")).strip()
    if s.get("completed") or s.get("ended"): raise ValueError("this strategy round has already ended")

    if variant == "CONNECT_FOUR":
        board=s.get("connect_board") or [[None]*7 for _ in range(6)]
        if s.get("pending_column") is None:
            col=int(action)
            if col<0 or col>6 or board[0][col] is not None: raise ValueError("column unavailable")
            s["pending_column"]=col; return {"action":"select","column":col},s
        result=core._grade(package,s,submission); col=s.pop("pending_column"); who="YOU" if result["correct"] else "THEM"
        for row in range(5,-1,-1):
            if board[row][col] is None: board[row][col]=who; break
        s["connect_board"]=board; _advance(s,result["correct"])
        winner=_connect_winner(board)
        if winner or all(board[0][c] is not None for c in range(7)):
            s["completed"]=True; s["result_label"]=f"{winner} connected four" if winner else "Board draw"
        return result,s

    if variant == "TIC_TAC_TOE":
        cells=dict(s.get("ttt_cells",{}))
        if s.get("pending_square") is None:
            sq=int(action)
            if sq<0 or sq>8 or str(sq) in cells: raise ValueError("square unavailable")
            s["pending_square"]=sq; return {"action":"select","square":sq},s
        result=core._grade(package,s,submission); sq=s.pop("pending_square"); cells[str(sq)]="YOU" if result["correct"] else "THEM"
        s["ttt_cells"]=cells; _advance(s,result["correct"]); winner=_line_winner(cells)
        if winner or len(cells)>=9:
            s["completed"]=True; s["result_label"]=f"{winner} won the board" if winner else "Board draw"
        return result,s

    if variant == "CHALLENGE_FLAG":
        s.setdefault("challenges",2)
        if s.get("review_pending"):
            if action=="accept":
                s["review_pending"]=False; s["removed_option_ids"]=[]; s["question_index"]=None
                _advance(s,False)
                if s["cursor"]>=8: s["completed"]=True; s["result_label"]=f"{s.get('score',0)} points"
                return {"action":"accept"},s
            if action=="challenge":
                if s["challenges"]<=0: raise ValueError("no challenges left")
                s["challenges"]-=1; s["review_pending"]=False
                return {"action":"select","review":"replay"},s
            raise ValueError("invalid review action")
        idx=s.get("question_index")
        if idx is None: idx=s["cursor"]; s["question_index"]=idx
        result=_grade_at(package,idx,submission)
        if result["correct"]:
            s["score"]=s.get("score",0)+100; s["removed_option_ids"]=[]; s["question_index"]=None; _advance(s,True)
        else:
            chosen=str(submission.get("choice_item_id","")).strip().upper()
            if s.get("removed_option_ids"):
                s["removed_option_ids"]=[]; s["question_index"]=None; _advance(s,False)
            elif s["challenges"]>0:
                s["review_pending"]=True; s["removed_option_ids"]=[chosen]; return result,s
            else:
                s["question_index"]=None; _advance(s,False)
        if s["cursor"]>=8: s["completed"]=True; s["result_label"]=f"{s.get('score',0)} points"
        return result,s

    if variant == "EXTRA_POINT":
        if s.get("conversion_pending"):
            if action=="kick":
                s["score"]=s.get("score",0)+1; s["conversion_pending"]=False
                if s.get("touchdowns",0)>=4 or s["cursor"]>=8:
                    s["completed"]=True; s["result_label"]=f"{s['score']} points"
                return {"action":"select","conversion":"kick"},s
            if action=="two":
                s["conversion_pending"]=False; s["two_point_question"]=True
                return {"action":"select","conversion":"two"},s
            raise ValueError("invalid conversion action")
        if s.get("two_point_question"):
            result=core._grade(package,s,submission)
            if result["correct"]: s["score"]=s.get("score",0)+2
            s["two_point_question"]=False; _advance(s,result["correct"])
            if s.get("touchdowns",0)>=4: s["completed"]=True; s["result_label"]=f"{s['score']} points"
            return result,s
        result=core._grade(package,s,submission)
        if result["correct"]:
            s["score"]=s.get("score",0)+6
            s["touchdowns"]=s.get("touchdowns",0)+1
            s["conversion_pending"]=True
            _advance(s,True)
        else:
            _advance(s,False)
        if s["cursor"]>=8 and not s.get("conversion_pending"):
            s["completed"]=True; s["result_label"]=f"{s.get('score',0)} points"
        return result,s

    if variant == "COMEBACK_MODE":
        result=core._grade(package,s,submission); s["possessions"]=s.get("possessions",0)+1
        if result["correct"]: s["score"]=s.get("score",0)+7
        _advance(s,result["correct"])
        if s["score"]>=21 or s["possessions"]>=6:
            s["completed"]=True; s["result_label"]="Comeback complete" if s["score"]>=21 else "Comeback fell short"
        return result,s

    if variant == "CATEGORY_DRAFT":
        uses=dict(s.get("category_uses",{}))
        if s.get("target_category") is None:
            if action not in _CATEGORIES or uses.get(action,0)>=2: raise ValueError("category unavailable")
            idx=_find_category_index(package,s["cursor"],action,set(s.get("used_question_indexes",[])))
            s["target_category"]=action; s["question_index"]=idx; return {"action":"select","category":action},s
        idx=s.pop("question_index"); cat=s.pop("target_category"); result=_grade_at(package,idx,submission)
        uses[cat]=uses.get(cat,0)+1; s["category_uses"]=uses
        used=list(s.get("used_question_indexes",[])); used.append(idx); s["used_question_indexes"]=used
        if result["correct"]: s["score"]=s.get("score",0)+1
        _advance(s,result["correct"])
        if sum(uses.values())>=6: s["completed"]=True; s["result_label"]=f"{s['score']} of 6 correct"
        return result,s

    if variant == "THREE_AND_OUT":
        result=core._grade(package,s,submission); s["drive_plays"]=s.get("drive_plays",0)+1
        if result["correct"]: s["drive_hit"]=True
        _advance(s,result["correct"])
        if s.get("drive_hit") or s["drive_plays"]>=3:
            if s.get("drive_hit"): s["drives_won"]=s.get("drives_won",0)+1
            else:
                s["drives_lost"]=s.get("drives_lost",0)+1; s["completed"]=True; s["result_label"]="Three and out"
            s["drive_plays"]=0; s["drive_hit"]=False
        if s.get("drives_won",0)>=4: s["completed"]=True; s["result_label"]="Four drives converted"
        return result,s

    if variant == "PICK_YOUR_POISON":
        if s.get("target_category") is None:
            pair=list(s.get("category_pair") or [_CATEGORIES[s.get("rounds_played",0)%3],_CATEGORIES[(s.get("rounds_played",0)+1)%3]])
            if action not in pair: raise ValueError("choose one of the offered categories")
            idx=_find_category_index(package,s["cursor"],action,set(s.get("used_question_indexes",[])))
            s["target_category"]=action; s["question_index"]=idx; s["category_pair"]=pair
            return {"action":"select","category":action},s
        idx=s.pop("question_index"); s.pop("target_category",None); result=_grade_at(package,idx,submission)
        used=list(s.get("used_question_indexes",[])); used.append(idx); s["used_question_indexes"]=used
        if result["correct"]: s["score"]=s.get("score",0)+1
        s["rounds_played"]=s.get("rounds_played",0)+1; s["category_pair"]=[_CATEGORIES[s["rounds_played"]%3],_CATEGORIES[(s["rounds_played"]+1)%3]]
        _advance(s,result["correct"])
        if s["rounds_played"]>=6: s["completed"]=True; s["result_label"]=f"{s['score']} of 6 won"
        return result,s

    if variant == "SECOND_CHANCE_QUEUE":
        idx=s.get("active_replay_index")
        if idx is None: idx=s["cursor"]
        result=_grade_at(package,idx,submission)
        if result["correct"]: s["score"]=s.get("score",0)+1
        if s.get("active_replay_index") is not None:
            s["active_replay_index"]=None; s["completed"]=True; _advance(s,result["correct"],0)
            s["result_label"]=f"{s['score']} points after replay"; return result,s
        if not result["correct"] and s.get("deferred_index") is None:
            s["deferred_index"]=idx
        _advance(s,result["correct"])
        if s["cursor"]>=8:
            if s.get("deferred_index") is not None:
                s["active_replay_index"]=s["deferred_index"]
            else:
                s["completed"]=True; s["result_label"]=f"{s['score']} of 8 correct"
        return result,s

    if variant == "COVERAGE_SHELL":
        stops=dict(s.get("zone_stops",{}))
        if s.get("target_zone") is None:
            if action not in ("short","middle","deep") or stops.get(action,0)>=2: raise ValueError("zone unavailable")
            s["target_zone"]=action; return {"action":"select","zone":action},s
        zone=s.pop("target_zone"); result=core._grade(package,s,submission)
        if result["correct"]: stops[zone]=stops.get(zone,0)+1
        else: s["completions_allowed"]=s.get("completions_allowed",0)+1
        s["zone_stops"]=stops; _advance(s,result["correct"])
        if all(stops.get(z,0)>=2 for z in ("short","middle","deep")): s["completed"]=True; s["result_label"]="All zones locked down"
        elif s.get("completions_allowed",0)>=3: s["completed"]=True; s["result_label"]="Coverage broken"
        return result,s

    if variant == "OFFENSE_DEFENSE":
        result=core._grade(package,s,submission); role="offense" if s.get("snap",0)%2==0 else "defense"
        if role=="offense" and result["correct"]: s["player_score"]=s.get("player_score",0)+7
        if role=="defense" and not result["correct"]: s["opponent_score"]=s.get("opponent_score",0)+7
        s["snap"]=s.get("snap",0)+1; _advance(s,result["correct"])
        if s["snap"]>=8:
            s["completed"]=True; p=s.get("player_score",0); o=s.get("opponent_score",0)
            s["result_label"]="You win" if p>o else ("Tie game" if p==o else "Opponent wins")
        return result,s

    if variant == "FIELD_GOAL_RANGE":
        if s.get("kick_question"):
            result=core._grade(package,s,submission); value=s.get("kick_value",1)
            if result["correct"]: s["score"]=value
            s["completed"]=True; s["kick_question"]=False; _advance(s,result["correct"])
            s["result_label"]=f"Field goal {'good' if result['correct'] else 'missed'} · {s.get('score',0)} pts"
            return result,s
        if s.get("decision_pending",True):
            if action=="kick":
                if s.get("yards",0)<20: raise ValueError("not yet in field goal range")
                s["kick_question"]=True; s["decision_pending"]=False; s["kick_value"]=1+s.get("yards",0)//20
                return {"action":"select","decision":"kick"},s
            if action=="drive":
                s["decision_pending"]=False; return {"action":"select","decision":"drive"},s
            raise ValueError("invalid field-goal decision")
        result=core._grade(package,s,submission)
        if result["correct"]: s["yards"]=min(80,s.get("yards",0)+10)
        _advance(s,result["correct"]); s["decision_pending"]=True
        if s["cursor"]>=8:
            if s.get("yards",0)>=20:
                s["kick_question"]=True
                s["decision_pending"]=False
                s["kick_value"]=1+s.get("yards",0)//20
            else:
                s["completed"]=True; s["result_label"]="Never reached field goal range"
        return result,s

    if variant == "TWO_MINUTE_DRILL":
        if s.get("clock") is None: s["clock"]=120
        if s.get("tempo") is None:
            if action not in ("hurry","normal"): raise ValueError("invalid tempo")
            cost=15 if action=="hurry" else 30
            if s["clock"]<cost: raise ValueError("not enough clock")
            s["clock"]-=cost; s["tempo"]=action; return {"action":"select","tempo":action},s
        result=core._grade(package,s,submission); tempo=s.pop("tempo")
        if result["correct"]: s["yards"]=s.get("yards",0)+(8 if tempo=="hurry" else 15)
        _advance(s,result["correct"])
        if s.get("yards",0)>=60: s["completed"]=True; s["result_label"]="Scoring range reached"
        elif s["clock"]<=0: s["completed"]=True; s["result_label"]="Clock expired"
        return result,s

    if variant == "CATEGORY_STREAK":
        streaks=dict(s.get("category_streaks",{}))
        if s.get("target_category") is None:
            if action not in _CATEGORIES or streaks.get(action,0)>=2: raise ValueError("category unavailable")
            idx=_find_category_index(package,s["cursor"],action,set(s.get("used_question_indexes",[])))
            s["target_category"]=action; s["question_index"]=idx; return {"action":"select","category":action},s
        idx=s.pop("question_index"); cat=s.pop("target_category"); result=_grade_at(package,idx,submission)
        streaks[cat]=min(2,streaks.get(cat,0)+1) if result["correct"] else 0; s["category_streaks"]=streaks
        used=list(s.get("used_question_indexes",[])); used.append(idx); s["used_question_indexes"]=used
        _advance(s,result["correct"])
        if all(streaks.get(c,0)>=2 for c in _CATEGORIES):
            s["completed"]=True; s["result_label"]="All category streaks complete"
        elif s["cursor"]>=18:
            s["completed"]=True; s["result_label"]="Streak window expired"
        return result,s

    if variant == "PERFECT_QUARTER":
        result=core._grade(package,s,submission)
        if result["correct"]: s["drive_correct"]=s.get("drive_correct",0)+1
        s["drive_play"]=s.get("drive_play",0)+1; _advance(s,result["correct"])
        if s["drive_play"]>=2:
            if s.get("drive_correct",0)==2: s["touchdowns"]=s.get("touchdowns",0)+1
            s["drive_index"]=s.get("drive_index",0)+1; s["drive_play"]=0; s["drive_correct"]=0
        if s.get("drive_index",0)>=4:
            s["completed"]=True; s["result_label"]="Perfect quarter" if s.get("touchdowns",0)>=3 else f"{s.get('touchdowns',0)} touchdowns"
        return result,s

    raise ValueError(f"unknown Wave 3 strategy variant {variant!r}")
