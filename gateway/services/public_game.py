"""Reads Engine Gateway -- public gameplay (v1.2 draft pilot, v1.3
generalized to a multi-mode public mode registry).

The production-safe boundary between the real Reads frontend (browser,
zero credentials) and the Engine. Everything in this module is a THIN
consumer of already-certified truth -- no game logic is reimplemented here
(same rule gateway/services/generation.py and graph.py already document):
question generation still goes through `tools.director_v02.pipeline` (the
same translate -> validate -> generate -> QA path `/v1/games/generate`
already uses), and persistence reuses the existing content-addressed
`gateway/services/packages.py` store. Part 9's explicit instruction --
"Public Gateway delivery is a consumer of certified engine truth, not a
competing generation system" -- is enforced by construction: this file has
no SQL, no graph traversal, no Director/Game Factory logic of its own.

--- WHY REUSING packages.py's package_id IS ENOUGH FOR A "GAME SESSION" ---
Part 7 asks for a game identifier that prevents obvious tampering "without
unnecessary cryptographic complexity". `package_id` already is exactly
that: a `GGP:<24 hex>` content hash of (spec, seed, ...), validated by
`packages._safe_filename_for_id()`'s strict allowlist regex before any
filesystem use, effectively unguessable (a client would have to find a
real sha256 preimage to forge one), and already has atomic, idempotent
storage. Reusing it here means a public `game_id` and an admin
`package_id` are literally the same identifier space -- no new storage
layer, no new ID scheme, nothing to keep in sync. Re-audited in v1.3 with
multiple modes live (Part 7): `validate_public_answer()` never takes a
client-declared `mode` at all -- the mode is derived entirely from the
loaded package itself, so there is no "declared mode" field for a client
to lie about, and a Draft `game_id` cannot be used to somehow validate a
Championship answer or vice versa (the package loaded IS the puzzle;
there's nothing else to target). See `test_public_game.py`'s
`test_cross_mode_game_id_stays_scoped_to_its_own_mode` for the real check.

--- ANSWER LEAKAGE BOUNDARY ---
`_public_view()` is the ONLY function in this file allowed to shape what a
browser receives for a fresh game, and it is deliberately an allow-list
(only the named fields are copied out), not a deny-list of "strip these
fields" -- a future field added to the internal package shape is excluded
by default, not accidentally leaked. `correctIndex`, `answer`,
`source_ids`, `provenance`, `funnel`, `qa_checks_performed`, and `notes`
are never present in a fresh-game response. `notes` is deliberately only
ever returned from `validate_public_answer()` (after a real guess), never
from `get_public_game()` -- matching the one existing Reads Quiz
convention this pilot borrows (`renderQuizQuestion()` in app.js only shows
`q.notes` once a question has been answered).

--- WHY draft_guess + championship_guess AND NOT EVERY REGISTERED CAPABILITY ---
`config.PUBLIC_MODE_ALLOWLIST` has exactly two entries as of v1.3 (Part 3/33:
explicit, hand-certified allow-list; Part 16/17: Grid and Six Degrees are
NOT migrated in this phase). `player_from_clues` is a real, registered
internal capability (see generation.list_capabilities()) that is
DELIBERATELY not yet public -- requesting it returns MODE_UNAVAILABLE (a
real, recognized capability, just not vetted for direct public delivery
yet), distinct from INVALID_MODE (not a real capability at all).

--- WHY THIS ISN'T A "DraftGuessHandler / ChampionshipGuessHandler" CLASS HIERARCHY ---
Part 30 sketches per-mode handler classes. Both certified modes here are
the SAME internal mechanic shape (`guess` -> Game Factory/adapter ->
4-option multiple choice, `options[correctIndex]`) -- introducing separate
handler classes for two modes with byte-identical fetch/validate logic
would be ceremony with no behavioral difference (Part 30's own "do not
overengineer... for hypothetical future modes" caveat). What actually WAS
Draft-specific coupling in v1.2, and is fixed here: (1) only one registry
entry existed at all, (2) there was no per-mode certified-difficulty check
(a mode's metadata could silently advertise a difficulty band that has
zero real candidates), (3) `/v1/public/modes` returned only
`{mode, competition, title}`, too thin for a client to make a real choice
between modes. `PUBLIC_MODES` entries now carry a `kind` field
(`"multiple_choice"` for both today) specifically so a future mode with a
genuinely different mechanic (e.g. free-text) has a real place to branch
from, without speculative branching code that has no mode to exercise it
yet.
"""
from __future__ import annotations

import collections
import secrets
import time
from typing import Any, Dict, List, Optional

from .. import config
from ..errors import GatewayError
from . import generation, oplog, packages

# --- Cross-Mode Repetition pass -----------------------------------------------
# The lightest mechanism that fits this file's existing, deliberately
# stateless architecture (see the module docstring's "packages.py's
# package_id IS ENOUGH FOR A GAME SESSION" reasoning): a small, bounded,
# in-memory recency window per client_id, tracking real board/entity ids
# (see e.g. cfb_odd_college_out.py's "board:{board_id}" entity_key) across
# EVERY mode that shares the underlying 595-board _group_board_common pool
# (Odd College Out, Spot the Fake Lineup, One School Missing, Three Clues /
# Era Gauntlet, Franchise Marathon's DEEP_CUT stage) -- the concrete real
# overlap the Absolute Final Closeout audit found (see registry.py's own
# comments on that shared pool). NOT returned to the client (entity_key
# values like "board:NFL_TEAM_SEASON:2015:NE" or "board:GOLD_SB_1999" would
# directly leak the correct answer for team/season-guessing modes -- see
# this module's own "ANSWER LEAKAGE BOUNDARY" section above) -- tracked
# server-side only, keyed by the same client_id already established by
# Pick'em's getClientId() convention (app.js). Bounded two ways so this can
# never become a permanent ban list: each client's own window is a
# fixed-size deque (oldest entity simply falls off), and the total number
# of tracked clients is capped (oldest CLIENT evicted once the cap is hit).
# Resets on every deploy (in-memory, not persisted) -- a real, disclosed
# limitation, not fabricated durability.
_RECENT_ENTITY_WINDOW = 30
_MAX_TRACKED_CLIENTS = 20000
_recent_entities_by_client: "collections.OrderedDict[str, collections.deque]" = collections.OrderedDict()


