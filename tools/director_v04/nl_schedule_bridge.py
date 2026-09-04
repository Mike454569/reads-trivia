"""Natural-language -> schedule-driven mechanic bridge.

WEEKLY_PICKEM and LIVE_WEEKLY_FANTASY_DRAFT are both fully built and fully
playable through POST /v1/creator/mechanics/round (Phase 7A/7B) -- but a
normal-language Creator request never reaches them, because the existing
translator -> tools.director_v02.registry lookup path only ever resolves a
(mechanic, domain, relationship_predicate) triple, and neither mechanic has
one (see weekly_pickem.py's and live_weekly_fantasy_draft.py's own module
docstrings for exactly why: both are schedule-driven -- "what's this week's
real slate/pool" -- not relationship-driven).

This is a small, explicit, standalone bridge, not a second translator: it
recognizes exactly two real intents from free text, extracts the real
(league, season, week) parameters those two mechanics already take, and
returns None for everything else -- including historical game-result
trivia ("who won the Alabama game", already served by the real
NFL_GAME_RESULT/CFB_GAME_RESULT capabilities) and NFL Draft trivia ("who
drafted this player", "what round was this player drafted in", already
served by the real NFL_DRAFT/DRAFTED_BY capability) -- which keep flowing
through the existing translator/registry pipeline completely unchanged.

Season/week extraction: an explicit season/week in the text is always used
as given (parsed, never guessed). When absent, this module resolves real
values rather than fabricating placeholders:
  - season defaults to the current calendar year -- the same real,
    non-arbitrary convention tools/data_refresh/nfl_refresh.py's and
    cfb_refresh.py's own `_current_season()` already use ("a season is
    named for the calendar year it plays in").
  - week defaults to the real current/next week, derived by querying the
    same `games`/`cfb_games_canonical` tables weekly_pickem.py and
    live_weekly_fantasy_draft.py themselves read: the earliest week whose
    first real kickoff hasn't happened yet, or (once a season is over) the
    most recent past week. If that (league, season) has no real schedule
    rows at all, week resolves to None -- an honest gap, surfaced by the
    caller as MISSING_DATA, never guessed around.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from tools.quiz_export import engine as engine_bootstrap  # noqa: E402

# --- WEEKLY_PICKEM recognition ----------------------------------------------
# Deliberately anchored on PREDICTIVE/SELECTION language about a weekly
# slate, never on "won"/"winner of THE [team] game" (past tense, a single
# already-decided historical result) -- that distinction is exactly what
# keeps this from ever intercepting a real WON_GAME/CFB_GAME_RESULT request.
_PICKEM_STRONG_PHRASE = re.compile(r"pick[\s-]?['’]?em\b", re.IGNORECASE)
_PICKEM_VERB = re.compile(
    r"\b(pick|picks|picking|choose|choosing|predict|predicts|predicting|prediction|predictions)\b",
    re.IGNORECASE,
)
_PICKEM_WINNER_WORD = re.compile(r"\bwinners?\b", re.IGNORECASE)
_PICKEM_SLATE_SIGNAL = re.compile(r"\b(week|weekly|slate)\b", re.IGNORECASE)
_LEAGUE_SIGNAL = re.compile(r"\bnfl\b|\bcollege\s+football\b|\bcfb\b|\bncaa\b", re.IGNORECASE)
_DRAFT_WORD = re.compile(r"\bdraft(ed|ing)?\b", re.IGNORECASE)
# Creator Semantic Routing pass: a real, found over-trigger -- "week" alone,
# paired only with the generic verb "pick" (as in "make me PICK who rushed
# for more yards"), used to satisfy the has_slate_or_league+picks? fallback
# below even though the request is a player-STAT comparison, not a weekly
# matchup-winner slate. Weekly Pick'em is fundamentally "predict game
# winners for a real week's slate" -- a request that names a per-game/
# per-player STAT (yards, rushing, passing, receiving, sacks, comparison
# language) is asking a genuinely different question, never this mechanic,
# regardless of whether "week" also appears. See mock.py's own same-week
# stat-comparison block for where this kind of request is honestly reported
# UNDERSTOOD_UNSUPPORTED_MECHANIC instead.
_STAT_COMPARISON_EXCLUSION_RE = re.compile(
    r"\b(yards?|yardage|rushed|rushing|passing|receiving|sacks?|interceptions?|compare|comparison|stats?)\b",
    re.IGNORECASE,
)

# --- LIVE_WEEKLY_FANTASY_DRAFT recognition ----------------------------------
# Anchored on the word "fantasy" itself, paired with a roster-construction
# word -- "fantasy" alone is a rare, unambiguous signal that never appears
# in real NFL-Draft-trivia phrasing ("who drafted this player", "what round
# was this player drafted in"), so requiring it means those stay untouched
# with no separate exclusion list needed.
_FANTASY_ANCHOR = re.compile(r"\bfantasy\b", re.IGNORECASE)
_FANTASY_BUILD_WORD = re.compile(r"\b(draft|drafting|lineup|team|roster)\b", re.IGNORECASE)

_WEEK_RE = re.compile(r"\bweek\s*#?\s*(\d{1,2}|wc|div|con|sb)\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_CFB_RE = re.compile(r"\bcollege\s+football\b|\bcollege\b|\bcfb\b|\bncaa\b", re.IGNORECASE)


def _detect_pickem(text: str) -> bool:
    if _PICKEM_STRONG_PHRASE.search(text):
        return True
    if _PICKEM_VERB.search(text) and _PICKEM_WINNER_WORD.search(text):
        return True
    # "picks"/"predictions" is a genuine weekly-pick'em signal only when
    # paired with a slate/week or league signal -- and never when "draft"
    # is also present ("draft picks" is NFL-Draft-trivia territory, a
    # completely different concept, not a predictive weekly slate).
    if not _DRAFT_WORD.search(text) and not _STAT_COMPARISON_EXCLUSION_RE.search(text):
        has_slate_or_league = bool(_PICKEM_SLATE_SIGNAL.search(text) or _LEAGUE_SIGNAL.search(text))
        if has_slate_or_league and re.search(r"\bpicks?\b", text, re.IGNORECASE):
            return True
        if _PICKEM_SLATE_SIGNAL.search(text) and re.search(r"\bpredictions?\b", text, re.IGNORECASE):
            return True
        # Player Experience pass: "give me the full college football slate"/
        # "give me all NFL games this week" -- a real, distinct intent this
        # app has no OTHER capability to serve (nothing else lists an
        # entire real week's real games), recognized even with neither
        # "pick(s)" nor "prediction(s)" present, as long as a real
        # league/slate/week signal co-occurs. _SLATE_FULL_RE is defined
        # below in this same module (module-level names resolve at call
        # time, not definition order, so this forward reference is safe).
        if has_slate_or_league and _SLATE_FULL_RE.search(text):
            return True
    return False


def _detect_fantasy_draft(text: str) -> bool:
    return bool(_FANTASY_ANCHOR.search(text) and _FANTASY_BUILD_WORD.search(text))


# Player Experience pass: real, CFB-only concepts (no NFL equivalent in
# this app -- the NFL has no AP-style Top 25 human poll, no "Power Four"
# grouping, no conference identity exposed anywhere in this app's NFL
# data) that a real request can use WITHOUT ever saying "college"/"cfb"
# explicitly (e.g. "Give me Top 25 Pick'em", "Give me an SEC Pick'em").
# _CONFERENCE_ALIASES is defined below in this same module -- reused here,
# never duplicated, so a real conference name only has to be listed once.
_CFB_ONLY_CONCEPT_RE = re.compile(r"\btop[\s-]?25\b|\bpower\s*(four|4)\b", re.IGNORECASE)


def _league_for(text: str) -> str:
    if _CFB_RE.search(text) or _CFB_ONLY_CONCEPT_RE.search(text):
        return "CFB"
    lowered = text.lower()
    for alias in _CONFERENCE_ALIASES:
        if re.search(r"\b" + re.escape(alias) + r"\b", lowered):
            return "CFB"
    return "NFL"


def _explicit_week(text: str) -> str | None:
    m = _WEEK_RE.search(text)
    return m.group(1).upper() if m else None


def _explicit_season(text: str) -> int | None:
    m = _YEAR_RE.search(text)
    return int(m.group(0)) if m else None


def _current_season() -> int:
    return datetime.now(timezone.utc).year


def resolve_current_week(c, league: str, season: int) -> str | None:
    """Real current/next week for (league, season), derived from the live
    schedule tables -- never fabricated. Returns None only when this
    (league, season) has no real schedule rows at all.

    Creator/Game Quality Correction pass, real bug fix: the NFL branch used
    to scope its own query to game_type='REG' only. Once every real REG
    week's date was in the past, it fell through to "the last REG week"
    (e.g. "18") FOREVER -- including during a real, live postseason
    (Wild Card/Divisional/Conference/Super Bowl), silently generating a
    pick'em for an already-finished regular-season week instead of the
    live postseason slate. `games.week` is a real, globally sequential
    integer across REG and postseason rows (confirmed directly: REG runs
    1-18, then WC=19/DIV=20/CON=21/SB=22, never reused) -- now includes
    every game_type, and returns the real game_type CODE (not the numeric
    week) for a postseason week, matching what weekly_pickem.py's own
    _nfl_slate_rows() / _NFL_POSTSEASON_WEEK_CODES already expect."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if league == "NFL":
        rows = c.execute(
            "SELECT week, game_type, MIN(game_date) AS first_date FROM games "
            "WHERE season=? GROUP BY week, game_type", (season,),
        ).fetchall()
        weeks = [(r["week"], r["game_type"], r["first_date"]) for r in rows if r["first_date"]]
        if not weeks:
            return None
        weeks.sort(key=lambda w: w[2])
        for week, game_type, first_date in weeks:
            if first_date[:10] >= today:
                return game_type if game_type != "REG" else str(week)
        last_week, last_game_type, _ = weeks[-1]  # every real game already final -- most recent past week
        return last_game_type if last_game_type != "REG" else str(last_week)

    # Dynamic Weekly Pick'em pass, real bug fix: cfb_games_canonical.week is
    # NOT globally unique across season_type the way games.week already is
    # for NFL (confirmed live: season=2025,week=1 holds 200 real regular-
    # season games PLUS 43 real bowls PLUS 11 real CFP games, all
    # mislabeled week=1). Scoping to season_type='regular' here fixes the
    # same real bug class the NFL branch above was already fixed for --
    # without it, a live CFB postseason would silently resolve back to a
    # bowl/CFP game mislabeled as an early regular-season week instead.
    rows = c.execute(
        "SELECT week, MIN(game_date) AS first_date, MAX(game_date) AS last_date FROM cfb_games_canonical "
        "WHERE season=? AND season_type='regular' GROUP BY week", (season,),
    ).fetchall()
    weeks = [(r["week"], r["first_date"], r["last_date"]) for r in rows if r["first_date"]]

    # Dynamic Weekly Pick'em pass, second real bug fix found while verifying
    # the first one: gather EVERY real candidate slate (regular weeks, each
    # CFP round, bowls) as (identifier, first_date, last_date) and rank them
    # UNIFORMLY by real date, rather than checking regular season first and
    # only falling back to postseason as an afterthought -- the earlier
    # version's final fallback (`weeks[-1]`) could return a real, but
    # already-superseded, LAST REGULAR week even once the real postseason
    # (which runs weeks after the regular season ends) had also already
    # finished, since it never compared against real postseason dates at
    # all. Tokens match weekly_pickem.py's own
    # _CFB_POSTSEASON_WEEK_TOKENS/_CFP_ROUND_TO_TOKEN exactly.
    candidates = [(str(week), first_date, last_date) for week, first_date, last_date in weeks]
    cfp_round_to_token = {
        "first_round": "CFP_FIRST_ROUND", "quarterfinal": "CFP_QUARTERFINAL",
        "semifinal": "CFP_SEMIFINAL", "championship": "CFP_CHAMPIONSHIP",
    }
    for round_name, token in cfp_round_to_token.items():
        row = c.execute(
            "SELECT MIN(game_date) AS d, MAX(game_date) AS d2 FROM cfb_games_canonical "
            "WHERE season=? AND is_playoff=1 AND playoff_round=?", (season, round_name),
        ).fetchone()
        if row["d"]:
            candidates.append((token, row["d"], row["d2"]))
    bowl_row = c.execute(
        "SELECT MIN(game_date) AS d, MAX(game_date) AS d2 FROM cfb_games_canonical "
        "WHERE season=? AND season_type='postseason' AND is_playoff=0", (season,),
    ).fetchone()
    if bowl_row["d"]:
        candidates.append(("BOWLS", bowl_row["d"], bowl_row["d2"]))

    if not candidates:
        return None  # genuinely no real schedule rows for this (league, season) at all

    # Real bug fix found verifying this live against the actual 2026 season:
    # a candidate's own real date RANGE can be wide enough (CFB week=1 alone
    # -- this source folds the informal "Week 0" season-openers into week=1
    # rather than giving them a distinct label -- spans a real 10 calendar
    # days, Aug 29-Sep 7 for 2026) that some of its games are already
    # final while most are still upcoming. Testing only first_date (as the
    # original version did) treated ANY already-played game within a week
    # as proof the WHOLE week was over, incorrectly jumping straight to
    # week 2 while 91 of week 1's 99 real games were still ahead. The real,
    # correct test is whether the slate's LAST real game has passed yet --
    # not its first.
    not_yet_concluded = [cand for cand in candidates if cand[2][:10] >= today]
    if not_yet_concluded:
        not_yet_concluded.sort(key=lambda cand: cand[1])
        return not_yet_concluded[0][0]  # the real slate with the earliest start that isn't fully over yet
    # Every real slate (regular AND postseason) is already in the past --
    # the one whose own real games ran LATEST is the most recently
    # concluded real story, never just "the last regular week" regardless
    # of whether a real postseason ran even later.
    candidates.sort(key=lambda cand: cand[2])
    return candidates[-1][0]


