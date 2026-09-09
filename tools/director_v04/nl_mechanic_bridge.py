"""Natural-language -> direct-taxonomy mechanic bridge (public-readiness
punch-list, item 6).

MATCHING, SORTING_TIMELINE, HIGHER_LOWER_STREAK, ELIMINATION_SURVIVAL, and
POSITION_LINEUP_GRID are all real, fully playable through
POST /v1/creator/mechanics/round -- but, same real gap
nl_schedule_bridge.py already documents for WEEKLY_PICKEM/
LIVE_WEEKLY_FANTASY_DRAFT, a normal-language Creator request never reaches
them: the existing translator only ever resolves a (mechanic, domain,
relationship_predicate) triple for the "guess"/"identify_player_from_clues"
mechanics. This is the analogous small, explicit, standalone bridge for
these five -- never a redesign of the translator itself.

Deliberately narrow, anchored phrasing (never a bare common word like
"match" or "sort" alone) -- same anti-false-positive discipline
nl_schedule_bridge.py already established, so this never intercepts an
unrelated request the real translator/registry pipeline already serves
correctly (e.g. "which players match this description" is NOT a MATCHING
request; "sort of a rivalry game" is NOT a SORTING_TIMELINE request).

POSITION_LINEUP_GRID has NO real CFB variant (see mechanic_engine.py's own
VARIANTS registry -- both its variants are NFL-only). A lineup request that
explicitly names CFB/college football is therefore NOT matched here at
all (returns None, falls through to the normal pipeline, which reports an
honest unsupported/missing-capability state) -- silently substituting an
NFL lineup board for an explicit CFB request would be exactly the kind of
false routing this bridge must never do.
"""
from __future__ import annotations

import re

_CFB_SIGNAL = re.compile(r"\bcollege\s+football\b|\bcfb\b|\bncaa\b|\bcollege\b", re.IGNORECASE)
_NFL_SIGNAL = re.compile(r"\bnfl\b|\bpro\s+football\b", re.IGNORECASE)

# --- MATCHING ---------------------------------------------------------------
_MATCHING_RE = re.compile(
    r"\bmatch(ing)?\s+(game|these|players?|picks?)\b|"
    r"\b(a|the)?\s*matching\s+game\b|"
    r"\bmatch\s+these\s+.*\bto\b|"
    r"\bpair(ing)?\s+(up\s+)?game\b",
    re.IGNORECASE,
)

# --- SORTING_TIMELINE ---------------------------------------------------------
_SORTING_RE = re.compile(
    r"\bsort(ing)?\s+(game|these|players?)\b|"
    r"\bput\s+these\s+.*\bin\s+order\b|"
    r"\border(ing)?\s+game\b|"
    r"\btimeline\s+game\b",
    re.IGNORECASE,
)

# --- HIGHER_LOWER_STREAK ---------------------------------------------------
_HIGHER_LOWER_RE = re.compile(
    r"\bhigher\s+or\s+lower\b|\bhigher[/\-]lower\b|"
    r"\bwho\s+had\s+more\b.*\byards?\b|"
    r"\bstreak\s+game\b.*\b(stat|yard|win)s?\b",
    re.IGNORECASE,
)

# --- ELIMINATION_SURVIVAL ---------------------------------------------------
_ELIMINATION_RE = re.compile(
    r"\belimination\s+game\b|\bsurvival\s+game\b|"
    r"\bodd[\s-]one[\s-]out\b|"
    r"\bkeep\s+eliminating\b|"
    r"\beliminat(e|ing)\s+the\s+one\s+that\s+doesn'?t\s+belong\b",
    re.IGNORECASE,
)

# --- COMPARISON_BRACKET (Reusable Game Format System pass) ------------------
_COMPARISON_RE = re.compile(
    r"\bbracket\s+game\b|\ba\s+bracket\b|\bin\s+a\s+bracket\b|"
    r"\bmake\s+.*\bbracket\b|"
    r"\bhead[\s-]to[\s-]head\s+bracket\b",
    re.IGNORECASE,
)

# --- POSITION_LINEUP_GRID ---------------------------------------------------
_LINEUP_RE = re.compile(
    r"\bguess\s+the\s+team\s+from\s+(its|the)\s+lineup\b|"
    r"\blineup\s+grid\b|"
    r"\bguess\s+the\s+(nfl\s+)?team\s+from\s+its\s+offensive\s+players\b|"
    r"\bstarting\s+lineup\b.*\bguess\b|\bguess\b.*\bstarting\s+lineup\b",
    re.IGNORECASE,
)

