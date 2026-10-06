"""Triage thousands of harvested football-story candidates into a review queue."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

from tools.quiz_export import engine as engine_bootstrap
from .story_sqlite import prepare_write_connection, commit_with_retry

HIGH_SIGNAL = {
    "BIZARRE_MOMENT": (
        "bizarre play", "weird play", "strangest play", "unusual touchdown",
        "crazy ending", "rare play", "accidental touchdown",
    ),
    "DRAFT_BUST": (
        "draft bust", "first round bust", "first-round bust", "failed draft pick",
        "draft disaster", "draft day mistake", "historic draft miss",
    ),
    "TRADE_ODDITY": (
        "weird trade", "shocking trade", "blockbuster trade", "trade request",
        "draft day trade", "draft-day trade", "trade deadline",
    ),
    "DISCIPLINE_LEGAL": (
        "suspended", "suspension", "discipline", "fine", "fined", "arrested",
        "arrest", "charged", "charge", "investigation",
    ),
    "COMEBACK_RETURN": (
        "comeback", "retirement", "came out of retirement", "returned to football",
        "unretired", "career comeback",
    ),
    "SIDELINE_INCIDENT": (
        "sideline incident", "sideline argument", "sideline altercation",
        "sideline confrontation", "sideline penalty", "bench incident",
    ),
    "COACHING_MELTDOWN": (
        "coach rant", "coach meltdown", "postgame rant", "press conference",
        "viral quote", "memorable quote", "coach said",
    ),
    "CELEBRATION_CONTROVERSY": (
        "touchdown celebration", "celebration penalty", "taunting penalty",
        "end zone celebration", "celebration fine", "sideline celebration",
    ),
    "RECRUITING_CHAOS": (
        "recruiting controversy", "recruiting flip", "signing day",
        "recruiting saga", "commitment flip", "recruiting surprise",
    ),
    "RECORD_ODDITY": (
        "record breaking", "record-breaking", "first player ever",
        "rare record", "strange record", "bizarre record",
    ),
    "INFAMOUS_MISTAKE": (
        "infamous mistake", "costly mistake", "forgot the rules", "wrong way",
        "botched play", "historic blunder",
    ),
    "OFF_FIELD_ODDITY": (
        "hard knocks", "bizarre", "weird", "unusual", "viral", "funny",
        "training camp", "costume", "prank", "strange story",
    ),
    "RIVALRY_INCIDENT": (
        "rivalry incident", "rivalry prank", "rivalry trophy", "rivalry fight",
        "rivalry controversy", "crazy ending",
    ),
    "TRANSFER_NIL_CHAOS": (
        "transfer portal", "nil controversy", "nil deal", "transfer flip",
        "portal commitment", "portal chaos",
    ),
    "PLAYOFF_FORGOTTEN": (
        "forgotten playoff", "forgotten playoff moment", "forgotten bowl",
        "playoff upset", "wild card", "college football playoff",
    ),
    "PRESS_CONFERENCE": (
        "press conference", "postgame", "news conference", "media availability",
        "locker room", "asked about", "coach said", "viral quote", "memorable quote",
    ),
    "RULE_ODDITY": (
        "rule change", "rules change", "unusual rule", "obscure rule",
        "penalty rule", "approved rule", "targeting", "kickoff rule",
        "rare penalty", "rule loophole",
    ),

    # Legacy family names already present in the corpus.
    "CELEBRATION_FAN": ("celebration", "touchdown celebration", "mascot", "fan", "taunt", "dance", "crowd", "end zone"),
    "DRAFT_CHAOS": ("draft", "trade up", "trade down", "draft-day", "slide", "surprise pick", "unexpected pick", "mr irrelevant"),
    "TRADE_CHAOS": ("trade", "blockbuster", "trade request", "trade deadline", "traded"),
    "BUST_REDEMPTION": ("draft bust", "first round bust", "first-round bust", "career turnaround", "late bloomer", "career revival", "breakout"),
    "GAME_ODDITY": ("weird play", "bizarre play", "strangest play", "unusual touchdown", "rare play", "crazy ending", "accidental touchdown", "forgot the rules"),
    "COACHING_ODDITY": ("coach quote", "coach rant", "coach fired", "sideline incident", "coach celebration", "coach prank"),
    "RIVALRY_ODDITY": ("rivalry prank", "rivalry trophy", "rivalry tradition", "rivalry game", "crazy ending"),
}

FOOTBALL_ANCHORS = (
    "nfl", "football", "quarterback", "coach", "touchdown", "college",
    "super bowl", "team", "player", "receiver", "running back",
)

LOW_SIGNAL = (
    "fantasy football", "betting odds", "sportsbook", "mock draft",
    "power rankings", "prediction", "pick against the spread",
)

# Any candidate containing these terms is review-only even if a broad safe
# search family discovered it. Query-family labels are hints, never a safety
# authority.
SENSITIVE_TITLE_TERMS = (
    "arrest", "arrested", "charged", "charge", "indicted", "convicted",
    "court", "lawsuit", "investigation", "suspended", "suspension",
    "discipline", "domestic violence", "assault", "dui", "dwi",
)

SOURCE_WEIGHT = {
    "PRIMARY": 25,
    "REPUTABLE_MEDIA": 15,
}


def _norm_title(title):
    text = re.sub(r"[^a-z0-9 ]+", " ", str(title).casefold())
    return " ".join(text.split())


def _title_signature(title):
    words = [w for w in _norm_title(title).split() if len(w) > 2]
    return hashlib.sha256(" ".join(words[:18]).encode()).hexdigest()[:20]


def _score(row):
    title = _norm_title(row["title"])
    family = str(row["family_hint"])
    score = SOURCE_WEIGHT.get(str(row["evidence_tier_hint"]), 0)

    for phrase in HIGH_SIGNAL.get(family, ()):
        if phrase in title:
            score += 12

    if any(anchor in title for anchor in FOOTBALL_ANCHORS):
        score += 8
    if any(term in title for term in LOW_SIGNAL):
        score -= 30
    if str(row["domain"]) in {"nfl.com", "ncaa.org"}:
        score += 8
    if row["seen_date"]:
        score += 2
    if int(row["sensitive_hint"] or 0):
        # Sensitive stories do not get a ranking bonus merely for being
        # sensational; they stay review-gated no matter how high the score.
        score -= 3
    return score


def triage_candidates(*, minimum_priority_score=30):
    c = prepare_write_connection(engine_bootstrap.connect())
    rows = c.execute(
        """SELECT * FROM football_story_candidates
           WHERE status IN ('REVIEW_REQUIRED','REVIEW_PRIORITY')
           ORDER BY first_harvested_at,candidate_id"""
    ).fetchall()

    signatures = {}
    counts = Counter()
    updates = []

    for row in rows:
        cid = str(row["candidate_id"])
        sig = _title_signature(row["title"])
        score = _score(row)

        normalized_title = _norm_title(row["title"])
        sensitive_copy = any(term in normalized_title for term in SENSITIVE_TITLE_TERMS)

        if any(term in normalized_title for term in LOW_SIGNAL):
            status = "REJECT_LOW_SIGNAL"
            counts[status] += 1
        elif sig in signatures:
            status = "REJECT_NEAR_DUPLICATE"
            counts[status] += 1
        elif int(row["sensitive_hint"] or 0) or sensitive_copy:
            status = "REVIEW_REQUIRED_SENSITIVE"
            signatures[sig] = cid
            counts[status] += 1
        elif score >= int(minimum_priority_score):
            status = "REVIEW_PRIORITY"
            signatures[sig] = cid
            counts[status] += 1
        else:
            status = "REVIEW_REQUIRED"
            signatures[sig] = cid
            counts[status] += 1

        updates.append((status, json.dumps({
            "triage_score": score,
            "title_signature": sig,
        }, sort_keys=True), cid))

    c.executemany(
        """UPDATE football_story_candidates
           SET status=?,review_notes=? WHERE candidate_id=?""",
        updates,
    )
    commit_with_retry(c)

    family_counts = c.execute(
        """SELECT family_hint,status,COUNT(*) n
           FROM football_story_candidates
           GROUP BY family_hint,status
           ORDER BY family_hint,status"""
    ).fetchall()
    c.close()

    return {
        "processed": len(rows),
        "status_counts": dict(counts),
        "family_status_counts": [
            {
                "family": str(r["family_hint"]),
                "status": str(r["status"]),
                "count": int(r["n"]),
            }
            for r in family_counts
        ],
    }


def export_review_batch(*, limit=1000, include_sensitive=False):
    c = engine_bootstrap.connect()
    statuses = ["REVIEW_PRIORITY"]
    if include_sensitive:
        statuses.append("REVIEW_REQUIRED_SENSITIVE")
    placeholders = ",".join("?" for _ in statuses)
    rows = c.execute(
        f"""SELECT candidate_id,source_url,title,domain,seen_date,family_hint,
                   evidence_tier_hint,sensitive_hint,review_notes
            FROM football_story_candidates
            WHERE status IN ({placeholders})
            ORDER BY
              CASE evidence_tier_hint WHEN 'PRIMARY' THEN 0 ELSE 1 END,
              seen_date DESC,
              candidate_id
            LIMIT ?""",
        (*statuses, max(1, min(int(limit), 10000))),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--include-sensitive", action="store_true")
    args = ap.parse_args()
    result = triage_candidates()
    result["review_batch"] = export_review_batch(
        limit=args.limit,
        include_sensitive=args.include_sensitive,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
