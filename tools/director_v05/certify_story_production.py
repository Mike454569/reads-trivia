"""Unified real-DB certification for the Story Factory.

Runs read-only diagnostics over the configured Engine database and produces
one operator-facing remediation queue. This intentionally does not harvest or
promote new stories; it certifies the current production state first.
"""
from __future__ import annotations

import json
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from .story_factory_health import story_factory_health
from .certify_story_question_quality import certify_story_question_quality
from .certify_story_game_reach import certify_story_game_reach


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _rejection_breakdown(conn):
    tables = _tables(conn)
    out = {
        "candidate_status": {},
        "enrichment_reasons": {},
        "review_risk_flags": {},
        "top_unresolved_subjects": [],
        "article_fetch_failures": 0,
        "confidence_failures": 0,
        "identity_failures": 0,
        "family_evidence_failures": 0,
    }

    if "football_story_candidates" in tables:
        rows = conn.execute(
            """SELECT status,COUNT(*) n
               FROM football_story_candidates
               GROUP BY status ORDER BY n DESC"""
        ).fetchall()
        out["candidate_status"] = {str(r["status"]): int(r["n"]) for r in rows}

    if "football_story_enrichment" in tables:
        rows = conn.execute(
            """SELECT COALESCE(decision_reason,'') reason,COUNT(*) n
               FROM football_story_enrichment
               WHERE decision!='AUTO_PROMOTED'
               GROUP BY COALESCE(decision_reason,'')
               ORDER BY n DESC"""
        ).fetchall()
        out["enrichment_reasons"] = {
            (str(r["reason"]) or "UNSPECIFIED"): int(r["n"])
            for r in rows
        }
        for reason, n in out["enrichment_reasons"].items():
            if reason.startswith("ARTICLE_FETCH:"):
                out["article_fetch_failures"] += n
            elif reason.startswith("CONFIDENCE_BELOW_THRESHOLD"):
                out["confidence_failures"] += n
            elif reason == "NO_SINGLE_CANONICAL_PERSON_SUBJECT":
                out["identity_failures"] += n
            elif reason == "NO_FAMILY_SPECIFIC_EVIDENCE":
                out["family_evidence_failures"] += n

    if "story_review_suggestions" in tables:
        flags = Counter()
        rows = conn.execute(
            """SELECT risk_flags_json
               FROM story_review_suggestions
               WHERE status='SUGGESTED_ONLY'"""
        ).fetchall()
        for row in rows:
            try:
                values = json.loads(row["risk_flags_json"] or "[]")
            except Exception:
                values = []
            flags.update(str(x) for x in values)
        out["review_risk_flags"] = dict(flags.most_common(25))

        unresolved = conn.execute(
            """SELECT c.title,c.domain,c.family_hint,s.confidence,s.risk_flags_json
               FROM story_review_suggestions s
               JOIN football_story_candidates c ON c.candidate_id=s.candidate_id
               WHERE s.status='SUGGESTED_ONLY'
                 AND s.suggested_subject_id IS NULL
               ORDER BY s.confidence DESC,c.seen_date DESC
               LIMIT 25"""
        ).fetchall()
        out["top_unresolved_subjects"] = [dict(r) for r in unresolved]

    return out


