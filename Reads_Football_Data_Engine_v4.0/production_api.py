"""Minimal production API surface for v2.1 hardening services."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import json,time
import production_engine as P
class H(BaseHTTPRequestHandler):
 def sendj(self,o,code=200):
  b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def body(self):
  n=int(self.headers.get("Content-Length","0"));return json.loads(self.rfile.read(n) or b"{}")
 def do_GET(self):
  q=parse_qs(urlparse(self.path).query);path=urlparse(self.path).path
  try:
   if path=="/v2.1/entitlement":return self.sendj(P.entitlement(q["user"][0],q["key"][0]))
   if path=="/v2.1/sync":return self.sendj(P.sync_get(q["user"][0],q["namespace"][0]))
   if path=="/v2.1/funnel":return self.sendj(P.build_daily_funnel(q.get("date",[None])[0]))
   return self.sendj({"error":"not_found"},404)
  except Exception as e:return self.sendj({"error":str(e)},400)
 def do_POST(self):
  d=self.body()
  try:
   if self.path=="/v2.1/account":return self.sendj(P.ensure_account(d["user_id"],d.get("email"),d.get("provider","APP"),d.get("subject")))
   if self.path=="/v2.1/session":return self.sendj(P.create_session(d["user_id"]))
   if self.path=="/v2.1/sync":return self.sendj(P.sync_put(d["user_id"],d["namespace"],d["expected_revision"],d["state"]))
   if self.path=="/v2.1/ranked/issue":return self.sendj(P.issue_ranked_match(d["user_id"],d["mode_id"],d["puzzle_ids"]))
   if self.path=="/v2.1/ranked/submit":return self.sendj(P.validate_ranked_submission(d["user_id"],d["match_token"],d["puzzle_ids"],d["total_ms"]))
   if self.path=="/v2.1/track":return self.sendj({"event_id":P.track(d["event_name"],d.get("user_id"),d.get("anonymous_id"),d.get("surface"),d.get("properties"))})
   return self.sendj({"error":"not_found"},404)
  except Exception as e:return self.sendj({"error":str(e)},400)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",8793),H).serve_forever()
