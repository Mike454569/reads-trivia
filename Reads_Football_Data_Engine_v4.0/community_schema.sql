CREATE TABLE creator_profiles (
  user_id TEXT PRIMARY KEY,
  handle TEXT UNIQUE,
  display_name TEXT,
  bio TEXT,
  avatar_url TEXT,
  is_verified INTEGER NOT NULL DEFAULT 0,
  creator_score REAL NOT NULL DEFAULT 0,
  follower_count INTEGER NOT NULL DEFAULT 0,
  following_count INTEGER NOT NULL DEFAULT 0,
  published_count INTEGER NOT NULL DEFAULT 0,
  total_plays INTEGER NOT NULL DEFAULT 0,
  total_likes INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE creator_follows (
  follower_user_id TEXT NOT NULL,
  creator_user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(follower_user_id,creator_user_id)
);

CREATE TABLE community_games (
  community_game_id TEXT PRIMARY KEY,
  creator_user_id TEXT NOT NULL REFERENCES users_game_profile(user_id),
  title TEXT NOT NULL,
  description TEXT,
  competition_id TEXT,
  mechanic TEXT NOT NULL,
  source_spec_id TEXT,
  source_template_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'PRIVATE',
  moderation_status TEXT NOT NULL DEFAULT 'DRAFT',
  publish_status TEXT NOT NULL DEFAULT 'DRAFT',
  difficulty_label TEXT,
  estimated_puzzle_count INTEGER NOT NULL DEFAULT 0,
  cover_text TEXT,
  tags_json TEXT NOT NULL DEFAULT '[]',
  rules_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT
);

CREATE TABLE community_game_puzzles (
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  ordinal INTEGER NOT NULL,
  puzzle_id TEXT NOT NULL,
  payload_override_json TEXT,
  PRIMARY KEY(community_game_id,ordinal)
);

CREATE TABLE community_game_likes (
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(community_game_id,user_id)
);

CREATE TABLE community_game_saves (
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(community_game_id,user_id)
);

CREATE TABLE community_game_plays (
  play_id TEXT PRIMARY KEY,
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  user_id TEXT,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  correct_count INTEGER,
  puzzle_count INTEGER,
  total_response_ms INTEGER,
  score REAL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE community_game_comments (
  comment_id TEXT PRIMARY KEY,
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  user_id TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'VISIBLE',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE community_game_reports (
  report_id TEXT PRIMARY KEY,
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  reporter_user_id TEXT,
  reason_code TEXT NOT NULL,
  detail TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  resolution_note TEXT
);

CREATE TABLE community_game_remixes (
  child_game_id TEXT PRIMARY KEY REFERENCES community_games(community_game_id),
  parent_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  remixer_user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE community_share_links (
  share_code TEXT PRIMARY KEY,
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  click_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE community_game_metrics (
  community_game_id TEXT PRIMARY KEY REFERENCES community_games(community_game_id),
  impressions INTEGER NOT NULL DEFAULT 0,
  plays INTEGER NOT NULL DEFAULT 0,
  completions INTEGER NOT NULL DEFAULT 0,
  likes INTEGER NOT NULL DEFAULT 0,
  saves INTEGER NOT NULL DEFAULT 0,
  comments INTEGER NOT NULL DEFAULT 0,
  reports INTEGER NOT NULL DEFAULT 0,
  avg_score REAL,
  avg_completion_ms REAL,
  trending_score REAL NOT NULL DEFAULT 0,
  quality_score REAL NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE moderation_actions (
  action_id TEXT PRIMARY KEY,
  community_game_id TEXT NOT NULL REFERENCES community_games(community_game_id),
  moderator_user_id TEXT,
  action TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE creator_notifications (
  notification_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  notification_type TEXT NOT NULL,
  actor_user_id TEXT,
  community_game_id TEXT,
  message TEXT NOT NULL,
  read_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW v_community_trending AS
SELECT g.community_game_id,g.title,g.creator_user_id,g.competition_id,g.mechanic,
       g.difficulty_label,m.plays,m.likes,m.saves,m.comments,m.trending_score,m.quality_score
FROM community_games g JOIN community_game_metrics m USING(community_game_id)
WHERE g.publish_status='PUBLISHED' AND g.moderation_status='APPROVED' AND g.visibility='PUBLIC'
ORDER BY m.trending_score DESC,m.quality_score DESC,m.plays DESC;

CREATE VIEW v_creator_leaderboard AS
SELECT user_id,handle,display_name,is_verified,follower_count,published_count,total_plays,total_likes,creator_score
FROM creator_profiles ORDER BY creator_score DESC,total_plays DESC,follower_count DESC;

CREATE INDEX idx_community_games_creator ON community_games(creator_user_id,publish_status);

CREATE INDEX idx_community_games_status ON community_games(publish_status,moderation_status,visibility);

CREATE INDEX idx_community_plays_game ON community_game_plays(community_game_id,started_at);