# --- CFB Pick'em slate recognition (Player Experience pass) ----------------
# Real behavioral fix: a bare CFB Pick'em request used to return the ENTIRE
# real week's slate (up to 99 games for a real Week 1) -- unplayable.
# Default (no slate keyword matched) is now FEATURED, never FULL. NFL
# requests never populate slate/conference at all (NFL has no slate
# concept -- weekly_pickem.py's own CFB_SLATES/build_cfb_slate_package are
# CFB-only by design).
# Player Experience pass, real bug fix found while testing this against
# the user's own real phrase list: the original tight `\s+` between
# full/all/every and slate/games/schedule never matched a real phrase with
# a league name in between ("full COLLEGE FOOTBALL slate", "all NFL
# games") -- allows up to 3 intervening words (a real league/context
# phrase, never an unbounded/greedy gap that could span an unrelated
# clause).
_SLATE_FULL_RE = re.compile(
    r"\b(full|all|every)\b(?:\s+\w+){0,3}?\s+(slate|games?|schedule)\b|\bevery\s+game\b", re.IGNORECASE
)
_SLATE_FEATURED_RE = re.compile(r"\bfeatured\b|\bbest\s+games?\b", re.IGNORECASE)
_SLATE_TOP25_RE = re.compile(r"\btop[\s-]?25\b|\branked\b", re.IGNORECASE)
_SLATE_POWER4_RE = re.compile(r"\bpower\s*(four|4)\b", re.IGNORECASE)

