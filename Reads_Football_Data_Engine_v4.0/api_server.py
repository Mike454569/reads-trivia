
"""
Reads Football API v1.4
GET /health
GET /modes
GET /daily?date=YYYY-MM-DD
GET /random?mode=MODE&difficulty=BAND
GET /graph/search?q=Tom%20Brady
GET /graph/path?start_type=team&start_id=NE&end_type=team&end_id=GB&max_depth=6
GET /six-degrees?seed=2026-08-07
GET /factory/capabilities
POST /factory/analyze
POST /factory/preview
POST /factory/publish
POST /factory/unpublish
POST /answer
POST /attempt
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse,parse_qs
from pathlib import Path
import sqlite3,json,random,re
import graph_explorer
import game_factory

DB=Path(__file__).with_name("reads_football_v4.0.sqlite")

def norm(s):
    s=str(s or "").strip().lower().replace("&"," and ")
    s=re.sub(r"[’'`]","",s)
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return " ".join(s.split())

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def public_puzzle(r):
    x=dict(r); payload=json.loads(x.pop("payload_json")); payload.pop("answer",None); x["payload"]=payload; return x

class H(BaseHTTPRequestHandler):
    def sendj(self,obj,status=200):
        b=json.dumps(obj,default=str).encode()
        self.send_response(status); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path); q=parse_qs(u.query); c=db()
        try:
            if u.path=="/health":
                self.sendj({
                    "database_version":c.execute("SELECT value FROM meta WHERE key='database_version'").fetchone()[0],
                    "eligible_puzzles":c.execute("SELECT COUNT(*) FROM puzzle_catalog WHERE eligible=1").fetchone()[0],
                    "modes":c.execute("SELECT COUNT(*) FROM mode_health WHERE eligible_puzzles>0").fetchone()[0],
                    "graph_nodes":c.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0],
                    "graph_edges":c.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0],
                    "open_collisions":c.execute("SELECT COUNT(*) FROM puzzle_collisions WHERE status='OPEN'").fetchone()[0]
                })
            elif u.path=="/modes":
                self.sendj([dict(r) for r in c.execute("SELECT * FROM mode_health ORDER BY mode_id")])
            elif u.path=="/daily":
                day=q.get("date",["2026-08-07"])[0]; mode=q.get("mode",[None])[0]
                sql="""SELECT d.puzzle_date,d.mode_id,p.puzzle_id,p.difficulty_score,p.difficulty_band,p.payload_json,p.verification_status
                       FROM daily_puzzles d JOIN puzzle_catalog p ON p.puzzle_id=d.puzzle_id WHERE d.puzzle_date=? AND p.eligible=1"""
                params=[day]
                if mode: sql+=" AND d.mode_id=?"; params.append(mode)
                sql+=" ORDER BY d.mode_id"
                self.sendj([public_puzzle(r) for r in c.execute(sql,params)])
            elif u.path=="/random":
                mode=q.get("mode",[None])[0]; diff=q.get("difficulty",[None])[0]
                sql="SELECT * FROM puzzle_catalog WHERE eligible=1"; params=[]
                if mode: sql+=" AND mode_id=?";params.append(mode)
                if diff: sql+=" AND difficulty_band=?";params.append(diff.upper())
                rs=list(c.execute(sql,params))
                self.sendj(public_puzzle(random.choice(rs)) if rs else {"error":"no eligible puzzle"},200 if rs else 404)
            elif u.path=="/graph/search":
                self.sendj(graph_explorer.search(q.get("q",[""])[0]))
            elif u.path=="/graph/path":
                path=graph_explorer.shortest_path(
                    q.get("start_type",[""])[0],q.get("start_id",[""])[0],
                    q.get("end_type",[""])[0],q.get("end_id",[""])[0],
                    int(q.get("max_depth",["6"])[0])
                )
                self.sendj({"path":path,"found":path is not None})
            elif u.path=="/six-degrees":
                self.sendj(graph_explorer.random_six(q.get("seed",["daily"])[0]))
            elif u.path=="/factory/capabilities":
                self.sendj(game_factory.capabilities())
            else: self.sendj({"error":"not found"},404)
        finally: c.close()
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"))
        try: body=json.loads(self.rfile.read(n) or b"{}")
        except: return self.sendj({"error":"invalid json"},400)
        c=db()
        try:
            if self.path=="/answer":
                row=c.execute("SELECT payload_json,source_entity_type,source_entity_id FROM puzzle_catalog WHERE puzzle_id=? AND eligible=1",(body.get("puzzle_id"),)).fetchone()
                if not row:return self.sendj({"error":"puzzle not found"},404)
                payload=json.loads(row["payload_json"]); canonical=str(payload.get("answer","")); accepted={norm(canonical)}
                for a in c.execute("SELECT accepted_answer FROM accepted_answers WHERE answer_type=? AND entity_id=?",(row["source_entity_type"],row["source_entity_id"])): accepted.add(a[0])
                good=norm(body.get("answer")) in accepted
                self.sendj({"correct":good,"canonical_answer":canonical if good else None})
            elif self.path=="/attempt":
                c.execute("""INSERT INTO puzzle_attempts(puzzle_id,user_key,correct,solve_ms,wrong_guess_count,hint_count,abandoned,device_class,player_rating_before)
                             VALUES (?,?,?,?,?,?,?,?,?)""",
                          (body.get("puzzle_id"),body.get("user_key"),1 if body.get("correct") else 0,body.get("solve_ms"),
                           body.get("wrong_guess_count",0),body.get("hint_count",0),1 if body.get("abandoned") else 0,
                           body.get("device_class"),body.get("player_rating_before")))
                c.commit();self.sendj({"ok":True},201)
            elif self.path=="/factory/analyze":
                desc=body.get("description","")
                spec=game_factory.compile_description(desc)
                self.sendj({"spec":spec,"feasibility":game_factory.feasibility(spec)})
            elif self.path=="/factory/preview":
                self.sendj(game_factory.preview(body.get("description",body.get("spec",{})),int(body.get("limit",12)),body.get("seed","preview")))
            elif self.path=="/factory/publish":
                self.sendj(game_factory.publish(body.get("spec_id"),body.get("mode_id"),int(body.get("limit",5000))))
            elif self.path=="/factory/unpublish":
                self.sendj(game_factory.unpublish(body.get("mode_id")))
            else:self.sendj({"error":"not found"},404)
        finally:c.close()

if __name__=="__main__":
    print("Reads Football API v1.4: http://127.0.0.1:8787")
    HTTPServer(("127.0.0.1",8787),H).serve_forever()
