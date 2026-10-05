from __future__ import annotations
import importlib.util
import json
import sys

sys.path.insert(0, "/app")

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

load("tools.director_v05.story_batch_processor","/tmp/story_batch_processor.py")
drain=load("tools.director_v05.story_batch_drain","/tmp/story_batch_drain.py")
print(json.dumps(
    drain.drain_story_queue(
        batch_size=5,
        max_batches=6,
        time_budget_seconds=600,
        include_deep_chains=False,
    ),
    sort_keys=True,
))
