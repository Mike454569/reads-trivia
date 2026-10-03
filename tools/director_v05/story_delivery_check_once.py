import json
from tools.director_v05 import lore_package
from tools.director_v04 import deep_trivia

out={}
try:
    pkg=lore_package.build_package(seed="prod-story-delivery",target_count=6,difficulty="hard")
    out["deep_lore"]={
        "qa_status":pkg.get("qa_status"),
        "question_count":len(pkg.get("questions") or []),
        "story_questions_used":int((pkg.get("_diagnostics") or {}).get("story_questions_used") or 0),
        "story_ready_available":int((pkg.get("_diagnostics") or {}).get("story_ready_available") or 0),
        "question_ids":[q.get("id") for q in (pkg.get("questions") or [])],
    }
except Exception as exc:
    out["deep_lore"]={"error":type(exc).__name__+":"+str(exc)}

try:
    rounds=deep_trivia.generate_rounds("prod-story-shared",6)
    out["shared_deep_pool"]={
        "round_count":len(rounds),
        "story_rounds":sum(1 for r in rounds if r.get("depth_source")=="STORY_FACTORY" or r.get("category")=="Football Lore"),
        "sources":[r.get("depth_source") for r in rounds],
        "categories":[r.get("category") for r in rounds],
    }
except Exception as exc:
    out["shared_deep_pool"]={"error":type(exc).__name__+":"+str(exc)}

print(json.dumps(out,sort_keys=True))
