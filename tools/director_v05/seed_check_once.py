import json, sqlite3
p="/data/engine/reads_football_v4.0.sqlite"
c=sqlite3.connect("file:"+p+"?mode=ro", uri=True, timeout=5)
def count(sql):
    return int(c.execute(sql).fetchone()[0])
print(json.dumps({
    "reviewed_events": count("select count(*) from universal_event where event_id like 'reviewed_%'"),
    "story_questions": count("select count(*) from story_generated_questions"),
    "reviewed_seed_questions": count("select count(*) from story_generated_questions where candidate_id like 'reviewed-seed:%'"),
    "enriched": count("select count(*) from football_story_enrichment"),
}, sort_keys=True))
c.close()

# fast-question-progress-check
