from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import json
import autonomous_expansion as A
class H(BaseHTTPRequestHandler):
 def j(self,o,code=200):
  b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def body(self):
  n=int(self.headers.get("Content-Length","0"));return json.loads(self.rfile.read(n) or b"{}")
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  if u.path=="/v3.1/discover":return self.j(A.propose_new_games(int(q.get("limit",["20"])[0])))
  if u.path=="/v3.1/memory":return self.j(A.recall_templates(q.get("q",[""])[0]))
  return self.j({"error":"not_found"},404)
 def do_POST(self):
  d=self.body()
  if self.path=="/v3.1/direct":return self.j(A.director_plus(d["request"]))
  if self.path=="/v3.1/memory":return self.j(A.remember_template(d["name"],d["description"],d["mechanic"],d["spec"],d["graph_plan"]))
  if self.path=="/v3.1/certify":return self.j(A.auto_certify(d["discovery_id"]))
  return self.j({"error":"not_found"},404)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",8801),H).serve_forever()
