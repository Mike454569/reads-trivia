"""Production-sized stress harness for Reads Engine v0.5.

Runs only against the configured Engine DB. It never mutates legacy source
tables and is safe to use as a diagnostic/certification workload.
"""
from __future__ import annotations
import argparse, json, time
from collections import Counter, defaultdict
from pathlib import Path

from tools.quiz_export import engine as engine_bootstrap
from .legacy_bridge import ADAPTERS, bridge_report, iter_facts
from .chain_engine import player_nfl_chains
from .chain_quality import eligible_chains, explain_rejection
from .question_pipeline import build_question
from .distractor_intelligence import Candidate
from .distractor_pools import nfl_draft_same_round_era

DEFAULT_MAX_FACTS_PER_ADAPTER=5000
DEFAULT_MAX_PLAYERS=1000

def _table_exists(c,name):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None

def _sample_nfl_player_ids(c,limit):
    if not _table_exists(c,"canonical_roster_seasons"): return []
    rows=c.execute(
      """SELECT player_id,COUNT(*) AS n FROM canonical_roster_seasons
         WHERE verification_status='SOURCE_BACKED'
         GROUP BY player_id ORDER BY n DESC,player_id LIMIT ?""",(limit,)).fetchall()
    return [str(r["player_id"]) for r in rows]

def _answer_label(c,player_id):
    if not _table_exists(c,"canonical_players"): return player_id
    r=c.execute("SELECT display_name FROM canonical_players WHERE player_id=?",(player_id,)).fetchone()
    return (r["display_name"] if r and r["display_name"] else player_id)

def _draft_context(c,player_id):
    if not _table_exists(c,"draft_facts"): return None,[],set()
    r=c.execute(
      """SELECT player_key,player_name,draft_season,draft_round,draft_pick_overall,draft_team
         FROM draft_facts WHERE player_key=? AND verification_status='SOURCE_BACKED'""",(player_id,)).fetchone()
    if not r:return None,[],set()
    correct=Candidate(str(r["player_key"]),r["player_name"],r["draft_season"],None,r["draft_team"],
                      f"ROUND_{r['draft_round']}",float(r["draft_pick_overall"] or 0),True)
    pool=nfl_draft_same_round_era(c,season=r["draft_season"],round_no=r["draft_round"],exclude_player_id=player_id)
    return correct,pool,{player_id}

