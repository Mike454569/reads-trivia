"""Detect high-value story candidates in NFL play-by-play."""
from __future__ import annotations

def classify(play):
    out=[]
    y=int(play.get("yards_gained") or 0)
    pid=str(play.get("play_id") or "")
    if y>=70 and play.get("touchdown"):
        out.append(("EXPLOSIVE_TD:"+pid,"ICONIC_PLAY",["explosive_play","touchdown"],str(y)+"-yard touchdown"))
    if play.get("down")==4 and y>=25:
        out.append(("FOURTH_DOWN:"+pid,"ON_FIELD_ODDITY",["fourth_down","explosive_play"],str(y)+" yards gained on fourth down"))
    if play.get("interception") and play.get("touchdown"):
        out.append(("PICK_SIX:"+pid,"ICONIC_PLAY",["interception","defensive_touchdown"],"Interception produced a touchdown"))
    if play.get("fumble_lost") and play.get("touchdown"):
        out.append(("FUMBLE_TD:"+pid,"ON_FIELD_ODDITY",["fumble","defensive_touchdown"],"Lost-fumble play produced a touchdown"))
    if play.get("own_kickoff_recovery"):
        out.append(("ONSIDE:"+pid,"ON_FIELD_ODDITY",["onside_kick","special_teams"],"Kicking team recovered its own kickoff"))
    if play.get("wpa") is not None and abs(float(play.get("wpa") or 0))>=0.35:
        out.append(("WPA_SWING:"+pid,"ICONIC_PLAY",["wpa","game_swing"],"Single play changed win probability by at least 35 percentage points"))
    return out
