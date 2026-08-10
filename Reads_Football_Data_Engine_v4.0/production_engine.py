"""Reads v2.1 production hardening: accounts, sync, RBAC, anti-cheat, entitlements, analytics."""
from pathlib import Path
import sqlite3,json,hashlib,secrets,datetime as dt,time,uuid
ROOT=Path(__file__).parent
DB=ROOT/"reads_football_v4.0.sqlite"
def db():
    c=sqlite3.connect(DB,timeout=30);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");return c
def hid(p,*x): return p+":"+hashlib.sha256("|".join(map(str,x)).encode()).hexdigest()[:24]
def now(): return dt.datetime.now(dt.timezone.utc)
def iso(t): return t.astimezone(dt.timezone.utc).isoformat()
def ensure_account(user,email=None,provider="APP",subject=None):
    c=db();c.execute("""INSERT INTO account_identities(user_id,email_normalized,auth_provider,provider_subject)
      VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET last_login_at=CURRENT_TIMESTAMP""",
      (user,email.lower().strip() if email else None,provider,subject))
    c.execute("INSERT OR IGNORE INTO user_roles(user_id,role_id,granted_by) VALUES(?, 'PLAYER','SYSTEM')",(user,))
    c.execute("INSERT OR IGNORE INTO users_game_profile(user_id) VALUES(?)",(user,))
    c.commit();c.close();return {"user_id":user}
def create_session(user,hours=720):
    ensure_account(user);raw=secrets.token_urlsafe(32);h=hashlib.sha256(raw.encode()).hexdigest();sid=hid("SES",user,h)
    c=db();c.execute("INSERT INTO auth_sessions(session_id,user_id,token_hash,expires_at) VALUES(?,?,?,?)",(sid,user,h,iso(now()+dt.timedelta(hours=hours))));c.commit();c.close()
    return {"session_id":sid,"token":raw,"expires_at":iso(now()+dt.timedelta(hours=hours))}
def authenticate(raw):
    h=hashlib.sha256(raw.encode()).hexdigest();c=db();r=c.execute("SELECT * FROM auth_sessions WHERE token_hash=? AND revoked_at IS NULL",(h,)).fetchone();c.close()
    if not r:return None
    if dt.datetime.fromisoformat(r["expires_at"])<now():return None
    return r["user_id"]
def sync_get(user,namespace):
    c=db();r=c.execute("SELECT revision,state_json,updated_at FROM cloud_sync_state WHERE user_id=? AND namespace=?",(user,namespace)).fetchone();c.close()
    return {"revision":0,"state":{}} if not r else {"revision":r["revision"],"state":json.loads(r["state_json"]),"updated_at":r["updated_at"]}
def sync_put(user,namespace,expected_revision,state):
    c=db();r=c.execute("SELECT revision FROM cloud_sync_state WHERE user_id=? AND namespace=?",(user,namespace)).fetchone();cur=r["revision"] if r else 0
    if cur!=expected_revision:c.close();return {"status":"CONFLICT","server":sync_get(user,namespace)}
    new=cur+1;c.execute("""INSERT INTO cloud_sync_state(user_id,namespace,revision,state_json) VALUES(?,?,?,?)
      ON CONFLICT(user_id,namespace) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=CURRENT_TIMESTAMP""",(user,namespace,new,json.dumps(state,sort_keys=True)))
    c.commit();c.close();return {"status":"SYNCED","revision":new}
def has_permission(user,permission):
    c=db();rows=c.execute("""SELECT r.permissions_json FROM user_roles u JOIN role_definitions r USING(role_id) WHERE u.user_id=?""",(user,)).fetchall();c.close()
    return any("*" in (p:=json.loads(r[0])) or permission in p for r in rows)
def grant_role(actor,user,role):
    if not has_permission(actor,"*"):raise PermissionError("admin required")
    c=db();c.execute("INSERT OR IGNORE INTO user_roles VALUES(?,?,?,CURRENT_TIMESTAMP)",(user,role,actor));c.commit();c.close();return {"granted":role}
def rate_limit(bucket,limit=120,window_seconds=60):
    c=db();r=c.execute("SELECT * FROM api_rate_limits WHERE bucket_key=?",(bucket,)).fetchone();n=now()
    if not r or (n-dt.datetime.fromisoformat(r["window_started_at"])).total_seconds()>=window_seconds:
        c.execute("INSERT OR REPLACE INTO api_rate_limits VALUES(?,?,1,NULL)",(bucket,iso(n)));c.commit();c.close();return {"allowed":True,"remaining":limit-1}
    count=r["request_count"]+1;allowed=count<=limit
    c.execute("UPDATE api_rate_limits SET request_count=?,blocked_until=? WHERE bucket_key=?",(count,None if allowed else iso(n+dt.timedelta(seconds=window_seconds)),bucket));c.commit();c.close()
    return {"allowed":allowed,"remaining":max(0,limit-count)}