_LEAGUE_VARIANT = {
    "MATCHING": {"NFL": "NFL_DRAFT_CLASS_MATCH", "CFB": "CFB_HEISMAN_SCHOOL_MATCH"},
    "SORTING_TIMELINE": {"NFL": "NFL_DRAFT_PICK_ORDER", "CFB": "CFB_HEISMAN_YEAR_ORDER"},
    "HIGHER_LOWER_STREAK": {"NFL": "NFL_TEAM_SEASON_WINS", "CFB": "CFB_TEAM_SEASON_WINS"},
    "ELIMINATION_SURVIVAL": {"NFL": "NFL_SUPER_BOWL_CHAMPION_SURVIVAL", "CFB": "CFB_NATIONAL_CHAMPION_SURVIVAL"},
    "COMPARISON_BRACKET": {"NFL": "NFL_TEAM_SEASON_WINS_BRACKET", "CFB": "CFB_TEAM_SEASON_WINS_BRACKET"},
}

# Reusable Game Format System pass: real, narrow-anchored FORMAT keyword
# detection layered onto the same `detect()` result -- format is a
# separate dimension from mechanic/variant (see visual_templates.py's own
# module comment), so this never changes which taxonomy_id/variant match
# above; it only adds an optional "format" key the caller can validate
# against that capability's real supported_formats (mechanic_engine.py
# has no opinion on formats at all -- format compatibility is checked in
# gateway/services/creator.py, alongside the visual_templates.py registry).
_FORMAT_RE = {
    "TIMELINE_RIBBON": re.compile(r"\btimeline\b|\bribbon\b", re.IGNORECASE),
    "BRACKET_TREE": re.compile(r"\bbracket\b", re.IGNORECASE),
}


def detect_format(request_text: str | None) -> str | None:
    """Returns a real format_id if the request names one by a real, narrow
    keyword, else None (meaning "no format requested -- auto-select").
    Never guesses from an ambiguous word alone (e.g. plain "order" or
    "sort" doesn't imply TIMELINE_RIBBON specifically -- only "timeline"/
    "ribbon" do)."""
    text = request_text or ""
    for format_id, pattern in _FORMAT_RE.items():
        if pattern.search(text):
            return format_id
    return None


def _league_for(text: str) -> str:
    """Real, explicit signal only -- CFB requires an explicit college/CFB/
    NCAA mention; everything else (including no league mentioned at all)
    defaults to NFL, matching every other mechanic's own default
    (mechanic_engine.py's PUBLIC_MECHANIC_MODES and the admin route both
    require an explicit variant -- NFL is the more common request in
    practice, same real-world default nl_schedule_bridge.py's own
    _league_for already uses)."""
    return "CFB" if _CFB_SIGNAL.search(text) else "NFL"


def detect(request_text: str | None) -> dict | None:
    """Returns {"taxonomy_id", "variant", "format"} for a recognized
    MATCHING/SORTING_TIMELINE/HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL/
    COMPARISON_BRACKET/POSITION_LINEUP_GRID request, or None -- in which
    case the caller keeps using the existing translator/registry pipeline
    (or nl_schedule_bridge.py) unchanged. `format` is None when no real
    format keyword was matched (see detect_format() above) -- the caller
    auto-selects in that case, never treats None as a rejection."""
    text = request_text or ""

    if _LINEUP_RE.search(text):
        if _CFB_SIGNAL.search(text):
            # No real CFB POSITION_LINEUP_GRID variant exists -- never
            # silently substitute the NFL one for an explicit CFB request.
            return None
        return {"taxonomy_id": "POSITION_LINEUP_GRID", "variant": "NFL_OFFENSE_LINEUP_COLLEGE_TEAM_ONLY", "format": None}

    for taxonomy_id, pattern in (
        ("MATCHING", _MATCHING_RE),
        ("SORTING_TIMELINE", _SORTING_RE),
        ("HIGHER_LOWER_STREAK", _HIGHER_LOWER_RE),
        ("ELIMINATION_SURVIVAL", _ELIMINATION_RE),
        ("COMPARISON_BRACKET", _COMPARISON_RE),
    ):
        if pattern.search(text):
            league = _league_for(text)
            return {"taxonomy_id": taxonomy_id, "variant": _LEAGUE_VARIANT[taxonomy_id][league],
                    "format": detect_format(text)}

    return None
