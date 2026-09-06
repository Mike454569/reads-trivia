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

import secrets
import time
from typing import Any, Dict, List, Optional

from .. import config
from ..errors import GatewayError
from . import generation, oplog, packages

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
        "certified_difficulties": frozenset({"medium", "hard"}),
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
        # Real survey: 12/12 eligible at medium and hard, 0/12 at easy (the
        # source workbook has no "Easy" rows at all -- disclosed in
        # cfb_rivalry_trivia.py's own known_limitations). Uses the richer,
        # 1,272-question curated trivia bank (43 real named rivalry packs)
        # rather than the smaller 48-rivalry RIVAL_OF-only capability --
        # "Which school is X's rival" is one of many real question types
        # this bank asks, not the only one (Section 4's own instruction).
        "certified_difficulties": frozenset({"medium", "hard"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_RIVALRY_TRIVIA",
            "relationship_predicate": "CORRECT_TRIVIA_ANSWER",
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
        # Real survey: 12/12 eligible at easy and medium. Hard excluded --
        # corrected during this pass's own browser QA, which caught an
        # earlier version of this comment claiming "the shared curated
        # board pool has zero real HARD boards." That was false: a direct
        # count against _group_board_common.fetch_all_boards() found 196
        # real Hard-labeled boards (of 595 total, across CURRENT_TEAM_2026/
        # DRAFT_CLASS/HONOR_GROUP/NFL_TEAM_SEASON_ROSTER). The real reason
        # hard stays uncertified: an explicit difficulty="hard" request to
        # generation.generate_public() for this mode was directly tested
        # (3 real attempts, 3 different seeds) and failed every time with
        # "No QA-passed question could be generated" -- the shared Director
        # pipeline's difficulty-targeted search doesn't reliably surface a
        # real Hard board for this domain within its bounded retry budget,
        # even though Hard content exists and does surface under "any" (no
        # filter). Fixing that search is a shared-pipeline change, out of
        # this pass's scope (wiring, not rebuilding, existing capability).
        "certified_difficulties": frozenset({"easy", "medium"}),
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
        "instructions": "You'll be given a real Super Bowl champion's clues one at a time -- opponent, "
                        "score, coach, MVP, or college. Guess the team and season.",
        "kind": "multiple_choice",
        # Real survey: 12/12 eligible at easy and medium (0 duplicate
        # questions), 0/12 at hard (same real-zero-HARD-band ceiling as the
        # shared curated board pool).
        "certified_difficulties": frozenset({"easy", "medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_THREE_CLUES_ONE_CHAMPION",
            "relationship_predicate": "TEAM_SEASON_FROM_THREE_CLUES",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Era Gauntlet: real bug found and fixed this pass (see
    # generation.generate_public()'s own docstring) -- the underlying
    # adapter already correctly returns exactly 7 real champions, one per
    # real represented decade (1960s-2020s), in real oldest-first order,
    # but the public route's hardcoded puzzle_count=1 could only ever
    # surface stage 0 forever, no matter the seed. Fixed by threading a
    # real `stage_index` (see get_public_game()) through to
    # generate_public()'s now-real `puzzle_count` parameter. Deliberately
    # "any"-difficulty only (certified_difficulties left empty): difficulty
    # filtering happens on the flat accepted-candidates list BEFORE the
    # era-ordering is re-applied, which could silently drop an era and
    # shift every later stage_index to the wrong era -- not worth the risk
    # for a mode whose whole point is "the real fixed history," not a
    # difficulty-scoped subset.
    "era_gauntlet_guess": {
        "competition": "CFB",
        "title": "Era Gauntlet",
        "instructions": "Progress through real NFL history -- one real Super Bowl champion from each "
                        "represented decade, oldest era first.",
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
        # Real survey: 12/12 eligible at easy and medium. Hard excluded for
        # the same verified reason as cfb_spot_the_fake_guess above (see
        # its comment): real Hard boards exist in this same shared
        # _group_board_common pool (196/595), but an explicit
        # difficulty="hard" request reliably fails to generate through the
        # shared Director pipeline -- confirmed by direct testing, not
        # assumed from a stale board-count claim. Draws from all 5 real
        # _group_board_common.py sources (SB_CHAMPION, CURRENT_TEAM_2026,
        # real team-season rosters, real Round-1 draft classes, real
        # First-Team All-Pro classes) -- that real variety is preserved,
        # not narrowed back to SB_CHAMPION-only.
        "certified_difficulties": frozenset({"easy", "medium"}),
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
        # Real survey: 12/12 eligible at any/easy/medium with ZERO
        # duplicate questions across all three bands (the cleanest survey
        # result of all 7 new modes). Hard excluded for the same verified
        # reason as cfb_spot_the_fake_guess/cfb_odd_college_out_guess above
        # (real Hard boards exist in the shared pool; the explicit-filter
        # generation path just doesn't reliably surface one -- confirmed by
        # direct testing). Same 5 real sources as cfb_odd_college_out_guess.
        # Confirmed (correcting an earlier assumption in this project's own
        # history): this is a
        # real GROUP-MEMBERSHIP question ("which college was NOT part of
        # this group"), not an ordered transfer-path/sequence -- the UI
        # uses a grouped-card display, not a sequence/path visual.
        "certified_difficulties": frozenset({"easy", "medium"}),
        "spec": {
            "mechanic": "guess",
            "domain": "CFB_ONE_SCHOOL_MISSING",
            "relationship_predicate": "MISSING_COLLEGE",
            "question_count": 1,
            "filters": {},
            "exclusions": [],
        },
    },
    # Franchise Marathon: the real, disclosed blocker -- the live route
    # hardcoded `filters: {}`, and even with a franchise_name filter
    # threaded through, puzzle_count=1 could only ever return a franchise's
    # OLDEST real title forever (same root cause as Era Gauntlet above; see
    # generation.generate_public()'s docstring for the full real diagnosis,
    # confirmed directly: Cowboys has 5 real distinct championship boards,
    # Packers 4, Patriots 6, Steelers 6, 49ers 5 -- verified via
    # sb_champion_offense_college.fetch_ordered_candidates() directly, not
    # assumed). Fixed the same way as Era Gauntlet: real `stage_index` +
    # `caller_filter_key: "franchise_name"` (the ONE caller-controlled
    # filter value this mode accepts -- see get_public_game()'s explicit
    # allow-list check). "any"-difficulty only, same real reason as Era
    # Gauntlet (difficulty filtering could shift which stage_index maps to
    # which real season).
    "franchise_marathon_guess": {
        "competition": "NFL",
        "title": "Franchise Marathon",
        "instructions": "Pick a real NFL franchise and play through its real Super Bowl-winning offenses "
                        "in chronological order, by college and position (player names hidden).",
        "kind": "multiple_choice",
        "sequential": True,
        "caller_filter_key": "franchise_name",
        "certified_difficulties": frozenset(),
        "spec": {
            "mechanic": "guess",
            "domain": "NFL_SB_CHAMPION_OFFENSE_COLLEGE",
            "relationship_predicate": "TEAM_SEASON_OF_CHAMPIONSHIP_OFFENSE_BY_COLLEGE",
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
                     filter_value: Optional[str] = None) -> dict:
    t0 = time.perf_counter()
    entry = _ensure_mode_public(mode)
    _ensure_difficulty_certified(mode, entry, difficulty)
    exclude = set(exclude_game_ids or [])
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
        if result["package_id"] not in exclude:
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
