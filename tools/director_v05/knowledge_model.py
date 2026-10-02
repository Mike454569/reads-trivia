"""Universal football knowledge vocabulary for Reads Engine v0.5."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class FactKind(str, Enum):
    IDENTITY="IDENTITY"; AFFILIATION="AFFILIATION"; ROSTER="ROSTER"
    SEASON_STAT="SEASON_STAT"; GAME_STAT="GAME_STAT"; PLAY="PLAY"; DRIVE="DRIVE"; GAME_RESULT="GAME_RESULT"
    STANDING="STANDING"; RANKING="RANKING"; AWARD="AWARD"; DRAFT="DRAFT"; RECRUITING="RECRUITING"
    TRANSFER="TRANSFER"; TRANSACTION="TRANSACTION"; CONTRACT="CONTRACT"; INJURY="INJURY"; COACHING="COACHING"
    DEPTH_CHART="DEPTH_CHART"; CHAMPIONSHIP="CHAMPIONSHIP"; RIVALRY="RIVALRY"; VENUE="VENUE"; RULE_CHANGE="RULE_CHANGE"
    MILESTONE="MILESTONE"; RECORD="RECORD"; LEGAL_EVENT="LEGAL_EVENT"; DISCIPLINE="DISCIPLINE"; SUSPENSION="SUSPENSION"
    RETIREMENT="RETIREMENT"; DEATH="DEATH"; MEDIA_EVENT="MEDIA_EVENT"; DERIVED="DERIVED"

class EvidenceTier(str, Enum):
    PRIMARY="PRIMARY"; AUTHORITATIVE="AUTHORITATIVE"; REPUTABLE_MEDIA="REPUTABLE_MEDIA"; SECONDARY="SECONDARY"

@dataclass(frozen=True)
class KnowledgeFamily:
    id:str; fact_kinds:tuple[FactKind,...]; min_evidence:EvidenceTier; sensitive:bool=False; notes:str=""

KNOWLEDGE_FAMILIES=(
    KnowledgeFamily("identity_career",(FactKind.IDENTITY,FactKind.AFFILIATION,FactKind.ROSTER),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("games_pbp",(FactKind.GAME_RESULT,FactKind.GAME_STAT,FactKind.DRIVE,FactKind.PLAY),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("season_performance",(FactKind.SEASON_STAT,FactKind.STANDING,FactKind.RECORD,FactKind.MILESTONE),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("draft",(FactKind.DRAFT,),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("awards_honors",(FactKind.AWARD,FactKind.CHAMPIONSHIP),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("college_pipeline",(FactKind.RECRUITING,FactKind.TRANSFER),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("transactions_contracts",(FactKind.TRANSACTION,FactKind.CONTRACT),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("injuries_availability",(FactKind.INJURY,FactKind.SUSPENSION),EvidenceTier.REPUTABLE_MEDIA,True),
    KnowledgeFamily("coaching",(FactKind.COACHING,),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("depth_charts",(FactKind.DEPTH_CHART,),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("rivalries_history",(FactKind.RIVALRY,),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("venues",(FactKind.VENUE,),EvidenceTier.AUTHORITATIVE),
    KnowledgeFamily("rules_history",(FactKind.RULE_CHANGE,),EvidenceTier.PRIMARY),
    KnowledgeFamily("discipline_legal",(FactKind.LEGAL_EVENT,FactKind.DISCIPLINE),EvidenceTier.PRIMARY,True,
                    "Store event type/status/disposition and source; arrest or charge never implies guilt."),
    KnowledgeFamily("retirement_obituary",(FactKind.RETIREMENT,FactKind.DEATH),EvidenceTier.REPUTABLE_MEDIA,True),
    KnowledgeFamily("football_culture",(FactKind.MEDIA_EVENT,),EvidenceTier.REPUTABLE_MEDIA,False,"Documented events only; no rumor ingestion."),
    KnowledgeFamily("derived_intelligence",(FactKind.DERIVED,),EvidenceTier.AUTHORITATIVE,False,"Formula/version plus input fact IDs required."),
)

DERIVED_METRICS={
 "DRAFT_VALUE":{"inputs":("DRAFT","SEASON_STAT","GAME_STAT","AWARD","ROSTER"),"description":"Career return relative to draft capital. Bust/steal are versioned derived labels, never unsourced facts."},
 "COMEBACK_MAGNITUDE":{"inputs":("PLAY","GAME_RESULT"),"description":"Largest verified deficit overcome to win."},
 "UPSET_MAGNITUDE":{"inputs":("RANKING","GAME_RESULT"),"description":"Ranking differential for verified upset games."},
 "CAREER_JOURNEY_COMPLEXITY":{"inputs":("AFFILIATION","TRANSFER","TRANSACTION"),"description":"Verified stops and transitions."},
 "CLUTCH_INDEX":{"inputs":("PLAY","GAME_STAT"),"description":"Versioned late/close-game performance definition."},
}

SENSITIVE_GAMEPLAY_RULES={
 "LEGAL_EVENT":("Require source metadata, date, jurisdiction, event type and disposition/status.",
                "Use precise legal verbs; never turn an allegation into guilt.","Never ingest rumor/social-only claims."),
 "INJURY":("Prefer official reports/team announcements.","Preserve reported vs confirmed distinction."),
}

def universal_layer_manifest()->dict:
    return {"fact_kinds":[x.value for x in FactKind],"knowledge_families":[x.id for x in KNOWLEDGE_FAMILIES],
            "derived_metrics":sorted(DERIVED_METRICS),"sensitive_gameplay_rules":sorted(SENSITIVE_GAMEPLAY_RULES)}
