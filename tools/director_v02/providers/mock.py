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
specific), then the four registered capability patterns (Draft,
Championship, Player From Clues, Starting Lineup), then a generic
NEEDS_CLARIFICATION fallback for requests that clearly mention
football/NFL content but not enough to resolve to any of the above, then
NO_MATCH for everything else.

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
_CFB_EXPLICIT_WORDS = {"cfb"}
_GAME_WORDS = {"game", "games"}
_RESULT_WORDS = {"result", "results", "won", "win", "score", "scored"}
_BOXSCORE_WORDS = {"boxscore", "yards", "yardage"}  # "box" + "score" (two tokens) checked separately below
_OFFTOPIC_WORDS = {"food", "foods", "favorite"}
_MIXED_SIGNAL_WORDS = {"both"}
_HARD_WORDS = {"hard", "difficult", "tough", "challenging"}
_EASY_WORDS = {"easy", "simple", "beginner"}
_MEDIUM_WORDS = {"medium", "moderate", "intermediate"}

_COUNT_RE = re.compile(r"\b(\d{1,3})\b")


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


def _result(request_text: str, status: str, spec: dict | None, notes: str, **extra) -> dict:
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
        has_hidden_names = bool(words & _HIDDEN_NAMES_WORDS) or "no names" in text.lower() or "without names" in text.lower() or "names hidden" in text.lower()
        has_heisman = bool(words & _HEISMAN_WORDS)
        has_offtopic = bool(words & _OFFTOPIC_WORDS)
        has_mixed_signal = bool(words & _MIXED_SIGNAL_WORDS)
        has_who_am_i = _has_who_am_i_phrase(text)
        has_nfl = "nfl" in words
        has_cfb_signal = bool(words & _CFB_EXPLICIT_WORDS) or has_college or "college football" in text.lower()
        has_game_word = bool(words & _GAME_WORDS)
        has_result_word = bool(words & _RESULT_WORDS)
        has_boxscore_word = bool(words & _BOXSCORE_WORDS) or ("box" in words and "score" in words)

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
        if (has_clue and has_player) or has_who_am_i:
            if has_cfb_signal and not has_nfl:
                return _result(
                    request_text, "UNDERSTOOD_UNSUPPORTED_MECHANIC", None,
                    "Recognized this as a CFB-worded player-from-clues/'who am I' "
                    "request (an explicit 'cfb' token, 'college football' phrase, or "
                    "'college'/'colleges' word, with no contradicting 'nfl' token). "
                    "This is a real, schema-expressible concept, but the only "
                    "registered player-from-clues capability (IDENTIFY_FROM_CLUES / "
                    "NFL_PLAYER_IDENTITY) is NFL-only -- there is no registered CFB "
                    "player-from-clues capability yet. Reporting unsupported rather "
                    "than silently generating an NFL question for a CFB-worded request.",
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
            return _result(
                request_text, "TRANSLATED", spec,
                "Matched clue/identify/'who am I' keywords with no CFB signal -> "
                "IDENTIFY_FROM_CLUES player-from-clues capability.",
            )

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
