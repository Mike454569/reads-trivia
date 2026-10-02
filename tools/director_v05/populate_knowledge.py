"""One-command production knowledge population report."""
from __future__ import annotations
from tools.quiz_export import engine as engine_bootstrap
from .populate_existing_lore import populate_existing
from .populate_nfl_trades import populate_nfl_trades
from .draft_intelligence import derive_nfl_draft_intelligence
from .story_mining import mine_nfl_games
from .pbp_story_mining import mine_nfl_pbp
from .game_chaos_mining import mine_nfl_game_chaos
from .lore_coverage import coverage
from .lore_trivia import lore_gameplay_report
from .lore_mechanics import advanced_lore_report

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
    result["coverage"]=coverage(c)
    result["lore_gameplay"]=lore_gameplay_report(c)
    result["advanced_lore"]=advanced_lore_report(c)
    result["events"]={r["event_type"]:r["n"] for r in c.execute(
      "SELECT event_type,COUNT(*) n FROM universal_event GROUP BY event_type")}
    result["derived"]={r["metric"]:r["n"] for r in c.execute(
      "SELECT metric,COUNT(*) n FROM universal_derived_fact GROUP BY metric")}
    c.close()
    return result

if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2,sort_keys=True))
