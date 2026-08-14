"""Tests for tools/director_v02/capability_gap_report.py -- the gap detector
that flags real `relationships` predicates with no registered Creator
capability yet, without auto-registering anything (see that module's own
docstring for why full auto-registration was deliberately rejected)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from tools.director_v02 import capability_gap_report as gap_report  # noqa: E402
from tools.director_v02 import registry  # noqa: E402
from tools.quiz_export import engine  # noqa: E402


def test_registered_predicates_matches_registry():
    predicates = gap_report.registered_predicates()
    assert "WON_CHAMPIONSHIP" in predicates
    assert "WON_AWARD" in predicates
    assert "DRAFTED_BY" in predicates
    assert len(predicates) == len({k[2] for k in registry.all_capability_keys()})


def test_scan_finds_the_two_new_capabilities_as_registered():
    c = engine.connect()
    try:
        report = gap_report.scan_for_capability_gaps(c)
    finally:
        c.close()
    registered_predicates = {e["predicate"] for e in report["registered"]}
    assert "WON_CHAMPIONSHIP" in registered_predicates
    assert "WON_AWARD" in registered_predicates


def test_scan_flags_a_real_known_gap_not_yet_registered():
    # PLAYED_IN_CHAMPIONSHIP (part of this session's own Wikipedia import)
    # deliberately has no registered capability -- a real, honest gap this
    # tool should surface, not silently fill in.
    c = engine.connect()
    try:
        report = gap_report.scan_for_capability_gaps(c)
    finally:
        c.close()
    all_gap_predicates = {e["predicate"] for e in report["undiscovered"]} | {
        e["predicate"] for e in report["schema_only_not_registered"]
    }
    assert "PLAYED_IN_CHAMPIONSHIP" in all_gap_predicates


def test_scan_never_mutates_the_database():
    c = engine.connect()
    try:
        before = c.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
        gap_report.scan_for_capability_gaps(c)
        after = c.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
    finally:
        c.close()
    assert before == after
