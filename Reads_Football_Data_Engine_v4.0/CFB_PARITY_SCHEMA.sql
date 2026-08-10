-- CFB parity import targets. These mirror NFL concepts.

CREATE TABLE cfb_team_seasons (
  season integer NOT NULL,
  school_id text NOT NULL,
  conference_id text,
  division text,
  wins integer,
  losses integer,
  ties integer,
  points_for integer,
  points_against integer,
  point_diff integer,
  rank_ap integer,
  rank_coaches integer,
  playoff_seed integer,
  postseason_result text,
  verification_status text NOT NULL,
  source_id text NOT NULL,
  PRIMARY KEY(season,school_id)
);

CREATE TABLE cfb_games (
  game_id text PRIMARY KEY,
  season integer NOT NULL,
  week integer,
  game_date text,
  home_school_id text NOT NULL,
  away_school_id text NOT NULL,
  home_score integer,
  away_score integer,
  stadium_id text,
  attendance integer,
  neutral_site integer,
  conference_game integer,
  verification_status text NOT NULL,
  source_id text NOT NULL
);

CREATE TABLE cfb_roster_seasons (
  season integer NOT NULL,
  school_id text NOT NULL,
  cfb_player_id text NOT NULL,
  position text,
  jersey_number integer,
  class_year text,
  hometown text,
  high_school text,
  verification_status text NOT NULL,
  source_id text NOT NULL,
  PRIMARY KEY(season,school_id,cfb_player_id)
);

CREATE TABLE cfb_player_season_stats (
  season integer NOT NULL,
  school_id text NOT NULL,
  cfb_player_id text NOT NULL,
  games integer,
  starts integer,
  passing_yards integer,
  passing_td integer,
  rushing_yards integer,
  rushing_td integer,
  receptions integer,
  receiving_yards integer,
  receiving_td integer,
  tackles real,
  sacks real,
  interceptions real,
  verification_status text NOT NULL,
  source_id text NOT NULL,
  PRIMARY KEY(season,school_id,cfb_player_id)
);

CREATE TABLE cfb_stadiums (
  stadium_id text PRIMARY KEY,
  stadium_name text NOT NULL,
  school_id text,
  city text,
  state text,
  capacity integer,
  surface text,
  open_year integer,
  verification_status text NOT NULL,
  source_id text NOT NULL
);

CREATE TABLE cfb_conferences (
  conference_id text PRIMARY KEY,
  display_name text NOT NULL,
  abbreviation text,
  subdivision text,
  verification_status text NOT NULL,
  source_id text NOT NULL
);

CREATE TABLE cfb_school_conference_history (
  school_id text NOT NULL,
  conference_id text NOT NULL,
  season_start integer NOT NULL,
  season_end integer,
  verification_status text NOT NULL,
  source_id text NOT NULL,
  PRIMARY KEY(school_id,conference_id,season_start)
);
