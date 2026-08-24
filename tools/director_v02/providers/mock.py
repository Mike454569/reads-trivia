"""Deterministic, keyword-based stand-in translator. NOT an LLM.

This exists so the v0.2/v0.3 pipeline (translate -> validate -> feasibility
-> generate -> QA -> package) is testable end-to-end without a network call
or an API credential, and so its behavior is exactly reproducible run to
run. Do not mistake this for NLU: it is a wider, hand-written keyword net
than v0.1's regex parser (enough to normalize the paraphrases in the test
sets across v0.2/v0.3), not semantic comprehension. It will not generalize
to phrasings outside the patterns below -- a real LLM provider (see
`providers/anthropic_provider.py`) is what actually generalizes.

Security property worth stating plainly: this translator NEVER copies any
substring of the input text into an output field. Every field it emits is a
literal chosen from a fixed, hardcoded Python set/dict based on whether a
keyword was *present*, never based on what surrounding text says. There is
no code path here through which attacker-supplied text could become a
`relationship_predicate`, `domain`, or any other spec value -- the emitted
values are always one of the literals already hardcoded below, full stop.

Decision order (see `translate()`): mixed-unsupported check first (most
specific), then the registered capability patterns (Player From Clues,
Draft, Super Bowl History, Season Awards, Championship, both Lineup
variants, Heisman, Box Score, Game Result, Attended College), then a
generic NEEDS_CLARIFICATION fallback for requests that clearly mention
football/NFL content but not enough to resolve to any of the above, then
NO_MATCH for everything else. Super Bowl History is checked BEFORE the
older Championship pattern specifically because both can match a "Super
Bowl" mention -- see the WON_CHAMPIONSHIP block's own comment for why order
matters there.

v1.8, Part F/B: the Starting Lineup pattern below deliberately also matches
requests that ask for "colleges" WITHOUT an explicit names-hidden signal --
matching the college phrasing to the real, name-based TEAM_OF_STARTING_
LINEUP capability is an honest best-effort match on INTENT (a real
position-by-position starting offense puzzle), not a claim that colleges are
actually used -- the generated package's own title/instructions/notes always
say plainly that this is a names-based puzzle, never colleges, regardless of
how the request was phrased. This mirrors an ordinary search engine matching
a query to the closest real result rather than fabricating one that doesn't
exist.

POSITION + COLLEGE PROOF-GAME FIX: a request that ALSO explicitly asks to
hide/anonymize names is a genuinely different, now-real capability
(NFL_OFFENSE_LINEUP_COLLEGE / TEAM_OF_STARTING_LINEUP_BY_COLLEGE) --
following a real identity-bridge expansion (tools/data_refresh/
nfl_college_identity_bridge.py), the ORIGINAL v1.8 proof-game request ("guess
the team from the colleges of the players on its offense, by position, names
hidden") is now genuinely data-backed for 5 skill positions (68 real
certified team-seasons) and is matched to its own real capability below,
never silently substituted with the names-based one.

STALE-COLLEGE-FEASIBILITY FIX: a general "guess a player's college" (not a
team's lineup) request, and a "guess the player from his college" (reverse
direction) request, are two MORE distinct real capabilities -- neither is a
team/lineup request at all. `_GUESS_COLLEGE_PHRASE_RE` / `_GUESS_PLAYER_
PHRASE_RE` use a directional phrase match (not just keyword presence) to
tell "guess the college/school ..." (-> ATTENDED_COLLEGE, ANSWER=college)
apart from "guess the ... player ..." (-> IDENTIFY_FROM_CLUES, which already
supports "college" and "draft_round" as clue types -- ANSWER=player
identity). Both route to real, registered, data-backed capabilities as of
the stale-college-feasibility fix (draft_facts.college backfill, 12,914 of
12,927 real draft rows) -- see tools/quiz_export/adapters/draft_college.py
and tools/director_v02/feasibility.py's own module docstring for the full
audit trail on why the OLD behavior (falling through to a hardcoded,
now-stale "college data is basically unusable" MISSING_DATA reason citing a
DIFFERENT table's 2,542-row count) was wrong.
"""
from __future__ import annotations

import re

from .base import Translator

TRANSLATOR_ID = "mock-deterministic-v1"

_PLAYER_WORDS = {"player", "players"}
_DRAFT_WORDS = {"draft", "drafted", "pick", "picked", "picks"}
_TEAM_WORDS = {"team", "teams", "franchise", "franchises", "club"}
_CLUE_WORDS = {"clue", "clues", "identify"}
_POSTSEASON_WORDS = {"playoff", "playoffs", "postseason", "championship"}
_OFFENSE_WORDS = {"offense", "offensive"}
_LINEUP_WORDS = {"lineup", "lineups", "starters", "starting"}
_POSITION_WORDS = {"position", "positions"}
_COLLEGE_WORDS = {"college", "colleges"}
_HIDDEN_NAMES_WORDS = {"hidden", "hide", "anonymous"}
_HEISMAN_WORDS = {"heisman"}
_WIN_WORDS = {"won", "win", "wins", "winner"}
_AWARD_WORDS = {"award", "awards", "trophy", "mvp"}
_CFB_EXPLICIT_WORDS = {"cfb"}
_GAME_WORDS = {"game", "games"}
_RESULT_WORDS = {"result", "results", "won", "win", "winner", "winners", "score", "scored"}
_BOXSCORE_WORDS = {"boxscore", "yards", "yardage"}  # "box" + "score" (two tokens) checked separately below
_OFFTOPIC_WORDS = {"food", "foods", "favorite"}
_MIXED_SIGNAL_WORDS = {"both"}
_HARD_WORDS = {"hard", "difficult", "tough", "challenging"}
_EASY_WORDS = {"easy", "simple", "beginner"}
_MEDIUM_WORDS = {"medium", "moderate", "intermediate"}

_COUNT_RE = re.compile(r"\b(\d{1,3})\b")
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

# Rivalry Data + Gold Standard Content Integration operation: real, curated
# rivalry-pack recognition for CFB_RIVALRY_TRIVIA (a DIFFERENT, richer
# capability from CFB_RIVALRY/RIVAL_OF below -- see registry.py's own
# comment on that capability triple for why). Nicknames distinctive enough
# to match on their own (never a generic word like "game"/"bowl" alone);
# "The Game" (#3) and "Battle for the Victory Bell" (shared by #22 and #27)
# are deliberately excluded from nickname-only matching -- resolved via the
# school-pair table below instead, never guessed.
_RIVALRY_NICKNAME_TO_PACK = {
    "iron bowl": 1, "red river rivalry": 2, "red river showdown": 2,
    "egg bowl": 5, "lone star showdown": 6, "palmetto bowl": 7,
    "third saturday in october": 8, "battle for the beer barrel": 9,
    "border war": 11, "governor's cup": 12, "governors cup": 12,
    "southwest classic": 13, "paul bunyan trophy": 14,
    "paul bunyan's axe": 15, "paul bunyans axe": 15,
    "old oaken bucket": 17, "cy-hawk trophy": 19, "cy hawk trophy": 19,
    "civil war": 20, "apple cup": 23, "territorial cup": 24, "revivalry": 25,
    "holy war": 26, "bayou bucket classic": 29, "sunflower showdown": 30,
    "bedlam": 31, "war on i-4": 33, "war on i4": 33, "backyard brawl": 34,
    "the big game": 35, "clean, old-fashioned hate": 37,
    "clean old-fashioned hate": 37, "clean old fashioned hate": 37,
    "commonwealth cup": 40,
}
# Real, hand-verified school-pair index -- direct mirror of the 43-pack
# table used to import cfb_rivalry_pack_index (see the import script). A
# None school means the source workbook itself left that side ambiguous
# (pack #13, "Texas/Texas A&M") -- never guessed here either.
_RIVALRY_PACK_SCHOOLS = {
    1: ("alabama", "auburn"), 2: ("oklahoma", "texas"), 3: ("michigan", "ohio state"),
    4: ("florida", "georgia"), 5: ("ole miss", "mississippi state"), 6: ("texas", "texas a&m"),
    7: ("clemson", "south carolina"), 8: ("alabama", "tennessee"), 9: ("tennessee", "vanderbilt"),
    10: ("lsu", "alabama"), 11: ("missouri", "kansas"), 12: ("kentucky", "louisville"),
    13: ("arkansas", None), 14: ("michigan", "michigan state"), 15: ("minnesota", "wisconsin"),
    16: ("nebraska", "oklahoma"), 17: ("indiana", "purdue"), 18: ("illinois", "northwestern"),
    19: ("iowa", "iowa state"), 20: ("oregon", "oregon state"), 21: ("penn state", "pitt"),
    22: ("ucla", "usc"), 23: ("washington", "washington state"), 24: ("arizona", "arizona state"),
    25: ("baylor", "tcu"), 26: ("byu", "utah"), 27: ("cincinnati", "miami oh"),
    28: ("colorado", "nebraska"), 29: ("houston", "rice"), 30: ("kansas", "kansas state"),
    31: ("oklahoma", "oklahoma state"), 32: ("texas a&m", "texas tech"), 33: ("ucf", "usf"),
    34: ("pitt", "west virginia"), 35: ("california", "stanford"), 36: ("florida state", "miami"),
    37: ("georgia", "georgia tech"), 38: ("north carolina", "nc state"), 39: ("smu", "tcu"),
    40: ("virginia", "virginia tech"), 41: ("boston college", "syracuse"), 42: ("maryland", "rutgers"),
    43: ("duke", "wake forest"),
}