# lowercase alias -> the exact real conference-name string
# tools.director_v04.weekly_pickem.REAL_CFB_CONFERENCES also uses (every
# value below is a real member of that set, confirmed live against the
# 2026 source data -- weekly_pickem.filter_games_for_slate() re-validates
# against that same set at slate-build time, so a typo here would surface
# as a real INVALID_REQUEST, never a silently-empty slate).
_CONFERENCE_ALIASES = {
    "sec": "SEC", "big ten": "Big Ten", "b1g": "Big Ten", "big 12": "Big 12", "big twelve": "Big 12",
    "acc": "ACC", "pac-12": "Pac-12", "pac 12": "Pac-12",
    "american athletic": "American Athletic", "aac": "American Athletic",
    "mountain west": "Mountain West", "conference usa": "Conference USA", "c-usa": "Conference USA",
    "mid-american": "Mid-American", "mac": "Mid-American", "sun belt": "Sun Belt", "swac": "SWAC",
}


def _detect_cfb_slate(text: str) -> tuple[str | None, str | None]:
    """Returns (slate, conference) -- both None if no slate keyword or real
    conference name is present in the text (the caller defaults to
    FEATURED in that case). Conference aliases are checked first and
    longest-alias-first, so e.g. "big ten" is never partially matched by a
    looser future alias fragment."""
    lowered = text.lower()
    for alias, real_name in sorted(_CONFERENCE_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"\b" + re.escape(alias) + r"\b", lowered):
            return "CONFERENCE", real_name
    if _SLATE_FULL_RE.search(text):
        return "FULL", None
    if _SLATE_FEATURED_RE.search(text):
        return "FEATURED", None
    if _SLATE_POWER4_RE.search(text):
        return "POWER4", None
    if _SLATE_TOP25_RE.search(text):
        return "TOP25", None
    return None, None


