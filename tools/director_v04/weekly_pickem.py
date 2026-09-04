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


# --- CFB slate variants (Player Experience pass) ----------------------------
#
# A real, previously-shipped gap: a bare CFB Pick'em request returned the
# ENTIRE real week's slate (up to 99 games for a real Week 1) -- unplayable.
# Everything below is a pure READ-TIME FILTER/SCORE over the exact same
# real full slate generate_slate()/build_package() already produce -- never
# a second candidate-pool query, never a parallel engine. mechanic_engine.py
# needs zero changes: it only ever reads package["games"], never how those
# games were selected, so grading/locking/VOID handling are provably
# unaffected by anything in this section.

CFB_SLATES = frozenset({"FULL", "FEATURED", "TOP25", "POWER4", "CONFERENCE"})
DEFAULT_CFB_SLATE = "FEATURED"
# Real, stable, publicly-known grouping -- not fabricated. Confirmed these
# are the exact literal conference-name strings the live 2026 source data
# itself uses (cfbfastR's schedule CSV), captured via cfb_games_refresh.py.
POWER_FOUR_CONFERENCES = frozenset({"SEC", "Big Ten", "Big 12", "ACC"})
REAL_CFB_CONFERENCES = frozenset({
    "ACC", "American Athletic", "Big 12", "Big Sky", "Big Ten", "Coastal Athletic",
    "Conference USA", "FBS Independents", "FCS Independents", "MEAC", "MVFC",
    "Mid-American", "Mountain West", "NEC", "OVC", "Pac-12", "Patriot", "SEC",
    "SWAC", "Southern", "Southland", "Sun Belt", "UAC",
})
# Fixed top-N, not a score threshold -- keeps the real weekly slate size
# predictable (a marquee week can't blow past it, a quiet week just returns
# fewer real games) rather than swinging wildly with how many games happen
# to clear an arbitrary point cutoff that week.
FEATURED_TARGET_COUNT = 20


def normalize_slate(slate: str | None) -> str:
    if slate is None:
        return DEFAULT_CFB_SLATE
    upper = slate.strip().upper()
    if upper not in CFB_SLATES:
        raise ValueError(f"slate must be one of {sorted(CFB_SLATES)}, got {slate!r}")
    return upper


def _ap_top25(c, season: int, week, season_type: str) -> dict[str, int]:
    """school_id -> real AP Top 25 rank for this real (season, week).
    Postseason rankings are stored at the same degenerate week=1 every
    postseason row uses (confirmed live -- the same real "everything
    mislabeled" pattern already disclosed for cfb_games_canonical's own
    bowls/CFP rows) -- queried by season_type, never by the postseason
    token string itself."""
    rank_week = 1 if season_type == "postseason" else int(week)
    rows = c.execute(
        "SELECT school_id, rank FROM cfb_rankings WHERE season=? AND week=? AND season_type=? AND poll='AP Top 25'",
        (season, rank_week, season_type),
    ).fetchall()
    return {r["school_id"]: r["rank"] for r in rows}


def _rivalry_pairs(c) -> set:
    rows = c.execute("SELECT school_a_id, school_b_id FROM cfb_rivalries").fetchall()
    return {frozenset((r["school_a_id"], r["school_b_id"])) for r in rows}


def _game_conference_meta(c, game_ids: list[str]) -> dict:
    if not game_ids:
        return {}
    placeholders = ",".join("?" for _ in game_ids)
    rows = c.execute(
        f"SELECT game_id, home_conference, away_conference, conference_game FROM cfb_games_canonical "
        f"WHERE game_id IN ({placeholders})", game_ids,
    ).fetchall()
    return {r["game_id"]: (r["home_conference"], r["away_conference"], r["conference_game"]) for r in rows}


def _betting_spreads(c, game_ids: list[str]) -> dict[str, float]:
    """Only real rows that actually exist -- confirmed live that
    cfb_betting_lines has ZERO rows for the current 2026 season. A
    game_id absent here contributes nothing to scoring below, never a
    fabricated/assumed spread."""
    if not game_ids:
        return {}
    placeholders = ",".join("?" for _ in game_ids)
    rows = c.execute(
        f"SELECT game_id, MIN(ABS(spread)) AS abs_spread FROM cfb_betting_lines "
        f"WHERE game_id IN ({placeholders}) AND spread IS NOT NULL GROUP BY game_id", game_ids,
    ).fetchall()
    return {r["game_id"]: r["abs_spread"] for r in rows}


def score_featured(game: dict, ranks: dict, rivalry_pairs: set, home_conf, away_conf,
                    conference_game, spread) -> int:
    """Real-data-only game-interest score. Every point comes from a real,
    confirmed-live signal -- missing data (no ranking, no rivalry, no real
    conference, no betting line) always contributes 0, never guessed at."""
    home_rank = ranks.get(game["home_team"])
    away_rank = ranks.get(game["away_team"])
    score = 0
    if home_rank or away_rank:
        score += 30
    if home_rank and away_rank:
        score += 40
    if (home_rank and home_rank <= 10) or (away_rank and away_rank <= 10):
        score += 20
    if (home_rank and home_rank <= 5) or (away_rank and away_rank <= 5):
        score += 15
    if frozenset((game["home_team"], game["away_team"])) in rivalry_pairs:
        score += 25
    # Power Four = at least one side in a real P4 conference (P4-vs-anyone)
    # -- a real judgment call, documented here rather than left implicit.
    home_p4 = home_conf in POWER_FOUR_CONFERENCES
    away_p4 = away_conf in POWER_FOUR_CONFERENCES
    if home_p4 or away_p4:
        score += 10
    if home_p4 and away_p4:
        score += 10
    if conference_game:
        score += 8
    if spread is not None:
        if spread <= 3:
            score += 15
        elif spread <= 7:
            score += 8
        elif spread <= 13:
            score += 3
    return score


