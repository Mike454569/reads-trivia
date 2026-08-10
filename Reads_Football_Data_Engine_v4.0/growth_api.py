"""Reads v2.2 Growth API."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
import json
import growth_engine as G
class H(BaseHTTPRequestHandler):
    def sendj(self,o,code=200):
        b=json.dumps(o).encode();self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def body(self):
        n=int(self.headers.get("Content-Length","0"));return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        u=urlparse(self.path);q=parse_qs(u.query)
        try:
            if u.path=="/v2.2/seo/page":
                page=G.render_seo_page(q["slug"][0]);return self.sendj(page or {"error":"not_found"},200 if page else 404)
            if u.path=="/v2.2/growth/metrics":return self.sendj(G.build_daily_growth_metrics(q.get("date",[None])[0]))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
    def do_POST(self):
        d=self.body()
        try:
            if self.path=="/v2.2/referral":return self.sendj(G.create_referral(d["user_id"],d.get("campaign","organic")))
            if self.path=="/v2.2/referral/attribute":return self.sendj(G.attribute_referral(d["referral_code"],d.get("user_id"),d.get("anonymous_id"),d.get("source","share"),d.get("medium","referral"),d.get("object_type"),d.get("object_id")))
            if self.path=="/v2.2/share":return self.sendj(G.create_share(d.get("user_id"),d["share_type"],d["object_type"],d["object_id"],d["headline"],d.get("body"),d.get("visual")))
            if self.path=="/v2.2/share/daily":return self.sendj(G.daily_share(d.get("user_id"),d["slate_date"],d["score"],d.get("streak"),d.get("results")))
            if self.path=="/v2.2/share/challenge":return self.sendj(G.challenge_share(d["user_id"],d["challenge_id"],d.get("headline","Think you can beat me?")))
            if self.path=="/v2.2/track":return self.sendj({"event_id":G.track(d["event_name"],d.get("user_id"),d.get("anonymous_id"),d.get("share_code"),d.get("referral_code"),d.get("campaign_id"),d.get("object_type"),d.get("object_id"),d.get("properties"))})
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
if __name__=="__main__":ThreadingHTTPServer(("127.0.0.1",8794),H).serve_forever()
