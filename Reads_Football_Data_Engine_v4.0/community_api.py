"""Reads v1.9 community JSON API."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlparse,parse_qs
import json
import community_engine as C

class H(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj).encode();self.send_response(code);self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def body(self):
        n=int(self.headers.get("Content-Length","0"));return json.loads(self.rfile.read(n) or b"{}")
    def do_GET(self):
        u=urlparse(self.path);q=parse_qs(u.query)
        try:
            if u.path=="/v1/community/trending":return self.sendj(C.trending(int(q.get("limit",[20])[0])))
            if u.path=="/v1/community/creators":return self.sendj(C.creator_leaderboard(int(q.get("limit",[20])[0])))
            if u.path=="/v1/community/following":return self.sendj(C.following_feed(q["user"][0],int(q.get("limit",[30])[0])))
            if u.path=="/v1/community/saved":return self.sendj(C.saved_games(q["user"][0],int(q.get("limit",[100])[0])))
            if u.path=="/v1/community/creator":return self.sendj(C.creator_profile(q["user"][0]))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)
    def do_POST(self):
        d=self.body()
        try:
            if self.path=="/v1/community/creator":return self.sendj(C.create_creator(d["user_id"],d["handle"],d.get("display_name"),d.get("bio")))
            if self.path=="/v1/community/create":return self.sendj(C.create_from_description(d["user_id"],d["title"],d.get("description"),d["game_description"],d.get("preview_limit",12),d.get("tags")))
            if self.path=="/v1/community/review":return self.sendj(C.submit_for_review(d["user_id"],d["community_game_id"],d.get("visibility","PUBLIC")))
            if self.path=="/v1/community/moderate":return self.sendj(C.moderate(d["community_game_id"],d["action"],d.get("moderator_user_id","SYSTEM"),d.get("reason")))
            if self.path=="/v1/community/publish":return self.sendj(C.publish(d["user_id"],d["community_game_id"],d.get("puzzle_limit",250)))
            if self.path=="/v1/community/like":return self.sendj(C.like(d["user_id"],d["community_game_id"],d.get("enabled",True)))
            if self.path=="/v1/community/save":return self.sendj(C.save(d["user_id"],d["community_game_id"],d.get("enabled",True)))
            if self.path=="/v1/community/follow":return self.sendj(C.follow(d["user_id"],d["creator_user_id"],d.get("enabled",True)))
            if self.path=="/v1/community/play/start":return self.sendj(C.start_play(d["community_game_id"],d.get("user_id")))
            if self.path=="/v1/community/play/complete":return self.sendj(C.complete_play(d["play_id"],d["correct_count"],d["total_response_ms"]))
            if self.path=="/v1/community/comment":return self.sendj(C.comment(d["user_id"],d["community_game_id"],d["body"]))
            if self.path=="/v1/community/report":return self.sendj(C.report(d.get("user_id"),d["community_game_id"],d["reason_code"],d.get("detail")))
            if self.path=="/v1/community/share":return self.sendj(C.share(d["user_id"],d["community_game_id"]))
            if self.path=="/v1/community/remix":return self.sendj(C.remix(d["user_id"],d["parent_game_id"],d.get("title")))
            return self.sendj({"error":"not_found"},404)
        except Exception as e:return self.sendj({"error":str(e)},400)

if __name__=="__main__":HTTPServer(("127.0.0.1",8789),H).serve_forever()
