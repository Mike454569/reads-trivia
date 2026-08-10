"""Reads v2.3 quality/knowledge API."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import json
import quality_intelligence as Q
class H(BaseHTTPRequestHandler):
 def sendj(self,o,code=200):
  b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  try:
   if u.path=="/v2.3/health":return self.sendj(Q.health_snapshot())
   if u.path=="/v2.3/graph/query":return self.sendj(Q.query_graph(q["type"][0],q["id"][0],q.get("predicate",[])))
   return self.sendj({"error":"not_found"},404)
  except Exception as e:return self.sendj({"error":str(e)},400)
 def do_POST(self):
  n=int(self.headers.get("Content-Length","0"));d=json.loads(self.rfile.read(n) or b"{}")
  try:
   if self.path=="/v2.3/audit":return self.sendj(Q.run_all())
   if self.path=="/v2.3/daily/certify":return self.sendj(Q.certify_daily(d["date"]))
   if self.path=="/v2.3/release/certify":return self.sendj(Q.release_certify(d.get("version","2.3.0"),True))
   return self.sendj({"error":"not_found"},404)
  except Exception as e:return self.sendj({"error":str(e)},400)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",8795),H).serve_forever()
