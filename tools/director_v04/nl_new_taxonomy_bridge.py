"""Natural-language -> new-taxonomy bridge (40-Format Expansion pass).

Same real gap, same fix pattern as nl_schedule_bridge.py/nl_mechanic_bridge.py:
the 6 new mechanic_engine.py taxonomies this pass added (GRID_CONSTRAINT_BOARD,
DRIVE_PROGRESSION, ROSTER_BUILD, KNOCKOUT_BRACKET, RELATIONSHIP_CHAIN,
BRANCH_STATE) have no (mechanic, domain, relationship_predicate) triple, so
a plain-English Creator request can never reach them through the normal
translator/registry pipeline. This is the analogous small, explicit,
standalone bridge for these 6 -- checked in gateway/services/creator.py
AFTER nl_schedule_bridge and nl_mechanic_bridge (most-specific-first,
documented order), never a change to either of those or to
providers/mock.py's own fragile if/elif chain.

Same anti-false-positive discipline as nl_mechanic_bridge.py: every pattern
requires a genuinely distinctive phrase (never a bare common word like
"draft" or "grid" alone) -- e.g. AUCTION_DRAFT requires ("auction"|"budget")
together with "draft", so a plain "make me a draft game" is untouched and
keeps resolving to the existing NFL_DRAFT capability exactly as it always
has.
"""
from __future__ import annotations

import re

_CFB_SIGNAL = re.compile(r"\bcollege\s+football\b|\bcfb\b|\bncaa\b|\bcollege\b", re.IGNORECASE)


def _league_for(text: str) -> str:
    return "CFB" if _CFB_SIGNAL.search(text) else "NFL"


# --- CONNECTION_GRID (GRID_CONSTRAINT_BOARD) --------------------------------
_CONNECTION_GRID_RE = re.compile(
    r"\bconnection\s+grid\b|\b3x3\s+grid\b|\bconnect(ion)?\s+grid\s+trivia\b", re.IGNORECASE,
)

# --- PERFECT_DRIVE / GOAL_LINE_STAND (DRIVE_PROGRESSION) --------------------
_PERFECT_DRIVE_RE = re.compile(r"\bperfect\s+drive\b|\bdrive\s+down\s+the\s+field\b", re.IGNORECASE)
# "four[- ]down(s)" covers both "four downs" and the user's own real
# example phrasing "four-down CFB trivia game" (a hyphenated adjective,
# not the plural noun phrase the original pattern alone required).
_GOAL_LINE_STAND_RE = re.compile(r"\bgoal\s+line\s+stand\b|\bfour[\s-]+downs?\b", re.IGNORECASE)

# --- LINEUP_BUILDER / AUCTION_DRAFT / CAP_CHALLENGE (ROSTER_BUILD) ----------
# Also covers the user's own real example phrasing "skill-position lineup
# game" / "skill position lineup" -- always anchored to "lineup" together
# with a build/construct signal, never a bare "lineup" alone (which must
# keep meaning the existing POSITION_LINEUP_GRID guess capability).
_LINEUP_BUILDER_RE = re.compile(
    r"\bbuild\s+an?\s+offense\b|\blineup\s+builder\b|"
    r"\b(build|construct)\w*\b.{0,30}\b(skill[\s-]position)?\s*lineup\b|"
    r"\bskill[\s-]position\s+lineup\b",
    re.IGNORECASE,
)
_AUCTION_DRAFT_RE = re.compile(
    r"\bauction\s+draft\b|\b(give|giving)\s+(everyone|each\s+player)\s+a\s+budget\b", re.IGNORECASE,
)
_CAP_CHALLENGE_RE = re.compile(r"\b(salary\s+)?cap\s+challenge\b", re.IGNORECASE)

# --- KNOCKOUT_TOURNAMENT (KNOCKOUT_BRACKET) ---------------------------------
_KNOCKOUT_RE = re.compile(r"\bknockout\s+tournament\b|\belimination\s+bracket\b", re.IGNORECASE)
_SIZE_16_RE = re.compile(r"\b16\b|\bsixteen\b", re.IGNORECASE)

