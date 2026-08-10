"""Reads v2.0 Live Intelligence admin API."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlparse,parse_qs
import sqlite3,json
import live_intelligence as L
DB=L.DB
class H(BaseHTTPRequestHandler):
    def sendj(self,o,code=200):
        b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path);q=parse_qs(u.query);c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
        try:
            if u.path=="/v2/live/feeds":o=[dict(r) for r in c.execute("SELECT * FROM live_data_feeds ORDER BY competition_id,dataset_name")]
            elif u.path=="/v2/live/alerts":o=[dict(r) for r in c.execute("SELECT * FROM admin_alerts WHERE status='OPEN' ORDER BY severity DESC,created_at DESC")]
            elif u.path=="/v2/live/queue":o=[dict(r) for r in c.execute("SELECT * FROM live_publish_queue WHERE decision IS NULL ORDER BY priority DESC,created_at")]
            elif u.path=="/v2/live/events":o=[dict(r) for r in c.execute("SELECT * FROM live_event_catalog ORDER BY event_date DESC LIMIT ?",(int(q.get("limit",[50])[0]),))]
            elif u.path=="/v2/live/slate":
                date=q.get("date",[None])[0];o=L.build_daily_slate(date)
            elif u.path=="/v2/live/outbox":
                o=[dict(r) for r in c.execute("SELECT * FROM notification_outbox ORDER BY created_at DESC LIMIT ?",(int(q.get("limit",[50])[0]),))]
            else:c.close();return self.sendj({"error":"not_found"},404)
            c.close();return self.sendj(o)
        except Exception as e:
            c.close();return self.sendj({"error":str(e)},400)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0"));d=json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path=="/v2/live/run":return self.sendj(L.pipeline(bool(d.get("run_updates",False))))
            if self.path=="/v2/live/event":
                eid=L.register_event(d["competition_id"],d["event_type"],d["event_date"],d["title"],d.get("payload",{}),d["source_id"],d.get("entity_type"),d.get("entity_id"),d.get("verified",True))
                return self.sendj({"event_id":eid,"generation":L.generate_from_event(eid)})
            if self.path=="/v2/live/publish":
                return self.sendj(L.publish_live_event(d["event_id"],d.get("actor","ADMIN"),d.get("notify",True)))
            if self.path=="/v2/live/reject":
                return self.sendj(L.reject_live_event(d["event_id"],d.get("actor","ADMIN"),d.get("reason","Rejected")))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
if __name__=="__main__":HTTPServer(("127.0.0.1",8792),H).serve_forever()
