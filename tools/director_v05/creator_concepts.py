"""Creator concept contract for universal/event-driven football games."""
from __future__ import annotations

CONCEPTS = {
 "FUNNY_MOMENTS":{"families":("culture_story",),"tags":("funny","bizarre","oddity"),"sensitive":False},
 "ABSURD_STORIES":{"families":("culture_story","off_field"),"tags":("bizarre","controversy","oddity"),"sensitive":True},
 "LEGAL_HISTORY":{"families":("off_field",),"tags":("legal",),"sensitive":True},
 "LEAGUE_DISCIPLINE":{"families":("off_field",),"tags":("discipline","suspension"),"sensitive":True},
 "DRAFT_BUSTS":{"families":("draft","derived"),"metric":"bust_score","sensitive":False},
 "DRAFT_STEALS":{"families":("draft","derived"),"metric":"steal_score","sensitive":False},
 "BIGGEST_COMEBACKS":{"families":("games","situational","derived"),"metric":"comeback_magnitude","sensitive":False},
 "BIGGEST_UPSETS":{"families":("games","rankings","derived"),"metric":"upset_magnitude","sensitive":False},
 "CAREER_JOURNEYS":{"families":("roster_career","derived"),"metric":"career_journey","sensitive":False},
 "ICONIC_GAMES":{"families":("games","culture_story"),"tags":("iconic",),"sensitive":False},
 "WEIRD_RECORDS":{"families":("records","culture_story"),"tags":("rare","oddity"),"sensitive":False},
 "COACHING_CHAOS":{"families":("coaching","culture_story"),"tags":("hire","fire","controversy"),"sensitive":False},
 "CONTRACT_CHAOS":{"families":("money","transactions","culture_story"),"tags":("contract","trade","holdout"),"sensitive":False},
}

COMPATIBLE_MECHANICS = (
 "MULTIPLE_CHOICE","TRUE_FALSE","WHO_AM_I","THREE_CLUES","TIMELINE","MATCHING",
 "SORTING","HIGHER_LOWER","ELIMINATION","BRACKET","COMMON_LINK","BINGO",
 "RISK_REWARD","SURVIVAL","DAILY","ENDLESS",
)

def concept(name:str)->dict:
    return dict(CONCEPTS[name.upper()])