# --- SIX_DEGREES / CHAIN_REACTION (RELATIONSHIP_CHAIN) ----------------------
_SIX_DEGREES_RE = re.compile(
    r"\bsix\s+degrees\b|\bconnect\s+these\s+two\s+players\b", re.IGNORECASE,
)
_CHAIN_REACTION_RE = re.compile(r"\bchain\s+reaction\b", re.IGNORECASE)

# --- CHOOSE_YOUR_PATH (BRANCH_STATE) ----------------------------------------
# [\s-]+ (not just \s+) so the user's own real example phrasing
# "choose-your-path" (hyphenated) matches, not only "choose your path".
_CHOOSE_YOUR_PATH_RE = re.compile(r"\bchoose[\s-]+your[\s-]+path\b", re.IGNORECASE)


def detect(request_text: str | None) -> dict | None:
    """Returns {"taxonomy_id", "variant", "format", "gen_kwargs"} for a
    recognized request, or None -- in which case the caller keeps using the
    existing nl_mechanic_bridge / translator pipeline unchanged."""
    text = request_text or ""

    if _CONNECTION_GRID_RE.search(text):
        return {"taxonomy_id": "GRID_CONSTRAINT_BOARD", "variant": "NFL_TEAM_DRAFT_ROUND_GRID",
                "format": "CONNECTION_GRID", "gen_kwargs": {}}

    if _GOAL_LINE_STAND_RE.search(text):
        league = _league_for(text)
        variant = "CFB_HEISMAN_GOAL_LINE_STAND" if league == "CFB" else "NFL_DRAFT_GOAL_LINE_STAND"
        return {"taxonomy_id": "DRIVE_PROGRESSION", "variant": variant,
                "format": "GOAL_LINE_STAND", "gen_kwargs": {"question_count": 10}}

    if _PERFECT_DRIVE_RE.search(text):
        league = _league_for(text)
        variant = "CFB_HEISMAN_PERFECT_DRIVE" if league == "CFB" else "NFL_DRAFT_PERFECT_DRIVE"
        return {"taxonomy_id": "DRIVE_PROGRESSION", "variant": variant,
                "format": "PERFECT_DRIVE", "gen_kwargs": {"question_count": 15}}

    if _AUCTION_DRAFT_RE.search(text):
        return {"taxonomy_id": "ROSTER_BUILD", "variant": "NFL_AUCTION_DRAFT",
                "format": "AUCTION_DRAFT", "gen_kwargs": {}}

    if _CAP_CHALLENGE_RE.search(text):
        return {"taxonomy_id": "ROSTER_BUILD", "variant": "NFL_AUCTION_DRAFT",
                "format": "CAP_CHALLENGE", "gen_kwargs": {}}

    if _LINEUP_BUILDER_RE.search(text):
        return {"taxonomy_id": "ROSTER_BUILD", "variant": "NFL_2010S_OFFENSE_BUILDER",
                "format": "LINEUP_BUILDER", "gen_kwargs": {}}

    if _KNOCKOUT_RE.search(text):
        league = _league_for(text)
        size = "16" if _SIZE_16_RE.search(text) else "4"
        variant = f"{league}_TEAM_SEASON_WINS_KNOCKOUT_{size}"
        return {"taxonomy_id": "KNOCKOUT_BRACKET", "variant": variant,
                "format": "KNOCKOUT_TOURNAMENT", "gen_kwargs": {}}

    if _SIX_DEGREES_RE.search(text):
        return {"taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
                "format": "SIX_DEGREES", "gen_kwargs": {"chain_count": 8}}

    if _CHAIN_REACTION_RE.search(text):
        return {"taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
                "format": "CHAIN_REACTION", "gen_kwargs": {"chain_count": 8}}

    if _CHOOSE_YOUR_PATH_RE.search(text):
        return {"taxonomy_id": "BRANCH_STATE", "variant": "NFL_TOPIC_PATH",
                "format": "CHOOSE_YOUR_PATH", "gen_kwargs": {}}

    return None
