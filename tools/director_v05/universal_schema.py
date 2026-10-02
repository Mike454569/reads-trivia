"""SQLite schema for universal sourced facts/events and derived intelligence."""
DDL=r"""
CREATE TABLE IF NOT EXISTS universal_event (
 event_id TEXT PRIMARY KEY,
 event_type TEXT NOT NULL,
 league TEXT,
 event_date TEXT,
 title TEXT NOT NULL,
 neutral_summary TEXT NOT NULL,
 source_url TEXT NOT NULL,
 source_publisher TEXT NOT NULL,
 source_date TEXT,
 evidence_tier TEXT NOT NULL,
 verification_status TEXT NOT NULL DEFAULT 'PENDING',
 jurisdiction TEXT,
 legal_stage TEXT,
 allegation_or_offense TEXT,
 disposition TEXT,
 disposition_date TEXT,
 sensitive INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_universal_event_type_date ON universal_event(event_type,event_date);
CREATE INDEX IF NOT EXISTS ix_universal_event_verify ON universal_event(verification_status,evidence_tier);

CREATE TABLE IF NOT EXISTS universal_event_evidence (
 event_id TEXT NOT NULL REFERENCES universal_event(event_id) ON DELETE CASCADE,
 source_url TEXT NOT NULL,
 publisher TEXT NOT NULL,
 published_date TEXT,
 evidence_tier TEXT NOT NULL,
 supports_fields_json TEXT NOT NULL DEFAULT '[]',
 PRIMARY KEY(event_id,source_url)
);
CREATE INDEX IF NOT EXISTS ix_event_evidence_event ON universal_event_evidence(event_id,evidence_tier);

CREATE TABLE IF NOT EXISTS universal_event_subject (
 event_id TEXT NOT NULL REFERENCES universal_event(event_id) ON DELETE CASCADE,
 subject_type TEXT NOT NULL,
 subject_id TEXT NOT NULL,
 role TEXT,
 PRIMARY KEY(event_id,subject_type,subject_id,role)
);
CREATE INDEX IF NOT EXISTS ix_universal_subject ON universal_event_subject(subject_type,subject_id);

CREATE TABLE IF NOT EXISTS universal_event_tag (
 event_id TEXT NOT NULL REFERENCES universal_event(event_id) ON DELETE CASCADE,
 tag TEXT NOT NULL,
 PRIMARY KEY(event_id,tag)
);
CREATE INDEX IF NOT EXISTS ix_universal_tag ON universal_event_tag(tag);

CREATE TABLE IF NOT EXISTS universal_derived_fact (
 derived_id TEXT PRIMARY KEY,
 metric TEXT NOT NULL,
 subject_type TEXT NOT NULL,
 subject_id TEXT NOT NULL,
 value_num REAL,
 value_text TEXT,
 formula_version TEXT NOT NULL,
 input_fact_ids_json TEXT NOT NULL,
 eligible_for_gameplay INTEGER NOT NULL DEFAULT 0,
 computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_universal_derived_metric ON universal_derived_fact(metric,eligible_for_gameplay);

CREATE TABLE IF NOT EXISTS universal_fact_evidence (
 fact_id TEXT NOT NULL,
 source_url TEXT NOT NULL,
 publisher TEXT NOT NULL,
 published_date TEXT,
 evidence_tier TEXT NOT NULL,
 retrieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(fact_id,source_url)
);
"""

def install(conn):
    conn.executescript(DDL)
    conn.commit()
