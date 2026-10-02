"""Refresh verified NFL trade events from nflverse/nfldata."""
from __future__ import annotations
import csv,io,urllib.request
from .event_ingest import upsert_event
URL="https://raw.githubusercontent.com/nflverse/nfldata/master/data/trades.csv"

def populate_nfl_trades(conn, *, timeout=60):
    req=urllib.request.Request(URL,headers={"User-Agent":"Reads-Football-Data-Refresh/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        text=resp.read().decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(text)))
    count=0
    for row in rows:
        tid=(row.get("trade_id") or "").strip()
        season=(row.get("season") or "").strip()
        date=(row.get("trade_date") or "").strip()
        gave=(row.get("gave") or "").strip()
        received=(row.get("received") or "").strip()
        if not tid or not season or not gave: continue
        subjects=[{"subject_type":"NFL_TEAM","subject_id":gave,"role":"gave"}]
        if received: subjects.append({"subject_type":"NFL_TEAM","subject_id":received,"role":"received"})
        desc=(row.get("gave_desc") or row.get("gave_description") or row.get("gave_value") or "").strip()
        upsert_event(conn,{"event_type":"TRADE","league":"NFL","event_date":date or season+"-01-01",
          "title":"NFL trade "+tid,"neutral_summary":desc or "Verified NFL trade component.",
          "source_url":"https://github.com/nflverse/nfldata/blob/master/data/trades.csv",
          "source_publisher":"nflverse / Lee Sharpe / Pro Football Reference","evidence_tier":"AUTHORITATIVE",
          "verification_status":"VERIFIED","subjects":subjects,"tags":["trade","transaction"],"sensitive":False})
        count+=1
    return {"downloaded":len(rows),"inserted":count}
