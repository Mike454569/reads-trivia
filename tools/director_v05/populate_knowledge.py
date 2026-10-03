"""One-command production knowledge population report."""
from __future__ import annotations
from tools.quiz_export import engine as engine_bootstrap
from .populate_existing_lore import populate_existing
from .populate_nfl_trades import populate_nfl_trades
from .draft_intelligence import derive_nfl_draft_intelligence
from .story_mining import mine_nfl_games
from .pbp_story_mining import mine_nfl_pbp
from .game_chaos_mining import mine_nfl_game_chaos
from .cfb_pbp_story_mining import mine_cfb_pbp
from .lore_coverage import coverage
from .lore_trivia import lore_gameplay_report
from .lore_mechanics import advanced_lore_report
from .lore_chains import lore_chain_report
from .lore_question_bank import bank_report
from .lore_format_bank import build_multiformat_bank
from .lore_label_audit import label_coverage_report
from .cfb_weather_lore import mine_cfb_weather_lore
from .nfl_contract_lore import mine_nfl_contract_lore
from .fact_gap_queue import fact_gap_queue
from .cfb_recruiting_lore import mine_cfb_recruiting_lore
from .official_rule_lore import populate_official_rule_lore

def run():
    c=engine_bootstrap.connect()
    c.execute("PRAGMA busy_timeout=30000")
    result={}
    result["existing"]=populate_existing(c)
    result["trades"]=populate_nfl_trades(c)
    result["draft_intelligence"]=derive_nfl_draft_intelligence(c)
    result["story_mining"]=mine_nfl_games(c)
    result["pbp_story_mining"]=mine_nfl_pbp(c)
    result["game_chaos_mining"]=mine_nfl_game_chaos(c)
    result["cfb_pbp_lore"]=mine_cfb_pbp(c)
    result["cfb_weather_lore"]=mine_cfb_weather_lore(c)
    result["nfl_contract_lore"]=mine_nfl_contract_lore(c)
    result["cfb_recruiting_lore"]=mine_cfb_recruiting_lore(c)
    result["official_rule_lore"]=populate_official_rule_lore(c)
    result["coverage"]=coverage(c)
    result["lore_gameplay"]=lore_gameplay_report(c)
    result["advanced_lore"]=advanced_lore_report(c)
    result["lore_chains"]=lore_chain_report(c)
    result["lore_question_banks"]=bank_report(c, limit_anchors=75, target=15)
    result["lore_multiformat"]=build_multiformat_bank(c, target=12, discovery_limit=250)
    result["lore_label_coverage"]=label_coverage_report(c)
    result["fact_gap_queue"]=fact_gap_queue(c)
    result["events"]={r["event_type"]:r["n"] for r in c.execute(
      "SELECT event_type,COUNT(*) n FROM universal_event GROUP BY event_type")}
    result["derived"]={r["metric"]:r["n"] for r in c.execute(
      "SELECT metric,COUNT(*) n FROM universal_derived_fact GROUP BY metric")}
    c.close()
    return result

if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2,sort_keys=True))
