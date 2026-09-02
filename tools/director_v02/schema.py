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
    "CFB_DUPLICATE_COLLEGE_HUNT",
    "CFB_FILL_THE_COLLEGES",
    "CFB_GAME_LEADER",
    "CFB_GAME_RESULT",
    "CFB_HEISMAN",
    "CFB_ODD_COLLEGE_OUT",
    "CFB_OFFENSE_LINEUP",
    "CFB_ONE_SCHOOL_MISSING",
    "CFB_PLAYER_IDENTITY",
    "CFB_PLAYER_SEASON",
    "CFB_POSITION_TRAP",
    "CFB_RANKING",
    "CFB_RIVALRY",
    "CFB_RIVALRY_TRIVIA",
    "CFB_SEASON_STATS",
    "CFB_SPOT_THE_FAKE_LINEUP",
    "CFB_STAT_COMPARISON",
    "CFB_THREE_CLUES_ONE_CHAMPION",
    "CFB_TRANSFER",
    "CFB_TRANSFER_PATH",
    "CFB_UPSET",
    "CFB_WHO_CHANGED",
    "CROSS_LEAGUE_HONORS",
    "NFL_ALL_PRO",
    "NFL_ALL_PRO_COLLEGE",
    "NFL_AWARDS",
    "NFL_CHAMPIONSHIP",
    "NFL_COACHING",
    "NFL_DEFENSIVE_COORDINATOR",
    "NFL_DEFENSIVE_EVENT",
    "NFL_DRAFT",
    "NFL_DRIVE",
    "NFL_GAME_BOXSCORE",
    "NFL_GAME_LEADER",
    "NFL_GAME_RESULT",
    "NFL_HALL_OF_FAME",
    "NFL_HOF_COLLEGE",
    "NFL_OFFENSE_COLLEGE_CURATED",
    "NFL_OFFENSE_LINEUP",
    "NFL_OFFENSE_LINEUP_COLLEGE",
    "NFL_OFFENSIVE_COORDINATOR",
    "NFL_PLAYER_IDENTITY",
    "NFL_PLAYER_SEASON",
    "NFL_PRO_BOWL",
    "NFL_PRO_BOWL_COLLEGE",
    "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
    "NFL_SCORING_PLAY",
    "NFL_SEASON_STATS",
    "NFL_SUPER_BOWL",
    # END GENERATED
})

ALLOWED_PREDICATES = frozenset({
    # BEGIN GENERATED -- see tools/director_v02/generate_schema_and_prompt.py
    "ALL_AMERICAN_TO_ALL_PRO",
    "ALL_AMERICAN_TO_PRO_BOWL",
    "ALTERED_POSITION",
    "ATTENDED_COLLEGE",
    "ATTENDED_COLLEGE_ALL_PRO",
    "ATTENDED_COLLEGE_HOF",
    "ATTENDED_COLLEGE_PRO_BOWL",
    "BETTING_UPSET",
    "CHANGED_POSITION",
    "COACHED_TEAM",
    "COLLEGE_OF_POSITION",
    "COORDINATED_DEFENSE",
    "COORDINATED_OFFENSE",
    "CORRECT_TRIVIA_ANSWER",
    "DRAFTED_BY",
    "DRIVE_RESULT",
    "FIRST_TOUCHDOWN_SCORER",
    "FORCED_FUMBLE",
    "HAD_FEWER_PENALTIES",
    "HAD_FEWER_TURNOVERS",
    "HAD_MORE_SACKS",
    "HAD_MORE_YARDS",
    "IDENTIFY_FROM_CLUES",
    "IMPOSTOR_COLLEGE",
    "INDUCTED_HOF",
    "LED_LEAGUE_IN_STAT",
    "MISSING_COLLEGE",
    "ORDERED_PATH_NFL_BRIDGED",
    "PASSING_COMPARISON",
    "PASSING_LEADER",
    "RANKED_HIGHER",
    "RANKED_IN_POLL",
    "RANKING_UPSET",
    "RECEIVING_COMPARISON",
    "RECEIVING_LEADER",
    "RECORDED_INTERCEPTION",
    "RECORDED_SACK",
    "RECOVERED_FUMBLE",
    "REPEATED_COLLEGE",
    "RIVAL_OF",
    "RUSHING_COMPARISON",
    "RUSHING_LEADER",
    "SCHOOL_OF_SEASON",
    "SELECTED_ALL_PRO",
    "SELECTED_PRO_BOWL",
    "SWAPPED_POSITION_PAIR",
    "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE",
    "TEAM_OF_SEASON",
    "TEAM_OF_STARTING_LINEUP",
    "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",
    "TEAM_POSTSEASON_RESULT",
    "TEAM_SEASON_FROM_THREE_CLUES",
    "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
    "TEAM_SEASON_OF_STARTING_OFFENSE",
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

# Filters/exclusions extension points. Kept as typed, structural fields (not
# a free-form dict/string) so a capability can declare support for a
# specific, named, allowlisted key without ever opening this up to
# arbitrary content. `rivalry_pack_number`/`rivalry_only` are the first real
# filter keys any capability supports (Rivalry Data + Gold Standard Content
# Integration operation) -- CFB_RIVALRY_TRIVIA uses them to scope generation
# to one specific rivalry pack (e.g. "Make me an Iron Bowl trivia game") or
# to rivalry-only rows generally ("give me a game about college football
# rivalries"). validator.py checks a spec's filter keys against BOTH this
# global allowlist AND the matched capability's own `supported_filter_keys`
# -- a key here but not on the capability is still rejected.
ALLOWED_FILTER_KEYS: frozenset[str] = frozenset({
    "rivalry_pack_number", "rivalry_only",
    # Franchise Marathon / Era Gauntlet (Gold Standard concepts #19/#51) --
    # both filters on NFL_SB_CHAMPION_OFFENSE_COLLEGE, see that capability's
    # own adapter (sb_champion_offense_college.py) for the real selection
    # logic each triggers.
    "franchise_name", "era_gauntlet",
    # "Theme Nights" / "O-Line Only" (Rivalry Pack + Gold Standard Game Ideas
    # Integration, workbook's own "6. More Puzzle Ideas" sheet) --
    # conference/division on NFL_OFFENSE_COLLEGE_CURATED only (real,
    # source-backed via season_standings; deliberately not offered on the
    # Super Bowl champion board -- see that adapter's own comment on why
    # today's division alignment would mislead for a pre-2002 champion).
    # oline_only is shared by both offense-by-college capabilities.
    "conference", "division", "oline_only",
    # Creator/Game Quality Correction pass: rank_min/rank_max scope
    # CFB_RANKING/RANKED_IN_POLL to an exact requested rank or rank range
    # (e.g. "which team was ranked No. 5" -> rank_min=5, rank_max=5; "a
    # Top-5 team" -> rank_min=1, rank_max=5) instead of pulling from the
    # full real Top 25 regardless of what was asked. biggest_only scopes
    # CFB_UPSET/RANKING_UPSET and BETTING_UPSET to the real upset-magnitude
    # threshold (see cfb_upset_ranking.py/cfb_upset_betting.py) instead of
    # every technically-qualifying upset.
    "rank_min", "rank_max", "biggest_only",
})
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
