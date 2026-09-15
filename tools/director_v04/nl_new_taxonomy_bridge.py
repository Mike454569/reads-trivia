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
    """A real CFB conference name (e.g. "SEC football") is just as strong a
    CFB signal as the word "college" itself -- the user's own real example
    phrase "choose-your-path game about SEC football" has no "college"/
    "cfb"/"ncaa" token at all, so relying on _CFB_SIGNAL alone would
    silently mis-route it to the NFL tree."""
    if _CFB_SIGNAL.search(text):
        return "CFB"
    lowered = text.lower()
    for alias in _CONFERENCE_ALIASES:
        if re.search(r"\b" + re.escape(alias) + r"\b", lowered):
            return "CFB"
    return "NFL"


# --- Real, DB-validated school/conference/franchise filter extraction for
# ROSTER_BUILD requests (LINEUP_BUILDER/AUCTION_DRAFT/CAP_CHALLENGE) -------
# Reuses nl_schedule_bridge.py's own real _CONFERENCE_ALIASES (never
# duplicated -- every value is a confirmed member of
# weekly_pickem.REAL_CFB_CONFERENCES) plus roster_build.py's own real
# school/franchise resolvers, so a filter is only ever populated when it
# genuinely resolves against certified Engine data -- never a guessed or
# fabricated name.
from tools.director_v04.nl_schedule_bridge import _CONFERENCE_ALIASES  # noqa: E402

_PROPER_RUN_RE = re.compile(r"\b[A-Z][a-zA-Z.'&]*(?:\s+[A-Z][a-zA-Z.'&]*)*\b")
_FILTER_STOPWORDS = {
    "build", "give", "giving", "make", "create", "generate", "lineup", "builder",
    "skill", "position", "auction", "draft", "budget", "cap", "challenge", "cfb",
    "nfl", "ncaa", "college", "football", "trivia", "game", "me", "i", "a", "an",
    "the", "for", "with", "using", "based", "on", "of", "and",
}


def _trim_stopwords(tokens: list[str]) -> list[str]:
    start, end = 0, len(tokens)
    while start < end and tokens[start].lower() in _FILTER_STOPWORDS:
        start += 1
    while end > start and tokens[end - 1].lower() in _FILTER_STOPWORDS:
        end -= 1
    return tokens[start:end]


def _proper_noun_candidates(text: str) -> list[str]:
    """Longest-first list of plausible school/franchise name candidates --
    trims generic request words (Build/Give/CFB/NFL/etc.) off both ends of
    each capitalized-word run, and also offers the run's last word alone
    (e.g. "Packers" out of "Green Bay Packers", "Alabama" out of "the
    Alabama Crimson Tide"). Every candidate still has to resolve against
    real Engine data below -- this only narrows what gets tried."""
    candidates: list[str] = []
    for m in _PROPER_RUN_RE.finditer(text):
        trimmed = _trim_stopwords(m.group(0).split())
        if not trimmed:
            continue
        candidates.append(" ".join(trimmed))
        if len(trimmed) > 1:
            candidates.append(trimmed[-1])
    seen: list[str] = []
    for cand in sorted(candidates, key=len, reverse=True):
        if cand not in seen:
            seen.append(cand)
    return seen


