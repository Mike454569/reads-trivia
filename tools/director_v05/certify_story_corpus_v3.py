"""Story Volume Certification v3.

Produces the hard corpus accounting required before treating Story Factory
volume as production-ready. This is read-only: it never promotes candidates or
changes question status.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from .story_factory_health import story_factory_health

READY_STATUSES = ("READY_FOR_BANK", "READY_FOR_FORMAT_BANK")
REQUIRED_FAMILIES = (
    "BIZARRE_MOMENT",
    "DRAFT_BUST",
    "TRADE_ODDITY",
    "DISCIPLINE_LEGAL",
    "COMEBACK_RETURN",
    "SIDELINE_INCIDENT",
    "COACHING_MELTDOWN",
    "CELEBRATION_CONTROVERSY",
    "RECRUITING_CHAOS",
    "RECORD_ODDITY",
    "INFAMOUS_MISTAKE",
    "OFF_FIELD_ODDITY",
    "RIVALRY_INCIDENT",
    "TRANSFER_NIL_CHAOS",
    "PLAYOFF_FORGOTTEN",
)


def _tables(conn):
    return {
        str(r[0])
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _count_map(conn, sql, params=()):
    return {
        str(r[0] or "UNKNOWN"): int(r[1])
        for r in conn.execute(sql, params).fetchall()
    }


def certify_story_corpus(
    *,
    min_verified_story_events=3000,
    min_playable_story_questions=20000,
    min_each_league=1,
):
    readiness = engine_bootstrap.check_engine_readiness()
    if not readiness.get("ready"):
        return {
            "certification": "STORY_VOLUME_V3",
            "status": "BLOCKED",
            "promotion_ready": False,
            "errors": [readiness.get("reason_code") or "ENGINE_NOT_READY"],
        }

    conn = engine_bootstrap.connect()
    try:
        tables = _tables(conn)
        health = story_factory_health(conn)

        verified_events = int(conn.execute(
            "SELECT COUNT(*) FROM universal_event WHERE verification_status='VERIFIED'"
        ).fetchone()[0])

        verified_story_events = 0
        verified_story_by_category = {}
        if "football_story_enrichment" in tables and "football_story_candidates" in tables:
            verified_story_events = int(conn.execute(
                """SELECT COUNT(DISTINCT e.promoted_event_id)
                   FROM football_story_enrichment e
                   JOIN universal_event u ON u.event_id=e.promoted_event_id
                   WHERE e.decision='AUTO_PROMOTED'
                     AND e.promoted_event_id IS NOT NULL
                     AND u.verification_status='VERIFIED'"""
            ).fetchone()[0])
            verified_story_by_category = _count_map(
                conn,
                """SELECT c.family_hint,COUNT(DISTINCT e.promoted_event_id)
                   FROM football_story_enrichment e
                   JOIN football_story_candidates c ON c.candidate_id=e.candidate_id
                   JOIN universal_event u ON u.event_id=e.promoted_event_id
                   WHERE e.decision='AUTO_PROMOTED'
                     AND e.promoted_event_id IS NOT NULL
                     AND u.verification_status='VERIFIED'
                   GROUP BY c.family_hint
                   ORDER BY 2 DESC"""
            )

        playable_story_questions = 0
        questions_per_mechanic = {}
        league_split = {}
        ready_by_family = {}
        if "story_generated_questions" in tables:
            marks = ",".join("?" for _ in READY_STATUSES)
            playable_story_questions = int(conn.execute(
                f"""SELECT COUNT(*) FROM story_generated_questions
                    WHERE status IN ({marks})""",
                READY_STATUSES,
            ).fetchone()[0])
            questions_per_mechanic = _count_map(
                conn,
                f"""SELECT mechanic,COUNT(*)
                    FROM story_generated_questions
                    WHERE status IN ({marks})
                    GROUP BY mechanic ORDER BY 2 DESC""",
                READY_STATUSES,
            )
            league_split = _count_map(
                conn,
                f"""SELECT COALESCE(u.league,'UNKNOWN'),COUNT(*)
                    FROM story_generated_questions q
                    LEFT JOIN universal_event u ON u.event_id=q.event_id
                    WHERE q.status IN ({marks})
                    GROUP BY COALESCE(u.league,'UNKNOWN')
                    ORDER BY 2 DESC""",
                READY_STATUSES,
            )
            if "football_story_candidates" in tables:
                ready_by_family = _count_map(
                    conn,
                    f"""SELECT c.family_hint,COUNT(*)
                        FROM story_generated_questions q
                        JOIN football_story_candidates c ON c.candidate_id=q.candidate_id
                        WHERE q.status IN ({marks})
                        GROUP BY c.family_hint
                        ORDER BY 2 DESC""",
                    READY_STATUSES,
                )

        candidate_status = {}
        candidate_families = {}
        source_domains = {}
        source_tiers = {}
        duplicates_rejected = 0
        weak_copy_rejects = 0
        sensitive_review_held = 0
        review_held_total = 0
        if "football_story_candidates" in tables:
            candidate_status = _count_map(
                conn,
                "SELECT status,COUNT(*) FROM football_story_candidates GROUP BY status ORDER BY 2 DESC",
            )
            candidate_families = _count_map(
                conn,
                "SELECT family_hint,COUNT(*) FROM football_story_candidates GROUP BY family_hint ORDER BY 2 DESC",
            )
            source_domains = _count_map(
                conn,
                "SELECT domain,COUNT(*) FROM football_story_candidates GROUP BY domain ORDER BY 2 DESC",
            )
            source_tiers = _count_map(
                conn,
                "SELECT evidence_tier_hint,COUNT(*) FROM football_story_candidates GROUP BY evidence_tier_hint ORDER BY 2 DESC",
            )
            duplicates_rejected = int(candidate_status.get("REJECT_NEAR_DUPLICATE", 0))
            weak_copy_rejects += int(candidate_status.get("REJECT_LOW_SIGNAL", 0))
            sensitive_review_held = int(candidate_status.get("REVIEW_REQUIRED_SENSITIVE", 0))
            review_held_total = sum(
                n for status, n in candidate_status.items()
                if status.startswith("REVIEW_REQUIRED")
            )

        processing_rejects = Counter()
        if "story_candidate_processing" in tables:
            for row in conn.execute(
                """SELECT COALESCE(last_error,''),COUNT(*)
                   FROM story_candidate_processing
                   WHERE last_error IS NOT NULL AND TRIM(last_error)<>''
                   GROUP BY last_error"""
            ).fetchall():
                err = str(row[0])
                n = int(row[1])
                if "STORY_V2_ROBOTIC_COPY" in err or "QUALITY_BELOW_THRESHOLD" in err:
                    weak_copy_rejects += n
                processing_rejects[err.split(":", 1)[0]] += n

        missing_families = [
            family for family in REQUIRED_FAMILIES
            if int(candidate_families.get(family, 0)) <= 0
        ]
        nfl = int(league_split.get("NFL", 0))
        cfb = int(league_split.get("CFB", 0))
        league_floor_met = nfl >= int(min_each_league) and cfb >= int(min_each_league)
        target_met = (
            verified_story_events >= int(min_verified_story_events)
            and playable_story_questions >= int(min_playable_story_questions)
            and league_floor_met
            and not missing_families
        )

        return {
            "certification": "STORY_VOLUME_V3",
            "status": "PASSED" if target_met else "NEEDS_MORE_VOLUME",
            "promotion_ready": target_met,
            "targets": {
                "verified_story_events": int(min_verified_story_events),
                "playable_story_questions": int(min_playable_story_questions),
                "minimum_each_league": int(min_each_league),
            },
            "verified_events_all_engine": verified_events,
            "verified_story_events": verified_story_events,
            "verified_story_events_by_category": verified_story_by_category,
            "playable_story_questions": playable_story_questions,
            "questions_per_mechanic": questions_per_mechanic,
            "nfl_vs_cfb": league_split,
            "playable_questions_by_category": ready_by_family,
            "duplicates_rejected": duplicates_rejected,
            "sensitive_review_held": sensitive_review_held,
            "review_held_total": review_held_total,
            "weak_copy_rejects": weak_copy_rejects,
            "processing_reject_classes": dict(processing_rejects),
            "source_coverage": {
                "domains": source_domains,
                "evidence_tiers": source_tiers,
                "domain_count": len(source_domains),
            },
            "candidate_status": candidate_status,
            "candidate_families": candidate_families,
            "required_families": list(REQUIRED_FAMILIES),
            "missing_required_families": missing_families,
            "league_floor_met": league_floor_met,
            "factory_health": health,
            "database_version": readiness.get("database_version"),
            "database_size_bytes": readiness.get("db_size_bytes"),
        }
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-verified-story-events", type=int, default=3000)
    ap.add_argument("--min-playable-story-questions", type=int, default=20000)
    ap.add_argument("--min-each-league", type=int, default=1)
    ap.add_argument("--enforce-targets", action="store_true")
    args = ap.parse_args()
    result = certify_story_corpus(
        min_verified_story_events=args.min_verified_story_events,
        min_playable_story_questions=args.min_playable_story_questions,
        min_each_league=args.min_each_league,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.enforce_targets and not result.get("promotion_ready"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
