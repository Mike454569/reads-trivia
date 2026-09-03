"""Shared real-status/winner derivation, used identically by
nfl_games_refresh.py and cfb_games_refresh.py so both leagues follow the
exact same real, disclosed rule during every schedule refresh -- never two
almost-the-same reimplementations that could quietly drift apart.

Real, disclosed limitation, confirmed directly against both live upstream
sources (nflverse's games.csv, cfbfastR's schedules CSV): neither ever
carries a live in-play, postponed, or canceled signal -- a canceled game
is simply absent as a row, never flagged. So:
  - FINAL + winner is only ever set from a real score pair -- never guessed.
  - IN_PROGRESS is a heuristic inferred purely from elapsed real kickoff
    time (a generous real window that covers a real overtime game), never
    a true live feed value.
  - POSTPONED/CANCELED can only ever be set by the admin override
    (gateway/services/admin_pickem.py) -- no refresh ever sets either
    value itself, and a refresh must never silently clear one an admin
    already set, UNLESS real evidence now contradicts it (a real score
    has appeared, or the source now reports a materially different real
    kickoff -- i.e. a real reschedule, not a stale flag lingering forever).
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KICKOFF_TO_LIKELY_FINAL_HOURS = 5.5
_ADMIN_ONLY_STATUSES = ("POSTPONED", "CANCELED")
_EASTERN = ZoneInfo("America/New_York")


def parse_iso(raw: str | None) -> datetime | None:
    """CFB's game_date is already a full ISO-8601 UTC timestamp -- also the
    generic fallback for an NFL row with a blank game_time (historical rows
    only; every real 2026 games.csv row has a real game_time -- see
    nfl_kickoff_utc below for the real, precise path)."""
    if not raw:
        return None
    text = raw.replace("Z", "+00:00")
    for candidate in (text, text[:10]):
        try:
            dt = datetime.fromisoformat(candidate)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def nfl_kickoff_utc(game_date: str | None, game_time: str | None) -> datetime | None:
    """Real NFL kickoff, combining the two separate real source fields --
    `games.game_date` is date-only ('2026-09-13'); the real kickoff HOUR
    lives in the separate `games.game_time` column ('13:00', '20:20').
    Confirmed directly against nflverse's own published data dictionary:
    gametime is real, 24-hour, and always Eastern regardless of the actual
    game's time zone -- so this is a deterministic real conversion, not a
    guess. Without game_time (historical rows only -- every real 2026 row
    has one), falls back to date-only UTC, same as before this pass."""
    if not game_date:
        return None
    if game_time:
        try:
            hh, mm = game_time.split(":")[:2]
            local = datetime.fromisoformat(game_date).replace(hour=int(hh), minute=int(mm), tzinfo=_EASTERN)
            return local.astimezone(timezone.utc)
        except (ValueError, IndexError):
            pass
    return parse_iso(game_date)


def derive_pending_status(kickoff: datetime | None, *, now: datetime | None = None) -> str:
    """Only ever called for a game with no real score yet -- a FINAL game's
    status is always derived directly from its real scores instead (see
    compute_status_and_winner below)."""
    if kickoff is None:
        return "UNKNOWN"
    now = now or datetime.now(timezone.utc)
    if kickoff > now:
        return "SCHEDULED"
    elapsed_hours = (now - kickoff).total_seconds() / 3600.0
    if elapsed_hours <= KICKOFF_TO_LIKELY_FINAL_HOURS:
        return "IN_PROGRESS"
    return "UNKNOWN"  # real gap: data lag, or an undetected postponement -- never guessed further


def compute_status_and_winner(
    *, existing_status: str | None, existing_kickoff: datetime | None, new_kickoff: datetime | None,
    home_score, away_score, home_code: str, away_code: str, now: datetime | None = None,
) -> tuple[str, str | None]:
    """Real, single source of truth for what a refresh should WRITE for one
    game's `status`/`winner` this run, given its OLD persisted status (read
    before this UPSERT) and the NEW real values just fetched from source."""
    if home_score is not None and away_score is not None:
        winner = "TIE" if home_score == away_score else (home_code if home_score > away_score else away_code)
        return "FINAL", winner
    if existing_status in _ADMIN_ONLY_STATUSES:
        reschedule = existing_kickoff is not None and new_kickoff is not None and existing_kickoff != new_kickoff
        if not reschedule:
            return existing_status, None
    return derive_pending_status(new_kickoff, now=now), None
