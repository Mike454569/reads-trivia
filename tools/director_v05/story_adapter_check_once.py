import json
from tools.quiz_export import engine as engine_bootstrap
out={}
c=engine_bootstrap.connect()
try:
    try:
        from tools.director_v05.story_question_pool import load_ready_story_questions
        qs=load_ready_story_questions(c,limit=25)
        out["deep_lore_story_pool"]={
            "available":len(qs),
            "question_ids":[q.get("question_id") for q in qs],
        }
    except Exception as exc:
        out["deep_lore_story_pool"]={"error":type(exc).__name__+":"+str(exc)}
    try:
        from tools.director_v04.story_arcade_adapter import load_story_mcqs
        all_q=load_story_mcqs(c,limit=25)
        nfl_q=load_story_mcqs(c,limit=25,league="NFL")
        cfb_q=load_story_mcqs(c,limit=25,league="CFB")
        out["arcade_story_pool"]={
            "all":len(all_q),
            "nfl":len(nfl_q),
            "cfb":len(cfb_q),
            "question_ids":[q.get("question_id") for q in all_q],
        }
    except Exception as exc:
        out["arcade_story_pool"]={"error":type(exc).__name__+":"+str(exc)}
finally:
    c.close()
print(json.dumps(out,sort_keys=True))