# Gold Standard "10. New Game Modes" concept-name recognition -- these are
# the workbook's own named concepts, distinctive enough to match on the
# phrase alone (mirroring "heisman"'s own unambiguous-alone precedent).
_GOLD_STANDARD_CONCEPT_PATTERNS = [
    (re.compile(r"college offense"), ("NFL_SB_CHAMPION_OFFENSE_COLLEGE", "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE")),
    (re.compile(r"fill the colleges?"), ("CFB_FILL_THE_COLLEGES", "COLLEGE_OF_POSITION")),
    (re.compile(r"odd college out"), ("CFB_ODD_COLLEGE_OUT", "IMPOSTOR_COLLEGE")),
    (re.compile(r"spot the fake"), ("CFB_SPOT_THE_FAKE_LINEUP", "ALTERED_POSITION")),
    (re.compile(r"who changed"), ("CFB_WHO_CHANGED", "CHANGED_POSITION")),
    (re.compile(r"three clues,?\s*one champion"), ("CFB_THREE_CLUES_ONE_CHAMPION", "TEAM_SEASON_FROM_THREE_CLUES")),
    (re.compile(r"position trap"), ("CFB_POSITION_TRAP", "SWAPPED_POSITION_PAIR")),
    (re.compile(r"duplicate (college )?hunt"), ("CFB_DUPLICATE_COLLEGE_HUNT", "REPEATED_COLLEGE")),
    (re.compile(r"one school missing"), ("CFB_ONE_SCHOOL_MISSING", "MISSING_COLLEGE")),
]


def _match_rivalry_pack(text_lower: str) -> int | None:
    """Returns a real rivalry_pack_number (1-43) if the request names a
    specific rivalry (by nickname or by naming both schools), else None.
    Never returns a fabricated/guessed pack -- a request naming only one
    side of an ambiguous pack (e.g. just "Arkansas", pack #13's unresolved
    second school) does not match here."""
    for nickname, pack_num in _RIVALRY_NICKNAME_TO_PACK.items():
        if nickname in text_lower:
            return pack_num
    for pack_num, (school_a, school_b) in _RIVALRY_PACK_SCHOOLS.items():
        if school_a and school_b and school_a in text_lower and school_b in text_lower:
            return pack_num
    return None

# Directional phrase matches (not just keyword presence) -- distinguishes
# "guess the college of a player" (answer=college) from "guess the player
# from his college" (answer=player identity). See the module docstring's
# STALE-COLLEGE-FEASIBILITY FIX section.
_GUESS_COLLEGE_PHRASE_RE = re.compile(r"guess\s+(the\s+)?(college|school)\b")
_GUESS_PLAYER_PHRASE_RE = re.compile(r"guess\s+(the\s+)?(nfl\s+)?player\b")
_SCHOOL_WORDS = {"school", "schools"}
_PLAYER_OF_THE_YEAR_RE = re.compile(r"player of the year")
_ROOKIE_OF_THE_YEAR_RE = re.compile(r"rookie of the year")

# Creator-gap-audit operation: keyword sets for the 9 new capabilities
# registered against real, previously-unused Engine tables (team_game_stats'
# sacks/turnovers/penalties columns, cfb_champion_school_links,
# player_season_stats/cfb_player_season_stats_real, coach_team_seasons,
# cfb_transfer_summary_v17, cfb_rivalries).
_SACKS_WORDS = {"sack", "sacks"}
_TURNOVER_WORDS = {"turnover", "turnovers"}
_PENALTY_WORDS = {"penalty", "penalties", "penalized"}
_NATIONAL_CHAMPIONSHIP_RE = re.compile(r"national championship|national champion")
_LEADER_WORDS = {"leader", "leaders", "led", "leading"}
_COACH_WORDS = {"coach", "coached", "coaching"}
_TRANSFER_WORDS = {"transfer", "transferred", "transfers"}
_RIVALRY_WORDS = {"rival", "rivals", "rivalry", "rivalries"}

# Reliability-design Phase 3: NFL Player + Season -> Team, the first
# conservative-compiler vertical slice. "season" alone (with player + team,
# and no draft/postseason/lineup/coaching/boxscore signal) is the real,
# distinguishing marker: "which team did [player] play for in [season]" is
# a genuinely different question from "which team drafted [player]"
# (DRAFTED_BY, needs a draft word) or "how did [team]'s season end"
# (TEAM_POSTSEASON_RESULT, needs a postseason word).
_SEASON_WORDS = {"season"}

# ============================== Creator Semantic Routing + Who Am I pass ==============================
# Fixes the central defect this pass exists for: high-specificity football
# concepts (All-Pro, Pro Bowl, Hall of Fame, coordinators, ...) being
# "stolen" by generic structural triggers (player+season+team, team+
# offense/lineup, game+result) that were checked first and matched on
# incidental keyword overlap. Every block below is checked BEFORE the
# generic patterns it used to lose to (player+season+team at line ~371,
# team+lineup at line ~581, game+result at line ~691) -- see each block's
# own comment for exactly which older pattern it now outranks and why.
#
# Two kinds of fix live in this section:
#   (1) REAL new capabilities (All-Pro/Pro Bowl/Hall of Fame/OC/DC) --
#       route to a genuinely registered, GENERATION_VERIFIED capability
#       (tools/quiz_export/adapters/nfl_all_pro.py and siblings).
#   (2) RECOGNIZED BUT NOT YET BUILT concepts (rankings, upsets, PBP
#       scoring plays, player-level defensive events, drives, CFB same-week
#       stat comparison, top single-game performer, transfer+ordered-path,
#       cross-league honors composition) -- this pass's real, scoped
#       priority was the 5 capabilities in (1); these report
#       UNDERSTOOD_UNSUPPORTED_MECHANIC honestly (never silently answering
#       a different question) rather than falling into whichever older,
#       unrelated pattern happened to share a keyword. This is itself the
#       fix for the "specific intent beats generic intent" defect even
#       without a new adapter behind it -- a wrong SUPPORTED game is worse
#       than an honest "not yet."

_ALL_PRO_RE = re.compile(r"all[\s-]?pro")
_FIRST_TEAM_RE = re.compile(r"first[\s-]?team")
_SECOND_TEAM_RE = re.compile(r"second[\s-]?team")
_PRO_BOWL_RE = re.compile(r"pro[\s-]?bowl(?:er)?")
_HOF_PHRASE_RE = re.compile(r"hall of fame|hall of famer")
_HOF_WORDS = {"hof", "canton", "inducted", "induction"}
_OC_PHRASE_RE = re.compile(r"offensive coordinator")
_DC_PHRASE_RE = re.compile(r"defensive coordinator")
_COORDINATOR_WORDS = {"oc", "dc", "coordinator", "coordinators", "coordinated"}
_OFFENSE_SIDE_WORDS = {"offense", "offensive", "oc"}
_DEFENSE_SIDE_WORDS = {"defense", "defensive", "dc"}

_RANKING_WORDS = {"ranking", "rankings", "ranked", "poll", "polls", "unranked"}
_RANKING_PHRASE_RE = re.compile(r"top\s?25|ap poll|cfp ranking|coaches poll|moved up|dropped in the rankings")
_UPSET_WORDS = {"upset", "upsets", "shocked", "underdog", "underdogs"}
_UPSET_PHRASE_RE = re.compile(r"knocked off|unranked beat|beat.{0,20}ranked")

_TOUCHDOWN_WORDS = {"touchdown", "touchdowns"}
_SCORED_FIRST_RE = re.compile(r"scored the first|first (touchdown|score)|touchdown scorer|who scored")
_DEFENSIVE_EVENT_WORDS = {"sack", "sacks", "interception", "interceptions", "fumble", "fumbles"}
_WHO_PHRASE_RE = re.compile(r"\bwho (recorded|made|had|got|scored|picked)\b")
_DRIVE_WORDS = {"drive", "drives"}

_TOP_PERFORMER_RE = re.compile(r"top (offensive )?performer|leading performer|best performer")
# Universal Data Reuse pass: real bug found via the exact retest prompt
# "two RBs from the same CFB week" -- the literal two-word "same week"/
# "same game" phrase never matched when a league qualifier sat between
# "same" and "week"/"game" ("same CFB week", "same NFL week"), a very
# natural way to phrase this. Optional league-word group closes that gap
# without loosening the match to false-positive on unrelated "same ... week"
# phrasing (still requires "week"/"game" immediately after the optional
# qualifier).
_SAME_WEEK_RE = re.compile(r"same (?:cfb|nfl|college)?\s*week|same (?:cfb|nfl)?\s*game")
_STAT_COMPARE_RE = re.compile(
    r"who (had|rushed|threw|gained) more|more \w+ yards\b|more yards|had more|threw more|"
    r"higher\b|lower\b|bigger game|who had the (bigger|better)"
)

_ORDERED_PATH_RE = re.compile(r"college path|ordered path|order (his|their|the) schools?|path to the nfl")
_LATER_NFL_RE = re.compile(r"later (made|became|went to|reached) the nfl|later made the nfl")

_ALL_AMERICAN_RE = re.compile(r"all[\s-]?american")
_GREAT_IN_COLLEGE_RE = re.compile(r"great in college|college star")
_NFL_STAR_RE = re.compile(r"nfl star|star(red)? in the nfl|became (a )?star")

# ============================== Creator Capability Completion pass ==============================
# Finer-grained sub-category signals for the concepts that graduated from
# "recognized but unsupported" to real, registered capabilities this pass.
_BETTING_UPSET_WORDS = {"betting", "bet", "spread", "odds", "moneyline", "underdog", "underdogs"}
_BETTING_UPSET_PHRASE_RE = re.compile(r"beat the spread|against the spread|outright")
_SACK_PHRASE_RE = re.compile(r"\bsack(ed|s)?\b")
_INTERCEPTION_PHRASE_RE = re.compile(r"\binterception(s)?\b|\bintercepted\b|picked off")
_FORCED_FUMBLE_PHRASE_RE = re.compile(r"forced (the |a )?fumble|force a fumble|who forced")
_FUMBLE_RECOVERY_PHRASE_RE = re.compile(r"recovered (the |a )?fumble|fumble recovery|who recovered")
_RUSHING_CATEGORY_WORDS = {"rushing", "rush", "rusher", "running", "rb", "rbs"}
_PASSING_CATEGORY_WORDS = {"passing", "passer", "quarterback", "qb", "qbs", "threw", "throwing"}
_RECEIVING_CATEGORY_WORDS = {"receiving", "reception", "receptions", "receiver", "wr", "wrs", "caught", "catching"}