def detect(request_text: str | None) -> dict | None:
    """Returns {"taxonomy_id", "variant", "league", "season", "week",
    "slate", "conference"} for a recognized WEEKLY_PICKEM /
    LIVE_WEEKLY_FANTASY_DRAFT request (season/week always real -- explicit
    from the text, or resolved from the live schedule; week is None only
    when genuinely no real schedule exists yet for that (league, season)).
    slate/conference are populated only for a CFB Pick'em request (None for
    NFL and for LIVE_WEEKLY_FANTASY_DRAFT, which have no slate concept) --
    slate defaults to "FEATURED" when no slate keyword/conference name is
    present in the text, never "FULL". Returns None if this text isn't one
    of these two intents, so the caller keeps using the existing
    translator/registry pipeline unchanged."""
    text = request_text or ""
    is_fantasy = _detect_fantasy_draft(text)
    is_pickem = False if is_fantasy else _detect_pickem(text)
    if not is_fantasy and not is_pickem:
        return None

    taxonomy_id = "LIVE_WEEKLY_FANTASY_DRAFT" if is_fantasy else "WEEKLY_PICKEM"
    league = _league_for(text)
    variant = f"{league}_WEEKLY_FANTASY_DRAFT" if is_fantasy else f"{league}_WEEKLY_PICKEM"

    season = _explicit_season(text) or _current_season()
    week = _explicit_week(text)
    if week is None:
        c = engine_bootstrap.connect()
        try:
            week = resolve_current_week(c, league, season)
        finally:
            c.close()

    slate = conference = None
    if is_pickem and league == "CFB":
        slate, conference = _detect_cfb_slate(text)
        if slate is None:
            slate = "FEATURED"

    return {"taxonomy_id": taxonomy_id, "variant": variant, "league": league, "season": season, "week": week,
            "slate": slate, "conference": conference}
