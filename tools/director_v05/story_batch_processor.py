"""Checkpointed Story Factory batch processor.

This is the durable production work queue for harvested story candidates.
It keeps candidate review state separate from processing state so interrupted
workers can resume safely without losing already-completed stories.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap

from .story_subject_match import build_subject_index
from .story_to_trivia_factory import (
    _ensure_schema as ensure_factory_schema,
    _prepare_write_connection,
    _commit_with_retry,
    process_candidate,
)

STATE_PENDING = "PENDING"
STATE_PROCESSING = "PROCESSING"
STATE_DONE = "DONE"
STATE_REVIEW = "REVIEW_REQUIRED"
STATE_RETRY = "FAILED_RETRYABLE"
STATE_FAILED = "FAILED_FINAL"

DEFAULT_BATCH_SIZE = 5
MAX_BATCH_SIZE = 25
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_STALE_MINUTES = 30


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _ensure_schema(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS story_candidate_processing (
            candidate_id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT 'PENDING',
            attempts INTEGER NOT NULL DEFAULT 0,
            claimed_at TEXT,
            heartbeat_at TEXT,
            finished_at TEXT,
            last_error TEXT,
            last_decision TEXT,
            generated_question_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(candidate_id) REFERENCES football_story_candidates(candidate_id)
        )
    """)
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_story_processing_state "
        "ON story_candidate_processing(state,attempts,updated_at)"
    )
    _commit_with_retry(c)


def sync_queue(c):
    """Add eligible candidates to the processing ledger without resetting work."""
    now = _now()
    c.execute(
        """INSERT OR IGNORE INTO story_candidate_processing(
               candidate_id,state,attempts,updated_at)
           SELECT candidate_id,'PENDING',0,?
           FROM football_story_candidates
           WHERE status='REVIEW_PRIORITY'
             AND COALESCE(sensitive_hint,0)=0""",
        (now,),
    )
    _commit_with_retry(c)


def reclaim_stale(c, *, stale_minutes=DEFAULT_STALE_MINUTES):
    cutoff = (
        dt.datetime.now(dt.timezone.utc)
        - dt.timedelta(minutes=max(1, int(stale_minutes)))
    ).isoformat()
    rows = c.execute(
        """SELECT candidate_id
           FROM story_candidate_processing
           WHERE state='PROCESSING'
             AND COALESCE(heartbeat_at,claimed_at,updated_at) < ?""",
        (cutoff,),
    ).fetchall()
    if not rows:
        return 0
    now = _now()
    ids = [str(r["candidate_id"]) for r in rows]
    c.executemany(
        """UPDATE story_candidate_processing
           SET state='FAILED_RETRYABLE',
               last_error='STALE_PROCESSING_RECLAIMED',
               claimed_at=NULL,
               heartbeat_at=NULL,
               updated_at=?
           WHERE candidate_id=?""",
        [(now, cid) for cid in ids],
    )
    _commit_with_retry(c)
    return len(ids)


def _claim_batch(c, *, batch_size, max_attempts):
    batch_size = max(1, min(int(batch_size), MAX_BATCH_SIZE))
    max_attempts = max(1, int(max_attempts))
    now = _now()

    # BEGIN IMMEDIATE makes the claim atomic: two workers cannot claim the same
    # candidate even if GitHub or an admin accidentally starts both.
    c.execute("BEGIN IMMEDIATE")
    rows = c.execute(
        """SELECT p.candidate_id
           FROM story_candidate_processing p
           JOIN football_story_candidates c
             ON c.candidate_id=p.candidate_id
           WHERE p.state IN ('PENDING','FAILED_RETRYABLE')
             AND p.attempts < ?
             AND c.status='REVIEW_PRIORITY'
             AND COALESCE(c.sensitive_hint,0)=0
           ORDER BY
             CASE c.evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
             c.seen_date DESC,
             p.attempts ASC,
             p.candidate_id
           LIMIT ?""",
        (max_attempts, batch_size),
    ).fetchall()
    ids = [str(r["candidate_id"]) for r in rows]
    if ids:
        c.executemany(
            """UPDATE story_candidate_processing
               SET state='PROCESSING',
                   attempts=attempts+1,
                   claimed_at=?,
                   heartbeat_at=?,
                   updated_at=?,
                   last_error=NULL
               WHERE candidate_id=?""",
            [(now, now, now, cid) for cid in ids],
        )
    _commit_with_retry(c)

    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    return c.execute(
        f"""SELECT * FROM football_story_candidates
            WHERE candidate_id IN ({marks})
            ORDER BY
              CASE evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
              seen_date DESC,candidate_id""",
        ids,
    ).fetchall()


