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
    return False


def _detect_fantasy_draft(text: str) -> bool:
    return bool(_FANTASY_ANCHOR.search(text) and _FANTASY_BUILD_WORD.search(text))


def _league_for(text: str) -> str:
    return "CFB" if _CFB_RE.search(text) else "NFL"


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
    (league, season) has no real schedule rows at all."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if league == "NFL":
        rows = c.execute(
            "SELECT week, MIN(game_date) AS first_date FROM games "
            "WHERE season=? AND game_type='REG' GROUP BY week", (season,),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT week, MIN(game_date) AS first_date FROM cfb_games_canonical "
            "WHERE season=? GROUP BY week", (season,),
        ).fetchall()
    weeks = [(r["week"], r["first_date"]) for r in rows if r["first_date"]]
    if not weeks:
        return None
    weeks.sort(key=lambda w: w[1])
    for week, first_date in weeks:
        if first_date[:10] >= today:
            return str(week)
    return str(weeks[-1][0])  # every real game already final -- most recent past week


def detect(request_text: str | None) -> dict | None:
    """Returns {"taxonomy_id", "variant", "league", "season", "week"} for a
    recognized WEEKLY_PICKEM / LIVE_WEEKLY_FANTASY_DRAFT request (season/week
    always real -- explicit from the text, or resolved from the live
    schedule; week is None only when genuinely no real schedule exists yet
    for that (league, season)) -- or None if this text isn't one of these
    two intents, so the caller keeps using the existing translator/registry
    pipeline unchanged."""
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

    return {"taxonomy_id": taxonomy_id, "variant": variant, "league": league, "season": season, "week": week}
