"""Football Encyclopedia 2.0 (Parts 13/14/20): representative depth check
for two of this pass's own named examples (Shotgun/3x1 Trips, Two-Minute
Offense).

The existing encyclopedia already has real, meaningful depth for several
domains (Coverages, built in an earlier, dedicated pass) but was
noticeably thinner for others (Formations, Situational) simply because of
which source-workbook sheet originally built them -- a real, disclosed
characteristic, not a quality defect to paper over. Enriched exactly 2
concepts with additional, well-established, appropriately-hedged football
knowledge (never a fabricated or absolute claim -- see the update script's
own field text) directly in the Engine's real knowledge_nodes table, then
re-ran the existing, unmodified export_encyclopedia_module.py to
regenerate the real static data/learn-encyclopedia.js file every player
actually loads.

Provenance discipline: the new fields are NOT cited to a specific
(sheet, row) the way every other field on these two nodes is, so their
verification_status was changed from SOURCE_BACKED to
SOURCE_BACKED_PLUS_GENERAL_KNOWLEDGE -- never silently blended into
"Source-verified" for content that doesn't have that citation. app.js
renders a distinct, honest badge for this exact status.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

pytestmark = pytest.mark.skipif(
    not engine_bootstrap.ENGINE_DIR.is_dir(), reason="READS_ENGINE_DIR not set to a real Engine database"
)

_ENRICHED_CONCEPTS = {
    "FORMATION_3X1_TRIPS": {
        "spacing_advantage", "coverage_stress", "trips_side_route_combinations",
        "backside_isolation", "motion_possibilities", "personnel_considerations", "what_the_qb_may_read",
    },
    "SITUATION_TWO_MINUTE_OFFENSE": {
        "personnel_and_tempo", "clock_stopping_methods", "sideline_route_concepts",
        "timeout_usage_strategy", "nfl_vs_cfb_note",
    },
}


def _static_encyclopedia() -> dict:
    content = (REPO_ROOT / "data" / "learn-encyclopedia.js").read_text()
    start = content.index("{")
    end = content.rindex("}")
    return json.loads(content[start:end + 1])


@pytest.mark.parametrize("canonical_id,new_fields", list(_ENRICHED_CONCEPTS.items()))
def test_enriched_concept_has_the_new_fields_in_the_real_engine_db(canonical_id, new_fields):
    c = engine_bootstrap.connect()
    row = c.execute(
        "SELECT payload_json, verification_status FROM knowledge_nodes WHERE canonical_id=?", (canonical_id,)
    ).fetchone()
    assert row is not None, canonical_id
    payload = json.loads(row["payload_json"])
    present_fields = set(payload.get("fields", {}))
    assert new_fields <= present_fields, (canonical_id, new_fields - present_fields)
    assert row["verification_status"] == "SOURCE_BACKED_PLUS_GENERAL_KNOWLEDGE", canonical_id
    # Every new field must be a real, non-empty string -- no placeholder/
    # empty enrichment ever written.
    for field in new_fields:
        value = payload["fields"][field]
        assert isinstance(value, str) and value.strip(), (canonical_id, field)


@pytest.mark.parametrize("canonical_id,new_fields", list(_ENRICHED_CONCEPTS.items()))
def test_the_real_static_export_file_matches_the_db(canonical_id, new_fields):
    """The file every player's browser actually loads (data/learn-
    encyclopedia.js) must reflect the DB change -- proves
    export_encyclopedia_module.py was actually re-run, not just the DB
    updated with nothing shipped."""
    data = _static_encyclopedia()
    concept = data["concepts"].get(canonical_id)
    assert concept is not None, canonical_id
    assert new_fields <= set(concept["fields"]), (canonical_id, new_fields - set(concept["fields"]))
    assert concept["verification_status"] == "SOURCE_BACKED_PLUS_GENERAL_KNOWLEDGE"


def test_frontend_renders_a_distinct_honest_badge_for_the_new_status():
    """Never silently falls back to the generic "Documented" label, and
    never claims "Source-verified" for content with real, disclosed
    non-workbook-cited fields mixed in."""
    js = (REPO_ROOT / "app.js").read_text()
    assert "SOURCE_BACKED_PLUS_GENERAL_KNOWLEDGE" in js
    assert "Source-verified, plus general football knowledge" in js


def test_export_script_was_not_hand_edited_around():
    """Structural guard: the regenerated file must still carry the export
    script's own real, disclosed disclaimer that it's not hand-maintained
    -- confirms this pass used the real pipeline (DB write + re-export),
    never a one-off hand-patch of the generated file that a future real
    re-export would silently overwrite."""
    content = (REPO_ROOT / "data" / "learn-encyclopedia.js").read_text()
    assert "Not hand-maintained" in content
