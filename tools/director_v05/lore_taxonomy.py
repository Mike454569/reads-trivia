"""Broad football-lore taxonomy: anything verifiable can become trivia."""
from __future__ import annotations

EVENT_FAMILIES={
 "ON_FIELD_ODDITY":{"tags":("bizarre_play","funny","oddity"),"sensitive":False},
 "CELEBRATION":{"tags":("celebration","funny"),"sensitive":False},
 "PRESS_CONFERENCE":{"tags":("quote","press_conference","viral"),"sensitive":False},
 "MASCOT_FAN_MOMENT":{"tags":("mascot","fan","funny"),"sensitive":False},
 "WEATHER_CHAOS":{"tags":("weather","snow","rain","heat","wind"),"sensitive":False},
 "RULE_ODDITY":{"tags":("rule","penalty","officiating"),"sensitive":False},
 "ICONIC_PLAY":{"tags":("iconic","play"),"sensitive":False},
 "UPSET":{"tags":("upset",),"sensitive":False},
 "COMEBACK":{"tags":("comeback",),"sensitive":False},
 "RECORD_EVENT":{"tags":("record","milestone","rare"),"sensitive":False},
 "TRADE":{"tags":("trade","transaction"),"sensitive":False},
 "SIGNING_RELEASE":{"tags":("signing","release","waiver","transaction"),"sensitive":False},
 "CONTRACT":{"tags":("contract","money","holdout"),"sensitive":False},
 "COACHING_MOVE":{"tags":("coach","hire","fire","resignation"),"sensitive":False},
 "RECRUITING":{"tags":("recruiting","commitment","flip"),"sensitive":False},
 "TRANSFER":{"tags":("transfer","portal"),"sensitive":False},
 "INJURY":{"tags":("injury","availability"),"sensitive":True},
 "LEAGUE_DISCIPLINE":{"tags":("discipline","suspension","fine"),"sensitive":True},
 "LEGAL_EVENT":{"tags":("legal","arrest","charge","court"),"sensitive":True},
 "CONTROVERSY":{"tags":("controversy",),"sensitive":True},
 "OFF_FIELD_ODDITY":{"tags":("off_field","bizarre","oddity"),"sensitive":False},
 "HISTORICAL_MILESTONE":{"tags":("history","milestone"),"sensitive":False},
}

TRIVIA_DIMENSIONS=(
 "WHO","WHAT","WHEN","WHERE","TEAM","SCHOOL","OPPONENT","SEASON","ORDER",
 "MAGNITUDE","CONNECTION","BEFORE_AFTER","TRUE_FALSE","COMMON_LINK",
)

def family(name):
    return dict(EVENT_FAMILIES[name.upper()])