def filter_games_for_slate(games: list[dict], *, slate: str | None, conference: str | None,
                            season: int, week) -> tuple[list[dict], dict]:
    """Pure filter/score over an already-generated FULL real slate --
    de-dup by game_id is structural (this only ever subsets one list,
    never unions multiple category queries with potential overlap).

    Stability note: the only inputs here that could churn intra-day are
    the ones deliberately excluded -- status/score are NOT scoring
    inputs at all. Rankings/betting-lines refresh weekly (Sundays only,
    per netlify.toml); cfb_rivalries has no refresh job at all (static
    curated data); conference names are structural facts that don't
    change once a matchup is scheduled. A deterministic recompute on
    every request is therefore already stable within a single real day --
    no new caching/pinning layer is needed, and building one would
    contradict this module's own "never a frozen fact" discipline."""
    slate_norm = normalize_slate(slate)
    meta = {"slate": slate_norm, "conference": None}
    if slate_norm == "FULL" or not games:
        return games, meta

    if slate_norm == "CONFERENCE":
        if not conference or conference not in REAL_CFB_CONFERENCES:
            raise ValueError(
                f"slate=CONFERENCE requires a real conference name from {sorted(REAL_CFB_CONFERENCES)}, got {conference!r}"
            )
        meta["conference"] = conference

    game_ids = [g["game_id"] for g in games]
    season_type = "postseason" if week in _CFB_POSTSEASON_WEEK_TOKENS else "regular"

    c = engine_bootstrap.connect()
    try:
        if slate_norm == "TOP25":
            ranks = _ap_top25(c, season, week, season_type)
            return [g for g in games if ranks.get(g["home_team"]) or ranks.get(g["away_team"])], meta

        conf_meta = _game_conference_meta(c, game_ids)

        if slate_norm == "POWER4":
            filtered = []
            for g in games:
                home_conf, away_conf, _ = conf_meta.get(g["game_id"], (None, None, None))
                if home_conf in POWER_FOUR_CONFERENCES or away_conf in POWER_FOUR_CONFERENCES:
                    filtered.append(g)
            return filtered, meta

        if slate_norm == "CONFERENCE":
            filtered = []
            for g in games:
                home_conf, away_conf, _ = conf_meta.get(g["game_id"], (None, None, None))
                if home_conf == conference or away_conf == conference:
                    filtered.append(g)
            return filtered, meta

        # FEATURED
        ranks = _ap_top25(c, season, week, season_type)
        rivalry_pairs = _rivalry_pairs(c)
        spreads = _betting_spreads(c, game_ids)
    finally:
        c.close()

    scored = []
    for g in games:
        home_conf, away_conf, conference_game = conf_meta.get(g["game_id"], (None, None, None))
        s = score_featured(g, ranks, rivalry_pairs, home_conf, away_conf, conference_game,
                            spreads.get(g["game_id"]))
        scored.append((s, g))
    # Tiebreak: score desc, then earliest kickoff, then game_id -- fully
    # deterministic, never random.
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("kickoff") or "", pair[1]["game_id"]))
    return [g for _, g in scored[:FEATURED_TARGET_COUNT]], meta


def build_cfb_slate_package(seed: str, variant: str, season: int, week, *,
                             slate: str | None, conference: str | None) -> dict:
    """CFB-only entrypoint reused identically by the public Gateway route
    and the Creator NL-bridge path. The one place slate/conference gets
    folded into the seed -- package_id is a content hash of
    variant|season|week|seed only (see build_package above), so two
    different real slates for the same (season, week) must get different
    seeds or they'd collide under packages.py's content-addressed
    storage."""
    if variant != "CFB_WEEKLY_PICKEM":
        raise ValueError("build_cfb_slate_package is CFB-only -- NFL has no slate concept")
    slate_norm = normalize_slate(slate)
    seed_with_slate = f"{seed}|slate={slate_norm}" + (f"|conf={conference}" if conference else "")
    package = dict(build_package(seed_with_slate, variant, season, week))
    games, slate_meta = filter_games_for_slate(
        package["games"], slate=slate_norm, conference=conference, season=season, week=week)
    package["games"] = games
    package["game_count"] = len(games)
    package["slate"] = slate_meta["slate"]
    package["conference"] = slate_meta["conference"]
    if len(games) < MIN_GAMES_FOR_SLATE:
        package["qa_status"] = "FAILED"
        package["shortfall_reason"] = (
            f"No real games match slate={slate_norm!r}"
            + (f", conference={conference!r}" if conference else "")
            + f" for {variant}, season={season}, week={week!r} -- refusing to fabricate a slate."
        )
    else:
        package["qa_status"] = "PASSED"
        package["shortfall_reason"] = None
    return package
