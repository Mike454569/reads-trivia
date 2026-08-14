"""CFB National Championship domain adapter (Creator-gap-audit operation).

Built on `cfb_champion_school_links` (101 rows, 1936-2025 seasons), which
resolves `cfb_champions`' free-text `champion_raw` to a real `school_id` --
confirmed directly this operation: every row already has a real, non-null
school_id, so (unlike NFL franchises, which relocate/rename and need
team_aliases' season-scoped resolution) no separate identity-resolution
step is needed here.

Real, disclosed limit found by auditing the table before building on it:
11 of the 91 real championship seasons (1936-2025) have TWO rows -- the
pre-BCS/pre-CFP era had multiple recognized national-champion selectors
(AP, Coaches' Poll, etc.) that sometimes disagreed, producing genuine
co-champions. Rather than picking one arbitrarily (which would silently
mark a real, historically-recognized champion as "wrong"), every season
with more than one champion row is excluded outright -- mirrors this
codebase's standing "never guess when the source itself is ambiguous"
discipline (same one nfl_game_boxscore.py already uses for exact-tie games).

Distractor schools are not season-scoped for the same real, disclosed
reason cfb_heisman.py's don't: cfb_school_seasons (the real per-season CFB
participation table) only covers 2002-2025, but championships go back to
1936. Every option shown is still a REAL school; distractors prefer other
real national-champion schools first (a real "plausible" pool, avoiding
the same obscure-D3-school problem cfb_heisman.py's own module docstring
documents fixing).
"""
from __future__ import annotations

from collections import Counter

from .. import engine, safety, difficulty as difficulty_mod, serializer
from .. import distractors as distractors_mod

OUT_PATH = None
CATEGORY = "CFB National Championship History"
REQUIRED_SOURCE = "READS_CFB_MASTER"
REQUIRED_VERIFICATION_STATUS = "SOURCE_BACKED_FROM_CFB_MASTER"
TRACK_ENTITY = True  # one question per real champion season

MIN_SEASON = 1936
MAX_SEASON = 2025


def safety_check(c) -> dict:
    return safety.check_verification_status_safety(
        c, "cfb_champion_school_links", REQUIRED_SOURCE, REQUIRED_VERIFICATION_STATUS,
    )


def _all_real_schools(c) -> dict:
    rows = c.execute("SELECT school_id, school_name FROM schools").fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def _champion_schools(c) -> dict:
    """The plausible-distractor pool: every real school that has itself won
    a real national championship -- mirrors cfb_heisman.py's own
    "other real Heisman-winning schools" pool, same reasoning."""
    rows = c.execute(
        "SELECT DISTINCT school_id, school_name FROM cfb_champion_school_links "
        "WHERE verification_status = ?", (REQUIRED_VERIFICATION_STATUS,),
    ).fetchall()
    return {r["school_id"]: r["school_name"] for r in rows}


def fetch_ordered_candidates(c, seed: str):
    # Excludes any season with more than one champion row (real, historical
    # co-champion disagreements -- see module docstring; never guessed at).
    rows = c.execute(
        """
        SELECT season, school_id, school_name, coach_raw, notes, verification_status
        FROM cfb_champion_school_links
        WHERE verification_status = ?
          AND season IN (
              SELECT season FROM cfb_champion_school_links GROUP BY season HAVING COUNT(*) = 1
          )
        ORDER BY season
        """,
        (REQUIRED_VERIFICATION_STATUS,),
    ).fetchall()
    rng_order = engine.seeded(seed)
    rows = list(rows)
    rng_order.shuffle(rows)
    return rows


def evaluate(c, row, rng, guard):
    season = row["season"]
    if not row["school_id"] or not row["school_name"]:
        return "SCHOOL_UNRESOLVED"

    plausible_schools = _champion_schools(c)
    full_schools = _all_real_schools(c)
    distractor_map = distractors_mod.sample_plausible(rng, row["school_id"], plausible_schools, full_schools, k=3)
    if distractor_map is None:
        return "INSUFFICIENT_DISTRACTORS"
    distractor_names = list(distractor_map.values())

    options = [row["school_name"]] + distractor_names
    if len(set(options)) != 4:
        return "DUPLICATE_OPTIONS"

    question = f"Which school won the {season} college football national championship?"
    if guard.question_seen(question):
        return "DUPLICATE_QUESTION"
    entity_key = f"cfb_champion:{season}"
    if guard.entity_seen(entity_key):
        return "DUPLICATE_SEASON"

    shuffled_options, correct_index = serializer.finalize_options(rng, row["school_name"], distractor_names)
    if not (0 <= correct_index <= 3) or shuffled_options[correct_index] != row["school_name"]:
        return "INVALID_CORRECT_INDEX"

    diff_score = (MAX_SEASON - season) / max(MAX_SEASON - MIN_SEASON, 1)
    band = engine.band(diff_score)
    diff_label = difficulty_mod.map_band(band)

    coach_note = f", coached by {row['coach_raw']}" if row["coach_raw"] else ""
    notes = f"{row['school_name']} won the {season} national championship{coach_note}. {row['notes'] or ''}".strip()

    return {
        "category": CATEGORY, "difficulty": diff_label, "question": question,
        "options": shuffled_options, "correctIndex": correct_index, "notes": notes,
        "_audit": {
            "season": season, "school_id": row["school_id"], "correct_answer_text": row["school_name"],
            "difficulty_score": round(diff_score, 4), "difficulty_band": band, "entity_key": entity_key,
            "verification_status": REQUIRED_VERIFICATION_STATUS, "source_id": REQUIRED_SOURCE,
        },
    }


def shortfall_reason(accepted_count, considered_count, target_count) -> str:
    return (
        f"Only {accepted_count} candidates passed every validation rule across the full "
        f"{considered_count} unambiguous (single-selector-agreement) championship seasons on record; "
        f"exported the maximum available ({accepted_count}) rather than loosen any rule to reach {target_count}. "
        f"11 real seasons with recognized co-champions (pre-BCS/CFP selector disagreements) are excluded "
        f"entirely, never guessed at."
    )


def extra_funnel_fields(accepted, exported) -> dict:
    by_band = Counter(q["_audit"]["difficulty_band"] for q in exported)
    seasons = [q["_audit"]["season"] for q in exported]
    schools = sorted(set(q["_audit"]["school_id"] for q in exported))
    return {
        "difficulty_band_distribution": dict(by_band),
        "min_season": min(seasons) if seasons else None,
        "max_season": max(seasons) if seasons else None,
        "unique_champion_schools": len(schools),
    }


def header_lines(seed: str) -> list[str]:
    return [
        "// Director-pipeline-only domain -- not exported to a static .js pilot file.",
        "// tools/quiz_export/adapters/cfb_championship.py -- CFB National Championship History.",
        f"// Deterministic seed: \"{seed}\".",
    ]


def human_review_context(record: dict) -> list[str]:
    a = record["_audit"]
    return [
        f"- **Season:** {a['season']}",
        f"- **Champion:** `{a['school_id']}` (\"{record['options'][record['correctIndex']]}\")",
        f"- **Underlying Engine source:** `cfb_champion_school_links`, verification_status "
        f"`{a['verification_status']}`, source_id `{a['source_id']}`",
    ]
