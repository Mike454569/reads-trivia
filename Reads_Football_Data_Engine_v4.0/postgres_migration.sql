-- Reads Football v0.8 PostgreSQL migration outline.
-- Run after base schema. This adds product, provenance, QA, telemetry, and template layers.

CREATE TABLE IF NOT EXISTS source_releases (
  release_id text PRIMARY KEY,
  source_id text NOT NULL REFERENCES sources(source_id),
  dataset_name text NOT NULL,
  release_version text,
  source_url text,
  retrieved_at timestamptz,
  sha256 text,
  license_note text,
  attribution_text text,
  transform_version text,
  import_status text NOT NULL DEFAULT 'PENDING',
  row_count bigint,
  notes text
);

CREATE TABLE IF NOT EXISTS field_provenance (
  entity_type text NOT NULL,
  entity_id text NOT NULL,
  field_name text NOT NULL,
  value_text text,
  source_id text NOT NULL REFERENCES sources(source_id),
  release_id text REFERENCES source_releases(release_id),
  verification_status text NOT NULL,
  confidence double precision,
  last_verified_at timestamptz,
  PRIMARY KEY(entity_type,entity_id,field_name,value_text,source_id)
);

CREATE TABLE IF NOT EXISTS puzzle_catalog (
  puzzle_id text PRIMARY KEY,
  mode_id text NOT NULL,
  source_entity_type text NOT NULL,
  source_entity_id text NOT NULL,
  season integer,
  difficulty_score double precision NOT NULL,
  difficulty_band text NOT NULL,
  ambiguity_score double precision NOT NULL DEFAULT 0,
  popularity_proxy double precision NOT NULL DEFAULT 0,
  eligible boolean NOT NULL DEFAULT true,
  exclusion_reason text,
  verification_status text NOT NULL,
  source_id text,
  payload_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS puzzle_attempts (
  attempt_id bigserial PRIMARY KEY,
  puzzle_id text NOT NULL REFERENCES puzzle_catalog(puzzle_id),
  user_key text,
  attempted_at timestamptz NOT NULL DEFAULT now(),
  correct boolean NOT NULL,
  solve_ms integer,
  wrong_guess_count integer NOT NULL DEFAULT 0,
  hint_count integer NOT NULL DEFAULT 0,
  abandoned boolean NOT NULL DEFAULT false,
  device_class text,
  player_rating_before double precision
);

CREATE TABLE IF NOT EXISTS user_error_reports (
  report_id bigserial PRIMARY KEY,
  puzzle_id text REFERENCES puzzle_catalog(puzzle_id),
  user_key text,
  report_type text NOT NULL,
  message text,
  submitted_at timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'OPEN'
);

CREATE INDEX IF NOT EXISTS puzzle_catalog_lookup_idx
  ON puzzle_catalog(mode_id,eligible,difficulty_band,difficulty_score);

CREATE INDEX IF NOT EXISTS puzzle_attempts_lookup_idx
  ON puzzle_attempts(puzzle_id,attempted_at);
