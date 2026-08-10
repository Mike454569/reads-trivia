"""Tiny JSON API wrapper for Reads v1.8 retention features."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlparse,parse_qs
import json
import retention_engine as R
class H(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path); q=parse_qs(u.query)
        try:
            if u.path=="/v1/feed": return self.sendj(R.personalized_feed(q["user"][0],int(q.get("limit",[20])[0])))
            if u.path=="/v1/streak": return self.sendj(R.update_streak(q["user"][0],q.get("date",[None])[0]))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0")); d=json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path=="/v1/event": return self.sendj({"event_id":R.record_event(d["user_id"],d["mode_id"],d["event_type"],d.get("puzzle_id"),d.get("correct"),d.get("response_ms"),d.get("wrong_guesses",0),d.get("hints_used",0),d.get("competition_id"),d.get("metadata"))})
            if self.path=="/v1/ranked/result": return self.sendj(R.ranked_result(d["user_id"],d["queue_id"],d["won"],d.get("opponent_rating",1000),d.get("season_id","S2026_PRESEASON")))
            if self.path=="/v1/challenge": return self.sendj(R.create_challenge(d["user_id"],d["mode_id"],d.get("count",5),d.get("opponent_user_id")))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
if __name__=="__main__": HTTPServer(("127.0.0.1",8788),H).serve_forever()