def _has_honor_level(text: str) -> str | None:
    if _FIRST_TEAM_RE.search(text):
        return "FIRST_TEAM"
    if _SECOND_TEAM_RE.search(text):
        return "SECOND_TEAM"
    return None


def _words(text: str) -> set[str]:
    # No apostrophe in the character class -- "team's" tokenizes to "team"
    # + "s", which is what lets a possessive phrasing still match the plain
    # keyword "team". This is a tokenizer detail, not semantic understanding.
    return set(re.findall(r"[a-z]+", text.lower()))


def _has_super_bowl_phrase(text: str) -> bool:
    return "super bowl" in text.lower()


def _has_who_am_i_phrase(text: str) -> bool:
    return "who am i" in text.lower()


def _difficulty_from_words(words: set[str]) -> str:
    if words & _HARD_WORDS:
        return "hard"
    if words & _EASY_WORDS:
        return "easy"
    if words & _MEDIUM_WORDS:
        return "medium"
    return "any"


def _question_count_from_text(text: str, default: int = 25) -> int:
    m = _COUNT_RE.search(text)
    return int(m.group(1)) if m else default


def _clamp_question_count_to_capability_bounds(spec: dict) -> dict:
    """Real defect found during the Creator audit: this translator's own
    default question_count (25, used whenever the request text names no
    explicit number -- see _question_count_from_text) can exceed a real
    registered capability's own max_question_count (confirmed live: NFL_
    SUPER_BOWL/WON_CHAMPIONSHIP's real max is 24, the exact size of its
    resolved candidate pool). The practical effect: the single most natural
    phrasing of a fully real, working request ("who won a Super Bowl?", no
    number mentioned) failed validator.py's bounds check and reported
    UNKNOWN -- a real capability, unreachable by its own default. Clamping
    here, in the one function every TRANSLATED spec already passes through,
    fixes this for every current and future capability at once rather than
    hand-patching each mechanic's own branch above; a spec whose predicate
    isn't (yet) a registered capability is left untouched -- validator.py's
    own registry.lookup() is still the real, single source of truth for
    whether it exists at all."""
    if spec is None:
        return spec
    from .. import registry
    cap = registry.lookup(spec.get("mechanic"), spec.get("domain"), spec.get("relationship_predicate"))
    if cap is None:
        return spec
    count = spec.get("question_count")
    if isinstance(count, int) and not isinstance(count, bool):
        spec["question_count"] = max(cap["min_question_count"], min(count, cap["max_question_count"]))
    return spec


def _result(request_text: str, status: str, spec: dict | None, notes: str, **extra) -> dict:
    if status == "TRANSLATED":
        spec = _clamp_question_count_to_capability_bounds(spec)
    out = {
        "raw_request_text": request_text,
        "translator_id": TRANSLATOR_ID,
        "translation_status": status,
        "spec": spec,
        "translator_notes": notes,
    }
    out.update(extra)
    return out


