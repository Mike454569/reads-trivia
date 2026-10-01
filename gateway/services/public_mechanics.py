"""Reads Engine Gateway -- public, unauthenticated access to MATCHING,
SORTING_TIMELINE, HIGHER_LOWER_STREAK, and ELIMINATION_SURVIVAL
(public-readiness punch-list closure pass).

Mirrors gateway/services/public_game.py's own trust-boundary reasoning
exactly: a real anonymous player never receives an admin token, and this
module is the ONLY place allowed to decide what such a caller can trigger
or see.

--- WHY THESE FOUR, AND NOT THE OTHER THREE PHASE 6/7 MECHANICS ---
MULTIPLE_CHOICE_SINGLE_FACT and POSITION_LINEUP_GRID already share the
"guess" mechanic's single-question-per-fetch contract with every existing
PUBLIC_MODES entry (public_game.py) -- POSITION_LINEUP_GRID's college
variant was simply ADDED to that existing, proven allowlist this pass
(gateway/services/public_game.py's `lineup_college_guess` entry), needing
no new route family at all. WEEKLY_PICKEM and LIVE_WEEKLY_FANTASY_DRAFT
are genuinely multi-user/room-shaped (standings, draft rooms, multiple
participants) -- the existing single-player public trust boundary this
module and public_game.py both use doesn't fit them without real new
session/room infrastructure, which is exactly the kind of redesign this
punch-list explicitly excludes. Left admin/Creator-only; reported as a
blocker in the final report, not forced live.

--- WHY THIS IS SAFE (the same read-only, closed-set argument
generate_public() already relies on, re-verified for these four) ---
`tools.director_v04.{matching,sorting,elimination,higher_lower}` (Phase 6)
each open exactly one connection (`engine.connect()`), issue only SELECT
queries, and close it -- confirmed by re-reading every line of all four
this pass. Every parameter these routes let a caller influence is a
`mode` string looked up against `PUBLIC_MECHANIC_MODES` below (a small,
explicit, hand-certified allowlist -- never an arbitrary taxonomy_id or
variant the way the ADMIN `/v1/creator/mechanics/round` route allows);
`round_count`/`pair_count`/`item_count`/`sequence_length` are always
SERVER-chosen constants from that same table, never caller input. A fresh
random seed is generated per request (same `secrets.token_hex` pattern
public_game.py already uses) -- no exclude-list retry loop is needed the
way public_game.py's is: these generators are fast enough (confirmed well
under 1s each in Phase 6 testing) that a fresh random seed is already a
real, different round essentially every time, and MECHANIC_ENGINE's own
`client_safe_view()`/`evaluate_submission()` (Phase 6, unchanged here) are
the SAME functions the admin route already uses -- the identical
allow-list leakage guarantee carries over unchanged, not re-implemented.

--- CONCURRENCY / BACKPRESSURE ---
A bounded, non-blocking semaphore (`config.PUBLIC_MECHANIC_MAX_CONCURRENCY`)
gates round-generation calls -- same "clean GENERATION_BUSY error, never
an unbounded queue" shape every other public/admin generation path in this
project already uses. Round state itself reuses packages.py (content-
addressed, atomic) and game_state.py (mutable progress, atomic) -- the
exact same storage the admin route already writes into; a public round_id
and an admin round_id live in the same id-space by construction, with no
new storage layer.
"""
from __future__ import annotations

import secrets
import threading
from typing import Any, Optional

from .. import config
from ..errors import GatewayError
from . import game_state, oplog, packages

CONTRACT_VERSION = 1

