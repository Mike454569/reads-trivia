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
    "NFL_DRAFT",
    "NFL_CHAMPIONSHIP",
    "NFL_PLAYER_IDENTITY",
    "NFL_OFFENSE_LINEUP",  # v1.8, Part F
    "CFB_HEISMAN",  # CFB data enrichment operation -- first CFB domain registered
    "NFL_GAME_RESULT",  # App-Wide Engine Migration operation
    "CFB_GAME_RESULT",  # App-Wide Engine Migration operation
    "NFL_GAME_BOXSCORE",  # Historical Engine Enrichment operation -- built on team_game_stats
    "NFL_OFFENSE_LINEUP_COLLEGE",  # position+college proof-game fix -- names-hidden variant, see registry.py
})

ALLOWED_PREDICATES = frozenset({
    "DRAFTED_BY",
    "TEAM_POSTSEASON_RESULT",
    "IDENTIFY_FROM_CLUES",
    "TEAM_OF_STARTING_LINEUP",  # v1.8, Part F
    "WON_HEISMAN",  # CFB data enrichment operation
    "WON_GAME",  # App-Wide Engine Migration operation -- shared by NFL_GAME_RESULT and CFB_GAME_RESULT
    "HAD_MORE_YARDS",  # Historical Engine Enrichment operation -- NFL_GAME_BOXSCORE
    "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",  # position+college proof-game fix
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