def _remediation_queue(health, quality, reach, rejects):
    items = []

    def add(priority, code, title, detail, metric=None):
        items.append({
            "priority": int(priority),
            "code": code,
            "title": title,
            "detail": detail,
            "metric": metric,
        })

    candidates = int(health.get("candidate_total") or 0)
    promoted = int(health.get("promoted_events") or 0)
    ready = int(health.get("ready_for_bank") or 0)
    format_ready = int(health.get("ready_for_format_bank") or 0)
    review_backlog = int(health.get("review_backlog") or 0)
    sensitive_backlog = int(health.get("sensitive_backlog") or 0)

    if candidates < 1000:
        add(
            100, "CORPUS_TOO_SMALL", "Scale candidate harvest",
            "The Story Factory has fewer than 1,000 harvested candidates. "
            "Run/widen the approved-source harvest before judging long-term variety.",
            candidates,
        )

    if candidates and promoted / max(1, candidates) < 0.03:
        add(
            98, "LOW_PROMOTION_RATE", "Fix promotion bottlenecks",
            "Fewer than 3% of harvested candidates are becoming verified lore. "
            "Use the rejection breakdown below to target extraction, identity, or evidence gates.",
            round(promoted / max(1, candidates), 4),
        )

    if rejects["identity_failures"] >= 10:
        add(
            97, "IDENTITY_RESOLUTION_GAP", "Expand canonical identity coverage",
            "Many otherwise useful stories fail because one unique canonical person subject cannot be resolved.",
            rejects["identity_failures"],
        )

    if rejects["article_fetch_failures"] >= 10:
        add(
            96, "ARTICLE_EXTRACTION_GAP", "Harden article extraction",
            "Approved-source pages are failing extraction often enough to suppress corpus growth.",
            rejects["article_fetch_failures"],
        )

    if rejects["family_evidence_failures"] >= 10:
        add(
            94, "FAMILY_CLASSIFICATION_GAP", "Improve story-family evidence detection",
            "Articles are being fetched and identified but do not meet family-specific evidence rules.",
            rejects["family_evidence_failures"],
        )

    if quality.get("status") == "FAILED":
        add(
            99, "QUESTION_QA_FAILURES", "Fix generated-question QA failures",
            "Persisted story questions are failing gameplay/provenance certification. "
            "No broad promotion should happen until these are cleared.",
            int(quality.get("failed") or 0),
        )

    if ready < 25:
        add(
            93, "TOO_FEW_PLAYABLE_MCQS", "Increase playable story-question yield",
            "Fewer than 25 story questions are currently ready for general game shells.",
            ready,
        )

    if format_ready < 10:
        add(
            89, "TOO_FEW_MULTIFORMAT_QUESTIONS", "Increase multi-format story yield",
            "The Story Factory does not yet have enough Common Link/Fact-Fake/Matching/chronology output for strong rotation.",
            format_ready,
        )

    leagues = health.get("league_balance") or {}
    nfl = int(leagues.get("NFL") or 0)
    cfb = int(leagues.get("CFB") or 0)
    total_league = nfl + cfb
    if total_league >= 20:
        smaller = min(nfl, cfb)
        if smaller / max(1, total_league) < 0.30:
            add(
                91, "NFL_CFB_IMBALANCE", "Rebalance NFL and CFB story coverage",
                "One league has less than 30% of promoted story events.",
                {"NFL": nfl, "CFB": cfb},
            )

    if not reach.get("corpus_ready"):
        add(
            95, "GAME_REACH_BLOCKED_BY_EMPTY_POOL", "Populate the story question pool",
            "The game integrations exist, but certification cannot prove reach until real story questions are present.",
            ready,
        )
    elif not reach.get("promotion_ready"):
        add(
            92, "GAME_REACH_INCOMPLETE", "Fix game-shell story reach",
            "The real package builders do not yet show story content across enough compatible games.",
            {
                "reached": int(reach.get("games_with_story_content") or 0),
                "tested": int(reach.get("games_tested") or 0),
            },
        )

    if review_backlog >= 500:
        add(
            85, "REVIEW_BACKLOG_HIGH", "Work the safe review backlog",
            "The non-sensitive review queue is large enough to become the limiting factor.",
            review_backlog,
        )

    if sensitive_backlog >= 100:
        add(
            70, "SENSITIVE_BACKLOG_HIGH", "Review sensitive stories separately",
            "Legal/discipline stories are intentionally manual-only and are accumulating.",
            sensitive_backlog,
        )

    items.sort(key=lambda x: (-x["priority"], x["code"]))
    return items


def certify_story_production():
    readiness = engine_bootstrap.check_engine_readiness()
    if not readiness.get("ready"):
        return {
            "certification": "STORY_PRODUCTION",
            "status": "BLOCKED",
            "reason": readiness.get("reason_code") or "ENGINE_NOT_READY",
            "database_version": readiness.get("database_version"),
            "remediation_queue": [{
                "priority": 100,
                "code": "ENGINE_NOT_READY",
                "title": "Restore Engine database readiness",
                "detail": "The configured Engine DB is not ready, so Story Factory production certification cannot run.",
                "metric": readiness.get("reason_code"),
            }],
        }

    c = engine_bootstrap.connect()
    try:
        health = story_factory_health(c)
        quality = certify_story_question_quality(c)
        rejects = _rejection_breakdown(c)
    finally:
        c.close()

    reach = certify_story_game_reach()
    remediation = _remediation_queue(health, quality, reach, rejects)

    status = "PASSED"
    if quality.get("status") == "FAILED" or reach.get("errors"):
        status = "FAILED"
    elif remediation:
        status = "NEEDS_WORK"

    return {
        "certification": "STORY_PRODUCTION",
        "status": status,
        "database_version": readiness.get("database_version"),
        "database_size_bytes": readiness.get("db_size_bytes"),
        "health": health,
        "question_quality": quality,
        "game_reach": reach,
        "rejection_breakdown": rejects,
        "remediation_queue": remediation,
        "top_priority": remediation[:10],
    }


def main():
    print(json.dumps(certify_story_production(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
