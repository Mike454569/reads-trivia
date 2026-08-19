"""Director v0.2 -- the structured spec schema an LLM (or the deterministic
mock) is allowed to emit, and nothing more.

Design rule: the LLM-facing spec is deliberately SMALLER than v0.1's Game
Factory spec. It expresses only `mechanic + domain + relationship_predicate +
question_count + difficulty + filters + exclusions`. Fields v0.1 needed for
execution -- `entity_type`, `object_type`, `answer_type`, `group_size`,
`competition_id` -- are NOT translator-facing here. They are derived,
Engine-side, from the registered capability triple
(mechanic, domain, relationship_predicate) via `registry.py`. This shrinks
the LLM's attack surface: it cannot supply a value for a field it was never
given the option to name.

Every enumerated field has an explicit allowlist below. There is no
free-form execution field anywhere in this schema. `filters` and
`exclusions` exist as extension points for a future capability that
declares support for them (see registry.py) -- today no registered
capability supports either, so both must be empty for a spec to validate.
"""
from __future__ import annotations

# --- Allowlists -------------------------------------------------------
# These are the full universe of values the schema can express at all.
# A capability being "expressible" here does NOT mean it is "supported" --
# see registry.py for what's actually registered/executable. That split is
# what lets Step 6 (UNDERSTOOD_BUT_UNSUPPORTED) exist: the translator can
# validly express a real football concept (e.g. a predicate) that simply
# has no adapter yet.

ALLOWED_MECHANICS = frozenset({
    "guess",  # four-option, single-fact mechanic
    "identify_player_from_clues",  # progressive-clue-sequence mechanic, added Director v0.4 --
                                    # see PLAYER_FROM_CLUES_MECHANIC_SPEC.md. NOT a guess variant --
                                    # no options/correctIndex, answer is a resolved entity.
})

ALLOWED_DOMAINS = frozenset({
    # BEGIN GENERATED -- see tools/director_v02/generate_schema_and_prompt.py
    "CFB_CHAMPIONSHIP",
    "CFB_GAME_RESULT",
    "CFB_HEISMAN",
    "CFB_PLAYER_IDENTITY",
    "CFB_PLAYER_SEASON",
    "CFB_RIVALRY",
    "CFB_SEASON_STATS",
    "CFB_TRANSFER",
    "NFL_ALL_PRO",
    "NFL_AWARDS",
    "NFL_CHAMPIONSHIP",
    "NFL_COACHING",
    "NFL_DEFENSIVE_COORDINATOR",
    "NFL_DRAFT",
    "NFL_GAME_BOXSCORE",
    "NFL_GAME_RESULT",
    "NFL_HALL_OF_FAME",
    "NFL_OFFENSE_LINEUP",
    "NFL_OFFENSE_LINEUP_COLLEGE",
    "NFL_OFFENSIVE_COORDINATOR",
    "NFL_PLAYER_IDENTITY",
    "NFL_PLAYER_SEASON",
    "NFL_PRO_BOWL",
    "NFL_SEASON_STATS",
    "NFL_SUPER_BOWL",
    # END GENERATED
})

ALLOWED_PREDICATES = frozenset({
    # BEGIN GENERATED -- see tools/director_v02/generate_schema_and_prompt.py
    "ATTENDED_COLLEGE",
    "COACHED_TEAM",
    "COORDINATED_DEFENSE",
    "COORDINATED_OFFENSE",
    "DRAFTED_BY",
    "HAD_FEWER_PENALTIES",
    "HAD_FEWER_TURNOVERS",
    "HAD_MORE_SACKS",
    "HAD_MORE_YARDS",
    "IDENTIFY_FROM_CLUES",
    "INDUCTED_HOF",
    "LED_LEAGUE_IN_STAT",
    "RIVAL_OF",
    "SCHOOL_OF_SEASON",
    "SELECTED_ALL_PRO",
    "SELECTED_PRO_BOWL",
    "TEAM_OF_SEASON",
    "TEAM_OF_STARTING_LINEUP",
    "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",
    "TEAM_POSTSEASON_RESULT",
    "WON_AWARD",
    "WON_CHAMPIONSHIP",
    "WON_GAME",
    "WON_HEISMAN",
    # END GENERATED
})

ALLOWED_DIFFICULTIES = frozenset({
    "any", "easy", "medium", "hard",
})

QUESTION_COUNT_MIN = 1
QUESTION_COUNT_MAX = 100  # matches the export size every prior approved pilot used

# The exact key set a valid DirectorSpec dict must have -- no more, no less.
# Extra keys (e.g. an injected "sql", "table", "path", "eval") are a hard
# schema-validation failure, not silently ignored.
REQUIRED_SPEC_KEYS = frozenset({
    "mechanic", "domain", "relationship_predicate", "question_count", "difficulty",
})
OPTIONAL_SPEC_KEYS = frozenset({
    "filters", "exclusions",
})
ALL_SPEC_KEYS = REQUIRED_SPEC_KEYS | OPTIONAL_SPEC_KEYS

# Filters/exclusions extension points. Empty today -- no registered
# capability supports any filter key or any exclusion. Kept as typed,
# structural fields (not a free-form dict/string) so a future capability can
# declare support for a specific, named, allowlisted key without ever
# opening this up to arbitrary content.
ALLOWED_FILTER_KEYS: frozenset[str] = frozenset()  # none supported yet
EXCLUSIONS_SUPPORTED = False  # no adapter supports exclusion lists yet


def default_spec_shape() -> dict:
    """The minimal valid shape a translator can emit for the one registered
    capability, useful for tests and as documentation of the expected shape."""
    return {
        "mechanic": "guess",
        "domain": "NFL_DRAFT",
        "relationship_predicate": "DRAFTED_BY",
        "question_count": 25,
        "difficulty": "any",
        "filters": {},
        "exclusions": [],
    }