def _finish(c, candidate_id, *, state, decision=None, generated=0, error=None):
    c.execute(
        """UPDATE story_candidate_processing
           SET state=?,
               finished_at=?,
               heartbeat_at=?,
               last_error=?,
               last_decision=?,
               generated_question_count=?,
               updated_at=?
           WHERE candidate_id=?""",
        (
            state,
            _now(),
            _now(),
            error,
            decision,
            int(generated or 0),
            _now(),
            str(candidate_id),
        ),
    )
    _commit_with_retry(c)


def process_story_batch(
    *,
    batch_size=DEFAULT_BATCH_SIZE,
    max_attempts=DEFAULT_MAX_ATTEMPTS,
    stale_minutes=DEFAULT_STALE_MINUTES,
    include_deep_chains=False,
):
    c = _prepare_write_connection(engine_bootstrap.connect())
    c.row_factory = sqlite3.Row
    ensure_factory_schema(c)
    _ensure_schema(c)
    sync_queue(c)
    reclaimed = reclaim_stale(c, stale_minutes=stale_minutes)
    rows = _claim_batch(
        c,
        batch_size=batch_size,
        max_attempts=max_attempts,
    )
    subject_index = build_subject_index(c)

    counts = Counter()
    examples = []
    for row in rows:
        cid = str(row["candidate_id"])
        try:
            result = process_candidate(
                c,
                row,
                subject_index,
                include_deep_chains=include_deep_chains,
            )
            decision = str(result.get("decision") or "UNKNOWN")
            generated = int(result.get("generated") or 0)
            if decision == "AUTO_PROMOTED":
                state = STATE_DONE
            elif decision.startswith("REVIEW_REQUIRED"):
                state = STATE_REVIEW
            else:
                state = STATE_REVIEW
            _finish(
                c,
                cid,
                state=state,
                decision=decision,
                generated=generated,
            )
            counts[state] += 1
            if len(examples) < 10:
                examples.append({
                    "candidate_id": cid,
                    "decision": decision,
                    "generated": generated,
                    "event_id": result.get("event_id"),
                })
        except Exception as exc:
            attempt_row = c.execute(
                "SELECT attempts FROM story_candidate_processing WHERE candidate_id=?",
                (cid,),
            ).fetchone()
            attempts = int(attempt_row["attempts"] if attempt_row else 1)
            final = attempts >= max(1, int(max_attempts))
            state = STATE_FAILED if final else STATE_RETRY
            _finish(
                c,
                cid,
                state=state,
                error=type(exc).__name__ + ":" + str(exc),
            )
            counts[state] += 1
            if len(examples) < 10:
                examples.append({
                    "candidate_id": cid,
                    "decision": state,
                    "error": type(exc).__name__ + ":" + str(exc),
                })

    ledger = {
        str(r["state"]): int(r["n"])
        for r in c.execute(
            "SELECT state,COUNT(*) n FROM story_candidate_processing GROUP BY state"
        ).fetchall()
    }
    generated_total = int(
        c.execute(
            "SELECT COALESCE(SUM(generated_question_count),0) "
            "FROM story_candidate_processing"
        ).fetchone()[0]
    )
    c.close()
    return {
        "claimed": len(rows),
        "reclaimed_stale": reclaimed,
        "counts": dict(counts),
        "ledger": ledger,
        "generated_from_checkpointed_batches": generated_total,
        "batch_size": max(1, min(int(batch_size), MAX_BATCH_SIZE)),
        "include_deep_chains": bool(include_deep_chains),
        "examples": examples,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    ap.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    ap.add_argument("--stale-minutes", type=int, default=DEFAULT_STALE_MINUTES)
    ap.add_argument("--deep-chains", action="store_true")
    args = ap.parse_args()
    print(json.dumps(process_story_batch(
        batch_size=args.batch_size,
        max_attempts=args.max_attempts,
        stale_minutes=args.stale_minutes,
        include_deep_chains=args.deep_chains,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