def issue_ranked_match(user,mode,puzzle_ids,ttl=600):
    seed=secrets.token_hex(16);token=secrets.token_urlsafe(24);commit=hashlib.sha256((seed+"|"+json.dumps(puzzle_ids,sort_keys=True)).encode()).hexdigest()
    c=db();c.execute("INSERT INTO ranked_match_tokens VALUES(?,?,?,?,?,?,NULL,?,?)",(token,user,mode,seed,iso(now()),iso(now()+dt.timedelta(seconds=ttl)),json.dumps(puzzle_ids),commit));c.commit();c.close()
    return {"match_token":token,"seed":seed,"puzzle_ids":puzzle_ids,"expires_at":iso(now()+dt.timedelta(seconds=ttl))}
def validate_ranked_submission(user,token,puzzle_ids,total_ms):
    c=db();r=c.execute("SELECT * FROM ranked_match_tokens WHERE match_token=? AND user_id=?",(token,user)).fetchone()
    signals=[]
    if not r:signals.append(("INVALID_TOKEN",5))
    else:
        if r["consumed_at"]:signals.append(("REPLAY",5))
        if dt.datetime.fromisoformat(r["expires_at"])<now():signals.append(("EXPIRED",3))
        if json.loads(r["puzzle_ids_json"])!=puzzle_ids:signals.append(("PUZZLE_SET_TAMPER",5))
        if total_ms < max(500,len(puzzle_ids)*350):signals.append(("IMPOSSIBLE_SPEED",4))
        if not signals:c.execute("UPDATE ranked_match_tokens SET consumed_at=CURRENT_TIMESTAMP WHERE match_token=?",(token,))
    for sig,sev in signals:
        c.execute("INSERT INTO anti_cheat_events VALUES(?,?,?,?,?,?,?,? ,CURRENT_TIMESTAMP,'OPEN')",
                  (hid("AC",user,token,sig,time.time_ns()),user,None,r["mode_id"] if r else None,None,sig,sev,json.dumps({"total_ms":total_ms})))
    c.commit();c.close();return {"accepted":not signals,"signals":[s[0] for s in signals]}
def tier_for(user):
    c=db();r=c.execute("""SELECT p.tier FROM user_subscriptions s JOIN subscription_products p USING(product_id)
      WHERE s.user_id=? AND s.status IN ('ACTIVE','TRIALING') ORDER BY CASE p.tier WHEN 'PLUS' THEN 2 ELSE 1 END DESC LIMIT 1""",(user,)).fetchone();c.close()
    return r[0] if r else "FREE"
def entitlement(user,key):
    c=db();o=c.execute("SELECT enabled,limit_value,expires_at FROM user_entitlement_overrides WHERE user_id=? AND entitlement_key=?",(user,key)).fetchone()
    if o and (not o["expires_at"] or dt.datetime.fromisoformat(o["expires_at"])>now()):c.close();return {"enabled":bool(o["enabled"]),"limit":o["limit_value"],"source":"override"}
    tier=tier_for(user);r=c.execute("SELECT enabled,limit_value FROM tier_entitlements WHERE tier=? AND entitlement_key=?",(tier,key)).fetchone();c.close()
    return {"enabled":bool(r["enabled"]) if r else False,"limit":r["limit_value"] if r else None,"source":tier}
def track(event_name,user=None,anonymous_id=None,surface=None,properties=None):
    eid=hid("AE",event_name,user or anonymous_id,time.time_ns());c=db();c.execute("INSERT INTO analytics_events VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)",(eid,user,anonymous_id,event_name,surface,json.dumps(properties or {},sort_keys=True)));c.commit();c.close();return eid
def build_daily_funnel(date=None):
    date=date or dt.date.today().isoformat();steps=["landing_view","game_start","game_complete","account_created","streak_extended","subscription_started"]
    c=db()
    for step in steps:
        r=c.execute("""SELECT COUNT(DISTINCT COALESCE(user_id,anonymous_id)),COUNT(*) FROM analytics_events
          WHERE event_name=? AND date(occurred_at)=?""",(step,date)).fetchone()
        c.execute("INSERT OR REPLACE INTO analytics_daily_funnel VALUES(?,?,?,?)",(date,step,r[0],r[1]))
    c.commit();rows=[dict(r) for r in c.execute("SELECT * FROM analytics_daily_funnel WHERE event_date=? ORDER BY rowid",(date,))];c.close();return rows
