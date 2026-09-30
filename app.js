// Bump both when shipping a change worth surfacing in the footer — APP_VERSION
// for any real feature/content change, CONTENT_UPDATED specifically when a
// question bank (data/*.js) changes, since that's the date players actually
// care about ("is the CFB bank still the old buggy one or the audited one").
var APP_VERSION = '3.20.0';
var CONTENT_UPDATED = 'Aug 4, 2026';
var SITE_URL = 'https://reads.football/';

// Director v0.5 local-only prototype flag. true = renders the real Player
// From Clues game, both from the hidden #clues route (see HIDDEN_ROUTES
// below, kept as a legacy deep link) and -- as of the UI/UX Upgrade Pass --
// a real LEAGUE_MODES.nfl card, surfaced on the home screen and NFL grid
// like any other mode. false makes the route, the card, the render branch,
// and the package-validation check all simultaneously inert -- no file
// deletion needed to roll back. See PLAYER_FROM_CLUES_FRONTEND_INTEGRATION_PLAN.md.
var ENABLE_PLAYER_FROM_CLUES_V01 = true;
// UI/UX Upgrade Pass: same real kill-switch discipline for the new CFB
// counterpart (data/cfb-player-from-clues-v01.js) -- false makes its
// LEAGUE_MODES.cfb card, render branch, and package-validation check all
// simultaneously inert.
var ENABLE_CFB_PLAYER_FROM_CLUES_V01 = true;

// Director v0.6 Gateway dev-loop flag. Default OFF -- this is NOT the
// production path (see READS_ENGINE_GATEWAY_V01_REPORT.md, Part O). When
// true AND window.PLAYER_FROM_CLUES_GATEWAY_DEV has real content (written by
// tools/gateway_dev_client.py against a locally-running Gateway), the
// existing Player From Clues renderer plays THAT package instead of the
// static baseline (window.PLAYER_FROM_CLUES_V01) -- proving the same
// renderer can consume a package that came from Reads -> Gateway ->
// Director -> Warehouse -> QA, not just a pre-generated static file. The
// static baseline is never modified or replaced by this flag.
var ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01 = false;

// Director v0.7/v1.2 pilot flags, Gateway URL. Default OFF (Part 33) --
// when true, the hidden #draftpilot / #championshippilot routes render a
// NEW mode that fetches a real, engine-generated question LIVE from the
// Gateway's public API (/v1/public/game, /v1/public/game/answer -- no
// admin token anywhere in this file, by construction: those routes don't
// require one) instead of reading from a local data/*.js file. These are
// the only Reads modes that depend on a network round-trip for their
// actual game content -- every other mode, including the
// ENABLE_ENGINE_QUIZ_DRAFT-merged "NFL Draft History" Quiz category
// below, remains 100% local/offline. When OFF, or if the Gateway is
// unreachable while ON, each pilot falls back to a real, already-working
// Quiz category -- see ENGINE_PILOT_MODES below.
//
// v1.4, Parts 12/13/29/30: read from `reads-config.js`'s small runtime
// config surface (loaded before this file, see index.html) instead of a
// hardcoded constant here -- lets an operator flip a pilot on/off or
// repoint the Gateway URL by editing ONE small, separate, low-risk file,
// never this one. Fails closed (Part 13): if reads-config.js failed to
// load at all, or `window.READS_CONFIG` is missing/malformed, every
// pilot reads as OFF here -- `=== true` never accidentally passes for a
// missing, null, or truthy-but-not-boolean value.
var READS_CONFIG = (typeof window !== 'undefined' && window.READS_CONFIG) || {};
var ENABLE_ENGINE_DRAFT_PILOT_V01 = READS_CONFIG.enableEngineDraftPilot === true;
var ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01 = READS_CONFIG.enableEngineChampionshipPilot === true;
// v1.7, Part C: same fail-closed pattern as the two flags above -- default
// OFF, only on if reads-config.js explicitly says so.
var ENABLE_ENGINE_SIX_DEGREES_V01 = READS_CONFIG.enableEngineSixDegrees === true;
// v1.8, Part F/O: same fail-closed pattern -- the Starting Lineup proof-game
// capability, default OFF.
var ENABLE_ENGINE_LINEUP_PILOT_V01 = READS_CONFIG.enableEngineLineupPilot === true;
// CFB data enrichment operation: same fail-closed pattern -- the first CFB
// engine mode, default OFF.
var ENABLE_ENGINE_HEISMAN_PILOT_V01 = READS_CONFIG.enableEngineHeismanPilot === true;
// Weekly Pick'em Player Experience pass: same fail-closed pattern -- OFF
// until a real deploy + canary verification against production (see
// reads-config.js's own comment on this flag).
var ENABLE_PICKEM_V01 = READS_CONFIG.enablePickem === true;
// Public-readiness punch-list: same fail-closed pattern for every mode
// this pass either newly certified public (lineupCollege, after its
// starvation fix) or found already-public-but-frontend-invisible
// (nflGameResult/cfbGameResult/nflGameBoxscore -- real, live capabilities
// with zero UI entry point before this). All default OFF until
// individually canary-verified, same as every pilot above.
var ENABLE_ENGINE_LINEUP_COLLEGE_PILOT_V01 = READS_CONFIG.enableEngineLineupCollegePilot === true;
var ENABLE_ENGINE_NFL_GAME_RESULT_PILOT_V01 = READS_CONFIG.enableEngineNflGameResultPilot === true;
var ENABLE_ENGINE_CFB_GAME_RESULT_PILOT_V01 = READS_CONFIG.enableEngineCfbGameResultPilot === true;
var ENABLE_ENGINE_NFL_GAME_BOXSCORE_PILOT_V01 = READS_CONFIG.enableEngineNflGameBoxscorePilot === true;
// The four new mechanic-shaped public modes (matching/sorting/higher-lower/
// elimination) -- same fail-closed pattern, default OFF.
var ENABLE_ENGINE_MATCHING_PILOT_V01 = READS_CONFIG.enableEngineMatchingPilot === true;
var ENABLE_ENGINE_SORTING_PILOT_V01 = READS_CONFIG.enableEngineSortingPilot === true;
var ENABLE_ENGINE_STAT_LADDER_PILOT_V01 = READS_CONFIG.enableEngineStatLadderPilot === true;
var ENABLE_ENGINE_HIGHER_LOWER_PILOT_V01 = READS_CONFIG.enableEngineHigherLowerPilot === true;
var ENABLE_ENGINE_ELIMINATION_PILOT_V01 = READS_CONFIG.enableEngineEliminationPilot === true;
var ENABLE_ENGINE_GUESS_THE_SEASON_PILOT_V01 = READS_CONFIG.enableEngineGuessTheSeasonPilot === true;
var ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01 = READS_CONFIG.enableEngineHeadToHeadDuelPilot === true;
var ENABLE_ENGINE_BEST_OF_SEVEN_DUEL_PILOT_V01 = READS_CONFIG.enableEngineBestOfSevenDuelPilot === true;
var ENABLE_ENGINE_PICK_THE_IMPOSTOR_PILOT_V01 = READS_CONFIG.enableEnginePickTheImpostorPilot === true;
var ENABLE_ENGINE_UNIQUE_ONE_OUT_PILOT_V01 = READS_CONFIG.enableEngineUniqueOneOutPilot === true;
var ENABLE_ENGINE_MISSING_PIECE_PILOT_V01 = READS_CONFIG.enableEngineMissingPiecePilot === true;
var ENABLE_ENGINE_BEFORE_AFTER_PILOT_V01 = READS_CONFIG.enableEngineBeforeAfterPilot === true;
var ENABLE_ENGINE_MAP_THE_CAREER_PILOT_V01 = READS_CONFIG.enableEngineMapTheCareerPilot === true;
var ENABLE_ENGINE_CAREER_PATH_PILOT_V01 = READS_CONFIG.enableEngineCareerPathPilot === true;
var ENABLE_ENGINE_RISK_IT_PILOT_V01 = READS_CONFIG.enableEngineRiskItPilot === true;
var ENABLE_ENGINE_WAGER_MODE_PILOT_V01 = READS_CONFIG.enableEngineWagerModePilot === true;
var ENABLE_ENGINE_LEADERBOARD_CLIMB_PILOT_V01 = READS_CONFIG.enableEngineLeaderboardClimbPilot === true;
var ENABLE_ENGINE_BLIND_RESUME_PILOT_V01 = READS_CONFIG.enableEngineBlindResumePilot === true;
var ENABLE_ENGINE_DOUBLE_OR_NOTHING_PILOT_V01 = READS_CONFIG.enableEngineDoubleOrNothingPilot === true;
var ENABLE_ENGINE_KING_OF_THE_HILL_PILOT_V01 = READS_CONFIG.enableEngineKingOfTheHillPilot === true;
var ENABLE_ENGINE_FACT_OR_FAKE_PILOT_V01 = READS_CONFIG.enableEngineFactOrFakePilot === true;
var ENABLE_ENGINE_GUESS_THE_RANKING_PILOT_V01 = READS_CONFIG.enableEngineGuessTheRankingPilot === true;
var ENABLE_ENGINE_STAT_TARGET_PILOT_V01 = READS_CONFIG.enableEngineStatTargetPilot === true;
var ENABLE_ENGINE_REVERSE_TRIVIA_PILOT_V01 = READS_CONFIG.enableEngineReverseTriviaPilot === true;
var ENABLE_ENGINE_THREE_STRIKES_PILOT_V01 = READS_CONFIG.enableEngineThreeStrikesPilot === true;
var ENABLE_ENGINE_MYSTERY_ROSTER_PILOT_V01 = READS_CONFIG.enableEngineMysteryRosterPilot === true;
var ENABLE_ENGINE_DRAFT_PICK_LADDER_PILOT_V01 = READS_CONFIG.enableEngineDraftPickLadderPilot === true;
var ENABLE_ENGINE_CATEGORY_ROULETTE_PILOT_V01 = READS_CONFIG.enableEngineCategoryRoulettePilot === true;
var ENABLE_ENGINE_COMMON_LINK_PILOT_V01 = READS_CONFIG.enableEngineCommonLinkPilot === true;
// Reusable Game Format System pass: the new `comparison` mechanic backing
// BRACKET_TREE -- same flag-off-by-default pilot convention as the 4
// mechanics above, until this gets its own real player-experience pass.
var ENABLE_ENGINE_COMPARISON_PILOT_V01 = READS_CONFIG.enableEngineComparisonPilot === true;
// Creator stress test / discovery pass: the first 4 modes promoted
// straight from Creator-only to public certification (real candidate
// surveys in gateway/services/public_game.py) -- same fail-closed
// pattern, default OFF until individually canary-verified against
// production.
var ENABLE_ENGINE_OFFENSE_COLLEGE_PILOT_V01 = READS_CONFIG.enableEngineOffenseCollegePilot === true;
var ENABLE_ENGINE_SB_CHAMPION_OFFENSE_COLLEGE_PILOT_V01 = READS_CONFIG.enableEngineSbChampionOffenseCollegePilot === true;
var ENABLE_ENGINE_CFB_RANKING_PILOT_V01 = READS_CONFIG.enableEngineCfbRankingPilot === true;
var ENABLE_ENGINE_CFB_UPSET_PILOT_V01 = READS_CONFIG.enableEngineCfbUpsetPilot === true;
// Public Mode Wiring pass (Pass 2.5): 8 real backend capabilities newly
// certified public this pass (gateway/services/public_game.py's own
// PUBLIC_MODES entries carry the real candidate surveys) -- same
// fail-closed pattern, default OFF until individually canary-verified.
var ENABLE_ENGINE_CFB_RIVALRY_PILOT_V01 = READS_CONFIG.enableEngineCfbRivalryPilot === true;
var ENABLE_ENGINE_CFB_RIVALRY_LOOKUP_PILOT_V01 = READS_CONFIG.enableEngineCfbRivalryLookupPilot === true;
var ENABLE_ENGINE_CFB_SPOT_THE_FAKE_PILOT_V01 = READS_CONFIG.enableEngineCfbSpotTheFakePilot === true;
var ENABLE_ENGINE_CFB_THREE_CLUES_PILOT_V01 = READS_CONFIG.enableEngineCfbThreeCluesPilot === true;
var ENABLE_ENGINE_ERA_GAUNTLET_PILOT_V01 = READS_CONFIG.enableEngineEraGauntletPilot === true;
var ENABLE_ENGINE_CFB_ODD_COLLEGE_OUT_PILOT_V01 = READS_CONFIG.enableEngineCfbOddCollegeOutPilot === true;
var ENABLE_ENGINE_CFB_ONE_SCHOOL_MISSING_PILOT_V01 = READS_CONFIG.enableEngineCfbOneSchoolMissingPilot === true;
var ENABLE_ENGINE_FRANCHISE_MARATHON_PILOT_V01 = READS_CONFIG.enableEngineFranchiseMarathonPilot === true;
// Finish-10-Formats pass: the 10 new game formats' real backend/public
// pipeline (gateway/services/public_mechanics.py's PUBLIC_MECHANIC_MODES) --
// same fail-closed pattern as every pilot above, default OFF until
// individually canary-verified against production.
var ENABLE_ENGINE_CONNECTION_GRID_PILOT_V01 = READS_CONFIG.enableEngineConnectionGridPilot === true;
var ENABLE_ENGINE_PERFECT_DRIVE_PILOT_V01 = READS_CONFIG.enableEnginePerfectDrivePilot === true;
var ENABLE_ENGINE_GOAL_LINE_STAND_PILOT_V01 = READS_CONFIG.enableEngineGoalLineStandPilot === true;
var ENABLE_ENGINE_LINEUP_BUILDER_PILOT_V01 = READS_CONFIG.enableEngineLineupBuilderPilot === true;
var ENABLE_ENGINE_AUCTION_DRAFT_PILOT_V01 = READS_CONFIG.enableEngineAuctionDraftPilot === true;
var ENABLE_ENGINE_CAP_CHALLENGE_PILOT_V01 = READS_CONFIG.enableEngineCapChallengePilot === true;
var ENABLE_ENGINE_KNOCKOUT_TOURNAMENT_PILOT_V01 = READS_CONFIG.enableEngineKnockoutTournamentPilot === true;
var ENABLE_ENGINE_SIX_DEGREES_CHAIN_PILOT_V01 = READS_CONFIG.enableEngineSixDegreesChainPilot === true;
var ENABLE_ENGINE_CHAIN_REACTION_PILOT_V01 = READS_CONFIG.enableEngineChainReactionPilot === true;
var ENABLE_ENGINE_CHOOSE_YOUR_PATH_PILOT_V01 = READS_CONFIG.enableEngineChooseYourPathPilot === true;
// Never hardcode a machine-specific filesystem path here; this is a
// network origin, not a path. Falls back to the same local-dev value as
// before if reads-config.js didn't provide one -- a missing Gateway URL
// is not itself a security concern (unlike the flags above), so this one
// fallback is a convenience default, not a fail-closed requirement.
var ENGINE_GATEWAY_BASE_URL = READS_CONFIG.engineGatewayBaseUrl || 'http://localhost:8850';

/* ============================== utilities ============================== */
function lsGet(key, fallback) {
  try { var v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
  catch (e) { return fallback; }
}
function lsSet(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
// Hand-rolled inline SVG icon set (Feather/Lucide-style minimal line icons,
// 24x24, stroke=currentColor) — replaces emoji-as-icons across the app's
// utilitarian chrome (nav, header controls, mode cards, toolbars, feedback).
// Inline <svg> instead of an icon font/sprite sheet so there's zero external
// dependency and the icon always inherits `color` from its surrounding CSS.
// Emoji are kept everywhere else (badges, legends grade reactions, trivia
// content) — those are decorative/personality flourishes, not UI chrome.
var ICON_PATHS = {
  home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.04 1.56V21a2 2 0 0 1-4 0v-.09A1.7 1.7 0 0 0 9 19.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.65 15a1.7 1.7 0 0 0-1.56-1.04H3a2 2 0 0 1 0-4h.09A1.7 1.7 0 0 0 4.65 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.65a1.7 1.7 0 0 0 1.04-1.56V3a2 2 0 0 1 4 0v.09a1.7 1.7 0 0 0 1.04 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.35 9a1.7 1.7 0 0 0 1.56 1.04H21a2 2 0 0 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1.04Z"/>',
  football: '<ellipse cx="12" cy="12" rx="9" ry="6" transform="rotate(-40 12 12)"/><path d="M8.5 15.5 15.5 8.5M9.8 14.2h1M10.6 13h1.2M11.5 11.7h1.2M12.3 10.5h1"/>',
  graduationCap: '<path d="M2 9 12 4l10 5-10 5-10-5Z"/><path d="M6 11.5V17c0 1.1 2.7 2 6 2s6-.9 6-2v-5.5"/><path d="M22 9v6"/>',
  trophy: '<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 5H4a1 1 0 0 0-1 1v1a4 4 0 0 0 4 4"/><path d="M17 5h3a1 1 0 0 1 1 1v1a4 4 0 0 1-4 4"/><path d="M12 14v3"/><path d="M8 21h8"/><path d="M9.5 17h5l1 4h-7l1-4Z"/>',
  helpCircle: '<circle cx="12" cy="12" r="9"/><path d="M9.2 9a2.8 2.8 0 1 1 3.9 2.6c-.8.4-1.1.9-1.1 1.9"/><path d="M12 17h.01"/>',
  volumeOn: '<path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/><path d="M19 6a9 9 0 0 1 0 12"/>',
  volumeOff: '<path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M17 9l5 6M22 9l-5 6"/>',
  close: '<path d="M5 5l14 14M19 5 5 19"/>',
  restart: '<path d="M3 11a9 9 0 1 1 2.6 6.4"/><path d="M3 17v-5h5"/>',
  share: '<circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="M8.3 10.7 15.7 6.3M8.3 13.3l7.4 4.4"/>',
  download: '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M4 19h16"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/>',
  check: '<path d="M4 12.5 9.5 18 20 6"/>',
  xMark: '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
  flame: '<path d="M12 2c1 3-3 4-3 8a3 3 0 0 0 6 0c1.3 1 2 2.6 2 4.3A5.3 5.3 0 0 1 11.7 22 5.3 5.3 0 0 1 6.4 16.7C6.4 12 12 10 12 2Z"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/><path d="M12 2v3"/>',
  zap: '<path d="M12 2 4 14h7l-1 8 9-13h-7l1-7Z"/>',
  brain: '<path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 3.5 3.5 0 0 0-2 6.2A3.5 3.5 0 0 0 9 19a3 3 0 0 0 3-3"/><path d="M12 4a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1 2 6.2A3.5 3.5 0 0 1 15 19a3 3 0 0 1-3-3"/><path d="M12 4v12"/>',
  book: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  play: '<path d="M6 4.5v15l13-7.5-13-7.5Z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  sync: '<path d="M4 10a8 8 0 0 1 13.7-5.7L20 6.5"/><path d="M20 4v3.5h-3.5"/><path d="M20 14a8 8 0 0 1-13.7 5.7L4 17.5"/><path d="M4 20v-3.5h3.5"/>',
  flag: '<path d="M5 21V4"/><path d="M5 4h13l-3 4.5L18 13H5"/>',
  versus: '<circle cx="8" cy="8" r="3.2"/><path d="M2.5 20c0-3.6 2.5-6.2 5.5-6.2s5.5 2.6 5.5 6.2"/><circle cx="17.5" cy="9" r="2.6"/><path d="M15.2 20c.3-2.9 1.9-5 4.3-5.8"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  hofJacket: '<path d="M6 6H18V21H6Z"/><path d="M6 6 11 12"/><path d="M18 6 13 12"/><circle cx="9" cy="15" r="1.1"/>',
  cfpTrophy: '<path d="M12 3 8 9 12 15 16 9Z"/><path d="M10 15h4v3h-4Z"/><rect x="7" y="18" width="10" height="3" rx="1"/>',
  lombardiTrophy: '<ellipse cx="12" cy="6" rx="4" ry="2.6" transform="rotate(-25 12 6)"/><path d="M12 8.5v2.5"/><path d="M9 11h6l3 10H6Z"/>',
  arrowUp: '<path d="M12 20V4"/><path d="M5 11l7-7 7 7"/>',
  arrowDown: '<path d="M12 4v16"/><path d="M5 13l7 7 7-7"/>',
  arrowRight: '<path d="M4 12h16"/><path d="M13 5l7 7-7 7"/>',
  barChart: '<path d="M4 20V10"/><path d="M12 20V4"/><path d="M20 20v-7"/>',
  shield: '<path d="M12 3 5 6v6c0 4.4 3 7.4 7 9 4-1.6 7-4.6 7-9V6Z"/>',
  star: '<path d="M12 2.5 15 9l7 .8-5.2 4.8 1.4 6.9L12 18l-6.2 3.5 1.4-6.9L2 9.8 9 9Z"/>',
  // Reads Game Screens Visual Identity pass: two small additions, not a
  // library -- a person silhouette with a question mark (Who Am I) and a
  // plain padlock (Pick'em's locked/kicked-off game state).
  mystery: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a8 8 0 0 1 16 0v1"/><path d="M9.8 15.2a1.9 1.9 0 1 1 2.5 1.8c-.5.2-.8.6-.8 1.2"/><path d="M11.5 20.4h.01"/>',
  lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  // Public Mode Wiring pass: Era Gauntlet's own symbol -- a real timeline
  // (a line with era markers), not reused from an unrelated concept.
  timeline: '<path d="M3 12h18"/><circle cx="5" cy="12" r="1.6"/><circle cx="10.3" cy="12" r="1.6"/><circle cx="15.7" cy="12" r="1.6"/><circle cx="21" cy="12" r="1.6" fill="currentColor"/>',
  // Risk & Wager visual identity pass: a real filled heart for the
  // lives/strikes pip track (RISK_IT/THREE_STRIKES).
  heart: '<path d="M12 20.5S3.5 15.2 3.5 9.1A4.6 4.6 0 0 1 12 6.5a4.6 4.6 0 0 1 8.5 2.6C20.5 15.2 12 20.5 12 20.5Z"/>',
  // Brand revamp: the app's own signature shape (the wordmark's goalpost
  // silhouette) -- used as a recurring decorative motif (completion
  // screens, empty states), never as a generic UI icon.
  goalpost: '<path d="M5 3v9"/><path d="M19 3v9"/><path d="M5 12h14"/><path d="M12 12v9"/><path d="M9 21l3-3 3 3"/>',
  // User feedback: "Film Room" was using the plain book icon, which
  // "makes zero sense" for a film-study section -- a real clapperboard
  // instead (board + open diagonal-striped clapper + hinge line).
  clapperboard: '<rect x="3" y="8" width="18" height="12" rx="1.5"/><path d="M3 8 5.5 3h3L6 8Z"/><path d="M9.5 8 12 3h3l-2.5 5Z"/><path d="M16 8 17.5 3h3l-1 5Z"/><path d="M3 12h18"/>',
};
function icon(name, cls) {
  var body = ICON_PATHS[name] || '';
  return '<svg class="icon' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + '</svg>';
}
// Brand revamp: a large, low-opacity goalpost watermark -- the app's own
// signature shape, reserved for real "moment" screens (round complete,
// empty states) rather than sprinkled everywhere. Purely decorative
// (aria-hidden); callers position it via the wrapping .brand-watermark-
// host container (position:relative + overflow:hidden).
function brandWatermarkHtml() {
  return '<div class="brand-watermark" aria-hidden="true">' + icon('goalpost') + '</div>';
}
// Brand revamp (user request: "why would it not show the logo with a
// loading bar" for the mode-switch loading screen): the real Reads
// square logo (already precached by the service worker -- see sw.js's
// own CORE_ASSETS list, so this is instant on any return visit) plus an
// honest INDETERMINATE progress bar. Never a fake percentage -- this
// fires while real mode-data <script> files are downloading
// (loadModeDataThenRun), which has no real, trackable progress value to
// show, so a sliding bar (not a filling-to-100% one) is the honest
// choice. Reserved for real full-screen "entering a mode" loads, not
// every small in-flow fetch -- those keep the existing compact spinner.
function brandLoadingScreenHtml(labelText) {
  return '<div class="panel loading-panel brand-loading-panel" aria-busy="true">' +
    '<img src="assets/brand/reads-logo-square.jpg" alt="" aria-hidden="true" class="brand-loading-logo">' +
    '<div class="brand-loading-bar" aria-hidden="true"><div class="brand-loading-bar-fill"></div></div>' +
    '<div class="loading-text">Loading ' + esc(labelText) + '&hellip;</div></div>';
}
// Full Visual + Interactive Redesign pass: a shared segmented round-progress
// bar (matching the redesigned game-screen mockup) -- `current` is the
// real 0-based index already tracked by every caller (t.index/s.roundIndex),
// `total` the real round/queue length. Purely decorative (aria-hidden) --
// the caller's own "Question X of Y" text stays the accessible label.
// Capped at 12 visible segments (a 25-question IQ Test round would
// otherwise render 25 slivers too thin to read as distinct segments) --
// beyond that the text label alone carries the progress info.
function progressDotsHtml(current, total) {
  if (!total || total < 2 || total > 12) return '';
  var segs = '';
  for (var i = 0; i < total; i++) {
    var cls = i < current ? 'done' : (i === current ? 'current' : '');
    segs += '<span class="' + cls + '"></span>';
  }
  return '<div class="progress-dots" aria-hidden="true">' + segs + '</div>';
}
// Pairs a caller's own real "Question X of Y..." text label with the
// segmented dots above in one consistent row -- text stays first/primary
// (what a screen reader announces), dots are a purely visual add-on.
function quizProgressRowHtml(labelHtml, current, total) {
  var dots = progressDotsHtml(current, total);
  if (!dots) return '<div class="quiz-progress">' + labelHtml + '</div>';
  return '<div class="quiz-progress-row"><div class="quiz-progress">' + labelHtml + '</div>' + dots + '</div>';
}
// Stadium broadcast finish: all figures come from the current round.
// Decorative result motion is separate from the existing live feedback.
function broadcastMarqueeHtml(kicker, title, detail, compact) {
  return '<div class="classic-broadcast-marquee' + (compact ? ' broadcast-marquee-compact' : '') + '">' +
    '<span>' + esc(kicker) + '</span><strong>' + esc(title) + '</strong>' +
    (detail ? '<em>' + esc(detail) + '</em>' : '') + '</div>';
}
function broadcastScorebugHtml(items) {
  return '<div class="broadcast-scorebug">' + items.map(function (item) {
    return '<div><span>' + esc(item[0]) + '</span><strong>' + esc(String(item[1])) + '</strong></div>';
  }).join('') + '</div>';
}
function broadcastCallHtml(correct, title) {
  return '<div class="broadcast-official-call ' + (correct ? 'broadcast-call-good' : 'broadcast-call-bad') + '" aria-hidden="true">' +
    '<span>OFFICIAL CALL</span><strong>' + esc(title || (correct ? 'THAT’S THE ONE' : 'NO GOOD')) + '</strong></div>';
}
function broadcastResultHtml(kicker, score, label, celebrate) {
  return '<section class="broadcast-result' + (celebrate ? ' broadcast-result-celebrate' : '') + '">' +
    brandWatermarkHtml() + '<span class="broadcast-result-kicker">' + esc(kicker) + '</span>' +
    '<strong class="broadcast-result-score">' + esc(String(score)) + '</strong>' +
    '<span class="broadcast-result-label">' + esc(label) + '</span>' +
    (celebrate ? '<div class="broadcast-result-sparks" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></div>' : '') + '</section>' + progressionResultHookHtml();
}
function broadcastClueMeterHtml(revealed, total) {
  var slots = '';
  for (var i = 0; i < total; i++) slots += '<span class="' + (i < revealed ? 'is-open' : '') + '">' + (i + 1) + '</span>';
  return '<div class="broadcast-clue-meter" aria-label="' + revealed + ' of ' + total + ' clues revealed">' +
    '<b>IDENTITY FILE</b><div aria-hidden="true">' + slots + '</div></div>';
}
function broadcastRecordHtml(wins, losses) {
  var slots = '';
  for (var i = 0; i < wins + losses; i++) slots += '<span class="' + (i < wins ? 'record-win' : 'record-loss') + '"></span>';
  return '<div class="broadcast-record" aria-hidden="true"><span>PROJECTED RECORD</span><div>' + slots + '</div></div>';
}
function broadcastGridHudHtml(g, cfb) {
  var correct = g.cells.filter(function (cell) { return cell.correct === true; }).length;
  return broadcastMarqueeHtml(cfb ? 'SATURDAY · GRID CHALLENGE' : 'NFL · GRID CHALLENGE', 'IMMACULATE GRID', 'Nine squares. Make every name count.', true) +
    broadcastScorebugHtml([['FILLED', g.answeredCount + '/9'], ['CORRECT', correct], ['RARITY PTS', g.totalScore]]);
}
function broadcastGridSelectionHtml(g) {
  var cell = g.cells[g.activeIndex];
  return '<div class="broadcast-grid-selection"><span>YOUR MATCHUP</span><strong>' +
    esc(g.rows[cell.r].label) + ' <i>×</i> ' + esc(g.cols[cell.c].label) + '</strong></div>';
}

// ============================== Reads Game Screen Visual Identity ==========
// One shared, compact header strip reused across every mechanic (Engine
// Pilot's ~12 modes, Weekly Pick'em, Who Am I) so every game screen carries
// the same subtle Reads branding -- icon + mode title, plus whichever of
// score/streak/difficulty actually apply to that mechanic -- without
// becoming a "giant branded poster." The question/content region below
// this is untouched; this only replaces each mode's own ad hoc title bar.
// Deliberately does NOT replace quizProgressRowHtml()/progressDotsHtml()
// (used by many other modes this pass doesn't touch) -- callers render
// this header, then their own progress row, exactly as before.
// Risk & Wager visual identity pass: a real pip track (filled = still
// have it, hollow = spent) -- shared by RISK_IT's lives and
// THREE_STRIKES' strikes, same depleting-left-to-right shape as a
// player would expect from either real-world concept.
function readsShellPipTrackHtml(iconName, total, remaining) {
  var pips = '';
  for (var i = 0; i < total; i++) {
    pips += '<span class="reads-shell-pip' + (i < remaining ? ' filled' : '') + '">' + icon(iconName) + '</span>';
  }
  return '<span class="reads-shell-pip-track">' + pips + '</span>';
}
function renderReadsShellHeader(opts) {
  opts = opts || {};
  var chips = '';
  if (opts.score != null) chips += '<span class="reads-shell-chip">' + esc(String(opts.score)) + '</span>';
  if (opts.streak != null) chips += '<span class="reads-shell-chip reads-shell-chip-streak">' + icon('flame') + ' ' + esc(String(opts.streak)) + '</span>';
  if (opts.difficulty) chips += '<span class="reads-shell-chip">' + esc(opts.difficulty) + '</span>';
  if (opts.badge) chips += '<span class="reads-shell-chip reads-shell-chip-accent">' + esc(opts.badge) + '</span>';
  // Risk & Wager visual identity pass: lives (RISK_IT) and strikes
  // (THREE_STRIKES) are both "N of a real starting budget remaining" --
  // rendered as a depleting pip track rather than plain "Lives: 2" text.
  if (opts.lives != null && opts.livesTotal != null) {
    chips += '<span class="reads-shell-chip reads-shell-chip-lives">' + readsShellPipTrackHtml('heart', opts.livesTotal, opts.lives) + '</span>';
  }
  if (opts.strikes != null && opts.strikesTotal != null) {
    chips += '<span class="reads-shell-chip reads-shell-chip-strikes">' + readsShellPipTrackHtml('xMark', opts.strikesTotal, opts.strikes) + '</span>';
  }
  // Real risk tier (LOW/MEDIUM/HIGH), color-coded green/gold/red so the
  // stakes read at a glance once a tier is committed.
  if (opts.tier) {
    chips += '<span class="reads-shell-chip reads-shell-chip-tier reads-shell-chip-tier-' + esc(opts.tier.name.toLowerCase()) + '">' +
      esc(opts.tier.name) + (opts.tier.points != null ? ' &middot; ' + esc(String(opts.tier.points)) + (opts.tier.points === 1 ? ' pt' : ' pts') : '') + '</span>';
  }
  // Brand revamp (user request: "the logo pop up in the Game modes in
  // the backgrounds"): a large, very quiet goalpost watermark behind
  // this shared header -- renders at the top of every enginePilot/
  // mechanicPilot format + Who Am I (~30 formats), so it's a real,
  // recurring presence throughout an actual play session, not just a
  // one-off completion moment. Bounded to the header's own box
  // (.reads-shell-header's own overflow:hidden) rather than the whole
  // panel, so it can't visually collide with real game content below.
  return '<div class="reads-shell-header">' +
    '<div class="reads-shell-header-watermark" aria-hidden="true">' + icon('goalpost') + '</div>' +
    '<div class="reads-shell-id">' +
    (opts.icon ? '<span class="reads-shell-icon">' + icon(opts.icon) + '</span>' : '') +
    '<span class="reads-shell-title">' + esc(opts.title || '') + '</span>' +
    '</div>' +
    (chips ? '<div class="reads-shell-chips">' + chips + '</div>' : '') +
    (opts.restartAttr ? '<button class="btn-tiny reads-shell-exit" ' + opts.restartAttr + ' aria-label="Restart">' + icon('restart') + '</button>' : '') +
    (opts.hideExit ? '' : '<button class="btn-tiny reads-shell-exit" ' + (opts.exitAttr || 'data-mode-exit') + '>' + icon('close') + ' Exit</button>') +
    '</div>';
}

// Shared two-sided selection component (Section 4 of the visual-identity
// pass): every genuinely binary mechanic -- NFL/CFB game-winner guesses,
// Weekly Pick'em matchups, CFB stat comparisons -- renders through this one
// function instead of five independent hand-built binary UIs. Deliberately
// does NOT touch Higher/Lower's own existing `.hl-card`/`.hl-guess-row`
// component (already bespoke and working -- see its own render code) but
// shares its visual language (large equally-weighted side-by-side cards,
// a center VS divider) so the two read as siblings, not two unrelated
// designs.
//
// sideA/sideB: { code, label, sublabel, meta, state: 'default'|'selected'|
//   'correct'|'wrong'|'locked', reveal (optional extra line shown once
//   answered/locked, e.g. a final score or a real stat value) }
// opts: { dataAttr: the data-* attribute name each side's button carries
//   with that side's `code` as its value (caller wires the click handler),
//   disabled: true once locked/answered, centerLabel: defaults to 'VS' }
function renderBinaryChoiceHtml(sideA, sideB, opts) {
  opts = opts || {};
  var dataAttr = opts.dataAttr || 'data-binary-choice';
  function side(s) {
    var cls = 'binary-choice-card';
    if (s.state === 'selected') cls += ' selected';
    if (s.state === 'correct') cls += ' correct';
    if (s.state === 'wrong') cls += ' wrong';
    var disabledAttr = opts.disabled ? ' disabled' : '';
    var extraAttrs = opts.extraAttrs ? ' ' + opts.extraAttrs : '';
    return '<button class="' + cls + '"' + disabledAttr + extraAttrs + ' ' + dataAttr + '="' + esc(s.code) + '">' +
      '<span class="binary-choice-label">' + esc(s.label) + '</span>' +
      (s.sublabel ? '<span class="binary-choice-sublabel">' + esc(s.sublabel) + '</span>' : '') +
      (s.meta ? '<span class="binary-choice-meta">' + esc(s.meta) + '</span>' : '') +
      (s.reveal ? '<span class="binary-choice-reveal">' + esc(s.reveal) + '</span>' : '') +
      '</button>';
  }
  return '<div class="binary-choice-row">' +
    side(sideA) +
    '<div class="binary-choice-vs">' + icon('versus') + '</div>' +
    side(sideB) +
    '</div>';
}

// Shared "equal candidate cards" component (Public Mode Wiring pass) --
// Odd College Out ("player selects the outlier") and One School Missing
// ("grouped-card display" for its real, confirmed-UNORDERED group-
// membership question -- see cfb_one_school_missing.py's own real shape)
// both want the same real thing: N equally-weighted real options
// presented as a grid, not a vertical A/B/C/D list. Reuses the exact
// .quiz-option correct/wrong/selected semantics under new class names so
// grading feedback looks and behaves identically to every other mode.
function renderCandidateCardsHtml(options, opts) {
  opts = opts || {};
  var dataAttr = opts.dataAttr || 'data-candidate-card';
  return '<div class="candidate-cards-grid">' +
    options.map(function (opt, i) {
      var cls = 'candidate-card';
      if (opts.state) cls += ' ' + opts.state(i, opt);
      var disabledAttr = opts.disabled ? ' disabled' : '';
      return '<button class="' + cls + '"' + disabledAttr + ' ' + dataAttr + '="' + i + '">' +
        '<span class="candidate-card-label">' + esc(opt) + '</span></button>';
    }).join('') +
    '</div>';
}

function slugify(s) { return (String(s).toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')) || 'player'; }
// Screen-by-Screen Polish pass: a real, reproducible bug found live on
// mobile -- every modal in this app (onboarding, share, rating, report,
// team picker, auth, mode sheet) follows the same accessible-dialog
// pattern of restoring focus to whatever triggered it on close. For a
// modal that opens automatically (onboarding's own first-load auto-open,
// with no real user click that triggered it), the "trigger element"
// captured is just whatever document.activeElement happened to be at
// that moment -- which turns out to be <main id="app"> itself (it carries
// tabindex="-1" for a real, separate reason: so screen readers can be
// sent there deliberately elsewhere). Focusing that page-spanning element
// makes the browser scroll it into view, which reads as a jarring ~60px
// jump on mobile the instant a player taps "Skip". Restoring focus to
// #app (or document.body, the only other value document.activeElement
// ever meaningfully defaults to with nothing focused) is never a real,
// intentional focus target for any of these modals, so this shared
// helper simply skips the restore in that case -- every other real
// trigger element (an actual button the player clicked) still gets focus
// back exactly as before.
function restoreFocus(el) {
  if (!el || !document.contains(el)) return;
  if (el.id === 'app' || el === document.body) return;
  el.focus();
}
function shuffle(arr) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
function normName(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim(); }
function fmtTime(sec) { sec = Math.max(0, Math.ceil(sec)); var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }

// Shuffled-deck draw, shared by every mode that pulls a random subset out of a
// much bigger pool (quiz rounds, IQ tests, speed sessions, silhouette rounds).
// A fresh shuffle-and-slice each time lets the same handful of items cluster
// by chance; this instead persists a shuffled "deck" per pool (localStorage,
// keyed so different filters/categories get their own independent deck) and
// draws off the front of it, refilling with a new shuffle of whatever hasn't
// been seen yet once it runs low — so the full pool cycles once before
// anything repeats.
function drawNoRepeat(deckKey, ids, count) {
  var storKey = 'deck__' + deckKey;
  var idSet = {};
  ids.forEach(function (id) { idSet[id] = true; });
  var deck = lsGet(storKey, []).filter(function (id) { return idSet[id]; });
  if (deck.length < count) {
    var leftoverSet = {};
    deck.forEach(function (id) { leftoverSet[id] = true; });
    var refill = shuffle(ids.filter(function (id) { return !leftoverSet[id]; }));
    deck = deck.concat(refill);
  }
  var drawn = deck.slice(0, count);
  lsSet(storKey, deck.slice(count));
  return drawn;
}

/* ============================== Engine vNext content memory + QA ============================== */
function contentMemoryKey() { return 'readsContentMemory__' + slugify(state.name || 'guest'); }
function getContentMemory() {
  var m=lsGet(contentMemoryKey(),{questions:[],entities:[]});
  // Migration from the interrupted/older Endless draft, which stored an
  // array of {key,entity,...} rows under the same key. Convert once into
  // the compact vNext shape so old local data cannot break new selection.
  if (Array.isArray(m)) {
    var q=[], e=[];
    m.forEach(function(x){ if(x&&x.key)q.push(String(x.key)); if(x&&x.entity)e.push(String(x.entity)); });
    return { questions:q.slice(-180), entities:e.slice(-120) };
  }
  m=m&&typeof m==='object'?m:{};
  m.questions=Array.isArray(m.questions)?m.questions:[];
  m.entities=Array.isArray(m.entities)?m.entities:[];
  return m;
}
function contentFingerprint(q, league) { return (league||'nfl')+'|'+hashStr(normName(q&&q.question||'')); }
function questionEntityTokens(q) {
  if(!q)return [];
  var correct=(q.options&&typeof q.correctIndex==='number')?q.options[q.correctIndex]:'';
  var text=String(q.question||'')+' '+String(correct||'');
  var stop={who:1,which:1,what:1,when:1,where:1,how:1,nfl:1,cfb:1,team:1,player:1,season:1,game:1,'which team':1,'which player':1,'what team':1,'what player':1};
  var tokens=(text.match(/\b[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){0,2}\b/g)||[])
    .map(normName).filter(function(x){return x.length>=3&&!stop[x]&&!/^(who|which|what|when|where|how)\b/.test(x);});
  var c=normName(correct);
  if(c&&c.length>=3&&!stop[c])tokens.push(c);
  var seen={}; return tokens.filter(function(x){if(seen[x])return false;seen[x]=true;return true;}).slice(0,6);
}
function rememberContentQuestion(q, league) {
  if(!q)return;
  var m=getContentMemory(), fp=contentFingerprint(q,league);
  m.questions=m.questions.filter(function(x){return x!==fp;}); m.questions.push(fp);
  questionEntityTokens(q).forEach(function(e){m.entities=m.entities.filter(function(x){return x!==e;});m.entities.push(e);});
  m.questions=m.questions.slice(-180); m.entities=m.entities.slice(-120); lsSet(contentMemoryKey(),m);
}
function contentRepeatPenalty(q, league) {
  var m=getContentMemory(), penalty=0, fp=contentFingerprint(q,league);
  if(m.questions.slice(-90).indexOf(fp)!==-1) penalty+=100;
  var recent={};m.entities.slice(-50).forEach(function(e){recent[e]=(recent[e]||0)+1;});
  questionEntityTokens(q).forEach(function(e){if(recent[e])penalty+=12*recent[e];});
  return penalty;
}
function mergeContentMemory(local, cloud) {
  local=local||{questions:[],entities:[]}; cloud=cloud||{questions:[],entities:[]};
  function mergeRecent(a,b,limit){var seen={},out=[];(a||[]).concat(b||[]).forEach(function(x){if(!x||seen[x])return;seen[x]=true;out.push(x);});return out.slice(-limit);}
  return {questions:mergeRecent(local.questions,cloud.questions,180),entities:mergeRecent(local.entities,cloud.entities,120)};
}
function questionQualityScore(q, league, targetDifficulty) {
  if(!q||typeof q.question!=='string'||!Array.isArray(q.options)||q.options.length<2)return 0;
  if(typeof q.correctIndex!=='number'||q.correctIndex<0||q.correctIndex>=q.options.length)return 0;
  var normalized=q.options.map(normName), unique={}; normalized.forEach(function(x){unique[x]=true;});
  if(Object.keys(unique).length!==q.options.length)return 0;
  var score=100;
  if(q.question.length<12)score-=25;
  if(q.question.length>220)score-=10;
  if(!normName(q.options[q.correctIndex]))score-=50;
  score-=Math.min(60,contentRepeatPenalty(q,league));
  if(targetDifficulty && String(q.difficulty||'').toLowerCase()!==String(targetDifficulty).toLowerCase())score-=8;
  return Math.max(0,score);
}
function qualityFilteredQuestions(pool, league, targetDifficulty) {
  var scored=(pool||[]).map(function(q){return {q:q,score:questionQualityScore(q,league,targetDifficulty)};})
    .filter(function(x){return x.score>=55;}).sort(function(x,y){return y.score-x.score;});
  return scored.length?scored.map(function(x){return x.q;}):(pool||[]).slice();
}
function drawGlobalNoRepeatQuestions(deckKey, pool, count, league, targetDifficulty) {
  var quality=qualityFilteredQuestions(pool,league,targetDifficulty);
  var fresh=quality.filter(function(q){return contentRepeatPenalty(q,league)<60;});
  var source=fresh.length>=Math.min(count,quality.length)?fresh:quality;
  var ids=drawNoRepeat(deckKey,source.map(function(q){return q.id;}),count);
  ids.forEach(function(id){var q=source.find(function(x){return x.id===id;});if(q)rememberContentQuestion(q,league);});
  return ids;
}

/* ============================== data + state ============================== */
/* ---- Engine content integration, Engine ID namespace 500000+ ----
   Kill switch: set to false to make the app behave exactly as it did before this
   integration — QUIZ stays the original hand-authored array and nothing else
   changes. See QUIZ_ENGINE_PRODUCTION_ROLLOUT_REPORT.md for the full rollout audit.
   App-Wide Engine Migration operation: generalized from a single hardcoded
   Draft source to a list of (global, label) sources so newly-registered
   Engine domains (e.g. NFL/CFB Game Results, built on the real automatically-
   refreshed games tables) blend in the same way without duplicating this
   validation logic per source. Each source is validated and folded in
   independently, in order -- one bad source only drops itself, never the
   others (a real improvement over the original all-or-nothing behavior,
   which would have silently discarded every other Engine source too). */
var ENABLE_ENGINE_QUIZ_DRAFT = true;
var ENGINE_QUIZ_SOURCES = [
  { key: 'QUIZ_DATA_ENGINE_DRAFT', enabled: function () { return ENABLE_ENGINE_QUIZ_DRAFT; } },
  { key: 'QUIZ_DATA_ENGINE_GAME_RESULT', enabled: function () { return ENABLE_ENGINE_QUIZ_DRAFT; } },
];

function buildEffectiveQuizPool(handAuthored, sources) {
  var pool = handAuthored.slice();
  var existingIds = {}, existingQuestions = {};
  pool.forEach(function (q) { existingIds[q.id] = true; existingQuestions[q.question] = true; });
  sources.forEach(function (src) {
    if (!src.enabled()) return;
    var engineSet = window[src.key];
    if (!Array.isArray(engineSet) || !engineSet.length) {
      console.warn('Engine Quiz source ' + src.key + ' unavailable or empty — skipped.');
      return;
    }
    var seenEngineIds = {}, valid = true;
    for (var i = 0; i < engineSet.length; i++) {
      var q = engineSet[i];
      // Deliberately no "category must already exist among hand-authored
      // categories" check (the original Draft-only version had one) -- a
      // genuinely new Engine domain is allowed to introduce a genuinely new
      // category; quizCategories() already derives its filter list live
      // from QUIZ itself (see below), so a new category needs no UI change
      // to become selectable.
      var ok = q && typeof q === 'object' &&
        typeof q.id === 'number' &&
        typeof q.category === 'string' && q.category &&
        typeof q.difficulty === 'string' && ['Easy', 'Medium', 'Hard'].indexOf(q.difficulty) !== -1 &&
        typeof q.question === 'string' && q.question &&
        Array.isArray(q.options) && q.options.length === 4 && new Set(q.options).size === 4 &&
        typeof q.correctIndex === 'number' && q.correctIndex >= 0 && q.correctIndex <= 3 &&
        typeof q.notes === 'string' &&
        !existingIds[q.id] && !seenEngineIds[q.id] &&
        !existingQuestions[q.question];
      if (!ok) {
        console.warn('Engine Quiz source ' + src.key + ' failed validation at index ' + i + ' — source skipped.');
        valid = false;
        break;
      }
      seenEngineIds[q.id] = true;
    }
    if (!valid) return;
    // pool/window.* sources are never mutated -- concat-equivalent via push
    // onto the local `pool` copy only.
    engineSet.forEach(function (q) {
      pool.push(q);
      existingIds[q.id] = true;
      existingQuestions[q.question] = true;
    });
  });
  return pool;
}
var QUIZ = buildEffectiveQuizPool(window.QUIZ_DATA || [], ENGINE_QUIZ_SOURCES);
var XSO = window.XSO_DATA || [];
// Football Learning Engine, Defensive Coverages module -- structured
// concepts/relationships/lessons/exercises, lazy-loaded like every other
// Learn section data file (see LEARN_SECTIONS' 'coverageClassroom' entry
// and openLearnSection()). Exported from the Engine's knowledge graph by
// tools/learn/export_coverage_module.py -- see that script and
// tools/learn/build_coverage_module.py for full provenance.
var LEARN_COVERAGES = window.LEARN_COVERAGE_MODULE || null;
// Football Learning Engine, full Encyclopedia module -- concepts across
// every football domain (positions, personnel, formations, route tree,
// passing concepts, run game, blocking, protection, QB play, defensive
// fronts/personnel/pressures/philosophy, special teams, situational,
// play calling, scouting, film study, history, geometry, coaching,
// officiating, rules, offensive systems), plus NFL/CFB team scheme
// profiles and historical statistical leaders. A SEPARATE data file/entry
// point from the Coverage Classroom above -- that module's lessons/
// exercises are untouched; this one is a browse-first encyclopedia (see
// renderEncyclopediaScreen()). Exported by
// tools/learn/export_encyclopedia_module.py -- see that script and
// tools/learn/build_encyclopedia_module.py for full provenance back to
// the exact source workbook (sheet, row) for every field.
var LEARN_ENCYCLOPEDIA = window.LEARN_ENCYCLOPEDIA || null;
// Football 101 Interactive Redesign: data-driven formation/front/coverage/
// concept diagram library (data/football-diagrams.js, generated by
// tools/learn/build_football_diagrams.py) plus its DOM-free SVG renderer
// (football-field.js). Both lazy-load alongside the encyclopedia data --
// see LEARN_SECTIONS' footballEncyclopedia entry below.
var FOOTBALL_DIAGRAMS = window.FOOTBALL_DIAGRAMS || null;
var FootballField = window.FootballField || null;
// Encyclopedia Diagrams + Deep Dives pass (data/encyclopedia-deep-dives.js):
// real "closest matching diagram" overrides + authored deep-dive text for
// concepts f101DiagramFor()'s own exact-canonical_id match can't reach --
// see that file's own module comment for the full real-signal reasoning.
var ENCYCLOPEDIA_DEEP_DIVES = window.ENCYCLOPEDIA_DEEP_DIVES || null;
var GRID_PLAYERS = window.GRID_PLAYERS || [];
var GRID_CRITERIA = window.GRID_CRITERIA || { team: [], stat: [], all: [] };
var BLITZ_LISTS = window.BLITZ_LISTS || [];
var SILHOUETTE_PLAYERS = window.SILHOUETTE_PLAYERS || [];
// App-Wide Engine Migration operation: CFB Quiz gets the same Engine-blending
// treatment NFL Quiz already had (buildEffectiveQuizPool is fully generic --
// see its own comment above). Real CFB Game Results content, built on
// tools/data_refresh/cfb_games_refresh.py's automatically-refreshed
// cfb_games_canonical table.
var ENGINE_CFB_QUIZ_SOURCES = [
  { key: 'QUIZ_DATA_ENGINE_CFB_GAME_RESULT', enabled: function () { return ENABLE_ENGINE_QUIZ_DRAFT; } },
];
var CFB = buildEffectiveQuizPool(window.CFB_DATA || [], ENGINE_CFB_QUIZ_SOURCES);
// CFB Speed audited (App-Wide Engine Migration, Part C): cfbSpeedQueue()
// reads CFB_SPEED directly, a wholly separate hand-authored pool from CFB
// (NFL Speed, by contrast, already shares QUIZ itself with NFL Quiz --
// speedQueue() reads QUIZ.map(...) directly, so it inherited Engine content
// automatically). Same identical record shape as CFB_DATA (verified: id/
// category/difficulty/question/options/correctIndex/notes), so the same
// buildEffectiveQuizPool blend applies unchanged -- CFB Speed gains the same
// real CFB_GAME_RESULT Engine content, independent of CFB's own copy of it
// (each call folds the Engine source into its own hand-authored base; the
// 1,415 existing CFB Speed questions are fully preserved as depth/fallback).
var CFB_SPEED = buildEffectiveQuizPool(window.CFB_SPEED_DATA || [], ENGINE_CFB_QUIZ_SOURCES);
var CFB_BLITZ_LISTS = window.CFB_BLITZ_LISTS || [];
var CFB_GRID_PLAYERS = window.CFB_GRID_PLAYERS || [];
var CFB_GRID_CRITERIA = window.CFB_GRID_CRITERIA || { team: [], stat: [], all: [] };
var HL_PASSING = window.HL_PASSING || [];
var HL_RUSHING = window.HL_RUSHING || [];
var HL_RECEIVING = window.HL_RECEIVING || [];
var HL_TACKLES = window.HL_TACKLES || [];
var HL_INTERCEPTIONS = window.HL_INTERCEPTIONS || [];
var HL_FUMBLES = window.HL_FUMBLES || [];
var HL_FIELDGOALS = window.HL_FIELDGOALS || [];
var HL_PUNTING = window.HL_PUNTING || [];
var HL_RETURNS = window.HL_RETURNS || [];
var HL_CONTRACTS = window.HL_CONTRACTS || [];
var HL_STADIUMS = window.HL_STADIUMS || [];

var DEFAULT_STATS = {
  quiz: { correctTotal: 0, questionsTotal: 0, roundsPlayed: 0, bestPct: 0 },
  xso: { correctTotal: 0, questionsTotal: 0, roundsPlayed: 0, bestPct: 0 },
  grid: { bestScore: 0, gamesPlayed: 0, cleanSweeps: 0 },
  blitz: { bestMatched: 0, attempts: 0 },
  speed: { bestScore: 0, bestStreak: 0, sessionsPlayed: 0 },
  silhouette: { bestScore: 0, roundsPlayed: 0, bestQuick: 0 },
  iq: { bestIQ: 0, testsTaken: 0 },
  legends: { bestWins: 0, bestScore: 0, bestGrade: '', gamesPlayed: 0 },
  higherLower: { bestStreak: 0, gamesPlayed: 0 },
  cfbQuiz: { correctTotal: 0, questionsTotal: 0, roundsPlayed: 0, bestPct: 0 },
  cfbIq: { bestIQ: 0, testsTaken: 0 },
  cfbSpeed: { bestScore: 0, bestStreak: 0, sessionsPlayed: 0 },
  cfbBlitz: { bestMatched: 0, attempts: 0 },
  cfbGrid: { bestScore: 0, gamesPlayed: 0, cleanSweeps: 0 },
  daily: { completions: 0, correctTotal: 0, questionsTotal: 0, bestPct: 0 },
  cfbLegends: { bestWins: 0, bestScore: 0, bestGrade: '', gamesPlayed: 0 },
  h2h: { wins: 0, losses: 0, ties: 0, matchesPlayed: 0 },
  endless: { bestScore: 0, bestStreak: 0, bestQuestions: 0, runs: 0 }
};

var lastFocusedScreen = null; // tracks screen changes for renderAll()'s focus management

var state = {
  name: lsGet('nflTriviaName', ''),
  screen: 'home',
  rankedPref: lsGet('nflTriviaRankedPref', {}),
  leaderboardMode: 'quiz',
  leaderboardRange: 'all',
  leaderboardData: [],
  stats: Object.assign({}, DEFAULT_STATS, lsGet('nflTriviaStats', {})),
  quiz: { screen: 'setup', category: '', difficulty: '', roundSize: 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] },
  xso: { screen: 'setup', category: '', difficulty: '', roundSize: 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] },
  grid: null,
  blitz: null,
  speed: null,
  silhouette: null,
  playerClues: null,
  playerCluesFilter: { decade: 'any', difficulty: 'any' },
  cfbPlayerClues: null,
  cfbPlayerCluesFilter: { decade: 'any', difficulty: 'any' },
  enginePilot: null,
  mechanicPilot: null,
  sixDegrees: null,
  creator: null,
  iq: null,
  legends: null,
  higherLower: null,
  cfbQuiz: { screen: 'setup', category: '', difficulty: '', roundSize: 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] },
  cfbIq: null,
  cfbSpeed: null,
  cfbBlitz: null,
  cfbGrid: null,
  daily: null,
  cfbLegends: null,
  h2h: null,
  h2hLive: null,
  study: null,
  learn: null,
  introTest: null,
  // Legacy compatibility flags for a Daily Reads that may have been
  // started from an older cached client before Daily Reads shipped.
  dailyChallengeActive: null,
  justCompletedDaily: null,
  // Same idea as dailyChallengeActive, but for a non-quiz-kind Head-to-Head
  // match currently being played inside another mode's own screen — see
  // h2hStartPlaying/h2hSubmitModeResult in the head-to-head section.
  h2hActive: null,
  // Transient UI state for the team-picker modal (screen: 'nfl'|'cfb',
  // filter: search text) — null while the modal's closed. The actual
  // favorite-team selections live in localStorage via getFavoriteTeams(),
  // not here, so they survive a refresh independent of this.
  teamPicker: null,
  friendCompare: null,
  settingsConfirmClear: false
};
// One-time migration: CFB 12-0 used to be "CFB 16-0" (a 16-game season —
// see the comment above the mode's code for why). Anyone who played it
// before that change may have a stored bestWins as high as 16, which would
// now render as an impossible negative-loss record (e.g. "15-(-3)") against
// the new 12-game max — clamp it down once so old data can't produce that.
if (state.stats.cfbLegends && state.stats.cfbLegends.bestWins > 12) state.stats.cfbLegends.bestWins = 12;

/* ============================== football rating ==============================
   A persistent, adaptive skill rating (separate from the one-off Football IQ Test
   score). Set once by a short blended NFL+CFB intro test the first time a name is
   entered, then nudged up/down by every subsequent game mode's result via a slow
   exponential moving average — one bad or lucky round barely moves it, but it
   drifts to reflect real performance over many sessions. Stored per name-slug so
   switching names doesn't carry someone else's rating along. */
var INTRO_TEST_SIZE = 16;
var RATING_DRIFT_ALPHA = 0.08;
function ratingKey() { return 'nflTriviaRating__' + slugify(state.name); }
// Rating now follows the same canonical-account rule as every other
// leaderboard mode. Existing name-keyed rating rows remain readable as a
// migration fallback until the account has written its UID-keyed row.
function ratingDocId() {
  return activeAuthUid ? ('account_' + activeAuthUid + '__rating') : ('rating__' + slugify(state.name));
}
function ratingPayload(r) {
  var fav = getFavoriteTeams();
  return {
    name: state.name,
    mode: 'rating',
    score: r.score,
    games: r.games || 0,
    playerKey: canonicalPlayerKey(),
    accountUid: activeAuthUid || null,
    favoriteNflTeam: fav.nfl || null,
    favoriteCfbTeam: fav.cfb || null
  };
}
function getRating() { return state.name ? lsGet(ratingKey(), null) : null; }
function setRating(r) {
  if (!state.name) return;
  lsSet(ratingKey(), r);
  if (window.__fbSync && window.__fbSync.pushScore) {
    window.__fbSync.pushScore(ratingDocId(), ratingPayload(r));
  }
}
function reconcileRating(list) {
  if (!state.name) return;
  var mySlug = slugify(state.name);
  var cloud = null;
  if (activeAuthUid) {
    cloud = list.find(function (r) { return r.mode === 'rating' && r.accountUid === activeAuthUid; });
  }
  if (!cloud) {
    cloud = list.find(function (r) { return r.mode === 'rating' && slugify(r.name || '') === mySlug; });
  }
  if (!cloud || typeof cloud.score !== 'number') return;
  var local = getRating();
  if (!local || (cloud.games || 0) > (local.games || 0)) {
    lsSet(ratingKey(), { score: cloud.score, games: cloud.games || 0 });
    pushRatingHistory(cloud.score);
    // If this came from a legacy name-keyed row for a real account, publish
    // the exact adopted value to the new UID-keyed row immediately.
    if (activeAuthUid && !cloud.accountUid && window.__fbSync && window.__fbSync.pushScore) {
      window.__fbSync.pushScore(ratingDocId(), ratingPayload({ score: cloud.score, games: cloud.games || 0 }));
    }
    if (state.screen === 'introTest') { state.introTest = null; state.screen = 'home'; }
    renderAll();
  } else if ((local.games || 0) > (cloud.games || 0) && window.__fbSync && window.__fbSync.pushScore) {
    window.__fbSync.pushScore(ratingDocId(), ratingPayload(local));
  } else if (activeAuthUid && !cloud.accountUid && window.__fbSync && window.__fbSync.pushScore) {
    window.__fbSync.pushScore(ratingDocId(), ratingPayload(local));
  }
}
// Cross-device sync for per-mode stats/badges/streak — the same "one doc
// per name, no password" idea reconcileRating() above already used for
// Football Rating, extended to the rest of state.stats. Unlike rating
// (one number, "more games played" is unambiguously more advanced), stats
// is ~17 mode objects with their own bests/counts — merged field-by-field,
// taking whichever device's value is further along for each field
// independently, so playing on two devices never LOSES progress on either
// one. bestGrade (a letter, not a number) needs its own rank table since
// Math.max() on 'S' vs 'A+' doesn't mean anything.
var STAT_GRADE_RANK = { S: 11, 'A+': 10, A: 9, 'A-': 8, 'B+': 7, B: 6, 'B-': 5, 'C+': 4, C: 3, D: 2, F: 1 };
function betterGrade(a, b) { return (STAT_GRADE_RANK[b] || 0) > (STAT_GRADE_RANK[a] || 0) ? b : (a || ''); }
function mergeStats(local, cloud) {
  if (!cloud) return local;
  var merged = {};
  Object.keys(DEFAULT_STATS).forEach(function (mode) {
    var l = local[mode] || {}, c = cloud[mode] || {}, out = {};
    Object.keys(DEFAULT_STATS[mode]).forEach(function (field) {
      out[field] = field === 'bestGrade' ? betterGrade(l[field], c[field]) : Math.max(Number(l[field]) || 0, Number(c[field]) || 0);
    });
    merged[mode] = out;
  });
  return merged;
}
// Streak isn't a running total like the stats above — it's inherently tied
// to actual calendar dates (miss a day, it resets), so "bigger number" and
// "more advanced" aren't the same thing here. Whichever device played most
// recently is the authoritative one; only fall back to comparing counts if
// they somehow played on the exact same date.
function mergeStreak(local, cloud) {
  if (!cloud || !cloud.lastPlayedDate) return local;
  if (!local.lastPlayedDate || cloud.lastPlayedDate > local.lastPlayedDate) return cloud;
  if (cloud.lastPlayedDate === local.lastPlayedDate && (cloud.count || 0) > (local.count || 0)) return cloud;
  return local;
}
function mergeFavoriteTeams(local, cloud) {
  local = local || { nfl: null, cfb: null, lastPicked: null, updatedAt: 0 };
  cloud = cloud || { nfl: null, cfb: null, lastPicked: null, updatedAt: 0 };
  return (Number(cloud.updatedAt) || 0) > (Number(local.updatedAt) || 0) ? cloud : local;
}
function pushProfileSnapshot() {
  if (!state.name || !window.__fbSync || !window.__fbSync.pushProfile) return;
  window.__fbSync.pushProfile(profileDocId(), {
    name: state.name,
    accountUid: activeAuthUid || null,
    stats: state.stats,
    streak: getStreak(),
    favoriteTeams: getFavoriteTeams(),
    dailyReads: dailyReadsProfileState(),
    rewards: rewardsProfileState(),
    progression: getProgression(),
    personalization: getPersonalizationState(),
    contentMemory: getContentMemory()
  });
}
// UID-keyed profiles are authoritative for real accounts. If this is the
// first load after migration, fall back once to the old username-keyed
// profile, merge it, and immediately republish under the UID.
function pullProfileSnapshot() {
  if (!state.name || !window.__fbSync || !window.__fbSync.getProfile) return;
  var canonicalId = profileDocId();
  var legacyId = slugify(state.name);
  window.__fbSync.getProfile(canonicalId).then(function (cloud) {
    if (cloud || canonicalId === legacyId) return { cloud: cloud, migrated: false };
    return window.__fbSync.getProfile(legacyId).then(function (legacy) {
      return { cloud: legacy, migrated: !!legacy };
    });
  }).then(function (result) {
    var cloud = result && result.cloud;
    if (!cloud) return;
    var beforeStats = JSON.stringify(state.stats);
    var beforeStreak = JSON.stringify(getStreak());
    var beforeFavorites = JSON.stringify(getFavoriteTeams());
    var beforeProgression = JSON.stringify(getProgression());
    var beforeDailyReads = JSON.stringify(dailyReadsProfileState());
    var beforeRewards = JSON.stringify(getRewards());
    var beforePersonalization = JSON.stringify(getPersonalizationState());
    var beforeContentMemory = JSON.stringify(getContentMemory());
    state.stats = mergeStats(state.stats, cloud.stats);
    var mergedStreak = mergeStreak(getStreak(), cloud.streak);
    var mergedFavorites = mergeFavoriteTeams(getFavoriteTeams(), cloud.favoriteTeams);
    var mergedProgression = mergeProgression(getProgression(), cloud.progression);
    var mergedDailyReads = mergeDailyReads(dailyReadsProfileState(), cloud.dailyReads);
    var mergedRewards = mergeRewards(getRewards(), cloud.rewards);
    var mergedPersonalization = mergePersonalization(getPersonalizationState(), cloud.personalization);
    var mergedContentMemory = mergeContentMemory(getContentMemory(), cloud.contentMemory);
    lsSet('nflTriviaStats', state.stats);
    lsSet(streakKey(), mergedStreak);
    lsSet(favoriteTeamsKey(), mergedFavorites);
    setProgression(mergedProgression);
    if (mergedDailyReads.result) lsSet(dailyKey(), mergedDailyReads.result);
    setDailyHistory(mergedDailyReads.history);
    setDailyRecords(mergedDailyReads.records);
    setDailyStreakClaims(mergedDailyReads.streakClaims);
    setRewards(mergedRewards, true);
    setPersonalizationState(mergedPersonalization, true);
    lsSet(contentMemoryKey(), mergedContentMemory);
    var changed = JSON.stringify(state.stats) !== beforeStats ||
      JSON.stringify(mergedStreak) !== beforeStreak ||
      JSON.stringify(mergedFavorites) !== beforeFavorites ||
      JSON.stringify(mergedProgression) !== beforeProgression ||
      JSON.stringify(mergedDailyReads) !== beforeDailyReads ||
      JSON.stringify(mergedRewards) !== beforeRewards ||
      JSON.stringify(mergedPersonalization) !== beforePersonalization ||
      JSON.stringify(mergedContentMemory) !== beforeContentMemory;
    if (changed || (result && result.migrated)) {
      pushProfileSnapshot();
      renderAll();
    }
  }).catch(function (err) { console.warn('Profile pull failed', err); });
}
// Friends list — deliberately just a local list of names, not another
// synced collection: nobody needs to see who's on someone else's list, and
// a plain localStorage array sidesteps friend-request/accept flow entirely.
// What each friend row shows is real, already-live data pulled from systems
// built above: their Football Rating comes straight out of the shared
// leaderboard state.leaderboardData already keeps live via onSnapshot, and
// their streak comes from the same per-name profiles doc pushProfileSnapshot()
// already writes for cross-device sync — no new backend concept needed.
var FRIENDS_KEY = 'nflTriviaFriends';
function getFriends() { return lsGet(FRIENDS_KEY, []); }
function setFriends(list) { lsSet(FRIENDS_KEY, list); }
function addFriend(name) {
  name = (name || '').trim();
  if (!name) return;
  var list = getFriends();
  if (list.some(function (f) { return slugify(f) === slugify(name); })) return;
  list.push(name);
  setFriends(list);
  var input = document.getElementById('friend-name-input');
  if (input) input.value = '';
  loadFriendsData();
}
function removeFriend(name) {
  setFriends(getFriends().filter(function (f) { return slugify(f) !== slugify(name); }));
  renderAll();
}
function friendLeaderboardIdentity(name) {
  var slug = slugify(name);
  return (state.leaderboardData || []).find(function (r) { return r.mode === 'rating' && slugify(r.name || '') === slug; }) || null;
}
function friendRatingFromLeaderboard(name) {
  var entry = friendLeaderboardIdentity(name);
  return entry ? { score: entry.score, games: entry.games || 0, accountUid: entry.accountUid || null } : null;
}
// Not a live listener like the leaderboard (that would mean one Firestore
// subscription per friend, torn down/rebuilt every time the list changes) —
// just a one-time fetch each time the Friends screen is opened, matching how
// pullProfileSnapshot() already treats profile docs as "check when you look,
// not watch forever."
var friendsProfileCache = {};
var friendsLoading = false;
function loadFriendsData() {
  var friends = getFriends();
  if (!friends.length || !window.__fbSync || !window.__fbSync.getProfile) { renderAll(); return; }
  friendsLoading = true;
  renderAll();
  Promise.all(friends.map(function (name) {
    var identity = friendLeaderboardIdentity(name);
    var uidProfileId = identity && identity.accountUid ? ('uid_' + identity.accountUid) : null;
    var legacyId = slugify(name);
    var first = uidProfileId ? window.__fbSync.getProfile(uidProfileId) : Promise.resolve(null);
    return first.then(function(profile) {
      if (profile || !uidProfileId) return profile;
      return window.__fbSync.getProfile(legacyId);
    }).then(function(profile) {
      friendsProfileCache[legacyId] = profile;
    }).catch(function () { friendsProfileCache[legacyId] = null; });
  })).then(function () {
    friendsLoading = false;
    renderAll();
  });
}
// Tracks how much the last updateRatingDrift() call actually moved the
// rating — read by each finish* function right after calling it, and shown
// on that round's share card. Reset to null at the top of every call so a
// Practice-mode round (which never calls updateRatingDrift at all) or a
// round played before any rating exists can't accidentally show a stale
// delta left over from a previous round.
var lastRatingDelta = null;
function updateRatingDrift(sessionPct) {
  lastRatingDelta = null;
  var r = getRating();
  if (!r) return;
  var before = r.score;
  var tierBefore = ratingTierFor(before);
  sessionPct = Math.max(0, Math.min(100, sessionPct));
  var sessionScore = 60 + sessionPct;
  r.score = Math.round(r.score * (1 - RATING_DRIFT_ALPHA) + sessionScore * RATING_DRIFT_ALPHA);
  r.games = (r.games || 0) + 1;
  setRating(r);
  lastRatingDelta = r.score - before;
  pushRatingHistory(r.score);
  showRatingMoveToast(tierBefore, ratingTierFor(r.score), r.score, lastRatingDelta);
}
// Fires after EVERY round that moves the rating (not just tier crossings)
// — the bar animates from where it sat before this round to where it sits
// now, so "your progress visibly moving" is something you see on every
// result, not just the rare moment you cross a tier line. A genuine tier
// change gets its own bigger/longer treatment (see the 'tier-toast-
// milestone' class) since a same-tier move and "you just became All-Pro"
// aren't the same size of moment. No sound here deliberately — this fires
// from inside updateRatingDrift(), which every finish* function calls
// immediately BEFORE its own playSound(); stacking a second sound here
// would just get cut off by that one a beat later (playSound() stops
// whatever's currently playing before starting the next clip).
var tierUpToastTimer = null;
function showRatingMoveToast(tierBefore, tierAfter, score, delta) {
  var el = document.getElementById('tier-up-toast');
  var fillEl = document.getElementById('tier-up-toast-fill');
  var tierEl = document.getElementById('tier-up-toast-tier');
  var deltaEl = document.getElementById('tier-up-toast-delta');
  var labelEl = document.getElementById('tier-up-toast-label');
  var iconEl = document.getElementById('tier-up-toast-icon');
  if (!el || !fillEl || !tierEl || !deltaEl) return;
  var tierChanged = tierAfter.min !== tierBefore.min;
  var wentUp = tierAfter.min > tierBefore.min;
  tierEl.textContent = tierAfter.name;
  deltaEl.textContent = (delta > 0 ? '+' : '') + delta + ' · ' + score;
  deltaEl.className = delta > 0 ? 'tier-up-toast-delta-up' : delta < 0 ? 'tier-up-toast-delta-down' : '';
  if (labelEl) labelEl.textContent = tierChanged ? (wentUp ? 'Tier Up!' : 'Tier Down') : 'Rating Update';
  if (iconEl) iconEl.textContent = tierChanged ? (wentUp ? '🎉' : '📉') : '🏈';
  el.classList.toggle('tier-toast-milestone', tierChanged);
  // Animate the fill FROM where it sat before TO where it sits now. A tier
  // change has no shared 0-100 scale between two different tiers to slide
  // across, so that case just fills up from empty into the new tier instead
  // of a meaningless cross-tier jump.
  fillEl.style.transition = 'none';
  fillEl.style.width = (tierChanged ? 0 : Math.round(tierBefore.pct * 100)) + '%';
  void fillEl.offsetWidth;
  fillEl.style.transition = '';
  fillEl.style.width = Math.round(tierAfter.pct * 100) + '%';
  el.classList.remove('show');
  void el.offsetWidth;
  el.classList.add('show');
  if (tierUpToastTimer) clearTimeout(tierUpToastTimer);
  tierUpToastTimer = setTimeout(function () { el.classList.remove('show'); }, tierChanged ? 3800 : 2200);
}
function introTestPool() {
  var half = Math.floor(INTRO_TEST_SIZE / 2);
  var nfl = shuffle(QUIZ).slice(0, half);
  var cfb = shuffle(CFB).slice(0, INTRO_TEST_SIZE - half);
  return shuffle(nfl.concat(cfb));
}
function startIntroTest() {
  state.introTest = { screen: 'intro', queue: [], index: 0, answers: [] };
  state.screen = 'introTest';
  renderAll();
}
function beginIntroQuestions() {
  state.introTest.queue = introTestPool();
  state.introTest.screen = 'test';
  renderAll();
}
function currentIntroQuestion() { return state.introTest.queue[state.introTest.index]; }
function answerIntroQuestion(optionIndex) {
  var t = state.introTest, q = currentIntroQuestion();
  if (!q) return;
  t.answers.push({ correct: optionIndex === q.correctIndex });
  t.index++;
  if (t.index >= t.queue.length) finishIntroTest();
  else renderAll();
}
function finishIntroTest() {
  var t = state.introTest;
  var correct = t.answers.filter(function (a) { return a.correct; }).length;
  var total = t.answers.length;
  t.correct = correct;
  t.total = total;
  t.score = Math.round(60 + (correct / total) * 100);
  t.screen = 'result';
  setRating({ score: t.score, games: 1 });
  pushRatingHistory(t.score);
  renderAll();
}
function skipIntroTest() { state.introTest = null; state.screen = 'home'; if (!consumePendingSocialChallenge() && !consumePendingLiveJoin()) renderAll(); }
function introTestDone() { state.introTest = null; state.screen = 'home'; if (!consumePendingSocialChallenge() && !consumePendingLiveJoin()) renderAll(); }
function retakeIntroTest() { startIntroTest(); }
// Unlike quiz options/grid squares (fresh DOM nodes every render, so a CSS
// animation on their class just replays automatically), #rating-badge is a
// single persistent element that only gets its text mutated in place — so
// retriggering its pulse animation needs an explicit class toggle + reflow.
var lastShownRatingScore = null;
// Named tiers over the score's practical range (60-160, see
// updateRatingDrift's sessionScore = 60 + sessionPct) — same "approximates
// rather than implies a hard ceiling" honesty the old ring fill already
// had, just given real names/checkpoints instead of an unlabeled percentage.
// Spans are even (20 points each) except the top tier, which has no "next"
// to measure against — see ratingTierFor's handling of that case.
var RATING_TIERS = [
  { name: 'Rookie', min: 60 },
  { name: 'Starter', min: 80 },
  { name: 'Pro', min: 100 },
  { name: 'All-Pro', min: 120 },
  { name: 'MVP', min: 140 }
];
function ratingTierFor(score) {
  var idx = 0;
  for (var i = 0; i < RATING_TIERS.length; i++) { if (score >= RATING_TIERS[i].min) idx = i; }
  var cur = RATING_TIERS[idx], next = RATING_TIERS[idx + 1] || null;
  var span = next ? (next.min - cur.min) : 20;
  var pct = next ? Math.max(0, Math.min(1, (score - cur.min) / span)) : 1;
  return { name: cur.name, min: cur.min, next: next ? next.name : null, ptsToNext: next ? Math.max(0, next.min - score) : 0, pct: pct };
}
function renderRatingBadge() {
  var el = document.getElementById('rating-badge');
  if (!el) return;
  var r = getRating();
  if (!r) { el.style.display = 'none'; lastShownRatingScore = null; return; }
  el.style.display = '';
  var tier = ratingTierFor(r.score);
  var subLabel = tier.next ? (tier.ptsToNext + ' to ' + tier.next) : 'Peak tier';
  el.innerHTML =
    '<span class="rating-badge-top">' + icon('football') + '<span class="rating-badge-score">' + r.score + '</span>' +
    '<span class="rating-badge-tier">' + esc(tier.name) + '</span></span>' +
    '<span class="rating-xp-track"><span class="rating-xp-fill" style="width:' + Math.round(tier.pct * 100) + '%"></span></span>';
  el.setAttribute('aria-label', 'Your Football Rating: ' + r.score + ', ' + tier.name + ' tier, ' + subLabel);
  if (lastShownRatingScore !== null && lastShownRatingScore !== r.score) {
    el.classList.remove('rating-pulse');
    void el.offsetWidth; // force reflow so the animation restarts
    el.classList.add('rating-pulse');
    var delta = r.score - lastShownRatingScore;
    var pop = document.createElement('span');
    pop.className = 'rating-delta-pop ' + (delta > 0 ? 'up' : 'down');
    pop.textContent = (delta > 0 ? '+' : '') + delta;
    el.appendChild(pop);
    setTimeout(function () { if (pop.parentNode) pop.parentNode.removeChild(pop); }, 1300);
  }
  lastShownRatingScore = r.score;
}

/* ============================== streak ==============================
   A daily-play streak, deliberately tied to the Daily Reads specifically
   (bumpStreak() is called from finishDailyChallenge(), not from every mode's
   finish function) — same pairing every real streak+daily-challenge feature
   uses elsewhere, and it means this needs zero changes to the 12 existing
   game modes. Local-only (not synced to Firebase) — purely a personal nudge
   shown on the Home screen and the Profile page. */
function pad2(n) { return (n < 10 ? '0' : '') + n; }
function dateStr(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
function todayStr() { return dateStr(new Date()); }
function daysAgoStr(n) { var d = new Date(); d.setDate(d.getDate() - n); return dateStr(d); }
function yesterdayStr() { return daysAgoStr(1); }
function daysBetween(a, b) { return Math.round((new Date(b) - new Date(a)) / 86400000); }
function streakKey() { return 'nflTriviaStreak__' + slugify(state.name); }
function getStreak() { return state.name ? lsGet(streakKey(), { count: 0, lastPlayedDate: '', graceUsedDate: '' }) : { count: 0, lastPlayedDate: '', graceUsedDate: '' }; }
// A streak grace is available once every 7 days (rolling from the last time
// one was actually used, not calendar-week-aligned) — survives exactly one
// missed day without resetting to 1. Missing 2+ days in a row, or missing a
// day while no grace is available, still resets normally. Not shown as an
// earnable/purchasable resource (this app has no points/currency economy to
// spend) — it's just a small, honest "one missed day won't wreck it" safety
// net, the way most real daily-streak products handle an off day.
function streakGraceAvailable(s) {
  if (!s.graceUsedDate) return true;
  return daysBetween(s.graceUsedDate, todayStr()) >= 7;
}
// Result set on state (see below) whenever bumpStreak() actually consumes a
// grace day — completeDailyChallengeFrom() and finishDailyChallenge() read
// this right after calling bumpStreak() so the result screen can say "streak
// saved" instead of the save happening invisibly.
var lastStreakGraceUsed = false;
function bumpStreak() {
  lastStreakGraceUsed = false;
  if (!state.name) return;
  var s = getStreak();
  var today = todayStr();
  if (s.lastPlayedDate === today) return;
  var gapDays = s.lastPlayedDate ? daysBetween(s.lastPlayedDate, today) : null;
  if (gapDays === 1 || !s.lastPlayedDate) {
    s.count = s.count + 1;
  } else if (gapDays === 2 && streakGraceAvailable(s)) {
    s.count = s.count + 1;
    s.graceUsedDate = today;
    lastStreakGraceUsed = true;
  } else {
    s.count = 1;
  }
  s.lastPlayedDate = today;
  lsSet(streakKey(), s);
}

/* ============================== daily challenge ==============================
   The one deliberate exception to "every round is freshly randomized" — a
   fixed 10-question set (5 NFL + 5 CFB, same blend as the intro test) that's
   IDENTICAL for every player on a given calendar date, via a tiny seeded PRNG
   instead of Math.random(). One attempt per day; always counts toward rating
   + leaderboard (no Practice variant, unlike every other mode). Reuses the
   already-eager QUIZ/CFB pools — no new data authoring needed. */
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(s) {
  var h = 0;
  for (var i = 0; i < s.length; i++) { h = (Math.imul(31, h) + s.charCodeAt(i)) | 0; }
  return h;
}
function seededShuffle(arr, rng) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rng() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
var DAILY_SIZE = 5;
var DAILY_READS_SLOT_LABELS = ['YOUR TEAM', 'WEAK SPOT', 'NFL QUICK HIT', 'CFB QUICK HIT', 'THE FINISHER'];
var DAILY_MECHANICS = {
  quick: { label: 'Quick Pick', short: '4-choice' },
  fifty: { label: '50 / 50', short: '2-choice' },
  elimination: { label: 'Eliminator', short: 'survive the board' },
  confidence: { label: 'Confidence Play', short: 'call your shot' },
  double: { label: 'Double Down', short: 'bonus point' }
};
var DAILY_STREAK_REWARDS = [
  { days: 3, xp: 25, label: 'On a Roll' },
  { days: 7, xp: 50, label: 'One Week Strong' },
  { days: 14, xp: 100, label: 'Two-Week Heater' },
  { days: 30, xp: 250, label: 'Monthly Machine' },
  { days: 100, xp: 1000, label: 'Daily Reads Legend' }
];
function dailyQuestionKey(q) { return (q._dailyLeague || 'NFL') + ':' + q.id; }
function dailyHistoryKey() { return 'nflTriviaDailyReadsHistory__' + slugify(state.name || 'guest'); }
function getDailyHistory() { return lsGet(dailyHistoryKey(), []); }
function setDailyHistory(v) { lsSet(dailyHistoryKey(), (v || []).slice(-35)); }
function dailyRecordsKey() { return 'nflTriviaDailyReadsRecords__' + slugify(state.name || 'guest'); }
function getDailyRecords() { return lsGet(dailyRecordsKey(), []); }
function setDailyRecords(v) {
  var byDate = {};
  (v || []).forEach(function (r) { if (r && r.date) byDate[r.date] = r; });
  var out = Object.keys(byDate).sort().map(function (d) { return byDate[d]; }).slice(-35);
  lsSet(dailyRecordsKey(), out);
}
function dailyStreakClaimsKey() { return 'readsDailyStreakClaims__' + slugify(state.name || 'guest'); }
function getDailyStreakClaims() { return lsGet(dailyStreakClaimsKey(), []); }
function setDailyStreakClaims(v) {
  var seen = {}, out = [];
  (v || []).forEach(function (n) { n = Number(n); if (n > 0 && !seen[n]) { seen[n] = true; out.push(n); } });
  out.sort(function (x,y) { return x-y; });
  lsSet(dailyStreakClaimsKey(), out);
}
function dailyReadsProfileState() {
  return { result: getDailyResult(), history: getDailyHistory(), records: getDailyRecords(), streakClaims: getDailyStreakClaims() };
}
function mergeDailyReads(local, cloud) {
  local = local || { result: null, history: [], records: [], streakClaims: [] };
  cloud = cloud || { result: null, history: [], records: [], streakClaims: [] };
  var lr = local.result, cr = cloud.result;
  var result = (!lr || (cr && String(cr.date || '') > String(lr.date || ''))) ? cr : lr;
  var seen = {}, history = [];
  (local.history || []).concat(cloud.history || []).forEach(function (k) {
    if (!seen[k]) { seen[k] = true; history.push(k); }
  });
  var recordMap = {};
  (local.records || []).concat(cloud.records || []).forEach(function (r) {
    if (!r || !r.date) return;
    var prev = recordMap[r.date];
    if (!prev || (Number(r.savedAt) || 0) >= (Number(prev.savedAt) || 0)) recordMap[r.date] = r;
  });
  var records = Object.keys(recordMap).sort().map(function (d) { return recordMap[d]; }).slice(-35);
  var claimSeen = {}, streakClaims = [];
  (local.streakClaims || []).concat(cloud.streakClaims || []).forEach(function (n) {
    n = Number(n);
    if (n > 0 && !claimSeen[n]) { claimSeen[n] = true; streakClaims.push(n); }
  });
  streakClaims.sort(function (x,y) { return x-y; });
  return { result: result || null, history: history.slice(-35), records: records, streakClaims: streakClaims };
}
function questionMentionsTeam(q, team) {
  if (!q || !team) return false;
  var hay = (String(q.question || '') + ' ' + (q.options || []).join(' ')).toLowerCase();
  var names = [team.name, team.code, team.id].filter(Boolean).map(function (x) { return String(x).toLowerCase(); });
  return names.some(function (n) { return n.length > 2 && hay.indexOf(n) !== -1; });
}
function dailyCandidatePool(source, league) {
  return (source || []).map(function (q) {
    return Object.assign({}, q, { _dailyLeague: league });
  });
}
function dailyDifficultyLevel(q) {
  var d = String(q && q.difficulty || '').toLowerCase();
  if (/expert|sicko|very hard/.test(d)) return 3;
  if (/hard|difficult/.test(d)) return 2;
  if (/medium|normal|moderate/.test(d)) return 1;
  if (/easy|rookie|beginner/.test(d)) return 0;
  return 1;
}
function recentDailyAverage() {
  var rows = getDailyRecords().slice(-7);
  if (!rows.length) return null;
  return Math.round(rows.reduce(function (sum, r) { return sum + (Number(r.pct) || 0); }, 0) / rows.length);
}
function adaptiveDailyDifficulty() {
  var rating = getRating();
  var score = rating ? Number(rating.score) || 100 : 100;
  var avg = recentDailyAverage();
  var level = score >= 128 ? 3 : score >= 108 ? 2 : score >= 88 ? 1 : 0;
  if (avg != null) {
    if (avg >= 85) level++;
    else if (avg < 50) level--;
  }
  return Math.max(0, Math.min(3, level));
}
function dailyDifficultyLabel(level) {
  return ['Easy', 'Medium', 'Hard', 'Expert'][Math.max(0, Math.min(3, level))];
}
function pickDailyCandidate(pool, rng, used, recent, predicate, preferredDifficulty) {
  function eligible(q, ignoreRecent, ignoreDifficulty) {
    var key = dailyQuestionKey(q);
    if (used[key]) return false;
    if (typeof contentMemoryAllows === 'function' && !ignoreRecent && !contentMemoryAllows(q, q._dailyLeague === 'CFB' ? 'cfb' : 'nfl')) return false;
    if (!ignoreRecent && recent[key]) return false;
    if (predicate && !predicate(q)) return false;
    if (!ignoreDifficulty && preferredDifficulty != null && Math.abs(dailyDifficultyLevel(q) - preferredDifficulty) > 0) return false;
    return true;
  }
  var candidates = pool.filter(function (q) { return eligible(q, false, false); });
  if (!candidates.length) candidates = pool.filter(function (q) { return eligible(q, true, false); });
  if (!candidates.length && preferredDifficulty != null) {
    candidates = pool.filter(function (q) { return eligible(q, false, true) && Math.abs(dailyDifficultyLevel(q) - preferredDifficulty) <= 1; });
  }
  if (!candidates.length && predicate) return pickDailyCandidate(pool, rng, used, recent, null, preferredDifficulty);
  if (!candidates.length) candidates = pool.filter(function (q) { return !used[dailyQuestionKey(q)]; });
  if (!candidates.length) return null;
  candidates.sort(function(a,b){return questionQualityScore(b,(b._dailyLeague||'NFL')==='CFB'?'cfb':'nfl',dailyDifficultyLabel(preferredDifficulty))-questionQualityScore(a,(a._dailyLeague||'NFL')==='CFB'?'cfb':'nfl',dailyDifficultyLabel(preferredDifficulty));});
  var top=candidates.slice(0,Math.max(1,Math.min(8,candidates.length)));
  var q = top[Math.floor(rng() * top.length)];
  used[dailyQuestionKey(q)] = true;
  rememberContentQuestion(q,(q._dailyLeague||'NFL')==='CFB'?'cfb':'nfl');
  return q;
}
function dailyWeakSpot() {
  var nfl = weakCategories('nfl')[0];
  var cfb = weakCategories('cfb')[0];
  if (!nfl && !cfb) return null;
  if (!nfl) return { league: 'CFB', category: cfb.category };
  if (!cfb) return { league: 'NFL', category: nfl.category };
  return nfl.count >= cfb.count ? { league: 'NFL', category: nfl.category } : { league: 'CFB', category: cfb.category };
}
function dailyLeaguePerformance() {
  var rows = getDailyRecords().slice(-7);
  var acc = { NFL:{c:0,t:0}, CFB:{c:0,t:0} };
  rows.forEach(function (r) {
    ['NFL','CFB'].forEach(function (league) {
      var x = r.leagueStats && r.leagueStats[league];
      if (!x) return;
      acc[league].c += Number(x.correct) || 0;
      acc[league].t += Number(x.total) || 0;
    });
  });
  function pct(x) { return x.t ? Math.round(100 * x.c / x.t) : null; }
  return { NFL:pct(acc.NFL), CFB:pct(acc.CFB) };
}
function dailyMechanicOrder(rng) {
  var middle = seededShuffle(['fifty','elimination','confidence'], rng);
  return ['quick'].concat(middle).concat(['double']);
}
function dailyVisibleIndexes(q, rng, mechanic) {
  var all = (q.options || []).map(function (_, i) { return i; });
  if (mechanic !== 'fifty' && mechanic !== 'double') return all;
  var wrong = all.filter(function (i) { return i !== q.correctIndex; });
  var other = wrong[Math.floor(rng() * wrong.length)];
  return seededShuffle([q.correctIndex, other], rng);
}
function decorateDailyQueue(out, rng, targetDifficulty) {
  var mechanics = dailyMechanicOrder(rng);
  out.forEach(function (q, i) {
    q._dailyMechanic = mechanics[i] || 'quick';
    q._dailyDifficultyTarget = Math.max(0, Math.min(3, targetDifficulty + (i === 0 ? -1 : i === 4 ? 1 : 0)));
    q._dailyVisibleIndexes = dailyVisibleIndexes(q, rng, q._dailyMechanic);
  });
  return out;
}
function dailyQuestionPool() {
  var seed = todayStr() + '__dailyReadsV2__' + (state.name || 'guest');
  var rng = mulberry32(hashStr(seed));
  var nflPool = dailyCandidatePool(QUIZ, 'NFL');
  var cfbPool = dailyCandidatePool(CFB, 'CFB');
  var all = nflPool.concat(cfbPool);
  var recent = {};
  getDailyHistory().slice(-20).forEach(function (k) { recent[k] = true; });
  var used = {};
  var out = [];
  var target = adaptiveDailyDifficulty();
  var favs = getFavoriteTeams();
  var preferredTeams = [];
  if (favs.nfl) preferredTeams.push({ league: 'NFL', team: favoriteTeamById('nfl', favs.nfl) });
  if (favs.cfb) preferredTeams.push({ league: 'CFB', team: favoriteTeamById('cfb', favs.cfb) });
  if (favs.lastPicked) {
    preferredTeams.sort(function (a) { return a.league === favs.lastPicked.toUpperCase() ? -1 : 1; });
  }
  var teamPick = null;
  for (var i = 0; i < preferredTeams.length && !teamPick; i++) {
    var tp = preferredTeams[i];
    var source = tp.league === 'NFL' ? nflPool : cfbPool;
    teamPick = pickDailyCandidate(source, rng, used, recent, function (q) { return questionMentionsTeam(q, tp.team); }, Math.max(0, target - 1));
  }
  if (!teamPick) teamPick = pickDailyCandidate(all, rng, used, recent, null, Math.max(0, target - 1));
  if (teamPick) {
    teamPick._dailySlot = DAILY_READS_SLOT_LABELS[0];
    teamPick._dailyReason = preferredTeams.length && questionMentionsTeam(teamPick, preferredTeams[0].team) ? 'Picked around one of your teams' : 'Personalized opener';
    out.push(teamPick);
  }

  var weak = dailyWeakSpot(), weakPick = null;
  if (weak) {
    var weakPool = weak.league === 'NFL' ? nflPool : cfbPool;
    weakPick = pickDailyCandidate(weakPool, rng, used, recent, function (q) { return q.category === weak.category; }, target);
  }
  if (!weakPick) weakPick = pickDailyCandidate(all, rng, used, recent, null, target);
  if (weakPick) {
    weakPick._dailySlot = DAILY_READS_SLOT_LABELS[1];
    weakPick._dailyReason = weak ? ('Based on your misses · ' + weak.category) : 'Build your range';
    out.push(weakPick);
  }

  var nflPick = pickDailyCandidate(nflPool, rng, used, recent, null, target);
  if (nflPick) { nflPick._dailySlot = DAILY_READS_SLOT_LABELS[2]; nflPick._dailyReason = 'NFL · ' + dailyDifficultyLabel(target); out.push(nflPick); }
  var cfbPick = pickDailyCandidate(cfbPool, rng, used, recent, null, target);
  if (cfbPick) { cfbPick._dailySlot = DAILY_READS_SLOT_LABELS[3]; cfbPick._dailyReason = 'College Football · ' + dailyDifficultyLabel(target); out.push(cfbPick); }

  var perf = dailyLeaguePerformance();
  var weakerLeague = perf.NFL != null && perf.CFB != null ? (perf.NFL <= perf.CFB ? 'NFL' : 'CFB') : null;
  var finishPool = weakerLeague === 'NFL' ? nflPool : weakerLeague === 'CFB' ? cfbPool : all;
  var finisher = pickDailyCandidate(finishPool, rng, used, recent, null, Math.min(3, target + 1));
  if (!finisher) finisher = pickDailyCandidate(all, rng, used, recent, null, Math.min(3, target + 1));
  if (finisher) {
    finisher._dailySlot = DAILY_READS_SLOT_LABELS[4];
    finisher._dailyReason = weakerLeague ? ('Challenge your ' + weakerLeague + ' side') : 'Finish strong';
    out.push(finisher);
  }
  return decorateDailyQueue(out.slice(0, DAILY_SIZE), rng, target);
}
function dailyKey() { return 'nflTriviaDaily__' + slugify(state.name); }
function getDailyResult() { return state.name ? lsGet(dailyKey(), null) : null; }
function playedToday() { var r = getDailyResult(); return !!(r && r.date === todayStr()); }
function dailyRecordFromState(pct) {
  var t = state.daily || {};
  return {
    date: todayStr(),
    savedAt: Date.now(),
    correct: t.correctCount || 0,
    total: t.queue ? t.queue.length : DAILY_SIZE,
    pct: pct,
    bonusPoints: t.bonusPoints || 0,
    leagueStats: t.leagueStats || { NFL:{correct:0,total:0}, CFB:{correct:0,total:0} },
    confidence: t.confidenceResults || [],
    mechanics: (t.queue || []).map(function (q) { return q._dailyMechanic || 'quick'; }),
    difficultyTarget: t.difficultyTarget == null ? adaptiveDailyDifficulty() : t.difficultyTarget
  };
}
function completeDailyReads(label, pct) {
  if (playedToday()) return;
  var st = state.stats.daily;
  st.completions++;
  if (typeof pct === 'number' && Math.round(pct) > st.bestPct) st.bestPct = Math.round(pct);
  lsSet('nflTriviaStats', state.stats);
  bumpStreak();
  var record = dailyRecordFromState(pct);
  var result = {
    date: todayStr(),
    type: 'dailyReads',
    label: label,
    correct: record.correct,
    total: record.total,
    pct: pct,
    bonusPoints: record.bonusPoints,
    graceUsed: lastStreakGraceUsed
  };
  if (state.name) lsSet(dailyKey(), result);
  var hist = getDailyHistory();
  (state.daily && state.daily.queue || []).forEach(function (q) { hist.push(dailyQuestionKey(q)); });
  setDailyHistory(hist);
  var records = getDailyRecords();
  records.push(record);
  setDailyRecords(records);
  var weekly = dailyRivalWeeklySnapshot();
  pushLeaderboard('daily', {
    completions: st.completions,
    bestPct: st.bestPct,
    lastPct: pct,
    bonusPoints: record.bonusPoints,
    dailyDate: record.date,
    dailyCorrect: record.correct,
    dailyTotal: record.total,
    todayRivalPoints: dailyRivalPoints(record),
    weekKey: weekly.weekKey,
    weeklyRivalPoints: weekly.points,
    weeklyDays: weekly.days,
    weeklyAvg: weekly.avg
  });
  awardDailyStreakMilestones();
  pushProfileSnapshot();
  state.justCompletedDaily = { typeId: 'dailyReads' };
}
function completeDailyChallengeFrom(typeId, label, pct) {
  if (!state.dailyChallengeActive || state.dailyChallengeActive.id !== typeId) return;
  state.dailyChallengeActive = null;
  completeDailyReads(label, pct);
}
function loadModeDataThenRun(mode, run, onError) {
  var files = MODE_DATA_FILES[mode];
  var pending = files && files.filter(function (f) { return !loadedScripts[f]; });
  if (pending && pending.length) {
    var app = document.getElementById('app');
    if (app) app.innerHTML = brandLoadingScreenHtml(modeLabelFor(mode));
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      run();
    }).catch(function () {
      if (onError) onError();
      if (app) app.innerHTML = '<div class="panel">Couldn’t load this mode. Check your connection and try again. <button class="btn-secondary" data-go="home">Home</button></div>';
    });
    return;
  }
  refreshDataAliases();
  run();
}
function startModeRanked(mode, startFn) {
  var prevPref = state.rankedPref[mode];
  state.rankedPref[mode] = true;
  startFn();
  state.rankedPref[mode] = prevPref;
}
function startDailyIntoMode(mode, startFn) {
  loadModeDataThenRun(mode, function () { startModeRanked(mode, startFn); }, function () { state.dailyChallengeActive = null; });
}
function startDailyChallenge() {
  beginProgressSession('daily');
  if (playedToday()) return;
  state.dailyChallengeActive = null;
  var queue = dailyQuestionPool();
  state.daily = {
    queue: queue,
    index: 0,
    correctCount: 0,
    bonusPoints: 0,
    answeredIndex: null,
    eliminated: {},
    attempts: {},
    confidenceByIndex: {},
    confidenceResults: [],
    missed: [],
    leagueStats: { NFL:{correct:0,total:0}, CFB:{correct:0,total:0} },
    difficultyTarget: adaptiveDailyDifficulty(),
    screen: 'question'
  };
  state.screen = 'daily';
  renderAll();
}
function currentDailyQuestion() { return state.daily.queue[state.daily.index]; }
function setDailyConfidence(n) {
  var t = state.daily, q = currentDailyQuestion();
  if (!t || !q || q._dailyMechanic !== 'confidence' || t.answeredIndex !== null) return;
  t.confidenceByIndex[t.index] = Math.max(1, Math.min(3, Number(n) || 1));
  renderAll();
}
function finalizeDailyQuestion(q, pickedIndex, firstTryCorrect) {
  var t = state.daily;
  t.answeredIndex = pickedIndex;
  if (firstTryCorrect) t.correctCount++;
  else if (!t.missed.some(function (m) { return m._dailyIndex === t.index; })) {
    t.missed.push({ _dailyIndex:t.index, question:q.question, options:q.options, correctIndex:q.correctIndex, pickedIndex:pickedIndex });
  }
  var league = q._dailyLeague === 'CFB' ? 'CFB' : 'NFL';
  t.leagueStats[league].total++;
  if (firstTryCorrect) t.leagueStats[league].correct++;
  if (q._dailyMechanic === 'double' && firstTryCorrect) t.bonusPoints++;
  if (q._dailyMechanic === 'confidence') {
    t.confidenceResults.push({ confidence: t.confidenceByIndex[t.index] || 1, correct: !!firstTryCorrect });
  }
  recordKnowledgeAnswer(league === 'CFB' ? 'cfb' : 'nfl', q.category || 'General', !!firstTryCorrect);
  if (typeof rememberContentQuestion === 'function') rememberContentQuestion(q, league === 'CFB' ? 'cfb' : 'nfl', 'daily');
}
function pickDailyAnswer(i) {
  var t = state.daily;
  if (!t || t.answeredIndex !== null) return;
  var q = currentDailyQuestion();
  if (!q) return;
  if (q._dailyMechanic === 'confidence' && !t.confidenceByIndex[t.index]) return;
  var isCorrect = i === q.correctIndex;
  var attempts = Number(t.attempts[t.index]) || 0;
  if (q._dailyMechanic === 'elimination' && !isCorrect) {
    t.attempts[t.index] = attempts + 1;
    t.eliminated[t.index] = t.eliminated[t.index] || {};
    t.eliminated[t.index][i] = true;
    if (!t.missed.some(function (m) { return m._dailyIndex === t.index; })) {
      t.missed.push({ _dailyIndex:t.index, question:q.question, options:q.options, correctIndex:q.correctIndex, pickedIndex:i });
    }
    playSound('wrong');
    renderAll();
    return;
  }
  var firstTryCorrect = isCorrect && attempts === 0;
  finalizeDailyQuestion(q, i, firstTryCorrect);
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextDailyQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  var t = state.daily;
  if (t.index + 1 >= t.queue.length) { finishDailyChallenge(); return; }
  t.index++;
  t.answeredIndex = null;
  renderAll();
}
function finishDailyChallenge() {
  var t = state.daily, st = state.stats.daily;
  var pct = Math.round(100 * t.correctCount / t.queue.length);
  st.correctTotal += t.correctCount;
  st.questionsTotal += t.queue.length;
  lsSet('nflTriviaStats', state.stats);
  updateRatingDrift(pct);
  t.ratingDelta = lastRatingDelta;
  playSound(pct <= 60 ? 'boo' : 'complete');
  completeDailyReads(t.correctCount + ' / ' + t.queue.length + ' correct', pct);
  t.screen = 'summary';
  renderAll();
}
function dailyMechanicPreviewHtml() {
  return ['quick','fifty','elimination','confidence','double'].map(function (id) {
    return '<span><b>' + esc(DAILY_MECHANICS[id].label) + '</b><small>' + esc(DAILY_MECHANICS[id].short) + '</small></span>';
  }).join('');
}
function weeklyDailyRecapData() {
  var rows = getDailyRecords().slice(-7);
  if (!rows.length) return null;
  var avg = Math.round(rows.reduce(function (s,r) { return s + (Number(r.pct) || 0); }, 0) / rows.length);
  var best = Math.max.apply(null, rows.map(function (r) { return Number(r.pct) || 0; }));
  var perfects = rows.filter(function (r) { return Number(r.pct) === 100; }).length;
  var bonus = rows.reduce(function (s,r) { return s + (Number(r.bonusPoints) || 0); }, 0);
  var high = [], allConfidence = [];
  rows.forEach(function (r) { (r.confidence || []).forEach(function (x) { allConfidence.push(x); if (Number(x.confidence) === 3) high.push(x); }); });
  var highHit = high.length ? Math.round(100 * high.filter(function (x) { return x.correct; }).length / high.length) : null;
  return { rows:rows, days:rows.length, avg:avg, best:best, perfects:perfects, bonus:bonus, highHit:highHit };
}
function dailyRivalPoints(record) {
  record = record || {};
  return (Number(record.correct) || 0) * 100 + (Number(record.bonusPoints) || 0) * 20 + (Number(record.difficultyTarget) || 0) * 10;
}
function dailyRivalWeekKey(dateStr) {
  var p = String(dateStr || todayStr()).split('-').map(Number);
  var d = new Date(p[0], (p[1] || 1) - 1, p[2] || 1);
  var day = d.getDay();
  var shift = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + shift);
  return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
}
function dailyRivalWeeklySnapshot() {
  var weekKey = dailyRivalWeekKey(todayStr());
  var rows = getDailyRecords().filter(function (r) { return dailyRivalWeekKey(r.date) === weekKey; });
  var points = rows.reduce(function (sum,r) { return sum + dailyRivalPoints(r); }, 0);
  var avg = rows.length ? Math.round(rows.reduce(function (sum,r) { return sum + (Number(r.pct) || 0); }, 0) / rows.length) : 0;
  return { weekKey:weekKey, days:rows.length, points:points, avg:avg };
}
function dailyRivalSort(rows, key) {
  return rows.slice().sort(function (x,y) {
    var diff = (Number(y[key]) || 0) - (Number(x[key]) || 0);
    if (diff) return diff;
    return (Number(y.lastPct) || 0) - (Number(x.lastPct) || 0);
  });
}
function dailyRivalRows(kind) {
  var all = (state.leaderboardData || []).filter(function (r) { return r.mode === 'daily'; });
  if (kind === 'week') {
    return dailyRivalSort(all.filter(function (r) { return r.weekKey === dailyRivalWeekKey(todayStr()); }), 'weeklyRivalPoints');
  }
  return dailyRivalSort(all.filter(function (r) { return r.dailyDate === todayStr(); }), 'todayRivalPoints');
}
function dailyRivalMeIndex(rows) {
  var key = canonicalPlayerKey();
  var exact = rows.findIndex(function (r) { return r.playerKey && r.playerKey === key; });
  if (exact >= 0) return exact + 1;
  var fallback = rows.findIndex(function (r) { return slugify(r.name || '') === slugify(state.name || ''); });
  return fallback >= 0 ? fallback + 1 : null;
}
function dailyRivalScopeRows(rows, scope) {
  if (scope === 'friends') {
    var names = getFriends().map(slugify);
    names.push(slugify(state.name || ''));
    return rows.filter(function (r) { return names.indexOf(slugify(r.name || '')) !== -1; });
  }
  if (scope === 'team') {
    var league = defaultCommunityLeague();
    var fav = getFavoriteTeams();
    var id = fav[league];
    if (!id) return [];
    var field = league === 'cfb' ? 'favoriteCfbTeam' : 'favoriteNflTeam';
    return rows.filter(function (r) { return r[field] === id; });
  }
  return rows;
}
function dailyRivalListHtml(rows, key, limit) {
  rows = rows.slice(0, limit || 5);
  if (!rows.length) return '<div class="daily-rivals-empty">No scores yet. Be the first one in.</div>';
  return '<div class="daily-rivals-list">' + rows.map(function (r,i) {
    return '<div class="daily-rival-row' + (slugify(r.name || '') === slugify(state.name || '') ? ' is-you' : '') + '">' +
      '<span class="daily-rival-rank">' + (i+1) + '</span><b>' + esc(r.name || 'Reads fan') + '</b>' +
      '<span>' + (Number(r[key]) || 0) + ' pts</span></div>';
  }).join('') + '</div>';
}
function dailyRivalsHtml(compact) {
  if (!state.name) return '';
  var todayRows = dailyRivalRows('today');
  var weekRows = dailyRivalRows('week');
  var todayRank = dailyRivalMeIndex(todayRows);
  var weekRank = dailyRivalMeIndex(weekRows);
  var friends = dailyRivalScopeRows(todayRows, 'friends');
  var team = dailyRivalScopeRows(todayRows, 'team');
  var league = defaultCommunityLeague();
  var favTeam = communityTeamForLeague(league);
  return '<section class="daily-rivals' + (compact ? ' compact' : '') + '">' +
    '<div class="dashboard-section-head"><div><span class="dashboard-eyebrow">DAILY RIVALS</span><h3>Beat the room</h3></div>' +
      '<span>' + (todayRank ? '#' + todayRank + ' today' : 'Play to rank') + '</span></div>' +
    '<p class="daily-rivals-note">Rival Points reward correct answers, Double Down bonuses, and tougher Daily difficulty.</p>' +
    '<div class="daily-rivals-rank-strip">' +
      '<span><b>' + (todayRank ? '#' + todayRank : '—') + '</b><small>Today</small></span>' +
      '<span><b>' + (weekRank ? '#' + weekRank : '—') + '</b><small>This week</small></span>' +
      '<span><b>' + friends.length + '</b><small>Friends active</small></span>' +
      '<span><b>' + team.length + '</b><small>' + esc(favTeam ? favTeam.name : 'Team') + ' active</small></span>' +
    '</div>' +
    (compact ? dailyRivalListHtml(todayRows, 'todayRivalPoints', 3) :
      '<div class="daily-rivals-columns"><div><h4>Today</h4>' + dailyRivalListHtml(todayRows,'todayRivalPoints',5) + '</div>' +
      '<div><h4>This Week</h4>' + dailyRivalListHtml(weekRows,'weeklyRivalPoints',5) + '</div>' +
      '<div><h4>Friends Today</h4>' + dailyRivalListHtml(friends,'todayRivalPoints',5) + '</div>' +
      '<div><h4>' + esc(favTeam ? favTeam.name + ' Fans' : 'Your Team') + '</h4>' + dailyRivalListHtml(team,'todayRivalPoints',5) + '</div></div>') +
    '</section>';
}
function dailyStreakRewardsHtml() {
  var count = getStreak().count || 0;
  var claims = getDailyStreakClaims();
  var next = DAILY_STREAK_REWARDS.find(function (r) { return r.days > count; });
  return '<section class="daily-streak-ladder"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">STREAK REWARDS</span><h3>Keep the heater alive</h3></div>' +
    '<span>' + (next ? (next.days - count) + ' day' + (next.days-count===1?'':'s') + ' to +' + next.xp + ' XP' : 'Legend status') + '</span></div>' +
    '<div class="daily-streak-milestones">' + DAILY_STREAK_REWARDS.map(function (r) {
      var claimed = claims.indexOf(r.days) !== -1;
      var active = count >= r.days;
      return '<span class="' + (active ? 'complete' : '') + '"><b>' + r.days + 'D</b><small>' + esc(r.label) + '</small><em>' + (claimed ? 'Claimed' : '+' + r.xp + ' XP') + '</em></span>';
    }).join('') + '</div></section>';
}
function awardDailyStreakMilestones() {
  if (!state.name) return;
  var count = getStreak().count || 0;
  var reward = DAILY_STREAK_REWARDS.find(function (r) { return r.days === count; });
  if (!reward) return;
  var claims = getDailyStreakClaims();
  if (claims.indexOf(reward.days) !== -1) return;
  claims.push(reward.days);
  setDailyStreakClaims(claims);
  var seasonId = footballSeasonIdForDate();
  var eventId = 'daily_streak_' + reward.days;
  if (activeAuthUid && window.__fbSync && window.__fbSync.awardProgress) {
    window.__fbSync.awardProgress(profileDocId(), eventId, {
      type:'DAILY_STREAK_MILESTONE', source:'daily_reads', days:reward.days
    }, reward.xp, seasonId).then(function (result) {
      if (!result || !result.duplicate) applyProgressAwardLocally(reward.xp, seasonId);
      pushSeasonLeaderboardSnapshot();
      pushProfileSnapshot();
      if (state.screen === 'daily' || state.screen === 'home' || state.screen === 'profile') renderAll();
    }).catch(function () {});
  } else {
    applyProgressAwardLocally(reward.xp, seasonId);
    pushSeasonLeaderboardSnapshot();
    pushProfileSnapshot();
  }
}
function weeklyDailyRecapHtml(compact) {
  var w = weeklyDailyRecapData();
  if (!w || w.days < 2) return '';
  return '<section class="weekly-daily-recap' + (compact ? ' compact' : '') + '">' +
    '<div class="dashboard-section-head"><div><span class="dashboard-eyebrow">LAST 7 DAILY READS</span><h3>Weekly Recap</h3></div><span>' + w.days + ' played</span></div>' +
    '<div class="weekly-daily-metrics">' +
      '<span><b>' + w.avg + '%</b><small>Average</small></span>' +
      '<span><b>' + w.best + '%</b><small>Best</small></span>' +
      '<span><b>' + w.perfects + '</b><small>Perfects</small></span>' +
      '<span><b>' + w.bonus + '</b><small>Double Down bonus</small></span>' +
      (w.highHit == null ? '' : '<span><b>' + w.highHit + '%</b><small>High-confidence hit rate</small></span>') +
    '</div>' +
    '<div class="weekly-daily-bars">' + w.rows.map(function (r) {
      return '<span title="' + esc(r.date) + ': ' + (Number(r.pct) || 0) + '%"><i style="height:' + Math.max(8, Number(r.pct) || 0) + '%"></i><small>' + esc(String(r.date).slice(5)) + '</small></span>';
    }).join('') + '</div>' +
    '</section>';
}
function dailyChallengeCardHtml() {
  var already = playedToday();
  var streak = getStreak();
  var streakBit = streak.count > 0 ? icon('flame', 'streak-flame') + ' ' + streak.count + '-day streak' : '';
  var badge = '<span class="daily-flame-badge">' + icon('flame') + '</span>';
  var eyebrow = '<div class="daily-card-eyebrow">YOUR DAILY 5 · V2</div>';
  if (already) {
    var r = getDailyResult();
    var label = r.label || ((r.correct || 0) + ' / ' + (r.total || DAILY_SIZE) + ' correct');
    return '<div class="panel daily-card daily-reads-card">' + eyebrow +
      '<div class="daily-card-title">' + badge + ' Daily Reads Complete</div>' +
      '<p class="mode-desc">' + icon('check') + ' ' + esc(label) + (r.bonusPoints ? ' + ' + r.bonusPoints + ' bonus' : '') + (streakBit ? ' &middot; ' + streakBit : '') + '. You’re done for today.</p>' +
      (r.graceUsed ? '<p class="mode-desc streak-saved-note">🛡️ Streak grace saved your run.</p>' : '') +
      '<button class="btn-secondary" data-go="daily">View Today’s Result</button>' +
      '</div>';
  }
  var favs = getFavoriteTeams();
  var personalized = !!(favs.nfl || favs.cfb || weakCategories('nfl').length || weakCategories('cfb').length);
  return '<div class="panel daily-card daily-reads-card">' +
    '<div class="daily-card-deco" aria-hidden="true">' + icon('football') + '</div>' +
    eyebrow +
    '<div class="daily-card-title">' + badge + ' Daily Reads</div>' +
    '<p class="mode-desc">Five quick games. About five minutes. ' +
      (personalized ? 'Built around your teams, weak spots, recent performance, and Football Rating.' : 'Your mix adapts as you play.') +
      '</p>' +
    '<div class="daily-v2-mechanics">' + dailyMechanicPreviewHtml() + '</div>' +
    '<p class="daily-difficulty-note">' + icon('target') + ' Today’s target: <b>' + esc(dailyDifficultyLabel(adaptiveDailyDifficulty())) + '</b></p>' +
    (streakBit ? '<p class="daily-card-streak">' + streakBit + '</p>' : '') +
    '<button class="btn-primary" data-daily-start>Start My Daily 5' + icon('arrowRight', 'daily-cta-arrow') + '</button>' +
    '</div>';
}
function dailyMechanicInstructions(q) {
  var id = q._dailyMechanic || 'quick';
  if (id === 'fifty') return 'Two choices. One read.';
  if (id === 'elimination') return 'Wrong picks disappear. First-try correct earns the point.';
  if (id === 'confidence') return 'Call your confidence before you lock the answer.';
  if (id === 'double') return 'Get it right for the Daily point + one bonus point.';
  return 'Read it and make the call.';
}
function renderDailyQuestion() {
  var t = state.daily, q = currentDailyQuestion();
  if (!q) return '<div class="panel"><h2 class="panel-title">Daily Reads</h2><p class="mode-desc">Couldn’t build today’s five. Head home and try again.</p><button class="btn-secondary" data-go="home">Home</button></div>';
  var answered = t.answeredIndex !== null;
  var mechanic = q._dailyMechanic || 'quick';
  var visible = q._dailyVisibleIndexes && q._dailyVisibleIndexes.length ? q._dailyVisibleIndexes : q.options.map(function (_,i) { return i; });
  var eliminated = t.eliminated[t.index] || {};
  var confidence = t.confidenceByIndex[t.index] || 0;
  return '<div class="panel daily-reads-game daily-mechanic-' + esc(mechanic) + '">' + modeToolbarHtml('daily') +
    '<div class="daily-reads-kicker"><span>' + esc(q._dailySlot || ('READ ' + (t.index + 1))) + '</span><small>' + esc(q._dailyReason || q._dailyLeague || '') + '</small></div>' +
    quizProgressRowHtml('Daily Reads &middot; Game ' + (t.index + 1) + ' of ' + t.queue.length, t.index, t.queue.length) +
    '<div class="daily-mechanic-banner"><b>' + esc(DAILY_MECHANICS[mechanic].label) + '</b><span>' + esc(dailyMechanicInstructions(q)) + '</span></div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    (mechanic === 'confidence' && !answered ? '<div class="daily-confidence"><span>Confidence</span>' +
      [1,2,3].map(function (n) { return '<button class="' + (confidence === n ? 'active' : '') + '" data-daily-confidence="' + n + '">' + n + (n === 1 ? ' · Lean' : n === 2 ? ' · Like it' : ' · Lock') + '</button>'; }).join('') +
      '</div>' : '') +
    '<div class="quiz-options daily-options">' +
    visible.map(function (i) {
      var opt = q.options[i];
      var cls = 'quiz-option';
      if (eliminated[i]) cls += ' daily-eliminated';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      var disabled = answered || eliminated[i] || (mechanic === 'confidence' && !confidence);
      return '<button class="' + cls + '" ' + (disabled ? 'disabled' : 'data-daily-answer="' + i + '"') + '>' +
        '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span></button>';
    }).join('') +
    '</div>' +
    (mechanic === 'elimination' && !answered && (Number(t.attempts[t.index]) || 0) ? '<div class="quiz-feedback feedback-bad">One down. Keep reading — the Daily point is gone, but finish the board.</div>' : '') +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex && (Number(t.attempts[t.index]) || 0) === 0 ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Board cleared.</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-daily-next>' + (t.index + 1 >= t.queue.length ? 'Finish Daily Reads' : 'Next Game') + '</button>'
      : '') +
    '</div>';
}
function renderDailySummary() {
  var t = state.daily, pct = Math.round(100 * t.correctCount / t.queue.length);
  var p = getProgression();
  var seasonId = footballSeasonIdForDate();
  var seasonXp = p.seasons && p.seasons[seasonId] ? Number(p.seasons[seasonId].xp) || 0 : 0;
  return '<div class="panel daily-reads-summary">' +
    '<h2 class="panel-title">' + icon('flame') + ' Daily Reads Complete</h2>' +
    '<div class="summary-score">' + t.correctCount + ' / ' + t.queue.length + ' correct (' + pct + '%)' + (t.bonusPoints ? ' · +' + t.bonusPoints + ' bonus' : '') + '</div>' +
    '<div class="daily-reads-reward"><b>+50 XP</b><span>Career + ' + esc(seasonId) + ' Season</span></div>' +
    '<div class="summary-note">' + icon('flame') + ' ' + getStreak().count + '-day streak. Career XP: ' + (p.careerXp || 0) + ' &middot; Season XP: ' + seasonXp + '.</div>' +
    (lastStreakGraceUsed ? '<div class="summary-note streak-saved-note">🛡️ You missed a day, but your streak survived — one grace day free every 7 days.</div>' : '') +
    '<div class="daily-summary-mechanics">' + t.queue.map(function (q, i) {
      var missed = t.missed.some(function (m) { return m._dailyIndex === i || m.question === q.question; });
      return '<span class="' + (missed ? 'missed' : 'hit') + '"><b>' + esc(DAILY_MECHANICS[q._dailyMechanic || 'quick'].label) + '</b><small>' + (missed ? 'Miss' : 'Hit') + '</small></span>';
    }).join('') + '</div>' +
    dailyRivalsHtml(true) +
    dailyStreakRewardsHtml() +
    weeklyDailyRecapHtml(true) +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-secondary" data-share="daily">' + icon('share') + ' Share</button>' +
    '<button class="btn-primary" data-go="home">Back to Dashboard</button>' +
    '</div></div>';
}
function renderDailyScreen() {
  if (!state.daily) {
    var r = getDailyResult();
    if (r && r.date === todayStr()) {
      var label = r.label || ((r.correct || 0) + ' / ' + (r.total || DAILY_SIZE) + ' correct');
      return '<div class="panel daily-reads-summary"><h2 class="panel-title">' + icon('flame') + ' Daily Reads &middot; Complete</h2>' +
        '<div class="summary-score">' + esc(label) + (r.bonusPoints ? ' · +' + r.bonusPoints + ' bonus' : '') + '</div>' +
        '<div class="summary-note">Streak: ' + getStreak().count + ' day' + (getStreak().count === 1 ? '' : 's') + '. Your next Daily 5 unlocks tomorrow.</div>' +
        weeklyDailyRecapHtml(true) +
        '<button class="btn-primary" data-go="home">Back to Dashboard</button></div>';
    }
    return '<div class="panel daily-reads-launch"><h2 class="panel-title">' + icon('flame') + ' Daily Reads v2</h2>' +
      '<p class="mode-desc">Five personalized mini-games. About five minutes total. Difficulty adapts to you.</p>' +
      '<div class="daily-v2-mechanics">' + dailyMechanicPreviewHtml() + '</div>' +
      '<button class="btn-primary" data-daily-start>Start My Daily 5</button></div>';
  }
  if (state.daily.screen === 'summary') return renderDailySummary();
  return renderDailyQuestion();
}

var blitzTimer = null, speedTimer = null, cfbSpeedTimer = null, cfbBlitzTimer = null;
function stopTimers() {
  if (blitzTimer) { clearInterval(blitzTimer); blitzTimer = null; }
  if (speedTimer) { clearInterval(speedTimer); speedTimer = null; }
  if (cfbSpeedTimer) { clearInterval(cfbSpeedTimer); cfbSpeedTimer = null; }
  if (cfbBlitzTimer) { clearInterval(cfbBlitzTimer); cfbBlitzTimer = null; }
}

/* ============================== nav ============================== */
function resetModeState(mode) {
  beginProgressSession(mode);
  // Restarting or navigating back into a mode (the only two ways this gets
  // called for a mode other than the daily/h2h routing helpers, which call
  // that mode's own start function directly instead) means any in-progress
  // Daily Reads or Head-to-Head round that was being played AS that mode
  // just got abandoned — clear the flag so a later, unrelated solo round in
  // this same mode can't get silently credited as finishing it.
  if (state.dailyChallengeActive && state.dailyChallengeActive.mode === mode) state.dailyChallengeActive = null;
  if (state.h2hActive && state.h2hActive.mode === mode) state.h2hActive = null;
  if (mode === 'quiz') state.quiz = { screen: 'setup', category: '', difficulty: '', roundSize: (state.quiz && state.quiz.roundSize) || 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] };
  else if (mode === 'xso') state.xso = { screen: 'setup', category: '', difficulty: '', roundSize: (state.xso && state.xso.roundSize) || 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] };
  else if (mode === 'grid') state.grid = null;
  else if (mode === 'blitz') state.blitz = null;
  else if (mode === 'speed') state.speed = null;
  else if (mode === 'higherLower') state.higherLower = null;
  else if (mode === 'silhouette') state.silhouette = null;
  else if (mode === 'playerClues') state.playerClues = null;
  else if (mode === 'cfbPlayerClues') state.cfbPlayerClues = null;
  else if (mode === 'enginePilot') state.enginePilot = null;
  else if (mode === 'mechanicPilot') state.mechanicPilot = null;
  else if (mode === 'iq') state.iq = null;
  else if (mode === 'legends') state.legends = null;
  else if (mode === 'cfbQuiz') state.cfbQuiz = { screen: 'setup', category: '', difficulty: '', roundSize: (state.cfbQuiz && state.cfbQuiz.roundSize) || 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] };
  else if (mode === 'cfbIq') state.cfbIq = null;
  else if (mode === 'cfbSpeed') state.cfbSpeed = null;
  else if (mode === 'cfbBlitz') state.cfbBlitz = null;
  else if (mode === 'cfbGrid') state.cfbGrid = null;
  else if (mode === 'daily') state.daily = null;
  else if (mode === 'cfbLegends') state.cfbLegends = null;
  else if (mode === 'h2h') state.h2h = null;
  else if (mode === 'h2hLive') { h2hLiveStopWatch(); state.h2hLive = null; }
  else if (mode === 'study') state.study = null;
  else if (mode === 'learn') state.learn = null;
  else if (mode === 'settings') state.settingsConfirmClear = false;
  else if (mode === 'pickem_nfl' || mode === 'pickem_cfb') state.pickem = null;
}
/* ============================== lazy data loading ==============================
   Only data/quiz.js (QUIZ) and data/cfb.js (CFB) load eagerly — they're needed
   immediately by the intro test every brand-new user hits, plus the Quiz/
   Speed/IQ modes that already reuse them. Every other mode's data file (the
   other ~75% of the app's 51k lines of data, cfb-speed.js alone is ~39% of
   it) loads on first entry into that specific mode instead. */
var MODE_DATA_FILES = {
  xso: ['data/xso.js'],
  grid: ['data/grid.js', 'data/grid-engine-players.js'],
  higherLower: ['data/grid.js', 'data/grid-engine-players.js', 'data/higher-lower-extra.js'],
  cfbGrid: ['data/cfb-grid.js'],
  blitz: ['data/blitz.js'],
  cfbBlitz: ['data/cfb-blitz.js'],
  silhouette: ['data/silhouette.js'],
  cfbSpeed: ['data/cfb-speed.js'],
  legends: ['data/legends.js', 'data/legends-meta.js'],
  cfbLegends: ['data/cfb-legends.js', 'data/cfb-legends-meta.js'],
  // Real page-weight fix: player-from-clues-v01.js grew from ~60KB (25
  // puzzles) to ~1.4MB (600 puzzles, real decade/difficulty data) this
  // pass -- it and its CFB counterpart were being loaded eagerly via a
  // plain <script> tag on EVERY page visit (see index.html), even for
  // users who never open either mode. Moved to the same on-demand lazy-load
  // path every other mode's data file already uses.
  playerClues: ['data/player-from-clues-v01.js'],
  cfbPlayerClues: ['data/cfb-player-from-clues-v01.js']
};
var loadedScripts = {};
var loadingScripts = {};
function loadScript(src) {
  if (loadedScripts[src]) return Promise.resolve();
  if (loadingScripts[src]) return loadingScripts[src];
  var p = new Promise(function (resolve, reject) {
    var el = document.createElement('script');
    el.src = src;
    el.onload = function () { loadedScripts[src] = true; resolve(); };
    el.onerror = function () { reject(new Error('Failed to load ' + src)); };
    document.body.appendChild(el);
  });
  loadingScripts[src] = p;
  return p;
}
// The top-level `var QUIZ = window.QUIZ_DATA || []`-style aliases (near the
// top of this file) are only captured once at parse time, so a data file
// that loads later needs this to re-point them at the now-populated
// window.* globals — plain top-level `var`s in one classic script are
// reassignable at any point, so this is safe to call any time.
function refreshDataAliases() {
  XSO = window.XSO_DATA || XSO;
  LEARN_COVERAGES = window.LEARN_COVERAGE_MODULE || LEARN_COVERAGES;
  LEARN_ENCYCLOPEDIA = window.LEARN_ENCYCLOPEDIA || LEARN_ENCYCLOPEDIA;
  FOOTBALL_DIAGRAMS = window.FOOTBALL_DIAGRAMS || FOOTBALL_DIAGRAMS;
  FootballField = window.FootballField || FootballField;
  ENCYCLOPEDIA_DEEP_DIVES = window.ENCYCLOPEDIA_DEEP_DIVES || ENCYCLOPEDIA_DEEP_DIVES;
  // Engine v4.0-sourced players (data/grid-engine-players.js, see
  // tools/grid_export/build_grid_engine_players.py) concatenated onto the
  // hand-curated pool -- recomputed from the two stable window.* sources
  // every call rather than mutated in place, so calling this more than
  // once (it runs after every lazy-load event, not just Grid's own) never
  // re-appends and never duplicates.
  GRID_PLAYERS = (window.GRID_PLAYERS || GRID_PLAYERS).concat(window.GRID_ENGINE_PLAYERS || []);
  GRID_CRITERIA = window.GRID_CRITERIA || GRID_CRITERIA;
  BLITZ_LISTS = window.BLITZ_LISTS || BLITZ_LISTS;
  SILHOUETTE_PLAYERS = window.SILHOUETTE_PLAYERS || SILHOUETTE_PLAYERS;
  CFB_SPEED = window.CFB_SPEED_DATA || CFB_SPEED;
  CFB_BLITZ_LISTS = window.CFB_BLITZ_LISTS || CFB_BLITZ_LISTS;
  CFB_GRID_PLAYERS = window.CFB_GRID_PLAYERS || CFB_GRID_PLAYERS;
  CFB_GRID_CRITERIA = window.CFB_GRID_CRITERIA || CFB_GRID_CRITERIA;
  LEGENDS_TEAMS = window.LEGENDS_TEAMS || LEGENDS_TEAMS;
  PLAYER_META = window.PLAYER_META || PLAYER_META;
  LEGENDS_DUOS = window.LEGENDS_DUOS || LEGENDS_DUOS;
  CFB_LEGENDS_TEAMS = window.CFB_LEGENDS_TEAMS || CFB_LEGENDS_TEAMS;
  CFB_PLAYER_META = window.CFB_PLAYER_META || CFB_PLAYER_META;
  CFB_LEGENDS_DUOS = window.CFB_LEGENDS_DUOS || CFB_LEGENDS_DUOS;
  HL_PASSING = window.HL_PASSING || HL_PASSING;
  HL_RUSHING = window.HL_RUSHING || HL_RUSHING;
  HL_RECEIVING = window.HL_RECEIVING || HL_RECEIVING;
  HL_TACKLES = window.HL_TACKLES || HL_TACKLES;
  HL_INTERCEPTIONS = window.HL_INTERCEPTIONS || HL_INTERCEPTIONS;
  HL_FUMBLES = window.HL_FUMBLES || HL_FUMBLES;
  HL_FIELDGOALS = window.HL_FIELDGOALS || HL_FIELDGOALS;
  HL_PUNTING = window.HL_PUNTING || HL_PUNTING;
  HL_RETURNS = window.HL_RETURNS || HL_RETURNS;
  HL_CONTRACTS = window.HL_CONTRACTS || HL_CONTRACTS;
  HL_STADIUMS = window.HL_STADIUMS || HL_STADIUMS;
  // Unlike the simple window.X || X aliases above, these two run real
  // validation (validatePlayerCluesPackage) -- re-run on every call (cheap,
  // idempotent) so a lazy-loaded player-from-clues file is actually picked
  // up the first time this mode is entered, not just at initial page load.
  if (typeof initPlayerCluesPackage === 'function') initPlayerCluesPackage();
  if (typeof initCfbPlayerCluesPackage === 'function') initCfbPlayerCluesPackage();
}
function enterMode(mode) {
  // Leaving an in-progress head-to-head match for anywhere else — stop its
  // live listener so it doesn't keep updating a screen nobody's looking at.
  if (state.screen === 'h2h' && mode !== 'h2h' && typeof h2hStopWatch === 'function') h2hStopWatch();
  if (state.screen === 'h2hLive' && mode !== 'h2hLive' && typeof h2hLiveStopWatch === 'function') h2hLiveStopWatch();
  stopTimers(); resetModeState(mode); state.screen = mode; renderAll();
  // "Continue where you left off" on Home reads this back — only real game
  // modes count, not navigational screens like leaderboard/profile/daily.
  if (LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).some(function (m) { return m.id === mode; })) {
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
  } else if (mode === 'h2h') {
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay('h2h');
    startSocialChallengeWatch();
  } else if (mode === 'h2hLive' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('h2hLive');
  } else if (mode === 'learn' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('learn');
  } else if (mode === 'friends') {
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay('friends');
    startSocialChallengeWatch();
    loadFriendsData();
  } else if (mode === 'community' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('community');
  } else if (mode === 'study' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('study');
  } else if (mode === 'xso' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('xso');
  }
}
// Modes that exist outside LEAGUE_MODES.nfl/.cfb (standalone Home cards,
// not part of either league's mode grid/dropdown) but still need a real
// label wherever modeLabelFor() is read — Report modal context text, the
// reports screen listing, etc.
var EXTRA_MODE_LABELS = { learn: 'Film Room', study: 'Study Mode', xso: "X's & O's", community: 'Team Community', daily: 'Daily Reads', h2h: 'Head-to-Head', playerClues: 'Player From Clues', cfbPlayerClues: 'CFB Player From Clues', endless: 'Endless Reads' };
function modeLabelFor(id) {
  var m = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).find(function (x) { return x.id === id; });
  return m ? m.title : (EXTRA_MODE_LABELS[id] || 'mode');
}
function goToMode(mode) {
  if (state.screen === 'community' && mode !== 'community') stopCommunityWatch();
  if (state.name) {
    var recNow = scoredModeRecommendations(3).some(function (r) { return r.mode.id === mode; });
    if (recNow) noteRecommendedModePlayed(mode);
  }
  // UI polish pass: real bug found by actually scrolling down on one
  // screen (e.g. a long quiz result review list) and then navigating to a
  // DIFFERENT mode -- the browser keeps the old scroll offset, so the new
  // mode can render with its question/instructions header already
  // scrolled off the top of the viewport. Every navigation through this
  // function (mode switches, Home, the mode-sheet) is the right single
  // place to reset it -- covers the whole app instead of patching each
  // mode's own start function individually.
  window.scrollTo(0, 0);
  // v1.6, Part C6: engine-backed discovery cards (ENGINE_DISCOVERY_ENTRIES,
  // only ever present when their flag is on) route into the shared engine
  // shell instead of the normal local-data-file path below -- they have no
  // MODE_DATA_FILES entry and never will (their content comes from the
  // Gateway, not a data/*.js file). closeModeSheet() already ran in the
  // caller (the single data-go click handler) exactly like every other
  // mode, so no special-casing is needed there.
  // v1.7 bug found by actually clicking the Coach Connections discovery
  // card, not assumed safe from reading the code: ENGINE_DISCOVERY_ENTRIES
  // now ALSO contains the Six Degrees entry (Part C8, below), which has no
  // `engineMode` field -- without the `.engineMode` check here, .find()
  // still matched it (same `id`), and startEnginePilotRound(undefined)
  // silently launched Draft (the default modeKey) instead of Six Degrees.
  // Guarding on `engineMode` specifically keeps this branch scoped to only
  // the entries that actually belong to engine-game-ui.js's shell.
  var engineEntry = ENGINE_DISCOVERY_ENTRIES.find(function (e) { return e.id === mode && e.engineMode; });
  if (engineEntry) {
    beginProgressSession(mode);
    // Same bookkeeping enterMode() does for every other LEAGUE_MODES entry
    // (line ~1017 above) -- so "Continue where you left off" (Part C14) and
    // Firebase's play-log both work for engine modes exactly like every
    // other mode, without engine-game-ui.js needing to know either exists.
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
    // Franchise Marathon: a real franchise choice is required before any
    // round can start (the mode has no "any franchise" default) -- route
    // to the IDLE screen's own franchise picker instead of immediately
    // starting a round with no filter value, which would silently fall
    // through to the unfiltered random-shuffle candidate order instead of
    // one real franchise's real chronological history.
    if (ENGINE_PILOT_MODES[engineEntry.engineMode].needsFilterValue) {
      enginePilotCurrentModeKey = engineEntry.engineMode;
      state.enginePilot = null;
      state.enginePilotPendingFranchise = null;
      state.screen = 'enginePilot';
      renderAll();
      return;
    }
    startEnginePilotRound(engineEntry.engineMode);
    return;
  }
  // Creator "one approval, fully live" pass: same routing pattern as the
  // engineMode branch just above, for ENGINE_DISCOVERY_ENTRIES entries that
  // belong to the newer mechanicPilot shell (engine-game-ui.js's
  // ENGINE_MECHANIC_MODES) instead of the older single-question enginePilot
  // shell -- these have a `mechanicMode` field instead of `engineMode`.
  var mechanicEntry = ENGINE_DISCOVERY_ENTRIES.find(function (e) { return e.id === mode && e.mechanicMode; });
  if (mechanicEntry) {
    beginProgressSession(mode);
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
    startMechanicPilotRound(mechanicEntry.mechanicMode);
    return;
  }
  // v1.7, Part C8: same unified-discovery routing as the block above, kept
  // as its own small check rather than folded into ENGINE_DISCOVERY_ENTRIES'
  // shape -- Six Degrees' start function takes no modeKey argument (there's
  // only one variant), so reusing that exact shape would need a needless
  // parameter every entry but this one ignores.
  if (mode === 'coach_connections' && ENABLE_ENGINE_SIX_DEGREES_V01) {
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
    startSixDegreesRound();
    return;
  }
  // Weekly Pick'em Player Experience pass: same unified-discovery routing
  // pattern as Six Degrees just above -- Pick'em's real shape (a whole
  // week's slate of games, each independently locked/graded) doesn't fit
  // engine-game-ui.js's one-question-at-a-time shell, so it gets its own
  // dedicated branch and start function (startPickemRound(league)) instead
  // of an ENGINE_DISCOVERY_ENTRIES `engineMode` key.
  if (mode === 'endless') {
    startEndlessMode();
    return;
  }
  if ((mode === 'pickem_nfl' || mode === 'pickem_cfb') && ENABLE_PICKEM_V01) {
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
    startPickemRound(mode === 'pickem_nfl' ? 'NFL' : 'CFB');
    return;
  }
  var files = MODE_DATA_FILES[mode];
  var pending = files && files.filter(function (f) { return !loadedScripts[f]; });
  if (pending && pending.length) {
    var app = document.getElementById('app');
    if (app) app.innerHTML = brandLoadingScreenHtml(modeLabelFor(mode));
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      enterMode(mode);
    }).catch(function () {
      if (app) app.innerHTML = '<div class="panel">Couldn’t load this mode’s data. Check your connection and try again. <button class="btn-secondary" data-go="home">Home</button></div>';
    });
    return;
  }
  // Data file(s) were already loaded by another mode/tab (e.g. Learn's
  // Heisman list also pulls in data/cfb-grid.js).
  if (files && files.length) refreshDataAliases();
  enterMode(mode);
}
function modeToolbarHtml(mode, ranked) {
  return (ranked === false ? '<div class="practice-pill">' + icon('graduationCap') + ' Practice — this round won’t be saved</div>' : '') +
    '<div class="mode-toolbar">' +
    '<button class="btn-tiny" data-report="' + mode + '">' + icon('flag') + ' Report</button>' +
    '<button class="btn-tiny" data-mode-restart="' + mode + '">' + icon('restart') + ' Restart</button>' +
    '<button class="btn-tiny" data-mode-exit>' + icon('close') + ' Exit to Home</button>' +
    '</div>';
}
// Practice-vs-Ranked: one shared "about to start" control (chip-row, same
// component as round-size/timer pickers) reused across all 12 existing game
// modes instead of a bespoke toggle per mode. state.rankedPref remembers
// each mode's last choice independently; absent/undefined defaults to
// Ranked (true) so existing users' behavior is unchanged until they opt in
// to Practice somewhere. Daily Reads is deliberately exempt — it always
// counts, no toggle is rendered for it.
function rankedToggleHtml(mode) {
  var ranked = state.rankedPref[mode] !== false;
  return '<div class="chip-row">' +
    '<button class="chip-toggle' + (ranked ? ' active' : '') + '" data-ranked-toggle="' + mode + ':1">' + icon('target') + ' Ranked</button>' +
    '<button class="chip-toggle' + (!ranked ? ' active' : '') + '" data-ranked-toggle="' + mode + ':0">' + icon('graduationCap') + ' Practice</button>' +
    '</div>';
}
function setRankedPref(mode, ranked) {
  state.rankedPref[mode] = ranked;
  lsSet('nflTriviaRankedPref', state.rankedPref);
  renderAll();
}

// Real accounts — username + password via Firebase Auth (see signUp/logIn/
// logOut in firebase-sync.js), replacing both the old free-text name bar
// AND the PIN-claim system that briefly stood in for real auth. Firebase
// Auth's email/password provider is used under the hood with a synthetic
// slug@reads.local address so nobody ever needs a real email — see
// firebase-sync.js's header comment for the full mechanism. Everything
// authenticated leaderboard/profile/rating writes now key off Firebase UID.
// Legacy username-keyed data is still read as a one-time migration fallback,
// so existing players keep their old progress automatically.
// Canonical account identity. Real Firebase accounts use one stable UID on
// every device; guests retain the original browser-scoped identity.
var activeAuthUid = null;
function canonicalPlayerKey() {
  if (activeAuthUid) return 'uid:' + activeAuthUid;
  return state.name ? 'guest:' + slugify(state.name) + ':' + getClientId() : '';
}
function profileDocId() {
  return activeAuthUid ? 'uid_' + activeAuthUid : slugify(state.name);
}

function saveName(name) {
  name = (name || '').trim();
  if (!name) return;
  state.name = name;
  lsSet('nflTriviaName', name);
  // The leaderboard snapshot (state.leaderboardData) almost always arrives
  // from Firestore before sign-in finishes — but reconcileRating() bails out
  // early with no name set, so a returning player's cloud rating/stats sat
  // there unused until now. Reconcile immediately against whatever's already
  // cached so logging in on a new device picks up the real rating right
  // away instead of wrongly launching the intro test and needing a refresh.
  reconcileRating(state.leaderboardData);
  didInitialProfilePull = true;
  pullProfileSnapshot();
  if (!getRating()) { startIntroTest(); return; }
  if (!consumePendingSocialChallenge() && !consumePendingLiveJoin()) renderAll();
}
function logOut() {
  if (window.__fbSync && window.__fbSync.logOut) window.__fbSync.logOut();
  activeAuthUid = null;
  state.name = '';
  lsSet('nflTriviaName', '');
  lsSet('nflTriviaLoggedIn', false);
  didInitialProfilePull = false;
  renderAll();
}

/* ============================== auth modal (sign up / log in) ============================== */
var authTriggerEl = null;
var authModalMode = 'login'; // 'login' | 'signup'
function openAuthModal(mode) {
  authModalMode = mode === 'signup' ? 'signup' : 'login';
  authTriggerEl = document.activeElement;
  renderAuthModal();
  var usernameEl = document.getElementById('auth-username-input');
  var passwordEl = document.getElementById('auth-password-input');
  if (usernameEl) usernameEl.value = '';
  if (passwordEl) passwordEl.value = '';
  var modal = document.getElementById('auth-modal');
  var backdrop = document.getElementById('auth-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () { if (usernameEl) usernameEl.focus(); }, 0);
}
// Re-labels the modal's static markup for the current mode rather than
// re-rendering it from renderAll() — this modal, like report/rating/pin
// before it, lives outside the normal render cycle so an in-progress typed
// username/password never gets wiped by an unrelated background re-render.
function renderAuthModal() {
  var titleEl = document.getElementById('auth-title');
  var contextEl = document.getElementById('auth-context');
  var submitBtn = document.getElementById('auth-submit');
  var switchBtn = document.getElementById('auth-switch');
  var errorEl = document.getElementById('auth-error');
  var passwordEl = document.getElementById('auth-password-input');
  if (errorEl) { errorEl.style.display = 'none'; errorEl.textContent = ''; }
  if (authModalMode === 'signup') {
    if (titleEl) titleEl.textContent = 'Sign Up';
    if (contextEl) contextEl.textContent = 'Pick a username and password — this is a real login, so your Football Rating, stats, favorite teams, and progress follow you to any device. No email needed. Playing under the same name you used before picks up right where you left off.';
    if (submitBtn) submitBtn.textContent = 'Create Account';
    if (switchBtn) switchBtn.textContent = 'Already have an account? Log In';
    if (passwordEl) passwordEl.autocomplete = 'new-password';
  } else {
    if (titleEl) titleEl.textContent = 'Log In';
    if (contextEl) contextEl.textContent = 'Log in to sync your Football Rating, stats, favorite teams, and progress across every device.';
    if (submitBtn) submitBtn.textContent = 'Log In';
    if (switchBtn) switchBtn.textContent = 'Don’t have an account? Sign Up';
    if (passwordEl) passwordEl.autocomplete = 'current-password';
  }
}
function closeAuthModal() {
  var modal = document.getElementById('auth-modal');
  var backdrop = document.getElementById('auth-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  restoreFocus(authTriggerEl);
  authTriggerEl = null;
}
function authModalSwitch() {
  authModalMode = authModalMode === 'signup' ? 'login' : 'signup';
  renderAuthModal();
  var usernameEl = document.getElementById('auth-username-input');
  if (usernameEl) usernameEl.focus();
}
function authModalError(msg) {
  var errorEl = document.getElementById('auth-error');
  if (errorEl) { errorEl.textContent = msg; errorEl.style.display = ''; }
}
// Firebase's own error codes, translated into the plain language this app's
// non-technical audience needs — same spirit as authFriendlyError's only
// caller, avoids ever surfacing a raw "auth/wrong-password" to a player.
function authFriendlyError(err) {
  var code = err && err.code;
  if (code === 'auth/email-already-in-use') return 'That username is taken — try another, or log in instead.';
  if (code === 'auth/user-not-found') return 'No account with that username.';
  if (code === 'auth/wrong-password' || code === 'auth/invalid-credential') return 'Wrong password.';
  if (code === 'auth/weak-password') return 'Password needs to be at least 6 characters.';
  if (code === 'auth/invalid-email') return 'Usernames can only use letters, numbers, and underscores.';
  return 'Something went wrong — check your connection and try again.';
}
function authModalSubmit() {
  var usernameEl = document.getElementById('auth-username-input');
  var passwordEl = document.getElementById('auth-password-input');
  var username = usernameEl ? usernameEl.value.trim() : '';
  var password = passwordEl ? passwordEl.value : '';
  if (!username) { authModalError('Enter a username.'); return; }
  if (!password) { authModalError('Enter a password.'); return; }
  if (!window.__fbSync || !window.__fbSync.signUp || !window.__fbSync.logIn) { authModalError('Not connected — check your connection and try again.'); return; }
  var submitBtn = document.getElementById('auth-submit');
  if (submitBtn) submitBtn.disabled = true;
  var action = authModalMode === 'signup' ? window.__fbSync.signUp(username, password) : window.__fbSync.logIn(username, password);
  action.then(function (result) {
    activeAuthUid = result.uid || activeAuthUid;
    closeAuthModal();
    saveName(result.username);
  }).catch(function (err) {
    console.error('Auth failed', err);
    authModalError(authFriendlyError(err));
  }).then(function () { if (submitBtn) submitBtn.disabled = false; });
}

// Full Visual + Interactive Redesign pass: a premium avatar-initial +
// identity treatment (matching the redesigned homepage mockup's profile
// strip), universal across every screen this already rendered on before
// (never home-only — see this function's original callsite in
// renderAll()). No new data: the initial is just state.name's own first
// character, uppercased -- never a fabricated photo/avatar-picker system.
// Favorite-team color rings the avatar when set (via the existing
// --home-accent/has-fav-team cascade already driving the header bar),
// so the identity strip carries the same real personalization signal
// everywhere it appears, not just on Home.
function nameBarHtml() {
  if (!state.name) {
    return '<div class="name-bar">' +
      '<button class="btn-primary" data-auth-open="login">Log In</button><button class="btn-secondary" data-auth-open="signup">Sign Up</button>' +
      '</div>';
  }
  var initial = state.name.trim().charAt(0).toUpperCase() || '?';
  return '<div class="name-bar">' +
    '<span class="name-bar-avatar" aria-hidden="true">' + esc(initial) + '</span>' +
    '<span class="name-bar-text"><span class="name-bar-eyebrow">Playing as</span><b>' + esc(state.name) + '</b></span>' +
    '<span class="name-bar-actions">' +
    '<button class="btn-secondary" data-go="profile">' + icon('barChart') + ' Stats</button>' +
    '<button class="btn-secondary" data-log-out>Log Out</button>' +
    '</span></div>';
}

/* ============================== home ============================== */
// Single source of truth for every mode's id/icon/title/description — drives the
// Home screen's mode-card grid AND the NFL/CFB dropdown-or-bottom-sheet picker
// (see openModeSheet), so the two never drift out of sync with each other.
// difficulty here is a per-MODE tag (how forgiving the format itself is —
// multiple-choice-with-feedback vs. open-recall-typing-with-no-hints, timed
// or not) — deliberately not called "Easy/Medium/Hard" so it can't be
// confused with Quiz's own internal per-QUESTION difficulty picker, which is
// a completely different, unrelated setting.
// v1.6, Part C6/C12: engine-backed modes plug into the SAME registry/card
// grid every hand-authored mode already uses -- a player sees one unified
// NFL Modes list, never "old mode vs. engine mode" (Part C6's own framing).
// Built conditionally on each pilot's existing flag (ENGINE_GATEWAY_UI's
// own gate, unchanged) so BOTH entries are simply absent from LEAGUE_MODES
// entirely -- not shown-but-disabled -- when a flag is off, matching Part
// C12 ("if flags are OFF: do not present dead cards that lead nowhere") and
// keeping the shipped default (both OFF) visually identical to v1.5's
// homepage. Title/desc are read from ENGINE_PILOT_MODES (engine-game-ui.js)
// rather than duplicated here, so there is exactly one place that owns that
// copy. `engineMode` is an internal-only routing marker (Part C5: "do not
// expose engine_backed to users unless useful internally") -- modeCardHtml()
// never reads it; only goToMode() below does, to dispatch into the shared
// engine shell instead of the normal local-mode path.
// UI/product polish pass: every entry now carries the same `difficulty`
// field every hand-authored card already has (modeCardHtml() only renders
// the badge when it's present -- these 5 cards were rendering with a
// visibly blank top-right corner next to every other card that has one,
// looking unfinished by comparison) and an explicit `league` so each entry
// lands in the tab it actually belongs to -- see the real bug this fixed,
// just below.
var ENGINE_DISCOVERY_ENTRIES = [];
if (typeof ENGINE_PILOT_MODES !== 'undefined') {
  if (ENGINE_PILOT_MODES.draft.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'draft_guess', icon: 'flag', title: ENGINE_PILOT_MODES.draft.title,
      desc: ENGINE_PILOT_MODES.draft.desc, engineMode: 'draft', league: 'nfl', difficulty: 'competitive',
    });
  }
  if (ENGINE_PILOT_MODES.championship.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'championship_guess', icon: 'lombardiTrophy', title: ENGINE_PILOT_MODES.championship.title,
      desc: ENGINE_PILOT_MODES.championship.desc, engineMode: 'championship', league: 'nfl', difficulty: 'competitive',
    });
  }
  // v1.8, Part F/O.
  if (ENGINE_PILOT_MODES.lineup.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'lineup_guess', icon: 'users', title: ENGINE_PILOT_MODES.lineup.title,
      desc: ENGINE_PILOT_MODES.lineup.desc, engineMode: 'lineup', league: 'nfl', difficulty: 'hardcore',
    });
  }
  // CFB data enrichment operation -- the first CFB entry in the same
  // unified discovery array, same shared-shell dispatch as every NFL entry
  // above (Part 14's "no separate CFB architecture" carried into the
  // frontend too). `league: 'cfb'` is the real fix: this used to have no
  // league tag at all, so it fell into LEAGUE_MODES.nfl by default (every
  // ENGINE_DISCOVERY_ENTRIES entry was concatenated onto the NFL array,
  // unconditionally) -- a real, visible bug found by actually opening the
  // NFL tab in production: "CFB Heisman Winners" was listed as an NFL
  // mode. Distinct icon from Championship's lombardiTrophy too (both used
  // the same trophy glyph before, making them hard to tell apart at a
  // glance in the same grid).
  if (ENGINE_PILOT_MODES.heisman.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_heisman_guess', icon: 'cfpTrophy', title: ENGINE_PILOT_MODES.heisman.title,
      desc: ENGINE_PILOT_MODES.heisman.desc, engineMode: 'heisman', league: 'cfb', difficulty: 'casual',
    });
  }
  // Creator stress test / discovery pass: 4 real, already-live capabilities
  // (Public-readiness punch-list / Historical Engine Enrichment operations)
  // that had a working flag + hidden route but NO discovery card at all --
  // a real user browsing the homepage had no way to ever find them, only a
  // direct hash link. Same registration pattern as every entry above.
  if (ENGINE_PILOT_MODES.lineupCollege.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'lineup_college_guess', icon: 'graduationCap', title: ENGINE_PILOT_MODES.lineupCollege.title,
      desc: ENGINE_PILOT_MODES.lineupCollege.desc, engineMode: 'lineupCollege', league: 'nfl', difficulty: 'hardcore',
    });
  }
  // Product Growth + Real User Testing pass: these three are each built
  // from one real, specific NFL/CFB game (a real matchup + its real
  // result/box score) -- exactly the "featured NFL games"/"featured CFB
  // games" discovery priority this pass calls for. Real content that
  // already existed; just wasn't marked featured yet.
  if (ENGINE_PILOT_MODES.nflGameResult.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'nfl_game_result_guess', icon: 'football', title: ENGINE_PILOT_MODES.nflGameResult.title,
      desc: ENGINE_PILOT_MODES.nflGameResult.desc, engineMode: 'nflGameResult', league: 'nfl', difficulty: 'casual', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.nflGameBoxscore.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'nfl_game_boxscore_guess', icon: 'sync', title: ENGINE_PILOT_MODES.nflGameBoxscore.title,
      desc: ENGINE_PILOT_MODES.nflGameBoxscore.desc, engineMode: 'nflGameBoxscore', league: 'nfl', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.cfbGameResult.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_game_result_guess', icon: 'football', title: ENGINE_PILOT_MODES.cfbGameResult.title,
      desc: ENGINE_PILOT_MODES.cfbGameResult.desc, engineMode: 'cfbGameResult', league: 'cfb', difficulty: 'casual', featured: true,
    });
  }
  // Creator stress test / discovery pass: the first 4 modes promoted
  // straight from Creator-only to public certification this pass (real
  // candidate surveys in gateway/services/public_game.py).
  // featured:true on the three modes this task explicitly named as things
  // "people can actually find" -- same first-tier grid treatment Quiz/Grid/
  // IQ Test/Player From Clues already get (modeSectionHtml() below), not
  // left to compete for attention in the larger unfeatured grid.
  if (ENGINE_PILOT_MODES.offenseCollege.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'offense_college_guess', icon: 'users', title: ENGINE_PILOT_MODES.offenseCollege.title,
      desc: ENGINE_PILOT_MODES.offenseCollege.desc, engineMode: 'offenseCollege', league: 'nfl', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.sbChampionOffenseCollege.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'sb_champion_offense_college_guess', icon: 'lombardiTrophy', title: ENGINE_PILOT_MODES.sbChampionOffenseCollege.title,
      desc: ENGINE_PILOT_MODES.sbChampionOffenseCollege.desc, engineMode: 'sbChampionOffenseCollege', league: 'nfl', difficulty: 'competitive',
    });
  }
  if (ENGINE_PILOT_MODES.cfbRanking.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_ranking_guess', icon: 'arrowUp', title: ENGINE_PILOT_MODES.cfbRanking.title,
      desc: ENGINE_PILOT_MODES.cfbRanking.desc, engineMode: 'cfbRanking', league: 'cfb', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.cfbUpset.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_upset_guess', icon: 'flame', title: ENGINE_PILOT_MODES.cfbUpset.title,
      desc: ENGINE_PILOT_MODES.cfbUpset.desc, engineMode: 'cfbUpset', league: 'cfb', difficulty: 'hardcore', featured: true,
    });
  }
  // Public Mode Wiring pass (Pass 2.5): 8 real backend capabilities newly
  // certified public this pass.
  if (ENGINE_PILOT_MODES.cfbRivalry.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_rivalry_guess', icon: 'versus', title: ENGINE_PILOT_MODES.cfbRivalry.title,
      desc: ENGINE_PILOT_MODES.cfbRivalry.desc, engineMode: 'cfbRivalry', league: 'cfb', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.cfbRivalryLookup.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_rivalry_lookup_guess', icon: 'shield', title: ENGINE_PILOT_MODES.cfbRivalryLookup.title,
      desc: ENGINE_PILOT_MODES.cfbRivalryLookup.desc, engineMode: 'cfbRivalryLookup', league: 'cfb', difficulty: 'casual',
    });
  }
  if (ENGINE_PILOT_MODES.spotTheFake.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_spot_the_fake_guess', icon: 'xMark', title: ENGINE_PILOT_MODES.spotTheFake.title,
      desc: ENGINE_PILOT_MODES.spotTheFake.desc, engineMode: 'spotTheFake', league: 'cfb', difficulty: 'hardcore', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.threeClues.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_three_clues_guess', icon: 'mystery', title: ENGINE_PILOT_MODES.threeClues.title,
      desc: ENGINE_PILOT_MODES.threeClues.desc, engineMode: 'threeClues', league: 'cfb', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.eraGauntlet.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'era_gauntlet_guess', icon: 'timeline', title: ENGINE_PILOT_MODES.eraGauntlet.title,
      desc: ENGINE_PILOT_MODES.eraGauntlet.desc, engineMode: 'eraGauntlet', league: 'cfb', difficulty: 'competitive', featured: true,
    });
  }
  if (ENGINE_PILOT_MODES.oddCollegeOut.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_odd_college_out_guess', icon: 'search', title: ENGINE_PILOT_MODES.oddCollegeOut.title,
      desc: ENGINE_PILOT_MODES.oddCollegeOut.desc, engineMode: 'oddCollegeOut', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_PILOT_MODES.oneSchoolMissing.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'cfb_one_school_missing_guess', icon: 'grid', title: ENGINE_PILOT_MODES.oneSchoolMissing.title,
      desc: ENGINE_PILOT_MODES.oneSchoolMissing.desc, engineMode: 'oneSchoolMissing', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_PILOT_MODES.franchiseMarathon.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'franchise_marathon_guess', icon: 'lombardiTrophy', title: ENGINE_PILOT_MODES.franchiseMarathon.title,
      desc: ENGINE_PILOT_MODES.franchiseMarathon.desc, engineMode: 'franchiseMarathon', league: 'nfl', difficulty: 'competitive', featured: true,
    });
  }
}
// Creator "one approval, fully live" pass: real discovery cards for the 12
// mechanicPilot-shell formats (15-Format Expansion's Blind Resume + all 11
// of the 75-Format Expansion's Wave 1) that, until now, had a working
// backend and a working renderer but were reachable ONLY by typing their
// exact hidden #hash URL -- zero menu card, so a real player had no way to
// ever find them. `mechanicMode` (not `engineMode`) tells goToMode() above
// to route through startMechanicPilotRound() instead of
// startEnginePilotRound(). Gated the same way every other engine card is:
// present in this array only when its own flagOn() is true.
if (typeof ENGINE_MECHANIC_MODES !== 'undefined') {
  // Same real gap as blindResume et al. below, just never swept before now
  // because the flag was off: no discovery card meant no real player could
  // ever find RISK_IT even once enabled.
  if (ENGINE_MECHANIC_MODES.riskIt.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'risk_it_guess', icon: 'flame', title: ENGINE_MECHANIC_MODES.riskIt.title,
      desc: ENGINE_MECHANIC_MODES.riskIt.desc, mechanicMode: 'riskIt', league: 'nfl', difficulty: 'hardcore',
    });
  }
  if (ENGINE_MECHANIC_MODES.riskItCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'risk_it_cfb_guess', icon: 'flame', title: ENGINE_MECHANIC_MODES.riskItCfb.title,
      desc: ENGINE_MECHANIC_MODES.riskItCfb.desc, mechanicMode: 'riskItCfb', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_MECHANIC_MODES.blindResume.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'blind_resume_guess', icon: 'mystery', title: ENGINE_MECHANIC_MODES.blindResume.title,
      desc: ENGINE_MECHANIC_MODES.blindResume.desc, mechanicMode: 'blindResume', league: 'nfl', difficulty: 'hardcore',
    });
  }
  // CFB retrofit pass -- built on cfb_player_season_stats_real.
  if (ENGINE_MECHANIC_MODES.blindResumeCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'blind_resume_cfb_guess', icon: 'mystery', title: ENGINE_MECHANIC_MODES.blindResumeCfb.title,
      desc: ENGINE_MECHANIC_MODES.blindResumeCfb.desc, mechanicMode: 'blindResumeCfb', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_MECHANIC_MODES.doubleOrNothing.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'double_or_nothing_guess', icon: 'zap', title: ENGINE_MECHANIC_MODES.doubleOrNothing.title,
      desc: ENGINE_MECHANIC_MODES.doubleOrNothing.desc, mechanicMode: 'doubleOrNothing', league: 'nfl', difficulty: 'competitive',
    });
  }
  // CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
  // see double_or_nothing.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.doubleOrNothingCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'double_or_nothing_cfb_guess', icon: 'zap', title: ENGINE_MECHANIC_MODES.doubleOrNothingCfb.title,
      desc: ENGINE_MECHANIC_MODES.doubleOrNothingCfb.desc, mechanicMode: 'doubleOrNothingCfb', league: 'cfb', difficulty: 'competitive',
    });
  }
  if (ENGINE_MECHANIC_MODES.kingOfTheHill.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'king_of_the_hill_guess', icon: 'shield', title: ENGINE_MECHANIC_MODES.kingOfTheHill.title,
      desc: ENGINE_MECHANIC_MODES.kingOfTheHill.desc, mechanicMode: 'kingOfTheHill', league: 'nfl', difficulty: 'competitive',
    });
  }
  // CFB retrofit pass -- reuses higher_lower.py's own already-certified
  // cfb_standings.total_wins data (FBS only), zero new data work.
  if (ENGINE_MECHANIC_MODES.kingOfTheHillCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'king_of_the_hill_cfb_guess', icon: 'shield', title: ENGINE_MECHANIC_MODES.kingOfTheHillCfb.title,
      desc: ENGINE_MECHANIC_MODES.kingOfTheHillCfb.desc, mechanicMode: 'kingOfTheHillCfb', league: 'cfb', difficulty: 'competitive',
    });
  }
  if (ENGINE_MECHANIC_MODES.factOrFake.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'fact_or_fake_guess', icon: 'search', title: ENGINE_MECHANIC_MODES.factOrFake.title,
      desc: ENGINE_MECHANIC_MODES.factOrFake.desc, mechanicMode: 'factOrFake', league: 'nfl', difficulty: 'casual',
    });
  }
  // CFB retrofit pass -- real game-result statement, see
  // fact_or_fake.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.factOrFakeCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'fact_or_fake_cfb_guess', icon: 'search', title: ENGINE_MECHANIC_MODES.factOrFakeCfb.title,
      desc: ENGINE_MECHANIC_MODES.factOrFakeCfb.desc, mechanicMode: 'factOrFakeCfb', league: 'cfb', difficulty: 'casual',
    });
  }
  if (ENGINE_MECHANIC_MODES.guessTheRanking.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'guess_the_ranking_guess', icon: 'barChart', title: ENGINE_MECHANIC_MODES.guessTheRanking.title,
      desc: ENGINE_MECHANIC_MODES.guessTheRanking.desc, mechanicMode: 'guessTheRanking', league: 'nfl', difficulty: 'competitive',
    });
  }
  // CFB retrofit pass -- self-contained real top-15 CFB career passing
  // yards query, see guess_the_ranking.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.guessTheRankingCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'guess_the_ranking_cfb_guess', icon: 'barChart', title: ENGINE_MECHANIC_MODES.guessTheRankingCfb.title,
      desc: ENGINE_MECHANIC_MODES.guessTheRankingCfb.desc, mechanicMode: 'guessTheRankingCfb', league: 'cfb', difficulty: 'competitive',
    });
  }
  if (ENGINE_MECHANIC_MODES.statTarget.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'stat_target_guess', icon: 'target', title: ENGINE_MECHANIC_MODES.statTarget.title,
      desc: ENGINE_MECHANIC_MODES.statTarget.desc, mechanicMode: 'statTarget', league: 'nfl', difficulty: 'competitive',
    });
  }
  // CFB retrofit pass -- same real capability, real CFB data source
  // (cfb_player_season_stats_real) instead of NFL's player_season_stats.
  if (ENGINE_MECHANIC_MODES.statTargetCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'stat_target_cfb_guess', icon: 'target', title: ENGINE_MECHANIC_MODES.statTargetCfb.title,
      desc: ENGINE_MECHANIC_MODES.statTargetCfb.desc, mechanicMode: 'statTargetCfb', league: 'cfb', difficulty: 'competitive',
    });
  }
  if (ENGINE_MECHANIC_MODES.reverseTrivia.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'reverse_trivia_guess', icon: 'sync', title: ENGINE_MECHANIC_MODES.reverseTrivia.title,
      desc: ENGINE_MECHANIC_MODES.reverseTrivia.desc, mechanicMode: 'reverseTrivia', league: 'nfl', difficulty: 'casual',
    });
  }
  // CFB retrofit pass -- real season passing stat line, see
  // reverse_trivia.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.reverseTriviaCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'reverse_trivia_cfb_guess', icon: 'sync', title: ENGINE_MECHANIC_MODES.reverseTriviaCfb.title,
      desc: ENGINE_MECHANIC_MODES.reverseTriviaCfb.desc, mechanicMode: 'reverseTriviaCfb', league: 'cfb', difficulty: 'casual',
    });
  }
  if (ENGINE_MECHANIC_MODES.threeStrikes.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'three_strikes_guess', icon: 'xMark', title: ENGINE_MECHANIC_MODES.threeStrikes.title,
      desc: ENGINE_MECHANIC_MODES.threeStrikes.desc, mechanicMode: 'threeStrikes', league: 'nfl', difficulty: 'hardcore',
    });
  }
  // CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
  // see three_strikes.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.threeStrikesCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'three_strikes_cfb_guess', icon: 'xMark', title: ENGINE_MECHANIC_MODES.threeStrikesCfb.title,
      desc: ENGINE_MECHANIC_MODES.threeStrikesCfb.desc, mechanicMode: 'threeStrikesCfb', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_MECHANIC_MODES.mysteryRoster.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'mystery_roster_guess', icon: 'lock', title: ENGINE_MECHANIC_MODES.mysteryRoster.title,
      desc: ENGINE_MECHANIC_MODES.mysteryRoster.desc, mechanicMode: 'mysteryRoster', league: 'nfl', difficulty: 'hardcore',
    });
  }
  // CFB retrofit pass -- real leading-passer/leading-rusher+receiver/
  // class_year substitutes, see mystery_roster.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.mysteryRosterCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'mystery_roster_cfb_guess', icon: 'lock', title: ENGINE_MECHANIC_MODES.mysteryRosterCfb.title,
      desc: ENGINE_MECHANIC_MODES.mysteryRosterCfb.desc, mechanicMode: 'mysteryRosterCfb', league: 'cfb', difficulty: 'hardcore',
    });
  }
  if (ENGINE_MECHANIC_MODES.draftPickLadder.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'draft_pick_ladder_guess', icon: 'arrowUp', title: ENGINE_MECHANIC_MODES.draftPickLadder.title,
      desc: ENGINE_MECHANIC_MODES.draftPickLadder.desc, mechanicMode: 'draftPickLadder', league: 'nfl', difficulty: 'competitive',
    });
  }
  if (ENGINE_MECHANIC_MODES.categoryRoulette.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'category_roulette_guess', icon: 'grid', title: ENGINE_MECHANIC_MODES.categoryRoulette.title,
      desc: ENGINE_MECHANIC_MODES.categoryRoulette.desc, mechanicMode: 'categoryRoulette', league: 'nfl', difficulty: 'casual',
    });
  }
  if (ENGINE_MECHANIC_MODES.commonLink.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'common_link_guess', icon: 'users', title: ENGINE_MECHANIC_MODES.commonLink.title,
      desc: ENGINE_MECHANIC_MODES.commonLink.desc, mechanicMode: 'commonLink', league: 'nfl', difficulty: 'competitive',
    });
  }
  // CFB retrofit pass -- real school/season/conference link types, see
  // common_link.py's own module docstring.
  if (ENGINE_MECHANIC_MODES.commonLinkCfb.flagOn()) {
    ENGINE_DISCOVERY_ENTRIES.push({
      id: 'common_link_cfb_guess', icon: 'users', title: ENGINE_MECHANIC_MODES.commonLinkCfb.title,
      desc: ENGINE_MECHANIC_MODES.commonLinkCfb.desc, mechanicMode: 'commonLinkCfb', league: 'cfb', difficulty: 'competitive',
    });
  }
}
// v1.7, Part C8 (v2 rebuild: graph-driven Coach Connections): joins the
// exact same discovery array -- card rendering (modeCardHtml) doesn't care
// that its routing (goToMode's own separate `mode === 'coach_connections'`
// check, above) differs slightly from the draft/championship entries'
// shared engineMode dispatch.
if (ENABLE_ENGINE_SIX_DEGREES_V01) {
  ENGINE_DISCOVERY_ENTRIES.push({
    id: 'coach_connections', icon: 'versus', title: 'Coach Connections',
    desc: 'Connect two NFL people through real career history — coaches, players, and teams.',
    league: 'nfl', difficulty: 'hardcore',
  });
}
// Weekly Pick'em Player Experience pass: same no-engineMode discovery
// pattern as Coach Connections/Six Degrees just above -- routed by its own
// dedicated goToMode() branch (startPickemRound), not the shared
// engineMode dispatch, since a whole week's slate doesn't fit that
// one-question-at-a-time shell.
if (ENABLE_PICKEM_V01) {
  ENGINE_DISCOVERY_ENTRIES.push({
    id: 'pickem_nfl', icon: 'flag', title: "NFL Pick'em",
    desc: "Pick the winner of every real game on this week's NFL slate.",
    league: 'nfl', difficulty: 'casual',
  });
  ENGINE_DISCOVERY_ENTRIES.push({
    id: 'pickem_cfb', icon: 'flag', title: "CFB Pick'em",
    desc: "Pick winners for a Featured, Top 25, Power Four, Conference, or Full college slate.",
    league: 'cfb', difficulty: 'casual',
  });
}
var LEAGUE_MODES = {
  nfl: [
    { id: 'quiz', icon: 'helpCircle', title: 'NFL Quiz', desc: QUIZ.length + ' multiple-choice questions across ' + quizCategories().length + ' categories. Choose category, difficulty, and round length.', featured: true, difficulty: 'casual' },
    { id: 'grid', icon: 'grid', title: 'NFL Grid', desc: 'A freshly generated 3x3 grid every round. Name a player who satisfies both the row and the column.', featured: true, difficulty: 'hardcore' },
    { id: 'blitz', icon: 'timer', title: 'NFL Blitz', desc: 'Sporcle-style: type every correct answer you can before the clock runs out.', difficulty: 'hardcore' },
    { id: 'speed', icon: 'zap', title: 'NFL Speed', desc: 'Rapid-fire multiple choice against the clock. Build a streak for bonus points.', difficulty: 'competitive' },
    { id: 'silhouette', icon: 'search', title: 'NFL Silhouette', desc: 'A generic pose silhouette and a ladder of clues — guess the player using as few hints as you can.', difficulty: 'competitive' },
    { id: 'iq', icon: 'brain', title: 'NFL IQ Test', desc: '25 questions, no feedback until the end. Get a Football IQ score and a category breakdown.', featured: true, difficulty: 'competitive' },
    { id: 'legends', icon: 'trophy', title: '17-0', desc: 'Draft a 7-player team from real players\' real seasons (1999-2025) and see if it grades out as a perfect season.', difficulty: 'competitive' },
    { id: 'higherLower', icon: 'arrowUp', title: 'Higher or Lower', desc: 'Two real players, one real stat — guess higher or lower than the last one. Keep going until you miss.', difficulty: 'casual' }
  ]
    // UI/UX Upgrade Pass: Player From Clues, surfaced as a real mode card for
    // the first time (previously only reachable via the hidden #clues route)
    // -- still gated on its own real flag, same discipline as every
    // ENGINE_DISCOVERY_ENTRIES entry below. featured:true because Section 1
    // of this pass explicitly calls out "NFL Who Am I" as a first-class
    // homepage priority.
    .concat(ENABLE_PLAYER_FROM_CLUES_V01 ? [
      { id: 'playerClues', icon: 'target', title: 'Player From Clues', desc: 'A ladder of real, verified clues about one NFL player — narrowing from broad to specific. Guess who it is with as few clues as you can.', featured: true, difficulty: 'competitive' },
    ] : [])
    .concat(ENGINE_DISCOVERY_ENTRIES.filter(function (e) { return e.league !== 'cfb'; })),
  cfb: [
    { id: 'cfbQuiz', icon: 'graduationCap', title: 'College Football Quiz', desc: CFB.length + ' CFB questions across ' + cfbCategories().length + ' categories — Heisman, rivalries, coaches, bowls, and more.', featured: true, difficulty: 'casual' },
    { id: 'cfbGrid', icon: 'grid', title: 'CFB Immaculate Grid', desc: 'A freshly generated 3x3 grid of schools and All-America/Heisman criteria. Name a player who satisfies both the row and the column.', featured: true, difficulty: 'hardcore' },
    { id: 'cfbBlitz', icon: 'timer', title: 'CFB Blitz', desc: 'Sporcle-style college football: type every correct answer you can before the clock runs out.', difficulty: 'hardcore' },
    { id: 'cfbSpeed', icon: 'zap', title: 'CFB Speed Round', desc: 'Rapid-fire college football multiple choice against the clock. Build a streak for bonus points.', difficulty: 'competitive' },
    { id: 'cfbIq', icon: 'book', title: 'College Football IQ Test', desc: 'The IQ Test format, college edition. 25 questions, no feedback until the end.', featured: true, difficulty: 'competitive' },
    { id: 'cfbLegends', icon: 'trophy', title: 'CFB 12-0', desc: 'Draft an 8-player college roster (including a whole team DEFENSE) from real players\' and teams\' real seasons (1990-2025), then see how your 12-game regular season plays out — and where it lands you in the postseason.', difficulty: 'competitive' }
  ]
    .concat(ENABLE_CFB_PLAYER_FROM_CLUES_V01 ? [
      { id: 'cfbPlayerClues', icon: 'target', title: 'CFB Player From Clues', desc: 'A ladder of real clues about a college football player — narrowing from broad to specific. Guess who it is with as few clues as you can.', featured: true, difficulty: 'competitive' },
    ] : [])
    .concat(ENGINE_DISCOVERY_ENTRIES.filter(function (e) { return e.league === 'cfb'; }))
};
var LEAGUE_LABELS = { nfl: 'NFL Modes', cfb: 'College Football Modes' };

/* ============================== favorite team ==============================
   NFL team codes/names match GRID_TEAM_NAMES in data/grid.js exactly (all 32
   teams supported by NFL Grid's own team criteria). The CFB list is the same
   48 schools CFB_GRID_SCHOOL_CODES in data/cfb-grid.js supports, PLUS every
   other current Power 4 (SEC/Big Ten/Big 12/ACC) school not already in that
   48 — the picker itself is meant to cover every major program a real fan
   might pick, which is a bigger list than what CFB Grid's own criteria pool
   happens to include. The practical effect: the CFB Grid gameplay nudge
   (cfbGridWeightOf, see the CFB Grid section) only ever does anything for
   the original 48 — for a Power-4-only school outside that set, the nudge
   condition just never matches and buildCfbGridAttempt() falls back to
   normal weighted selection, same as having no favorite at all. Every other
   part of this feature (the picker, header accent, greeting, share-card
   tint, "Your Team" chip) works identically for all 73 schools regardless.
   Hardcoded here (not read from either data file) because this needs to work
   from a cold Home-screen load, before either lazy-loaded file has
   necessarily been fetched. Colors are each team/school's real, publicly-
   documented primary color (the same kind of value sports-reference sites
   list freely) — NOT logos. Deliberately no logo images anywhere in this
   feature: real NFL/NCAA team logos are trademarked, this repo has no logo
   assets, and fetching or embedding them for a publicly-shared app would be
   a real trademark risk with no clean fallback — color + team name carries
   the same identity without that risk. */
// `chant` is each team's real, distinctive rallying cry (not a generic "Go
// [Mascot]", which nearly every program has and doesn't say anything unique
// about it — "War Eagle", "Roll Tide" style phrases specific to that team's
// own culture/history) — deliberately included ONLY where I'm genuinely
// confident it's real and well-known, left off entirely otherwise rather
// than inventing a plausible-sounding one. Every render site treats a
// missing chant as "say nothing extra," never a placeholder.
var NFL_TEAMS = [
  { id: 'ARI', name: 'Arizona Cardinals', color: '#97233F', color2: '#000000' },
  { id: 'ATL', name: 'Atlanta Falcons', color: '#A71930', color2: '#000000' },
  { id: 'BAL', name: 'Baltimore Ravens', color: '#241773', color2: '#000000' },
  { id: 'BUF', name: 'Buffalo Bills', color: '#00338D', color2: '#C60C30' },
  { id: 'CAR', name: 'Carolina Panthers', color: '#0085CA', color2: '#101820' },
  { id: 'CHI', name: 'Chicago Bears', color: '#0B162A', color2: '#C83803', chant: 'Bear Down!' },
  { id: 'CIN', name: 'Cincinnati Bengals', color: '#FB4F14', color2: '#000000' },
  { id: 'CLE', name: 'Cleveland Browns', color: '#311D00', color2: '#FF3C00' },
  { id: 'DAL', name: 'Dallas Cowboys', color: '#041E42', color2: '#869397' },
  { id: 'DEN', name: 'Denver Broncos', color: '#FB4F14', color2: '#002244' },
  { id: 'DET', name: 'Detroit Lions', color: '#0076B6', color2: '#B0B7BC' },
  { id: 'GB', name: 'Green Bay Packers', color: '#203731', color2: '#FFB612', chant: 'Go Pack Go!' },
  { id: 'HOU', name: 'Houston Texans', color: '#03202F', color2: '#A71930' },
  { id: 'IND', name: 'Indianapolis Colts', color: '#002C5F' },
  { id: 'JAX', name: 'Jacksonville Jaguars', color: '#006778', color2: '#D7A22A' },
  { id: 'KC', name: 'Kansas City Chiefs', color: '#E31837', color2: '#FFB81C' },
  { id: 'LAC', name: 'Los Angeles Chargers', color: '#0080C6', color2: '#FFC20E' },
  { id: 'LAR', name: 'Los Angeles Rams', color: '#003594', color2: '#FFA300' },
  { id: 'LV', name: 'Las Vegas Raiders', color: '#000000', color2: '#A5ACAF' },
  { id: 'MIA', name: 'Miami Dolphins', color: '#008E97', color2: '#FC4C02' },
  { id: 'MIN', name: 'Minnesota Vikings', color: '#4F2683', color2: '#FFC62F', chant: 'Skol!' },
  { id: 'NE', name: 'New England Patriots', color: '#002244', color2: '#C60C30' },
  { id: 'NO', name: 'New Orleans Saints', color: '#D3BC8D', color2: '#101820', chant: 'Who Dat!' },
  { id: 'NYG', name: 'New York Giants', color: '#0B2265', color2: '#A71930' },
  { id: 'NYJ', name: 'New York Jets', color: '#125740' },
  { id: 'PHI', name: 'Philadelphia Eagles', color: '#004C54', color2: '#A5ACAF', chant: 'Fly Eagles Fly!' },
  { id: 'PIT', name: 'Pittsburgh Steelers', color: '#FFB612', color2: '#101820', chant: 'Here We Go!' },
  { id: 'SF', name: 'San Francisco 49ers', color: '#AA0000', color2: '#B3995D' },
  { id: 'SEA', name: 'Seattle Seahawks', color: '#002244', color2: '#69BE28' },
  { id: 'TB', name: 'Tampa Bay Buccaneers', color: '#D50A0A', color2: '#34302B' },
  { id: 'TEN', name: 'Tennessee Titans', color: '#0C2340', color2: '#C8102E' },
  { id: 'WAS', name: 'Washington Commanders', color: '#5A1414', color2: '#FFB612' }
];
var CFB_TEAMS = [
  { id: 'Notre Dame', name: 'Notre Dame', code: "ND", color: '#0C2340', color2: '#C99700', chant: 'Wake Up the Echoes!' },
  { id: 'Yale', name: 'Yale', code: "YALE", color: '#00356B' },
  { id: 'Alabama', name: 'Alabama', code: "BAMA", color: '#9E1B32', chant: 'Roll Tide!' },
  { id: 'Ohio State', name: 'Ohio State', code: "OSU", color: '#BB0000', color2: '#666666', chant: 'O-H! I-O!' },
  { id: 'Michigan', name: 'Michigan', code: "MICH", color: '#00274C', color2: '#FFCB05', chant: 'Go Blue!' },
  { id: 'Oklahoma', name: 'Oklahoma', code: "OU", color: '#841617', color2: '#F4E5C2', chant: 'Boomer Sooner!' },
  { id: 'Southern California', name: 'USC', code: "USC", color: '#990000', color2: '#FFC72C', chant: 'Fight On!' },
  { id: 'Princeton', name: 'Princeton', code: "PRIN", color: '#FF8F00' },
  { id: 'Harvard', name: 'Harvard', code: "HARV", color: '#A51C30' },
  { id: 'Nebraska', name: 'Nebraska', code: "NEB", color: '#E41C38', color2: '#F5F1E7', chant: 'Go Big Red!' },
  { id: 'Pittsburgh', name: 'Pittsburgh', code: "PITT", color: '#003594', color2: '#FFB81C' },
  { id: 'Texas', name: 'Texas', code: "TEX", color: '#BF5700', color2: '#FFFFFF', chant: 'Hook \'Em Horns!' },
  { id: 'Minnesota', name: 'Minnesota', code: "MINN", color: '#7A0019', color2: '#FFC62F', chant: 'Ski-U-Mah!' },
  { id: 'Penn State', name: 'Penn State', code: "PSU", color: '#041E42', color2: '#FFFFFF', chant: 'We Are... Penn State!' },
  { id: 'Army', name: 'Army', code: "ARMY", color: '#000000', color2: '#C4B581' },
  { id: 'LSU', name: 'LSU', code: "LSU", color: '#461D7C', color2: '#FDD023', chant: 'Geaux Tigers!' },
  { id: 'Stanford', name: 'Stanford', code: "STAN", color: '#8C1515' },
  { id: 'Penn', name: 'Penn', code: "PENN", color: '#011F5B' },
  { id: 'Georgia', name: 'Georgia', code: "UGA", color: '#BA0C2F', color2: '#000000', chant: 'Go Dawgs! Sic \'Em!' },
  { id: 'Illinois', name: 'Illinois', code: "ILL", color: '#E84A27', color2: '#13294B', chant: 'Oskee Wow-Wow!' },
  { id: 'Wisconsin', name: 'Wisconsin', code: "WISC", color: '#C5050C', chant: 'On Wisconsin!' },
  { id: 'Iowa', name: 'Iowa', code: "IOWA", color: '#FFCD00', color2: '#000000' },
  { id: 'Michigan State', name: 'Michigan State', code: "MSU", color: '#18453B', chant: 'Go Green! Go White!' },
  { id: 'Syracuse', name: 'Syracuse', code: "CUSE", color: '#F76900', color2: '#000E54' },
  { id: 'Florida', name: 'Florida', code: "UF", color: '#0021A5', color2: '#FA4616', chant: 'Gator Chomp!' },
  { id: 'Auburn', name: 'Auburn', code: "AUB", color: '#0C2340', color2: '#DD550C', chant: 'War Eagle!' },
  { id: 'Texas A&M', name: 'Texas A&M', code: "TAMU", color: '#500000', chant: 'Gig \'Em!' },
  { id: 'Florida State', name: 'Florida State', code: "FSU", color: '#782F40', color2: '#CEB888' },
  { id: 'Oklahoma State', name: 'Oklahoma State', code: "OKST", color: '#FF7300', color2: '#000000' },
  { id: 'TCU', name: 'TCU', code: "TCU", color: '#4D1979', chant: 'Riff Ram!' },
  { id: 'Colorado', name: 'Colorado', code: "COLO", color: '#000000', color2: '#CFB87C' },
  { id: 'Oregon', name: 'Oregon', code: "ORE", color: '#154733', color2: '#FEE123' },
  { id: 'Miami (FL)', name: 'Miami (FL)', code: "MIA", color: '#005030', color2: '#F47321', chant: 'The U!' },
  { id: 'UCLA', name: 'UCLA', code: "UCLA", color: '#2D68C4', color2: '#FFD100' },
  { id: 'Arkansas', name: 'Arkansas', code: "ARK", color: '#9D2235', color2: '#000000', chant: 'Woo Pig Sooie!' },
  { id: 'NC State', name: 'NC State', code: "NCST", color: '#CC0000' },
  { id: 'Texas Tech', name: 'Texas Tech', code: "TTU", color: '#CC0000', color2: '#000000' },
  { id: 'Arizona', name: 'Arizona', code: "ARIZ", color: '#AB0520', color2: '#0C234B', chant: 'Bear Down!' },
  { id: 'BYU', name: 'BYU', code: "BYU", color: '#002E5D' },
  { id: 'Clemson', name: 'Clemson', code: "CLEM", color: '#F56600', color2: '#522D80' },
  { id: 'Boston College', name: 'Boston College', code: "BC", color: '#98002E', color2: '#BC9B6A' },
  { id: 'Tennessee', name: 'Tennessee', code: "TENN", color: '#FF8200', color2: '#FFFFFF' },
  { id: 'Utah', name: 'Utah', code: "UTAH", color: '#CC0000' },
  { id: 'Kansas State', name: 'Kansas State', code: "KSU", color: '#512888', chant: 'EMAW!' },
  { id: 'Maryland', name: 'Maryland', code: "UMD", color: '#E03A3E', color2: '#000000' },
  { id: 'Baylor', name: 'Baylor', code: "BAY", color: '#154734', color2: '#FFB81C', chant: 'Sic \'Em Bears!' },
  { id: 'Georgia Tech', name: 'Georgia Tech', code: "GT", color: '#B3A369', color2: '#003057' },
  { id: 'Louisville', name: 'Louisville', code: "LOU", color: '#AD0000', color2: '#000000' },
  // The rest of the current Power 4 (SEC/Big Ten/Big 12/ACC) not already
  // covered above — see the header comment: these work everywhere in this
  // feature except the CFB Grid gameplay nudge, which only applies to the
  // original 48-school set CFB Grid's own criteria pool actually supports.
  { id: 'Kentucky', name: 'Kentucky', code: "UK", color: '#0033A0' },
  { id: 'Mississippi State', name: 'Mississippi State', code: "MSST", color: '#660000', chant: 'Hail State!' },
  { id: 'Missouri', name: 'Missouri', code: "MIZ", color: '#F1B82D', color2: '#000000', chant: 'M-I-Z... Z-O-U!' },
  { id: 'Ole Miss', name: 'Ole Miss', code: "MISS", color: '#CE1126', color2: '#14213D', chant: 'Hotty Toddy!' },
  { id: 'South Carolina', name: 'South Carolina', code: "SC", color: '#73000A', color2: '#000000' },
  { id: 'Vanderbilt', name: 'Vanderbilt', code: "VANDY", color: '#866D4B', color2: '#000000', chant: 'Anchor Down!' },
  { id: 'Indiana', name: 'Indiana', code: "IU", color: '#990000' },
  { id: 'Northwestern', name: 'Northwestern', code: "NW", color: '#4E2A84' },
  { id: 'Purdue', name: 'Purdue', code: "PUR", color: '#CEB888', color2: '#000000', chant: 'Boiler Up!' },
  { id: 'Rutgers', name: 'Rutgers', code: "RUTG", color: '#CC0033', color2: '#000000', chant: 'R-U Rah Rah!' },
  { id: 'Washington', name: 'Washington', code: "WASH", color: '#4B2E83', color2: '#FEC52E' },
  { id: 'Arizona State', name: 'Arizona State', code: "ASU", color: '#8C1D40', color2: '#FFC627', chant: 'Fork \'Em!' },
  { id: 'Cincinnati', name: 'Cincinnati', code: "CIN", color: '#E00122', color2: '#000000' },
  { id: 'Houston', name: 'Houston', code: "HOU", color: '#C8102E' },
  { id: 'Iowa State', name: 'Iowa State', code: "ISU", color: '#C8102E', color2: '#F1BE48' },
  { id: 'Kansas', name: 'Kansas', code: "KU", color: '#0051BA', color2: '#E8000D', chant: 'Rock Chalk Jayhawk!' },
  { id: 'UCF', name: 'UCF', code: "UCF", color: '#BA9B37', color2: '#000000' },
  { id: 'West Virginia', name: 'West Virginia', code: "WVU", color: '#002855', color2: '#EAAA00' },
  { id: 'California', name: 'California', code: "CAL", color: '#003262', color2: '#FDB515' },
  { id: 'Duke', name: 'Duke', code: "DUKE", color: '#003087' },
  { id: 'North Carolina', name: 'North Carolina', code: "UNC", color: '#7BAFD4', color2: '#13294B' },
  { id: 'SMU', name: 'SMU', code: "SMU", color: '#C8102E', color2: '#354CA1' },
  { id: 'Virginia', name: 'Virginia', code: "UVA", color: '#232D4B', color2: '#E57200', chant: 'Wahoowa!' },
  { id: 'Virginia Tech', name: 'Virginia Tech', code: "VT", color: '#630031', color2: '#CF4420' },
  { id: 'Wake Forest', name: 'Wake Forest', code: "WAKE", color: '#9E7E38', color2: '#000000' },
  // Brand revamp: 2 real schools that appear in CFB 12-0's own legends
  // data (data/cfb-legends.js) but were missing here -- found by
  // actually diffing the 2 lists, not assumed complete. Real official
  // school colors.
  { id: 'Pitt', name: 'Pitt', code: "PITT", color: '#003594', color2: '#FFB81C' },
  { id: 'Boise State', name: 'Boise State', code: "BSU", color: '#0033A0', color2: '#D64309' }
];
// Most teams are genuinely one-color for this app's purposes (a swatch dot
// doesn't need a school's full palette), but a few — Auburn's navy+orange
// chief among them — read as flatly wrong with just one. color2 is opt-in
// per team; a diagonal split reads clearly as "two-tone" even at swatch
// size, unlike a gradient blend which would just look muddy.
function teamSwatchStyle(t) {
  if (t.color2) return 'background: linear-gradient(135deg, ' + t.color + ' 50%, ' + t.color2 + ' 50%)';
  return 'background: ' + t.color;
}
// Brand revamp (user request: "team logos" in 17-0/CFB 12-0 -- by which
// they mean a real abbreviation + real team colors, this app has zero
// external logo image assets by design): looks a real team-season name
// up in NFL_TEAMS/CFB_TEAMS by exact name (confirmed live against both
// legends data files -- every real name in data/legends.js and
// data/cfb-legends.js has a real match) and renders a small colored
// badge with the real code/abbreviation, using the same real swatch-
// gradient + blended-text-color logic the team picker already
// established. Returns '' (never a fabricated placeholder) if a name
// somehow doesn't match.
function teamCodeBadgeHtml(league, teamName) {
  var list = league === 'cfb' ? CFB_TEAMS : NFL_TEAMS;
  var t = list.find(function (x) { return x.name === teamName; });
  if (!t) return '';
  var code = t.code || t.id;
  return '<span class="team-code-badge" style="' + teamSwatchStyle(t) + '; color: ' + blendedTeamTextColor(t) + '">' + esc(code) + '</span>';
}
function favoriteTeamsKey() { return 'nflTriviaFavoriteTeams'; }
function getFavoriteTeams() {
  var v = lsGet(favoriteTeamsKey(), { nfl: null, cfb: null, lastPicked: null, updatedAt: 0 });
  if (v.updatedAt == null) v.updatedAt = 0;
  return v;
}
function setFavoriteTeams(v) {
  v = Object.assign({}, v, { updatedAt: Date.now() });
  lsSet(favoriteTeamsKey(), v);
  pushProfileSnapshot();
  syncAchievementUnlocks();
}
function favoriteTeamById(league, id) {
  var list = league === 'nfl' ? NFL_TEAMS : CFB_TEAMS;
  return list.find(function (t) { return t.id === id; }) || null;
}
// Two-step (NFL, then CFB) searchable picker, same accessible-dialog pattern
// as the rating/share/report modals — but its own body is re-rendered
// directly (renderTeamPickerBody) rather than through the main renderAll(),
// same reason the onboarding modal works this way: it's outside #app, and a
// full renderAll() would be pointless work just to update a few dozen list
// rows. Search re-renders on every keystroke, so — same as Learn's filter
// input and the main renderAll()'s name/game-input refocus block — the
// search box has to explicitly refocus + restore cursor position itself
// after every re-render, or the innerHTML replace would steal focus after
// the very first character typed.
var teamPickerTriggerEl = null;
function openTeamPicker() {
  state.teamPicker = { screen: 'nfl', filter: '' };
  teamPickerTriggerEl = document.activeElement;
  renderTeamPickerBody();
  var modal = document.getElementById('team-picker-modal');
  var backdrop = document.getElementById('team-picker-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
}
function closeTeamPicker() {
  var modal = document.getElementById('team-picker-modal');
  var backdrop = document.getElementById('team-picker-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  restoreFocus(teamPickerTriggerEl);
  teamPickerTriggerEl = null;
  state.teamPicker = null;
  renderAll(); // picking a team can change the header accent/home greeting
}
function renderTeamPickerBody() {
  var s = state.teamPicker;
  if (!s) return;
  var league = s.screen;
  var list = league === 'nfl' ? NFL_TEAMS : CFB_TEAMS;
  var current = getFavoriteTeams();
  var filter = s.filter.toLowerCase();
  var filtered = list.filter(function (t) { return !filter || t.name.toLowerCase().indexOf(filter) !== -1; });
  var body = document.getElementById('team-picker-body');
  if (!body) return;
  body.innerHTML =
    '<div class="team-picker-tabs" role="tablist">' +
    '<button class="team-picker-tab' + (league === 'nfl' ? ' active' : '') + '" role="tab" aria-selected="' + (league === 'nfl') + '" data-team-tab="nfl">NFL</button>' +
    '<button class="team-picker-tab' + (league === 'cfb' ? ' active' : '') + '" role="tab" aria-selected="' + (league === 'cfb') + '" data-team-tab="cfb">College Football</button>' +
    '</div>' +
    '<p class="mode-desc">Optional — used for a few personal touches around the app (and a light nudge in the random mix, never a hard filter). Change or clear it here anytime.</p>' +
    '<input id="team-picker-search" class="learn-filter-input" placeholder="Search teams…" value="' + esc(s.filter) + '" autocomplete="off" />' +
    '<div class="team-picker-list">' +
    (filtered.length ? filtered.map(function (t) {
      var active = current[league] === t.id;
      return '<button class="team-picker-row' + (active ? ' active' : '') + '" data-team-pick="' + league + ':' + esc(t.id) + '">' +
        '<span class="team-picker-swatch" style="' + teamSwatchStyle(t) + '"></span>' +
        '<span class="team-picker-row-text"><span>' + esc(t.name) + '</span>' + (t.chant ? '<span class="team-picker-chant">' + esc(t.chant) + '</span>' : '') + '</span>' +
        (active ? icon('check') : '') +
        '</button>';
    }).join('') : '<p class="mode-desc">No teams match “' + esc(s.filter) + '”.</p>') +
    '</div>' +
    '<div class="btn-row team-picker-actions">' +
    (current[league] ? '<button class="btn-secondary" data-team-clear="' + league + '">Clear</button>' : '') +
    '<button class="btn-primary" data-team-done>Done</button>' +
    '</div>';
  var input = document.getElementById('team-picker-search');
  if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
}
function teamPickerPick(league, id) {
  var current = getFavoriteTeams();
  current[league] = current[league] === id ? null : id; // clicking the already-active team unsets it
  // Whichever team you just touched becomes the "primary" one (see
  // primaryFavoriteTeam below) — otherwise picking a College team while an
  // NFL team was already set would silently keep showing the NFL color
  // everywhere, which reads as "picking a team didn't do anything."
  current.lastPicked = current[league] ? league : null;
  setFavoriteTeams(current);
  renderTeamPickerBody();
}
function teamPickerClear(league) {
  var current = getFavoriteTeams();
  current[league] = null;
  if (current.lastPicked === league) current.lastPicked = null;
  setFavoriteTeams(current);
  renderTeamPickerBody();
}
function teamPickerSetFilter(v) {
  if (!state.teamPicker) return;
  state.teamPicker.filter = v;
  renderTeamPickerBody();
}
function teamPickerSetTab(league) {
  if (!state.teamPicker || state.teamPicker.screen === league) return;
  state.teamPicker.screen = league;
  state.teamPicker.filter = '';
  renderTeamPickerBody();
}
// The one favorite team used for the header accent bar / share-card tint
// when both leagues are set — whichever one was picked/changed most
// recently (lastPicked, set in teamPickerPick above), so switching your
// College team actually shows up even if an NFL team was already set. Falls
// back to NFL-then-CFB only for an older stored value from before
// lastPicked existed, or if lastPicked's own team got cleared elsewhere.
function primaryFavoriteTeam() {
  var fav = getFavoriteTeams();
  if (fav.lastPicked && fav[fav.lastPicked]) return favoriteTeamById(fav.lastPicked, fav[fav.lastPicked]);
  if (fav.nfl) return favoriteTeamById('nfl', fav.nfl);
  if (fav.cfb) return favoriteTeamById('cfb', fav.cfb);
  return null;
}
// Sets both a plain hex custom property (for solid-color uses like the
// header bar / greeting text) and an "r,g,b" triplet (so CSS can build its
// own rgba() washes at whatever opacity a given spot needs — a background
// glow needs to be much more transparent than a border ever would) — same
// hex-parsing approach as hexToRgbaString/shadeHexColor in the share-card
// section, just exposed as CSS variables instead of used directly in canvas
// calls. body.has-fav-team drives the always-on bits (header bar, greeting);
// body.home-fav-theme additionally drives the fuller Home-screen wash
// (background glow, quick-action card accents) and is scoped to state.screen
// === 'home' specifically — everywhere else in the app stays exactly as
// themed by league (orange/teal), not by favorite team.
function hexToRgbTriplet(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  return ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255);
}
// A fixed dark --accent-text (tuned for the app's own light-gold --accent)
// reads fine on gold but goes near-invisible on a dark team color like
// Auburn's navy — pickBadgeTextColor (already used for CFB Grid's team
// badges) picks white-or-dark per actual contrast instead. Blending color +
// color2 to their midpoint first, rather than testing color alone, is what
// keeps a two-tone badge/circle (icon sits roughly at the gradient's center)
// from picking a text color that only works against one end of it.
function blendedTeamTextColor(team) {
  var c1 = team.color.replace('#', ''), c2 = (team.color2 || team.color).replace('#', '');
  var mix = [0, 2, 4].map(function (i) {
    return Math.round((parseInt(c1.substr(i, 2), 16) + parseInt(c2.substr(i, 2), 16)) / 2)
      .toString(16).padStart(2, '0');
  }).join('');
  return pickBadgeTextColor(mix);
}
function relativeLuminance(r, g, b) {
  var lin = function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}
// A team color also gets used directly AS a foreground (rating XP-bar fill,
// recommended-mode icons, the greeting text) against this app's near-black
// background — fine for a bright team color like Steelers gold, but a dark
// primary (Auburn navy, Ravens purple, half the league's navy/black
// helmets) goes nearly invisible there the same way the badge text did.
// Unlike blendedTeamTextColor (which picks BETWEEN white/dark for a color
// used as a background), this keeps the team's actual hue and just lightens
// it — mixing toward white a step at a time — until it clears a readable
// contrast ratio against the app background, so it still looks like "that
// team's color," just legible.
function readableOnDark(hex) {
  var r = parseInt(hex.substr(1, 2), 16), g = parseInt(hex.substr(3, 2), 16), b = parseInt(hex.substr(5, 2), 16);
  var bgL = 0.006; // ~relative luminance of this app's --bg (#0c110d)
  var contrast = function (L) { return (Math.max(L, bgL) + 0.05) / (Math.min(L, bgL) + 0.05); };
  var tries = 0;
  while (contrast(relativeLuminance(r, g, b)) < 3.2 && tries < 12) {
    r += (255 - r) * 0.16; g += (255 - g) * 0.16; b += (255 - b) * 0.16;
    tries++;
  }
  return '#' + [r, g, b].map(function (v) { return Math.round(v).toString(16).padStart(2, '0'); }).join('');
}
function applyFavoriteTeamAccent() {
  var team = primaryFavoriteTeam();
  var root = document.documentElement.style;
  root.setProperty('--fav-team-color', team ? team.color : '');
  // Falls back to the primary color when a team has no color2, so every
  // rule that blends both (the header bar, home-screen glow/border gradients
  // below) degrades to looking identical to a solid single color instead of
  // needing a separate "has two colors" branch in the CSS.
  root.setProperty('--fav-team-color-2', team ? (team.color2 || team.color) : '');
  root.setProperty('--fav-team-text', team ? blendedTeamTextColor(team) : '');
  root.setProperty('--fav-team-color-readable', team ? readableOnDark(team.color) : '');
  root.setProperty('--fav-team-color-2-readable', team ? readableOnDark(team.color2 || team.color) : '');
  if (team) {
    root.setProperty('--fav-team-color-rgb', hexToRgbTriplet(team.color));
    root.setProperty('--fav-team-color-2-rgb', hexToRgbTriplet(team.color2 || team.color));
  } else {
    root.setProperty('--fav-team-color-rgb', '');
    root.setProperty('--fav-team-color-2-rgb', '');
  }
  document.body.classList.toggle('has-fav-team', !!team);
  document.body.classList.toggle('home-fav-theme', !!team && state.screen === 'home');
}
// A few interchangeable templates rather than one fixed line, picked
// deterministically per day+name (same mulberry32/hashStr pattern as the
// Daily Reads and recommendedModeHtml) so it's stable through a session
// but not the exact same sentence every single day.
var FAVORITE_TEAM_GREETINGS = ['What’s up, {team} fan?', 'Ready to roll, {team} fan?', 'Let’s go, {team}!', 'Hey there, {team} faithful.'];
// NFL_TEAMS' own id IS a real abbreviation already ('KC', 'SF', ...) so it
// doubles as team.code there; CFB_TEAMS carries an explicit code field since
// its id is the full school name instead.
function favoriteTeamBadgeHtml() {
  var team = primaryFavoriteTeam();
  if (!team) return '';
  return '<span class="fav-team-badge" style="' + teamSwatchStyle(team) + '">' + esc(team.code || team.id) + '</span>';
}
function favoriteTeamGreeting() {
  var team = primaryFavoriteTeam();
  if (!team || !state.name) return '';
  var rng = mulberry32(hashStr(todayStr() + '_greeting_' + state.name));
  var template = FAVORITE_TEAM_GREETINGS[Math.floor(rng() * FAVORITE_TEAM_GREETINGS.length)];
  var line = template.replace('{team}', team.name) + (team.chant ? ' ' + team.chant : '');
  return '<p class="fav-team-greeting">' + favoriteTeamBadgeHtml() + esc(line) + '</p>';
}
var TEAM_PROMPT_DISMISS_KEY = 'nflTriviaTeamPromptDismissed';
function teamPickerPromptCardHtml() {
  var fav = getFavoriteTeams();
  if (fav.nfl || fav.cfb) return '';
  if (!state.name || lsGet(TEAM_PROMPT_DISMISS_KEY, false)) return '';
  return '<div class="panel daily-card">' +
    '<div class="daily-card-title">' + icon('flag') + ' Got a team?</div>' +
    '<p class="mode-desc">Pick a favorite NFL and/or College team for a few personal touches around the app — totally optional, change it anytime from the header.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-team-picker-toggle>Pick My Teams</button>' +
    '<button class="btn-secondary" data-team-prompt-dismiss>Not Now</button>' +
    '</div></div>';
}
function dismissTeamPrompt() { lsSet(TEAM_PROMPT_DISMISS_KEY, true); renderAll(); }

/* ============================== favorite-team communities ============================== */
var communityRows = [];
var communityDraft = '';
var communityLoading = false;
var communityError = '';
var communityUnsubscribe = null;
var communityActiveLeague = null;
var COMMUNITY_POST_LIMIT = 180;
function communityTeamForLeague(league) {
  var fav = getFavoriteTeams();
  return league && fav[league] ? favoriteTeamById(league, fav[league]) : null;
}
function defaultCommunityLeague() {
  var fav = getFavoriteTeams();
  if (fav.lastPicked && fav[fav.lastPicked]) return fav.lastPicked;
  if (fav.nfl) return 'nfl';
  if (fav.cfb) return 'cfb';
  return null;
}
function communityTeamKey(league, team) {
  if (!league || !team) return '';
  return league + '__' + slugify(team.id || team.name);
}
function communityCreatedAtMs(row) {
  if (!row || !row.createdAt) return 0;
  if (typeof row.createdAt.toMillis === 'function') return row.createdAt.toMillis();
  if (typeof row.createdAt.seconds === 'number') return row.createdAt.seconds * 1000;
  return Number(row.createdAt) || 0;
}
function communityRelativeTime(row) {
  var ms = communityCreatedAtMs(row);
  if (!ms) return 'just now';
  var diff = Math.max(0, Date.now() - ms);
  var mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm';
  var hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + 'h';
  var days = Math.floor(hrs / 24);
  return days + 'd';
}
function stopCommunityWatch() {
  if (communityUnsubscribe) { communityUnsubscribe(); communityUnsubscribe = null; }
}
function startCommunityWatch(league) {
  var team = communityTeamForLeague(league);
  stopCommunityWatch();
  communityActiveLeague = league;
  communityRows = [];
  communityLoading = true;
  communityError = '';
  if (!team || !window.__fbSync || !window.__fbSync.watchCommunity) {
    communityLoading = false;
    renderAll();
    return;
  }
  communityUnsubscribe = window.__fbSync.watchCommunity(communityTeamKey(league, team), function (rows) {
    communityRows = Array.isArray(rows) ? rows : [];
    communityLoading = false;
    if (state.screen === 'community') renderAll();
  });
}
function communityCardHtml() {
  if (!state.name) return '';
  var league = defaultCommunityLeague();
  var team = communityTeamForLeague(league);
  if (!team) return '';
  return '<button class="community-home-card" data-go="community">' +
    '<span class="community-home-icon">' + favoriteTeamBadgeHtml() + '</span>' +
    '<span class="community-home-copy"><span class="community-home-kicker">YOUR TEAM COMMUNITY</span>' +
    '<strong>' + esc(team.name) + ' Fans</strong><small>Talk ball with people repping your team.</small></span>' +
    icon('arrowRight', 'continue-card-chevron') +
    '</button>';
}
function renderCommunityPost(row) {
  var badge = row.badgeTitle ? ((row.badgeIcon || '🏈') + ' ' + esc(row.badgeTitle)) : '';
  var isActivity = row.type === 'activity';
  return '<article class="community-post' + (isActivity ? ' community-activity' : '') + '">' +
    (isActivity ? '<div class="community-activity-kicker">' + (row.activityKind === 'challenge' ? 'TEAM CHALLENGE' : 'GAME RESULT') + '</div>' : '') +
    '<div class="community-post-head"><div><b>' + esc(row.authorName || 'Reads fan') + '</b>' +
    (badge ? '<span class="community-post-badge">' + badge + '</span>' : '') +
    '</div><time>' + esc(communityRelativeTime(row)) + '</time></div>' +
    '<p>' + esc(row.text || '') + '</p>' +
    '<div class="community-post-meta">' +
      (row.careerRank ? '<span>' + esc(row.careerRank) + '</span>' : '') +
      (row.rating ? '<span>' + row.rating + ' rating</span>' : '') +
      (row.streak ? '<span>' + row.streak + '-day streak</span>' : '') +
    '</div>' +
    '</article>';
}
function communityChallengeStorageKey(teamKey, date) {
  return 'readsCommunityChallenge__' + teamKey + '__' + (date || todayStr());
}
function communityChallengeFor(league, team) {
  if (!league || !team) return null;
  var rng = mulberry32(hashStr(todayStr() + '__community__' + communityTeamKey(league, team)));
  var targets = [70, 80, 90];
  var target = targets[Math.floor(rng() * targets.length)];
  return {
    id: todayStr() + '__' + communityTeamKey(league, team),
    mode: league === 'cfb' ? 'cfbQuiz' : 'quiz',
    target: target,
    title: team.name + ' Daily Challenge',
    desc: 'Score ' + target + '% or better in ' + (league === 'cfb' ? 'College Football Quiz' : 'NFL Quiz') + ' today.',
    xp: 75
  };
}
function currentCompletionPercent(mode) {
  var t = mode === 'quiz' ? state.quiz : mode === 'cfbQuiz' ? state.cfbQuiz : null;
  if (!t || !t.queue || !t.queue.length) return null;
  return Math.round(100 * (Number(t.correctCount) || 0) / t.queue.length);
}
function communityChallengeStatus(league, team) {
  var teamKey = communityTeamKey(league, team);
  var key = communityChallengeStorageKey(teamKey, todayStr());
  var local = lsGet(key, { completed: false, pct: null, completedAt: null });
  if (local.completed) return local;
  if (activeAuthUid) {
    var remote = communityRows.find(function (row) {
      return row.id === ('challenge_' + todayStr() + '_' + activeAuthUid) &&
        row.authorUid === activeAuthUid &&
        row.teamId === team.id;
    });
    if (remote) return { completed: true, pct: remote.scoreValue == null ? null : remote.scoreValue, completedAt: communityCreatedAtMs(remote) };
  }
  return local;
}
function markCommunityChallengeComplete(league, team, challenge, pct) {
  var teamKey = communityTeamKey(league, team);
  var storageKey = communityChallengeStorageKey(teamKey, todayStr());
  var current = lsGet(storageKey, { completed: false });
  if (current.completed) return;
  lsSet(storageKey, { completed: true, pct: pct, completedAt: Date.now() });
  if (activeAuthUid && window.__fbSync && window.__fbSync.awardProgress) {
    var eventId = 'community_challenge_' + challenge.id;
    var seasonId = footballSeasonIdForDate();
    window.__fbSync.awardProgress(profileDocId(), eventId, {
      type: 'COMMUNITY_CHALLENGE_COMPLETED',
      source: 'community',
      teamKey: teamKey,
      mode: challenge.mode,
      scorePct: pct
    }, challenge.xp, seasonId).then(function (result) {
      if (!result || !result.duplicate) {
        applyProgressAwardLocally(challenge.xp, seasonId);
        syncAchievementUnlocks();
      }
    }).catch(function () {});
  }
  if (activeAuthUid && window.__fbSync && window.__fbSync.postCommunityActivity) {
    var badge = selectedBadge();
    var career = progressionRankFor(getProgression().careerXp || 0);
    window.__fbSync.postCommunityActivity(teamKey, 'challenge_' + todayStr() + '_' + activeAuthUid, {
      activityKind: 'challenge',
      teamId: team.id,
      teamName: team.name,
      league: league,
      badgeTitle: badge ? badge.title : null,
      badgeIcon: badge ? badge.icon : null,
      careerRank: career.name,
      text: 'Completed today’s team challenge with ' + pct + '%.',
      scoreValue: pct,
      scoreLabel: 'Quiz score'
    }).catch(function () {});
  }
}
function checkCommunityChallengeFromCompletion(mode) {
  if (!activeAuthUid) return;
  var fav = getFavoriteTeams();
  ['nfl','cfb'].forEach(function (league) {
    var team = fav[league] ? favoriteTeamById(league, fav[league]) : null;
    if (!team) return;
    var challenge = communityChallengeFor(league, team);
    if (!challenge || challenge.mode !== mode) return;
    var pct = currentCompletionPercent(mode);
    if (pct != null && pct >= challenge.target) markCommunityChallengeComplete(league, team, challenge, pct);
  });
}
function communityActivitySummary(mode, fields) {
  var label = modeLabelFor(mode);
  var text = 'Finished ' + label + '.';
  var scoreValue = null, scoreLabel = '';
  if (mode === 'quiz' || mode === 'cfbQuiz') {
    var pct = currentCompletionPercent(mode);
    if (pct != null) { text = 'Dropped ' + pct + '% in ' + label + '.'; scoreValue = pct; scoreLabel = 'Score'; }
  } else if (mode === 'daily' && state.daily && state.daily.queue && state.daily.queue.length) {
    var dpct = Math.round(100 * state.daily.correctCount / state.daily.queue.length);
    text = 'Finished Daily Reads at ' + dpct + '%.';
    scoreValue = dpct; scoreLabel = 'Daily Reads';
  } else if (fields && typeof fields.bestScore === 'number') {
    text = 'Finished ' + label + ' with a score of ' + fields.bestScore + '.';
    scoreValue = fields.bestScore; scoreLabel = 'Score';
  } else if (fields && typeof fields.bestPct === 'number') {
    text = 'Finished ' + label + ' at ' + fields.bestPct + '%.';
    scoreValue = fields.bestPct; scoreLabel = 'Best';
  }
  return { text: text, scoreValue: scoreValue, scoreLabel: scoreLabel };
}
function postCommunityGameActivity(mode, fields) {
  if (!activeAuthUid || !window.__fbSync || !window.__fbSync.postCommunityActivity) return;
  var fav = getFavoriteTeams();
  var summary = communityActivitySummary(mode, fields);
  var badge = selectedBadge();
  var career = progressionRankFor(getProgression().careerXp || 0);
  var rating = getRating();
  var streak = getStreak();
  var activityIdBase = (mode === 'daily' ? ('daily_' + todayStr()) : progressEventIdFor(mode));
  ['nfl','cfb'].forEach(function (league) {
    var team = fav[league] ? favoriteTeamById(league, fav[league]) : null;
    if (!team) return;
    var relevant = mode === 'daily' || mode === 'h2h' ||
      (league === 'cfb' ? mode.indexOf('cfb') === 0 : mode.indexOf('cfb') !== 0);
    if (!relevant) return;
    window.__fbSync.postCommunityActivity(communityTeamKey(league, team), 'game_' + slugify(activityIdBase) + '_' + activeAuthUid, {
      activityKind: 'game',
      teamId: team.id,
      teamName: team.name,
      league: league,
      mode: mode,
      badgeTitle: badge ? badge.title : null,
      badgeIcon: badge ? badge.icon : null,
      careerRank: career.name,
      rating: rating ? rating.score : null,
      streak: streak.count || 0,
      text: summary.text,
      scoreValue: summary.scoreValue,
      scoreLabel: summary.scoreLabel
    }).catch(function () {});
  });
}
function communityLeaderboardRows(league, team) {
  var teamId = team && team.id;
  if (!teamId) return [];
  var field = league === 'cfb' ? 'favoriteCfbTeam' : 'favoriteNflTeam';
  var rows = state.leaderboardData.filter(function (r) {
    return r.mode === 'rating' && r[field] === teamId && typeof r.score === 'number';
  });
  rows.sort(function (a,b) {
    if ((b.score || 0) !== (a.score || 0)) return (b.score || 0) - (a.score || 0);
    return leaderboardRowTimestamp(b) - leaderboardRowTimestamp(a);
  });
  return rows.slice(0, 10);
}

function communitySeasonRowsForTeam(league, team) {
  if (!team) return [];
  var seasonId=footballSeasonIdForDate(), field=league==='cfb'?'favoriteCfbTeam':'favoriteNflTeam';
  return (state.leaderboardData||[]).filter(function(r){
    return r.mode==='season'&&String(r.seasonId||'')===seasonId&&r[field]===team.id&&typeof r.seasonXp==='number';
  });
}
function communityTeamSeasonXp(league, team) {
  return communitySeasonRowsForTeam(league,team).reduce(function(sum,r){return sum+(Number(r.seasonXp)||0);},0);
}
function communityTeamSeasonRank(league, team) {
  if(!team)return null;
  var field=league==='cfb'?'favoriteCfbTeam':'favoriteNflTeam', seasonId=footballSeasonIdForDate(), totals={};
  (state.leaderboardData||[]).forEach(function(r){
    if(r.mode!=='season'||String(r.seasonId||'')!==seasonId||!r[field]||typeof r.seasonXp!=='number')return;
    totals[r[field]]=(totals[r[field]]||0)+(Number(r.seasonXp)||0);
  });
  var ids=Object.keys(totals).sort(function(x,y){return totals[y]-totals[x];});
  var idx=ids.indexOf(team.id);
  return idx===-1?null:{rank:idx+1,total:ids.length,xp:totals[team.id]||0};
}
function communityCurrentWeekKey() {
  return dailyRivalWeekKey(todayStr());
}
function communityWeeklyTeamPoints(league, team) {
  if(!team)return 0;
  var field=league==='cfb'?'favoriteCfbTeam':'favoriteNflTeam', wk=communityCurrentWeekKey();
  return (state.leaderboardData||[]).filter(function(r){
    return r.mode==='daily'&&r[field]===team.id&&r.weekKey===wk;
  }).reduce(function(sum,r){return sum+(Number(r.weeklyRivalPoints)||0);},0);
}
function communityKnownRival(league, team) {
  if(!team)return null;
  var nfl={DAL:'PHI',PHI:'DAL',GB:'CHI',CHI:'GB',PIT:'BAL',BAL:'PIT',KC:'LV',LV:'KC',SF:'SEA',SEA:'SF',NYJ:'BUF',BUF:'NYJ',NO:'ATL',ATL:'NO',CLE:'CIN',CIN:'CLE',DEN:'KC',MIN:'GB'};
  var cfb={
    'Alabama':'Auburn','Auburn':'Alabama','Ohio State':'Michigan','Michigan':'Ohio State',
    'Oklahoma':'Texas','Texas':'Oklahoma','Notre Dame':'Southern California','Southern California':'Notre Dame',
    'Florida':'Florida State','Florida State':'Florida','Georgia':'Florida','Clemson':'South Carolina',
    'South Carolina':'Clemson','Ole Miss':'Mississippi State','Mississippi State':'Ole Miss',
    'Iowa':'Iowa State','Iowa State':'Iowa','Oregon':'Oregon State','Oregon State':'Oregon',
    'Washington':'Washington State','Washington State':'Washington'
  };
  var id=league==='cfb'?cfb[team.id]:nfl[team.id];
  return id?favoriteTeamById(league,id):null;
}
function communityFallbackBattleTeam(league, team) {
  var list=league==='cfb'?CFB_TEAMS:NFL_TEAMS;
  if(!team||!list.length)return null;
  var idx=list.findIndex(function(t){return t.id===team.id;});
  return list[(Math.max(0,idx)+1)%list.length]||null;
}
function communityBattleTeam(league, team) {
  return communityKnownRival(league,team)||communityFallbackBattleTeam(league,team);
}
function communityContributionPct(league, team) {
  var rows=communitySeasonRowsForTeam(league,team), mine=getProgression().seasons&&getProgression().seasons[footballSeasonIdForDate()];
  var xp=mine?Number(mine.xp)||0:0;
  if(!rows.length||!xp)return {xp:xp,pct:null};
  var below=rows.filter(function(r){return (Number(r.seasonXp)||0)<=xp;}).length;
  return {xp:xp,pct:Math.max(1,Math.round(100*below/rows.length))};
}
function communityTeamPulseHtml(league, team) {
  var rank=communityTeamSeasonRank(league,team), fans=communitySeasonRowsForTeam(league,team).length, contribution=communityContributionPct(league,team);
  return '<section class="community-team-pulse">'+
    '<div class="community-feed-head"><h3>'+esc(team.name)+' Pulse</h3><span>'+esc(footballSeasonIdForDate())+' season</span></div>'+
    '<div class="community-pulse-grid">'+
      '<div><b>'+Number(rank?rank.xp:0).toLocaleString()+'</b><span>Team XP</span></div>'+
      '<div><b>'+(rank?'#'+rank.rank:'—')+'</b><span>Reads Team Rank</span></div>'+
      '<div><b>'+fans+'</b><span>Ranked Fans</span></div>'+
      '<div><b>'+Number(contribution.xp||0).toLocaleString()+'</b><span>Your XP</span></div>'+
    '</div>'+
    (contribution.pct?'<div class="community-contribution"><span>YOUR CONTRIBUTION</span><b>Top '+Math.max(1,100-contribution.pct+1)+'% of '+esc(team.name)+' fans</b><div><i style="width:'+contribution.pct+'%"></i></div></div>':'')+
    '</section>';
}
function communityBattleHtml(league, team) {
  var opponent=communityBattleTeam(league,team);
  if(!opponent)return '';
  var us=communityWeeklyTeamPoints(league,team), them=communityWeeklyTeamPoints(league,opponent), total=Math.max(1,us+them);
  var usPct=Math.round(100*us/total), known=!!communityKnownRival(league,team);
  var lead=us===them?'Tied up':us>them?team.name+' leads':opponent.name+' leads';
  return '<section class="community-battle-card">'+
    '<div class="community-battle-head"><div><span class="dashboard-eyebrow">'+(known?'RIVALRY BATTLE':'WEEKLY TEAM BATTLE')+'</span><h3>'+esc(team.name)+' vs. '+esc(opponent.name)+'</h3></div><b>'+esc(lead)+'</b></div>'+
    '<div class="community-battle-score"><div><span>'+esc(team.code||team.id)+'</span><b>'+us.toLocaleString()+'</b><small>Rival Points</small></div>'+
    '<div class="community-battle-vs">VS</div><div><span>'+esc(opponent.code||opponent.id)+'</span><b>'+them.toLocaleString()+'</b><small>Rival Points</small></div></div>'+
    '<div class="community-battle-meter"><i style="width:'+usPct+'%"></i></div>'+
    '<div class="community-battle-foot"><span>Every Daily Reads run adds to your team’s weekly total.</span><button class="btn-primary" data-go="daily">'+(us<them?'Help '+esc(team.code||team.id)+' take the lead':'Run up the score')+'</button></div>'+
    '</section>';
}

function communityDailyRivalsHtml(league, team) {
  if (!team) return '';
  var field = league === 'cfb' ? 'favoriteCfbTeam' : 'favoriteNflTeam';
  var rows = dailyRivalRows('today').filter(function (r) { return r[field] === team.id; });
  return '<section class="community-leaderboard community-daily-rivals">' +
    '<div class="community-feed-head"><h3>Daily Rivals</h3><span>Today · Rival Points</span></div>' +
    (rows.length ? '<div class="community-rank-list">' + rows.slice(0,10).map(function (r,i) {
      return '<div class="community-rank-row"><span class="community-rank-pos">' + (i+1) + '</span>' +
        '<b>' + esc(r.name || 'Reads fan') + '</b><span>' + (Number(r.todayRivalPoints) || 0) + ' pts</span></div>';
    }).join('') + '</div>' :
    '<div class="community-empty"><b>No Daily scores yet.</b><span>Finish today’s Daily Reads to put your team on the board.</span></div>') +
    '</section>';
}
function communityLeaderboardHtml(league, team) {
  var rows = communityLeaderboardRows(league, team);
  return '<section class="community-leaderboard">' +
    '<div class="community-feed-head"><h3>Team Leaderboard</h3><span>Football Rating</span></div>' +
    (rows.length ? '<div class="community-rank-list">' + rows.map(function (r, i) {
      return '<div class="community-rank-row"><span class="community-rank-pos">' + (i + 1) + '</span>' +
        '<b>' + esc(r.name || 'Reads fan') + '</b><span>' + r.score + '</span></div>';
    }).join('') + '</div>' :
    '<div class="community-empty"><b>No ranked fans yet.</b><span>Play a ranked game to join your team leaderboard.</span></div>') +
    '</section>';
}
function communityChallengeHtml(league, team) {
  var challenge = communityChallengeFor(league, team);
  if (!challenge) return '';
  var status = communityChallengeStatus(league, team);
  return '<section class="community-challenge-card' + (status.completed ? ' completed' : '') + '">' +
    '<div><span class="dashboard-eyebrow">TODAY’S TEAM CHALLENGE</span><h3>' + esc(challenge.title) + '</h3>' +
    '<p>' + esc(challenge.desc) + '</p></div>' +
    '<div class="community-challenge-actions">' +
      '<span class="community-challenge-xp">+' + challenge.xp + ' XP</span>' +
      (status.completed
        ? '<span class="community-challenge-done">' + icon('check') + ' Completed' + (status.pct != null ? ' · ' + status.pct + '%' : '') + '</span>'
        : '<button class="btn-primary" data-go="' + challenge.mode + '">Play Challenge</button>') +
    '</div>' +
    '</section>';
}

function renderCommunityScreen() {
  var fav = getFavoriteTeams();
  var hasNfl = !!fav.nfl, hasCfb = !!fav.cfb;
  if (!hasNfl && !hasCfb) {
    return '<div class="panel"><div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('users') + ' Team Communities</h2>' +
      '<p class="mode-desc">Pick a favorite NFL or College team first. That team becomes your community.</p>' +
      '<button class="btn-primary" data-team-picker-toggle>Pick My Teams</button></div>';
  }
  var league = communityActiveLeague && fav[communityActiveLeague] ? communityActiveLeague : defaultCommunityLeague();
  var team = communityTeamForLeague(league);
  if (!communityUnsubscribe && window.__fbSync && window.__fbSync.watchCommunity) {
    setTimeout(function () { if (state.screen === 'community') startCommunityWatch(league); }, 0);
  }
  var selected = selectedBadge();
  var career = progressionRankFor(getProgression().careerXp || 0);
  var rating = getRating();
  var streak = getStreak();
  var tabs = (hasNfl && hasCfb) ? '<div class="community-tabs">' +
    '<button class="' + (league === 'nfl' ? 'active' : '') + '" data-community-league="nfl">NFL</button>' +
    '<button class="' + (league === 'cfb' ? 'active' : '') + '" data-community-league="cfb">College</button>' +
    '</div>' : '';
  var composer = activeAuthUid
    ? '<div class="community-composer"><textarea id="community-post-input" maxlength="' + COMMUNITY_POST_LIMIT + '" rows="3" placeholder="What’s on your mind, ' + esc(team.name) + ' fans?">' + esc(communityDraft) + '</textarea>' +
      '<div class="community-composer-foot"><span>' + COMMUNITY_POST_LIMIT + ' max</span><button class="btn-primary" data-community-post>Post</button></div>' +
      '<div class="community-quick-posts"><button data-community-preset="Daily Reads done. Who’s beating my score?">Daily Reads done</button>' +
      '<button data-community-preset="Who actually knows ball in here?">Who knows ball?</button>' +
      '<button data-community-preset="Challenge me in Head-to-Head.">Challenge me</button></div></div>'
    : '<div class="community-login-note"><b>Want to post?</b><span>Log in to join the conversation. You can still read the room.</span><button class="btn-secondary" data-auth-open="login">Log In</button></div>';
  return '<div class="panel community-screen">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    tabs +
    '<div class="community-hero" style="' + teamSwatchStyle(team) + '">' +
      '<div class="community-hero-badge">' + esc(team.code || team.id) + '</div>' +
      '<div><span class="dashboard-eyebrow">TEAM COMMUNITY</span><h2>' + esc(team.name) + ' Fans</h2><p>Game reactions, trash talk, trivia flexes, and challenges.</p></div>' +
    '</div>' +
    '<div class="community-you"><span>You’re posting as</span><b>' + esc(state.name || 'Guest') + '</b>' +
      (selected ? '<span>' + selected.icon + ' ' + esc(selected.title) + '</span>' : '') +
      '<span>' + esc(career.name) + '</span>' +
      (rating ? '<span>' + rating.score + ' rating</span>' : '') +
      (streak.count ? '<span>' + streak.count + '-day streak</span>' : '') +
    '</div>' +
    communityTeamPulseHtml(league, team) +
    communityBattleHtml(league, team) +
    communityChallengeHtml(league, team) +
    communityDailyRivalsHtml(league, team) +
    communityLeaderboardHtml(league, team) +
    composer +
    (communityError ? '<div class="community-error">' + esc(communityError) + '</div>' : '') +
    '<div class="community-feed-head"><h3>Latest</h3><span>' + communityRows.length + ' post' + (communityRows.length === 1 ? '' : 's') + '</span></div>' +
    (communityLoading ? '<div class="loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading the room…</div></div>' :
      communityRows.length ? '<div class="community-feed">' + communityRows.map(renderCommunityPost).join('') + '</div>' :
      '<div class="community-empty"><b>Be the first one in.</b><span>No posts yet for this team.</span></div>') +
    '</div>';
}
function switchCommunityLeague(league) {
  if (!communityTeamForLeague(league)) return;
  startCommunityWatch(league);
  renderAll();
}
function setCommunityPreset(text) {
  var input = document.getElementById('community-post-input');
  if (!input) return;
  communityDraft = text || '';
  input.value = communityDraft;
  input.focus();
}
function submitCommunityPost() {
  if (!activeAuthUid || !state.name) { openAuthModal('login'); return; }
  var league = communityActiveLeague && communityTeamForLeague(communityActiveLeague) ? communityActiveLeague : defaultCommunityLeague();
  var team = communityTeamForLeague(league);
  var input = document.getElementById('community-post-input');
  var text = input ? input.value.trim() : communityDraft.trim();
  if (!team || !text) return;
  if (text.length > COMMUNITY_POST_LIMIT) text = text.slice(0, COMMUNITY_POST_LIMIT);
  var lastPostAt = Number(lsGet('readsCommunityLastPostAt', 0)) || 0;
  if (Date.now() - lastPostAt < 10000) {
    communityError = 'Give it a few seconds before posting again.';
    renderAll();
    return;
  }
  var badge = selectedBadge();
  var career = progressionRankFor(getProgression().careerXp || 0);
  var rating = getRating();
  var streak = getStreak();
  communityError = '';
  lsSet('readsCommunityLastPostAt', Date.now());
  communityDraft = '';
  if (input) input.value = '';
  window.__fbSync.postCommunity(communityTeamKey(league, team), {
    teamId: team.id,
    teamName: team.name,
    league: league,
    authorName: state.name,
    badgeId: badge ? badge.id : null,
    badgeTitle: badge ? badge.title : null,
    badgeIcon: badge ? badge.icon : null,
    careerRank: career.name,
    rating: rating ? rating.score : null,
    streak: streak.count || 0,
    text: text
  }).catch(function () {
    communityError = 'Couldn’t post right now. Try again.';
    if (state.screen === 'community') renderAll();
  });
}

var MODE_DIFFICULTY_LABEL = { casual: 'Casual', competitive: 'Competitive', hardcore: 'Hardcore' };
function modeCardHtml(m) {
  // Full Visual + Interactive Redesign pass: a real "NEW" badge (never
  // played by this player, per the same modeTimesPlayed() signal
  // recommendedModeHtml()'s own "New to you" copy already uses) and a
  // "Play Now" chevron affordance on featured cards, matching the
  // redesigned homepage mockup -- no fabricated freshness flag, no new
  // per-mode metadata.
  var isNew = state.name && modeTimesPlayed(m.id) === 0;
  return '<button class="mode-card' + (m.featured ? ' featured' : '') + '" data-go="' + m.id + '">' +
    (m.difficulty ? '<span class="mode-difficulty mode-difficulty-' + m.difficulty + '">' + MODE_DIFFICULTY_LABEL[m.difficulty] + '</span>' : '') +
    (isNew ? '<span class="mode-new-badge">New</span>' : '') +
    '<div class="mode-icon">' + icon(m.icon) + '</div>' +
    '<div class="mode-title">' + esc(m.title) + '</div>' +
    '<div class="mode-desc">' + esc(m.desc) + '</div>' +
    (m.featured ? '<span class="mode-card-play">Play Now' + icon('arrowRight') + '</span>' : '') +
    '</button>';
}
// UI/UX Upgrade Pass: featured modes (Quiz/Grid/IQ Test/Player From Clues --
// real, already-curated via each entry's own `featured` flag, nothing new
// invented here) now render in their own grid FIRST, ahead of the rest of
// that league's modes -- real visual + positional hierarchy ("featured /
// primary / secondary", per this pass's own explicit ask) instead of relying
// on .mode-card.featured's bigger-card styling alone to carry it while the
// cards themselves stayed interleaved in whatever order LEAGUE_MODES happened
// to list them in.
function modeSectionHtml(league) {
  var all = LEAGUE_MODES[league];
  var featured = all.filter(function (m) { return m.featured; });
  var rest = all.filter(function (m) { return !m.featured; });
  if (state.name) {
    var scoreMap = {};
    scoredModeRecommendations(999).forEach(function(r){ scoreMap[r.mode.id]=r.score; });
    featured.sort(function(x,y){ return (scoreMap[y.id]||0)-(scoreMap[x.id]||0); });
    rest.sort(function(x,y){ return (scoreMap[y.id]||0)-(scoreMap[x.id]||0); });
  }
  var subtitle = league === 'nfl' ? 'Pro football challenges' : 'Saturdays, rivalries &amp; tradition';
  return '<div class="mode-section-header"><div><h2 class="mode-section-title mode-section-title-' + league + '">' + esc(LEAGUE_LABELS[league]) +
    '<span class="mode-section-count">' + all.length + ' games</span></h2><p>' + subtitle + '</p></div></div>' +
    (featured.length ? '<div class="mode-grid mode-grid-' + league + ' mode-grid-featured">' + featured.map(modeCardHtml).join('') + '</div>' : '') +
    (rest.length ? '<div class="mode-grid mode-grid-' + league + ' mode-grid-secondary" aria-label="More ' + esc(LEAGUE_LABELS[league]) + ' games">' + rest.map(modeCardHtml).join('') + '</div>' : '');
}
function continuePlayingCardHtml() {
  var last = lsGet('nflTriviaLastMode', null);
  if (!last || !LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).some(function (m) { return m.id === last; })) return '';
  // Full Visual + Interactive Redesign pass: icon-circle + "Resume" chevron
  // treatment matching the redesigned homepage's row style -- deliberately
  // NOT a progress bar/percentage (the mockup shows one, but this app
  // doesn't persist an in-round resume point once a mode is left, so a
  // literal progress fraction here would be fabricated; real data only).
  return '<button class="continue-card" data-go="' + esc(last) + '">' +
    '<span class="continue-card-icon">' + icon('play') + '</span>' +
    '<span class="continue-card-text"><span class="continue-card-label">Continue Playing</span>' +
    '<span class="continue-card-mode">' + esc(modeLabelFor(last)) + '</span></span>' +
    '<span class="continue-card-resume">Resume' + icon('arrowRight') + '</span>' +
    '</button>';
}
// A mode's "times played" lives under a different key per mode (roundsPlayed,
// gamesPlayed, attempts, testsTaken, sessionsPlayed, completions) since each
// stats shape grew independently in DEFAULT_STATS — this just normalizes
// across all of them for the one thing recommendedModeHtml() needs to know.
function modeTimesPlayed(id) {
  var st = state.stats[id];
  if (!st) return 0;
  return st.roundsPlayed || st.gamesPlayed || st.attempts || st.testsTaken || st.sessionsPlayed || st.completions || 0;
}
// "Recommended for you" — deliberately deterministic per day+name (same
// seeded-PRNG pattern as the Daily Reads) rather than Math.random(),
// so the suggestion doesn't change on every re-render/click and instead
// reads as a considered daily pick. Prioritizes modes never played at all
// (exploration); once everything's been tried at least once, falls back to
// whichever mode has been played the least (keeps rotation fresh).
// Full Visual + Interactive Redesign pass: shared icon-circle + text +
// chevron row builder for "More Ways to Play" -- same real per-card data
// each of these already computed (h2h record, friend count, review-pool
// size), just one consistent premium row shape instead of every card
// hand-assembling its own continue-card markup.
function discoverRowHtml(mode, iconName, title, sublabel, extraClass) {
  return '<button class="continue-card discover-row' + (extraClass ? ' ' + extraClass : '') + '" data-go="' + esc(mode) + '">' +
    '<span class="continue-card-icon">' + icon(iconName) + '</span>' +
    '<span class="continue-card-text"><span class="continue-card-mode">' + esc(title) + '</span>' +
    '<span class="continue-card-label">' + esc(sublabel) + '</span></span>' +
    icon('arrowRight', 'continue-card-chevron') +
    '</button>';
}
function h2hCardHtml() {
  var st = state.stats.h2h || {};
  var recordBit = st.matchesPlayed ? (st.wins + '-' + st.losses + (st.ties ? '-' + st.ties : '')) : 'New';
  return discoverRowHtml('h2h', 'versus', 'Head-to-Head', 'Challenge a friend · ' + recordBit, 'h2h-card');
}
function learnCardHtml() {
  // User feedback: the book icon "makes zero sense" for Film Room --
  // matches the nav tab's own fix (clapperboard).
  return discoverRowHtml('learn', 'clapperboard', 'The Film Room', "Facts, history, HOF & scheme concepts", 'learn-card');
}
function friendsCardHtml() {
  var count = getFriends().length;
  var label = count ? (count + ' friend' + (count === 1 ? '' : 's') + ' added') : 'See how they stack up';
  return discoverRowHtml('friends', 'users', 'Friends', label, 'friends-card');
}
function personalizationKey() { return 'readsPersonalizationV2__' + slugify(state.name || 'guest'); }
function defaultPersonalizationState() { return { playEvents: [], categoryStats: { nfl:{}, cfb:{} }, weeklyClaims: [], retentionClaims: [], lastHomeSeen: '', updatedAt: 0 }; }
function getPersonalizationState() {
  var p = lsGet(personalizationKey(), defaultPersonalizationState());
  p.playEvents = Array.isArray(p.playEvents) ? p.playEvents : [];
  p.categoryStats = p.categoryStats || { nfl:{}, cfb:{} };
  p.categoryStats.nfl = p.categoryStats.nfl || {};
  p.categoryStats.cfb = p.categoryStats.cfb || {};
  p.weeklyClaims = Array.isArray(p.weeklyClaims) ? p.weeklyClaims : [];
  p.retentionClaims = Array.isArray(p.retentionClaims) ? p.retentionClaims : [];
  p.lastHomeSeen = p.lastHomeSeen || '';
  return p;
}
function setPersonalizationState(p, skipSync) {
  p = Object.assign(defaultPersonalizationState(), p || {}, { updatedAt: Date.now() });
  p.playEvents = (p.playEvents || []).slice(-120);
  lsSet(personalizationKey(), p);
  if (!skipSync) pushProfileSnapshot();
}
function mergePersonalization(local, cloud) {
  local = local || defaultPersonalizationState(); cloud = cloud || defaultPersonalizationState();
  var events = {}, mergedEvents = [];
  (local.playEvents || []).concat(cloud.playEvents || []).forEach(function (e) {
    if (!e || !e.at || !e.mode) return;
    var key = e.mode + '|' + e.at;
    if (!events[key]) { events[key] = true; mergedEvents.push(e); }
  });
  mergedEvents.sort(function (x,y) { return (Number(x.at)||0)-(Number(y.at)||0); });
  var stats = { nfl:{}, cfb:{} };
  ['nfl','cfb'].forEach(function (league) {
    var cats = {};
    [local, cloud].forEach(function (src) {
      var obj = src.categoryStats && src.categoryStats[league] || {};
      Object.keys(obj).forEach(function (cat) {
        var x = obj[cat] || {};
        cats[cat] = cats[cat] || { correct:0, total:0 };
        cats[cat].correct = Math.max(cats[cat].correct, Number(x.correct) || 0);
        cats[cat].total = Math.max(cats[cat].total, Number(x.total) || 0);
      });
    });
    stats[league] = cats;
  });
  var claims = {};
  (local.weeklyClaims || []).concat(cloud.weeklyClaims || []).forEach(function (id) { if (id) claims[id] = true; });
  var retentionClaims = {};
  (local.retentionClaims || []).concat(cloud.retentionClaims || []).forEach(function (id) { if (id) retentionClaims[id] = true; });
  var newer = (Number(cloud.updatedAt)||0) > (Number(local.updatedAt)||0) ? cloud : local;
  return { playEvents: mergedEvents.slice(-120), categoryStats: stats, weeklyClaims: Object.keys(claims), retentionClaims:Object.keys(retentionClaims), lastHomeSeen:newer.lastHomeSeen||'', updatedAt: Math.max(Number(local.updatedAt)||0, Number(cloud.updatedAt)||0) };
}
function recordKnowledgeAnswer(league, category, correct) {
  if (!state.name || !category) return;
  league = league === 'cfb' ? 'cfb' : 'nfl';
  var p = getPersonalizationState();
  var row = p.categoryStats[league][category] || { correct:0, total:0 };
  row.total++;
  if (correct) row.correct++;
  p.categoryStats[league][category] = row;
  setPersonalizationState(p, true);
}
function completionPctForPersonalization(mode, fields) {
  fields = fields || {};
  if (typeof fields.lastPct === 'number') return fields.lastPct;
  if (typeof fields.bestPct === 'number') return fields.bestPct;
  if ((mode === 'quiz' || mode === 'cfbQuiz') && state[mode] && state[mode].queue && state[mode].queue.length) return Math.round(100 * state[mode].correctCount / state[mode].queue.length);
  if (mode === 'daily' && state.daily && state.daily.queue && state.daily.queue.length) return Math.round(100 * state.daily.correctCount / state.daily.queue.length);
  return null;
}
function recordPersonalizationCompletion(mode, fields) {
  if (!state.name || !mode) return;
  checkRetentionMissionCompletion(mode);
  var p = getPersonalizationState();
  p.playEvents.push({ mode:mode, league:modeLeague(mode), at:Date.now(), pct:completionPctForPersonalization(mode, fields) });
  setPersonalizationState(p, true);
  checkWeeklyPersonalGoals();
  checkWeeklyRetentionReward();
}
function personalizationMasteryRows() {
  var p = getPersonalizationState(), rows = [];
  ['nfl','cfb'].forEach(function (league) {
    Object.keys(p.categoryStats[league] || {}).forEach(function (cat) {
      var x = p.categoryStats[league][cat];
      if (!x || !x.total) return;
      rows.push({ league:league, category:cat, correct:x.correct||0, total:x.total||0, pct:Math.round(100*(x.correct||0)/x.total) });
    });
  });
  return rows.sort(function (x,y) { return y.total-x.total; });
}
function personalizationLeagueProfile() {
  var events = getPersonalizationState().playEvents || [];
  var out = { nfl:{plays:0,pcts:[]}, cfb:{plays:0,pcts:[]} };
  events.forEach(function (e) {
    if (e.league !== 'nfl' && e.league !== 'cfb') return;
    var l = e.league; out[l].plays++;
    if (typeof e.pct === 'number') out[l].pcts.push(e.pct);
  });
  ['nfl','cfb'].forEach(function (l) {
    out[l].avg = out[l].pcts.length ? Math.round(out[l].pcts.reduce(function(s,n){return s+n;},0)/out[l].pcts.length) : null;
  });
  return out;
}
function weeklyGoalWeekKey() { return dailyRivalWeekKey(todayStr()); }
function weeklyPersonalGoals() {
  var week = weeklyGoalWeekKey(), p = getPersonalizationState();
  var events = (p.playEvents || []).filter(function (e) {
    var d = new Date(Number(e.at)||0), ds = d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
    return dailyRivalWeekKey(ds) === week;
  });
  var nfl = events.filter(function(e){return e.league==='nfl'||e.league==='mixed';}).length;
  var cfb = events.filter(function(e){return e.league==='cfb'||e.league==='mixed';}).length;
  var daily = getDailyRecords().filter(function(r){return dailyRivalWeekKey(r.date)===week;}).length;
  var mastery = personalizationMasteryRows();
  var weak = mastery.filter(function(r){return r.total>=3;}).sort(function(x,y){return x.pct-y.pct;})[0];
  var goals = [
    { id:week+'_daily3', label:'Daily Habit', desc:'Complete Daily Reads 3 times this week.', current:daily, target:3, xp:75 },
    { id:week+'_balance', label:'Play Both Sides', desc:'Play 2 NFL and 2 College games this week.', current:Math.min(2,nfl)+Math.min(2,cfb), target:4, xp:100 }
  ];
  if (weak) {
    var weakLeagueGames = events.filter(function(e){return (e.league==='cfb'?'cfb':'nfl')===weak.league;}).length;
    goals.push({ id:week+'_weak_'+slugify(weak.league), label:'Attack Your Weak Side', desc:'Play 2 '+(weak.league==='cfb'?'College':'NFL')+' games. '+weak.category+' is your lowest tracked category at '+weak.pct+'%.', current:weakLeagueGames, target:2, xp:100, weak:weak });
  } else goals.push({ id:week+'_games5', label:'Build Your Profile', desc:'Play 5 ranked games so Reads can learn your game.', current:events.length, target:5, xp:75 });
  return goals;
}
function checkWeeklyPersonalGoals() {
  if (!state.name) return;
  var p = getPersonalizationState(), claims = {};
  (p.weeklyClaims||[]).forEach(function(id){claims[id]=true;});
  weeklyPersonalGoals().forEach(function(g){
    if (claims[g.id] || g.current < g.target) return;
    p.weeklyClaims.push(g.id); claims[g.id]=true;
    var seasonId = footballSeasonIdForDate();
    if (activeAuthUid && window.__fbSync && window.__fbSync.awardProgress) {
      window.__fbSync.awardProgress(profileDocId(), 'personal_goal_'+g.id, {type:'PERSONAL_GOAL_COMPLETED',source:'personalization',goalId:g.id}, g.xp, seasonId)
        .then(function(result){ if(!result || !result.duplicate) applyProgressAwardLocally(g.xp,seasonId); pushSeasonLeaderboardSnapshot(); pushProfileSnapshot(); }).catch(function(){});
    } else applyProgressAwardLocally(g.xp, seasonId);
  });
  setPersonalizationState(p, true);
}
function personalizationMasteryHtml() {
  if (!state.name) return '';
  var rows = personalizationMasteryRows().filter(function(r){return r.total>=3;});
  if (!rows.length) return '<section class="personalization-panel"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">YOUR FOOTBALL BRAIN</span><h3>Mastery Map</h3></div><span>Learning as you play</span></div><p class="mode-desc">Play Quiz, College Quiz, and Daily Reads to build category mastery.</p></section>';
  var strongest = rows.slice().sort(function(x,y){return y.pct-x.pct;}).slice(0,3);
  var weakest = rows.slice().sort(function(x,y){return x.pct-y.pct;}).slice(0,3);
  function cards(list, cls){return list.map(function(r){return '<div class="mastery-chip '+cls+'"><span>'+esc(r.league.toUpperCase())+'</span><b>'+esc(r.category)+'</b><strong>'+r.pct+'%</strong><small>'+r.correct+'/'+r.total+' correct</small></div>';}).join('');}
  return '<section class="personalization-panel"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">YOUR FOOTBALL BRAIN</span><h3>Mastery Map</h3></div><span>Real answer history</span></div><div class="mastery-columns"><div><h4>Strengths</h4>'+cards(strongest,'strong')+'</div><div><h4>Work On</h4>'+cards(weakest,'weak')+'</div></div></section>';
}
function weeklyPersonalGoalsHtml() {
  if (!state.name) return '';
  var claims=getPersonalizationState().weeklyClaims||[];
  var goals=weeklyPersonalGoals();
  return '<section class="personalization-panel weekly-personal-goals"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">THIS WEEK</span><h3>Your Missions</h3></div><span>Adaptive goals</span></div><div class="personal-goal-grid">'+goals.map(function(g){var done=claims.indexOf(g.id)!==-1||g.current>=g.target;var pct=Math.max(0,Math.min(100,Math.round(100*g.current/g.target)));return '<div class="personal-goal '+(done?'complete':'')+'"><div><b>'+esc(g.label)+'</b><span>+'+g.xp+' XP</span></div><p>'+esc(g.desc)+'</p><div class="personal-goal-track"><i style="width:'+pct+'%"></i></div><small>'+(done?'Complete':Math.min(g.current,g.target)+' / '+g.target)+'</small></div>';}).join('')+'</div></section>';
}
function lastPersonalizationPlayDate() {
  var events = getPersonalizationState().playEvents || [];
  if (!events.length) return '';
  var last = events[events.length - 1], d = new Date(Number(last.at)||0);
  return dateStr(d);
}
function comebackGapDays() {
  var last = lastPersonalizationPlayDate();
  return last ? daysBetween(last, todayStr()) : 0;
}
function retentionMission() {
  if (!state.name) return null;
  var gap = comebackGapDays();
  if (gap < 2) return null;
  var rec = scoredModeRecommendations(1)[0];
  var mastery = personalizationMasteryRows().filter(function(r){return r.total>=3;}).sort(function(x,y){return x.pct-y.pct;})[0];
  return {
    id:'comeback_'+todayStr(),
    gap:gap,
    xp:Math.min(200, 50 + gap * 10),
    mode:rec ? rec.mode.id : 'quiz',
    title:'Comeback Drive',
    desc: mastery ? 'Shake off the rust with a game aimed at your '+mastery.category+' weak spot.' : 'Get back on the board with one ranked game.'
  };
}
function retentionMissionHtml() {
  var m = retentionMission();
  if (!m) return '';
  var claimed = (getPersonalizationState().retentionClaims||[]).indexOf(m.id)!==-1;
  return '<section class="retention-comeback-card '+(claimed?'complete':'')+'"><div><span class="dashboard-eyebrow">WELCOME BACK</span><h3>'+esc(m.title)+'</h3><p>'+esc(m.desc)+'</p><small>'+m.gap+' days since your last ranked game</small></div><div><b>+'+m.xp+' XP</b>'+(claimed?'<span>'+icon('check')+' Complete</span>':'<button class="btn-primary" data-go="'+esc(m.mode)+'">Start Comeback</button>')+'</div></section>';
}
function checkRetentionMissionCompletion(mode) {
  var m = retentionMission();
  if (!m || mode !== m.mode) return;
  var p = getPersonalizationState();
  if ((p.retentionClaims||[]).indexOf(m.id)!==-1) return;
  p.retentionClaims.push(m.id);
  setPersonalizationState(p,true);
  var seasonId=footballSeasonIdForDate();
  if (activeAuthUid && window.__fbSync && window.__fbSync.awardProgress) {
    window.__fbSync.awardProgress(profileDocId(),'retention_'+m.id,{type:'COMEBACK_MISSION_COMPLETED',source:'retention',gapDays:m.gap,mode:mode},m.xp,seasonId)
      .then(function(result){if(!result||!result.duplicate) applyProgressAwardLocally(m.xp,seasonId);pushSeasonLeaderboardSnapshot();pushProfileSnapshot();if(state.screen==='home')renderAll();}).catch(function(){});
  } else {
    applyProgressAwardLocally(m.xp,seasonId);
    pushSeasonLeaderboardSnapshot();
  }
}
function weeklyRetentionGoal() {
  var week=weeklyGoalWeekKey();
  var days=getDailyRecords().filter(function(r){return dailyRivalWeekKey(r.date)===week;}).length;
  return { id:week+'_retention5', label:'Five-Day Drive', current:days, target:5, xp:150, desc:'Complete Daily Reads on 5 days this week.' };
}
function weeklyRetentionGoalHtml() {
  if(!state.name) return '';
  var g=weeklyRetentionGoal(), p=getPersonalizationState(), claimed=(p.retentionClaims||[]).indexOf(g.id)!==-1;
  var pct=Math.max(0,Math.min(100,Math.round(100*g.current/g.target)));
  return '<section class="retention-weekly-card '+(claimed?'complete':'')+'"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">WEEKLY HABIT</span><h3>'+esc(g.label)+'</h3></div><span>+'+g.xp+' XP</span></div><p>'+esc(g.desc)+'</p><div class="personal-goal-track"><i style="width:'+pct+'%"></i></div><small>'+(claimed?'Reward claimed':Math.min(g.current,g.target)+' / '+g.target+' days')+'</small></section>';
}
function checkWeeklyRetentionReward() {
  if(!state.name) return;
  var g=weeklyRetentionGoal(), p=getPersonalizationState();
  if(g.current<g.target || (p.retentionClaims||[]).indexOf(g.id)!==-1) return;
  p.retentionClaims.push(g.id); setPersonalizationState(p,true);
  var seasonId=footballSeasonIdForDate();
  if(activeAuthUid&&window.__fbSync&&window.__fbSync.awardProgress){
    window.__fbSync.awardProgress(profileDocId(),'retention_'+g.id,{type:'WEEKLY_RETENTION_COMPLETED',source:'retention'},g.xp,seasonId)
      .then(function(result){if(!result||!result.duplicate)applyProgressAwardLocally(g.xp,seasonId);pushSeasonLeaderboardSnapshot();pushProfileSnapshot();}).catch(function(){});
  } else applyProgressAwardLocally(g.xp,seasonId);
}
function unfinishedBusinessHtml() {
  if(!state.name) return '';
  var cards=[];
  var last=lsGet('nflTriviaLastMode',null);
  if(last && LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).some(function(m){return m.id===last;})) {
    cards.push({mode:last,label:'Run it back',title:modeLabelFor(last),sub:'Your most recent mode'});
  }
  var weak=personalizationMasteryRows().filter(function(r){return r.total>=3;}).sort(function(x,y){return x.pct-y.pct;})[0];
  if(weak){
    var targetMode=weak.league==='cfb'?'cfbQuiz':'quiz';
    cards.push({mode:targetMode,label:'Fix the tape',title:weak.category,sub:weak.pct+'% mastery · '+(weak.league==='cfb'?'College':'NFL')});
  }
  var rec=scoredModeRecommendations(3).find(function(r){return !cards.some(function(c){return c.mode===r.mode.id;});});
  if(rec) cards.push({mode:rec.mode.id,label:'Fresh look',title:rec.mode.title,sub:rec.reason});
  if(!cards.length)return '';
  return '<section class="retention-unfinished"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">UNFINISHED BUSINESS</span><h3>Pick up where Reads says it matters</h3></div><span>'+cards.length+' plays</span></div><div class="retention-unfinished-grid">'+cards.slice(0,3).map(function(c){return '<button data-go="'+esc(c.mode)+'"><span>'+esc(c.label)+'</span><b>'+esc(c.title)+'</b><small>'+esc(c.sub)+'</small>'+icon('arrowRight')+'</button>';}).join('')+'</div></section>';
}
function returnHookHtml() {
  if(!state.name) return '';
  var streak=getStreak(), rec=scoredModeRecommendations(1)[0], dailyDone=playedToday();
  var msg=dailyDone ? 'Daily Reads is handled. Keep your week moving with '+(rec?rec.mode.title:'another ranked game')+'.' :
    (streak.count ? 'Your '+streak.count+'-day streak is live. Today’s Daily Reads keeps it moving.' : 'Start today with Daily Reads and build your first streak.');
  return '<div class="retention-return-hook"><span>'+icon('flame')+'</span><div><b>Today’s move</b><small>'+esc(msg)+'</small></div><button class="btn-tiny" data-go="'+(dailyDone && rec?rec.mode.id:'daily')+'">'+(dailyDone?'Play Next':'Do Daily')+'</button></div>';
}
function recommendationHistoryKey() { return 'readsRecommendationHistory__' + slugify(state.name || 'guest'); }
function getRecommendationHistory() { return lsGet(recommendationHistoryKey(), []); }
function noteRecommendedModePlayed(mode) {
  if (!state.name || !mode) return;
  var h = getRecommendationHistory().filter(function (x) { return x && x.mode !== mode; });
  h.push({ mode: mode, at: Date.now() });
  lsSet(recommendationHistoryKey(), h.slice(-20));
}
function modeLeague(id) {
  if (id === 'endless' && typeof ENDLESS !== 'undefined' && ENDLESS && ENDLESS.league) return ENDLESS.league;
  return id && id.indexOf('cfb') === 0 ? 'cfb' : 'nfl';
}
function modeMasteryScore(id) {
  var st = state.stats[id] || {};
  if (typeof st.bestPct === 'number') return st.bestPct;
  if (typeof st.bestIQ === 'number') return Math.min(100, Math.round(st.bestIQ / 1.6));
  if (typeof st.bestScore === 'number') return Math.min(100, st.bestScore);
  if (typeof st.bestStreak === 'number') return Math.min(100, st.bestStreak * 5);
  return null;
}
function personalizedDifficultyTarget(league) {
  league = league === 'cfb' ? 'cfb' : 'nfl';
  var r = getRating();
  var mastery = personalizationMasteryRows().filter(function(x){return x.league===league && x.total>=3;});
  var avg = mastery.length ? Math.round(mastery.reduce(function(s,x){return s+x.pct;},0)/mastery.length) : null;
  var score = r ? Number(r.score)||100 : 100;
  if (avg != null) score = Math.round((score + (60 + avg)) / 2);
  if (score >= 135) return 'Hard';
  if (score >= 105) return 'Medium';
  return 'Easy';
}
function adaptiveDifficultyNoteHtml(league) {
  if (!state.name) return '';
  return '<div class="adaptive-difficulty-note">'+icon('target')+' Reads recommends <b>'+esc(personalizedDifficultyTarget(league))+'</b> difficulty from your Football Rating and tracked mastery.</div>';
}
function recommendationReasonFor(mode, scoreBits) {
  if (scoreBits.unplayed) return 'New to you';
  if (scoreBits.masteryFit) return 'Attack a weak spot';
  if (scoreBits.weakLeague) return 'Build your weak side';
  if (scoreBits.favoriteLeague) return 'Fits your teams';
  if (scoreBits.lowMastery) return 'Room to improve';
  if (scoreBits.cooldown) return 'Fresh rotation';
  if (scoreBits.fresh) return 'Keep it fresh';
  return 'Picked for you';
}
function scoredModeRecommendations(limit) {
  if (!state.name) return [];
  var all = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  var fav = getFavoriteTeams();
  var last = lsGet('nflTriviaLastMode', null);
  var hist = getRecommendationHistory();
  var recentModes = {};
  hist.slice(-5).forEach(function (x) { if (x && x.mode) recentModes[x.mode] = true; });
  if (last) recentModes[last] = true;

  var profile = personalizationLeagueProfile();
  var nflPlays = LEAGUE_MODES.nfl.reduce(function (n,m) { return n + modeTimesPlayed(m.id); }, 0);
  var cfbPlays = LEAGUE_MODES.cfb.reduce(function (n,m) { return n + modeTimesPlayed(m.id); }, 0);
  var weakerLeague = profile.nfl.avg != null && profile.cfb.avg != null && profile.nfl.avg !== profile.cfb.avg
    ? (profile.nfl.avg < profile.cfb.avg ? 'nfl' : 'cfb')
    : (nflPlays === cfbPlays ? null : (nflPlays < cfbPlays ? 'nfl' : 'cfb'));
  var playEvents = getPersonalizationState().playEvents || [];
  var recentCounts = {};
  playEvents.slice(-8).forEach(function(e){recentCounts[e.mode]=(recentCounts[e.mode]||0)+1;});
  var masteryRows = personalizationMasteryRows().filter(function(r){return r.total>=3;});
  var weakMasteryLeague = masteryRows.length ? masteryRows.slice().sort(function(x,y){return x.pct-y.pct;})[0].league : null;
  var daySeed = hashStr(todayStr() + '_smartReco_' + state.name);

  return all.map(function (m, idx) {
    var plays = modeTimesPlayed(m.id);
    var mastery = modeMasteryScore(m.id);
    var league = modeLeague(m.id);
    var bits = {
      unplayed: plays === 0,
      weakLeague: weakerLeague === league,
      favoriteLeague: !!fav[league],
      lowMastery: mastery != null && mastery < 70,
      masteryFit: weakMasteryLeague === league,
      cooldown: !recentCounts[m.id],
      fresh: !recentModes[m.id]
    };
    var score = 0;
    if (bits.unplayed) score += 42;
    if (bits.favoriteLeague) score += 18;
    if (bits.weakLeague) score += 12;
    if (bits.lowMastery) score += 18;
    if (bits.masteryFit) score += 14;
    if (bits.cooldown) score += 10;
    if (bits.fresh) score += 20;
    score += Math.max(0, 12 - Math.min(12, plays * 2));
    if (m.featured) score += 5;
    if (recentModes[m.id]) score -= 45;
    if ((recentCounts[m.id] || 0) >= 2) score -= 35 * recentCounts[m.id];
    // Stable daily tie-breaker keeps recommendations consistent through rerenders.
    score += ((hashStr(m.id + '_' + daySeed + '_' + idx) % 100) / 100);
    return { mode: m, score: score, reason: recommendationReasonFor(m, bits), bits: bits };
  }).sort(function (a,b) { return b.score - a.score; }).slice(0, limit || 3);
}
function recommendedModeHtml() {
  if (!state.name) return '';
  var recs = scoredModeRecommendations(1);
  if (!recs.length) return '';
  var pick = recs[0];
  return '<button class="recommend-card" data-go="' + pick.mode.id + '" data-recommended-mode="' + pick.mode.id + '">' +
    '<span class="recommend-card-icon">' + icon(pick.mode.icon) + '</span>' +
    '<span class="recommend-card-text"><span class="recommend-card-label">' + esc(pick.reason) + ' &middot; Recommended</span>' +
    '<span class="recommend-card-mode">' + esc(pick.mode.title) + '</span></span>' +
    icon('arrowRight', 'continue-card-chevron') +
    '</button>';
}
function recommendationShelfHtml() {
  if (!state.name) return '';
  var recs = scoredModeRecommendations(3);
  if (!recs.length) return '';
  return '<section class="smart-recommendations"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">FOR YOU</span><h3>Recommended Next</h3></div><span>Based on your play</span></div>' +
    '<div class="smart-recommendation-grid">' +
    recs.map(function (r) {
      return '<button class="smart-recommendation-card" data-go="' + r.mode.id + '" data-recommended-mode="' + r.mode.id + '">' +
        '<span class="smart-recommendation-icon">' + icon(r.mode.icon) + '</span>' +
        '<span class="smart-recommendation-reason">' + esc(r.reason) + '</span>' +
        '<strong>' + esc(r.mode.title) + '</strong>' +
        '<small>' + (modeTimesPlayed(r.mode.id) ? modeTimesPlayed(r.mode.id) + ' played' : 'Never played') + ' · ' + esc(personalizedDifficultyTarget(modeLeague(r.mode.id))) + ' target</small>' +
        '</button>';
    }).join('') + '</div></section>';
}
// UI/UX upgrade pass: a completion screen shouldn't be a dead end past its
// own "Play Again" button. Two real pieces, shown only when they apply —
// never fabricated: (1) if this round WAS today's Daily Reads (grid/
// blitz/silhouette/legends all route through their own normal result
// screen, not a separate daily one, so without this they finished with zero
// acknowledgment that their streak just moved), say so with the real streak
// count, same copy convention renderDailySummary() already uses; (2) the
// same real, deterministic recommendedModeHtml() the home screen uses, so
// there's always an obvious next thing to play besides repeating this one.
function dailyCompletionBannerHtml(dailyTypeId) {
  if (!state.justCompletedDaily || state.justCompletedDaily.typeId !== dailyTypeId) return '';
  var streak = getStreak();
  return '<div class="daily-complete-banner">' + icon('flame') + ' Today’s Daily Reads complete' +
    (streak.count > 0 ? ' — ' + streak.count + '-day streak' : '') + '. Come back tomorrow for a new one.</div>';
}
function postGameNextStepsHtml(dailyTypeId) {
  var rec = scoredModeRecommendations(1)[0];
  var mastery = personalizationMasteryRows().filter(function(r){return r.total>=3;}).sort(function(x,y){return x.pct-y.pct;})[0];
  var mode=state.screen;
  return dailyCompletionBannerHtml(dailyTypeId) +
    (mastery ? '<div class="one-more-game-context"><b>Reads learned something:</b> '+esc(mastery.category)+' is currently your biggest tracked weak spot at '+mastery.pct+'%.</div>' : '') +
    socialChallengeButtonHtml(mode) +
    (rec ? '<div class="one-more-game-label">ONE MORE GAME · '+esc(rec.reason)+'</div>' : '') +
    recommendedModeHtml();
}
// UI re-audit: this used to be a hardcoded "12 ways to play" in the tagline
// below -- real, live-verified stale copy (production actually offers 19:
// 12 NFL + 7 CFB, once the engine-backed modes shipped). Computed from
// LEAGUE_MODES itself so it can never drift out of sync with the real mode
// count again, regardless of which flags are on for a given deployment --
// the exact bug that let the old number go stale in the first place.
function totalModeCount() {
  return LEAGUE_MODES.nfl.length + LEAGUE_MODES.cfb.length;
}
// UI/UX upgrade pass: the home screen used to stack the Daily Reads,
// Continue Playing, Recommended, Head-to-Head, Live Match, X's & O's, Film
// Room, Friends, and Study cards full-width, one after another, ALL before
// a visitor ever reached the actual NFL/CFB mode grids — up to 8 identical-
// looking `.continue-card` rows of scrolling before "what can I actually
// play" appeared. The three that are genuinely time-sensitive/personal
// (Daily Reads, Continue Playing, Recommended) stay full-width and
// prominent right under the hero. Everything else — real features, but not
// urgent — moves into one compact "More Ways to Play" grid, the same
// pattern the NFL/CFB mode grids already use, so the page reaches real
// game content much sooner without losing any discoverability.
function discoverGridHtml() {
  var cards = [h2hCardHtml(), h2hLiveCardHtml(), xsoCardHtml(), learnCardHtml(), friendsCardHtml(), studyCardHtml()]
    .filter(function (html) { return html; });
  if (!cards.length) return '';
  return '<h2 class="mode-section-title">More Ways to Play</h2>' +
    '<div class="discover-grid">' + cards.join('') + '</div>';
}
var PROGRESSION_RANKS = [
  { name: 'Rookie', min: 0 },
  { name: 'Starter', min: 250 },
  { name: 'Playmaker', min: 750 },
  { name: 'Veteran', min: 1500 },
  { name: 'All-Pro', min: 3000 },
  { name: 'Legend', min: 6000 }
];
function progressionRankFor(xp) {
  xp = Math.max(0, Number(xp) || 0);
  var current = PROGRESSION_RANKS[0], next = null;
  for (var i = 0; i < PROGRESSION_RANKS.length; i++) {
    if (xp >= PROGRESSION_RANKS[i].min) current = PROGRESSION_RANKS[i];
    else { next = PROGRESSION_RANKS[i]; break; }
  }
  var pct = 1;
  if (next) pct = Math.max(0, Math.min(1, (xp - current.min) / (next.min - current.min)));
  return { name: current.name, next: next && next.name, xp: xp, pct: pct, toNext: next ? next.min - xp : 0 };
}

var lastProgressAward = null;
function progressionAwardPreview(mode, xp, seasonId) {
  var p=getProgression(), beforeCareer=progressionRankFor(p.careerXp||0);
  var season=normalizeSeasonProgress(p.seasons&&p.seasons[seasonId]);
  var beforeSeason=seasonRankFor(season.xp||0);
  var afterCareer=progressionRankFor((p.careerXp||0)+xp);
  var afterSeason=seasonRankFor((season.xp||0)+xp);
  lastProgressAward={
    mode:mode,xp:xp,seasonId:seasonId,
    careerBefore:beforeCareer,careerAfter:afterCareer,
    seasonBefore:beforeSeason,seasonAfter:afterSeason,
    createdAt:Date.now()
  };
}
function progressionResultHookHtml() {
  var x=lastProgressAward;
  if(!x||Date.now()-x.createdAt>120000)return '';
  if(state.screen!==x.mode&&!(x.mode==='daily'&&state.screen==='daily'))return '';
  var careerUp=x.careerBefore.name!==x.careerAfter.name;
  var seasonUp=x.seasonBefore.name!==x.seasonAfter.name;
  return '<div class="progression-result-hook'+((careerUp||seasonUp)?' rank-up':'')+'">'+
    '<div class="progression-result-main"><span>'+((careerUp||seasonUp)?'RANK UP':'PROGRESSION')+'</span><b>+'+x.xp+' XP</b></div>'+
    '<div class="progression-result-lines">'+
      '<span><b>Career:</b> '+esc(x.careerAfter.name)+(x.careerAfter.next?' · '+x.careerAfter.toNext+' XP to '+esc(x.careerAfter.next):' · Max rank')+'</span>'+
      '<span><b>'+esc(x.seasonId)+' Season:</b> '+esc(x.seasonAfter.name)+(x.seasonAfter.next?' · '+x.seasonAfter.toNext+' XP to '+esc(x.seasonAfter.next):' · Top tier')+'</span>'+
    '</div>'+
  '</div>';
}
function careerLadderHtml() {
  var xp=Number(getProgression().careerXp)||0, rank=progressionRankFor(xp);
  return '<section class="career-ladder"><div class="profile-section-head"><div><span class="dashboard-eyebrow">CAREER PATH</span><h3>Reads Career</h3></div><span>'+xp.toLocaleString()+' XP</span></div>'+
    '<div class="career-ladder-track">'+PROGRESSION_RANKS.map(function(r,i){
      var unlocked=xp>=r.min, current=r.name===rank.name;
      return '<div class="career-ladder-step'+(unlocked?' unlocked':'')+(current?' current':'')+'">'+
        '<span class="career-ladder-icon">'+(unlocked?(i===PROGRESSION_RANKS.length-1?'👑':'🏈'):'🔒')+'</span>'+
        '<b>'+esc(r.name)+'</b><small>'+r.min.toLocaleString()+' XP</small>'+
      '</div>';
    }).join('')+'</div>'+
    '<div class="career-ladder-next"><span class="dashboard-xp-track"><span style="width:'+Math.round(rank.pct*100)+'%"></span></span>'+
      '<b>'+(rank.next?rank.toNext+' XP until '+esc(rank.next):'Career maxed — Legend status')+'</b></div></section>';
}
function seasonTrophyFor(item) {
  var rank=seasonRankFor(item.data.xp), icons={Rookie:'🎟️',Prospect:'🏈',Starter:'⭐',Playmaker:'⚡','All-Pro':'💎',MVP:'🏆'};
  return {icon:icons[rank.name]||'🏈',name:rank.name};
}
function seasonTrophyCaseHtml() {
  var list=seasonHistoryList();
  if(!list.length)return '';
  return '<section class="season-trophy-case"><div class="profile-section-head"><div><span class="dashboard-eyebrow">SEASON TROPHIES</span><h3>Your Football Years</h3></div><span>'+list.length+' earned</span></div>'+
    '<div class="season-trophy-grid">'+list.map(function(item){
      var trophy=seasonTrophyFor(item), d=item.data;
      return '<article class="season-trophy"><span>'+trophy.icon+'</span><div><b>'+esc(item.id)+' '+esc(trophy.name)+'</b><small>'+d.xp.toLocaleString()+' XP · '+d.gamesPlayed+' games'+(d.topMode?' · '+esc(modeLabelFor(d.topMode)):'')+'</small></div></article>';
    }).join('')+'</div></section>';
}

function nextAchievementProgress() {
  var earned = {};
  getRewards().unlockedBadgeIds.forEach(function (id) { earned[id] = true; });
  var candidates = [
    { id:'firstRead', label:'First Read', current:state.stats.daily.completions || 0, target:1 },
    { id:'dailyGrinder', label:'Daily Grinder', current:state.stats.daily.completions || 0, target:10 },
    { id:'daily25', label:'Daily Habit', current:state.stats.daily.completions || 0, target:25 },
    { id:'onFire', label:'On Fire', current:getStreak().count || 0, target:7 },
    { id:'streak30', label:'Iron Streak', current:getStreak().count || 0, target:30 }
  ].filter(function (x) { return !earned[x.id] && x.current < x.target; });
  if (!candidates.length) return null;
  candidates.sort(function (a,b) {
    return (b.current / b.target) - (a.current / a.target);
  });
  var c = candidates[0];
  c.pct = Math.max(0, Math.min(100, Math.round((c.current / c.target) * 100)));
  return c;
}
function dashboardActionStripHtml() {
  if (!state.name) return '';
  var dailyDone = playedToday();
  var achievement = nextAchievementProgress();
  var favLeague = defaultCommunityLeague();
  var favTeam = communityTeamForLeague(favLeague);
  var challenge = favTeam ? communityChallengeFor(favLeague, favTeam) : null;
  var challengeDone = favTeam && challenge ? communityChallengeStatus(favLeague, favTeam).completed : false;
  return '<div class="dashboard-action-strip">' +
    '<button data-go="daily" class="' + (dailyDone ? 'done' : '') + '"><span>' + icon(dailyDone ? 'check' : 'flame') + '</span><b>' + (dailyDone ? 'Daily Reads done' : 'Do Daily Reads') + '</b><small>' + (dailyDone ? 'Come back tomorrow' : 'Keep your streak alive') + '</small></button>' +
    (challenge ? '<button data-go="community" class="' + (challengeDone ? 'done' : '') + '"><span>' + icon(challengeDone ? 'check' : 'users') + '</span><b>' + (challengeDone ? 'Team challenge done' : 'Team challenge') + '</b><small>' + esc(favTeam.name) + '</small></button>' : '') +
    (achievement ? '<button data-go="profile"><span>' + icon('trophy') + '</span><b>' + esc(achievement.label) + '</b><small>' + achievement.current + ' / ' + achievement.target + '</small></button>' : '') +
    '</div>';
}

function personalDashboardHtml() {
  if (!state.name) return '';
  var p = getProgression();
  var seasonId = footballSeasonIdForDate();
  var seasonalXp = p.seasons && p.seasons[seasonId] ? Number(p.seasons[seasonId].xp) || 0 : 0;
  var career = progressionRankFor(p.careerXp);
  var seasonal = progressionRankFor(seasonalXp);
  var streak = getStreak();
  var rating = getRating();
  var fav = primaryFavoriteTeam();
  var equippedBadge = selectedBadge();
  var equippedCosmetic = selectedProfileCosmetic();
  function rankCard(label, rank, suffix) {
    return '<div class="dashboard-rank-card"><div class="dashboard-card-label">' + esc(label) + '</div>' +
      '<div class="dashboard-rank-name">' + esc(rank.name) + '</div>' +
      '<div class="dashboard-xp-line"><b>' + rank.xp + ' XP</b><span>' + (rank.next ? rank.toNext + ' to ' + esc(rank.next) : 'Max rank') + '</span></div>' +
      '<span class="dashboard-xp-track"><span style="width:' + Math.round(rank.pct * 100) + '%"></span></span>' +
      (suffix ? '<div class="dashboard-card-foot">' + esc(suffix) + '</div>' : '') +
      '</div>';
  }
  return '<section class="personal-dashboard" aria-label="Your Reads dashboard">' +
    "<div class=\"dashboard-head\"><div><span class=\"dashboard-eyebrow\">YOUR READS</span><h2>" + esc(state.name) + "'s Dashboard</h2></div>" +
    '<div class="dashboard-identity-tools">' +
      (equippedBadge ? '<span class="dashboard-equipped-badge" title="' + esc(equippedBadge.desc) + '">' + equippedBadge.icon + ' ' + esc(equippedBadge.title) + '</span>' : '') +
      (fav ? '<span class="dashboard-team">' + favoriteTeamBadgeHtml() + esc(fav.name) + '</span>' : '') +
    '</div></div>' +
    '<div class="dashboard-cosmetic-label">' + esc(equippedCosmetic.title) + ' profile frame</div>' +
    '<div class="dashboard-ranks">' +
    rankCard('Career Rank', career, 'Permanent') +
    rankCard(seasonId + ' Season', seasonal, 'Resets next football season') +
    '</div>' +
    '<div class="dashboard-quick-stats">' +
    '<div><span>' + icon('flame') + '</span><b>' + (streak.count || 0) + '</b><small>Day Streak</small></div>' +
    '<div><span>' + icon('shield') + '</span><b>' + (rating ? rating.score : '—') + '</b><small>Football Rating</small></div>' +
    '<div><span>' + icon('trophy') + '</span><b>' + (state.stats.daily.completions || 0) + '</b><small>Daily Wins</small></div>' +
    '</div>' +
    returnHookHtml() +
    dashboardActionStripHtml() +
    currentSeasonRecapHtml() +
    seasonLeaderboardHtml() +
    '</section>';
}

function renderHome() {
  return '<div class="hero"><img src="assets/brand/reads-logo.jpg" alt="Reads" class="hero-logo" />' +
    '<div class="hero-kicker">Built for people who actually know ball</div>' +
    '<h1 class="hero-tagline">NFL &amp; College Football trivia, ' + totalModeCount() + ' ways to play.</h1>' +
    favoriteTeamGreeting() +
    '<p>One adaptive Football Rating tracks how good you actually are — across every mode, every device.</p>' +
    '<div class="hero-actions"><button class="btn-primary" data-go="quiz">Play NFL Quiz ' + icon('arrowRight') + '</button>' +
    '<button class="btn-secondary" data-go="grid">Play Immaculate Grid</button></div></div>' +
    teamPickerPromptCardHtml() +
    personalDashboardHtml() +
    friendRivalAlertHtml() +
    teamBattleHtml() +
    liveFootballHomeHtml() +
    endlessHomeCardHtml() +
    reengagementCenterHtml() +
    retentionMissionHtml() +
    unfinishedBusinessHtml() +
    communityCardHtml() +
    dailyChallengeCardHtml() +
    weeklyDailyRecapHtml(false) +
    dailyRivalsHtml(false) +
    dailyStreakRewardsHtml() +
    continuePlayingCardHtml() +
    recommendationShelfHtml() +
    personalizationMasteryHtml() +
    weeklyPersonalGoalsHtml() +
    weeklyRetentionGoalHtml() +
    modeSectionHtml('nfl') +
    modeSectionHtml('cfb') +
    discoverGridHtml() +
    '<button class="btn-secondary leaderboard-link" data-go="leaderboard">' + icon('trophy') + ' View Leaderboard</button>' +
    (getRating() ? '<button class="btn-secondary leaderboard-link" data-retake-intro>' + icon('restart') + ' Retake Intro Test (resets Football Rating)</button>' : '') ;
}

/* ============================== NFL/CFB mode picker (dropdown / bottom sheet) ==============================
   Same panel serves as a small anchored dropdown on desktop and a full-width
   slide-up bottom sheet on mobile — see #mode-sheet's media query in styles.css.
   Triggered by any [data-league-toggle] button (there are two: one in #top-nav
   for desktop, one in #bottom-nav for mobile — only one is ever visible at a
   time per the breakpoint, but both work identically). */
var modeSheetOpenLeague = null;
var modeSheetTriggerEl = null; // focus returns here on close — standard accessible-dialog pattern
function openModeSheet(league) {
  modeSheetOpenLeague = league;
  modeSheetTriggerEl = document.activeElement;
  var titleEl = document.getElementById('mode-sheet-title');
  var itemsEl = document.getElementById('mode-sheet-items');
  if (titleEl) titleEl.textContent = LEAGUE_LABELS[league];
  if (itemsEl) {
    var favTeam = favoriteTeamById(league, getFavoriteTeams()[league]);
    itemsEl.innerHTML =
      (favTeam ? '<button class="mode-sheet-your-team" data-team-picker-toggle><span class="team-picker-swatch" style="' + teamSwatchStyle(favTeam) + '"></span>Your team: ' + esc(favTeam.name) + (favTeam.chant ? ' — ' + esc(favTeam.chant) : '') + '</button>' : '') +
      LEAGUE_MODES[league].map(function (m) {
        return '<button class="mode-sheet-item" data-go="' + m.id + '"><span class="msi-icon">' + icon(m.icon) + '</span><span class="msi-text">' + esc(m.title) +
          '<span class="msi-desc">' + esc(m.desc) + '</span></span></button>';
      }).join('');
  }
  var sheet = document.getElementById('mode-sheet');
  var backdrop = document.getElementById('mode-sheet-backdrop');
  if (sheet) sheet.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    var isOpen = btn.dataset.leagueToggle === league;
    btn.classList.toggle('sheet-open', isOpen);
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  // Move focus into the dialog once its open transition has started — the
  // close button is always present regardless of which league's items just
  // got rendered, so it's a reliable landing spot.
  setTimeout(function () {
    var closeBtn = document.getElementById('mode-sheet-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeModeSheet() {
  modeSheetOpenLeague = null;
  var sheet = document.getElementById('mode-sheet');
  var backdrop = document.getElementById('mode-sheet-backdrop');
  if (sheet) sheet.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    btn.classList.remove('sheet-open');
    btn.setAttribute('aria-expanded', 'false');
  });
  restoreFocus(modeSheetTriggerEl);
  modeSheetTriggerEl = null;
}
function toggleModeSheet(league) {
  if (modeSheetOpenLeague === league) closeModeSheet();
  else openModeSheet(league);
}

/* ============================== onboarding ==============================
   A short, dismissible 4-step walkthrough. Auto-opens once, the very first
   time the app is ever loaded on a device (tracked by ONBOARD_KEY in
   localStorage) — separate from name entry / the intro test, since a brand
   new visitor should understand what this app even is before either of
   those. Re-openable any time via the "?" button in the header — which is
   now CONTEXTUAL: while state.screen is an actual game mode, "?" shows a
   quick one-step tip for just that mode (reusing its own LEAGUE_MODES desc
   text) instead of the full walkthrough, so returning players don't have to
   sit through the whole intro again just to check a mode's rules. See
   contextualHelpSteps() and the help-toggle click handler below. The full
   walkthrough's final step's button is a real call-to-action (not just a
   "close" button) — worded and wired differently depending on where this
   person already is: straight into the intro test for a brand-new visitor,
   or into today's Daily Reads for someone who already has a rating. A
   contextual mode tip's button always just says "Got it" and closes. */
var ONBOARD_KEY = 'nflTriviaOnboarded';
// A real, answerable question (id 15 in data/quiz.js — the '72 Dolphins'
// perfect season, eagerly loaded so it's always available here) rendered
// with the exact same quiz-option/feedback markup and classes as the real
// Quiz mode, so clicking an answer during onboarding IS the real interaction,
// not a mockup of it — "show, don't tell" in place of the old text-only step.
var ONBOARDING_SAMPLE_QID = 15;
function onboardingSampleQuestion() { return QUIZ.find(function (q) { return q.id === ONBOARDING_SAMPLE_QID; }); }
var ONBOARDING_STEPS = [
  {
    title: 'What is Reads?',
    // UI re-audit: real, live-verified stale copy fixed here too (same "12"
    // hardcoded number as renderHome()'s old tagline) -- totalModeCount()
    // is defined above this array, so it's already real by the time this
    // module-level array literal runs.
    body: 'NFL and College Football trivia with ' + totalModeCount() + ' game modes, built around one thing that follows you everywhere: your <b>Football Rating</b> — an adaptive number that tracks your real skill over time instead of resetting every round. It’s free and works right in your browser — sign up with just a username and password, no email needed.'
  },
  { title: 'Try a real question', type: 'sample' },
  {
    title: 'Pick your mode',
    body: '<div class="onboarding-modes">' +
      '<span class="onboarding-mode-chip">' + icon('helpCircle') + ' Quiz</span>' +
      '<span class="onboarding-mode-chip">' + icon('grid') + ' Grid</span>' +
      '<span class="onboarding-mode-chip">' + icon('timer') + ' Blitz</span>' +
      '<span class="onboarding-mode-chip">' + icon('zap') + ' Speed</span>' +
      '<span class="onboarding-mode-chip">' + icon('search') + ' Silhouette</span>' +
      '<span class="onboarding-mode-chip">' + icon('trophy') + ' 12-0/17-0</span>' +
      '</div>Straight trivia, a name-the-player grid, timed challenges, and a fantasy-style roster draft — every mode exists for both NFL and College Football. Every one of them also has a Practice option, for when you just want to play without it touching your rating.'
  },
  {
    title: 'Come back every day',
    body: 'A <b>Daily Reads</b> drops every day — the same one for everyone, so it doubles as its own mini leaderboard. Complete it to build your streak, and don’t stress about one bad day: a grace day every week keeps your streak alive even if you miss.'
  },
  {
    title: 'Your rating goes with you',
    body: 'Log in once and your Football Rating, stats, and leaderboard rank sync across every device you play on — same account, same progress, anywhere. The leaderboard itself can be filtered to today, this week, or all-time.'
  },
  {
    title: 'Save it to your Home Screen',
    body: '<div class="onboarding-install-list">' +
      '<div class="onboarding-install-row">' + icon('share', 'onboarding-install-icon') + '<div><b>iPhone / iPad (Safari)</b><br>Tap the Share icon, then “Add to Home Screen.”</div></div>' +
      '<div class="onboarding-install-row">' + icon('download', 'onboarding-install-icon') + '<div><b>Android (Chrome)</b><br>Tap the ⋮ menu, then “Add to Home screen” or “Install app.”</div></div>' +
      '<div class="onboarding-install-row">' + icon('download', 'onboarding-install-icon') + '<div><b>Desktop (Chrome/Edge)</b><br>Click the install icon in the address bar, or the ⋮ menu → “Install Reads…”</div></div>' +
      '</div>Installed, it opens full-screen like a real app — no browser bar — and solo play still works offline.'
  }
];
// A one-off single-step "walkthrough" for the contextual "?" case — see
// openOnboarding(steps) below, which accepts either this shape or the full
// ONBOARDING_STEPS array interchangeably.
function contextualHelpSteps(m) {
  return [{ title: m.title, body: '<div class="onboarding-modes"><span class="onboarding-mode-chip">' + icon(m.icon) + ' ' + esc(m.title) + '</span></div>' + esc(m.desc) }];
}
var onboardingActiveSteps = ONBOARDING_STEPS;
var onboardingIndex = 0;
var onboardingSampleAnswered = null;
var onboardingTriggerEl = null;
function onboardingCtaLabel() {
  if (onboardingActiveSteps !== ONBOARDING_STEPS) return 'Got it';
  return getRating() ? "Try Today's Challenge" : 'Start the Intro Test';
}
function renderOnboardingSample() {
  var q = onboardingSampleQuestion();
  // Safety fallback only — QUIZ loads eagerly before app.js ever runs, so
  // this should be unreachable in practice.
  if (!q) return '<p class="mode-desc">Real questions, real feedback — try any mode from Home to see for yourself.</p>';
  var answered = onboardingSampleAnswered !== null;
  return '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === onboardingSampleAnswered) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-onboarding-sample-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (onboardingSampleAnswered === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Not quite — it was ' + esc(q.options[q.correctIndex]) + '.</span>') + '</div>' +
        '<p class="mode-desc">That’s the whole loop — pick, get instant feedback, move on. Every mode builds on it a little differently.</p>'
      : '')
    ;
}
function onboardingPickSample(i) {
  if (onboardingSampleAnswered !== null) return;
  onboardingSampleAnswered = i;
  var q = onboardingSampleQuestion();
  playSound(q && i === q.correctIndex ? 'correct' : 'wrong');
  renderOnboardingStep();
}
function renderOnboardingStep() {
  var step = onboardingActiveSteps[onboardingIndex];
  var body = document.getElementById('onboarding-body');
  if (body) body.innerHTML = '<div class="onboarding-step-title" id="onboarding-title">' + esc(step.title) + '</div>' +
    '<div class="onboarding-step-body">' + (step.type === 'sample' ? renderOnboardingSample() : step.body) + '</div>';
  var dots = document.getElementById('onboarding-dots');
  if (dots) {
    dots.innerHTML = onboardingActiveSteps.length > 1 ? onboardingActiveSteps.map(function (_, i) {
      return '<span class="onboarding-dot' + (i === onboardingIndex ? ' active' : '') + '"></span>';
    }).join('') : '';
  }
  var nextBtn = document.getElementById('onboarding-next');
  if (nextBtn) nextBtn.textContent = onboardingIndex === onboardingActiveSteps.length - 1 ? onboardingCtaLabel() : 'Next';
}
function openOnboarding(steps) {
  onboardingActiveSteps = steps || ONBOARDING_STEPS;
  onboardingIndex = 0;
  onboardingSampleAnswered = null;
  onboardingTriggerEl = document.activeElement;
  renderOnboardingStep();
  var modal = document.getElementById('onboarding-modal');
  var backdrop = document.getElementById('onboarding-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var nextBtn = document.getElementById('onboarding-next');
    if (nextBtn) nextBtn.focus();
  }, 0);
}
function closeOnboarding() {
  // The correct-answer crowd-cheer SFX now has its own max-duration cap
  // (sound.js's SFX_MAX_DURATION), but onboarding's sample question is
  // answered exactly once — nothing after it calls playSound() again to
  // cut it off the way every other mode naturally does — so this stops it
  // immediately on close rather than waiting out the cap.
  if (typeof stopSfx === 'function') stopSfx();
  var modal = document.getElementById('onboarding-modal');
  var backdrop = document.getElementById('onboarding-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  lsSet(ONBOARD_KEY, true);
  restoreFocus(onboardingTriggerEl);
  onboardingTriggerEl = null;
}
// The CTA itself: for a returning visitor who already has a rating, jump
// straight into today's Daily Reads. For a brand-new visitor, either
// start the intro test directly (if they already typed a name on a prior
// visit but never took it) or just land back on Home with the name field
// focused — saveName() already auto-starts the intro test the moment a name
// is saved with no existing rating, so this closes the loop naturally either
// way without duplicating that logic here. A contextual mode tip (see
// contextualHelpSteps above) skips all of this — "Got it" just closes.
function onboardingFinish() {
  closeOnboarding();
  if (onboardingActiveSteps !== ONBOARDING_STEPS) { renderAll(); return; }
  if (getRating()) { goToMode('daily'); return; }
  if (state.name) { startIntroTest(); return; }
  renderAll();
}
function onboardingNext() {
  if (typeof stopSfx === 'function') stopSfx();
  if (onboardingIndex >= onboardingActiveSteps.length - 1) { onboardingFinish(); return; }
  onboardingIndex++;
  renderOnboardingStep();
}

/* ============================== missed-question pool (for Study mode) ==============================
   A persisted, per-league, per-name log of question ids you've gotten wrong
   in Quiz or CFB Quiz — this is what Study mode below draws its round from,
   and grouping it by each question's own `category` field is also exactly
   how "weak categories" gets derived (see weakCategories) — no separate
   category-accuracy tracking needed, it falls straight out of the same log.
   A question is added the moment you miss it anywhere (pickQuizAnswer/
   pickCfbAnswer already call addToMissedPool below) and removed the moment
   you answer it correctly ANYWHERE, not just in Study mode itself — getting
   it right in a normal round "graduates" it out of your weak pool too, so
   Study mode isn't the only way to fix a weak spot. Capped at 200 entries
   (oldest dropped first) so this can't grow unbounded over months of play.
   Local-only, same as the streak/badges — not synced to Firebase. */
var MISSED_POOL_CAP = 200;
function missedPoolKey(league) { return 'nflTriviaMissedPool__' + league + '__' + slugify(state.name); }
function getMissedPool(league) { return state.name ? lsGet(missedPoolKey(league), []) : []; }
function addToMissedPool(league, id) {
  if (!state.name) return;
  var pool = getMissedPool(league);
  if (pool.indexOf(id) === -1) {
    pool.push(id);
    if (pool.length > MISSED_POOL_CAP) pool.shift();
    lsSet(missedPoolKey(league), pool);
  }
}
function removeFromMissedPool(league, id) {
  if (!state.name) return;
  var pool = getMissedPool(league);
  var idx = pool.indexOf(id);
  if (idx !== -1) { pool.splice(idx, 1); lsSet(missedPoolKey(league), pool); }
}
// Real signal, not a separate tracked stat: which categories show up most
// among your currently-missed questions. Naturally shrinks as questions get
// mastered (removed from the pool), so this always reflects your CURRENT
// weak spots, not a lifetime tally that never improves.
function weakCategories(league) {
  var pool = getMissedPool(league);
  var source = league === 'nfl' ? QUIZ : CFB;
  var counts = {};
  pool.forEach(function (id) {
    var q = source.find(function (qq) { return qq.id === id; });
    if (q) counts[q.category] = (counts[q.category] || 0) + 1;
  });
  return Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).map(function (cat) { return { category: cat, count: counts[cat] }; });
}

/* ============================== classic quiz ============================== */
function quizCategories() { return Array.from(new Set(QUIZ.map(function (q) { return q.category; }))).sort(); }
function quizDifficulties() { return Array.from(new Set(QUIZ.map(function (q) { return q.difficulty; }))).sort(); }
function quizPool(category, difficulty) {
  return QUIZ.filter(function (q) {
    return (!category || q.category === category) && (!difficulty || q.difficulty === difficulty);
  });
}
function currentQuizQuestion() {
  var id = state.quiz.queue[state.quiz.index];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startQuizRound(category, difficulty, roundSize) {
  beginProgressSession('quiz');
  var pool = quizPool(category, difficulty);
  if (typeof filterFreshQuestions === 'function') {
    var freshPool = filterFreshQuestions(pool, 'nfl', 70);
    if (freshPool.length >= Math.min(roundSize, pool.length)) pool = freshPool;
  }
  var ids = drawGlobalNoRepeatQuestions('quiz_' + (category || 'all') + '_' + (difficulty || 'all'), pool, roundSize, 'nfl', difficulty);
  state.quiz = { screen: 'question', category: category, difficulty: difficulty, roundSize: roundSize, queue: ids, index: 0, correctCount: 0, answeredIndex: null, missed: [], ranked: state.rankedPref.quiz !== false };
  renderAll();
}
function pickQuizAnswer(i) {
  if (state.quiz.answeredIndex !== null) return;
  state.quiz.answeredIndex = i;
  var q = currentQuizQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) { state.quiz.correctCount++; if (q) removeFromMissedPool('nfl', q.id); }
  else if (q) { state.quiz.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i }); addToMissedPool('nfl', q.id); }
  if (q) {
    recordKnowledgeAnswer('nfl', q.category || 'General', !!isCorrect);
    if (typeof rememberContentQuestion === 'function') rememberContentQuestion(q, 'nfl', 'quiz');
  }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextQuizQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  if (state.quiz.index + 1 >= state.quiz.queue.length) {
    state.quiz.screen = 'summary';
    finishQuizRound();
  } else {
    state.quiz.index++;
    state.quiz.answeredIndex = null;
  }
  renderAll();
}
function finishQuizRound() {
  var pct = Math.round(100 * state.quiz.correctCount / state.quiz.queue.length);
  if (state.quiz.ranked !== false) {
    var st = state.stats.quiz;
    st.correctTotal += state.quiz.correctCount;
    st.questionsTotal += state.quiz.queue.length;
    st.roundsPlayed++;
    if (pct > st.bestPct) st.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    state.quiz.ratingDelta = lastRatingDelta;
    pushLeaderboard('quiz', { correctTotal: st.correctTotal, questionsTotal: st.questionsTotal, roundsPlayed: st.roundsPlayed, bestPct: st.bestPct });
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}
function playQuizAgain() { startQuizRound(state.quiz.category, state.quiz.difficulty, state.quiz.roundSize); }
function quizBackToSetup() { state.quiz.screen = 'setup'; renderAll(); }

function renderQuizSetup() {
  var t = state.quiz;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz">' +
    broadcastMarqueeHtml('NFL · THE KNOWLEDGE DESK', 'MAKE THE CALL', 'Pick your category. Set your difficulty. Own the round.') +
    '<div class="field-row">' +
    '<label>Category<select id="quiz-cat"><option value="">All categories</option>' +
    quizCategories().map(function (c) { return '<option value="' + esc(c) + '"' + (t.category === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') +
    '</select></label>' +
    '<label>Difficulty<select id="quiz-diff"><option value="">All difficulties</option>' +
    quizDifficulties().map(function (d) { return '<option value="' + esc(d) + '"' + (t.difficulty === d ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('') +
    '</select></label>' +
    '</div>' +
    '<div class="chip-row">' +
    [5, 10, 20, 30].map(function (n) { return '<button class="chip-toggle' + (t.roundSize === n ? ' active' : '') + '" data-quiz-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    adaptiveDifficultyNoteHtml('nfl') +
    rankedToggleHtml('quiz') +
    '<button class="btn-primary" data-quiz-start>Start Round</button>' +
    '</div>';
}
function renderQuizQuestion() {
  var t = state.quiz, q = currentQuizQuestion();
  if (!q) return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz">No questions match those filters. <button class="btn-secondary" data-quiz-setup>Change Filters</button></div>';
  var answered = t.answeredIndex !== null;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz">' + modeToolbarHtml('quiz', t.ranked) +
    broadcastScorebugHtml([['QUESTION', (t.index + 1) + '/' + t.queue.length], ['CORRECT', t.correctCount], ['LEAGUE', 'NFL']]) +
    quizProgressRowHtml('Question ' + (t.index + 1) + ' of ' + t.queue.length + ' &middot; ' + esc(q.category) + ' &middot; ' + esc(q.difficulty), t.index, t.queue.length) +
    '<section class="stadium-question-card"><span class="stadium-question-kicker">' + esc(q.category) + '</span><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-quiz-answer="' + i + '"') + '>' +
        '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span>' + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? broadcastCallHtml(t.answeredIndex === q.correctIndex) + '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-quiz-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
// Shared by Quiz and CFB Quiz's result screens — both track missed questions
// in the exact same shape (see pickQuizAnswer/pickCfbAnswer), same idea as
// Blitz's inline "Missed:" list and Silhouette's, just with the correct
// answer shown alongside since these are multiple-choice, not free-typed.
function quizMissedReviewHtml(missed) {
  if (!missed.length) return '';
  return '<div class="quiz-missed-review">' +
    '<div class="quiz-missed-review-title">Review missed questions (' + missed.length + ')</div>' +
    missed.map(function (m) {
      return '<div class="quiz-missed-row">' +
        '<div class="quiz-missed-question">' + esc(m.question) + '</div>' +
        '<div class="quiz-missed-answer wrong">' + icon('xMark') + ' Your answer: ' + esc(m.options[m.pickedIndex]) + '</div>' +
        '<div class="quiz-missed-answer correct">' + icon('check') + ' Correct answer: ' + esc(m.options[m.correctIndex]) + '</div>' +
        '</div>';
    }).join('') +
    '</div>';
}
function renderQuizSummary() {
  var t = state.quiz, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz">' +
    broadcastResultHtml('FINAL · NFL QUIZ', pct + '%', t.correctCount + ' / ' + t.queue.length + ' correct', pct >= 80) +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-quiz-again>Play Again</button>' +
    '<button class="btn-secondary" data-share="quiz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-quiz-setup>Change Filters</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml(null) + '</div>';
}
function renderQuizScreen() {
  var t = state.quiz;
  if (t.screen === 'question') return renderQuizQuestion();
  if (t.screen === 'summary') return renderQuizSummary();
  return renderQuizSetup();
}

/* ============================== x's & o's ==============================
   Same engine as Quiz/CFB Quiz (data/xso.js's XSO_DATA is authored in the
   identical {id, category, difficulty, question, options[4], correctIndex,
   notes} shape), but the content itself is different in kind, not just
   league: every question tests scheme/strategy (formations, coverages,
   blocking, route concepts) instead of history/records/facts, which is why
   this is its own mode rather than a 17th Quiz category. Deliberately not
   part of LEAGUE_MODES.nfl/.cfb — the content isn't NFL- or CFB-specific
   (an Under Center formation or a Cover 3 shell means the same thing in
   both), so it gets its own standalone section on Home instead of living
   inside either league's mode grid or dropdown picker (see xsoCardHtml()
   and renderHome() below), same non-LEAGUE_MODES treatment Study/Friends/
   H2H already get. Also doubles as The Film Room's Concepts Almanac
   section content (see LEARN_SECTIONS) via the same reuse pattern QUIZ/CFB
   already have for their own Trivia Almanacs — one data file, two uses. */
function xsoCategories() { return Array.from(new Set(XSO.map(function (q) { return q.category; }))).sort(); }
function xsoDifficulties() { return Array.from(new Set(XSO.map(function (q) { return q.difficulty; }))).sort(); }
function xsoPool(category, difficulty) {
  return XSO.filter(function (q) {
    return (!category || q.category === category) && (!difficulty || q.difficulty === difficulty);
  });
}
function currentXsoQuestion() {
  var id = state.xso.queue[state.xso.index];
  return XSO.find(function (q) { return q.id === id; });
}
function startXsoRound(category, difficulty, roundSize) {
  beginProgressSession('xso');
  var pool = xsoPool(category, difficulty);
  var ids = drawNoRepeat('xso_' + (category || 'all') + '_' + (difficulty || 'all'), pool.map(function (q) { return q.id; }), roundSize);
  state.xso = { screen: 'question', category: category, difficulty: difficulty, roundSize: roundSize, queue: ids, index: 0, correctCount: 0, answeredIndex: null, missed: [], ranked: state.rankedPref.xso !== false };
  renderAll();
}
function pickXsoAnswer(i) {
  if (state.xso.answeredIndex !== null) return;
  state.xso.answeredIndex = i;
  var q = currentXsoQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) state.xso.correctCount++;
  else if (q) state.xso.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i });
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextXsoQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  if (state.xso.index + 1 >= state.xso.queue.length) {
    state.xso.screen = 'summary';
    finishXsoRound();
  } else {
    state.xso.index++;
    state.xso.answeredIndex = null;
  }
  renderAll();
}
function finishXsoRound() {
  var pct = Math.round(100 * state.xso.correctCount / state.xso.queue.length);
  if (state.xso.ranked !== false) {
    var st = state.stats.xso;
    st.correctTotal += state.xso.correctCount;
    st.questionsTotal += state.xso.queue.length;
    st.roundsPlayed++;
    if (pct > st.bestPct) st.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    state.xso.ratingDelta = lastRatingDelta;
    pushLeaderboard('xso', { correctTotal: st.correctTotal, questionsTotal: st.questionsTotal, roundsPlayed: st.roundsPlayed, bestPct: st.bestPct });
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}
function playXsoAgain() { startXsoRound(state.xso.category, state.xso.difficulty, state.xso.roundSize); }
function xsoBackToSetup() { state.xso.screen = 'setup'; renderAll(); }

function renderXsoSetup() {
  var t = state.xso;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--scheme">' +
    broadcastMarqueeHtml('THE PLAYBOOK · SCHEME CHALLENGE', 'X’S & O’S', 'Read the formation. Know the coverage. Make the call.') +
    '<p class="mode-desc">Formations, coverages, blocking, and route concepts. New to the playbook? Start on Easy or Medium.</p>' +
    '<div class="field-row">' +
    '<label>Category<select id="xso-cat"><option value="">All categories</option>' +
    xsoCategories().map(function (c) { return '<option value="' + esc(c) + '"' + (t.category === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') +
    '</select></label>' +
    '<label>Difficulty<select id="xso-diff"><option value="">All difficulties</option>' +
    xsoDifficulties().map(function (d) { return '<option value="' + esc(d) + '"' + (t.difficulty === d ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('') +
    '</select></label>' +
    '</div>' +
    '<div class="chip-row">' +
    [5, 10, 20, 30].map(function (n) { return '<button class="chip-toggle' + (t.roundSize === n ? ' active' : '') + '" data-xso-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    rankedToggleHtml('xso') +
    '<button class="btn-primary" data-xso-start>Start Round</button>' +
    '</div>';
}
function renderXsoQuestion() {
  var t = state.xso, q = currentXsoQuestion();
  if (!q) return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--scheme">No questions match those filters. <button class="btn-secondary" data-xso-setup>Change Filters</button></div>';
  var answered = t.answeredIndex !== null;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--scheme">' + modeToolbarHtml('xso', t.ranked) +
    broadcastScorebugHtml([['QUESTION', (t.index + 1) + '/' + t.queue.length], ['CORRECT', t.correctCount], ['DESK', 'THE PLAYBOOK']]) +
    '<div class="quiz-progress">Question ' + (t.index + 1) + ' of ' + t.queue.length + ' &middot; ' + esc(q.category) + ' &middot; ' + esc(q.difficulty) + '</div>' +
    '<section class="stadium-question-card"><span class="stadium-question-kicker">' + esc(q.category) + '</span><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-xso-answer="' + i + '"') + '>' +
        '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span>' + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? broadcastCallHtml(t.answeredIndex === q.correctIndex) + '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-xso-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderXsoSummary() {
  var t = state.xso, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--scheme">' +
    broadcastResultHtml('FINAL · THE PLAYBOOK', pct + '%', t.correctCount + ' / ' + t.queue.length + ' correct', pct >= 80) +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-xso-again>Play Again</button>' +
    '<button class="btn-secondary" data-share="xso">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-xso-setup>Change Filters</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderXsoScreen() {
  var t = state.xso;
  if (t.screen === 'question') return renderXsoQuestion();
  if (t.screen === 'summary') return renderXsoSummary();
  return renderXsoSetup();
}

/* ============================== college football quiz ============================== */
function cfbCategories() { return Array.from(new Set(CFB.map(function (q) { return q.category; }))).sort(); }
function cfbDifficulties() { return Array.from(new Set(CFB.map(function (q) { return q.difficulty; }))).sort(); }
function cfbPool(category, difficulty) {
  return CFB.filter(function (q) {
    return (!category || q.category === category) && (!difficulty || q.difficulty === difficulty);
  });
}
function currentCfbQuestion() {
  var id = state.cfbQuiz.queue[state.cfbQuiz.index];
  return CFB.find(function (q) { return q.id === id; });
}
function startCfbQuizRound(category, difficulty, roundSize) {
  beginProgressSession('cfbQuiz');
  var pool = cfbPool(category, difficulty);
  if (typeof filterFreshQuestions === 'function') {
    var freshPool = filterFreshQuestions(pool, 'cfb', 70);
    if (freshPool.length >= Math.min(roundSize, pool.length)) pool = freshPool;
  }
  var ids = drawGlobalNoRepeatQuestions('cfbquiz_' + (category || 'all') + '_' + (difficulty || 'all'), pool, roundSize, 'cfb', difficulty);
  state.cfbQuiz = { screen: 'question', category: category, difficulty: difficulty, roundSize: roundSize, queue: ids, index: 0, correctCount: 0, answeredIndex: null, missed: [], ranked: state.rankedPref.cfbQuiz !== false };
  renderAll();
}
function pickCfbAnswer(i) {
  if (state.cfbQuiz.answeredIndex !== null) return;
  state.cfbQuiz.answeredIndex = i;
  var q = currentCfbQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) { state.cfbQuiz.correctCount++; if (q) removeFromMissedPool('cfb', q.id); }
  else if (q) { state.cfbQuiz.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i }); addToMissedPool('cfb', q.id); }
  if (q) {
    recordKnowledgeAnswer('cfb', q.category || 'General', !!isCorrect);
    if (typeof rememberContentQuestion === 'function') rememberContentQuestion(q, 'cfb', 'cfbQuiz');
  }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextCfbQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  if (state.cfbQuiz.index + 1 >= state.cfbQuiz.queue.length) {
    state.cfbQuiz.screen = 'summary';
    finishCfbQuizRound();
  } else {
    state.cfbQuiz.index++;
    state.cfbQuiz.answeredIndex = null;
  }
  renderAll();
}
function finishCfbQuizRound() {
  var pct = Math.round(100 * state.cfbQuiz.correctCount / state.cfbQuiz.queue.length);
  if (state.cfbQuiz.ranked !== false) {
    var st = state.stats.cfbQuiz;
    st.correctTotal += state.cfbQuiz.correctCount;
    st.questionsTotal += state.cfbQuiz.queue.length;
    st.roundsPlayed++;
    if (pct > st.bestPct) st.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    state.cfbQuiz.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbQuiz', { correctTotal: st.correctTotal, questionsTotal: st.questionsTotal, roundsPlayed: st.roundsPlayed, bestPct: st.bestPct });
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}
function playCfbAgain() { startCfbQuizRound(state.cfbQuiz.category, state.cfbQuiz.difficulty, state.cfbQuiz.roundSize); }
function cfbBackToSetup() { state.cfbQuiz.screen = 'setup'; renderAll(); }

function renderCfbSetup() {
  var t = state.cfbQuiz;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--cfb">' +
    broadcastMarqueeHtml('CFB · THE KNOWLEDGE DESK', 'MAKE THE CALL', 'Pick your category. Set your difficulty. Own the round.') +
    '<div class="field-row">' +
    '<label>Category<select id="cfb-cat"><option value="">All categories</option>' +
    cfbCategories().map(function (c) { return '<option value="' + esc(c) + '"' + (t.category === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') +
    '</select></label>' +
    '<label>Difficulty<select id="cfb-diff"><option value="">All difficulties</option>' +
    cfbDifficulties().map(function (d) { return '<option value="' + esc(d) + '"' + (t.difficulty === d ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('') +
    '</select></label>' +
    '</div>' +
    '<div class="chip-row">' +
    [5, 10, 20, 30].map(function (n) { return '<button class="chip-toggle' + (t.roundSize === n ? ' active' : '') + '" data-cfb-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    adaptiveDifficultyNoteHtml('cfb') +
    rankedToggleHtml('cfbQuiz') +
    '<button class="btn-primary" data-cfb-start>Start Round</button>' +
    '</div>';
}
function renderCfbQuestion() {
  var t = state.cfbQuiz, q = currentCfbQuestion();
  if (!q) return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--cfb">No questions match those filters. <button class="btn-secondary" data-cfb-setup>Change Filters</button></div>';
  var answered = t.answeredIndex !== null;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--cfb">' + modeToolbarHtml('cfbQuiz', t.ranked) +
    broadcastScorebugHtml([['QUESTION', (t.index + 1) + '/' + t.queue.length], ['CORRECT', t.correctCount], ['LEAGUE', 'CFB']]) +
    quizProgressRowHtml('Question ' + (t.index + 1) + ' of ' + t.queue.length + ' &middot; ' + esc(q.category) + ' &middot; ' + esc(q.difficulty), t.index, t.queue.length) +
    '<section class="stadium-question-card"><span class="stadium-question-kicker">' + esc(q.category) + '</span><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-cfb-answer="' + i + '"') + '>' +
        '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span>' + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? broadcastCallHtml(t.answeredIndex === q.correctIndex) + '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-cfb-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderCfbSummary() {
  var t = state.cfbQuiz, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--quiz broadcast-finish--cfb">' +
    broadcastResultHtml('FINAL · CFB QUIZ', pct + '%', t.correctCount + ' / ' + t.queue.length + ' correct', pct >= 80) +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-again>Play Again</button>' +
    '<button class="btn-secondary" data-share="cfbQuiz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-cfb-setup>Change Filters</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml(null) + '</div>';
}
function renderCfbScreen() {
  var t = state.cfbQuiz;
  if (t.screen === 'question') return renderCfbQuestion();
  if (t.screen === 'summary') return renderCfbSummary();
  return renderCfbSetup();
}

/* ============================== study mode ==============================
   Not a real 13th game mode (not in LEAGUE_MODES, no leaderboard entry, no
   rating impact) — a small remedial-practice tool built entirely on top of
   the missed-question pool above: pulls a round from whichever league's
   pool you pick, reusing the exact same quiz-question/quiz-options/quiz-
   feedback markup Quiz/CFB Quiz already use. Answering correctly here (or
   anywhere else) removes a question from the pool — "mastering" it — so
   this naturally shrinks over time instead of being a fixed drill set.
   Deliberately not ranked: this is about fixing weak spots, not chasing a
   score, so it never touches Football Rating or the leaderboard. */
var STUDY_ROUND_SIZE = 15;
function studyQuestionIds(league) {
  var pool = getMissedPool(league);
  var rng = mulberry32(Math.floor(Math.random() * 2147483647));
  return seededShuffle(pool, rng).slice(0, STUDY_ROUND_SIZE);
}
function currentStudyQuestion() {
  var s = state.study;
  var id = s.queue[s.index];
  var source = s.league === 'nfl' ? QUIZ : CFB;
  return source.find(function (q) { return q.id === id; });
}
function startStudy(league) {
  var ids = studyQuestionIds(league);
  if (!ids.length) return;
  state.study = { screen: 'question', league: league, queue: ids, index: 0, correctCount: 0, masteredCount: 0, answeredIndex: null };
  state.screen = 'study';
  renderAll();
}
function pickStudyAnswer(i) {
  var s = state.study;
  if (s.answeredIndex !== null) return;
  s.answeredIndex = i;
  var q = currentStudyQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) {
    s.correctCount++;
    s.masteredCount++;
    removeFromMissedPool(s.league, q.id);
  }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextStudyQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  var s = state.study;
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; renderAll(); return; }
  s.index++;
  s.answeredIndex = null;
  renderAll();
}
function renderStudySetup() {
  var nflPool = getMissedPool('nfl'), cfbPool = getMissedPool('cfb');
  var nflWeak = weakCategories('nfl').slice(0, 3), cfbWeak = weakCategories('cfb').slice(0, 3);
  if (!nflPool.length && !cfbPool.length) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('brain') + ' Study</h2>' +
      '<p class="mode-desc">Nothing to study yet — play a round of Quiz or CFB Quiz, and any question you miss shows up here so you can drill it later. Get it right anywhere and it’s marked mastered.</p>' +
      '</div>';
  }
  var leagueSectionHtml = function (label, league, pool, weak) {
    if (!pool.length) return '';
    return '<div class="about-section">' +
      '<h3 class="about-heading">' + esc(label) + ' — ' + pool.length + ' to review</h3>' +
      (weak.length ? '<p class="mode-desc">Weakest categories: ' + weak.map(function (w) { return esc(w.category) + ' (' + w.count + ')'; }).join(', ') + '</p>' : '') +
      '<button class="btn-primary" data-study-start="' + league + '">Study ' + Math.min(STUDY_ROUND_SIZE, pool.length) + ' Question' + (Math.min(STUDY_ROUND_SIZE, pool.length) === 1 ? '' : 's') + '</button>' +
      '</div>';
  };
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('brain') + ' Study</h2>' +
    '<p class="mode-desc">Every question you’ve missed in Quiz or CFB Quiz, ready to drill again. Doesn’t affect your Football Rating or the leaderboard — this is just for you.</p>' +
    leagueSectionHtml('NFL', 'nfl', nflPool, nflWeak) +
    leagueSectionHtml('College Football', 'cfb', cfbPool, cfbWeak) +
    '</div>';
}
function renderStudyQuestion() {
  var s = state.study, q = currentStudyQuestion();
  if (!q) return renderStudySetup();
  var answered = s.answeredIndex !== null;
  return '<div class="panel">' + modeToolbarHtml('study') +
    '<div class="quiz-progress">Study &middot; ' + (s.league === 'nfl' ? 'NFL' : 'College Football') + ' &middot; Question ' + (s.index + 1) + ' of ' + s.queue.length + ' &middot; ' + esc(q.category) + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-study-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (s.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct — mastered! It won’t show up here again unless you miss it later.</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect — still in your review pool.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-study-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderStudySummary() {
  var s = state.study;
  var remaining = getMissedPool(s.league).length;
  return '<div class="panel">' +
    '<h2 class="panel-title">Study Session Complete</h2>' +
    '<div class="summary-score">' + s.correctCount + ' / ' + s.queue.length + ' correct</div>' +
    '<div class="summary-note">' + s.masteredCount + ' question' + (s.masteredCount === 1 ? '' : 's') + ' mastered this session &middot; ' + remaining + ' still in your ' + (s.league === 'nfl' ? 'NFL' : 'College Football') + ' review pool.</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-study-start="' + s.league + '">Keep Studying</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderStudyScreen() {
  if (!state.study) return renderStudySetup();
  if (state.study.screen === 'summary') return renderStudySummary();
  if (state.study.screen === 'question') return renderStudyQuestion();
  return renderStudySetup();
}
// Standalone Home card for X's & O's — not part of LEAGUE_MODES.nfl/.cfb
// since the content itself (formations, coverages, blocking schemes) isn't
// NFL- or CFB-specific, same "own card, own screen, not in either league's
// mode grid" treatment Study/Friends/H2H already get. Always visible
// (unlike studyCardHtml(), which only shows once there's something to
// review) since this is a real standalone mode from the first visit on,
// not a follow-up nudge.
function xsoCardHtml() {
  return discoverRowHtml('xso', 'target', "X's & O's", 'Formations, coverages & blocking schemes', 'xso-card');
}
function studyCardHtml() {
  if (!state.name) return '';
  var total = getMissedPool('nfl').length + getMissedPool('cfb').length;
  if (!total) return '';
  return discoverRowHtml('study', 'brain', 'Study', total + ' question' + (total === 1 ? '' : 's') + ' to review');
}

/* ============================== immaculate grid ============================== */
// A light nudge, not a hard filter: unlike CFB Grid's weighted pick (see
// cfbGridWeightOf), NFL Grid's row selection is a plain shuffle, so the
// simplest way to bias it without restructuring that is a probabilistic
// force-include — most rounds behave exactly as before, but there's a real
// (not guaranteed) chance the favorite team's own criterion gets slotted in
// as one of the 3 rows instead of being left to a 3-in-32 shuffle draw.
var GRID_FAVORITE_TEAM_BIAS = 0.3;
function buildGridAttempt() {
  var teamCritPool = GRID_CRITERIA.team.slice();
  var favId = getFavoriteTeams().nfl;
  var rows;
  if (favId && Math.random() < GRID_FAVORITE_TEAM_BIAS) {
    var favCrit = teamCritPool.find(function (c) { return c.team === favId; });
    rows = favCrit ? [favCrit].concat(shuffle(teamCritPool.filter(function (c) { return c.team !== favId; })).slice(0, 2)) : shuffle(teamCritPool).slice(0, 3);
  } else {
    rows = shuffle(teamCritPool).slice(0, 3);
  }
  var usedIds = rows.map(function (c) { return c.id; });
  var restPool = shuffle(GRID_CRITERIA.all.filter(function (c) { return usedIds.indexOf(c.id) === -1; }));
  var cols = restPool.slice(0, 3);
  var cells = [], validCount = 0;
  for (var r = 0; r < 3; r++) {
    for (var c = 0; c < 3; c++) {
      var rowC = rows[r], colC = cols[c];
      var matches = GRID_PLAYERS.filter(function (p) { return rowC.test(p) && colC.test(p); });
      if (matches.length > 0) validCount++;
      cells.push({ r: r, c: c, matches: matches, guess: null, correct: null, points: 0 });
    }
  }
  return { rows: rows, cols: cols, cells: cells, validCount: validCount };
}
function buildGrid() {
  var best = null;
  for (var i = 0; i < 250; i++) {
    var attempt = buildGridAttempt();
    if (attempt.validCount === 9) return attempt;
    if (!best || attempt.validCount > best.validCount) best = attempt;
  }
  return best;
}
function startGridRound() {
  beginProgressSession('grid');
  // UI/UX upgrade pass: a fresh round is never "today's Daily Reads"
  // unless completeDailyChallengeFrom() sets this again -- clears any
  // stale flag from an earlier, unrelated daily completion this session so
  // dailyCompletionBannerHtml() can't show on a later non-daily round.
  state.justCompletedDaily = null;
  var g = buildGrid();
  state.grid = { rows: g.rows, cols: g.cols, cells: g.cells, usedPlayers: [], activeIndex: null, input: '', screen: 'board', answeredCount: 0, totalScore: 0, lastError: '', ranked: state.rankedPref.grid !== false };
  state.screen = 'grid';
  renderAll();
}
function selectGridCell(idx) {
  var g = state.grid;
  if (!g || g.screen !== 'board') return;
  if (g.cells[idx].correct !== null) return;
  g.activeIndex = idx;
  g.input = '';
  g.lastError = '';
  renderAll();
}
function submitGridGuess() {
  var g = state.grid;
  if (!g || g.activeIndex === null) return;
  var cell = g.cells[g.activeIndex];
  var norm = normName(g.input);
  if (!norm) return;
  var player = GRID_PLAYERS.find(function (p) { return normName(p.name) === norm; });
  if (player && g.usedPlayers.indexOf(player.name) !== -1) {
    g.lastError = 'Already used ' + player.name + ' on this board — try someone else.';
    renderAll();
    return;
  }
  g.lastError = '';
  var isMatch = !!player && cell.matches.some(function (m) { return m.name === player.name; });
  cell.guess = player ? player.name : g.input;
  cell.correct = isMatch;
  playSound(isMatch ? 'correct' : 'wrong');
  if (isMatch) {
    cell.points = Math.max(10, Math.round(100 / cell.matches.length));
    g.totalScore += cell.points;
    g.usedPlayers.push(player.name);
  } else {
    cell.points = 0;
  }
  g.answeredCount++;
  g.activeIndex = null;
  g.input = '';
  if (g.answeredCount >= 9) {
    g.screen = 'summary';
    finishGridRound();
  }
  renderAll();
}
function finishGridRound() {
  var g = state.grid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  if (g.ranked !== false) {
    var st = state.stats.grid;
    st.gamesPlayed++;
    if (g.totalScore > st.bestScore) st.bestScore = g.totalScore;
    if (correctCells === 9) st.cleanSweeps++;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correctCells / 9);
    g.ratingDelta = lastRatingDelta;
    pushLeaderboard('grid', { bestScore: st.bestScore, gamesPlayed: st.gamesPlayed, cleanSweeps: st.cleanSweeps });
  }
  completeDailyChallengeFrom('grid', correctCells + ' / 9 squares', 100 * correctCells / 9);
  h2hSubmitModeResult('grid', correctCells, 9);
  playSound('complete');
}

function renderGridSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--grid game-intro game-intro-grid">' +
    '<div class="game-intro-icon">' + icon('grid') + '</div><div class="game-intro-eyebrow">9 squares. No repeats.</div>' +
    '<h2 class="game-intro-title">Immaculate Grid</h2>' +
    '<p class="game-intro-copy">Match a player to both clues. You only get one shot at each square, and the names nobody else thinks of score the most.</p>' +
    '<div class="game-intro-features"><span>' + icon('target') + '<b>3×3</b> fresh grid</span><span>' + icon('lock') + '<b>One guess</b> per square</span><span>' + icon('trophy') + '<b>Rarity</b> scoring</span></div>' +
    '<div class="grid-intro-preview" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>' +
    rankedToggleHtml('grid') +
    '<button class="btn-primary game-intro-cta" data-grid-start>Deal My Grid ' + icon('arrowRight') + '</button>' +
    '</div>';
}
// Team/school badge colors are real per-team colors (32 NFL + 48 CFB), so a
// fixed white text color doesn't have reliable WCAG contrast — some (Rams
// gold, Chargers powder blue) are too light for white text to read well.
// Pick whichever of white/near-black actually contrasts better against each
// specific badge color, same relative-luminance formula WCAG itself uses.
function pickBadgeTextColor(hex) {
  hex = String(hex || '').replace('#', '');
  if (hex.length !== 6) return '#fff';
  var r = parseInt(hex.substr(0, 2), 16) / 255;
  var g = parseInt(hex.substr(2, 2), 16) / 255;
  var b = parseInt(hex.substr(4, 2), 16) / 255;
  var lin = function (v) { return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  var L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  var contrastWithWhite = 1.05 / (L + 0.05);
  var contrastWithBlack = (L + 0.05) / 0.05;
  return contrastWithWhite >= contrastWithBlack ? '#ffffff' : '#0b1220';
}
// Grid scoring (Math.max(10, Math.round(100 / cell.matches.length)) in
// submitGridGuess/submitCfbGridGuess) IS already rarity-based — a square
// with only 3 possible correct players scores way more than one with 80 —
// but that was only ever surfaced as a bare point number, with nothing
// telling you WHY 47 points is impressive and 10 isn't. This turns the same
// pool-size math already being computed into an actual visible tier, live,
// the moment a square is answered — same idea as the real Immaculate
// Grid's rarity %, just tiered instead of a raw percentage since this pool
// size ranges from single digits to hundreds depending on the criteria.
function gridRarityTier(poolSize) {
  if (poolSize <= 3) return { label: 'Immaculate', cls: 'legendary' };
  if (poolSize <= 8) return { label: 'Rare', cls: 'rare' };
  if (poolSize <= 20) return { label: 'Uncommon', cls: 'uncommon' };
  return { label: 'Common', cls: 'common' };
}
function gridRarityTagHtml(poolSize) {
  var t = gridRarityTier(poolSize);
  return '<span class="grid-rarity rarity-' + t.cls + '">' + esc(t.label) + '</span>';
}
// A real 9/9 clean sweep is rare enough (this app tracks it as its own
// "Perfect Grid" badge already — see BADGES/cleanSweeps) that it deserves
// more than the same quiet summary screen as a 5/9. One big banner, one
// bigger confetti burst (double the size of the existing per-square burst
// via .grid-immaculate-confetti), one word.
function gridImmaculateBannerHtml(correctCells) {
  if (correctCells !== 9) return '';
  return '<div class="grid-immaculate-banner">' + brandWatermarkHtml() + '<div class="grid-immaculate-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">IMMACULATE!</h2></div>';
}
function criteriaHeaderHtml(c) {
  if (c.type === 'team') {
    var color = (window.GRID_TEAM_COLORS && window.GRID_TEAM_COLORS[c.team]) || '#444';
    return '<div class="team-badge" style="background:' + color + ';color:' + pickBadgeTextColor(color) + '">' + esc(c.team) + '</div><div>' + esc(c.label) + '</div>';
  }
  if (c.type === 'school') {
    var schoolColor = (window.CFB_GRID_SCHOOL_COLORS && window.CFB_GRID_SCHOOL_COLORS[c.school]) || '#444';
    var schoolCode = (window.CFB_GRID_SCHOOL_CODES && window.CFB_GRID_SCHOOL_CODES[c.school]) || c.school;
    return '<div class="team-badge" style="background:' + schoolColor + ';color:' + pickBadgeTextColor(schoolColor) + '">' + esc(schoolCode) + '</div><div>' + esc(c.label) + '</div>';
  }
  return '<div>' + esc(c.label) + '</div>';
}
function renderGridBoard() {
  var g = state.grid;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--grid">' + modeToolbarHtml('grid', g.ranked) +
    broadcastGridHudHtml(g, false) +
    '<div class="game-progress"><span style="width:' + Math.round(g.answeredCount / 9 * 100) + '%"></span></div>' +
    '<div class="grid-stage"><div class="grid-table">' +
    '<div class="grid-cell grid-corner" aria-hidden="true">' + icon('goalpost') + '</div>';
  g.cols.forEach(function (c) { html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(c) + '</div>'; });
  for (var r = 0; r < 3; r++) {
    html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(g.rows[r]) + '</div>';
    for (var c = 0; c < 3; c++) {
      var idx = r * 3 + c, cell = g.cells[idx];
      var cls = 'grid-cell grid-square';
      var content = '';
      if (cell.correct === true) { cls += ' correct'; content = '<div class="grid-answer">' + esc(cell.guess) + '</div><div class="grid-points">+' + cell.points + '</div>' + gridRarityTagHtml(cell.matches.length); }
      else if (cell.correct === false) { cls += ' wrong'; content = '<div class="grid-answer">' + esc(cell.guess || '—') + '</div><div class="grid-points">' + icon('close') + '</div>'; }
      else if (g.activeIndex === idx) { cls += ' active'; content = '<div class="grid-hint">Type below ↓</div>'; }
      else { content = '<div class="grid-hint">Tap to answer</div>'; }
      html += '<button class="' + cls + '" data-grid-cell="' + idx + '" ' + (cell.correct !== null ? 'disabled' : '') + '>' + content + '</button>';
    }
  }
  html += '</div></div>';
  if (g.activeIndex !== null) {
    html += broadcastGridSelectionHtml(g) + '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="grid-input" autocomplete="off" placeholder="Type a player name…" value="' + esc(g.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="grid-input-typeahead" />' +
      '<div id="grid-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-grid-submit>Submit</button>' +
      (g.lastError ? '<div class="grid-error" role="alert">' + esc(g.lastError) + '</div>' : '') +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderGridSummary() {
  var g = state.grid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--grid">' +
    broadcastResultHtml('FINAL · NFL GRID', correctCells + '/9', g.totalScore + ' rarity points', correctCells === 9) +
    gridImmaculateBannerHtml(correctCells) +
    '<div class="summary-score">' + correctCells + ' / 9 correct &middot; ' + g.totalScore + ' pts</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="grid-recap">';
  g.cells.forEach(function (cell) {
    var rowLabel = g.rows[cell.r].label, colLabel = g.cols[cell.c].label;
    var pool = cell.matches.map(function (m) { return m.name; });
    var poolText = pool.slice(0, 6).join(', ') + (pool.length > 6 ? ', +' + (pool.length - 6) + ' more' : '');
    html += '<div class="grid-recap-row ' + (cell.correct ? 'correct' : 'wrong') + '">' +
      '<b>' + esc(rowLabel) + ' × ' + esc(colLabel) + ':</b> your answer — ' + esc(cell.guess || '(none)') +
      '<div class="grid-recap-pool">' + gridRarityTagHtml(pool.length) + ' Valid answers (' + pool.length + '): ' + esc(poolText) + '</div></div>';
  });
  html += '</div><div class="btn-row">' +
    '<button class="btn-primary" data-grid-again>New Grid</button>' +
    '<button class="btn-secondary" data-share="grid">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('grid') + '</div>';
  return html;
}
function renderGridScreen() {
  if (!state.grid) return renderGridSetup();
  if (state.grid.screen === 'summary') return renderGridSummary();
  return renderGridBoard();
}

/* ============================== college football immaculate grid ============================== */
function weightedPickWithoutReplacement(items, weightFn, n) {
  var pool = items.slice();
  var picked = [];
  for (var k = 0; k < n && pool.length; k++) {
    var total = 0, i;
    for (i = 0; i < pool.length; i++) total += weightFn(pool[i]);
    var r = Math.random() * total, acc = 0, idx = pool.length - 1;
    for (i = 0; i < pool.length; i++) {
      acc += weightFn(pool[i]);
      if (r <= acc) { idx = i; break; }
    }
    picked.push(pool[idx]);
    pool.splice(idx, 1);
  }
  return picked;
}
// Weight every criterion — rows and columns alike — by how many players it actually
// matches, rather than a crude "this type is usually sparse" guess. Schools/awards/etc.
// with few matching players become proportionally less likely to get picked at all,
// so thin criteria (a newly-added school with 2 players, a rare award) still show up
// for variety but don't dominate and tank how often a fully solvable grid gets dealt.
// Memoized since CFB_GRID_PLAYERS/CFB_GRID_CRITERIA never change at runtime.
var cfbGridCriteriaWeight = null;
function cfbGridWeightOf(c) {
  if (!cfbGridCriteriaWeight) {
    cfbGridCriteriaWeight = {};
    CFB_GRID_CRITERIA.all.forEach(function (crit) {
      cfbGridCriteriaWeight[crit.id] = CFB_GRID_PLAYERS.filter(crit.test).length;
    });
  }
  var w = Math.min(1, (cfbGridCriteriaWeight[c.id] || 0) / 10) + 0.05;
  // A light nudge, not a hard filter (per the favorite-team feature's own
  // design goal): multiplies rather than replaces the existing depth-based
  // weight, so a favorite school with very few valid grid matches still
  // can't get force-picked into a mostly-broken grid — it's just noticeably
  // more likely to show up than any other equally-deep school would be.
  var favSchool = getFavoriteTeams().cfb;
  if (favSchool && c.type === 'school' && c.school === favSchool) w *= 6;
  return w;
}
function buildCfbGridAttempt() {
  var rows = weightedPickWithoutReplacement(CFB_GRID_CRITERIA.team, cfbGridWeightOf, 3);
  var usedIds = rows.map(function (c) { return c.id; });
  var restPool = CFB_GRID_CRITERIA.all.filter(function (c) { return usedIds.indexOf(c.id) === -1; });
  var cols = weightedPickWithoutReplacement(restPool, cfbGridWeightOf, 3);
  var cells = [], validCount = 0;
  for (var r = 0; r < 3; r++) {
    for (var c = 0; c < 3; c++) {
      var rowC = rows[r], colC = cols[c];
      var matches = CFB_GRID_PLAYERS.filter(function (p) { return rowC.test(p) && colC.test(p); });
      if (matches.length > 0) validCount++;
      cells.push({ r: r, c: c, matches: matches, guess: null, correct: null, points: 0 });
    }
  }
  return { rows: rows, cols: cols, cells: cells, validCount: validCount };
}
function buildCfbGrid() {
  var best = null;
  for (var i = 0; i < 1200; i++) {
    var attempt = buildCfbGridAttempt();
    if (attempt.validCount === 9) return attempt;
    if (!best || attempt.validCount > best.validCount) best = attempt;
  }
  return best;
}
function startCfbGridRound() {
  beginProgressSession('cfbGrid');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  var g = buildCfbGrid();
  state.cfbGrid = { rows: g.rows, cols: g.cols, cells: g.cells, usedPlayers: [], activeIndex: null, input: '', screen: 'board', answeredCount: 0, totalScore: 0, lastError: '', ranked: state.rankedPref.cfbGrid !== false };
  state.screen = 'cfbGrid';
  renderAll();
}
function selectCfbGridCell(idx) {
  var g = state.cfbGrid;
  if (!g || g.screen !== 'board') return;
  if (g.cells[idx].correct !== null) return;
  g.activeIndex = idx;
  g.input = '';
  g.lastError = '';
  renderAll();
}
function submitCfbGridGuess() {
  var g = state.cfbGrid;
  if (!g || g.activeIndex === null) return;
  var cell = g.cells[g.activeIndex];
  var norm = normName(g.input);
  if (!norm) return;
  var player = CFB_GRID_PLAYERS.find(function (p) { return normName(p.name) === norm; });
  if (player && g.usedPlayers.indexOf(player.name) !== -1) {
    g.lastError = 'Already used ' + player.name + ' on this board — try someone else.';
    renderAll();
    return;
  }
  g.lastError = '';
  var isMatch = !!player && cell.matches.some(function (m) { return m.name === player.name; });
  cell.guess = player ? player.name : g.input;
  cell.correct = isMatch;
  playSound(isMatch ? 'correct' : 'wrong');
  if (isMatch) {
    cell.points = Math.max(10, Math.round(100 / cell.matches.length));
    g.totalScore += cell.points;
    g.usedPlayers.push(player.name);
  } else {
    cell.points = 0;
  }
  g.answeredCount++;
  g.activeIndex = null;
  g.input = '';
  if (g.answeredCount >= 9) {
    g.screen = 'summary';
    finishCfbGridRound();
  }
  renderAll();
}
function finishCfbGridRound() {
  var g = state.cfbGrid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  if (g.ranked !== false) {
    var st = state.stats.cfbGrid;
    st.gamesPlayed++;
    if (g.totalScore > st.bestScore) st.bestScore = g.totalScore;
    if (correctCells === 9) st.cleanSweeps++;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correctCells / 9);
    g.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbGrid', { bestScore: st.bestScore, gamesPlayed: st.gamesPlayed, cleanSweeps: st.cleanSweeps });
    completeDailyChallengeFrom('cfbGrid', correctCells + ' / 9 squares', 100 * correctCells / 9);
  }
  h2hSubmitModeResult('cfbGrid', correctCells, 9);
  playSound('complete');
}

function renderCfbGridSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--grid broadcast-finish--cfb game-intro game-intro-grid">' +
    '<div class="game-intro-icon">' + icon('grid') + '</div><div class="game-intro-eyebrow">Schools. Awards. Legends.</div>' +
    '<h2 class="game-intro-title">CFB Immaculate Grid</h2>' +
    '<p class="game-intro-copy">Connect college stars to schools, Heismans, and All-America honors. One guess per square, with bigger points for deeper cuts.</p>' +
    '<div class="game-intro-features"><span>' + icon('target') + '<b>3×3</b> fresh grid</span><span>' + icon('lock') + '<b>One guess</b> per square</span><span>' + icon('trophy') + '<b>Rarity</b> scoring</span></div>' +
    '<div class="grid-intro-preview" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>' +
    rankedToggleHtml('cfbGrid') +
    '<button class="btn-primary game-intro-cta" data-cfb-grid-start>Deal My Grid ' + icon('arrowRight') + '</button>' +
    '</div>';
}
function renderCfbGridBoard() {
  var g = state.cfbGrid;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--grid broadcast-finish--cfb">' + modeToolbarHtml('cfbGrid', g.ranked) +
    broadcastGridHudHtml(g, true) +
    '<div class="game-progress"><span style="width:' + Math.round(g.answeredCount / 9 * 100) + '%"></span></div>' +
    '<div class="grid-stage"><div class="grid-table">' +
    '<div class="grid-cell grid-corner" aria-hidden="true">' + icon('goalpost') + '</div>';
  g.cols.forEach(function (c) { html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(c) + '</div>'; });
  for (var r = 0; r < 3; r++) {
    html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(g.rows[r]) + '</div>';
    for (var c = 0; c < 3; c++) {
      var idx = r * 3 + c, cell = g.cells[idx];
      var cls = 'grid-cell grid-square';
      var content = '';
      if (cell.correct === true) { cls += ' correct'; content = '<div class="grid-answer">' + esc(cell.guess) + '</div><div class="grid-points">+' + cell.points + '</div>' + gridRarityTagHtml(cell.matches.length); }
      else if (cell.correct === false) { cls += ' wrong'; content = '<div class="grid-answer">' + esc(cell.guess || '—') + '</div><div class="grid-points">' + icon('close') + '</div>'; }
      else if (g.activeIndex === idx) { cls += ' active'; content = '<div class="grid-hint">Type below ↓</div>'; }
      else { content = '<div class="grid-hint">Tap to answer</div>'; }
      html += '<button class="' + cls + '" data-cfb-grid-cell="' + idx + '" ' + (cell.correct !== null ? 'disabled' : '') + '>' + content + '</button>';
    }
  }
  html += '</div></div>';
  if (g.activeIndex !== null) {
    html += broadcastGridSelectionHtml(g) + '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="cfb-grid-input" autocomplete="off" placeholder="Type a player name…" value="' + esc(g.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cfb-grid-input-typeahead" />' +
      '<div id="cfb-grid-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-cfb-grid-submit>Submit</button>' +
      (g.lastError ? '<div class="grid-error" role="alert">' + esc(g.lastError) + '</div>' : '') +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderCfbGridSummary() {
  var g = state.cfbGrid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--grid broadcast-finish--cfb">' +
    broadcastResultHtml('FINAL · CFB GRID', correctCells + '/9', g.totalScore + ' rarity points', correctCells === 9) +
    gridImmaculateBannerHtml(correctCells) +
    '<div class="summary-score">' + correctCells + ' / 9 correct &middot; ' + g.totalScore + ' pts</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="grid-recap">';
  g.cells.forEach(function (cell) {
    var rowLabel = g.rows[cell.r].label, colLabel = g.cols[cell.c].label;
    var pool = cell.matches.map(function (m) { return m.name; });
    var poolText = pool.slice(0, 6).join(', ') + (pool.length > 6 ? ', +' + (pool.length - 6) + ' more' : '');
    html += '<div class="grid-recap-row ' + (cell.correct ? 'correct' : 'wrong') + '">' +
      '<b>' + esc(rowLabel) + ' × ' + esc(colLabel) + ':</b> your answer — ' + esc(cell.guess || '(none)') +
      '<div class="grid-recap-pool">' + gridRarityTagHtml(pool.length) + ' Valid answers (' + pool.length + '): ' + esc(poolText) + '</div></div>';
  });
  html += '</div><div class="btn-row">' +
    '<button class="btn-primary" data-cfb-grid-again>New Grid</button>' +
    '<button class="btn-secondary" data-share="cfbGrid">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('cfbGrid') + '</div>';
  return html;
}
function renderCfbGridScreen() {
  if (!state.cfbGrid) return renderCfbGridSetup();
  if (state.cfbGrid.screen === 'summary') return renderCfbGridSummary();
  return renderCfbGridBoard();
}

/* ============================== blitz ============================== */
function normalizeBlitzText(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim(); }
function startBlitz(listId, timerLen) {
  beginProgressSession('blitz');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  var list = BLITZ_LISTS.find(function (l) { return l.id === listId; });
  state.blitz = { listId: listId, list: list, timerLen: timerLen, screen: 'playing', endsAt: Date.now() + timerLen * 1000, timeLeft: timerLen, matched: [], input: '', lastFeedback: '', ranked: state.rankedPref.blitz !== false };
  state.screen = 'blitz';
  stopTimers();
  blitzTimer = setInterval(blitzTick, 250);
  renderAll();
}
function blitzTick() {
  if (!state.blitz || state.blitz.screen !== 'playing') return;
  var remain = (state.blitz.endsAt - Date.now()) / 1000;
  if (remain <= 0) { state.blitz.timeLeft = 0; endBlitz(); return; }
  state.blitz.timeLeft = remain;
  // Patch the timer text directly instead of a full renderAll() — a full
  // DOM rebuild 4x/sec was intermittently eating clicks/keystrokes on the
  // input and Add button.
  var timerEl = document.getElementById('blitz-timer-display');
  if (timerEl) {
    timerEl.textContent = fmtTime(remain);
    // Full Visual + Interactive Redesign pass: real urgency in the final
    // 10 real seconds -- toggled here (not left to a CSS-only always-on
    // animation) since it's driven by the actual remaining time, not a
    // guess.
    timerEl.classList.toggle('blitz-timer-urgent', remain <= 10);
  }
}
function submitBlitzGuess() {
  var b = state.blitz;
  if (!b || b.screen !== 'playing') return;
  var norm = normalizeBlitzText(b.input);
  if (!norm) return;
  var found = null;
  for (var i = 0; i < b.list.answers.length; i++) {
    var a = b.list.answers[i];
    if (b.matched.indexOf(a.answer) !== -1) continue;
    var candidates = [a.answer].concat(a.aliases || []);
    for (var j = 0; j < candidates.length; j++) {
      if (normalizeBlitzText(candidates[j]) === norm) { found = a; break; }
    }
    if (found) break;
  }
  if (found) {
    b.matched.push(found.answer);
    b.lastFeedback = 'correct';
    playSound('correct');
    if (b.matched.length >= b.list.answers.length) { b.input = ''; endBlitz(); return; }
  } else {
    b.lastFeedback = 'miss';
    playSound('wrong');
  }
  b.input = '';
  renderAll();
}
function endBlitz() {
  if (blitzTimer) { clearInterval(blitzTimer); blitzTimer = null; }
  state.blitz.screen = 'results';
  finishBlitzRound();
  renderAll();
}
function finishBlitzRound() {
  var b = state.blitz;
  var pct = 100 * b.matched.length / b.list.answers.length;
  if (b.ranked !== false) {
    var st = state.stats.blitz;
    st.attempts++;
    if (b.matched.length > st.bestMatched) st.bestMatched = b.matched.length;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    b.ratingDelta = lastRatingDelta;
    pushLeaderboard('blitz', { bestMatched: st.bestMatched, attempts: st.attempts });
    completeDailyChallengeFrom('blitz', b.matched.length + ' / ' + b.list.answers.length + ' found', pct);
    h2hSubmitModeResult('blitz', b.matched.length, b.list.answers.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderBlitzSetup() {
  var lists = BLITZ_LISTS;
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Blitz</h2>' +
    '<p class="mode-desc">Type every correct answer you can before time runs out. Nicknames and abbreviations count.</p>' +
    '<div class="blitz-list-picker">' +
    lists.map(function (l) {
      return '<button class="blitz-list-card" data-blitz-list="' + esc(l.id) + '"><b>' + esc(l.title) + '</b><div class="mode-desc">' + esc(l.prompt) + ' (' + l.answers.length + ' answers)</div></button>';
    }).join('') +
    '</div></div>';
}
function renderBlitzTimerPicker(listId) {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + esc(BLITZ_LISTS.find(function (l) { return l.id === listId; }).title) + '</h2>' +
    rankedToggleHtml('blitz') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-blitz-start="' + listId + '" data-blitz-timer="' + n + '">' + n + 's</button>'; }).join('') +
    '</div>' +
    '<button class="btn-secondary" data-blitz-setup>Back</button>' +
    '</div>';
}
function renderBlitzPlaying() {
  var b = state.blitz, total = b.list.answers.length;
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--blitz">' + modeToolbarHtml('blitz', b.ranked) +
    '<div class="classic-broadcast-marquee"><span>NFL · LIGHTNING ROUND</span><strong>' + esc(b.list.title) + '</strong><em>' + esc(b.list.prompt) + '</em></div>' +
    '<div class="blitz-header"><div class="blitz-title">TIME REMAINING</div><div class="blitz-timer" id="blitz-timer-display">' + fmtTime(b.timeLeft) + '</div></div>' +
    '<div class="blitz-progress">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="blitz-input-row">' +
    '<input id="blitz-input" autocomplete="off" placeholder="Type an answer and hit Enter…" value="' + esc(b.input) + '" autofocus />' +
    '<button class="btn-primary" data-blitz-submit>Add</button>' +
    '</div>' +
    (b.lastFeedback === 'miss' ? '<div class="blitz-feedback wrong" aria-live="polite">Not a match — try again.</div>' : '') +
    '<div class="blitz-matched">' + b.matched.map(function (m) { return '<span class="blitz-chip">' + esc(m) + '</span>'; }).join('') + '</div>' +
    '</div>';
}
function renderBlitzResults() {
  var b = state.blitz, total = b.list.answers.length;
  var missed = b.list.answers.filter(function (a) { return b.matched.indexOf(a.answer) === -1; });
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--blitz">' +
    '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">TIME!</h2></div>' +
    '<h2 class="panel-title">NFL Blitz Complete — ' + esc(b.list.title) + '</h2>' +
    '<div class="summary-score">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (a) { return esc(a.answer); }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you got every answer!</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-blitz-list="' + esc(b.listId) + '">Try Another List</button>' +
    '<button class="btn-secondary" data-share="blitz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('blitz') + '</div>';
}
function renderBlitzScreen() {
  var b = state.blitz;
  if (!b) return renderBlitzSetup();
  if (b.screen === 'pickTimer') return renderBlitzTimerPicker(b.listId);
  if (b.screen === 'playing') return renderBlitzPlaying();
  if (b.screen === 'results') return renderBlitzResults();
  return renderBlitzSetup();
}

/* ============================== college football blitz ============================== */
function startCfbBlitz(listId, timerLen) {
  beginProgressSession('cfbBlitz');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  var list = CFB_BLITZ_LISTS.find(function (l) { return l.id === listId; });
  state.cfbBlitz = { listId: listId, list: list, timerLen: timerLen, screen: 'playing', endsAt: Date.now() + timerLen * 1000, timeLeft: timerLen, matched: [], input: '', lastFeedback: '', ranked: state.rankedPref.cfbBlitz !== false };
  state.screen = 'cfbBlitz';
  stopTimers();
  cfbBlitzTimer = setInterval(cfbBlitzTick, 250);
  renderAll();
}
function cfbBlitzTick() {
  if (!state.cfbBlitz || state.cfbBlitz.screen !== 'playing') return;
  var remain = (state.cfbBlitz.endsAt - Date.now()) / 1000;
  if (remain <= 0) { state.cfbBlitz.timeLeft = 0; endCfbBlitz(); return; }
  state.cfbBlitz.timeLeft = remain;
  var timerEl = document.getElementById('cfb-blitz-timer-display');
  if (timerEl) {
    timerEl.textContent = fmtTime(remain);
    timerEl.classList.toggle('blitz-timer-urgent', remain <= 10);
  }
}
function submitCfbBlitzGuess() {
  var b = state.cfbBlitz;
  if (!b || b.screen !== 'playing') return;
  var norm = normalizeBlitzText(b.input);
  if (!norm) return;
  var found = null;
  for (var i = 0; i < b.list.answers.length; i++) {
    var a = b.list.answers[i];
    if (b.matched.indexOf(a.answer) !== -1) continue;
    var candidates = [a.answer].concat(a.aliases || []);
    for (var j = 0; j < candidates.length; j++) {
      if (normalizeBlitzText(candidates[j]) === norm) { found = a; break; }
    }
    if (found) break;
  }
  if (found) {
    b.matched.push(found.answer);
    b.lastFeedback = 'correct';
    playSound('correct');
    if (b.matched.length >= b.list.answers.length) { b.input = ''; endCfbBlitz(); return; }
  } else {
    b.lastFeedback = 'miss';
    playSound('wrong');
  }
  b.input = '';
  renderAll();
}
function endCfbBlitz() {
  if (cfbBlitzTimer) { clearInterval(cfbBlitzTimer); cfbBlitzTimer = null; }
  state.cfbBlitz.screen = 'results';
  finishCfbBlitzRound();
  renderAll();
}
function finishCfbBlitzRound() {
  var b = state.cfbBlitz;
  var pct = 100 * b.matched.length / b.list.answers.length;
  if (b.ranked !== false) {
    var st = state.stats.cfbBlitz;
    st.attempts++;
    if (b.matched.length > st.bestMatched) st.bestMatched = b.matched.length;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    b.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbBlitz', { bestMatched: st.bestMatched, attempts: st.attempts });
    completeDailyChallengeFrom('cfbBlitz', b.matched.length + ' / ' + b.list.answers.length + ' found', pct);
    h2hSubmitModeResult('cfbBlitz', b.matched.length, b.list.answers.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderCfbBlitzSetup() {
  var lists = CFB_BLITZ_LISTS;
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB Blitz</h2>' +
    '<p class="mode-desc">Type every correct answer you can before time runs out. Nicknames and abbreviations count.</p>' +
    '<div class="blitz-list-picker">' +
    lists.map(function (l) {
      return '<button class="blitz-list-card" data-cfb-blitz-list="' + esc(l.id) + '"><b>' + esc(l.title) + '</b><div class="mode-desc">' + esc(l.prompt) + ' (' + l.answers.length + ' answers)</div></button>';
    }).join('') +
    '</div></div>';
}
function renderCfbBlitzTimerPicker(listId) {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + esc(CFB_BLITZ_LISTS.find(function (l) { return l.id === listId; }).title) + '</h2>' +
    rankedToggleHtml('cfbBlitz') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-cfb-blitz-start="' + listId + '" data-cfb-blitz-timer="' + n + '">' + n + 's</button>'; }).join('') +
    '</div>' +
    '<button class="btn-secondary" data-cfb-blitz-setup>Back</button>' +
    '</div>';
}
function renderCfbBlitzPlaying() {
  var b = state.cfbBlitz, total = b.list.answers.length;
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--blitz classic-broadcast--cfb">' + modeToolbarHtml('cfbBlitz', b.ranked) +
    '<div class="classic-broadcast-marquee"><span>CFB · LIGHTNING ROUND</span><strong>' + esc(b.list.title) + '</strong><em>' + esc(b.list.prompt) + '</em></div>' +
    '<div class="blitz-header"><div class="blitz-title">TIME REMAINING</div><div class="blitz-timer" id="cfb-blitz-timer-display">' + fmtTime(b.timeLeft) + '</div></div>' +
    '<div class="blitz-progress">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="blitz-input-row">' +
    '<input id="cfb-blitz-input" autocomplete="off" placeholder="Type an answer and hit Enter…" value="' + esc(b.input) + '" autofocus />' +
    '<button class="btn-primary" data-cfb-blitz-submit>Add</button>' +
    '</div>' +
    (b.lastFeedback === 'miss' ? '<div class="blitz-feedback wrong" aria-live="polite">Not a match — try again.</div>' : '') +
    '<div class="blitz-matched">' + b.matched.map(function (m) { return '<span class="blitz-chip">' + esc(m) + '</span>'; }).join('') + '</div>' +
    '</div>';
}
function renderCfbBlitzResults() {
  var b = state.cfbBlitz, total = b.list.answers.length;
  var missed = b.list.answers.filter(function (a) { return b.matched.indexOf(a.answer) === -1; });
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--blitz classic-broadcast--cfb">' +
    '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">TIME!</h2></div>' +
    '<h2 class="panel-title">Blitz Complete — ' + esc(b.list.title) + '</h2>' +
    '<div class="summary-score">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (a) { return esc(a.answer); }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you got every answer!</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-blitz-list="' + esc(b.listId) + '">Try Another List</button>' +
    '<button class="btn-secondary" data-share="cfbBlitz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('cfbBlitz') + '</div>';
}
function renderCfbBlitzScreen() {
  var b = state.cfbBlitz;
  if (!b) return renderCfbBlitzSetup();
  if (b.screen === 'pickTimer') return renderCfbBlitzTimerPicker(b.listId);
  if (b.screen === 'playing') return renderCfbBlitzPlaying();
  if (b.screen === 'results') return renderCfbBlitzResults();
  return renderCfbBlitzSetup();
}

/* ============================== speed round ============================== */
function speedQueue() { var ids = QUIZ.map(function (q) { return q.id; }); return drawNoRepeat('speed', ids, ids.length); }
function currentSpeedQuestion() {
  var s = state.speed;
  var id = s.queue[s.qIndex % s.queue.length];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startSpeedRound(sessionLen) {
  beginProgressSession('speed');
  state.speed = {
    sessionLen: sessionLen, qLen: 6, screen: 'playing',
    sessionEndsAt: Date.now() + sessionLen * 1000, qEndsAt: Date.now() + 6 * 1000,
    queue: speedQueue(), qIndex: 0, answeredIndex: null,
    score: 0, streak: 0, bestStreak: 0, correctCount: 0, totalCount: 0,
    sessionTimeLeft: sessionLen, qTimeLeft: 6, ranked: state.rankedPref.speed !== false
  };
  state.screen = 'speed';
  stopTimers();
  speedTimer = setInterval(speedTick, 200);
  renderAll();
}
function speedTick() {
  var s = state.speed;
  if (!s || s.screen !== 'playing') return;
  var now = Date.now();
  s.sessionTimeLeft = Math.max(0, (s.sessionEndsAt - now) / 1000);
  if (s.sessionTimeLeft <= 0) { endSpeedRound(); return; }
  s.qTimeLeft = Math.max(0, (s.qEndsAt - now) / 1000);
  if (s.answeredIndex === null && s.qTimeLeft <= 0) { registerSpeedAnswer(-1); return; }
  // Patch the timer/bar directly instead of a full renderAll() — a full DOM
  // rebuild 5x/sec was intermittently eating clicks on the answer buttons.
  var sessEl = document.getElementById('speed-session-timer');
  if (sessEl) {
    sessEl.textContent = fmtTime(s.sessionTimeLeft);
    sessEl.classList.toggle('blitz-timer-urgent', s.sessionTimeLeft <= 10);
  }
  var barEl = document.getElementById('speed-qbar-fill');
  if (barEl) {
    var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
    barEl.style.width = qPct + '%';
    barEl.classList.toggle('speed-qbar-fill-urgent', qPct <= 25);
  }
}
function registerSpeedAnswer(optionIndex) {
  var s = state.speed;
  if (!s || s.screen !== 'playing' || s.answeredIndex !== null) return;
  s.answeredIndex = optionIndex;
  var q = currentSpeedQuestion();
  var correct = q && optionIndex === q.correctIndex;
  s.totalCount++;
  if (correct) {
    s.correctCount++;
    s.streak++;
    if (s.streak > s.bestStreak) s.bestStreak = s.streak;
    var mult = 1 + Math.floor(s.streak / 3) * 0.5;
    s.score += Math.round(20 * mult);
  } else {
    s.streak = 0;
  }
  playSound(correct ? 'correct' : 'wrong');
  renderAll();
  setTimeout(advanceSpeedQuestion, 550);
}
function advanceSpeedQuestion() {
  var s = state.speed;
  if (!s || s.screen !== 'playing') return;
  if (typeof stopSfx === 'function') stopSfx();
  if (Date.now() >= s.sessionEndsAt) return;
  s.qIndex++;
  if (s.qIndex >= s.queue.length) { s.queue = speedQueue(); s.qIndex = 0; }
  s.answeredIndex = null;
  s.qEndsAt = Date.now() + s.qLen * 1000;
  renderAll();
}
function endSpeedRound() {
  if (speedTimer) { clearInterval(speedTimer); speedTimer = null; }
  state.speed.screen = 'summary';
  finishSpeedRound();
  renderAll();
}
function finishSpeedRound() {
  var s = state.speed;
  var pct = s.totalCount > 0 ? 100 * s.correctCount / s.totalCount : 100;
  if (s.ranked !== false) {
    var st = state.stats.speed;
    st.sessionsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    if (s.bestStreak > st.bestStreak) st.bestStreak = s.bestStreak;
    lsSet('nflTriviaStats', state.stats);
    if (s.totalCount > 0) { updateRatingDrift(pct); s.ratingDelta = lastRatingDelta; }
    pushLeaderboard('speed', { bestScore: st.bestScore, bestStreak: st.bestStreak, sessionsPlayed: st.sessionsPlayed });
  }
  h2hSubmitModeResult('speed', s.correctCount, s.totalCount, s.score);
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderSpeedSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Speed</h2>' +
    '<p class="mode-desc">Rapid-fire multiple choice — about 6 seconds per question, non-stop until time runs out. Chain correct answers for a streak multiplier.</p>' +
    rankedToggleHtml('speed') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-speed-start="' + n + '">' + n + 's session</button>'; }).join('') +
    '</div></div>';
}
function renderSpeedPlaying() {
  var s = state.speed, q = currentSpeedQuestion();
  var answered = s.answeredIndex !== null;
  var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--speed">' + modeToolbarHtml('speed', s.ranked) +
    '<div class="classic-broadcast-marquee"><span>NFL · LIVE CLOCK</span><strong>MAKE THE CALL</strong><em>Keep the streak alive</em></div>' +
    '<div class="speed-header"><div>Session: <span id="speed-session-timer">' + fmtTime(s.sessionTimeLeft) + '</span></div><div>Score: ' + s.score + '</div><div>Streak: ' + s.streak + '</div></div>' +
    '<div class="speed-qbar"><div class="speed-qbar-fill" id="speed-qbar-fill" style="width:' + qPct + '%"></div></div>' +
    '<section class="stadium-question-card"><div class="stadium-question-kicker">NEXT SNAP</div><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-speed-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderSpeedSummary() {
  var s = state.speed;
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--speed">' +
    '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">FINAL WHISTLE</h2></div>' +
    '<h2 class="panel-title">NFL Speed Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + s.correctCount + ' / ' + s.totalCount + ' correct &middot; best streak ' + s.bestStreak + '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-speed-start="' + s.sessionLen + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="speed">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderSpeedScreen() {
  if (!state.speed) return renderSpeedSetup();
  if (state.speed.screen === 'summary') return renderSpeedSummary();
  if (state.speed.screen === 'playing') return renderSpeedPlaying();
  return renderSpeedSetup();
}

/* ============================== higher or lower ==============================
   Classic "guess if the next one is higher or lower" format, endless streak
   until a miss — one of the most viral, shareable trivia formats around.

   HL_CATEGORIES is a two-level pool structure: pick a CATEGORY first (which
   entities you're comparing — career-honors players, 2025 season stat
   leaders by unit, contracts, or CFB stadiums), then a STAT within that
   category (which number). Every category besides the original "Career
   Accolades" pulls from data/higher-lower-extra.js (real 2025 regular-season
   leaders from NFL.com, real current contracts from Over The Cap, and real
   FBS stadium capacities) — lazy-loaded the same way data/grid.js already is
   for this mode, see MODE_DATA_FILES.higherLower.

   Each category's `pool` is a function (not a plain array) so categories
   whose raw data needs reshaping — Stadium Capacity's source rows use
   `stadium`/`school` fields, not the `name` every other pool's entities
   already have — can normalize once per draw instead of needing a special
   case threaded through every render/compare call site. `filterZero` is the
   ONE thing kept from the original design: Career Accolades' GRID_PLAYERS
   pool is huge (1144 players) and most have zero of any given accolade, so
   that category alone excludes zero-scores per stat to keep comparisons
   meaningful; every new category is already a pre-filtered leaderboard (top
   ~24, or every FBS stadium), so nothing there needs that filter.

   CFB still doesn't get a "Career Accolades" equivalent of its own —
   CFB_GRID_PLAYERS has no comparable numeric stat with real spread — but
   the new Stadium Capacity category is a genuine, entirely real CFB pool
   (138 FBS programs), so Higher or Lower isn't NFL-only anymore. */
function hlFmtCommas(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function hlFmtMoney(n) { return '$' + n + 'M'; }
function hlFmtPct(n) { return n + '%'; }
var HIGHER_LOWER_ACCOLADE_STATS = [
  { id: 'combined', label: 'Career Pro Bowl + All-Pro selections', scoreFn: function (p) { return (p.proBowls || 0) + (p.allPro || 0); } },
  { id: 'proBowls', label: 'Career Pro Bowl selections', scoreFn: function (p) { return p.proBowls || 0; } },
  { id: 'allPro', label: 'Career All-Pro selections', scoreFn: function (p) { return p.allPro || 0; } },
  { id: 'moments', label: 'Signature career moments (MVP + Super Bowl win + Super Bowl MVP + Hall of Fame)', scoreFn: function (p) { return (p.mvp ? 1 : 0) + (p.sbChamp ? 1 : 0) + (p.sbMVP ? 1 : 0) + (p.hof ? 1 : 0); } }
];
function higherLowerPlayerLine(p) {
  return esc(p.position || '') + (p.college ? ' &middot; ' + esc(p.college) : '') + (p.teams && p.teams.length ? ' &middot; ' + esc(p.teams.join('/')) : '');
}
function hl2025Line(p) { return '2025 season &middot; ' + esc(p.team); }
var HL_CATEGORIES = [
  {
    id: 'accolades', label: 'Career Accolades', entityLabel: 'player', filterZero: true,
    pool: function () { return GRID_PLAYERS; }, lineFn: higherLowerPlayerLine, stats: HIGHER_LOWER_ACCOLADE_STATS
  },
  {
    id: 'passing', label: '2025 Passing', entityLabel: 'player',
    pool: function () { return HL_PASSING; }, lineFn: hl2025Line,
    stats: [
      { id: 'passYds', label: 'Passing Yards', scoreFn: function (p) { return p.passYds; } },
      { id: 'passTD', label: 'Passing Touchdowns', scoreFn: function (p) { return p.passTD; } },
      { id: 'passInt', label: 'Interceptions Thrown', scoreFn: function (p) { return p.passInt; } },
      { id: 'passRating', label: 'Passer Rating', scoreFn: function (p) { return p.passRating; } },
      { id: 'passSacks', label: 'Times Sacked', scoreFn: function (p) { return p.passSacks; } }
    ]
  },
  {
    id: 'rushing', label: '2025 Rushing', entityLabel: 'player',
    pool: function () { return HL_RUSHING; }, lineFn: hl2025Line,
    stats: [
      { id: 'rushYds', label: 'Rushing Yards', scoreFn: function (p) { return p.rushYds; } },
      { id: 'rushTD', label: 'Rushing Touchdowns', scoreFn: function (p) { return p.rushTD; } },
      { id: 'rushLng', label: 'Longest Rush', scoreFn: function (p) { return p.rushLng; } }
    ]
  },
  {
    id: 'receiving', label: '2025 Receiving', entityLabel: 'player',
    pool: function () { return HL_RECEIVING; }, lineFn: hl2025Line,
    stats: [
      { id: 'rec', label: 'Receptions', scoreFn: function (p) { return p.rec; } },
      { id: 'recYds', label: 'Receiving Yards', scoreFn: function (p) { return p.recYds; } },
      { id: 'recTD', label: 'Receiving Touchdowns', scoreFn: function (p) { return p.recTD; } }
    ]
  },
  {
    id: 'tackles', label: '2025 Tackles', entityLabel: 'player',
    pool: function () { return HL_TACKLES; }, lineFn: hl2025Line,
    stats: [
      { id: 'tklCombined', label: 'Combined Tackles', scoreFn: function (p) { return p.tklCombined; } },
      { id: 'tklSolo', label: 'Solo Tackles', scoreFn: function (p) { return p.tklSolo; } },
      { id: 'tklAssists', label: 'Assisted Tackles', scoreFn: function (p) { return p.tklAssists; } },
      { id: 'tklSacks', label: 'Sacks', scoreFn: function (p) { return p.tklSacks; } }
    ]
  },
  {
    id: 'interceptions', label: '2025 Interceptions', entityLabel: 'player',
    pool: function () { return HL_INTERCEPTIONS; }, lineFn: hl2025Line,
    stats: [
      { id: 'int', label: 'Interceptions', scoreFn: function (p) { return p.int; } },
      { id: 'intYds', label: 'Interception Return Yards', scoreFn: function (p) { return p.intYds; } }
    ]
  },
  {
    id: 'fumbles', label: '2025 Forced Fumbles', entityLabel: 'player',
    pool: function () { return HL_FUMBLES; }, lineFn: hl2025Line,
    stats: [
      { id: 'forcedFum', label: 'Forced Fumbles', scoreFn: function (p) { return p.forcedFum; } },
      { id: 'fumRec', label: 'Fumble Recoveries', scoreFn: function (p) { return p.fumRec; } }
    ]
  },
  {
    id: 'fieldgoals', label: '2025 Field Goals', entityLabel: 'player',
    pool: function () { return HL_FIELDGOALS; }, lineFn: hl2025Line,
    stats: [
      { id: 'fgMade', label: 'Field Goals Made', scoreFn: function (p) { return p.fgMade; } },
      { id: 'fgAtt', label: 'Field Goal Attempts', scoreFn: function (p) { return p.fgAtt; } },
      { id: 'fgPct', label: 'Field Goal %', scoreFn: function (p) { return p.fgPct; }, fmt: hlFmtPct },
      { id: 'fgLng', label: 'Longest Field Goal', scoreFn: function (p) { return p.fgLng; } }
    ]
  },
  {
    id: 'punting', label: '2025 Punting', entityLabel: 'player',
    pool: function () { return HL_PUNTING; }, lineFn: hl2025Line,
    stats: [
      { id: 'puntAvg', label: 'Punting Average', scoreFn: function (p) { return p.puntAvg; } },
      { id: 'puntYds', label: 'Punting Yards', scoreFn: function (p) { return p.puntYds; } }
    ]
  },
  {
    id: 'returns', label: '2025 Kick/Punt Returns', entityLabel: 'player',
    pool: function () { return HL_RETURNS; }, lineFn: function (p) { return esc(p.returnType) + ' return &middot; 2025 season &middot; ' + esc(p.team); },
    stats: [
      { id: 'returnAvg', label: 'Return Average', scoreFn: function (p) { return p.returnAvg; } },
      { id: 'returnYds', label: 'Return Yards', scoreFn: function (p) { return p.returnYds; } }
    ]
  },
  {
    id: 'contracts', label: 'Contract Value', entityLabel: 'player',
    pool: function () { return HL_CONTRACTS; }, lineFn: function (p) { return esc(p.pos) + ' &middot; ' + esc(p.team); },
    stats: [
      { id: 'totalValue', label: 'Total Contract Value', scoreFn: function (p) { return p.totalValue; }, fmt: hlFmtMoney },
      { id: 'apy', label: 'Average Per Year', scoreFn: function (p) { return p.apy; }, fmt: hlFmtMoney },
      { id: 'totalGtd', label: 'Total Guaranteed', scoreFn: function (p) { return p.totalGtd; }, fmt: hlFmtMoney },
      { id: 'pctGtd', label: '% of Contract Guaranteed', scoreFn: function (p) { return p.pctGtd; }, fmt: hlFmtPct }
    ]
  },
  {
    id: 'stadiums', label: 'CFB Stadium Capacity', entityLabel: 'stadium',
    pool: function () {
      return HL_STADIUMS.map(function (st) { return { name: st.stadium, school: st.school, nickname: st.nickname, conf: st.conf, city: st.city, capacity: st.capacity }; });
    },
    lineFn: function (p) { return esc(p.school) + ' ' + esc(p.nickname) + ' &middot; ' + esc(p.conf) + ' &middot; ' + esc(p.city); },
    stats: [
      { id: 'capacity', label: 'Stadium Capacity', scoreFn: function (p) { return p.capacity; }, fmt: hlFmtCommas }
    ]
  }
];
function hlCategoryConfig(catId) { return HL_CATEGORIES.find(function (c) { return c.id === catId; }) || HL_CATEGORIES[0]; }
function hlStatConfig(catId, statId) {
  var cat = hlCategoryConfig(catId);
  return cat.stats.find(function (s) { return s.id === statId; }) || cat.stats[0];
}
function higherLowerPool(catId, statId) {
  var cat = hlCategoryConfig(catId);
  var cfg = hlStatConfig(catId, statId);
  var pool = cat.pool();
  if (cat.filterZero) pool = pool.filter(function (p) { return cfg.scoreFn(p) > 0; });
  return pool;
}
function higherLowerScore(p, catId, statId) { return hlStatConfig(catId, statId).scoreFn(p); }
function higherLowerScoreDisplay(p, catId, statId) {
  var cfg = hlStatConfig(catId, statId);
  var v = cfg.scoreFn(p);
  return cfg.fmt ? cfg.fmt(v) : v;
}
function higherLowerDrawPlayer(catId, statId, usedNames) {
  var pool = higherLowerPool(catId, statId).filter(function (p) { return usedNames.indexOf(p.name) === -1; });
  // Pool exhausted — allow repeats rather than dead-end an otherwise-still-
  // going run (career-accolade pools run 334-651 deep, but a few new
  // categories like Fumbles/Punting/Returns only have ~18-20 entries and a
  // real streak CAN reach that).
  if (!pool.length) pool = higherLowerPool(catId, statId);
  return pool[Math.floor(Math.random() * pool.length)];
}
// Remembered for the session (not persisted across visits) so re-starting
// after a loss defaults back to whatever you were just playing, same
// convenience as Quiz remembering its last round size. Stat prefs are kept
// PER CATEGORY (not one shared value) since a stat id from one category
// (e.g. 'combined') isn't valid in another (e.g. 'passing') — switching
// categories always needs to land on one of ITS OWN stats.
var higherLowerCategoryPref = 'accolades';
var higherLowerStatPrefByCategory = { accolades: 'combined' };
function setHigherLowerCategory(catId) {
  higherLowerCategoryPref = catId;
  if (!higherLowerStatPrefByCategory[catId]) higherLowerStatPrefByCategory[catId] = hlCategoryConfig(catId).stats[0].id;
  renderAll();
}
function setHigherLowerStat(statId) { higherLowerStatPrefByCategory[higherLowerCategoryPref] = statId; renderAll(); }
function startHigherLower() {
  beginProgressSession('higherLower');
  var catId = higherLowerCategoryPref;
  var statId = higherLowerStatPrefByCategory[catId] || hlCategoryConfig(catId).stats[0].id;
  var first = higherLowerDrawPlayer(catId, statId, []);
  var second = higherLowerDrawPlayer(catId, statId, [first.name]);
  state.higherLower = {
    screen: 'playing', category: catId, stat: statId, current: first, next: second, streak: 0, revealedScore: null, lastCorrect: null,
    usedNames: [first.name, second.name], ranked: state.rankedPref.higherLower !== false
  };
  state.screen = 'higherLower';
  renderAll();
}
function submitHigherLowerGuess(direction) {
  var s = state.higherLower;
  if (!s || s.screen !== 'playing') return;
  var curScore = higherLowerScore(s.current, s.category, s.stat), nextScore = higherLowerScore(s.next, s.category, s.stat);
  // A tie always counts as correct — standard house rule for this format,
  // and the honest one: nothing in "higher or lower" was violated by a
  // dead-even comparison, so it shouldn't end the run either direction.
  var correct = curScore === nextScore || (direction === 'higher' ? nextScore > curScore : nextScore < curScore);
  s.lastCorrect = correct;
  s.revealedScore = nextScore;
  playSound(correct ? 'correct' : 'wrong');
  if (correct) { s.streak++; s.screen = 'reveal'; }
  else { s.screen = 'over'; finishHigherLower(); }
  renderAll();
}
function higherLowerContinue() {
  var s = state.higherLower;
  if (!s || s.screen !== 'reveal') return;
  s.current = s.next;
  s.next = higherLowerDrawPlayer(s.category, s.stat, s.usedNames);
  s.usedNames.push(s.next.name);
  s.revealedScore = null;
  s.lastCorrect = null;
  s.screen = 'playing';
  renderAll();
}
function finishHigherLower() {
  var s = state.higherLower;
  if (s.ranked !== false) {
    var st = state.stats.higherLower;
    st.gamesPlayed++;
    if (s.streak > st.bestStreak) st.bestStreak = s.streak;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(Math.min(100, s.streak * 10));
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('higherLower', { bestStreak: st.bestStreak, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('higherLower', s.streak + ' streak', Math.min(100, s.streak * 10));
  h2hSubmitModeResult('higherLower', s.streak, null);
}
function renderHigherLowerSetup() {
  var cat = hlCategoryConfig(higherLowerCategoryPref);
  var statPref = higherLowerStatPrefByCategory[higherLowerCategoryPref] || cat.stats[0].id;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--duel">' +
    broadcastMarqueeHtml('THE STAT BATTLE', 'HIGHER OR LOWER', 'One number revealed. One number hidden. How long can you last?') +
    '<p class="mode-desc">Two real numbers, one real stat — see one, guess whether the next is higher or lower. Keep going until you miss — how long a streak can you build?</p>' +
    '<div class="chip-row">' +
    HL_CATEGORIES.map(function (c) { return '<button class="chip-toggle' + (higherLowerCategoryPref === c.id ? ' active' : '') + '" data-hl-category="' + c.id + '">' + esc(c.label) + '</button>'; }).join('') +
    '</div>' +
    '<div class="chip-row">' +
    cat.stats.map(function (st) { return '<button class="chip-toggle' + (statPref === st.id ? ' active' : '') + '" data-hl-stat="' + st.id + '">' + esc(st.label) + '</button>'; }).join('') +
    '</div>' +
    rankedToggleHtml('higherLower') +
    '<button class="btn-primary" data-hl-start>Start</button>' +
    '</div>';
}
function renderHigherLowerPlaying() {
  var s = state.higherLower;
  var revealing = s.screen === 'reveal';
  var cat = hlCategoryConfig(s.category);
  var statLabel = hlStatConfig(s.category, s.stat).label;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--duel">' + modeToolbarHtml('higherLower', s.ranked) +
    broadcastScorebugHtml([['STREAK', s.streak], ['STAT', statLabel], ['CATEGORY', cat.label]]) +
    '<div class="broadcast-duel">' +
    '<div class="hl-card hl-card-current"><span class="broadcast-card-kicker">THE BENCHMARK</span>' +
    '<div class="hl-name">' + esc(s.current.name) + '</div>' +
    '<div class="hl-line">' + cat.lineFn(s.current) + '</div>' +
    '<div class="hl-score">' + higherLowerScoreDisplay(s.current, s.category, s.stat) + '</div>' +
    '<div class="hl-score-label">' + esc(statLabel) + '</div>' +
    '</div>' +
    '<div class="hl-vs" aria-hidden="true">VS</div>' +
    '<div class="hl-card hl-card-next' + (revealing ? (s.lastCorrect ? ' correct' : ' wrong') : '') + '">' +
    '<div class="hl-name">' + esc(s.next.name) + '</div>' +
    '<div class="hl-line">' + cat.lineFn(s.next) + '</div>' +
    (revealing
      ? '<div class="hl-score">' + higherLowerScoreDisplay(s.next, s.category, s.stat) + '</div><div class="hl-score-label">' + (s.lastCorrect ? icon('check') + ' Correct!' : icon('xMark') + ' Not quite') + '</div>'
      : '<div class="hl-score hl-score-hidden">?</div><div class="hl-score-label">More or fewer than ' + esc(s.current.name) + '?</div>') +
    '</div>' +
    '</div>' +
    (revealing ? broadcastCallHtml(s.lastCorrect, s.lastCorrect ? 'STREAK ALIVE' : 'STREAK OVER') : '') +
    (revealing
      ? '<button class="btn-primary hl-continue" data-hl-continue>Next ' + (cat.entityLabel === 'stadium' ? 'Stadium' : 'Player') + '</button>'
      : '<div class="hl-guess-row">' +
        '<button class="hl-guess-btn hl-lower" data-hl-guess="lower">' + icon('arrowDown') + ' Lower</button>' +
        '<button class="hl-guess-btn hl-higher" data-hl-guess="higher">' + icon('arrowUp') + ' Higher</button>' +
        '</div>') +
    '</div>';
}
function renderHigherLowerOver() {
  var s = state.higherLower;
  var cat = hlCategoryConfig(s.category);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--duel">' +
    broadcastResultHtml('FINAL · STAT BATTLE', s.streak, 'Your final streak', s.streak >= 5) +
    '<div class="hl-card hl-card-next wrong">' +
    '<div class="hl-name">' + esc(s.next.name) + '</div>' +
    '<div class="hl-line">' + cat.lineFn(s.next) + '</div>' +
    '<div class="hl-score">' + higherLowerScoreDisplay(s.next, s.category, s.stat) + '</div>' +
    '<div class="hl-score-label">vs ' + esc(s.current.name) + '\'s ' + higherLowerScoreDisplay(s.current, s.category, s.stat) + '</div>' +
    '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-hl-start>Play Again</button>' +
    '<button class="btn-secondary" data-share="higherLower">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderHigherLowerScreen() {
  if (!state.higherLower) return renderHigherLowerSetup();
  if (state.higherLower.screen === 'over') return renderHigherLowerOver();
  return renderHigherLowerPlaying();
}

/* ============================== college football speed round ============================== */
function cfbSpeedQueue() { var ids = CFB_SPEED.map(function (q) { return q.id; }); return drawNoRepeat('cfbspeed', ids, ids.length); }
function currentCfbSpeedQuestion() {
  var s = state.cfbSpeed;
  var id = s.queue[s.qIndex % s.queue.length];
  return CFB_SPEED.find(function (q) { return q.id === id; });
}
function startCfbSpeedRound(sessionLen) {
  beginProgressSession('cfbSpeed');
  state.cfbSpeed = {
    sessionLen: sessionLen, qLen: 6, screen: 'playing',
    sessionEndsAt: Date.now() + sessionLen * 1000, qEndsAt: Date.now() + 6 * 1000,
    queue: cfbSpeedQueue(), qIndex: 0, answeredIndex: null,
    score: 0, streak: 0, bestStreak: 0, correctCount: 0, totalCount: 0,
    sessionTimeLeft: sessionLen, qTimeLeft: 6, ranked: state.rankedPref.cfbSpeed !== false
  };
  state.screen = 'cfbSpeed';
  stopTimers();
  cfbSpeedTimer = setInterval(cfbSpeedTick, 200);
  renderAll();
}
function cfbSpeedTick() {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing') return;
  var now = Date.now();
  s.sessionTimeLeft = Math.max(0, (s.sessionEndsAt - now) / 1000);
  if (s.sessionTimeLeft <= 0) { endCfbSpeedRound(); return; }
  s.qTimeLeft = Math.max(0, (s.qEndsAt - now) / 1000);
  if (s.answeredIndex === null && s.qTimeLeft <= 0) { registerCfbSpeedAnswer(-1); return; }
  var sessEl = document.getElementById('cfb-speed-session-timer');
  if (sessEl) {
    sessEl.textContent = fmtTime(s.sessionTimeLeft);
    sessEl.classList.toggle('blitz-timer-urgent', s.sessionTimeLeft <= 10);
  }
  var barEl = document.getElementById('cfb-speed-qbar-fill');
  if (barEl) {
    var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
    barEl.style.width = qPct + '%';
    barEl.classList.toggle('speed-qbar-fill-urgent', qPct <= 25);
  }
}
function registerCfbSpeedAnswer(optionIndex) {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing' || s.answeredIndex !== null) return;
  s.answeredIndex = optionIndex;
  var q = currentCfbSpeedQuestion();
  var correct = q && optionIndex === q.correctIndex;
  s.totalCount++;
  if (correct) {
    s.correctCount++;
    s.streak++;
    if (s.streak > s.bestStreak) s.bestStreak = s.streak;
    var mult = 1 + Math.floor(s.streak / 3) * 0.5;
    s.score += Math.round(20 * mult);
  } else {
    s.streak = 0;
  }
  playSound(correct ? 'correct' : 'wrong');
  renderAll();
  setTimeout(advanceCfbSpeedQuestion, 550);
}
function advanceCfbSpeedQuestion() {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing') return;
  if (typeof stopSfx === 'function') stopSfx();
  if (Date.now() >= s.sessionEndsAt) return;
  s.qIndex++;
  if (s.qIndex >= s.queue.length) { s.queue = cfbSpeedQueue(); s.qIndex = 0; }
  s.answeredIndex = null;
  s.qEndsAt = Date.now() + s.qLen * 1000;
  renderAll();
}
function endCfbSpeedRound() {
  if (cfbSpeedTimer) { clearInterval(cfbSpeedTimer); cfbSpeedTimer = null; }
  state.cfbSpeed.screen = 'summary';
  finishCfbSpeedRound();
  renderAll();
}
function finishCfbSpeedRound() {
  var s = state.cfbSpeed;
  var pct = s.totalCount > 0 ? 100 * s.correctCount / s.totalCount : 100;
  if (s.ranked !== false) {
    var st = state.stats.cfbSpeed;
    st.sessionsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    if (s.bestStreak > st.bestStreak) st.bestStreak = s.bestStreak;
    lsSet('nflTriviaStats', state.stats);
    if (s.totalCount > 0) { updateRatingDrift(pct); s.ratingDelta = lastRatingDelta; }
    pushLeaderboard('cfbSpeed', { bestScore: st.bestScore, bestStreak: st.bestStreak, sessionsPlayed: st.sessionsPlayed });
  }
  h2hSubmitModeResult('cfbSpeed', s.correctCount, s.totalCount, s.score);
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderCfbSpeedSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB Speed Round</h2>' +
    '<p class="mode-desc">Rapid-fire college football multiple choice — about 6 seconds per question, non-stop until time runs out. Chain correct answers for a streak multiplier.</p>' +
    rankedToggleHtml('cfbSpeed') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-cfb-speed-start="' + n + '">' + n + 's session</button>'; }).join('') +
    '</div></div>';
}
function renderCfbSpeedPlaying() {
  var s = state.cfbSpeed, q = currentCfbSpeedQuestion();
  var answered = s.answeredIndex !== null;
  var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--speed classic-broadcast--cfb">' + modeToolbarHtml('cfbSpeed', s.ranked) +
    '<div class="classic-broadcast-marquee"><span>CFB · LIVE CLOCK</span><strong>MAKE THE CALL</strong><em>Keep the streak alive</em></div>' +
    '<div class="speed-header"><div>Session: <span id="cfb-speed-session-timer">' + fmtTime(s.sessionTimeLeft) + '</span></div><div>Score: ' + s.score + '</div><div>Streak: ' + s.streak + '</div></div>' +
    '<div class="speed-qbar"><div class="speed-qbar-fill" id="cfb-speed-qbar-fill" style="width:' + qPct + '%"></div></div>' +
    '<section class="stadium-question-card"><div class="stadium-question-kicker">NEXT SNAP</div><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-cfb-speed-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderCfbSpeedSummary() {
  var s = state.cfbSpeed;
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--speed classic-broadcast--cfb">' +
    '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">FINAL WHISTLE</h2></div>' +
    '<h2 class="panel-title">CFB Speed Round Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + s.correctCount + ' / ' + s.totalCount + ' correct &middot; best streak ' + s.bestStreak + '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-speed-start="' + s.sessionLen + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="cfbSpeed">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbSpeedScreen() {
  if (!state.cfbSpeed) return renderCfbSpeedSetup();
  if (state.cfbSpeed.screen === 'summary') return renderCfbSpeedSummary();
  if (state.cfbSpeed.screen === 'playing') return renderCfbSpeedPlaying();
  return renderCfbSpeedSetup();
}

/* ============================== silhouette ============================== */
var POSITION_LABELS = { QB: 'Quarterback', RB: 'Running Back', WR: 'Wide Receiver', TE: 'Tight End', C: 'Center', CB: 'Cornerback', DL: 'Defensive Line', DT: 'Defensive Tackle', DE: 'Defensive End', EDGE: 'Edge Rusher', LB: 'Linebacker', OG: 'Guard', OT: 'Tackle', OL: 'Offensive Line', S: 'Safety', K: 'Kicker' };
function expandPosition(position) {
  return String(position).split('/').map(function (tok) { tok = tok.trim(); return POSITION_LABELS[tok.toUpperCase()] || tok; }).join(' / ');
}
// Football player pictogram — "American Football Player" icon by Delapouite
// (game-icons.net), CC BY 3.0. Used here instead of a hand-drawn figure;
// attribution lives in the app footer and README.
var FOOTBALL_PLAYER_ICON_PATH = 'M256 41c-29.8 0-50.9 10.83-65.3 26.98C176.4 84.12 169 106 169 128c0 17.5 4.9 29.1 12.3 39h8.8l-7.1-38.2v-.8c0-7 3.8-13.2 8.6-17.3 4.9-4.2 10.8-7 17.6-9.2 1.9-.6 3.8-1.2 5.8-1.74V71h82v28.76c2 .54 3.9 1.14 5.8 1.74 6.8 2.2 12.7 5 17.6 9.2 4.8 4.1 8.6 10.3 8.6 17.3v.8l-7.1 38.2h8.8c7.4-9.9 12.3-21.5 12.3-39 0-22-7.4-43.88-21.7-60.02C306.9 51.83 285.8 41 256 41zm-23 48v14h46V89h-46zm-44.5 96 4.7 14h27.2l-3.4-14h-28.5zm46.9 0 3.4 14h34.4l3.4-14h-41.2zm59.6 0-3.4 14h27.2l4.7-14H295zm-121.5 11.9-27.3 3.9c-22.5 7.6-41.3 19-54.2 30-12.48 10.7-18.29 22-18.79 24.8l14.23 57L141.2 326l28.4-28.4 12.8 12.8-29 29 2.4 27.1 34-13.6c4.4-17.9 12-33.2 20.8-45.4 13.7-19 29.3-31.3 45.4-31.3 16.1 0 31.6 12.3 45.4 31.3 8.8 12.2 16.4 27.5 20.8 45.4l34 13.6 2.4-27.1-29-29 12.8-12.8 28.4 28.4 53.8-13.4 14.3-57.1c-.2-1.3-1.2-4.7-4.1-8.9-3.1-4.7-8.1-10.2-14.7-15.8-12.9-11-31.8-22.4-54.3-30l-27.3-3.9-10.2 30.6-.2.5c-5.7 11.2-16.9 18.1-29.6 22.5-12.8 4.4-27.6 6.5-42.5 6.5-14.9 0-29.7-2.1-42.5-6.5-12.7-4.4-23.9-11.3-29.6-22.5l-.2-.5-10.2-30.6zm25.6 20.1 1.1 3.2c2.5 4.7 9.2 9.8 19.3 13.3 3.1 1.1 6.4 2 9.9 2.8l-4.7-19.3h-25.6zm44 0 5.3 21.8c2.5.1 5.1.2 7.6.2s5.1-.1 7.6-.2l5.3-21.8h-25.8zm44.2 0-4.7 19.3c3.5-.8 6.8-1.7 9.9-2.8 10.1-3.5 16.8-8.6 19.3-13.3l1.1-3.2h-25.6zM256 294.2c-4.3 0-19.2 7.8-30.9 23.8-11.6 16.1-21.1 39.4-21.1 67.4 0 28.1 9.5 51.4 21.1 67.5 11.7 16 26.6 23.8 30.9 23.8 4.2 0 19.2-7.8 30.8-23.9 11.7-16.1 21.2-39.3 21.2-67.4 0-28-9.5-51.3-21.2-67.4-11.6-16-26.6-23.8-30.8-23.8zm-9 31.1h18v15.1h13.3v18H265v18h13.3v18H265v18.1h13.3v18H265v15.1h-18v-15.1h-13.4v-18H247v-18.1h-13.4v-18H247v-18h-13.4v-18H247v-15.1zm-165.66 4.3c-12.1 7.2-22.18 20.4-29.12 36.1C44.78 382.4 41 401.5 41 416c0 6.1 1.61 9.8 4.51 12.9 2.9 3.1 7.62 5.7 14.24 7.4 13.24 3.4 33.37 2.7 54.65-1.2 21.3-3.8 43.8-10.7 62.7-18.4 4-1.7 7.8-3.4 11.4-5.1-1.6-8.2-2.5-17-2.5-26.2 0-4 .2-8 .5-11.8l-87.16 34.8-9.7-14.8c8-8 19.86-19.8 29.46-31.4 4.8-5.7 9-11.4 11.9-16.3.8-1.3 1.1-2.3 1.7-3.5l-51.36-12.8zm349.36 0-51.4 12.8c.6 1.2.9 2.2 1.7 3.5 2.9 4.9 7.1 10.6 11.9 16.3 9.6 11.6 21.5 23.4 29.5 31.4l-9.7 14.8-87.2-34.8c.3 3.8.5 7.8.5 11.8 0 9.2-.9 18-2.5 26.2 3.6 1.7 7.4 3.4 11.4 5.1 18.9 7.7 41.4 14.6 62.7 18.4 21.3 3.9 41.4 4.6 54.7 1.2 6.6-1.7 11.3-4.3 14.2-7.4 2.9-3.1 4.5-6.8 4.5-12.9 0-14.5-3.8-33.6-11.2-50.3-7-15.7-17-28.9-29.1-36.1zm-237.6 99.8c-2.9 1.3-6 2.6-9.2 3.9-6.8 2.8-13.9 5.4-21.3 7.9l5.6 61.8h175.6l5.6-61.8c-7.4-2.5-14.5-5.1-21.3-7.9-3.2-1.3-6.3-2.6-9.2-3.9-4.5 13-10.6 24.5-17.5 34-13.8 19-29.3 31.3-45.4 31.3-16.1 0-31.7-12.3-45.4-31.3-6.9-9.5-13-21-17.5-34z';
function renderSilhouetteSvg(position, color) {
  return '<svg viewBox="0 0 512 512" class="silhouette-svg" preserveAspectRatio="xMidYMid meet"><path fill="' + color + '" d="' + FOOTBALL_PLAYER_ICON_PATH + '"/></svg>';
}
// Real per-player cutout, if one has been dropped in assets/silhouettes/<slug>.png
// (see assets/silhouettes/EXPECTED_FILENAMES.txt for the exact expected name per
// player). Rendered as an overlay on top of the generic pictogram; if the image
// 404s, onerror hides the <img> so the pictogram underneath shows through. If the
// image loads, onload hides the pictogram (previousElementSibling) instead — the
// two are never shown stacked/visible at the same time.
function renderSilhouetteStage(p, color) {
  var slug = slugify(p.name);
  return '<div class="silhouette-stage">' +
    renderSilhouetteSvg(p.position, color) +
    '<img class="silhouette-photo" src="assets/silhouettes/' + slug + '.png" alt="" ' +
    'onload="this.previousElementSibling.style.display=\'none\'" onerror="this.style.display=\'none\'" />' +
    '</div>';
}
function silhouetteAccoladesText(p) {
  var badges = [];
  if (p.hof) badges.push('Hall of Famer');
  if (p.mvp) badges.push('MVP winner');
  if (p.sbChamp) badges.push('Super Bowl champion');
  return badges.length ? badges.join(', ') : 'No Super Bowl rings, MVP awards, or Hall of Fame induction (yet)';
}
function silhouetteClues(p) {
  return [
    'Position: ' + expandPosition(p.position),
    'Drafted: ' + (p.draftDecade || 'Unknown'),
    'Team(s): ' + p.team,
    'Accolades: ' + silhouetteAccoladesText(p),
    'Signature move: ' + p.pose,
    'Recognition notes: ' + p.notes
  ];
}
function loadSilhouetteItem() {
  var s = state.silhouette, p = s.queue[s.index];
  s.currentClues = silhouetteClues(p);
  s.revealedCount = 0;
  s.itemState = 'guessing';
  s.input = '';
  s.lastWrong = false;
  s.lastPoints = 0;
}
function startSilhouetteRound(roundSize) {
  beginProgressSession('silhouette');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  var size = Math.min(roundSize, SILHOUETTE_PLAYERS.length);
  var allNames = SILHOUETTE_PLAYERS.map(function (p) { return p.name; });
  var names = drawNoRepeat('silhouette', allNames, size);
  var pool = names.map(function (n) { return SILHOUETTE_PLAYERS.find(function (p) { return p.name === n; }); });
  state.silhouette = { roundSize: roundSize, queue: pool, index: 0, score: 0, results: [], screen: 'round', ranked: state.rankedPref.silhouette !== false };
  loadSilhouetteItem();
  state.screen = 'silhouette';
  renderAll();
}
function revealSilhouetteClue() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  if (s.revealedCount < s.currentClues.length) s.revealedCount++;
  renderAll();
}
function submitSilhouetteGuess() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  var norm = normName(s.input);
  if (!norm) return;
  var p = s.queue[s.index];
  if (normName(p.name) === norm) {
    var pts = Math.max(10, 100 - s.revealedCount * 20);
    s.score += pts;
    s.results.push({ name: p.name, correct: true, points: pts });
    s.lastPoints = pts;
    s.lastWrong = false;
    s.itemState = 'revealed';
    playSound('correct');
  } else {
    s.lastWrong = true;
    if (s.revealedCount < s.currentClues.length) s.revealedCount++;
    playSound('wrong');
  }
  s.input = '';
  renderAll();
}
function giveUpSilhouette() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  s.results.push({ name: s.queue[s.index].name, correct: false, points: 0 });
  s.lastPoints = 0;
  s.lastWrong = false;
  s.itemState = 'revealed';
  renderAll();
}
function advanceSilhouette() {
  var s = state.silhouette;
  if (typeof stopSfx === 'function') stopSfx();
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; finishSilhouetteRound(); renderAll(); return; }
  s.index++;
  loadSilhouetteItem();
  renderAll();
}
function finishSilhouetteRound() {
  var s = state.silhouette;
  var silCorrect = s.results.filter(function (r) { return r.correct; }).length;
  var pct = 100 * silCorrect / s.results.length;
  if (s.ranked !== false) {
    var st = state.stats.silhouette;
    st.roundsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    var quickGuesses = s.results.filter(function (r) { return r.correct && r.points >= 80; }).length;
    if (quickGuesses > st.bestQuick) st.bestQuick = quickGuesses;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('silhouette', { bestScore: st.bestScore, roundsPlayed: st.roundsPlayed, bestQuick: st.bestQuick });
    completeDailyChallengeFrom('silhouette', silCorrect + ' / ' + s.results.length + ' correct', pct);
    h2hSubmitModeResult('silhouette', silCorrect, s.results.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderSilhouetteSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Silhouette</h2>' +
    '<p class="mode-desc">A generic pose silhouette for a real player from our pool — guess who it is. Wrong guesses (or asking for a hint) reveal a clue: position, draft info, college, a team they played for, then accolades. Fewer clues used = more points.</p>' +
    rankedToggleHtml('silhouette') +
    '<div class="chip-row">' +
    [5, 10].map(function (n) { return '<button class="chip-toggle" data-silhouette-start="' + n + '">' + n + ' players</button>'; }).join('') +
    '</div></div>';
}
function renderSilhouetteRound() {
  var s = state.silhouette, p = s.queue[s.index];
  var html = '<div class="panel stadium-game classic-broadcast classic-broadcast--silhouette">' + modeToolbarHtml('silhouette', s.ranked) +
    '<div class="classic-broadcast-marquee"><span>NFL · MYSTERY PLAYER</span><strong>WHO IS IT?</strong><em>Player ' + (s.index + 1) + ' / ' + s.queue.length + ' · ' + s.score + ' pts</em></div>' +
    renderSilhouetteStage(p, s.itemState === 'revealed' ? '#d9a63c' : '#c9d3e6');
  if (s.itemState === 'revealed') {
    html += '<div class="silhouette-reveal">' + esc(p.name) + (s.lastPoints ? ' — +' + s.lastPoints + ' pts' : ' — no points') + '</div>' +
      '<button class="btn-primary" data-silhouette-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Silhouette') + '</button>';
  } else {
    html += '<div class="silhouette-clues">' +
      s.currentClues.slice(0, s.revealedCount).map(function (c) { return '<div class="silhouette-clue">' + esc(c) + '</div>'; }).join('') +
      '</div>' +
      (s.lastWrong ? '<div class="blitz-feedback wrong" aria-live="polite">Not quite — here\'s another clue.</div>' : '') +
      '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="silhouette-input" autocomplete="off" placeholder="Who is it?" value="' + esc(s.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="silhouette-input-typeahead" />' +
      '<div id="silhouette-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-silhouette-submit>Guess</button>' +
      '</div>' +
      '<div class="btn-row">' +
      '<button class="btn-secondary" data-silhouette-hint>Reveal a Clue</button>' +
      '<button class="btn-secondary" data-silhouette-giveup>Give Up</button>' +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderSilhouetteSummary() {
  var s = state.silhouette;
  var correctCount = s.results.filter(function (r) { return r.correct; }).length;
  // "Quick guess" matches the exact threshold finishSilhouetteRound() already
  // uses for st.bestQuick (points >= 80, i.e. correct with 0-1 clues
  // revealed) — this is that same definition surfaced per-round instead of
  // only ever showing up as a lifetime-best stat.
  var quickGuesses = s.results.filter(function (r) { return r.correct && r.points >= 80; });
  var missed = s.results.filter(function (r) { return !r.correct; });
  return '<div class="panel stadium-game classic-broadcast classic-broadcast--silhouette">' +
    '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' + icon('trophy') + ' <h2 class="complete-banner-text">MYSTERY SOLVED</h2></div>' +
    '<h2 class="panel-title">NFL Silhouette Round Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + correctCount + ' / ' + s.queue.length + ' guessed</div>' +
    (quickGuesses.length ? '<div class="iq-insight">' + icon('zap') + ' ' + quickGuesses.length + ' quick guess' + (quickGuesses.length === 1 ? '' : 'es') + ' (1 clue or less): <b>' + quickGuesses.map(function (r) { return esc(r.name); }).join(', ') + '</b></div>' : '') +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (r) { return esc(r.name); }).join(', ') + '</div>' : (s.queue.length ? '<div class="blitz-missed">Clean sweep — you got every player!</div>' : '')) +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-silhouette-start="' + s.roundSize + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="silhouette">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('silhouette') + '</div>';
}
function renderSilhouetteScreen() {
  if (!state.silhouette) return renderSilhouetteSetup();
  if (state.silhouette.screen === 'summary') return renderSilhouetteSummary();
  return renderSilhouetteRound();
}

/* ============================== player from clues ==============================
   Director v0.5 local-only prototype. Consumes window.PLAYER_FROM_CLUES_V01
   (data/player-from-clues-v01.js, generated by
   tools/export_player_from_clues_frontend.py from the already-approved
   Engine package -- see GAME_DIRECTOR_V04_REPORT.md) as pure data. No football
   fact, clue text, or answer is invented or computed here -- this section only
   renders what the package already contains and checks a typed guess against
   the package's own answer.playerId/displayName for that specific puzzle.
   Modeled directly on the Silhouette section above (progressive clue reveal +
   typeahead guess + reveal state + queue + summary), with no scoring/ranked/
   leaderboard/rating integration per this milestone's explicit restrictions. */
var PLAYER_CLUES_PACKAGE = null;
var PLAYER_CLUES_VALIDATION_ERROR = null;
// Step 11: validated once at load, independently of construction -- refuses
// to let a malformed/unproven package reach the renderer at all.
function validatePlayerCluesPackage(pkg) {
  if (!pkg || typeof pkg !== 'object') return 'PACKAGE_MISSING';
  if (pkg.qaStatus !== 'PASSED') return 'QA_STATUS_NOT_PASSED';
  if (!Array.isArray(pkg.puzzles) || !pkg.puzzles.length) return 'NO_PUZZLES';
  var seenIds = {};
  for (var i = 0; i < pkg.puzzles.length; i++) {
    var p = pkg.puzzles[i];
    if (p.id == null || seenIds[p.id]) return 'DUPLICATE_OR_MISSING_PUZZLE_ID';
    seenIds[p.id] = true;
    if (!p.answer || !p.answer.playerId || !p.answer.displayName) return 'MISSING_ANSWER_IDENTITY';
    if (!Array.isArray(p.clues) || p.clues.length < 3) return 'MISSING_OR_INSUFFICIENT_CLUES';
    if (p.finalCandidateCount !== 1) return 'FINAL_CANDIDATE_COUNT_NOT_ONE';
    for (var j = 0; j < p.clues.length; j++) {
      var c = p.clues[j];
      if (!c || !c.text || !c.provenance || !c.provenance.sourceId || !c.provenance.verificationStatus) return 'MISSING_CLUE_PROVENANCE';
    }
  }
  return null;
}
function initPlayerCluesPackage() {
  if (!ENABLE_PLAYER_FROM_CLUES_V01) return;
  // Gateway dev-loop source swap (Director v0.6, Part O) -- default-off,
  // never the production path. Falls back to the static baseline whenever
  // the dev flag is off OR the Gateway-produced file hasn't been generated
  // yet (still the null placeholder -- see data/player-from-clues-gateway-dev.js).
  var useGatewayDev = ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01 && window.PLAYER_FROM_CLUES_GATEWAY_DEV;
  var source = useGatewayDev ? window.PLAYER_FROM_CLUES_GATEWAY_DEV : window.PLAYER_FROM_CLUES_V01;
  var err = validatePlayerCluesPackage(source);
  if (err) { PLAYER_CLUES_VALIDATION_ERROR = err; PLAYER_CLUES_PACKAGE = null; return; }
  PLAYER_CLUES_PACKAGE = source;
}
function playerCluesAnswerPool() {
  // Step 5: autocomplete pool = the distinct answer names already present in
  // THIS approved package -- nothing external, nothing invented.
  if (!PLAYER_CLUES_PACKAGE) return [];
  var seen = {}, out = [];
  PLAYER_CLUES_PACKAGE.puzzles.forEach(function (p) {
    if (!seen[p.answer.displayName]) { seen[p.answer.displayName] = true; out.push({ name: p.answer.displayName }); }
  });
  return out;
}
function playerCluesAvailableDecades() {
  // Real, derived from whatever decades this exact package actually
  // contains -- never a hardcoded list that could silently drift out of
  // sync with the data (see tools/export_player_from_clues_frontend.py's
  // _decade_for_puzzle()).
  if (!PLAYER_CLUES_PACKAGE) return [];
  var seen = {}, out = [];
  PLAYER_CLUES_PACKAGE.puzzles.forEach(function (p) {
    if (p.decade != null && !seen[p.decade]) { seen[p.decade] = true; out.push(p.decade); }
  });
  return out.sort(function (a, b) { return a - b; });
}
function playerCluesFilteredPuzzles() {
  if (!PLAYER_CLUES_PACKAGE) return [];
  var f = state.playerCluesFilter;
  return PLAYER_CLUES_PACKAGE.puzzles.filter(function (p) {
    if (f.decade !== 'any' && p.decade !== f.decade) return false;
    if (f.difficulty !== 'any' && p.difficultyBand !== f.difficulty) return false;
    return true;
  });
}
function setPlayerCluesFilter(key, value) {
  state.playerCluesFilter[key] = value;
  renderAll();
}
function loadPlayerCluesItem() {
  var s = state.playerClues;
  s.revealedCount = 1; // clue #1 visible immediately, per Step 4
  s.itemState = 'guessing';
  s.input = '';
  s.lastWrong = false;
  s.startedAt = Date.now();
}
// Share Your Result pass: a real, blocking defect found while testing the
// new Share button on this mode's summary screen -- with the default
// "Any Decade / Any Difficulty" filter (what a first-time player sees),
// the queue was the ENTIRE filtered pool (up to all 600 real puzzles),
// and advancePlayerClues() only ever sets screen='summary' after the
// LAST item in the queue -- so the summary screen (where Share, and the
// only "you're done" moment at all, lives) was practically unreachable in
// a normal session; a player would have to answer or give up on all 600
// in one sitting. Capped to the same real drawNoRepeat() sampling every
// other round-based mode (Quiz, etc.) already uses -- a real, bounded
// round each time, with no immediate repeats across sessions until the
// whole filtered pool has cycled through.
var PLAYER_CLUES_ROUND_SIZE = 5;
function startPlayerCluesRound() {
  if (!PLAYER_CLUES_PACKAGE) return;
  var pool = playerCluesFilteredPuzzles();
  if (!pool.length) return; // Start button is disabled in this state, but never proceed on 0 matches
  var f = state.playerCluesFilter;
  var ids = drawNoRepeat('playerClues_' + f.decade + '_' + f.difficulty, pool.map(function (p) { return p.id; }), Math.min(PLAYER_CLUES_ROUND_SIZE, pool.length));
  var byId = {};
  pool.forEach(function (p) { byId[p.id] = p; });
  state.playerClues = { queue: ids.map(function (id) { return byId[id]; }), index: 0, correctCount: 0, results: [], screen: 'round' };
  loadPlayerCluesItem();
  state.screen = 'playerClues';
  renderAll();
}
function revealPlayerCluesClue() {
  var s = state.playerClues;
  if (!s || s.itemState !== 'guessing') return;
  var p = s.queue[s.index];
  if (s.revealedCount < p.clues.length) s.revealedCount++;
  renderAll();
}
// Note: no playtest-logging call lives here by design -- exactly like the
// existing Draft playtest logger, playtest-player-from-clues.js wraps this
// function (and givePlayerCluesUp) from the OUTSIDE to observe results,
// so this file has zero knowledge of / dependency on that temporary
// instrumentation and works identically whether or not it's loaded.
function submitPlayerCluesGuess() {
  var s = state.playerClues;
  if (!s || s.itemState !== 'guessing') return;
  var norm = normName(s.input);
  if (!norm) return;
  var p = s.queue[s.index];
  var correct = normName(p.answer.displayName) === norm;
  if (correct) {
    s.results.push({ id: p.id, correct: true, cluesRevealed: s.revealedCount });
    s.correctCount++;
    s.lastWrong = false;
    s.itemState = 'revealed';
    playSound('correct');
  } else {
    s.lastWrong = true;
    playSound('wrong');
    if (s.revealedCount < p.clues.length) {
      s.revealedCount++;
    } else {
      // Out of clues and still wrong -- nothing left to reveal, end the puzzle.
      s.results.push({ id: p.id, correct: false, cluesRevealed: s.revealedCount });
      s.itemState = 'revealed';
    }
  }
  s.input = '';
  renderAll();
}
function givePlayerCluesUp() {
  var s = state.playerClues;
  if (!s || s.itemState !== 'guessing') return;
  var p = s.queue[s.index];
  s.results.push({ id: p.id, correct: false, cluesRevealed: s.revealedCount });
  s.itemState = 'revealed';
  renderAll();
}
function advancePlayerClues() {
  var s = state.playerClues;
  if (typeof stopSfx === 'function') stopSfx();
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; renderAll(); return; }
  s.index++;
  loadPlayerCluesItem();
  renderAll();
}
function playerCluesToolbarHtml(s) {
  return renderReadsShellHeader({
    icon: 'mystery', title: 'Who Am I',
    score: s ? s.correctCount + ' correct' : null,
    restartAttr: 'data-mode-restart="playerClues"',
  });
}
function renderPlayerCluesSetup() {
  if (!PLAYER_CLUES_PACKAGE) {
    return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues"><h2 class="panel-title">Player From Clues</h2>' +
      '<p class="mode-desc">These player clues couldn’t load. Try again in a moment.</p>' +
      '<div class="btn-row"><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  var f = state.playerCluesFilter;
  var decades = playerCluesAvailableDecades();
  var difficulties = ['Easy', 'Medium', 'Hard'];
  var matchCount = playerCluesFilteredPuzzles().length;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues">' +
    broadcastMarqueeHtml('NFL · IDENTITY FILE', 'WHO AM I?', 'Read the clues. Name the player. Fewer hints, bigger bragging rights.') +
    '<p class="mode-desc">' + esc(PLAYER_CLUES_PACKAGE.gameInstructions) + '</p>' +
    '<p class="mode-desc">' + PLAYER_CLUES_PACKAGE.puzzleCount + ' players. ' + PLAYER_CLUES_ROUND_SIZE + ' mysteries per round.</p>' +
    '<div class="broadcast-practice-note">Practice mode · These rounds don’t affect your rating or leaderboard.</div>' +
    '<div class="chip-row" role="group" aria-label="Filter by decade">' +
    '<button class="chip-toggle' + (f.decade === 'any' ? ' active' : '') + '" data-clues-filter-decade="any">Any Decade</button>' +
    decades.map(function (d) {
      return '<button class="chip-toggle' + (f.decade === d ? ' active' : '') + '" data-clues-filter-decade="' + d + '">' + d + 's</button>';
    }).join('') +
    '</div>' +
    '<div class="chip-row" role="group" aria-label="Filter by difficulty">' +
    '<button class="chip-toggle' + (f.difficulty === 'any' ? ' active' : '') + '" data-clues-filter-difficulty="any">Any Difficulty</button>' +
    difficulties.map(function (d) {
      return '<button class="chip-toggle' + (f.difficulty === d ? ' active' : '') + '" data-clues-filter-difficulty="' + d + '">' + d + '</button>';
    }).join('') +
    '</div>' +
    (matchCount ? '<p class="mode-desc">' + matchCount + ' puzzle' + (matchCount === 1 ? '' : 's') + ' match this filter.</p>'
      : '<p class="mode-desc blitz-feedback wrong">No puzzles match this combination — try a different decade or difficulty.</p>') +
    '<div class="btn-row"><button class="btn-primary" data-clues-start' + (matchCount ? '' : ' disabled') + '>Start</button></div>' +
    '</div>';
}
// Section: Who Am I -- a real mystery-identity presentation. Same
// typeahead + progressive-reveal interaction as before (zero logic
// change: still s.revealedCount/s.itemState/s.input), but its own real
// classes (.whoami-*) instead of borrowing Silhouette's/Blitz's/Grid's --
// a player should feel like they're uncovering an identity, not playing a
// worse version of a different mode.
function renderPlayerCluesRound() {
  var s = state.playerClues, p = s.queue[s.index];
  var totalClues = p.clues.length;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--clues whoami-panel">' + playerCluesToolbarHtml(s) +
    broadcastClueMeterHtml(s.revealedCount, totalClues) +
    quizProgressRowHtml('Puzzle ' + (s.index + 1) + ' of ' + s.queue.length, s.index, s.queue.length);
  if (s.itemState === 'revealed') {
    var lastResult = s.results[s.results.length - 1];
    var isCorrect = lastResult && lastResult.correct;
    html += '<div class="whoami-reveal ' + (isCorrect ? 'whoami-reveal-correct' : 'whoami-reveal-wrong') + '">' +
      '<div class="whoami-reveal-icon">' + icon(isCorrect ? 'check' : 'xMark') + '</div>' +
      '<div class="whoami-reveal-name">' + esc(p.answer.displayName) + '</div>' +
      '<div class="whoami-reveal-line">' + (isCorrect ? 'Identified in ' + lastResult.cluesRevealed + ' clue' + (lastResult.cluesRevealed === 1 ? '' : 's') : 'Not quite') + '</div>' +
      '</div>' +
      '<button class="btn-primary" data-clues-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Mystery Player') + '</button>';
  } else {
    html += '<div class="whoami-clue-count">' + icon('mystery') + ' Clue ' + s.revealedCount + ' of ' + totalClues + '</div>' +
      '<div class="whoami-clues">' +
      p.clues.slice(0, s.revealedCount).map(function (c, i) {
        return '<div class="whoami-clue' + (i === s.revealedCount - 1 ? ' whoami-clue-latest' : '') + '">' +
          '<span class="whoami-clue-num">' + (i + 1) + '</span>' +
          '<span class="whoami-clue-text">' + esc(c.text) + '</span></div>';
      }).join('') +
      '</div>' +
      (s.lastWrong ? '<div class="whoami-wrong-line" aria-live="polite">' + icon('xMark') + ' Not quite' + (s.revealedCount < totalClues ? ' — here’s another clue.' : '.') + '</div>' : '') +
      '<div class="whoami-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="clues-input" autocomplete="off" placeholder="Who is it?" value="' + esc(s.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="clues-input-typeahead" />' +
      '<div id="clues-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-clues-submit>Guess</button>' +
      '</div>' +
      '<div class="btn-row">' +
      (s.revealedCount < totalClues ? '<button class="btn-secondary" data-clues-hint>' + icon('search') + ' Reveal Next Clue</button>' : '') +
      '<button class="btn-secondary" data-clues-giveup>Give Up</button>' +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderPlayerCluesSummary() {
  var s = state.playerClues;
  var correctCount = s.results.filter(function (r) { return r.correct; }).length;
  var missed = s.results.filter(function (r) { return !r.correct; });
  var avgClues = s.results.length ? (s.results.reduce(function (sum, r) { return sum + r.cluesRevealed; }, 0) / s.results.length) : 0;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues">' +
    renderReadsShellHeader({ icon: 'mystery', title: 'Who Am I — Complete', hideExit: true }) +
    broadcastResultHtml('IDENTITY FILES · CLOSED', correctCount + '/' + s.queue.length, 'Players identified · ' + avgClues.toFixed(1) + ' clues used on average', correctCount === s.queue.length) +
    '<div class="whoami-summary-stats">' +
    '<span class="reads-shell-chip">Avg. ' + avgClues.toFixed(1) + ' clues used</span>' +
    '</div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (r) {
      var puzzle = PLAYER_CLUES_PACKAGE.puzzles.find(function (pp) { return pp.id === r.id; });
      return esc(puzzle ? puzzle.answer.displayName : String(r.id));
    }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you identified every player!</div>') +
    '<div class="summary-note">Practice round · Your rating and leaderboard are unchanged.</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-clues-start>Play Again</button>' +
    '<button class="btn-secondary" data-share="playerClues">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + recommendedModeHtml() + '</div>';
}
function renderPlayerCluesScreen() {
  if (!ENABLE_PLAYER_FROM_CLUES_V01) return renderHome();
  if (!state.playerClues) return renderPlayerCluesSetup();
  if (state.playerClues.screen === 'summary') return renderPlayerCluesSummary();
  return renderPlayerCluesRound();
}

/* ============================== CFB player from clues ==============================
   UI/UX Upgrade Pass: CFB counterpart, same shape/logic as the NFL section
   above, kept as its own parallel set of functions rather than a
   parametrized shared one -- matches this file's own established
   NFL/CFB-pair convention everywhere else (startGridRound/startCfbGridRound,
   etc.), and keeps zero risk of a CFB-specific change ever regressing the
   already-working NFL mode.
   Reliability pass (Pass 2.7): data/cfb-player-from-clues-v01.js is now
   real Engine output (3,300 puzzles, tools/export_cfb_player_from_clues_frontend.py),
   replacing a 12-puzzle hand-authored Heisman-only prototype that was
   never swapped for the real, already-working identify_player_from_clues/
   CFB_PLAYER_IDENTITY capability -- see that script's own module docstring
   for the full root-cause history. */
var CFB_PLAYER_CLUES_PACKAGE = null;
var CFB_PLAYER_CLUES_VALIDATION_ERROR = null;
function initCfbPlayerCluesPackage() {
  var source = window.CFB_PLAYER_FROM_CLUES_V01;
  var err = validatePlayerCluesPackage(source);
  if (err) { CFB_PLAYER_CLUES_VALIDATION_ERROR = err; CFB_PLAYER_CLUES_PACKAGE = null; return; }
  CFB_PLAYER_CLUES_PACKAGE = source;
}
function cfbPlayerCluesAnswerPool() {
  if (!CFB_PLAYER_CLUES_PACKAGE) return [];
  var seen = {}, out = [];
  CFB_PLAYER_CLUES_PACKAGE.puzzles.forEach(function (p) {
    if (!seen[p.answer.displayName]) { seen[p.answer.displayName] = true; out.push({ name: p.answer.displayName }); }
  });
  return out;
}
// Reliability pass (Pass 2.7): real decade/difficulty filtering, matching
// the NFL section's own playerCluesAvailableDecades()/
// playerCluesFilteredPuzzles()/setPlayerCluesFilter() exactly -- this pool
// now carries the same real decade/difficultyBand metadata (see
// tools/export_cfb_player_from_clues_frontend.py) that the NFL pack always
// has, so there's no longer a reason for the CFB screen to skip this step.
function cfbPlayerCluesAvailableDecades() {
  if (!CFB_PLAYER_CLUES_PACKAGE) return [];
  var seen = {}, out = [];
  CFB_PLAYER_CLUES_PACKAGE.puzzles.forEach(function (p) {
    if (p.decade != null && !seen[p.decade]) { seen[p.decade] = true; out.push(p.decade); }
  });
  return out.sort(function (a, b) { return a - b; });
}
function cfbPlayerCluesFilteredPuzzles() {
  if (!CFB_PLAYER_CLUES_PACKAGE) return [];
  var f = state.cfbPlayerCluesFilter;
  return CFB_PLAYER_CLUES_PACKAGE.puzzles.filter(function (p) {
    if (f.decade !== 'any' && p.decade !== f.decade) return false;
    // Player Experience pass: "Any Difficulty" means any of the real
    // Easy/Medium/Hard recognizable-player bands -- Sicko (zero real
    // recognizability signal, see cfb_player_from_clues.py) is a
    // separate, explicit, deliberately-chosen tier, never silently mixed
    // into the default experience a casual fan gets by picking "Any."
    if (f.difficulty === 'any') return p.difficultyBand !== 'Sicko';
    return p.difficultyBand === f.difficulty;
  });
}
function setCfbPlayerCluesFilter(key, value) {
  state.cfbPlayerCluesFilter[key] = value;
  renderAll();
}
function loadCfbPlayerCluesItem() {
  var s = state.cfbPlayerClues;
  s.revealedCount = 1;
  s.itemState = 'guessing';
  s.input = '';
  s.lastWrong = false;
  s.startedAt = Date.now();
}
// Share Your Result pass: same real drawNoRepeat()-sampled round-size cap
// as the NFL version above, for consistency -- this pool is small enough
// (12 puzzles) that grinding through all of it in one sitting was at
// least reachable (unlike NFL's 600), but every session played the exact
// same 12 puzzles in the exact same fixed order (.slice() never
// shuffles), which is its own real repetition problem on replay.
function startCfbPlayerCluesRound() {
  if (!CFB_PLAYER_CLUES_PACKAGE) return;
  var pool = cfbPlayerCluesFilteredPuzzles();
  if (!pool.length) return; // Start button is disabled in this state, but never proceed on 0 matches
  var f = state.cfbPlayerCluesFilter;
  var ids = drawNoRepeat('cfbPlayerClues_' + f.decade + '_' + f.difficulty, pool.map(function (p) { return p.id; }), Math.min(PLAYER_CLUES_ROUND_SIZE, pool.length));
  var byId = {};
  pool.forEach(function (p) { byId[p.id] = p; });
  state.cfbPlayerClues = { queue: ids.map(function (id) { return byId[id]; }), index: 0, correctCount: 0, results: [], screen: 'round' };
  loadCfbPlayerCluesItem();
  state.screen = 'cfbPlayerClues';
  renderAll();
}
function revealCfbPlayerCluesClue() {
  var s = state.cfbPlayerClues;
  if (!s || s.itemState !== 'guessing') return;
  var p = s.queue[s.index];
  if (s.revealedCount < p.clues.length) s.revealedCount++;
  renderAll();
}
function submitCfbPlayerCluesGuess() {
  var s = state.cfbPlayerClues;
  if (!s || s.itemState !== 'guessing') return;
  var norm = normName(s.input);
  if (!norm) return;
  var p = s.queue[s.index];
  var correct = normName(p.answer.displayName) === norm;
  if (correct) {
    s.results.push({ id: p.id, correct: true, cluesRevealed: s.revealedCount });
    s.correctCount++;
    s.lastWrong = false;
    s.itemState = 'revealed';
    playSound('correct');
  } else {
    s.lastWrong = true;
    playSound('wrong');
    if (s.revealedCount < p.clues.length) {
      s.revealedCount++;
    } else {
      s.results.push({ id: p.id, correct: false, cluesRevealed: s.revealedCount });
      s.itemState = 'revealed';
    }
  }
  s.input = '';
  renderAll();
}
function giveCfbPlayerCluesUp() {
  var s = state.cfbPlayerClues;
  if (!s || s.itemState !== 'guessing') return;
  var p = s.queue[s.index];
  s.results.push({ id: p.id, correct: false, cluesRevealed: s.revealedCount });
  s.itemState = 'revealed';
  renderAll();
}
function advanceCfbPlayerClues() {
  var s = state.cfbPlayerClues;
  if (typeof stopSfx === 'function') stopSfx();
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; renderAll(); return; }
  s.index++;
  loadCfbPlayerCluesItem();
  renderAll();
}
function cfbPlayerCluesToolbarHtml(s) {
  return renderReadsShellHeader({
    icon: 'mystery', title: 'Who Am I (CFB)',
    score: s ? s.correctCount + ' correct' : null,
    restartAttr: 'data-mode-restart="cfbPlayerClues"',
  });
}
function renderCfbPlayerCluesSetup() {
  if (!CFB_PLAYER_CLUES_PACKAGE) {
    return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues broadcast-finish--cfb"><h2 class="panel-title">CFB Player From Clues</h2>' +
      '<p class="mode-desc">These college player clues couldn’t load. Try again in a moment.</p>' +
      '<div class="btn-row"><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  // Reliability pass (Pass 2.7): real Engine-generated pool, replacing the
  // old 12-puzzle hand-authored Heisman-only prototype -- same decade/
  // difficulty filter UI the NFL screen already has, since this pool now
  // carries the same real metadata.
  // Player Experience pass (user request: "use players that are more
  // relevant and that casual and normal cfb fans would know and then make
  // a sicko difficulty where CFB sickos can test themselves"): Easy/Medium/
  // Hard now draw exclusively from a real recognizability-signal pool
  // (All-America/NFL-drafted/genuine season-stat notability); Sicko is a
  // separate, explicit, opt-in tier with zero recognizability signal --
  // never blended into "Any Difficulty" (see cfbPlayerCluesFilteredPuzzles()).
  var f = state.cfbPlayerCluesFilter;
  var decades = cfbPlayerCluesAvailableDecades();
  var difficulties = ['Easy', 'Medium', 'Hard', 'Sicko'];
  var matchCount = cfbPlayerCluesFilteredPuzzles().length;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues broadcast-finish--cfb">' +
    broadcastMarqueeHtml('CFB · IDENTITY FILE', 'WHO AM I?', 'Read the clues. Name the player. Fewer hints, bigger bragging rights.') +
    '<p class="mode-desc">' + esc(CFB_PLAYER_CLUES_PACKAGE.gameInstructions) + '</p>' +
    '<p class="mode-desc">' + CFB_PLAYER_CLUES_PACKAGE.puzzleCount + ' college players. ' + PLAYER_CLUES_ROUND_SIZE + ' mysteries per round.</p>' +
    '<div class="broadcast-practice-note">Practice mode · These rounds don’t affect your rating or leaderboard.</div>' +
    '<div class="chip-row" role="group" aria-label="Filter by decade">' +
    '<button class="chip-toggle' + (f.decade === 'any' ? ' active' : '') + '" data-cfb-clues-filter-decade="any">Any Decade</button>' +
    decades.map(function (d) {
      return '<button class="chip-toggle' + (f.decade === d ? ' active' : '') + '" data-cfb-clues-filter-decade="' + d + '">' + d + 's</button>';
    }).join('') +
    '</div>' +
    '<div class="chip-row" role="group" aria-label="Filter by difficulty">' +
    '<button class="chip-toggle' + (f.difficulty === 'any' ? ' active' : '') + '" data-cfb-clues-filter-difficulty="any">Any Difficulty</button>' +
    difficulties.map(function (d) {
      return '<button class="chip-toggle' + (f.difficulty === d ? ' active' : '') + '" data-cfb-clues-filter-difficulty="' + d + '">' + d + '</button>';
    }).join('') +
    '</div>' +
    (matchCount ? '<p class="mode-desc">' + matchCount + ' puzzle' + (matchCount === 1 ? '' : 's') + ' match this filter.</p>'
      : '<p class="mode-desc blitz-feedback wrong">No puzzles match this combination — try a different decade or difficulty.</p>') +
    '<div class="btn-row"><button class="btn-primary" data-cfb-clues-start' + (matchCount ? '' : ' disabled') + '>Start</button></div>' +
    '</div>';
}
function renderCfbPlayerCluesRound() {
  var s = state.cfbPlayerClues, p = s.queue[s.index];
  var totalClues = p.clues.length;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--clues broadcast-finish--cfb whoami-panel">' + cfbPlayerCluesToolbarHtml(s) +
    broadcastClueMeterHtml(s.revealedCount, totalClues) +
    quizProgressRowHtml('Puzzle ' + (s.index + 1) + ' of ' + s.queue.length, s.index, s.queue.length);
  if (s.itemState === 'revealed') {
    var lastResult = s.results[s.results.length - 1];
    var isCorrect = lastResult && lastResult.correct;
    html += '<div class="whoami-reveal ' + (isCorrect ? 'whoami-reveal-correct' : 'whoami-reveal-wrong') + '">' +
      '<div class="whoami-reveal-icon">' + icon(isCorrect ? 'check' : 'xMark') + '</div>' +
      '<div class="whoami-reveal-name">' + esc(p.answer.displayName) + '</div>' +
      '<div class="whoami-reveal-line">' + (isCorrect ? 'Identified in ' + lastResult.cluesRevealed + ' clue' + (lastResult.cluesRevealed === 1 ? '' : 's') : 'Not quite') + '</div>' +
      '</div>' +
      '<button class="btn-primary" data-cfb-clues-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Mystery Player') + '</button>';
  } else {
    html += '<div class="whoami-clue-count">' + icon('mystery') + ' Clue ' + s.revealedCount + ' of ' + totalClues + '</div>' +
      '<div class="whoami-clues">' +
      p.clues.slice(0, s.revealedCount).map(function (c, i) {
        return '<div class="whoami-clue' + (i === s.revealedCount - 1 ? ' whoami-clue-latest' : '') + '">' +
          '<span class="whoami-clue-num">' + (i + 1) + '</span>' +
          '<span class="whoami-clue-text">' + esc(c.text) + '</span></div>';
      }).join('') +
      '</div>' +
      (s.lastWrong ? '<div class="whoami-wrong-line" aria-live="polite">' + icon('xMark') + ' Not quite' + (s.revealedCount < totalClues ? ' — here’s another clue.' : '.') + '</div>' : '') +
      '<div class="whoami-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="cfb-clues-input" autocomplete="off" placeholder="Who is it?" value="' + esc(s.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cfb-clues-input-typeahead" />' +
      '<div id="cfb-clues-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-cfb-clues-submit>Guess</button>' +
      '</div>' +
      '<div class="btn-row">' +
      (s.revealedCount < totalClues ? '<button class="btn-secondary" data-cfb-clues-hint>' + icon('search') + ' Reveal Next Clue</button>' : '') +
      '<button class="btn-secondary" data-cfb-clues-giveup>Give Up</button>' +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderCfbPlayerCluesSummary() {
  var s = state.cfbPlayerClues;
  var correctCount = s.results.filter(function (r) { return r.correct; }).length;
  var missed = s.results.filter(function (r) { return !r.correct; });
  var avgClues = s.results.length ? (s.results.reduce(function (sum, r) { return sum + r.cluesRevealed; }, 0) / s.results.length) : 0;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--clues broadcast-finish--cfb">' +
    renderReadsShellHeader({ icon: 'mystery', title: 'Who Am I (CFB) — Complete', hideExit: true }) +
    broadcastResultHtml('IDENTITY FILES · CLOSED', correctCount + '/' + s.queue.length, 'Players identified · ' + avgClues.toFixed(1) + ' clues used on average', correctCount === s.queue.length) +
    '<div class="whoami-summary-stats"><span class="reads-shell-chip">Avg. ' + avgClues.toFixed(1) + ' clues used</span></div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (r) {
      var puzzle = CFB_PLAYER_CLUES_PACKAGE.puzzles.find(function (pp) { return pp.id === r.id; });
      return esc(puzzle ? puzzle.answer.displayName : String(r.id));
    }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you identified every player!</div>') +
    '<div class="summary-note">Practice round · Your rating and leaderboard are unchanged.</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-clues-start>Play Again</button>' +
    '<button class="btn-secondary" data-share="cfbPlayerClues">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + recommendedModeHtml() + '</div>';
}
function renderCfbPlayerCluesScreen() {
  if (!ENABLE_CFB_PLAYER_FROM_CLUES_V01) return renderHome();
  if (!state.cfbPlayerClues) return renderCfbPlayerCluesSetup();
  if (state.cfbPlayerClues.screen === 'summary') return renderCfbPlayerCluesSummary();
  return renderCfbPlayerCluesRound();
}

/* ============================== engine game shell ==============================
   v1.5: moved to engine-game-ui.js (its own file, loaded before this one --
   see index.html) -- ENGINE_PILOT_MODES, ENGINE_GAME_SCREEN, and every
   startEnginePilotRound/pickEnginePilotAnswer/advanceEnginePilot/
   renderEnginePilotScreen function this app.js still calls (state init
   above, event dispatch and render dispatch below, hash-routing bootstrap
   near the end of this file) now live there. Grep engine-game-ui.js if
   you're looking for the Draft/Championship engine-pilot implementation. */

/* ============================== football iq test ============================== */
var IQ_TEST_SIZE = 25;
function currentIQQuestion() {
  var s = state.iq;
  var id = s.queue[s.index];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startIQTest() {
  beginProgressSession('iq');
  var size = Math.min(IQ_TEST_SIZE, QUIZ.length);
  var queue = drawNoRepeat('iq', QUIZ.map(function (q) { return q.id; }), size);
  state.iq = { queue: queue, index: 0, answers: [], screen: 'test', ranked: state.rankedPref.iq !== false };
  state.screen = 'iq';
  renderAll();
}
function answerIQQuestion(i) {
  var s = state.iq;
  if (!s || s.screen !== 'test') return;
  var q = currentIQQuestion();
  s.answers.push({ category: q.category, correct: i === q.correctIndex });
  if (s.index + 1 >= s.queue.length) {
    s.screen = 'result';
    finishIQTest();
  } else {
    s.index++;
  }
  renderAll();
}
function iqTitle(iq) {
  if (iq >= 160) return 'Football Genius';
  if (iq >= 140) return 'Elite Analyst';
  if (iq >= 120) return 'Draft Room Ready';
  if (iq >= 100) return 'Solid Fan';
  if (iq >= 85) return 'Casual Watcher';
  if (iq >= 70) return 'Still Learning the Rules';
  return 'Needs a Football 101 Class';
}
function finishIQTest() {
  var s = state.iq;
  var correct = s.answers.filter(function (a) { return a.correct; }).length;
  var total = s.answers.length;
  var iq = Math.round(60 + (correct / total) * 100);
  s.correct = correct;
  s.total = total;
  s.iqScore = iq;
  if (s.ranked !== false) {
    var st = state.stats.iq;
    st.testsTaken++;
    if (iq > st.bestIQ) st.bestIQ = iq;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correct / total);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('iq', { bestIQ: st.bestIQ, testsTaken: st.testsTaken });
  }
  playSound(iq <= 60 ? 'boo' : 'complete');
}
// Shared by NFL/CFB IQ Test results — turns the flat per-category breakdown
// (already existed) into one readable "here's what actually moved your
// score" insight line, only when there's enough of a spread to say anything
// meaningful (needs at least 2 categories with a different hit rate, and at
// least 2 questions in each side so a single lucky/unlucky guess can't
// anoint a whole category as your "strongest"/"weakest").
function iqStrongestWeakest(breakdown) {
  var eligible = breakdown.filter(function (b) { return b.total >= 2; });
  if (eligible.length < 2) return null;
  var byPct = eligible.slice().sort(function (a, b) { return (b.correct / b.total) - (a.correct / a.total); });
  var best = byPct[0], worst = byPct[byPct.length - 1];
  if (best.correct / best.total === worst.correct / worst.total) return null;
  return { best: best, worst: worst };
}
function iqCategoryBreakdown(s) {
  var byCat = {};
  s.answers.forEach(function (a) {
    if (!byCat[a.category]) byCat[a.category] = { correct: 0, total: 0 };
    byCat[a.category].total++;
    if (a.correct) byCat[a.category].correct++;
  });
  return Object.keys(byCat).sort().map(function (cat) { return { category: cat, correct: byCat[cat].correct, total: byCat[cat].total }; });
}

function renderIQSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq">' +
    broadcastMarqueeHtml('NFL · SCOUTING COMBINE', 'TEST YOUR FOOTBALL IQ', IQ_TEST_SIZE + ' questions. One final scouting report.') +
    broadcastScorebugHtml([['QUESTIONS', IQ_TEST_SIZE], ['FEEDBACK', 'AT THE END'], ['IQ SCALE', '60–160']]) +
    '<p class="mode-desc">' + IQ_TEST_SIZE + ' questions pulled from every category, mixed difficulty. No right/wrong feedback until the end — just like a real test. Your score maps to a Football IQ from 60-160, plus a category-by-category breakdown.</p>' +
    rankedToggleHtml('iq') +
    '<button class="btn-primary" data-iq-start>Start Test</button>' +
    '</div>';
}
function renderIQTest() {
  var s = state.iq, q = currentIQQuestion();
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq">' + modeToolbarHtml('iq', s.ranked) +
    broadcastScorebugHtml([['QUESTION', (s.index + 1) + '/' + s.queue.length], ['CATEGORY', q.category], ['REPORT', 'SEALED']]) +
    '<div class="game-progress"><span style="width:' + Math.round(s.index / s.queue.length * 100) + '%"></span></div>' +
    '<section class="stadium-question-card"><span class="stadium-question-kicker">COMBINE QUESTION ' + (s.index + 1) + '</span><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-iq-answer="' + i + '">' + '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span>' + '</button>';
    }).join('') +
    '</div></div>';
}
function renderIQResult() {
  var s = state.iq;
  var breakdown = iqCategoryBreakdown(s);
  var insight = iqStrongestWeakest(breakdown);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq">' +
    broadcastResultHtml('NFL · SCOUTING REPORT', s.iqScore, iqTitle(s.iqScore), s.iqScore >= 130) +
    '<div class="summary-score">' + s.correct + ' / ' + s.total + ' correct</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    (insight ? '<div class="iq-insight">Strongest: <b>' + esc(insight.best.category) + '</b> (' + insight.best.correct + '/' + insight.best.total + ') &middot; Weakest: <b>' + esc(insight.worst.category) + '</b> (' + insight.worst.correct + '/' + insight.worst.total + ')</div>' : '') +
    '<div class="iq-breakdown">' +
    breakdown.map(function (b) { return '<div class="iq-breakdown-row"><span>' + esc(b.category) + '</span><span>' + b.correct + ' / ' + b.total + '</span><div class="broadcast-category-meter" aria-hidden="true"><i style="width:' + Math.round(b.correct / b.total * 100) + '%"></i></div></div>'; }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-iq-start>Retake Test</button>' +
    '<button class="btn-secondary" data-share="iq">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderIQScreen() {
  if (!state.iq) return renderIQSetup();
  if (state.iq.screen === 'result') return renderIQResult();
  return renderIQTest();
}

/* ============================== intro test (football rating) ============================== */
function renderIntroIntro() {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + icon('football') + ' Welcome, ' + esc(state.name) + '!</h2>' +
    '<p class="mode-desc">Before you dive in, answer ' + INTRO_TEST_SIZE + ' quick questions — a mix of NFL and College Football — to set your starting Football Rating. From here it drifts up or down a little based on how you do in every game mode you play, so it settles into a real skill rating over time instead of a one-off score.</p>' +
    '<button class="btn-primary" data-intro-begin>Start</button>' +
    '<p class="mode-desc" style="margin-top:10px;"><a href="#" data-intro-skip>Skip for now</a></p>' +
    '</div>';
}
function renderIntroQuestion() {
  var t = state.introTest, q = currentIntroQuestion();
  return '<div class="panel">' +
    '<div class="quiz-progress">Question ' + (t.index + 1) + ' of ' + t.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-intro-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderIntroResult() {
  var t = state.introTest;
  return '<div class="panel">' +
    '<h2 class="panel-title">Your Starting Football Rating</h2>' +
    '<div class="iq-score">' + t.score + '</div>' +
    '<div class="summary-score">' + t.correct + ' / ' + t.total + ' correct</div>' +
    '<div class="summary-note">This is your baseline — every game mode you play from here nudges it up or down a little based on how you do.</div>' +
    '<button class="btn-primary" data-intro-continue>Let\'s Play</button>' +
    '</div>';
}
function renderIntroScreen() {
  var t = state.introTest;
  if (t.screen === 'intro') return renderIntroIntro();
  if (t.screen === 'result') return renderIntroResult();
  return renderIntroQuestion();
}

/* ============================== college football iq test ============================== */
function currentCfbIQQuestion() {
  var s = state.cfbIq;
  var id = s.queue[s.index];
  return CFB.find(function (q) { return q.id === id; });
}
function startCfbIQTest() {
  beginProgressSession('cfbIq');
  var size = Math.min(IQ_TEST_SIZE, CFB.length);
  var queue = drawNoRepeat('cfbiq', CFB.map(function (q) { return q.id; }), size);
  state.cfbIq = { queue: queue, index: 0, answers: [], screen: 'test', ranked: state.rankedPref.cfbIq !== false };
  state.screen = 'cfbIq';
  renderAll();
}
function answerCfbIQQuestion(i) {
  var s = state.cfbIq;
  if (!s || s.screen !== 'test') return;
  var q = currentCfbIQQuestion();
  s.answers.push({ category: q.category, correct: i === q.correctIndex });
  if (s.index + 1 >= s.queue.length) {
    s.screen = 'result';
    finishCfbIQTest();
  } else {
    s.index++;
  }
  renderAll();
}
function cfbIqTitle(iq) {
  if (iq >= 160) return 'CFB Historian';
  if (iq >= 140) return 'Elite Analyst';
  if (iq >= 120) return 'Saturday Regular';
  if (iq >= 100) return 'Solid Fan';
  if (iq >= 85) return 'Casual Watcher';
  if (iq >= 70) return 'Still Learning the Rules';
  return 'Needs a CFB 101 Class';
}
function finishCfbIQTest() {
  var s = state.cfbIq;
  var correct = s.answers.filter(function (a) { return a.correct; }).length;
  var total = s.answers.length;
  var iq = Math.round(60 + (correct / total) * 100);
  s.correct = correct;
  s.total = total;
  s.iqScore = iq;
  if (s.ranked !== false) {
    var st = state.stats.cfbIq;
    st.testsTaken++;
    if (iq > st.bestIQ) st.bestIQ = iq;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correct / total);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbIq', { bestIQ: st.bestIQ, testsTaken: st.testsTaken });
  }
  playSound(iq <= 60 ? 'boo' : 'complete');
}
function cfbIqCategoryBreakdown(s) {
  var byCat = {};
  s.answers.forEach(function (a) {
    if (!byCat[a.category]) byCat[a.category] = { correct: 0, total: 0 };
    byCat[a.category].total++;
    if (a.correct) byCat[a.category].correct++;
  });
  return Object.keys(byCat).sort().map(function (cat) { return { category: cat, correct: byCat[cat].correct, total: byCat[cat].total }; });
}

function renderCfbIQSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq broadcast-finish--cfb">' +
    broadcastMarqueeHtml('CFB · SCOUTING COMBINE', 'TEST YOUR FOOTBALL IQ', IQ_TEST_SIZE + ' questions. One final scouting report.') +
    broadcastScorebugHtml([['QUESTIONS', IQ_TEST_SIZE], ['FEEDBACK', 'AT THE END'], ['IQ SCALE', '60–160']]) +
    '<p class="mode-desc">' + IQ_TEST_SIZE + ' CFB questions pulled from every category, mixed difficulty. No right/wrong feedback until the end. Your score maps to a CFB IQ from 60-160, plus a category-by-category breakdown.</p>' +
    rankedToggleHtml('cfbIq') +
    '<button class="btn-primary" data-cfb-iq-start>Start Test</button>' +
    '</div>';
}
function renderCfbIQTest() {
  var s = state.cfbIq, q = currentCfbIQQuestion();
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq broadcast-finish--cfb">' + modeToolbarHtml('cfbIq', s.ranked) +
    broadcastScorebugHtml([['QUESTION', (s.index + 1) + '/' + s.queue.length], ['CATEGORY', q.category], ['REPORT', 'SEALED']]) +
    '<div class="game-progress"><span style="width:' + Math.round(s.index / s.queue.length * 100) + '%"></span></div>' +
    '<section class="stadium-question-card"><span class="stadium-question-kicker">COMBINE QUESTION ' + (s.index + 1) + '</span><div class="quiz-question stadium-question">' + esc(q.question) + '</div></section>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-cfb-iq-answer="' + i + '">' + '<span class="broadcast-option-letter">' + String.fromCharCode(65 + i) + '</span><span>' + esc(opt) + '</span>' + '</button>';
    }).join('') +
    '</div></div>';
}
function renderCfbIQResult() {
  var s = state.cfbIq;
  var breakdown = cfbIqCategoryBreakdown(s);
  var insight = iqStrongestWeakest(breakdown);
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--iq broadcast-finish--cfb">' +
    broadcastResultHtml('CFB · SCOUTING REPORT', s.iqScore, cfbIqTitle(s.iqScore), s.iqScore >= 130) +
    '<div class="summary-score">' + s.correct + ' / ' + s.total + ' correct</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    (insight ? '<div class="iq-insight">Strongest: <b>' + esc(insight.best.category) + '</b> (' + insight.best.correct + '/' + insight.best.total + ') &middot; Weakest: <b>' + esc(insight.worst.category) + '</b> (' + insight.worst.correct + '/' + insight.worst.total + ')</div>' : '') +
    '<div class="iq-breakdown">' +
    breakdown.map(function (b) { return '<div class="iq-breakdown-row"><span>' + esc(b.category) + '</span><span>' + b.correct + ' / ' + b.total + '</span><div class="broadcast-category-meter" aria-hidden="true"><i style="width:' + Math.round(b.correct / b.total * 100) + '%"></i></div></div>'; }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-iq-start>Retake Test</button>' +
    '<button class="btn-secondary" data-share="cfbIq">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbIQScreen() {
  if (!state.cfbIq) return renderCfbIQSetup();
  if (state.cfbIq.screen === 'result') return renderCfbIQResult();
  return renderCfbIQTest();
}

/* ============================== 17-0 legends draft ============================== */
var LEGENDS_TEAMS = window.LEGENDS_TEAMS || [];
var PLAYER_META = window.PLAYER_META || {};
var LEGENDS_DUOS = window.LEGENDS_DUOS || { legendary: [], elite: [] };
var CFB_LEGENDS_TEAMS = window.CFB_LEGENDS_TEAMS || [];
var CFB_PLAYER_META = window.CFB_PLAYER_META || {};
var CFB_LEGENDS_DUOS = window.CFB_LEGENDS_DUOS || { legendary: [], elite: [] };
var LEGENDS_SLOTS = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX'];
function legendsEligibleSlots(position) {
  if (position === 'QB') return ['QB'];
  if (position === 'RB') return ['RB1', 'RB2', 'FLEX'];
  if (position === 'WR') return ['WR1', 'WR2', 'FLEX'];
  if (position === 'TE') return ['TE', 'FLEX'];
  return [];
}
function legendsPlayerTeams(name) {
  var teams = [];
  LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (p.name === name && teams.indexOf(t.team) === -1) teams.push(t.team);
    });
  });
  return teams;
}
var LEGENDS_PERFECT_SCORE = null;
function legendsPerfectScore() {
  if (LEGENDS_PERFECT_SCORE !== null) return LEGENDS_PERFECT_SCORE;
  var byPos = { QB: [], RB: [], WR: [], TE: [] };
  LEGENDS_TEAMS.forEach(function (t) { t.players.forEach(function (p) { if (byPos[p.position]) byPos[p.position].push(p.fppg); }); });
  Object.keys(byPos).forEach(function (k) { byPos[k].sort(function (a, b) { return b - a; }); });
  // Real fix: the old formula summed the single #1 all-time FPPG at every
  // slot (QB/RB/RB/WR/WR/TE/FLEX, with FLEX pulling yet another #1-or-#2)
  // plus a flat +14 chemistry bonus assumed for free. Every one of those
  // values can come from a different, unconnected real team-season, and the
  // draft is 7 rounds of a single random roll each (only 1 team re-roll + 1
  // year re-roll total) -- landing on the literal all-time #1 at every slot
  // in one session is astronomically improbable, making 17-0 effectively
  // unreachable (reported directly by the project owner after playing).
  // Using the 3rd-best (not #1) at each slot as the "elite tier" reference
  // -- there are 3 real chances to roll into that tier across the pool
  // instead of exactly 1 -- and a smaller, real +6 chemistry estimate
  // (2-3 genuine bonus pairs, not an assumed maximum) brings the ceiling
  // down to something a skilled, lucky run can actually clear.
  var maxQB = byPos.QB[2] || byPos.QB[0] || 25;
  var maxRB = byPos.RB[2] || byPos.RB[0] || 22;
  var maxWR = byPos.WR[2] || byPos.WR[0] || 22;
  var maxTE = byPos.TE[2] || byPos.TE[0] || 18;
  var maxFlex = Math.max(byPos.RB[3] || maxRB, byPos.WR[3] || maxWR, maxTE);
  LEGENDS_PERFECT_SCORE = maxQB + maxRB * 2 + maxWR * 2 + maxTE + maxFlex + 6;
  return LEGENDS_PERFECT_SCORE;
}
function legendsRollEntry() { return LEGENDS_TEAMS[Math.floor(Math.random() * LEGENDS_TEAMS.length)]; }
function legendsOpenSlotCount(slots, position) {
  return legendsEligibleSlots(position).filter(function (s) { return !slots[s]; }).length;
}
function legendsPickedNames(slots) {
  return LEGENDS_SLOTS.map(function (sl) { return slots[sl] && slots[sl].name; }).filter(Boolean);
}
function legendsRollHasLegalPick(entry, slots) {
  var picked = legendsPickedNames(slots);
  return entry.players.some(function (p) { return legendsOpenSlotCount(slots, p.position) > 0 && picked.indexOf(p.name) === -1; });
}
function legendsDoRoll(state_) {
  var entry = legendsRollEntry(), tries = 0;
  while (!legendsRollHasLegalPick(entry, state_.slots) && tries < 500) { entry = legendsRollEntry(); tries++; }
  state_.rolledEntry = entry;
}
function startLegends() {
  beginProgressSession('legends');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  var slots = {};
  LEGENDS_SLOTS.forEach(function (s) { slots[s] = null; });
  state.legends = { screen: 'draft', round: 1, slots: slots, teamRerollUsed: false, yearRerollUsed: false, rolledEntry: null, lastPick: null, ranked: state.rankedPref.legends !== false };
  legendsDoRoll(state.legends);
  state.screen = 'legends';
  renderAll();
}
function legendsPickPlayer(playerIdx) {
  var s = state.legends;
  if (!s || s.screen !== 'draft') return;
  var entry = s.rolledEntry, p = entry.players[playerIdx];
  if (legendsPickedNames(s.slots).indexOf(p.name) !== -1) return;
  var openSlots = legendsEligibleSlots(p.position).filter(function (sl) { return !s.slots[sl]; });
  if (!openSlots.length) return;
  var slot = openSlots[0];
  if (openSlots.length > 1 && openSlots.indexOf('FLEX') !== -1) {
    var nonFlex = openSlots.filter(function (sl) { return sl !== 'FLEX'; });
    if (nonFlex.length) slot = nonFlex[0];
  }
  s.slots[slot] = { name: p.name, position: p.position, fppg: p.fppg, team: entry.team, year: entry.year };
  s.lastPick = p.name + ' added at ' + legendsSlotLabel(slot);
  if (s.round >= 7) {
    s.screen = 'result';
    finishLegends();
  } else {
    s.round++;
    legendsDoRoll(s);
  }
  renderAll();
}
function legendsRerollTeam() {
  var s = state.legends;
  if (!s || s.screen !== 'draft' || s.teamRerollUsed) return;
  s.teamRerollUsed = true;
  var current = s.rolledEntry.team;
  var options = LEGENDS_TEAMS.filter(function (t) { return t.team !== current && legendsRollHasLegalPick(t, s.slots); });
  s.rolledEntry = options.length ? options[Math.floor(Math.random() * options.length)] : s.rolledEntry;
  renderAll();
}
function legendsRerollYear() {
  var s = state.legends;
  if (!s || s.screen !== 'draft' || s.yearRerollUsed) return;
  s.yearRerollUsed = true;
  var current = s.rolledEntry;
  var options = LEGENDS_TEAMS.filter(function (t) { return t.team === current.team && t.year !== current.year && legendsRollHasLegalPick(t, s.slots); });
  if (!options.length) options = LEGENDS_TEAMS.filter(function (t) { return legendsRollHasLegalPick(t, s.slots); });
  s.rolledEntry = options.length ? options[Math.floor(Math.random() * options.length)] : s.rolledEntry;
  renderAll();
}
function legendsDuoMatch(list, a, b) {
  return list.some(function (pair) { return (pair[0] === a && pair[1] === b) || (pair[0] === b && pair[1] === a); });
}
function legendsCalcChemistry(picks) {
  var bonus = {}, log = [];
  picks.forEach(function (p) { bonus[p.name] = 0; });
  for (var i = 0; i < picks.length; i++) {
    for (var j = i + 1; j < picks.length; j++) {
      var a = picks[i], b = picks[j], pairBonus = 0, reasons = [];
      var metaA = PLAYER_META[a.name] || {}, metaB = PLAYER_META[b.name] || {};
      if (a.team === b.team && a.year === b.year) { pairBonus += 2; reasons.push('Same Team (+2)'); }
      if (metaA.college && metaA.college === metaB.college) { pairBonus += 2; reasons.push('Same College (+2)'); }
      if (metaA.draftYear && metaA.draftYear === metaB.draftYear) { pairBonus += 1; reasons.push('Same Draft (+1)'); }
      var teamsA = legendsPlayerTeams(a.name), teamsB = legendsPlayerTeams(b.name);
      if (teamsA.some(function (t) { return teamsB.indexOf(t) !== -1; })) { pairBonus += 1; reasons.push('Past Teammates (+1)'); }
      if (legendsDuoMatch(LEGENDS_DUOS.legendary, a.name, b.name)) { pairBonus += 2; reasons.push('Legendary Connection (+2)'); }
      else if (legendsDuoMatch(LEGENDS_DUOS.elite, a.name, b.name)) { pairBonus += 1; reasons.push('Elite Connection (+1)'); }
      if (pairBonus > 0) {
        bonus[a.name] += pairBonus;
        bonus[b.name] += pairBonus;
        log.push({ a: a.name, b: b.name, bonus: pairBonus, reasons: reasons });
      }
    }
  }
  return { bonus: bonus, log: log };
}
function legendsGrade(pct) {
  if (pct >= 0.95) return { grade: 'S', label: 'GOAT' };
  if (pct >= 0.88) return { grade: 'A+', label: 'Iconic' };
  if (pct >= 0.80) return { grade: 'A', label: 'Undisputed Champ' };
  if (pct >= 0.72) return { grade: 'A-', label: 'League Champ' };
  if (pct >= 0.64) return { grade: 'B+', label: 'Runner-Up' };
  if (pct >= 0.56) return { grade: 'B', label: '2nd Round Exit' };
  if (pct >= 0.48) return { grade: 'B-', label: 'First Round Exit' };
  if (pct >= 0.40) return { grade: 'C+', label: 'Missed Playoffs' };
  if (pct >= 0.32) return { grade: 'C', label: 'Mid' };
  if (pct >= 0.22) return { grade: 'D', label: 'Rebuilding' };
  return { grade: 'F', label: 'Toilet Bowl' };
}
function finishLegends() {
  var s = state.legends;
  var picks = LEGENDS_SLOTS.map(function (slot) { return Object.assign({ slot: slot }, s.slots[slot]); });
  var chem = legendsCalcChemistry(picks);
  var baseTotal = 0, finalTotal = 0;
  picks.forEach(function (p) {
    var b = chem.bonus[p.name] || 0;
    p.chemistry = b;
    p.finalFppg = p.fppg + b;
    baseTotal += p.fppg;
    finalTotal += p.finalFppg;
  });
  var perfect = legendsPerfectScore();
  var pct = Math.max(0, Math.min(1, finalTotal / perfect));
  var wins = Math.round(17 * pct);
  var losses = 17 - wins;
  var g = legendsGrade(pct);
  s.picks = picks;
  s.chemLog = chem.log;
  s.baseTotal = Math.round(baseTotal * 10) / 10;
  s.finalTotal = Math.round(finalTotal * 10) / 10;
  s.perfectScore = Math.round(perfect * 10) / 10;
  s.wins = wins;
  s.losses = losses;
  s.grade = g.grade;
  s.gradeLabel = g.label;
  if (s.ranked !== false) {
    var st = state.stats.legends;
    st.gamesPlayed++;
    if (wins > st.bestWins || (wins === st.bestWins && finalTotal > st.bestScore)) { st.bestWins = wins; st.bestScore = s.finalTotal; st.bestGrade = g.grade; }
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct * 100);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('legends', { bestWins: st.bestWins, bestRecord: st.bestWins + '-' + (17 - st.bestWins), bestScore: st.bestScore, bestGrade: st.bestGrade, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('legends', wins + '-' + losses + ' (' + g.grade + ')', pct * 100);
  h2hSubmitModeResult('legends', wins, 17);
  playSound(g.grade === 'F' ? 'boo' : 'complete');
}

function renderLegendsSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--roster game-intro game-intro-legends">' +
    '<div class="game-intro-icon">' + icon('trophy') + '</div><div class="game-intro-eyebrow">Build the perfect roster</div>' +
    '<h2 class="game-intro-title">Can You Go 17–0?</h2>' +
    '<p class="game-intro-copy">Seven team-seasons. Seven picks. Stack stars, hunt chemistry, and build a roster good enough to finish perfect.</p>' +
    '<div class="game-intro-features"><span>' + icon('users') + '<b>7-player</b> roster</span><span>' + icon('sync') + '<b>2 rerolls</b> total</span><span>' + icon('zap') + '<b>Chemistry</b> bonuses</span></div>' +
    '<div class="legends-intro-record"><span>0–0</span><i>YOUR DYNASTY STARTS HERE</i><span>17–0</span></div>' +
    rankedToggleHtml('legends') +
    '<button class="btn-primary game-intro-cta" data-legends-start>Enter the Draft ' + icon('arrowRight') + '</button>' +
    '</div>';
}
function legendsSlotLabel(slot) { return slot.replace(/\d/, function (d) { return ' ' + d; }); }
function renderLegendsDraft() {
  var s = state.legends, entry = s.rolledEntry;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--roster">' + modeToolbarHtml('legends', s.ranked) +
    broadcastScorebugHtml([['ON THE CLOCK', s.round + '/7'], ['ROSTER FILLED', (s.round - 1) + '/7'], ['REROLLS LEFT', (s.teamRerollUsed ? 0 : 1) + (s.yearRerollUsed ? 0 : 1)]]) +
    '<div class="game-progress"><span style="width:' + Math.round((s.round - 1) / 7 * 100) + '%"></span></div>' +
    (s.lastPick ? '<div class="draft-pick-toast">' + icon('check') + esc(s.lastPick) + '</div>' : '') +
    '<div class="legends-roll-card"><span class="legends-roll-label">ON THE CLOCK</span><div class="legends-roll">' + teamCodeBadgeHtml('nfl', entry.team) + ' <b>' + esc(entry.team) + '</b> <span>' + entry.year + '</span></div></div>' +
    '<div class="legends-slots">' +
    LEGENDS_SLOTS.map(function (slot) {
      var filled = s.slots[slot];
      return '<div class="legends-slot' + (filled ? ' filled' : '') + '"><div class="legends-slot-name">' + legendsSlotLabel(slot) + '</div>' +
        (filled ? '<div class="legends-slot-player">' + esc(filled.name) + '</div>' : '<div class="legends-slot-empty">open</div>') + '</div>';
    }).join('') +
    '</div>' +
    '<div class="broadcast-section-label">THE AVAILABLE TALENT <span>PICK ONE</span></div><div class="legends-options">' +
    entry.players.map(function (p, i) {
      var alreadyPicked = legendsPickedNames(s.slots).indexOf(p.name) !== -1;
      var open = !alreadyPicked && legendsOpenSlotCount(s.slots, p.position) > 0;
      return '<button class="legends-option" ' + (open ? 'data-legends-pick="' + i + '"' : 'disabled') + '>' +
        '<div class="legends-option-top"><div class="legends-option-name">' + esc(p.name) + (alreadyPicked ? ' (already drafted)' : '') + '</div><span class="position-pill">' + p.position + '</span></div>' +
        '<div class="legends-option-meta"><b>' + p.fppg + '</b> fantasy points per game</div>' +
        '<div class="legends-value-meter"><span style="width:' + Math.min(100, Math.round(p.fppg / 35 * 100)) + '%"></span></div>' +
        (open ? '<div class="legends-option-pick">Draft player ' + icon('arrowRight') + '</div>' : '') +
        '</button>';
    }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" ' + (s.teamRerollUsed ? 'disabled' : 'data-legends-reroll-team') + '>Re-roll Team' + (s.teamRerollUsed ? ' (used)' : '') + '</button>' +
    '<button class="btn-secondary" ' + (s.yearRerollUsed ? 'disabled' : 'data-legends-reroll-year') + '>Re-roll Year' + (s.yearRerollUsed ? ' (used)' : '') + '</button>' +
    '</div></div>';
  return html;
}
function renderLegendsResult() {
  var s = state.legends;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--roster">' +
    broadcastResultHtml('NFL · ROSTER REPORT', s.grade, s.gradeLabel, s.wins === 17) +
    broadcastRecordHtml(s.wins, s.losses) +
    '<div class="summary-score">Projected record: ' + s.wins + '-' + s.losses + '</div>' +
    '<div class="summary-note">Base FPPG ' + s.baseTotal + ' + Chemistry = ' + s.finalTotal + ' (perfect-team ceiling: ' + s.perfectScore + ')</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="legends-roster">' +
    s.picks.map(function (p) {
      return '<div class="legends-roster-row"><span class="legends-roster-slot">' + legendsSlotLabel(p.slot) + '</span>' +
        '<span class="legends-roster-player">' + teamCodeBadgeHtml('nfl', p.team) + ' ' + esc(p.name) + ' <i>(' + esc(p.team) + ' ' + p.year + ')</i></span>' +
        '<span class="legends-roster-score">' + p.fppg + (p.chemistry ? ' +' + p.chemistry : '') + ' = ' + Math.round(p.finalFppg * 10) / 10 + '</span></div>';
    }).join('') +
    '</div>' +
    (s.chemLog.length ? '<div class="legends-chem-log"><b>Chemistry:</b>' +
      s.chemLog.map(function (c) { return '<div class="legends-chem-row">' + esc(c.a) + ' + ' + esc(c.b) + ': ' + c.reasons.join(', ') + '</div>'; }).join('') +
      '</div>' : '<div class="legends-chem-log">No chemistry connections this time — a bit of a disconnected roster.</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-legends-start>Draft Again</button>' +
    '<button class="btn-secondary" data-share="legends">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('legends') + '</div>';
}
function renderLegendsScreen() {
  if (!state.legends) return renderLegendsSetup();
  if (state.legends.screen === 'result') return renderLegendsResult();
  return renderLegendsDraft();
}

/* ============================== CFB 12-0 legends draft ==============================
   College football edition of 17-0, originally built from the user-provided
   CFB_16-0_Game_Template.xlsx spec (hence the old filename). Structurally
   mirrors the NFL legends* functions above (same roll -> pick -> chemistry ->
   grade loop), duplicated rather than shared — matches this codebase's
   existing per-league convention (quiz/cfbQuiz, iq/cfbIq, etc.) and is
   necessary here anyway since several strings differ (8 rounds not 7, "12-0"
   not "17-0", CFB-flavored grade labels). Two things are genuinely new, not
   just a port: an 8th roster slot (DEF: DL/LB/DB), and a real 12-game FBS
   regular season (not 17 like the NFL version) — the postseason (National
   Championship / Playoff round / bowl game) is then predicted FROM that
   regular-season record separately, via cfbLegendsPostseasonLabel() below,
   rather than being folded into the win count itself. */
var CFB_LEGENDS_SLOTS = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX', 'DEF'];
function cfbLegendsEligibleSlots(position) {
  if (position === 'QB') return ['QB'];
  if (position === 'RB') return ['RB1', 'RB2', 'FLEX'];
  if (position === 'WR') return ['WR1', 'WR2', 'FLEX'];
  if (position === 'TE') return ['TE', 'FLEX'];
  if (position === 'DEF') return ['DEF'];
  return [];
}
function cfbLegendsPlayerTeams(name) {
  var teams = [];
  CFB_LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (p.name === name && teams.indexOf(t.team) === -1) teams.push(t.team);
    });
  });
  return teams;
}
// Memoized only WITHIN a single draft, not across the whole page session --
// startCfbLegends() resets this to null every time a draft starts. It used
// to cache forever after the first call, which meant the very first draft
// played in a tab (sometimes racing a lazy data-file load, or a stale
// service-worker response before a fresh deploy fully took over) could lock
// in a wrong ceiling that then silently stuck around for every later draft
// in that same tab, no matter how many times the page was reloaded or the
// underlying data changed -- exactly the "ceiling says 203 but the file on
// disk says 139.5" bug this comment is here to prevent from recurring.
var CFB_LEGENDS_PERFECT_SCORE = null;
function cfbLegendsPerfectScore() {
  if (CFB_LEGENDS_PERFECT_SCORE !== null) return CFB_LEGENDS_PERFECT_SCORE;
  var byPos = { QB: [], RB: [], WR: [], TE: [], DEF: [] };
  CFB_LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (byPos[p.position]) byPos[p.position].push(p.fppg);
    });
  });
  Object.keys(byPos).forEach(function (k) { byPos[k].sort(function (a, b) { return b - a; }); });
  var maxQB = byPos.QB[0] || 25, maxRB = byPos.RB[0] || 22, maxWR = byPos.WR[0] || 22, maxTE = byPos.TE[0] || 18, maxDef = byPos.DEF[0] || 10;
  var maxFlex = Math.max(byPos.RB[1] || maxRB, byPos.WR[1] || maxWR, maxTE);
  CFB_LEGENDS_PERFECT_SCORE = maxQB + maxRB * 2 + maxWR * 2 + maxTE + maxFlex + maxDef;
  return CFB_LEGENDS_PERFECT_SCORE;
}
// Every team-year entry a slot is currently filled with is already tagged
// with its own `team` field (set in cfbLegendsPickPlayer below) — this is
// just the deduped list of schools on the board right now, used by the
// same-school roll bias in cfbLegendsRollEntry.
function cfbLegendsPickedSchools(slots) {
  var schools = [];
  CFB_LEGENDS_SLOTS.forEach(function (sl) {
    if (slots[sl] && slots[sl].team && schools.indexOf(slots[sl].team) === -1) schools.push(slots[sl].team);
  });
  return schools;
}
// Picks the NEXT team-season to roll from a persisted, shuffled, no-repeat
// deck of indices into CFB_LEGENDS_TEAMS (same drawNoRepeat() philosophy
// used everywhere else in this app for randomized draws, adapted here for
// one-at-a-time interactive rolls instead of a batch-drawn queue) — plain
// Math.random() over the flat array used to mean a team with more entries
// in the pool showed up proportionally more often, and nothing stopped the
// exact same team-year from being rolled twice in one draft. usedIds is
// this draft's own exclusion list (see cfbLegendsDoRoll) — entries still
// get consumed from the persisted cross-draft deck even when skipped for
// being used-this-draft, which is fine: they come back on the next reshuffle.
//
// Soft "team chemistry" bias: usedEntryIds excludes a team-YEAR entry from
// ever being rolled twice in the same draft by design (so "Same Team" — same
// team AND year — can never fire; that's intentional, you can't draft two
// starters off literally the same single roll). But with 69 programs spread
// across only 8 rolls per draft, landing on the SAME SCHOOL twice (a
// different year — the "Same School" bonus, which CAN fire) was rare enough
// by pure chance that chemistry barely ever showed up, capping most drafts
// well below the higher grades. Once at least one slot is filled, there's a
// real (not guaranteed — still needs to feel like a random roll, and it's
// only checked when a same-school option actually exists) chance the next
// roll deliberately favors a different team-year entry from a school already
// on the roster instead of the deck's plain draw order.
// 0.07 checked EVERY round from round 2 on (up to 7 independent chances in
// an 8-round draft) compounds a lot more than the flat number suggests —
// tuned against a 2000-draft simulation of the real 207-entry pool: raises
// "at least one same-school pair" from ~25% of drafts (the old, "impossible"-
// feeling baseline) to ~54%, roughly tripling the average chemistry points
// per draft, while a 3+-school stack stays rare (~2% of drafts) rather than
// routine. That's "noticeably more achievable," not "guaranteed every game."
var CFB_LEGENDS_SAME_SCHOOL_BIAS = 0.07;
function cfbLegendsRollEntry(usedIds, slots) {
  var storKey = 'deck__cfbLegends';
  var allIds = CFB_LEGENDS_TEAMS.map(function (_, i) { return i; });
  var deck = lsGet(storKey, []).filter(function (id) { return id < CFB_LEGENDS_TEAMS.length; });
  if (!deck.length) deck = shuffle(allIds);
  var pickedSchools = slots ? cfbLegendsPickedSchools(slots) : [];
  if (pickedSchools.length && Math.random() < CFB_LEGENDS_SAME_SCHOOL_BIAS) {
    var sameSchoolIds = deck.filter(function (id) {
      return usedIds.indexOf(id) === -1 && pickedSchools.indexOf(CFB_LEGENDS_TEAMS[id].team) !== -1;
    });
    if (sameSchoolIds.length) {
      var chosen = sameSchoolIds[Math.floor(Math.random() * sameSchoolIds.length)];
      deck.splice(deck.indexOf(chosen), 1);
      lsSet(storKey, deck);
      return { id: chosen, entry: CFB_LEGENDS_TEAMS[chosen] };
    }
  }
  var idx = deck.findIndex(function (id) { return usedIds.indexOf(id) === -1; });
  if (idx === -1) {
    deck = shuffle(allIds);
    idx = deck.findIndex(function (id) { return usedIds.indexOf(id) === -1; });
    if (idx === -1) idx = 0; // every single entry already used this draft (won't happen — pool is far bigger than 8 rounds)
  }
  var id = deck[idx];
  deck.splice(idx, 1);
  lsSet(storKey, deck);
  return { id: id, entry: CFB_LEGENDS_TEAMS[id] };
}
function cfbLegendsOpenSlotCount(slots, position) {
  return cfbLegendsEligibleSlots(position).filter(function (s) { return !slots[s]; }).length;
}
function cfbLegendsPickedNames(slots) {
  return CFB_LEGENDS_SLOTS.map(function (sl) { return slots[sl] && slots[sl].name; }).filter(Boolean);
}
function cfbLegendsRollHasLegalPick(entry, slots) {
  var picked = cfbLegendsPickedNames(slots);
  return entry.players.some(function (p) { return cfbLegendsOpenSlotCount(slots, p.position) > 0 && picked.indexOf(p.name) === -1; });
}
function cfbLegendsDoRoll(state_) {
  state_.usedEntryIds = state_.usedEntryIds || [];
  var picked = cfbLegendsRollEntry(state_.usedEntryIds, state_.slots), tries = 0;
  while (!cfbLegendsRollHasLegalPick(picked.entry, state_.slots) && tries < 500) {
    picked = cfbLegendsRollEntry(state_.usedEntryIds, state_.slots);
    tries++;
  }
  state_.rolledEntry = picked.entry;
  state_.rolledEntryId = picked.id;
  if (state_.usedEntryIds.indexOf(picked.id) === -1) state_.usedEntryIds.push(picked.id);
}
function startCfbLegends() {
  beginProgressSession('cfbLegends');
  state.justCompletedDaily = null; // see startGridRound()'s comment
  CFB_LEGENDS_PERFECT_SCORE = null;
  var slots = {};
  CFB_LEGENDS_SLOTS.forEach(function (s) { slots[s] = null; });
  state.cfbLegends = { screen: 'draft', round: 1, slots: slots, teamRerollUsed: false, yearRerollUsed: false, rolledEntry: null, rolledEntryId: null, usedEntryIds: [], lastPick: null, ranked: state.rankedPref.cfbLegends !== false };
  cfbLegendsDoRoll(state.cfbLegends);
  state.screen = 'cfbLegends';
  renderAll();
}
function cfbLegendsPickPlayer(playerIdx) {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft') return;
  var entry = s.rolledEntry, p = entry.players[playerIdx];
  if (cfbLegendsPickedNames(s.slots).indexOf(p.name) !== -1) return;
  var openSlots = cfbLegendsEligibleSlots(p.position).filter(function (sl) { return !s.slots[sl]; });
  if (!openSlots.length) return;
  var slot = openSlots[0];
  if (openSlots.length > 1 && openSlots.indexOf('FLEX') !== -1) {
    var nonFlex = openSlots.filter(function (sl) { return sl !== 'FLEX'; });
    if (nonFlex.length) slot = nonFlex[0];
  }
  s.slots[slot] = { name: p.name, position: p.position, fppg: p.fppg, team: entry.team, year: entry.year };
  s.lastPick = p.name + ' added at ' + legendsSlotLabel(slot);
  if (s.round >= 8) {
    s.screen = 'result';
    finishCfbLegends();
  } else {
    s.round++;
    cfbLegendsDoRoll(s);
  }
  renderAll();
}
// Both re-rolls index CFB_LEGENDS_TEAMS directly (not via the shared deck —
// each is used at most once per draft, a much smaller randomness surface
// than the 8 main per-round rolls) but still respect usedEntryIds so a
// re-roll can't land on a team-year already seen earlier this same draft;
// falls back to ignoring that exclusion only if literally nothing else
// qualifies, same "never leave the player with an illegal roll" guarantee
// the original code had.
function cfbLegendsIndexedTeams() { return CFB_LEGENDS_TEAMS.map(function (t, i) { return { t: t, i: i }; }); }
function cfbLegendsApplyReroll(s, options) {
  if (!options.length) return;
  var pick = options[Math.floor(Math.random() * options.length)];
  s.rolledEntry = pick.t;
  s.rolledEntryId = pick.i;
  if (s.usedEntryIds.indexOf(pick.i) === -1) s.usedEntryIds.push(pick.i);
}
function cfbLegendsRerollTeam() {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft' || s.teamRerollUsed) return;
  s.teamRerollUsed = true;
  var current = s.rolledEntry.team;
  var all = cfbLegendsIndexedTeams();
  var options = all.filter(function (o) { return o.t.team !== current && s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return o.t.team !== current && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  cfbLegendsApplyReroll(s, options);
  renderAll();
}
function cfbLegendsRerollYear() {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft' || s.yearRerollUsed) return;
  s.yearRerollUsed = true;
  var current = s.rolledEntry;
  var all = cfbLegendsIndexedTeams();
  var options = all.filter(function (o) { return o.t.team === current.team && o.t.year !== current.year && s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return o.t.team === current.team && o.t.year !== current.year && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return cfbLegendsRollHasLegalPick(o.t, s.slots); });
  cfbLegendsApplyReroll(s, options);
  renderAll();
}
// legendsDuoMatch (defined above, in the NFL legends section) is fully
// generic — just a list + two names — so it's reused here as-is rather than
// duplicated.
function cfbLegendsCalcChemistry(picks) {
  var bonus = {}, log = [];
  picks.forEach(function (p) { bonus[p.name] = 0; });
  for (var i = 0; i < picks.length; i++) {
    for (var j = i + 1; j < picks.length; j++) {
      var a = picks[i], b = picks[j], pairBonus = 0, reasons = [];
      var metaA = CFB_PLAYER_META[a.name] || {}, metaB = CFB_PLAYER_META[b.name] || {};
      if (a.team === b.team && a.year === b.year) { pairBonus += 2; reasons.push('Same Team (+2)'); }
      if (metaA.school && metaA.school === metaB.school) { pairBonus += 2; reasons.push('Same School (+2)'); }
      if (metaA.signingClass && metaA.signingClass === metaB.signingClass) { pairBonus += 1; reasons.push('Same Signing Class (+1)'); }
      var teamsA = cfbLegendsPlayerTeams(a.name), teamsB = cfbLegendsPlayerTeams(b.name);
      if (teamsA.some(function (t) { return teamsB.indexOf(t) !== -1; })) { pairBonus += 1; reasons.push('Past Teammates (+1)'); }
      if (legendsDuoMatch(CFB_LEGENDS_DUOS.legendary, a.name, b.name)) { pairBonus += 2; reasons.push('Legendary Connection (+2)'); }
      else if (legendsDuoMatch(CFB_LEGENDS_DUOS.elite, a.name, b.name)) { pairBonus += 1; reasons.push('Elite Connection (+1)'); }
      if (pairBonus > 0) {
        bonus[a.name] += pairBonus;
        bonus[b.name] += pairBonus;
        log.push({ a: a.name, b: b.name, bonus: pairBonus, reasons: reasons });
      }
    }
  }
  return { bonus: bonus, log: log };
}
// Same S-through-F thresholds as the NFL legendsGrade(), but with the
// CFB-flavored labels (including emoji) from the spreadsheet's own
// "4. Grading Scale" sheet.
// Grade is derived straight from the regular-season record (wins — the same
// number cfbLegendsPostseasonLabel below uses), not a separate pct-threshold
// scale, so the letter grade can never disagree with the actual postseason
// outcome shown right under it (e.g. a 6-6 team can't grade out "B-" while
// its own postseason line says it missed the 12-team field entirely — that
// mismatch is exactly what this was rebalanced to fix).
function cfbLegendsGrade(pct) {
  var wins = Math.round(12 * pct);
  if (wins >= 12) return { grade: 'S', label: 'GOAT 🐐' };
  if (wins === 11) return { grade: 'A+', label: 'Runner-Up 🤩' };
  if (wins === 10) return { grade: 'A-', label: 'Final Four' };
  if (wins === 9) return { grade: 'B+', label: 'Quarterfinalist' };
  if (wins === 8) return { grade: 'B-', label: 'First Round Exit' };
  if (wins === 7) return { grade: 'C+', label: 'Bubble Team' };
  if (wins === 6) return { grade: 'C-', label: 'Missed the Field' };
  if (wins === 5) return { grade: 'D+', label: 'Rebuilding' };
  if (wins === 4) return { grade: 'D', label: 'Rebuilding' };
  return { grade: 'F', label: 'Toilet Bowl 💩' };
}
// Real, lower-tier bowl names for the "missed the 12-team field" tier (see
// cfbLegendsPostseasonLabel below) — picked randomly per grade band so a
// weaker roster's capstone game varies playthrough to playthrough instead of
// always naming the exact same bowl.
var CFB_BOWL_NAMES = {
  'C+': ['Cotton Bowl', 'Alamo Bowl', 'Holiday Bowl'],
  C: ['Sun Bowl', 'Music City Bowl', 'Pinstripe Bowl'],
  D: ['Independence Bowl', 'Gasparilla Bowl', 'Birmingham Bowl'],
  F: ['New Mexico Bowl', 'Frisco Bowl', 'Bahamas Bowl']
};
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
// Postseason placement is predicted straight from the 12-game regular-season
// record — not from the roster grade — since that's how it actually works
// in real CFB: your record decides your seed/bowl, not some abstract quality
// score. 12-0 is the only unbeaten and wins it all; 11-1 and 10-2 are strong
// Playoff seeds that go deep; 9-3/8-4 are the bubble of the 12-team field;
// 7-5 and below missed the Playoff and play a real, record-appropriate bowl
// game instead (named from CFB_BOWL_NAMES above). Static and deterministic
// (aside from which bowl name), since this app's offline/static architecture
// has no runtime AI narration to draw on.
function cfbLegendsPostseasonLabel(wins) {
  if (wins >= 12) return '🏆 National Champions — the only unbeaten team in the country, and it showed. Won it all.';
  if (wins === 11) return '🥈 Runner-Up — made the National Championship Game and came up just short.';
  if (wins === 10) return 'Lost in the Semifinal of the 12-team Playoff';
  if (wins === 9) return 'Lost in the Quarterfinal of the 12-team Playoff';
  if (wins === 8) return 'Lost in the First Round of the 12-team Playoff';
  if (wins === 7) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES['C+']);
  if (wins === 6) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.C);
  if (wins === 5) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.D);
  return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.F);
}
// The spec's "fun one-line verdict" (sheet 5, step 6: 'Give the final grade
// and a fun one-line verdict, e.g. "Iconic 👑 — this squad is a problem"').
function cfbLegendsVerdict(grade, label) {
  var VERDICTS = {
    S: 'this roster doesn’t lose.',
    'A+': 'this squad is a problem.',
    'A-': 'one of the best rosters you can build.',
    'B+': 'so close to perfect, so far.',
    'B-': 'good roster, bad matchup.',
    'C+': 'a bubble team through and through.',
    'C-': 'a middling season, nothing more.',
    'D+': 'a rough year with a few bright spots.',
    D: 'this roster needs a lot more pieces.',
    F: 'an absolute disaster of a draft.'
  };
  return label + ' — ' + (VERDICTS[grade] || '');
}
function finishCfbLegends() {
  var s = state.cfbLegends;
  var picks = CFB_LEGENDS_SLOTS.map(function (slot) { return Object.assign({ slot: slot }, s.slots[slot]); });
  var chem = cfbLegendsCalcChemistry(picks);
  var baseTotal = 0, finalTotal = 0;
  picks.forEach(function (p) {
    var b = chem.bonus[p.name] || 0;
    p.chemistry = b;
    p.finalFppg = p.fppg + b;
    baseTotal += p.fppg;
    finalTotal += p.finalFppg;
  });
  var perfect = cfbLegendsPerfectScore();
  var pct = Math.max(0, Math.min(1, finalTotal / perfect));
  var wins = Math.round(12 * pct);
  var losses = 12 - wins;
  var g = cfbLegendsGrade(pct);
  s.picks = picks;
  s.chemLog = chem.log;
  s.baseTotal = Math.round(baseTotal * 10) / 10;
  s.finalTotal = Math.round(finalTotal * 10) / 10;
  s.perfectScore = Math.round(perfect * 10) / 10;
  s.wins = wins;
  s.losses = losses;
  s.grade = g.grade;
  s.gradeLabel = g.label;
  s.postseasonLabel = cfbLegendsPostseasonLabel(wins);
  s.verdict = cfbLegendsVerdict(g.grade, g.label);
  if (s.ranked !== false) {
    var st = state.stats.cfbLegends;
    st.gamesPlayed++;
    if (wins > st.bestWins || (wins === st.bestWins && finalTotal > st.bestScore)) { st.bestWins = wins; st.bestScore = s.finalTotal; st.bestGrade = g.grade; }
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct * 100);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbLegends', { bestWins: st.bestWins, bestRecord: st.bestWins + '-' + (12 - st.bestWins), bestScore: st.bestScore, bestGrade: st.bestGrade, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('cfbLegends', wins + '-' + losses + ' (' + g.grade + ')', pct * 100);
  h2hSubmitModeResult('cfbLegends', wins, 12);
  playSound(g.grade === 'F' ? 'boo' : 'complete');
}

function renderCfbLegendsSetup() {
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--roster broadcast-finish--cfb game-intro game-intro-legends">' +
    '<div class="game-intro-icon">' + icon('trophy') + '</div><div class="game-intro-eyebrow">Build a national champion</div>' +
    '<h2 class="game-intro-title">Can You Go 12–0?</h2>' +
    '<p class="game-intro-copy">Eight team-seasons. Eight picks. Build an offense, add a defense, stack chemistry, and chase an undefeated regular season.</p>' +
    '<div class="game-intro-features"><span>' + icon('users') + '<b>8-player</b> roster</span><span>' + icon('sync') + '<b>2 rerolls</b> total</span><span>' + icon('trophy') + '<b>Playoff</b> finish</span></div>' +
    '<div class="legends-intro-record"><span>0–0</span><i>YOUR TITLE RUN STARTS HERE</i><span>12–0</span></div>' +
    rankedToggleHtml('cfbLegends') +
    '<button class="btn-primary game-intro-cta" data-cfb-legends-start>Enter the Draft ' + icon('arrowRight') + '</button>' +
    '</div>';
}
function renderCfbLegendsDraft() {
  var s = state.cfbLegends, entry = s.rolledEntry;
  var html = '<div class="panel stadium-game broadcast-finish broadcast-finish--roster broadcast-finish--cfb">' + modeToolbarHtml('cfbLegends', s.ranked) +
    broadcastScorebugHtml([['ON THE CLOCK', s.round + '/8'], ['ROSTER FILLED', (s.round - 1) + '/8'], ['REROLLS LEFT', (s.teamRerollUsed ? 0 : 1) + (s.yearRerollUsed ? 0 : 1)]]) +
    '<div class="game-progress"><span style="width:' + Math.round((s.round - 1) / 8 * 100) + '%"></span></div>' +
    (s.lastPick ? '<div class="draft-pick-toast">' + icon('check') + esc(s.lastPick) + '</div>' : '') +
    '<div class="legends-roll-card"><span class="legends-roll-label">ON THE CLOCK</span><div class="legends-roll">' + teamCodeBadgeHtml('cfb', entry.team) + ' <b>' + esc(entry.team) + '</b> <span>' + entry.year + '</span></div></div>' +
    '<div class="legends-slots">' +
    CFB_LEGENDS_SLOTS.map(function (slot) {
      var filled = s.slots[slot];
      return '<div class="legends-slot' + (filled ? ' filled' : '') + '"><div class="legends-slot-name">' + legendsSlotLabel(slot) + '</div>' +
        (filled ? '<div class="legends-slot-player">' + esc(filled.name) + '</div>' : '<div class="legends-slot-empty">open</div>') + '</div>';
    }).join('') +
    '</div>' +
    '<div class="broadcast-section-label">THE AVAILABLE TALENT <span>PICK ONE</span></div><div class="legends-options">' +
    entry.players.map(function (p, i) {
      var alreadyPicked = cfbLegendsPickedNames(s.slots).indexOf(p.name) !== -1;
      var open = !alreadyPicked && cfbLegendsOpenSlotCount(s.slots, p.position) > 0;
      return '<button class="legends-option" ' + (open ? 'data-cfb-legends-pick="' + i + '"' : 'disabled') + '>' +
        '<div class="legends-option-top"><div class="legends-option-name">' + esc(p.name) + (alreadyPicked ? ' (already drafted)' : '') + '</div><span class="position-pill">' + p.position + '</span></div>' +
        '<div class="legends-option-meta"><b>' + p.fppg + '</b> fantasy points per game</div>' +
        '<div class="legends-value-meter"><span style="width:' + Math.min(100, Math.round(p.fppg / 35 * 100)) + '%"></span></div>' +
        (open ? '<div class="legends-option-pick">Draft player ' + icon('arrowRight') + '</div>' : '') +
        '</button>';
    }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" ' + (s.teamRerollUsed ? 'disabled' : 'data-cfb-legends-reroll-team') + '>Re-roll Team' + (s.teamRerollUsed ? ' (used)' : '') + '</button>' +
    '<button class="btn-secondary" ' + (s.yearRerollUsed ? 'disabled' : 'data-cfb-legends-reroll-year') + '>Re-roll Year' + (s.yearRerollUsed ? ' (used)' : '') + '</button>' +
    '</div></div>';
  return html;
}
function renderCfbLegendsResult() {
  var s = state.cfbLegends;
  return '<div class="panel stadium-game broadcast-finish broadcast-finish--roster broadcast-finish--cfb">' +
    broadcastResultHtml('CFB · ROSTER REPORT', s.grade, s.verdict, s.wins === 12) +
    broadcastRecordHtml(s.wins, s.losses) +
    '<div class="summary-score">Regular season: ' + s.wins + '-' + s.losses + '</div>' +
    '<div class="summary-note">' + esc(s.postseasonLabel) + '</div>' +
    '<div class="summary-note">Base FPPG ' + s.baseTotal + ' + Chemistry = ' + s.finalTotal + ' (perfect-team ceiling: ' + s.perfectScore + ')</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Log in above to save this to the leaderboard.') + '</div>' +
    '<div class="legends-roster">' +
    s.picks.map(function (p) {
      return '<div class="legends-roster-row"><span class="legends-roster-slot">' + legendsSlotLabel(p.slot) + '</span>' +
        '<span class="legends-roster-player">' + teamCodeBadgeHtml('cfb', p.team) + ' ' + esc(p.name) + ' <i>(' + esc(p.team) + ' ' + p.year + ')</i></span>' +
        '<span class="legends-roster-score">' + p.fppg + (p.chemistry ? ' +' + p.chemistry : '') + ' = ' + Math.round(p.finalFppg * 10) / 10 + '</span></div>';
    }).join('') +
    '</div>' +
    (s.chemLog.length ? '<div class="legends-chem-log"><b>Chemistry:</b>' +
      s.chemLog.map(function (c) { return '<div class="legends-chem-row">' + esc(c.a) + ' + ' + esc(c.b) + ': ' + c.reasons.join(', ') + '</div>'; }).join('') +
      '</div>' : '<div class="legends-chem-log">No chemistry connections this time — a bit of a disconnected roster.</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-legends-start>Draft Again</button>' +
    '<button class="btn-secondary" data-share="cfbLegends">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div>' + postGameNextStepsHtml('cfbLegends') + '</div>';
}
function renderCfbLegendsScreen() {
  if (!state.cfbLegends) return renderCfbLegendsSetup();
  if (state.cfbLegends.screen === 'result') return renderCfbLegendsResult();
  return renderCfbLegendsDraft();
}

/* ============================== head-to-head ==============================
   Async head-to-head: two named players share a short room code (out-of-
   band — text, Discord, whatever) and each plays their own round on their
   own time rather than needing to be online together — whoever's result is
   higher once both have finished wins the match. Deliberately NOT truly
   live/simultaneous — see the project's H2H design notes for why async won
   out. One Firestore doc per match (games/nflTrivia/matches/{code}), read/
   written via window.__fbSync.getMatch/setMatch/watchMatch (firebase-
   sync.js). A head-to-head round always counts toward Football Rating and
   the underlying mode's normal stats, same as a solo round — plus a
   separate win/loss/tie record (state.stats.h2h) specific to head-to-head.

   Every game mode is available (H2H_MODES below). Two kinds:
   - kind: 'quiz' (Quiz/CFB Quiz) — the original design: both players get the
     IDENTICAL seeded question set (seeded from the match code itself, same
     mulberry32/seededShuffle pattern as the Daily Reads), answered in
     this file's own quiz-style flow (h2hCurrentQuestion/h2hPickAnswer/etc).
   - kind: 'mode' or 'blitz' (everything else — Grid, Blitz, Silhouette,
     Speed, 17-0/12-0) — routes into that mode's own real engine instead of
     a bespoke H2H flow (startH2hIntoMode, mirroring startDailyIntoMode for
     the Daily Reads), then that mode's own finish function reports back
     via h2hSubmitModeResult. These do NOT get an identical seeded challenge
     the way Quiz does — each player gets that mode's own normal randomness
     (Blitz is the one exception: the match creator picks a specific list,
     stored on the match doc, so both players do face the same list). Fully
     seeding Grid's board / Silhouette's player set / a Legends draft's rolls
     off the match code would make every mode perfectly fair head-to-head,
     but is real additional engineering per mode — this ships full mode
     coverage now; identical-challenge fairness for these is a possible
     later pass, not a blocker to having the mode available at all.
   IQ Test / CFB IQ Test are deliberately NOT included — they already reuse
   the exact same question pool as Quiz/CFB Quiz (so add nothing new to
   challenge a friend with) and their defining trait, no feedback until the
   very end, doesn't fit this file's always-immediate-feedback question flow
   without a second bespoke render path for no real benefit. */
var H2H_MODES = [
  { id: 'quiz', label: 'NFL Quiz', kind: 'quiz', pool: function () { return QUIZ; }, roundSizeOptions: [5, 10, 20], resultSuffix: 'correct' },
  { id: 'cfbQuiz', label: 'CFB Quiz', kind: 'quiz', pool: function () { return CFB; }, roundSizeOptions: [5, 10, 20], resultSuffix: 'correct' },
  { id: 'grid', label: 'NFL Grid', kind: 'mode', resultSuffix: 'squares' },
  { id: 'cfbGrid', label: 'CFB Grid', kind: 'mode', resultSuffix: 'squares' },
  { id: 'blitz', label: 'NFL Blitz', kind: 'blitz', resultSuffix: 'found' },
  { id: 'cfbBlitz', label: 'CFB Blitz', kind: 'blitz', resultSuffix: 'found' },
  { id: 'silhouette', label: 'Silhouette', kind: 'mode', roundSizeOptions: [5, 10], resultSuffix: 'correct' },
  { id: 'speed', label: 'NFL Speed', kind: 'mode', resultSuffix: 'points', usesPoints: true },
  { id: 'cfbSpeed', label: 'CFB Speed', kind: 'mode', resultSuffix: 'points', usesPoints: true },
  { id: 'legends', label: '17-0', kind: 'mode', resultSuffix: 'wins' },
  { id: 'cfbLegends', label: 'CFB 12-0', kind: 'mode', resultSuffix: 'wins' }
];
function h2hModeConfig(id) { return H2H_MODES.find(function (x) { return x.id === id; }); }
function h2hModeLabel(id) {
  var m = h2hModeConfig(id);
  return m ? m.label : id;
}
var H2H_CODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // no 0/O/1/I/L — easy to read/type aloud
function generateH2HCode() {
  var s = '';
  for (var i = 0; i < 4; i++) s += H2H_CODE_CHARS[Math.floor(Math.random() * H2H_CODE_CHARS.length)];
  return s;
}
function h2hPool(mode) {
  var m = H2H_MODES.find(function (x) { return x.id === mode; });
  return m ? m.pool() : [];
}
function h2hQuestionIds(mode, code, roundSize) {
  var rng = mulberry32(hashStr(code));
  return seededShuffle(h2hPool(mode), rng).slice(0, roundSize).map(function (q) { return q.id; });
}
function h2hCurrentQuestion() {
  var s = state.h2h;
  var id = s.queue[s.index];
  return h2hPool(s.mode).find(function (q) { return q.id === id; });
}
function h2hMyCodes() { return lsGet('nflTriviaH2hCodes', []); }
function h2hRememberCode(code) {
  var list = h2hMyCodes();
  if (list.indexOf(code) === -1) { list.unshift(code); lsSet('nflTriviaH2hCodes', list.slice(0, 20)); }
}
function h2hAlreadyCounted(code) { return h2hMyCounted().indexOf(code) !== -1; }
function h2hMyCounted() { return lsGet('nflTriviaH2hCounted', []); }
function h2hMarkCounted(code) {
  var list = h2hMyCounted();
  if (list.indexOf(code) === -1) { list.push(code); lsSet('nflTriviaH2hCounted', list.slice(-50)); }
}
var h2hUnsub = null;
function h2hStopWatch() { if (h2hUnsub) { h2hUnsub(); h2hUnsub = null; } }
function h2hWatch(code) {
  h2hStopWatch();
  if (window.__fbSync && window.__fbSync.watchMatch) h2hUnsub = window.__fbSync.watchMatch(code, h2hOnMatchUpdate);
}
// Fires on every live update to the watched match doc (opponent joining,
// opponent finishing their round, etc). Auto-advances the lobby to the
// summary screen once both players have a finishedAt, and counts the
// win/loss/tie exactly once per match (h2hMarkCounted guards re-counting on
// a later update or a revisit). Silently skipped while s.screen === 'question'
// so an opponent finishing mid-way through YOUR round can't yank the screen
// out from under you.
function h2hOnMatchUpdate(match) {
  var s = state.h2h;
  if (!s || !match) return;
  s.match = match;
  h2hMaybeCountRecord();
  if(s.code) socialSyncChallengeResult(match,s.code);
  if (s.screen === 'lobby') {
    var slugs = Object.keys(match.players || {});
    var me = match.players[s.mySlug];
    var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
    var opp = oppSlug ? match.players[oppSlug] : null;
    if (me && me.finishedAt && opp && opp.finishedAt) s.screen = 'summary';
  }
  // Skip the re-render while actively mid-round — either the quiz-kind
  // question flow (state.h2h.screen === 'question') or a non-quiz mode's own
  // screen (state.h2hActive still set, since state.h2h.screen itself just
  // stays 'lobby' the whole time a non-quiz round is being played elsewhere)
  // — so an opponent's update landing at that exact moment can't yank focus
  // off an input or rebuild a board mid-guess out from under the player.
  if (s.screen !== 'question' && !state.h2hActive) renderAll();
}
// Compares two match-player records and returns >0 if `mine` did better,
// <0 if `opp` did, 0 for a tie. Prefers the `points` field (a raw-score
// tiebreak some modes report — see H2H_MODES' usesPoints) when both records
// have one, since plain correctCount/total isn't a fair comparator for a
// timed mode like Speed; falls back to correctCount for every other mode,
// and for any older match doc from before `points` existed.
function h2hCompareRecords(mine, opp) {
  if (mine.points != null && opp.points != null) return mine.points - opp.points;
  return mine.correctCount - opp.correctCount;
}
function h2hMaybeCountRecord() {
  var s = state.h2h, match = s && s.match;
  if (!match || h2hAlreadyCounted(s.code)) return;
  var slugs = Object.keys(match.players || {});
  if (slugs.length !== 2) return;
  var mine = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  if (!mine || !opp || !mine.finishedAt || !opp.finishedAt) return;
  var st = state.stats.h2h;
  st.matchesPlayed++;
  var diff = h2hCompareRecords(mine, opp);
  if (diff > 0) st.wins++;
  else if (diff < 0) st.losses++;
  else st.ties++;
  lsSet('nflTriviaStats', state.stats);
  pushLeaderboard('h2h', { wins: st.wins, losses: st.losses, ties: st.ties, matchesPlayed: st.matchesPlayed });
  h2hMarkCounted(s.code);
}
function h2hBackToMenu() {
  h2hStopWatch();
  state.h2hActive = null;
  state.h2h = { screen: 'menu', mode: 'quiz', roundSize: 10, listId: null, error: null };
  renderAll();
}
function h2hRematch() {
  var s=state.h2h, match=s&&s.match;
  if(!match) return h2hBackToMenu();
  var slugs=Object.keys(match.players||{});
  var oppSlug=slugs.filter(function(sl){return sl!==s.mySlug;})[0];
  var opp=oppSlug?match.players[oppSlug]:null;
  var mode=s.mode||match.mode||'quiz';
  var size=s.roundSize||match.roundSize||10;
  var listId=s.listId||match.listId||null;
  h2hStopWatch();
  state.h2hActive=null;
  state.h2h={screen:'create',mode:mode,roundSize:size,listId:listId,error:null,intendedOpponent:opp?opp.name:null};
  renderAll();
}
function h2hSetRoundSize(n) { state.h2h.roundSize = n; renderAll(); }
// Changing the mode on the create screen resets round-size/list to that
// mode's own defaults, and lazy-loads its data file if the create screen
// needs it up front (Blitz needs BLITZ_LISTS loaded to show list names —
// every other mode's data can still load lazily once the match actually
// starts, same as entering it from the home screen would).
function h2hSetMode(modeId) {
  var s = state.h2h, m = h2hModeConfig(modeId);
  if (!m) return;
  s.mode = modeId;
  s.roundSize = (m.roundSizeOptions && m.roundSizeOptions[0]) || 10;
  s.listId = null;
  if (m.kind === 'blitz') {
    s.loadingCreateData = true;
    renderAll();
    loadModeDataThenRun(modeId, function () {
      s.loadingCreateData = false;
      var lists = modeId === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS;
      s.listId = lists.length ? lists[0].id : null;
      renderAll();
    });
    return;
  }
  renderAll();
}
function h2hSetList(listId) { state.h2h.listId = listId; renderAll(); }
function h2hCreateMatch(mode) {
  var s = state.h2h;
  var code = generateH2HCode();
  var mySlug = slugify(state.name);
  var match = { mode: mode, roundSize: s.roundSize, listId: s.listId || null, status: 'waiting', players: {} };
  match.players[mySlug] = { name: state.name, correctCount: null, total: null, finishedAt: null };
  if (!window.__fbSync || !window.__fbSync.setMatch) return;
  window.__fbSync.setMatch(code, match, false).then(function () {
    h2hRememberCode(code);
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.mode = mode;
    s.screen = 'lobby';
    s.error = null;
    h2hWatch(code);
    if(s.intendedOpponent) createSocialChallengeInvite(s.intendedOpponent,code,mode);
    renderAll();
  }).catch(function (err) {
    console.error('Create match failed', err);
    s.error = 'Could not create the match — check your connection and try again.';
    renderAll();
  });
}
function h2hJoinMatch(codeInput) {
  var s = state.h2h;
  var code = (codeInput || '').toUpperCase().trim();
  if (!code) return;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match) { s.error = 'No match found with that code.'; renderAll(); return; }
    var slugs = Object.keys(match.players || {});
    if (slugs.indexOf(mySlug) === -1 && slugs.length >= 2) { s.error = 'That match already has two players.'; renderAll(); return; }
    if (slugs.indexOf(mySlug) === -1) {
      match.players[mySlug] = { name: state.name, correctCount: null, total: null, finishedAt: null };
      match.status = 'active';
    }
    window.__fbSync.setMatch(code, match, false).then(function () {
      h2hRememberCode(code);
      s.code = code;
      s.match = match;
      s.mySlug = mySlug;
      s.mode = match.mode;
      s.roundSize = match.roundSize;
      s.listId = match.listId || null;
      s.screen = 'lobby';
      s.error = null;
      h2hWatch(code);
      renderAll();
    });
  }).catch(function (err) {
    console.error('Join match failed', err);
    s.error = 'Could not join — check your connection and try again.';
    renderAll();
  });
}
function h2hOpenExistingCode(code) {
  var s = state.h2h;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match) return;
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.mode = match.mode;
    s.roundSize = match.roundSize;
    s.listId = match.listId || null;
    var slugs = Object.keys(match.players || {});
    var me = match.players[mySlug];
    var oppSlug = slugs.filter(function (sl) { return sl !== mySlug; })[0];
    var opp = oppSlug ? match.players[oppSlug] : null;
    s.screen = (me && me.finishedAt && opp && opp.finishedAt) ? 'summary' : 'lobby';
    h2hWatch(code);
    renderAll();
  });
}
function h2hStartPlaying() {
  beginProgressSession('h2h');
  var s = state.h2h, m = h2hModeConfig(s.mode);
  h2hStopWatch();
  if (!m || m.kind === 'quiz') {
    s.queue = h2hQuestionIds(s.mode, s.code, s.roundSize);
    s.index = 0;
    s.correctCount = 0;
    s.answeredIndex = null;
    s.screen = 'question';
    renderAll();
    return;
  }
  // Non-quiz mode: hand off to that mode's own real screen/engine (same
  // pattern as the Daily Reads's startDailyIntoMode) — h2hSubmitModeResult
  // (below) is what brings control back to the 'h2h' screen once that mode's
  // own finish function runs.
  state.h2hActive = { code: s.code, mode: s.mode };
  startH2hIntoMode(s.mode, s.listId, s.roundSize);
}
// Loads the target mode's data if needed, forces it ranked, then starts it
// with whatever config this match agreed on (a specific Blitz list; a
// Silhouette round size; nothing extra for Grid/Speed/Legends).
function startH2hIntoMode(mode, listId, roundSize) {
  loadModeDataThenRun(mode, function () {
    startModeRanked(mode, function () {
      if (mode === 'grid') startGridRound();
      else if (mode === 'cfbGrid') startCfbGridRound();
      else if (mode === 'blitz') startBlitz(listId, 90);
      else if (mode === 'cfbBlitz') startCfbBlitz(listId, 90);
      else if (mode === 'silhouette') startSilhouetteRound(roundSize || 5);
      else if (mode === 'speed') startSpeedRound(60);
      else if (mode === 'cfbSpeed') startCfbSpeedRound(60);
      else if (mode === 'legends') startLegends();
      else if (mode === 'cfbLegends') startCfbLegends();
    });
  }, function () { state.h2hActive = null; });
}
// The non-quiz-kind counterpart to h2hFinishRound above — called from each
// of those modes' own finish functions (finishGridRound, finishBlitzRound,
// etc.) once state.h2hActive confirms this specific round was played as a
// head-to-head match rather than a normal solo one. correctCount/total are
// always the "X out of Y" shown on the lobby/summary screens; points is an
// optional raw-score field (see h2hCompareRecords) for modes — just Speed —
// where a plain ratio doesn't fairly capture who did better.
function h2hSubmitModeResult(modeId, correctCount, total, points) {
  if (!state.h2hActive || state.h2hActive.mode !== modeId) return;
  state.h2hActive = null;
  var s = state.h2h;
  if (!s || !s.code) return;
  var match = s.match || { mode: modeId, status: 'active', players: {} };
  match.players = match.players || {};
  var rec = { name: state.name, correctCount: correctCount, total: total, finishedAt: Date.now() };
  if (points != null) rec.points = points;
  match.players[s.mySlug] = rec;
  var slugs = Object.keys(match.players);
  var allFinished = slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].finishedAt; });
  match.status = allFinished ? 'complete' : 'active';
  s.match = match;
  s.screen = 'summary';
  state.screen = 'h2h';
  if (window.__fbSync && window.__fbSync.setMatch) {
    window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Match result submit failed', err); });
  }
  h2hMaybeCountRecord();
  h2hWatch(s.code);
  renderAll();
}
function h2hPickAnswer(i) {
  var s = state.h2h;
  if (s.answeredIndex !== null) return;
  s.answeredIndex = i;
  var q = h2hCurrentQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) s.correctCount++;
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function h2hNextQuestion() {
  var s = state.h2h;
  if (s.index + 1 >= s.queue.length) { h2hFinishRound(); return; }
  s.index++;
  s.answeredIndex = null;
  renderAll();
}
// Counts like a completely normal solo round for rating + the underlying
// mode's own stats/leaderboard (state.stats.quiz / cfbQuiz) — a head-to-head
// match is still real trivia, not a side mode with its own scoring universe.
// The win/loss/tie record is a separate, additional thing tracked on top
// (see h2hMaybeCountRecord), not instead of the normal stats.
function h2hFinishRound() {
  var s = state.h2h;
  var pct = Math.round(100 * s.correctCount / s.queue.length);
  var st = state.stats[s.mode];
  st.correctTotal += s.correctCount;
  st.questionsTotal += s.queue.length;
  st.roundsPlayed++;
  if (pct > st.bestPct) st.bestPct = pct;
  lsSet('nflTriviaStats', state.stats);
  updateRatingDrift(pct);
  s.ratingDelta = lastRatingDelta;
  pushLeaderboard(s.mode, { bestPct: st.bestPct, correctTotal: st.correctTotal, roundsPlayed: st.roundsPlayed });

  var match = s.match || { mode: s.mode, roundSize: s.roundSize, status: 'active', players: {} };
  match.players = match.players || {};
  match.players[s.mySlug] = { name: state.name, correctCount: s.correctCount, total: s.queue.length, finishedAt: Date.now() };
  var slugs = Object.keys(match.players);
  var allFinished = slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].finishedAt; });
  match.status = allFinished ? 'complete' : 'active';
  s.match = match;
  if (window.__fbSync && window.__fbSync.setMatch) {
    window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Match result submit failed', err); });
  }
  s.screen = 'summary';
  playSound(pct >= 60 ? 'complete' : 'boo');
  h2hMaybeCountRecord();
  h2hWatch(s.code);
  renderAll();
}
function renderH2HMenu() {
  if (!state.name) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('versus') + ' Head-to-Head</h2>' +
      '<p class="mode-desc">Log in above, then come back here to challenge a friend.</p>' +
      '</div>';
  }
  var st = state.stats.h2h || {};
  var codes = h2hMyCodes();
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('versus') + ' Head-to-Head</h2>' +
    '<p class="mode-desc">Challenge a specific friend to the same question set and see who scores higher. Your record: ' + (st.wins || 0) + '-' + (st.losses || 0) + (st.ties ? '-' + st.ties : '') + '.</p>' +
    socialChallengeInboxHtml() +
    (state.h2h && state.h2h.intendedOpponent ? '<div class="h2h-target-friend">Challenge for <b>'+esc(state.h2h.intendedOpponent)+'</b>. Pick the mode, create the match, then send them the code.</div>' : '') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-go-create>Create Match</button>' +
    '<button class="btn-secondary" data-h2h-go-join>Join Match</button>' +
    '</div>' +
    (codes.length ? '<h3 class="mode-section-title" style="margin-top:20px;">Your matches</h3><div class="h2h-recent-list">' +
      codes.slice(0, 8).map(function (c) { return '<button class="btn-tiny" data-h2h-open-code="' + esc(c) + '">' + esc(c) + '</button>'; }).join('') +
      '</div>' : '') +
    '</div>';
}
function renderH2HCreate() {
  var s = state.h2h, m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var configHtml = '';
  if (m.kind === 'blitz') {
    if (s.loadingCreateData) {
      configHtml = '<p class="mode-desc">Loading lists…</p>';
    } else {
      var lists = s.mode === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS;
      configHtml = '<div class="field-row"><label>List<select id="h2h-list">' +
        lists.map(function (l) { return '<option value="' + esc(l.id) + '"' + (s.listId === l.id ? ' selected' : '') + '>' + esc(l.title) + '</option>'; }).join('') +
        '</select></label></div>';
    }
  } else if (m.roundSizeOptions) {
    configHtml = '<div class="chip-row">' +
      m.roundSizeOptions.map(function (n) { return '<button class="chip-toggle' + (s.roundSize === n ? ' active' : '') + '" data-h2h-roundsize="' + n + '">' + n + (m.kind === 'quiz' ? ' questions' : ' players') + '</button>'; }).join('') +
      '</div>';
  } else {
    configHtml = '<p class="mode-desc">No extra setup — both of you play a normal round of ' + esc(m.label) + '.</p>';
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Create a Match</h2>' +
    '<div class="field-row"><label>Mode<select id="h2h-mode">' +
    H2H_MODES.map(function (mm) { return '<option value="' + mm.id + '"' + (s.mode === mm.id ? ' selected' : '') + '>' + esc(mm.label) + '</option>'; }).join('') +
    '</select></label></div>' +
    configHtml +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-create' + (m.kind === 'blitz' && !s.listId ? ' disabled' : '') + '>Create &amp; Get Code</button>' +
    '</div>';
}
function renderH2HJoin() {
  var s = state.h2h;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Join a Match</h2>' +
    '<div class="field-row"><label>Match code<input id="h2h-code-input" maxlength="4" placeholder="e.g. 7F3K" autocomplete="off" autocapitalize="characters" style="text-transform:uppercase;" /></label></div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-join>Join</button>' +
    '</div>';
}
function renderH2HLobby() {
  var s = state.h2h, match = s.match || { players: {} };
  var m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var slugs = Object.keys(match.players || {});
  var me = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  var myDone = !!(me && me.finishedAt);
  var setupNote = m.kind === 'quiz' ? s.roundSize + ' questions, the exact same set for both of you.' :
    m.kind === 'blitz' ? 'Same list for both of you — ' + esc((s.mode === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS).find(function (l) { return l.id === s.listId; }).title) + '.' :
    'Both of you play a normal round of ' + esc(m.label) + ' — whoever’s result is higher wins.';
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Head-to-Head &middot; ' + esc(h2hModeLabel(s.mode)) + '</h2>' +
    '<div class="h2h-code">' + esc(s.code) + '</div>' +
    '<p class="mode-desc">Share this code with whoever you’re playing — ' + setupNote + '</p>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + (myDone ? me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix : 'Not played yet') + '</span></div>' +
    '<div class="h2h-player-row"><span>' + (opp ? esc(opp.name) : 'Waiting for opponent to join…') + '</span><span>' + (opp && opp.finishedAt ? opp.correctCount + ' / ' + opp.total + ' ' + m.resultSuffix : opp ? 'Not played yet' : '') + '</span></div>' +
    '</div>' +
    (myDone
      ? '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + ' to finish…</p>'
      : '<button class="btn-primary" data-h2h-start-play>Start Playing</button>') +
    '</div>';
}
function renderH2HQuestion() {
  var s = state.h2h, q = h2hCurrentQuestion();
  var answered = s.answeredIndex !== null;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-exit>' + icon('close') + ' Exit to Home</button></div>' +
    '<div class="quiz-progress">Head-to-Head &middot; Question ' + (s.index + 1) + ' of ' + s.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-h2h-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (s.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-h2h-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderH2HSummary() {
  var s = state.h2h, match = s.match || { players: {} };
  var m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var slugs = Object.keys(match.players || {});
  var me = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  var oppDone = !!(opp && opp.finishedAt);
  var diff = oppDone ? h2hCompareRecords(me, opp) : 0;
  var result = oppDone ? (diff > 0 ? 'win' : diff < 0 ? 'loss' : 'tie') : null;
  return '<div class="panel">' +
    '<h2 class="panel-title">Head-to-Head Result</h2>' +
    (!oppDone
      ? '<div class="summary-score">You scored ' + me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix + '</div>' +
        '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + ' to finish — check back later, or send the invite again.</p>' +
        '<div class="h2h-invite-strip"><b>Challenge code '+esc(s.code)+'</b><button class="btn-secondary" data-social-copy="'+esc(s.code)+'">'+icon('copy')+' Copy Invite</button></div>'
      : '<div class="h2h-result-banner h2h-result-' + result + '">' + (result === 'win' ? icon('trophy') + ' You Won!' : result === 'loss' ? 'You Lost' : 'Tie Game') + '</div>' +
        '<div class="h2h-players">' +
        '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix + '</span></div>' +
        '<div class="h2h-player-row"><span>' + esc(opp.name) + '</span><span>' + opp.correctCount + ' / ' + opp.total + ' ' + m.resultSuffix + '</span></div>' +
        '</div>') +
    '<div class="btn-row">' +
    (oppDone ? '<button class="btn-primary" data-h2h-rematch>Run It Back</button>' : '<button class="btn-primary" data-h2h-back-menu>New Match</button>') +
    '<button class="btn-secondary" data-share="h2h">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderH2HScreen() {
  if (!state.h2h) state.h2h = { screen: 'menu', mode: 'quiz', roundSize: 10, listId: null, error: null };
  var s = state.h2h;
  if (s.screen === 'create') return renderH2HCreate();
  if (s.screen === 'join') return renderH2HJoin();
  if (s.screen === 'lobby') return renderH2HLobby();
  if (s.screen === 'question') return renderH2HQuestion();
  if (s.screen === 'summary') return renderH2HSummary();
  return renderH2HMenu();
}

/* ============================== live head-to-head ==============================
   A second, separate H2H flow — the async version above is deliberately NOT
   simultaneous (see its own header comment for why). This one is: two
   players see the same question at the same moment and each other's result
   the instant both have answered. Scoped to kind:'quiz' H2H_MODES only (NFL
   Quiz / CFB Quiz) — those are the only modes with a discrete per-question
   flow that a live sync point actually fits; Grid/Blitz/Silhouette/Speed/
   Legends each run their own full-screen engine with no natural place to
   hook a live opponent-status check.

   There's no server/Cloud Function anywhere in this app, so nothing has
   sole authority over when the match advances to the next question — both
   clients independently watch the same Firestore match doc (same matches
   collection, same getMatch/setMatch/watchMatch bridge the async version
   uses, just tagged live:true) and derive the same next state from it.
   Whichever client gets there first writes the next index (or 'finished');
   the other, redundant write that follows is harmless — same "plain reads/
   writes, no transaction, fine at this app's scale" tradeoff firebase-
   sync.js already documents for matches in general. A per-question local
   timer (LIVE_QUESTION_SECONDS) keeps a round from ever stalling forever:
   on timeout, a client submits its own still-blank answer as "no pick" and
   also fills in a placeholder for the OPPONENT if theirs never arrived —
   covers a closed/backgrounded opponent tab, since nobody else could ever
   submit on their behalf otherwise. */
var H2H_LIVE_MODES = H2H_MODES.filter(function (m) { return m.kind === 'quiz'; });
var LIVE_QUESTION_SECONDS = 15;
var LIVE_REVEAL_MS = 2500;
var h2hLiveUnsub = null;
var h2hLiveTimerId = null;
var h2hLiveAdvanceScheduled = -1; // guards this client scheduling the same index's advance twice
function h2hLiveClearTimer() { if (h2hLiveTimerId) { clearTimeout(h2hLiveTimerId); h2hLiveTimerId = null; } }
function h2hLiveStopWatch() { if (h2hLiveUnsub) { h2hLiveUnsub(); h2hLiveUnsub = null; } h2hLiveClearTimer(); }
function h2hLiveWatch(code) {
  h2hLiveStopWatch();
  if (window.__fbSync && window.__fbSync.watchMatch) h2hLiveUnsub = window.__fbSync.watchMatch(code, h2hLiveOnMatchUpdate);
}
function h2hLiveInviteLink(code) { return SITE_URL + '#live=' + code; }
function h2hLiveOpponentSlug(match, mySlug) {
  var slugs = Object.keys(match.players || {});
  return slugs.filter(function (sl) { return sl !== mySlug; })[0] || null;
}
function h2hLiveBackToMenu() {
  h2hLiveStopWatch();
  h2hLiveAdvanceScheduled = -1;
  state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  renderAll();
}
function h2hLiveSetMode(modeId) {
  var s = state.h2hLive, m = h2hModeConfig(modeId);
  if (!s || !m || m.kind !== 'quiz') return;
  s.mode = modeId;
  s.roundSize = (m.roundSizeOptions && m.roundSizeOptions[0]) || 10;
  renderAll();
}
function h2hLiveSetRoundSize(n) { state.h2hLive.roundSize = n; renderAll(); }
function h2hLiveCreateMatch() {
  var s = state.h2hLive;
  var code = generateH2HCode();
  var mySlug = slugify(state.name);
  var match = { live: true, mode: s.mode, roundSize: s.roundSize, status: 'waiting', index: 0, players: {}, answers: {} };
  match.players[mySlug] = { name: state.name, ready: false };
  match.answers[mySlug] = {};
  if (!window.__fbSync || !window.__fbSync.setMatch) return;
  window.__fbSync.setMatch(code, match, false).then(function () {
    h2hRememberCode(code); // shares the async version's "your recent matches" list — live/async codes side by side is fine, both are just match docs
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.screen = 'lobby';
    s.error = null;
    h2hLiveWatch(code);
    renderAll();
  }).catch(function (err) {
    console.error('Create live match failed', err);
    s.error = 'Could not create the match — check your connection and try again.';
    renderAll();
  });
}
function h2hLiveJoinMatch(codeInput) {
  var s = state.h2hLive;
  var code = (codeInput || '').toUpperCase().trim();
  if (!code) return;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match || !match.live) { s.error = 'No live match found with that code.'; s.screen = 'join'; renderAll(); return; }
    var slugs = Object.keys(match.players || {});
    if (slugs.indexOf(mySlug) === -1 && slugs.length >= 2) { s.error = 'That match already has two players.'; s.screen = 'join'; renderAll(); return; }
    if (slugs.indexOf(mySlug) === -1) {
      match.players[mySlug] = { name: state.name, ready: false };
      match.answers = match.answers || {};
      match.answers[mySlug] = {};
    }
    window.__fbSync.setMatch(code, match, false).then(function () {
      h2hRememberCode(code);
      s.code = code;
      s.match = match;
      s.mySlug = mySlug;
      s.mode = match.mode;
      s.roundSize = match.roundSize;
      s.screen = 'lobby';
      s.error = null;
      h2hLiveWatch(code);
      renderAll();
    });
  }).catch(function (err) {
    console.error('Join live match failed', err);
    s.error = 'Could not join — check your connection and try again.';
    s.screen = 'join';
    renderAll();
  });
}
function h2hLiveSetReady() {
  var s = state.h2hLive, match = s.match;
  if (!match || !match.players[s.mySlug]) return;
  match.players[s.mySlug].ready = true;
  s.match = match;
  window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Ready-up failed', err); });
  renderAll();
}
function h2hLiveQueue(s) { return h2hQuestionIds(s.mode, s.code, s.roundSize); }
function h2hLiveCurrentQuestion(s) {
  var queue = h2hLiveQueue(s);
  var id = queue[s.match.index];
  return h2hPool(s.mode).find(function (q) { return q.id === id; });
}
function h2hLiveScore(match, slug) {
  var a = (match.answers && match.answers[slug]) || {};
  var correct = 0, total = 0;
  Object.keys(a).forEach(function (k) { total++; if (a[k].correct) correct++; });
  return { correct: correct, total: total };
}
function h2hLivePickAnswer(i) {
  var s = state.h2hLive, match = s.match;
  if (!match) return;
  var idx = match.index;
  match.answers = match.answers || {};
  match.answers[s.mySlug] = match.answers[s.mySlug] || {};
  if (match.answers[s.mySlug][idx] !== undefined) return;
  var q = h2hLiveCurrentQuestion(s);
  var correct = !!(q && i === q.correctIndex);
  match.answers[s.mySlug][idx] = { choice: i, correct: correct };
  s.match = match;
  playSound(correct ? 'correct' : 'wrong');
  h2hLiveClearTimer();
  window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Live answer submit failed', err); });
  renderAll();
}
// One local timer per question, (re)started the moment that question
// becomes current (see h2hLiveOnMatchUpdate) — fires LIVE_QUESTION_SECONDS
// later and force-fills any still-missing answer (mine and/or the
// opponent's) so a slow or vanished opponent can never stall the round.
function h2hLiveStartQuestionTimer() {
  h2hLiveClearTimer();
  var s = state.h2hLive;
  var code = s.code, idx = s.match.index;
  h2hLiveTimerId = setTimeout(function () {
    var cs = state.h2hLive;
    if (!cs || cs.code !== code || !cs.match || cs.match.index !== idx) return;
    var match = cs.match;
    match.answers = match.answers || {};
    var oppSlug = h2hLiveOpponentSlug(match, cs.mySlug);
    var changed = false;
    match.answers[cs.mySlug] = match.answers[cs.mySlug] || {};
    if (match.answers[cs.mySlug][idx] === undefined) { match.answers[cs.mySlug][idx] = { choice: -1, correct: false }; changed = true; }
    if (oppSlug) {
      match.answers[oppSlug] = match.answers[oppSlug] || {};
      if (match.answers[oppSlug][idx] === undefined) { match.answers[oppSlug][idx] = { choice: -1, correct: false }; changed = true; }
    }
    cs.match = match;
    renderAll();
    if (changed) window.__fbSync.setMatch(code, match, true).catch(function (err) { console.error('Live timeout submit failed', err); });
  }, LIVE_QUESTION_SECONDS * 1000);
}
// Runs on every client once both players have answered the current
// question — schedules (once per index, per client) the write that moves
// the match to the next question after a short reveal pause. Both clients
// do this independently and land on the identical next value, so the
// redundant second write is a harmless no-op rather than a conflict.
function h2hLiveMaybeScheduleAdvance() {
  var s = state.h2hLive, match = s.match;
  if (!match || match.status === 'finished') return;
  var idx = match.index;
  if (h2hLiveAdvanceScheduled === idx) return;
  var slugs = Object.keys(match.players || {});
  if (slugs.length !== 2) return;
  var bothAnswered = slugs.every(function (sl) { return match.answers && match.answers[sl] && match.answers[sl][idx] !== undefined; });
  if (!bothAnswered) return;
  h2hLiveAdvanceScheduled = idx;
  var code = s.code;
  setTimeout(function () {
    var cs = state.h2hLive;
    if (!cs || cs.code !== code || !cs.match || cs.match.index !== idx) return; // stale — already moved on
    var m = cs.match;
    var queue = h2hLiveQueue(cs);
    if (idx + 1 >= queue.length) m.status = 'finished';
    else m.index = idx + 1;
    cs.match = m;
    window.__fbSync.setMatch(code, m, true).catch(function (err) { console.error('Live advance failed', err); });
  }, LIVE_REVEAL_MS);
}
function h2hLiveMaybeCountRecord() {
  var s = state.h2hLive, match = s && s.match;
  if (!match || match.status !== 'finished' || h2hAlreadyCounted(s.code)) return;
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  if (!oppSlug) return;
  var mine = h2hLiveScore(match, s.mySlug), opp = h2hLiveScore(match, oppSlug);
  var st = state.stats.h2h;
  st.matchesPlayed++;
  var diff = mine.correct - opp.correct;
  if (diff > 0) st.wins++;
  else if (diff < 0) st.losses++;
  else st.ties++;
  lsSet('nflTriviaStats', state.stats);
  pushLeaderboard('h2h', { wins: st.wins, losses: st.losses, ties: st.ties, matchesPlayed: st.matchesPlayed });
  h2hMarkCounted(s.code);
  // Counts toward the underlying mode's own stats/rating too, same as a
  // normal solo round — mirrors h2hFinishRound's identical reasoning above.
  if (mine.total > 0) {
    var pct = Math.round(100 * mine.correct / mine.total);
    var modeSt = state.stats[s.mode];
    modeSt.correctTotal += mine.correct;
    modeSt.questionsTotal += mine.total;
    modeSt.roundsPlayed++;
    if (pct > modeSt.bestPct) modeSt.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    pushLeaderboard(s.mode, { bestPct: modeSt.bestPct, correctTotal: modeSt.correctTotal, roundsPlayed: modeSt.roundsPlayed });
  }
}
function h2hLiveOnMatchUpdate(match) {
  var s = state.h2hLive;
  if (!s || !match) return;
  var prevIndex = s.match ? s.match.index : -1;
  var prevStatus = s.match ? s.match.status : null;
  s.match = match;
  if (s.screen === 'lobby') {
    var slugs = Object.keys(match.players || {});
    if (slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].ready; })) {
      if (match.status !== 'active') {
        match.status = 'active';
        window.__fbSync.setMatch(s.code, match, true).catch(function () {});
      }
      s.screen = 'playing';
    }
  }
  if (s.screen === 'playing') {
    if (match.status === 'finished') {
      h2hLiveClearTimer();
      s.screen = 'summary';
      h2hLiveMaybeCountRecord();
    } else {
      if (match.index !== prevIndex || prevStatus !== 'active') { h2hLiveAdvanceScheduled = -1; h2hLiveStartQuestionTimer(); }
      h2hLiveMaybeScheduleAdvance();
    }
  }
  renderAll();
}
function h2hLiveShareLink(link, btn) {
  if (navigator.share) { navigator.share({ title: 'Reads — Live Match', text: 'Join my live trivia match on Reads:', url: link }).catch(function () {}); return; }
  copyTextToClipboard(link, btn);
}
function h2hLiveCardHtml() {
  return discoverRowHtml('h2hLive', 'versus', 'Live Match', 'Both online now · real-time', 'h2h-live-card');
}
function renderH2HLiveMenu() {
  if (!state.name) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('versus') + ' Live Match</h2>' +
      '<p class="mode-desc">Log in above, then come back here to start a live match.</p>' +
      '</div>';
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('versus') + ' Live Match</h2>' +
    '<p class="mode-desc">Both of you answer the same questions at the same time and see each other’s results the instant you’re both done — needs you both online right now. For playing on your own schedule, use Head-to-Head from Home instead.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-live-go-create>Create Match</button>' +
    '<button class="btn-secondary" data-h2h-live-go-join>Join Match</button>' +
    '</div>' +
    '</div>';
}
function renderH2HLiveCreate() {
  var s = state.h2hLive, m = h2hModeConfig(s.mode) || H2H_LIVE_MODES[0];
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Create a Live Match</h2>' +
    '<div class="field-row"><label>Mode<select id="h2h-live-mode">' +
    H2H_LIVE_MODES.map(function (mm) { return '<option value="' + mm.id + '"' + (s.mode === mm.id ? ' selected' : '') + '>' + esc(mm.label) + '</option>'; }).join('') +
    '</select></label></div>' +
    '<div class="chip-row">' +
    m.roundSizeOptions.map(function (n) { return '<button class="chip-toggle' + (s.roundSize === n ? ' active' : '') + '" data-h2h-live-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-live-create>Create &amp; Get Code</button>' +
    '</div>';
}
function renderH2HLiveJoin() {
  var s = state.h2hLive;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Join a Live Match</h2>' +
    '<div class="field-row"><label>Match code<input id="h2h-live-code-input" maxlength="4" placeholder="e.g. 7F3K" autocomplete="off" autocapitalize="characters" style="text-transform:uppercase;" /></label></div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-live-join>Join</button>' +
    '</div>';
}
function renderH2HLiveLobby() {
  var s = state.h2hLive, match = s.match || { players: {} };
  var me = match.players[s.mySlug];
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var link = h2hLiveInviteLink(s.code);
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Live Match &middot; ' + esc(h2hModeLabel(s.mode)) + '</h2>' +
    '<div class="h2h-code">' + esc(s.code) + '</div>' +
    '<p class="mode-desc">Send this link to whoever you’re playing — one tap and they’re in.</p>' +
    '<div class="btn-row"><button class="btn-secondary" data-h2h-live-share-link="' + esc(link) + '">' + icon('share') + ' Share Invite Link</button></div>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + (me && me.ready ? icon('check') + ' Ready' : 'Not ready') + '</span></div>' +
    '<div class="h2h-player-row"><span>' + (opp ? esc(opp.name) : 'Waiting for opponent to join…') + '</span><span>' + (opp ? (opp.ready ? icon('check') + ' Ready' : 'Not ready') : '') + '</span></div>' +
    '</div>' +
    (opp && me && !me.ready ? '<button class="btn-primary" data-h2h-live-ready>I’m Ready</button>' :
      me && me.ready ? '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + '…</p>' : '') +
    '</div>';
}
function renderH2HLivePlaying() {
  var s = state.h2hLive, match = s.match;
  if (!match) return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading…</div></div>';
  var idx = match.index;
  var q = h2hLiveCurrentQuestion(s);
  if (!q) return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading…</div></div>';
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var myAnswer = match.answers && match.answers[s.mySlug] && match.answers[s.mySlug][idx];
  var oppAnswer = oppSlug && match.answers && match.answers[oppSlug] && match.answers[oppSlug][idx];
  var answered = myAnswer !== undefined;
  var revealed = answered && oppAnswer !== undefined;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-exit>' + icon('close') + ' Exit to Home</button></div>' +
    '<div class="quiz-progress">Live &middot; Question ' + (idx + 1) + ' of ' + s.roundSize + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (revealed) {
        if (i === q.correctIndex) cls += ' correct';
        else if (myAnswer.choice === i) cls += ' wrong';
      } else if (answered && myAnswer.choice === i) {
        cls += ' selected';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-h2h-live-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (revealed
      ? '<div class="quiz-feedback" aria-live="polite">' + (myAnswer.correct ? '<span class="feedback-good">' + icon('check') + ' You got it!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Missed it.</span>') +
        ' ' + esc(opp ? opp.name : 'Opponent') + (oppAnswer.correct ? ' got it too.' : ' missed it.') + '</div>'
      : answered
      ? '<p class="mode-desc" aria-live="polite">Waiting on ' + esc(opp ? opp.name : 'your opponent') + '…</p>'
      : '') +
    '</div>';
}
function renderH2HLiveSummary() {
  var s = state.h2hLive, match = s.match || { players: {} };
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var mine = h2hLiveScore(match, s.mySlug);
  var oppScore = oppSlug ? h2hLiveScore(match, oppSlug) : { correct: 0, total: 0 };
  var diff = mine.correct - oppScore.correct;
  var result = diff > 0 ? 'win' : diff < 0 ? 'loss' : 'tie';
  return '<div class="panel">' +
    '<h2 class="panel-title">Live Match Result</h2>' +
    '<div class="h2h-result-banner h2h-result-' + result + '">' + (result === 'win' ? icon('trophy') + ' You Won!' : result === 'loss' ? 'You Lost' : 'Tie Game') + '</div>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + mine.correct + ' / ' + mine.total + ' correct</span></div>' +
    '<div class="h2h-player-row"><span>' + esc(opp ? opp.name : 'Opponent') + '</span><span>' + oppScore.correct + ' / ' + oppScore.total + ' correct</span></div>' +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-live-back-menu>New Match</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderH2HLiveScreen() {
  if (!state.h2hLive) state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  var s = state.h2hLive;
  if (s.screen === 'create') return renderH2HLiveCreate();
  if (s.screen === 'join') return renderH2HLiveJoin();
  if (s.screen === 'lobby') return renderH2HLiveLobby();
  if (s.screen === 'playing') return renderH2HLivePlaying();
  if (s.screen === 'summary') return renderH2HLiveSummary();
  return renderH2HLiveMenu();
}

/* ============================== share cards ==============================
   One shared card-render + share pipeline for every mode's result screen,
   rather than 14 bespoke ones. Renders an offscreen canvas (text/shapes
   only, no image assets drawn onto it — so this has zero cross-origin/
   canvas-tainting risk and, unlike Firebase sync or the service worker,
   works even over file://) and hands it to the OS's native share sheet via
   the Web Share API where supported (the only path that gives Instagram a
   real, working target — Instagram has no web share-intent of its own).
   Falls back to a small modal (download / share-to-X / share-app-to-
   Facebook) on desktop/unsupported browsers. */
// Share Your Result pass: a player's Reads IDENTITY line -- Football
// Rating, tier (Rookie..MVP), and current daily-play streak -- shown on
// every share card/text regardless of whether THIS round happened to move
// the rating (shareRatingLine above only ever fired on a delta, so modes
// that don't touch the rating at all -- Who Am I, the engine-pilot guess
// modes -- never showed anything). Absolute, not a notification: matches
// "their Reads status" as its own persistent line, same real
// getRating()/ratingTierFor()/getStreak() data the Home screen's own
// rating badge and streak flame already use -- nothing new computed, and
// '' (omitted) for a Practice round or anyone without a rating yet, same
// as before. Still folds in this round's delta, in parens, when one
// exists -- real, useful context, not lost, just no longer the only thing
// shown.
function shareStatusLine(delta) {
  var r = getRating();
  if (!r) return '';
  var tier = ratingTierFor(r.score);
  var ratingBit = 'Football Rating ' + r.score + (delta != null && delta !== 0 ? ' (' + (delta > 0 ? '+' : '') + delta + ')' : '');
  var parts = [ratingBit, tier.name];
  var streak = getStreak();
  if (streak.count > 0) parts.push(streak.count + '-day streak');
  return parts.join(' · ');
}
function shareConfigFor(mode) {
  if (mode === 'profile') {
    var pp=getProgression(), career=progressionRankFor(pp.careerXp||0), seasonId=footballSeasonIdForDate();
    var season=normalizeSeasonProgress(pp.seasons&&pp.seasons[seasonId]), seasonRank=seasonRankFor(season.xp||0);
    var pr=getRating(), ps=getStreak(), fav=primaryFavoriteTeam();
    var detail=[pr?pr.score+' Football Rating':'',ps.count?ps.count+'-day streak':'',fav?fav.name+' fan':''].filter(Boolean).join(' · ');
    return {title:'Reads Profile',headline:career.name,sub:seasonId+' '+seasonRank.name+' · '+Number(pp.careerXp||0).toLocaleString()+' career XP',detail:detail,
      shareText:'My Reads Football profile: '+career.name+' career rank · '+seasonId+' '+seasonRank.name+(pr?' · '+pr.score+' Football Rating':'')+(ps.count?' · '+ps.count+'-day streak':'')+'. reads.football'};
  }
  if (mode === 'quiz' || mode === 'cfbQuiz' || mode === 'xso') {
    var t = state[mode];
    var pct = Math.round(100 * t.correctCount / t.queue.length);
    var label = mode === 'quiz' ? 'NFL Quiz' : mode === 'cfbQuiz' ? 'CFB Quiz' : "X's & O's";
    var rl = shareStatusLine(t.ratingDelta);
    return { title: label, headline: pct + '%', sub: t.correctCount + ' / ' + t.queue.length + ' correct', detail: rl,
      shareText: 'I scored ' + pct + '% on ' + label + ' in Reads! 🏈' + (rl ? ' ' + rl : '') };
  }
  if (mode === 'daily') {
    var d = state.daily;
    var pct2 = Math.round(100 * d.correctCount / d.queue.length);
    // Share Your Result pass: streakN/streakBit used to be daily's own
    // one-off way of showing the streak since shareRatingLine (the old,
    // delta-only helper) never included it -- shareStatusLine now folds
    // the real streak into every mode's line universally, so keeping this
    // as a second, separate streak mention would just duplicate it.
    var rlD = shareStatusLine(d.ratingDelta);
    var rivalToday = dailyRivalRows('today');
    var rivalWeek = dailyRivalRows('week');
    var rankToday = dailyRivalMeIndex(rivalToday);
    var rankWeek = dailyRivalMeIndex(rivalWeek);
    var rivalPts = dailyRivalPoints(dailyRecordFromState(pct2));
    var rivalLine = rivalPts + ' Rival Points' + (rankToday ? ' · #' + rankToday + ' today' : '') + (rankWeek ? ' · #' + rankWeek + ' this week' : '');
    return { title: 'Daily Reads', headline: pct2 + '%', sub: d.correctCount + ' / ' + d.queue.length + ' correct' + (d.bonusPoints ? ' · +' + d.bonusPoints + ' bonus' : ''), detail: [rivalLine, rlD].filter(Boolean).join(' · '),
      shareText: 'Daily Reads: ' + pct2 + '% · ' + rivalPts + ' Rival Points' + (rankToday ? ' · #' + rankToday + ' today' : '') + '. Think you can beat it? reads.football' };
  }
  if (mode === 'grid' || mode === 'cfbGrid') {
    var g = state[mode];
    var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
    var label2 = mode === 'grid' ? 'NFL Grid' : 'CFB Grid';
    var rlG = shareStatusLine(g.ratingDelta);
    var sweepBit = correctCells === 9 ? 'Clean sweep!' : '';
    return { title: label2, headline: correctCells + '/9', sub: g.totalScore + ' points', detail: [sweepBit, rlG].filter(Boolean).join(' · '),
      shareText: 'I got ' + correctCells + '/9 on the ' + label2 + ' in Reads (' + g.totalScore + ' pts)!' + (rlG ? ' ' + rlG : '') };
  }
  if (mode === 'blitz' || mode === 'cfbBlitz') {
    var b = state[mode], total = b.list.answers.length;
    var label3 = mode === 'blitz' ? 'NFL Blitz' : 'CFB Blitz';
    var rlB = shareStatusLine(b.ratingDelta);
    var bSweepBit = b.matched.length === total ? 'Clean sweep!' : '';
    return { title: label3, headline: b.matched.length + '/' + total, sub: b.list.title, detail: [bSweepBit, rlB].filter(Boolean).join(' · '),
      shareText: 'I found ' + b.matched.length + '/' + total + ' on "' + b.list.title + '" in Reads ' + label3 + '!' + (rlB ? ' ' + rlB : '') };
  }
  if (mode === 'speed' || mode === 'cfbSpeed') {
    var s = state[mode];
    var label4 = mode === 'speed' ? 'NFL Speed' : 'CFB Speed';
    var rlS = shareStatusLine(s.ratingDelta);
    return { title: label4, headline: s.score + ' pts', sub: s.correctCount + ' / ' + s.totalCount + ' correct', detail: ['Best streak: ' + s.bestStreak, rlS].filter(Boolean).join(' · '),
      shareText: 'I scored ' + s.score + ' points on ' + label4 + ' in Reads! Best streak: ' + s.bestStreak + (rlS ? ' ' + rlS : '') };
  }
  if (mode === 'silhouette') {
    var sil = state.silhouette;
    var silCorrectCount = sil.results.filter(function (r) { return r.correct; }).length;
    var rlSil = shareStatusLine(sil.ratingDelta);
    return { title: 'NFL Silhouette', headline: sil.score + ' pts', sub: silCorrectCount + ' / ' + sil.queue.length + ' guessed', detail: rlSil,
      shareText: 'I scored ' + sil.score + ' points on NFL Silhouette in Reads!' + (rlSil ? ' ' + rlSil : '') };
  }
  if (mode === 'higherLower') {
    var hl = state.higherLower;
    var hlCat = hlCategoryConfig(hl.category);
    var hlNoun = hlCat.entityLabel === 'stadium' ? 'stadium' : 'player';
    var rlHl = shareStatusLine(hl.ratingDelta);
    return { title: 'Higher or Lower — ' + hlCat.label, headline: String(hl.streak), sub: hl.streak === 1 ? hlNoun : hlNoun + 's', detail: rlHl,
      shareText: 'I built a ' + hl.streak + '-' + hlNoun + ' streak on Higher or Lower (' + hlCat.label + ') in Reads! Can you beat it?' + (rlHl ? ' ' + rlHl : '') };
  }
  if (mode === 'iq' || mode === 'cfbIq') {
    var iq = state[mode];
    var label5 = mode === 'iq' ? 'Football IQ Test' : 'College Football IQ Test';
    var titleFn = mode === 'iq' ? iqTitle : cfbIqTitle;
    var rlIq = shareStatusLine(iq.ratingDelta);
    return { title: label5, headline: String(iq.iqScore), sub: titleFn(iq.iqScore), detail: [iq.correct + ' / ' + iq.total + ' correct', rlIq].filter(Boolean).join(' · '),
      shareText: 'My ' + label5 + ' score in Reads: ' + iq.iqScore + ' (' + titleFn(iq.iqScore) + ')' + (rlIq ? ' ' + rlIq : '') };
  }
  if (mode === 'legends' || mode === 'cfbLegends') {
    var l = state[mode];
    var label6 = mode === 'legends' ? '17-0' : 'CFB 12-0';
    var rlL = shareStatusLine(l.ratingDelta);
    var recordLabel6 = mode === 'cfbLegends' ? 'Regular season' : 'Projected record';
    var postseasonBit6 = mode === 'cfbLegends' ? l.postseasonLabel : '';
    return { title: label6, headline: l.grade, sub: l.gradeLabel, detail: [recordLabel6 + ': ' + l.wins + '-' + l.losses, postseasonBit6, rlL].filter(Boolean).join(' · '),
      shareText: 'My ' + label6 + ' team graded out ' + l.grade + ' (' + l.gradeLabel + ') in Reads! ' + recordLabel6 + ' ' + l.wins + '-' + l.losses + (postseasonBit6 ? ' — ' + postseasonBit6 : '') + (rlL ? ' ' + rlL : '') };
  }
  if (mode === 'h2h') {
    var h = state.h2h, hMatch = h.match || { players: {} };
    var hSlugs = Object.keys(hMatch.players || {});
    var hMe = hMatch.players[h.mySlug] || { correctCount: h.correctCount, total: h.queue.length };
    var hOppSlug = hSlugs.filter(function (sl) { return sl !== h.mySlug; })[0];
    var hOpp = hOppSlug ? hMatch.players[hOppSlug] : null;
    var hOppDone = !!(hOpp && hOpp.finishedAt);
    var hRl = shareStatusLine(h.ratingDelta);
    var hResult = !hOppDone ? '' : (hMe.correctCount > hOpp.correctCount ? 'Won' : hMe.correctCount < hOpp.correctCount ? 'Lost' : 'Tied') + ' vs ' + hOpp.name;
    return { title: 'Head-to-Head', headline: hMe.correctCount + '/' + hMe.total, sub: hResult || 'Waiting on opponent', detail: hRl,
      shareText: 'Head-to-Head in Reads: ' + hMe.correctCount + '/' + hMe.total + (hResult ? ' — ' + hResult : '') + '!' + (hRl ? ' ' + hRl : '') };
  }
  // Share Your Result pass: Player From Clues (NFL/CFB Who Am I) had no
  // share hook at all -- real result data (results[].correct) already
  // existed, just never read by this function.
  if (mode === 'playerClues' || mode === 'cfbPlayerClues') {
    var pc = state[mode];
    var pcCorrect = pc.results.filter(function (r) { return r.correct; }).length;
    var pcLabel = mode === 'playerClues' ? 'NFL Player From Clues' : 'CFB Player From Clues';
    var pcRl = shareStatusLine();
    return { title: pcLabel, headline: pcCorrect + '/' + pc.queue.length, sub: 'players solved', detail: pcRl,
      shareText: 'I solved ' + pcCorrect + '/' + pc.queue.length + ' ' + pcLabel + ' on Reads Football.' + (pcRl ? ' ' + pcRl : '') };
  }
  // Share Your Result pass: every real "guess" capability served through
  // the shared engine-pilot shell (Offense by College, SB Champion Offense
  // by College, CFB Rankings, CFB Upsets, NFL/CFB Game Result, NFL Box
  // Scores, plus Draft/Championship/Lineup/Heisman) gets a real share card
  // from this one branch -- keyed by ENGINE_PILOT_MODES (the same registry
  // renderEnginePilotScreen() itself reads) rather than one hardcoded
  // branch per mode, so a future capability added to that shared shell
  // gets sharing for free instead of silently missing it again.
  if (ENGINE_PILOT_MODES[mode] && state.enginePilot && state.enginePilot.modeKey === mode) {
    var epCfg = ENGINE_PILOT_MODES[mode], ep = state.enginePilot;
    var epRl = shareStatusLine();
    return { title: epCfg.title, headline: ep.correctCount + '/' + ep.roundSize, sub: 'correct', detail: epRl,
      shareText: 'I got ' + ep.correctCount + '/' + ep.roundSize + ' on ' + epCfg.title + ' in Reads Football.' + (epRl ? ' ' + epRl : '') };
  }
  // User feedback: "fix the share card for every game mode" -- the ~20
  // mechanicPilot formats (Risk It, Three Strikes, Double or Nothing,
  // Blind Resume, Mystery Roster, Common Link, Guess the Ranking, Stat
  // Target, Fact or Fake, Reverse Trivia, King of the Hill, NFL+CFB)
  // had NO share config at all -- their Complete screen had no Share
  // button, and even if one existed shareResultCard would have silently
  // no-op'd (shareConfigFor returned null). Reuses
  // renderMechanicPilotCompleteSummary's own real per-kind summary text
  // (engine-game-ui.js) for the sub-line rather than duplicating that
  // per-kind logic a second time -- one real source of truth for "what
  // actually happened this round." Headline prefers a real running
  // score/points/streak value already on the server view when one
  // exists for this kind, falling back to a plain correct/complete
  // readout for single-round kinds that don't track a running number.
  if (ENGINE_MECHANIC_MODES[mode] && state.mechanicPilot && state.mechanicPilot.modeKey === mode) {
    var mpCfg = ENGINE_MECHANIC_MODES[mode], mp = state.mechanicPilot;
    var mpR = mp.result || {}, mpV = mp.view || {};
    var mpHeadline = 'Complete';
    if (mpV.score != null) mpHeadline = String(mpV.score);
    else if (mpV.points != null) mpHeadline = String(mpV.points);
    else if (mpV.consecutive_defenses != null) mpHeadline = String(mpV.consecutive_defenses);
    else if (mpR.correct === true) mpHeadline = 'Correct!';
    var mpSummaryHtml = renderMechanicPilotCompleteSummary(mpCfg, mp);
    var mpSub = String(mpSummaryHtml).replace(/<[^>]+>/g, '').trim() || mpCfg.title;
    var mpRl = shareStatusLine();
    return { title: mpCfg.title, headline: mpHeadline, sub: mpSub, detail: mpRl,
      shareText: 'I played ' + mpCfg.title + ' in Reads! ' + mpSub + (mpRl ? ' ' + mpRl : '') };
  }
  return null;
}
// Strokes one of the app's own SVG icons (ICON_PATHS) onto a canvas 2D
// context — extracts each <path d="..."> from the markup string and draws
// it via Path2D, so the share card uses the literal same trophy/etc glyph
// as the rest of the UI instead of a separately-drawn one-off. (x, y) is
// the icon's top-left in canvas space; size is the rendered width/height —
// ICON_PATHS is authored on a 24x24 viewBox, so scale = size / 24.
function svgAttr(tag, name) {
  var m = tag.match(new RegExp(name + '="([^"]+)"'));
  return m ? parseFloat(m[1]) : 0;
}
function drawIconPath(ctx, name, x, y, size, color) {
  var html = ICON_PATHS[name];
  if (!html) return;
  var tags = html.match(/<[a-z]+[^>]*\/>/g) || [];
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(size / 24, size / 24);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  tags.forEach(function (tag) {
    if (tag.indexOf('<path') === 0) {
      var d = tag.match(/d="([^"]+)"/);
      if (d) ctx.stroke(new Path2D(d[1]));
    } else if (tag.indexOf('<circle') === 0) {
      ctx.beginPath();
      ctx.arc(svgAttr(tag, 'cx'), svgAttr(tag, 'cy'), svgAttr(tag, 'r'), 0, Math.PI * 2);
      ctx.stroke();
    } else if (tag.indexOf('<rect') === 0) {
      ctx.strokeRect(svgAttr(tag, 'x'), svgAttr(tag, 'y'), svgAttr(tag, 'width'), svgAttr(tag, 'height'));
    } else if (tag.indexOf('<ellipse') === 0) {
      ctx.beginPath();
      ctx.ellipse(svgAttr(tag, 'cx'), svgAttr(tag, 'cy'), svgAttr(tag, 'rx'), svgAttr(tag, 'ry'), 0, 0, Math.PI * 2);
      ctx.stroke();
    }
  });
  ctx.restore();
}
function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
// Lightens (positive percent) or darkens (negative) a "#rrggbb" hex color by
// blending it toward white/black — used to build the share card's gradient
// bar from a single favorite-team color without needing 3 hand-picked shades
// per team the way the fixed brand-orange gradient below has.
function shadeHexColor(hex, percent) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  var r = (num >> 16) & 255, g = (num >> 8) & 255, b = num & 255;
  var t = percent < 0 ? 0 : 255, p = Math.abs(percent);
  return 'rgb(' + (Math.round((t - r) * p) + r) + ',' + (Math.round((t - g) * p) + g) + ',' + (Math.round((t - b) * p) + b) + ')';
}
function hexToRgbaString(hex, alpha) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  return 'rgba(' + ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255) + ',' + alpha + ')';
}
// format: 'square' (1080x1080, X/general-purpose) or 'story' (1080x1920,
// Instagram/Snapchat Stories). The header (logo/brand, divider) and footer
// pill stay pinned to their same distance from the top/bottom regardless of
// format — only the vertical CENTER of the layout (where the glow, title,
// big headline number, sub/detail lines sit) moves to the middle of
// whatever's left between them, so a story card doesn't just look like a
// square card with a huge empty gap stretched into the bottom.
// Share Your Result pass: every piece of real, variable-length text on the
// card (title, headline, sub, status line, identity line, footer) now
// routes through this one shrink-then-ellipsis routine instead of each
// having its own copy-pasted loop -- a long real username, mode title, or
// tier/streak combo shrinks first (down to minPx), then truncates with an
// ellipsis as a last resort, so nothing can ever run past the card's own
// edges or collide with a neighboring element. Returns the actual px size
// used, since the identity-line swatch dot needs to know it to vertically
// balance against the (possibly shrunk) text.
// Real bug fix (user report: "why is the reads logo not on the share
// card"): the card was never actually drawing the real Reads logo -- it
// drew a hand-rolled approximation instead (a thin drawIconPath goalpost
// outline + plain system-font "READS" text), which doesn't read as *the*
// logo at a glance the way the real chrome/gold wordmark image does
// everywhere else in the app (splash, loading screen, app icon). Preload
// the actual asset once at script load so it's essentially guaranteed
// ready by the time a user reaches any share button several screens deep,
// and draw it as a real image on the canvas in drawShareCard below.
var _shareLogoImg = null;
(function preloadShareLogoImg() {
  var img = new Image();
  img.onload = function () { _shareLogoImg = img; };
  img.src = 'assets/brand/reads-logo.jpg';
})();
function fitShareText(ctx, text, font, maxWidth, startPx, minPx, weight) {
  var px = startPx;
  ctx.font = weight + ' ' + px + 'px ' + font;
  while (ctx.measureText(text).width > maxWidth && px > minPx) {
    px -= 2;
    ctx.font = weight + ' ' + px + 'px ' + font;
  }
  while (ctx.measureText(text).width > maxWidth && text.length > 4) {
    text = text.slice(0, -2) + '…';
  }
  return { text: text, px: px };
}
function drawShareCard(ctx, cfg, format) {
  var W = 1080, H = format === 'story' ? 1920 : 1080, FONT = '-apple-system, "Segoe UI", Helvetica, Arial, sans-serif';
  var midY = format === 'story' ? 1000 : 500;
  var shareDesign = selectedShareDesign();
  var shareDesignId = shareDesign ? shareDesign.id : 'classic';
  // A favorite team (if set) themes the glow/bars/headline-number/team line —
  // the one thing on this card that's actually personal to whoever's sharing
  // it. The corner "READS" brand mark deliberately stays brand-orange either
  // way, so the card still reads as this app's no matter whose team color
  // is on it. rawAccent/rawAccent2 are the team's true colors (used for the
  // bar and swatch dot, where staying faithful to the team matters more than
  // contrast); accent/accent2 run through readableOnDark first — the same
  // fix already applied to the on-screen rating ring/greeting text — because
  // a dark team color (Ravens purple, Auburn navy, Saints black) used
  // straight as the giant headline number's fill was otherwise nearly
  // invisible against this card's own dark background. That was the actual
  // bug behind "doesn't look like my team" — the color was there, just
  // unreadable, not more personalized so much as broken.
  var fav = primaryFavoriteTeam();
  var rawAccent = fav ? fav.color : '#d9a63c';
  var rawAccent2 = fav ? (fav.color2 || fav.color) : shadeHexColor(rawAccent, -0.2);
  if (shareDesignId === 'allpro' || shareDesignId === 'legend') {
    rawAccent = '#d9a63c';
    rawAccent2 = shareDesignId === 'legend' ? '#7b5814' : '#f0cf77';
  }
  var accent = readableOnDark(rawAccent);
  var accent2 = readableOnDark(rawAccent2);

  // Subtle top-to-bottom gradient instead of a flat fill — reads as a lot
  // less "placeholder" than a single flat navy rectangle.
  var bgGrad = ctx.createLinearGradient(0, 0, 0, H);
  if (shareDesignId === 'team' && fav) {
    bgGrad.addColorStop(0, shadeHexColor(fav.color, -0.65));
    bgGrad.addColorStop(1, '#070a12');
  } else if (shareDesignId === 'spotlight') {
    bgGrad.addColorStop(0, '#16264b');
    bgGrad.addColorStop(1, '#070b14');
  } else if (shareDesignId === 'allpro') {
    bgGrad.addColorStop(0, '#211d12');
    bgGrad.addColorStop(1, '#090b10');
  } else if (shareDesignId === 'legend') {
    bgGrad.addColorStop(0, '#15120b');
    bgGrad.addColorStop(1, '#050607');
  } else {
    bgGrad.addColorStop(0, '#101a34');
    bgGrad.addColorStop(1, '#080d18');
  }
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  if (shareDesignId === 'allpro' || shareDesignId === 'legend') {
    ctx.strokeStyle = shareDesignId === 'legend' ? 'rgba(217,166,60,0.95)' : 'rgba(240,207,119,0.85)';
    ctx.lineWidth = shareDesignId === 'legend' ? 14 : 9;
    ctx.strokeRect(ctx.lineWidth / 2, ctx.lineWidth / 2, W - ctx.lineWidth, H - ctx.lineWidth);
  }

  // Soft spotlight glow centered behind the headline stat — draws the eye
  // straight to the number instead of every element competing at equal
  // visual weight. Stronger + wider, and a touch more opaque when a favorite
  // team is set, so the theming actually reads at a glance instead of being
  // a barely-there tint.
  var glow = ctx.createRadialGradient(W / 2, midY, 40, W / 2, midY, 520);
  var glowAlpha = shareDesignId === 'spotlight' ? 0.42 : shareDesignId === 'team' ? 0.38 : (fav ? 0.30 : 0.20);
  glow.addColorStop(0, hexToRgbaString(accent, glowAlpha));
  glow.addColorStop(1, hexToRgbaString(accent, 0));
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);

  // Two-tone bar when the team actually has a second color (Auburn's navy
  // into orange, etc.) instead of the old single-color-faded-into-itself
  // gradient, which flattened every two-tone team down to looking like a
  // solid-color program.
  var barGrad = ctx.createLinearGradient(0, 0, W, 0);
  barGrad.addColorStop(0, shadeHexColor(rawAccent, 0.35));
  barGrad.addColorStop(0.5, rawAccent);
  barGrad.addColorStop(1, rawAccent2);
  ctx.fillStyle = barGrad;
  ctx.fillRect(0, 0, W, 18);
  ctx.fillRect(0, H - 18, W, 18);

  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';
  if (_shareLogoImg) {
    // The real chrome/gold Reads wordmark image -- same asset used for the
    // splash/loading screen -- drawn straight onto the card so it actually
    // reads as *the* logo instead of a hand-drawn approximation of it.
    var logoW = 250, logoH = logoW * (_shareLogoImg.height / _shareLogoImg.width);
    ctx.drawImage(_shareLogoImg, 60, 36, logoW, logoH);
  } else {
    // Fallback for the rare case the image hasn't finished preloading yet
    // (drawIconPath supports plain <path>-only icons like this one; no
    // transform= sub-elements, same constraint that ruled out the football
    // icon here originally).
    drawIconPath(ctx, 'goalpost', 60, 64, 42, '#d9a63c');
    ctx.fillStyle = '#d9a63c';
    ctx.font = '800 44px ' + FONT;
    ctx.fillText('READS', 116, 112);
    ctx.fillStyle = '#9aa8c2';
    ctx.font = '600 26px ' + FONT;
    ctx.fillText('NFL & CFB Trivia', 116, 150);
  }
  ctx.strokeStyle = 'rgba(238,242,248,0.1)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(60, 192); ctx.lineTo(W - 60, 192); ctx.stroke();

  // Share Your Result pass: player identity line -- username (if set) and
  // favorite team (if set), combined into the SAME single row the
  // favorite-team swatch already occupied rather than adding a new row,
  // so this stays a pure content change with zero layout-cascade risk
  // (title/headline/sub/detail below are all positioned off midY, which
  // this row's height was never part of). "Team Name fan" matches this
  // pass's own example copy exactly; chant is dropped from this line
  // specifically to leave room for the username without three-stacking
  // text on one row -- the swatch dot alone already carries the team's
  // color identity. Auto-shrinks (same technique as the headline number
  // below), then truncates with an ellipsis as a last resort, so a
  // pathologically long real username can never run off the card or
  // collide with the swatch dot.
  // Full Visual + Interactive Redesign pass: the identity line now draws as
  // a real pill badge (rounded-rect background + border), matching the
  // redesigned share-card mockup's "★ TEAM NAME FAN" treatment, instead of
  // bare text floating on the dark background. Still leads with the real
  // two-tone team-color swatch dot when a favorite team is set (a more
  // precise, real personalization signal than a flat star glyph alone
  // would be -- Auburn's navy+orange, e.g., isn't just "one team color"),
  // with the same star glyph the mockup uses added alongside it, not
  // instead of it.
  // Real bug fix (user report: title text rendered "on top of" this
  // pill): titleY below was a fixed offset from midY (280 for square
  // format) with NO awareness of where this pill's own bottom edge
  // actually landed (260) -- only a 20px gap, nowhere near enough real
  // clearance for a 42px title font's own ascent (~30px+) above its
  // baseline. contentTopY tracks the real bottom of whatever was just
  // drawn (this pill, when present) so titleY can guarantee real
  // clearance regardless of format/identity-line length, instead of a
  // fixed number that only happened to work when no pill was drawn.
  var contentTopY = 192;
  var identityParts = [];
  if (state.name) identityParts.push(state.name);
  if (fav) identityParts.push(fav.name + ' fan');
  if (identityParts.length) {
    var pillY = 192 + 24, pillH = 44, pillPadX = 18;
    var dotR = 10;
    ctx.font = '700 27px ' + FONT;
    var identityFit0 = fitShareText(ctx, identityParts.join('  ·  '), FONT, W - 120 - (fav ? 40 : 24), 27, 18, '700');
    var textW = ctx.measureText(identityFit0.text).width;
    var iconW = fav ? (dotR * 2 + 10) : (22 + 8);
    var pillW = pillPadX * 2 + iconW + textW;
    var pillX = 60;
    // accent (readableOnDark), not rawAccent -- a dark true team color
    // (Cowboys navy, Ravens purple) at even 0.55 alpha was nearly
    // invisible as a pill outline against this card's own dark
    // background; the swatch dot below is where staying faithful to the
    // team's literal dark color matters, this pill boundary needs to
    // actually read as a pill first.
    roundRectPath(ctx, pillX, pillY, pillW, pillH, pillH / 2);
    ctx.fillStyle = hexToRgbaString(accent, 0.14);
    ctx.fill();
    ctx.strokeStyle = hexToRgbaString(accent, 0.6);
    ctx.lineWidth = 1.5;
    roundRectPath(ctx, pillX, pillY, pillW, pillH, pillH / 2);
    ctx.stroke();
    var iconCX = pillX + pillPadX + (fav ? dotR : 11), iconCY = pillY + pillH / 2;
    if (fav) {
      ctx.save();
      ctx.beginPath(); ctx.arc(iconCX, iconCY, dotR, 0, Math.PI * 2); ctx.clip();
      ctx.fillStyle = rawAccent; ctx.fillRect(iconCX - dotR, iconCY - dotR, dotR, dotR * 2);
      ctx.fillStyle = rawAccent2; ctx.fillRect(iconCX, iconCY - dotR, dotR, dotR * 2);
      ctx.restore();
      ctx.strokeStyle = 'rgba(238,242,248,0.35)';
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(iconCX, iconCY, dotR, 0, Math.PI * 2); ctx.stroke();
    } else {
      drawIconPath(ctx, 'star', iconCX - 11, iconCY - 11, 22, accent);
    }
    ctx.textAlign = 'left';
    ctx.font = '700 ' + identityFit0.px + 'px ' + FONT;
    ctx.fillStyle = '#eef2f8';
    ctx.fillText(identityFit0.text, pillX + pillPadX + iconW, pillY + pillH / 2 + 9);
    contentTopY = pillY + pillH;
  }

  // Decorative flanking dashes around the mode title -- matches the
  // mockup's "— CFB 12-0 —" treatment, purely ornamental (drawn AFTER
  // measuring the real title text so the dashes always sit just outside
  // it regardless of length).
  ctx.textAlign = 'center';
  var titleFit = fitShareText(ctx, cfg.title, FONT, W - 200, 42, 26, '700');
  // 56px real clearance from contentTopY to the title's OWN baseline,
  // plus that baseline still needs to clear a ~42px font's real ascent
  // (~30px above the baseline) -- the max() only kicks in for square
  // format (where midY-220 alone wasn't enough room above the identity
  // pill); story format's own midY-220 already had plenty of clearance
  // and is unaffected.
  var titleY = Math.max(midY - 220, contentTopY + 56), titleWidth = ctx.measureText(titleFit.text).width;
  ctx.fillStyle = '#eef2f8';
  ctx.fillText(titleFit.text, W / 2, titleY);
  ctx.strokeStyle = hexToRgbaString(rawAccent, 0.5);
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(W / 2 - titleWidth / 2 - 46, titleY - 8); ctx.lineTo(W / 2 - titleWidth / 2 - 18, titleY - 8);
  ctx.moveTo(W / 2 + titleWidth / 2 + 18, titleY - 8); ctx.lineTo(W / 2 + titleWidth / 2 + 46, titleY - 8);
  ctx.stroke();

  // Headline number auto-shrinks if a longer value (e.g. a big Speed-round
  // point total) would otherwise run past the card's edges — short values
  // (percentages, grades, streak counts) still get the full, bold size this
  // card is built around.
  var headlineFit = fitShareText(ctx, cfg.headline, FONT, W - 160, 160, 70, '800');
  ctx.fillStyle = accent;
  ctx.fillText(headlineFit.text, W / 2, midY);

  var subFit = fitShareText(ctx, cfg.sub, FONT, W - 120, 46, 28, '600');
  ctx.fillStyle = '#eef2f8';
  ctx.fillText(subFit.text, W / 2, midY + 90);
  // Full Visual + Interactive Redesign pass: a real 3-box stat row (Football
  // Rating / Tier / Streak) replacing the old single-line detail text --
  // matches the redesigned share-card mockup's stat strip. Pulls the same
  // real getRating()/ratingTierFor()/getStreak() data shareStatusLine()
  // already uses for the plain-text share message (that string is
  // untouched, still used for the native-share/copy/X text) -- this is
  // purely how the CANVAS card presents the identical real numbers.
  // Streak box only appears when the real streak is > 0 (never a fake
  // "0-day streak" box). cfg.detail (any mode-specific extra bit folded
  // into it, e.g. this round's rating delta) still renders as its own
  // smaller line above the boxes when present, so nothing already shown
  // is silently dropped.
  var statR = getRating();
  if (cfg.detail) {
    var detailFit = fitShareText(ctx, cfg.detail, FONT, W - 120, 32, 20, '500');
    ctx.fillStyle = '#9aa8c2';
    ctx.fillText(detailFit.text, W / 2, midY + 140);
  }
  if (statR) {
    var statTier = ratingTierFor(statR.score);
    var statStreak = getStreak();
    var boxes = [{ icn: 'trophy', val: String(statR.score), lbl: 'Football Rating' }, { icn: 'shield', val: statTier.name, lbl: 'Tier' }];
    if (statStreak.count > 0) boxes.push({ icn: 'flame', val: statStreak.count + '-Day', lbl: 'Streak' });
    var boxY = midY + (cfg.detail ? 168 : 150), boxH = 96, boxGap = 16, boxAreaW = W - 120;
    var boxW = (boxAreaW - boxGap * (boxes.length - 1)) / boxes.length;
    boxes.forEach(function (b, i) {
      var bx = 60 + i * (boxW + boxGap);
      roundRectPath(ctx, bx, boxY, boxW, boxH, 16);
      ctx.fillStyle = 'rgba(238,242,248,0.05)';
      ctx.fill();
      ctx.strokeStyle = hexToRgbaString(rawAccent, 0.3);
      ctx.lineWidth = 1.5;
      roundRectPath(ctx, bx, boxY, boxW, boxH, 16);
      ctx.stroke();
      drawIconPath(ctx, b.icn, bx + boxW / 2 - 12, boxY + 14, 24, accent);
      ctx.textAlign = 'center';
      var valFit = fitShareText(ctx, b.val, FONT, boxW - 18, 26, 15, '800');
      ctx.fillStyle = '#eef2f8';
      ctx.fillText(valFit.text, bx + boxW / 2, boxY + 68);
      ctx.font = '600 15px ' + FONT;
      ctx.fillStyle = '#9aa8c2';
      ctx.fillText(b.lbl, bx + boxW / 2, boxY + 87);
    });
  }

  // Footer name/date as a soft pill chip rather than bare text floating at
  // the bottom — a small thing that makes the whole card feel considered
  // rather than assembled from four independent fillText calls. Border picks
  // up the team's raw color at low opacity so the theming carries all the
  // way to the bottom of the card, not just the middle. Capped to a fixed
  // max width (rather than only shrinking once too wide, like every other
  // line above) since the pill's own background rectangle is sized off the
  // text width -- a very long real username still needs a hard ceiling so
  // the pill itself can never run past the card's left/right edges.
  var footerFit = fitShareText(ctx, (state.name ? state.name + ' — ' : '') + todayStr(), FONT, W - 160, 30, 20, '600');
  ctx.font = '600 ' + footerFit.px + 'px ' + FONT;
  var footerWidth = ctx.measureText(footerFit.text).width;
  var footerX = W / 2 - footerWidth / 2 - 28, footerY = H - 98, footerW = footerWidth + 56, footerH = 54;
  ctx.fillStyle = 'rgba(238,242,248,0.06)';
  roundRectPath(ctx, footerX, footerY, footerW, footerH, 27);
  ctx.fill();
  ctx.strokeStyle = hexToRgbaString(rawAccent, 0.45);
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, footerX, footerY, footerW, footerH, 27);
  ctx.stroke();
  ctx.fillStyle = '#c3cbdc';
  ctx.fillText(footerFit.text, W / 2, H - 63);
}
function shareResultCard(mode) {
  var cfg = shareConfigFor(mode);
  if (!cfg) return;
  // Every share path (native share sheet, copy-text, Share to X) reads
  // cfg.shareText — appending the site link once, here, means whoever
  // receives it has something to tap through and play themselves instead
  // of just seeing a score with no way to act on it.
  cfg.shareText = cfg.shareText + ' Play at ' + SITE_URL;
  var canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = 1080;
  var ctx = canvas.getContext('2d');
  drawShareCard(ctx, cfg);
  canvas.toBlob(function (blob) {
    var file = null;
    if (blob) { try { file = new File([blob], 'reads-result.png', { type: 'image/png' }); } catch (e) { file = null; } }
    if (file && navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      navigator.share({ files: [file], title: cfg.title, text: cfg.shareText, url: SITE_URL }).catch(function () {});
    } else {
      openShareModal(canvas.toDataURL('image/png'), cfg);
    }
  }, 'image/png');
}
var shareTriggerEl = null;
var shareCurrentCfg = null;
// 'square' (1080x1080 — X/general) or 'story' (1080x1920 — Instagram/Snap
// Stories). Only the modal fallback path gets a choice — the native
// navigator.share() branch in shareResultCard() shares whatever the OS
// share sheet was opened with (square) and closes immediately, so there's
// no UI moment to offer a toggle there anyway.
var shareCurrentFormat = 'square';
function renderShareDesignPicker() {
  var row = document.getElementById('share-design-row');
  if (!row) return;
  var selected = selectedShareDesign();
  var xp = Number(getProgression().careerXp) || 0;
  row.innerHTML = SHARE_CARD_DESIGNS.map(function (d) {
    var unlocked = xp >= d.minXp;
    var active = selected && selected.id === d.id;
    return '<button class="share-design-chip' + (active ? ' active' : '') + '"' +
      (unlocked ? ' data-share-design="' + esc(d.id) + '"' : ' disabled') + '>' +
      '<b>' + esc(d.title) + '</b><small>' + (unlocked ? (active ? 'Selected' : 'Use design') : d.minXp + ' XP') + '</small>' +
      '</button>';
  }).join('');
}
function renderShareCard(format) {
  if (!shareCurrentCfg) return;
  var canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = format === 'story' ? 1920 : 1080;
  drawShareCard(canvas.getContext('2d'), shareCurrentCfg, format);
  var img = document.getElementById('share-preview');
  if (img) img.src = canvas.toDataURL('image/png');
  shareCurrentFormat = format;
  document.querySelectorAll('[data-share-format]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.shareFormat === format);
  });
}
function openShareModal(dataUrl, cfg) {
  shareCurrentCfg = cfg;
  shareCurrentFormat = 'square';
  renderShareDesignPicker();
  shareTriggerEl = document.activeElement;
  var img = document.getElementById('share-preview');
  if (img) img.src = dataUrl;
  document.querySelectorAll('[data-share-format]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.shareFormat === 'square');
  });
  var fbBtn = document.getElementById('share-facebook');
  if (fbBtn) fbBtn.style.display = (location.protocol === 'http:' || location.protocol === 'https:') ? '' : 'none';
  var modal = document.getElementById('share-modal');
  var backdrop = document.getElementById('share-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('share-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeShareModal() {
  var modal = document.getElementById('share-modal');
  var backdrop = document.getElementById('share-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  restoreFocus(shareTriggerEl);
  shareTriggerEl = null;
  shareCurrentCfg = null;
  shareCurrentFormat = 'square';
}
/* ============================== report a problem ==============================
   A lightweight flag button (in the shared modeToolbarHtml(), next to Restart/
   Exit) that writes straight to a Firestore review queue — see submitReport()
   in firebase-sync.js and the hidden #reports route (renderReportsScreen())
   for how it's reviewed. Auto-captures the exact question being shown where
   the mode has one (quiz-style modes only — CURRENT_QUESTION_GETTERS), so a
   report doesn't depend on the player typing out which question they meant. */
var CURRENT_QUESTION_GETTERS = {
  quiz: currentQuizQuestion, cfbQuiz: currentCfbQuestion, daily: currentDailyQuestion,
  speed: currentSpeedQuestion, cfbSpeed: currentCfbSpeedQuestion,
  iq: currentIQQuestion, cfbIq: currentCfbIQQuestion, study: currentStudyQuestion, xso: currentXsoQuestion
};
function currentQuestionContext(mode) {
  var getter = CURRENT_QUESTION_GETTERS[mode];
  if (!getter) return null;
  try {
    var q = getter();
    return q ? { id: q.id, text: q.question } : null;
  } catch (e) { return null; }
}
var reportTriggerEl = null;
var reportCurrentMode = null;
var reportCategory = 'Wrong answer';
function openReportModal(mode) {
  reportCurrentMode = mode;
  reportCategory = 'Wrong answer';
  reportTriggerEl = document.activeElement;
  var ctx = currentQuestionContext(mode);
  var contextEl = document.getElementById('report-context');
  if (contextEl) {
    contextEl.textContent = ctx ? ('Reporting: ' + modeLabelFor(mode) + ' — “' + ctx.text + '”') : ('Reporting a problem in ' + modeLabelFor(mode) + '.');
  }
  document.querySelectorAll('#report-category-row .chip-toggle').forEach(function (btn, i) {
    btn.classList.toggle('active', i === 0);
  });
  var noteEl = document.getElementById('report-note');
  if (noteEl) noteEl.value = '';
  var confirmEl = document.getElementById('report-confirm');
  if (confirmEl) confirmEl.style.display = 'none';
  var submitBtn = document.getElementById('report-submit');
  if (submitBtn) { submitBtn.style.display = ''; submitBtn.disabled = false; submitBtn.textContent = 'Send Report'; }
  var modal = document.getElementById('report-modal');
  var backdrop = document.getElementById('report-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('report-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeReportModal() {
  var modal = document.getElementById('report-modal');
  var backdrop = document.getElementById('report-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  restoreFocus(reportTriggerEl);
  reportTriggerEl = null;
  reportCurrentMode = null;
}
function setReportCategory(cat) {
  reportCategory = cat;
  document.querySelectorAll('#report-category-row .chip-toggle').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.reportCategory === cat);
  });
}
function submitReport() {
  if (!reportCurrentMode) return;
  var noteEl = document.getElementById('report-note');
  var note = noteEl ? noteEl.value.trim() : '';
  var ctx = currentQuestionContext(reportCurrentMode);
  var payload = {
    mode: reportCurrentMode,
    modeLabel: modeLabelFor(reportCurrentMode),
    category: reportCategory,
    note: note,
    questionId: ctx ? ctx.id : null,
    questionText: ctx ? ctx.text : null,
    reporterName: state.name || null
  };
  var submitBtn = document.getElementById('report-submit');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }
  if (window.__fbSync && window.__fbSync.submitReport) window.__fbSync.submitReport(payload);
  var confirmEl = document.getElementById('report-confirm');
  if (confirmEl) confirmEl.style.display = '';
  if (submitBtn) submitBtn.style.display = 'none';
  setTimeout(closeReportModal, 1400);
}
function renderReportsScreen() {
  var reports = (window.__fbSync && window.__fbSync.reports) || [];
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Reported Questions</h2>' +
    '<p class="mode-desc">' + reports.length + ' report' + (reports.length === 1 ? '' : 's') + '. Hidden page, not linked anywhere in the app.</p>';
  if (!reports.length) {
    html += '<p class="mode-desc">Nothing reported yet.</p>';
  } else {
    html += '<div class="reports-list">' + reports.map(function (r) {
      return '<div class="report-row">' +
        '<div class="report-row-top"><b>' + esc(r.modeLabel || r.mode || 'Unknown mode') + '</b><span class="report-row-cat">' + esc(r.category || '') + '</span></div>' +
        (r.questionText ? '<div class="report-row-question">' + esc(r.questionText) + '</div>' : '') +
        (r.note ? '<div class="report-row-note">' + esc(r.note) + '</div>' : '') +
        '<div class="report-row-meta">' + esc(r.reporterName || 'Anonymous') + '</div>' +
        '</div>';
    }).join('') + '</div>';
  }
  html += '</div>';
  return html;
}
function shareDownloadImage() {
  var img = document.getElementById('share-preview');
  if (!img || !img.src) return;
  var a = document.createElement('a');
  a.href = img.src;
  a.download = shareCurrentFormat === 'story' ? 'reads-result-story.png' : 'reads-result.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
function shareToX() {
  if (!shareCurrentCfg) return;
  var url = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(shareCurrentCfg.shareText);
  window.open(url, '_blank', 'noopener');
}
function shareToFacebook() {
  var url = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(location.href);
  window.open(url, '_blank', 'noopener');
}
function shareCopyConfirm(btn) {
  if (!btn) return;
  var original = btn.innerHTML;
  btn.innerHTML = icon('check') + ' Copied!';
  setTimeout(function () { btn.innerHTML = original; }, 1600);
}
function shareCopyText() {
  if (!shareCurrentCfg) return;
  var btn = document.getElementById('share-copy');
  var text = shareCurrentCfg.shareText;
  // navigator.clipboard requires a secure context (http(s)/localhost) — not
  // available over file://, so this falls back to the older
  // execCommand('copy')-via-hidden-textarea trick, which works everywhere.
  if (navigator.clipboard && navigator.clipboard.writeText && (location.protocol === 'https:' || location.protocol === 'http:')) {
    navigator.clipboard.writeText(text).then(function () { shareCopyConfirm(btn); }).catch(function () { shareCopyTextFallback(text, btn); });
  } else {
    shareCopyTextFallback(text, btn);
  }
}
// Same copy-to-clipboard approach as shareCopyText(), just for an arbitrary
// string (the contact email on the Privacy Policy page) instead of the
// current share card's text — same secure-context check, same
// execCommand('copy') fallback for http/file:// contexts.
function copyTextToClipboard(text, btn) {
  if (navigator.clipboard && navigator.clipboard.writeText && (location.protocol === 'https:' || location.protocol === 'http:')) {
    navigator.clipboard.writeText(text).then(function () { shareCopyConfirm(btn); }).catch(function () { shareCopyTextFallback(text, btn); });
  } else {
    shareCopyTextFallback(text, btn);
  }
}
function shareCopyTextFallback(text, btn) {
  try {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    shareCopyConfirm(btn);
  } catch (e) {}
}

/* ============================== progression foundation ============================== */
// Permanent career XP + football-season XP. Values live in Firestore for
// signed-in accounts and are cached locally only for fast rendering/offline
// continuity. Reward values are intentionally centralized so tuning never
// requires hunting through individual game modes.
var PROGRESSION_XP = {
  GAME_COMPLETED: 25,
  DAILY_COMPLETED: 50,
  H2H_COMPLETED: 40,
  FILM_SESSION: 30,
  FILM_BOSS: 50
};
var progressSessionIds = {};
var awardedProgressSessions = {};
function beginProgressSession(mode) {
  if (!mode) return;
  progressSessionIds[mode] = mode + '_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 9);
  awardedProgressSessions[mode] = null;
}
function progressEventIdFor(mode) {
  if (!progressSessionIds[mode]) beginProgressSession(mode);
  return progressSessionIds[mode];
}
function footballSeasonIdForDate(date) {
  date = date || new Date();
  // A football season remains the previous calendar year's season through
  // the winter/spring offseason; July starts the new season identity.
  return date.getMonth() >= 6 ? String(date.getFullYear()) : String(date.getFullYear() - 1);
}
function progressionLocalKey() {
  var who = activeAuthUid ? ('uid_' + activeAuthUid) : slugify(state.name || 'guest');
  return 'nflTriviaProgression__' + who;
}
function emptySeasonProgress() {
  return {
    xp:0,gamesPlayed:0,dailyCompletions:0,bestStreak:0,finalRating:null,topMode:null,topModePlays:0,
    modePlays:{},questionsAnswered:0,h2hWins:0,h2hLosses:0,h2hTies:0,endlessBestScore:0,endlessBestQuestions:0,
    completedAt:null
  };
}
function emptyProgression() { return { careerXp: 0, seasons: {} }; }
function normalizeSeasonProgress(v) {
  v = v || {};
  var out = Object.assign(emptySeasonProgress(), v);
  out.xp = Number(out.xp) || 0;
  out.gamesPlayed = Number(out.gamesPlayed) || 0;
  out.dailyCompletions = Number(out.dailyCompletions) || 0;
  out.bestStreak = Number(out.bestStreak) || 0;
  out.topModePlays = Number(out.topModePlays) || 0;
  out.modePlays = out.modePlays && typeof out.modePlays === 'object' ? out.modePlays : {};
  out.questionsAnswered = Number(out.questionsAnswered) || 0;
  out.h2hWins = Number(out.h2hWins) || 0;
  out.h2hLosses = Number(out.h2hLosses) || 0;
  out.h2hTies = Number(out.h2hTies) || 0;
  out.endlessBestScore = Number(out.endlessBestScore) || 0;
  out.endlessBestQuestions = Number(out.endlessBestQuestions) || 0;
  return out;
}
function getProgression() { return lsGet(progressionLocalKey(), emptyProgression()); }
function setProgression(v) { lsSet(progressionLocalKey(), v || emptyProgression()); }
function mergeProgression(local, cloud) {
  local = local || emptyProgression();
  cloud = cloud || emptyProgression();
  var out = { careerXp: Math.max(Number(local.careerXp) || 0, Number(cloud.careerXp) || 0), seasons: {} };
  var keys = {};
  Object.keys(local.seasons || {}).forEach(function (k) { keys[k] = true; });
  Object.keys(cloud.seasons || {}).forEach(function (k) { keys[k] = true; });
  Object.keys(keys).forEach(function (k) {
    var l = normalizeSeasonProgress(local.seasons && local.seasons[k]);
    var c = normalizeSeasonProgress(cloud.seasons && cloud.seasons[k]);
    var modeKeys={}, mergedModes={};
    Object.keys(l.modePlays||{}).forEach(function(m){modeKeys[m]=true;});
    Object.keys(c.modePlays||{}).forEach(function(m){modeKeys[m]=true;});
    Object.keys(modeKeys).forEach(function(m){mergedModes[m]=Math.max(Number(l.modePlays[m])||0,Number(c.modePlays[m])||0);});
    var topMode=null, topModePlays=0;
    Object.keys(mergedModes).forEach(function(m){if(mergedModes[m]>topModePlays){topMode=m;topModePlays=mergedModes[m];}});
    out.seasons[k] = {
      xp: Math.max(l.xp, c.xp),
      gamesPlayed: Math.max(l.gamesPlayed, c.gamesPlayed),
      dailyCompletions: Math.max(l.dailyCompletions, c.dailyCompletions),
      bestStreak: Math.max(l.bestStreak, c.bestStreak),
      finalRating: c.finalRating != null ? c.finalRating : l.finalRating,
      topMode: topMode || c.topMode || l.topMode || null,
      topModePlays: Math.max(topModePlays,l.topModePlays,c.topModePlays),
      modePlays: mergedModes,
      questionsAnswered: Math.max(l.questionsAnswered,c.questionsAnswered),
      h2hWins: Math.max(l.h2hWins,c.h2hWins),
      h2hLosses: Math.max(l.h2hLosses,c.h2hLosses),
      h2hTies: Math.max(l.h2hTies,c.h2hTies),
      endlessBestScore: Math.max(l.endlessBestScore,c.endlessBestScore),
      endlessBestQuestions: Math.max(l.endlessBestQuestions,c.endlessBestQuestions),
      completedAt: Math.max(Number(l.completedAt) || 0, Number(c.completedAt) || 0) || null
    };
  });
  return out;
}
function applyProgressAwardLocally(xp, seasonId) {
  var p = getProgression();
  p.careerXp = (Number(p.careerXp) || 0) + xp;
  p.seasons = p.seasons || {};
  p.seasons[seasonId] = normalizeSeasonProgress(p.seasons[seasonId]);
  p.seasons[seasonId].xp += xp;
  setProgression(p);
}
var recordedSeasonSessions = {};

function seasonQuestionCountForCompletion(mode, fields) {
  var s=state[mode];
  if(mode==='daily'&&state.daily&&state.daily.queue)return state.daily.queue.length||0;
  if(mode==='h2h'&&state.h2h){
    if(state.h2h.queue&&state.h2h.queue.length)return state.h2h.queue.length;
    var me=state.h2h.match&&state.h2h.match.players&&state.h2h.match.players[state.h2h.mySlug];
    return me&&Number(me.total)||0;
  }
  if(mode==='endless')return fields&&Number(fields.lastQuestions)||0;
  if(mode==='learn'&&state.filmStudy)return state.filmStudy.questions.length||0;
  if(s&&s.queue&&Array.isArray(s.queue))return s.queue.length||0;
  if(s&&typeof s.totalCount==='number')return s.totalCount||0;
  return 0;
}
function seasonH2hResult() {
  var s=state.h2h, match=s&&s.match;
  if(!s||!match||!match.players)return null;
  var slugs=Object.keys(match.players), mine=match.players[s.mySlug];
  var oppSlug=slugs.filter(function(sl){return sl!==s.mySlug;})[0], opp=oppSlug?match.players[oppSlug]:null;
  if(!mine||!opp||!mine.finishedAt||!opp.finishedAt)return null;
  var diff=h2hCompareRecords(mine,opp);
  return diff>0?'win':diff<0?'loss':'tie';
}

function recordSeasonGame(mode, fields) {
  if (!state.name || !mode) return;
  var eventId = mode === 'daily' ? ('daily_' + todayStr()) : progressEventIdFor(mode);
  if (recordedSeasonSessions[mode] === eventId) return;
  recordedSeasonSessions[mode] = eventId;
  var seasonId = footballSeasonIdForDate();
  var p = getProgression();
  p.seasons = p.seasons || {};
  var season = normalizeSeasonProgress(p.seasons[seasonId]);
  season.gamesPlayed += 1;
  if (mode === 'daily') season.dailyCompletions += 1;
  season.bestStreak = Math.max(season.bestStreak, getStreak().count || 0);
  season.questionsAnswered += seasonQuestionCountForCompletion(mode, fields);
  season.modePlays = season.modePlays || {};
  season.modePlays[mode] = (Number(season.modePlays[mode]) || 0) + 1;
  if (season.modePlays[mode] >= season.topModePlays) {
    season.topMode = mode;
    season.topModePlays = season.modePlays[mode];
  }
  if(mode==='h2h'){
    var hResult=seasonH2hResult();
    if(hResult==='win')season.h2hWins+=1;
    else if(hResult==='loss')season.h2hLosses+=1;
    else if(hResult==='tie')season.h2hTies+=1;
  }
  if(mode==='endless'&&fields){
    season.endlessBestScore=Math.max(season.endlessBestScore,Number(fields.lastScore)||0);
    season.endlessBestQuestions=Math.max(season.endlessBestQuestions,Number(fields.lastQuestions)||0);
  }
  var rating = getRating();
  season.finalRating = rating ? rating.score : season.finalRating;
  p.seasons[seasonId] = season;
  setProgression(p);
}
function closePreviousSeasonsIfNeeded() {
  var p = getProgression();
  var current = footballSeasonIdForDate();
  var changed = false;
  Object.keys(p.seasons || {}).forEach(function (id) {
    if (id === current) return;
    var season = normalizeSeasonProgress(p.seasons[id]);
    if (!season.completedAt && season.xp > 0) {
      season.completedAt = Date.now();
      p.seasons[id] = season;
      changed = true;
    }
  });
  if (changed) setProgression(p);
}
var SEASON_RANKS = [
  { name: 'Rookie', min: 0 },
  { name: 'Prospect', min: 300 },
  { name: 'Starter', min: 900 },
  { name: 'Playmaker', min: 1800 },
  { name: 'All-Pro', min: 3500 },
  { name: 'MVP', min: 6000 }
];
function seasonRankFor(xp) {
  xp = Math.max(0, Number(xp) || 0);
  var current = SEASON_RANKS[0], next = null;
  for (var i = 0; i < SEASON_RANKS.length; i++) {
    if (xp >= SEASON_RANKS[i].min) current = SEASON_RANKS[i];
    else { next = SEASON_RANKS[i]; break; }
  }
  var pct = 1;
  if (next) pct = Math.max(0, Math.min(1, (xp - current.min) / (next.min - current.min)));
  return { name: current.name, next: next && next.name, xp: xp, pct: pct, toNext: next ? next.min - xp : 0 };
}
function seasonMilestonesFor(data) {
  data = normalizeSeasonProgress(data);
  return [
    { label:'Season Opener', current:data.gamesPlayed, target:10 },
    { label:'Daily Regular', current:data.dailyCompletions, target:10 },
    { label:'Hot Streak', current:data.bestStreak, target:7 },
    { label:'1K Club', current:data.xp, target:1000 }
  ].map(function (m) {
    return Object.assign({}, m, { complete:m.current >= m.target, pct:Math.max(0, Math.min(100, Math.round((m.current / m.target) * 100))) });
  });
}
function seasonHistoryList() {
  closePreviousSeasonsIfNeeded();
  var p = getProgression();
  return Object.keys(p.seasons || {}).sort(function (a,b) { return Number(b) - Number(a); }).map(function (id) {
    return { id:id, data:normalizeSeasonProgress(p.seasons[id]) };
  });
}
function seasonLeaderboardRows() {
  var seasonId = footballSeasonIdForDate();
  var rows = (state.leaderboardData || []).filter(function (r) {
    return r.mode === 'season' && String(r.seasonId || '') === seasonId && typeof r.seasonXp === 'number';
  });
  rows.sort(function (a,b) {
    if ((b.seasonXp || 0) !== (a.seasonXp || 0)) return (b.seasonXp || 0) - (a.seasonXp || 0);
    return leaderboardRowTimestamp(b) - leaderboardRowTimestamp(a);
  });
  return rows;
}
function pushSeasonLeaderboardSnapshot() {
  if (!state.name || !window.__fbSync || !window.__fbSync.pushScore) return;
  var seasonId = footballSeasonIdForDate();
  var p = getProgression();
  var season = normalizeSeasonProgress(p.seasons && p.seasons[seasonId]);
  var fav = getFavoriteTeams();
  var docId = activeAuthUid ? ('account_' + activeAuthUid + '__season_' + seasonId)
    : (slugify(state.name) + '_' + getClientId() + '__season_' + seasonId);
  window.__fbSync.pushScore(docId, {
    name: state.name,
    mode: 'season',
    seasonId: seasonId,
    seasonXp: season.xp,
    gamesPlayed: season.gamesPlayed,
    dailyCompletions: season.dailyCompletions,
    bestStreak: season.bestStreak,
    finalRating: season.finalRating,
    questionsAnswered: season.questionsAnswered,
    h2hWins: season.h2hWins,
    h2hLosses: season.h2hLosses,
    h2hTies: season.h2hTies,
    endlessBestScore: season.endlessBestScore,
    endlessBestQuestions: season.endlessBestQuestions,
    accountUid: activeAuthUid || null,
    playerKey: canonicalPlayerKey(),
    favoriteNflTeam: fav.nfl || null,
    favoriteCfbTeam: fav.cfb || null
  });
}
function seasonLeaderboardHtml() {
  var rows = seasonLeaderboardRows().slice(0,10);
  var seasonId = footballSeasonIdForDate();
  return '<section class="season-leaderboard-card"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">' + esc(seasonId) + ' SEASON</span><h3>Season Leaderboard</h3></div><span>Season XP</span></div>' +
    (rows.length ? '<div class="community-rank-list">' + rows.map(function (r,i) {
      return '<div class="community-rank-row"><span class="community-rank-pos">' + (i+1) + '</span><b>' + esc(r.name || 'Reads fan') + '</b><span>' + (r.seasonXp || 0) + ' XP</span></div>';
    }).join('') + '</div>' : '<div class="community-empty"><b>No season standings yet.</b><span>Finish a ranked game to enter the ' + esc(seasonId) + ' race.</span></div>') +
    '</section>';
}
function seasonHistoryHtml() {
  var list = seasonHistoryList();
  if (!list.length) return '';
  var current = footballSeasonIdForDate();
  return '<section class="profile-season-history"><div class="profile-section-head"><div><span class="dashboard-eyebrow">CAREER HISTORY</span><h3>Seasons</h3></div><span>' + list.length + ' season' + (list.length === 1 ? '' : 's') + '</span></div>' +
    '<div class="season-history-grid">' +
    list.map(function (item) {
      var d = item.data, rank = seasonRankFor(d.xp);
      var trophy=seasonTrophyFor(item);
      return '<article class="season-history-card' + (item.id === current ? ' current' : '') + '">' +
        '<div class="season-history-head"><b>' + esc(item.id) + '</b><span>' + (item.id === current ? 'Current' : 'Final') + '</span></div>' +
        '<div class="season-history-rank"><span class="season-history-trophy">'+trophy.icon+'</span>' + esc(rank.name) + '</div>' +
        '<div class="season-history-xp">' + d.xp.toLocaleString() + ' XP</div>' +
        '<div class="season-history-stats"><span>' + d.gamesPlayed + ' games</span><span>' + d.questionsAnswered.toLocaleString() + ' questions</span><span>' + d.dailyCompletions + ' Daily Reads</span><span>' + d.bestStreak + '-day best streak</span>' +
        '<span>H2H: '+d.h2hWins+'-'+d.h2hLosses+(d.h2hTies?'-'+d.h2hTies:'')+'</span>'+
        (d.endlessBestScore ? '<span>Endless best: '+d.endlessBestScore.toLocaleString()+'</span>' : '') +
        (d.finalRating != null ? '<span>' + d.finalRating + ' final rating</span>' : '') +
        (d.topMode ? '<span>Most played: ' + esc(modeLabelFor(d.topMode)) + ' ×' + d.topModePlays + '</span>' : '') +
        '</div></article>';
    }).join('') + '</div></section>';
}
function currentSeasonRecapHtml() {
  var p = getProgression();
  var id = footballSeasonIdForDate();
  var d = normalizeSeasonProgress(p.seasons && p.seasons[id]);
  var rank = seasonRankFor(d.xp);
  var milestones = seasonMilestonesFor(d);
  var trophy=seasonTrophyFor({id:id,data:d});
  var favLeague=defaultCommunityLeague(), favTeam=communityTeamForLeague(favLeague);
  var contribution=favTeam?communityContributionPct(favLeague,favTeam):null;
  return '<section class="season-recap-card">' +
    '<div class="season-recap-title"><span class="season-recap-trophy">'+trophy.icon+'</span><div><span class="dashboard-eyebrow">' + esc(id) + ' READS SEASON</span><h3>' + esc(rank.name) + '</h3><p>' + d.xp.toLocaleString() + ' season XP · ' + d.gamesPlayed + ' games · ' + d.questionsAnswered.toLocaleString() + ' questions</p></div></div>' +
    '<div class="season-rank-progress"><div><b>' + esc(rank.name) + '</b><span>' + (rank.next ? rank.toNext + ' XP to ' + esc(rank.next) : 'Top seasonal tier') + '</span></div>' +
    '<span class="dashboard-xp-track"><span style="width:' + Math.round(rank.pct * 100) + '%"></span></span></div>' +
    '<div class="season-recap-metrics season-recap-metrics-v2">' +
      '<span><b>' + d.bestStreak + '</b><small>Best streak</small></span>' +
      '<span><b>' + (d.finalRating == null ? '—' : d.finalRating) + '</b><small>Rating</small></span>' +
      '<span><b>' + d.h2hWins + '-' + d.h2hLosses + (d.h2hTies?'-'+d.h2hTies:'') + '</b><small>H2H record</small></span>' +
      '<span><b>' + (d.endlessBestScore ? d.endlessBestScore.toLocaleString() : '—') + '</b><small>Endless best</small></span>' +
      '<span><b>' + (d.topMode ? esc(modeLabelFor(d.topMode)) : '—') + '</b><small>Most played</small></span>' +
      '<span><b>' + d.dailyCompletions + '</b><small>Daily Reads</small></span>' +
    '</div>' +
    (contribution&&contribution.pct?'<div class="season-team-contribution"><span>'+favoriteTeamBadgeHtml()+' '+esc(favTeam.name)+'</span><b>Top '+Math.max(1,100-contribution.pct+1)+'% team contributor</b></div>':'')+
    '<div class="season-milestones">' + milestones.map(function (m) {
      return '<div class="' + (m.complete ? 'complete' : '') + '"><span>' + (m.complete ? icon('check') : icon('trophy')) + '</span><b>' + esc(m.label) + '</b><small>' + Math.min(m.current,m.target) + ' / ' + m.target + '</small></div>';
    }).join('') + '</div></section>';
}

function progressionEventForCompletion(mode, fields) {
  var eventType = mode === 'daily' ? 'DAILY_READS_COMPLETED' : (mode === 'h2h' ? 'CHALLENGE_COMPLETED' : (mode === 'learn' ? 'FILM_SESSION_COMPLETED' : 'GAME_COMPLETED'));
  return {
    type: eventType,
    mode: mode,
    league: mode === 'endless' ? 'MIXED' : (mode && mode.indexOf('cfb') === 0 ? 'CFB' : 'NFL'),
    source: 'leaderboard_completion',
    fields: fields || {}
  };
}
function awardProgressForCompletion(mode, fields) {
  if (!state.name || !mode) return;
  var eventId = mode === 'daily' ? ('daily_' + todayStr()) : progressEventIdFor(mode);
  if (awardedProgressSessions[mode] === eventId) return;
  awardedProgressSessions[mode] = eventId;
  var seasonId = footballSeasonIdForDate();
  var xp = mode === 'daily' ? PROGRESSION_XP.DAILY_COMPLETED :
    (mode === 'h2h' ? PROGRESSION_XP.H2H_COMPLETED : (mode === 'learn' ? ((fields&&fields.boss)?PROGRESSION_XP.FILM_BOSS:PROGRESSION_XP.FILM_SESSION) : PROGRESSION_XP.GAME_COMPLETED));
  var eventData = progressionEventForCompletion(mode, fields);
  progressionAwardPreview(mode, xp, seasonId);
  if (activeAuthUid && window.__fbSync && window.__fbSync.awardProgress) {
    window.__fbSync.awardProgress(profileDocId(), eventId, eventData, xp, seasonId).then(function (result) {
      if (!result || !result.duplicate) {
        applyProgressAwardLocally(xp, seasonId);
        syncAchievementUnlocks();
      }
      // Always republish the season snapshot after a confirmed transaction.
      // If the XP event was already recorded but a prior leaderboard write
      // failed, this repairs the standings without paying the event twice.
      pushSeasonLeaderboardSnapshot();
      if (state.screen === 'daily' || state.screen === 'home' || state.screen === 'profile') renderAll();
    }).catch(function () {
      // Gameplay must never fail because progression sync is unavailable.
      awardedProgressSessions[mode] = null;
    });
  } else {
    applyProgressAwardLocally(xp, seasonId);
    pushSeasonLeaderboardSnapshot();
    syncAchievementUnlocks();
  }
}

/* ============================== leaderboard ============================== */
// Two different people typing the same display name (very likely with common
// first names in a friend group) would otherwise write to the exact same
// Firestore doc (slugify("Mike")) and silently overwrite each other's scores.
// A random ID generated once per browser and persisted locally keeps each
// device's leaderboard entry distinct even when names collide, without
// requiring unique names or accounts.
function getClientId() {
  var id = lsGet('nflTriviaClientId', null);
  if (!id) {
    id = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
    lsSet('nflTriviaClientId', id);
  }
  return id;
}
function pushLeaderboard(mode, fields) {
  if (!state.name) return;
  var docId = activeAuthUid ? ('account_' + activeAuthUid + '__' + mode)
    : (slugify(state.name) + '_' + getClientId() + '__' + mode);
  var favTeamsForScore = getFavoriteTeams();
  var payload = Object.assign({
    name: state.name,
    mode: mode,
    playerKey: canonicalPlayerKey(),
    accountUid: activeAuthUid || null,
    favoriteNflTeam: favTeamsForScore.nfl || null,
    favoriteCfbTeam: favTeamsForScore.cfb || null
  }, fields);
  if (window.__fbSync && window.__fbSync.pushScore) window.__fbSync.pushScore(docId, payload);
  recordPersonalizationCompletion(mode, fields);
  recordSeasonGame(mode, fields);
  pushProfileSnapshot();
  awardProgressForCompletion(mode, fields);
  checkCommunityChallengeFromCompletion(mode);
  postCommunityGameActivity(mode, fields);
  syncAchievementUnlocks();
  syncPushEngagementSnapshot(true);
}
function leaderboardRowTimestamp(row) {
  if (!row || !row.updatedAt) return 0;
  if (typeof row.updatedAt.toMillis === 'function') return row.updatedAt.toMillis();
  if (typeof row.updatedAt.seconds === 'number') return row.updatedAt.seconds * 1000;
  return Number(row.updatedAt) || 0;
}
function normalizeLeaderboardRows(list) {
  list = Array.isArray(list) ? list : [];
  var accountNameModes = {};
  list.forEach(function (row) {
    if (row && (row.accountUid || (row.playerKey && row.playerKey.indexOf('uid:') === 0))) {
      accountNameModes[(row.mode || '') + '|' + slugify(row.name || '')] = true;
    }
  });
  var chosen = {};
  list.forEach(function (row) {
    if (!row || !row.mode) return;
    var isAccount = !!(row.accountUid || (row.playerKey && row.playerKey.indexOf('uid:') === 0));
    var nameMode = row.mode + '|' + slugify(row.name || '');
    if (!isAccount && accountNameModes[nameMode]) return;
    var identity = isAccount
      ? (row.accountUid ? 'uid:' + row.accountUid : row.playerKey)
      : ('legacy:' + (row.id || 'unknown'));
    var key = row.mode + '|' + identity;
    var previous = chosen[key];
    if (!previous || leaderboardRowTimestamp(row) >= leaderboardRowTimestamp(previous)) chosen[key] = row;
  });
  return Object.keys(chosen).map(function (key) { return chosen[key]; });
}
// True once this device has done its one-time cross-device stats/streak
// pull for the current name — applyLeaderboard fires on every leaderboard
// change (could be fairly often with several people playing), but the pull
// itself only needs to happen once Firebase first actually connects, not
// on every subsequent update. logOut() resets this so logging into a
// different account mid-session still gets its own pull.
var didInitialProfilePull = false;
window.__triviaSync = {
  applyLeaderboard: function (list) {
    state.leaderboardData = normalizeLeaderboardRows(list);
    reconcileRating(state.leaderboardData);
    syncPushEngagementSnapshot(false);
    if (!didInitialProfilePull && state.name) { didInitialProfilePull = true; pullProfileSnapshot(); }
    if (state.screen === 'leaderboard' || state.screen === 'community' || state.screen === 'home' || state.screen === 'daily' || state.screen === 'friends') renderAll();
  },
  // Fires from firebase-sync.js's onAuthStateChanged every time the signed-
  // in Firebase user changes — including a plain anonymous session, which
  // is why authUser is null in that case (not "logged out", just "never
  // logged in for real"). Only acts on the "restore a persisted real login
  // this device already had" case (guarded by !state.name, since an
  // explicit Log In/Sign Up already calls saveName() itself the instant it
  // resolves — this only needs to catch the cold-boot case where Firebase
  // silently restores a previous session before any UI interaction at all)
  // and the "a previously-real session unexpectedly dropped back to
  // anonymous" case (token expired/revoked elsewhere) — anything else is a
  // no-op.
  applyAuthUser: function (authUser) {
    if (authUser && authUser.username) {
      var uidChanged = activeAuthUid !== authUser.uid;
      activeAuthUid = authUser.uid || null;
      if (uidChanged) didInitialProfilePull = false;
      lsSet('nflTriviaLoggedIn', true);
      if (!state.name) saveName(authUser.username);
      else if (!didInitialProfilePull) { didInitialProfilePull = true; pullProfileSnapshot(); }
    } else if (!authUser && lsGet('nflTriviaLoggedIn', false)) {
      activeAuthUid = null;
      lsSet('nflTriviaLoggedIn', false);
      if (state.name) { state.name = ''; lsSet('nflTriviaName', ''); renderAll(); }
    }
  },
  // Fires on every live update to the analytics play-count doc (see
  // renderStatsScreen) — without this, the hidden #stats page only ever
  // showed whatever counts were current the moment you loaded it, since
  // nothing told it to redraw when fresher numbers arrived in the
  // background. Same "only re-render if you're actually looking at the
  // screen this data feeds" guard as applyLeaderboard above.
  applyPlayCounts: function () {
    if (state.screen === 'stats') renderAll();
  }
};

var LEADERBOARD_MODES = [
  { id: 'rating', label: 'Football Rating', sortKey: 'score', cols: [['score', 'Rating'], ['games', 'Games Played']] },
  { id: 'season', label: footballSeasonIdForDate() + ' Season', sortKey: 'seasonXp', cols: [['seasonXp', 'Season XP'], ['gamesPlayed', 'Games'], ['bestStreak', 'Best Streak']] },
  { id: 'daily', label: 'Daily Reads', sortKey: 'completions', cols: [['completions', 'Days Completed'], ['bestPct', 'Best %']] },
  { id: 'endless', label: 'Endless Reads', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestQuestions', 'Best Questions'], ['bestStreak', 'Best Streak'], ['runs', 'Runs']] },
  { id: 'quiz', label: 'NFL Quiz', sortKey: 'bestPct', cols: [['bestPct', 'Best %'], ['correctTotal', 'Total Correct'], ['roundsPlayed', 'Rounds']] },
  { id: 'xso', label: "X's & O's", sortKey: 'bestPct', cols: [['bestPct', 'Best %'], ['correctTotal', 'Total Correct'], ['roundsPlayed', 'Rounds']] },
  { id: 'grid', label: 'NFL Grid', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['cleanSweeps', 'Clean Sweeps'], ['gamesPlayed', 'Games']] },
  { id: 'blitz', label: 'NFL Blitz', sortKey: 'bestMatched', cols: [['bestMatched', 'Best Matched'], ['attempts', 'Attempts']] },
  { id: 'speed', label: 'NFL Speed', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestStreak', 'Best Streak'], ['sessionsPlayed', 'Sessions']] },
  { id: 'silhouette', label: 'NFL Silhouette', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestQuick', 'Best Quick Guesses'], ['roundsPlayed', 'Rounds']] },
  { id: 'iq', label: 'NFL IQ Test', sortKey: 'bestIQ', cols: [['bestIQ', 'Best IQ'], ['testsTaken', 'Tests Taken']] },
  { id: 'higherLower', label: 'Higher or Lower', sortKey: 'bestStreak', cols: [['bestStreak', 'Best Streak'], ['gamesPlayed', 'Runs']] },
  { id: 'legends', label: '17-0', sortKey: 'bestWins', cols: [['bestRecord', 'Best Record'], ['bestGrade', 'Best Grade'], ['gamesPlayed', 'Drafts']] },
  { id: 'cfbQuiz', label: 'CFB Quiz', sortKey: 'bestPct', cols: [['bestPct', 'Best %'], ['correctTotal', 'Total Correct'], ['roundsPlayed', 'Rounds']] },
  { id: 'cfbIq', label: 'CFB IQ', sortKey: 'bestIQ', cols: [['bestIQ', 'Best IQ'], ['testsTaken', 'Tests Taken']] },
  { id: 'cfbSpeed', label: 'CFB Speed Round', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestStreak', 'Best Streak'], ['sessionsPlayed', 'Sessions']] },
  { id: 'cfbBlitz', label: 'CFB Blitz', sortKey: 'bestMatched', cols: [['bestMatched', 'Best Matched'], ['attempts', 'Attempts']] },
  { id: 'cfbGrid', label: 'CFB Immaculate Grid', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['cleanSweeps', 'Clean Sweeps'], ['gamesPlayed', 'Games']] },
  { id: 'cfbLegends', label: 'CFB 12-0', sortKey: 'bestWins', cols: [['bestRecord', 'Best Record'], ['bestGrade', 'Best Grade'], ['gamesPlayed', 'Drafts']] },
  { id: 'h2h', label: 'Head-to-Head', sortKey: 'wins', cols: [['wins', 'Wins'], ['losses', 'Losses'], ['ties', 'Ties']] },
  // User request: "keep a record of your pick em's throughout the season
  // so u can compete with other users" -- pushed by loadPickemSeasonRecord()
  // in pickem-ui.js every time a real season record is fetched.
  { id: 'pickemNfl', label: "NFL Pick'em", sortKey: 'winPct', cols: [['winPct', 'Win %'], ['correctCount', 'Correct'], ['gradedCount', 'Graded'], ['weeksPlayed', 'Weeks Played']] },
  { id: 'pickemCfb', label: "CFB Pick'em", sortKey: 'winPct', cols: [['winPct', 'Win %'], ['correctCount', 'Correct'], ['gradedCount', 'Graded'], ['weeksPlayed', 'Weeks Played']] }
];
// "Today"/"This Week" reads each row's updatedAt (a Firestore serverTimestamp
// set on every pushScore() — see firebase-sync.js) rather than any separate
// per-period snapshot: since pushScore always writes the player's CURRENT
// best for that mode (merged into one persistent doc per name+device+mode,
// not a new doc per round), this really means "players who've touched this
// mode within the window, showing their current best" — an honest, useful
// "who's active lately" view, not a true period-reset leaderboard (that would
// need storing per-round history, real added backend complexity for a nice-
// to-have). Labeled clearly in the UI so it doesn't overclaim what it is.
var LEADERBOARD_RANGES = [
  { id: 'all', label: 'All-Time' },
  { id: 'week', label: 'This Week' },
  { id: 'today', label: 'Today' }
];
function leaderboardTimestampMs(row) {
  var ts = row.updatedAt;
  if (!ts) return null;
  if (typeof ts.toMillis === 'function') return ts.toMillis();
  if (typeof ts.seconds === 'number') return ts.seconds * 1000;
  return null;
}
function leaderboardRowInRange(row, range) {
  if (range === 'all') return true;
  var ms = leaderboardTimestampMs(row);
  if (ms == null) return false; // no timestamp yet (e.g. optimistic local echo before the server round-trip resolves serverTimestamp()) — excluded rather than guessed
  var windowMs = range === 'today' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
  return (Date.now() - ms) < windowMs;
}
// Relative-time formatting for the "top of the week" callout and the
// activity feed below — both just need a rough "how long ago", not a full
// date/time display.
function formatRelativeTime(ms) {
  var s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  if (s < 60) return 'just now';
  var m = Math.round(s / 60);
  if (m < 60) return m + 'm ago';
  var h = Math.round(m / 60);
  if (h < 24) return h + 'h ago';
  var d = Math.round(h / 24);
  return d + 'd ago';
}
// A special callout above the table specifically for the This Week view —
// same underlying data as the table's own #1 row, just given the visual
// weight an actual "this week's leader" deserves instead of blending into
// the rest of the list.
function leaderboardTopOfWeekHtml(mode, rows) {
  if (state.leaderboardRange !== 'week' || !rows.length) return '';
  var leader = rows[0];
  return '<div class="leaderboard-top-of-week">' + icon('trophy') +
    ' <b>' + esc(leader.name) + '</b> is on top of the week in ' + esc(mode.label) + ' — ' +
    mode.cols.map(function (c) { return esc(c[1]) + ' ' + esc(leader[c[0]] != null ? leader[c[0]] : 0); }).join(', ') +
    '</div>';
}
// Derived entirely from state.leaderboardData's existing updatedAt field
// (already written by pushScore()/serverTimestamp() for the week/today
// leaderboard filter above) rather than a new Firestore collection — a
// genuine live "the app is alive" feed without adding new backend schema,
// security rules, or write paths. Global across every mode (not scoped to
// whichever leaderboard tab is open), newest first, capped at 8.
function recentActivityHtml() {
  var withTime = state.leaderboardData
    .map(function (r) { return { row: r, ms: leaderboardTimestampMs(r) }; })
    .filter(function (x) { return x.ms != null; })
    .sort(function (a, b) { return b.ms - a.ms; })
    .slice(0, 8);
  if (!withTime.length) return '';
  return '<div class="leaderboard-activity">' +
    '<h3 class="mode-section-title">Recent Activity</h3>' +
    withTime.map(function (x) {
      var m = LEADERBOARD_MODES.find(function (mm) { return mm.id === x.row.mode; });
      var mainCol = m && m.cols[0];
      var valueBit = mainCol && x.row[mainCol[0]] != null ? ' — ' + esc(mainCol[1]) + ' ' + esc(x.row[mainCol[0]]) : '';
      return '<div class="leaderboard-activity-row"><b>' + esc(x.row.name) + '</b> played ' + esc(m ? m.label : x.row.mode) + valueBit + ' <span class="leaderboard-activity-time">' + formatRelativeTime(x.ms) + '</span></div>';
    }).join('') +
    '</div>';
}
// Full Visual + Interactive Redesign pass: a premium personal-stats hero
// (matching the redesigned leaderboard mockup's rating shield + trend +
// stat strip) at the top of the Leaderboard screen -- real data only,
// same discipline the task explicitly called for. Every field here is
// something this app already computes/stores somewhere (getRating(),
// ratingTierFor(), getRatingHistory(), getStreak(), state.stats, the
// same modeTimesPlayed()/LEADERBOARD_MODES the Home screen's "Recommended"
// and Profile page already use) -- nothing new is invented, and there is
// deliberately NO worldwide percentile, no fake player count, and no
// fabricated "vs last 7 days" framing (getRatingHistory() stores the last
// RATING_HISTORY_MAX rounds, not one point per calendar day, so this is
// honestly labeled "recent trend" against however many real rounds are
// actually in that window instead of a specific day count that isn't
// really being measured). Returns '' before a player has a rating at all
// (Practice-only / never named) -- nothing to show yet, not a fabricated
// zero-state.
function leaderboardHeroHtml() {
  var r = getRating();
  if (!r) return '';
  var tier = ratingTierFor(r.score);
  var history = getRatingHistory();
  var trendDelta = history.length >= 2 ? (r.score - history[0]) : null;
  var sparkline = ratingSparklineSvg(history);
  var streak = getStreak();
  var dailyStats = state.stats.daily || {};
  var favEntry = LEADERBOARD_MODES.filter(function (m) { return m.id !== 'rating'; })
    .map(function (m) { return { label: m.label, n: modeTimesPlayed(m.id) }; })
    .reduce(function (best, cur) { return (!best || cur.n > best.n) ? cur : best; }, null);
  var statStrip = [
    { icon: 'flame', value: streak.count, label: 'Day' + (streak.count === 1 ? '' : 's') + ' Streak' },
    { icon: 'barChart', value: r.games || 0, label: 'Total Games' }
  ];
  if (dailyStats.completions > 0) statStrip.push({ icon: 'target', value: (dailyStats.bestPct || 0) + '%', label: 'Best Daily' });
  if (favEntry && favEntry.n > 0) statStrip.push({ icon: 'star', value: favEntry.label, label: 'Favorite Mode', isText: true });
  return '<div class="rating-hero">' +
    '<div class="rating-hero-badge">' +
    '<div class="rating-hero-shield">' + icon('shield') + '<div class="rating-hero-shield-text"><span class="rating-hero-tier">' + esc(tier.name) + '</span><span class="rating-hero-score">' + r.score + '</span></div></div>' +
    '</div>' +
    '<div class="rating-hero-main">' +
    '<div class="rating-hero-headrow"><span class="rating-hero-label">Football Rating</span>' +
    (trendDelta != null ? '<span class="rating-hero-trend ' + (trendDelta >= 0 ? 'up' : 'down') + '">' + icon(trendDelta >= 0 ? 'arrowUp' : 'arrowDown') + ' ' + Math.abs(trendDelta) + '</span>' : '') +
    '</div>' +
    '<div class="rating-hero-score-row"><span class="rating-hero-score-big">' + r.score + '</span>' + sparkline + '</div>' +
    '<span class="rating-xp-track rating-xp-track-lg"><span class="rating-xp-fill" style="width:' + Math.round(tier.pct * 100) + '%"></span></span>' +
    '<div class="rating-hero-tier-row"><span>' + r.score + '</span><span>' + (tier.next ? tier.ptsToNext + ' pts to ' + esc(tier.next) : 'Peak tier') + '</span></div>' +
    '</div></div>' +
    '<div class="rating-hero-stats">' +
    statStrip.map(function (s) {
      return '<div class="rating-hero-stat"><div class="rating-hero-stat-top">' + icon(s.icon) + '<b' + (s.isText ? ' class="rating-hero-stat-text"' : '') + '>' + esc(String(s.value)) + '</b></div><span>' + esc(s.label) + '</span></div>';
    }).join('') +
    '</div>';
}
function renderLeaderboard() {
  var mode = LEADERBOARD_MODES.find(function (m) { return m.id === state.leaderboardMode; });
  var mySlug = state.name ? slugify(state.name) : null;
  var allRanked = state.leaderboardData.filter(function (r) { return r.mode === mode.id && leaderboardRowInRange(r, state.leaderboardRange); })
    .sort(function (a, b) { return (b[mode.sortKey] || 0) - (a[mode.sortKey] || 0); });
  var rows = allRanked.slice(0, 25);
  var myFullRank = mySlug ? allRanked.findIndex(function (r) { return slugify(r.name) === mySlug; }) : -1;
  var html = '<div class="panel">' +
    '<h2 class="panel-title">' + icon('trophy') + ' Leaderboard</h2>' +
    leaderboardHeroHtml() +
    '<div class="chip-row">' +
    LEADERBOARD_MODES.map(function (m) { return '<button class="chip-toggle' + (state.leaderboardMode === m.id ? ' active' : '') + '" data-leaderboard-mode="' + m.id + '">' + esc(m.label) + '</button>'; }).join('') +
    '</div>' +
    '<div class="chip-row leaderboard-range-row">' +
    LEADERBOARD_RANGES.map(function (r) { return '<button class="chip-toggle' + (state.leaderboardRange === r.id ? ' active' : '') + '" data-leaderboard-range="' + r.id + '">' + esc(r.label) + '</button>'; }).join('') +
    '</div>' +
    leaderboardTopOfWeekHtml(mode, rows);
  if (!rows.length) {
    html += '<p class="mode-desc">No scores yet for ' + esc(mode.label) + (state.leaderboardRange === 'all' ? '' : ' (' + esc(LEADERBOARD_RANGES.find(function (r) { return r.id === state.leaderboardRange; }).label) + ')') + '. Play a round to be the first on the board!</p>';
  } else {
    html += '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>#</th><th>Name</th>' + mode.cols.map(function (c) { return '<th>' + esc(c[1]) + '</th>'; }).join('') + '</tr></thead><tbody>';
    rows.forEach(function (r, i) {
      var isMe = mySlug && slugify(r.name) === mySlug;
      // Full Visual + Interactive Redesign pass: a real tier chip next to
      // each name on the Football Rating leaderboard specifically (the
      // only leaderboard mode whose score maps to a real RATING_TIERS
      // tier) -- computed from that row's own real score, never a
      // separate/fabricated field.
      var tierChip = mode.id === 'rating' && r.score != null
        ? ' <span class="leaderboard-tier-chip">' + esc(ratingTierFor(r.score).name) + '</span>' : '';
      // Brand revamp: a real gold/silver/bronze medal badge for the top 3
      // real ranks instead of a plain number -- the classic leaderboard
      // "podium" convention, on-brand with the app's own gold/chrome
      // accent duality.
      var rankCell = i < 3
        ? '<span class="leaderboard-medal leaderboard-medal-' + (i + 1) + '">' + (i + 1) + '</span>'
        : String(i + 1);
      html += '<tr class="' + (isMe ? 'leaderboard-row-me' : '') + '"><td>' + rankCell + '</td><td>' + esc(r.name) + tierChip + (isMe ? ' <span class="leaderboard-you-tag">You</span>' : '') + '</td>' + mode.cols.map(function (c) { return '<td>' + esc(r[c[0]] != null ? r[c[0]] : 0) + '</td>'; }).join('') + '</tr>';
    });
    html += '</tbody></table></div>';
    if (myFullRank >= 25) {
      var myRow = allRanked[myFullRank];
      html += '<div class="leaderboard-my-rank">Your rank: <b>#' + (myFullRank + 1) + '</b> of ' + allRanked.length + ' &middot; ' +
        mode.cols.map(function (c) { return esc(c[1]) + ' ' + esc(myRow[c[0]] != null ? myRow[c[0]] : 0); }).join(' &middot; ') +
        '</div>';
    }
  }
  html += recentActivityHtml();
  html += '</div>';
  return html;
}

/* ============================== mode-popularity stats (owner-only) ==============================
   The whole "analytics" story for this app, by deliberate choice over a
   third-party tool (Plausible/GA/etc — see the decision recorded in project
   memory): a single shared Firestore counter doc (games/nflTrivia/analytics/
   playCounts), incremented once per real mode entry via
   window.__fbSync.logPlay() in enterMode(). No per-user tracking, no
   external script.
   This app has no real auth/admin-role system at all (every device signs in
   anonymously, same as everyone else), so "viewable only by you" can't mean
   real access control without adding a login system just for this — out of
   proportion for a friend-group trivia app. Instead this screen is reachable
   only via a hidden route (visit the site with #stats in the URL) and isn't
   linked from anywhere in the UI, so regular players won't stumble onto it.
   See the hash check near the bottom of this file (search "#stats"). */
function renderStatsScreen() {
  var counts = (window.__fbSync && window.__fbSync.playCounts) || {};
  var all = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  var rows = all.map(function (m) { return { id: m.id, title: m.title, n: counts[m.id] || 0 }; })
    .sort(function (a, b) { return b.n - a.n; });
  var total = counts.total || 0;
  var maxN = Math.max.apply(null, rows.map(function (r) { return r.n; }).concat([1]));
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Mode Popularity</h2>' +
    '<p class="mode-desc">How many times each mode has been opened, across everyone who’s played &mdash; ' + total + ' total. Hidden page, not linked anywhere in the app.</p>' +
    '<div class="stats-bars">' +
    rows.map(function (r) {
      var pct = Math.round(100 * r.n / maxN);
      return '<div class="stats-bar-row">' +
        '<div class="stats-bar-label">' + esc(r.title) + '</div>' +
        '<div class="stats-bar-track"><div class="stats-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<div class="stats-bar-value">' + r.n + '</div>' +
        '</div>';
    }).join('') +
    '</div>' +
    '</div>';
  return html;
}

/* ============================== about ==============================
   Trust-signal page: what this app is, how the question banks were
   actually built (honestly — some modes have been through a much deeper
   fact-check pass than others; this doesn't claim otherwise), what data is
   stored, and how to flag a bad question. Linked from the footer only. */
function renderAbout() {
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">About Reads</h2>' +
    '<div class="about-section">' +
    '<p class="mode-desc">Reads is free NFL and College Football trivia — ' + totalModeCount() + ' game modes, a live shared leaderboard, and one adaptive Football Rating that follows you across every mode and device. No accounts, no passwords — just a name.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">How the questions are made</h3>' +
    '<p class="mode-desc">Every question bank started from real research — spreadsheets of Heisman winners, national champions, coaching records, career and single-season statistical leaders, bowl history, and rivalries, cross-checked against primary sources rather than written from memory. Wrong-answer options are deliberately pulled from that same real data (other real winners, other real years, other real players) instead of invented — so a wrong answer is still a true fact, just not the one being asked about.</p>' +
    '<p class="mode-desc">The College Football Quiz and IQ Test banks went through a full audit pass: every question was checked for factual accuracy, contradictory or duplicate answer options were found and fixed, near-duplicate questions were removed, and roughly 150 new questions were generated fresh from a dedicated verified reference workbook. The other banks are held to the same real-data-only standard but haven’t all been through that exact same line-by-line review yet — which is exactly what the report link below is for.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Your data</h3>' +
    '<p class="mode-desc">Your name, scores, and Football Rating sync to a shared Firestore database so the leaderboard and rating work across devices — that’s the only place any of it goes. Your streak and a few other stats stay local to your device only. No third-party analytics, no ad trackers. Full details: <button class="link-btn" data-go="privacy">Privacy Policy</button>.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Found a bad question?</h3>' +
    '<p class="mode-desc">Every mode has a ' + icon('flag') + ' Report button next to Restart/Exit while you’re playing — flag it and it goes straight into a review queue.</p>' +
    '</div>' +
    '</div>';
}
/* ============================== push notifications ==============================
   Real Web Push (arrives even when the app/tab isn't open), not a locally
   scheduled notification — the actual sending happens server-side, once a
   day, from netlify/functions/send-daily-push.js. This half just handles
   the browser's subscribe/unsubscribe dance and hands the resulting
   PushSubscription to the backend to store.

   VAPID_PUBLIC_KEY is safe to ship in client code — it's the whole point of
   a public key. Its private counterpart lives only in Netlify's env vars,
   used server-side to sign outgoing pushes so browsers can verify they
   really came from this app's backend and not something else that got
   hold of a subscription endpoint. */
var VAPID_PUBLIC_KEY = 'BEQcgDnLWmFofJ7DLYv7z_DJYRcY58jiM4X_CEf2gCRRKx0N1Wu2QTLF0hSNG8Vn4l8bT0Oi3bzrWNscEDmSuC0';
var PUSH_ENABLED_KEY = 'nflTriviaPushEnabled';
var PUSH_PREFS_KEY = 'nflTriviaPushPrefs';
var PUSH_META_SYNC_KEY = 'nflTriviaPushMetaSync';
function pushSupported() { return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window; }
function pushEnabledLocally() { return lsGet(PUSH_ENABLED_KEY, false); }
function getPushPreferences() {
  return Object.assign({ daily:true, rivals:true, missions:true, comeback:true }, lsGet(PUSH_PREFS_KEY, {}));
}
function setPushPreference(key, value) {
  var p=getPushPreferences(); p[key]=!!value; lsSet(PUSH_PREFS_KEY,p);
  syncPushEngagementSnapshot(true);
  renderAll();
}
function pushEngagementSnapshot() {
  var weekly=weeklyRetentionGoal();
  var goals=weeklyPersonalGoals();
  var standings=weeklyFriendStandings();
  var meIndex=standings.findIndex(function(r){return slugify(r.name)===slugify(state.name||'');});
  var rivalAhead=meIndex>=0 ? standings.slice(0,meIndex).slice(-1)[0] : null;
  var comeback=retentionMission();
  return {
    name:state.name||'',
    updatedAt:Date.now(),
    localDate:todayStr(),
    dailyDone:playedToday(),
    streak:Number(getStreak().count)||0,
    comebackGap:comeback?comeback.gap:0,
    comebackMode:comeback?comeback.mode:null,
    weeklyHabitCurrent:weekly.current,
    weeklyHabitTarget:weekly.target,
    missionsOpen:goals.filter(function(g){return g.current<g.target;}).length,
    rivalName:rivalAhead?rivalAhead.name:null,
    rivalGap:rivalAhead&&meIndex>=0?(rivalAhead.total-standings[meIndex].total):0,
    prefs:getPushPreferences()
  };
}
function syncPushEngagementSnapshot(force) {
  if (!pushEnabledLocally() || !pushSupported() || !state.name) return Promise.resolve();
  var last=Number(lsGet(PUSH_META_SYNC_KEY,0))||0;
  if(!force && Date.now()-last<15*60*1000) return Promise.resolve();
  return navigator.serviceWorker.ready.then(function(reg){return reg.pushManager.getSubscription();}).then(function(sub){
    if(!sub) return;
    return fetch('/.netlify/functions/save-subscription',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({subscription:sub.toJSON ? sub.toJSON() : sub, meta:pushEngagementSnapshot()})
    });
  }).then(function(){lsSet(PUSH_META_SYNC_KEY,Date.now());}).catch(function(err){console.warn('Push metadata sync failed',err);});
}
// PushManager wants the VAPID public key as a raw Uint8Array, not the
// base64url string it's distributed as everywhere else (URL, env vars) —
// this is the standard conversion, same one every Web Push guide uses.
function urlBase64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  var rawData = atob(base64);
  var outputArray = new Uint8Array(rawData.length);
  for (var i = 0; i < rawData.length; i++) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}
function enablePushNotifications() {
  if (!pushSupported()) { alert("This browser doesn't support push notifications."); return Promise.resolve(); }
  return Notification.requestPermission().then(function (permission) {
    if (permission !== 'granted') return;
    return navigator.serviceWorker.ready.then(function (reg) {
      return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) });
    }).then(function (sub) {
      return fetch('/.netlify/functions/save-subscription', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription: sub.toJSON ? sub.toJSON() : sub, meta: pushEngagementSnapshot() })
      });
    }).then(function () {
      lsSet(PUSH_ENABLED_KEY, true);
      renderAll();
    });
  }).catch(function (err) { console.warn('Push subscribe failed', err); });
}
function disablePushNotifications() {
  if (!pushSupported()) return Promise.resolve();
  return navigator.serviceWorker.ready.then(function (reg) {
    return reg.pushManager.getSubscription();
  }).then(function (sub) {
    if (!sub) return;
    return fetch('/.netlify/functions/save-subscription', {
      method: 'DELETE', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subscription: sub.toJSON ? sub.toJSON() : sub })
    }).then(function () { return sub.unsubscribe(); });
  }).then(function () {
    lsSet(PUSH_ENABLED_KEY, false);
    renderAll();
  }).catch(function (err) { console.warn('Push unsubscribe failed', err); });
}
function togglePushNotifications() {
  return pushEnabledLocally() ? disablePushNotifications() : enablePushNotifications();
}

/* ============================== settings ==============================
   Reachable from Profile → Settings — one place for the preferences that
   were previously scattered (sound only in the header, ranked/practice only
   on each mode's own setup screen, favorite teams only behind the header
   gear icon). Doesn't duplicate any storage/logic of its own — every
   control here calls the exact same functions those original entry points
   already used (toggleMute, openTeamPicker, setModeRankedPref/rankedToggleHtml,
   clearAllUserData), so there's exactly one source of truth for each
   setting regardless of where it's changed from. */
function reengagementNudges() {
  if(!state.name) return [];
  var out=[], prefs=getPushPreferences(), streak=getStreak(), weekly=weeklyRetentionGoal();
  if(prefs.daily && !playedToday()) out.push({type:'daily',icon:'flame',title:'Your Daily 5 is ready',body:(streak.count?streak.count+'-day streak on the line. ':'')+'Five games. About five minutes.',go:'daily',priority:100});
  var standings=weeklyFriendStandings(), meIndex=standings.findIndex(function(r){return slugify(r.name)===slugify(state.name||'');});
  if(prefs.rivals && meIndex>0){
    var ahead=standings[meIndex-1], me=standings[meIndex];
    out.push({type:'rival',icon:'versus',title:ahead.name+' is ahead of you',body:(ahead.total-me.total)+' points separate you in the weekly friend race.',go:'friends',priority:90});
  }
  var openGoal=weeklyPersonalGoals().filter(function(g){return g.current<g.target;}).sort(function(x,y){return (y.current/y.target)-(x.current/x.target);})[0];
  if(prefs.missions && openGoal && openGoal.current>0) out.push({type:'mission',icon:'target',title:'Mission almost there',body:openGoal.label+': '+openGoal.current+' / '+openGoal.target+'. Finish it for +'+openGoal.xp+' XP.',go:openGoal.weak?(openGoal.weak.league==='cfb'?'cfbQuiz':'quiz'):'daily',priority:70});
  if(prefs.missions && weekly.current>=3 && weekly.current<weekly.target) out.push({type:'habit',icon:'trophy',title:'Finish the Five-Day Drive',body:weekly.current+' / '+weekly.target+' Daily Reads days this week. +'+weekly.xp+' XP is waiting.',go:'daily',priority:75});
  var comeback=retentionMission();
  if(prefs.comeback && comeback) out.push({type:'comeback',icon:'restart',title:'Comeback Drive available',body:'You’ve been away '+comeback.gap+' days. One ranked game earns +'+comeback.xp+' XP.',go:comeback.mode,priority:95});
  return out.sort(function(x,y){return y.priority-x.priority;});
}
function reengagementCenterHtml() {
  var nudges=reengagementNudges().slice(0,3);
  if(!nudges.length) return '';
  return '<section class="reengagement-center"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">DON’T MISS IT</span><h3>Your next reasons to play</h3></div><span>'+nudges.length+' active</span></div><div class="reengagement-grid">'+nudges.map(function(n){return '<button data-go="'+esc(n.go)+'"><span class="reengagement-icon">'+icon(n.icon)+'</span><div><b>'+esc(n.title)+'</b><small>'+esc(n.body)+'</small></div>'+icon('arrowRight')+'</button>';}).join('')+'</div></section>';
}
function settingsClearDataSectionHtml() {
  if (!state.settingsConfirmClear) {
    return '<button class="btn-secondary" data-settings-clear-ask>' + icon('xMark') + ' Clear My Data</button>';
  }
  return '<div class="settings-clear-confirm">' +
    '<p class="mode-desc">This erases your name, Football Rating, streak, badges, favorite teams, and every local stat on THIS device. It can’t be undone. Your leaderboard/rating entry on other devices (if any) isn’t affected until they also clear.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-settings-clear-confirm>Yes, Clear Everything</button>' +
    '<button class="btn-secondary" data-settings-clear-cancel>Cancel</button>' +
    '</div></div>';
}
function renderSettings() {
  var fav = getFavoriteTeams();
  var nflTeam = fav.nfl ? favoriteTeamById('nfl', fav.nfl) : null;
  var cfbTeam = fav.cfb ? favoriteTeamById('cfb', fav.cfb) : null;
  var allModes = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="profile">' + icon('home') + ' Back to Profile</button><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Settings</h2>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Sound</h3>' +
    '<p class="mode-desc">Background music and correct/wrong/complete sound effects (haptics on mobile follow the same switch).</p>' +
    '<button class="btn-secondary" data-settings-mute-toggle>' + (typeof soundMuted !== 'undefined' && soundMuted ? icon('volumeOff') + ' Sound is Off — Turn On' : icon('volumeOn') + ' Sound is On — Turn Off') + '</button>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Notifications</h3>' +
    '<p class="mode-desc">' + (pushSupported() ? "Reads sends at most one scheduled re-engagement push at a time, chosen from the things you care about below." : "Your browser doesn't support push notifications.") + '</p>' +
    (pushSupported() ? '<button class="btn-secondary" data-settings-push-toggle>' + (pushEnabledLocally() ? icon('volumeOff') + ' Notifications On — Turn Off' : icon('volumeOn') + ' Turn On Notifications') + '</button>' : '') +
    (pushSupported() && pushEnabledLocally() ? '<div class="notification-pref-grid">' + Object.keys(getPushPreferences()).map(function(k){var labels={daily:'Daily 5 ready',rivals:'Friend/rival movement',missions:'Weekly mission progress',comeback:'Comeback reminders'};return '<button class="chip-toggle '+(getPushPreferences()[k]?'active':'')+'" data-push-pref="'+k+'">'+esc(labels[k])+'</button>';}).join('') + '</div>' : '') +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Favorite Teams</h3>' +
    '<p class="mode-desc">' +
    (nflTeam || cfbTeam ? ('NFL: <b>' + esc(nflTeam ? nflTeam.name : 'Not set') + '</b> &middot; College: <b>' + esc(cfbTeam ? cfbTeam.name : 'Not set') + '</b>') : 'Not set yet — used for a few personal touches around the app and a light nudge in the random mix.') +
    '</p>' +
    '<button class="btn-secondary" data-team-picker-toggle>' + icon('users') + ' Change Teams</button>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Ranked vs. Practice, per mode</h3>' +
    '<p class="mode-desc">Ranked rounds count toward your Football Rating, stats, and the leaderboard; Practice rounds don’t. Each mode remembers its own choice — change any of them here, or from that mode’s own start screen.</p>' +
    '<div class="settings-ranked-grid">' +
    allModes.map(function (m) { return '<div class="settings-ranked-row"><span>' + esc(m.title) + '</span>' + rankedToggleHtml(m.id) + '</div>'; }).join('') +
    '</div>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Your Data</h3>' +
    '<p class="mode-desc">Full details on what’s stored and where: <button class="link-btn" data-go="privacy">Privacy Policy</button>.</p>' +
    settingsClearDataSectionHtml() +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">More</h3>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" data-go="about">' + icon('helpCircle') + ' About & How Questions Are Made</button>' +
    '</div>' +
    '</div>' +
    '</div>';
}
function settingsClearDataAsk() { state.settingsConfirmClear = true; renderAll(); }
function settingsClearDataCancel() { state.settingsConfirmClear = false; renderAll(); }
function clearAllUserData() {
  var keys = [];
  for (var i = 0; i < localStorage.length; i++) {
    var k = localStorage.key(i);
    if (k && (k.indexOf('nflTrivia') === 0 || k.indexOf('reads') === 0)) keys.push(k);
  }
  keys.forEach(function (k) { localStorage.removeItem(k); });
  location.reload();
}
/* ============================== privacy policy ==============================
   A real, specific policy — not boilerplate — describing exactly what this
   app collects and where it goes, since Firebase + real names makes this
   worth getting right. Linked from the footer and from the About page. */
function renderPrivacy() {
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Privacy Policy</h2>' +
    '<p class="mode-desc">Last updated ' + CONTENT_UPDATED + '. Reads is a small, free trivia app built for a group of friends — this policy describes exactly what it collects and why, not generic legal boilerplate.</p>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">What Reads collects</h3>' +
    '<p class="mode-desc">Reads has real accounts: you pick a username and password. No real email address is ever required — behind the scenes, Firebase Authentication (a Google Cloud product) is given a synthetic address built from your username, purely so its login system has something in that field. Your password is handled and stored by Firebase Authentication, not by Reads itself. Once you\'re signed in, playing a round can send the following to a shared Firebase/Firestore database:</p>' +
    '<ul class="privacy-list">' +
    '<li>Your name, exactly as you typed it.</li>' +
    '<li>Your scores and stats per game mode (best %, rounds played, etc.), used to build the leaderboard.</li>' +
    '<li>Your Football Rating and how many games it\'s based on.</li>' +
    '<li>If you play Head-to-Head: the match result (both players\' names and scores) is visible to whoever you\'re matched with.</li>' +
    '<li>If you use the Report button: the flagged question, your optional note, and your name (if you\'ve set one).</li>' +
    '</ul>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">What stays on your device only</h3>' +
    '<p class="mode-desc">Your daily-challenge streak, your Football Rating history (used for the little sparkline on your profile), which onboarding screens you\'ve seen, your practice/ranked preferences, and the shuffled-question "deck" that avoids repeats — none of this ever leaves your browser\'s local storage.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Who can see it</h3>' +
    '<p class="mode-desc">The leaderboard, Football Rating board, and Head-to-Head results are intentionally shared and visible to anyone playing the app — that\'s the point of a live leaderboard. The Report queue lives at a hidden, unlisted page rather than behind a real login (this app has no account system to gate it with), so treat it as unlisted, not private. There\'s no ad tracking, no third-party analytics, and nothing is sold or shared outside this Firebase project.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">How you connect</h3>' +
    '<p class="mode-desc">Your username and password sign your browser in to Firebase Authentication using its email/password login method, via that synthetic per-username address described above — so it\'s allowed to read and write the shared data above under your account. Before this account system existed, the app used an anonymous per-device Firebase ID with no personal info attached; some older client behavior described elsewhere in this app may still reference that, but real sign-in is how it works today.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Deleting your data</h3>' +
    '<p class="mode-desc">Clearing your browser\'s site data/local storage removes everything stored on your device. There\'s no self-service delete button for the shared leaderboard/rating/report data yet — email the address below and it\'ll be removed by hand.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Changes</h3>' +
    '<p class="mode-desc">If what this app collects changes, this page gets updated and the date at the top will change.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Questions</h3>' +
    '<p class="mode-desc">Email us about this policy or your data:</p>' +
    '<div class="contact-email-row">' +
    '<a class="contact-email" href="mailto:readstrivia@gmail.com">readstrivia@gmail.com</a>' +
    '<button class="btn-tiny" data-copy-email="readstrivia@gmail.com">' + icon('copy') + ' Copy</button>' +
    '</div>' +
    '</div>' +
    '</div>';
}

/* ============================== learn ==============================
   A browsable reference section — NFL/CFB facts, history, stat leaders,
   Hall of Famers — deliberately NOT another quiz/game mode, just filterable
   lists. Ships with 8 sections, all sourced from data this app already has
   verified for its game modes (CFB_GRID_PLAYERS, GRID_PLAYERS, plus the
   existing CFB/QUIZ trivia banks for the two Trivia Almanac sections)
   rather than authoring new content — see LEARN_SECTIONS below for exactly
   which field backs which section.

   The two "Trivia Almanac" sections reuse this app's own 456-question CFB
   quiz bank and 482-question NFL quiz bank (CFB/QUIZ, already loaded eagerly
   at startup for the Quiz modes) as fact cards instead of tables — each
   question's correct option plus its `notes` field reads as a standalone
   fact ("Q, A, and why"), which doesn't fit a table's fixed columns the way
   the roster-stat sections do. dataFiles is deliberately [] for these two:
   CFB/QUIZ are core assets loaded via a <script> tag in index.html, not via
   loadScript(), so listing them here would just re-fetch and re-run an
   already-loaded file for no reason.

   Two honesty notes baked into the section choices themselves (found while
   designing this, not something to quietly paper over):
   - CFB_GRID_PLAYERS' `years` field is a player's All-America SELECTION
     year(s), not a dedicated Heisman-year or championship-year field —
     Archie Griffin, the only 2x Heisman winner, has years:[1974] only, not
     [1974, 1975]. Sections that show a year label it "AA Year," not
     "Heisman Year," and the natChamp section doesn't imply the year shown
     is when the title was actually won.
   - Pro Football Hall of Fame status is tracked as two separate booleans
     (CFB_GRID_PLAYERS.hof, 52 true; GRID_PLAYERS.hof, 158 true) for the
     same real honor, curated independently with no guaranteed overlap.
     v1's Hall of Fame section sources GRID_PLAYERS only rather than
     merging both pools with no dedup guarantee — a real "not done yet,"
     not an oversight. */
var LEARN_SECTIONS = [
  // The Football Learning Engine's first real curriculum module -- distinct
  // from every other card here, which browse verified player/trivia FACTS.
  // This one teaches CONCEPTS (structured, with prerequisites, lessons, and
  // interactive reps) via a dedicated 'classroom' sub-screen (see
  // openLearnSection()/renderClassroomScreen()), not the generic filter/
  // table section renderer every other card below uses.
  // The full Football Learning Encyclopedia -- browse-first (search ->
  // domain -> concept), covering every football domain the source
  // workbook supports. Distinct from coverageClassroom below (which stays
  // a focused, lesson-based teaching module for one topic); this is the
  // "look anything up" reference the rest of Learn now sits inside of.
  { id: 'footballEncyclopedia', league: 'both', icon: 'book', title: 'Football Encyclopedia',
    desc: 'Positions, personnel, formations, routes, passing concepts, run game, blocking, protection, QB play, defensive fronts, pressures, schemes, and more -- searchable and organized beginner to advanced.',
    // Also loads learn-coverages.js (not just learn-encyclopedia.js) so a
    // COVERAGES-domain concept page's "learn this hands-on" cross-link into
    // the Coverage Classroom (see renderEncyclopediaConceptDetail()) always
    // works, even if the user opens the Encyclopedia without ever visiting
    // the Classroom card first. football-field.js + football-diagrams.js
    // (Football 101 Interactive Redesign) are the reusable SVG diagram
    // engine and its data-driven formation/front/coverage/concept library --
    // lazy-loaded here too, never part of the initial page load, exactly
    // like every other Learn data file.
    dataFiles: ['data/learn-encyclopedia.js', 'data/learn-coverages.js', 'football-field.js', 'data/football-diagrams.js', 'data/encyclopedia-deep-dives.js'] },
  { id: 'coverageClassroom', league: 'nfl', icon: 'brain', title: 'Defensive Coverages: The Classroom',
    desc: 'Learn to read a defense -- Cover 0 through Cover 6, man vs. zone, and real rotations, taught step by step with interactive reps.',
    dataFiles: ['data/learn-coverages.js'] },
  { id: 'cfbHeisman', league: 'cfb', icon: 'trophy', title: 'Heisman Trophy Winners',
    desc: 'Every Heisman winner tracked in the CFB player pool.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbMultiAA', league: 'cfb', icon: 'graduationCap', title: 'Multi-Time All-Americans',
    desc: 'Players named a consensus All-American more than once.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbNatChamp', league: 'cfb', icon: 'cfpTrophy', title: 'National Champions',
    desc: 'Players who were on a national championship roster.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbAwards', league: 'cfb', icon: 'zap', title: 'Position Award Winners',
    desc: 'Maxwell, Outland, Lombardi, and 14 more national position awards.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'nflHof', league: 'nfl', icon: 'hofJacket', title: 'Pro Football Hall of Fame',
    desc: 'Every Hall of Famer tracked in the NFL player pool.', dataFiles: ['data/grid.js', 'data/grid-engine-players.js'] },
  { id: 'nflDecorated', league: 'nfl', icon: 'target', title: 'Pro Bowl & All-Pro Selections',
    desc: 'Every player with at least one Pro Bowl or All-Pro nod.', dataFiles: ['data/grid.js', 'data/grid-engine-players.js'] },
  { id: 'cfbTrivia', league: 'cfb', icon: 'brain', title: 'CFB Trivia Almanac',
    desc: CFB.length + ' real facts across Heisman history, coaches, rivalries, and more.', dataFiles: [] },
  { id: 'nflTrivia', league: 'nfl', icon: 'lombardiTrophy', title: 'NFL Trivia Almanac',
    desc: QUIZ.length + ' real facts across Super Bowl history, records, and more.', dataFiles: [] },
  { id: 'xsoAlmanac', league: 'both', icon: 'versus', title: "X's & O's Almanac",
    // dataFiles listed (unlike the two Trivia Almanacs above) because XSO,
    // unlike QUIZ/CFB, isn't a core asset loaded via <script> tag — it's
    // lazy-loaded the same way every other mode-specific data file is.
    desc: '700 scheme/strategy facts across formations, coverages, blocking, and more.', dataFiles: ['data/xso.js'] }
];
function learnSectionById(id) { return LEARN_SECTIONS.find(function (s) { return s.id === id; }); }
function learnMatchesFilter(filter, searchBlob) {
  return !filter || normName(searchBlob).indexOf(normName(filter)) !== -1;
}
function learnEmptyRow(filter) {
  return '<tr><td colspan="5" class="mode-desc">No matches for "' + esc(filter) + '".</td></tr>';
}
// Category chips, added alongside the free-text filter so each section can
// also be narrowed by whatever grouping actually fits its data — position
// for the roster-stat sections, award name for cfbAwards, and the trivia
// bank's own `category` field for the two Trivia Almanac sections. Every
// section keeps its own `categories()` getter (same "duplicate per-section
// code" convention as the rest of this file) since what counts as a
// "category" genuinely differs per section; learnInCategory()/
// learnCategoryChips() are the only shared plumbing.
function learnUniqueSorted(arr) {
  var seen = {}, out = [];
  arr.forEach(function (v) { if (v && !seen[v]) { seen[v] = true; out.push(v); } });
  return out.sort();
}
function learnInCategory(selected, itemCats) {
  return !selected || itemCats.indexOf(selected) !== -1;
}
function learnCategoryChips(categories, selected) {
  if (!categories.length) return '';
  return '<div class="chip-row learn-chip-row">' +
    '<button class="chip-toggle' + (!selected ? ' active' : '') + '" data-learn-cat="">All</button>' +
    categories.map(function (c) {
      return '<button class="chip-toggle' + (c === selected ? ' active' : '') + '" data-learn-cat="' + esc(c) + '">' + esc(c) + '</button>';
    }).join('') +
    '</div>';
}

function learnCfbHeismanPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.heisman === true; }); }
function learnCfbHeismanCategories() {
  var pos = [];
  learnCfbHeismanPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbHeismanYear(p) { return p.heismanYear || p.years[0]; }
function learnCfbHeismanRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbHeismanPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return (learnCfbHeismanYear(a) || 0) - (learnCfbHeismanYear(b) || 0) || a.name.localeCompare(b.name); });
}
function renderLearnCfbHeisman() {
  var rows = learnCfbHeismanRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Year</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      var pos = p.positions.join('/');
      // Position shown both next to the name (so it's visible without
      // scrolling right on narrow screens) and in its own column.
      return '<tr><td>' + esc(p.name) + (pos ? ' <span class="learn-pos-tag">(' + esc(pos) + ')</span>' : '') + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(pos || '—') + '</td><td>' + (learnCfbHeismanYear(p) || '—') + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbMultiAAPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.multiAA === true; }); }
function learnCfbMultiAACategories() {
  var pos = [];
  learnCfbMultiAAPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbMultiAARows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbMultiAAPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return b.years.length - a.years.length || (a.years[0] || 0) - (b.years[0] || 0) || a.name.localeCompare(b.name); });
}
function renderLearnCfbMultiAA() {
  var rows = learnCfbMultiAARows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Selection Years</th><th>Times</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.years.slice().sort().join(', ')) + '</td><td>' + p.years.length + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbNatChampPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.natChamp === true; }); }
function learnCfbNatChampCategories() {
  var pos = [];
  learnCfbNatChampPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbNatChampRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbNatChampPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return a.name.localeCompare(b.name); });
}
function renderLearnCfbNatChamp() {
  var rows = learnCfbNatChampRows();
  return '<p class="mode-desc">Players who were on a national championship roster at some point in their career. The AA Year column is their All-America selection year(s) for context — not necessarily the same season as the title.</p>' +
    '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>AA Year(s)</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.years.join(', ')) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbAwardsPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.awards && p.awards.length > 0; }); }
function learnCfbAwardsCategories() {
  var aw = [];
  learnCfbAwardsPool().forEach(function (p) { aw = aw.concat(p.awards); });
  return learnUniqueSorted(aw);
}
function learnCfbAwardsRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbAwardsPool()
    .filter(function (p) { return learnInCategory(cat, p.awards); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ') + ' ' + p.awards.join(' ')); })
    .sort(function (a, b) { return a.awards.slice().sort()[0].localeCompare(b.awards.slice().sort()[0]) || a.name.localeCompare(b.name); });
}
function renderLearnCfbAwards() {
  var rows = learnCfbAwardsRows();
  return '<p class="mode-desc">17 real national position awards (Maxwell, Outland Trophy, Lombardi, Walter Camp, Davey O\'Brien, Jim Thorpe, Butkus, and more) — sorted by award. AA Year is their All-America selection year for context, not necessarily the same season as the award.</p>' +
    '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Award(s)</th><th>AA Year</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.awards.join(', ')) + '</td><td>' + (p.years[0] || '—') + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnEmptyCard(filter) {
  return '<p class="mode-desc">No matches for "' + esc(filter) + '".</p>';
}
function learnTriviaCategories(pool) {
  return learnUniqueSorted(pool.map(function (q) { return q.category; }));
}
function learnTriviaRows(pool) {
  var filter = state.learn.filter, cat = state.learn.category;
  return pool.filter(function (q) { return q.question && q.options && q.options.length; })
    .filter(function (q) { return learnInCategory(cat, [q.category]); })
    .filter(function (q) {
      return learnMatchesFilter(filter, q.category + ' ' + q.question + ' ' + (q.options[q.correctIndex] || '') + ' ' + (q.notes || ''));
    })
    .sort(function (a, b) { return a.category.localeCompare(b.category) || a.id - b.id; });
}
function renderLearnTriviaCards(rows) {
  return '<div class="learn-fact-list">' +
    (rows.length ? rows.map(function (q) {
      return '<div class="learn-fact-card">' +
        '<span class="learn-pill">' + esc(q.category) + '</span>' +
        '<div class="learn-fact-q">' + esc(q.question) + '</div>' +
        '<details class="film-fact-reveal"><summary>Make your read, then reveal the answer</summary><div class="learn-fact-a">' + esc(q.options[q.correctIndex]) + '</div>' +
        (q.notes ? '<div class="learn-fact-notes">' + esc(q.notes) + '</div>' : '') + '</details>' +
        '</div>';
    }).join('') : learnEmptyCard(state.learn.filter)) +
    '</div>';
}
function renderLearnCfbTrivia() {
  var rows = learnTriviaRows(CFB);
  return '<p class="mode-desc">' + rows.length + ' CFB facts across Heisman history, national championships, coaches, rivalries, and more — search by team, player, or topic.</p>' +
    renderLearnTriviaCards(rows);
}
function renderLearnNflTrivia() {
  var rows = learnTriviaRows(QUIZ);
  return '<p class="mode-desc">' + rows.length + ' NFL facts across Super Bowl history, franchise records, coaches, and more — search by team, player, or topic.</p>' +
    renderLearnTriviaCards(rows);
}
function renderLearnXso() {
  var rows = learnTriviaRows(XSO);
  return '<p class="mode-desc">' + rows.length + ' scheme/strategy facts across formations, coverages, blocking, route concepts, and more — search by term or topic. The X\'s &amp; O\'s mode is the quiz version of this same bank.</p>' +
    renderLearnTriviaCards(rows);
}

function learnNflHofPool() { return GRID_PLAYERS.filter(function (p) { return p.hof === true; }); }
function learnNflHofCategories() {
  return learnUniqueSorted(learnNflHofPool().map(function (p) { return p.position; }));
}
function learnNflHofRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnNflHofPool()
    .filter(function (p) { return learnInCategory(cat, [p.position]); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + (p.college || '') + ' ' + p.teams.join(' ')); })
    .sort(function (a, b) { return a.name.localeCompare(b.name); });
}
function learnDraftLabel(p) {
  if (!p.draft) return '—';
  if (p.draft.round === 0) return 'Undrafted, ' + p.draft.year;
  return p.draft.round ? 'Round ' + p.draft.round + ', ' + p.draft.year : '—';
}
function renderLearnNflHof() {
  var rows = learnNflHofRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>Position</th><th>College</th><th>Teams</th><th>Draft</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.position || '—') + '</td><td>' + esc(p.college || '—') + '</td><td>' + esc(p.teams.join(', ')) + '</td><td>' + esc(learnDraftLabel(p)) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnNflDecoratedPool() { return GRID_PLAYERS.filter(function (p) { return (p.proBowls || 0) > 0 || (p.allPro || 0) > 0; }); }
function learnNflDecoratedCategories() {
  return learnUniqueSorted(learnNflDecoratedPool().map(function (p) { return p.position; }));
}
function learnNflDecoratedRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnNflDecoratedPool()
    .filter(function (p) { return learnInCategory(cat, [p.position]); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + (p.college || '') + ' ' + p.teams.join(' ')); })
    .sort(function (a, b) { return ((b.proBowls || 0) + (b.allPro || 0)) - ((a.proBowls || 0) + (a.allPro || 0)) || (b.proBowls || 0) - (a.proBowls || 0) || a.name.localeCompare(b.name); });
}
function learnBadges(p) {
  var b = [];
  if (p.mvp) b.push('MVP');
  if (p.sbChamp) b.push('SB Champ');
  if (p.sbMVP) b.push('SB MVP');
  return b.length ? b.map(function (x) { return '<span class="learn-pill">' + esc(x) + '</span>'; }).join(' ') : '—';
}
function renderLearnNflDecorated() {
  var rows = learnNflDecoratedRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>Position</th><th>Pro Bowls</th><th>All-Pro</th><th>Also</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.position || '—') + '</td><td>' + (p.proBowls || 0) + '</td><td>' + (p.allPro || 0) + '</td><td>' + learnBadges(p) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnSectionCategories(id) {
  return id === 'cfbHeisman' ? learnCfbHeismanCategories() :
    id === 'cfbMultiAA' ? learnCfbMultiAACategories() :
    id === 'cfbNatChamp' ? learnCfbNatChampCategories() :
    id === 'cfbAwards' ? learnCfbAwardsCategories() :
    id === 'nflHof' ? learnNflHofCategories() :
    id === 'nflDecorated' ? learnNflDecoratedCategories() :
    id === 'cfbTrivia' ? learnTriviaCategories(CFB) :
    id === 'nflTrivia' ? learnTriviaCategories(QUIZ) :
    id === 'xsoAlmanac' ? learnTriviaCategories(XSO) : [];
}

/* Film Room: local study notebook, daily reps, and coach dashboard. */
function filmNotebook() {
  var n=lsGet('readsFilmNotebook__' + slugify(state.name || 'guest'), { saved: [], viewed: {}, reps: 0, correct: 0, days: {}, last: null, mastery:{}, sessions:0, bossWins:0, review:[] });
  n.saved=Array.isArray(n.saved)?n.saved:[]; n.viewed=n.viewed||{}; n.days=n.days||{}; n.mastery=n.mastery||{}; n.review=Array.isArray(n.review)?n.review:[];
  n.reps=Number(n.reps)||0; n.correct=Number(n.correct)||0; n.sessions=Number(n.sessions)||0; n.bossWins=Number(n.bossWins)||0;
  return n;
}
function filmSaveNotebook(n) { lsSet('readsFilmNotebook__' + slugify(state.name || 'guest'), n); }
var FILM_FAMILIES=[
  {id:'coverage',label:'Coverages',icon:'🛡️',rx:/cover|coverage|zone|man defense|secondary|safety/i},
  {id:'pressure',label:'Pressures',icon:'⚡',rx:/blitz|pressure|rush|pass rush|protection/i},
  {id:'routes',label:'Routes & Pass Game',icon:'↗️',rx:/route|passing|receiver|concept|mesh|levels|flood|smash|spacing/i},
  {id:'run',label:'Run Game',icon:'🏃',rx:/run game|rushing|zone run|power|counter|gap scheme|blocking/i},
  {id:'fronts',label:'Fronts & Personnel',icon:'🧱',rx:/front|formation|personnel|alignment|defensive line|box/i},
  {id:'situational',label:'Situational Football',icon:'🧠',rx:/down|distance|red zone|goal line|two-minute|clock|situational|third down|fourth down/i},
  {id:'history',label:'Football History',icon:'🏆',rx:/history|award|heisman|hall of fame|champion|super bowl|record/i}
];
function filmFamilyForQuestion(q){
  var hay=String((q&&q.category)||'')+' '+String((q&&q.question)||'')+' '+String((q&&q.notes)||'');
  for(var i=0;i<FILM_FAMILIES.length;i++)if(FILM_FAMILIES[i].rx.test(hay))return FILM_FAMILIES[i].id;
  return 'footballIQ';
}
function filmFamilyMeta(id){
  return FILM_FAMILIES.find(function(f){return f.id===id;})||{id:'footballIQ',label:'Football IQ',icon:'🏈'};
}
function filmRecordRep(correct,q) {
  var n = filmNotebook(); n.reps++; if (correct) n.correct++;
  var family=filmFamilyForQuestion(q), rec=n.mastery[family]||{attempts:0,correct:0,lastPracticed:0};
  rec.attempts++; if(correct)rec.correct++; rec.lastPracticed=Date.now(); n.mastery[family]=rec;
  if(!correct&&q){
    n.review.unshift({family:family,question:q.question||q.prompt||'',answer:q.options&&q.correctIndex!=null?q.options[q.correctIndex]:'',notes:q.notes||q.explanation||'',at:Date.now()});
    n.review=n.review.slice(0,30);
  }
  n.days[new Date().toLocaleDateString('en-CA')] = true; filmSaveNotebook(n);
}
function filmMasteryLevel(rec){
  rec=rec||{attempts:0,correct:0}; if(!rec.attempts)return {name:'Rookie',pct:0,next:'Starter'};
  var pct=Math.round(100*rec.correct/rec.attempts);
  if(rec.attempts>=12&&pct>=88)return {name:'Guru',pct:pct,next:null};
  if(rec.attempts>=8&&pct>=80)return {name:'Coordinator',pct:pct,next:'Guru'};
  if(rec.attempts>=5&&pct>=70)return {name:'Starter',pct:pct,next:'Coordinator'};
  return {name:'Rookie',pct:pct,next:'Starter'};
}
function filmWeakFamily(){
  var n=filmNotebook(), ids=FILM_FAMILIES.map(function(f){return f.id;});
  ids.push('footballIQ');
  ids.sort(function(x,y){
    var a=n.mastery[x]||{attempts:0,correct:0},b=n.mastery[y]||{attempts:0,correct:0};
    var ap=a.attempts?(a.correct/a.attempts):-.2,bp=b.attempts?(b.correct/b.attempts):-.2;
    return ap-bp || a.attempts-b.attempts;
  });
  return ids[0];
}
function filmMeter(value, total, label) {
  return '<div class="film-meter"><div><span>' + esc(label) + '</span><strong>' + value + ' / ' + total + '</strong></div><div class="film-meter-track"><span style="width:' + Math.min(100, total ? 100 * value / total : 0) + '%"></span></div></div>';
}
function filmMasteryTreeHtml(){
  var n=filmNotebook(), families=FILM_FAMILIES.concat([{id:'footballIQ',label:'Football IQ',icon:'🏈'}]);
  return '<section class="film-mastery-tree"><div class="dashboard-section-head"><div><span class="film-eyebrow">SKILL TREE</span><h3>Concept Mastery</h3></div><span>'+n.reps+' total reps</span></div>'+
    '<div class="film-mastery-grid">'+families.map(function(f){
      var rec=n.mastery[f.id]||{attempts:0,correct:0}, level=filmMasteryLevel(rec);
      return '<article class="film-mastery-card mastery-'+slugify(level.name)+'"><span class="film-mastery-icon">'+f.icon+'</span><div><b>'+esc(f.label)+'</b><small>'+level.name+' · '+rec.attempts+' reps'+(rec.attempts?' · '+level.pct+'%':'')+'</small></div><span class="film-mastery-bar"><i style="width:'+Math.min(100,rec.attempts?level.pct:4)+'%"></i></span></article>';
    }).join('')+'</div></section>';
}
function filmCoachAssignmentHtml(){
  var id=filmWeakFamily(), meta=filmFamilyMeta(id), rec=filmNotebook().mastery[id]||{attempts:0,correct:0}, level=filmMasteryLevel(rec);
  var why=!rec.attempts?'You have not logged reps here yet.':level.pct<70?'This is your lowest-accuracy area.':'This area has the most room for more reps.';
  return '<section class="film-coach-assignment"><div><span class="film-eyebrow">COACH’S ASSIGNMENT</span><h3>'+meta.icon+' '+esc(meta.label)+'</h3><p>'+esc(why)+' Today’s adaptive session will lean into it.</p></div><button class="btn-primary" data-film-study-family="'+esc(id)+'">Work on '+esc(meta.label)+'</button></section>';
}
function filmReviewQueueHtml(){
  var rows=filmNotebook().review.slice(0,3);
  if(!rows.length)return '';
  return '<section class="film-review-queue"><div class="dashboard-section-head"><div><span class="film-eyebrow">TAPE REVIEW</span><h3>Missed Reads</h3></div><button class="btn-tiny" data-film-review>Review all</button></div>'+
    '<div>'+rows.map(function(r){return '<article><span>'+filmFamilyMeta(r.family).icon+'</span><div><b>'+esc(r.question)+'</b><small>'+esc(r.answer||'Review the coaching note')+'</small></div></article>';}).join('')+'</div></section>';
}
function filmPoolForFamily(pool,family){
  if(!family)return pool.slice();
  var filtered=pool.filter(function(q){return filmFamilyForQuestion(q)===family;});
  return filtered.length?filtered:pool.slice();
}
function filmSeededPick(pool,count,seed){
  return pool.filter(function(q){return !/\bdraft\b/i.test(String(q.question||'')+' '+String(q.category||''));})
    .map(function(q,i){return {q:q,rank:hashStr(String(seed)+'|'+String(q.id||q.question)+'|'+i)};})
    .sort(function(x,y){return x.rank-y.rank;}).slice(0,count).map(function(v){return v.q;});
}
function filmBuildSessionQuestions(family,count,boss){
  var day=new Date().toLocaleDateString('en-CA'), seed=hashStr(day+'|'+family+'|'+(boss?'boss':'daily')+'|'+state.name);
  var pools=[XSO,QUIZ,CFB], broad=[];
  pools.forEach(function(p){broad=broad.concat(filmPoolForFamily(p,family));});
  var target=filmSeededPick(broad,Math.max(count,4),seed);
  if(target.length<count){
    var fallback=filmSeededPick(XSO.concat(QUIZ,CFB),count*2,seed+17);
    fallback.forEach(function(q){if(target.indexOf(q)===-1&&target.length<count)target.push(q);});
  }
  if(boss){
    target.sort(function(x,y){
      var xd=String(x.difficulty||'').toLowerCase(),yd=String(y.difficulty||'').toLowerCase();
      var xs=xd==='expert'?3:xd==='hard'?2:xd==='medium'?1:0,ys=yd==='expert'?3:yd==='hard'?2:yd==='medium'?1:0;
      return ys-xs;
    });
  }
  return target.slice(0,count);
}
function completeFilmStudySession(){
  var s=state.filmStudy;if(!s||s.completed||s.index<s.questions.length)return;
  s.completed=true;
  var n=filmNotebook(), pct=s.questions.length?Math.round(100*s.correct/s.questions.length):0;
  n.sessions=(n.sessions||0)+1;
  if(s.type==='boss'&&pct>=80)n.bossWins=(n.bossWins||0)+1;
  filmSaveNotebook(n);
  awardProgressForCompletion('learn',{boss:s.type==='boss',correct:s.correct,total:s.questions.length,pct:pct,targetFamily:s.targetFamily});
}

function filmStatsHtml() {
  var n = filmNotebook(), p = getClassroomProgress(), complete = Object.keys(p).filter(function (id) { return p[id].completed; }).length;
  return '<div class="film-stats"><div><strong>' + complete + '</strong><span>Lessons complete</span></div><div><strong>' + n.reps + '</strong><span>Study reps</span></div><div><strong>' + (n.reps ? Math.round(n.correct / n.reps * 100) + '%' : '—') + '</strong><span>Rep accuracy</span></div><div><strong>' + Object.keys(n.days).length + '</strong><span>Days studied</span></div></div>';
}
function filmDashboard() {
  var n = filmNotebook();
  var groups = [
    { title: 'The playbook', note: 'Learn the game. See the assignments. Make the read.', ids: ['footballEncyclopedia', 'coverageClassroom', 'xsoAlmanac'] },
    { title: 'Pro football archive', note: 'Legends, accolades, and the moments that built the league.', ids: ['nflHof', 'nflDecorated', 'nflTrivia'] },
    { title: 'College football archive', note: 'Champions, award winners, and Saturday history.', ids: ['cfbHeisman', 'cfbMultiAA', 'cfbNatChamp', 'cfbAwards', 'cfbTrivia'] }
  ];
  var filter = state.learn.filmFilter || '';
  var cards = groups.map(function (g, groupIndex) {
    var sections = g.ids.map(learnSectionById).filter(function (v) { return learnMatchesFilter(filter, v.title + ' ' + v.desc + ' ' + g.title); });
    return sections.length ? '<section class="film-group" id="film-group-' + groupIndex + '"><div class="film-group-head"><h3>' + g.title + '</h3><p>' + g.note + '</p></div><div class="mode-grid">' + sections.map(learnSectionCardHtml).join('') + '</div></section>' : '';
  }).join('');
  var last = n.last;
  var resume = last ? '<button class="btn-secondary" data-film-resume>Continue: ' + esc(last.label) + ' →</button>' : '<button class="btn-secondary" data-learn-open="coverageClassroom">Start with defensive coverages →</button>';
  return '<div class="panel film-dashboard"><div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Home</button></div>' +
    '<div class="film-hero"><span class="film-eyebrow">READS / COACH’S NOTEBOOK</span><h2>The Film Room</h2><p>See the field.<br>Understand the game.</p><div class="film-chalk-art" aria-hidden="true">X &nbsp; X &nbsp; X<br>↗ &nbsp; ↑ &nbsp; ↖<br>O &nbsp; O &nbsp; O</div></div>' +
    filmStatsHtml() + filmCoachAssignmentHtml() + filmMasteryTreeHtml() + '<div class="film-session"><div><span class="film-eyebrow">TODAY’S STUDY SESSION</span><h3>Five adaptive reps. Sharper football IQ.</h3><p>Reads leans into the areas you need most, then raises the bar as you improve.</p></div><button class="btn-primary" data-film-study>Take the reps ' + icon('arrowRight') + '</button></div>' + '<div class="film-boss-card"><div><span class="film-eyebrow">COORDINATOR TEST</span><h3>Ten reps. No hiding.</h3><p>A tougher boss session weighted toward your weakest concept family. Score 80% to earn the win.</p></div><button class="btn-secondary" data-film-boss>Take the Test</button></div>' + filmReviewQueueHtml() +
    '<div class="film-resume">' + resume + '<button class="btn-tiny" data-film-saved>Saved concepts (' + n.saved.length + ')</button></div>' +
    '<label class="film-search-label" for="film-search-input">Find your next session</label><input id="film-search-input" class="learn-filter-input" placeholder="Search sections: coverages, history, awards…" value="' + esc(filter) + '">' +
    '<div class="chip-row film-jump-nav" aria-label="Film Room sections">' + groups.map(function(g,i) { return '<button class="chip-toggle" data-film-jump="' + i + '">' + esc(['Playbook', 'NFL archive', 'College archive'][i]) + '</button>'; }).join('') + '</div>' + (cards || '<p class="mode-desc">No sections match. Try “coverage” or “NFL”.</p>') + '<p class="film-local-note">Your notebook is saved on this device for this profile.</p></div>';
}
function startFilmStudy(family,boss) {
  family=family||filmWeakFamily(); boss=!!boss;
  beginProgressSession('learn');
  state.learn.screen='study';state.learn.loadingSection='xsoAlmanac';state.learn.loadError=null;renderAll();
  var ready=loadedScripts['data/xso.js']?Promise.resolve():loadScript('data/xso.js');
  ready.then(function(){
    refreshDataAliases();
    if(state.learn.screen!=='study')return;
    var count=boss?10:5, questions=filmBuildSessionQuestions(family,count,boss);
    state.filmStudy={questions:questions,index:0,answered:null,correct:0,review:[],type:boss?'boss':'daily',targetFamily:family,completed:false};
    state.learn.loadingSection=null;renderAll();
  }).catch(function(){if(state.learn.screen==='study'){state.learn.loadingSection=null;state.learn.loadError='xsoAlmanac';renderAll();}});
}
function startFilmBoss(){startFilmStudy(filmWeakFamily(),true);}
function startFilmReview(){
  var n=filmNotebook(), rows=n.review.slice(0,10);
  if(!rows.length){startFilmStudy();return;}
  beginProgressSession('learn');
  state.learn.screen='study';
  state.filmStudy={
    questions:rows.map(function(r,i){
      var opts=[r.answer||'Review the correct read','Not this read','Different assignment','Check the coaching note'];
      return {id:'review_'+i,category:filmFamilyMeta(r.family).label,question:r.question,options:opts,correctIndex:0,notes:r.notes||''};
    }),
    index:0,answered:null,correct:0,review:[],type:'review',targetFamily:'review',completed:false
  };
  renderAll();
}
function renderFilmStudy() {
  var s=state.filmStudy;
  if(!s||!s.questions.length)return '<div class="panel"><button class="btn-secondary" data-film-study>Start study session</button></div>';
  var head='<div class="mode-toolbar"><button class="btn-tiny" data-learn-back>← Film Room</button><span class="film-eyebrow">'+
    (s.type==='boss'?'COORDINATOR TEST':s.type==='review'?'TAPE REVIEW':'ADAPTIVE REPS')+'</span></div>';
  if(s.index>=s.questions.length){
    completeFilmStudySession();
    var fpct=s.questions.length?Math.round(100*s.correct/s.questions.length):0;
    return '<div class="panel">'+head+
      '<div class="film-milestone" role="status"><span class="film-eyebrow">'+
      (s.type==='boss'?(fpct>=80?'COORDINATOR TEST PASSED':'COORDINATOR TEST COMPLETE'):'SESSION COMPLETE')+
      '</span><strong>'+s.correct+'<small> / '+s.questions.length+'</small></strong><h2>'+
      (s.type==='boss'?(fpct>=80?'You passed the headset test.':'Run the tape and come back sharper.'):(s.correct===s.questions.length?'You made every read.':'Put the tape to work.'))+
      '</h2><p>'+
      (s.type==='boss'?(fpct>=80?'Boss win logged. Your Film Room résumé just got stronger.':'Score 80% next time to earn the Coordinator Test win.'):'Review the coaching notes, then attack your next assignment.')+
      '</p></div>'+progressionResultHookHtml()+
      '<div class="film-review">'+s.review.map(function(r){
        return '<div><span class="learn-pill">'+(r.correct?'Good read':'Review this')+'</span><h3>'+esc(r.q.question)+'</h3><p><strong>'+esc(r.q.options[r.q.correctIndex])+'</strong></p>'+(r.q.notes?'<p>'+esc(r.q.notes)+'</p>':'')+'</div>';
      }).join('')+'</div>'+
      '<button class="btn-primary" data-learn-back>Back to the Film Room</button></div>';
  }
  var q=s.questions[s.index],answered=s.answered!==null;
  return '<div class="panel">'+head+
    filmMeter(s.index,s.questions.length,'Session progress')+
    '<div class="film-session-target"><span>'+filmFamilyMeta(s.targetFamily).icon+'</span><b>'+esc(filmFamilyMeta(s.targetFamily).label)+'</b><small>'+(s.type==='boss'?'Boss focus':'Adaptive focus')+'</small></div>'+
    '<span class="learn-pill">'+esc(q.category)+'</span><h2 class="quiz-question">'+esc(q.question)+'</h2>'+
    '<div class="quiz-options">'+q.options.map(function(opt,i){
      return '<button class="quiz-option'+(answered&&i===q.correctIndex?' correct':answered&&i===s.answered?' wrong':'')+'" data-film-answer="'+i+'"'+(answered?' disabled':'')+'><span class="film-option-letter">'+String.fromCharCode(65+i)+'</span>'+esc(opt)+'</button>';
    }).join('')+'</div>'+
    (answered?'<div class="quiz-feedback" role="status"><span class="film-eyebrow">'+(s.answered===q.correctIndex?'GOOD READ':'COACH’S CORRECTION')+'</span><h3>'+esc(q.options[q.correctIndex])+'</h3>'+(q.notes?'<p>'+esc(q.notes)+'</p>':'<p>Lock in that answer before moving to your next rep.</p>')+'</div><button class="btn-primary" data-film-next>'+(s.index+1===s.questions.length?'Review session':'Next rep →')+'</button>':'')+
    '</div>';
}
function renderFilmSaved() {
  var n = filmNotebook();
  return '<div class="panel"><button class="btn-tiny" data-learn-back>← Film Room</button><span class="film-eyebrow">YOUR PLAYBOOK</span><h2 class="panel-title">Saved concepts</h2><p class="mode-desc">Keep the reads you want to revisit close at hand.</p><div class="encyc-row-list">' + (n.saved.map(function(v) { return '<button class="encyc-row" data-film-concept="' + esc(v.kind + ':' + v.id) + '"><span class="encyc-row-label">' + esc(v.label) + '</span><span class="encyc-row-meta">Open notes →</span></button>'; }).join('') || '<p class="mode-desc">Open a concept in the Football Encyclopedia and tap Save to playbook.</p>') + '</div></div>';
}
function filmOpenConcept(kind, id) {
  var targetState = state.learn;
  targetState.screen = 'encyclopedia'; targetState.loadingSection = 'footballEncyclopedia'; targetState.loadError = null; renderAll();
  var pending = learnSectionById('footballEncyclopedia').dataFiles.filter(function(f) { return !loadedScripts[f]; });
  Promise.all(pending.map(loadScript)).then(function() {
    refreshDataAliases();
    if (state.learn !== targetState || state.screen !== 'learn') return;
    targetState.loadingSection = null; openEncyclopediaConcept(kind, id);
  }).catch(function() { if (state.learn === targetState) { targetState.loadingSection = null; targetState.loadError = 'footballEncyclopedia'; renderAll(); } });
}
function learnSectionCardHtml(s) {
  var shortDesc = { footballEncyclopedia: 'An interactive playbook for positions, formations, coverages, routes, and schemes.', coverageClassroom: 'Read the defense, break down assignments, and test yourself with guided reps.', xsoAlmanac: '700 scheme and strategy facts. Make your read, then reveal the answer.' };
  return '<button class="mode-card" data-learn-open="' + s.id + '">' +
    '<div class="mode-icon">' + (s.image ? '<img src="' + esc(s.image) + '" alt="" />' : icon(s.icon)) + '</div>' +
    '<div class="mode-title">' + esc(s.title) + '</div>' +
    '<div class="mode-desc">' + esc(shortDesc[s.id] || s.desc) + '</div>' + '<span class="film-card-action">Open session →</span>' +
    '</button>';
}
function renderLearnMenu() { return filmDashboard(); }
function renderLearnSectionDetail() {
  var s = learnSectionById(state.learn.sectionId);
  if (!s) return renderLearnMenu();
  var body =
    s.id === 'cfbHeisman' ? renderLearnCfbHeisman() :
    s.id === 'cfbMultiAA' ? renderLearnCfbMultiAA() :
    s.id === 'cfbNatChamp' ? renderLearnCfbNatChamp() :
    s.id === 'cfbAwards' ? renderLearnCfbAwards() :
    s.id === 'nflHof' ? renderLearnNflHof() :
    s.id === 'nflDecorated' ? renderLearnNflDecorated() :
    s.id === 'cfbTrivia' ? renderLearnCfbTrivia() :
    s.id === 'nflTrivia' ? renderLearnNflTrivia() :
    s.id === 'xsoAlmanac' ? renderLearnXso() : '';
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">' + esc(s.title) + '</h2>' +
    '<input id="learn-filter-input" class="learn-filter-input" placeholder="Filter by name, school, or team…" value="' + esc(state.learn.filter) + '" />' +
    learnCategoryChips(learnSectionCategories(s.id), state.learn.category) +
    body +
    '</div>';
}
function renderLearnScreen() { return '<div class="film-room">' + renderLearnScreenBody() + '</div>'; }
function renderLearnScreenBody() {
  if (!state.learn) state.learn = { screen: 'menu', sectionId: null, filter: '', category: '', loadingSection: null, loadError: null };
  var s = state.learn;
  if (s.loadingSection) {
    var section = learnSectionById(s.loadingSection);
    return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading ' + esc(section ? section.title : 'section') + '…</div></div>';
  }
  if (s.loadError) {
    return '<div class="panel"><div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' Back</button></div>' +
      '<p class="mode-desc">Couldn’t load this section. Check your connection and try again.</p><button class="btn-primary" data-film-retry>Try again</button></div>';
  }
  if (s.screen === 'study') return renderFilmStudy();
  if (s.screen === 'saved') return renderFilmSaved();
  if (s.screen === 'classroom') return renderClassroomScreen();
  if (s.screen === 'encyclopedia') return renderEncyclopediaScreen();
  return s.screen === 'section' ? renderLearnSectionDetail() : renderLearnMenu();
}
function learnBackToMenu() {
  state.learn = { screen: 'menu', sectionId: null, filter: '', category: '', loadingSection: null, loadError: null };
  state.classroom = null;
  state.encyclopedia = null;
  renderAll();
}
function openLearnSection(id) {
  var s = state.learn, section = learnSectionById(id);
  if (!section) return;
  var notebook = filmNotebook(); notebook.last = { section: id, label: section.title }; filmSaveNotebook(notebook);
  var isClassroom = id === 'coverageClassroom';
  var isEncyclopedia = id === 'footballEncyclopedia';
  var pending = section.dataFiles.filter(function (f) { return !loadedScripts[f]; });
  if (pending.length) {
    s.loadingSection = id;
    s.loadError = null;
    renderAll();
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      s.loadingSection = null;
      if (isClassroom) { s.screen = 'classroom'; }
      else if (isEncyclopedia) { s.screen = 'encyclopedia'; }
      else { s.screen = 'section'; s.sectionId = id; s.filter = ''; s.category = ''; }
      renderAll();
    }).catch(function () {
      s.loadingSection = null;
      s.loadError = id;
      renderAll();
    });
    return;
  }
  if (isClassroom) { s.screen = 'classroom'; renderAll(); return; }
  if (isEncyclopedia) { s.screen = 'encyclopedia'; renderAll(); return; }
  s.screen = 'section';
  s.sectionId = id;
  s.filter = '';
  s.category = '';
  renderAll();
}

/* ============================== Football Learning Engine ==============
   Defensive Coverages classroom -- a real curriculum (lessons with real
   prerequisites, structured concept content, interactive reps, and local
   mastery tracking) layered on top of the LEARN_COVERAGES data file. This
   is deliberately a SEPARATE state namespace (state.classroom) from the
   simple filter/category browsing state.learn already uses -- a lesson's
   step/exercise progression is meaningfully more complex than "filter a
   table," and keeping them apart avoids overloading that simple shape.
   Still nested under the same top-level Learn screen (state.screen ===
   'learn') so exit/navigation patterns stay consistent with the rest of
   the app. No server-side account system exists in this app (every other
   stat/progress feature is local-profile-based, keyed by slugify(state.name)
   — dailyKey() is the existing precedent) -- mastery/progress here follows
   that exact same convention rather than inventing a server-side one. */
function classroomMasteryKey() { return 'nflTriviaClassroomMastery__' + slugify(state.name); }
function classroomProgressKey() { return 'nflTriviaClassroomProgress__' + slugify(state.name); }
function getClassroomMastery() { return lsGet(classroomMasteryKey(), {}); }
function getClassroomProgress() { return lsGet(classroomProgressKey(), {}); }
function recordClassroomAttempt(conceptId, correct) {
  if (!state.name) return; // no local profile yet -- nothing to attribute progress to
  var m = getClassroomMastery();
  var rec = m[conceptId] || { attempts: 0, correct: 0 };
  rec.attempts++;
  if (correct) rec.correct++;
  rec.lastPracticed = Date.now();
  m[conceptId] = rec;
  lsSet(classroomMasteryKey(), m);
}
// Thresholds are a simple, disclosed heuristic (not a claim of pedagogical
// research) -- "not_started" (0 attempts), "learning" (<3 attempts, or
// <60% correct), "practicing" (60-84%), "mastered" (85%+ across 3+ reps).
function classroomMasteryLevel(conceptId) {
  var m = getClassroomMastery()[conceptId];
  if (!m || !m.attempts) return 'not_started';
  if (m.attempts < 3) return 'learning';
  var pct = m.correct / m.attempts;
  if (pct >= 0.85) return 'mastered';
  if (pct >= 0.6) return 'practicing';
  return 'learning';
}
function classroomWeakConcepts() {
  var m = getClassroomMastery();
  return Object.keys(m).filter(function (id) { return classroomMasteryLevel(id) === 'learning'; });
}
function markClassroomLessonStarted(lessonId) {
  if (!state.name) return;
  var p = getClassroomProgress();
  p[lessonId] = p[lessonId] || {};
  p[lessonId].started = true;
  lsSet(classroomProgressKey(), p);
}
function markClassroomLessonCompleted(lessonId) {
  if (!state.name) return;
  var p = getClassroomProgress();
  p[lessonId] = p[lessonId] || {};
  p[lessonId].started = true;
  p[lessonId].completed = true;
  p[lessonId].stepIndex = 0;
  lsSet(classroomProgressKey(), p);
}
function classroomLessons() { return (LEARN_COVERAGES && LEARN_COVERAGES.lessons) || []; }
function classroomLessonById(id) { return classroomLessons().find(function (l) { return l.lesson_id === id; }); }
function classroomConcept(id) { return LEARN_COVERAGES && LEARN_COVERAGES.concepts[id]; }
function classroomExercise(id) { return LEARN_COVERAGES && LEARN_COVERAGES.exercises[id]; }
function classroomLessonUnlocked(lesson) {
  var p = getClassroomProgress();
  return lesson.prerequisites.every(function (id) { return p[id] && p[id].completed; });
}

function startClassroomLesson(lessonId) {
  var lesson = classroomLessonById(lessonId);
  if (!lesson || !classroomLessonUnlocked(lesson)) return;
  markClassroomLessonStarted(lessonId);
  state.classroom = {
    screen: 'lesson', lessonId: lessonId, stepIndex: Math.min((getClassroomProgress()[lessonId] || {}).stepIndex || 0, lesson.steps.length - 1),
    exerciseQueue: [], exerciseIndex: 0, answeredIndex: null,
    practiceMode: false, practiceResults: { correct: 0, total: 0 },
  };
  classroomEnterStep();
  renderAll();
}
function classroomEnterStep() {
  var s = state.classroom, lesson = classroomLessonById(s.lessonId), step = lesson.steps[s.stepIndex];
  if (step.step_type === 'interactive_rep' || step.step_type === 'check_understanding') {
    s.exerciseQueue = step.exercise_ids.slice();
    s.exerciseIndex = 0;
    s.answeredIndex = null;
  }
}
function classroomNextStep() {
  var s = state.classroom, lesson = classroomLessonById(s.lessonId);
  if (s.stepIndex + 1 >= lesson.steps.length) {
    markClassroomLessonCompleted(s.lessonId);
    s.screen = 'path';
    s.justCompleted = s.lessonId;
    renderAll();
    return;
  }
  s.stepIndex++;
  if (state.name) { var p = getClassroomProgress(); p[s.lessonId] = p[s.lessonId] || {}; p[s.lessonId].stepIndex = s.stepIndex; lsSet(classroomProgressKey(), p); }
  classroomEnterStep();
  renderAll();
}
function classroomPrevStep() {
  var s = state.classroom;
  if (s.stepIndex <= 0) { s.screen = 'path'; renderAll(); return; }
  s.stepIndex--;
  classroomEnterStep();
  renderAll();
}
function startClassroomPractice(lessonId) {
  var lesson = classroomLessonById(lessonId);
  if (!lesson) return;
  var exIds = [];
  lesson.steps.forEach(function (st) { if (st.exercise_ids) exIds = exIds.concat(st.exercise_ids); });
  state.classroom = {
    screen: 'practice', lessonId: lessonId, stepIndex: -1,
    exerciseQueue: shuffle(exIds), exerciseIndex: 0, answeredIndex: null,
    practiceMode: true, practiceResults: { correct: 0, total: 0 },
  };
  renderAll();
}
function classroomAnswerExercise(idx) {
  var s = state.classroom;
  if (s.answeredIndex !== null) return;
  var ex = classroomExercise(s.exerciseQueue[s.exerciseIndex]);
  var correct = idx === ex.correctIndex;
  s.answeredIndex = idx;
  recordClassroomAttempt(ex.concept, correct);
  filmRecordRep(correct,{category:(classroomConcept(ex.concept)&&classroomConcept(ex.concept).label)||'Coverage',question:ex.prompt,options:ex.options,correctIndex:ex.correctIndex,notes:ex.explanation});
  if (s.practiceMode) {
    s.practiceResults.total++;
    if (correct) s.practiceResults.correct++;
  }
  playSound(correct ? 'correct' : 'wrong');
  renderAll();
}
function classroomExerciseNext() {
  var s = state.classroom;
  s.exerciseIndex++;
  s.answeredIndex = null;
  if (s.exerciseIndex >= s.exerciseQueue.length) {
    if (s.practiceMode) { s.screen = 'practiceResult'; renderAll(); return; }
    classroomNextStep();
    return;
  }
  renderAll();
}
function classroomExitToLearnMenu() {
  state.classroom = null;
  state.learn.screen = 'menu';
  renderAll();
}
function classroomBackToPath() {
  state.classroom.screen = 'path';
  renderAll();
}

// Reusable structured diagram renderer (Learn Engine section 6) -- a
// simplified schematic (labeled boxes on a bounded field rectangle), not a
// fully illustrated play diagram. `align` values map to fixed percentage
// positions; unrecognized aligns fall back to a center default rather than
// erroring, so a future concept with a new alignment degrades gracefully.
var CLASSROOM_ALIGN_POS = {
  outside_left: { x: 8, y: 22 }, outside_right: { x: 92, y: 22 },
  middle: { x: 50, y: 10 }, underneath: { x: 50, y: 60 },
  left_half: { x: 25, y: 10 }, right_half: { x: 75, y: 10 },
  left_middle: { x: 38, y: 10 }, right_middle: { x: 62, y: 10 },
  quarters_side_outside: { x: 8, y: 10 }, quarters_side_middle: { x: 30, y: 10 },
  half_side_middle: { x: 70, y: 10 }, half_side_outside: { x: 92, y: 24 },
};
function renderCoverageDiagram(spec) {
  if (!spec || !spec.defenders || !spec.defenders.length) return '';
  var dots = spec.defenders.map(function (d) {
    var pos = CLASSROOM_ALIGN_POS[d.align] || { x: 50, y: 30 };
    var depthCls = (d.depth === 'deep' || d.depth === 'deep_late') ? 'diagram-depth-deep' :
      (d.depth === 'line' ? 'diagram-depth-line' : 'diagram-depth-underneath');
    return '<button type="button" class="diagram-defender ' + depthCls + '" style="left:' + pos.x + '%; top:' + pos.y + '%;" ' +
      'data-film-assignment="' + esc(d.assignment || '') + '" title="' + esc(d.assignment || '') + '">' + esc(d.role) + '</button>';
  }).join('');
  return '<div class="coverage-diagram"><div class="diagram-los"><span>Line of scrimmage</span></div>' + dots + '</div><p class="mode-desc">Tap a defender to see the assignment.</p><div class="film-assignment-note" role="status" hidden></div>';
}

function classroomMasteryBadgeHtml(conceptId) {
  var level = classroomMasteryLevel(conceptId);
  if (level === 'not_started') return '';
  var label = level === 'mastered' ? 'Mastered' : level === 'practicing' ? 'Practicing' : 'Learning';
  return '<span class="classroom-mastery-badge classroom-mastery-' + level + '">' + label + '</span>';
}
function renderClassroomPath() {
  var lessons = classroomLessons(), progress = getClassroomProgress();
  var weak = classroomWeakConcepts();
  var rows = lessons.map(function (l) {
    var unlocked = classroomLessonUnlocked(l);
    var st = progress[l.lesson_id] || {};
    var actionLabel = st.completed ? 'Review' : (st.started ? 'Continue' : 'Start');
    return '<div class="classroom-lesson-row' + (unlocked ? '' : ' classroom-locked') + '">' +
      '<div class="classroom-lesson-info">' +
        '<div class="classroom-lesson-title">' + esc(l.title) + classroomMasteryBadgeHtml(l.concept) + '</div>' +
        '<div class="classroom-lesson-summary">' + esc(l.summary) + '</div>' +
      '</div>' +
      (unlocked ?
        '<div class="classroom-lesson-actions">' +
          '<button class="btn-secondary btn-tiny" data-classroom-lesson="' + l.lesson_id + '">' + actionLabel + '</button>' +
          (st.completed ? '<button class="btn-tiny" data-classroom-practice="' + l.lesson_id + '">Practice</button>' : '') +
        '</div>'
      : '<div class="classroom-lesson-actions"><span class="classroom-lock-note">Complete prior lessons first</span></div>') +
      '</div>';
  }).join('');
  var weakNote = weak.length ?
    '<p class="mode-desc classroom-weak-note">You’re still learning: ' +
    weak.map(function (id) { var c = classroomConcept(id); return c ? esc(c.label) : id; }).join(', ') +
    '. Practice a completed lesson above to reinforce it.</p>' : '';
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-classroom-exit>' + icon('close') + ' ← Film Room</button></div>' +
    '<h2 class="panel-title">Defensive Coverages</h2>' +
    '<p class="mode-desc">Learn to read a defense, one coverage at a time. Each lesson teaches a real concept, shows you what it looks like, and checks your understanding with real reps.</p>' +
    (state.classroom && state.classroom.justCompleted ? '<div class="film-milestone film-milestone-small" role="status"><span class="film-eyebrow">LESSON COMPLETE</span><h3>' + esc(classroomLessonById(state.classroom.justCompleted).title) + '</h3><p>Keep going, or put this coverage to the test with practice reps.</p></div>' : '') +
    filmMeter(Object.keys(progress).filter(function(id) { return progress[id].completed; }).length, lessons.length, 'Your coverage path') + weakNote +
    '<div class="classroom-lesson-list">' + rows + '</div>' +
    '</div>';
}
function classroomStepLabel(type) {
  return { teach: 'Teach', show: 'Show', explain: 'Explain', interactive_rep: 'Interactive Rep',
    check_understanding: 'Check Understanding', apply: 'Apply' }[type] || type;
}
function renderClassroomExercise(ex, answeredIndex) {
  var answered = answeredIndex !== null;
  return (ex.structured && ex.structured.defenders ? renderCoverageDiagram(ex.structured) : '') +
    '<div class="quiz-question">' + esc(ex.prompt) + '</div>' +
    '<div class="quiz-options">' +
    ex.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === ex.correctIndex) cls += ' correct';
        else if (i === answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-classroom-answer="' + i + '"') + '>' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered ?
      '<div class="quiz-feedback" aria-live="polite">' +
        (answeredIndex === ex.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Good read.</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Coach’s correction: ' + esc(ex.options[ex.correctIndex]) + '.</span>') +
        ' ' + esc(ex.explanation) +
      '</div>' +
      '<button class="btn-primary" data-classroom-exercise-next>Next</button>'
    : '');
}
function renderClassroomStepContent(step) {
  if (step.step_type === 'show') {
    return '<div class="classroom-step-text">' + esc(step.content) + '</div>' +
      (step.diagram_spec ? renderCoverageDiagram(step.diagram_spec) : '');
  }
  return '<div class="classroom-step-text">' + esc(step.content) + '</div>';
}
function renderClassroomLesson() {
  var s = state.classroom, lesson = classroomLessonById(s.lessonId);
  if (!lesson) { s.screen = 'path'; return renderClassroomPath(); }
  var step = lesson.steps[s.stepIndex];
  var isExerciseStep = step.step_type === 'interactive_rep' || step.step_type === 'check_understanding';
  var body;
  if (isExerciseStep) {
    var ex = classroomExercise(s.exerciseQueue[s.exerciseIndex]);
    body = '<div class="quiz-progress">Rep ' + (s.exerciseIndex + 1) + ' of ' + s.exerciseQueue.length + '</div>' +
      renderClassroomExercise(ex, s.answeredIndex);
  } else {
    body = renderClassroomStepContent(step) +
      '<div class="btn-row">' +
      (s.stepIndex > 0 ? '<button class="btn-secondary" data-classroom-step-back>Back</button>' : '') +
      '<button class="btn-primary" data-classroom-step-next>' + (s.stepIndex + 1 >= lesson.steps.length ? 'Finish Lesson' : 'Next') + '</button>' +
      '</div>';
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-classroom-path>' + icon('close') + ' Back to Path</button></div>' +
    '<h2 class="panel-title">' + esc(lesson.title) + '</h2>' +
    filmMeter(s.stepIndex + 1, lesson.steps.length, 'Lesson progress') + '<div class="classroom-step-pill">' + classroomStepLabel(step.step_type) + ' · Step ' + (s.stepIndex + 1) + ' of ' + lesson.steps.length + '</div>' +
    body +
    '</div>';
}
function renderClassroomPractice() {
  var s = state.classroom;
  if (s.screen === 'practiceResult') {
    var r = s.practiceResults, pct = r.total ? Math.round(100 * r.correct / r.total) : 0;
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-classroom-path>' + icon('close') + ' Back to Path</button></div>' +
      '<div class="film-milestone"><span class="film-eyebrow">PRACTICE COMPLETE</span><strong>' + pct + '<small>%</small></strong><h2>Trust your reads.</h2></div>' +
      '<p class="mode-desc">' + r.correct + ' / ' + r.total + ' correct (' + pct + '%).</p>' +
      '<button class="btn-primary" data-classroom-path>Back to Path</button>' +
      '</div>';
  }
  var lesson = classroomLessonById(s.lessonId);
  var ex = classroomExercise(s.exerciseQueue[s.exerciseIndex]);
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-classroom-path>' + icon('close') + ' Back to Path</button></div>' +
    '<h2 class="panel-title">Practice: ' + esc(lesson ? lesson.title : '') + '</h2>' +
    '<div class="quiz-progress">Rep ' + (s.exerciseIndex + 1) + ' of ' + s.exerciseQueue.length + '</div>' +
    renderClassroomExercise(ex, s.answeredIndex) +
    '</div>';
}
function renderClassroomScreen() {
  if (!state.classroom) state.classroom = {
    screen: 'path', lessonId: null, stepIndex: 0, exerciseQueue: [], exerciseIndex: 0,
    answeredIndex: null, practiceMode: false, practiceResults: { correct: 0, total: 0 },
  };
  var s = state.classroom;
  if (s.screen === 'lesson') return renderClassroomLesson();
  if (s.screen === 'practice' || s.screen === 'practiceResult') return renderClassroomPractice();
  return renderClassroomPath();
}

/* ============================== Football Encyclopedia ==================
   Browse-first (search -> domain -> concept), covering every domain
   LEARN_ENCYCLOPEDIA.domains lists -- see tools/learn/build_encyclopedia_
   module.py for the full ingestion/merge/provenance discipline behind this
   data. Deliberately NOT quiz/lesson-first: every concept is readable with
   no interactive gate (mission's explicit "browse -> search -> open
   concept -> read explanation -> explore related concepts, without being
   forced into a test"). The existing Coverage Classroom (state.classroom
   above) remains the separate, hands-on lesson experience for that one
   topic -- a COVERAGES-domain concept page here links into it rather than
   duplicating its lesson content. */
function encyclopediaAllConcepts() {
  return (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.concepts) || {};
}
function encyclopediaDomains() {
  var domains = (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.domains) || [];
  return domains.slice().sort(function (a, b) { return a.order - b.order; });
}
function encyclopediaConceptsForDomain(domainId) {
  var all = encyclopediaAllConcepts();
  var out = [];
  for (var id in all) { if (all[id].domain === domainId) out.push(all[id]); }
  out.sort(function (a, b) {
    var sa = a.subcategory || '', sb = b.subcategory || '';
    if (sa !== sb) return sa < sb ? -1 : 1;
    return (a.label || '').localeCompare(b.label || '');
  });
  return out;
}
function encyclopediaTeamProfilesForDomain(domainId) {
  var all = (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.team_scheme_profiles) || {};
  var out = [];
  for (var id in all) { if (all[id].domain === domainId) out.push(all[id]); }
  out.sort(function (a, b) { return (a.team || '').localeCompare(b.team || ''); });
  return out;
}
function encyclopediaHistoricalForDomain() {
  var all = (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.historical_records) || {};
  var out = [];
  for (var id in all) out.push(all[id]);
  out.sort(function (a, b) { return (b.season || 0) - (a.season || 0); });
  return out;
}
function encyclopediaDomainCount(domainId) {
  if (domainId === 'NFL_SCHEMES' || domainId === 'CFB_SCHEMES') return encyclopediaTeamProfilesForDomain(domainId).length;
  if (domainId === 'GREAT_UNITS') return encyclopediaHistoricalForDomain().length;
  return encyclopediaConceptsForDomain(domainId).length;
}
function encyclopediaConceptByCanonicalId(id) { return encyclopediaAllConcepts()[id]; }
function encyclopediaPrettyLabel(key) {
  return String(key).replace(/_/g, ' ').replace(/\b\w/g, function (ch) { return ch.toUpperCase(); });
}
function encyclopediaRelatedFor(canonicalId) {
  var rels = (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.relationships) || [];
  var out = [];
  rels.forEach(function (r) {
    if (r.source === canonicalId) out.push({ predicate: r.predicate, id: r.target, direction: 'out' });
    else if (r.target === canonicalId) out.push({ predicate: r.predicate, id: r.source, direction: 'in' });
  });
  return out;
}
var ENCYCLOPEDIA_SEARCH_LIMIT = 60;
// Section 15: the one real, verified gap in the existing substring search
// (checked directly against the live data, not assumed) -- "aka" aliases
// like Cover 4's ["Quarters"] were already reachable via the generic
// `for (k in c.fields)` loop below, so a query for "quarters" already
// worked. What did NOT work: the data only ever spells coverages as
// digits ("Cover 4"), never as words ("Cover Four") -- normalizing a
// leading number word after "cover " closes that specific gap without
// inventing a broader alias table for things that already matched.
var F101_NUMBER_WORDS = { one: '1', two: '2', three: '3', four: '4', five: '5', six: '6' };
function encyclopediaNormalizeQuery(q) {
  return q.replace(/\bcover\s+(one|two|three|four|five|six)\b/g, function (_, w) { return 'cover ' + F101_NUMBER_WORDS[w]; });
}
function encyclopediaSearch(query) {
  var q = encyclopediaNormalizeQuery((query || '').trim().toLowerCase());
  if (!q) return [];
  var results = [];
  var all = encyclopediaAllConcepts();
  for (var id in all) {
    var c = all[id];
    var hay = (c.label || '') + ' ' + (c.subcategory || '') + ' ' + (c.domain || '');
    if (c.fields) { for (var k in c.fields) hay += ' ' + c.fields[k]; }
    if (hay.toLowerCase().indexOf(q) !== -1) {
      results.push({ kind: 'concept', id: id, label: c.label, domain: c.domain, sub: c.subcategory });
      if (results.length >= ENCYCLOPEDIA_SEARCH_LIMIT) return results;
    }
  }
  var teams = (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.team_scheme_profiles) || {};
  for (var tid in teams) {
    var t = teams[tid];
    if ((t.label || '').toLowerCase().indexOf(q) !== -1) {
      results.push({ kind: 'team', id: tid, label: t.label, domain: t.domain, sub: t.league });
      if (results.length >= ENCYCLOPEDIA_SEARCH_LIMIT) return results;
    }
  }
  return results;
}

// Football 101 Interactive Redesign, Section 4/5: looks a canonical_id up
// across every diagram category. Returns {diagram, category} or null --
// concept pages with no matching diagram fall back to the original
// text-only rendering untouched (Section 21: never damage existing
// content that has nothing to visualize).
var F101_DIAGRAM_CATEGORY_KEYS = { formations: 'formation', fronts: 'front', coverages: 'coverage', passConcepts: 'pass_concept', runConcepts: 'run_concept' };
function f101DiagramFor(canonicalId) {
  if (!FOOTBALL_DIAGRAMS || !canonicalId) return null;
  for (var key in F101_DIAGRAM_CATEGORY_KEYS) {
    var bucket = FOOTBALL_DIAGRAMS[key];
    if (bucket && bucket[canonicalId]) return { diagram: bucket[canonicalId], category: F101_DIAGRAM_CATEGORY_KEYS[key], bucketKey: key };
  }
  // Encyclopedia Diagrams + Deep Dives pass: a real, curated "closest
  // matching diagram" for a named variant with no diagram of its own (e.g.
  // Cover 3 Cloud -> the base Cover 3 diagram) -- see data/encyclopedia-
  // deep-dives.js's own module comment. Flagged isVariant so the render
  // side shows an honest "closest related diagram" caveat instead of
  // implying an exact match, and skips Test Me (which would generate
  // questions against the base diagram's own canonical_id, not this one).
  var dive = ENCYCLOPEDIA_DEEP_DIVES && ENCYCLOPEDIA_DEEP_DIVES[canonicalId];
  if (dive && dive.diagramOverride) {
    for (var key2 in F101_DIAGRAM_CATEGORY_KEYS) {
      var bucket2 = FOOTBALL_DIAGRAMS[key2];
      if (bucket2 && bucket2[dive.diagramOverride]) {
        return { diagram: bucket2[dive.diagramOverride], category: F101_DIAGRAM_CATEGORY_KEYS[key2], bucketKey: key2, isVariant: true };
      }
    }
  }
  return null;
}
function f101DefaultDiagramView() {
  return { showResponsibilities: false, showRoutes: false, showBlocks: false, showCoverage: false, showWeakness: false, activePlayerId: null };
}
function f101QuickSummary(node, diagram) {
  var fields = node.fields || {};
  return fields.summary || fields.what_to_identify || fields.core_responsibilities || diagram.notes || diagram.description || '';
}

function openEncyclopediaDomain(domainId) {
  state.encyclopedia = state.encyclopedia || {};
  state.encyclopedia.screen = 'domain';
  state.encyclopedia.domainId = domainId;
  state.encyclopedia.conceptId = null;
  renderAll();
}
function openEncyclopediaConcept(kind, id) {
  state.encyclopedia = state.encyclopedia || {};
  state.encyclopedia.screen = 'concept';
  state.encyclopedia.conceptKind = kind;
  state.encyclopedia.conceptId = id;
  var n = filmNotebook(), key = kind + ':' + id;
  var node = kind === 'concept' ? encyclopediaConceptByCanonicalId(id) : kind === 'team' ? (LEARN_ENCYCLOPEDIA.team_scheme_profiles || {})[id] : (LEARN_ENCYCLOPEDIA.historical_records || {})[id];
  n.viewed[key] = Date.now(); n.last = { section: 'footballEncyclopedia', kind: kind, id: id, label: node ? node.label : id }; filmSaveNotebook(n);
  state.encyclopedia.diagramView = f101DefaultDiagramView();
  state.encyclopedia.readMode = 'quick';
  state.f101Quiz = { active: false };
  renderAll();
}
function encyclopediaBackToDomains() {
  state.encyclopedia = { screen: 'domains', domainId: null, conceptId: null, filter: state.encyclopedia ? state.encyclopedia.filter : '' };
  renderAll();
}
function encyclopediaBackToDomain() {
  state.encyclopedia.screen = 'domain';
  state.encyclopedia.conceptId = null;
  renderAll();
}

// Football 101 Interactive Redesign, Section 2: a visual, grouped landing
// page instead of one flat 29-row domain list. Every domain id below is
// real (LEARN_ENCYCLOPEDIA.domains) and every one of the 29 appears in
// exactly one group -- this groups the SAME real data into the redesign
// brief's recommended category shape rather than inventing new categories
// or dropping any domain (Section 21: never remove valid content).
var F101_CATEGORY_GROUPS = [
  { label: 'Start Here', icon: 'graduationCap', domains: ['FOOTBALL_101', 'RULES'] },
  { label: 'Positions', icon: 'users', domains: ['POSITIONS', 'PERSONNEL'] },
  { label: 'Offense', icon: 'football', domains: ['OFFENSIVE_SYSTEMS', 'QB_PLAY'] },
  { label: 'Formations', icon: 'grid', domains: ['FORMATIONS'] },
  { label: 'Run Concepts', icon: 'flame', domains: ['RUN_GAME', 'BLOCKING'] },
  { label: 'Pass Concepts', icon: 'versus', domains: ['PASSING_CONCEPTS', 'ROUTE_TREE', 'PASS_PROTECTION'] },
  { label: 'Defense', icon: 'shield', domains: ['DEFENSIVE_PHILOSOPHY', 'DEFENSIVE_PERSONNEL', 'DEFENSIVE_FRONTS', 'RUN_FITS'] },
  { label: 'Coverages', icon: 'target', domains: ['COVERAGES'] },
  { label: 'Blitzes / Pressures', icon: 'zap', domains: ['PRESSURES'] },
  { label: 'Reading the Game', icon: 'search', domains: ['GEOMETRY', 'FILM_STUDY', 'SCOUTING'] },
  { label: 'NFL & College Schemes', icon: 'trophy', domains: ['NFL_SCHEMES', 'CFB_SCHEMES', 'GREAT_UNITS'] },
  { label: 'Terminology & Play Calling', icon: 'book', domains: ['PLAY_CALLING'] },
  { label: 'Strategy & Situational', icon: 'barChart', domains: ['SITUATIONAL', 'COACHING', 'SPECIAL_TEAMS'] },
  { label: 'Football History', icon: 'star', domains: ['HISTORY'] },
];

function renderEncyclopediaSearchBox() {
  var val = (state.encyclopedia && state.encyclopedia.filter) || '';
  return '<input id="encyclopedia-search-input" class="learn-filter-input" placeholder="Search concepts, terms, teams…" value="' + esc(val) + '" />';
}

function renderEncyclopediaDomains() {
  var filter = (state.encyclopedia && state.encyclopedia.filter) || '';
  if (filter.trim()) {
    var results = encyclopediaSearch(filter);
    var rows = results.map(function (r) {
      return '<button class="encyc-row" data-encyc-open="' + r.kind + ':' + esc(r.id) + '">' +
        '<span class="encyc-row-label">' + esc(r.label) + '</span>' +
        '<span class="encyc-row-meta">' + esc(encyclopediaPrettyLabel(r.domain || '')) + (r.sub ? ' · ' + esc(r.sub) : '') + '</span>' +
        '</button>';
    }).join('');
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' ← Film Room</button></div>' +
      '<h2 class="panel-title">Football Encyclopedia</h2>' +
      renderEncyclopediaSearchBox() +
      '<div class="encyc-results">' + (rows || '<p class="mode-desc">No matches. Try a different term.</p>') + '</div>' +
      '</div>';
  }
  var domains = encyclopediaDomains();
  var byId = {};
  domains.forEach(function (d) { byId[d.id] = d; });
  var groupsHtml = F101_CATEGORY_GROUPS.map(function (group) {
    var totalCount = group.domains.reduce(function (sum, id) { return sum + encyclopediaDomainCount(id); }, 0);
    if (totalCount === 0) return '';
    var cardsHtml = group.domains.map(function (id) {
      var d = byId[id];
      var count = encyclopediaDomainCount(id);
      if (!d || count === 0) return '';
      return '<button class="f101-cat-card" data-encyc-domain="' + id + '">' +
        '<span class="f101-cat-icon">' + icon(group.icon) + '</span>' +
        '<span class="f101-cat-label">' + esc(d.label) + '</span>' +
        '<span class="f101-cat-count">' + count + '</span>' +
        '</button>';
    }).join('');
    return '<div class="f101-cat-group">' +
      '<div class="f101-cat-group-label">' + icon(group.icon) + ' ' + esc(group.label) + '</div>' +
      '<div class="f101-cat-grid">' + cardsHtml + '</div>' +
      '</div>';
  }).join('');
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' ← Film Room</button></div>' +
    '<h2 class="panel-title">Football 101</h2>' +
    '<p class="mode-desc">Learn any concept: what it is, see it on the field, how it works, and test yourself -- browse by topic or search for anything by name.</p>' +
    renderEncyclopediaSearchBox() +
    '<div class="f101-cat-groups">' + groupsHtml + '</div>' +
    '</div>';
}

function renderEncyclopediaDomainDetail() {
  var domainId = state.encyclopedia.domainId;
  var domain = encyclopediaDomains().find(function (d) { return d.id === domainId; });
  var title = domain ? domain.label : domainId;
  var body;
  if (domainId === 'NFL_SCHEMES' || domainId === 'CFB_SCHEMES') {
    var teams = encyclopediaTeamProfilesForDomain(domainId);
    body = '<div class="encyc-caution">' + icon('flag') +
      ' These team scheme profiles are coaching-lineage and prior-film PROJECTIONS, not confirmed current-season film evidence -- see each profile for the exact caveat.</div>' +
      '<div class="encyc-row-list">' + teams.map(function (t) {
        return '<button class="encyc-row" data-encyc-open="team:' + esc(t.canonical_id) + '">' +
          '<span class="encyc-row-label">' + esc(t.team) + '</span><span class="encyc-row-meta">' + esc(String(t.season)) + '</span></button>';
      }).join('') + '</div>';
  } else if (domainId === 'GREAT_UNITS') {
    var records = encyclopediaHistoricalForDomain();
    body = '<div class="encyc-row-list">' + records.map(function (r) {
      return '<button class="encyc-row" data-encyc-open="hist:' + esc(r.canonical_id) + '">' +
        '<span class="encyc-row-label">' + esc(r.label) + '</span>' +
        '<span class="encyc-row-meta">' + esc(r.league) + ' ' + esc(r.side) + '</span></button>';
    }).join('') + '</div>';
  } else {
    var concepts = encyclopediaConceptsForDomain(domainId);
    var bySub = {}, order = [];
    concepts.forEach(function (c) {
      var sub = c.subcategory || 'General';
      if (!bySub[sub]) { bySub[sub] = []; order.push(sub); }
      bySub[sub].push(c);
    });
    body = order.map(function (sub) {
      return '<div class="encyc-subcategory-label">' + esc(sub) + '</div>' +
        '<div class="encyc-row-list">' + bySub[sub].map(function (c) {
          return '<button class="encyc-row" data-encyc-open="concept:' + esc(c.canonical_id) + '">' +
            '<span class="encyc-row-label">' + esc(c.label) + '</span></button>';
        }).join('') + '</div>';
    }).join('');
    // Real bug found in visual QA: diagram-only formations (currently just
    // Wing-T) had a real diagram and a real detail-page fallback (see
    // renderEncyclopediaConceptDetail()) but were never listed ANYWHERE,
    // making them unreachable through normal navigation. Listed here,
    // clearly separated, never mixed into the source-verified rows above.
    if (FOOTBALL_DIAGRAMS && FOOTBALL_DIAGRAMS.formations && domainId === 'FORMATIONS') {
      var diagramOnly = Object.keys(FOOTBALL_DIAGRAMS.formations)
        .map(function (k) { return FOOTBALL_DIAGRAMS.formations[k]; })
        .filter(function (d) { return d.verified === false; });
      if (diagramOnly.length) {
        body += '<div class="encyc-subcategory-label">Diagram References</div>' +
          '<div class="encyc-row-list">' + diagramOnly.map(function (d) {
            return '<button class="encyc-row" data-encyc-open="concept:' + esc(d.id) + '">' +
              '<span class="encyc-row-label">' + esc(d.display_name) + '</span></button>';
          }).join('') + '</div>';
      }
    }
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-encyc-domains>' + icon('close') + ' All Domains</button></div>' +
    '<h2 class="panel-title">' + esc(title) + '</h2>' +
    body +
    '</div>';
}

function renderEncyclopediaFieldsList(fields) {
  if (!fields) return '';
  var keys = Object.keys(fields);
  if (!keys.length) return '';
  return '<dl class="encyc-fields">' + keys.map(function (k) {
    var v = fields[k];
    var text = Array.isArray(v) ? v.join('; ') : String(v);
    return '<dt>' + esc(encyclopediaPrettyLabel(k)) + '</dt><dd>' + esc(text) + '</dd>';
  }).join('') + '</dl>';
}

// Football 101 Interactive Redesign, Sections 3/4/9/12: the "See It" block
// -- reusable SVG diagram, progressive-disclosure toggle chips (only shown
// when the diagram actually has that kind of data -- Show Routes never
// appears on a front/formation with no routes), and the click/tap player
// panel. All toggle state lives on state.encyclopedia.diagramView so it
// persists across a re-render but resets whenever a new concept opens
// (see openEncyclopediaConcept()).
function renderF101DiagramBlock(diagram, category, variantNote) {
  var dv = state.encyclopedia.diagramView || f101DefaultDiagramView();
  var chips = [];
  chips.push({ key: 'showResponsibilities', label: 'Show Responsibilities' });
  if (diagram.routes && diagram.routes.length) chips.push({ key: 'showRoutes', label: 'Show Routes' });
  if (diagram.blocks && diagram.blocks.length) chips.push({ key: 'showBlocks', label: 'Show Blocking' });
  if (diagram.zones && diagram.zones.length) chips.push({ key: 'showCoverage', label: 'Show Coverage' });
  if (diagram.weaknesses || diagram.weakness) chips.push({ key: 'showWeakness', label: 'Show Weakness' });
  var chipsHtml = chips.map(function (c) {
    return '<button class="chip-toggle' + (dv[c.key] ? ' active' : '') + '" data-f101-toggle="' + c.key + '">' + esc(c.label) + '</button>';
  }).join('') + '<button class="chip-toggle" data-f101-reset>Reset Diagram</button>';

  var svg = FootballField ? FootballField.renderDiagramSVG(diagram, dv) : '';
  var weaknessText = dv.showWeakness ? (diagram.weaknesses || diagram.weakness) : '';
  var weaknessHtml = weaknessText ? '<div class="f101-weakness-callout">' + icon('flag') + ' ' + esc(weaknessText) + '</div>' : '';

  var panelHtml = '';
  if (dv.activePlayerId && FootballField) {
    var info = FootballField.describePlayer(diagram, dv.activePlayerId, (LEARN_ENCYCLOPEDIA && LEARN_ENCYCLOPEDIA.concepts) || {});
    if (info) {
      panelHtml = '<div class="f101-player-panel">' +
        '<div class="f101-player-panel-head">' + esc(info.role) + '<button class="btn-tiny" data-f101-player-close>' + icon('close') + '</button></div>' +
        (info.assignment ? '<p class="f101-player-panel-line"><strong>Here:</strong> ' + esc(info.assignment) + '</p>' : '') +
        (info.coreResponsibilities ? '<p class="f101-player-panel-line"><strong>Core responsibility:</strong> ' + esc(info.coreResponsibilities) + '</p>' : '') +
        (info.evaluationTraits ? '<p class="f101-player-panel-line"><strong>What matters:</strong> ' + esc(info.evaluationTraits) + '</p>' : '') +
        '</div>';
    }
  }

  var accessibleDesc = '<p class="f101-svg-alt-text">' + esc(diagram.description || '') + '</p>';

  return '<div class="f101-see-it">' +
    '<div class="f101-see-it-label">On the chalkboard</div><p class="mode-desc">Tap a player to inspect the assignment. Toggle routes, coverage, and responsibilities to break down the play.</p>' +
    '<div class="chip-row">' + chipsHtml + '</div>' +
    '<div class="f101-field-wrap">' + svg + '</div>' +
    accessibleDesc +
    weaknessHtml +
    panelHtml +
    (diagram.verified === false ? '<div class="encyc-caution">' + icon('flag') + ' Diagram reference -- not yet a source-verified encyclopedia entry.</div>' : '') +
    (diagram.variation_note ? '<p class="mode-desc">' + esc(diagram.variation_note) + '</p>' : '') +
    (variantNote ? '<div class="encyc-caution">' + icon('flag') + ' ' + esc(variantNote) + '</div>' : '') +
    '</div>';
}

// Football 101 Interactive Redesign, Section 13: reuses the app's existing
// .quiz-question/.quiz-options/.quiz-option contract (same classes ~13
// other modes already render with -- see styles.css) instead of a second
// quiz engine. The question itself is generated by football-field.js
// purely from the diagram's own real data (see generateTestMeQuestion's
// docstring) -- never a fabricated fact.
function renderF101TestMe(canonicalId, diagram, category, bucketKey) {
  var q = state.f101Quiz;
  if (!q || !q.active || q.canonicalId !== canonicalId) {
    return '<button class="btn-secondary" data-f101-test-me="' + esc(canonicalId) + ':' + esc(category) + ':' + esc(bucketKey) + '">' + icon('brain') + ' Test Me</button>';
  }
  var optionsHtml = q.options.map(function (opt, i) {
    var cls = 'quiz-option';
    var answered = q.answeredIndex !== -1 && q.answeredIndex !== undefined;
    if (answered) {
      if (i === q.correctIndex) cls += ' correct';
      else if (i === q.answeredIndex) cls += ' wrong';
    }
    return '<button class="' + cls + '" data-f101-quiz-answer="' + i + '"' + (answered ? ' disabled' : '') + '>' + esc(opt) + '</button>';
  }).join('');
  var feedback = (q.answeredIndex !== -1 && q.answeredIndex !== undefined)
    ? '<div class="quiz-feedback">' + (q.answeredIndex === q.correctIndex
        ? '<span class="feedback-good">' + icon('check') + ' Correct.</span>'
        : '<span class="feedback-bad">' + icon('xMark') + ' Coach’s correction: ' + esc(q.options[q.correctIndex]) + '.</span>') + (q.explanation ? '<p>' + esc(q.explanation) + '</p>' : '') + '<p>Trace the assignments on the chalkboard above to check the read.</p></div>'
    : '';
  return '<div class="f101-test-me">' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' + optionsHtml + '</div>' +
    feedback +
    '<button class="btn-tiny" data-f101-test-me-close>' + icon('close') + ' Close</button>' +
    '</div>';
}

function renderEncyclopediaConceptDetail() {
  var id = state.encyclopedia.conceptId;
  var kind = state.encyclopedia.conceptKind || 'concept';
  var node, title, badgeText, badgeClass, fields, sourceRows;

  if (kind === 'team') {
    node = (LEARN_ENCYCLOPEDIA.team_scheme_profiles || {})[id];
    if (!node) return renderEncyclopediaDomains();
    title = node.label;
    badgeText = 'Lineage-projected -- needs film verification';
    badgeClass = 'encyc-badge-caution';
    fields = node.fields;
    sourceRows = node.source_rows;
  } else if (kind === 'hist') {
    node = (LEARN_ENCYCLOPEDIA.historical_records || {})[id];
    if (!node) return renderEncyclopediaDomains();
    title = node.label;
    badgeText = 'Source-verified historical record';
    badgeClass = 'encyc-badge-verified';
    fields = node.fields;
    sourceRows = node.source_rows;
  } else {
    node = encyclopediaConceptByCanonicalId(id);
    if (!node) {
      // Real bug found in visual QA: a diagram-only entry (currently just
      // Wing-T -- FOOTBALL_DIAGRAMS.*[id].verified === false) has no
      // backing LEARN_ENCYCLOPEDIA node, so this page had nowhere to go
      // but bounce back to the domain list -- making the diagram
      // unreachable through any real navigation path. Synthesize a
      // minimal node from the diagram itself rather than inventing
      // encyclopedia-shaped content; renderF101DiagramBlock's own
      // verified:false caution still renders below, so this never claims
      // source-verified status it doesn't have.
      var diagOnly = f101DiagramFor(id);
      if (!diagOnly) return renderEncyclopediaDomains();
      node = { label: diagOnly.diagram.display_name, fields: {}, verification_status: 'DIAGRAM_ONLY' };
    }
    title = node.label;
    // UI/UX pass: this used to fall back to the raw backend
    // verification_status enum (e.g. "SOURCE_BACKED_DERIVED",
    // "WIKIPEDIA_STRUCTURED_SECONDARY") whenever it wasn't exactly
    // "SOURCE_BACKED" -- real technical leakage a player would see as a
    // badge on the page. Every real tier still gets honest, player-facing
    // copy; nothing backend-shaped is ever shown verbatim.
    if (node.verification_status === 'DIAGRAM_ONLY') {
      badgeText = 'Diagram reference -- not a source-verified encyclopedia entry';
      badgeClass = 'encyc-badge-caution';
    } else if (node.verification_status === 'SOURCE_BACKED_PLUS_GENERAL_KNOWLEDGE') {
      // Encyclopedia 2.0 pass: honest, distinct badge for a real gap this
      // pass found -- some concept pages have thinner depth than others
      // (a real, disclosed consequence of which source-workbook sheet
      // built them, not a quality problem to hide) and were enriched with
      // additional, well-established football knowledge that ISN'T cited
      // to a specific workbook (sheet, row) the way the rest of this
      // node's fields are. Never silently presented as "Source-verified"
      // for content that doesn't have that same citation.
      badgeText = 'Source-verified, plus general football knowledge';
      badgeClass = 'encyc-badge-verified';
    } else {
      badgeText = node.verification_status === 'SOURCE_BACKED' ? 'Source-verified' : 'Documented';
      badgeClass = 'encyc-badge-verified';
    }
    fields = node.fields || {};
    sourceRows = node.source_rows;
  }

  // Football 101 Interactive Redesign, Sections 3/4/14: attach a diagram
  // and a Quick Read/Deep Dive toggle only when one actually exists for
  // this concept -- every other concept page renders exactly as before
  // (Section 21: never touch content that has nothing to visualize).
  var f101Match = kind === 'concept' ? f101DiagramFor(id) : null;
  var readMode = state.encyclopedia.readMode || 'quick';
  var readToggleHtml = '', seeItHtml = '', testMeHtml = '', quickSummaryHtml = '';
  if (f101Match) {
    readToggleHtml = '<div class="chip-row">' +
      '<button class="chip-toggle' + (readMode === 'quick' ? ' active' : '') + '" data-f101-readmode="quick">Quick Read</button>' +
      '<button class="chip-toggle' + (readMode === 'deep' ? ' active' : '') + '" data-f101-readmode="deep">Deep Dive</button>' +
      '</div>';
    if (readMode === 'quick') {
      var summary = f101QuickSummary(node, f101Match.diagram);
      quickSummaryHtml = summary ? '<p class="mode-desc">' + esc(summary) + '</p>' : '';
    }
    // Encyclopedia Diagrams + Deep Dives pass: a variant match (e.g. Cover 3
    // Cloud borrowing the base Cover 3 diagram) is real and useful, but
    // isn't the same as an exact diagram for THIS concept -- an honest
    // caveat naming both, and no Test Me (which would generate questions
    // against the borrowed diagram's own canonical_id, not this concept).
    var variantNote = f101Match.isVariant
      ? 'Closest real diagram available (' + esc(f101Match.diagram.display_name || '') + ') -- see the write-up below for how ' + esc(title) + ' specifically differs.'
      : null;
    seeItHtml = renderF101DiagramBlock(f101Match.diagram, f101Match.category, variantNote);
    if (!f101Match.isVariant) testMeHtml = renderF101TestMe(id, f101Match.diagram, f101Match.category, f101Match.bucketKey);
  }
  // Encyclopedia Diagrams + Deep Dives pass (user request: "if u can't use
  // a diagram add a deep dive"): real, authored football teaching content
  // for a concept with no exact diagram of its own -- shown whether or not
  // a variant diagram was also found above, since the diagram alone (exact
  // or borrowed) never explains this concept's own specific nuance.
  var authoredDive = kind === 'concept' && ENCYCLOPEDIA_DEEP_DIVES ? ENCYCLOPEDIA_DEEP_DIVES[id] : null;
  var authoredDiveHtml = authoredDive
    ? '<div class="encyc-authored-dive"><div class="encyc-authored-dive-label">' + icon('book') + ' In Depth</div>' +
      '<p class="mode-desc">' + esc(authoredDive.text) + '</p></div>'
    : '';

  var related = kind === 'concept' ? encyclopediaRelatedFor(id) : [];
  var relatedHtml = related.length ? (
    '<div class="encyc-related-label">Related concepts</div>' +
    '<div class="encyc-row-list">' + related.map(function (r) {
      var target = encyclopediaConceptByCanonicalId(r.id);
      if (!target) return '';
      var arrow = r.direction === 'out' ? '→' : '←';
      return '<button class="encyc-row" data-encyc-open="concept:' + esc(r.id) + '">' +
        '<span class="encyc-row-label">' + arrow + ' ' + esc(encyclopediaPrettyLabel(r.predicate)) + ' ' + esc(target.label) + '</span></button>';
    }).join('') + '</div>'
  ) : '';

  var classroomLink = '';
  if (kind === 'concept' && node.domain === 'COVERAGES' && LEARN_COVERAGES && LEARN_COVERAGES.concepts && LEARN_COVERAGES.concepts[id]) {
    classroomLink = '<button class="btn-secondary btn-tiny encyc-classroom-link" data-encyc-goto-classroom>' + icon('brain') + ' Learn this hands-on in the Coverage Classroom</button>';
  }

  var provenance = sourceRows && sourceRows.length
    ? '<div class="encyc-provenance">Source: ' + sourceRows.map(function (r) {
        return esc(r.sheet ? (r.sheet + ' row ' + r.row) : String(r));
      }).join(', ') + '</div>'
    : '';

  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-encyc-back-domain>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">' + esc(title) + '</h2>' +
    '<span class="encyc-badge ' + badgeClass + '">' + esc(badgeText) + '</span>' +
    (node.subcategory ? '<div class="encyc-subcategory-label">' + esc(encyclopediaPrettyLabel(node.subcategory)) + '</div>' : '') +
    '<div class="film-concept-tools"><button class="btn-secondary btn-tiny" data-film-save>' + (filmNotebook().saved.some(function(v) { return v.kind === kind && v.id === id; }) ? 'Saved to playbook ✓' : 'Save to playbook +') + '</button><span class="film-eyebrow">COACH’S NOTES</span></div>' + readToggleHtml +
    quickSummaryHtml +
    seeItHtml +
    authoredDiveHtml +
    ((!f101Match || readMode === 'deep') ? renderEncyclopediaFieldsList(fields) : '') +
    (testMeHtml ? '<div class="f101-test-me-row">' + testMeHtml + '</div>' : '') +
    classroomLink +
    relatedHtml +
    provenance +
    '</div>';
}

function renderEncyclopediaScreen() {
  if (!state.encyclopedia) state.encyclopedia = { screen: 'domains', domainId: null, conceptId: null, filter: '' };
  var s = state.encyclopedia;
  if (s.screen === 'concept') return renderEncyclopediaConceptDetail();
  if (s.screen === 'domain') return renderEncyclopediaDomainDetail();
  return renderEncyclopediaDomains();
}

/* ============================== social challenges v2 ============================== */
var socialChallengeRows = [];
var socialChallengeUnsub = null;
function stopSocialChallengeWatch(){if(socialChallengeUnsub){socialChallengeUnsub();socialChallengeUnsub=null;}}
function startSocialChallengeWatch(){
  stopSocialChallengeWatch();
  if(!state.name||!window.__fbSync||!window.__fbSync.watchSocialChallenges)return;
  socialChallengeUnsub=window.__fbSync.watchSocialChallenges(state.name,function(rows){
    socialChallengeRows=Array.isArray(rows)?rows:[];
    if(state.screen==='friends'||state.screen==='h2h')renderAll();
  });
}
function socialChallengeMs(row){
  var v=row&&(row.updatedAt||row.createdAt);
  if(!v)return 0;
  if(typeof v.toMillis==='function')return v.toMillis();
  if(v.seconds)return v.seconds*1000;
  return Number(v)||0;
}
function socialChallengeRelative(row){
  var ms=socialChallengeMs(row);if(!ms)return 'just now';
  var mins=Math.floor(Math.max(0,Date.now()-ms)/60000);
  if(mins<1)return 'just now';if(mins<60)return mins+'m ago';
  var hrs=Math.floor(mins/60);if(hrs<24)return hrs+'h ago';
  return Math.floor(hrs/24)+'d ago';
}
function socialIncomingChallenges(){
  var me=slugify(state.name||'');
  return socialChallengeRows.filter(function(r){return r.recipientSlug===me&&r.status==='pending';});
}
function socialOutgoingChallenges(){
  var me=slugify(state.name||'');
  return socialChallengeRows.filter(function(r){return r.senderSlug===me&&r.status==='pending';});
}
function socialCompletedChallengesWith(name){
  var me=slugify(state.name||''), other=slugify(name||'');
  return socialChallengeRows.filter(function(r){
    return r.status==='complete'&&((r.senderSlug===me&&r.recipientSlug===other)||(r.senderSlug===other&&r.recipientSlug===me));
  });
}
function socialRivalryRecord(name){
  var rows=socialCompletedChallengesWith(name), me=slugify(state.name||''), w=0,l=0,t=0;
  rows.forEach(function(r){
    if(!r.winnerSlug)t++;
    else if(r.winnerSlug===me)w++;
    else l++;
  });
  return {wins:w,losses:l,ties:t,total:rows.length};
}
function socialChallengeLink(code){
  return SITE_URL+'#challenge='+encodeURIComponent(code||'');
}
function copySocialChallengeLink(code){
  var text='I challenged you on Reads. Beat me: '+socialChallengeLink(code);
  if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).catch(function(){});
}
function createSocialChallengeInvite(name, code, mode){
  if(!activeAuthUid||!name||!code||!window.__fbSync||!window.__fbSync.createSocialChallenge)return;
  window.__fbSync.createSocialChallenge({
    recipientName:name,matchCode:code,mode:mode||'quiz',modeLabel:h2hModeLabel(mode||'quiz'),status:'pending'
  }).catch(function(err){console.error('Challenge invite failed',err);});
}
function acceptSocialChallenge(id){
  var row=socialChallengeRows.find(function(r){return r.id===id;});
  if(!row||!row.matchCode)return;
  if(window.__fbSync&&window.__fbSync.updateSocialChallenge)window.__fbSync.updateSocialChallenge(id,{status:'accepted'}).catch(function(){});
  state.h2h={screen:'join',mode:row.mode||'quiz',roundSize:10,listId:null,error:null,intendedOpponent:row.senderName||null};
  state.screen='h2h';
  h2hJoinMatch(row.matchCode);
}
function dismissSocialChallenge(id){
  if(window.__fbSync&&window.__fbSync.updateSocialChallenge)window.__fbSync.updateSocialChallenge(id,{status:'declined'}).catch(function(){});
}
function socialSyncChallengeResult(match,code){
  if(!match||!code||!window.__fbSync||!window.__fbSync.updateSocialChallenge)return;
  var row=socialChallengeRows.find(function(r){return r.matchCode===code&&r.status!=='complete';});
  if(!row)return;
  var players=match.players||{}, slugs=Object.keys(players);
  if(slugs.length!==2)return;
  var p1=players[slugs[0]],p2=players[slugs[1]];
  if(!p1||!p2||!p1.finishedAt||!p2.finishedAt)return;
  var diff=h2hCompareRecords(p1,p2), winnerSlug=diff===0?null:(diff>0?slugs[0]:slugs[1]);
  window.__fbSync.updateSocialChallenge(row.id,{status:'complete',winnerSlug:winnerSlug,completedAt:Date.now()}).catch(function(){});
}
function socialChallengeInboxHtml(){
  if(!activeAuthUid)return '<section class="social-inbox"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">CHALLENGE INBOX</span><h3>Your matchups</h3></div></div><div class="community-login-note"><b>Log in for cross-device challenges.</b><span>Friend invites and rematches will show here.</span><button class="btn-secondary" data-auth-open="login">Log In</button></div></section>';
  var incoming=socialIncomingChallenges(), outgoing=socialOutgoingChallenges();
  return '<section class="social-inbox"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">CHALLENGE INBOX</span><h3>Your matchups</h3></div><span>'+incoming.length+' waiting</span></div>'+
    (!incoming.length&&!outgoing.length?'<div class="community-empty"><b>No open challenges.</b><span>Challenge a friend below and start a rivalry.</span></div>':'')+
    (incoming.length?'<div class="social-inbox-group"><h4>Incoming</h4>'+incoming.map(function(r){return '<article class="social-challenge-card incoming"><div><span>'+esc(r.modeLabel||h2hModeLabel(r.mode))+'</span><b>'+esc(r.senderName||'Reads fan')+' challenged you</b><small>'+esc(socialChallengeRelative(r))+'</small></div><div class="social-challenge-actions"><button class="btn-primary" data-social-accept="'+esc(r.id)+'">Play Now</button><button class="btn-tiny" data-social-decline="'+esc(r.id)+'">Dismiss</button></div></article>';}).join('')+'</div>':'')+
    (outgoing.length?'<div class="social-inbox-group"><h4>Sent</h4>'+outgoing.map(function(r){return '<article class="social-challenge-card"><div><span>'+esc(r.modeLabel||h2hModeLabel(r.mode))+'</span><b>Waiting on '+esc(r.recipientName||'friend')+'</b><small>'+esc(socialChallengeRelative(r))+'</small></div><button class="btn-tiny" data-social-copy="'+esc(r.matchCode)+'">Copy Invite</button></article>';}).join('')+'</div>':'')+
    '</section>';
}


/* ============================== friends ==============================
   No accounts, no requests to accept — just a local list of names you're
   tracking, matched against the same shared leaderboard/profile data every
   other cross-device feature this session already built (see
   pushProfileSnapshot()/pullProfileSnapshot() above). */
function weeklyFriendStandings() {
  var names = getFriends().map(slugify);
  names.push(slugify(state.name || ''));
  var week = dailyRivalWeekKey(todayStr());
  var daily = (state.leaderboardData || []).filter(function(r){
    return r.mode === 'daily' && r.weekKey === week && names.indexOf(slugify(r.name || '')) !== -1;
  });
  var season = (state.leaderboardData || []).filter(function(r){
    return r.mode === 'season' && String(r.seasonId || '') === footballSeasonIdForDate() && names.indexOf(slugify(r.name || '')) !== -1;
  });
  var map = {};
  names.forEach(function(sl){ map[sl]={name:sl===slugify(state.name||'')?state.name:((getFriends().find(function(n){return slugify(n)===sl;})||sl)),dailyPoints:0,seasonXp:0}; });
  daily.forEach(function(r){var sl=slugify(r.name||''); if(map[sl]) map[sl].dailyPoints=Math.max(map[sl].dailyPoints,Number(r.weeklyRivalPoints)||0);});
  season.forEach(function(r){var sl=slugify(r.name||''); if(map[sl]) map[sl].seasonXp=Math.max(map[sl].seasonXp,Number(r.seasonXp)||0);});
  return Object.keys(map).map(function(k){var x=map[k];x.total=x.dailyPoints+x.seasonXp;return x;}).sort(function(x,y){return y.total-x.total;});
}
function weeklyFriendStandingsHtml() {
  var rows=weeklyFriendStandings();
  if(rows.length<2) return '';
  var me=rows.findIndex(function(r){return slugify(r.name)===slugify(state.name||'');});
  return '<section class="social-weekly"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">FRIEND GROUP</span><h3>Weekly Standings</h3></div><span>'+(me>=0?'You’re #'+(me+1):'This week')+'</span></div><div class="social-standings">'+rows.slice(0,8).map(function(r,i){return '<div class="'+(slugify(r.name)===slugify(state.name||'')?'is-you':'')+'"><span>'+(i===0?'👑':(i+1))+'</span><b>'+esc(r.name)+'</b><small>'+r.dailyPoints+' Daily pts · '+r.seasonXp+' Season XP</small><strong>'+r.total+'</strong></div>';}).join('')+'</div></section>';
}
function friendRivalAlertHtml() {
  var rows=weeklyFriendStandings();
  var meIndex=rows.findIndex(function(r){return slugify(r.name)===slugify(state.name||'');});
  if(meIndex<0 || rows.length<2) return '';
  var me=rows[meIndex], ahead=rows.filter(function(r){return r.total>me.total && slugify(r.name)!==slugify(state.name||'');}).slice(-1)[0];
  if(!ahead) {
    var next=rows.filter(function(r){return r.total<me.total;})[0];
    if(!next) return '';
    return '<div class="social-rival-alert"><span>👑</span><div><b>You’re leading your friend group.</b><small>'+esc(next.name)+' is '+(me.total-next.total)+' points back this week.</small></div></div>';
  }
  return '<div class="social-rival-alert"><span>⚔️</span><div><b>'+esc(ahead.name)+' is ahead of you.</b><small>'+ (ahead.total-me.total) +' points separate you this week.</small></div><button class="btn-tiny" data-friend-challenge="'+esc(ahead.name)+'">Challenge</button></div>';
}
function teamBattleRows() {
  var rows=(state.leaderboardData||[]).filter(function(r){return r.mode==='daily' && r.weekKey===dailyRivalWeekKey(todayStr());});
  var grouped={};
  rows.forEach(function(r){
    [['nfl',r.favoriteNflTeam],['cfb',r.favoriteCfbTeam]].forEach(function(pair){
      var league=pair[0],id=pair[1]; if(!id)return;
      var key=league+'|'+id; grouped[key]=grouped[key]||{league:league,id:id,points:0,players:{}};
      grouped[key].points+=Number(r.weeklyRivalPoints)||0; grouped[key].players[slugify(r.name||'')]=true;
    });
  });
  return Object.keys(grouped).map(function(k){var g=grouped[k];var t=favoriteTeamById(g.league,g.id);g.name=t?t.name:g.id;g.count=Object.keys(g.players).length;return g;}).sort(function(x,y){return y.points-x.points;});
}
function teamBattleHtml() {
  var fav=getFavoriteTeams(), rows=teamBattleRows();
  var mine=rows.filter(function(r){return (r.league==='nfl'&&r.id===fav.nfl)||(r.league==='cfb'&&r.id===fav.cfb);});
  if(!mine.length || rows.length<2) return '';
  var primary=mine[0];
  var opponent=rows.find(function(r){return r.league===primary.league && r.id!==primary.id;});
  if(!opponent) return '';
  return '<section class="social-team-battle"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">COMMUNITY BATTLE</span><h3>'+esc(primary.name)+' vs. '+esc(opponent.name)+'</h3></div><span>This week</span></div><div class="team-battle-score"><div><b>'+esc(primary.name)+'</b><strong>'+primary.points+'</strong><small>'+primary.count+' active</small></div><span>VS</span><div><b>'+esc(opponent.name)+'</b><strong>'+opponent.points+'</strong><small>'+opponent.count+' active</small></div></div><p>Every Daily Reads Rival Point adds to your team total.</p></section>';
}
function friendProfileComparisonHtml(name) {
  if(!name) return '';
  var slug=slugify(name), profile=friendsProfileCache[slug], friendRating=friendRatingFromLeaderboard(name), myRating=getRating();
  if(!profile && !friendRating) return '<section class="friend-compare-card"><button class="btn-tiny" data-friend-compare-close>'+icon('close')+' Close</button><h3>'+esc(name)+'</h3><p class="mode-desc">No synced profile data available yet.</p></section>';
  var myMastery=personalizationMasteryRows().filter(function(r){return r.total>=3;}).sort(function(x,y){return y.pct-x.pct;})[0];
  var fp=profile&&profile.personalization, fRows=[];
  if(fp&&fp.categoryStats){['nfl','cfb'].forEach(function(l){Object.keys(fp.categoryStats[l]||{}).forEach(function(cat){var x=fp.categoryStats[l][cat];if(x&&x.total>=3)fRows.push({category:cat,pct:Math.round(100*(x.correct||0)/x.total)});});});}
  fRows.sort(function(x,y){return y.pct-x.pct;});
  var fProg=profile&&profile.progression?profile.progression:{careerXp:0};
  return '<section class="friend-compare-card"><div class="dashboard-section-head"><div><span class="dashboard-eyebrow">PROFILE COMPARISON</span><h3>'+esc(state.name)+' vs. '+esc(name)+'</h3></div><button class="btn-tiny" data-friend-compare-close>'+icon('close')+' Close</button></div><div class="friend-compare-grid"><div><small>Football Rating</small><b>'+(myRating?myRating.score:'—')+'</b><span>vs</span><b>'+(friendRating?friendRating.score:'—')+'</b></div><div><small>Career XP</small><b>'+((getProgression().careerXp)||0)+'</b><span>vs</span><b>'+((fProg&&fProg.careerXp)||0)+'</b></div><div><small>Top mastery</small><b>'+esc(myMastery?myMastery.category:'—')+'</b><span>vs</span><b>'+esc(fRows[0]?fRows[0].category:'—')+'</b></div></div></section>';
}
function challengeFriendToMode(name, mode) {
  if(!state.name) return;
  mode=mode||'quiz';
  if(!H2H_MODES.some(function(m){return m.id===mode;})) mode='quiz';
  state.h2h={screen:'create',mode:mode,roundSize:10,listId:null,error:null,intendedOpponent:name||null};
  state.screen='h2h';
  renderAll();
}
function socialChallengeButtonHtml(mode) {
  if(!state.name || !H2H_MODES.some(function(m){return m.id===mode;})) return '';
  return '<button class="btn-secondary social-beat-score" data-social-challenge-mode="'+esc(mode)+'">'+icon('versus')+' Challenge a Friend</button>';
}
function renderFriendsScreen() {
  var friends = getFriends();
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('users') + ' Friends</h2>' +
    '<p class="mode-desc">Add friends by their exact username, compare profiles, challenge them, and race for the weekly crown.</p>' +
    socialChallengeInboxHtml() +
    friendRivalAlertHtml() +
    weeklyFriendStandingsHtml() +
    friendProfileComparisonHtml(state.friendCompare) +
    '<div class="field-row"><input id="friend-name-input" placeholder="Friend’s name" autocomplete="off" maxlength="40" />' +
    '<button class="btn-primary" data-friend-add>Add</button></div>';
  if (!friends.length) {
    html += '<p class="mode-desc">No friends added yet.</p>';
  } else if (friendsLoading) {
    html += '<div class="loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading friends…</div></div>';
  } else {
    html += '<div class="friends-list">' + friends.map(friendRowHtml).join('') + '</div>';
  }
  html += '</div>';
  return html;
}
function friendRowHtml(name) {
  var slug = slugify(name);
  var rating = friendRatingFromLeaderboard(name);
  var profile = friendsProfileCache[slug];
  var streakCount = profile && profile.streak ? (profile.streak.count || 0) : 0;
  var todayRivals = dailyRivalRows('today');
  var rivalIndex = todayRivals.findIndex(function (r) { return slugify(r.name || '') === slug; });
  var rival = rivalIndex >= 0 ? todayRivals[rivalIndex] : null;
  var statsBits = [];
  if (rating) statsBits.push(icon('football') + ' ' + rating.score + ' rating');
  else statsBits.push('No rating yet');
  if (streakCount > 0) statsBits.push(icon('flame') + ' ' + streakCount + '-day streak');
  if (rival) statsBits.push(icon('target') + ' Daily #' + (rivalIndex + 1) + ' · ' + (Number(rival.todayRivalPoints) || 0) + ' pts');
  var record=socialRivalryRecord(name);
  if(record.total) statsBits.push(icon('versus')+' '+record.wins+'-'+record.losses+(record.ties?'-'+record.ties:'')+' vs you');
  return '<div class="friend-row">' +
    '<div class="friend-info"><div class="friend-name">' + esc(name) + '</div>' +
    '<div class="friend-stats">' + statsBits.join(' &middot; ') + '</div></div>' +
    '<div class="friend-actions"><button class="btn-tiny" data-friend-compare="' + esc(name) + '">Compare</button><button class="btn-tiny" data-friend-challenge="' + esc(name) + '">'+icon('versus')+' Challenge</button><button class="btn-tiny" data-friend-remove="' + esc(name) + '">' + icon('close') + ' Remove</button></div>' +
    '</div>';
}

/* ============================== profile ==============================
   A personal stats page — state.stats has been write-only until now (every
   finish* function updates it, nothing reads it back for display). Reuses
   LEADERBOARD_MODES' existing label/cols config against state.stats instead
   of state.leaderboardData, so the per-mode column definitions live in one
   place rather than being duplicated for this screen. */
/* ============================== achievement badges ==============================
   Computed live from state.stats/getStreak() every time the Profile page
   renders — no separate "earned badges" data to keep in sync, a badge is
   just a threshold check against data every mode already tracks. */
var BADGES = [
  { id: 'perfectGrid', icon: '🔲', title: 'Perfect Grid', desc: 'Clean-swept the NFL Immaculate Grid (9/9).', check: function (st) { return (st.grid.cleanSweeps || 0) > 0; } },
  { id: 'perfectCfbGrid', icon: '🔲', title: 'CFB Perfect Grid', desc: 'Clean-swept the CFB Immaculate Grid (9/9).', check: function (st) { return (st.cfbGrid.cleanSweeps || 0) > 0; } },
  { id: 'blitzMaster', icon: '⏱️', title: 'Blitz Master', desc: 'Matched 20+ answers in a single NFL Blitz round.', check: function (st) { return (st.blitz.bestMatched || 0) >= 20; } },
  { id: 'cfbBlitzMaster', icon: '⏱️', title: 'CFB Blitz Master', desc: 'Matched 20+ answers in a single CFB Blitz round.', check: function (st) { return (st.cfbBlitz.bestMatched || 0) >= 20; } },
  { id: 'speedDemon', icon: '⚡', title: 'Speed Demon', desc: 'Built a 10+ answer streak in NFL Speed.', check: function (st) { return (st.speed.bestStreak || 0) >= 10; } },
  { id: 'cfbSpeedDemon', icon: '⚡', title: 'CFB Speed Demon', desc: 'Built a 10+ answer streak in CFB Speed.', check: function (st) { return (st.cfbSpeed.bestStreak || 0) >= 10; } },
  { id: 'genius', icon: '🧠', title: 'Football Genius', desc: 'Scored 140+ on the Football IQ Test.', check: function (st) { return (st.iq.bestIQ || 0) >= 140; } },
  { id: 'cfbGenius', icon: '📚', title: 'CFB Genius', desc: 'Scored 140+ on the College Football IQ Test.', check: function (st) { return (st.cfbIq.bestIQ || 0) >= 140; } },
  { id: 'sharpshooter', icon: '🎯', title: 'Sharpshooter', desc: '90%+ on an NFL Quiz round.', check: function (st) { return (st.quiz.bestPct || 0) >= 90; } },
  { id: 'cfbSpecialist', icon: '🎓', title: 'CFB Specialist', desc: 'Played 20+ rounds across every College Football mode combined.', check: function (st) {
    return (st.cfbQuiz.roundsPlayed || 0) + (st.cfbGrid.gamesPlayed || 0) + (st.cfbBlitz.attempts || 0) + (st.cfbSpeed.sessionsPlayed || 0) + (st.cfbIq.testsTaken || 0) + (st.cfbLegends.gamesPlayed || 0) >= 20;
  } },
  { id: 'perfectSeason', icon: '🏆', title: 'Perfect Season', desc: 'Drafted a 17-0 team that actually went 17-0.', check: function (st) { return (st.legends.bestWins || 0) >= 17; } },
  { id: 'perfect12', icon: '🏆', title: 'Perfect 12-0', desc: 'Drafted a CFB 12-0 team that actually went undefeated and won the National Championship.', check: function (st) { return (st.cfbLegends.bestWins || 0) >= 12; } },
  { id: 'sharpEye', icon: '🕵️', title: 'Sharp Eye', desc: '5+ quick guesses (few clues used) in one Silhouette round.', check: function (st) { return (st.silhouette.bestQuick || 0) >= 5; } },
  { id: 'onFire', icon: '🔥', title: 'On Fire', desc: 'Hit a 7-day Daily Reads streak.', check: function (st, streak) { return streak.count >= 7; } },
  { id: 'dailyGrinder', icon: '📅', title: 'Daily Grinder', desc: 'Completed 10+ Daily Reads.', check: function (st) { return (st.daily.completions || 0) >= 10; } },
  { id: 'rivalry', icon: '⚔️', title: 'Got Next', desc: 'Won a Head-to-Head match against a friend.', check: function (st) { return (st.h2h.wins || 0) >= 1; } },
  { id: 'higherLowerStreak', icon: '📈', title: 'On a Heater', desc: 'Built a 15+ player streak in Higher or Lower.', check: function (st) { return (st.higherLower.bestStreak || 0) >= 15; } }
];
var FILM_BADGES = [
  { id:'filmStarter', icon:'🎬', title:'Film Grinder', desc:'Logged 25 Film Room reps.', check:function(){return filmNotebook().reps>=25;} },
  { id:'filmCoordinator', icon:'🎧', title:'Coordinator', desc:'Passed the Coordinator Test.', check:function(){return filmNotebook().bossWins>=1;} },
  { id:'filmGuru', icon:'🧠', title:'Scheme Guru', desc:'Reached Guru mastery in any Film Room concept family.', check:function(){var n=filmNotebook();return Object.keys(n.mastery||{}).some(function(k){return filmMasteryLevel(n.mastery[k]).name==='Guru';});} }
];
BADGES = BADGES.concat(FILM_BADGES);

var REWARD_BADGES = [
  { id: 'firstRead', icon: '📖', title: 'First Read', desc: 'Completed your first Daily Reads.', check: function (st) { return (st.daily.completions || 0) >= 1; } },
  { id: 'daily25', icon: '🗓️', title: 'Daily Habit', desc: 'Completed 25 Daily Reads.', check: function (st) { return (st.daily.completions || 0) >= 25; } },
  { id: 'streak30', icon: '🔥', title: 'Iron Streak', desc: 'Reached a 30-day Daily Reads streak.', check: function (st, streak) { return streak.count >= 30; } },
  { id: 'starterRank', icon: '🏈', title: 'Starter', desc: 'Reached Starter career rank.', check: function () { return (getProgression().careerXp || 0) >= 250; } },
  { id: 'playmakerRank', icon: '⭐', title: 'Playmaker', desc: 'Reached Playmaker career rank.', check: function () { return (getProgression().careerXp || 0) >= 750; } },
  { id: 'veteranRank', icon: '🛡️', title: 'Veteran', desc: 'Reached Veteran career rank.', check: function () { return (getProgression().careerXp || 0) >= 1500; } },
  { id: 'allProRank', icon: '💎', title: 'All-Pro', desc: 'Reached All-Pro career rank.', check: function () { return (getProgression().careerXp || 0) >= 3000; } },
  { id: 'legendRank', icon: '👑', title: 'Reads Legend', desc: 'Reached Legend career rank.', check: function () { return (getProgression().careerXp || 0) >= 6000; } },
  { id: 'teamLoyal', icon: '🚩', title: 'Rep Your Colors', desc: 'Set a favorite NFL or CFB team.', check: function () { var f = getFavoriteTeams(); return !!(f.nfl || f.cfb); } }
];
BADGES = BADGES.concat(REWARD_BADGES);

var PROFILE_COSMETICS = [
  { id: 'classic', title: 'Classic', minXp: 0, desc: 'Clean Reads profile frame.' },
  { id: 'team', title: 'Team Colors', minXp: 250, desc: 'Profile frame styled around your favorite team.' },
  { id: 'spotlight', title: 'Spotlight', minXp: 750, desc: 'Broadcast-style profile spotlight.' },
  { id: 'allpro', title: 'All-Pro', minXp: 3000, desc: 'Premium All-Pro profile treatment.' },
  { id: 'legend', title: 'Legend', minXp: 6000, desc: 'Top-tier Reads Legend profile frame.' }
];
var SHARE_CARD_DESIGNS = [
  { id: 'classic', title: 'Classic Reads', minXp: 0, desc: 'The clean Reads broadcast card.' },
  { id: 'team', title: 'Team Takeover', minXp: 250, desc: 'Leans hard into your favorite team colors.' },
  { id: 'spotlight', title: 'Prime Time', minXp: 750, desc: 'Brighter spotlight and broadcast glow.' },
  { id: 'allpro', title: 'All-Pro Gold', minXp: 3000, desc: 'Gold-framed card for All-Pro careers.' },
  { id: 'legend', title: 'Legend', minXp: 6000, desc: 'Premium dark-gold Legend treatment.' }
];
function rewardsKey() { return 'nflTriviaRewards__' + slugify(state.name || 'guest'); }
function defaultRewards() { return { unlockedBadgeIds: [], selectedBadgeId: null, selectedCosmeticId: 'classic', selectedShareDesignId: 'classic', updatedAt: 0 }; }
function getRewards() {
  var r = lsGet(rewardsKey(), defaultRewards());
  r.unlockedBadgeIds = Array.isArray(r.unlockedBadgeIds) ? r.unlockedBadgeIds : [];
  r.selectedCosmeticId = r.selectedCosmeticId || 'classic';
  r.selectedShareDesignId = r.selectedShareDesignId || 'classic';
  return r;
}
function setRewards(r, skipSync) {
  r = Object.assign(defaultRewards(), r || {}, { updatedAt: Date.now() });
  lsSet(rewardsKey(), r);
  if (!skipSync) pushProfileSnapshot();
}
function mergeRewards(local, cloud) {
  local = local || defaultRewards(); cloud = cloud || defaultRewards();
  var seen = {}, unlocked = [];
  (local.unlockedBadgeIds || []).concat(cloud.unlockedBadgeIds || []).forEach(function (id) {
    if (!seen[id]) { seen[id] = true; unlocked.push(id); }
  });
  var newer = (Number(cloud.updatedAt) || 0) > (Number(local.updatedAt) || 0) ? cloud : local;
  return {
    unlockedBadgeIds: unlocked,
    selectedBadgeId: newer.selectedBadgeId || null,
    selectedCosmeticId: newer.selectedCosmeticId || 'classic',
    selectedShareDesignId: newer.selectedShareDesignId || 'classic',
    updatedAt: Math.max(Number(local.updatedAt) || 0, Number(cloud.updatedAt) || 0)
  };
}
function earnedBadges() {
  var st = state.stats, streak = getStreak();
  var persisted = {};
  getRewards().unlockedBadgeIds.forEach(function (id) { persisted[id] = true; });
  return BADGES.filter(function (b) {
    if (persisted[b.id]) return true;
    try { return b.check(st, streak); } catch (e) { return false; }
  });
}
function unlockedCosmetics() {
  var xp = Number(getProgression().careerXp) || 0;
  return PROFILE_COSMETICS.filter(function (c) { return xp >= c.minXp; });
}
function unlockedShareDesigns() {
  var xp = Number(getProgression().careerXp) || 0;
  return SHARE_CARD_DESIGNS.filter(function (d) { return xp >= d.minXp; });
}
function selectedBadge() {
  var r = getRewards();
  var earned = earnedBadges();
  return earned.find(function (b) { return b.id === r.selectedBadgeId; }) || earned[0] || null;
}
function selectedProfileCosmetic() {
  var r = getRewards();
  return unlockedCosmetics().find(function (c) { return c.id === r.selectedCosmeticId; }) || PROFILE_COSMETICS[0];
}
function selectedShareDesign() {
  var r = getRewards();
  return unlockedShareDesigns().find(function (d) { return d.id === r.selectedShareDesignId; }) || SHARE_CARD_DESIGNS[0];
}
function rewardsProfileState() { return getRewards(); }
function awardAchievementXp(badgeId) {
  if (!activeAuthUid || !window.__fbSync || !window.__fbSync.awardProgress) return;
  var seasonId = footballSeasonIdForDate();
  var eventId = 'achievement_' + badgeId;
  window.__fbSync.awardProgress(profileDocId(), eventId, { type: 'ACHIEVEMENT_UNLOCKED', badgeId: badgeId, source: 'rewards' }, 50, seasonId)
    .then(function (result) { if (!result || !result.duplicate) applyProgressAwardLocally(50, seasonId); })
    .catch(function () {});
}
function syncAchievementUnlocks() {
  if (!state.name) return [];
  var r = getRewards();
  var earned = earnedBadges();
  var known = {};
  r.unlockedBadgeIds.forEach(function (id) { known[id] = true; });
  var newly = earned.filter(function (b) { return !known[b.id]; });
  if (!newly.length) return [];
  newly.forEach(function (b) {
    r.unlockedBadgeIds.push(b.id);
    awardAchievementXp(b.id);
  });
  setRewards(r);
  showAchievementCelebration(newly);
  return newly;
}
function selectProfileBadge(id) {
  var badge = earnedBadges().find(function (b) { return b.id === id; });
  if (!badge) return;
  var r = getRewards(); r.selectedBadgeId = id; setRewards(r); renderAll();
}
function selectProfileCosmetic(id) {
  if (!unlockedCosmetics().some(function (c) { return c.id === id; })) return;
  var r = getRewards(); r.selectedCosmeticId = id; setRewards(r); renderAll();
}
function selectShareDesign(id) {
  if (!unlockedShareDesigns().some(function (d) { return d.id === id; })) return;
  var r = getRewards(); r.selectedShareDesignId = id; setRewards(r);
  renderShareDesignPicker();
  renderShareCard(shareCurrentFormat || 'square');
}

/* ============================== achievement celebrations ============================== */
var achievementCelebrationQueue = [];
var achievementCelebrationTimer = null;
function showAchievementCelebration(badges) {
  if (!badges || !badges.length || typeof document === 'undefined') return;
  badges.forEach(function (b) { achievementCelebrationQueue.push(b); });
  if (!achievementCelebrationTimer) playNextAchievementCelebration();
}
function playNextAchievementCelebration() {
  if (!achievementCelebrationQueue.length) { achievementCelebrationTimer = null; return; }
  var badge = achievementCelebrationQueue.shift();
  var old = document.getElementById('achievement-celebration');
  if (old && old.parentNode) old.parentNode.removeChild(old);
  var wrap = document.createElement('div');
  wrap.id = 'achievement-celebration';
  wrap.className = 'achievement-celebration';
  wrap.setAttribute('role', 'status');
  wrap.setAttribute('aria-live', 'polite');
  wrap.innerHTML =
    '<div class="achievement-burst" aria-hidden="true"></div>' +
    '<div class="achievement-celebration-card">' +
      '<div class="achievement-celebration-eyebrow">ACHIEVEMENT UNLOCKED</div>' +
      '<div class="achievement-celebration-icon">' + badge.icon + '</div>' +
      '<div class="achievement-celebration-title">' + esc(badge.title) + '</div>' +
      '<div class="achievement-celebration-desc">' + esc(badge.desc) + '</div>' +
      '<div class="achievement-celebration-xp">+50 XP</div>' +
    '</div>';
  document.body.appendChild(wrap);
  requestAnimationFrame(function () { wrap.classList.add('show'); });
  achievementCelebrationTimer = setTimeout(function () {
    wrap.classList.remove('show');
    setTimeout(function () {
      if (wrap.parentNode) wrap.parentNode.removeChild(wrap);
      achievementCelebrationTimer = null;
      playNextAchievementCelebration();
    }, 260);
  }, 2200);
}

/* ============================== rating history (sparkline) ==============================
   A capped local-only history of Football Rating values, appended every time
   it actually changes (updateRatingDrift, plus the one-time intro-test
   seed) — not synced to Firebase, purely a personal "how has this moved"
   visual on the Profile page. */
var RATING_HISTORY_MAX = 20;
function ratingHistoryKey() { return 'nflTriviaRatingHistory__' + slugify(state.name); }
function getRatingHistory() { return state.name ? lsGet(ratingHistoryKey(), []) : []; }
function pushRatingHistory(score) {
  if (!state.name) return;
  var h = getRatingHistory();
  h.push(score);
  if (h.length > RATING_HISTORY_MAX) h = h.slice(h.length - RATING_HISTORY_MAX);
  lsSet(ratingHistoryKey(), h);
}
function ratingSparklineSvg(history) {
  if (!history || history.length < 2) return '';
  var w = 160, h = 40, pad = 4;
  var min = Math.min.apply(null, history), max = Math.max.apply(null, history);
  var range = max - min || 1;
  var points = history.map(function (v, i) {
    var x = pad + (i / (history.length - 1)) * (w - pad * 2);
    var y = h - pad - ((v - min) / range) * (h - pad * 2);
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
  return '<svg class="rating-sparkline" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" aria-hidden="true">' +
    '<polyline points="' + points + '" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>';
}

function renderProfile() {
  syncAchievementUnlocks();
  var r = getRating();
  var streak = getStreak();
  var progression = getProgression();
  var career = progressionRankFor(progression.careerXp || 0);
  var earned = earnedBadges();
  var rewards = getRewards();
  var selected = selectedBadge();
  var cosmetic = selectedProfileCosmetic();
  var cosmeticClass = ' profile-cosmetic-' + cosmetic.id;
  var html = '<div class="panel profile-rewards-shell' + cosmeticClass + '">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-share="profile">' + icon('share') + ' Share Profile</button><button class="btn-tiny" data-go="settings">' + icon('settings') + ' Settings</button><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<div class="profile-identity-card">' +
      '<div class="profile-identity-main">' +
        '<div class="profile-avatar-mark">' + (selected ? selected.icon : icon('football')) + '</div>' +
        '<div><span class="dashboard-eyebrow">READS PROFILE</span><h2 class="panel-title">' + (state.name ? esc(state.name) : 'Your Profile') + '</h2>' +
        '<div class="profile-equipped-line">' + (selected ? esc(selected.title) + ' badge' : 'No badge equipped yet') + ' &middot; ' + esc(cosmetic.title) + ' frame</div></div>' +
      '</div>' +
      '<div class="profile-rank-chip"><b>' + esc(career.name) + '</b><span>' + (progression.careerXp || 0) + ' career XP</span></div>' +
    '</div>';
  if (r) {
    var sparkline = ratingSparklineSvg(getRatingHistory());
    html += '<div class="profile-headline-row">' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('football') + ' ' + r.score + '</div><div class="profile-headline-label">Football Rating &middot; ' + (r.games || 0) + ' games</div>' + sparkline + '</div>' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('flame') + ' ' + streak.count + '</div><div class="profile-headline-label">Day' + (streak.count === 1 ? '' : 's') + ' streak</div></div>' +
      '</div>';
  }

  html += careerLadderHtml();
  html += seasonTrophyCaseHtml();
  html += '<div class="profile-section-head"><div><span class="dashboard-eyebrow">TROPHY CASE</span><h3>Achievements</h3></div><span>' + earned.length + ' / ' + BADGES.length + ' unlocked</span></div>' +
    '<p class="mode-desc">Achievements are permanent. Tap any earned badge to equip it on your profile. New achievements award bonus XP once.</p>' +
    '<div class="profile-badges-grid profile-trophy-grid">' +
    BADGES.map(function (b) {
      var got = earned.some(function (e) { return e.id === b.id; });
      var active = selected && selected.id === b.id;
      return '<button class="profile-badge' + (got ? ' earned' : '') + (active ? ' selected' : '') + '"' +
        (got ? ' data-profile-badge="' + esc(b.id) + '"' : ' disabled') + ' title="' + esc(b.desc) + '">' +
        '<div class="profile-badge-icon">' + (got ? b.icon : '🔒') + '</div>' +
        '<div class="profile-badge-title">' + esc(b.title) + '</div>' +
        '<div class="profile-badge-desc">' + esc(b.desc) + '</div>' +
        (active ? '<span class="profile-equipped">Equipped</span>' : '') +
        '</button>';
    }).join('') +
    '</div>';

  html += '<div class="profile-section-head"><div><span class="dashboard-eyebrow">PROFILE COSMETICS</span><h3>Frames</h3></div><span>Career rewards</span></div>' +
    '<div class="profile-cosmetic-grid">' +
    PROFILE_COSMETICS.map(function (c) {
      var unlocked = (progression.careerXp || 0) >= c.minXp;
      var active = cosmetic.id === c.id;
      return '<button class="profile-cosmetic-card' + (unlocked ? ' unlocked' : '') + (active ? ' selected' : '') + '"' +
        (unlocked ? ' data-profile-cosmetic="' + esc(c.id) + '"' : ' disabled') + '>' +
        '<span class="profile-cosmetic-preview profile-cosmetic-preview-' + esc(c.id) + '">' + favoriteTeamBadgeHtml() + '</span>' +
        '<b>' + esc(c.title) + '</b><small>' + esc(c.desc) + '</small>' +
        '<span class="profile-cosmetic-unlock">' + (unlocked ? (active ? 'Equipped' : 'Tap to equip') : c.minXp + ' career XP') + '</span>' +
        '</button>';
    }).join('') +
    '</div>' +
    '<div class="profile-section-head"><div><span class="dashboard-eyebrow">SHARE CARDS</span><h3>Card Designs</h3></div><span>Unlock with career XP</span></div>' +
    '<div class="profile-share-design-grid">' +
    SHARE_CARD_DESIGNS.map(function (d) {
      var unlocked = (progression.careerXp || 0) >= d.minXp;
      var active = selectedShareDesign().id === d.id;
      return '<button class="profile-share-design-card share-design-' + esc(d.id) + (unlocked ? ' unlocked' : '') + (active ? ' selected' : '') + '"' +
        (unlocked ? ' data-share-design="' + esc(d.id) + '"' : ' disabled') + '>' +
        '<span class="profile-share-design-preview"><span>READS</span><b>' + esc(d.title) + '</b></span>' +
        '<strong>' + esc(d.title) + '</strong><small>' + esc(d.desc) + '</small>' +
        '<span class="profile-cosmetic-unlock">' + (unlocked ? (active ? 'Selected' : 'Tap to select') : d.minXp + ' career XP') + '</span>' +
        '</button>';
    }).join('') +
    '</div>' +
    '</div>';
  html += seasonHistoryHtml();
  html += '<div class="profile-mode-grid">' + profileModeCardsHtml() + '</div>';
  return html;
}
// Shared by the full Profile page and the tappable Football Rating popup
// (openRatingModal below) — both show the same per-mode breakdown that
// feeds the one drifting rating, just in different containers.
function profileModeCardsHtml() {
  return LEADERBOARD_MODES.filter(function (m) { return m.id !== 'rating'; }).map(function (m) {
    var st = state.stats[m.id] || {};
    // bestRecord (17-0 / CFB 12-0) is only ever computed at leaderboard-push
    // time from bestWins, never stored in state.stats itself — derive it
    // here the same way rather than showing a stale/blank value. The two
    // modes have different regular-season lengths (17 games NFL, 12 games CFB).
    var getVal = function (key) {
      if (key === 'bestRecord' && st.bestRecord == null && st.bestWins != null) {
        var perfectGames = m.id === 'cfbLegends' ? 12 : 17;
        return st.bestWins + '-' + (perfectGames - st.bestWins);
      }
      return st[key] != null ? st[key] : 0;
    };
    return '<div class="profile-mode-card">' +
      '<div class="profile-mode-title">' + esc(m.label) + '</div>' +
      m.cols.map(function (c) { return '<div class="profile-mode-stat"><span>' + esc(c[1]) + '</span><b>' + esc(getVal(c[0])) + '</b></div>'; }).join('') +
      '</div>';
  }).join('');
}
var ratingModalTriggerEl = null;
function openRatingModal() {
  var r = getRating();
  if (!r) return;
  ratingModalTriggerEl = document.activeElement;
  var streak = getStreak();
  var sparkline = ratingSparklineSvg(getRatingHistory());
  var tier = ratingTierFor(r.score);
  var summary = document.getElementById('rating-modal-summary');
  if (summary) {
    summary.innerHTML = '<div class="profile-headline-row">' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('football') + ' ' + r.score + '</div><div class="profile-headline-label">Football Rating &middot; ' + (r.games || 0) + ' games</div>' + sparkline + '</div>' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('flame') + ' ' + streak.count + '</div><div class="profile-headline-label">Day' + (streak.count === 1 ? '' : 's') + ' streak</div></div>' +
      '</div>' +
      '<div class="rating-modal-tier">' +
      '<div class="rating-modal-tier-row"><span class="rating-modal-tier-name">' + esc(tier.name) + '</span>' +
      (tier.next ? '<span class="rating-modal-tier-next">' + tier.ptsToNext + ' pts to ' + esc(tier.next) + '</span>' : '<span class="rating-modal-tier-next">Peak tier</span>') + '</div>' +
      '<span class="rating-xp-track rating-xp-track-lg"><span class="rating-xp-fill" style="width:' + Math.round(tier.pct * 100) + '%"></span></span>' +
      '</div>';
  }
  var breakdown = document.getElementById('rating-modal-breakdown');
  if (breakdown) breakdown.innerHTML = profileModeCardsHtml();
  var modal = document.getElementById('rating-modal');
  var backdrop = document.getElementById('rating-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('rating-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeRatingModal() {
  var modal = document.getElementById('rating-modal');
  var backdrop = document.getElementById('rating-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  restoreFocus(ratingModalTriggerEl);
  ratingModalTriggerEl = null;
}

/* ============================== render ============================== */
function renderAll() {
  var app = document.getElementById('app');
  if (!app) return;
  var html = nameBarHtml();
  if (state.screen === 'home') html += renderHome();
  else if (state.screen === 'quiz') html += renderQuizScreen();
  else if (state.screen === 'xso') html += renderXsoScreen();
  else if (state.screen === 'grid') html += renderGridScreen();
  else if (state.screen === 'blitz') html += renderBlitzScreen();
  else if (state.screen === 'speed') html += renderSpeedScreen();
  else if (state.screen === 'higherLower') html += renderHigherLowerScreen();
  else if (state.screen === 'silhouette') html += renderSilhouetteScreen();
  else if (state.screen === 'iq') html += renderIQScreen();
  else if (state.screen === 'legends') html += renderLegendsScreen();
  else if (state.screen === 'cfbQuiz') html += renderCfbScreen();
  else if (state.screen === 'cfbIq') html += renderCfbIQScreen();
  else if (state.screen === 'cfbSpeed') html += renderCfbSpeedScreen();
  else if (state.screen === 'cfbBlitz') html += renderCfbBlitzScreen();
  else if (state.screen === 'cfbGrid') html += renderCfbGridScreen();
  else if (state.screen === 'cfbLegends') html += renderCfbLegendsScreen();
  else if (state.screen === 'leaderboard') html += renderLeaderboard();
  else if (state.screen === 'profile') html += renderProfile();
  else if (state.screen === 'settings') html += renderSettings();
  else if (state.screen === 'daily') html += renderDailyScreen();
  else if (state.screen === 'introTest') html += renderIntroScreen();
  else if (state.screen === 'stats') html += renderStatsScreen();
  else if (state.screen === 'about') html += renderAbout();
  else if (state.screen === 'privacy') html += renderPrivacy();
  else if (state.screen === 'reports') html += renderReportsScreen();
  else if (state.screen === 'h2h') html += renderH2HScreen();
  else if (state.screen === 'learn') html += renderLearnScreen();
  else if (state.screen === 'friends') html += renderFriendsScreen();
  else if (state.screen === 'community') html += renderCommunityScreen();
  else if (state.screen === 'h2hLive') html += renderH2HLiveScreen();
  else if (state.screen === 'study') html += renderStudyScreen();
  else if (state.screen === 'playerClues') html += renderPlayerCluesScreen();
  else if (state.screen === 'cfbPlayerClues') html += renderCfbPlayerCluesScreen();
  else if (state.screen === 'enginePilot') html += renderEnginePilotScreen();
  else if (state.screen === 'mechanicPilot') html += renderMechanicPilotScreen();
  else if (state.screen === 'sixDegrees') html += renderSixDegreesScreen();
  else if (state.screen === 'creator') html += renderCreatorScreen();
  else if (state.screen === 'pickem') html += renderPickemScreen();
  else if (state.screen === 'liveFootball') html += renderLiveFootballScreen();
  else if (state.screen === 'endless') html += renderEndlessScreen();
  app.innerHTML = html;
  renderRatingBadge();
  applyFavoriteTeamAccent();
  if (typeof liveFootballMaybeRefresh === 'function' && (state.screen === 'home' || state.screen === 'liveFootball')) liveFootballMaybeRefresh(false);
  if (typeof syncBgMusic === 'function') syncBgMusic();

  var specificFocusHandled = false;
  var gridInput = document.getElementById('grid-input');
  if (gridInput) { gridInput.focus(); gridInput.setSelectionRange(gridInput.value.length, gridInput.value.length); specificFocusHandled = true; }
  var cfbGridInput = document.getElementById('cfb-grid-input');
  if (cfbGridInput) { cfbGridInput.focus(); cfbGridInput.setSelectionRange(cfbGridInput.value.length, cfbGridInput.value.length); specificFocusHandled = true; }
  var blitzInput = document.getElementById('blitz-input');
  if (blitzInput) { blitzInput.focus(); blitzInput.setSelectionRange(blitzInput.value.length, blitzInput.value.length); specificFocusHandled = true; }
  var cfbBlitzInput = document.getElementById('cfb-blitz-input');
  if (cfbBlitzInput) { cfbBlitzInput.focus(); cfbBlitzInput.setSelectionRange(cfbBlitzInput.value.length, cfbBlitzInput.value.length); specificFocusHandled = true; }
  var silhouetteInput = document.getElementById('silhouette-input');
  if (silhouetteInput) { silhouetteInput.focus(); silhouetteInput.setSelectionRange(silhouetteInput.value.length, silhouetteInput.value.length); specificFocusHandled = true; }
  var cluesInput = document.getElementById('clues-input');
  if (cluesInput) { cluesInput.focus(); cluesInput.setSelectionRange(cluesInput.value.length, cluesInput.value.length); specificFocusHandled = true; }
  var cfbCluesInput = document.getElementById('cfb-clues-input');
  if (cfbCluesInput) { cfbCluesInput.focus(); cfbCluesInput.setSelectionRange(cfbCluesInput.value.length, cfbCluesInput.value.length); specificFocusHandled = true; }
  // The Learn filter box re-renders the whole table on every keystroke
  // (see the 'input' listener above) — without this, the innerHTML replace
  // would steal focus after the very first character typed.
  var filmSearchInput = document.getElementById('film-search-input');
  if (filmSearchInput && state.learn.filmFilter) { filmSearchInput.focus(); filmSearchInput.setSelectionRange(filmSearchInput.value.length, filmSearchInput.value.length); specificFocusHandled = true; }
  var learnFilterInput = document.getElementById('learn-filter-input');
  if (learnFilterInput) { learnFilterInput.focus(); learnFilterInput.setSelectionRange(learnFilterInput.value.length, learnFilterInput.value.length); specificFocusHandled = true; }
  var encyclopediaSearchInput = document.getElementById('encyclopedia-search-input');
  if (encyclopediaSearchInput) { encyclopediaSearchInput.focus(); encyclopediaSearchInput.setSelectionRange(encyclopediaSearchInput.value.length, encyclopediaSearchInput.value.length); specificFocusHandled = true; }

  // Move focus to the new screen's content on real navigation (mode A -> mode
  // B), so screen-reader users get announced into the new panel instead of
  // focus silently falling back to <body> (innerHTML replacement destroys
  // whatever was previously focused). Deliberately skipped when a specific
  // input above already claimed focus, and only fires on an actual screen
  // change — not on every re-render within the same mode (e.g. answering a
  // quiz question), which would be disruptive rather than helpful.
  if (!specificFocusHandled && state.screen !== lastFocusedScreen) {
    app.focus({ preventScroll: true });
  }
  lastFocusedScreen = state.screen;

  var navScreenMatch = function (btn) { btn.classList.toggle('active', btn.dataset.go === state.screen); };
  document.querySelectorAll('#top-nav [data-go], #bottom-nav [data-go]').forEach(navScreenMatch);
  var currentLeague = LEAGUE_MODES.nfl.some(function (m) { return m.id === state.screen; }) ? 'nfl'
    : LEAGUE_MODES.cfb.some(function (m) { return m.id === state.screen; }) ? 'cfb' : null;
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.leagueToggle === currentLeague);
  });
}

/* ============================== typeahead ==============================
   A custom-styled autocomplete dropdown, replacing the browser's native
   <input list="..."> datalist for the three modes that search a real player
   pool (NFL/CFB Grid, Silhouette). Datalist's suggestion popup can't be
   restyled at all in Safari/Firefox and only minimally in Chrome, so no
   amount of CSS was ever going to make it look like the rest of this app —
   it was always going to read as a bare OS control. Deliberately NOT wired
   through renderAll() (which would steal focus and rebuild the whole screen
   on every keystroke — the same reason state.grid.input etc. are tracked
   silently below with an early `return`) — this writes directly into its
   own small sibling <div>, same technique the team-picker/Learn filter
   searches already use for a live-updating list. */
var TYPEAHEAD_CONFIGS = {
  'grid-input': {
    pool: function () { return GRID_PLAYERS; },
    exclude: function () { return state.grid ? state.grid.usedPlayers : []; },
    onPick: function (name) { state.grid.input = name; submitGridGuess(); }
  },
  'cfb-grid-input': {
    pool: function () { return CFB_GRID_PLAYERS; },
    exclude: function () { return state.cfbGrid ? state.cfbGrid.usedPlayers : []; },
    onPick: function (name) { state.cfbGrid.input = name; submitCfbGridGuess(); }
  },
  'silhouette-input': {
    pool: function () { return SILHOUETTE_PLAYERS; },
    exclude: function () { return []; },
    onPick: function (name) { state.silhouette.input = name; submitSilhouetteGuess(); }
  },
  'clues-input': {
    pool: function () { return playerCluesAnswerPool(); },
    exclude: function () { return []; },
    onPick: function (name) { state.playerClues.input = name; submitPlayerCluesGuess(); }
  },
  'cfb-clues-input': {
    pool: function () { return cfbPlayerCluesAnswerPool(); },
    exclude: function () { return []; },
    onPick: function (name) { state.cfbPlayerClues.input = name; submitCfbPlayerCluesGuess(); }
  }
};
var typeaheadActiveIndex = -1;
function typeaheadListEl(inputId) { return document.getElementById(inputId + '-typeahead'); }
function typeaheadMatches(inputId, query) {
  var cfg = TYPEAHEAD_CONFIGS[inputId];
  var norm = normName(query);
  if (!cfg || !norm) return [];
  var excluded = cfg.exclude();
  return cfg.pool().filter(function (p) {
    return normName(p.name).indexOf(norm) !== -1 && excluded.indexOf(p.name) === -1;
  }).slice(0, 8);
}
// Plain case-insensitive indexOf against the real (non-normalized) name —
// matching itself uses normName so "Ja'Marr" still matches a query typed
// without the apostrophe, but that's overkill for just deciding where to
// draw a <mark>: worst case for the rare name where the two disagree is a
// suggestion with no highlight, not a wrong or broken one.
function typeaheadHighlight(name, query) {
  var q = query.trim();
  var idx = q ? name.toLowerCase().indexOf(q.toLowerCase()) : -1;
  if (idx === -1) return esc(name);
  return esc(name.slice(0, idx)) + '<mark>' + esc(name.slice(idx, idx + q.length)) + '</mark>' + esc(name.slice(idx + q.length));
}
function renderTypeahead(inputId) {
  var listEl = typeaheadListEl(inputId);
  var inputEl = document.getElementById(inputId);
  if (!listEl || !inputEl) return;
  var query = inputEl.value;
  var matches = typeaheadMatches(inputId, query);
  if (!matches.length) { listEl.innerHTML = ''; listEl.classList.remove('open'); inputEl.setAttribute('aria-expanded', 'false'); typeaheadActiveIndex = -1; return; }
  typeaheadActiveIndex = 0;
  listEl.innerHTML = matches.map(function (p, i) {
    return '<button type="button" role="option" class="typeahead-row' + (i === 0 ? ' active' : '') + '" data-typeahead-pick="' + esc(p.name) + '">' + typeaheadHighlight(p.name, query) + '</button>';
  }).join('');
  listEl.classList.add('open');
  inputEl.setAttribute('aria-expanded', 'true');
}
function closeTypeahead(inputId) {
  var listEl = typeaheadListEl(inputId);
  var inputEl = document.getElementById(inputId);
  if (listEl) { listEl.innerHTML = ''; listEl.classList.remove('open'); }
  if (inputEl) inputEl.setAttribute('aria-expanded', 'false');
  typeaheadActiveIndex = -1;
}
function typeaheadMove(inputId, delta) {
  var listEl = typeaheadListEl(inputId);
  if (!listEl) return false;
  var rows = listEl.querySelectorAll('.typeahead-row');
  if (!rows.length) return false;
  typeaheadActiveIndex = (typeaheadActiveIndex + delta + rows.length) % rows.length;
  rows.forEach(function (r, i) { r.classList.toggle('active', i === typeaheadActiveIndex); });
  rows[typeaheadActiveIndex].scrollIntoView({ block: 'nearest' });
  return true;
}
// Enter should commit whichever suggestion is highlighted when the dropdown
// is open (standard combobox behavior), but fall through to the existing
// submit-whatever-was-typed flow when it's closed/empty — e.g. someone
// pastes/types an exact name and hits Enter before any matches render.
function typeaheadPickActive(inputId) {
  var listEl = typeaheadListEl(inputId);
  if (!listEl || !listEl.classList.contains('open')) return false;
  var rows = listEl.querySelectorAll('.typeahead-row');
  if (!rows.length || typeaheadActiveIndex < 0) return false;
  var name = rows[typeaheadActiveIndex].dataset.typeaheadPick;
  closeTypeahead(inputId);
  TYPEAHEAD_CONFIGS[inputId].onPick(name);
  return true;
}

/* ============================== events ============================== */
document.addEventListener('click', function (e) {
  var t = e.target.closest('[data-go], [data-log-out], [data-auth-open], #auth-close, #auth-backdrop, #auth-submit, #auth-switch, ' +
    '[data-quiz-roundsize], [data-quiz-start], [data-quiz-answer], [data-quiz-next], [data-quiz-again], [data-quiz-setup], ' +
    '[data-xso-roundsize], [data-xso-start], [data-xso-answer], [data-xso-next], [data-xso-again], [data-xso-setup], ' +
    '[data-study-start], [data-study-answer], [data-study-next], ' +
    '[data-grid-start], [data-grid-cell], [data-grid-submit], [data-grid-again], ' +
    '[data-blitz-list], [data-blitz-start], [data-blitz-submit], [data-blitz-setup], ' +
    '[data-speed-start], [data-speed-answer], [data-leaderboard-mode], [data-leaderboard-range], ' +
    '[data-hl-start], [data-hl-guess], [data-hl-continue], [data-hl-stat], [data-hl-category], ' +
    '[data-silhouette-start], [data-silhouette-submit], [data-silhouette-hint], [data-silhouette-giveup], [data-silhouette-next], ' +
    '[data-clues-start], [data-clues-submit], [data-clues-hint], [data-clues-giveup], [data-clues-next], ' +
    '[data-clues-filter-decade], [data-clues-filter-difficulty], ' +
    '[data-cfb-clues-start], [data-cfb-clues-submit], [data-cfb-clues-hint], [data-cfb-clues-giveup], [data-cfb-clues-next], ' +
    '[data-cfb-clues-filter-decade], [data-cfb-clues-filter-difficulty], ' +
    '[data-pilot-start], [data-pilot-answer], [data-pilot-next], [data-pilot-retry], [data-pilot-fallback], [data-pilot-franchise-pick], [data-pilot-reveal-clue], ' +
    '[data-mechanic-start], [data-mechanic-retry], [data-mechanic-fallback], [data-mechanic-next], [data-mechanic-exit], ' +
    '[data-match-left], [data-match-submit], [data-sort-up], [data-sort-down], [data-sort-submit], ' +
    '[data-mechanic-hl-guess], [data-elim-guess], [data-mechanic-comparison-match], [data-mechanic-sort-format], ' +
    '[data-mechanic-grid-cell], [data-mechanic-grid-submit], [data-mechanic-grid-cancel], [data-mechanic-drive-answer], ' +
    '[data-mechanic-roster-pick], [data-mechanic-roster-slot], [data-mechanic-roster-candidate], ' +
    '[data-mechanic-roster-deselect], [data-mechanic-roster-submit-lineup], [data-mechanic-chain-submit], ' +
    '[data-mechanic-branch-choice], [data-mechanic-branch-answer], [data-mechanic-season-submit], ' +
    '[data-mechanic-duel-choice], [data-mechanic-impostor-pick], [data-mechanic-missing-piece-pick], ' +
    '[data-mechanic-career-path-pick], [data-mechanic-risk-tier], [data-mechanic-risk-answer], ' +
    '[data-mechanic-wager-submit], [data-mechanic-wager-answer], [data-mechanic-blind-resume-pick], ' +
    '[data-mechanic-don-answer], [data-mechanic-don-bank], [data-mechanic-guess-the-ranking-pick], ' +
    '[data-mechanic-stat-target-pick], [data-mechanic-reverse-trivia-pick], [data-mechanic-three-strikes-answer], ' +
    '[data-mechanic-mystery-reveal], [data-mechanic-mystery-guess], [data-mechanic-draft-pick-ladder-pick], ' +
    '[data-mechanic-category-roulette-pick], [data-mechanic-common-link-pick], ' +
    '[data-sixdegrees-start], [data-sixdegrees-retry], [data-sixdegrees-fallback], [data-sixdegrees-reveal], [data-sixdegrees-giveup], [data-sixdegrees-pick-id], ' +
    '#creator-auth-submit, [data-creator-auth-submit], [data-creator-logout], [data-creator-nav], [data-creator-queue-filter], ' +
    '[data-creator-check-feasibility], [data-creator-generate], [data-creator-review], [data-creator-example], ' +
    '[data-creator-format-pick], ' +
    '[data-iq-start], [data-iq-answer], ' +
    '[data-legends-start], [data-legends-pick], [data-legends-reroll-team], [data-legends-reroll-year], ' +
    '[data-cfb-legends-start], [data-cfb-legends-pick], [data-cfb-legends-reroll-team], [data-cfb-legends-reroll-year], ' +
    '[data-cfb-roundsize], [data-cfb-start], [data-cfb-answer], [data-cfb-next], [data-cfb-again], [data-cfb-setup], ' +
    '[data-cfb-iq-start], [data-cfb-iq-answer], ' +
    '[data-cfb-speed-start], [data-cfb-speed-answer], ' +
    '[data-cfb-blitz-list], [data-cfb-blitz-start], [data-cfb-blitz-submit], [data-cfb-blitz-setup], ' +
    '[data-cfb-grid-start], [data-cfb-grid-cell], [data-cfb-grid-submit], [data-cfb-grid-again], ' +
    '[data-intro-begin], [data-intro-answer], [data-intro-skip], [data-intro-continue], [data-retake-intro], ' +
    '[data-daily-start], [data-daily-answer], [data-daily-confidence], [data-daily-next], ' +
    '[data-ranked-toggle], ' +
    '[data-share], #share-close, #share-backdrop, #share-download, #share-x, #share-facebook, #share-copy, [data-share-format], ' +
    '[data-report], #report-close, #report-backdrop, #report-submit, [data-report-category], [data-copy-email], ' +
    '#rating-badge, #rating-close, #rating-backdrop, ' +
    '#team-picker-close, #team-picker-backdrop, [data-team-tab], [data-team-pick], [data-team-clear], [data-team-done], [data-team-picker-toggle], [data-team-prompt-dismiss], ' +
    '[data-settings-mute-toggle], [data-settings-push-toggle], [data-push-pref], [data-settings-clear-ask], [data-settings-clear-confirm], [data-settings-clear-cancel], ' +
    '[data-h2h-go-create], [data-h2h-go-join], [data-h2h-back-menu], [data-h2h-roundsize], [data-h2h-create], ' +
    '[data-h2h-join], [data-h2h-open-code], [data-h2h-start-play], [data-h2h-answer], [data-h2h-next], [data-h2h-rematch], [data-h2h-exit], ' +
    '[data-h2h-live-go-create], [data-h2h-live-go-join], [data-h2h-live-back-menu], [data-h2h-live-roundsize], [data-h2h-live-create], ' +
    '[data-h2h-live-join], [data-h2h-live-ready], [data-h2h-live-share-link], [data-h2h-live-answer], [data-h2h-live-exit], ' +
    '[data-film-assignment], [data-film-jump], [data-film-study], [data-film-study-family], [data-film-boss], [data-film-review], [data-film-answer], [data-film-next], [data-film-saved], [data-film-save], [data-film-concept], [data-film-resume], [data-film-retry], [data-learn-open], [data-learn-back], [data-learn-cat], ' +
    '[data-classroom-exit], [data-classroom-lesson], [data-classroom-practice], [data-classroom-path], ' +
    '[data-classroom-step-next], [data-classroom-step-back], [data-classroom-answer], [data-classroom-exercise-next], ' +
    '[data-encyc-domain], [data-encyc-domains], [data-encyc-open], [data-encyc-back-domain], [data-encyc-goto-classroom], ' +
    '[data-f101-toggle], [data-f101-reset], [data-f101-readmode], [data-f101-player], [data-f101-player-close], ' +
    '[data-f101-test-me], [data-f101-quiz-answer], [data-f101-test-me-close], ' +
    '[data-friend-add], [data-friend-remove], [data-friend-compare], [data-friend-compare-close], [data-friend-challenge], [data-social-challenge-mode], [data-social-accept], [data-social-decline], [data-social-copy], [data-profile-badge], [data-profile-cosmetic], [data-share-design], [data-community-league], [data-community-post], [data-community-preset], ' +
    '[data-typeahead-pick], ' +
    '[data-league-toggle], #mode-sheet-close, #mode-sheet-backdrop, ' +
    '#help-toggle, #onboarding-next, #onboarding-skip, #onboarding-backdrop, [data-onboarding-sample-answer], ' +
    '[data-mode-restart], [data-mode-exit], ' +
    '[data-pickem-slate], [data-pickem-conference], [data-pickem-game], [data-pickem-retry], ' +
    '[data-live-football-open], [data-live-football-refresh], [data-live-game-challenge], [data-live-challenge-start], [data-live-challenge-answer], [data-live-challenge-next], [data-live-challenge-close], ' +
    '[data-endless-start], [data-endless-answer], [data-endless-next]');
  if (!t) return;

  // User request: the correct-answer crowd-cheer (and wrong-answer whistle)
  // used to just play out its fixed SFX_MAX_DURATION cap (sound.js)
  // regardless of what the player did next -- clicking straight through to
  // the next question no longer waits out that timer; any sound still
  // playing from the previous answer cuts off immediately on any of these
  // real navigation clicks, the same way starting a brand-new playSound()
  // already does via its own stopSfx() call.
  stopSfx();

  if (t.id === 'help-toggle') {
    var helpMode = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).find(function (x) { return x.id === state.screen; });
    openOnboarding(helpMode ? contextualHelpSteps(helpMode) : null);
    return;
  }
  if (t.dataset.onboardingSampleAnswer !== undefined) { onboardingPickSample(parseInt(t.dataset.onboardingSampleAnswer, 10)); return; }
  if (t.id === 'onboarding-next') { onboardingNext(); return; }
  if (t.id === 'onboarding-skip' || t.id === 'onboarding-backdrop') { closeOnboarding(); return; }
  if (t.dataset.share !== undefined) { shareResultCard(t.dataset.share); return; }
  if (t.id === 'share-close' || t.id === 'share-backdrop') { closeShareModal(); return; }
  if (t.id === 'share-download') { shareDownloadImage(); return; }
  if (t.id === 'share-x') { shareToX(); return; }
  if (t.id === 'share-facebook') { shareToFacebook(); return; }
  if (t.id === 'share-copy') { shareCopyText(); return; }
  if (t.dataset.shareFormat !== undefined) { if (t.dataset.shareFormat !== shareCurrentFormat) renderShareCard(t.dataset.shareFormat); return; }
  if (t.dataset.report !== undefined) { openReportModal(t.dataset.report); return; }
  if (t.id === 'report-close' || t.id === 'report-backdrop') { closeReportModal(); return; }
  if (t.dataset.reportCategory !== undefined) { setReportCategory(t.dataset.reportCategory); return; }
  if (t.id === 'report-submit') { submitReport(); return; }
  if (t.id === 'rating-badge') { openRatingModal(); return; }
  if (t.id === 'rating-close' || t.id === 'rating-backdrop') { closeRatingModal(); return; }
  if (t.id === 'auth-close' || t.id === 'auth-backdrop') { closeAuthModal(); return; }
  if (t.id === 'auth-submit') { authModalSubmit(); return; }
  if (t.id === 'auth-switch') { authModalSwitch(); return; }
  if (t.dataset.authOpen !== undefined) { openAuthModal(t.dataset.authOpen); return; }
  if (t.dataset.logOut !== undefined) { logOut(); return; }
  // User feedback: the top-bar gear icon "makes zero sense" opening the
  // team picker -- it now genuinely goes to Settings (data-go="settings"
  // on the button itself, handled by the generic data-go branch below).
  // Every OTHER real entry point to the team picker (onboarding's "Pick
  // My Teams", the mode-sheet's "Your team" pill, Settings' own "Change
  // Teams") still uses data-team-picker-toggle and is unaffected.
  if (t.dataset.teamPickerToggle !== undefined) { openTeamPicker(); return; }
  if (t.dataset.teamPromptDismiss !== undefined) { dismissTeamPrompt(); return; }
  if (t.dataset.settingsMuteToggle !== undefined) { toggleMute(); renderAll(); return; }
  if (t.dataset.settingsPushToggle !== undefined) { togglePushNotifications(); return; }
  if (t.dataset.pushPref !== undefined) { var pp=getPushPreferences(); setPushPreference(t.dataset.pushPref,!pp[t.dataset.pushPref]); return; }
  if (t.dataset.settingsClearAsk !== undefined) { settingsClearDataAsk(); return; }
  if (t.dataset.settingsClearConfirm !== undefined) { clearAllUserData(); return; }
  if (t.dataset.settingsClearCancel !== undefined) { settingsClearDataCancel(); return; }
  if (t.id === 'team-picker-close' || t.id === 'team-picker-backdrop' || t.dataset.teamDone !== undefined) { closeTeamPicker(); return; }
  if (t.dataset.teamTab !== undefined) { teamPickerSetTab(t.dataset.teamTab); return; }
  if (t.dataset.teamPick !== undefined) { var tp = t.dataset.teamPick.split(':'); teamPickerPick(tp[0], tp.slice(1).join(':')); return; }
  if (t.dataset.teamClear !== undefined) { teamPickerClear(t.dataset.teamClear); return; }
  if (t.dataset.copyEmail !== undefined) { copyTextToClipboard(t.dataset.copyEmail, t); return; }
  if (t.dataset.h2hGoCreate !== undefined) { state.h2h.screen = 'create'; state.h2h.error = null; renderAll(); return; }
  if (t.dataset.h2hGoJoin !== undefined) { state.h2h.screen = 'join'; state.h2h.error = null; renderAll(); return; }
  if (t.dataset.h2hBackMenu !== undefined) { h2hBackToMenu(); return; }
  if (t.dataset.h2hRoundsize !== undefined) { h2hSetRoundSize(parseInt(t.dataset.h2hRoundsize, 10)); return; }
  if (t.dataset.h2hCreate !== undefined) {
    var h2hModeSel = document.getElementById('h2h-mode');
    h2hCreateMatch(h2hModeSel ? h2hModeSel.value : state.h2h.mode);
    return;
  }
  if (t.dataset.h2hJoin !== undefined) {
    var h2hCodeInput = document.getElementById('h2h-code-input');
    h2hJoinMatch(h2hCodeInput ? h2hCodeInput.value : '');
    return;
  }
  if (t.dataset.h2hOpenCode !== undefined) { h2hOpenExistingCode(t.dataset.h2hOpenCode); return; }
  if (t.dataset.h2hStartPlay !== undefined) { h2hStartPlaying(); return; }
  if (t.dataset.h2hAnswer !== undefined) { h2hPickAnswer(parseInt(t.dataset.h2hAnswer, 10)); return; }
  if (t.dataset.h2hNext !== undefined) { h2hNextQuestion(); return; }
  if (t.dataset.h2hRematch !== undefined) { h2hRematch(); return; }
  if (t.dataset.h2hExit !== undefined) { h2hStopWatch(); goToMode('home'); return; }
  if (t.dataset.h2hLiveGoCreate !== undefined) { state.h2hLive.screen = 'create'; state.h2hLive.error = null; renderAll(); return; }
  if (t.dataset.h2hLiveGoJoin !== undefined) { state.h2hLive.screen = 'join'; state.h2hLive.error = null; renderAll(); return; }
  if (t.dataset.h2hLiveBackMenu !== undefined) { h2hLiveBackToMenu(); return; }
  if (t.dataset.h2hLiveRoundsize !== undefined) { h2hLiveSetRoundSize(parseInt(t.dataset.h2hLiveRoundsize, 10)); return; }
  if (t.dataset.h2hLiveCreate !== undefined) { h2hLiveCreateMatch(); return; }
  if (t.dataset.h2hLiveJoin !== undefined) {
    var h2hLiveCodeInput = document.getElementById('h2h-live-code-input');
    h2hLiveJoinMatch(h2hLiveCodeInput ? h2hLiveCodeInput.value : '');
    return;
  }
  if (t.dataset.h2hLiveReady !== undefined) { h2hLiveSetReady(); return; }
  if (t.dataset.h2hLiveShareLink !== undefined) { h2hLiveShareLink(t.dataset.h2hLiveShareLink, t); return; }
  if (t.dataset.h2hLiveAnswer !== undefined) { h2hLivePickAnswer(parseInt(t.dataset.h2hLiveAnswer, 10)); return; }
  if (t.dataset.h2hLiveExit !== undefined) { h2hLiveStopWatch(); goToMode('home'); return; }

  if (t.dataset.filmAssignment !== undefined) { var note = t.closest('.coverage-diagram').nextElementSibling.nextElementSibling; note.hidden = false; note.textContent = t.textContent + ': ' + (t.dataset.filmAssignment || 'Assignment not listed for this diagram.'); return; }
  if (t.dataset.filmJump !== undefined) { var group = document.getElementById('film-group-' + t.dataset.filmJump); if (group) group.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); return; }
  if (t.dataset.filmStudy !== undefined) { startFilmStudy(); return; }
  if (t.dataset.filmStudyFamily !== undefined) { startFilmStudy(t.dataset.filmStudyFamily,false); return; }
  if (t.dataset.filmBoss !== undefined) { startFilmBoss(); return; }
  if (t.dataset.filmReview !== undefined) { startFilmReview(); return; }
  if (t.dataset.filmRetry !== undefined) { var retry = state.learn.loadError; state.learn.loadError = null; if (state.learn.screen === 'study') startFilmStudy(); else openLearnSection(retry); return; }
  if (t.dataset.filmAnswer !== undefined) {
    var fs = state.filmStudy; if (!fs || fs.answered !== null) return;
    var fq = fs.questions[fs.index]; fs.answered = Number(t.dataset.filmAnswer);
    var good = fs.answered === fq.correctIndex; if (good) fs.correct++;
    fs.review.push({ q: fq, correct: good }); filmRecordRep(good,fq); playSound(good ? 'correct' : 'wrong'); renderAll(); return;
  }
  if (t.dataset.filmNext !== undefined) { if (state.filmStudy && state.filmStudy.answered !== null) { state.filmStudy.index++; state.filmStudy.answered = null; completeFilmStudySession(); renderAll(); } return; }
  if (t.dataset.filmSaved !== undefined) { state.learn.screen = 'saved'; renderAll(); return; }
  if (t.dataset.filmResume !== undefined) { var last = filmNotebook().last; if (last) { if (last.id) filmOpenConcept(last.kind, last.id); else openLearnSection(last.section); } return; }
  if (t.dataset.filmConcept !== undefined) { var parts = t.dataset.filmConcept.split(':'); filmOpenConcept(parts[0], parts.slice(1).join(':')); return; }
  if (t.dataset.filmSave !== undefined) {
    var n = filmNotebook(), e = state.encyclopedia, kind = e.conceptKind || 'concept', id = e.conceptId;
    var index = n.saved.findIndex(function(v) { return v.kind === kind && v.id === id; });
    if (index >= 0) n.saved.splice(index, 1); else n.saved.push({ kind: kind, id: id, label: document.querySelector('.film-room .panel-title').textContent });
    filmSaveNotebook(n); renderAll(); return;
  }

  if (t.dataset.learnOpen !== undefined) { openLearnSection(t.dataset.learnOpen); return; }
  if (t.dataset.learnBack !== undefined) { learnBackToMenu(); return; }
  if (t.dataset.learnCat !== undefined) { state.learn.category = t.dataset.learnCat; renderAll(); return; }
  if (t.dataset.classroomExit !== undefined) { classroomExitToLearnMenu(); return; }
  if (t.dataset.classroomLesson !== undefined) { startClassroomLesson(t.dataset.classroomLesson); return; }
  if (t.dataset.classroomPractice !== undefined) { startClassroomPractice(t.dataset.classroomPractice); return; }
  if (t.dataset.classroomPath !== undefined) { classroomBackToPath(); return; }
  if (t.dataset.classroomStepNext !== undefined) { classroomNextStep(); return; }
  if (t.dataset.classroomStepBack !== undefined) { classroomPrevStep(); return; }
  if (t.dataset.classroomAnswer !== undefined) { classroomAnswerExercise(parseInt(t.dataset.classroomAnswer, 10)); return; }
  if (t.dataset.classroomExerciseNext !== undefined) { classroomExerciseNext(); return; }
  if (t.dataset.encycDomain !== undefined) { openEncyclopediaDomain(t.dataset.encycDomain); return; }
  if (t.dataset.encycDomains !== undefined) { encyclopediaBackToDomains(); return; }
  if (t.dataset.encycOpen !== undefined) {
    var encycParts = t.dataset.encycOpen.split(':');
    openEncyclopediaConcept(encycParts[0], encycParts.slice(1).join(':'));
    return;
  }
  if (t.dataset.encycBackDomain !== undefined) {
    if (state.encyclopedia && state.encyclopedia.domainId) encyclopediaBackToDomain();
    else encyclopediaBackToDomains();
    return;
  }
  if (t.dataset.encycGotoClassroom !== undefined) {
    var gotoClassroomLessonId = null;
    if (LEARN_COVERAGES && LEARN_COVERAGES.lessons) {
      var matchLesson = LEARN_COVERAGES.lessons.find(function (l) { return l.concept === state.encyclopedia.conceptId; });
      if (matchLesson) gotoClassroomLessonId = matchLesson.lesson_id;
    }
    state.learn.screen = 'classroom';
    state.classroom = null;
    if (gotoClassroomLessonId) { renderAll(); startClassroomLesson(gotoClassroomLessonId); }
    else renderAll();
    return;
  }
  if (t.dataset.f101Toggle !== undefined) {
    var dv = state.encyclopedia.diagramView || f101DefaultDiagramView();
    dv[t.dataset.f101Toggle] = !dv[t.dataset.f101Toggle];
    state.encyclopedia.diagramView = dv;
    renderAll();
    return;
  }
  if (t.dataset.f101Reset !== undefined) { state.encyclopedia.diagramView = f101DefaultDiagramView(); renderAll(); return; }
  if (t.dataset.f101Readmode !== undefined) { state.encyclopedia.readMode = t.dataset.f101Readmode; renderAll(); return; }
  if (t.dataset.f101Player !== undefined) {
    var dv2 = state.encyclopedia.diagramView || f101DefaultDiagramView();
    dv2.activePlayerId = dv2.activePlayerId === t.dataset.f101Player ? null : t.dataset.f101Player;
    state.encyclopedia.diagramView = dv2;
    renderAll();
    return;
  }
  if (t.dataset.f101PlayerClose !== undefined) {
    if (state.encyclopedia.diagramView) state.encyclopedia.diagramView.activePlayerId = null;
    renderAll();
    return;
  }
  if (t.dataset.f101TestMe !== undefined) {
    var tmParts = t.dataset.f101TestMe.split(':');
    var tmId = tmParts[0], tmCategory = tmParts[1], tmBucket = tmParts[2];
    var tmBucketData = FOOTBALL_DIAGRAMS ? FOOTBALL_DIAGRAMS[tmBucket] : null;
    var tmDiagram = tmBucketData ? tmBucketData[tmId] : null;
    if (tmDiagram && FootballField) {
      var tmSiblings = Object.keys(tmBucketData).map(function (k) { return tmBucketData[k]; });
      var tmQ = FootballField.generateTestMeQuestion(tmDiagram, tmCategory, tmSiblings, Math.floor(Math.random() * 1000));
      if (tmQ) state.f101Quiz = { active: true, canonicalId: tmId, question: tmQ.question, options: tmQ.options, correctIndex: tmQ.correctIndex, explanation: tmDiagram.notes || tmDiagram.description || '', answeredIndex: -1 };
    }
    renderAll();
    return;
  }
  if (t.dataset.f101QuizAnswer !== undefined) {
    if (state.f101Quiz && state.f101Quiz.active && state.f101Quiz.answeredIndex === -1) {
      state.f101Quiz.answeredIndex = parseInt(t.dataset.f101QuizAnswer, 10);
      filmRecordRep(state.f101Quiz.answeredIndex === state.f101Quiz.correctIndex);
      playSound(state.f101Quiz.answeredIndex === state.f101Quiz.correctIndex ? 'correct' : 'wrong');
    }
    renderAll();
    return;
  }
  if (t.dataset.f101TestMeClose !== undefined) { state.f101Quiz = { active: false }; renderAll(); return; }
  if (t.dataset.friendAdd !== undefined) { var friendInput = document.getElementById('friend-name-input'); addFriend(friendInput ? friendInput.value : ''); return; }
  if (t.dataset.friendRemove !== undefined) { removeFriend(t.dataset.friendRemove); return; }
  if (t.dataset.friendCompare !== undefined) { state.friendCompare=t.dataset.friendCompare; renderAll(); return; }
  if (t.dataset.friendCompareClose !== undefined) { state.friendCompare=null; renderAll(); return; }
  if (t.dataset.friendChallenge !== undefined) { challengeFriendToMode(t.dataset.friendChallenge, 'quiz'); return; }
  if (t.dataset.socialChallengeMode !== undefined) { challengeFriendToMode(null, t.dataset.socialChallengeMode); return; }
  if (t.dataset.socialAccept !== undefined) { acceptSocialChallenge(t.dataset.socialAccept); return; }
  if (t.dataset.socialDecline !== undefined) { dismissSocialChallenge(t.dataset.socialDecline); return; }
  if (t.dataset.socialCopy !== undefined) { copySocialChallengeLink(t.dataset.socialCopy); return; }
  if (t.dataset.communityLeague !== undefined) { switchCommunityLeague(t.dataset.communityLeague); return; }
  if (t.dataset.communityPost !== undefined) { submitCommunityPost(); return; }
  if (t.dataset.communityPreset !== undefined) { setCommunityPreset(t.dataset.communityPreset); return; }
  if (t.dataset.profileBadge !== undefined) { selectProfileBadge(t.dataset.profileBadge); return; }
  if (t.dataset.profileCosmetic !== undefined) { selectProfileCosmetic(t.dataset.profileCosmetic); return; }
  if (t.dataset.shareDesign !== undefined) { selectShareDesign(t.dataset.shareDesign); return; }
  if (t.dataset.typeaheadPick !== undefined) {
    var taListEl = t.closest('.typeahead-list');
    var taInputId = taListEl ? taListEl.id.replace(/-typeahead$/, '') : null;
    if (taInputId && TYPEAHEAD_CONFIGS[taInputId]) { closeTypeahead(taInputId); TYPEAHEAD_CONFIGS[taInputId].onPick(t.dataset.typeaheadPick); }
    return;
  }
  if (t.dataset.leagueToggle !== undefined) { toggleModeSheet(t.dataset.leagueToggle); return; }
  if (t.id === 'mode-sheet-close' || t.id === 'mode-sheet-backdrop') { closeModeSheet(); return; }
  if (t.dataset.go !== undefined) { closeModeSheet(); goToMode(t.dataset.go); return; }

  if (t.dataset.introBegin !== undefined) { beginIntroQuestions(); return; }
  if (t.dataset.introAnswer !== undefined) { answerIntroQuestion(parseInt(t.dataset.introAnswer, 10)); return; }
  if (t.dataset.introSkip !== undefined) { e.preventDefault(); skipIntroTest(); return; }
  if (t.dataset.introContinue !== undefined) { introTestDone(); return; }
  if (t.dataset.retakeIntro !== undefined) { retakeIntroTest(); return; }

  if (t.dataset.dailyStart !== undefined) { startDailyChallenge(); return; }
  if (t.dataset.dailyAnswer !== undefined) { pickDailyAnswer(parseInt(t.dataset.dailyAnswer, 10)); return; }
  if (t.dataset.dailyConfidence !== undefined) { setDailyConfidence(parseInt(t.dataset.dailyConfidence, 10)); return; }
  if (t.dataset.dailyNext !== undefined) { nextDailyQuestion(); return; }

  if (t.dataset.rankedToggle !== undefined) {
    var parts = t.dataset.rankedToggle.split(':');
    setRankedPref(parts[0], parts[1] === '1');
    return;
  }

  if (t.dataset.quizRoundsize !== undefined) { state.quiz.roundSize = parseInt(t.dataset.quizRoundsize, 10); renderAll(); return; }
  if (t.dataset.quizStart !== undefined) {
    var cat = document.getElementById('quiz-cat'), diff = document.getElementById('quiz-diff');
    startQuizRound(cat ? cat.value : '', diff ? diff.value : '', state.quiz.roundSize);
    return;
  }
  if (t.dataset.quizAnswer !== undefined) { pickQuizAnswer(parseInt(t.dataset.quizAnswer, 10)); return; }
  if (t.dataset.quizNext !== undefined) { nextQuizQuestion(); return; }
  if (t.dataset.studyStart !== undefined) { startStudy(t.dataset.studyStart); return; }
  if (t.dataset.studyAnswer !== undefined) { pickStudyAnswer(parseInt(t.dataset.studyAnswer, 10)); return; }
  if (t.dataset.studyNext !== undefined) { nextStudyQuestion(); return; }
  if (t.dataset.quizAgain !== undefined) { playQuizAgain(); return; }
  if (t.dataset.quizSetup !== undefined) { quizBackToSetup(); return; }
  if (t.dataset.xsoRoundsize !== undefined) { state.xso.roundSize = parseInt(t.dataset.xsoRoundsize, 10); renderAll(); return; }
  if (t.dataset.xsoStart !== undefined) {
    var xsoCat = document.getElementById('xso-cat'), xsoDiff = document.getElementById('xso-diff');
    startXsoRound(xsoCat ? xsoCat.value : '', xsoDiff ? xsoDiff.value : '', state.xso.roundSize);
    return;
  }
  if (t.dataset.xsoAnswer !== undefined) { pickXsoAnswer(parseInt(t.dataset.xsoAnswer, 10)); return; }
  if (t.dataset.xsoNext !== undefined) { nextXsoQuestion(); return; }
  if (t.dataset.xsoAgain !== undefined) { playXsoAgain(); return; }
  if (t.dataset.xsoSetup !== undefined) { xsoBackToSetup(); return; }

  if (t.dataset.gridStart !== undefined) { startGridRound(); return; }
  if (t.dataset.gridCell !== undefined) { selectGridCell(parseInt(t.dataset.gridCell, 10)); return; }
  if (t.dataset.gridSubmit !== undefined) { submitGridGuess(); return; }
  if (t.dataset.gridAgain !== undefined) { startGridRound(); return; }

  if (t.dataset.cfbGridStart !== undefined) { startCfbGridRound(); return; }
  if (t.dataset.cfbGridCell !== undefined) { selectCfbGridCell(parseInt(t.dataset.cfbGridCell, 10)); return; }
  if (t.dataset.cfbGridSubmit !== undefined) { submitCfbGridGuess(); return; }
  if (t.dataset.cfbGridAgain !== undefined) { startCfbGridRound(); return; }

  if (t.dataset.blitzList !== undefined) { state.blitz = { listId: t.dataset.blitzList, screen: 'pickTimer' }; state.screen = 'blitz'; renderAll(); return; }
  if (t.dataset.blitzStart !== undefined) { startBlitz(t.dataset.blitzStart, parseInt(t.dataset.blitzTimer, 10)); return; }
  if (t.dataset.blitzSubmit !== undefined) { submitBlitzGuess(); return; }
  if (t.dataset.blitzSetup !== undefined) { state.blitz = null; renderAll(); return; }

  if (t.dataset.speedStart !== undefined) { startSpeedRound(parseInt(t.dataset.speedStart, 10)); return; }
  if (t.dataset.speedAnswer !== undefined) { registerSpeedAnswer(parseInt(t.dataset.speedAnswer, 10)); return; }
  if (t.dataset.hlCategory !== undefined) { setHigherLowerCategory(t.dataset.hlCategory); return; }
  if (t.dataset.hlStat !== undefined) { setHigherLowerStat(t.dataset.hlStat); return; }
  if (t.dataset.hlStart !== undefined) { startHigherLower(); return; }
  if (t.dataset.hlGuess !== undefined) { submitHigherLowerGuess(t.dataset.hlGuess); return; }
  if (t.dataset.hlContinue !== undefined) { higherLowerContinue(); return; }

  if (t.dataset.leaderboardMode !== undefined) { state.leaderboardMode = t.dataset.leaderboardMode; renderAll(); return; }
  if (t.dataset.leaderboardRange !== undefined) { state.leaderboardRange = t.dataset.leaderboardRange; renderAll(); return; }

  if (t.dataset.silhouetteStart !== undefined) { startSilhouetteRound(parseInt(t.dataset.silhouetteStart, 10)); return; }
  if (t.dataset.silhouetteSubmit !== undefined) { submitSilhouetteGuess(); return; }
  if (t.dataset.silhouetteHint !== undefined) { revealSilhouetteClue(); return; }
  if (t.dataset.silhouetteGiveup !== undefined) { giveUpSilhouette(); return; }
  if (t.dataset.silhouetteNext !== undefined) { advanceSilhouette(); return; }
  if (t.dataset.cluesFilterDecade !== undefined) {
    var decadeVal = t.dataset.cluesFilterDecade === 'any' ? 'any' : parseInt(t.dataset.cluesFilterDecade, 10);
    setPlayerCluesFilter('decade', decadeVal); return;
  }
  if (t.dataset.cluesFilterDifficulty !== undefined) { setPlayerCluesFilter('difficulty', t.dataset.cluesFilterDifficulty); return; }
  if (t.dataset.cluesStart !== undefined) { startPlayerCluesRound(); return; }
  if (t.dataset.cluesSubmit !== undefined) { submitPlayerCluesGuess(); return; }
  if (t.dataset.cluesHint !== undefined) { revealPlayerCluesClue(); return; }
  if (t.dataset.cluesGiveup !== undefined) { givePlayerCluesUp(); return; }
  if (t.dataset.cluesNext !== undefined) { advancePlayerClues(); return; }
  if (t.dataset.cfbCluesFilterDecade !== undefined) {
    var cfbDecadeVal = t.dataset.cfbCluesFilterDecade === 'any' ? 'any' : parseInt(t.dataset.cfbCluesFilterDecade, 10);
    setCfbPlayerCluesFilter('decade', cfbDecadeVal); return;
  }
  if (t.dataset.cfbCluesFilterDifficulty !== undefined) { setCfbPlayerCluesFilter('difficulty', t.dataset.cfbCluesFilterDifficulty); return; }
  if (t.dataset.cfbCluesStart !== undefined) { startCfbPlayerCluesRound(); return; }
  if (t.dataset.cfbCluesSubmit !== undefined) { submitCfbPlayerCluesGuess(); return; }
  if (t.dataset.cfbCluesHint !== undefined) { revealCfbPlayerCluesClue(); return; }
  if (t.dataset.cfbCluesGiveup !== undefined) { giveCfbPlayerCluesUp(); return; }
  if (t.dataset.cfbCluesNext !== undefined) { advanceCfbPlayerClues(); return; }

  if (t.dataset.pilotFranchisePick !== undefined) { state.enginePilotPendingFranchise = t.dataset.pilotFranchisePick; renderAll(); return; }
  if (t.dataset.pilotRevealClue !== undefined) {
    var pilotClueState = state.enginePilot;
    if (pilotClueState && (pilotClueState.cluesRevealedCount || 1) < 3) { pilotClueState.cluesRevealedCount = (pilotClueState.cluesRevealedCount || 1) + 1; renderAll(); }
    return;
  }
  if (t.dataset.pilotStart !== undefined) {
    var pilotCfgForStart = enginePilotModeConfig(enginePilotCurrentModeKey);
    // "Play Again" from a just-finished sequential round (state.enginePilot
    // still holds the completed round's own filterValue) reuses that same
    // real franchise -- the picker's own pending-selection state was
    // already cleared when THAT round started, so falling back to it here
    // would silently no-op Play Again for Franchise Marathon specifically.
    var filterValueForStart = (state.enginePilot && state.enginePilot.filterValue) || state.enginePilotPendingFranchise;
    if (pilotCfgForStart.needsFilterValue && !filterValueForStart) return; // Start is disabled in this state, but never proceed on no real selection
    startEnginePilotRound(undefined, filterValueForStart);
    return;
  }
  if (t.dataset.pilotAnswer !== undefined) { pickEnginePilotAnswer(parseInt(t.dataset.pilotAnswer, 10)); return; }
  if (t.dataset.pilotNext !== undefined) { advanceEnginePilot(); return; }
  if (t.dataset.pilotRetry !== undefined) { enginePilotRetry(); return; }
  if (t.dataset.pilotFallback !== undefined) { enginePilotFallback(); return; }

  if (t.dataset.mechanicStart !== undefined) { startMechanicPilotRound(); return; }
  if (t.dataset.mechanicRetry !== undefined) { mechanicPilotRetry(); return; }
  if (t.dataset.mechanicFallback !== undefined) { mechanicPilotFallback(); return; }
  if (t.dataset.mechanicNext !== undefined) { mechanicPilotAdvance(); return; }
  if (t.dataset.mechanicExit !== undefined) { state.mechanicPilot = null; goToMode('home'); return; }
  if (t.dataset.matchLeft !== undefined) {
    if (state.mechanicPilot) { state.mechanicPilot.matchSelection[t.dataset.matchLeft] = t.dataset.matchRight; renderAll(); }
    return;
  }
  if (t.dataset.matchSubmit !== undefined) {
    if (state.mechanicPilot) submitMechanicPilotAction({ mapping: state.mechanicPilot.matchSelection });
    return;
  }
  if (t.dataset.sortUp !== undefined || t.dataset.sortDown !== undefined) {
    var s = state.mechanicPilot;
    if (s && s.sortOrder) {
      var i = parseInt(t.dataset.sortUp !== undefined ? t.dataset.sortUp : t.dataset.sortDown, 10);
      var j = t.dataset.sortUp !== undefined ? i - 1 : i + 1;
      if (j >= 0 && j < s.sortOrder.length) { var tmp = s.sortOrder[i]; s.sortOrder[i] = s.sortOrder[j]; s.sortOrder[j] = tmp; renderAll(); }
    }
    return;
  }
  if (t.dataset.sortSubmit !== undefined) {
    if (state.mechanicPilot) {
      // STAT_LADDER's post-answer reveal (values_by_item_id) needs each
      // item's real label, but by the time the submit response arrives
      // s.view has already advanced to the NEXT round -- capture the
      // CURRENT round's labels now, before they're gone.
      var mp = state.mechanicPilot;
      if (mp.view && mp.view.items_shuffled) {
        mp.lastSortLabels = {};
        mp.view.items_shuffled.forEach(function (it) { mp.lastSortLabels[it.item_id] = it.label; });
      }
      submitMechanicPilotAction({ order: mp.sortOrder });
      mp.sortOrder = null;
    }
    return;
  }
  if (t.dataset.mechanicHlGuess !== undefined) { submitMechanicPilotAction({ guess: t.dataset.mechanicHlGuess }); return; }
  if (t.dataset.elimGuess !== undefined) { submitMechanicPilotAction({ guess: t.dataset.elimGuess === 'true' }); return; }
  if (t.dataset.mechanicSortFormat !== undefined) {
    if (state.mechanicPilot) { state.mechanicPilot.sortFormat = t.dataset.mechanicSortFormat; renderAll(); }
    return;
  }
  if (t.dataset.mechanicComparisonMatch !== undefined) {
    var s = state.mechanicPilot;
    var matchId = t.dataset.mechanicComparisonMatch, side = t.dataset.mechanicComparisonSide;
    var match = null;
    (s && s.view && s.view.rounds || []).some(function (r) {
      return r.matchups.some(function (m) { if (m.match_id === matchId) { match = m; return true; } return false; });
    });
    if (match) submitMechanicPilotAction({ match_id: matchId, predicted_winner: side === 'a' ? match.entrant_a : match.entrant_b });
    return;
  }

  // Finish-10-Formats pass: 5 new Mechanic Pilot interactions
  // (KNOCKOUT_TOURNAMENT reuses the existing data-mechanic-comparison-match
  // handler above unchanged -- same real view shape, same submit contract).
  if (t.dataset.mechanicGridCell !== undefined) {
    if (state.mechanicPilot) { state.mechanicPilot.gridActiveCell = t.dataset.mechanicGridCell; renderAll(); }
    return;
  }
  if (t.dataset.mechanicGridCancel !== undefined) {
    if (state.mechanicPilot) { state.mechanicPilot.gridActiveCell = null; renderAll(); }
    return;
  }
  if (t.dataset.mechanicGridSubmit !== undefined) {
    var gridKey = state.mechanicPilot && state.mechanicPilot.gridActiveCell;
    if (!gridKey) return;
    var gridParts = gridKey.split(':');
    var gridInputEl = document.getElementById('mechanic-grid-input');
    var gridGuess = gridInputEl ? gridInputEl.value.trim() : '';
    if (!gridGuess) return;
    state.mechanicPilot.gridActiveCell = null;
    submitMechanicPilotAction({ row_index: parseInt(gridParts[0], 10), col_index: parseInt(gridParts[1], 10), guess: gridGuess });
    return;
  }
  if (t.dataset.mechanicDriveAnswer !== undefined) {
    var s = state.mechanicPilot;
    var driveOptIdx = parseInt(t.dataset.mechanicDriveAnswer, 10);
    if (s && s.view && s.view.options) submitMechanicPilotAction({ answer: s.view.options[driveOptIdx] });
    return;
  }
  if (t.dataset.mechanicRosterPick !== undefined) {
    submitMechanicPilotAction({ player_id: t.dataset.mechanicRosterPick });
    return;
  }
  if (t.dataset.mechanicRosterSlot !== undefined) {
    if (state.mechanicPilot) { state.mechanicPilot.rosterOpenSlot = parseInt(t.dataset.mechanicRosterSlot, 10); renderAll(); }
    return;
  }
  if (t.dataset.mechanicRosterCandidate !== undefined) {
    var rs = state.mechanicPilot;
    if (rs && rs.rosterOpenSlot !== null && rs.rosterOpenSlot !== undefined) {
      var openSlot = rs.rosterOpenSlot;
      rs.rosterOpenSlot = null;
      submitMechanicPilotAction({ action: 'select', slot_index: openSlot, player_id: t.dataset.mechanicRosterCandidate });
    }
    return;
  }
  if (t.dataset.mechanicRosterDeselect !== undefined) {
    submitMechanicPilotAction({ action: 'deselect', slot_index: parseInt(t.dataset.mechanicRosterDeselect, 10) });
    return;
  }
  if (t.dataset.mechanicRosterSubmitLineup !== undefined) {
    submitMechanicPilotAction({ action: 'submit_lineup' });
    return;
  }
  if (t.dataset.mechanicChainSubmit !== undefined) {
    var chainInputEl = document.getElementById('mechanic-chain-input');
    var chainGuess = chainInputEl ? chainInputEl.value.trim() : '';
    if (!chainGuess) return;
    submitMechanicPilotAction({ guess: chainGuess });
    return;
  }
  if (t.dataset.mechanicSeasonSubmit !== undefined) {
    var seasonInputEl = document.getElementById('mechanic-season-input');
    var seasonGuess = seasonInputEl ? seasonInputEl.value.trim() : '';
    if (!seasonGuess) return;
    submitMechanicPilotAction({ guess_season: seasonGuess });
    return;
  }
  if (t.dataset.mechanicDuelChoice !== undefined) {
    submitMechanicPilotAction({ choice: t.dataset.mechanicDuelChoice });
    return;
  }
  if (t.dataset.mechanicImpostorPick !== undefined) {
    var impostorIdx = parseInt(t.dataset.mechanicImpostorPick, 10);
    var impostorView = state.mechanicPilot && state.mechanicPilot.view;
    var impostorItem = impostorView && impostorView.items && impostorView.items[impostorIdx];
    if (!impostorItem) return;
    submitMechanicPilotAction({ impostor_item_id: impostorItem.item_id });
    return;
  }
  if (t.dataset.mechanicMissingPiecePick !== undefined) {
    var missingPieceIdx = parseInt(t.dataset.mechanicMissingPiecePick, 10);
    var missingPieceView = state.mechanicPilot && state.mechanicPilot.view;
    var missingPieceItem = missingPieceView && missingPieceView.items && missingPieceView.items[missingPieceIdx];
    if (!missingPieceItem) return;
    submitMechanicPilotAction({ answer_item_id: missingPieceItem.item_id });
    return;
  }
  if (t.dataset.mechanicCareerPathPick !== undefined) {
    var careerPathIdx = parseInt(t.dataset.mechanicCareerPathPick, 10);
    var careerPathView = state.mechanicPilot && state.mechanicPilot.view;
    var careerPathItem = careerPathView && careerPathView.options && careerPathView.options[careerPathIdx];
    if (!careerPathItem) return;
    submitMechanicPilotAction({ guess_item_id: careerPathItem.item_id });
    return;
  }
  if (t.dataset.mechanicRiskTier !== undefined) {
    submitMechanicPilotAction({ action: 'choose_tier', tier: t.dataset.mechanicRiskTier });
    return;
  }
  if (t.dataset.mechanicRiskAnswer !== undefined) {
    var riskAnswerIdx = parseInt(t.dataset.mechanicRiskAnswer, 10);
    var riskView = state.mechanicPilot && state.mechanicPilot.view;
    var riskOption = riskView && riskView.options && riskView.options[riskAnswerIdx];
    if (!riskOption) return;
    submitMechanicPilotAction({ action: 'answer', choice_item_id: riskOption.item_id });
    return;
  }
  if (t.dataset.mechanicWagerSubmit !== undefined) {
    var wagerInputEl = document.getElementById('mechanic-wager-input');
    var wagerRaw = wagerInputEl ? wagerInputEl.value.trim() : '';
    if (!wagerRaw || !/^\d+$/.test(wagerRaw)) return;
    submitMechanicPilotAction({ action: 'place_wager', wager: parseInt(wagerRaw, 10) });
    return;
  }
  if (t.dataset.mechanicWagerAnswer !== undefined) {
    var wagerAnswerIdx = parseInt(t.dataset.mechanicWagerAnswer, 10);
    var wagerView = state.mechanicPilot && state.mechanicPilot.view;
    var wagerOption = wagerView && wagerView.options && wagerView.options[wagerAnswerIdx];
    if (!wagerOption) return;
    submitMechanicPilotAction({ action: 'answer', choice_item_id: wagerOption.item_id });
    return;
  }
  if (t.dataset.mechanicBlindResumePick !== undefined) {
    var blindResumeIdx = parseInt(t.dataset.mechanicBlindResumePick, 10);
    var blindResumeView = state.mechanicPilot && state.mechanicPilot.view;
    var blindResumeOption = blindResumeView && blindResumeView.options && blindResumeView.options[blindResumeIdx];
    if (!blindResumeOption) return;
    submitMechanicPilotAction({ choice_item_id: blindResumeOption.item_id });
    return;
  }
  if (t.dataset.mechanicDonAnswer !== undefined) {
    var donAnswerIdx = parseInt(t.dataset.mechanicDonAnswer, 10);
    var donView = state.mechanicPilot && state.mechanicPilot.view;
    var donOption = donView && donView.options && donView.options[donAnswerIdx];
    if (!donOption) return;
    submitMechanicPilotAction({ action: 'answer', choice_item_id: donOption.item_id });
    return;
  }
  if (t.dataset.mechanicDonBank !== undefined) {
    submitMechanicPilotAction({ action: 'bank' });
    return;
  }
  if (t.dataset.mechanicGuessTheRankingPick !== undefined) {
    var gtrIdx = parseInt(t.dataset.mechanicGuessTheRankingPick, 10);
    var gtrView = state.mechanicPilot && state.mechanicPilot.view;
    var gtrOption = gtrView && gtrView.options && gtrView.options[gtrIdx];
    if (!gtrOption) return;
    submitMechanicPilotAction({ choice_item_id: gtrOption.item_id });
    return;
  }
  if (t.dataset.mechanicStatTargetPick !== undefined) {
    var stIdx = parseInt(t.dataset.mechanicStatTargetPick, 10);
    var stView = state.mechanicPilot && state.mechanicPilot.view;
    var stOption = stView && stView.options && stView.options[stIdx];
    if (!stOption) return;
    submitMechanicPilotAction({ choice_item_id: stOption.item_id });
    return;
  }
  if (t.dataset.mechanicReverseTriviaPick !== undefined) {
    var rtIdx = parseInt(t.dataset.mechanicReverseTriviaPick, 10);
    var rtView = state.mechanicPilot && state.mechanicPilot.view;
    var rtOption = rtView && rtView.options && rtView.options[rtIdx];
    if (!rtOption) return;
    submitMechanicPilotAction({ choice_item_id: rtOption.item_id });
    return;
  }
  if (t.dataset.mechanicThreeStrikesAnswer !== undefined) {
    var tsIdx = parseInt(t.dataset.mechanicThreeStrikesAnswer, 10);
    var tsView = state.mechanicPilot && state.mechanicPilot.view;
    var tsOption = tsView && tsView.options && tsView.options[tsIdx];
    if (!tsOption) return;
    submitMechanicPilotAction({ choice_item_id: tsOption.item_id });
    return;
  }
  if (t.dataset.mechanicMysteryReveal !== undefined) {
    submitMechanicPilotAction({ action: 'reveal' });
    return;
  }
  if (t.dataset.mechanicMysteryGuess !== undefined) {
    var mrIdx = parseInt(t.dataset.mechanicMysteryGuess, 10);
    var mrView = state.mechanicPilot && state.mechanicPilot.view;
    var mrOption = mrView && mrView.options && mrView.options[mrIdx];
    if (!mrOption) return;
    submitMechanicPilotAction({ action: 'guess', choice_item_id: mrOption.item_id });
    return;
  }
  if (t.dataset.mechanicDraftPickLadderPick !== undefined) {
    var dplIdx = parseInt(t.dataset.mechanicDraftPickLadderPick, 10);
    var dplView = state.mechanicPilot && state.mechanicPilot.view;
    var dplOption = dplView && dplView.options && dplView.options[dplIdx];
    if (!dplOption) return;
    submitMechanicPilotAction({ choice_item_id: dplOption.item_id });
    return;
  }
  if (t.dataset.mechanicCategoryRoulettePick !== undefined) {
    var crIdx = parseInt(t.dataset.mechanicCategoryRoulettePick, 10);
    var crView = state.mechanicPilot && state.mechanicPilot.view;
    var crOption = crView && crView.options && crView.options[crIdx];
    if (!crOption) return;
    submitMechanicPilotAction({ choice_item_id: crOption.item_id });
    return;
  }
  if (t.dataset.mechanicCommonLinkPick !== undefined) {
    var clIdx = parseInt(t.dataset.mechanicCommonLinkPick, 10);
    var clView = state.mechanicPilot && state.mechanicPilot.view;
    var clOption = clView && clView.options && clView.options[clIdx];
    if (!clOption) return;
    submitMechanicPilotAction({ choice_item_id: clOption.item_id });
    return;
  }
  if (t.dataset.mechanicBranchChoice !== undefined) {
    submitMechanicPilotAction({ choice_id: t.dataset.mechanicBranchChoice });
    return;
  }
  if (t.dataset.mechanicBranchAnswer !== undefined) {
    var bs = state.mechanicPilot;
    var branchOptIdx = parseInt(t.dataset.mechanicBranchAnswer, 10);
    if (bs && bs.view && bs.view.options) submitMechanicPilotAction({ answer: bs.view.options[branchOptIdx] });
    return;
  }

  if (t.dataset.sixdegreesStart !== undefined) { startSixDegreesRound(); return; }
  if (t.dataset.sixdegreesPickId !== undefined) {
    submitSixDegreesMove(t.dataset.sixdegreesPickType, t.dataset.sixdegreesPickId, t.dataset.sixdegreesPickName);
    return;
  }
  if (t.dataset.sixdegreesRetry !== undefined) { loadSixDegreesGame(); return; }
  if (t.dataset.sixdegreesFallback !== undefined) { sixDegreesFallback(); return; }
  if (t.dataset.sixdegreesReveal !== undefined) { revealSixDegrees(); return; }
  if (t.dataset.sixdegreesGiveup !== undefined) { giveUpSixDegrees(); return; }
  if (t.dataset.pickemSlate !== undefined) { changePickemSlate(t.dataset.pickemSlate, null); return; }
  if (t.dataset.pickemConference !== undefined) { changePickemSlate('CONFERENCE', t.dataset.pickemConference); return; }
  if (t.dataset.pickemGame !== undefined) { submitPickemPick(t.dataset.pickemGame, t.dataset.pickemTeam); return; }
  if (t.dataset.pickemRetry !== undefined) { loadPickemView(); return; }
  if (t.dataset.liveFootballOpen !== undefined) { openLiveFootballHub(); return; }
  if (t.dataset.liveFootballRefresh !== undefined) { liveFootballMaybeRefresh(true); renderAll(); return; }
  if (t.dataset.liveGameChallenge !== undefined) { startLiveFootballChallenge(t.dataset.liveGameChallenge); return; }
  if (t.dataset.liveChallengeStart !== undefined) { startLiveFootballChallenge(null); return; }
  if (t.dataset.liveChallengeAnswer !== undefined) { answerLiveFootballChallenge(t.dataset.liveChallengeAnswer); return; }
  if (t.dataset.liveChallengeNext !== undefined) { nextLiveFootballChallenge(); return; }
  if (t.dataset.liveChallengeClose !== undefined) { LIVE_FOOTBALL.challenge = null; renderAll(); return; }
  if (t.dataset.endlessStart !== undefined) { startEndlessMode(); return; }
  if (t.dataset.endlessAnswer !== undefined) { answerEndless(Number(t.dataset.endlessAnswer)); return; }
  if (t.dataset.endlessNext !== undefined) { nextEndless(); return; }
  if (t.id === 'creator-auth-submit' || t.dataset.creatorAuthSubmit !== undefined) {
    var tokenInput = document.getElementById('creator-token-input');
    creatorSubmitToken(tokenInput ? tokenInput.value : '');
    return;
  }
  if (t.dataset.creatorLogout !== undefined) { creatorLogout(); return; }
  if (t.dataset.creatorNav === 'home') { creatorGoHome(); return; }
  if (t.dataset.creatorNav === 'queue') { creatorLoadQueue(''); return; }
  if (t.dataset.creatorNav === 'capabilities') { creatorLoadCapabilities(); return; }
  if (t.dataset.creatorQueueFilter !== undefined) { creatorLoadQueue(t.dataset.creatorQueueFilter); return; }
  if (t.dataset.creatorCheckFeasibility !== undefined) {
    var reqInput = document.getElementById('creator-request-input');
    creatorCheckFeasibility(reqInput ? reqInput.value.trim() : '');
    return;
  }
  if (t.dataset.creatorGenerate !== undefined) { creatorGenerate(); return; }
  if (t.dataset.creatorExample !== undefined) { creatorUseExample(t.dataset.creatorExample); return; }
  if (t.dataset.creatorFormatPick !== undefined) { creatorPickFormat(parseInt(t.dataset.creatorFormatPick, 10)); return; }
  if (t.dataset.creatorReview !== undefined) { creatorSetReview(t.dataset.creatorPackageId, t.dataset.creatorReview); return; }

  if (t.dataset.iqStart !== undefined) { startIQTest(); return; }
  if (t.dataset.iqAnswer !== undefined) { answerIQQuestion(parseInt(t.dataset.iqAnswer, 10)); return; }

  if (t.dataset.legendsStart !== undefined) { startLegends(); return; }
  if (t.dataset.legendsPick !== undefined) { legendsPickPlayer(parseInt(t.dataset.legendsPick, 10)); return; }
  if (t.dataset.legendsRerollTeam !== undefined) { legendsRerollTeam(); return; }
  if (t.dataset.legendsRerollYear !== undefined) { legendsRerollYear(); return; }

  if (t.dataset.cfbLegendsStart !== undefined) { startCfbLegends(); return; }
  if (t.dataset.cfbLegendsPick !== undefined) { cfbLegendsPickPlayer(parseInt(t.dataset.cfbLegendsPick, 10)); return; }
  if (t.dataset.cfbLegendsRerollTeam !== undefined) { cfbLegendsRerollTeam(); return; }
  if (t.dataset.cfbLegendsRerollYear !== undefined) { cfbLegendsRerollYear(); return; }

  if (t.dataset.cfbRoundsize !== undefined) { state.cfbQuiz.roundSize = parseInt(t.dataset.cfbRoundsize, 10); renderAll(); return; }
  if (t.dataset.cfbStart !== undefined) {
    var cfbCat = document.getElementById('cfb-cat'), cfbDiff = document.getElementById('cfb-diff');
    startCfbQuizRound(cfbCat ? cfbCat.value : '', cfbDiff ? cfbDiff.value : '', state.cfbQuiz.roundSize);
    return;
  }
  if (t.dataset.cfbAnswer !== undefined) { pickCfbAnswer(parseInt(t.dataset.cfbAnswer, 10)); return; }
  if (t.dataset.cfbNext !== undefined) { nextCfbQuestion(); return; }
  if (t.dataset.cfbAgain !== undefined) { playCfbAgain(); return; }
  if (t.dataset.cfbSetup !== undefined) { cfbBackToSetup(); return; }

  if (t.dataset.cfbIqStart !== undefined) { startCfbIQTest(); return; }
  if (t.dataset.cfbIqAnswer !== undefined) { answerCfbIQQuestion(parseInt(t.dataset.cfbIqAnswer, 10)); return; }

  if (t.dataset.cfbSpeedStart !== undefined) { startCfbSpeedRound(parseInt(t.dataset.cfbSpeedStart, 10)); return; }
  if (t.dataset.cfbSpeedAnswer !== undefined) { registerCfbSpeedAnswer(parseInt(t.dataset.cfbSpeedAnswer, 10)); return; }

  if (t.dataset.cfbBlitzList !== undefined) { state.cfbBlitz = { listId: t.dataset.cfbBlitzList, screen: 'pickTimer' }; state.screen = 'cfbBlitz'; renderAll(); return; }
  if (t.dataset.cfbBlitzStart !== undefined) { startCfbBlitz(t.dataset.cfbBlitzStart, parseInt(t.dataset.cfbBlitzTimer, 10)); return; }
  if (t.dataset.cfbBlitzSubmit !== undefined) { submitCfbBlitzGuess(); return; }
  if (t.dataset.cfbBlitzSetup !== undefined) { state.cfbBlitz = null; renderAll(); return; }

  if (t.dataset.modeRestart !== undefined) {
    if (t.dataset.modeRestart === 'endless') { startEndlessMode(); return; }
    stopTimers(); resetModeState(t.dataset.modeRestart); renderAll(); return;
  }
  if (t.dataset.modeExit !== undefined) { goToMode('home'); return; }
});

// Mobile keyboard polish: on a touch/coarse-pointer device (matchMedia guard
// so desktop mouse users never get an unwanted scroll-jump), nudge a just-
// focused game-answer input into view once the on-screen keyboard has had a
// moment to animate in. 'focus' doesn't bubble, so this needs the capture
// phase. Works alongside interactive-widget=resizes-content in index.html
// (which shrinks the layout viewport instead of letting the keyboard just
// overlay it) rather than replacing it — belt and suspenders, since browser
// support for that meta value still varies.
var MOBILE_KEYBOARD_INPUT_IDS = ['grid-input', 'cfb-grid-input', 'blitz-input', 'cfb-blitz-input', 'silhouette-input', 'clues-input', 'cfb-clues-input', 'sixdegrees-search-input'];
document.addEventListener('focus', function (e) {
  if (MOBILE_KEYBOARD_INPUT_IDS.indexOf(e.target.id) === -1) return;
  if (!window.matchMedia || !window.matchMedia('(pointer: coarse)').matches) return;
  var el = e.target;
  setTimeout(function () { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, 250);
}, true);
// blur fires (and a click-delegate handler runs closeTypeahead itself once a
// pick is actually made) before a tap on a suggestion button's own click
// event has a chance to fire — closing the list immediately here would
// remove it from the DOM mid-tap and the pick would silently do nothing.
// Delaying long enough for that click to land, then closing only if nothing
// else already did, is the standard fix for this exact race.
document.addEventListener('blur', function (e) {
  if (e.target.id === 'sixdegrees-search-input') {
    setTimeout(sixDegreesCloseSearch, 200);
    return;
  }
  if (!TYPEAHEAD_CONFIGS[e.target.id]) return;
  setTimeout(function () { closeTypeahead(e.target.id); }, 200);
}, true);

document.addEventListener('input', function (e) {
  if (e.target.id === 'grid-input') { state.grid.input = e.target.value; renderTypeahead('grid-input'); return; }
  if (e.target.id === 'cfb-grid-input') { state.cfbGrid.input = e.target.value; renderTypeahead('cfb-grid-input'); return; }
  if (e.target.id === 'blitz-input') { state.blitz.input = e.target.value; return; }
  if (e.target.id === 'cfb-blitz-input') { state.cfbBlitz.input = e.target.value; return; }
  if (e.target.id === 'silhouette-input') { state.silhouette.input = e.target.value; renderTypeahead('silhouette-input'); return; }
  if (e.target.id === 'clues-input') { state.playerClues.input = e.target.value; renderTypeahead('clues-input'); return; }
  // Real bug found: this CFB counterpart was missing entirely -- typing in
  // the CFB Player From Clues box never updated state.cfbPlayerClues.input
  // (stuck at '' forever) and never rendered the typeahead dropdown, so a
  // player could type a name but Guess always submitted an empty string and
  // no suggestion list ever appeared to pick from.
  if (e.target.id === 'cfb-clues-input') { state.cfbPlayerClues.input = e.target.value; renderTypeahead('cfb-clues-input'); return; }
  if (e.target.id === 'sixdegrees-search-input') { sixDegreesOnSearchInput(e.target.value); return; }
  // Unlike the inputs above (which only read their value on submit, no
  // re-render per keystroke), the Learn filter box needs to narrow the
  // table live as you type — see renderAll()'s focus-preservation block
  // for the matching refocus step this requires.
  if (e.target.id === 'film-search-input') { state.learn.filmFilter = e.target.value; renderAll(); return; }
  if (e.target.id === 'learn-filter-input') { state.learn.filter = e.target.value; renderAll(); return; }
  if (e.target.id === 'encyclopedia-search-input') { state.encyclopedia.filter = e.target.value; renderAll(); return; }
  if (e.target.id === 'team-picker-search') { teamPickerSetFilter(e.target.value); return; }
  if (e.target.id === 'community-post-input') { communityDraft = e.target.value; return; }
});

document.addEventListener('change', function (e) {
  if (e.target.id === 'quiz-cat') { state.quiz.category = e.target.value; return; }
  if (e.target.id === 'quiz-diff') { state.quiz.difficulty = e.target.value; return; }
  if (e.target.id === 'xso-cat') { state.xso.category = e.target.value; return; }
  if (e.target.id === 'xso-diff') { state.xso.difficulty = e.target.value; return; }
  if (e.target.id === 'cfb-cat') { state.cfbQuiz.category = e.target.value; return; }
  if (e.target.id === 'cfb-diff') { state.cfbQuiz.difficulty = e.target.value; return; }
  if (e.target.id === 'h2h-mode') { h2hSetMode(e.target.value); return; }
  if (e.target.id === 'h2h-list') { h2hSetList(e.target.value); return; }
  if (e.target.id === 'h2h-live-mode') { h2hLiveSetMode(e.target.value); return; }
});

// Keeps Tab cycling inside an open modal instead of escaping to whatever's
// behind the backdrop (standard WAI-ARIA dialog pattern) — Shift+Tab off the
// first focusable element wraps to the last, and Tab off the last wraps back
// to the first. Called from the keydown handler below, once per open dialog.
function trapTabKey(e, container) {
  var focusables = container.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
  if (!focusables.length) return;
  var first = focusables[0], last = focusables[focusables.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}
document.addEventListener('keydown', function (e) {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('[data-f101-player]')) { e.preventDefault(); e.target.dispatchEvent(new MouseEvent('click', { bubbles: true })); return; }
  var modeSheetEl = document.getElementById('mode-sheet');
  var onboardingModalEl = document.getElementById('onboarding-modal');
  var shareModalEl = document.getElementById('share-modal');
  var reportModalEl = document.getElementById('report-modal');
  var ratingModalEl = document.getElementById('rating-modal');
  var teamPickerModalEl = document.getElementById('team-picker-modal');
  var authModalEl = document.getElementById('auth-modal');
  if (e.key === 'Escape' && TYPEAHEAD_CONFIGS[e.target.id] && typeaheadListEl(e.target.id) && typeaheadListEl(e.target.id).classList.contains('open')) {
    closeTypeahead(e.target.id);
    return;
  }
  if (e.key === 'Escape' && e.target.id === 'sixdegrees-search-input') {
    sixDegreesCloseSearch();
    return;
  }
  if (e.key === 'Escape' && modeSheetOpenLeague) { closeModeSheet(); return; }
  if (e.key === 'Escape' && onboardingModalEl && onboardingModalEl.classList.contains('open')) { closeOnboarding(); return; }
  if (e.key === 'Escape' && shareModalEl && shareModalEl.classList.contains('open')) { closeShareModal(); return; }
  if (e.key === 'Escape' && reportModalEl && reportModalEl.classList.contains('open')) { closeReportModal(); return; }
  if (e.key === 'Escape' && ratingModalEl && ratingModalEl.classList.contains('open')) { closeRatingModal(); return; }
  if (e.key === 'Escape' && teamPickerModalEl && teamPickerModalEl.classList.contains('open')) { closeTeamPicker(); return; }
  if (e.key === 'Escape' && authModalEl && authModalEl.classList.contains('open')) { closeAuthModal(); return; }
  if (e.key === 'Tab') {
    if (modeSheetEl && modeSheetEl.classList.contains('open')) { trapTabKey(e, modeSheetEl); return; }
    if (onboardingModalEl && onboardingModalEl.classList.contains('open')) { trapTabKey(e, onboardingModalEl); return; }
    if (shareModalEl && shareModalEl.classList.contains('open')) { trapTabKey(e, shareModalEl); return; }
    if (reportModalEl && reportModalEl.classList.contains('open')) { trapTabKey(e, reportModalEl); return; }
    if (ratingModalEl && ratingModalEl.classList.contains('open')) { trapTabKey(e, ratingModalEl); return; }
    if (teamPickerModalEl && teamPickerModalEl.classList.contains('open')) { trapTabKey(e, teamPickerModalEl); return; }
    if (authModalEl && authModalEl.classList.contains('open')) { trapTabKey(e, authModalEl); return; }
    return;
  }
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && TYPEAHEAD_CONFIGS[e.target.id]) {
    if (typeaheadMove(e.target.id, e.key === 'ArrowDown' ? 1 : -1)) e.preventDefault();
    return;
  }
  if (e.key !== 'Enter') return;
  if (e.target.id === 'grid-input') { if (!typeaheadPickActive('grid-input')) submitGridGuess(); }
  else if (e.target.id === 'cfb-grid-input') { if (!typeaheadPickActive('cfb-grid-input')) submitCfbGridGuess(); }
  else if (e.target.id === 'blitz-input') { submitBlitzGuess(); }
  else if (e.target.id === 'cfb-blitz-input') { submitCfbBlitzGuess(); }
  else if (e.target.id === 'silhouette-input') { if (!typeaheadPickActive('silhouette-input')) submitSilhouetteGuess(); }
  else if (e.target.id === 'clues-input') { if (!typeaheadPickActive('clues-input')) submitPlayerCluesGuess(); }
  else if (e.target.id === 'cfb-clues-input') { if (!typeaheadPickActive('cfb-clues-input')) submitCfbPlayerCluesGuess(); }
  else if (e.target.id === 'sixdegrees-search-input') { sixDegreesPickTopResult(); }
  else if (e.target.id === 'auth-username-input' || e.target.id === 'auth-password-input') { authModalSubmit(); }
  else if (e.target.id === 'friend-name-input') { addFriend(e.target.value); }
});

/* ============================== init ============================== */
// Grid/CFB-Grid/Silhouette datalists are (re)built once their data file
// loads — see goToMode's lazy-load branch above — not unconditionally here,
// since GRID_PLAYERS/CFB_GRID_PLAYERS/SILHOUETTE_PLAYERS are empty until then.
var footerVersionEl = document.getElementById('footer-version');
if (footerVersionEl) footerVersionEl.textContent = 'Reads v' + APP_VERSION + ' · Questions last updated ' + CONTENT_UPDATED;

// A live-match invite link (see h2hLiveInviteLink) looks like
// https://reads.football/#live=7F3K — captured and cleared from the
// URL immediately so refreshing or re-sharing the plain page URL later
// can't re-trigger a join. Consumed right here if this device already has a
// name (the common case — a friend who already plays tapping another
// friend's link), or later via consumePendingLiveJoin() from saveName()/
// introTestDone()/skipIntroTest() if this is a brand-new visitor who still
// has to pick a name and take the intro test first.
var pendingSocialChallengeCode = null;
var socialChallengeHashMatch = /^#challenge=([A-Za-z0-9]{4})$/.exec(location.hash);
if (socialChallengeHashMatch) {
  pendingSocialChallengeCode = socialChallengeHashMatch[1].toUpperCase();
  history.replaceState(null, '', location.pathname + location.search);
}
function consumePendingSocialChallenge() {
  if (!pendingSocialChallengeCode || !state.name) return false;
  var code = pendingSocialChallengeCode;
  pendingSocialChallengeCode = null;
  state.h2h = { screen:'join', mode:'quiz', roundSize:10, listId:null, error:null };
  state.screen = 'h2h';
  h2hJoinMatch(code);
  return true;
}
var pendingLiveJoinCode = null;
var liveHashMatch = /^#live=([A-Za-z0-9]{4})$/.exec(location.hash);
if (liveHashMatch) {
  pendingLiveJoinCode = liveHashMatch[1].toUpperCase();
  history.replaceState(null, '', location.pathname + location.search);
}
function consumePendingLiveJoin() {
  if (!pendingLiveJoinCode || !state.name) return false;
  var code = pendingLiveJoinCode;
  pendingLiveJoinCode = null;
  state.screen = 'h2hLive';
  state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  h2hLiveJoinMatch(code);
  return true;
}

initPlayerCluesPackage();
initCfbPlayerCluesPackage();
var HIDDEN_ROUTES = { '#stats': 'stats', '#reports': 'reports', '#creator': 'creator' };
if (ENABLE_PLAYER_FROM_CLUES_V01) HIDDEN_ROUTES['#clues'] = 'playerClues';
if (ENABLE_ENGINE_DRAFT_PILOT_V01) HIDDEN_ROUTES['#draftpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01) HIDDEN_ROUTES['#championshippilot'] = 'enginePilot';
if (ENABLE_ENGINE_LINEUP_PILOT_V01) HIDDEN_ROUTES['#lineuppilot'] = 'enginePilot';
if (ENABLE_ENGINE_HEISMAN_PILOT_V01) HIDDEN_ROUTES['#heismanpilot'] = 'enginePilot';
// Public-readiness punch-list: same registration pattern for the 4 modes
// this pass wired into the shared Engine Pilot shell.
if (ENABLE_ENGINE_LINEUP_COLLEGE_PILOT_V01) HIDDEN_ROUTES['#lineupcollegepilot'] = 'enginePilot';
if (ENABLE_ENGINE_NFL_GAME_RESULT_PILOT_V01) HIDDEN_ROUTES['#nflgameresultpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_GAME_RESULT_PILOT_V01) HIDDEN_ROUTES['#cfbgameresultpilot'] = 'enginePilot';
if (ENABLE_ENGINE_NFL_GAME_BOXSCORE_PILOT_V01) HIDDEN_ROUTES['#nflgameboxscorepilot'] = 'enginePilot';
// Creator stress test / discovery pass: same registration pattern for the
// 4 modes newly promoted to public certification this pass.
if (ENABLE_ENGINE_OFFENSE_COLLEGE_PILOT_V01) HIDDEN_ROUTES['#offensecollegepilot'] = 'enginePilot';
if (ENABLE_ENGINE_SB_CHAMPION_OFFENSE_COLLEGE_PILOT_V01) HIDDEN_ROUTES['#sbchampionoffensecollegepilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_RANKING_PILOT_V01) HIDDEN_ROUTES['#cfbrankingpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_UPSET_PILOT_V01) HIDDEN_ROUTES['#cfbupsetpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_RIVALRY_PILOT_V01) HIDDEN_ROUTES['#cfbrivalrypilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_RIVALRY_LOOKUP_PILOT_V01) HIDDEN_ROUTES['#cfbrivalrylookuppilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_SPOT_THE_FAKE_PILOT_V01) HIDDEN_ROUTES['#spotthefakepilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_THREE_CLUES_PILOT_V01) HIDDEN_ROUTES['#threecluespilot'] = 'enginePilot';
if (ENABLE_ENGINE_ERA_GAUNTLET_PILOT_V01) HIDDEN_ROUTES['#eragauntletpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_ODD_COLLEGE_OUT_PILOT_V01) HIDDEN_ROUTES['#oddcollegeoutpilot'] = 'enginePilot';
if (ENABLE_ENGINE_CFB_ONE_SCHOOL_MISSING_PILOT_V01) HIDDEN_ROUTES['#oneschoolmissingpilot'] = 'enginePilot';
if (ENABLE_ENGINE_FRANCHISE_MARATHON_PILOT_V01) HIDDEN_ROUTES['#franchisemarathonpilot'] = 'enginePilot';
// Public-readiness punch-list: the 4 new-shape mechanic-pilot modes route
// to their own 'mechanicPilot' screen (a separate shared shell -- see
// engine-game-ui.js's own module comment for why these don't fit the
// single-question enginePilot shell).
if (ENABLE_ENGINE_MATCHING_PILOT_V01) HIDDEN_ROUTES['#matchingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_SORTING_PILOT_V01) HIDDEN_ROUTES['#sortingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_STAT_LADDER_PILOT_V01) HIDDEN_ROUTES['#statladdernflrushingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_STAT_LADDER_PILOT_V01) HIDDEN_ROUTES['#statladdernflpassingtdpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_STAT_LADDER_PILOT_V01) HIDDEN_ROUTES['#statladdercfbrushingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_HIGHER_LOWER_PILOT_V01) HIDDEN_ROUTES['#higherlowerenginepilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_ELIMINATION_PILOT_V01) HIDDEN_ROUTES['#eliminationpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_COMPARISON_PILOT_V01) HIDDEN_ROUTES['#comparisonpilot'] = 'mechanicPilot';
// Finish-10-Formats pass: same registration pattern for the 10 new real
// game formats, all routed through the shared 'mechanicPilot' screen.
if (ENABLE_ENGINE_CONNECTION_GRID_PILOT_V01) HIDDEN_ROUTES['#connectiongridpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_PERFECT_DRIVE_PILOT_V01) HIDDEN_ROUTES['#perfectdrivenflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_PERFECT_DRIVE_PILOT_V01) HIDDEN_ROUTES['#perfectdrivecfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_GOAL_LINE_STAND_PILOT_V01) HIDDEN_ROUTES['#goallinestandnflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_GOAL_LINE_STAND_PILOT_V01) HIDDEN_ROUTES['#goallinestandcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_LINEUP_BUILDER_PILOT_V01) HIDDEN_ROUTES['#lineupbuildernflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_LINEUP_BUILDER_PILOT_V01) HIDDEN_ROUTES['#lineupbuildercfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_AUCTION_DRAFT_PILOT_V01) HIDDEN_ROUTES['#auctiondraftnflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_AUCTION_DRAFT_PILOT_V01) HIDDEN_ROUTES['#auctiondraftcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CAP_CHALLENGE_PILOT_V01) HIDDEN_ROUTES['#capchallengenflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CAP_CHALLENGE_PILOT_V01) HIDDEN_ROUTES['#capchallengecfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_KNOCKOUT_TOURNAMENT_PILOT_V01) HIDDEN_ROUTES['#knockouttournamentnflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_KNOCKOUT_TOURNAMENT_PILOT_V01) HIDDEN_ROUTES['#knockouttournamentcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_SIX_DEGREES_CHAIN_PILOT_V01) HIDDEN_ROUTES['#sixdegreeschainpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CHAIN_REACTION_PILOT_V01) HIDDEN_ROUTES['#chainreactionpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CHOOSE_YOUR_PATH_PILOT_V01) HIDDEN_ROUTES['#chooseyourpathpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CHOOSE_YOUR_PATH_PILOT_V01) HIDDEN_ROUTES['#chooseyourpathcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_GUESS_THE_SEASON_PILOT_V01) HIDDEN_ROUTES['#guesstheseasonpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01) HIDDEN_ROUTES['#headtoheadduelrushingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01) HIDDEN_ROUTES['#headtoheadduelpassingtdpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01) HIDDEN_ROUTES['#headtoheadduelcfbrushingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_BEST_OF_SEVEN_DUEL_PILOT_V01) HIDDEN_ROUTES['#bestofsevenduelpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_PICK_THE_IMPOSTOR_PILOT_V01) HIDDEN_ROUTES['#picktheimpostornflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_PICK_THE_IMPOSTOR_PILOT_V01) HIDDEN_ROUTES['#picktheimpostorcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_UNIQUE_ONE_OUT_PILOT_V01) HIDDEN_ROUTES['#uniqueoneoutpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MISSING_PIECE_PILOT_V01) HIDDEN_ROUTES['#missingpiecenflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MISSING_PIECE_PILOT_V01) HIDDEN_ROUTES['#missingpiececfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_BEFORE_AFTER_PILOT_V01) HIDDEN_ROUTES['#beforeafternflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_BEFORE_AFTER_PILOT_V01) HIDDEN_ROUTES['#beforeaftercfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MAP_THE_CAREER_PILOT_V01) HIDDEN_ROUTES['#mapthecareernflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MAP_THE_CAREER_PILOT_V01) HIDDEN_ROUTES['#mapthecareercfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CAREER_PATH_PILOT_V01) HIDDEN_ROUTES['#careerpathnflpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CAREER_PATH_PILOT_V01) HIDDEN_ROUTES['#careerpathcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_RISK_IT_PILOT_V01) HIDDEN_ROUTES['#riskitpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_RISK_IT_PILOT_V01) HIDDEN_ROUTES['#riskitcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_WAGER_MODE_PILOT_V01) HIDDEN_ROUTES['#wagermodepilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_LEADERBOARD_CLIMB_PILOT_V01) HIDDEN_ROUTES['#leaderboardclimbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_BLIND_RESUME_PILOT_V01) HIDDEN_ROUTES['#blindresumepilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_BLIND_RESUME_PILOT_V01) HIDDEN_ROUTES['#blindresumecfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_DOUBLE_OR_NOTHING_PILOT_V01) HIDDEN_ROUTES['#doubleornothingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_DOUBLE_OR_NOTHING_PILOT_V01) HIDDEN_ROUTES['#doubleornothingcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_KING_OF_THE_HILL_PILOT_V01) HIDDEN_ROUTES['#kingofthehillpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_KING_OF_THE_HILL_PILOT_V01) HIDDEN_ROUTES['#kingofthehillcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_FACT_OR_FAKE_PILOT_V01) HIDDEN_ROUTES['#factorfakepilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_FACT_OR_FAKE_PILOT_V01) HIDDEN_ROUTES['#factorfakecfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_GUESS_THE_RANKING_PILOT_V01) HIDDEN_ROUTES['#guesstherankingpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_GUESS_THE_RANKING_PILOT_V01) HIDDEN_ROUTES['#guesstherankingcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_STAT_TARGET_PILOT_V01) HIDDEN_ROUTES['#stattargetpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_STAT_TARGET_PILOT_V01) HIDDEN_ROUTES['#stattargetcfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_REVERSE_TRIVIA_PILOT_V01) HIDDEN_ROUTES['#reversetriviapilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_REVERSE_TRIVIA_PILOT_V01) HIDDEN_ROUTES['#reversetriviacfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_THREE_STRIKES_PILOT_V01) HIDDEN_ROUTES['#threestrikespilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_THREE_STRIKES_PILOT_V01) HIDDEN_ROUTES['#threestrikescfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MYSTERY_ROSTER_PILOT_V01) HIDDEN_ROUTES['#mysteryrosterpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_MYSTERY_ROSTER_PILOT_V01) HIDDEN_ROUTES['#mysteryrostercfbpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_DRAFT_PICK_LADDER_PILOT_V01) HIDDEN_ROUTES['#draftpickladderpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_CATEGORY_ROULETTE_PILOT_V01) HIDDEN_ROUTES['#categoryroulettepilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_COMMON_LINK_PILOT_V01) HIDDEN_ROUTES['#commonlinkpilot'] = 'mechanicPilot';
if (ENABLE_ENGINE_COMMON_LINK_PILOT_V01) HIDDEN_ROUTES['#commonlinkcfbpilot'] = 'mechanicPilot';
if (HIDDEN_ROUTES[location.hash]) {
  state.screen = HIDDEN_ROUTES[location.hash];
  // Both engine-pilot hashes map to the same 'enginePilot' screen (Part 9:
  // one shared adapter) -- this is the one place that resolves WHICH pilot
  // a bare hash visit means, before any round/state.enginePilot exists.
  if (location.hash === ENGINE_PILOT_MODES.championship.hash) enginePilotCurrentModeKey = 'championship';
  else if (location.hash === ENGINE_PILOT_MODES.draft.hash) enginePilotCurrentModeKey = 'draft';
  else if (location.hash === ENGINE_PILOT_MODES.lineup.hash) enginePilotCurrentModeKey = 'lineup';
  else if (location.hash === ENGINE_PILOT_MODES.heisman.hash) enginePilotCurrentModeKey = 'heisman';
  else if (location.hash === ENGINE_PILOT_MODES.lineupCollege.hash) enginePilotCurrentModeKey = 'lineupCollege';
  else if (location.hash === ENGINE_PILOT_MODES.nflGameResult.hash) enginePilotCurrentModeKey = 'nflGameResult';
  else if (location.hash === ENGINE_PILOT_MODES.cfbGameResult.hash) enginePilotCurrentModeKey = 'cfbGameResult';
  else if (location.hash === ENGINE_PILOT_MODES.nflGameBoxscore.hash) enginePilotCurrentModeKey = 'nflGameBoxscore';
  else if (location.hash === ENGINE_PILOT_MODES.offenseCollege.hash) enginePilotCurrentModeKey = 'offenseCollege';
  else if (location.hash === ENGINE_PILOT_MODES.sbChampionOffenseCollege.hash) enginePilotCurrentModeKey = 'sbChampionOffenseCollege';
  else if (location.hash === ENGINE_PILOT_MODES.cfbRanking.hash) enginePilotCurrentModeKey = 'cfbRanking';
  else if (location.hash === ENGINE_PILOT_MODES.cfbUpset.hash) enginePilotCurrentModeKey = 'cfbUpset';
  else if (location.hash === ENGINE_PILOT_MODES.cfbRivalry.hash) enginePilotCurrentModeKey = 'cfbRivalry';
  else if (location.hash === ENGINE_PILOT_MODES.cfbRivalryLookup.hash) enginePilotCurrentModeKey = 'cfbRivalryLookup';
  else if (location.hash === ENGINE_PILOT_MODES.spotTheFake.hash) enginePilotCurrentModeKey = 'spotTheFake';
  else if (location.hash === ENGINE_PILOT_MODES.threeClues.hash) enginePilotCurrentModeKey = 'threeClues';
  else if (location.hash === ENGINE_PILOT_MODES.eraGauntlet.hash) enginePilotCurrentModeKey = 'eraGauntlet';
  else if (location.hash === ENGINE_PILOT_MODES.oddCollegeOut.hash) enginePilotCurrentModeKey = 'oddCollegeOut';
  else if (location.hash === ENGINE_PILOT_MODES.oneSchoolMissing.hash) enginePilotCurrentModeKey = 'oneSchoolMissing';
  else if (location.hash === ENGINE_PILOT_MODES.franchiseMarathon.hash) enginePilotCurrentModeKey = 'franchiseMarathon';
  else if (location.hash === ENGINE_MECHANIC_MODES.matching.hash) mechanicPilotCurrentModeKey = 'matching';
  else if (location.hash === ENGINE_MECHANIC_MODES.sorting.hash) mechanicPilotCurrentModeKey = 'sorting';
  else if (location.hash === ENGINE_MECHANIC_MODES.higherLowerEngine.hash) mechanicPilotCurrentModeKey = 'higherLowerEngine';
  else if (location.hash === ENGINE_MECHANIC_MODES.elimination.hash) mechanicPilotCurrentModeKey = 'elimination';
  else if (location.hash === ENGINE_MECHANIC_MODES.comparisonBracket.hash) mechanicPilotCurrentModeKey = 'comparisonBracket';
  else if (location.hash === ENGINE_MECHANIC_MODES.connectionGrid.hash) mechanicPilotCurrentModeKey = 'connectionGrid';
  else if (location.hash === ENGINE_MECHANIC_MODES.perfectDriveNfl.hash) mechanicPilotCurrentModeKey = 'perfectDriveNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.perfectDriveCfb.hash) mechanicPilotCurrentModeKey = 'perfectDriveCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.goalLineStandNfl.hash) mechanicPilotCurrentModeKey = 'goalLineStandNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.goalLineStandCfb.hash) mechanicPilotCurrentModeKey = 'goalLineStandCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.lineupBuilderNfl.hash) mechanicPilotCurrentModeKey = 'lineupBuilderNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.lineupBuilderCfb.hash) mechanicPilotCurrentModeKey = 'lineupBuilderCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.auctionDraftNfl.hash) mechanicPilotCurrentModeKey = 'auctionDraftNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.auctionDraftCfb.hash) mechanicPilotCurrentModeKey = 'auctionDraftCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.capChallengeNfl.hash) mechanicPilotCurrentModeKey = 'capChallengeNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.capChallengeCfb.hash) mechanicPilotCurrentModeKey = 'capChallengeCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.knockoutTournamentNfl.hash) mechanicPilotCurrentModeKey = 'knockoutTournamentNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.knockoutTournamentCfb.hash) mechanicPilotCurrentModeKey = 'knockoutTournamentCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.sixDegreesChain.hash) mechanicPilotCurrentModeKey = 'sixDegreesChain';
  else if (location.hash === ENGINE_MECHANIC_MODES.chainReaction.hash) mechanicPilotCurrentModeKey = 'chainReaction';
  else if (location.hash === ENGINE_MECHANIC_MODES.chooseYourPathNfl.hash) mechanicPilotCurrentModeKey = 'chooseYourPathNfl';
  else if (location.hash === ENGINE_MECHANIC_MODES.chooseYourPathCfb.hash) mechanicPilotCurrentModeKey = 'chooseYourPathCfb';
  // Bug fix (Creator "one approval, fully live" pass): these 12 formats
  // (15-Format Expansion's Blind Resume + all 11 of the 75-Format
  // Expansion's Wave 1) had a real hash route in HIDDEN_ROUTES and a real
  // `hash` on their ENGINE_MECHANIC_MODES entry, but were never added to
  // this resolution chain -- visiting their hidden URL directly set
  // state.screen = 'mechanicPilot' but left mechanicPilotCurrentModeKey at
  // its 'matching' default, silently launching the wrong game. Found by
  // actually tracing the route resolution, not assumed correct because the
  // registry entries existed.
  else if (location.hash === ENGINE_MECHANIC_MODES.riskIt.hash) mechanicPilotCurrentModeKey = 'riskIt';
  else if (location.hash === ENGINE_MECHANIC_MODES.riskItCfb.hash) mechanicPilotCurrentModeKey = 'riskItCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.blindResume.hash) mechanicPilotCurrentModeKey = 'blindResume';
  else if (location.hash === ENGINE_MECHANIC_MODES.blindResumeCfb.hash) mechanicPilotCurrentModeKey = 'blindResumeCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.doubleOrNothing.hash) mechanicPilotCurrentModeKey = 'doubleOrNothing';
  else if (location.hash === ENGINE_MECHANIC_MODES.doubleOrNothingCfb.hash) mechanicPilotCurrentModeKey = 'doubleOrNothingCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.kingOfTheHill.hash) mechanicPilotCurrentModeKey = 'kingOfTheHill';
  else if (location.hash === ENGINE_MECHANIC_MODES.kingOfTheHillCfb.hash) mechanicPilotCurrentModeKey = 'kingOfTheHillCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.factOrFake.hash) mechanicPilotCurrentModeKey = 'factOrFake';
  else if (location.hash === ENGINE_MECHANIC_MODES.factOrFakeCfb.hash) mechanicPilotCurrentModeKey = 'factOrFakeCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.guessTheRanking.hash) mechanicPilotCurrentModeKey = 'guessTheRanking';
  else if (location.hash === ENGINE_MECHANIC_MODES.guessTheRankingCfb.hash) mechanicPilotCurrentModeKey = 'guessTheRankingCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.statTarget.hash) mechanicPilotCurrentModeKey = 'statTarget';
  else if (location.hash === ENGINE_MECHANIC_MODES.statTargetCfb.hash) mechanicPilotCurrentModeKey = 'statTargetCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.reverseTrivia.hash) mechanicPilotCurrentModeKey = 'reverseTrivia';
  else if (location.hash === ENGINE_MECHANIC_MODES.reverseTriviaCfb.hash) mechanicPilotCurrentModeKey = 'reverseTriviaCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.threeStrikes.hash) mechanicPilotCurrentModeKey = 'threeStrikes';
  else if (location.hash === ENGINE_MECHANIC_MODES.threeStrikesCfb.hash) mechanicPilotCurrentModeKey = 'threeStrikesCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.mysteryRoster.hash) mechanicPilotCurrentModeKey = 'mysteryRoster';
  else if (location.hash === ENGINE_MECHANIC_MODES.mysteryRosterCfb.hash) mechanicPilotCurrentModeKey = 'mysteryRosterCfb';
  else if (location.hash === ENGINE_MECHANIC_MODES.draftPickLadder.hash) mechanicPilotCurrentModeKey = 'draftPickLadder';
  else if (location.hash === ENGINE_MECHANIC_MODES.categoryRoulette.hash) mechanicPilotCurrentModeKey = 'categoryRoulette';
  else if (location.hash === ENGINE_MECHANIC_MODES.commonLink.hash) mechanicPilotCurrentModeKey = 'commonLink';
  else if (location.hash === ENGINE_MECHANIC_MODES.commonLinkCfb.hash) mechanicPilotCurrentModeKey = 'commonLinkCfb';
  if (state.screen === 'creator') {
    state.creator = {
      screen: creatorToken() ? CREATOR_SCREEN.HOME : CREATOR_SCREEN.AUTH,
      requestText: '', feasibility: null, generated: null, queue: [], queueFilter: '',
      capabilities: null, error: null,
    };
  }
  renderAll();
} else if (state.name && !getRating()) { startIntroTest(); } else if (!consumePendingSocialChallenge() && !consumePendingLiveJoin()) { renderAll(); }
if (!HIDDEN_ROUTES[location.hash] && !lsGet(ONBOARD_KEY, false) && !pendingLiveJoinCode && !pendingSocialChallengeCode) { openOnboarding(); }

// Splash screen: shown by default in index.html, fades out shortly after load
// regardless of Firebase connection state (so a slow/broken connection never
// leaves someone staring at it) — purely a branded loading moment, not a
// blocking gate on anything.
setTimeout(function () {
  var splash = document.getElementById('splash-screen');
  if (!splash) return;
  splash.classList.add('splash-hidden');
  setTimeout(function () { splash.style.display = 'none'; }, 550);
}, 1300);

// Service workers require http(s) (or localhost) — this silently no-ops over
// file://, same documented limitation as the shared leaderboard sync. No need
// to warn about it; solo play already works fully offline without it.
if ('serviceWorker' in navigator && (location.protocol === 'http:' || location.protocol === 'https:')) {
  navigator.serviceWorker.register('sw.js').catch(function () {});
}
