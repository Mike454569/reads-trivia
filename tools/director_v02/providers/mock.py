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
_RIVALRY_WORDS = {"rival", "rivals", "rivalry"}

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
_WHO_PHRASE_RE = re.compile(r"\bwho (recorded|made|had|got|scored)\b")
_DRIVE_WORDS = {"drive", "drives"}

_TOP_PERFORMER_RE = re.compile(r"top (offensive )?performer|leading performer|best performer")
_SAME_WEEK_RE = re.compile(r"same week|same game")
_STAT_COMPARE_RE = re.compile(r"who (had|rushed|threw|gained) more|more yards|higher\b|lower\b")

_ORDERED_PATH_RE = re.compile(r"college path|ordered path|order (his|their|the) schools?|path to the nfl")
_LATER_NFL_RE = re.compile(r"later (made|became|went to|reached) the nfl|later made the nfl")

_ALL_AMERICAN_RE = re.compile(r"all[\s-]?american")
_GREAT_IN_COLLEGE_RE = re.compile(r"great in college|college star")
_NFL_STAR_RE = re.compile(r"nfl star|star(red)? in the nfl|became (a )?star")


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

        # --- All-Pro (real capability: NFL_ALL_PRO/SELECTED_ALL_PRO) -----
        # Section 4/26: must outrank the generic player+season+team pattern
        # below (a request like "which player was First-Team All-Pro that
        # season" also contains player+season+team keywords). Checked here,
        # first, so it always wins that collision.
        # Section 7/8 composition: an All-Pro request that ALSO names a
        # college/school ("which All-Pro attended this college") or reads
        # as a cross-league honors composition ("All-American who later
        # became an All-Pro") is a genuinely different, composed question
        # this pass did not build a capability for -- reported honestly as
        # UNDERSTOOD_UNSUPPORTED_MECHANIC (never silently downgraded to the
        # plain single-honor capability, and never silently answered as a
        # generic college-attendance question) rather than matched here.
        if has_all_pro_phrase:
            if (has_college_or_school and not has_lineup) or has_all_american_phrase or has_later_nfl_phrase:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized a real All-Pro concept composed with a second real concept this pass did "
                    "not build a capability for (All-Pro + college attendance, or an All-American-to-"
                    "All-Pro cross-league composition). NFL_ALL_PRO/SELECTED_ALL_PRO (a standalone "
                    "'which player was All-Pro' question) is registered and real; this composed question "
                    "is not, and is not silently downgraded to the plain version.",
                    understood={"concept": "NFL_ALL_PRO composed with a second concept"},
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

        # --- Pro Bowl (real capability: NFL_PRO_BOWL/SELECTED_PRO_BOWL) --
        if has_pro_bowl_phrase:
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

        # --- Hall of Fame (real capability: NFL_HALL_OF_FAME/INDUCTED_HOF) --
        # "identify" is one of _CLUE_WORDS, so a HOF request phrased as
        # "identify a Hall of Fame player" would otherwise match the
        # Player-From-Clues block above -- checked instead in THIS block's
        # favor by placing this whole section before that block would be
        # wrong (Player-From-Clues is a real, more specific mechanic when a
        # genuine clue-sequence request is meant); in practice a bare HOF
        # phrase without "clue"/"who am i" still reaches here because the
        # Player-From-Clues block above requires has_clue-and-has_player or
        # has_who_am_i, neither of which a plain "guess who's in the Hall
        # of Fame" request trips.
        if has_hof_signal:
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

        # --- Recognized-but-not-yet-built real football concepts --------
        # Section 27's positive-status contract cuts both ways: a request
        # this specific must never fall through to a SUPPORTED capability
        # that answers a different question. Each of these is a real,
        # schema-expressible football concept with real underlying data
        # (cfb_rankings, cfb_betting_lines, nfl_plays, nfl_plays_defense_ext,
        # nfl_drives_real, cfb_player_game_stats_real, player_game_stats),
        # just not one this pass built an adapter+registered capability for
        # -- reported honestly, never silently answered by an unrelated
        # registered capability.
        if has_ranking_signal and not has_upset_signal:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real CFB rankings/polls concept (cfb_rankings has real AP/Coaches/CFP "
                "ranking data) -- no registered Creator capability exists for it yet. Not falling through "
                "to an unrelated capability just because 'game'/'team' also appear.",
                understood={"concept": "CFB rankings/polls"},
            )
        if has_upset_signal:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real CFB upset concept (a lower-ranked/unranked team beating a higher-ranked "
                "one via cfb_rankings, or a betting underdog winning outright via cfb_betting_lines -- two "
                "genuinely different real definitions) -- no registered Creator capability exists for "
                "either yet. Not falling through to the plain CFB_GAME_RESULT capability, which answers a "
                "different question (who won, not who was upset).",
                understood={"concept": "CFB upset (ranking or betting)"},
            )
        if (has_scored_first_phrase or (has_touchdown_word and has_game_word)) and not (has_postseason or has_lineup):
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real play-by-play scoring-event concept (nfl_plays has real touchdown/scorer "
                "data) -- no registered Creator capability exists for it yet. Not falling through to "
                "WON_GAME, which answers a different question (who won, not who scored).",
                understood={"concept": "NFL PBP scoring event"},
            )
        if has_defensive_event_word and (has_who_made_phrase or not has_game_word):
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real player-level defensive-event concept (nfl_plays_defense_ext has real "
                "sack/interception/forced-fumble/recovery identities) -- no registered Creator capability "
                "exists for a WHO-recorded-it question yet. Not falling through to the team-level "
                "HAD_MORE_SACKS box-score capability, which answers a different question (which team, not "
                "which player).",
                understood={"concept": "NFL player-level defensive event"},
            )
        if has_drive_word:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real drive-outcome concept (nfl_drives_real has real drive result/points "
                "data) -- no registered Creator capability exists for it yet.",
                understood={"concept": "NFL/CFB drive outcome"},
            )
        if has_same_week_phrase and has_stat_compare_phrase:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real same-week player-stat comparison concept (cfb_player_game_stats_real/"
                "player_game_stats have real per-game stat lines) -- no registered Creator capability "
                "exists for it yet. Not falling through to WEEKLY_PICKEM, which is a schedule-driven "
                "matchup-pick game, not a stat comparison -- a bare 'week' mention alone is never enough "
                "to route there.",
                understood={"concept": "same-week player stat comparison"},
            )
        if has_top_performer_phrase:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real top-single-game-performer concept (player_game_stats/"
                "cfb_player_game_stats_real have real per-game stat lines a passing/rushing/receiving "
                "leader could be computed from) -- no registered Creator capability exists for it yet. "
                "Not falling through to TEAM_OF_STARTING_LINEUP, which answers a different question "
                "(the whole starting lineup, not a single game's leader).",
                understood={"concept": "top single-game performer"},
            )
        if has_ordered_path_phrase or (has_transfer_word and has_later_nfl_phrase):
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real transfer-path-with-NFL-qualifier concept (cfb_transfer_summary_v17 has "
                "real multi-school career data, and an NFL bridge could filter to players who reached the "
                "NFL) -- the existing CFB_TRANSFER/ATTENDED_COLLEGE capability answers a plain 'which "
                "school did they attend' question, not an ORDERED path or an NFL-reached filter, so this "
                "more specific request is reported unsupported rather than silently downgraded to the "
                "plain version.",
                understood={"concept": "CFB transfer ordered path + NFL qualifier"},
            )
        if has_all_american_phrase and (has_nfl_star_phrase or has_later_nfl_phrase or has_pro_bowl_phrase or has_hof_signal):
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized a real cross-league honors composition (All-American -> later NFL All-Pro/Pro "
                "Bowl/Hall of Fame -- cfb_all_america_certified bridged to the new NFL honors tables) -- "
                "no registered Creator capability composes these two real relationships yet. Not silently "
                "downgraded to a plain college-attendance question.",
                understood={"concept": "All-American -> NFL honors cross-league composition"},
            )
        if has_great_in_college_phrase and has_nfl_star_phrase:
            return _result(
                request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                "Recognized fuzzy 'great in college, star in the NFL' language, grounded to real objective "
                "honors (great in college -> All-American; NFL star -> All-Pro/Pro Bowl/Hall of Fame) "
                "rather than an invented subjective greatness score -- no registered Creator capability "
                "composes these two real relationships yet. Not silently downgraded to a plain "
                "college-attendance question.",
                understood={"concept": "fuzzy college-to-NFL-stardom, grounded to real honors"},
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
        if has_team and has_college and has_hidden_names and (has_offense or has_lineup or has_position):
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
                "Matched team + position/offense/lineup + college + names-hidden keywords -> "
                "TEAM_OF_STARTING_LINEUP_BY_COLLEGE guess capability. Note: shows only the 5 skill "
                "positions (no offensive line) -- see the package's own notes/known_limitations for why.",
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