def _extract_roster_filters(text: str) -> tuple[str | None, dict]:
    """Returns (league_override, filters). league_override is None when no
    real school/franchise name resolved, in which case the caller falls
    back to _league_for(text)'s plain keyword check. Never invents a
    filter value -- a candidate only becomes a filter once it is confirmed
    against the real Engine database (schools / team_seasons tables)."""
    from tools.director_v04.roster_build import _cfb_school_id_for_name, _nfl_franchise_team_codes
    from tools.quiz_export import engine as engine_bootstrap

    filters: dict = {}
    lowered = text.lower()
    for alias, real_name in sorted(_CONFERENCE_ALIASES.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"\b" + re.escape(alias) + r"\b", lowered):
            filters["conference"] = real_name
            break

    candidates = _proper_noun_candidates(text)
    school_name = franchise_name = None
    if candidates:
        c = engine_bootstrap.connect()
        try:
            for cand in candidates:
                if _cfb_school_id_for_name(c, cand):
                    school_name = cand
                    break
                if _nfl_franchise_team_codes(c, cand):
                    franchise_name = cand
                    break
        finally:
            c.close()

    if school_name:
        filters["school_name"] = school_name
        return "CFB", filters
    if franchise_name:
        filters["franchise_name"] = franchise_name
        return "NFL", filters
    return ("CFB" if filters.get("conference") else None), filters


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
#
# The "offense" alternative originally required "build an offense" as a
# rigid contiguous phrase -- real requests never actually talk that way
# ("build ME an offense", "build an SEC offense", "build an all-star
# offense"), so the task's own named example ("Build me an SEC offense.")
# silently failed to route at all. Given the same .{0,30} gap-tolerance
# idiom the "lineup" alternative already uses, for consistency rather than
# a second, differently-shaped fix.
_LINEUP_BUILDER_RE = re.compile(
    r"\b(build|construct)\w*\b.{0,30}\boffense\b|\blineup\s+builder\b|"
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

# --- GUESS_THE_SEASON (15-Format Expansion pass, Part 2) --------------------
# Only one real variant exists (NFL_SUPER_BOWL_SEASON -- see
# guess_the_season.py's own module docstring for why CFB isn't offered
# here) so, unlike every league-branching regex above, this never checks
# _league_for(text) -- there is nothing to branch to yet.
_GUESS_THE_SEASON_RE = re.compile(
    r"\bguess\s+the\s+(season|year)\b|"
    r"\bwhat\s+(season|year)\s+(was|is)\s+this\b|"
    r"\b(name|identify)\s+the\s+(season|year)\b",
    re.IGNORECASE,
)

# --- HEAD_TO_HEAD_DUEL (PAIRWISE_COMPARE, 15-Format Expansion pass, Part 2,
# format #3) ------------------------------------------------------------
# Same real "who had more <stat>" signal STAT_LADDER's own
# nl_mechanic_bridge.py regex established, reused here for a binary
# ("who had more" between exactly two named things) rather than a ranking
# -- "head to head"/"1v1"/"duel" are the distinctive phrase; a bare "who
# had more X" alone would collide with ordinary 2-option `guess` questions
# already served elsewhere, so a real duel/head-to-head signal is required.
_HEAD_TO_HEAD_DUEL_RE = re.compile(
    r"\bhead[\s-]to[\s-]head\b|\b1\s*v\s*1\b|\bone[\s-]on[\s-]one\s+duel\b|\bduel\b",
    re.IGNORECASE,
)
_CAREER_PASSING_TD_RE = re.compile(r"\b(career\s+)?passing\s+(touchdowns?|tds?)\b|\bquarterbacks?\b", re.IGNORECASE)

# --- BEST_OF_SEVEN_DUEL (PAIRWISE_COMPARE, 15-Format Expansion pass, Part 2,
# format #4) ------------------------------------------------------------
# Checked BEFORE _HEAD_TO_HEAD_DUEL_RE -- "best of seven duel" also
# contains the bare word "duel", which would otherwise match the plain
# HEAD_TO_HEAD_DUEL pattern first. Only one real variant exists
# (NFL_CAREER_QB_BEST_OF_SEVEN -- see head_to_head_duel.py's own module
# docstring for why this is NFL-QB-only for now), so this never branches
# on league/stat the way HEAD_TO_HEAD_DUEL's own routing does.
_BEST_OF_SEVEN_DUEL_RE = re.compile(r"\bbest\s+of\s+(seven|7)\b", re.IGNORECASE)

# --- PICK_THE_IMPOSTOR (15-Format Expansion pass, Part 2, format #5) -------
# "impostor"/"doesn't belong"/"which one wasn't" are the distinctive
# phrase -- a bare "which one is different" alone would be too generic
# (could mean almost anything), so this requires either the format's own
# name or a real "doesn't belong to this real group" framing.
_PICK_THE_IMPOSTOR_RE = re.compile(
    r"\bimpostor\b|\bimposter\b|\bdoesn'?t\s+belong\b|\bwhich\s+one\s+(wasn'?t|isn'?t|didn'?t)\b",
    re.IGNORECASE,
)

# --- UNIQUE_ONE_OUT (PICK_THE_IMPOSTOR, 15-Format Expansion pass, Part 2,
# format #6) ------------------------------------------------------------
# Checked BEFORE _PICK_THE_IMPOSTOR_RE -- shares its exact same taxonomy
# and round shape (see pick_the_impostor.py's own module docstring), but
# is its own distinctly-named format with its own real domain (NFL Draft
# class membership, not team/school roster membership), so it gets its
# own distinctive trigger phrase rather than falling into the more
# generic "which one wasn't" pattern above.
_UNIQUE_ONE_OUT_RE = re.compile(r"\bunique\s+one\s+out\b|\bodd\s+one\s+out\b", re.IGNORECASE)

# --- MISSING_PIECE (15-Format Expansion pass, Part 2, format #7) -----------
# "missing piece"/"who's missing"/"which one belongs" are the distinctive
# phrase -- the inverse framing of PICK_THE_IMPOSTOR (find the real
# completion, not the real misfit), so this needs its own trigger rather
# than sharing _PICK_THE_IMPOSTOR_RE's "which one wasn't" pattern.
_MISSING_PIECE_RE = re.compile(
    r"\bmissing\s+piece\b|\bwho'?s\s+missing\b|\bwhich\s+one\s+(belongs|also\s+belongs)\b",
    re.IGNORECASE,
)

# --- BEFORE_AFTER (15-Format Expansion pass, Part 2, format #8) -----------
# "before and after"/"before or after"/"which came first"/"played for
# first" are the distinctive phrase -- a bare "first" or "before" alone
# is far too generic (used constantly in unrelated phrasing), so this
# requires the format's own real "before/after" or "which came first"
# framing.
_BEFORE_AFTER_RE = re.compile(
    r"\bbefore\s+(and|or)\s+after\b|\bwhich\s+(one\s+)?(came|was)\s+first\b|"
    r"\bwhich\b.{0,50}\bfor\s+first\b",
    re.IGNORECASE,
)

# --- CAREER_PATH (15-Format Expansion pass, Part 2, format #10) -----------
# "career path" is the format's own real distinctive phrase -- never
# confused with MAP_THE_CAREER's own "map the career"/"order the teams
# played for" trigger (nl_mechanic_bridge.py, a different bridge checked
# earlier in the fixed pipeline order, and a structurally different
# phrase that never overlaps this one).
_CAREER_PATH_RE = re.compile(
    r"\bcareer\s+path\b|\bwhich\s+(real\s+)?player\s+had\s+this\s+path\b",
    re.IGNORECASE,
)

# --- RISK_IT (15-Format Expansion pass, Part 2, format #11) ---------------
# "risk it"/"risk tier"/"pick a risk" are the format's own real
# distinctive phrase -- "risk" alone would be too generic (used in
# unrelated football phrasing like "boom or bust"), so this requires a
# genuine risk-TIER framing.
_RISK_IT_RE = re.compile(r"\brisk\s+it\b|\brisk\s+tier\b|\bpick\s+a\s+risk\b", re.IGNORECASE)

# --- WAGER_MODE (15-Format Expansion pass, Part 2, format #12) -----------
# "wager" is the format's own real distinctive word -- no other bridge in
# this pipeline uses it, so a bare "wager" is safe (unlike "risk", which
# needed a tighter tier-specific phrase above).
_WAGER_MODE_RE = re.compile(r"\bwager\b", re.IGNORECASE)

# --- LEADERBOARD_CLIMB (15-Format Expansion pass, Part 2, format #14) -----
# "leaderboard climb"/"climb the leaderboard" are the format's own real
# distinctive phrase -- a bare "leaderboard" alone would be too generic
# (this app has real, unrelated mode-popularity leaderboards elsewhere).
_LEADERBOARD_CLIMB_RE = re.compile(r"\b(leaderboard\s+climb|climb\s+the\s+leaderboard)\b", re.IGNORECASE)


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
        league, filters = _extract_roster_filters(text)
        league = league or _league_for(text)
        variant = "CFB_AUCTION_DRAFT" if league == "CFB" else "NFL_AUCTION_DRAFT"
        return {"taxonomy_id": "ROSTER_BUILD", "variant": variant, "format": "AUCTION_DRAFT",
                "gen_kwargs": {"filters": filters} if filters else {}}

    if _CAP_CHALLENGE_RE.search(text):
        league, filters = _extract_roster_filters(text)
        league = league or _league_for(text)
        variant = "CFB_CAP_CHALLENGE" if league == "CFB" else "NFL_CAP_CHALLENGE"
        return {"taxonomy_id": "ROSTER_BUILD", "variant": variant, "format": "CAP_CHALLENGE",
                "gen_kwargs": {"filters": filters} if filters else {}}

    if _LINEUP_BUILDER_RE.search(text):
        league, filters = _extract_roster_filters(text)
        league = league or _league_for(text)
        variant = "CFB_SKILL_POSITION_BUILDER" if league == "CFB" else "NFL_2010S_OFFENSE_BUILDER"
        return {"taxonomy_id": "ROSTER_BUILD", "variant": variant, "format": "LINEUP_BUILDER",
                "gen_kwargs": {"filters": filters} if filters else {}}

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
        variant = "CFB_TOPIC_PATH" if _league_for(text) == "CFB" else "NFL_TOPIC_PATH"
        return {"taxonomy_id": "BRANCH_STATE", "variant": variant,
                "format": "CHOOSE_YOUR_PATH", "gen_kwargs": {}}

    if _GUESS_THE_SEASON_RE.search(text):
        return {"taxonomy_id": "GUESS_THE_SEASON", "variant": "NFL_SUPER_BOWL_SEASON",
                "format": "GUESS_THE_SEASON", "gen_kwargs": {}}

    if _BEST_OF_SEVEN_DUEL_RE.search(text):
        return {"taxonomy_id": "PAIRWISE_COMPARE", "variant": "NFL_CAREER_QB_BEST_OF_SEVEN",
                "format": "BEST_OF_SEVEN_DUEL", "gen_kwargs": {}}

    if _HEAD_TO_HEAD_DUEL_RE.search(text):
        league = _league_for(text)
        if league == "CFB":
            variant = "CFB_CAREER_RUSHING_YARDS_DUEL"
        elif _CAREER_PASSING_TD_RE.search(text):
            variant = "NFL_CAREER_PASSING_TD_DUEL"
        else:
            variant = "NFL_SEASON_RUSHING_YARDS_DUEL"
        return {"taxonomy_id": "PAIRWISE_COMPARE", "variant": variant,
                "format": "HEAD_TO_HEAD_DUEL", "gen_kwargs": {}}

    if _UNIQUE_ONE_OUT_RE.search(text):
        return {"taxonomy_id": "PICK_THE_IMPOSTOR", "variant": "NFL_DRAFT_CLASS_ONE_OUT",
                "format": "UNIQUE_ONE_OUT", "gen_kwargs": {}}

    if _PICK_THE_IMPOSTOR_RE.search(text):
        variant = "CFB_SCHOOL_ROSTER_IMPOSTOR" if _league_for(text) == "CFB" else "NFL_TEAM_ROSTER_IMPOSTOR"
        return {"taxonomy_id": "PICK_THE_IMPOSTOR", "variant": variant,
                "format": "PICK_THE_IMPOSTOR", "gen_kwargs": {}}

    if _MISSING_PIECE_RE.search(text):
        variant = "CFB_SCHOOL_ROSTER_MISSING_PIECE" if _league_for(text) == "CFB" else "NFL_TEAM_ROSTER_MISSING_PIECE"
        return {"taxonomy_id": "MISSING_PIECE", "variant": variant,
                "format": "MISSING_PIECE", "gen_kwargs": {}}

    if _BEFORE_AFTER_RE.search(text):
        variant = "CFB_SCHOOL_TRANSFER_BEFORE_AFTER" if _league_for(text) == "CFB" else "NFL_TEAM_CHANGE_BEFORE_AFTER"
        return {"taxonomy_id": "BEFORE_AFTER", "variant": variant,
                "format": "BEFORE_AFTER", "gen_kwargs": {}}

    if _CAREER_PATH_RE.search(text):
        variant = "CFB_PLAYER_CAREER_PATH_IDENTIFY" if _league_for(text) == "CFB" else "NFL_PLAYER_CAREER_PATH_IDENTIFY"
        return {"taxonomy_id": "CAREER_PATH", "variant": variant,
                "format": "CAREER_PATH", "gen_kwargs": {}}

    if _RISK_IT_RE.search(text):
        return {"taxonomy_id": "RISK_IT", "variant": "NFL_DRAFT_RISK_IT",
                "format": "RISK_IT", "gen_kwargs": {}}

    if _WAGER_MODE_RE.search(text):
        return {"taxonomy_id": "WAGER_MODE", "variant": "WAGER_MODE_MIXED",
                "format": "WAGER_MODE", "gen_kwargs": {}}

    if _LEADERBOARD_CLIMB_RE.search(text):
        return {"taxonomy_id": "LEADERBOARD_CLIMB", "variant": "NFL_CAREER_PASSING_YARDS_CLIMB",
                "format": "LEADERBOARD_CLIMB", "gen_kwargs": {}}

    return None