def run(*,max_facts_per_adapter=DEFAULT_MAX_FACTS_PER_ADAPTER,max_players=DEFAULT_MAX_PLAYERS,populate=True):
    c=engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=30000")
    started=time.time()
    population={}
    if populate:
        try:
            from .populate_existing_lore import populate_existing
            from .draft_intelligence import derive_nfl_draft_intelligence
            population["existing"]=populate_existing(c); c.commit()
            population["draft_intelligence"]=derive_nfl_draft_intelligence(c); c.commit()
            from .story_mining import mine_nfl_games
            population["story_mining"]=mine_nfl_games(c); c.commit()
            from .pbp_story_mining import mine_nfl_pbp
            population["pbp_story_mining"]=mine_nfl_pbp(c); c.commit()
            from .game_chaos_mining import mine_nfl_game_chaos
            population["game_chaos_mining"]=mine_nfl_game_chaos(c); c.commit()
            from .cfb_pbp_story_mining import mine_cfb_pbp
            population["cfb_pbp_lore"]=mine_cfb_pbp(c); c.commit()
            from .cfb_weather_lore import mine_cfb_weather_lore
            population["cfb_weather_lore"]=mine_cfb_weather_lore(c); c.commit()
            from .nfl_contract_lore import mine_nfl_contract_lore
            population["nfl_contract_lore"]=mine_nfl_contract_lore(c); c.commit()
            from .cfb_recruiting_lore import mine_cfb_recruiting_lore
            population["cfb_recruiting_lore"]=mine_cfb_recruiting_lore(c); c.commit()
            from .official_rule_lore import populate_official_rule_lore
            population["official_rule_lore"]=populate_official_rule_lore(c); c.commit()
            from .reviewed_story_corpus import ingest_reviewed_corpus
            population["reviewed_story_corpus"]=ingest_reviewed_corpus(c); c.commit()
            from .lore_coverage import coverage
            population["coverage"]=coverage(c)
            from .lore_trivia import lore_gameplay_report
            population["lore_gameplay"]=lore_gameplay_report(c)
            from .lore_mechanics import advanced_lore_report
            population["advanced_lore"]=advanced_lore_report(c)
            from .lore_chains import lore_chain_report
            population["lore_chains"]=lore_chain_report(c)
            from .lore_question_bank import bank_report
            population["lore_question_banks"]=bank_report(c, limit_anchors=75, target=15)
            from .lore_format_bank import build_multiformat_bank
            population["lore_multiformat"]=build_multiformat_bank(c, target=12, discovery_limit=250)
            from .lore_label_audit import label_coverage_report
            population["lore_label_coverage"]=label_coverage_report(c)
            from .fact_gap_queue import fact_gap_queue
            population["fact_gap_queue"]=fact_gap_queue(c)
            from .certify_story_question_quality import certify_story_question_quality
            population["story_question_quality"]=certify_story_question_quality(c)
            try:
                from .populate_nfl_trades import populate_nfl_trades
                population["trades"]=populate_nfl_trades(c); c.commit()
            except Exception as trade_exc:
                population["trades_error"]=type(trade_exc).__name__+":"+str(trade_exc)
        except Exception as exc:
            population["error"]=type(exc).__name__+":"+str(exc)
    report={
      "version":"1.2.0","population":population,"bridge":bridge_report(c),"facts":{},"chains":{},
      "questions":{},"failures":{},"timing":{}
    }
    # Bridge scan: validates every configured adapter can actually yield rows.
    for name in ADAPTERS:
        t0=time.time(); count=0
        try:
            for _ in iter_facts(c,name,limit=max_facts_per_adapter): count+=1
            report["facts"][name]={"status":"OK","sampled":count}
        except Exception as e:
            report["facts"][name]={"status":"ERROR","sampled":count,"error":type(e).__name__+":"+str(e)}
        report["timing"][f"facts:{name}"]=round(time.time()-t0,3)

    rejection=Counter(); chain_counts=Counter(); question_counts=Counter()
    examples=defaultdict(list)
    players=_sample_nfl_player_ids(c,max_players)
    for pid in players:
        try:
            chains=player_nfl_chains(c,pid)
        except Exception as e:
            rejection["CHAIN_EXCEPTION"]+=1
            if len(examples["CHAIN_EXCEPTION"])<10:examples["CHAIN_EXCEPTION"].append({"player_id":pid,"error":repr(e)})
            continue
        chain_counts["discovered"]+=len(chains)
        eligible=eligible_chains(chains)
        chain_counts["eligible"]+=len(eligible)
        for ch in chains:
            if ch not in eligible:
                reason=explain_rejection(ch,chains) or "CHAIN_FILTERED"
                rejection[reason]+=1
        for ch in eligible:
            # THREE_CLUES exercises the full clue/assembly/QA stack without
            # requiring a distractor pool; MCQ is attempted when draft context exists.
            for mechanic in ("THREE_CLUES","MULTIPLE_CHOICE"):
                try:
                    label=_answer_label(c,pid)
                    kwargs={"answer_label":label,"difficulty_band":"HARD","current_season":2026,
                            "valid_answer_ids":{pid}}
                    if mechanic=="MULTIPLE_CHOICE":
                        correct,pool,valid=_draft_context(c,pid)
                        if correct is None:
                            rejection["NO_DRAFT_DISTRACTOR_CONTEXT"]+=1;continue
                        kwargs.update(correct_candidate=correct,distractor_candidates=pool,all_correct_ids=valid)
                    q=build_question(ch,mechanic,**kwargs)
                    question_counts[f"{mechanic}:PASSED"]+=1
                    if sum(question_counts.values())<=10:
                        examples["PASSED"].append({"player_id":pid,"mechanic":mechanic,"question_id":q["question_id"]})
                except Exception as e:
                    key=str(e).split(":")[0] or type(e).__name__
                    rejection[key]+=1
                    if len(examples[key])<10:examples[key].append({"player_id":pid,"mechanic":mechanic,"error":repr(e)})

    report["chains"]=dict(chain_counts)
    report["questions"]=dict(question_counts)
    report["failures"]={"counts":dict(rejection),"examples":dict(examples)}
    report["timing"]["total_seconds"]=round(time.time()-started,3)
    c.close()
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-facts-per-adapter",type=int,default=DEFAULT_MAX_FACTS_PER_ADAPTER)
    ap.add_argument("--max-players",type=int,default=DEFAULT_MAX_PLAYERS)
    ap.add_argument("--out",default="")
    args=ap.parse_args()
    report=run(max_facts_per_adapter=args.max_facts_per_adapter,max_players=args.max_players)
    payload=json.dumps(report,indent=2,sort_keys=True)
    if args.out: Path(args.out).write_text(payload+"\n",encoding="utf-8")
    print(payload)

if __name__=="__main__": main()
