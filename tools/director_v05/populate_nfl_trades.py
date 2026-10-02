"""Populate verified NFL trade events from nflverse's PFR/Lee Sharpe feed."""
from __future__ import annotations
import csv,io,urllib.request
from collections import defaultdict
from .event_ingest import upsert_event
URL="https://raw.githubusercontent.com/nflverse/nfldata/master/data/trades.csv"

def populate_nfl_trades(conn, *, timeout=60):
    req=urllib.request.Request(URL,headers={"User-Agent":"Reads-Football-Data-Refresh/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        rows=list(csv.DictReader(io.StringIO(resp.read().decode("utf-8-sig"))))
    groups=defaultdict(list)
    for row in rows:
        if (row.get("trade_id") or "").strip():
            groups[(row["trade_id"].strip(),(row.get("trade_date") or "").strip(),(row.get("season") or "").strip())].append(row)
    inserted=0
    for (tid,date,season),parts in groups.items():
        teams=sorted({(x.get("gave") or "").strip() for x in parts}|{(x.get("received") or "").strip() for x in parts})
        teams=[x for x in teams if x]
        players=[]; picks=[]
        for x in parts:
            name=(x.get("pfr_name") or "").strip()
            pick=(x.get("pick_number") or "").strip()
            rnd=(x.get("pick_round") or "").strip()
            ps=(x.get("pick_season") or "").strip()
            if name and not ps: players.append(name)
            if ps: picks.append(" ".join(v for v in [ps,("R"+rnd if rnd else ""),("#"+pick if pick else "")] if v))
        bits=[]
        if players: bits.append("players: "+", ".join(sorted(set(players))))
        if picks: bits.append("draft assets: "+", ".join(sorted(set(picks))))
        subjects=[{"subject_type":"NFL_TEAM","subject_id":t,"role":"trade_party"} for t in teams]
        for x in parts:
            pid=(x.get("pfr_id") or "").strip(); ps=(x.get("pick_season") or "").strip()
            if pid and not ps: subjects.append({"subject_type":"NFL_PLAYER","subject_id":pid,"role":"traded_player"})
        upsert_event(conn,{"event_type":"TRADE","league":"NFL","event_date":date or (season+"-01-01" if season else None),
          "title":"NFL trade "+tid,"neutral_summary":"; ".join(bits) or "Verified NFL trade.",
          "source_url":"https://github.com/nflverse/nfldata/blob/master/data/trades.csv",
          "source_publisher":"nflverse / Lee Sharpe / Pro Football Reference","evidence_tier":"AUTHORITATIVE",
          "verification_status":"VERIFIED","subjects":subjects,"tags":["trade","transaction"],"sensitive":False})
        inserted+=1
    return {"component_rows":len(rows),"trade_events":inserted}
