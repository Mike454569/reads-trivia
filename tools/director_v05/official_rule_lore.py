"""Curated official football rule-change facts for RULE_ODDITY lore.

Only official governing-body sources belong here. Proposed changes are excluded
unless the source explicitly says they were approved/adopted.
"""
from __future__ import annotations

from .event_ingest import upsert_event

RULE_CHANGES = [
    {
        "event_id":"rule_nfl_2026_onside_anytime",
        "league":"NFL",
        "event_date":"2026-01-01",
        "title":"NFL allows declared onside kicks at any time",
        "neutral_summary":"Beginning with the 2026 NFL rules, a kicking team may declare an onside kick at any time during the game.",
        "source_url":"https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
        "source_publisher":"NFL Football Operations",
        "rule_ref":"6-1-6",
        "tags":["rule","onside_kick","kickoff"],
    },
    {
        "event_id":"rule_nfl_2026_kickoff_alignment",
        "league":"NFL",
        "event_date":"2026-01-01",
        "title":"NFL changes receiving-team kickoff alignment",
        "neutral_summary":"The 2026 NFL rules modify alignment requirements for receiving-team players in the setup zone on a kickoff or safety kick.",
        "source_url":"https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
        "source_publisher":"NFL Football Operations",
        "rule_ref":"6-1-3",
        "tags":["rule","kickoff","alignment"],
    },
    {
        "event_id":"rule_nfl_2026_touchback_50",
        "league":"NFL",
        "event_date":"2026-01-01",
        "title":"NFL changes touchback spot for kicks from the 50",
        "neutral_summary":"The 2026 NFL rules modify the dead-ball spot after a touchback when the kickoff is from the 50-yard line.",
        "source_url":"https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
        "source_publisher":"NFL Football Operations",
        "rule_ref":"6-1-5",
        "tags":["rule","kickoff","touchback"],
    },
    {
        "event_id":"rule_nfl_2026_disqualification_consult",
        "league":"NFL",
        "event_date":"2026-01-01",
        "title":"NFL expands league-office consultation on disqualifications",
        "neutral_summary":"The 2026 NFL rules permit league personnel to consult with on-field officials on potential disqualifications for flagrant football and non-football acts, even when no flag was called on the field.",
        "source_url":"https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
        "source_publisher":"NFL Football Operations",
        "rule_ref":"19-2",
        "tags":["rule","officiating","disqualification"],
    },
    {
        "event_id":"rule_ncaa_2026_targeting_trial",
        "league":"CFB",
        "event_date":"2026-03-19",
        "title":"Division I adopts 2026 targeting repeat-offense trial",
        "neutral_summary":"For the 2026 Division I season, a first targeting disqualification does not by itself require missing the first half of the next game; a second requires missing that next first half, and a third requires missing the entire next game.",
        "source_url":"https://www.ncaa.org/news/media-center-changes-to-penalty-structure-for-targeting-in-di-football-approved/",
        "source_publisher":"NCAA",
        "rule_ref":"2026 Division I targeting trial",
        "tags":["rule","targeting","discipline","officiating"],
    },
]


def populate_official_rule_lore(conn):
    inserted = 0
    for rule in RULE_CHANGES:
        upsert_event(conn, {
            "event_id": rule["event_id"],
            "event_type": "RULE_ODDITY",
            "league": rule["league"],
            "event_date": rule["event_date"],
            "title": rule["title"],
            "neutral_summary": rule["neutral_summary"],
            "source_url": rule["source_url"],
            "source_publisher": rule["source_publisher"],
            "evidence_tier": "PRIMARY",
            "verification_status": "VERIFIED",
            "subjects": [],
            "tags": rule["tags"] + ["official_rule_change", rule["rule_ref"].casefold()],
            "sensitive": False,
        })
        inserted += 1
    conn.commit()
    return {"events": inserted, "source": "OFFICIAL_RULES"}