# Public mode id -> (real taxonomy_id + variant + server-chosen generation
# params). Every value here is a real, already-certified-in-Phase-6 variant
# (tools/director_v02/mechanic_engine.py's own VARIANTS registry) -- this
# table only decides which of those are ALSO safe for anonymous traffic,
# never invents a new one.
PUBLIC_MECHANIC_MODES: dict[str, dict[str, Any]] = {
    "matching_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "MATCHING", "variant": "NFL_DRAFT_CLASS_MATCH",
        "title": "NFL Draft Class Matching",
        "instructions": "Match each real NFL Draft pick to the real team that drafted him.",
        "kind": "matching", "gen_kwargs": {"round_count": 1, "pair_count": 4},
    },
    "matching_cfb_heisman": {
        "competition": "CFB", "taxonomy_id": "MATCHING", "variant": "CFB_HEISMAN_SCHOOL_MATCH",
        "title": "CFB Heisman Matching",
        "instructions": "Match each real Heisman Trophy winner to the school he played for.",
        "kind": "matching", "gen_kwargs": {"round_count": 1, "pair_count": 4},
    },
    "sorting_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_DRAFT_PICK_ORDER",
        "title": "NFL Draft Order",
        "instructions": "Put these real NFL Draft picks in order, earliest overall selection first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "sorting_cfb_heisman": {
        "competition": "CFB", "taxonomy_id": "SORTING_TIMELINE", "variant": "CFB_HEISMAN_YEAR_ORDER",
        "title": "Heisman Timeline",
        "instructions": "Put these real Heisman Trophy winners in order, earliest year first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    # STAT_LADDER (40-Format Expansion Part 2) -- same SORTING_TIMELINE
    # mechanic/taxonomy as the two variants above, same reasoning for why
    # each variant gets its own dedicated public mode entry (matches how
    # sorting_nfl_draft/sorting_cfb_heisman are each independently listed,
    # not just reachable via Creator's dynamic NL generation).
    "stat_ladder_nfl_rushing": {
        "competition": "NFL", "taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_SEASON_RUSHING_YARDS_LADDER",
        "title": "NFL Rushing Ladder",
        "instructions": "Rank these real NFL rushers from a single season, most rushing yards first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "stat_ladder_nfl_passing_td": {
        "competition": "NFL", "taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_CAREER_PASSING_TD_LADDER",
        "title": "NFL Passing TD Ladder",
        "instructions": "Rank these real NFL quarterbacks by career passing touchdowns, most first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "stat_ladder_cfb_rushing": {
        "competition": "CFB", "taxonomy_id": "SORTING_TIMELINE", "variant": "CFB_CAREER_RUSHING_YARDS_LADDER",
        "title": "CFB Rushing Ladder",
        "instructions": "Rank these real CFB players by career rushing yards, most first.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    # MAP_THE_CAREER (15-Format Expansion Part 2, format #9) -- same
    # SORTING_TIMELINE mechanic/taxonomy as STAT_LADDER above, same real
    # reasoning for a dedicated public mode entry per variant.
    "map_the_career_nfl": {
        "competition": "NFL", "taxonomy_id": "SORTING_TIMELINE", "variant": "NFL_PLAYER_CAREER_TEAM_ORDER",
        "title": "Map the Career",
        "instructions": "Put these real teams in the order this real NFL player actually played for them.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "map_the_career_cfb": {
        "competition": "CFB", "taxonomy_id": "SORTING_TIMELINE", "variant": "CFB_PLAYER_CAREER_SCHOOL_ORDER",
        "title": "Map the Career: College Football",
        "instructions": "Put these real schools in the order this real CFB player actually played for them.",
        "kind": "sorting", "gen_kwargs": {"round_count": 1, "item_count": 4},
    },
    "higher_lower_nfl_wins": {
        "competition": "NFL", "taxonomy_id": "HIGHER_LOWER_STREAK", "variant": "NFL_TEAM_SEASON_WINS",
        "title": "NFL Wins Streak",
        "instructions": "Guess whether the next real NFL team-season had a higher or lower win total. One miss ends the streak.",
        "kind": "higher_lower", "gen_kwargs": {"sequence_length": 12},
    },
    "higher_lower_cfb_wins": {
        "competition": "CFB", "taxonomy_id": "HIGHER_LOWER_STREAK", "variant": "CFB_TEAM_SEASON_WINS",
        "title": "CFB Wins Streak",
        "instructions": "Guess whether the next real CFB (FBS) team-season had a higher or lower win total. One miss ends the streak.",
        "kind": "higher_lower", "gen_kwargs": {"sequence_length": 12},
    },
    "elimination_nfl_super_bowl": {
        "competition": "NFL", "taxonomy_id": "ELIMINATION_SURVIVAL", "variant": "NFL_SUPER_BOWL_CHAMPION_SURVIVAL",
        "title": "Super Bowl Champion Survival",
        "instructions": "One miss ends the run. Answer True or False for each real NFL team-season.",
        "kind": "elimination", "gen_kwargs": {"sequence_length": 12},
    },
    "elimination_cfb_national_champion": {
        "competition": "CFB", "taxonomy_id": "ELIMINATION_SURVIVAL", "variant": "CFB_NATIONAL_CHAMPION_SURVIVAL",
        "title": "National Champion Survival",
        "instructions": "One miss ends the run. Answer True or False for each real CFB (FBS) team-season.",
        "kind": "elimination", "gen_kwargs": {"sequence_length": 12},
    },
    # Reusable Game Format System pass: the new COMPARISON_BRACKET mechanic
    # (tools/director_v04/comparison.py), backing the new BRACKET_TREE
    # format. gen_kwargs is empty -- comparison.build_package() takes no
    # tunable knobs (a real, fixed 8-entry bracket every time).
    "comparison_nfl_wins": {
        "competition": "NFL", "taxonomy_id": "COMPARISON_BRACKET", "variant": "NFL_TEAM_SEASON_WINS_BRACKET",
        "title": "NFL Wins Bracket",
        "instructions": "Predict the real winner of every matchup in this real 8-team bracket, based on "
                        "regular-season win total.",
        "kind": "comparison", "gen_kwargs": {},
    },
    "comparison_cfb_wins": {
        "competition": "CFB", "taxonomy_id": "COMPARISON_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_BRACKET",
        "title": "CFB Wins Bracket",
        "instructions": "Predict the real winner of every matchup in this real 8-team bracket, based on "
                        "regular-season win total.",
        "kind": "comparison", "gen_kwargs": {},
    },
    # ==========================================================================
    # Finish-10-Formats pass: the 6 new taxonomies from the 40-Format
    # Expansion pass, now real, public, unauthenticated modes -- not
    # admin-preview-only. Same real safety argument as every entry above:
    # each generator opens one connection, issues only SELECT queries
    # (GRID_CONSTRAINT_BOARD's answer-check is the one live re-verification
    # query, also read-only), and every caller-influenced value is looked up
    # against this fixed table, never taken directly from the request.
    "connection_grid_nfl": {
        "competition": "NFL", "taxonomy_id": "GRID_CONSTRAINT_BOARD", "variant": "NFL_TEAM_DRAFT_ROUND_GRID",
        "title": "NFL Connection Grid",
        "instructions": "Each cell needs a real player who satisfies BOTH its row and column criteria.",
        "kind": "grid_constraint", "gen_kwargs": {},
    },
    "perfect_drive_nfl": {
        "competition": "NFL", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "NFL_DRAFT_PERFECT_DRIVE",
        "title": "Perfect Drive (NFL)",
        "instructions": "Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 15},
    },
    "perfect_drive_cfb": {
        "competition": "CFB", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "CFB_HEISMAN_PERFECT_DRIVE",
        "title": "Perfect Drive (CFB)",
        "instructions": "Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 15},
    },
    "goal_line_stand_nfl": {
        "competition": "NFL", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "NFL_DRAFT_GOAL_LINE_STAND",
        "title": "Goal Line Stand (NFL)",
        "instructions": "You have 4 downs to score. A wrong answer costs a down.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 10},
    },
    "goal_line_stand_cfb": {
        "competition": "CFB", "taxonomy_id": "DRIVE_PROGRESSION", "variant": "CFB_HEISMAN_GOAL_LINE_STAND",
        "title": "Goal Line Stand (CFB)",
        "instructions": "You have 4 downs to score. A wrong answer costs a down.",
        "kind": "drive_progression", "gen_kwargs": {"question_count": 10},
    },
    "lineup_builder_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_2010S_OFFENSE_BUILDER",
        "title": "2010s Offense Builder",
        "instructions": "Build a real roster from real 2010s starters -- one real player per slot, no player twice.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "lineup_builder_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_SKILL_POSITION_BUILDER",
        "title": "CFB Skill Position Builder",
        "instructions": "Build a real CFB skill-position lineup -- one real player per slot, no player twice.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "auction_draft_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_AUCTION_DRAFT",
        "title": "NFL Auction Draft",
        "instructions": "Draft a real roster one slot at a time under a fictional $50,000,000 budget. "
                        "Each player's cost is a fictional value derived from real career production.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "auction_draft_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_AUCTION_DRAFT",
        "title": "CFB Auction Draft",
        "instructions": "Draft a real roster one slot at a time under a fictional $50,000,000 budget. "
                        "Each player's cost is a fictional value derived from real career production.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "cap_challenge_nfl": {
        "competition": "NFL", "taxonomy_id": "ROSTER_BUILD", "variant": "NFL_CAP_CHALLENGE",
        "title": "NFL Cap Challenge",
        "instructions": "Freely select, swap, or remove real players per slot under a fictional "
                        "$50,000,000 cap. Nothing locks in until you submit the finished lineup.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "cap_challenge_cfb": {
        "competition": "CFB", "taxonomy_id": "ROSTER_BUILD", "variant": "CFB_CAP_CHALLENGE",
        "title": "CFB Cap Challenge",
        "instructions": "Freely select, swap, or remove real players per slot under a fictional "
                        "$50,000,000 cap. Nothing locks in until you submit the finished lineup.",
        "kind": "roster_build", "gen_kwargs": {},
    },
    "knockout_tournament_nfl": {
        "competition": "NFL", "taxonomy_id": "KNOCKOUT_BRACKET", "variant": "NFL_TEAM_SEASON_WINS_KNOCKOUT_16",
        "title": "NFL Knockout Tournament",
        "instructions": "Predict the real winner of every matchup in this real 16-team knockout field, "
                        "based on regular-season win total.",
        "kind": "knockout_bracket", "gen_kwargs": {},
    },
    "knockout_tournament_cfb": {
        "competition": "CFB", "taxonomy_id": "KNOCKOUT_BRACKET", "variant": "CFB_TEAM_SEASON_WINS_KNOCKOUT_16",
        "title": "CFB Knockout Tournament",
        "instructions": "Predict the real winner of every matchup in this real 16-team knockout field, "
                        "based on regular-season win total.",
        "kind": "knockout_bracket", "gen_kwargs": {},
    },
    # SIX_DEGREES and CHAIN_REACTION share the identical real bounded-chain
    # backend/data (tools/director_v04/relationship_chain.py) -- two format
    # framings over one real mechanic, never two implementations.
    "six_degrees_cfb_nfl": {
        "competition": "CFB", "taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
        "title": "Six Degrees: College to NFL",
        "instructions": "See a real player's college. Guess the real NFL team that drafted him.",
        "kind": "relationship_chain", "gen_kwargs": {"chain_count": 8},
    },
    "chain_reaction_cfb_nfl": {
        "competition": "CFB", "taxonomy_id": "RELATIONSHIP_CHAIN", "variant": "CFB_SCHOOL_TO_NFL_TEAM_CHAIN",
        "title": "Chain Reaction: College to NFL",
        "instructions": "Follow the real chain from college to the NFL team that drafted him.",
        "kind": "relationship_chain", "gen_kwargs": {"chain_count": 8},
        # Backward-compatible presentation alias of six_degrees_cfb_nfl.
        # It stays callable for old links/saved state but is intentionally
        # excluded from discovery so the UI cannot count the same game twice.
        "discoverable": False,
    },
    "choose_your_path_nfl": {
        "competition": "NFL", "taxonomy_id": "BRANCH_STATE", "variant": "NFL_TOPIC_PATH",
        "title": "Choose Your Path",
        "instructions": "Pick a path at each step -- your choice determines the next real question.",
        "kind": "branch_state", "gen_kwargs": {},
    },
    "choose_your_path_cfb": {
        "competition": "CFB", "taxonomy_id": "BRANCH_STATE", "variant": "CFB_TOPIC_PATH",
        "title": "Choose Your Path: College Football",
        "instructions": "Pick a path at each step -- your choice determines the next real question.",
        "kind": "branch_state", "gen_kwargs": {},
    },
    # 15-Format Expansion pass (Part 2), format #2 -- see
    # tools/director_v04/guess_the_season.py's own module docstring.
    "guess_the_season_nfl": {
        "competition": "NFL", "taxonomy_id": "GUESS_THE_SEASON", "variant": "NFL_SUPER_BOWL_SEASON",
        "title": "Guess the Season",
        "instructions": "Read the real clues, then guess the real NFL season (e.g. 2019) they all describe.",
        "kind": "guess_the_season", "gen_kwargs": {"round_count": 5, "difficulty": "MEDIUM"},
    },
    # 15-Format Expansion pass (Part 2), format #3 -- see
    # tools/director_v04/head_to_head_duel.py's own module docstring.
    "head_to_head_duel_nfl_rushing": {
        "competition": "NFL", "taxonomy_id": "PAIRWISE_COMPARE", "variant": "NFL_SEASON_RUSHING_YARDS_DUEL",
        "title": "Rushing Duel",
        "instructions": "Tap whichever real player you think had more rushing yards that season.",
        "kind": "pairwise_compare", "gen_kwargs": {"round_count": 5},
    },
    "head_to_head_duel_nfl_passing_td": {
        "competition": "NFL", "taxonomy_id": "PAIRWISE_COMPARE", "variant": "NFL_CAREER_PASSING_TD_DUEL",
        "title": "Passing TD Duel",
        "instructions": "Tap whichever real quarterback you think threw more career passing touchdowns.",
        "kind": "pairwise_compare", "gen_kwargs": {"round_count": 5},
    },
    "head_to_head_duel_cfb_rushing": {
        "competition": "CFB", "taxonomy_id": "PAIRWISE_COMPARE", "variant": "CFB_CAREER_RUSHING_YARDS_DUEL",
        "title": "CFB Rushing Duel",
        "instructions": "Tap whichever real CFB player you think has more career rushing yards.",
        "kind": "pairwise_compare", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #4 -- see
    # tools/director_v04/head_to_head_duel.py's own module docstring for
    # the real, disclosed NFL-QB-only scope this variant starts with.
    "best_of_seven_duel_nfl_qb": {
        "competition": "NFL", "taxonomy_id": "PAIRWISE_COMPARE", "variant": "NFL_CAREER_QB_BEST_OF_SEVEN",
        "title": "QB Best of Seven",
        "instructions": "Tap whichever real quarterback had more in each of up to 7 real career categories "
                         "-- most categories won takes the duel.",
        "kind": "pairwise_compare", "gen_kwargs": {"round_count": 7},
    },
    # 15-Format Expansion pass (Part 2), format #5 -- see
    # tools/director_v04/pick_the_impostor.py's own module docstring.
    "pick_the_impostor_nfl": {
        "competition": "NFL", "taxonomy_id": "PICK_THE_IMPOSTOR", "variant": "NFL_TEAM_ROSTER_IMPOSTOR",
        "title": "Pick the Impostor",
        "instructions": "3 of these 4 real players were really on the same real NFL roster -- tap whichever one wasn't.",
        "kind": "pick_the_impostor", "gen_kwargs": {"round_count": 5},
    },
    "pick_the_impostor_cfb": {
        "competition": "CFB", "taxonomy_id": "PICK_THE_IMPOSTOR", "variant": "CFB_SCHOOL_ROSTER_IMPOSTOR",
        "title": "Pick the Impostor: College Football",
        "instructions": "3 of these 4 real players really played for the same real school -- tap whichever one didn't.",
        "kind": "pick_the_impostor", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #6 -- see
    # tools/director_v04/pick_the_impostor.py's own module docstring.
    "unique_one_out_nfl": {
        "competition": "NFL", "taxonomy_id": "PICK_THE_IMPOSTOR", "variant": "NFL_DRAFT_CLASS_ONE_OUT",
        "title": "Unique One Out",
        "instructions": "3 of these 4 real players were really drafted in the same real NFL Draft class -- tap whichever one wasn't.",
        "kind": "pick_the_impostor", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #7 -- see
    # tools/director_v04/missing_piece.py's own module docstring.
    "missing_piece_nfl": {
        "competition": "NFL", "taxonomy_id": "MISSING_PIECE", "variant": "NFL_TEAM_ROSTER_MISSING_PIECE",
        "title": "Missing Piece",
        "instructions": "3 real players from the same real NFL roster are shown -- tap whichever of these 4 also really belongs.",
        "kind": "missing_piece", "gen_kwargs": {"round_count": 5},
    },
    "missing_piece_cfb": {
        "competition": "CFB", "taxonomy_id": "MISSING_PIECE", "variant": "CFB_SCHOOL_ROSTER_MISSING_PIECE",
        "title": "Missing Piece: College Football",
        "instructions": "3 real players from the same real school roster are shown -- tap whichever of these 4 also really belongs.",
        "kind": "missing_piece", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #8 -- see
    # tools/director_v04/before_after.py's own module docstring.
    "before_after_nfl": {
        "competition": "NFL", "taxonomy_id": "BEFORE_AFTER", "variant": "NFL_TEAM_CHANGE_BEFORE_AFTER",
        "title": "Before & After",
        "instructions": "Tap whichever real team you think this real player played for FIRST.",
        "kind": "before_after", "gen_kwargs": {"round_count": 5},
    },
    "before_after_cfb": {
        "competition": "CFB", "taxonomy_id": "BEFORE_AFTER", "variant": "CFB_SCHOOL_TRANSFER_BEFORE_AFTER",
        "title": "Before & After: College Football",
        "instructions": "Tap whichever real school you think this real player played for FIRST.",
        "kind": "before_after", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #10 -- see
    # tools/director_v04/career_path.py's own module docstring.
    "career_path_nfl": {
        "competition": "NFL", "taxonomy_id": "CAREER_PATH", "variant": "NFL_PLAYER_CAREER_PATH_IDENTIFY",
        "title": "Career Path",
        "instructions": "Read the real career path, then tap whichever real NFL player it belongs to.",
        "kind": "career_path", "gen_kwargs": {"round_count": 5},
    },
    "career_path_cfb": {
        "competition": "CFB", "taxonomy_id": "CAREER_PATH", "variant": "CFB_PLAYER_CAREER_PATH_IDENTIFY",
        "title": "Career Path: College Football",
        "instructions": "Read the real career path, then tap whichever real CFB player it belongs to.",
        "kind": "career_path", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #11 -- see
    # tools/director_v04/risk_it.py's own module docstring.
    "risk_it_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "RISK_IT", "variant": "NFL_DRAFT_RISK_IT",
        "title": "Risk It",
        "instructions": "Pick a real risk tier before you see the question -- LOW is easier and worth less, "
                         "HIGH uses a more obscure stat season and is worth more. A wrong answer costs a life.",
        "kind": "risk_it", "gen_kwargs": {"round_count": 7},
    },
    # CFB retrofit pass -- real per-season passing/rushing/receiving rank as
    # the recognizability proxy, see risk_it.py's own module docstring.
    "risk_it_cfb_passing": {
        "competition": "CFB", "taxonomy_id": "RISK_IT", "variant": "CFB_SEASON_PASSING_RISK_IT",
        "title": "Risk It (CFB)",
        "instructions": "Pick a real risk tier before you see the question -- LOW uses a top-ranked season "
                         "performance, while HIGH goes deeper down a real leaderboard and is worth more. "
                         "A wrong answer costs a life.",
        "kind": "risk_it", "gen_kwargs": {"round_count": 7},
    },
    # 15-Format Expansion pass (Part 2), format #12 -- see
    # tools/director_v04/wager_mode.py's own module docstring.
    "wager_mode_mixed": {
        "competition": "NFL", "taxonomy_id": "WAGER_MODE", "variant": "WAGER_MODE_MIXED",
        "title": "Wager Mode",
        "instructions": "You'll see only a real category. Wager any amount of your fictional balance, then "
                         "the real question is revealed -- a correct answer adds your wager, a wrong answer "
                         "subtracts it.",
        "kind": "wager_mode", "gen_kwargs": {"round_count": 5},
    },
    # 15-Format Expansion pass (Part 2), format #14 -- see
    # tools/director_v04/leaderboard_climb.py's own module docstring.
    "leaderboard_climb_nfl": {
        "competition": "NFL", "taxonomy_id": "LEADERBOARD_CLIMB", "variant": "NFL_CAREER_PASSING_YARDS_CLIMB",
        "title": "Leaderboard Climb",
        "instructions": "Tap whichever real player you think ranks HIGHER on this real leaderboard -- a "
                         "correct answer climbs you up one real rung; a wrong answer ends your climb.",
        "kind": "leaderboard_climb", "gen_kwargs": {},
    },
    # 15-Format Expansion pass (Part 2), format #15 (final of 15) -- see
    # tools/director_v04/blind_resume.py's own module docstring.
    "blind_resume_nfl_qb": {
        "competition": "NFL", "taxonomy_id": "BLIND_RESUME", "variant": "NFL_QB_CAREER_BLIND_RESUME",
        "title": "Blind Resume",
        "instructions": "A real player's career passing resume is shown with the name hidden -- tap "
                         "whichever real candidate you think it belongs to.",
        "kind": "blind_resume", "gen_kwargs": {"round_count": 7},
    },
    # CFB retrofit pass -- built on cfb_player_season_stats_real +
    # cfb_roster_seasons_real.position='QB', see blind_resume.py's own
    # module docstring for the real games->completions substitution.
    "blind_resume_cfb_qb": {
        "competition": "CFB", "taxonomy_id": "BLIND_RESUME", "variant": "CFB_QB_CAREER_BLIND_RESUME",
        "title": "Blind Resume (CFB)",
        "instructions": "A real college player's career passing resume is shown with the name hidden -- tap "
                         "whichever real candidate you think it belongs to.",
        "kind": "blind_resume", "gen_kwargs": {"round_count": 7},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # double_or_nothing.py's own module docstring.
    "double_or_nothing_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "DOUBLE_OR_NOTHING", "variant": "NFL_DRAFT_DOUBLE_OR_NOTHING",
        "title": "Double or Nothing",
        "instructions": "Answer the real question -- a correct answer banks or doubles your real points. "
                         "After every correct answer, bank your points or risk them on the next, harder "
                         "real question. One wrong answer loses everything.",
        "kind": "double_or_nothing", "gen_kwargs": {"round_count": 8},
    },
    # CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
    # see double_or_nothing.py's own module docstring.
    "double_or_nothing_cfb_passing": {
        "competition": "CFB", "taxonomy_id": "DOUBLE_OR_NOTHING", "variant": "CFB_SEASON_PASSING_DOUBLE_OR_NOTHING",
        "title": "Double or Nothing (CFB)",
        "instructions": "Answer the real question -- a correct answer banks or doubles your real points. "
                         "After every correct answer, bank your points or risk them on the next, harder "
                         "real question. One wrong answer loses everything.",
        "kind": "double_or_nothing", "gen_kwargs": {"round_count": 8},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # king_of_the_hill.py's own module docstring.
    "king_of_the_hill_nfl": {
        "competition": "NFL", "taxonomy_id": "KING_OF_THE_HILL", "variant": "NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL",
        "title": "King of the Hill",
        "instructions": "Tap whichever of the champion or the next real challenger you think really had "
                         "more real wins that season -- a correct prediction keeps the gauntlet going; a "
                         "wrong prediction ends your run.",
        "kind": "king_of_the_hill", "gen_kwargs": {},
    },
    # CFB retrofit pass -- reuses higher_lower.py's own already-certified
    # cfb_standings.total_wins data (FBS only), zero new data work.
    "king_of_the_hill_cfb": {
        "competition": "CFB", "taxonomy_id": "KING_OF_THE_HILL", "variant": "CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL",
        "title": "King of the Hill (CFB)",
        "instructions": "Tap whichever of the champion or the next real college challenger you think really "
                         "had more real wins that season -- a correct prediction keeps the gauntlet going; a "
                         "wrong prediction ends your run.",
        "kind": "king_of_the_hill", "gen_kwargs": {},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # fact_or_fake.py's own module docstring.
    "fact_or_fake_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "FACT_OR_FAKE", "variant": "NFL_DRAFT_FACT_OR_FAKE",
        "title": "Fact or Fake",
        "instructions": "Read the NFL history statement -- tap TRUE if it's a real, verbatim fact, or FAKE if "
                         "it's been altered.",
        "kind": "fact_or_fake", "gen_kwargs": {"round_count": 10},
    },
    # CFB retrofit pass -- real game-result statement, see fact_or_fake.py's
    # own module docstring.
    "fact_or_fake_cfb_game": {
        "competition": "CFB", "taxonomy_id": "FACT_OR_FAKE", "variant": "CFB_GAME_RESULT_FACT_OR_FAKE",
        "title": "Fact or Fake (CFB)",
        "instructions": "Read the real final score -- tap TRUE if it's a real, verbatim result, or FAKE if "
                         "it's been altered.",
        "kind": "fact_or_fake", "gen_kwargs": {"round_count": 10},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # guess_the_ranking.py's own module docstring.
    "guess_the_ranking_nfl": {
        "competition": "NFL", "taxonomy_id": "GUESS_THE_RANKING", "variant": "NFL_CAREER_PASSING_YARDS_RANKING",
        "title": "Guess the Ranking",
        "instructions": "A real player is named -- tap the real rank you think they hold on this real "
                         "career leaderboard.",
        "kind": "guess_the_ranking", "gen_kwargs": {"round_count": 8},
    },
    # CFB retrofit pass -- self-contained real top-15 CFB career passing
    # yards query, see guess_the_ranking.py's own module docstring.
    "guess_the_ranking_cfb": {
        "competition": "CFB", "taxonomy_id": "GUESS_THE_RANKING", "variant": "CFB_CAREER_PASSING_YARDS_RANKING",
        "title": "Guess the Ranking (CFB)",
        "instructions": "A real college player is named -- tap the real rank you think they hold on this "
                         "real career leaderboard.",
        "kind": "guess_the_ranking", "gen_kwargs": {"round_count": 8},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # stat_target.py's own module docstring.
    "stat_target_nfl_rushing": {
        "competition": "NFL", "taxonomy_id": "STAT_TARGET", "variant": "NFL_SEASON_RUSHING_YARDS_TARGET",
        "title": "Stat Target",
        "instructions": "A real target rushing-yards number is shown -- tap whichever real player's real "
                         "single-season total came closest to it.",
        "kind": "stat_target", "gen_kwargs": {"round_count": 8},
    },
    # CFB retrofit pass -- built on cfb_player_season_stats_real, see
    # stat_target.py's own module docstring for real pool size/coverage.
    "stat_target_cfb_rushing": {
        "competition": "CFB", "taxonomy_id": "STAT_TARGET", "variant": "CFB_SEASON_RUSHING_YARDS_TARGET",
        "title": "Stat Target (CFB)",
        "instructions": "A real target rushing-yards number is shown -- tap whichever real college player's "
                         "real single-season total came closest to it.",
        "kind": "stat_target", "gen_kwargs": {"round_count": 8},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # reverse_trivia.py's own module docstring.
    "reverse_trivia_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "REVERSE_TRIVIA", "variant": "NFL_DRAFT_REVERSE_TRIVIA",
        "title": "Reverse Trivia",
        "instructions": "A real player is named -- tap the 1 of 4 real statements that's actually true "
                         "about them.",
        "kind": "reverse_trivia", "gen_kwargs": {"round_count": 8},
    },
    # CFB retrofit pass -- real season passing stat line, see
    # reverse_trivia.py's own module docstring.
    "reverse_trivia_cfb_passing": {
        "competition": "CFB", "taxonomy_id": "REVERSE_TRIVIA", "variant": "CFB_SEASON_PASSING_REVERSE_TRIVIA",
        "title": "Reverse Trivia (CFB)",
        "instructions": "A real college player is named -- tap the 1 of 4 real statements that's actually "
                         "true about them.",
        "kind": "reverse_trivia", "gen_kwargs": {"round_count": 8},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # three_strikes.py's own module docstring.
    "three_strikes_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "THREE_STRIKES", "variant": "NFL_DRAFT_THREE_STRIKES",
        "title": "Three Strikes",
        "instructions": "Answer real questions of rising real difficulty -- a wrong answer costs a strike. "
                         "Survive 3 strikes and the run ends.",
        "kind": "three_strikes", "gen_kwargs": {"round_count": 12},
    },
    # CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
    # see three_strikes.py's own module docstring.
    "three_strikes_cfb_passing": {
        "competition": "CFB", "taxonomy_id": "THREE_STRIKES", "variant": "CFB_SEASON_PASSING_THREE_STRIKES",
        "title": "Three Strikes (CFB)",
        "instructions": "Answer real questions of rising real difficulty -- a wrong answer costs a strike. "
                         "Survive 3 strikes and the run ends.",
        "kind": "three_strikes", "gen_kwargs": {"round_count": 12},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # mystery_roster.py's own module docstring.
    "mystery_roster_nfl": {
        "competition": "NFL", "taxonomy_id": "MYSTERY_ROSTER", "variant": "NFL_TEAM_SEASON_MYSTERY_ROSTER",
        "title": "Mystery Roster",
        "instructions": "Reveal real clues about a mystery real NFL team-season one at a time, or guess at "
                         "any point -- fewer reveals before a correct guess earns more points.",
        "kind": "mystery_roster", "gen_kwargs": {"round_count": 6},
    },
    # CFB retrofit pass -- real leading-passer/leading-rusher+receiver/
    # class_year substitutes, see mystery_roster.py's own module docstring.
    "mystery_roster_cfb": {
        "competition": "CFB", "taxonomy_id": "MYSTERY_ROSTER", "variant": "CFB_TEAM_SEASON_MYSTERY_ROSTER",
        "title": "Mystery Roster (CFB)",
        "instructions": "Reveal real clues about a mystery real college team-season one at a time, or guess "
                         "at any point -- fewer reveals before a correct guess earns more points.",
        "kind": "mystery_roster", "gen_kwargs": {"round_count": 6},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # draft_pick_ladder.py's own module docstring.
    "draft_pick_ladder_nfl": {
        "competition": "NFL", "taxonomy_id": "DRAFT_PICK_LADDER", "variant": "NFL_DRAFT_PICK_LADDER",
        "title": "Draft Pick Ladder",
        "instructions": "A real player and their real draft season are named -- tap the real overall pick "
                         "number they were drafted with.",
        "kind": "draft_pick_ladder", "gen_kwargs": {"round_count": 9},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # category_roulette.py's own module docstring.
    "category_roulette_mixed": {
        "competition": "NFL", "taxonomy_id": "CATEGORY_ROULETTE", "variant": "CATEGORY_ROULETTE_MIXED",
        "title": "Category Roulette",
        "instructions": "Each round's real category is shown immediately -- read the real question and "
                         "tap the correct real answer.",
        "kind": "category_roulette", "gen_kwargs": {"round_count": 6},
    },
    # 75-Format Expansion, Wave 1 -- see tools/director_v04/
    # common_link.py's own module docstring.
    "common_link_nfl_draft": {
        "competition": "NFL", "taxonomy_id": "COMMON_LINK", "variant": "NFL_DRAFT_COMMON_LINK",
        "title": "Common Link",
        "instructions": "3 real NFL players are named -- tap the 1 of 4 real statements that correctly "
                         "explains what connects them.",
        "kind": "common_link", "gen_kwargs": {"round_count": 8},
    },
    # CFB retrofit pass -- real school/season/conference link types, see
    # common_link.py's own module docstring.
    "common_link_cfb_season": {
        "competition": "CFB", "taxonomy_id": "COMMON_LINK", "variant": "CFB_SEASON_COMMON_LINK",
        "title": "Common Link (CFB)",
        "instructions": "3 real college players are named -- tap the 1 of 4 real statements that correctly "
                         "explains what connects them.",
        "kind": "common_link", "gen_kwargs": {"round_count": 8},
    },

    # 100-format Expansion Wave 2: 15 genuinely different strategy loops.
    # All share one audited mixed-trivia knowledge source, but each variant
    # has its own server-side state machine and interaction contract.
    "bingo_blitz_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "BINGO_BLITZ",
        "title": "Bingo Blitz", "instructions": "Claim a three-cell line on a 3x3 board.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "territory_takeover_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TERRITORY_TAKEOVER",
        "title": "Territory Takeover", "instructions": "Choose zones and outscore the opponent by claiming territory.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "exact_ten_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "EXACT_TEN",
        "title": "Exact Ten", "instructions": "Choose 1-3 point plays and land on exactly 10 without busting.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "pyramid_climb_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "PYRAMID_CLIMB",
        "title": "Pyramid Climb", "instructions": "Pick a lane and climb five levels; misses knock you down.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "lockbox_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "LOCKBOX",
        "title": "Lockbox", "instructions": "Open three locks, then beat the final vault question.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "combo_meter_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "COMBO_METER",
        "title": "Combo Meter", "instructions": "Build a scoring multiplier with consecutive correct answers.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "checkpoint_rally_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CHECKPOINT_RALLY",
        "title": "Checkpoint Rally", "instructions": "Advance to eight; misses send you back to your last saved checkpoint.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "escalator_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "ESCALATOR",
        "title": "Escalator", "instructions": "Risk one or two steps per question and reach step 10.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "power_up_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "POWER_UP",
        "title": "Power Up", "instructions": "Earn energy with correct answers and spend it on a server-safe 50/50.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "category_conquest_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CATEGORY_CONQUEST",
        "title": "Category Conquest", "instructions": "Choose and capture all three real trivia categories.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "scoreboard_swing_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "SCOREBOARD_SWING",
        "title": "Scoreboard Swing", "instructions": "Correct answers score seven; misses give the opponent three. First to 21 wins.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "momentum_bar_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "MOMENTUM_BAR",
        "title": "Momentum Bar", "instructions": "Push momentum to +8 before it falls to -4.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "timeout_tokens_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TIMEOUT_TOKENS",
        "title": "Timeout Tokens", "instructions": "Manage two skips and one double-score token across the run.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "perfect_set_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "PERFECT_SET",
        "title": "Perfect Set", "instructions": "Win two of three best-of-three trivia sets.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "triple_or_take_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TRIPLE_OR_TAKE",
        "title": "Triple or Take", "instructions": "Choose 1-3 question series; clear the whole series to bank bigger points.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 24},
    },
    "connect_four_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CONNECT_FOUR",
        "title": "Connect Four", "instructions": "Drop four of your discs in a row before the opponent.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "tic_tac_toe_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TIC_TAC_TOE",
        "title": "Tic-Tac-Toe", "instructions": "Claim a three-cell line before the opponent.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "challenge_flag_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CHALLENGE_FLAG",
        "title": "Challenge Flag", "instructions": "Use two replay challenges to overturn missed answers.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "extra_point_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "EXTRA_POINT",
        "title": "Extra Point", "instructions": "Score touchdowns, then choose one safe point or a two-point trivia try.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "comeback_mode_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "COMEBACK_MODE",
        "title": "Comeback Mode", "instructions": "Erase a 21-point deficit in six possessions.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "category_draft_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CATEGORY_DRAFT",
        "title": "Category Draft", "instructions": "Draft each real category at most twice across six picks.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "three_and_out_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "THREE_AND_OUT",
        "title": "Three & Out", "instructions": "Get at least one answer right on each three-play drive.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "pick_your_poison_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "PICK_YOUR_POISON",
        "title": "Pick Your Poison", "instructions": "Choose between two visible categories before each question.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "second_chance_queue_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "SECOND_CHANCE_QUEUE",
        "title": "Second Chance Queue", "instructions": "Defer your first miss and replay that exact question at the end.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "coverage_shell_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "COVERAGE_SHELL",
        "title": "Coverage Shell", "instructions": "Record two stops in every zone before allowing three completions.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "offense_defense_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "OFFENSE_DEFENSE",
        "title": "Offense / Defense", "instructions": "Alternate offense and defense snaps and outscore the opponent.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "field_goal_range_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "FIELD_GOAL_RANGE",
        "title": "Field Goal Range", "instructions": "Build field position, then decide when to attempt the kick.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "two_minute_drill_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TWO_MINUTE_DRILL",
        "title": "Two-Minute Drill", "instructions": "Choose tempo and reach 60 yards before 120 seconds expire.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "category_streak_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CATEGORY_STREAK",
        "title": "Category Streak", "instructions": "Build a two-answer streak in all three real categories.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "perfect_quarter_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "PERFECT_QUARTER",
        "title": "Perfect Quarter", "instructions": "Score touchdowns on at least three of four two-question drives.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 30},
    },
    "red_zone_ladder_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "RED_ZONE_LADDER",
        "title": "Red Zone Ladder", "instructions": "Climb from the 20 to the end zone before three misses.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "drive_builder_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "DRIVE_BUILDER",
        "title": "Drive Builder", "instructions": "Complete short, medium, and deep plays to build a scoring drive.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "hot_hand_switch_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "HOT_HAND_SWITCH",
        "title": "Hot Hand Switch", "instructions": "Stay with a hot category or switch and reset the multiplier.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "overtime_shootout_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "OVERTIME_SHOOTOUT",
        "title": "Overtime Shootout", "instructions": "Trade overtime possessions until somebody leads.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "first_down_chain_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "FIRST_DOWN_CHAIN",
        "title": "First Down Chain", "instructions": "Earn four first downs before a turnover on downs.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "blitz_package_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "BLITZ_PACKAGE",
        "title": "Blitz Package", "instructions": "Choose pressure level and get five sacks before allowing three touchdowns.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "zone_control_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "ZONE_CONTROL",
        "title": "Zone Control", "instructions": "Capture all nine zones before the question window closes.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "play_caller_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "PLAY_CALLER",
        "title": "Play Caller", "instructions": "Call run, pass, or play action before each snap.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "possession_arrow_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "POSSESSION_ARROW",
        "title": "Possession Arrow", "instructions": "Score while possession flips after every miss.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "sudden_death_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "SUDDEN_DEATH",
        "title": "Sudden Death", "instructions": "One miss can end it; outlast the opponent.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "score_bank_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "SCORE_BANK",
        "title": "Score Bank", "instructions": "Grow a pot, then decide when to bank it safely.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "audible_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "AUDIBLE",
        "title": "Audible", "instructions": "Keep the call or spend one of two audibles to change category.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "fourth_down_decision_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "FOURTH_DOWN_DECISION",
        "title": "Fourth Down Decision", "instructions": "Take three or risk the drive for seven on fourth down.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "series_sweep_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "SERIES_SWEEP",
        "title": "Series Sweep", "instructions": "Win a best-of-five series and chase the 3-0 sweep.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "road_to_100_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "ROAD_TO_100",
        "title": "Road to 100", "instructions": "Choose 10-, 20-, or 30-point shots and race to 100.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "option_eraser_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "OPTION_ERASER",
        "title": "Option Eraser", "instructions": "Manage three erasers that remove one wrong option before a question.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "route_tree_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "ROUTE_TREE",
        "title": "Route Tree", "instructions": "Complete slant, post, and go routes in any order.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "turnover_battle_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "TURNOVER_BATTLE",
        "title": "Turnover Battle", "instructions": "Reach 50 yards before committing three turnovers.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "category_lockout_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CATEGORY_LOCKOUT",
        "title": "Category Lockout", "instructions": "Score in every category before misses lock one out.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "hail_mary_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "HAIL_MARY",
        "title": "Hail Mary", "instructions": "Earn a final rescue question if regulation ends one short.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "moving_target_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "MOVING_TARGET",
        "title": "Moving Target", "instructions": "Hit an exact target score that shifts after every answer.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "draft_order_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "DRAFT_ORDER",
        "title": "Draft Order", "instructions": "Trade up from pick 10 to pick one before five misses.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
    "championship_run_mixed": {
        "competition": "MIXED", "taxonomy_id": "STRATEGY_ARCADE", "variant": "CHAMPIONSHIP_RUN",
        "title": "Championship Run", "instructions": "Survive four playoff stages with escalating requirements.",
        "kind": "strategy_arcade", "gen_kwargs": {"round_count": 36},
    },
}

_generation_semaphore = threading.Semaphore(config.PUBLIC_MECHANIC_MAX_CONCURRENCY)


def list_public_mechanic_modes() -> list[dict]:
    """Client-safe mode discovery -- same allow-list discipline as
    public_game.py's list_public_modes(): only fields a client needs to
    choose a mode, never internal taxonomy/variant identifiers."""
    return [
        {"mode": mode_id, "competition": entry["competition"], "title": entry["title"],
         "instructions": entry["instructions"], "kind": entry["kind"],
         "available": config.PUBLIC_GAME_ENABLED}
        for mode_id, entry in PUBLIC_MECHANIC_MODES.items()
        if entry.get("discoverable", True)
    ]


def _ensure_mode_public(mode: str) -> dict:
    if not config.PUBLIC_GAME_ENABLED:
        oplog.record_event("public_mechanic_disabled", mode=None, reason="master_switch_off")
        raise GatewayError("SERVICE_UNAVAILABLE", "Public gameplay is currently disabled.")
    entry = PUBLIC_MECHANIC_MODES.get(mode)
    if entry is None:
        raise GatewayError("INVALID_MODE", f"mode={mode!r} is not a recognized mechanic mode.")
    return entry


def start_public_round(*, mode: str) -> dict:
    from tools.director_v02 import mechanic_engine

    entry = _ensure_mode_public(mode)
    taxonomy_id, variant = entry["taxonomy_id"], entry["variant"]
    seed = secrets.token_hex(8)

    acquired = _generation_semaphore.acquire(blocking=False)
    if not acquired:
        raise GatewayError("GENERATION_BUSY", "This game is popular right now -- try again in a moment.")
    try:
        if taxonomy_id == "MATCHING":
            package = mechanic_engine.generate_matching_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "SORTING_TIMELINE":
            package = mechanic_engine.generate_sorting_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "HIGHER_LOWER_STREAK":
            package = mechanic_engine.generate_higher_lower_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "ELIMINATION_SURVIVAL":
            package = mechanic_engine.generate_elimination_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "COMPARISON_BRACKET":
            package = mechanic_engine.generate_comparison_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "GRID_CONSTRAINT_BOARD":
            package = mechanic_engine.generate_grid_constraint_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "DRIVE_PROGRESSION":
            package = mechanic_engine.generate_drive_progression_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "ROSTER_BUILD":
            package = mechanic_engine.generate_roster_build_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "KNOCKOUT_BRACKET":
            package = mechanic_engine.generate_knockout_bracket_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "RELATIONSHIP_CHAIN":
            package = mechanic_engine.generate_relationship_chain_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "BRANCH_STATE":
            package = mechanic_engine.generate_branch_state_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "GUESS_THE_SEASON":
            package = mechanic_engine.generate_guess_the_season_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "PAIRWISE_COMPARE":
            package = mechanic_engine.generate_pairwise_compare_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "PICK_THE_IMPOSTOR":
            package = mechanic_engine.generate_pick_the_impostor_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "MISSING_PIECE":
            package = mechanic_engine.generate_missing_piece_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "BEFORE_AFTER":
            package = mechanic_engine.generate_before_after_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "CAREER_PATH":
            package = mechanic_engine.generate_career_path_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "RISK_IT":
            package = mechanic_engine.generate_risk_it_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "WAGER_MODE":
            package = mechanic_engine.generate_wager_mode_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "LEADERBOARD_CLIMB":
            package = mechanic_engine.generate_leaderboard_climb_round(variant=variant, seed=seed)
        elif taxonomy_id == "BLIND_RESUME":
            package = mechanic_engine.generate_blind_resume_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "DOUBLE_OR_NOTHING":
            package = mechanic_engine.generate_double_or_nothing_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "KING_OF_THE_HILL":
            package = mechanic_engine.generate_king_of_the_hill_round(variant=variant, seed=seed)
        elif taxonomy_id == "FACT_OR_FAKE":
            package = mechanic_engine.generate_fact_or_fake_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "GUESS_THE_RANKING":
            package = mechanic_engine.generate_guess_the_ranking_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "STAT_TARGET":
            package = mechanic_engine.generate_stat_target_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "REVERSE_TRIVIA":
            package = mechanic_engine.generate_reverse_trivia_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "THREE_STRIKES":
            package = mechanic_engine.generate_three_strikes_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "MYSTERY_ROSTER":
            package = mechanic_engine.generate_mystery_roster_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "DRAFT_PICK_LADDER":
            package = mechanic_engine.generate_draft_pick_ladder_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "CATEGORY_ROULETTE":
            package = mechanic_engine.generate_category_roulette_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "COMMON_LINK":
            package = mechanic_engine.generate_common_link_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        elif taxonomy_id == "STRATEGY_ARCADE":
            package = mechanic_engine.generate_strategy_arcade_round(variant=variant, seed=seed, **entry["gen_kwargs"])
        else:  # unreachable given PUBLIC_MECHANIC_MODES' own real contents, defensive only
            raise GatewayError("INVALID_MODE", f"mode={mode!r} has no public generator wired.")
    finally:
        _generation_semaphore.release()

    if package.get("qa_status") != "PASSED":
        oplog.record_event("public_mechanic_no_eligible", mode=mode)
        raise GatewayError("NO_ELIGIBLE_GAME", package.get("shortfall_reason") or
                            f"No qualifying round could be generated for mode={mode!r} right now.")

    stored = packages.save_package(package)
    progress = mechanic_engine.initial_progress(taxonomy_id)
    progress["taxonomy_id"] = taxonomy_id
    progress["public_mode"] = mode  # so submit-side telemetry can report which public mode this was, never used for trust decisions
    game_state.create_state(stored["package_id"], progress)

    view = mechanic_engine.client_safe_view(taxonomy_id, stored, progress)
    oplog.record_event("public_mechanic_round_started", mode=mode)
    return {
        "round_id": stored["package_id"], "mode": mode, "title": entry["title"], "kind": entry["kind"],
        "instructions": entry["instructions"], "metadata": {"contract_version": CONTRACT_VERSION},
        "view": view,
    }


def get_public_round(*, round_id: str) -> dict:
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        stored, progress = None, None
    if stored is None or progress is None or "public_mode" not in progress:
        # The "public_mode" check keeps this route scoped to rounds THIS
        # module created -- a real admin-created round_id (no public_mode
        # key) is reported not-found here, never silently served, even
        # though the underlying storage is shared (see module docstring).
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    taxonomy_id = progress["taxonomy_id"]
    view = mechanic_engine.client_safe_view(taxonomy_id, stored, progress)
    return {"round_id": round_id, "mode": progress["public_mode"], "view": view}


def submit_public_round(*, round_id: str, submission: dict) -> dict:
    from tools.director_v02 import mechanic_engine

    try:
        stored = packages.load_package(round_id)
        progress = game_state.load_state(round_id)
    except (packages.PackageIdInvalid, game_state.StateIdInvalid):
        stored, progress = None, None
    if stored is None or progress is None or "public_mode" not in progress:
        raise GatewayError("INVALID_GAME_ID", "No such game -- it may have expired or never existed.")

    taxonomy_id, mode = progress["taxonomy_id"], progress["public_mode"]
    try:
        result, new_progress = mechanic_engine.evaluate_submission(taxonomy_id, stored, progress, submission)
    except mechanic_engine.MechanicError as e:
        raise GatewayError("INVALID_REQUEST", str(e))
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        # Same real, found-and-fixed bug as the admin route's identical
        # guard (gateway/app.py's mechanics_submit_round) -- a malformed
        # submission shape (e.g. a string where a mapping/order was
        # expected) must fail cleanly, never a raw 500.
        raise GatewayError("INVALID_REQUEST", "This round has no more rounds/items to submit against, "
                            "or the submission was not shaped correctly for this mechanic.")

    new_progress["taxonomy_id"] = taxonomy_id
    new_progress["public_mode"] = mode
    game_state.save_state(round_id, new_progress)
    view = mechanic_engine.client_safe_view(taxonomy_id, stored, new_progress)
    oplog.record_event("public_mechanic_submitted", mode=mode,
                        correct=result.get("correct") if isinstance(result.get("correct"), bool) else None)
    return {"round_id": round_id, "mode": mode, "result": result, "view": view}
