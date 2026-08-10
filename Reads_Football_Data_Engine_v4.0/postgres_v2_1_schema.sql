-- Reads Football v2.1 PostgreSQL production schema

BEGIN;

CREATE TABLE IF NOT EXISTS "accepted_answers" (
  "answer_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "canonical_answer" TEXT NOT NULL,
  "accepted_answer" TEXT NOT NULL,
  "answer_class" TEXT NOT NULL,
  PRIMARY KEY ("answer_type", "entity_id", "accepted_answer")
);

CREATE TABLE IF NOT EXISTS "account_identities" (
  "user_id" TEXT,
  "email_normalized" TEXT,
  "auth_provider" TEXT NOT NULL DEFAULT 'APP',
  "provider_subject" TEXT,
  "account_status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "last_login_at" TEXT,
  PRIMARY KEY ("user_id")
);

CREATE TABLE IF NOT EXISTS "achievements" (
  "achievement_id" TEXT,
  "name" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "rule_json" TEXT NOT NULL,
  "xp_reward" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("achievement_id")
);

CREATE TABLE IF NOT EXISTS "admin_alerts" (
  "alert_id" TEXT,
  "severity" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "detail" TEXT,
  "object_type" TEXT,
  "object_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "resolved_at" TEXT,
  PRIMARY KEY ("alert_id")
);

CREATE TABLE IF NOT EXISTS "analytics_daily_funnel" (
  "event_date" TEXT NOT NULL,
  "step_key" TEXT NOT NULL,
  "users" BIGINT NOT NULL DEFAULT 0,
  "events" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("event_date", "step_key")
);

CREATE TABLE IF NOT EXISTS "analytics_events" (
  "event_id" TEXT,
  "user_id" TEXT,
  "anonymous_id" TEXT,
  "event_name" TEXT NOT NULL,
  "surface" TEXT,
  "properties_json" TEXT NOT NULL DEFAULT '{}',
  "occurred_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id")
);

CREATE TABLE IF NOT EXISTS "anti_cheat_events" (
  "anti_cheat_id" TEXT,
  "user_id" TEXT,
  "session_id" TEXT,
  "mode_id" TEXT,
  "puzzle_id" TEXT,
  "signal_type" TEXT NOT NULL,
  "severity" BIGINT NOT NULL DEFAULT 1,
  "evidence_json" TEXT NOT NULL DEFAULT '{}',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "review_status" TEXT NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY ("anti_cheat_id")
);

CREATE TABLE IF NOT EXISTS "api_rate_limits" (
  "bucket_key" TEXT,
  "window_started_at" TEXT NOT NULL,
  "request_count" BIGINT NOT NULL DEFAULT 0,
  "blocked_until" TEXT,
  PRIMARY KEY ("bucket_key")
);

CREATE TABLE IF NOT EXISTS "auth_sessions" (
  "session_id" TEXT,
  "user_id" TEXT NOT NULL,
  "token_hash" TEXT NOT NULL,
  "issued_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "expires_at" TEXT NOT NULL,
  "revoked_at" TEXT,
  "ip_hash" TEXT,
  "user_agent_hash" TEXT,
  PRIMARY KEY ("session_id")
);

CREATE TABLE IF NOT EXISTS "backup_registry" (
  "backup_id" TEXT,
  "backup_type" TEXT NOT NULL,
  "database_version" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "path" TEXT NOT NULL,
  "sha256" TEXT NOT NULL,
  "size_bytes" BIGINT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'VERIFIED',
  "notes" TEXT,
  PRIMARY KEY ("backup_id")
);