class MockDeterministicTranslator(Translator):
    translator_id = TRANSLATOR_ID

    def translate(self, request_text: str) -> dict:
        text = self._truncate(request_text)
        words = _words(text)

        has_player = bool(words & _PLAYER_WORDS)
        has_draft = bool(words & _DRAFT_WORDS)
        has_team = bool(words & _TEAM_WORDS)
        has_clue = bool(words & _CLUE_WORDS)
        has_postseason = bool(words & _POSTSEASON_WORDS) or _has_super_bowl_phrase(text)
        has_offense = bool(words & _OFFENSE_WORDS)
        has_lineup = bool(words & _LINEUP_WORDS)
        has_position = bool(words & _POSITION_WORDS)
        has_college = bool(words & _COLLEGE_WORDS)
        has_college_or_school = has_college or bool(words & _SCHOOL_WORDS)
        has_guess_college_phrase = bool(_GUESS_COLLEGE_PHRASE_RE.search(text.lower()))
        has_guess_player_phrase = bool(_GUESS_PLAYER_PHRASE_RE.search(text.lower()))
        has_hidden_names = bool(words & _HIDDEN_NAMES_WORDS) or "no names" in text.lower() or "without names" in text.lower() or "names hidden" in text.lower()
        has_heisman = bool(words & _HEISMAN_WORDS)
        has_win_word = bool(words & _WIN_WORDS)
        has_award_word = bool(words & _AWARD_WORDS)
        has_player_of_year_phrase = bool(_PLAYER_OF_THE_YEAR_RE.search(text.lower()))
        has_rookie_of_year_phrase = bool(_ROOKIE_OF_THE_YEAR_RE.search(text.lower()))
        has_sacks_word = bool(words & _SACKS_WORDS)
        has_turnover_word = bool(words & _TURNOVER_WORDS)
        has_penalty_word = bool(words & _PENALTY_WORDS)
        has_national_championship_phrase = bool(_NATIONAL_CHAMPIONSHIP_RE.search(text.lower()))
        has_leader_word = bool(words & _LEADER_WORDS)
        has_coach_word = bool(words & _COACH_WORDS)
        has_transfer_word = bool(words & _TRANSFER_WORDS)
        has_rivalry_word = bool(words & _RIVALRY_WORDS)
        has_season_word = bool(words & _SEASON_WORDS)
        has_offtopic = bool(words & _OFFTOPIC_WORDS)
        has_mixed_signal = bool(words & _MIXED_SIGNAL_WORDS)
        has_who_am_i = _has_who_am_i_phrase(text)
        has_nfl = "nfl" in words
        has_cfb_signal = bool(words & _CFB_EXPLICIT_WORDS) or has_college or "college football" in text.lower()
        has_game_word = bool(words & _GAME_WORDS)
        has_result_word = bool(words & _RESULT_WORDS)
        has_boxscore_word = bool(words & _BOXSCORE_WORDS) or ("box" in words and "score" in words)

        # Creator Semantic Routing pass: new signals, computed once here,
        # used by the high-specificity blocks checked immediately below
        # (before the mixed-signal/clue/draft/season/lineup/game patterns
        # that used to shadow them).
        text_lower = text.lower()
        # "who made first team AP that year" / "who got first-team honors
        # that season" (Section 25's own real paraphrase examples) never
        # say the words "All-Pro" -- "AP" (Associated Press, the body that
        # names the AP All-Pro team this capability is scoped to) or
        # "honors"/"honor" co-occurring with an explicit First-Team/Second-
        # Team phrase is specific enough, in this football-trivia-only
        # translator, to mean the same real concept.
        has_all_pro_phrase = bool(_ALL_PRO_RE.search(text_lower)) or (
            bool(_has_honor_level(text_lower)) and (("ap" in words) or bool(words & {"honors", "honor"}))
        )
        has_pro_bowl_phrase = bool(_PRO_BOWL_RE.search(text_lower))
        has_hof_signal = bool(_HOF_PHRASE_RE.search(text_lower)) or bool(words & _HOF_WORDS)
        has_oc_phrase = bool(_OC_PHRASE_RE.search(text_lower))
        has_dc_phrase = bool(_DC_PHRASE_RE.search(text_lower))
        has_coordinator_word = bool(words & _COORDINATOR_WORDS)
        has_ranking_signal = bool(words & _RANKING_WORDS) or bool(_RANKING_PHRASE_RE.search(text_lower))
        has_upset_signal = bool(words & _UPSET_WORDS) or bool(_UPSET_PHRASE_RE.search(text_lower))
        has_scored_first_phrase = bool(_SCORED_FIRST_RE.search(text_lower))
        has_touchdown_word = bool(words & _TOUCHDOWN_WORDS)
        has_defensive_event_word = bool(words & _DEFENSIVE_EVENT_WORDS)
        # A bare "fumble" mention never collides with a real team-boxscore
        # capability (there is no HAD_MORE_FUMBLES the way HAD_MORE_SACKS
        # exists for "sack"+"game") -- so it's always safe to consider,
        # unlike sack/interception phrasing which must stay gated behind
        # has_who_made_phrase/no-game-word to protect HAD_MORE_SACKS' own
        # "game"+"sacks" routing below from being shadowed.
        has_fumble_word = bool(words & {"fumble", "fumbles"})
        has_who_made_phrase = bool(_WHO_PHRASE_RE.search(text_lower))
        has_drive_word = bool(words & _DRIVE_WORDS)
        has_top_performer_phrase = bool(_TOP_PERFORMER_RE.search(text_lower))
        has_same_week_phrase = bool(_SAME_WEEK_RE.search(text_lower))
        has_stat_compare_phrase = bool(_STAT_COMPARE_RE.search(text_lower))
        has_ordered_path_phrase = bool(_ORDERED_PATH_RE.search(text_lower))
        has_later_nfl_phrase = bool(_LATER_NFL_RE.search(text_lower))
        has_all_american_phrase = bool(_ALL_AMERICAN_RE.search(text_lower))
        has_great_in_college_phrase = bool(_GREAT_IN_COLLEGE_RE.search(text_lower))
        has_nfl_star_phrase = bool(_NFL_STAR_RE.search(text_lower))
        has_betting_upset_signal = bool(words & _BETTING_UPSET_WORDS) or bool(_BETTING_UPSET_PHRASE_RE.search(text_lower))
        has_sack_phrase = bool(_SACK_PHRASE_RE.search(text_lower))
        has_interception_phrase = bool(_INTERCEPTION_PHRASE_RE.search(text_lower))
        has_forced_fumble_phrase = bool(_FORCED_FUMBLE_PHRASE_RE.search(text_lower))
        has_fumble_recovery_phrase = bool(_FUMBLE_RECOVERY_PHRASE_RE.search(text_lower))
        has_rushing_category = bool(words & _RUSHING_CATEGORY_WORDS)
        has_passing_category = bool(words & _PASSING_CATEGORY_WORDS)
        has_receiving_category = bool(words & _RECEIVING_CATEGORY_WORDS)

        # --- All-Pro (real capabilities: NFL_ALL_PRO/SELECTED_ALL_PRO,
        # NFL_ALL_PRO_COLLEGE/ATTENDED_COLLEGE_ALL_PRO, CROSS_LEAGUE_HONORS/
        # ALL_AMERICAN_TO_ALL_PRO) -- Section 4/26: must outrank the generic
        # player+season+team pattern below. Checked here, first, so it
        # always wins that collision.
        # Creator Capability Completion pass: the college-composition and
        # cross-league-composition branches now route to real, registered
        # capabilities instead of the honest-but-unsupported report this
        # block used to return -- see nfl_all_pro_college.py and
        # cfb_all_american_to_all_pro.py's own module docstrings.
        if has_all_pro_phrase:
            if has_all_american_phrase or has_later_nfl_phrase:
                spec = {
                    "mechanic": "guess", "domain": "CROSS_LEAGUE_HONORS", "relationship_predicate": "ALL_AMERICAN_TO_ALL_PRO",
                    "question_count": _question_count_from_text(text), "difficulty": "any",
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched All-Pro + All-American/cross-league-composition signal -> "
                    "ALL_AMERICAN_TO_ALL_PRO (real, disclosed double-name-joined bridge; small real pool), "
                    "never silently downgraded to the plain single-honor capability.",
                )
            if has_college_or_school and not has_lineup:
                spec = {
                    "mechanic": "guess", "domain": "NFL_ALL_PRO_COLLEGE", "relationship_predicate": "ATTENDED_COLLEGE_ALL_PRO",
                    "question_count": _question_count_from_text(text), "difficulty": "any",
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched All-Pro + college composition -> ATTENDED_COLLEGE_ALL_PRO (real, "
                    "player_id-joined composition), never stripping the All-Pro qualifier and never "
                    "silently downgraded to generic college-attendance trivia.",
                )
            spec = {
                "mechanic": "guess", "domain": "NFL_ALL_PRO", "relationship_predicate": "SELECTED_ALL_PRO",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            honor = _has_honor_level(text_lower)
            note = (
                "Matched 'All-Pro' phrase" + (f" with an explicit {honor} signal" if honor else "") +
                " -> SELECTED_ALL_PRO guess capability (which real player was named All-Pro), outranking "
                "the generic player+season+team pattern this request would otherwise also match."
            )
            return _result(request_text, "TRANSLATED", spec, note)

        # --- Pro Bowl (real capabilities: NFL_PRO_BOWL/SELECTED_PRO_BOWL,
        # NFL_PRO_BOWL_COLLEGE, CROSS_LEAGUE_HONORS/ALL_AMERICAN_TO_PRO_BOWL) --
        if has_pro_bowl_phrase:
            if has_all_american_phrase or has_later_nfl_phrase:
                spec = {
                    "mechanic": "guess", "domain": "CROSS_LEAGUE_HONORS", "relationship_predicate": "ALL_AMERICAN_TO_PRO_BOWL",
                    "question_count": _question_count_from_text(text), "difficulty": "any",
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched Pro Bowl + All-American/cross-league-composition signal -> "
                    "ALL_AMERICAN_TO_PRO_BOWL (real, disclosed double-name-joined bridge).",
                )
            if has_college_or_school and not has_lineup:
                spec = {
                    "mechanic": "guess", "domain": "NFL_PRO_BOWL_COLLEGE", "relationship_predicate": "ATTENDED_COLLEGE_PRO_BOWL",
                    "question_count": _question_count_from_text(text), "difficulty": "any",
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched Pro Bowl + college composition -> ATTENDED_COLLEGE_PRO_BOWL (real, "
                    "player_id-joined composition), never stripping the Pro Bowl qualifier.",
                )
            spec = {
                "mechanic": "guess", "domain": "NFL_PRO_BOWL", "relationship_predicate": "SELECTED_PRO_BOWL",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched 'Pro Bowl' phrase -> SELECTED_PRO_BOWL guess capability (which real player was "
                "selected to the Pro Bowl), outranking the generic player+season+team pattern.",
            )

        # --- Hall of Fame (real capabilities: NFL_HALL_OF_FAME/INDUCTED_HOF,
        # NFL_HOF_COLLEGE) -- "identify" is one of _CLUE_WORDS, so a HOF
        # request phrased as "identify a Hall of Fame player" would
        # otherwise match the Player-From-Clues block above -- checked
        # instead in THIS block's favor by placing this whole section
        # before that block would be wrong (Player-From-Clues is a real,
        # more specific mechanic when a genuine clue-sequence request is
        # meant); in practice a bare HOF phrase without "clue"/"who am i"
        # still reaches here because the Player-From-Clues block above
        # requires has_clue-and-has_player or has_who_am_i, neither of
        # which a plain "guess who's in the Hall of Fame" request trips.
        # All-American -> Hall of Fame composition is NOT registered (real,
        # measured overlap: 0) -- that specific composed request is
        # reported honestly further below, never silently downgraded here.
        if has_hof_signal:
            if not (has_all_american_phrase or has_later_nfl_phrase):
                if has_college_or_school and not has_lineup:
                    spec = {
                        "mechanic": "guess", "domain": "NFL_HOF_COLLEGE", "relationship_predicate": "ATTENDED_COLLEGE_HOF",
                        "question_count": _question_count_from_text(text), "difficulty": "any",
                        "filters": {}, "exclusions": [],
                    }
                    return _result(
                        request_text, "TRANSLATED", spec,
                        "Matched Hall of Fame + college composition -> ATTENDED_COLLEGE_HOF (real, "
                        "player_id-joined composition), never stripping the HOF qualifier.",
                    )
                spec = {
                    "mechanic": "guess", "domain": "NFL_HALL_OF_FAME", "relationship_predicate": "INDUCTED_HOF",
                    "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched Hall of Fame/HOF/Canton/inducted keyword -> INDUCTED_HOF guess capability "
                    "(which real player was inducted), outranking the generic player+season+team pattern.",
                )

        # --- Coordinators (real capabilities: NFL_OFFENSIVE_COORDINATOR/
        # NFL_DEFENSIVE_COORDINATOR) -- Section 9/10/26: must outrank the
        # team+offense/lineup pattern below (a coordinator request contains
        # "team" + "offensive"/"defensive", which that pattern's own
        # has_offense check already treats as a lineup signal) and the
        # plain has_coach_word pattern (a coordinator is not a head coach).
        # Side (offense vs defense) resolved by an explicit phrase first,
        # then by which side-word co-occurs with a bare "coordinator"
        # mention; genuinely ambiguous (neither side signaled) falls through
        # to an honest clarifying question rather than guessing a side.
        if has_oc_phrase or has_dc_phrase or (has_coordinator_word and (bool(words & _OFFENSE_SIDE_WORDS) or bool(words & _DEFENSE_SIDE_WORDS))):
            is_offense = has_oc_phrase or (not has_dc_phrase and bool(words & _OFFENSE_SIDE_WORDS) and not bool(words & _DEFENSE_SIDE_WORDS))
            is_defense = has_dc_phrase or (not has_oc_phrase and bool(words & _DEFENSE_SIDE_WORDS) and not bool(words & _OFFENSE_SIDE_WORDS))
            if is_offense and not is_defense:
                domain, predicate, side = "NFL_OFFENSIVE_COORDINATOR", "COORDINATED_OFFENSE", "offensive"
            elif is_defense and not is_offense:
                domain, predicate, side = "NFL_DEFENSIVE_COORDINATOR", "COORDINATED_DEFENSE", "defensive"
            else:
                return _result(
                    request_text, "NEEDS_CLARIFICATION", None,
                    "Recognized a coordinator request but couldn't tell which side of the ball -- "
                    "offensive or defensive coordinator?",
                    understood={"concept": "NFL coordinator"}, missing_fields=["relationship_predicate"],
                    clarifying_question="Do you want the offensive coordinator or the defensive coordinator?",
                )
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": "any",
                "filters": {}, "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                f"Matched {side} coordinator signal -> {predicate} guess capability (real 2026-season "
                f"coordinator data only -- see the capability's own known_limitations), outranking the "
                f"generic team+offense/lineup pattern and the plain head-coach pattern.",
            )

        # --- Creator Capability Completion pass: real, registered routing --
        # Every concept below now maps to a real, GENERATION_VERIFIED
        # capability instead of the honest-but-unsupported report this
        # section used to return. Section 27's positive-status contract
        # still cuts both ways: never falls through to an unrelated
        # registered capability that answers a different question.
        # CFB_RANKING/CFB_UPSET are CFB-only capabilities (built on
        # cfb_rankings/cfb_games_canonical/cfb_betting_lines) -- an
        # explicitly NFL-worded request with no CFB signal ("NFL power
        # rankings", "Super Bowl upset") must never be silently routed to
        # them. Reported honestly instead of falling through further down
        # the chain to an unrelated capability.
        nfl_exclusive = has_nfl and not has_cfb_signal
        if has_ranking_signal and not has_upset_signal:
            if nfl_exclusive:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a rankings concept worded as NFL-specific -- the only registered rankings "
                    "capability (RANKED_IN_POLL) is CFB-only (cfb_rankings has no NFL equivalent).",
                    understood={"concept": "NFL rankings"},
                )
            spec = {
                "mechanic": "guess", "domain": "CFB_RANKING", "relationship_predicate": "RANKED_IN_POLL",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched CFB rankings/polls signal -> RANKED_IN_POLL guess capability (AP Top 25).")

        if has_upset_signal:
            if nfl_exclusive:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized an upset concept worded as NFL-specific -- both registered upset "
                    "capabilities (RANKING_UPSET, BETTING_UPSET) are CFB-only.",
                    understood={"concept": "NFL upset"},
                )
            if has_betting_upset_signal and not has_ranking_signal:
                spec = {
                    "mechanic": "guess", "domain": "CFB_UPSET", "relationship_predicate": "BETTING_UPSET",
                    "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                    "filters": {}, "exclusions": [],
                }
                return _result(request_text, "TRANSLATED", spec,
                                "Matched an explicit betting/underdog/spread signal -> BETTING_UPSET guess "
                                "capability (real pregame consensus underdog winning outright).")
            spec = {
                "mechanic": "guess", "domain": "CFB_UPSET", "relationship_predicate": "RANKING_UPSET",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched a general upset signal with no explicit betting/underdog/spread "
                            "signal -> RANKING_UPSET guess capability (the default, clearly-labeled "
                            "interpretation: a lower-ranked/unranked team beating a higher-ranked one).")

        if (has_scored_first_phrase or (has_touchdown_word and has_game_word)) and not (has_postseason or has_lineup):
            if has_cfb_signal and not has_nfl:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a real CFB play-by-play scoring-event concept, but cfb_plays has no "
                    "player-identity columns at all (no passer/rusher/receiver key, confirmed directly "
                    "against its real schema) -- a genuine data gap, not an unwritten adapter. Not falling "
                    "through to CFB_GAME_RESULT/WON_GAME, which answers a different question.",
                    understood={"concept": "CFB PBP scoring event"},
                )
            spec = {
                "mechanic": "guess", "domain": "NFL_SCORING_PLAY", "relationship_predicate": "FIRST_TOUCHDOWN_SCORER",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched NFL PBP first-touchdown-scorer signal -> FIRST_TOUCHDOWN_SCORER guess "
                            "capability, never downgraded to WON_GAME (who won, not who scored).")

        # Creator Capability Completion pass fix: the original gate required
        # has_defensive_event_word (a literal sack/interception/fumble
        # word), which "who picked off the QB" never satisfies despite
        # _INTERCEPTION_PHRASE_RE already handling "picked off" correctly --
        # widened to accept any of the phrase-regexes actually used to pick
        # the predicate below, not just the cruder word-set. has_fumble_word
        # additionally bypasses the who-made/no-game requirement entirely
        # (see its own comment above) so a genuinely ambiguous bare "fumble"
        # mention -- e.g. "guess about a fumble in this game" -- still
        # reaches the real disambiguating branch below instead of being
        # silently dropped before ever being considered.
        if has_fumble_word or (
            (has_defensive_event_word or has_sack_phrase or has_interception_phrase)
            and (has_who_made_phrase or not has_game_word)
        ):
            if has_sack_phrase:
                domain, predicate, label = "NFL_DEFENSIVE_EVENT", "RECORDED_SACK", "sack"
            elif has_interception_phrase:
                domain, predicate, label = "NFL_DEFENSIVE_EVENT", "RECORDED_INTERCEPTION", "interception"
            elif has_forced_fumble_phrase:
                domain, predicate, label = "NFL_DEFENSIVE_EVENT", "FORCED_FUMBLE", "forced fumble"
            elif has_fumble_recovery_phrase:
                domain, predicate, label = "NFL_DEFENSIVE_EVENT", "RECOVERED_FUMBLE", "fumble recovery"
            else:
                # A bare "fumble" mention with neither "forced" nor
                # "recovered" language is genuinely ambiguous between the
                # two real, distinct capabilities -- ask, never guess.
                return _result(
                    request_text, "NEEDS_CLARIFICATION", None,
                    "Recognized a real fumble-related defensive event but couldn't tell which -- who forced "
                    "it, or who recovered it?",
                    understood={"concept": "NFL fumble event"}, missing_fields=["relationship_predicate"],
                    clarifying_question="Do you want to guess who forced the fumble, or who recovered it?",
                )
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            f"Matched player-level {label} signal -> {predicate} guess capability, never "
                            f"downgraded to the team-level box-score comparison capability.")

        if has_drive_word:
            if has_cfb_signal and not has_nfl:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a real CFB drive-outcome concept, but this Engine has no cfb_drives-shaped "
                    "table at all (cfb_plays has a drive_id column but no separate drive-level result/"
                    "summary table) -- a genuine data gap, not an unwritten adapter.",
                    understood={"concept": "CFB drive outcome"},
                )
            spec = {
                "mechanic": "guess", "domain": "NFL_DRIVE", "relationship_predicate": "DRIVE_RESULT",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched NFL drive-outcome signal -> DRIVE_RESULT guess capability.")

        if has_same_week_phrase and has_stat_compare_phrase:
            if nfl_exclusive:
                # Real, disclosed gap: this pass only built the CFB variant
                # (cfb_player_game_stats_real) -- no NFL same-week player-
                # stat comparison capability was registered this pass.
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a real same-week player-stat comparison concept worded as NFL-specific -- "
                    "only the CFB variant (CFB_STAT_COMPARISON) is registered this pass; no NFL equivalent "
                    "capability exists yet. Not falling through to WEEKLY_PICKEM or an unrelated capability.",
                    understood={"concept": "NFL same-week player stat comparison"},
                )
            if has_passing_category:
                domain, predicate = "CFB_STAT_COMPARISON", "PASSING_COMPARISON"
            elif has_receiving_category:
                domain, predicate = "CFB_STAT_COMPARISON", "RECEIVING_COMPARISON"
            else:
                domain, predicate = "CFB_STAT_COMPARISON", "RUSHING_COMPARISON"  # real, disclosed default
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            f"Matched real same-week player-stat comparison signal -> {predicate} guess "
                            f"capability. A bare 'week' mention alone never routes to WEEKLY_PICKEM.")

        if has_top_performer_phrase:
            if has_passing_category:
                predicate = "PASSING_LEADER"
            elif has_receiving_category:
                predicate = "RECEIVING_LEADER"
            else:
                predicate = "RUSHING_LEADER"  # real, disclosed default -- the question always names the category
            domain = "CFB_GAME_LEADER" if (has_cfb_signal and not has_nfl) else "NFL_GAME_LEADER"
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            f"Matched 'top performer' signal -> {predicate} guess capability (an objective, "
                            f"disclosed single-stat-category team leader -- never a fabricated cross-"
                            f"position score), never downgraded to TEAM_OF_STARTING_LINEUP.")

        if has_ordered_path_phrase or (has_transfer_word and has_later_nfl_phrase):
            spec = {
                "mechanic": "guess", "domain": "CFB_TRANSFER_PATH", "relationship_predicate": "ORDERED_PATH_NFL_BRIDGED",
                "question_count": _question_count_from_text(text), "difficulty": "any",
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched transfer-path + NFL-reached qualifier -> ORDERED_PATH_NFL_BRIDGED guess "
                            "capability (real, small, disclosed NFL-bridged pool), never downgraded to the "
                            "plain CFB_TRANSFER/ATTENDED_COLLEGE 'which school' question.")

        if has_all_american_phrase and (has_nfl_star_phrase or has_later_nfl_phrase or has_pro_bowl_phrase or has_hof_signal):
            if has_hof_signal and not (has_nfl_star_phrase or has_pro_bowl_phrase):
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a real All-American -> Hall of Fame cross-league composition, but the real, "
                    "measured overlap between this Engine's certified All-America table and its Hall of "
                    "Fame table (via the only real NFL<->CFB player bridge) is 0 -- a genuine data-gap "
                    "limitation, not an unwritten adapter.",
                    understood={"concept": "All-American -> NFL Hall of Fame cross-league composition"},
                )
            predicate = "ALL_AMERICAN_TO_PRO_BOWL" if has_pro_bowl_phrase else "ALL_AMERICAN_TO_ALL_PRO"
            spec = {
                "mechanic": "guess", "domain": "CROSS_LEAGUE_HONORS", "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": "any",
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            f"Matched cross-league honors composition -> {predicate} guess capability (real, "
                            f"disclosed double-name-joined bridge; a genuinely small real pool).")

        if has_great_in_college_phrase and has_nfl_star_phrase:
            spec = {
                "mechanic": "guess", "domain": "CROSS_LEAGUE_HONORS", "relationship_predicate": "ALL_AMERICAN_TO_ALL_PRO",
                "question_count": _question_count_from_text(text), "difficulty": "any",
                "filters": {}, "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched fuzzy 'great in college, star in the NFL' language, grounded to real objective "
                "honors (great in college -> All-American; NFL star -> All-Pro, the default composed honor) "
                "-> ALL_AMERICAN_TO_ALL_PRO guess capability -- never an invented subjective greatness score.",
            )

        # Compound request explicitly asking for more than one thing, where
        # at least one part has no supported data ("both a QB's team and his
        # favorite food"). Checked FIRST and narrowly (requires the explicit
        # "both" coordination signal, not just any co-occurrence of an
        # off-topic word with a football word) so a simple single-topic
        # unsupported request (e.g. "players' favorite foods" alone) still
        # falls through to plain NO_MATCH below, unchanged from v0.2.
        if has_mixed_signal and has_offtopic:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized this as a compound request combining a football-guessing "
                "part with a part that has no supported data at all ('favorite food' "
                "or similar -- no Engine domain covers this). Not silently dropping "
                "the unsupported half: neither part can be safely generated, so the "
                "whole request is blocked rather than partially fulfilled.",
            )

        # Player From Clues, added Director v0.4. Checked before the draft
        # pattern so a request that mentions clues isn't misread as a
        # draft-guessing request. Before v0.4 this exact pattern
        # (clue + player keywords) returned UNDERSTOOD_UNSUPPORTED_MECHANIC --
        # now that tools/director_v04/player_from_clues.py genuinely
        # generates and QA-passes real puzzles, it routes to that capability
        # instead. "who am i" is matched as its own phrase since that classic
        # framing doesn't necessarily use the word "clue" at all.
        #
        # COMPETITION-AWARE FIX (CFB expansion, Mission A5): a prior version
        # of this pattern matched purely on clue/player/who-am-i keywords
        # with no league check at all, so a CFB-worded request ("identify a
        # player from his college career") silently resolved to SUPPORTED
        # against the NFL-only IDENTIFY_FROM_CLUES capability -- found by
        # actually testing the Creator against that exact request, not
        # assumed. Real fix, not a keyword patch: `has_cfb_signal` (an
        # explicit "cfb" token, the literal phrase "college football", or
        # any "college"/"colleges" word) is checked BEFORE building a spec.
        # If a CFB signal is present and no "nfl" token contradicts it, this
        # is a real, schema-expressible concept
        # (identify_player_from_clues / CFB) with genuinely no registered
        # capability behind it (there is no CFB equivalent of
        # tools/director_v04/player_from_clues.py), so it is reported
        # UNDERSTOOD_UNSUPPORTED_MECHANIC honestly rather than silently
        # generating an NFL question for a CFB-worded ask. A bare request
        # with neither an "nfl" nor a "cfb"/"college" signal (e.g. plain
        # "identify this player from clues") still defaults to the NFL
        # capability, consistent with every other pattern in this file
        # (Draft/Championship/Lineup also default to NFL domains without
        # requiring an explicit "nfl" token) -- an explicit "nfl" token
        # always wins over an incidental "college" mention.
        # STALE-COLLEGE-FEASIBILITY FIX: also route a "guess the PLAYER from
        # his college [and other draft facts]" request here -- a directional
        # phrase match (not just keyword presence, see module docstring),
        # requires no team framing (a team request is a different capability
        # entirely). IDENTIFY_FROM_CLUES already supports both "college" and
        # "draft_round" as real clue types (tools/director_v04/
        # player_from_clues.py), so this is genuinely supported today, not a
        # new adapter.
        college_player_clue_request = has_guess_player_phrase and has_college_or_school and not has_team
        if (has_clue and has_player) or has_who_am_i or college_player_clue_request:
            # Creator Semantic Routing + Who Am I pass: a real CFB parity
            # capability now exists (identify_player_from_clues/
            # CFB_PLAYER_IDENTITY -- tools/director_v04/
            # cfb_player_from_clues.py, GENERATION_VERIFIED), so a
            # CFB-worded request routes to it directly instead of the
            # honest-but-unsupported report this branch used to return.
            if has_cfb_signal and not has_nfl:
                cfb_spec = {
                    "mechanic": "identify_player_from_clues",
                    "domain": "CFB_PLAYER_IDENTITY",
                    "relationship_predicate": "IDENTIFY_FROM_CLUES",
                    "question_count": _question_count_from_text(text),
                    "difficulty": "any",
                    "filters": {}, "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", cfb_spec,
                    "Matched clue/identify/'who am I' keywords with an explicit 'cfb' token, 'college "
                    "football' phrase, or 'college'/'colleges' word (no contradicting 'nfl' token) -> "
                    "IDENTIFY_FROM_CLUES / CFB_PLAYER_IDENTITY (the real CFB parity capability), never "
                    "silently generating an NFL question for a CFB-worded request.",
                )
            spec = {
                "mechanic": "identify_player_from_clues",
                "domain": "NFL_PLAYER_IDENTITY",
                "relationship_predicate": "IDENTIFY_FROM_CLUES",
                "question_count": _question_count_from_text(text),
                "difficulty": "any",  # only value this capability supports -- see PLAYER_FROM_CLUES_MECHANIC_SPEC.md, Part H
                "filters": {},
                "exclusions": [],
            }
            note = (
                "Matched 'guess the player' + college/school keywords with no team framing -> "
                "IDENTIFY_FROM_CLUES (college and draft round are both real, supported clue types)."
                if college_player_clue_request and not (has_clue and has_player) and not has_who_am_i else
                "Matched clue/identify/'who am I' keywords with no CFB signal -> "
                "IDENTIFY_FROM_CLUES player-from-clues capability."
            )
            return _result(request_text, "TRANSLATED", spec, note)

        if has_player and has_draft and has_team:
            spec = {
                "mechanic": "guess",
                "domain": "NFL_DRAFT",
                "relationship_predicate": "DRAFTED_BY",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched player + drafted/picked + team/franchise keywords "
                "-> DRAFTED_BY guess capability.",
            )

        # Player + Season -> Team/School (TEAM_OF_SEASON / SCHOOL_OF_SEASON),
        # Reliability-design Phase 3 (NFL) and Phase 4 (CFB) conservative-
        # compiler vertical slices -- same real question shape, two real
        # sports. Requires player + season + (team OR college/school signal)
        # with NO draft/postseason/lineup/coaching/boxscore/transfer signal
        # -- each of those is a genuinely different real question already
        # matched by its own pattern (draft: which team DRAFTED a player;
        # postseason: how a team's SEASON ended; lineup: a team's full
        # starting offense; coaching: which team a COACH coached; transfer:
        # CFB_TRANSFER's own "one of several schools across a whole career"
        # question, never a specific season) that must keep winning over
        # this one when its own signal is present, checked via the
        # `not (...)` guard rather than ordering alone, since "season" can
        # co-occur with any of them. Competition-aware the same way the
        # shared-predicate NFL/CFB pairs elsewhere in this file are: an
        # explicit CFB signal (with no contradicting NFL token) routes to
        # the CFB capability; everything else defaults to NFL.
        if (
            has_player and has_season_word and (has_team or has_college_or_school)
            and not (has_draft or has_postseason or has_lineup or has_offense or has_coach_word
                     or has_boxscore_word or has_transfer_word)
            and not (has_game_word and has_result_word)
        ):
            if has_cfb_signal and not has_nfl:
                domain, predicate = "CFB_PLAYER_SEASON", "SCHOOL_OF_SEASON"
                note = (
                    "Matched player + season + college/school keywords with a CFB signal and no "
                    "draft/postseason/lineup/coaching/boxscore/transfer signal -> SCHOOL_OF_SEASON (CFB) "
                    "guess capability (which real school a player was on in a given season, not a "
                    "multi-school career like CFB_TRANSFER)."
                )
            else:
                domain, predicate = "NFL_PLAYER_SEASON", "TEAM_OF_SEASON"
                note = (
                    "Matched player + team + season keywords with no draft/postseason/lineup/coaching/"
                    "boxscore signal -> TEAM_OF_SEASON (NFL) guess capability (which real team a player "
                    "was on in a given season, not who drafted them or how their team's season ended)."
                )
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec, note)

        # NFL Super Bowl History (WON_CHAMPIONSHIP), added after the NFL
        # Wikipedia history import. Checked BEFORE the older team+postseason
        # pattern below, and requires a real "who won" signal, not just any
        # Super Bowl mention -- a request like "guess which team won the
        # Super Bowl" also contains "team" and matches _has_super_bowl_phrase
        # (a _POSTSEASON_WORDS trigger), so without this earlier, more
        # specific check it would silently fall into TEAM_POSTSEASON_RESULT
        # (a different real question: how one team's own season ended, not
        # who won a specific Super Bowl game). Excludes an award-word
        # co-occurrence ("who won Super Bowl MVP") so that phrasing falls
        # through to the NFL_AWARDS pattern below instead.
        if _has_super_bowl_phrase(text) and has_win_word and not has_award_word:
            spec = {
                "mechanic": "guess",
                "domain": "NFL_SUPER_BOWL",
                "relationship_predicate": "WON_CHAMPIONSHIP",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched 'Super Bowl' + won/win keywords with no award-word co-occurrence -> "
                "WON_CHAMPIONSHIP guess capability (which team won a specific Super Bowl game).",
            )

        # CFB National Championship (WON_CHAMPIONSHIP), Creator-gap-audit
        # operation. "National championship" is inherently a CFB-only term
        # (the NFL's own title game is always called the Super Bowl, never
        # this) -- no explicit "cfb"/"college" word is required for this
        # phrase alone to route here, unlike other CFB patterns in this file
        # that default to NFL absent an explicit signal.
        if has_national_championship_phrase:
            spec = {
                "mechanic": "guess", "domain": "CFB_CHAMPIONSHIP", "relationship_predicate": "WON_CHAMPIONSHIP",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched 'national championship'/'national champion' phrase -> "
                            "WON_CHAMPIONSHIP (CFB) guess capability.")

        # NFL Season Awards (WON_AWARD), added the same operation -- AP MVP/
        # OPOY/DPOY/OROY/DROY plus Super Bowl MVP. "mvp"/"award"/"awards"/
        # "trophy" alone, or the "player of the year"/"rookie of the year"
        # phrases, are unambiguous enough in a football-trivia context (same
        # reasoning cfb_heisman's single-keyword match already uses).
        if has_award_word or has_player_of_year_phrase or has_rookie_of_year_phrase:
            spec = {
                "mechanic": "guess",
                "domain": "NFL_AWARDS",
                "relationship_predicate": "WON_AWARD",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched award/MVP/trophy/'player of the year'/'rookie of the year' keywords -> "
                "WON_AWARD guess capability (AP MVP/OPOY/DPOY/OROY/DROY + Super Bowl MVP).",
            )

        # NFL/CFB Season Stat Leaders (LED_LEAGUE_IN_STAT), Creator-gap-audit
        # operation. "not has_game_word" guards against a hypothetical
        # single-game phrasing colliding with this season-long-leaderboard
        # capability -- competition-aware the same way WON_GAME is (explicit
        # CFB signal with no contradicting NFL token routes to CFB; a bare
        # request defaults to NFL).
        if has_leader_word and not has_game_word:
            if has_cfb_signal and not has_nfl:
                domain, note = "CFB_SEASON_STATS", "Matched leader/led keywords with a CFB signal -> LED_LEAGUE_IN_STAT (CFB) guess capability."
            else:
                domain, note = "NFL_SEASON_STATS", "Matched leader/led keywords -> LED_LEAGUE_IN_STAT (NFL) guess capability."
            spec = {
                "mechanic": "guess", "domain": domain, "relationship_predicate": "LED_LEAGUE_IN_STAT",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec, note)

        # NFL Coaching History (COACHED_TEAM), Creator-gap-audit operation.
        # "coach"/"coached"/"coaching" alone is unambiguous enough in a
        # football-trivia context (same single-keyword discipline "heisman"/
        # award words already use above) -- no CFB equivalent is registered
        # (cfb_coaches has real, disclosed data-quality problems -- see
        # tools/quiz_export/adapters/cfb_heisman.py's own module docstring
        # for the precedent of NOT building on a table with known parsing
        # artifacts), so this always routes to NFL, never CFB.
        if has_coach_word:
            spec = {
                "mechanic": "guess", "domain": "NFL_COACHING", "relationship_predicate": "COACHED_TEAM",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched coach/coached/coaching keyword -> COACHED_TEAM (NFL) guess capability.")

        # CFB Transfer Portal (ATTENDED_COLLEGE via CFB_TRANSFER domain),
        # Creator-gap-audit operation. Checked BEFORE the general "guess the
        # college of a player" fallback further below, which would otherwise
        # also match a transfer-worded request and send it to the NFL_DRAFT/
        # ATTENDED_COLLEGE capability instead -- "transfer" is a real,
        # distinct signal for the CFB-specific multi-school capability.
        if has_transfer_word:
            spec = {
                "mechanic": "guess", "domain": "CFB_TRANSFER", "relationship_predicate": "ATTENDED_COLLEGE",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched transfer/transferred keyword -> ATTENDED_COLLEGE (CFB_TRANSFER) guess capability.")

        # Gold Standard "10. New Game Modes" named-concept recognition
        # (Rivalry Data + Gold Standard Content Integration operation) --
        # each phrase below is the workbook's own concept name, distinctive
        # enough to match alone (same precedent as "heisman"). Era Gauntlet
        # (#51) scopes the base College Offense capability to one board per
        # real era via `filters: {"era_gauntlet": True}`; Franchise Marathon
        # (#19) is real but NOT matched by name here -- extracting an
        # arbitrary franchise name from free text safely is out of scope
        # this pass, so it stays reachable only via a direct filters call
        # (`franchise_name`), never guessed from text.
        text_lower_gs = text.lower()
        if "era gauntlet" in text_lower_gs:
            spec = {
                "mechanic": "guess", "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
                "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {"era_gauntlet": True}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched 'era gauntlet' -> TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE guess "
                            "capability, scoped to one real champion per era.")
        for pattern, (dom, pred) in _GOLD_STANDARD_CONCEPT_PATTERNS:
            if pattern.search(text_lower_gs):
                spec = {
                    "mechanic": "guess", "domain": dom, "relationship_predicate": pred,
                    "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                    "filters": {}, "exclusions": [],
                }
                return _result(request_text, "TRANSLATED", spec,
                                f"Matched Gold Standard concept name -> {pred} ({dom}) guess capability.")

        # CFB Rivalry TRIVIA (CORRECT_TRIVIA_ANSWER), Rivalry Data + Gold
        # Standard Content Integration operation -- checked BEFORE the older,
        # narrower CFB_RIVALRY/RIVAL_OF pattern below (a single "who is X's
        # rival" fact) because a request naming a SPECIFIC rivalry (by
        # nickname or by naming both schools) or explicitly asking for
        # rivalry TRIVIA wants the richer, curated 20-question-per-pack bank,
        # not a single rival-lookup fact. A specific pack match routes with
        # `filters: {"rivalry_pack_number": N}` (e.g. "Make me an Iron Bowl
        # trivia game" -> just that pack's 20 questions); a generic rivalry-
        # trivia request with no specific pack named routes with
        # `filters: {"rivalry_only": True}` (the 860 rivalry rows across all
        # 43 packs, not the 412 general-category rows). See
        # tools/quiz_export/adapters/cfb_rivalry_trivia.py's own module
        # docstring for the full data audit trail.
        text_lower = text.lower()
        has_trivia_word = "trivia" in text_lower
        matched_pack = _match_rivalry_pack(text_lower)
        if matched_pack is not None and (matched_pack in _RIVALRY_NICKNAME_TO_PACK.values() or has_rivalry_word or has_trivia_word or has_game_word):
            spec = {
                "mechanic": "guess", "domain": "CFB_RIVALRY_TRIVIA", "relationship_predicate": "CORRECT_TRIVIA_ANSWER",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {"rivalry_pack_number": matched_pack}, "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                f"Matched a specific named rivalry -> CFB_RIVALRY_TRIVIA guess capability, scoped to "
                f"rivalry pack #{matched_pack}.",
            )
        # Narrower than the general "game about rivalries" case below on
        # purpose -- a bare fact-lookup phrasing like "guess who this
        # school's rival is" (no game/trivia signal) must still fall
        # through to the older, single-fact CFB_RIVALRY/RIVAL_OF capability
        # right below (see test_feasibility.py::test_supported_for_cfb_
        # rivalry_request). `has_game_word`, not the broader `has_cfb_
        # signal`, is what distinguishes "a GAME about rivalries" from
        # "who is X's rival".
        if has_rivalry_word and (has_trivia_word or has_game_word):
            spec = {
                "mechanic": "guess", "domain": "CFB_RIVALRY_TRIVIA", "relationship_predicate": "CORRECT_TRIVIA_ANSWER",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {"rivalry_only": True}, "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched 'rivalry'/'rivalries' + 'trivia'/'game' keywords (no specific pack named) -> "
                "CFB_RIVALRY_TRIVIA guess capability, scoped to rivalry-only rows across all 43 packs.",
            )

        # CFB Rivalries (RIVAL_OF), Creator-gap-audit operation. "rival(s)"/
        # "rivalry" alone is unambiguous in a football-trivia context.
        if has_rivalry_word:
            spec = {
                "mechanic": "guess", "domain": "CFB_RIVALRY", "relationship_predicate": "RIVAL_OF",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched rival/rivalry keyword -> RIVAL_OF (CFB) guess capability.")

        # Super Bowl Champion Offense by College (Rivalry Data + Gold
        # Standard Content Integration operation) -- checked BEFORE the
        # general "team + postseason -> TEAM_POSTSEASON_RESULT" pattern right
        # below, narrowly (requires an explicit college/offense-or-lineup
        # signal too), so a request that specifically asks to guess a Super
        # Bowl champion's TEAM AND SEASON from its offense by COLLEGE routes
        # to the richer, curated capability instead of the plain win/loss
        # postseason-result one. Answers Gold Standard concept #1 ("College
        # Offense") and this operation's own explicit "Give me a Super Bowl
        # winning offense by colleges and make me guess the team and season"
        # request. See tools/quiz_export/adapters/sb_champion_offense_college.py.
        if has_postseason and has_college and (has_offense or has_lineup):
            spec = {
                "mechanic": "guess",
                "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
                "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched Super Bowl/postseason + college + offense/lineup keywords -> "
                "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE guess capability (curated, all 60 real "
                "Super Bowl champions 1967-2026, names hidden).",
            )

        if has_team and has_postseason:
            spec = {
                "mechanic": "guess",
                "domain": "NFL_CHAMPIONSHIP",
                "relationship_predicate": "TEAM_POSTSEASON_RESULT",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched team/franchise + playoff/postseason/championship/Super Bowl "
                "keywords -> TEAM_POSTSEASON_RESULT guess capability.",
            )

        # POSITION + COLLEGE PROOF-GAME FIX: a "position + college, NAMES
        # HIDDEN" request must NOT silently fall into the general Starting
        # Lineup pattern below -- that pattern's own capability only ever
        # shows player NAMES, never colleges, so matching it here would be
        # exactly the silent-fallback-to-names the earlier correction pass
        # forbade. Checked BEFORE the general pattern, narrowly (requires an
        # explicit hidden/hide/anonymous/"no names" signal, not just any
        # college mention -- a plain college-phrased lineup request still
        # correctly falls through to the general pattern below, which
        # honestly explains the names-not-colleges substitution in its own
        # copy).
        #
        # As of the identity-bridge expansion (tools/data_refresh/
        # nfl_college_identity_bridge.py), this IS now a real, registered
        # capability (NFL_OFFENSE_LINEUP_COLLEGE / TEAM_OF_STARTING_LINEUP_
        # BY_COLLEGE -- 68 real, certified team-seasons, 5 skill positions,
        # OL honestly excluded -- see tools/quiz_export/adapters/
        # lineup_college.py's own module docstring for the full audit
        # trail), so this now returns TRANSLATED, not NO_MATCH.
        #
        # Rivalry Data + Gold Standard Content Integration operation: a
        # request that names NO specific historical season now routes to the
        # NEWER, richer NFL_OFFENSE_COLLEGE_CURATED capability instead (32
        # real CURRENT (2026) teams, all 11 positions including the full
        # offensive line, curated-workbook-sourced -- see
        # tools/quiz_export/adapters/nfl_offense_college_curated.py's own
        # module docstring for why this doesn't just replace the historical
        # capability outright). A request that DOES name a specific
        # historical year (`_YEAR_RE`) still routes to the original
        # bridge-sourced, season-scoped capability below -- unchanged
        # behavior for that narrower, more specific phrasing.
        if (has_team or has_nfl) and has_college and has_hidden_names and (has_offense or has_lineup or has_position):
            if _YEAR_RE.search(text):
                spec = {
                    "mechanic": "guess",
                    "domain": "NFL_OFFENSE_LINEUP_COLLEGE",
                    "relationship_predicate": "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",
                    "question_count": _question_count_from_text(text),
                    "difficulty": _difficulty_from_words(words),
                    "filters": {},
                    "exclusions": [],
                }
                return _result(
                    request_text, "TRANSLATED", spec,
                    "Matched team + position/offense/lineup + college + names-hidden keywords + an "
                    "explicit historical year -> TEAM_OF_STARTING_LINEUP_BY_COLLEGE guess capability. "
                    "Note: shows only the 5 skill positions (no offensive line) -- see the package's own "
                    "notes/known_limitations for why.",
                )
            spec = {
                "mechanic": "guess",
                "domain": "NFL_OFFENSE_COLLEGE_CURATED",
                "relationship_predicate": "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched team + position/offense/lineup + college + names-hidden keywords, no specific "
                "historical year named -> TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE guess capability (curated, "
                "all 32 current NFL teams, all 11 positions including the offensive line, names hidden).",
            )

        # Starting Lineup, added v1.8, Part F. Requires "team" plus (offense OR
        # lineup OR position OR college) -- broad enough to catch the exact
        # college-phrased proof-game request (see module docstring for why
        # "college" phrasing routes here honestly, not deceptively) as well as
        # more direct phrasings like "starting lineup by position".
        if has_team and (has_offense or has_lineup or (has_position and has_college)):
            spec = {
                "mechanic": "guess",
                "domain": "NFL_OFFENSE_LINEUP",
                "relationship_predicate": "TEAM_OF_STARTING_LINEUP",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched team + offense/lineup/position/college keywords -> "
                "TEAM_OF_STARTING_LINEUP guess capability. Note: the generated "
                "puzzle uses real player NAMES, not colleges -- see the package's "
                "own instructions/notes for why (colleges are not reliably present "
                "in this database for NFL players).",
            )

        # CFB Heisman, added during the CFB data enrichment operation. A real
        # gap found by actually testing the Creator against a real "Make me a
        # CFB Heisman guessing game" request, not assumed: the capability was
        # registered in CAPABILITY_REGISTRY (reachable via direct spec-based
        # generation, which is how the public API and every test call it) but
        # had NO translator keyword recognition at all, so the Creator's
        # natural-language path reported NO_MATCH for a real, fully-certified
        # capability. "heisman" alone is unambiguous enough in a football-
        # trivia context to not need a compound AND condition the way the
        # patterns above do.
        if has_heisman:
            spec = {
                "mechanic": "guess",
                "domain": "CFB_HEISMAN",
                "relationship_predicate": "WON_HEISMAN",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched 'heisman' keyword -> WON_HEISMAN guess capability.",
            )

        # NFL/CFB Game Results, added during the App-Wide Engine Migration
        # operation (built on tools/data_refresh/{nfl,cfb}_games_refresh.py's
        # real, automatically-refreshed games tables). Checked after the
        # Championship pattern above (a request like "guess the result of
        # the Super Bowl" is more specifically about postseason framing and
        # should keep matching that capability, not this newer, more
        # general one) and after Heisman (unambiguous, no competing signal).
        # Competition-aware the same way the clue/player pattern is: an
        # explicit CFB signal with no contradicting "nfl" token routes to
        # the CFB capability; everything else (including a bare request
        # with no league signal at all) defaults to NFL, consistent with
        # every other pattern in this file.
        # NFL Game Box Scores, added during the Historical Engine Enrichment
        # operation (built on tools/data_refresh/nfl_team_game_stats_refresh.py's
        # real, automatically-refreshed team_game_stats table). Checked
        # BEFORE the general game+result pattern below: a box-score request
        # ("yards", "box score") also contains "game" and often "score", so
        # it would otherwise be swept into the plain WON_GAME capability --
        # this is a genuinely different question (which team gained more
        # yards, not who won). NFL-only -- team_game_stats has no CFB
        # equivalent yet.
        # Creator-gap-audit operation: sacks/turnovers/penalties box-score
        # comparisons -- checked BEFORE the plain yards pattern below (a
        # "which team had more sacks" request also contains "game" and could
        # otherwise fall through to the generic WON_GAME result pattern).
        # Each is its own real capability, not a filter on HAD_MORE_YARDS --
        # see registry.py's own comment on why. NFL-only, same real reason
        # HAD_MORE_YARDS is NFL-only (team_game_stats has no CFB equivalent).
        if has_game_word and has_sacks_word:
            spec = {
                "mechanic": "guess", "domain": "NFL_GAME_BOXSCORE", "relationship_predicate": "HAD_MORE_SACKS",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched 'game' + sack(s) keywords -> HAD_MORE_SACKS (NFL) guess capability.")
        if has_game_word and has_turnover_word:
            spec = {
                "mechanic": "guess", "domain": "NFL_GAME_BOXSCORE", "relationship_predicate": "HAD_FEWER_TURNOVERS",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched 'game' + turnover(s) keywords -> HAD_FEWER_TURNOVERS (NFL) guess capability.")
        if has_game_word and has_penalty_word:
            spec = {
                "mechanic": "guess", "domain": "NFL_GAME_BOXSCORE", "relationship_predicate": "HAD_FEWER_PENALTIES",
                "question_count": _question_count_from_text(text), "difficulty": _difficulty_from_words(words),
                "filters": {}, "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec,
                            "Matched 'game' + penalty/penalties keywords -> HAD_FEWER_PENALTIES (NFL) guess capability.")

        if has_game_word and has_boxscore_word:
            spec = {
                "mechanic": "guess",
                "domain": "NFL_GAME_BOXSCORE",
                "relationship_predicate": "HAD_MORE_YARDS",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            note = "Matched 'game' + box score/yards keywords -> HAD_MORE_YARDS (NFL) guess capability."
            return _result(request_text, "TRANSLATED", spec, note)

        if has_game_word and has_result_word:
            if has_cfb_signal and not has_nfl:
                domain, predicate = "CFB_GAME_RESULT", "WON_GAME"
                note = "Matched 'game' + result/score keywords with a CFB signal -> WON_GAME (CFB) guess capability."
            else:
                domain, predicate = "NFL_GAME_RESULT", "WON_GAME"
                note = "Matched 'game' + result/score keywords -> WON_GAME (NFL) guess capability."
            spec = {
                "mechanic": "guess",
                "domain": domain,
                "relationship_predicate": predicate,
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(request_text, "TRANSLATED", spec, note)

        # STALE-COLLEGE-FEASIBILITY FIX: the reverse direction -- "guess the
        # college/school of a player" (not a team's lineup). Checked LAST,
        # after every other, more specific pattern above (Player-From-Clues,
        # Draft, Championship, both Lineup variants, Heisman, Box Score, Game
        # Result) -- deliberately broad ("guess the college" + any "player"
        # mention, no team framing) so a MORE specific request that happens
        # to also contain those words (e.g. "guess the college football
        # player who won the Heisman") still resolves to its own real,
        # already-registered capability first, never shadowed by this
        # general fallback. A real ordering bug caught by testing this exact
        # example during the fix, not assumed. Competition-aware the same
        # way the pattern above is: an explicit CFB signal with no
        # contradicting "nfl" token is honestly reported as unsupported (no
        # CFB equivalent of this capability exists either), never silently
        # generating an NFL question for a CFB-worded request.
        if has_guess_college_phrase and has_player and not has_team:
            if has_cfb_signal and not has_nfl:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized this as a CFB-worded 'guess the player's college' request "
                    "(an explicit 'cfb' token, 'college football' phrase, or 'college'/'colleges' "
                    "word, with no contradicting 'nfl' token). This is a real, schema-expressible "
                    "concept, but the only registered player<->college capability (ATTENDED_COLLEGE "
                    "/ NFL_DRAFT) is NFL-only -- there is no registered CFB equivalent.",
                )
            spec = {
                "mechanic": "guess",
                "domain": "NFL_DRAFT",
                "relationship_predicate": "ATTENDED_COLLEGE",
                "question_count": _question_count_from_text(text),
                "difficulty": _difficulty_from_words(words),
                "filters": {},
                "exclusions": [],
            }
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched 'guess the college/school' + player keywords with no team framing -> "
                "ATTENDED_COLLEGE guess capability (draft_facts.college, real backfilled data).",
            )

        # Genuine ambiguity: clearly an NFL-related trivia/game request, but
        # not specific enough to resolve to either registered capability or
        # a recognized-but-unsupported concept. Do not guess -- ask.
        # Excludes has_offtopic: a request naming a specific unsupported
        # subject (e.g. "favorite foods") isn't something clarification
        # would resolve -- no capability choice fixes a missing data domain,
        # so that case falls through to NO_MATCH below instead, unchanged
        # from v0.2's documented behavior for that exact request.
        if has_nfl and (has_player or has_team) and not has_offtopic:
            return _result(
                request_text, "NEEDS_CLARIFICATION", None,
                "Recognized this as an NFL trivia/game request but it doesn't specify "
                "enough to pick a game -- could be draft-guessing, playoff-result-"
                "guessing, or something else entirely.",
                understood={"competition": "NFL"},
                missing_fields=["domain", "relationship_predicate"],
                clarifying_question=(
                    "What kind of NFL trivia game do you want -- for example, guessing "
                    "which team drafted a player, or guessing how a team's season ended "
                    "in the playoffs?"
                ),
            )

        return _result(
            request_text, "NO_MATCH", None,
            "No recognized game-concept keywords matched (checked: player-drafted-team "
            "pattern, team-postseason pattern, player-from-clues pattern, "
            "mixed-unsupported pattern).",
        )
