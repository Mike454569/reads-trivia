from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import json
import game_director as D
class H(BaseHTTPRequestHandler):
 def j(self,o,code=200):
  b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  if u.path=="/v3/director/examples":return self.j(D.examples())
  if u.path=="/v3/director/preview":return self.j(D.preview(q.get("q",[""])[0],int(q.get("limit",["12"])[0])))
  return self.j({"error":"not_found"},404)
 def do_POST(self):
  n=int(self.headers.get("Content-Length","0"));d=json.loads(self.rfile.read(n) or b"{}")
  if self.path=="/v3/director/interpret":return self.j(D.interpret(d["request"]))
  if self.path=="/v3/director/preview":return self.j(D.preview(d["request"],d.get("limit",20),d.get("seed","director")))
  if self.path=="/v3/director/publish":return self.j(D.publish(d["request"],d["mode_id"],d.get("limit",50),d.get("seed","publish")))
  return self.j({"error":"not_found"},404)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",8800),H).serve_forever()