CREATE TABLE IF NOT EXISTS "canonical_cfb_players" (
  "cfb_player_id" TEXT,
  "espn_athlete_id" TEXT,
  "display_name" TEXT NOT NULL,
  "first_name" TEXT,
  "last_name" TEXT,
  "height_in" BIGINT,
  "weight_lb" BIGINT,
  "hometown_city" TEXT,
  "hometown_state" TEXT,
  "hometown_country" TEXT,
  "headshot_url" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  "source_id" TEXT NOT NULL DEFAULT 'SPORTSDATAVERSE_CFB',
  PRIMARY KEY ("cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "canonical_players" (
  "player_id" TEXT,
  "gsis_id" TEXT,
  "pfr_id" TEXT,
  "display_name" TEXT NOT NULL,
  "birth_date" TEXT,
  "height_in" BIGINT,
  "weight_lb" BIGINT,
  "primary_position" TEXT,
  "primary_school_id" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'INCOMPLETE',
  "source_id" TEXT,
  PRIMARY KEY ("player_id")
);

CREATE TABLE IF NOT EXISTS "canonical_roster_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "player_id" TEXT NOT NULL,
  "jersey_number" BIGINT,
  "position" TEXT,
  "roster_status" TEXT,
  "school_id" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'INCOMPLETE',
  "source_id" TEXT,
  "games" BIGINT,
  "starts" BIGINT,
  "years_experience" BIGINT,
  "av" DOUBLE PRECISION,
  PRIMARY KEY ("season", "team_code", "player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_award_facts" (
  "award_fact_id" TEXT,
  "award_id" TEXT NOT NULL,
  "award_name" TEXT NOT NULL,
  "award_year" BIGINT NOT NULL,
  "cfb_player_id" TEXT,
  "player_name" TEXT,
  "school_id" TEXT,
  "school_name" TEXT,
  "source_tab" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_FROM_CFB_MASTER',
  PRIMARY KEY ("award_fact_id")
);

CREATE TABLE IF NOT EXISTS "cfb_awards" (
  "award_id" TEXT NOT NULL,
  "award_name" TEXT NOT NULL,
  "award_year" BIGINT NOT NULL,
  "cfb_player_id" TEXT,
  "player_name" TEXT,
  "school_id" TEXT,
  "school_name" TEXT,
  "source_tab" TEXT
);

CREATE TABLE IF NOT EXISTS "cfb_champion_school_links" (
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "school_name" TEXT NOT NULL,
  "coach_raw" TEXT,
  "notes" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_FROM_CFB_MASTER',
  PRIMARY KEY ("season", "school_id")
);

CREATE TABLE IF NOT EXISTS "cfb_champions" (
  "season" BIGINT,
  "champion_raw" TEXT,
  "coach_raw" TEXT,
  "notes" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "cfb_coach_school_links" (
  "cfb_coach_id" TEXT NOT NULL,
  "school_id" TEXT NOT NULL,
  "context" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_FROM_CFB_MASTER',
  PRIMARY KEY ("cfb_coach_id", "school_id")
);

CREATE TABLE IF NOT EXISTS "cfb_coaches" (
  "cfb_coach_id" TEXT,
  "coach_name" TEXT NOT NULL,
  "school_context" TEXT,
  "source_contexts" TEXT,
  "first_year" BIGINT,
  "last_year" BIGINT,
  "status" TEXT,
  PRIMARY KEY ("cfb_coach_id")
);

CREATE TABLE IF NOT EXISTS "cfb_game_team_meta" (
  "game_id" TEXT NOT NULL,
  "school_id" TEXT NOT NULL,
  "school_name" TEXT NOT NULL,
  "is_home" BIGINT NOT NULL,
  "division" TEXT,
  "conference" TEXT,
  PRIMARY KEY ("game_id", "school_id")
);

CREATE TABLE IF NOT EXISTS "cfb_games_canonical" (
  "game_id" TEXT,
  "season" BIGINT NOT NULL,
  "week" BIGINT,
  "game_date" TEXT,
  "home_school_id" TEXT,
  "away_school_id" TEXT,
  "home_score" BIGINT,
  "away_score" BIGINT,
  "stadium_name" TEXT,
  "conference_game" BIGINT,
  "verification_status" TEXT NOT NULL DEFAULT 'INCOMPLETE',
  "source_id" TEXT,
  PRIMARY KEY ("game_id")
);

CREATE TABLE IF NOT EXISTS "cfb_identity_links" (
  "legacy_cfb_player_id" TEXT NOT NULL,
  "canonical_cfb_player_id" TEXT NOT NULL,
  "match_rule" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL,
  PRIMARY KEY ("legacy_cfb_player_id", "canonical_cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_player_school_links" (
  "cfb_player_id" TEXT NOT NULL,
  "school_id" TEXT NOT NULL,
  "source_context" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_FROM_CFB_MASTER',
  PRIMARY KEY ("cfb_player_id", "school_id")
);

CREATE TABLE IF NOT EXISTS "cfb_player_season_stats_real" (
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "cfb_player_id" TEXT NOT NULL,
  "player_name" TEXT NOT NULL,
  "conference" TEXT,
  "completions" BIGINT NOT NULL DEFAULT 0,
  "passing_yards" BIGINT NOT NULL DEFAULT 0,
  "passing_tds" BIGINT NOT NULL DEFAULT 0,
  "interceptions_thrown" BIGINT NOT NULL DEFAULT 0,
  "rush_attempts" BIGINT NOT NULL DEFAULT 0,
  "rushing_yards" BIGINT NOT NULL DEFAULT 0,
  "rushing_tds" BIGINT NOT NULL DEFAULT 0,
  "receptions" BIGINT NOT NULL DEFAULT 0,
  "receiving_yards" BIGINT NOT NULL DEFAULT 0,
  "receiving_tds" BIGINT NOT NULL DEFAULT 0,
  "defensive_interceptions" BIGINT NOT NULL DEFAULT 0,
  "sacks" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "forced_fumbles" BIGINT NOT NULL DEFAULT 0,
  "fumble_recoveries" BIGINT NOT NULL DEFAULT 0,
  "pass_breakups" BIGINT NOT NULL DEFAULT 0,
  "field_goals_attempted" BIGINT NOT NULL DEFAULT 0,
  "field_goals_made" BIGINT NOT NULL DEFAULT 0,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_DERIVED',
  "source_id" TEXT NOT NULL DEFAULT 'SPORTSDATAVERSE_CFB',
  PRIMARY KEY ("season", "school_id", "cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_players" (
  "cfb_player_id" TEXT,
  "player_name" TEXT NOT NULL,
  "first_year" BIGINT,
  "last_year" BIGINT,
  "school_names" TEXT,
  "school_ids" TEXT,
  "contexts" TEXT,
  "status" TEXT,
  PRIMARY KEY ("cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_rivalries" (
  "rivalry_id" TEXT,
  "matchup" TEXT,
  "school_a_id" TEXT,
  "school_a" TEXT,
  "school_b_id" TEXT,
  "school_b" TEXT,
  "nickname" TEXT,
  "first_meeting" TEXT,
  "total_meetings" TEXT,
  "series_record" TEXT,
  "trophy" TEXT,
  "fun_fact" TEXT,
  PRIMARY KEY ("rivalry_id")
);

CREATE TABLE IF NOT EXISTS "cfb_roster_seasons_real" (
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "cfb_player_id" TEXT NOT NULL,
  "jersey_number" BIGINT,
  "class_year" TEXT,
  "position" TEXT,
  "height_in" BIGINT,
  "weight_lb" BIGINT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  "source_id" TEXT NOT NULL DEFAULT 'SPORTSDATAVERSE_CFB',
  PRIMARY KEY ("season", "school_id", "cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_school_seasons" (
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "school_name" TEXT NOT NULL,
  "division" TEXT,
  "conference" TEXT,
  "wins" BIGINT NOT NULL DEFAULT 0,
  "losses" BIGINT NOT NULL DEFAULT 0,
  "ties" BIGINT NOT NULL DEFAULT 0,
  "games" BIGINT NOT NULL DEFAULT 0,
  "points_for" BIGINT NOT NULL DEFAULT 0,
  "points_against" BIGINT NOT NULL DEFAULT 0,
  "point_diff" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("season", "school_id")
);

CREATE TABLE IF NOT EXISTS "cfb_stadium_usage" (
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "stadium_name" TEXT NOT NULL,
  "home_games" BIGINT NOT NULL,
  PRIMARY KEY ("season", "school_id", "stadium_name")
);

CREATE TABLE IF NOT EXISTS "cfb_team_fact_entities" (
  "school_id" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "fact_key" TEXT NOT NULL,
  "fact_value" TEXT,
  "source_sheet" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_FROM_CFB_MASTER',
  PRIMARY KEY ("school_id", "category", "fact_key")
);

CREATE TABLE IF NOT EXISTS "cfb_transfer_summary" (
  "cfb_player_id" TEXT,
  "display_name" TEXT NOT NULL,
  "first_school_id" TEXT,
  "last_school_id" TEXT,
  "school_count" BIGINT NOT NULL,
  "season_count" BIGINT NOT NULL,
  "transfer_count" BIGINT NOT NULL,
  "first_season" BIGINT,
  "last_season" BIGINT,
  "path_json" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL DEFAULT 'DERIVED_SOURCE_BACKED',
  PRIMARY KEY ("cfb_player_id")
);

CREATE TABLE IF NOT EXISTS "cfb_transfer_summary_v17" (
  "cfb_player_id" TEXT,
  "display_name" TEXT,
  "school_count" TEXT,
  "first_season" TEXT,
  "last_season" TEXT,
  "schools" TEXT
);

CREATE TABLE IF NOT EXISTS "challenge_results" (
  "challenge_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "correct_count" BIGINT NOT NULL DEFAULT 0,
  "total_response_ms" BIGINT NOT NULL DEFAULT 0,
  "score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "completed_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("challenge_id", "user_id")
);

CREATE TABLE IF NOT EXISTS "challenges" (
  "challenge_id" TEXT,
  "creator_user_id" TEXT NOT NULL,
  "opponent_user_id" TEXT,
  "mode_id" TEXT NOT NULL,
  "seed" TEXT NOT NULL,
  "puzzle_ids_json" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "expires_at" TEXT,
  "completed_at" TEXT,
  PRIMARY KEY ("challenge_id")
);

CREATE TABLE IF NOT EXISTS "cloud_sync_state" (
  "user_id" TEXT NOT NULL,
  "namespace" TEXT NOT NULL,
  "revision" BIGINT NOT NULL DEFAULT 0,
  "state_json" TEXT NOT NULL DEFAULT '{}',
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "namespace")
);

CREATE TABLE IF NOT EXISTS "coach_game_assignments" (
  "game_id" TEXT NOT NULL,
  "team_code" TEXT NOT NULL,
  "side" TEXT NOT NULL,
  "coach_id" TEXT NOT NULL,
  "opponent_team" TEXT,
  "is_home" BIGINT NOT NULL,
  "season" BIGINT NOT NULL,
  PRIMARY KEY ("game_id", "team_code", "coach_id")
);

CREATE TABLE IF NOT EXISTS "coach_team_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "coach_id" TEXT NOT NULL,
  "coach_name" TEXT NOT NULL,
  "games_observed" BIGINT NOT NULL,
  "first_game_date" TEXT,
  "last_game_date" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("season", "team_code", "coach_id")
);

CREATE TABLE IF NOT EXISTS "coaches" (
  "coach_id" TEXT,
  "coach_name" TEXT NOT NULL,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("coach_id")
);

CREATE TABLE IF NOT EXISTS "community_game_comments" (
  "comment_id" TEXT,
  "community_game_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'VISIBLE',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("comment_id")
);

CREATE TABLE IF NOT EXISTS "community_game_likes" (
  "community_game_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("community_game_id", "user_id")
);

CREATE TABLE IF NOT EXISTS "community_game_metrics" (
  "community_game_id" TEXT,
  "impressions" BIGINT NOT NULL DEFAULT 0,
  "plays" BIGINT NOT NULL DEFAULT 0,
  "completions" BIGINT NOT NULL DEFAULT 0,
  "likes" BIGINT NOT NULL DEFAULT 0,
  "saves" BIGINT NOT NULL DEFAULT 0,
  "comments" BIGINT NOT NULL DEFAULT 0,
  "reports" BIGINT NOT NULL DEFAULT 0,
  "avg_score" DOUBLE PRECISION,
  "avg_completion_ms" DOUBLE PRECISION,
  "trending_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "quality_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("community_game_id")
);

CREATE TABLE IF NOT EXISTS "community_game_plays" (
  "play_id" TEXT,
  "community_game_id" TEXT NOT NULL,
  "user_id" TEXT,
  "started_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "completed_at" TEXT,
  "correct_count" BIGINT,
  "puzzle_count" BIGINT,
  "total_response_ms" BIGINT,
  "score" DOUBLE PRECISION,
  "metadata_json" TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY ("play_id")
);

CREATE TABLE IF NOT EXISTS "community_game_puzzles" (
  "community_game_id" TEXT NOT NULL,
  "ordinal" BIGINT NOT NULL,
  "puzzle_id" TEXT NOT NULL,
  "payload_override_json" TEXT,
  PRIMARY KEY ("community_game_id", "ordinal")
);

CREATE TABLE IF NOT EXISTS "community_game_remixes" (
  "child_game_id" TEXT,
  "parent_game_id" TEXT NOT NULL,
  "remixer_user_id" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("child_game_id")
);

CREATE TABLE IF NOT EXISTS "community_game_reports" (
  "report_id" TEXT,
  "community_game_id" TEXT NOT NULL,
  "reporter_user_id" TEXT,
  "reason_code" TEXT NOT NULL,
  "detail" TEXT,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "resolved_at" TEXT,
  "resolution_note" TEXT,
  PRIMARY KEY ("report_id")
);

CREATE TABLE IF NOT EXISTS "community_game_saves" (
  "community_game_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("community_game_id", "user_id")
);

CREATE TABLE IF NOT EXISTS "community_games" (
  "community_game_id" TEXT,
  "creator_user_id" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "competition_id" TEXT,
  "mechanic" TEXT NOT NULL,
  "source_spec_id" TEXT,
  "source_template_id" TEXT,
  "visibility" TEXT NOT NULL DEFAULT 'PRIVATE',
  "moderation_status" TEXT NOT NULL DEFAULT 'DRAFT',
  "publish_status" TEXT NOT NULL DEFAULT 'DRAFT',
  "difficulty_label" TEXT,
  "estimated_puzzle_count" BIGINT NOT NULL DEFAULT 0,
  "cover_text" TEXT,
  "tags_json" TEXT NOT NULL DEFAULT '[]',
  "rules_json" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "published_at" TEXT,
  PRIMARY KEY ("community_game_id")
);

CREATE TABLE IF NOT EXISTS "community_share_links" (
  "share_code" TEXT,
  "community_game_id" TEXT NOT NULL,
  "created_by" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "expires_at" TEXT,
  "click_count" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("share_code")
);

CREATE TABLE IF NOT EXISTS "competitions" (
  "competition_id" TEXT,
  "sport" TEXT NOT NULL,
  "level" TEXT NOT NULL,
  "display_name" TEXT NOT NULL,
  "governing_body" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("competition_id")
);

CREATE TABLE IF NOT EXISTS "competitive_seasons" (
  "season_id" TEXT,
  "name" TEXT NOT NULL,
  "starts_at" TEXT NOT NULL,
  "ends_at" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'PLANNED',
  PRIMARY KEY ("season_id")
);

CREATE TABLE IF NOT EXISTS "creator_follows" (
  "follower_user_id" TEXT NOT NULL,
  "creator_user_id" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("follower_user_id", "creator_user_id")
);

CREATE TABLE IF NOT EXISTS "creator_notifications" (
  "notification_id" TEXT,
  "user_id" TEXT NOT NULL,
  "notification_type" TEXT NOT NULL,
  "actor_user_id" TEXT,
  "community_game_id" TEXT,
  "message" TEXT NOT NULL,
  "read_at" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("notification_id")
);

CREATE TABLE IF NOT EXISTS "creator_profiles" (
  "user_id" TEXT,
  "handle" TEXT,
  "display_name" TEXT,
  "bio" TEXT,
  "avatar_url" TEXT,
  "is_verified" BIGINT NOT NULL DEFAULT 0,
  "creator_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "follower_count" BIGINT NOT NULL DEFAULT 0,
  "following_count" BIGINT NOT NULL DEFAULT 0,
  "published_count" BIGINT NOT NULL DEFAULT 0,
  "total_plays" BIGINT NOT NULL DEFAULT 0,
  "total_likes" BIGINT NOT NULL DEFAULT 0,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id")
);

CREATE TABLE IF NOT EXISTS "cross_league_identity_bridge" (
  "bridge_id" TEXT,
  "cfb_player_id" TEXT,
  "nfl_player_key" TEXT,
  "player_name" TEXT,
  "school_id" TEXT,
  "school_name" TEXT,
  "cfb_evidence_year" BIGINT,
  "nfl_draft_year" BIGINT,
  "nfl_draft_team" TEXT,
  "nfl_position" TEXT,
  "match_rule" TEXT,
  "confidence" DOUBLE PRECISION,
  "production_safe" BIGINT,
  "verification_status" TEXT,
  "evidence_json" TEXT,
  PRIMARY KEY ("bridge_id")
);

CREATE TABLE IF NOT EXISTS "cross_league_identity_bridge_v16" (
  "bridge_id" TEXT,
  "cfb_player_id" TEXT NOT NULL,
  "nfl_player_key" TEXT NOT NULL,
  "player_name" TEXT NOT NULL,
  "school_id" TEXT,
  "school_name" TEXT,
  "cfb_last_evidence_year" BIGINT,
  "nfl_draft_year" BIGINT,
  "nfl_draft_team" TEXT,
  "nfl_position" TEXT,
  "espn_id" TEXT,
  "gsis_id" TEXT,
  "pfr_id" TEXT,
  "match_rule" TEXT NOT NULL,
  "confidence" DOUBLE PRECISION NOT NULL,
  "verification_status" TEXT NOT NULL,
  "evidence_json" TEXT NOT NULL,
  PRIMARY KEY ("bridge_id")
);

CREATE TABLE IF NOT EXISTS "cross_league_identity_bridge_v17" (
  "bridge_id" TEXT,
  "cfb_player_id" TEXT NOT NULL,
  "espn_athlete_id" TEXT,
  "nfl_player_key" TEXT NOT NULL,
  "player_name" TEXT NOT NULL,
  "school_id" TEXT,
  "school_name" TEXT,
  "cfb_first_year" BIGINT,
  "cfb_last_year" BIGINT,
  "nfl_draft_year" BIGINT,
  "nfl_draft_team" TEXT,
  "cfb_position_group" TEXT,
  "nfl_position_group" TEXT,
  "nfl_position" TEXT,
  "match_rule" TEXT NOT NULL,
  "confidence" DOUBLE PRECISION NOT NULL,
  "verification_status" TEXT NOT NULL,
  "evidence_json" TEXT NOT NULL,
  PRIMARY KEY ("bridge_id")
);

CREATE TABLE IF NOT EXISTS "cross_league_identity_candidates" (
  "candidate_id" TEXT,
  "cfb_player_id" TEXT NOT NULL,
  "nfl_player_key" TEXT NOT NULL,
  "player_name" TEXT NOT NULL,
  "school_id" TEXT,
  "school_name" TEXT,
  "cfb_last_evidence_year" BIGINT,
  "nfl_draft_year" BIGINT,
  "nfl_draft_team" TEXT,
  "nfl_position" TEXT,
  "espn_id" TEXT,
  "gsis_id" TEXT,
  "pfr_id" TEXT,
  "match_rule" TEXT NOT NULL,
  "confidence" DOUBLE PRECISION NOT NULL,
  "decision" TEXT NOT NULL,
  "production_safe" BIGINT NOT NULL DEFAULT 0,
  "evidence_json" TEXT NOT NULL,
  PRIMARY KEY ("candidate_id")
);

CREATE TABLE IF NOT EXISTS "cross_league_identity_rejections_v17" (
  "cfb_player_id" TEXT,
  "player_name" TEXT,
  "reason" TEXT,
  "candidate_count" BIGINT,
  "evidence_json" TEXT
);

CREATE TABLE IF NOT EXISTS "daily_puzzles" (
  "puzzle_date" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "puzzle_id" TEXT NOT NULL,
  "seed_text" TEXT NOT NULL,
  PRIMARY KEY ("puzzle_date", "mode_id")
);

CREATE TABLE IF NOT EXISTS "daily_slate_templates" (
  "slate_template_id" TEXT,
  "name" TEXT NOT NULL,
  "competition_id" TEXT,
  "slots_json" TEXT NOT NULL,
  "active" BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY ("slate_template_id")
);

CREATE TABLE IF NOT EXISTS "daily_slates" (
  "slate_date" TEXT NOT NULL,
  "slate_template_id" TEXT NOT NULL,
  "slot_key" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "puzzle_id" TEXT,
  "seed" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'READY',
  "reason" TEXT,
  PRIMARY KEY ("slate_date", "slate_template_id", "slot_key")
);

CREATE TABLE IF NOT EXISTS "daily_streak_events" (
  "user_id" TEXT NOT NULL,
  "streak_date" TEXT NOT NULL,
  "qualifying_plays" BIGINT NOT NULL DEFAULT 0,
  "qualified" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("user_id", "streak_date")
);

CREATE TABLE IF NOT EXISTS "data_coverage" (
  "domain_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "dataset_name" TEXT NOT NULL,
  "coverage_start" BIGINT,
  "coverage_end" BIGINT,
  "current_through" TEXT,
  "completeness" TEXT NOT NULL,
  "production_safe" BIGINT NOT NULL,
  "source_id" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("domain_id")
);

CREATE TABLE IF NOT EXISTS "draft_facts" (
  "player_key" TEXT,
  "player_name" TEXT NOT NULL,
  "draft_season" BIGINT,
  "draft_team" TEXT,
  "draft_round" BIGINT,
  "draft_pick_overall" BIGINT,
  "position" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("player_key")
);

CREATE TABLE IF NOT EXISTS "entitlement_definitions" (
  "entitlement_key" TEXT,
  "description" TEXT NOT NULL,
  PRIMARY KEY ("entitlement_key")
);

CREATE TABLE IF NOT EXISTS "entity_aliases" (
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "alias" TEXT NOT NULL,
  "alias_type" TEXT,
  "season_start" BIGINT,
  "season_end" BIGINT,
  "accepted_in_answers" BIGINT NOT NULL DEFAULT 1,
  "verification_status" TEXT NOT NULL DEFAULT 'VERIFIED',
  PRIMARY KEY ("entity_type", "entity_id", "alias")
);

CREATE TABLE IF NOT EXISTS "event_game_rules" (
  "rule_id" TEXT,
  "event_type" TEXT NOT NULL,
  "competition_id" TEXT,
  "game_factory_description" TEXT NOT NULL,
  "min_verified_facts" BIGINT NOT NULL DEFAULT 1,
  "auto_generate" BIGINT NOT NULL DEFAULT 1,
  "auto_publish" BIGINT NOT NULL DEFAULT 0,
  "notes" TEXT,
  PRIMARY KEY ("rule_id")
);

CREATE TABLE IF NOT EXISTS "event_generated_games" (
  "event_id" TEXT NOT NULL,
  "rule_id" TEXT NOT NULL,
  "factory_spec_id" TEXT,
  "mode_id" TEXT,
  "generated_count" BIGINT NOT NULL DEFAULT 0,
  "qa_excluded" BIGINT NOT NULL DEFAULT 0,
  "publish_status" TEXT NOT NULL DEFAULT 'PREVIEW',
  "generated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id", "rule_id")
);

CREATE TABLE IF NOT EXISTS "factory_rule_capabilities" (
  "capability_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "rule_kind" TEXT NOT NULL,
  "supported" BIGINT NOT NULL,
  "source_table" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("capability_id")
);

CREATE TABLE IF NOT EXISTS "factory_rule_examples" (
  "example_id" TEXT,
  "description" TEXT NOT NULL,
  "expected_status" TEXT NOT NULL,
  "expected_rule_kind" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("example_id")
);

CREATE TABLE IF NOT EXISTS "feature_flags" (
  "flag_key" TEXT,
  "enabled" BIGINT NOT NULL DEFAULT 0,
  "rollout_percent" BIGINT NOT NULL DEFAULT 0,
  "config_json" TEXT NOT NULL DEFAULT '{}',
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("flag_key")
);

CREATE TABLE IF NOT EXISTS "field_provenance" (
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "field_name" TEXT NOT NULL,
  "value_text" TEXT,
  "source_id" TEXT NOT NULL,
  "release_id" TEXT,
  "verification_status" TEXT NOT NULL,
  "confidence" DOUBLE PRECISION,
  "last_verified_at" TEXT,
  PRIMARY KEY ("entity_type", "entity_id", "field_name", "value_text", "source_id")
);

CREATE TABLE IF NOT EXISTS "franchises" (
  "franchise_id" TEXT,
  "display_name" TEXT NOT NULL,
  "team_codes" TEXT,
  "coverage_start" BIGINT,
  "coverage_end" BIGINT,
  "source_id" TEXT DEFAULT 'NFLVERSE_DATA',
  PRIMARY KEY ("franchise_id")
);

CREATE TABLE IF NOT EXISTS "freshness_registry" (
  "domain_id" TEXT,
  "last_verified_at" TEXT,
  "expected_refresh_minutes" BIGINT NOT NULL,
  "stale_after_minutes" BIGINT NOT NULL,
  "stale" BIGINT NOT NULL DEFAULT 0,
  "current_source_id" TEXT,
  "current_release_id" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("domain_id")
);

CREATE TABLE IF NOT EXISTS "game_factory_candidates" (
  "candidate_id" TEXT,
  "spec_id" TEXT NOT NULL,
  "seed_text" TEXT,
  "difficulty_score" DOUBLE PRECISION NOT NULL,
  "difficulty_band" TEXT NOT NULL,
  "ambiguity_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "eligible" BIGINT NOT NULL DEFAULT 1,
  "exclusion_reason" TEXT,
  "payload_json" TEXT NOT NULL,
  "source_refs_json" TEXT NOT NULL DEFAULT '[]',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("candidate_id")
);

CREATE TABLE IF NOT EXISTS "game_factory_capabilities" (
  "capability_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "mechanic" TEXT NOT NULL,
  "entity_type" TEXT,
  "predicate" TEXT,
  "object_type" TEXT,
  "supported" BIGINT NOT NULL,
  "source_table" TEXT,
  "production_safe" BIGINT NOT NULL DEFAULT 1,
  "notes" TEXT,
  PRIMARY KEY ("capability_id")
);

CREATE TABLE IF NOT EXISTS "game_factory_publications" (
  "publication_id" TEXT,
  "spec_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "published_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "unpublished_at" TEXT,
  "active" BIGINT NOT NULL DEFAULT 1,
  "candidate_count" BIGINT NOT NULL,
  "notes" TEXT,
  PRIMARY KEY ("publication_id")
);

CREATE TABLE IF NOT EXISTS "game_factory_qa" (
  "qa_id" BIGINT,
  "spec_id" TEXT NOT NULL,
  "candidate_id" TEXT,
  "severity" TEXT NOT NULL,
  "issue_type" TEXT NOT NULL,
  "detail" TEXT NOT NULL,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "resolved" BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY ("qa_id")
);

CREATE TABLE IF NOT EXISTS "game_factory_specs" (
  "spec_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "created_from" TEXT NOT NULL,
  "description" TEXT,
  "competition_id" TEXT NOT NULL,
  "mechanic" TEXT NOT NULL,
  "answer_type" TEXT,
  "entity_type" TEXT,
  "relationship_predicate" TEXT,
  "object_type" TEXT,
  "filters_json" TEXT NOT NULL DEFAULT '{}',
  "group_size" BIGINT NOT NULL DEFAULT 4,
  "difficulty_min" DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  "difficulty_max" DOUBLE PRECISION NOT NULL DEFAULT 1.0,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "feasibility_status" TEXT NOT NULL DEFAULT 'UNCHECKED',
  "estimated_candidates" BIGINT NOT NULL DEFAULT 0,
  "eligible_candidates" BIGINT NOT NULL DEFAULT 0,
  "ambiguity_rate" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "source_coverage_json" TEXT NOT NULL DEFAULT '{}',
  "notes" TEXT,
  "rules_json" TEXT DEFAULT '{}',
  "rule_version" TEXT DEFAULT '1.4',
  "complexity_score" DOUBLE PRECISION DEFAULT 0,
  "required_capabilities_json" TEXT DEFAULT '[]',
  "missing_capabilities_json" TEXT DEFAULT '[]',
  PRIMARY KEY ("spec_id")
);

CREATE TABLE IF NOT EXISTS "game_mode_templates" (
  "template_id" TEXT,
  "display_name" TEXT NOT NULL,
  "mechanic" TEXT NOT NULL,
  "answer_entity_type" TEXT NOT NULL,
  "required_predicates" TEXT,
  "nfl_status" TEXT NOT NULL,
  "cfb_status" TEXT NOT NULL,
  "notes" TEXT,
  PRIMARY KEY ("template_id")
);

CREATE TABLE IF NOT EXISTS "game_templates" (
  "template_id" TEXT,
  "template_yaml" TEXT NOT NULL,
  "enabled" BIGINT NOT NULL DEFAULT 1,
  "validation_status" TEXT NOT NULL DEFAULT 'UNVALIDATED',
  "notes" TEXT,
  PRIMARY KEY ("template_id")
);

CREATE TABLE IF NOT EXISTS "gameplay_events" (
  "event_id" TEXT,
  "user_id" TEXT NOT NULL,
  "puzzle_id" TEXT,
  "mode_id" TEXT NOT NULL,
  "competition_id" TEXT,
  "event_type" TEXT NOT NULL,
  "is_correct" BIGINT,
  "response_ms" BIGINT,
  "wrong_guesses" BIGINT NOT NULL DEFAULT 0,
  "hints_used" BIGINT NOT NULL DEFAULT 0,
  "occurred_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "metadata_json" TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY ("event_id")
);

CREATE TABLE IF NOT EXISTS "games" (
  "game_id" TEXT,
  "season" BIGINT NOT NULL,
  "game_type" TEXT,
  "week" TEXT,
  "game_date" TEXT,
  "weekday" TEXT,
  "game_time" TEXT,
  "away_team" TEXT,
  "away_score" BIGINT,
  "home_team" TEXT,
  "home_score" BIGINT,
  "result_margin" BIGINT,
  "total_points" BIGINT,
  "overtime" BIGINT,
  "away_rest" BIGINT,
  "home_rest" BIGINT,
  "away_moneyline" DOUBLE PRECISION,
  "home_moneyline" DOUBLE PRECISION,
  "spread_line" DOUBLE PRECISION,
  "total_line" DOUBLE PRECISION,
  "division_game" BIGINT,
  "roof" TEXT,
  "surface" TEXT,
  "temperature" DOUBLE PRECISION,
  "wind" DOUBLE PRECISION,
  "away_qb_source_id" TEXT,
  "home_qb_source_id" TEXT,
  "away_qb_name" TEXT,
  "home_qb_name" TEXT,
  "away_coach_name" TEXT,
  "home_coach_name" TEXT,
  "referee" TEXT,
  "stadium_id" TEXT,
  "stadium_name" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  PRIMARY KEY ("game_id")
);

CREATE TABLE IF NOT EXISTS "generated_cfb_roster_packs" (
  "pack_id" TEXT,
  "season" BIGINT NOT NULL,
  "school_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "payload_json" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED_DERIVED',
  PRIMARY KEY ("pack_id")
);

CREATE TABLE IF NOT EXISTS "generated_game_packs" (
  "pack_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "seed_text" TEXT NOT NULL,
  "difficulty_band" TEXT,
  "payload_json" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL,
  PRIMARY KEY ("pack_id")
);

CREATE TABLE IF NOT EXISTS "generated_roster_packs" (
  "pack_id" TEXT,
  "mode_id" TEXT NOT NULL,
  "season" BIGINT,
  "team_code" TEXT,
  "payload_json" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL DEFAULT 'DERIVED_SOURCE_BACKED',
  PRIMARY KEY ("pack_id")
);

CREATE TABLE IF NOT EXISTS "graph_edges" (
  "edge_id" BIGINT,
  "subject_type" TEXT NOT NULL,
  "subject_id" TEXT NOT NULL,
  "predicate" TEXT NOT NULL,
  "object_type" TEXT NOT NULL,
  "object_id" TEXT NOT NULL,
  "season_start" BIGINT,
  "season_end" BIGINT,
  "source_id" TEXT,
  "verification_status" TEXT NOT NULL,
  PRIMARY KEY ("edge_id")
);

CREATE TABLE IF NOT EXISTS "graph_nodes" (
  "node_type" TEXT NOT NULL,
  "node_id" TEXT NOT NULL,
  "display_name" TEXT,
  "popularity_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("node_type", "node_id")
);

CREATE TABLE IF NOT EXISTS "graph_path_cache" (
  "start_type" TEXT NOT NULL,
  "start_id" TEXT NOT NULL,
  "end_type" TEXT NOT NULL,
  "end_id" TEXT NOT NULL,
  "max_depth" BIGINT NOT NULL,
  "path_json" TEXT NOT NULL,
  "path_length" BIGINT NOT NULL,
  "generated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("start_type", "start_id", "end_type", "end_id", "max_depth")
);

CREATE TABLE IF NOT EXISTS "identity_bridge_runs" (
  "run_id" TEXT,
  "run_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "player_master_sha256" TEXT,
  "cfb_players_considered" BIGINT,
  "nfl_players_considered" BIGINT,
  "exact_espn_links" BIGINT,
  "exact_pfr_links" BIGINT,
  "legacy_evidence_links" BIGINT,
  "rejected_ambiguous" BIGINT,
  "total_production_links" BIGINT,
  "notes" TEXT,
  PRIMARY KEY ("run_id")
);

CREATE TABLE IF NOT EXISTS "import_batches" (
  "batch_id" TEXT,
  "dataset_name" TEXT NOT NULL,
  "source_id" TEXT NOT NULL,
  "source_file" TEXT NOT NULL,
  "source_sha256" TEXT NOT NULL,
  "started_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "finished_at" TEXT,
  "status" TEXT NOT NULL,
  "rows_read" BIGINT NOT NULL DEFAULT 0,
  "rows_staged" BIGINT NOT NULL DEFAULT 0,
  "rows_published" BIGINT NOT NULL DEFAULT 0,
  "rows_rejected" BIGINT NOT NULL DEFAULT 0,
  "qa_issue_count" BIGINT NOT NULL DEFAULT 0,
  "transform_version" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("batch_id")
);

CREATE TABLE IF NOT EXISTS "import_rejections" (
  "rejection_id" BIGINT,
  "batch_id" TEXT NOT NULL,
  "row_number" BIGINT,
  "reason_code" TEXT NOT NULL,
  "detail" TEXT,
  "raw_json" TEXT,
  PRIMARY KEY ("rejection_id")
);

CREATE TABLE IF NOT EXISTS "league_mode_bindings" (
  "template_id" TEXT NOT NULL,
  "competition_id" TEXT NOT NULL,
  "concrete_mode_id" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "source_view" TEXT,
  "eligibility_rule" TEXT,
  PRIMARY KEY ("template_id", "competition_id")
);

CREATE TABLE IF NOT EXISTS "live_data_feeds" (
  "feed_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "dataset_name" TEXT NOT NULL,
  "source_id" TEXT,
  "source_url" TEXT,
  "refresh_policy" TEXT NOT NULL,
  "freshness_minutes" BIGINT NOT NULL DEFAULT 1440,
  "enabled" BIGINT NOT NULL DEFAULT 1,
  "production_safe" BIGINT NOT NULL DEFAULT 0,
  "last_success_at" TEXT,
  "last_attempt_at" TEXT,
  "last_status" TEXT,
  "notes" TEXT,
  PRIMARY KEY ("feed_id")
);

CREATE TABLE IF NOT EXISTS "live_event_catalog" (
  "event_id" TEXT,
  "competition_id" TEXT NOT NULL,
  "event_type" TEXT NOT NULL,
  "event_date" TEXT NOT NULL,
  "entity_type" TEXT,
  "entity_id" TEXT,
  "title" TEXT NOT NULL,
  "payload_json" TEXT NOT NULL,
  "source_id" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'PENDING',
  "freshness_status" TEXT NOT NULL DEFAULT 'FRESH',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("event_id")
);

CREATE TABLE IF NOT EXISTS "live_event_puzzles" (
  "live_puzzle_id" TEXT,
  "event_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "prompt" TEXT NOT NULL,
  "answer" TEXT NOT NULL,
  "payload_json" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL,
  "publish_status" TEXT NOT NULL DEFAULT 'PREVIEW',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("live_puzzle_id")
);

CREATE TABLE IF NOT EXISTS "live_fact_changes" (
  "change_id" TEXT,
  "run_id" TEXT NOT NULL,
  "entity_type" TEXT NOT NULL,
  "entity_id" TEXT NOT NULL,
  "field_name" TEXT NOT NULL,
  "old_value" TEXT,
  "new_value" TEXT,
  "change_type" TEXT NOT NULL,
  "source_id" TEXT,
  "detected_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "qa_status" TEXT NOT NULL DEFAULT 'PENDING',
  "publish_status" TEXT NOT NULL DEFAULT 'HELD',
  PRIMARY KEY ("change_id")
);

CREATE TABLE IF NOT EXISTS "live_ingest_runs" (
  "run_id" TEXT,
  "feed_id" TEXT NOT NULL,
  "started_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "finished_at" TEXT,
  "status" TEXT NOT NULL,
  "source_version" TEXT,
  "source_sha256" TEXT,
  "rows_seen" BIGINT NOT NULL DEFAULT 0,
  "rows_inserted" BIGINT NOT NULL DEFAULT 0,
  "rows_updated" BIGINT NOT NULL DEFAULT 0,
  "rows_rejected" BIGINT NOT NULL DEFAULT 0,
  "qa_issues" BIGINT NOT NULL DEFAULT 0,
  "log_json" TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY ("run_id")
);

CREATE TABLE IF NOT EXISTS "live_publication_audit" (
  "publication_id" TEXT,
  "event_id" TEXT NOT NULL,
  "live_puzzle_id" TEXT NOT NULL,
  "puzzle_id" TEXT,
  "mode_id" TEXT NOT NULL,
  "action" TEXT NOT NULL,
  "actor" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("publication_id")
);

CREATE TABLE IF NOT EXISTS "live_publish_queue" (
  "queue_id" TEXT,
  "object_type" TEXT NOT NULL,
  "object_id" TEXT NOT NULL,
  "reason" TEXT NOT NULL,
  "qa_status" TEXT NOT NULL DEFAULT 'PENDING',
  "priority" BIGINT NOT NULL DEFAULT 50,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "reviewed_at" TEXT,
  "reviewed_by" TEXT,
  "decision" TEXT,
  PRIMARY KEY ("queue_id")
);

CREATE TABLE IF NOT EXISTS "meta" (
  "key" TEXT,
  "value" TEXT NOT NULL,
  PRIMARY KEY ("key")
);

CREATE TABLE IF NOT EXISTS "migration_runs" (
  "migration_id" TEXT,
  "target" TEXT NOT NULL,
  "started_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "finished_at" TEXT,
  "status" TEXT NOT NULL,
  "details_json" TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY ("migration_id")
);

CREATE TABLE IF NOT EXISTS "mode_health" (
  "mode_id" TEXT,
  "eligible_puzzles" BIGINT NOT NULL,
  "easy_count" BIGINT NOT NULL,
  "medium_count" BIGINT NOT NULL,
  "hard_count" BIGINT NOT NULL,
  "expert_count" BIGINT NOT NULL,
  "min_difficulty" DOUBLE PRECISION,
  "max_difficulty" DOUBLE PRECISION,
  "notes" TEXT,
  PRIMARY KEY ("mode_id")
);

CREATE TABLE IF NOT EXISTS "mode_user_skill" (
  "user_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "rating" DOUBLE PRECISION NOT NULL DEFAULT 1000,
  "games_played" BIGINT NOT NULL DEFAULT 0,
  "wins" BIGINT NOT NULL DEFAULT 0,
  "correct_answers" BIGINT NOT NULL DEFAULT 0,
  "attempts" BIGINT NOT NULL DEFAULT 0,
  "avg_response_ms" DOUBLE PRECISION,
  "skill_band" TEXT NOT NULL DEFAULT 'UNRANKED',
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "mode_id")
);

CREATE TABLE IF NOT EXISTS "moderation_actions" (
  "action_id" TEXT,
  "community_game_id" TEXT NOT NULL,
  "moderator_user_id" TEXT,
  "action" TEXT NOT NULL,
  "reason" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("action_id")
);

CREATE TABLE IF NOT EXISTS "nfl_cfb_player_links" (
  "cfb_player_id" TEXT NOT NULL,
  "nfl_player_key" TEXT NOT NULL,
  "cfb_player_name" TEXT,
  "nfl_player_name" TEXT,
  "nfl_draft_year" BIGINT,
  "nfl_draft_team" TEXT,
  "match_rule" TEXT,
  "match_status" TEXT NOT NULL,
  "review_note" TEXT,
  PRIMARY KEY ("cfb_player_id", "nfl_player_key")
);

CREATE TABLE IF NOT EXISTS "nfl_players_draft" (
  "player_key" TEXT,
  "draft_season" BIGINT,
  "draft_team" TEXT,
  "draft_round" BIGINT,
  "draft_pick_overall" BIGINT,
  "pfr_id" TEXT,
  "player_name" TEXT NOT NULL,
  "nflverse_player_id" TEXT,
  "side" TEXT,
  "category" TEXT,
  "position" TEXT,
  "id_quality" TEXT,
  "source_id" TEXT DEFAULT 'NFLVERSE_DATA',
  PRIMARY KEY ("player_key")
);

CREATE TABLE IF NOT EXISTS "notification_outbox" (
  "notification_id" TEXT,
  "audience_type" TEXT NOT NULL,
  "audience_key" TEXT,
  "notification_type" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "deep_link" TEXT,
  "payload_json" TEXT NOT NULL DEFAULT '{}',
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "sent_at" TEXT,
  PRIMARY KEY ("notification_id")
);

CREATE TABLE IF NOT EXISTS "personalization_feed_cache" (
  "user_id" TEXT NOT NULL,
  "slot" BIGINT NOT NULL,
  "puzzle_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "reason" TEXT NOT NULL,
  "score" DOUBLE PRECISION NOT NULL,
  "generated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "slot")
);

CREATE TABLE IF NOT EXISTS "player_identity_links" (
  "canonical_player_id" TEXT NOT NULL,
  "nfl_player_key" TEXT NOT NULL,
  "match_rule" TEXT NOT NULL,
  "verification_status" TEXT NOT NULL,
  PRIMARY KEY ("canonical_player_id", "nfl_player_key")
);

CREATE TABLE IF NOT EXISTS "player_profiles" (
  "player_type" TEXT NOT NULL,
  "player_id" TEXT NOT NULL,
  "display_name" TEXT NOT NULL,
  "primary_team_or_school" TEXT,
  "first_year" BIGINT,
  "last_year" BIGINT,
  "graph_degree" BIGINT NOT NULL DEFAULT 0,
  "profile_json" TEXT NOT NULL,
  PRIMARY KEY ("player_type", "player_id")
);

CREATE TABLE IF NOT EXISTS "player_season_stats" (
  "season" BIGINT NOT NULL,
  "player_key" TEXT NOT NULL,
  "team_code" TEXT,
  "games" BIGINT,
  "starts" BIGINT,
  "pass_yards" BIGINT,
  "pass_td" BIGINT,
  "rush_yards" BIGINT,
  "rush_td" BIGINT,
  "receptions" BIGINT,
  "rec_yards" BIGINT,
  "rec_td" BIGINT,
  "sacks" DOUBLE PRECISION,
  "interceptions" DOUBLE PRECISION,
  "tackles" DOUBLE PRECISION,
  "fg_made" BIGINT,
  "fg_att" BIGINT,
  "verification_status" TEXT NOT NULL DEFAULT 'INCOMPLETE',
  "source_id" TEXT,
  PRIMARY KEY ("season", "player_key", "team_code")
);

CREATE TABLE IF NOT EXISTS "puzzle_attempts" (
  "attempt_id" BIGINT,
  "puzzle_id" TEXT NOT NULL,
  "user_key" TEXT,
  "attempted_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "correct" BIGINT NOT NULL,
  "solve_ms" BIGINT,
  "wrong_guess_count" BIGINT NOT NULL DEFAULT 0,
  "hint_count" BIGINT NOT NULL DEFAULT 0,
  "abandoned" BIGINT NOT NULL DEFAULT 0,
  "device_class" TEXT,
  "player_rating_before" DOUBLE PRECISION,
  PRIMARY KEY ("attempt_id")
);

CREATE TABLE IF NOT EXISTS "puzzle_catalog" (
  "puzzle_id" TEXT,
  "mode_id" TEXT NOT NULL,
  "source_entity_type" TEXT NOT NULL,
  "source_entity_id" TEXT NOT NULL,
  "season" BIGINT,
  "difficulty_score" DOUBLE PRECISION NOT NULL,
  "difficulty_band" TEXT NOT NULL,
  "ambiguity_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "popularity_proxy" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "eligible" BIGINT NOT NULL DEFAULT 1,
  "exclusion_reason" TEXT,
  "verification_status" TEXT NOT NULL,
  "source_id" TEXT,
  "payload_json" TEXT NOT NULL,
  PRIMARY KEY ("puzzle_id")
);

CREATE TABLE IF NOT EXISTS "puzzle_collisions" (
  "collision_id" BIGINT,
  "mode_id" TEXT NOT NULL,
  "normalized_prompt" TEXT NOT NULL,
  "answer_count" BIGINT NOT NULL,
  "answers_json" TEXT NOT NULL,
  "puzzle_ids_json" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY ("collision_id")
);

CREATE TABLE IF NOT EXISTS "puzzle_difficulty_live" (
  "puzzle_id" TEXT,
  "attempts" BIGINT NOT NULL DEFAULT 0,
  "correct" BIGINT NOT NULL DEFAULT 0,
  "solve_rate" DOUBLE PRECISION,
  "avg_response_ms" DOUBLE PRECISION,
  "avg_wrong_guesses" DOUBLE PRECISION,
  "avg_hints" DOUBLE PRECISION,
  "abandon_rate" DOUBLE PRECISION,
  "empirical_score" DOUBLE PRECISION,
  "empirical_band" TEXT,
  "confidence" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("puzzle_id")
);

CREATE TABLE IF NOT EXISTS "qa_issues" (
  "issue_id" BIGINT,
  "severity" TEXT NOT NULL,
  "entity_type" TEXT,
  "entity_id" TEXT,
  "field_name" TEXT,
  "issue_type" TEXT NOT NULL,
  "detail" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("issue_id")
);

CREATE TABLE IF NOT EXISTS "qa_reviews" (
  "review_id" BIGINT,
  "issue_id" BIGINT,
  "reviewer" TEXT,
  "action" TEXT NOT NULL,
  "old_value" TEXT,
  "new_value" TEXT,
  "notes" TEXT,
  "reviewed_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("review_id")
);

CREATE TABLE IF NOT EXISTS "qb_game_starts" (
  "game_id" TEXT NOT NULL,
  "team_code" TEXT NOT NULL,
  "side" TEXT NOT NULL,
  "qb_source_id" TEXT,
  "qb_name" TEXT,
  "opponent_team" TEXT,
  "is_home" BIGINT NOT NULL,
  "season" BIGINT NOT NULL,
  PRIMARY KEY ("game_id", "team_code")
);

CREATE TABLE IF NOT EXISTS "qb_team_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "qb_source_id" TEXT,
  "qb_name" TEXT NOT NULL,
  "starts_observed" BIGINT NOT NULL,
  "first_start_date" TEXT,
  "last_start_date" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("season", "team_code", "qb_name")
);

CREATE TABLE IF NOT EXISTS "ranked_match_tokens" (
  "match_token" TEXT,
  "user_id" TEXT NOT NULL,
  "mode_id" TEXT NOT NULL,
  "seed" TEXT NOT NULL,
  "issued_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "expires_at" TEXT NOT NULL,
  "consumed_at" TEXT,
  "puzzle_ids_json" TEXT NOT NULL,
  "answer_commitment" TEXT NOT NULL,
  PRIMARY KEY ("match_token")
);

CREATE TABLE IF NOT EXISTS "ranked_ratings" (
  "season_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "queue_id" TEXT NOT NULL,
  "rating" DOUBLE PRECISION NOT NULL DEFAULT 1000,
  "games_played" BIGINT NOT NULL DEFAULT 0,
  "wins" BIGINT NOT NULL DEFAULT 0,
  "losses" BIGINT NOT NULL DEFAULT 0,
  "draws" BIGINT NOT NULL DEFAULT 0,
  "peak_rating" DOUBLE PRECISION NOT NULL DEFAULT 1000,
  "division" TEXT NOT NULL DEFAULT 'UNRANKED',
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("season_id", "user_id", "queue_id")
);

CREATE TABLE IF NOT EXISTS "refresh_runs" (
  "run_id" TEXT,
  "started_at" TEXT NOT NULL,
  "finished_at" TEXT,
  "source_id" TEXT,
  "dataset_name" TEXT,
  "status" TEXT NOT NULL,
  "rows_downloaded" BIGINT,
  "rows_imported" BIGINT,
  "rows_rejected" BIGINT,
  "qa_issue_count" BIGINT,
  "log_json" TEXT,
  PRIMARY KEY ("run_id")
);

CREATE TABLE IF NOT EXISTS "relationships" (
  "relationship_id" BIGINT,
  "subject_type" TEXT NOT NULL,
  "subject_id" TEXT NOT NULL,
  "predicate" TEXT NOT NULL,
  "object_type" TEXT NOT NULL,
  "object_id" TEXT NOT NULL,
  "season_start" BIGINT,
  "season_end" BIGINT,
  "source_id" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'DERIVED',
  PRIMARY KEY ("relationship_id")
);

CREATE TABLE IF NOT EXISTS "request_metrics" (
  "metric_id" TEXT,
  "route" TEXT NOT NULL,
  "method" TEXT NOT NULL,
  "status_code" BIGINT NOT NULL,
  "duration_ms" BIGINT NOT NULL,
  "user_id" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("metric_id")
);

CREATE TABLE IF NOT EXISTS "role_definitions" (
  "role_id" TEXT,
  "description" TEXT NOT NULL,
  "permissions_json" TEXT NOT NULL,
  PRIMARY KEY ("role_id")
);

CREATE TABLE IF NOT EXISTS "roster_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "franchise_id" TEXT,
  "player_key" TEXT NOT NULL,
  "gsis_id" TEXT,
  "player_name" TEXT NOT NULL,
  "position" TEXT,
  "depth_role" TEXT,
  "jersey_number" BIGINT,
  "school_id" TEXT,
  "years_with_team" BIGINT,
  "roster_status" TEXT,
  "verification_status" TEXT NOT NULL DEFAULT 'INCOMPLETE',
  "source_id" TEXT,
  PRIMARY KEY ("season", "team_code", "player_key")
);

CREATE TABLE IF NOT EXISTS "school_aliases" (
  "alias_name" TEXT,
  "school_id" TEXT NOT NULL,
  "canonical_name" TEXT NOT NULL,
  "alias_reason" TEXT,
  "status" TEXT,
  PRIMARY KEY ("alias_name")
);

CREATE TABLE IF NOT EXISTS "schools" (
  "school_id" TEXT,
  "school_name" TEXT NOT NULL,
  "status" TEXT NOT NULL,
  "source_tabs" TEXT,
  PRIMARY KEY ("school_id")
);

CREATE TABLE IF NOT EXISTS "season_records" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "wins" BIGINT,
  "losses" BIGINT,
  "ties" BIGINT,
  "games" BIGINT,
  "win_pct" DOUBLE PRECISION,
  "points_for" BIGINT,
  "points_against" BIGINT,
  "point_diff" BIGINT,
  "seed" BIGINT,
  "playoff_result" TEXT,
  PRIMARY KEY ("season", "team_code")
);

CREATE TABLE IF NOT EXISTS "season_standings" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "conference" TEXT,
  "division" TEXT,
  "wins" BIGINT,
  "losses" BIGINT,
  "ties" BIGINT,
  "win_pct" DOUBLE PRECISION,
  "division_rank" BIGINT,
  "points_for" BIGINT,
  "points_against" BIGINT,
  "point_diff" BIGINT,
  "strength_of_victory" DOUBLE PRECISION,
  "strength_of_schedule" DOUBLE PRECISION,
  "seed" BIGINT,
  "playoff_result" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("season", "team_code")
);

CREATE TABLE IF NOT EXISTS "service_health_events" (
  "health_event_id" TEXT,
  "service" TEXT NOT NULL,
  "severity" TEXT NOT NULL,
  "event_type" TEXT NOT NULL,
  "message" TEXT NOT NULL,
  "metadata_json" TEXT NOT NULL DEFAULT '{}',
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "resolved_at" TEXT,
  PRIMARY KEY ("health_event_id")
);

CREATE TABLE IF NOT EXISTS "source_releases" (
  "release_id" TEXT,
  "source_id" TEXT NOT NULL,
  "dataset_name" TEXT NOT NULL,
  "release_version" TEXT,
  "source_url" TEXT,
  "retrieved_at" TEXT,
  "sha256" TEXT,
  "license_note" TEXT,
  "attribution_text" TEXT,
  "transform_version" TEXT,
  "import_status" TEXT NOT NULL DEFAULT 'PENDING',
  "row_count" BIGINT,
  "notes" TEXT,
  PRIMARY KEY ("release_id")
);

CREATE TABLE IF NOT EXISTS "sources" (
  "source_id" TEXT,
  "source_name" TEXT NOT NULL,
  "source_url" TEXT,
  "license_note" TEXT,
  "attribution_required" BIGINT NOT NULL DEFAULT 0,
  "approved_for_import" BIGINT NOT NULL DEFAULT 0,
  "notes" TEXT,
  PRIMARY KEY ("source_id")
);

CREATE TABLE IF NOT EXISTS "sponsorship_slots" (
  "slot_id" TEXT,
  "surface" TEXT NOT NULL,
  "placement" TEXT NOT NULL,
  "max_frequency" BIGINT NOT NULL DEFAULT 1,
  "enabled" BIGINT NOT NULL DEFAULT 0,
  "config_json" TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY ("slot_id")
);

CREATE TABLE IF NOT EXISTS "stadiums" (
  "stadium_id" TEXT,
  "stadium_name" TEXT,
  "first_season" BIGINT,
  "last_season" BIGINT,
  "observed_roofs" TEXT,
  "observed_surfaces" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("stadium_id")
);

CREATE TABLE IF NOT EXISTS "staging_cfb_games" (
  "batch_id" TEXT NOT NULL,
  "source_row" BIGINT NOT NULL,
  "game_id" TEXT,
  "season" BIGINT,
  "week" BIGINT,
  "game_date" TEXT,
  "home_school" TEXT,
  "away_school" TEXT,
  "home_score" BIGINT,
  "away_score" BIGINT,
  "stadium_name" TEXT,
  "conference_game" BIGINT,
  "raw_json" TEXT,
  PRIMARY KEY ("batch_id", "source_row")
);

CREATE TABLE IF NOT EXISTS "staging_players" (
  "batch_id" TEXT NOT NULL,
  "source_row" BIGINT NOT NULL,
  "gsis_id" TEXT,
  "display_name" TEXT,
  "birth_date" TEXT,
  "height_in" BIGINT,
  "weight_lb" BIGINT,
  "college_name" TEXT,
  "position" TEXT,
  "draft_year" BIGINT,
  "draft_round" BIGINT,
  "draft_pick" BIGINT,
  "pfr_id" TEXT,
  "raw_json" TEXT,
  PRIMARY KEY ("batch_id", "source_row")
);

CREATE TABLE IF NOT EXISTS "staging_rosters" (
  "batch_id" TEXT NOT NULL,
  "source_row" BIGINT NOT NULL,
  "season" BIGINT,
  "team_code" TEXT,
  "gsis_id" TEXT,
  "full_name" TEXT,
  "position" TEXT,
  "jersey_number" BIGINT,
  "roster_status" TEXT,
  "college_name" TEXT,
  "raw_json" TEXT,
  PRIMARY KEY ("batch_id", "source_row")
);

CREATE TABLE IF NOT EXISTS "stg_c_01_player_draft" (
  "player_key" TEXT,
  "season" TEXT,
  "team" TEXT,
  "round" TEXT,
  "pick" TEXT,
  "pfr_id" TEXT,
  "pfr_name" TEXT,
  "player_id" TEXT,
  "side" TEXT,
  "category" TEXT,
  "position" TEXT,
  "id_quality" TEXT,
  "source_url" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_02_franchises" (
  "franchise_id" TEXT,
  "current_display_name" TEXT,
  "team_codes" TEXT,
  "source_coverage_start" TEXT,
  "source_coverage_end" TEXT,
  "source_url" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_03_team_aliases" (
  "team_code" TEXT,
  "franchise_id" TEXT,
  "full_name" TEXT,
  "season_start" TEXT,
  "season_end" TEXT,
  "source_url" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_04_team_seasons" (
  "season" TEXT,
  "team" TEXT,
  "nfl" TEXT,
  "nfl_team_id" TEXT,
  "espn" TEXT,
  "pfr" TEXT,
  "pff" TEXT,
  "pfflabel" TEXT,
  "fo" TEXT,
  "full" TEXT,
  "location" TEXT,
  "short_location" TEXT,
  "nickname" TEXT,
  "hyphenated" TEXT,
  "sbr" TEXT,
  "sbr_wins" TEXT,
  "sbr_name" TEXT,
  "draft_kings" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_05_games" (
  "game_id" TEXT,
  "season" TEXT,
  "game_type" TEXT,
  "week" TEXT,
  "gameday" TEXT,
  "weekday" TEXT,
  "gametime" TEXT,
  "away_team" TEXT,
  "away_score" TEXT,
  "home_team" TEXT,
  "home_score" TEXT,
  "result" TEXT,
  "total" TEXT,
  "overtime" TEXT,
  "pfr" TEXT,
  "espn" TEXT,
  "away_rest" TEXT,
  "home_rest" TEXT,
  "away_moneyline" TEXT,
  "home_moneyline" TEXT,
  "spread_line" TEXT,
  "total_line" TEXT,
  "div_game" TEXT,
  "roof" TEXT,
  "surface" TEXT,
  "temp" TEXT,
  "wind" TEXT,
  "away_qb_id" TEXT,
  "home_qb_id" TEXT,
  "away_qb_name" TEXT,
  "home_qb_name" TEXT,
  "away_coach" TEXT,
  "home_coach" TEXT,
  "referee" TEXT,
  "stadium_id" TEXT,
  "stadium" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_06_standings" (
  "season" TEXT,
  "conf" TEXT,
  "division" TEXT,
  "team" TEXT,
  "wins" TEXT,
  "losses" TEXT,
  "ties" TEXT,
  "pct" TEXT,
  "div_rank" TEXT,
  "scored" TEXT,
  "allowed" TEXT,
  "net" TEXT,
  "sov" TEXT,
  "sos" TEXT,
  "seed" TEXT,
  "playoff" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_c_07_trades" (
  "trade_id" TEXT,
  "season" TEXT,
  "trade_date" TEXT,
  "gave" TEXT,
  "received" TEXT,
  "pick_season" TEXT,
  "pick_round" TEXT,
  "pick_number" TEXT,
  "conditional" TEXT,
  "pfr_id" TEXT,
  "pfr_name" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u01_schools" (
  "school_id" TEXT,
  "school_name" TEXT,
  "source_tabs" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u02_cfb_players" (
  "cfb_player_id" TEXT,
  "player_name" TEXT,
  "first_year" TEXT,
  "last_year" TEXT,
  "school_names" TEXT,
  "school_ids" TEXT,
  "contexts" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u03_cfb_coaches" (
  "cfb_coach_id" TEXT,
  "coach_name" TEXT,
  "school_context" TEXT,
  "source_contexts" TEXT,
  "first_year" TEXT,
  "last_year" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u04_cfb_awards" (
  "award_id" TEXT,
  "award_name" TEXT,
  "year" TEXT,
  "cfb_player_id" TEXT,
  "player_name" TEXT,
  "school_id" TEXT,
  "school_name" TEXT,
  "source_tab" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u05_rivalries" (
  "rivalry_id" TEXT,
  "matchup" TEXT,
  "school_a_id" TEXT,
  "school_a" TEXT,
  "school_b_id" TEXT,
  "school_b" TEXT,
  "nickname" TEXT,
  "first_meeting" TEXT,
  "total_meetings" TEXT,
  "series_record" TEXT,
  "trophy" TEXT,
  "fun_fact" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u06_champions" (
  "year" TEXT,
  "champion_raw" TEXT,
  "coach_raw" TEXT,
  "notes" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u07_nfl_cfb_links" (
  "cfb_player_id" TEXT,
  "cfb_player_name" TEXT,
  "nfl_player_key" TEXT,
  "nfl_player_name" TEXT,
  "nfl_draft_year" TEXT,
  "nfl_draft_team" TEXT,
  "match_rule" TEXT,
  "match_status" TEXT,
  "review_note" TEXT
);

CREATE TABLE IF NOT EXISTS "stg_u08_school_aliases" (
  "alias_name" TEXT,
  "canonical_name" TEXT,
  "canonical_school_id" TEXT,
  "alias_reason" TEXT,
  "status" TEXT
);

CREATE TABLE IF NOT EXISTS "subscription_products" (
  "product_id" TEXT,
  "name" TEXT NOT NULL,
  "tier" TEXT NOT NULL,
  "billing_period" TEXT,
  "price_cents" BIGINT,
  "currency" TEXT NOT NULL DEFAULT 'USD',
  "active" BIGINT NOT NULL DEFAULT 1,
  "provider_product_ref" TEXT,
  "features_json" TEXT NOT NULL DEFAULT '[]',
  PRIMARY KEY ("product_id")
);

CREATE TABLE IF NOT EXISTS "team_aliases" (
  "team_code" TEXT NOT NULL,
  "franchise_id" TEXT NOT NULL,
  "full_name" TEXT NOT NULL,
  "season_start" BIGINT,
  "season_end" BIGINT,
  PRIMARY KEY ("team_code", "full_name", "season_start")
);

CREATE TABLE IF NOT EXISTS "team_game_results" (
  "game_id" TEXT NOT NULL,
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "opponent_team" TEXT NOT NULL,
  "is_home" BIGINT NOT NULL,
  "points_for" BIGINT,
  "points_against" BIGINT,
  "result" TEXT,
  PRIMARY KEY ("game_id", "team_code")
);

CREATE TABLE IF NOT EXISTS "team_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "franchise_id" TEXT,
  "full_name" TEXT,
  "location" TEXT,
  "nickname" TEXT,
  "conference" TEXT,
  "division" TEXT,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("season", "team_code")
);

CREATE TABLE IF NOT EXISTS "team_stadium_seasons" (
  "season" BIGINT NOT NULL,
  "team_code" TEXT NOT NULL,
  "stadium_id" TEXT NOT NULL,
  "stadium_name" TEXT,
  "home_games_observed" BIGINT NOT NULL,
  "source_id" TEXT NOT NULL DEFAULT 'NFLVERSE_DATA',
  "verification_status" TEXT NOT NULL DEFAULT 'SOURCE_BACKED',
  PRIMARY KEY ("season", "team_code", "stadium_id")
);

CREATE TABLE IF NOT EXISTS "tier_entitlements" (
  "tier" TEXT NOT NULL,
  "entitlement_key" TEXT NOT NULL,
  "enabled" BIGINT NOT NULL DEFAULT 1,
  "limit_value" BIGINT,
  PRIMARY KEY ("tier", "entitlement_key")
);

CREATE TABLE IF NOT EXISTS "user_achievements" (
  "user_id" TEXT NOT NULL,
  "achievement_id" TEXT NOT NULL,
  "unlocked_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "progress" DOUBLE PRECISION NOT NULL DEFAULT 1,
  PRIMARY KEY ("user_id", "achievement_id")
);

CREATE TABLE IF NOT EXISTS "user_devices" (
  "device_id" TEXT,
  "user_id" TEXT NOT NULL,
  "platform" TEXT,
  "app_version" TEXT,
  "last_seen_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "push_token_ref" TEXT,
  PRIMARY KEY ("device_id")
);

CREATE TABLE IF NOT EXISTS "user_entitlement_overrides" (
  "user_id" TEXT NOT NULL,
  "entitlement_key" TEXT NOT NULL,
  "enabled" BIGINT NOT NULL,
  "limit_value" BIGINT,
  "expires_at" TEXT,
  "reason" TEXT,
  PRIMARY KEY ("user_id", "entitlement_key")
);

CREATE TABLE IF NOT EXISTS "user_error_reports" (
  "report_id" BIGINT,
  "puzzle_id" TEXT,
  "user_key" TEXT,
  "report_type" TEXT NOT NULL,
  "message" TEXT,
  "submitted_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  PRIMARY KEY ("report_id")
);

CREATE TABLE IF NOT EXISTS "user_roles" (
  "user_id" TEXT NOT NULL,
  "role_id" TEXT NOT NULL,
  "granted_by" TEXT,
  "granted_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "role_id")
);

CREATE TABLE IF NOT EXISTS "user_subscriptions" (
  "subscription_id" TEXT,
  "user_id" TEXT NOT NULL,
  "product_id" TEXT NOT NULL,
  "provider" TEXT NOT NULL,
  "provider_customer_ref" TEXT,
  "provider_subscription_ref" TEXT,
  "status" TEXT NOT NULL,
  "current_period_end" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("subscription_id")
);

CREATE TABLE IF NOT EXISTS "user_topic_affinity" (
  "user_id" TEXT NOT NULL,
  "topic_type" TEXT NOT NULL,
  "topic_key" TEXT NOT NULL,
  "interest_score" DOUBLE PRECISION NOT NULL DEFAULT 0,
  "mastery_score" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
  "impressions" BIGINT NOT NULL DEFAULT 0,
  "plays" BIGINT NOT NULL DEFAULT 0,
  "updated_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("user_id", "topic_type", "topic_key")
);

CREATE TABLE IF NOT EXISTS "users_game_profile" (
  "user_id" TEXT,
  "display_name" TEXT,
  "created_at" TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "last_active_at" TEXT,
  "total_xp" BIGINT NOT NULL DEFAULT 0,
  "level" BIGINT NOT NULL DEFAULT 1,
  "current_streak" BIGINT NOT NULL DEFAULT 0,
  "longest_streak" BIGINT NOT NULL DEFAULT 0,
  "last_streak_date" TEXT,
  "personalization_enabled" BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY ("user_id")
);

COMMIT;