import json, sqlite3
p="/data/engine/reads_football_v4.0.sqlite"
c=sqlite3.connect("file:"+p+"?mode=ro",uri=True,timeout=10)
c.row_factory=sqlite3.Row
rows=c.execute("""SELECT question_id,event_id,mechanic,status,question_json
                  FROM story_generated_questions ORDER BY question_id""").fetchall()
out={"total":len(rows),"passed":0,"failed":0,"by_mechanic":{},"by_status":{},"failures":[]}
for row in rows:
    q=json.loads(row["question_json"])
    errors=[]
    mech=str(q.get("mechanic") or row["mechanic"] or "")
    out["by_mechanic"][mech]=out["by_mechanic"].get(mech,0)+1
    st=str(row["status"])
    out["by_status"][st]=out["by_status"].get(st,0)+1
    answer=q.get("answer") or {}
    label=str(answer.get("label") or "").strip()
    aid=str(answer.get("id") or "").strip()
    clues=[str(x.get("text") if isinstance(x,dict) else x).strip() for x in (q.get("clues") or [])]
    if len(clues)<3: errors.append("NEEDS_THREE_CLUES")
    if any(not x for x in clues): errors.append("BLANK_CLUE")
    if len({x.casefold() for x in clues})!=len(clues): errors.append("DUPLICATE_CLUE")
    if not label or label==aid: errors.append("UNRESOLVED_ANSWER_LABEL")
    if mech=="MULTIPLE_CHOICE":
        opts=[str(x) for x in (q.get("options") or [])]
        if len(opts)!=4: errors.append("MCQ_REQUIRES_FOUR_OPTIONS")
        if len({x.casefold().strip() for x in opts})!=len(opts): errors.append("MCQ_DUPLICATE_OPTIONS")
        if opts.count(label)!=1: errors.append("MCQ_ANSWER_NOT_UNIQUE")
    elif mech!="PROGRESSIVE_CLUE":
        errors.append("UNEXPECTED_MECHANIC")
    e=c.execute("SELECT verification_status,sensitive,league FROM universal_event WHERE event_id=?",(row["event_id"],)).fetchone()
    if not e: errors.append("EVENT_MISSING")
    else:
        if str(e["verification_status"])!="VERIFIED": errors.append("EVENT_NOT_VERIFIED")
        if int(e["sensitive"] or 0): errors.append("SENSITIVE_EVENT")
        ev=c.execute("SELECT COUNT(*) FROM universal_event_evidence WHERE event_id=?",(row["event_id"],)).fetchone()[0]
        if int(ev)<1: errors.append("NO_EVIDENCE")
    if errors:
        out["failed"]+=1
        out["failures"].append({"question_id":row["question_id"],"event_id":row["event_id"],"errors":errors})
    else:
        out["passed"]+=1
out["pass_rate"]=round(out["passed"]/max(1,out["total"]),4)
print(json.dumps(out,sort_keys=True))
c.close()
