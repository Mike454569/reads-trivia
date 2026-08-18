"""Capability catalog -- schema + one-time backfill migration.

Reliability-design Phase 1 (approved design: relationship catalog + truthful
lifecycle states, revised three times before implementation was authorized).
This is a real, machine-readable catalog of what the Game Creator can
actually generate -- built specifically to make the failure mode "a
capability was labeled SUPPORTED but generation returned a real runtime
error" structurally impossible: SUPPORTED must trace to a recorded,
verified lifecycle state, never to registry presence alone.

This is a MIGRATION, not a recurring data refresh (unlike every other
module in tools/data_refresh/), so it deliberately does NOT register itself
in refresh_runs or admin_refresh.py's dispatcher -- there is nothing here
for a schedule to re-pull periodically. It still uses the exact same
backup-before/verify-after/restore-on-failure safety net
(safety.create_verified_backup / safety.restore_from_backup) as every other
DB-mutating script in this project, because the risk profile (a bug here
could corrupt the Engine DB) is the same regardless of whether the trigger
is a schedule or a one-time `python -m` invocation.

Two tables:
  capability_catalog       -- one row per real (mechanic, domain, predicate)
                               relationship the Creator can generate from
  mechanic_taxonomy         -- reference list of known game-mechanic SHAPES
                               (seeded with the 2 that exist today; the other
                               4 named in the approved design are seeded as
                               NOT_STARTED placeholders, not fabricated as
                               built)

Backfill: reads `tools.director_v02.registry.CAPABILITY_REGISTRY` directly
(the real, live source of truth -- never re-derived from parsed text) and
creates one catalog row per entry, `verification_status=
LEGACY_PUBLIC_PENDING_REVALIDATION` (never HUMAN_APPROVED -- these are
grandfathered by real production runtime, not newly certified under this
process) and `public_availability=PUBLIC_ENABLED` (preserving today's real,
unchanged availability). Real count found live at backfill time: 21
capabilities, not the 27 referenced during design discussion -- the
discrepancy is disclosed, not silently reconciled; it most likely reflects
the 6 CFBD Engine-data-refresh domains added this same session, which are
real Engine datasets but not Creator game-generation capabilities and do
not belong in this catalog.

Coverage/identity-resolution/season-range fields are left NULL for every
backfilled row, not estimated -- filling them in with a real, measured
number is exactly the job of the "gradual audit of the 27 [sic 21] existing
capabilities" phase, not this one. Guessing a plausible-looking number here
would be the same category of dishonesty this whole design exists to
eliminate.
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.data_refresh import safety  # noqa: E402

# Every valid lifecycle state. LEGACY_PUBLIC_PENDING_REVALIDATION is reachable
# ONLY via this backfill -- catalog.py's transition() function (Phase 1,
# lifecycle-enforcement module) never allows any other state to transition
# INTO it, and it is not part of the normal forward progression.
VALID_LIFECYCLE_STATES = frozenset({
    "DISCOVERED", "DATA_PRESENT", "STRUCTURALLY_VALIDATED", "IMPLEMENTED",
    "GENERATION_VERIFIED", "HUMAN_APPROVED", "PUBLIC_ENABLED",
    "LEGACY_PUBLIC_PENDING_REVALIDATION", "BLOCKED",
})


def _ensure_schema(c) -> None:
    c.execute("""
        CREATE TABLE IF NOT EXISTS capability_catalog (
            capability_id               TEXT PRIMARY KEY,
            version                     INTEGER NOT NULL DEFAULT 1,
            mechanic                    TEXT NOT NULL,
            domain                      TEXT NOT NULL,
            relationship_predicate      TEXT NOT NULL,

            input_entity_type           TEXT,
            input_scoping_fields        TEXT,
            output_entity_type          TEXT,

            source_tables               TEXT,
            source_columns               TEXT,
            required_joins               TEXT,
            canonical_identity_fields    TEXT,
            identity_resolution_method   TEXT,
            identity_resolution_rate     REAL,

            season_coverage_min         INTEGER,
            season_coverage_max         INTEGER,
            season_coverage_notes        TEXT,
            team_or_school_coverage      TEXT,
            player_coverage              TEXT,
            game_coverage                 TEXT,

            source_id                    TEXT,
            refresh_dataset_key          TEXT,
            freshness_category           TEXT,
            freshness_notes               TEXT,

            tie_rule                     TEXT,
            ambiguity_rule                TEXT,
            eligible_answer_rule          TEXT,
            distractor_scoping_rule       TEXT,
            min_candidate_pool_size       INTEGER,

            known_limitations             TEXT,

            -- Declarative-contract fields (revision 3, §2) -- nullable in
            -- Phase 1; populated during the gradual audit, never guessed now.
            input_entity_types            TEXT,
            output_entity_types           TEXT,
            canonical_join_keys            TEXT,
            season_scope                   TEXT,
            cardinality                     TEXT,
            safe_chain_eligible             INTEGER,
            ambiguity_behavior               TEXT,
            provenance_compatibility_tag     TEXT,
            combination_denied_with          TEXT,
            requires_custom_review           INTEGER,

            -- Creator-Intelligence-layer field (revision 3, §1) -- nullable
            -- in Phase 1; the Intelligence layer itself is a later phase.
            gameplay_archetype               TEXT,
            supported_round_structures        TEXT,

            verification_status               TEXT NOT NULL,
            human_review_status                TEXT,
            compiler_support                    TEXT NOT NULL DEFAULT 'HAND_WRITTEN',
            runtime_adapter_module               TEXT,
            public_availability                  TEXT NOT NULL,

            last_validation_report_id             TEXT,
            last_validated_at                      TEXT,
            created_at                              TEXT NOT NULL,
            updated_at                               TEXT NOT NULL,

            UNIQUE (mechanic, domain, relationship_predicate)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS mechanic_taxonomy (
            taxonomy_id                TEXT PRIMARY KEY,
            display_name                TEXT NOT NULL,
            description                  TEXT,
            creator_pipeline_supported    INTEGER NOT NULL DEFAULT 0,
            app_hand_built_elsewhere       INTEGER NOT NULL DEFAULT 0,
            min_required_catalog_fields     TEXT,
            created_at                       TEXT NOT NULL
        )
    """)
    c.commit()
    _migrate_add_template_status_column(c)


# Reliability Design Phase 6: real production-readiness status per template,
# distinct from creator_pipeline_supported (which only ever meant "the
# Creator pipeline knows this taxonomy exists", not "a real, tested,
# client-safe, no-leakage round can actually be generated and played" --
# exactly the ambiguity Phase 5's false-playability bug exploited). A plain
# ALTER TABLE (not a table rebuild) since sqlite3 supports ADD COLUMN
# directly and every existing row gets the same honest default.
_TEMPLATE_STATUS_VALUES = frozenset({"NOT_BUILT", "SCHEMA_ONLY", "PRODUCTION_READY"})


def _migrate_add_template_status_column(c) -> None:
    cols = {row[1] for row in c.execute("PRAGMA table_info(mechanic_taxonomy)")}
    if "template_status" not in cols:
        c.execute("ALTER TABLE mechanic_taxonomy ADD COLUMN template_status TEXT NOT NULL DEFAULT 'NOT_BUILT'")
        c.commit()


def set_template_status(c, taxonomy_id: str, status: str) -> None:
    if status not in _TEMPLATE_STATUS_VALUES:
        raise ValueError(f"status must be one of {sorted(_TEMPLATE_STATUS_VALUES)}, got {status!r}")
    c.execute("UPDATE mechanic_taxonomy SET template_status=? WHERE taxonomy_id=?", (status, taxonomy_id))
    c.commit()


_TAXONOMY_SEED = [
    # The 2 that genuinely exist and are wired through game_director_v01.py today.
    ("MULTIPLE_CHOICE_SINGLE_FACT", "Multiple-choice identification",
     "Single input entity -> single output value, 4 real options.", 1, 1, None),
    ("PROGRESSIVE_CLUE_IDENTIFY", "Progressive clue reveal",
     "One entity, 3-5 independently verified clues revealed in order.", 1, 1, None),
    # The other 4 named in the approved design -- seeded as real placeholders,
    # NOT fabricated as built. creator_pipeline_supported=0 is the honest,
    # load-bearing fact here.
    ("MATCHING", "Matching", "Real N:N or 1:1 mapping between two entity sets.", 0, 0, None),
    ("SORTING_TIMELINE", "Sorting / timeline ordering",
     "Entity set with a real, unambiguous, tie-free orderable attribute.", 0, 0, None),
    ("HIGHER_LOWER_STREAK", "Higher/lower streak",
     "Real, directly comparable numeric value between two same-type entities.", 0, 1, None),
    ("ELIMINATION_SURVIVAL", "Elimination / category survival",
     "Real, unambiguous category-membership test.", 0, 0, None),
    # Reliability Design Phase 6: formalizes the pre-existing POSITION_LINEUP /
    # POSITION_LINEUP_COLLEGE visual templates (tools/director_v02/
    # visual_templates.py, engine-game-ui.js's renderPositionLineupBoard/
    # renderPositionLineupCollegeBoard) as their own real taxonomy entry --
    # same underlying "guess" mechanic/answer contract as
    # MULTIPLE_CHOICE_SINGLE_FACT, but a genuinely different round shape
    # (a position board, not a plain question sentence), so Creator-facing
    # diversity treats it as its own template rather than silently
    # collapsing into MATCHING (the bug this phase's audit found in
    # concepts.py's old domain-substring compatibility rule).
    ("POSITION_LINEUP_GRID", "Position lineup board",
     "A real team-season's starting offense, shown by position, guessed by team (and optionally season).", 1, 1, None),
]


def _seed_taxonomy(c) -> int:
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    inserted = 0
    for taxonomy_id, display_name, description, pipeline_supported, hand_built, min_fields in _TAXONOMY_SEED:
        cur = c.execute(
            "INSERT OR IGNORE INTO mechanic_taxonomy(taxonomy_id, display_name, description, "
            "creator_pipeline_supported, app_hand_built_elsewhere, min_required_catalog_fields, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (taxonomy_id, display_name, description, pipeline_supported, hand_built, min_fields, now),
        )
        inserted += cur.rowcount
    return inserted


def _capability_id(domain: str, predicate: str) -> str:
    return f"{domain}__{predicate}"


def backfill_legacy_capabilities(c) -> dict:
    """Reads the REAL, live registry.CAPABILITY_REGISTRY (never a parsed
    copy) and inserts one catalog row per entry that doesn't already exist.
    Idempotent -- re-running never duplicates or overwrites a row a later
    phase has already moved off LEGACY_PUBLIC_PENDING_REVALIDATION."""
    from tools.director_v02 import registry

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    inserted = 0
    skipped_existing = 0
    rows_report = []

    for (mechanic, domain, predicate), cap in registry.CAPABILITY_REGISTRY.items():
        capability_id = _capability_id(domain, predicate)
        existing = c.execute(
            "SELECT capability_id FROM capability_catalog WHERE capability_id=?", (capability_id,)
        ).fetchone()
        if existing:
            skipped_existing += 1
            continue

        adapter = cap.get("adapter")
        adapter_module_path = getattr(adapter, "__name__", None)
        known_limitations = list(cap.get("known_limitations", []))

        c.execute(
            "INSERT INTO capability_catalog("
            "capability_id, version, mechanic, domain, relationship_predicate, "
            "input_entity_type, output_entity_type, known_limitations, "
            "verification_status, human_review_status, compiler_support, "
            "runtime_adapter_module, public_availability, created_at, updated_at"
            ") VALUES (?,1,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                capability_id, mechanic, domain, predicate,
                cap.get("entity_type"), cap.get("answer_type"),
                json.dumps(known_limitations),
                "LEGACY_PUBLIC_PENDING_REVALIDATION", "LEGACY_GRANDFATHERED", "HAND_WRITTEN",
                adapter_module_path, "PUBLIC_ENABLED", now, now,
            ),
        )
        inserted += 1
        rows_report.append({
            "capability_id": capability_id, "mechanic": mechanic, "domain": domain,
            "predicate": predicate, "runtime_adapter_module": adapter_module_path,
        })

    return {"inserted": inserted, "skipped_existing": skipped_existing, "rows": rows_report}


def run_capability_catalog_migration() -> dict:
    backup = safety.create_verified_backup()
    try:
        c = engine_bootstrap.connect()
        c.execute("BEGIN")
        try:
            _ensure_schema(c)
            taxonomy_inserted = _seed_taxonomy(c)
            backfill_result = backfill_legacy_capabilities(c)
            c.commit()
        except Exception:
            c.rollback()
            raise

        integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"PRAGMA integrity_check failed after migration: {integrity}")
        fk_errors = c.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"{len(fk_errors)} foreign_key_check violation(s) after migration")

        total_catalog_rows = c.execute("SELECT COUNT(*) FROM capability_catalog").fetchone()[0]
        by_status = c.execute(
            "SELECT verification_status, COUNT(*) FROM capability_catalog GROUP BY verification_status"
        ).fetchall()
        c.close()
        return {
            "status": "SUCCESS",
            "taxonomy_rows_inserted": taxonomy_inserted,
            "capability_rows_inserted": backfill_result["inserted"],
            "capability_rows_already_present": backfill_result["skipped_existing"],
            "total_catalog_rows": total_catalog_rows,
            "counts_by_status": {row[0]: row[1] for row in by_status},
            "backfilled_capabilities": backfill_result["rows"],
            "backup_id": backup["backup_id"],
        }
    except Exception as e:
        restore_info = safety.restore_from_backup(backup["path"])
        return {"status": "FAILED_RESTORED", "reason": repr(e), "backup": backup, "restore": restore_info}
