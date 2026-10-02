"""One-command production knowledge population report."""
from __future__ import annotations
from tools.quiz_export import engine as engine_bootstrap
from .populate_existing_lore import populate_existing
from .populate_nfl_trades import populate_nfl_trades
from .draft_intelligence import derive_nfl_draft_intelligence

def run():
    c=engine_bootstrap.connect()
    result={"existing":populate_existing(c),"trades":populate_nfl_trades(c),
            "draft_intelligence":derive_nfl_draft_intelligence(c)}
    result["events"]={r["event_type"]:r["n"] for r in c.execute(
      "SELECT event_type,COUNT(*) n FROM universal_event GROUP BY event_type")}
    result["derived"]={r["metric"]:r["n"] for r in c.execute(
      "SELECT metric,COUNT(*) n FROM universal_derived_fact GROUP BY metric")}
    c.close()
    return result

if __name__=="__main__":
    import json
    print(json.dumps(run(),indent=2,sort_keys=True))