def _recent_entities_for(client_id: str) -> collections.deque:
    dq = _recent_entities_by_client.get(client_id)
    if dq is not None:
        _recent_entities_by_client.move_to_end(client_id)
        return dq
    dq = collections.deque(maxlen=_RECENT_ENTITY_WINDOW)
    _recent_entities_by_client[client_id] = dq
    if len(_recent_entities_by_client) > _MAX_TRACKED_CLIENTS:
        _recent_entities_by_client.popitem(last=False)
    return dq

# The public game contract's own version (Part 31) -- distinct from
# `package_version` (metadata.version below), which is the internal
# Director package SCHEMA version. contract_version only needs to move if
# the shape of THIS response (the fields a client parses) changes in a
# breaking way; nothing has needed that yet, so it starts at 1.
CONTRACT_VERSION = 1

# Public mode id -> (internal Director capability spec, public-facing copy,
# real certified difficulty support). The public mode id is a stable,
# independent vocabulary -- NOT the internal (mechanic, domain,
# relationship_predicate) tuple -- so the public contract never has to
# change shape if internal registry naming changes.
#
# `certified_difficulties`: hand-verified against REAL candidate surveys
# (Part 20/3), never copied from the internal capability registry's
# `supported_difficulties` (which is technically-supported-by-the-adapter-
# code, not empirically-has-real-candidates -- a real, different thing).
# "any" is not listed per-mode because it isn't a difficulty band claim at
# all -- it means "no difficulty filter", which trivially always has
# candidates if the mode has any candidates. Both modes below were
# surveyed directly this phase: 0 "Easy" candidates for either (Draft:
# 0/232 accepted; Championship: 0/296 accepted) -- so "easy" is
# deliberately absent from both, not an oversight.
PUBLIC_MODES: Dict[str, Dict[str, Any]] = {
    "draft_guess": {
        "competition": "NFL",
        "title": "NFL Draft History: Guess the Team",
        "instructions": "You'll be shown a real NFL player. Pick the team that actually drafted him.",
        "kind": "multiple_choice",
        # Absolute Final Closeout fix: "easy" was real-zero at the time this
        # was first certified (the vendored Engine's own band() function
        # never scored this domain low enough), but draft.py's evaluate()
        # now applies a real, defensible difficulty override (round-1
        # top-10 picks; any round-1 pick from season>=2010) -- re-surveyed
        # (target_count=5000): 220 real, distinct, QA-passed Easy
        # candidates. This registry entry had been fixed at the adapter/
        # internal-registry level but never actually certified public here
        # -- caught by cross-checking the live /v1/capabilities response
        # against registry.py, not assumed from memory.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_DRAFT",
            "relationship_predicate": "DRAFTED_BY",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "championship_guess": {
        "competition": "NFL",
        "title": "NFL Playoffs: Guess the Result",
        "instructions": "You'll be shown a real NFL team and season. Pick how their postseason actually ended.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_CHAMPIONSHIP",
            "relationship_predicate": "TEAM_POSTSEASON_RESULT",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Absolute Final Closeout: NFL_SUPER_BOWL was already catalog-verified
    # (LEGACY_PUBLIC_PENDING_REVALIDATION) but never wired to a real public
    # route -- only 24 of 60 real Super Bowls resolved a real team identity
    # before this pass's real-name-based resolution fix (nfl_super_bowl.py),
    # too thin to have been worth exposing. All 60 now resolve; real
    # candidate survey this pass: Easy 18, Medium 12, Hard 30 -- all three
    # bands genuinely represented.
    "nfl_super_bowl_guess": {
        "competition": "NFL",
        "title": "NFL Super Bowl History",
        "instructions": "You'll be shown a real Super Bowl. Pick the team that actually won it.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_SUPER_BOWL",
            "relationship_predicate": "WON_CHAMPIONSHIP",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Added v1.8, Part F/O -- the milestone's primary acceptance-test capability,
    # certified public the same deliberate way Draft/Championship were (Part 33).
    # Real candidate survey this phase, all 412 accepted candidates: Easy 125,
    # Medium 64, Hard 223 -- unlike Draft/Championship, this domain genuinely has
    # "easy" candidates (more recent seasons), so all three bands are certified.
    "lineup_guess": {
        "competition": "NFL",
        "title": "NFL Starting Lineups: Guess the Team",
        "instructions": "You'll be shown a real NFL team's starting offense, by position. Pick the team.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_OFFENSE_LINEUP",
            "relationship_predicate": "TEAM_OF_STARTING_LINEUP",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Added during the production deployment + CFB data enrichment
    # operation -- the FIRST CFB public mode. Real candidate survey this
    # phase, all 91 real Heisman winners accepted, zero rejections: Hard 46,
    # Easy 27, Medium 18 -- all three bands genuinely certified. Proves the
    # exact same public API/registry/answer-validation/frontend-adapter
    # pipeline that already serves 3 NFL modes also serves a genuinely new
    # CFB domain with zero architectural change (the operation's own Phase
    # 14 mandate) -- competition is "CFB" here, everything else about how
    # this mode is fetched/served/validated is byte-identical code to the
    # NFL modes above.
    "cfb_heisman_guess": {
        "competition": "CFB",
        "title": "CFB Heisman Winners: Guess the School",
        "instructions": "You'll be shown a real Heisman Trophy winner and year. Pick the school he played for.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_HEISMAN",
            "relationship_predicate": "WON_HEISMAN",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Added during the App-Wide Engine Migration operation -- the first
    # mode built on a real, automatically-refreshed games table
    # (tools/data_refresh/nfl_games_refresh.py) rather than a one-time
    # import. Real candidate survey: 6,484 of 7,261 candidates (1999-2025)
    # accepted, all three difficulty bands genuinely well-represented
    # (Hard 2,934 / Medium 1,331 / Easy 2,219) -- see
    # tools/director_v02/registry.py's known_limitations for the real,
    # disclosed rejection reason (777 TEAM_UNRESOLVED).
    "nfl_game_result_guess": {
        "competition": "NFL",
        "title": "NFL Game Results: Guess the Winner",
        "instructions": "You'll be shown a real NFL matchup. Pick the team that won.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_GAME_RESULT",
            "relationship_predicate": "WON_GAME",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # The CFB mirror -- same architecture, built on
    # tools/data_refresh/cfb_games_refresh.py's real, automatically-
    # refreshed cfb_games_canonical table. Real candidate survey: 36,184
    # of 36,184 candidates (2002-2025) accepted (100%), all three
    # difficulty bands genuinely well-represented (Easy 19,524 / Medium
    # 7,551 / Hard 9,109).
    "cfb_game_result_guess": {
        "competition": "CFB",
        "title": "CFB Game Results: Guess the Winner",
        "instructions": "You'll be shown a real college football matchup. Pick the team that won.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_GAME_RESULT",
            "relationship_predicate": "WON_GAME",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Historical Engine Enrichment operation: built on the newly-populated
    # team_game_stats table (real per-game team box scores, cross-verified
    # against a known real final score before being trusted -- see
    # tools/data_refresh/nfl_team_game_stats_refresh.py). Genuinely distinct
    # from nfl_game_result_guess -- asks which team gained more total
    # yards, not who won (these frequently differ). Real candidate survey:
    # 5,738 of 7,233 candidates (1999-2025) accepted (1,495 rejected as
    # TEAM_UNRESOLVED, same disclosed pattern as nfl_game_result_guess),
    # all three difficulty bands genuinely well-represented (Easy 2,187 /
    # Medium 1,144 / Hard 2,407).
    # Public-readiness punch-list: the college-identity variant of the
    # lineup board. Was previously safe-but-never-exposed while the real
    # generation-timeout starvation defect for this domain was open (see
    # gateway/services/generation.py's _LINEUP_ISOLATED_DOMAINS docstring
    # for the fix) -- certified public only after that fix was verified.
    # Real candidate survey this pass, out of 412 real team-seasons: 66
    # accepted (Easy 48, Medium 13, Hard 5), 344 rejected as
    # COLLEGE_UNRESOLVED (a real, disclosed data ceiling -- see
    # tools/quiz_export/adapters/lineup_college.py's own module docstring),
    # 3 TEAM_UNRESOLVED, 2 DUPLICATE_QUESTION.
    "lineup_college_guess": {
        "competition": "NFL",
        "title": "NFL Starting Lineups: Guess the Team (By College)",
        "instructions": "You'll be shown a real NFL team's starting offense, by position and college "
                        "(player names hidden). Pick the team.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_OFFENSE_LINEUP_COLLEGE",
            "relationship_predicate": "TEAM_OF_STARTING_LINEUP_BY_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "nfl_game_boxscore_guess": {
        "competition": "NFL",
        "title": "NFL Box Scores: Guess Who Gained More Yards",
        "instructions": "You'll be shown a real NFL matchup. Pick the team that gained more total yards.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_GAME_BOXSCORE",
            "relationship_predicate": "HAD_MORE_YARDS",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Discovery/replayability pass: the first 4 modes promoted out of
    # Creator-only status straight to public certification, following the
    # exact same discipline as every mode above -- a real candidate survey
    # run directly against generate_package_from_spec() (the identical
    # function real gameplay uses, not a re-derivation) at target_count=5000
    # per difficulty band, results in tools/director_v02/ (see this
    # operation's own notes for the raw counts). Only bands with real,
    # nonzero, QA-passed candidates are ever listed in
    # certified_difficulties -- never assumed from supported_difficulties.
    "offense_college_guess": {
        "competition": "NFL",
        "title": "NFL Offense by College: Guess the Team",
        "instructions": "You'll be shown a real, current NFL team's starting offense by college and "
                        "position (player names hidden). Pick the team.",
        "kind": "multiple_choice",
        # Real survey: 32 total (Easy 8 / Medium 19 / Hard 5) -- all three
        # bands genuinely represented, all real, current (2026) team-seasons.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_OFFENSE_COLLEGE_CURATED",
            "relationship_predicate": "TEAM_OF_CURRENT_OFFENSE_BY_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "sb_champion_offense_college_guess": {
        "competition": "NFL",
        "title": "Super Bowl Champions: Guess the Team by College",
        "instructions": "You'll be shown a real Super Bowl-winning offense by college and position "
                        "(player names hidden). Pick the team and season.",
        "kind": "multiple_choice",
        # Real survey: 52 total (Easy 31 / Medium 21 / Hard 0) -- "hard"
        # deliberately absent, same discipline as draft_guess/
        # championship_guess excluding a real-zero band rather than
        # guessing at one.
        "certified_difficulties": frozenset({"easy", "medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
            "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_ranking_guess": {
        "competition": "CFB",
        "title": "CFB Rankings: Guess the Team",
        "instructions": "You'll be shown a real AP Top 25 ranking snapshot. Pick the team that held that rank.",
        "kind": "multiple_choice",
        # Real survey: 4,978 total (Easy 881 / Medium 1,404 / Hard 2,663) --
        # all three bands genuinely well-represented.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_RANKING",
            "relationship_predicate": "RANKED_IN_POLL",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_upset_guess": {
        "competition": "CFB",
        "title": "CFB Upsets: Guess the Winner",
        "instructions": "You'll be shown a real college football matchup where the AP-ranked team lost. "
                        "Pick the team that pulled off the upset.",
        "kind": "multiple_choice",
        # Real survey: 1,044 total (Easy 146 / Medium 154 / Hard 724) -- all
        # three bands genuinely well-represented. RANKING_UPSET only (not
        # its BETTING_UPSET sibling) -- the plainer, more universally
        # understood "upset" definition for a first public certification.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_UPSET",
            "relationship_predicate": "RANKING_UPSET",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # ======================================================================
    # Public Mode Wiring pass (Pass 2.5): the 7 real backend capabilities
    # audited in the prior pass (Reads Game Screen Visual Identity) that
    # already existed as real, tested Director/Creator adapters but were
    # never reachable through the public API. Each entry below was verified
    # via a real candidate survey run directly against
    # generation.generate_public() -- the exact function this file's own
    # get_public_game() calls -- at 12 seeds per difficulty band, not
    # assumed from reading adapter code. See this pass's own report for the
    # full counts. Every `filters`/`certified_difficulties` value here is
    # the one that survey actually measured, same discipline as every
    # mode above.
    # Section 11 finding, fixed rather than left as a genuine gap: a
    # generic "something about rivalries" NL request (no "trivia"/"game"
    # keyword) deliberately routes to this SMALLER, real, separately-
    # registered capability (CFB_RIVALRY/RIVAL_OF, 48 real named rivalries,
    # 96 real question directions -- see mock.py's own has_rivalry_word/
    # has_trivia_word/has_game_word branching) rather than the richer
    # CFB_RIVALRY_TRIVIA bank above -- that branch point already existed
    # and is by design, not something this pass should rewire. Making this
    # capability ALSO public (not just cfb_rivalry_guess) is what actually
    # closes the gap: verified directly, "Make me something about
    # rivalries" now resolves to a spec that matches this real mode.
    "cfb_rivalry_lookup_guess": {
        "competition": "CFB",
        "title": "CFB Rivalries: Name the Rival",
        "instructions": "You'll be shown a real school. Pick its real, named rivalry opponent.",
        "kind": "multiple_choice",
        # Real survey: 48 real rivalries (96 real question directions),
        # medium-only -- the adapter itself fixes difficulty at Medium for
        # every question (no real recency axis exists for a standing
        # rivalry fact); "easy"/"hard" correctly return 0 real candidates.
        "certified_difficulties": frozenset({"medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_RIVALRY",
            "relationship_predicate": "RIVAL_OF",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_rivalry_guess": {
        "competition": "CFB",
        "title": "CFB Rivalries",
        "instructions": "You'll be shown a real question from a real, named CFB rivalry (Iron Bowl, "
                        "Civil War, and more). Pick the correct answer.",
        "kind": "multiple_choice",
        # Player Experience pass, real fix: this mode's own instructions
        # already promised "a real question from a real, named CFB
        # rivalry" -- but the spec below had no rivalry_only filter, so it
        # actually drew from the FULL 1,272-row curated bank (860 real
        # rivalry rows + 412 real GENERAL category rows -- Heisman Trophy,
        # National Championships, Coaches, Records & Stats, and more,
        # nothing to do with any specific rivalry). Scoped to
        # rivalry_only=True (cfb_rivalry_trivia.py's own existing, already-
        # wired filter key) so a real "Who won the Heisman in 1985?"
        # question can no longer surface in a mode advertised as rivalry-
        # specific. Real, measured pool after scoping: 846 candidates (77
        # Easy, 0 Medium, 769 Hard) -- "medium" removed from certified
        # difficulties below rather than declared and silently returning
        # empty, same discipline this project follows for every other
        # real-zero band (the rivalry-only source rows are only ever
        # Hard/Very Hard, plus the 83 Medium-and-named-rivalry rows already
        # promoted to Easy -- nothing left in the middle).
        "certified_difficulties": frozenset({"easy", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_RIVALRY_TRIVIA",
            "relationship_predicate": "CORRECT_TRIVIA_ANSWER",
            "question_count": 1,
            "filters": {"rivalry_only": True},
            "exclusions": [],
        },
    },
    # MASTER WORKBOOK ingestion pass: CFB_2026_CURRENT_ROSTER made public.
    # Real, disclosed scope limit carried into the instructions themselves
    # (not hidden) -- only 8 of 136 real FBS programs have recoverable
    # 2026 roster data (see tools/data_refresh/cfb_2026_roster_workbook_import.py's
    # own module docstring for why). Real, measured pool: 637 candidates,
    # 100% Medium (the adapter itself has no other difficulty branch) --
    # "easy"/"hard" correctly return 0 real candidates, so only "medium"
    # is certified rather than declared and silently returning empty.
    "cfb_2026_roster_guess": {
        "competition": "CFB",
        "title": "CFB 2026 Roster",
        "instructions": "You'll be shown a real player's position, class, and hometown from a real 2026 "
                        "roster (Alabama, Auburn, Georgia Tech, Kansas, Oregon, Texas, UCLA, or USC). "
                        "Guess his real team.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_2026_CURRENT_ROSTER",
            "relationship_predicate": "ON_2026_ROSTER",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Power 4 Coverage Closeout workbook: CFB_2026_HEAD_COACH made public.
    # Real, measured pool: 67 candidates (one per real Power 4 team), 100%
    # Medium (the adapter itself has no other difficulty branch).
    "cfb_2026_coach_guess": {
        "competition": "CFB",
        "title": "CFB 2026 Head Coaches",
        "instructions": "You'll be shown a real 2026 Power 4 head coach's name. Guess his real team.",
        "kind": "multiple_choice",
        "certified_difficulties": frozenset({"medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_2026_HEAD_COACH",
            "relationship_predicate": "COACHES_TEAM_2026",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_spot_the_fake_guess": {
        "competition": "CFB",
        "title": "Spot the Fake",
        "instructions": "You'll be shown a real starting lineup by position and college -- except one "
                        "slot's college has been swapped for a different, wrong school. Find the fake.",
        "kind": "multiple_choice",
        # Real survey: 203/196/196 real, distinct, QA-passed candidates at
        # easy/medium/hard respectively (target_count=5000 direct survey
        # against generate_package_from_spec(), Reliability pass/Pass 2.6).
        # Hard was wrongly excluded in Pass 2.5 -- that pass's own comment
        # here diagnosed it as "the shared Director pipeline's difficulty-
        # targeted search doesn't reliably surface a real Hard board...
        # within its bounded retry budget." That diagnosis was wrong: there
        # is no bounded-search issue in generate_package_from_spec() at all
        # (it evaluates every real candidate, then filters by difficulty --
        # confirmed by reading it). The actual cause was one level up:
        # tools/director_v02/registry.py's CFB_SPOT_THE_FAKE_LINEUP entry
        # hardcoded supported_difficulties={"any","easy","medium"} (a stale
        # value copy-pasted from before this domain's board pool was
        # expanded from a 60-board SB_CHAMPION-only source with genuinely
        # zero real Hard boards to today's 595-board 5-source pool). That
        # registry-level gate rejected difficulty="hard" as
        # UNDERSTOOD_BUT_UNSUPPORTED before generation ever ran -- which
        # looks identical to a generation failure from the caller's side
        # (both surface as "no eligible question"), but is a completely
        # different bug with a completely different fix. Corrected in
        # registry.py this pass; certified here to match.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_SPOT_THE_FAKE_LINEUP",
            "relationship_predicate": "ALTERED_POSITION",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_three_clues_guess": {
        "competition": "CFB",
        "title": "Three Clues, One Champion",
        "instructions": "You'll be given clues about a real NFL team's season one at a time -- real "
                        "opponent, score, coach, MVP, season record, or college. Guess the team and season.",
        "kind": "multiple_choice",
        # Era Gauntlet rebuild (Pass 2.7): this domain no longer draws only
        # from the 60 real SB_CHAMPION boards -- it now spans 502 real
        # team-seasons (SB_CHAMPION + CURRENT_TEAM_2026 +
        # NFL_TEAM_SEASON_ROSTER; see cfb_three_clues_one_champion.py's own
        # module docstring). Real per-difficulty survey (target_count=5000,
        # this pass's own methodology): 171 real, distinct Easy / 164 real,
        # distinct Medium / 164 real, distinct Hard candidates, all
        # qa_status PASSED -- unlike the old 60-board SB_CHAMPION-only pool,
        # this wider pool genuinely has real Hard-band candidates (the
        # NFL_TEAM_SEASON_ROSTER source's own difficulty scoring spans all
        # three bands by season recency).
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_THREE_CLUES_ONE_CHAMPION",
            "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Era Gauntlet: Pass 2.5 found and fixed a real bug (see
    # generation.generate_public()'s own docstring) -- the public route's
    # hardcoded puzzle_count=1 could only ever surface stage 0 forever, no
    # matter the seed. Fixed by threading a real `stage_index` (see
    # get_public_game()) through to generate_public()'s now-real
    # `puzzle_count` parameter.
    #
    # Era Gauntlet rebuild (Pass 2.7): the underlying adapter used to only
    # ever have real Super Bowl champions to choose from (100% Super Bowl
    # content, one per real represented decade) -- not a deliberate design,
    # just the only real pool cfb_three_clues_one_champion.py imported. It
    # now draws from 502 real team-seasons (SB_CHAMPION + CURRENT_TEAM_2026
    # + NFL_TEAM_SEASON_ROSTER -- see that module's own docstring), so a
    # real 7-era run is now typically mostly REAL non-champion team-seasons
    # (real record, real coach, real college facts) with real champions
    # appearing as one real possibility among many per era, not the only
    # one. Deliberately "any"-difficulty only (certified_difficulties left
    # empty): difficulty filtering happens on the flat accepted-candidates
    # list BEFORE the era-ordering is re-applied, which could silently drop
    # an era and shift every later stage_index to the wrong era -- not
    # worth the risk for a mode whose whole point is "the real fixed
    # history," not a difficulty-scoped subset.
    "era_gauntlet_guess": {
        "competition": "CFB",
        "title": "Era Gauntlet",
        "instructions": "Progress through real NFL history -- one real team's season from each "
                        "represented decade (a real champion, current team, or historical roster), "
                        "oldest era first.",
        "kind": "multiple_choice",
        "sequential": True,
        "certified_difficulties": frozenset(),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_THREE_CLUES_ONE_CHAMPION",
            "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES",
            "question_count": 1,
            "filters": {"era_gauntlet": True},
            "exclusions": [],
        },
    },
    "cfb_odd_college_out_guess": {
        "competition": "CFB",
        "title": "Odd College Out",
        "instructions": "You'll be shown four real colleges. Three were part of the same real group "
                        "(a championship roster, a draft class, an All-Pro class). Find the one that wasn't.",
        "kind": "multiple_choice",
        # Real survey: 203/196/196 real, distinct, QA-passed candidates at
        # easy/medium/hard (target_count=5000 direct survey, Pass 2.6). Hard
        # was wrongly excluded in Pass 2.5, whose comment here blamed "the
        # shared Director pipeline's difficulty-targeted search" -- the real
        # cause (see cfb_spot_the_fake_guess's comment for the full
        # diagnosis) was a stale registry.py supported_difficulties
        # allowlist rejecting hard before generation ever ran. Corrected in
        # registry.py this pass. Draws from all 5 real _group_board_common.py
        # sources (SB_CHAMPION, CURRENT_TEAM_2026, real team-season rosters,
        # real Round-1 draft classes, real First-Team All-Pro classes) --
        # that real variety is preserved, not narrowed back to
        # SB_CHAMPION-only.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_ODD_COLLEGE_OUT",
            "relationship_predicate": "IMPOSTOR_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    "cfb_one_school_missing_guess": {
        "competition": "CFB",
        "title": "One School Missing",
        "instructions": "You'll be shown most of a real group's colleges. Pick the real one that's missing.",
        "kind": "multiple_choice",
        # Real survey: 203/196/196 real, distinct, QA-passed candidates at
        # easy/medium/hard (target_count=5000 direct survey, Pass 2.6), with
        # ZERO duplicate questions across all three bands (the cleanest
        # survey result of all 8 new modes). Hard was wrongly excluded in
        # Pass 2.5 -- see cfb_spot_the_fake_guess's comment for the full
        # diagnosis (a stale registry.py supported_difficulties allowlist,
        # not a real data or search-reliability problem; corrected in
        # registry.py this pass). Same 5 real sources as
        # cfb_odd_college_out_guess. Confirmed (correcting an earlier
        # assumption in this project's own history): this is a real
        # GROUP-MEMBERSHIP question ("which college was NOT part of this
        # group"), not an ordered transfer-path/sequence -- the UI uses a
        # grouped-card display, not a sequence/path visual.
        "certified_difficulties": frozenset({"easy", "medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_ONE_SCHOOL_MISSING",
            "relationship_predicate": "MISSING_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Franchise Marathon (Closeout pass, Part 3 rebuild): no longer a filter
    # over NFL_SB_CHAMPION_OFFENSE_COLLEGE -- a real 8-stage progression
    # (identity/season-record/coach/draft/award/playoffs/roster/deep-cut)
    # over franchise_marathon.py's own adapter. Super Bowl content now
    # appears in exactly ONE stage (deep-cut), never the whole mode. Same
    # real `stage_index` + `caller_filter_key: "franchise_name"` mechanism
    # as before; "any"-difficulty only, since difficulty is determined by
    # stage position (built into the adapter), not caller-selectable.
    "franchise_marathon_guess": {
        "competition": "NFL",
        "title": "Franchise Marathon",
        "instructions": "Pick a real NFL franchise and play through 8 real stages of its history -- "
                        "identity, season records, coaches, draft picks, awards, playoff runs, roster "
                        "history, and (for champions) one Super Bowl deep-cut.",
        "kind": "multiple_choice",
        "sequential": True,
        "caller_filter_key": "franchise_name",
        "certified_difficulties": frozenset(),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_FRANCHISE_MARATHON",
            "relationship_predicate": "FRANCHISE_MARATHON_STAGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
}

# Real, registered internal capabilities (generation.list_capabilities())
# that are NOT on the public allow-list -- used only to give an honest
# MODE_UNAVAILABLE instead of a misleading INVALID_MODE for a mode id a
# caller might reasonably expect to exist. Kept as literal, hand-verified
# strings (not derived from the registry) so this file never accidentally
# expands the public surface just because a new internal capability ships.
KNOWN_NOT_YET_PUBLIC_MODES = frozenset({"player_from_clues"})

assert set(PUBLIC_MODES) == config.PUBLIC_MODE_ALLOWLIST, (
    "PUBLIC_MODES and config.PUBLIC_MODE_ALLOWLIST have drifted apart -- these must name the same modes."
)

MAX_GAME_FETCH_ATTEMPTS = 5  # bounded retry for the exclude-recent-repeats loop (Part 27) -- never unbounded

# relationship_predicate -> public mode id -- built once from PUBLIC_MODES
# so validate_public_answer() can report `mode` in its telemetry event
# (Part 17) without needing a `mode` parameter from the client (Part 7:
# there deliberately isn't one). Keyed by relationship_predicate ALONE,
# not the (domain, predicate) pair the request spec uses -- a real
# mismatch found by actually inspecting a generated package, not assumed:
# the VALIDATED/stored `parsed_spec` (game_director_v01's output) never
# contains a `domain` key at all -- the validator normalizes it away into
# `entity_type`/`competition_id`/`object_type` instead. `relationship_
# predicate` is the one field that survives unchanged and is already
# unique per certified mode (DRAFTED_BY vs. TEAM_POSTSEASON_RESULT), so it
# alone is a safe, real lookup key -- re-verified directly against a real
# generated package's actual `parsed_spec` shape.
_MODE_BY_PREDICATE: Dict[str, List[str]] = {}
for _mode_id, _entry in PUBLIC_MODES.items():
    _MODE_BY_PREDICATE.setdefault(_entry["spec"]["relationship_predicate"], []).append(_mode_id)
del _mode_id, _entry


def _mode_for_package(stored: dict) -> Optional[str]:
    """Telemetry-only lookup (Part 17) -- never used for grading (that's
    always mode-agnostic options[correctIndex], see validate_public_answer's
    own docstring). Public Mode Wiring pass: two real (domain, predicate)
    collisions now exist -- franchise_marathon_guess reuses
    sb_champion_offense_college_guess's, era_gauntlet_guess reuses
    cfb_three_clues_guess's -- same real capability, a different real
    filter, so a plain predicate->mode dict would silently let one clobber
    the other's telemetry label. Disambiguated by the one real, observable
    fact available: a fixed-filter mode's OWN declared spec['filters'] is
    compared directly against the stored package's actual filters (exact
    match); a caller-filter mode (franchise_marathon_guess) is matched by
    its declared caller_filter_key's presence instead, since its real
    filter VALUE varies per request and can never equal a fixed template."""
    spec = stored.get("parsed_spec") or {}
    candidates = _MODE_BY_PREDICATE.get(spec.get("relationship_predicate")) or []
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    filters = spec.get("filters") or {}
    for mode_id in candidates:
        entry = PUBLIC_MODES[mode_id]
        key = entry.get("caller_filter_key")
        if key and key in filters:
            return mode_id
    for mode_id in candidates:
        entry = PUBLIC_MODES[mode_id]
        if not entry.get("caller_filter_key") and (entry["spec"].get("filters") or {}) == filters:
            return mode_id
    return candidates[0]


def list_public_modes() -> List[dict]:
    """Part 19: client-safe mode discovery. Only ever the fields a client
    needs to make a real choice (which mode, what difficulties actually
    work, what kind of gameplay to render) -- never internal source
    tables, answer truth, or QA/admin detail (Part 13). `available` reflects
    BOTH production rollout controls (Part 10/11: the master
    PUBLIC_GAME_ENABLED switch and the per-mode READS_PUBLIC_MODES
    narrowing) -- a client can build an honest "currently unavailable" UI
    from this alone, without needing to first attempt a fetch and parse an
    error."""
    modes_currently_allowed = config.public_modes_allowed()
    return [
        {
            "mode": mode_id,
            "competition": entry["competition"],
            "title": entry["title"],
            "kind": entry["kind"],
            "difficulties": sorted(entry["certified_difficulties"]) + ["any"],
            "available": config.PUBLIC_GAME_ENABLED and mode_id in modes_currently_allowed,
        }
        for mode_id, entry in PUBLIC_MODES.items()
    ]


def _ensure_public_gameplay_enabled() -> None:
    """Part 10: the master operator kill switch, checked before anything
    else -- one env var (READS_PUBLIC_GAME_ENABLED=false) takes every
    public mode down with a clean, structured response, no redeploy."""
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_game_mode_disabled", mode=None, reason="master_switch_off")
        raise GatewayError(
            "SERVICE_UNAVAILABLE",
            "Public gameplay is currently disabled.",
        )


def _ensure_mode_public(mode: str) -> dict:
    _ensure_public_gameplay_enabled()
    if mode in PUBLIC_MODES:
        if mode not in config.public_modes_allowed():
            # Part 11: code-certified but currently rolled back via
            # READS_PUBLIC_MODES -- the client-facing meaning is identical
            # to MODE_UNAVAILABLE ("not offered right now"), regardless of
            # whether that's a permanent code decision or a temporary ops
            # one, so it reuses the same code rather than inventing a
            # distinction no client actually needs to act on differently.
            oplog.record_event("public_game_mode_disabled", mode=mode, reason="mode_narrowed")
            raise GatewayError(
                "MODE_UNAVAILABLE",
                f"mode={mode!r} is temporarily unavailable.",
            )
        return PUBLIC_MODES[mode]
    if mode in KNOWN_NOT_YET_PUBLIC_MODES:
        raise GatewayError(
            "MODE_UNAVAILABLE",
            f"mode={mode!r} is a real Reads Engine capability but is not yet available through the "
            f"public API.",
        )
    raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized mode.")


def _ensure_difficulty_certified(mode: str, entry: dict, difficulty: Optional[str]) -> None:
    """Part 20/21: reject an uncertified difficulty request BEFORE burning
    real generation attempts on it. Real bug this fixes (found empirically,
    not assumed): requesting difficulty="easy" for draft_guess in v1.2
    silently spent all 5 retry attempts (each a real Engine DB round-trip)
    only to land on NO_ELIGIBLE_GAME every time, because "easy" has zero
    real candidates for this mode -- a fact known in advance, not something
    that needs re-discovering per request. "any" always passes: it isn't a
    difficulty-band claim, it's "no filter", which trivially works if the
    mode has any real candidates at all."""
    if difficulty is None or difficulty == "any":
        return
    if difficulty in entry["certified_difficulties"]:
        return
    raise GatewayError(
        "INVALID_REQUEST",
        f"mode={mode!r} does not have certified {difficulty!r}-difficulty candidates. "
        f"Certified difficulties: {sorted(entry['certified_difficulties'])} (plus 'any').",
    )


def _public_view(mode: str, entry: dict, stored: dict) -> dict:
    """The ONE place allowed to decide what a browser sees for a fresh
    game. Allow-list, not a deny-list -- see module docstring."""
    q = stored["questions"][0]
    return {
        "game_id": stored["package_id"],
        "mode": mode,
        "competition": entry["competition"],
        "difficulty": q.get("difficulty"),
        # Public Mode Wiring pass: this used to read stored.get("game_title")/
        # ("game_instructions") -- the underlying package's own generic,
        # domain-derived title. That was silently correct for the first 12
        # public modes (each one the ONLY public mode on its domain/predicate)
        # but broke the instant two modes legitimately share a domain
        # (era_gauntlet_guess reuses cfb_three_clues_guess's
        # CFB_THREE_CLUES_ONE_CHAMPION/TEAM_SEASON_FROM_THREE_CLUES): a real
        # fetch of era_gauntlet_guess came back titled "Three Clues, One
        # Champion" instead of "Era Gauntlet", caught only by actually
        # calling this route, not by reading the code. entry["title"]/
        # entry["instructions"] are this mode's own declared identity (the
        # same source list_public_modes() already uses) and are correct
        # for every mode, shared-domain or not.
        "title": entry["title"],
        "instructions": entry["instructions"],
        "payload": {
            "prompt": q["question"],
            "options": list(q["options"]),
            # v1.8, Part D/E: still an allow-list, not a deny-list (module
            # docstring) -- `visual_payload` here is the SAME data every
            # option/prompt field already is: the puzzle's own given
            # information (e.g. player names on a lineup board), never the
            # answer. Defaults match game_director_v01.py's own defaults so a
            # pre-v1.8 mode (Draft/Championship) is unaffected.
            "visual_template": q.get("visual_template", "DEFAULT_MULTIPLE_CHOICE"),
            "visual_payload": q.get("visual_payload"),
        },
        "metadata": {
            "seed": (stored.get("_diagnostics") or {}).get("seed"),
            "version": stored.get("package_version"),
            "contract_version": CONTRACT_VERSION,
        },
    }


def get_public_game(*, mode: str, difficulty: Optional[str], seed: Optional[str],
                     exclude_game_ids: Optional[List[str]],
                     stage_index: Optional[int] = None,
                     filter_value: Optional[str] = None,
                     client_id: Optional[str] = None) -> dict:
    t0 = time.perf_counter()
    entry = _ensure_mode_public(mode)
    _ensure_difficulty_certified(mode, entry, difficulty)
    exclude = set(exclude_game_ids or [])
    recent_entities = _recent_entities_for(client_id) if client_id else None
    attempts_used = 0

    # Public Mode Wiring pass: Franchise Marathon / Era Gauntlet real fix.
    # `stage_index` is only accepted for a mode whose PUBLIC_MODES entry
    # declares `"sequential": True` -- every other mode's call_spec/
    # puzzle_count below is byte-identical to before this change.
    if stage_index is not None and not entry.get("sequential"):
        raise GatewayError("INVALID_REQUEST", f"mode={mode!r} does not support stage_index.")
    if filter_value is not None and not entry.get("caller_filter_key"):
        raise GatewayError("INVALID_REQUEST", f"mode={mode!r} does not accept a caller-supplied filter.")

    # A real bug caught by actually calling this (not assumed from reading
    # the pipeline code): the Director validator requires `difficulty`
    # INSIDE the spec dict itself -- the separate `difficulty=` kwarg to
    # generation.generate() is applied too late to satisfy that check.
    # Confirmed directly: the same spec without this field fails validation
    # with "spec is missing required fields: ['difficulty']" before
    # generation ever runs.
    call_spec = dict(entry["spec"])
    call_spec["difficulty"] = difficulty or "any"
    if filter_value is not None:
        # e.g. entry["caller_filter_key"] == "franchise_name" -- the ONE
        # caller-controlled key this mode declared support for; every other
        # filter on this spec (if any) stays exactly as PUBLIC_MODES wrote
        # it, never caller-overridable.
        call_spec["filters"] = dict(call_spec.get("filters") or {})
        call_spec["filters"][entry["caller_filter_key"]] = filter_value
    puzzle_count = (stage_index + 1) if stage_index is not None else 1

    stored = None
    last_eligible = None  # most recent QA-passed, non-empty result, even if it's in the exclude set
    for attempt in range(MAX_GAME_FETCH_ATTEMPTS):
        # A caller-pinned seed is honored exactly once, never silently
        # replaced -- Part 26 (determinism) outranks Part 27 (avoid
        # immediate repeats) when they conflict. Without a pinned seed,
        # each attempt gets a fresh random seed so a real exclude list can
        # actually find a different real question.
        attempts_used = attempt + 1
        real_seed = seed if (seed and attempt == 0) else secrets.token_hex(8)
        # Public Mode Wiring pass: package_id is a hash of (request_text,
        # seed, predicate, package_version) ONLY (see game_director_v01.py) --
        # target_count/puzzle_count and filters are NOT part of it. Two
        # different stage_index requests with the same real_seed would
        # therefore compute the IDENTICAL package_id while trimming to
        # DIFFERENT real content, which packages.save_package() correctly
        # detects and rejects as a collision (caught by actually calling
        # this, not assumed). Folding stage_index into the seed used for
        # generation gives each stage its own real package_id -- safe
        # because neither sequential adapter's real candidate ORDER depends
        # on the seed (franchise_name sorts by real season; era_gauntlet's
        # per-era slot is keyed by real era start-year), only which
        # DISTRACTORS get picked -- so which real season/era occupies a
        # given stage_index never changes, only its wrong-answer options.
        gen_seed = f"{real_seed}:stage{stage_index}" if stage_index is not None else real_seed
        # v1.6, Part A: the public-only bounded-concurrency path (its own
        # worker pool, sized well above 1) -- not generation.generate(), the
        # single-slot admin path. Never called with arbitrary caller
        # input -- call_spec always comes from this module's own certified
        # PUBLIC_MODES templates, never from the request body directly.
        result = generation.generate_public(
            spec=call_spec, difficulty=difficulty, seed=gen_seed, puzzle_count=puzzle_count,
        )
        # Real bug caught by actually running Part 25's pilot-data
        # verification, not assumed from reading the code: game_director_v01
        # sets qa_status "PASSED" whenever contract_failures is empty --
        # which is also true when `questions` is EMPTY (nothing to fail
        # validation), e.g. a narrow difficulty filter matching zero
        # candidates for this particular seed's small deterministic sample.
        # Treating that as eligible caused an IndexError in _public_view's
        # `stored["questions"][0]`. One unlucky seed isn't a hard failure --
        # retry with another seed, same as any other ineligible attempt.
        eligible = bool(result.get("package_id")) and result.get("qa_status") == "PASSED" and result.get("questions")
        if not eligible:
            if seed and attempt == 0:
                # The caller's pinned seed genuinely isn't eligible --
                # don't silently swap in a different seed than the one
                # explicitly requested (Part 26 determinism).
                break
            continue
        # Public Mode Wiring pass: a sequential mode's real stage count is
        # a property of the DATA (how many real titles a franchise has;
        # how many real eras are represented), not the seed -- retrying
        # with a different seed cannot manufacture a stage that doesn't
        # exist. Real, honest "you reached the end" outcome, raised
        # immediately rather than burned through retry attempts.
        if stage_index is not None and len(result["questions"]) <= stage_index:
            oplog.record_event(
                "public_game_sequence_complete", mode=mode, difficulty=difficulty or "any",
                generation_attempts=attempts_used, latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            )
            raise GatewayError(
                "SEQUENCE_COMPLETE",
                f"mode={mode!r} has {len(result['questions'])} real stage(s) for this "
                f"selection -- stage_index={stage_index} is past the end.",
                extra={"stage_count": len(result["questions"])},
            )
        if stage_index is not None:
            # Trim down to exactly the one real question at stage_index --
            # everything downstream (_public_view, packages.save_package,
            # validate_public_answer) keeps its existing "one package_id =
            # one question" invariant unchanged.
            result = dict(result)
            result["questions"] = [result["questions"][stage_index]]
        last_eligible = result
        # Cross-Mode Repetition pass: same "meaningless for a sequential
        # mode" carve-out the exclude_game_ids docstring above already
        # establishes -- Franchise Marathon/Era Gauntlet stages are a real,
        # intentionally-ordered progression, so entity recency (which would
        # try to skip to a DIFFERENT stage_index's answer) is never checked
        # when stage_index is set.
        entity_key = None
        if recent_entities is not None and stage_index is None:
            entity_key = result["questions"][0].get("entity_key")
        if result["package_id"] not in exclude and (entity_key is None or entity_key not in recent_entities):
            stored = result
            break
    if stored is None:
        if last_eligible is None:
            oplog.record_event(
                "public_game_no_eligible", mode=mode, difficulty=difficulty or "any",
                generation_attempts=attempts_used, latency_ms=round((time.perf_counter() - t0) * 1000, 3),
            )
            raise GatewayError(
                "NO_ELIGIBLE_GAME",
                f"No QA-passed question could be generated for mode={mode!r} right now.",
            )
        # Every eligible attempt landed on an excluded game_id -- real,
        # honest outcome for a very small eligible pool, not an
        # infrastructure failure.
        stored = last_eligible

    if recent_entities is not None:
        # Recorded even for a sequential (stage_index) request -- a
        # Franchise Marathon DEEP_CUT stage still occupies a real board
        # from the exact same shared pool, and a LATER non-sequential mode
        # call in this session should know to avoid repeating it, even
        # though the sequential mode's own retry loop above never consults
        # recent_entities to pick which stage it serves.
        served_entity_key = stored["questions"][0].get("entity_key")
        if served_entity_key is not None:
            recent_entities.append(served_entity_key)

    saved = packages.save_package(stored)
    view = _public_view(mode, entry, saved)
    oplog.record_event(
        "public_game_served", mode=mode, difficulty=view["difficulty"],
        generation_attempts=attempts_used, latency_ms=round((time.perf_counter() - t0) * 1000, 3),
    )
    return view


def validate_public_answer(*, game_id: str, answer: str) -> dict:
    """Part 6/32: one shared validator for every public mode -- there is no
    per-mode branch here because every certified mode today shares the same
    `options[correctIndex]` label shape (Part 30's docstring explains why
    that means no handler classes are needed yet). Normalization
    (strip + case-fold exact match) is mode-agnostic by construction: it
    compares whatever label string the mode's own generator put in
    `options`, never a hand-maintained alias table in this file or in the
    browser. No `mode` parameter is accepted from the client at all -- the
    mode is implied entirely by which package `game_id` resolves to, which
    is also why cross-mode tampering has no surface here (Part 7).

    Part 10: also honors the master kill switch -- a real emergency
    shutdown should stop answer submission too, not just leave already-
    in-flight games playable while new ones can't be fetched."""
    _ensure_public_gameplay_enabled()
    try:
        stored = packages.load_package(game_id)
    except packages.PackageIdInvalid:
        stored = None
    if not stored:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    t0 = time.perf_counter()
    q = stored["questions"][0]
    norm = answer.strip().lower()
    correct_label = q["options"][q["correctIndex"]]
    is_correct = norm == correct_label.strip().lower() or norm == str(q.get("answer", "")).strip().lower()
    oplog.record_event(
        "public_answer_submitted", mode=_mode_for_package(stored), correct=is_correct,
        latency_ms=round((time.perf_counter() - t0) * 1000, 3),
        # Never the raw `answer` string itself (Part 17: "avoid logging raw
        # free-text answers") -- only whether it was right.
    )
    return {
        "correct": is_correct,
        "canonical_answer": correct_label,
        # Matches existing Quiz semantics (app.js renderQuizQuestion): the
        # correct answer -- and any notes -- are only ever revealed AFTER a
        # real guess, never in the initial game payload.
        "notes": q.get("notes") or None,
    }
