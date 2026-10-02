"""Gap-audit specification for the Reads universal football engine.

This inventory intentionally separates raw/verified facts from derived labels
and narrative events. It is the ingestion roadmap used before Creator is
allowed to claim support for a concept.
"""
from __future__ import annotations

AUDIT_FAMILIES = {
 "core_identity": ["players","teams","franchises","schools","positions","aliases","biographical"],
 "roster_career": ["season_rosters","starters","depth_charts","team_history","college_history","transfers","transactions"],
 "games": ["schedules","results","box_scores","player_game_stats","team_game_stats","drives","play_by_play","scoring_events"],
 "situational": ["down_distance","field_position","score_state","red_zone","third_down","fourth_down","two_minute","overtime"],
 "season_stats": ["player_season","team_season","splits","advanced","snap_counts","participation","leaders"],
 "postseason": ["playoffs","bowls","cfp","conference_titles","super_bowls","championships"],
 "rankings": ["ap","coaches","cfp","historical_rank_at_game_time","upsets"],
 "honors": ["all_pro","pro_bowl","hof","all_america","heisman","major_awards","award_voting"],
 "draft": ["picks","trades","draft_capital","combine","career_outcomes"],
 "recruiting": ["recruits","stars","rankings","commitments","signing_classes","portal"],
 "coaching": ["head_coaches","coordinators","staffs","coaching_tree","tenure","firings","hires"],
 "money": ["contracts","salary_cap","dead_cap","franchise_tag","extensions"],
 "availability": ["injury_reports","inactive","ir","suspensions","opt_outs"],
 "venues": ["stadiums","locations","surface","weather","attendance","neutral_site"],
 "records": ["league_records","school_records","franchise_records","milestones","streaks"],
 "rules": ["rule_changes","era_boundaries","overtime_rules","schedule_format"],
 "off_field": ["legal_events","league_discipline","school_discipline","investigations","case_dispositions"],
 "culture_story": ["funny_moments","bizarre_events","iconic_quotes","celebrations","controversies","media_moments","oddities"],
 "derived": ["draft_value","bust_score","steal_score","comeback_magnitude","upset_magnitude","clutch_index",
             "dynasty_score","career_journey","what_if_context","rarity","similarity"],
}

REQUIRED_EVENT_FIELDS = (
 "event_id","event_type","subject_ids","league","event_date","title","neutral_summary",
 "source_url","source_publisher","source_date","evidence_tier","verification_status",
)

LEGAL_EVENT_FIELDS = REQUIRED_EVENT_FIELDS + (
 "jurisdiction","legal_stage","allegation_or_offense","disposition","disposition_date",
)

NARRATIVE_EVENT_FIELDS = REQUIRED_EVENT_FIELDS + (
 "story_tags","game_id","season","team_ids","player_ids","quote_exact","quote_source",
)

DERIVED_FIELDS = (
 "derived_id","metric","subject_id","value","formula_version","input_fact_ids",
 "computed_at","eligible_for_gameplay",
)

CREATOR_TARGETS = (
 "Any verified fact can feed any compatible mechanic.",
 "Multi-hop joins can traverse player/team/school/game/coach/draft/event relationships.",
 "Narrative prompts retrieve sourced event cards before question generation.",
 "Derived labels expose formula/version and never masquerade as raw facts.",
 "Sensitive events require provenance and precise status/disposition wording.",
 "Every generated answer carries evidence IDs so Creator can explain/verify it.",
)

# Highest-value missing/partial families to close first. Presence is not asserted
# here; the executable DB audit will classify PRESENT/PARTIAL/MISSING by coverage.
PRIORITY_WAVES = (
 ("wave_1_composability", ("core_identity","roster_career","games","season_stats","postseason","honors","draft","coaching")),
 ("wave_2_depth", ("situational","rankings","recruiting","availability","records","venues")),
 ("wave_3_story_engine", ("off_field","culture_story","rules","money")),
 ("wave_4_intelligence", ("derived",)),
)
