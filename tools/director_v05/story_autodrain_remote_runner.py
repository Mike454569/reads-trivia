from __future__ import annotations
import importlib.util
import json
import sys
import traceback

sys.path.insert(0, "/app")

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

try:
    load("tools.director_v05.story_sqlite","/tmp/story_sqlite.py")
    load("tools.director_v05.story_candidate_harvest","/tmp/story_candidate_harvest.py")
    load("tools.director_v05.story_to_trivia_factory","/tmp/story_to_trivia_factory.py")
    load("tools.director_v05.story_batch_processor","/tmp/story_batch_processor.py")
    drain=load("tools.director_v05.story_batch_drain","/tmp/story_batch_drain.py")
    result=drain.drain_story_queue(
        batch_size=5,
        max_batches=6,
        time_budget_seconds=600,
        include_deep_chains=False,
    )
    print(json.dumps({"ok":True,"result":result},sort_keys=True), flush=True)
except Exception as exc:
    print(json.dumps({
        "ok":False,
        "error":type(exc).__name__+":"+str(exc),
        "traceback":traceback.format_exc(),
    },sort_keys=True), flush=True)
    raise
