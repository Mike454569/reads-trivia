"""WEEKLY_PICKEM -- Reliability Design Phase 7A, real mechanic template #8.

A real weekly pick'em: a slate of real NFL or CFB games for one (season,
week), where the player predicts each game's winner. Structurally
different from every other Phase 6 mechanic template, and this is the one
real architectural decision this module makes deliberately, not by
accident: every existing mechanic's "truth" (a past Super Bowl winner, a
team-season's real win total, a real draft slot) is already fully known
and settled at GENERATION time, so it is baked once into the immutable
package (`_private_value`/`_private_membership`/`_private_answer_key`).
WEEKLY_PICKEM's truth is NOT settled at generation time for a genuinely
real, common case -- most of a week's games haven't been played yet. The
real winner only becomes knowable LATER, from the exact same
`games`/`cfb_games_canonical` tables every other game-result capability
already reads (nfl_game_result.py / cfb_game_result.py), as those rows get
real scores via the ordinary daily/weekly refresh schedule.

Consequence: this module stores only the STATIC slate facts in its package
(game_id, real team codes, real kickoff date) -- never a game's result.
Grading is never a frozen fact and never a scheduled sweep; `mechanic_engine
.py`'s WEEKLY_PICKEM view/evaluate functions re-derive each game's real,
current status FRESH from the live tables on every request (see
`live_game_statuses()` below) -- "automatic grading after games become
final" is therefore always true by construction, not by a cron job nobody
has to remember to run.

Completion signal is IDENTICAL to the convention nfl_game_result.py /
cfb_game_result.py already established: both `home_score`/`away_score`
non-null means FINAL, always derived live from the row's own current
score columns, never cached. Dynamic Weekly Pick'em pass: `games`/
`cfb_games_canonical` now also carry a real, persisted `status` column
(tools/data_refresh/pickem_schema_migration.py) -- but it exists ONLY to
carry the one real signal live derivation can never produce on its own:
POSTPONED/CANCELED, set exclusively by the admin override
(gateway/services/admin_pickem.py), since neither real upstream source
(nflverse's games.csv, cfbfastR's schedules CSV) ever asserts either value
itself (confirmed directly). Everything else (SCHEDULED/IN_PROGRESS/
UNKNOWN/FINAL) is still computed live from the row's own real score/
kickoff values on every call, in `_status_for()` below -- this project
still never fabricates a status the source data doesn't actually assert;
IN_PROGRESS specifically is a disclosed heuristic (elapsed real kickoff
time), never a true live-feed signal (see tools/data_refresh/
_pickem_status.py's own docstring).

Team/school identity: picks and slate entries are keyed on the SAME raw
codes already stored on the game row (`games.home_team`/`away_team` team
codes for NFL, `cfb_games_canonical.home_school_id`/`away_school_id` for
CFB) -- never a resolved franchise_id/display name, so a pick is always
checked against the exact two real values the game row itself asserts, no
resolution ambiguity possible. Display names ARE resolved (via the same
`resolve_franchise()`/`team_aliases` helper every NFL adapter in this
codebase already reuses, and a direct `schools` lookup for CFB, matching
`cfb_player_season_school.py`'s own resolution strategy) purely for the
client-facing label -- never for identity/grading.
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402
from tools.quiz_export.adapters.draft import resolve_franchise  # noqa: E402
from tools.data_refresh import _pickem_status  # noqa: E402

PACKAGE_SCHEMA_VERSION = "1.0"
MECHANIC = "WEEKLY_PICKEM"
# A real NFL/CFB week can legitimately have very few games (a bye-heavy
# week, or a small bowl-season slate) -- 1, not some arbitrary round
# number, is the only honest floor; never pad a slate with a game that
# didn't happen to reach a nicer-looking minimum.
MIN_GAMES_FOR_SLATE = 1

VARIANTS = frozenset({"NFL_WEEKLY_PICKEM", "CFB_WEEKLY_PICKEM"})
_NFL_POSTSEASON_WEEK_CODES = frozenset({"WC", "DIV", "CON", "SB"})
# Dynamic Weekly Pick'em pass: cfb_games_canonical.week is NOT globally
# unique across season_type the way games.week already is for NFL --
# confirmed live: season=2025,week=1 holds 200 real regular-season games
# PLUS 43 real non-playoff bowls PLUS 11 real CFP games, all mislabeled
# week=1. These tokens are the CFB equivalent of _NFL_POSTSEASON_WEEK_CODES
# above -- a real, distinct slate selector, never a numeric week value.
_CFB_POSTSEASON_WEEK_TOKENS = frozenset(
    {"CFP_FIRST_ROUND", "CFP_QUARTERFINAL", "CFP_SEMIFINAL", "CFP_CHAMPIONSHIP", "BOWLS"}
)
_CFP_ROUND_TO_TOKEN = {
    "first_round": "CFP_FIRST_ROUND", "quarterfinal": "CFP_QUARTERFINAL",
    "semifinal": "CFP_SEMIFINAL", "championship": "CFP_CHAMPIONSHIP",
}
_TOKEN_TO_CFP_ROUND = {v: k for k, v in _CFP_ROUND_TO_TOKEN.items()}


def safety_check(c) -> dict:
    from tools.quiz_export import safety
    return {
        "games": safety.check_source_id_only_safety(c, "games", "NFLVERSE_DATA"),
        "cfb_games_canonical": safety.check_table_wide_safety(c, "cfb_games_canonical", "SPORTSDATAVERSE_CFB"),
    }


def _cfb_kickoff(raw: str | None) -> datetime | None:
    return _pickem_status.parse_iso(raw)


def _status_for(persisted_status: str | None, home_score, away_score, kickoff_dt) -> tuple[str, str | None]:
    """Returns (status, winner_side) where winner_side is 'home'/'away'/'TIE'
    only when status=='FINAL', else None. Never leaked/guessed otherwise.

    Dynamic Weekly Pick'em pass: POSTPONED/CANCELED can ONLY ever come from
    the row's own persisted `status` column (set exclusively by the admin
    override, gateway/services/admin_pickem.py -- neither real upstream
    source ever asserts either value, confirmed directly) -- checked first,
    before any score/date derivation, since no other signal can ever
    produce these two. Everything else is still derived LIVE from the row's
    own real score/kickoff values every call, never trusted from a
    possibly-stale persisted value -- see module docstring."""
    if persisted_status in ("POSTPONED", "CANCELED"):
        return persisted_status, None
    if home_score is not None and away_score is not None:
        if home_score == away_score:
            return "FINAL", "TIE"
        return "FINAL", ("home" if home_score > away_score else "away")
    return _pickem_status.derive_pending_status(kickoff_dt), None


def _nfl_slate_rows(c, season: int, week: str) -> list:
    if week in _NFL_POSTSEASON_WEEK_CODES:
        return c.execute(
            "SELECT game_id, home_team, away_team, home_score, away_score, game_date, game_time, status "
            "FROM games WHERE season=? AND game_type=? ORDER BY game_id", (season, week),
        ).fetchall()
    return c.execute(
        "SELECT game_id, home_team, away_team, home_score, away_score, game_date, game_time, status "
        "FROM games WHERE season=? AND week=? AND game_type='REG' ORDER BY game_id", (season, str(week)),
    ).fetchall()


def _cfb_postseason_slate_rows(c, season: int, token: str) -> list:
    if token == "BOWLS":
        # Real, honest limitation, disclosed not hidden: cfbfastR's source
        # data has no per-bowl-week partition -- every non-playoff bowl
        # carries the same degenerate week=1 label regardless of real
        # calendar date (confirmed directly: 43 real bowl games spanning
        # Nov-Jan, all under week=1). Bucketing them into one real "Bowl
        # Season" slate, ordered by real game_date, is the most honest
        # representation available -- never invented into fake sub-weeks.
        return c.execute(
            "SELECT game_id, home_school_id AS home_team, away_school_id AS away_team, "
            "home_score, away_score, game_date, status FROM cfb_games_canonical "
            "WHERE season=? AND season_type='postseason' AND is_playoff=0 "
            "ORDER BY game_date, game_id", (season,),
        ).fetchall()
    round_name = _TOKEN_TO_CFP_ROUND[token]
    return c.execute(
        "SELECT game_id, home_school_id AS home_team, away_school_id AS away_team, "
        "home_score, away_score, game_date, status FROM cfb_games_canonical "
        "WHERE season=? AND is_playoff=1 AND playoff_round=? ORDER BY game_id", (season, round_name),
    ).fetchall()


def _cfb_slate_rows(c, season: int, week) -> list:
    if week in _CFB_POSTSEASON_WEEK_TOKENS:
        return _cfb_postseason_slate_rows(c, season, week)
    return c.execute(
        "SELECT game_id, home_school_id AS home_team, away_school_id AS away_team, "
        "home_score, away_score, game_date, status FROM cfb_games_canonical "
        "WHERE season=? AND week=? AND season_type='regular' ORDER BY game_id", (season, int(week)),
    ).fetchall()


def check_slate_feasibility(variant: str, season: int, week) -> dict:
    """Real, honest feasibility check -- the Creator/feasibility integration
    surface for this mechanic (WEEKLY_PICKEM has no (mechanic, domain,
    relationship_predicate) triple to look up in the existing capability
    registry -- it is schedule-driven, not relationship-driven -- so this
    is its own dedicated, directly-callable, directly-testable check rather
    than a forced fit into that unrelated system)."""
    if variant not in VARIANTS:
        return {"support_status": "UNKNOWN", "reason": f"variant must be one of {sorted(VARIANTS)}, got {variant!r}"}
    c = engine_bootstrap.connect()
    try:
        rows = _nfl_slate_rows(c, season, week) if variant == "NFL_WEEKLY_PICKEM" else _cfb_slate_rows(c, season, week)
    finally:
        c.close()
    real_game_count = len(rows)
    if real_game_count == 0:
        return {
            "support_status": "MISSING_DATA", "variant": variant, "season": season, "week": week,
            "real_game_count": 0,
            "reason": f"No real games found for {variant}, season={season}, week={week!r} -- "
                      f"either this season/week hasn't been scheduled/ingested yet, or the week value is invalid.",
        }
    return {
        "support_status": "SUPPORTED", "variant": variant, "season": season, "week": week,
        "real_game_count": real_game_count,
    }


def live_game_statuses(variant: str, game_ids: list[str]) -> dict[str, dict]:
    """Fresh, real, per-game status -- see module docstring for why this is
    NEVER cached in the immutable package. Callable independently of a
    generated package (used by both the client view and submission
    evaluation, always re-derived, never trusted from a prior call)."""
    if not game_ids:
        return {}
    c = engine_bootstrap.connect()
    try:
        placeholders = ",".join("?" for _ in game_ids)
        if variant == "NFL_WEEKLY_PICKEM":
            rows = c.execute(
                f"SELECT game_id, home_team, away_team, home_score, away_score, game_date, game_time, status "
                f"FROM games WHERE game_id IN ({placeholders})", game_ids,
            ).fetchall()
        else:
            rows = c.execute(
                f"SELECT game_id, home_school_id AS home_team, away_school_id AS away_team, "
                f"home_score, away_score, game_date, status FROM cfb_games_canonical WHERE game_id IN ({placeholders})",
                game_ids,
            ).fetchall()
    finally:
        c.close()
    out = {}
    for r in rows:
        kickoff_dt = (_pickem_status.nfl_kickoff_utc(r["game_date"], r["game_time"])
                      if variant == "NFL_WEEKLY_PICKEM" else _cfb_kickoff(r["game_date"]))
        status, winner_side = _status_for(r["status"], r["home_score"], r["away_score"], kickoff_dt)
        winner_code = None
        if status == "FINAL":
            winner_code = "TIE" if winner_side == "TIE" else (r["home_team"] if winner_side == "home" else r["away_team"])
        out[r["game_id"]] = {
            "status": status, "winner_code": winner_code,
            "home_score": r["home_score"], "away_score": r["away_score"],
            "kickoff_utc": kickoff_dt.isoformat() if kickoff_dt else None,
        }
    return out


def _nfl_display(c, team_code: str, season: int) -> str:
    fr, err = resolve_franchise(c, team_code, season)
    return fr["full_name"] if not err and fr else team_code


def _cfb_display(c, school_id: str) -> str:
    row = c.execute("SELECT school_name FROM schools WHERE school_id=?", (school_id,)).fetchone()
    return row["school_name"] if row else school_id


def generate_slate(seed: str, variant: str, season: int, week) -> dict:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {sorted(VARIANTS)}, got {variant!r}")

    c = engine_bootstrap.connect()
    try:
        safety_result = safety_check(c)
        rows = _nfl_slate_rows(c, season, week) if variant == "NFL_WEEKLY_PICKEM" else _cfb_slate_rows(c, season, week)
        games = []
        for r in rows:
            home_display = _nfl_display(c, r["home_team"], season) if variant == "NFL_WEEKLY_PICKEM" \
                else _cfb_display(c, r["home_team"])
            away_display = _nfl_display(c, r["away_team"], season) if variant == "NFL_WEEKLY_PICKEM" \
                else _cfb_display(c, r["away_team"])
            games.append({
                "game_id": r["game_id"], "home_team": r["home_team"], "away_team": r["away_team"],
                "home_display": home_display, "away_display": away_display, "kickoff": r["game_date"],
            })
    finally:
        c.close()

    # Deterministic order, matching every other director_v04 generator's
    # own seeded-shuffle discipline -- games are already real/complete for
    # this slate (no candidate pool to sample DOWN from), so the seed only
    # controls display order, never which games are included.
    rng = engine_bootstrap.seeded(seed)
    rng.shuffle(games)

    shortfall_reason = None
    if len(games) < MIN_GAMES_FOR_SLATE:
        shortfall_reason = (
            f"No real games found for {variant}, season={season}, week={week!r} -- "
            f"refusing to fabricate a slate rather than show an empty/invented one."
        )
    return {"games": games, "safety": safety_result, "shortfall_reason": shortfall_reason}


def build_package(seed: str, variant: str, season: int, week) -> dict:
    result = generate_slate(seed, variant, season, week)
    package_id = "GGP9:" + hashlib.sha256(
        f"WEEKLYPICKEM|{variant}|{season}|{week}|{seed}|{PACKAGE_SCHEMA_VERSION}".encode()
    ).hexdigest()[:24]
    return {
        "package_id": package_id, "package_version": PACKAGE_SCHEMA_VERSION, "mechanic": MECHANIC,
        "domain_variant": variant, "season": season, "week": week,
        "game_title": "NFL Weekly Pick'em" if variant == "NFL_WEEKLY_PICKEM" else "CFB Weekly Pick'em",
        "game_instructions": "Pick the winner of every real game in this week's slate. Picks lock once a "
                              "game is final -- correctness is revealed automatically as each real result comes in.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "PASSED" if len(result["games"]) >= MIN_GAMES_FOR_SLATE else "FAILED",
        "games": result["games"], "game_count": len(result["games"]),
        "production_safety": result["safety"], "shortfall_reason": result["shortfall_reason"],
        "review_status": "UNREVIEWED", "_diagnostics": {"seed": seed},
    }
