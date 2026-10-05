// Reads Engine-native Game Shell (v1.5, Parts 4-14, 41).
//
// The one reusable shell every certified public engine mode renders through,
// instead of app.js growing a new mode-specific render/state block per mode.
// Draft and Championship (the two modes certified public as of v1.3/v1.4,
// see gateway/config.py's PUBLIC_MODE_ALLOWLIST) are its first two
// consumers -- a third certified mode plugs in by adding one entry to
// ENGINE_PILOT_MODES below, not by writing new render/state logic.
//
// Extracted, not rewritten: every function below is the same shared adapter
// v1.3 already generalized (one state machine + render path for both
// modes, not one per mode) -- v1.5 moves it into its own file (Part 41: app.js
// was already 8,500+ lines before this move) and fixes real user-facing gaps
// found by actually reading what a player would see, not assumed:
//   - the loading/error copy said "engine" and the GENERATION_BUSY error
//     literally rendered its raw server string -- "Another generation job is
//     already running. This Gateway allows only one generation job at a time
//     (Director v0.6, Part H) -- retry shortly." -- directly to the player.
//     Real users should never see backend architecture citations. See
//     ENGINE_GAME_ERROR_COPY below.
//   - both mode titles said "(Live Engine Pilot)" -- visible developer/
//     internal-milestone wording a real player has no reason to see (Part 25).
//   - the in-flight answer-submission state had no visible feedback beyond
//     disabled buttons (Part 9's "Submitting: prevent duplicate submission"
//     was already true; "feels submitted" was not).
//
// Deliberately reuses Quiz's own CSS classes (.panel, .quiz-question,
// .quiz-options, .quiz-option, .quiz-feedback, .btn-primary/.btn-secondary)
// rather than inventing a parallel visual language -- v1.2/v1.3 already
// established this on purpose, v1.5 keeps it intentional: an engine-backed
// question and a local Quiz question render through literally the same
// component classes, so they're visually indistinguishable by construction
// (Part 30), not by separately-maintained styling that could drift.
//
// What this file does NOT change (out of scope for a UI phase, Part 33/48):
// the public API contract, server-side answer validation, feature-flag
// defaults, or fallback semantics. It reads ENABLE_ENGINE_DRAFT_PILOT_V01 /
// ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01 / ENGINE_GATEWAY_BASE_URL (declared in
// app.js from reads-config.js) and calls global helpers app.js already
// defines (esc, icon, playSound, startQuizRound, renderHome, renderAll,
// state) -- safe regardless of this file's <script> position relative to
// app.js's, since every reference happens inside a function body, evaluated
// long after both scripts have finished loading, EXCEPT the one place
// app.js reads ENGINE_PILOT_MODES at its own top level (its hash-routing
// bootstrap, `if (location.hash === ENGINE_PILOT_MODES...)`) -- that's why
// index.html loads this file BEFORE app.js, the same requirement
// reads-config.js already has for window.READS_CONFIG.

/* ============================== state model (Part 5) ==============================
   A named state per s.screen instead of scattered raw string literals.
   Five real states plus one implicit one:
     IDLE            -- state.enginePilot is null (start screen, "Start" button)
     LOADING         -- fetching a new question from the Gateway
     QUESTION_READY  -- question shown, awaiting a pick
     SUBMITTING      -- pick sent to the server, awaiting validation (Part 9:
                         answer options render disabled; the shell now also
                         shows a "Checking your answer" line, not just silence)
     ANSWERED        -- server responded; s.answerResult.correct distinguishes
                         CORRECT/INCORRECT, s.answerResult.canonical_answer IS
                         the REVEALED state -- collapsed into one screen value
                         rather than three, since the render branch and the
                         data needed are identical, just conditionally styled
     ERROR           -- fetch/validate failed; s.error is always shell-owned,
                         polished copy (see ENGINE_GAME_ERROR_COPY), never a
                         raw server string
   COMPLETE (round finished) is its own value, and FALLBACK is not a screen
   of this shell at all -- it's cfg.fallback() escaping to an entirely
   different, already-working screen (Quiz), which is the correct semantics
   for "give up on the engine and play the real, working alternative." */
var ENGINE_GAME_SCREEN = {
  LOADING: 'loading',
  QUESTION_READY: 'question',
  SUBMITTING: 'answering',
  ANSWERED: 'answered',
  ERROR: 'error',
  COMPLETE: 'summary',
};

/* ============================== user-facing error copy (Part 11/43/44) ==============================
   The server's error `code` is a stable, safe contract (gateway/errors.py) --
   its `message` is not: some of those strings cite internal implementation
   detail ("Director v0.6, Part H") that makes sense in an API response but
   never belongs in front of a real player. This shell NEVER renders
   err.message. Every error the player can see comes from this table (or the
   default), keyed only by the safe `code`. */
var ENGINE_GAME_ERROR_COPY = {
  GENERATION_BUSY: "This game is popular right now — try again in a moment.",
  NO_ELIGIBLE_GAME: "We couldn't find a new question right now.",
  SERVICE_UNAVAILABLE: 'This game is temporarily unavailable.',
  MODE_UNAVAILABLE: 'This game is temporarily unavailable.',
  CLIENT_TIMEOUT: "That took too long to load — check your connection and try again.",
  INVALID_GAME_ID: "That question expired — let's get you a new one.",
};
var ENGINE_GAME_ERROR_DEFAULT = "Couldn't load that — please try again.";
// Real gap found: RATE_LIMITED (a real, honest 429 from the server's own
// per-IP submit/round rate limiter -- 60 submits/min, 20 new rounds/min)
// had no entry here at all, so it silently fell through to the generic
// ENGINE_GAME_ERROR_DEFAULT copy with no indication of what actually
// happened or that mashing "Try Again" immediately won't help. Handled
// as its own function (not a static string) since the real wait time is
// server-computed and varies per request -- shown when available, a safe
// generic phrase otherwise.
function _rateLimitedCopy(err) {
  var seconds = err && err.retryAfterSeconds;
  if (typeof seconds === 'number' && seconds > 0) {
    return "You're going a little fast — try again in " + Math.ceil(seconds) + "s.";
  }
  return "You're going a little fast — give it a few seconds and try again.";
}
function enginePilotUserFacingError(err) {
  var code = err && err.code;
  if (code === 'RATE_LIMITED') return _rateLimitedCopy(err);
  return (code && ENGINE_GAME_ERROR_COPY[code]) || ENGINE_GAME_ERROR_DEFAULT;
}

/* ============================== mode registry (Part 7) ==============================
   One entry per certified public mode. Adding a third certified mode is
   exactly this: one more key here, everything below stays unchanged --
   the whole point of a registry instead of if/else-per-mode UI code. */
var ENGINE_PILOT_ROUNDSIZE = 10;
var ENGINE_PILOT_MODES = {
  draft: {
    apiMode: 'draft_guess',
    icon: 'flag',
    hash: '#draftpilot',
    flagOn: function () { return ENABLE_ENGINE_DRAFT_PILOT_V01; },
    // Matches the Gateway's own public-facing title (gateway/services/
    // public_game.py's PUBLIC_MODES) so the same clean name appears whether
    // it's read from the API's list_public_modes() or hardcoded here for
    // the pre-fetch Start screen -- no "(Live Engine Pilot)"/"Engine"
    // wording a real player has no reason to see (Part 25/44).
    title: 'NFL Draft History: Guess the Team',
    desc: 'See a real NFL Draft pick and guess which team made it.',
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    // Real fallback, not a placeholder (Part 12/20): "NFL Draft History" is
    // an existing, already-working Quiz category backed by real
    // engine-exported content (data/quiz-engine-draft-production.js,
    // merged into QUIZ when ENABLE_ENGINE_QUIZ_DRAFT is on) -- conceptually
    // the same game, playable with zero network dependency.
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  championship: {
    apiMode: 'championship_guess',
    icon: 'lombardiTrophy',
    hash: '#championshippilot',
    flagOn: function () { return ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01; },
    title: 'NFL Playoffs: Guess the Result',
    desc: 'See a real NFL team and season, and guess how their postseason actually ended.',
    fallbackLabel: 'Play Super Bowl History (Quiz) Instead',
    // Part 12: mode-aware fallback -- "Super Bowl History" is a real,
    // already-loaded, hand-authored Quiz category (data/quiz.js, 60
    // questions), the honest Championship equivalent of Draft's fallback
    // above. Deliberately NOT data/quiz-engine-championship-award-pilot.js
    // -- that engine-exported file exists on disk but was never wired into
    // QUIZ (unlike ENABLE_ENGINE_QUIZ_DRAFT's draft merge), and wiring it
    // in is a separate, unrequested content change outside this phase's
    // scope (see the v1.3 report's Frontend section).
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
  },
  // v1.8, Part F/O -- the milestone's primary acceptance-test capability.
  lineup: {
    apiMode: 'lineup_guess',
    icon: 'grid',
    hash: '#lineuppilot',
    flagOn: function () { return ENABLE_ENGINE_LINEUP_PILOT_V01; },
    title: 'NFL Starting Lineups: Guess the Team',
    desc: "See a real NFL team's starting offense, laid out by position, and guess the team.",
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    // No dedicated local Quiz category exists for this brand-new domain
    // (unlike Draft/Championship, which reuse an existing hand-authored or
    // engine-exported category) -- Draft History is the closest honest
    // "real NFL trivia, works offline" fallback, not a placeholder.
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  // CFB data enrichment operation -- the first CFB engine mode. Plugs into
  // this exact same shared shell with zero new render/state code, proving
  // the shell (built for NFL modes) generalizes to a genuinely different
  // competition, not just new NFL predicates.
  heisman: {
    apiMode: 'cfb_heisman_guess',
    icon: 'trophy',
    hash: '#heismanpilot',
    flagOn: function () { return ENABLE_ENGINE_HEISMAN_PILOT_V01; },
    title: 'CFB Heisman Winners: Guess the School',
    desc: "See a real Heisman Trophy winner and year, and guess which school he played for.",
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    // No local CFB-award Quiz category exists (this is a brand-new CFB
    // domain, same real gap lineup.py's fallback comment above discloses
    // for its own NFL domain) -- Draft History is the closest honest,
    // already-working, zero-network fallback, not a placeholder.
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  // Public-readiness punch-list: the college-identity lineup variant --
  // same "guess" mechanic/single-question contract as `lineup` above,
  // just a different real capability (NFL_OFFENSE_LINEUP_COLLEGE), so it
  // reuses this exact shared shell with zero new render/state code. Only
  // certified public after the real generation-timeout starvation defect
  // for this domain was fixed and regression-tested this pass.
  lineupCollege: {
    apiMode: 'lineup_college_guess',
    icon: 'grid',
    hash: '#lineupcollegepilot',
    flagOn: function () { return ENABLE_ENGINE_LINEUP_COLLEGE_PILOT_V01; },
    title: 'NFL Starting Lineups: Guess the Team (By College)',
    desc: "See a real NFL team's starting offense by position and college (names hidden), and guess the team.",
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  // Public-readiness punch-list: three real, already-live public
  // capabilities (App-Wide Engine Migration / Historical Engine
  // Enrichment operations) that had zero frontend entry point before this
  // pass -- confirmed live on `/v1/public/modes` but absent from
  // ENGINE_PILOT_MODES. Same shared shell, zero new render/state code.
  nflGameResult: {
    apiMode: 'nfl_game_result_guess',
    icon: 'versus',
    hash: '#nflgameresultpilot',
    flagOn: function () { return ENABLE_ENGINE_NFL_GAME_RESULT_PILOT_V01; },
    title: 'NFL Game Results: Guess the Winner',
    desc: "See a real NFL matchup, and guess which team won.",
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  cfbGameResult: {
    apiMode: 'cfb_game_result_guess',
    icon: 'versus',
    hash: '#cfbgameresultpilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_GAME_RESULT_PILOT_V01; },
    title: 'CFB Game Results: Guess the Winner',
    desc: "See a real college football matchup, and guess which team won.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  nflGameBoxscore: {
    apiMode: 'nfl_game_boxscore_guess',
    icon: 'barChart',
    hash: '#nflgameboxscorepilot',
    flagOn: function () { return ENABLE_ENGINE_NFL_GAME_BOXSCORE_PILOT_V01; },
    title: 'NFL Box Scores: Guess Who Gained More Yards',
    desc: "See a real NFL matchup, and guess which team gained more total yards.",
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // Creator stress test / discovery pass: the first 4 modes promoted
  // straight from Creator-only to public certification -- same shared
  // shell, zero new render/state code. Real candidate surveys recorded in
  // gateway/services/public_game.py's own PUBLIC_MODES entries.
  offenseCollege: {
    apiMode: 'offense_college_guess',
    icon: 'grid',
    hash: '#offensecollegepilot',
    flagOn: function () { return ENABLE_ENGINE_OFFENSE_COLLEGE_PILOT_V01; },
    title: 'NFL Offense by College: Guess the Team',
    desc: "See a real, current NFL team's starting offense by college and position (names hidden), and guess the team.",
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  sbChampionOffenseCollege: {
    apiMode: 'sb_champion_offense_college_guess',
    icon: 'lombardiTrophy',
    hash: '#sbchampionoffensecollegepilot',
    flagOn: function () { return ENABLE_ENGINE_SB_CHAMPION_OFFENSE_COLLEGE_PILOT_V01; },
    title: 'Super Bowl Champions: Guess the Team by College',
    desc: "See a real Super Bowl-winning offense by college and position (names hidden), and guess the team and season.",
    fallbackLabel: 'Play Super Bowl History (Quiz) Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
  },
  cfbRanking: {
    apiMode: 'cfb_ranking_guess',
    icon: 'target',
    hash: '#cfbrankingpilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_RANKING_PILOT_V01; },
    title: 'CFB Rankings: Guess the Team',
    desc: "See a real AP Top 25 ranking snapshot, and guess which team held that rank.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  cfbUpset: {
    apiMode: 'cfb_upset_guess',
    icon: 'zap',
    hash: '#cfbupsetpilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_UPSET_PILOT_V01; },
    title: 'CFB Upsets: Guess the Winner',
    desc: "See a real college football matchup where the AP-ranked team lost, and guess who pulled off the upset.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // ==========================================================================
  // Public Mode Wiring pass (Pass 2.5): 8 real backend capabilities newly
  // certified public this pass (see gateway/services/public_game.py's own
  // PUBLIC_MODES entries for the real candidate surveys behind each).
  // eraGauntlet/franchiseMarathon are the two "sequential" modes -- see
  // their own `sequential: true` flag below and startEnginePilotRound()'s
  // real stage_index handling.
  cfbRivalry: {
    apiMode: 'cfb_rivalry_guess',
    icon: 'versus',
    hash: '#cfbrivalrypilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_RIVALRY_PILOT_V01; },
    title: 'CFB Rivalries',
    desc: "See a real question from a real, named CFB rivalry (Iron Bowl, Civil War, and more).",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  cfbRivalryLookup: {
    apiMode: 'cfb_rivalry_lookup_guess',
    icon: 'shield',
    hash: '#cfbrivalrylookuppilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_RIVALRY_LOOKUP_PILOT_V01; },
    title: 'CFB Rivalries: Name the Rival',
    desc: "See a real school, and guess its real, named rivalry opponent.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  spotTheFake: {
    apiMode: 'cfb_spot_the_fake_guess',
    icon: 'xMark',
    hash: '#spotthefakepilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_SPOT_THE_FAKE_PILOT_V01; },
    title: 'Spot the Fake',
    desc: "See a real starting lineup by position and college -- one slot's college has been swapped for a fake. Find it.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  threeClues: {
    apiMode: 'cfb_three_clues_guess',
    icon: 'mystery',
    hash: '#threecluespilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_THREE_CLUES_PILOT_V01; },
    title: "Three Clues, One Champion",
    desc: "Three real clues, revealed one at a time. Guess the NFL team and season.",
    fallbackLabel: 'Play NFL Trivia Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
  },
  eraGauntlet: {
    apiMode: 'era_gauntlet_guess',
    icon: 'timeline',
    hash: '#eragauntletpilot',
    flagOn: function () { return ENABLE_ENGINE_ERA_GAUNTLET_PILOT_V01; },
    title: 'Era Gauntlet',
    desc: "Play through seven real NFL history stages, with clues from the actual decade shown at each stop.",
    fallbackLabel: 'Play NFL Trivia Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
    sequential: true,
  },
  oddCollegeOut: {
    apiMode: 'cfb_odd_college_out_guess',
    icon: 'search',
    hash: '#oddcollegeoutpilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_ODD_COLLEGE_OUT_PILOT_V01; },
    title: 'Odd College Out',
    desc: "See four real colleges. Three were part of the same real group -- find the one that wasn't.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  oneSchoolMissing: {
    apiMode: 'cfb_one_school_missing_guess',
    icon: 'grid',
    hash: '#oneschoolmissingpilot',
    flagOn: function () { return ENABLE_ENGINE_CFB_ONE_SCHOOL_MISSING_PILOT_V01; },
    title: 'One School Missing',
    desc: "See most of a real group's colleges. Pick the real one that's missing.",
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  franchiseMarathon: {
    apiMode: 'franchise_marathon_guess',
    icon: 'lombardiTrophy',
    hash: '#franchisemarathonpilot',
    flagOn: function () { return ENABLE_ENGINE_FRANCHISE_MARATHON_PILOT_V01; },
    title: 'Franchise Marathon',
    desc: "Pick an NFL franchise and play through its real history, from team identity and records to players and postseason runs.",
    fallbackLabel: 'Play NFL Trivia Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
    sequential: true,
    needsFilterValue: true,
    filterParamName: 'franchise',
    // All 32 real current NFL franchises -- verified directly this pass
    // (generate_package_from_spec() called for each real franchise_name
    // value below against the rebuilt 8-stage adapter): every one reaches
    // 7 or 8 real, QA-passed stages, qa_status PASSED. This list used to
    // cover only 10 franchises, left over from BEFORE Franchise Marathon's
    // Closeout Part 3 rebuild (when the mode was a thin filter over
    // sb_champion_offense_college.py's 60-board SB_CHAMPION table, so a
    // franchise needed a real Super Bowl title just to have ANY surviving
    // stage) -- the rebuilt adapter draws from 7 different real Engine
    // tables (identity/season-record/coach/draft/award/playoffs/roster,
    // deep-cut only for real champions), so every real franchise now has a
    // full marathon regardless of championship history. `value` is matched
    // via a real, case-insensitive LIKE against team_seasons.full_name
    // (_team_codes_for_franchise) -- the nickname alone is enough for
    // every team EXCEPT Washington, whose 3 real distinct full_name eras
    // (Redskins/Football Team/Commanders) share no common nickname
    // substring; "washington" (the constant city) is required there to
    // reach the franchise's full real 2002-2026 history, including its
    // real Super Bowl deep-cut stage (as "Washington Redskins" in the
    // curated SB_CHAMPION table) and its real IDENTITY/rename stage --
    // confirmed directly: searching "commanders" alone silently misses
    // both.
    franchiseChoices: [
      { value: 'cardinals', label: 'Arizona Cardinals' },
      { value: 'falcons', label: 'Atlanta Falcons' },
      { value: 'ravens', label: 'Baltimore Ravens' },
      { value: 'bills', label: 'Buffalo Bills' },
      { value: 'panthers', label: 'Carolina Panthers' },
      { value: 'bears', label: 'Chicago Bears' },
      { value: 'bengals', label: 'Cincinnati Bengals' },
      { value: 'browns', label: 'Cleveland Browns' },
      { value: 'cowboys', label: 'Dallas Cowboys' },
      { value: 'broncos', label: 'Denver Broncos' },
      { value: 'lions', label: 'Detroit Lions' },
      { value: 'packers', label: 'Green Bay Packers' },
      { value: 'texans', label: 'Houston Texans' },
      { value: 'colts', label: 'Indianapolis Colts' },
      { value: 'jaguars', label: 'Jacksonville Jaguars' },
      { value: 'chiefs', label: 'Kansas City Chiefs' },
      { value: 'raiders', label: 'Raiders (Oakland/Las Vegas)' },
      { value: 'chargers', label: 'Chargers (San Diego/LA)' },
      { value: 'rams', label: 'Rams (St. Louis/LA)' },
      { value: 'dolphins', label: 'Miami Dolphins' },
      { value: 'vikings', label: 'Minnesota Vikings' },
      { value: 'patriots', label: 'New England Patriots' },
      { value: 'saints', label: 'New Orleans Saints' },
      { value: 'giants', label: 'New York Giants' },
      { value: 'jets', label: 'New York Jets' },
      { value: 'eagles', label: 'Philadelphia Eagles' },
      { value: 'steelers', label: 'Pittsburgh Steelers' },
      { value: '49ers', label: 'San Francisco 49ers' },
      { value: 'seahawks', label: 'Seattle Seahawks' },
      { value: 'buccaneers', label: 'Tampa Bay Buccaneers' },
      { value: 'titans', label: 'Tennessee Titans' },
      { value: 'washington', label: 'Washington Commanders' },
    ],
  },
};
var enginePilotCurrentModeKey = 'draft';
function enginePilotModeConfig(modeKey) {
  return ENGINE_PILOT_MODES[modeKey] || ENGINE_PILOT_MODES.draft;
}

// v1.4, Part 15: a dead/unreachable Gateway must not leave a player staring
// at a spinner indefinitely -- the browser's own default fetch timeout is
// effectively "none" for most network failure modes (a stalled TCP
// connection can hang far longer than any real user will wait). 10s is
// generous headroom over every real measured latency this project has ever
// observed (Draft fetch ~0.26s avg/0.51s worst, Championship ~0.03s avg,
// answer validation ~0.002s) while still failing fast enough to reach the
// existing error/retry/fallback screen in a reasonable time. Part 16:
// deliberately NO automatic retry here -- a retry storm against an already-
// struggling Gateway is exactly the failure mode Part 16 warns about; the
// existing "Try Again" button is the retry mechanism, explicit and
// user-triggered, never silent or automatic.
var ENGINE_PILOT_FETCH_TIMEOUT_MS = 30000;
function enginePilotFetchJson(path, options) {
  var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
  var timeoutId = controller ? setTimeout(function () { controller.abort(); }, ENGINE_PILOT_FETCH_TIMEOUT_MS) : null;
  var opts = options ? Object.assign({}, options) : {};
  if (controller) opts.signal = controller.signal;
  return fetch(ENGINE_GATEWAY_BASE_URL + path, opts).then(function (res) {
    if (timeoutId) clearTimeout(timeoutId);
    if (!res.ok) {
      return res.json().catch(function () { return {}; }).then(function (body) {
        // The raw body.error.message is kept on the thrown Error for
        // console/debugging visibility only -- the shell's render path
        // never displays it (see enginePilotUserFacingError above), only
        // `err.code`, the stable/safe half of the server's error contract.
        var err = new Error((body.error && body.error.message) || ('HTTP ' + res.status));
        err.code = body.error && body.error.code;
        // Real gap found ("all the games do this when you get something
        // wrong" -- players hitting the real per-IP submit rate limit,
        // 60 req/60s, get a real RATE_LIMITED 429 with no matching entry
        // in ENGINE_GAME_ERROR_COPY, so it fell through to the generic
        // "Couldn't load that" message with no indication of what
        // actually happened or that immediately retrying won't help.
        // retry_after_seconds is real, server-computed -- carried through
        // here so the user-facing copy can tell them how long to wait.
        err.retryAfterSeconds = body.error && body.error.retry_after_seconds;
        throw err;
      });
    }
    return res.json();
  }).catch(function (err) {
    if (timeoutId) clearTimeout(timeoutId);
    if (err && err.name === 'AbortError') {
      var timeoutErr = new Error('Client-side fetch timeout after ' + ENGINE_PILOT_FETCH_TIMEOUT_MS + 'ms.');
      timeoutErr.code = 'CLIENT_TIMEOUT';
      throw timeoutErr;
    }
    throw err;
  });
}

// Player-facing quality guardrails for two generator defects that should
// never survive to the screen, even if an older Gateway release or cached
// package is briefly served during deployment.
function normalizeEnginePilotPackageForPlayer(modeKey, game) {
  if (!game || !game.payload) return game;
  if (modeKey === 'nflGameBoxscore') {
    var prompt = game.payload.prompt || '';
    var matchup = /game between (?:the )?(.+?) and (?:the )?(.+?), which team gained more total yards\?/i.exec(prompt);
    if (matchup) {
      var teams = [matchup[1].trim(), matchup[2].trim()];
      if (teams[0] && teams[1] && teams[0] !== teams[1]) game.payload.options = teams;
    }
  }
  return game;
}
function enginePilotQualityScore(modeKey, game) {
  if (!game || !game.payload) return { score: 0, reasons: ['missing payload'] };
  var p = game.payload, score = 100, reasons = [];
  var prompt = String(p.prompt || p.question || '');
  if (!prompt) { score -= 55; reasons.push('missing prompt'); }
  else if (prompt.length < 12) { score -= 20; reasons.push('thin prompt'); }
  else if (prompt.length > 500) { score -= 10; reasons.push('overlong prompt'); }
  if (Array.isArray(p.options)) {
    if (p.options.length < 2) { score -= 55; reasons.push('too few options'); }
    var seen = {}, dup = false;
    p.options.forEach(function (opt) { var k = String(opt || '').trim().toLowerCase(); if (!k || seen[k]) dup = true; seen[k] = true; });
    if (dup) { score -= 45; reasons.push('duplicate/blank options'); }
  }
  if (modeKey === 'threeClues' && /finished that real season 0-0(?:[.,;]|$)/i.test(prompt)) {
    score -= 80; reasons.push('known bogus 0-0 season clue');
  }
  if (/\b(undefined|null|nan)\b/i.test(prompt)) { score -= 60; reasons.push('invalid rendered value'); }
  return { score: Math.max(0, score), reasons: reasons };
}
function enginePilotPackageNeedsQualityRetry(modeKey, game) {
  return enginePilotQualityScore(modeKey, game).score < 70;
}
function startEnginePilotRound(modeKey, filterValue) {
  if (modeKey) enginePilotCurrentModeKey = modeKey;
  state.enginePilot = {
    modeKey: enginePilotCurrentModeKey, screen: ENGINE_GAME_SCREEN.LOADING, roundIndex: 0, roundSize: ENGINE_PILOT_ROUNDSIZE,
    correctCount: 0, seenGameIds: [], current: null, error: null,
    // Public Mode Wiring pass: stageIndex/filterValue/sequenceCompleted are
    // no-ops for every mode except the two "sequential" ones (see
    // ENGINE_PILOT_MODES' own sequential/needsFilterValue flags) -- every
    // other mode's behavior below is byte-identical to before this change.
    stageIndex: 0, filterValue: filterValue || null, sequenceCompleted: false, sequenceStageCount: null,
    // Era Gauntlet distinctness pass (user request: "let's not make the
    // era gauntlet just like the Three Clues and one champion gameplay"):
    // a real per-stage correct/incorrect record, used to turn the shared
    // timeline into an actual "your run through history" result instead
    // of a plain done/current dot -- harmless, unused array for every
    // other mode.
    stageResults: [],
    // Real bug fix ("all the games do this when you get something
    // wrong") -- same real gap as mechanicPilot's own errorContext (see
    // that shell's startMechanicPilotRound for the full writeup): the
    // ERROR screen's single "Try Again" button used to always call
    // loadNextEnginePilotQuestion(), even when the real failure was on
    // SUBMITTING an already-picked answer -- discarding it and serving an
    // unrelated new question instead of just resubmitting.
    errorContext: null, qualityRetryCount: 0,
  };
  state.enginePilotPendingFranchise = null;
  state.screen = 'enginePilot';
  renderAll();
  loadNextEnginePilotQuestion();
}
// Real bug fix ("all the games do this when you get something wrong"):
// same real reason as mechanicPilot's own mechanicPilotRetry() -- the
// ERROR screen's single "Try Again" button used to always call
// loadNextEnginePilotQuestion() regardless of whether the failure was on
// loading a question (fine to just retry) or on SUBMITTING an
// already-picked answer (which silently discarded that answer and served
// an unrelated new question instead of resubmitting it).
function enginePilotRetry() {
  var s = state.enginePilot;
  if (!s) return;
  if (s.errorContext === 'submit' && s.current && s.pickedOption !== null) {
    _submitEnginePilotAnswer(s.pickedOption);
    return;
  }
  loadNextEnginePilotQuestion();
}
function enginePilotFallback() {
  // A real bug caught by actually clicking this in a browser, not assumed
  // from reading the code (v1.2): startQuizRound() does NOT set
  // state.screen itself (every other caller reaches it via
  // goToMode('quiz') first, which does) -- each mode's fallback() above
  // sets it explicitly so renderAll() doesn't keep dispatching to the
  // (now-null) enginePilot screen after a real fallback.
  var modeKey = (state.enginePilot && state.enginePilot.modeKey) || enginePilotCurrentModeKey;
  enginePilotModeConfig(modeKey).fallback();
}
function loadNextEnginePilotQuestion() {
  var s = state.enginePilot;
  if (!s) return;
  var cfg = enginePilotModeConfig(s.modeKey);
  s.screen = ENGINE_GAME_SCREEN.LOADING;
  s.error = null;
  renderAll();
  var url = '/v1/public/game?mode=' + encodeURIComponent(cfg.apiMode);
  // Cross-Mode Repetition pass: getClientId() (app.js, already the exact
  // helper Pick'em's pickem-ui.js reuses) lets the Gateway recognize the
  // same real board/entity across DIFFERENT engine-pilot modes played back
  // to back in this browser -- see public_game.py's own module comment.
  // Sent on every mode, not just the ones that share the 595-board pool:
  // harmless for a mode with no entity_key (recent_entities check is a
  // no-op for it), and keeps this one call site mode-agnostic.
  url += '&client_id=' + encodeURIComponent(getClientId());
  if (cfg.sequential) {
    // Real progression (Franchise Marathon / Era Gauntlet): stage_index
    // addresses a specific real position in an intentionally-ordered
    // candidate list (chronological season / oldest-era-first) -- exclude
    // is meaningless here (see get_public_game()'s own docstring for why
    // target_count=1 + exclude-based retry could never advance a
    // sequential mode before this pass).
    url += '&stage=' + s.stageIndex;
  } else {
    var exclude = s.seenGameIds.slice(-20).join(',');
    if (exclude) url += '&exclude=' + encodeURIComponent(exclude);
  }
  if (cfg.needsFilterValue && s.filterValue) {
    url += '&' + (cfg.filterParamName || 'filter_value') + '=' + encodeURIComponent(s.filterValue);
  }
  enginePilotFetchJson(url)
    .then(function (game) {
      if (state.enginePilot !== s) return; // player navigated away while this was in flight
      // SEQUENCE_COMPLETE is a well-defined 200 (see gateway/errors.py) --
      // enginePilotFetchJson only ever throws on a non-2xx status, so this
      // arrives here as a normal resolved value, not a .catch(). A real,
      // honest "you reached the end" outcome, not an error state.
      if (game.error) {
        if (game.error.code === 'SEQUENCE_COMPLETE') {
          s.sequenceCompleted = true;
          s.sequenceStageCount = game.error.stage_count != null ? game.error.stage_count : s.stageIndex;
          finishEnginePilotSession(s.correctCount, s.sequenceStageCount);
          s.screen = ENGINE_GAME_SCREEN.COMPLETE;
          renderAll();
          return;
        }
        s.errorContext = 'load';
        s.screen = ENGINE_GAME_SCREEN.ERROR;
        s.error = enginePilotUserFacingError(game.error);
        renderAll();
        return;
      }
      if (enginePilotPackageNeedsQualityRetry(s.modeKey, game) && s.qualityRetryCount < 8) {
        s.qualityRetryCount++;
        if (game.game_id) s.seenGameIds.push(game.game_id);
        loadNextEnginePilotQuestion();
        return;
      }
      normalizeEnginePilotPackageForPlayer(s.modeKey, game);
      s.qualityRetryCount = 0;
      s.current = game;
      s.pickedOption = null;
      s.answerResult = null;
      s.cluesRevealedCount = 1; // Three Clues / Era Gauntlet: each new question starts back at Clue 1 of 3
      s.screen = ENGINE_GAME_SCREEN.QUESTION_READY;
      renderAll();
    })
    .catch(function (err) {
      if (state.enginePilot !== s) return;
      s.errorContext = 'load';
      s.screen = ENGINE_GAME_SCREEN.ERROR;
      s.error = enginePilotUserFacingError(err);
      renderAll();
    });
}
function pickEnginePilotAnswer(optionIndex) {
  var s = state.enginePilot;
  if (!s || s.screen !== ENGINE_GAME_SCREEN.QUESTION_READY || s.pickedOption !== null) return;
  s.pickedOption = optionIndex;
  _submitEnginePilotAnswer(optionIndex);
}
// Real bug fix ("all the games do this when you get something wrong"):
// factored out of pickEnginePilotAnswer() so a retry after a SUBMIT
// failure can resubmit the exact same already-picked answer (s.current/
// s.pickedOption are both still on `s`, untouched by the failure) without
// re-running pickEnginePilotAnswer()'s own "already picked" guard, which
// would otherwise block a retry from ever re-firing.
function _submitEnginePilotAnswer(optionIndex) {
  var s = state.enginePilot;
  if (!s) return;
  var game = s.current;
  var chosenLabel = game.payload.options[optionIndex];
  s.screen = ENGINE_GAME_SCREEN.SUBMITTING;
  renderAll();
  enginePilotFetchJson('/v1/public/game/answer', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: game.game_id, answer: chosenLabel }),
  }).then(function (result) {
    if (state.enginePilot !== s) return;
    s.answerResult = result;
    s.seenGameIds.push(game.game_id);
    if (result.correct) s.correctCount++;
    s.stageResults.push({
      decade: game.payload.visual_payload && game.payload.visual_payload.era_decade_label,
      correct: !!result.correct,
    });
    playSound(result.correct ? 'correct' : 'wrong');
    s.screen = ENGINE_GAME_SCREEN.ANSWERED;
    renderAll();
  }).catch(function (err) {
    if (state.enginePilot !== s) return;
    s.errorContext = 'submit';
    s.screen = ENGINE_GAME_SCREEN.ERROR;
    s.error = enginePilotUserFacingError(err);
    renderAll();
  });
}
function advanceEnginePilot() {
  var s = state.enginePilot;
  if (!s) return;
  var cfg = enginePilotModeConfig(s.modeKey);
  if (cfg.sequential) {
    // No fixed roundSize for a sequential mode -- the real stage count
    // varies (a franchise's real title count; Era Gauntlet's real 7
    // represented decades) and is only known for certain once the server
    // returns SEQUENCE_COMPLETE (see loadNextEnginePilotQuestion()).
    s.stageIndex++;
    loadNextEnginePilotQuestion();
    return;
  }
  if (s.roundIndex + 1 >= s.roundSize) {
    finishEnginePilotSession(s.correctCount, s.roundSize);
    s.screen = ENGINE_GAME_SCREEN.COMPLETE;
    renderAll();
    return;
  }
  s.roundIndex++;
  loadNextEnginePilotQuestion();
}
// User request: "let's make sure that all game modes are connected to
// your Football score." Real, live gap found: none of the ~17 Engine
// Pilot modes (Three Clues, Era Gauntlet, CFB Rivalries, Odd College Out,
// Franchise Marathon, and more -- everything routed through this shared
// shell) ever called updateRatingDrift(), despite being exactly the same
// "N questions, X correct" shape as Quiz/CFB Quiz, which already do. This
// is the one shared choke point both completion paths above call through,
// mirroring every legacy finish* function's own "updateRatingDrift(pct)
// right before the completion screen" call, and same denominator
// discipline sequential modes already established for their own summary
// stat display just above. showRatingMoveToast() (fired from inside
// updateRatingDrift itself) is the real user-facing feedback -- no
// separate share-card plumbing exists for this shell to hang a stored
// delta off of, unlike the legacy modes that use one.
function finishEnginePilotSession(correctCount, totalCount) {
  if (!totalCount) return; // a real, disclosed zero-stage edge case -- never divide by zero
  updateRatingDrift(100 * correctCount / totalCount);
}
/* v1.8, Part E/F: POSITION_LINEUP visual template -- a real football
   position board (5 skill positions, then 5 grouped OL) instead of a plain
   question sentence. Purely presentational: the answer/options underneath
   are rendered exactly the same way regardless of visual_template (Part D's
   mechanic/template separation -- this function never touches answer
   validation). See tools/director_v02/visual_templates.py and
   tools/quiz_export/adapters/lineup.py for why OL is one grouped row of 5,
   not 5 individually-labeled slots. */
// Era Gauntlet's real timeline. The backend's quota-based SB-cap redesign
// (capping 100%-Super-Bowl-only decades like the 1960s-1990s at 2 stages
// per run) means the real stage-to-decade mapping varies run to run -- it
// is NOT always "stage 0 = 1960s, stage 1 = 1970s, ...". The adapter now
// returns the real, per-run decade sequence in every stage's
// visual_payload.era_sequence_labels (tools/quiz_export/adapters/
// cfb_three_clues_one_champion.py's _era_gauntlet_candidates()) -- this
// fallback array is only a last resort for an old cached game object that
// predates that field.
var ERA_GAUNTLET_ERA_LABELS_FALLBACK = ['1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'];
// Era Gauntlet distinctness pass (user request: "let's not make the era
// gauntlet just like the Three Clues and one champion gameplay"): the
// timeline used to only ever show a plain "done" dot regardless of
// whether that stage was answered correctly -- identical information to
// Franchise Marathon's own stage counter, just drawn as dots. Now shows a
// real check/miss per completed era (from s.stageResults, populated at
// answer time in pickEnginePilotAnswer above), turning this into an
// actual "your run through history" record, not a progress bar that
// happens to have decade labels on it.
function renderEraGauntletTimelineHtml(stageIndex, sequenceLabels, stageResults) {
  var labels = (sequenceLabels && sequenceLabels.length) ? sequenceLabels : ERA_GAUNTLET_ERA_LABELS_FALLBACK;
  var results = stageResults || [];
  var markers = labels.map(function (label, i) {
    var cls = 'era-gauntlet-marker';
    var title = '';
    if (i < stageIndex) {
      var res = results[i];
      cls += res && res.correct ? ' done' : ' missed';
      title = ' title="' + (res && res.correct ? 'Correct' : 'Missed') + '"';
    } else if (i === stageIndex) {
      cls += ' current';
    }
    return '<div class="' + cls + '"' + title + '><span class="era-gauntlet-dot"></span><span class="era-gauntlet-label">' + label + '</span></div>';
  }).join('<div class="era-gauntlet-connector"></div>');
  return '<div class="era-gauntlet-timeline" role="img" aria-label="Era ' + (stageIndex + 1) + ' of ' + labels.length + ': ' +
    esc(labels[stageIndex] || '') + '">' + markers + '</div>';
}
function renderPositionLineupBoard(payload) {
  // UI/product polish pass: this used to be two visually-identical rows of
  // gray boxes with no framing -- functionally clear, but read as a
  // generic quiz layout rather than a real lineup/roster puzzle. Added: an
  // eyebrow label (matches the site's existing eyebrow-badge convention,
  // e.g. the Daily Challenge card), and a row sub-label distinguishing the
  // 5 skill positions from the grouped O-Line -- both purely presentational,
  // no change to the answer contract underneath.
  var positions = (payload && payload.positions) || [];
  var season = payload && payload.season;
  var skillRow = positions.slice(0, 5);
  var olRow = positions.slice(5, 10);
  function cell(p) {
    return '<div class="lineup-cell"><div class="lineup-pos">' + esc(p.position) + '</div>' +
      '<div class="lineup-name">' + esc(p.name) + '</div></div>';
  }
  return '<div class="lineup-board">' +
    '<div class="lineup-board-eyebrow">' + icon('users') + ' Starting Offense' + (season ? ' &middot; ' + esc(String(season)) : '') + '</div>' +
    '<div class="lineup-row-label">Skill Positions</div>' +
    '<div class="lineup-row">' + skillRow.map(cell).join('') + '</div>' +
    '<div class="lineup-row-label">Offensive Line</div>' +
    '<div class="lineup-row">' + olRow.map(cell).join('') + '</div>' +
    '</div>';
}
/* Position+college proof-game fix: the names-hidden sibling of
   renderPositionLineupBoard above -- same board layout, but only the 5
   skill positions (no OL row -- see tools/quiz_export/adapters/
   lineup_college.py for why real college data can't honestly cover the
   offensive line) and each cell shows a real COLLEGE instead of a name. */
function renderPositionLineupCollegeBoard(payload, spotFake, projected) {
  var positions = (payload && payload.positions) || [];
  var season = payload && payload.season;
  var conferenceMembers = spotFake && positions.some(function (p) { return /^Member\s+\d+$/i.test(p.position || ''); });
  var hasOffensiveLine = positions.some(function (p) { return /^(LT|LG|C|RG|RT)$/i.test(p.position || ''); });
  function cell(p) {
    return '<div class="lineup-cell"><div class="lineup-pos">' + esc(p.position) + '</div>' +
      '<div class="lineup-name">' + esc(p.college) + '</div></div>';
  }
  var boardRows = hasOffensiveLine && !spotFake
    ? '<div class="lineup-row-label">Offensive Line</div><div class="lineup-row">' +
      positions.filter(function (p) { return /^(LT|LG|C|RG|RT)$/i.test(p.position || ''); }).map(cell).join('') + '</div>' +
      '<div class="lineup-row-label">Skill Positions</div><div class="lineup-row lineup-row--six">' +
      positions.filter(function (p) { return !/^(LT|LG|C|RG|RT)$/i.test(p.position || ''); }).map(cell).join('') + '</div>'
    : '<div class="lineup-row-label">' + (conferenceMembers ? 'Find the swapped school' : (hasOffensiveLine ? 'Offensive lineup' : 'Skill Positions')) + '</div>' +
      '<div class="lineup-row">' + positions.map(cell).join('') + '</div>';
  return '<div class="lineup-board' + (spotFake ? ' spotfake-lineup' : '') + '">' +
    '<div class="lineup-board-eyebrow">' + icon('users') + ' ' +
    (conferenceMembers ? 'Conference members' : (spotFake ? 'Lineup by college' :
      (projected ? 'Projected offense by college' : 'Starting offense (by college, names hidden)'))) +
    (season ? ' &middot; ' + esc(String(season)) : '') + '</div>' +
    boardRows +
    '</div>';
}
// Full Visual + Interactive Redesign pass: "make ranking numbers visually
// important" -- a pure text-presentation pass over the real prompt string
// already returned by the Engine (CFB Rankings/Upsets prompts always say
// "No. N" for a real AP Top 25 rank -- confirmed against real live
// prompts this same session, e.g. "ranked No. 8 in the AP Top 25...").
// Wraps that exact real substring in a styled span -- never invents,
// reorders, or otherwise touches the real fact string itself, and is a
// no-op (falls through to esc(prompt) unchanged) for every prompt that
// doesn't contain that pattern.
function highlightRankNumbers(promptText) {
  var escaped = esc(promptText);
  return escaped.replace(/No\.\s?\d+/g, function (m) { return '<span class="rank-number-highlight">' + m + '</span>'; });
}
// Three Clues, One Champion / Era Gauntlet: real progressive clue reveal
// (Section 6 -- "do not dump all three clues into a generic text block at
// once"). No backend/visual_payload change needed -- the adapter's own
// prompt format is a single, stable string
// ("Exactly 3 real clues, 1 champion: {clue1}; {clue2}; {clue3}. Guess the
// Super Bowl-winning team AND season.", see
// cfb_three_clues_one_champion.py) -- parsed client-side into its real 3
// clue segments. Falls back to showing the whole prompt unparsed (never
// broken) if the real format ever doesn't match exactly 3 segments.
var THREE_CLUES_PROMPT_RE = /^Exactly 3 real clues, 1 (?:champion|team): (.+)\. (?:Guess the Super Bowl-winning team AND season|Guess the team AND season)\.$/;
function parseThreeCluesPrompt(prompt) {
  var m = THREE_CLUES_PROMPT_RE.exec(prompt);
  if (!m) return null;
  var parts = m[1].split('; ').filter(Boolean);
  return parts.length === 3 ? parts : null;
}
function renderThreeCluesProgressiveHtml(game, revealedCount) {
  var clues = parseThreeCluesPrompt(game.payload.prompt);
  if (!clues) return '<div class="quiz-question">' + highlightRankNumbers(game.payload.prompt) + '</div>';
  var shown = clues.slice(0, revealedCount);
  return '<div class="three-clues-count">' + icon('mystery') + ' Clue ' + revealedCount + ' of 3</div>' +
    '<div class="three-clues-list">' + shown.map(function (c, i) {
      return '<div class="three-clues-card' + (i === revealedCount - 1 ? ' three-clues-card-latest' : '') + '">' +
        '<span class="three-clues-num">' + (i + 1) + '</span><span class="three-clues-text">' + esc(c) + '</span></div>';
    }).join('') + '</div>' +
    (revealedCount < 3 ? '<button class="btn-secondary" data-pilot-reveal-clue>' + icon('search') + ' Reveal Clue ' + (revealedCount + 1) + '</button>' : '');
}
function renderEnginePilotPromptHtml(game, s) {
  var promptHtml = highlightRankNumbers(game.payload.prompt);
  var broadcastModes = {
    draft: ['NFL DRAFT ARCHIVE', 'NAME THE TEAM', 'draftarchive'],
    nflGameResult: ['FINAL SCORE', 'PICK THE WINNER', 'result'],
    nflGameBoxscore: ['BOX SCORE', 'YARDAGE BATTLE', 'boxscore'],
    cfbRanking: ['AP POLL', 'FILL THE RANK', 'poll'],
    cfbUpset: ['UPSET ALERT', 'WHO WON?', 'upset'],
    championship: ['POSTSEASON', 'HOW DID THEY FINISH?', 'postseason'],
    heisman: ['HEISMAN FILE', 'NAME THE SCHOOL', 'heisman'],
    cfbRivalry: ['RIVALRY WEEK', 'THE MATCHUP', 'rivalry'],
    cfbRivalryLookup: ['RIVALRY FILE', 'KNOW THE HISTORY', 'rivalfile'],
    spotTheFake: ['ROSTER AUDIT', 'FIND THE FAKE', 'spotfake'],
    cfbGameResult: ['SATURDAY REPLAY', 'PICK THE WINNER', 'saturday'],
    oddCollegeOut: ['OUTLIER SCAN', 'ONE DOESN’T BELONG', 'oddcollege'],
    oneSchoolMissing: ['MISSING SLOT', 'COMPLETE THE GROUP', 'schoolmissing'],
    lineup: ['LINEUP REVEAL', 'NAME THE TEAM', 'lineup'],
    offenseCollege: ['HIDDEN NAMES', 'TRACE THE COLLEGES', 'collegeorigin'],
    lineupCollege: ['COLLEGE TRAIL', 'NAME THE NFL TEAM', 'lineupcollege'],
    sbChampionOffenseCollege: ['CHAMPIONSHIP ROSTER', 'NAME THE CHAMPION', 'sbcollege'],
    threeClues: ['THREE CLUES', 'NAME THE TEAM', 'threeclues'],
    eraGauntlet: ['THROUGH THE DECADES', 'ERA GAUNTLET', 'eragauntlet'],
    franchiseMarathon: ['FRANCHISE FILE', 'MARATHON', 'marathon'],
  };
  var broadcast = s && broadcastModes[s.modeKey];
  if (broadcast) {
    var boardTitle = broadcast[1], boardDetail = '', question = game.payload.prompt;
    if (s.modeKey === 'championship') {
      var seasonMatch = /^How did the (.+) finish the (\d{4}) NFL season\?$/i.exec(question);
      if (seasonMatch) { boardTitle = seasonMatch[1]; boardDetail = seasonMatch[2] + ' SEASON'; }
    } else if (s.modeKey === 'heisman') {
      var heismanMatch = /^Which school did (\d{4}) Heisman Trophy winner (.+) play for\?$/i.exec(question);
      if (heismanMatch) { boardTitle = heismanMatch[2]; boardDetail = heismanMatch[1] + ' WINNER'; }
    } else if (s.modeKey === 'cfbRivalry') {
      var rivalryMatch = /^([^:]{3,90}):\s*(.+)$/.exec(question);
      if (rivalryMatch) { boardTitle = rivalryMatch[1]; question = rivalryMatch[2]; }
    } else if (s.modeKey === 'oneSchoolMissing') {
      var missingMatch = /^Here are (\d+) of the colleges from (.+?): (.+)\. Which real college from that group is missing\?$/i.exec(question);
      if (missingMatch) { boardTitle = missingMatch[2].replace(/^the /i, '').replace(/' real starting offense$/i, ''); boardDetail = missingMatch[1] + ' REVEALED'; question = 'Which real college from that group is missing?'; }
    } else if (s.modeKey === 'lineup' || s.modeKey === 'offenseCollege' || s.modeKey === 'lineupCollege') {
      var lineupSeason = game.payload.visual_payload && game.payload.visual_payload.season;
      if (lineupSeason) boardDetail = String(lineupSeason) + (s.modeKey === 'offenseCollege' ? ' PROJECTED OFFENSE' : ' STARTING OFFENSE');
    } else if (s.modeKey === 'sbChampionOffenseCollege') {
      boardDetail = 'TEAM + SEASON · NAMES HIDDEN';
    } else if (s.modeKey === 'eraGauntlet') {
      boardDetail = (game.payload.visual_payload && game.payload.visual_payload.era_decade_label || 'NFL HISTORY') + ' · STAGE ' + (s.stageIndex + 1);
    } else if (s.modeKey === 'franchiseMarathon') {
      var selectedFranchise = (enginePilotModeConfig(s.modeKey).franchiseChoices.find(function (f) { return f.value === s.filterValue; }) || {}).label || s.filterValue;
      boardTitle = selectedFranchise || boardTitle;
      boardDetail = 'STAGE ' + (s.stageIndex + 1);
    }
    return '<div class="pilot-broadcast-board pilot-broadcast-board--' + broadcast[2] + '">' +
      '<span>' + broadcast[0] + '</span><strong>' + esc(boardTitle) + '</strong>' +
      (boardDetail ? '<em>' + esc(boardDetail) + '</em>' : '') +
      '<i aria-hidden="true"></i></div>' +
      (s.modeKey === 'oneSchoolMissing' && missingMatch ? '<div class="pilot-missing-list">' + missingMatch[3].split(', ').map(function (school) {
        return '<span>' + esc(school) + '</span>';
      }).join('') + '<span class="is-unknown">?</span></div>' : '') +
      (s.modeKey === 'threeClues' || s.modeKey === 'eraGauntlet'
        ? renderThreeCluesProgressiveHtml(game, s.cluesRevealedCount || 1)
        : stadiumQuestionHtml(s.modeKey === 'spotTheFake' ? 'ONE SLOT IS WRONG' :
          (s.modeKey === 'oddCollegeOut' ? 'FIND THE OUTLIER' : 'MAKE THE CALL'), question)) +
      (s.modeKey === 'spotTheFake' && game.payload.visual_template === 'POSITION_LINEUP_COLLEGE' && game.payload.visual_payload
        ? renderPositionLineupCollegeBoard(game.payload.visual_payload, true) : '') +
      (s.modeKey === 'lineup' && game.payload.visual_template === 'POSITION_LINEUP' && game.payload.visual_payload
        ? renderPositionLineupBoard(game.payload.visual_payload) : '') +
      (s.modeKey === 'offenseCollege' && game.payload.visual_template === 'POSITION_LINEUP_COLLEGE' && game.payload.visual_payload
        ? renderPositionLineupCollegeBoard(game.payload.visual_payload, false, true) : '') +
      ((s.modeKey === 'lineupCollege' || s.modeKey === 'sbChampionOffenseCollege' || s.modeKey === 'franchiseMarathon') &&
        game.payload.visual_template === 'POSITION_LINEUP_COLLEGE' && game.payload.visual_payload
        ? renderPositionLineupCollegeBoard(game.payload.visual_payload) : '');
  }
  if (game.payload.visual_template === 'POSITION_LINEUP' && game.payload.visual_payload) {
    return '<div class="quiz-question">' + promptHtml + '</div>' +
      renderPositionLineupBoard(game.payload.visual_payload);
  }
  if (game.payload.visual_template === 'POSITION_LINEUP_COLLEGE' && game.payload.visual_payload) {
    return '<div class="quiz-question">' + promptHtml + '</div>' +
    renderPositionLineupCollegeBoard(game.payload.visual_payload);
  }
  if (s && (s.modeKey === 'threeClues' || s.modeKey === 'eraGauntlet')) {
    return renderThreeCluesProgressiveHtml(game, s.cluesRevealedCount || 1);
  }
  return '<div class="quiz-question">' + promptHtml + '</div>';
}
/* Section 6/7/21 fix: cfg.title used to appear only on the pre-start IDLE
   screen and vanish for the rest of the round -- once play started, the
   only context left on screen was "Question X of Y" with no reminder of
   which mode (or, for Higher/Lower kinds, which real stat) you're even
   playing. Reuses .quiz-progress' existing small/dim text style (same
   discipline as the rest of this file -- no parallel visual language),
   never invents new copy: cfg.title is the same real, human-readable
   string already shown on the Start screen. */
function enginePilotToolbarHtml(cfg, extraOpts) {
  if (!cfg) return '<div class="mode-toolbar"><button class="btn-tiny" data-mode-exit>' + icon('close') + ' Exit to Home</button></div>';
  var opts = { icon: cfg.icon, title: cfg.title };
  if (extraOpts) { for (var k in extraOpts) opts[k] = extraOpts[k]; }
  return renderReadsShellHeader(opts);
}
function renderEnginePilotScreen() {
  var s = state.enginePilot;
  var cfg = enginePilotModeConfig(s ? s.modeKey : enginePilotCurrentModeKey);
  var draftPanelClass = cfg === ENGINE_PILOT_MODES.draft ? 'panel stadium-game broadcast-finish broadcast-finish--draftarchive' : 'panel';
  if (!cfg.flagOn()) return renderHome();
  if (!s) {
    // IDLE -- state.enginePilot hasn't been created yet.
    // Franchise Marathon: a real franchise must be chosen before Start is
    // meaningful (the mode has no "any franchise" default -- see
    // get_public_game()'s own INVALID_REQUEST guard for a missing filter
    // value on a mode that declares caller_filter_key).
    var franchiseHtml = '';
    if (cfg.needsFilterValue) {
      var picked = state.enginePilotPendingFranchise;
      franchiseHtml = '<div class="chip-row" role="group" aria-label="Choose a franchise">' +
        cfg.franchiseChoices.map(function (f) {
          return '<button class="chip-toggle' + (picked === f.value ? ' active' : '') + '" data-pilot-franchise-pick="' + esc(f.value) + '">' +
            esc(f.label) + '</button>';
        }).join('') + '</div>';
    }
    var startDisabled = cfg.needsFilterValue && !state.enginePilotPendingFranchise;
    return '<div class="' + draftPanelClass + '">' +
      (cfg === ENGINE_PILOT_MODES.draft ? broadcastMarqueeHtml('NFL · DRAFT ARCHIVE', 'ON THE CLOCK', cfg.desc) : '<h2 class="panel-title">' + esc(cfg.title) + '</h2>') +
      '<p class="mode-desc">' + esc(cfg.desc) + '</p>' +
      franchiseHtml +
      '<div class="btn-row"><button class="btn-primary" data-pilot-start' + (startDisabled ? ' disabled' : '') + '>Start</button></div>' +
      '</div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.LOADING) {
    // Part 10: a real, football-native loading line -- no "engine"/
    // "Gateway" wording (Part 44: the infrastructure should disappear
    // behind the experience), and aria-live so a screen reader announces
    // the transition instead of going silent between questions.
    // Brand revamp: this line previously had zero motion cue (text only)
    // while every classic-mode loading state got the real spinner --
    // inverted from what you'd expect (the newer flow actually felt
    // LESS animated). Same shared .loading-spinner, compact inline size.
    return '<div class="' + draftPanelClass + '">' + enginePilotToolbarHtml(cfg) +
      '<div class="inline-loading" aria-live="polite"><span class="loading-spinner loading-spinner-sm"></span>Finding your next question&hellip;</div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.ERROR) {
    // Part 11/43: s.error is always shell-owned, polished copy by this
    // point (see enginePilotUserFacingError) -- never a raw server string,
    // never an HTTP status code, never an internal error `code` like
    // GENERATION_BUSY shown as-is. aria-live="assertive" here (vs
    // "polite" elsewhere) since an error is worth interrupting for.
    return '<div class="' + draftPanelClass + '">' + enginePilotToolbarHtml(cfg) +
      '<p class="mode-desc" aria-live="assertive">' + esc(s.error) + '</p>' +
      '<div class="btn-row">' +
      '<button class="btn-primary" data-pilot-retry>Try Again</button>' +
      '<button class="btn-secondary" data-pilot-fallback>' + esc(cfg.fallbackLabel) + '</button>' +
      '</div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.COMPLETE) {
    // Product Growth + Real User Testing pass: this shell is the shared
    // completion screen for ~10 real modes (Offense by College, SB
    // Champion Offense by College, CFB Rankings, CFB Upsets, NFL/CFB Game
    // Result, NFL Box Scores, ...) -- it used to offer only "Play Again",
    // with Home reachable solely via the small toolbar link above. Every
    // other mode's completion screen already pairs Play Again with a real
    // Home button and the same recommended-next-mode nudge; this brings
    // the shared engine-pilot shell in line with that, in one place.
    // Public Mode Wiring pass: a sequential mode's real completion is
    // "reached the real end of the sequence" (a franchise's full real
    // title history; all 7 real represented decades), not a fixed
    // roundSize -- only ever shows a stat this file actually tracked
    // (s.correctCount/s.sequenceStageCount), never a fabricated
    // personal-best/history value this shell doesn't store.
    var completeTitle = 'Round Complete';
    var completeStat = s.correctCount + ' / ' + s.roundSize + ' correct.';
    if (cfg.sequential && s.sequenceCompleted) {
      var stageCount = s.sequenceStageCount != null ? s.sequenceStageCount : s.stageIndex;
      if (s.modeKey === 'franchiseMarathon') {
        var franchiseLabel = (cfg.franchiseChoices.find(function (f) { return f.value === s.filterValue; }) || {}).label || s.filterValue;
        completeTitle = 'Marathon Complete';
        completeStat = 'You played through all ' + stageCount + ' real ' + esc(franchiseLabel) +
          ' history stage' + (stageCount === 1 ? '' : 's') + ' -- ' + s.correctCount + ' / ' + stageCount + ' correct.';
      } else if (s.modeKey === 'eraGauntlet') {
        completeTitle = 'Gauntlet Complete';
        completeStat = 'You reached the end of the gauntlet -- ' + stageCount + ' real historical eras, ' +
          s.correctCount + ' / ' + stageCount + ' correct.';
      }
    }
    // Era Gauntlet distinctness pass: a real era-by-era recap (reusing the
    // same timeline this run already showed in progress, now fully
    // "done", each stage colored by whether it was actually answered
    // correctly) instead of ending on the exact same plain text-only
    // summary every other engine-pilot mode shares -- gives this mode's
    // finish its own identity instead of reading as a generic quiz wrap-up.
    var recapHtml = '';
    if (s.modeKey === 'eraGauntlet' && s.stageResults.length) {
      var recapLabels = (s.current && s.current.payload.visual_payload && s.current.payload.visual_payload.era_sequence_labels)
        || s.stageResults.map(function (r) { return r.decade; });
      recapHtml = renderEraGauntletTimelineHtml(recapLabels.length, recapLabels, s.stageResults);
    }
    // Brand revamp: this shell was the one real gap in the completion-
    // banner treatment (found during the earlier UX audit) -- every
    // mechanicPilot format already got the confetti banner, this ~21-
    // format enginePilot shell just showed a plain heading. Same shared
    // banner now, so every completion screen in the app -- Immaculate
    // Grid, mechanicPilot, and this shell -- reads as the same real
    // Reads moment instead of 2 different finishes.
    return '<div class="' + draftPanelClass + '">' + enginePilotToolbarHtml(cfg) +
      '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' +
      icon('trophy') + ' <h2 class="complete-banner-text">' + esc(completeTitle) + '</h2></div>' +
      '<p class="mode-desc">' + completeStat + '</p>' +
      recapHtml +
      '<div class="btn-row"><button class="btn-primary" data-pilot-start>Play Again</button>' +
      '<button class="btn-secondary" data-share="' + esc(s.modeKey) + '">' + icon('share') + ' Share</button>' +
      '<button class="btn-secondary" data-go="home">Home</button></div>' +
      postGameNextStepsHtml(null) + '</div>';
  }
  // QUESTION_READY and SUBMITTING share this render path (same markup,
  // options just go disabled + a "Checking..." line appears while
  // submitting) -- ANSWERED also falls through here so the question/options
  // stay visible while the reveal renders alongside them, matching how
  // Quiz's own renderQuizQuestion() already does it.
  var game = s.current, answered = s.screen === ENGINE_GAME_SCREEN.ANSWERED;
  var submitting = s.screen === ENGINE_GAME_SCREEN.SUBMITTING;
  var options = game.payload.options;
  // Real backend pass (Creator/Game Quality Correction, Sept 2026) already
  // emits true 2-option packages for game-winner/stat-comparison
  // capabilities (see serializer.finalize_binary_options()) -- whichever
  // Engine Pilot mode's current question happens to carry exactly 2
  // options renders through the shared binary-choice component instead of
  // a vertical 4-option list, with zero backend/state change: same
  // s.pickedOption, same data-pilot-answer index, same pickEnginePilotAnswer().
  var isBinary = options.length === 2;
  // Odd College Out / One School Missing: real "equal candidate cards"
  // (Sections 8/9) instead of a vertical A/B/C/D list -- same real
  // options/correctIndex grading underneath, same data-pilot-answer index.
  var isCandidateCards = s.modeKey === 'oddCollegeOut' || s.modeKey === 'oneSchoolMissing';
  var optionsHtml;
  if (isCandidateCards) {
    optionsHtml = renderCandidateCardsHtml(options, {
      dataAttr: 'data-pilot-answer',
      disabled: s.screen !== ENGINE_GAME_SCREEN.QUESTION_READY,
      state: function (i, opt) {
        if (answered) {
          if (opt === s.answerResult.canonical_answer) return 'correct';
          if (i === s.pickedOption) return 'wrong';
          return '';
        }
        return (submitting && i === s.pickedOption) ? 'selected' : '';
      },
    });
  } else if (isBinary) {
    var sideFor = function (i) {
      var st = 'default';
      if (answered) {
        if (options[i] === s.answerResult.canonical_answer) st = 'correct';
        else if (i === s.pickedOption) st = 'wrong';
      } else if ((submitting || answered) && i === s.pickedOption) {
        st = 'selected';
      }
      return { code: String(i), label: options[i], state: st };
    };
    optionsHtml = renderBinaryChoiceHtml(sideFor(0), sideFor(1), {
      dataAttr: 'data-pilot-answer',
      disabled: s.screen !== ENGINE_GAME_SCREEN.QUESTION_READY,
    });
  } else {
    optionsHtml = '<div class="quiz-options">' +
      options.map(function (opt, i) {
        var cls = 'quiz-option';
        if (answered) {
          if (opt === s.answerResult.canonical_answer) cls += ' correct';
          else if (i === s.pickedOption) cls += ' wrong';
        } else if (submitting && i === s.pickedOption) {
          cls += ' selected';
        }
        return '<button class="' + cls + '" ' + (s.screen === ENGINE_GAME_SCREEN.QUESTION_READY ? 'data-pilot-answer="' + i + '"' : 'disabled') + '>' +
          String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
      }).join('') +
      '</div>';
  }
  // Upset-specific visual accent (Section: CFB Biggest Upsets) -- a real,
  // restrained frame (not a fake "SHOCKING" badge, no fabricated betting-
  // line/underdog data the actual response doesn't carry) applied only to
  // this one mode via its modeKey, since the shared shell below is
  // otherwise identical across all ~12 Engine Pilot modes.
  var broadcastVariant = { draft: 'draftarchive', nflGameResult: 'result', nflGameBoxscore: 'boxscore', cfbRanking: 'poll', cfbUpset: 'upset',
    championship: 'postseason', heisman: 'heisman', cfbRivalry: 'rivalry', cfbRivalryLookup: 'rivalfile', spotTheFake: 'spotfake',
    cfbGameResult: 'saturday', oddCollegeOut: 'oddcollege', oneSchoolMissing: 'schoolmissing', lineup: 'lineup', offenseCollege: 'collegeorigin',
    lineupCollege: 'lineupcollege', sbChampionOffenseCollege: 'sbcollege', threeClues: 'threeclues', eraGauntlet: 'eragauntlet', franchiseMarathon: 'marathon' }[s.modeKey];
  var panelCls = 'panel' + (s.modeKey === 'cfbUpset' ? ' upset-panel' : '') +
    (broadcastVariant ? ' stadium-game pilot-broadcast-game pilot-broadcast-game--' + broadcastVariant : '');
  // Section 7 (progress should match the mechanic): a sequential mode's
  // real progress is "which real stage," not "question X of a fixed
  // roundSize" -- Era Gauntlet's real domain size (7 represented decades)
  // is fixed/known, so it gets a real "N of 7"; Franchise Marathon's real
  // stage count varies per franchise and is only known once the server
  // says SEQUENCE_COMPLETE, so it only ever shows "Stage N" (badge shown
  // in the header via franchiseLabel below), never a fabricated total.
  var progressHtml;
  var franchiseLabel = null;
  if (cfg.sequential && s.modeKey === 'eraGauntlet') {
    var eraSequenceLabels = game.payload && game.payload.visual_payload && game.payload.visual_payload.era_sequence_labels;
    progressHtml = renderEraGauntletTimelineHtml(s.stageIndex, eraSequenceLabels, s.stageResults);
  } else if (cfg.sequential && s.modeKey === 'franchiseMarathon') {
    franchiseLabel = (cfg.franchiseChoices.find(function (f) { return f.value === s.filterValue; }) || {}).label || s.filterValue;
    progressHtml = quizProgressRowHtml('Stage ' + (s.stageIndex + 1), null, null);
  } else {
    progressHtml = quizProgressRowHtml('Question ' + (s.roundIndex + 1) + ' of ' + s.roundSize, s.roundIndex, s.roundSize);
  }
  var headerOpts = { score: s.correctCount + ' correct', difficulty: game.difficulty };
  if (franchiseLabel) headerOpts.badge = franchiseLabel;
  var feedbackNotes = s.answerResult && s.answerResult.notes;
  if (feedbackNotes && /^From the curated Reads Football /i.test(feedbackNotes)) feedbackNotes = '';
  return '<div class="' + panelCls + '">' + enginePilotToolbarHtml(cfg, headerOpts) +
    progressHtml +
    renderEnginePilotPromptHtml(game, s) +
    optionsHtml +
    // Part 9: real, visible feedback that a submission is in flight (not
    // just silently-disabled buttons) -- aria-live so it's announced.
    (submitting ? '<div class="quiz-progress" aria-live="polite">Checking your answer&hellip;</div>' : '') +
    (answered
      ? (broadcastVariant ? '<div class="pilot-broadcast-call pilot-broadcast-call--' + (s.answerResult.correct ? 'good' : 'bad') + '" aria-hidden="true"><span>OFFICIAL CALL</span><strong>' + (s.answerResult.correct ? 'YOU GOT IT' : 'NO GOOD') + '</strong></div>' : '') +
        '<div class="quiz-feedback" aria-live="polite">' + (s.answerResult.correct ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (feedbackNotes ? ' ' + esc(feedbackNotes) : '') + '</div>' +
        '<button class="btn-primary" data-pilot-next>' + (s.roundIndex + 1 >= s.roundSize ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}

/* ============================== Mechanic Pilot shell (public-readiness punch-list) ==============================
   A second shared shell, alongside Engine Pilot above, for the four
   mechanics that do NOT share the "guess" single-question contract
   (MATCHING/SORTING_TIMELINE/HIGHER_LOWER_STREAK/ELIMINATION_SURVIVAL --
   pairing, ordering, streak, and survival are all genuinely different
   interaction shapes, so this shell preserves each one's own real
   mechanic rather than forcing them into multiple-choice, per this
   pass's own instruction). Calls the new, unauthenticated
   /v1/public/mechanics/* routes (gateway/services/public_mechanics.py) --
   never the admin-gated /v1/creator/mechanics/* routes. Reuses
   enginePilotFetchJson/ENGINE_GAME_ERROR_COPY/enginePilotUserFacingError
   from the shell above unchanged (same timeout, same never-show-raw-
   server-text discipline), and the same .panel/.btn-primary/.btn-secondary/
   .quiz-feedback CSS classes -- no parallel visual language. */
var ENGINE_MECHANIC_MODES = {
  matching: {
    publicMode: 'matching_nfl_draft', hash: '#matchingpilot',
    flagOn: function () { return ENABLE_ENGINE_MATCHING_PILOT_V01; },
    title: 'NFL Draft Class Matching', kind: 'matching',
    desc: 'Match each real NFL Draft pick to the real team that drafted him.',
    fallbackLabel: 'Play NFL Draft History (Quiz) Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('NFL Draft History', '', 10); },
  },
  sorting: {
    publicMode: 'sorting_cfb_heisman', hash: '#sortingpilot',
    flagOn: function () { return ENABLE_ENGINE_SORTING_PILOT_V01; },
    title: 'Heisman Timeline', kind: 'sorting',
    desc: 'Put real Heisman Trophy winners in order, earliest year first.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // STAT_LADDER (15-Format Expansion Part 2, format #1) real gap fix --
  // these 3 real public modes existed with no client entry point at all
  // until this pass. Same generic 'sorting' kind as the plain sorting
  // pilot above -- zero new renderer code.
  statLadderNflRushing: {
    publicMode: 'stat_ladder_nfl_rushing', hash: '#statladdernflrushingpilot',
    flagOn: function () { return ENABLE_ENGINE_STAT_LADDER_PILOT_V01; },
    title: 'NFL Rushing Ladder', kind: 'sorting',
    desc: 'Rank these real NFL rushers from a single season, most rushing yards first.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  statLadderNflPassingTd: {
    publicMode: 'stat_ladder_nfl_passing_td', hash: '#statladdernflpassingtdpilot',
    flagOn: function () { return ENABLE_ENGINE_STAT_LADDER_PILOT_V01; },
    title: 'NFL Passing TD Ladder', kind: 'sorting',
    desc: 'Rank these real NFL quarterbacks by career passing touchdowns, most first.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  statLadderCfbRushing: {
    publicMode: 'stat_ladder_cfb_rushing', hash: '#statladdercfbrushingpilot',
    flagOn: function () { return ENABLE_ENGINE_STAT_LADDER_PILOT_V01; },
    title: 'CFB Rushing Ladder', kind: 'sorting',
    desc: 'Rank these real CFB players by career rushing yards, most first.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  higherLowerEngine: {
    publicMode: 'higher_lower_nfl_wins', hash: '#higherlowerenginepilot',
    flagOn: function () { return ENABLE_ENGINE_HIGHER_LOWER_PILOT_V01; },
    title: 'NFL Wins Streak', kind: 'higher_lower',
    desc: 'Guess whether the next real NFL team-season had a higher or lower win total.',
    fallbackLabel: 'Play Higher or Lower Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'home'; },
  },
  elimination: {
    publicMode: 'elimination_nfl_super_bowl', hash: '#eliminationpilot',
    flagOn: function () { return ENABLE_ENGINE_ELIMINATION_PILOT_V01; },
    title: 'Super Bowl Champion Survival', kind: 'elimination',
    desc: 'One miss ends the run. Answer True or False for each real NFL team-season.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // Reusable Game Format System pass: the new `comparison` mechanic,
  // rendered as a real BRACKET_TREE format (renderBracketTreeBody below) --
  // the first mechanic in this shell with more than one real format
  // (see SORT_LIST_DEFAULT/TIMELINE_RIBBON for the other, on 'sorting').
  comparisonBracket: {
    publicMode: 'comparison_nfl_wins', hash: '#comparisonpilot',
    flagOn: function () { return ENABLE_ENGINE_COMPARISON_PILOT_V01; },
    title: 'NFL Wins Bracket', kind: 'comparison',
    desc: 'Predict the real winner of every matchup in this real 8-team bracket, based on regular-season win total.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // ==========================================================================
  // Finish-10-Formats pass: the 10 real new game formats, each backed by a
  // real, live-verified taxonomy from the 40-Format Expansion pass and now
  // wired through the exact same real public pipeline (gateway/services/
  // public_mechanics.py) every mechanic above already uses -- no parallel
  // architecture, no admin-preview-only shortcut.
  connectionGrid: {
    publicMode: 'connection_grid_nfl', hash: '#connectiongridpilot',
    flagOn: function () { return ENABLE_ENGINE_CONNECTION_GRID_PILOT_V01; },
    title: 'NFL Connection Grid', kind: 'grid_constraint',
    desc: 'Each cell needs a real player who satisfies both its row and column criteria.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  perfectDriveNfl: {
    publicMode: 'perfect_drive_nfl', hash: '#perfectdrivenflpilot',
    flagOn: function () { return ENABLE_ENGINE_PERFECT_DRIVE_PILOT_V01; },
    title: 'Perfect Drive (NFL)', kind: 'drive_progression',
    desc: 'Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  perfectDriveCfb: {
    publicMode: 'perfect_drive_cfb', hash: '#perfectdrivecfbpilot',
    flagOn: function () { return ENABLE_ENGINE_PERFECT_DRIVE_PILOT_V01; },
    title: 'Perfect Drive (CFB)', kind: 'drive_progression',
    desc: 'Answer correctly to gain real yardage toward the end zone. One wrong answer ends the drive.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  goalLineStandNfl: {
    publicMode: 'goal_line_stand_nfl', hash: '#goallinestandnflpilot',
    flagOn: function () { return ENABLE_ENGINE_GOAL_LINE_STAND_PILOT_V01; },
    title: 'Goal Line Stand (NFL)', kind: 'drive_progression',
    desc: 'You have 4 downs to score. A wrong answer costs a down.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  goalLineStandCfb: {
    publicMode: 'goal_line_stand_cfb', hash: '#goallinestandcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_GOAL_LINE_STAND_PILOT_V01; },
    title: 'Goal Line Stand (CFB)', kind: 'drive_progression',
    desc: 'You have 4 downs to score. A wrong answer costs a down.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  lineupBuilderNfl: {
    publicMode: 'lineup_builder_nfl', hash: '#lineupbuildernflpilot',
    flagOn: function () { return ENABLE_ENGINE_LINEUP_BUILDER_PILOT_V01; },
    title: '2010s Offense Builder', kind: 'roster_build',
    desc: 'Build a real roster from real 2010s starters -- one real player per slot, no player twice.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  lineupBuilderCfb: {
    publicMode: 'lineup_builder_cfb', hash: '#lineupbuildercfbpilot',
    flagOn: function () { return ENABLE_ENGINE_LINEUP_BUILDER_PILOT_V01; },
    title: 'CFB Skill Position Builder', kind: 'roster_build',
    desc: 'Build a real CFB skill-position lineup -- one real player per slot, no player twice.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  auctionDraftNfl: {
    publicMode: 'auction_draft_nfl', hash: '#auctiondraftnflpilot',
    flagOn: function () { return ENABLE_ENGINE_AUCTION_DRAFT_PILOT_V01; },
    title: 'NFL Auction Draft', kind: 'roster_build',
    desc: 'Draft a real roster one slot at a time under a fictional $50,000,000 budget.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  auctionDraftCfb: {
    publicMode: 'auction_draft_cfb', hash: '#auctiondraftcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_AUCTION_DRAFT_PILOT_V01; },
    title: 'CFB Auction Draft', kind: 'roster_build',
    desc: 'Draft a real roster one slot at a time under a fictional $50,000,000 budget.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  capChallengeNfl: {
    publicMode: 'cap_challenge_nfl', hash: '#capchallengenflpilot',
    flagOn: function () { return ENABLE_ENGINE_CAP_CHALLENGE_PILOT_V01; },
    title: 'NFL Cap Challenge', kind: 'roster_build',
    desc: 'Freely select, swap, or remove real players under a fictional $50,000,000 cap.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  capChallengeCfb: {
    publicMode: 'cap_challenge_cfb', hash: '#capchallengecfbpilot',
    flagOn: function () { return ENABLE_ENGINE_CAP_CHALLENGE_PILOT_V01; },
    title: 'CFB Cap Challenge', kind: 'roster_build',
    desc: 'Freely select, swap, or remove real players under a fictional $50,000,000 cap.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  knockoutTournamentNfl: {
    publicMode: 'knockout_tournament_nfl', hash: '#knockouttournamentnflpilot',
    flagOn: function () { return ENABLE_ENGINE_KNOCKOUT_TOURNAMENT_PILOT_V01; },
    title: 'NFL Knockout Tournament', kind: 'knockout_bracket',
    desc: 'Predict the real winner of every matchup in this real 16-team knockout field.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  knockoutTournamentCfb: {
    publicMode: 'knockout_tournament_cfb', hash: '#knockouttournamentcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_KNOCKOUT_TOURNAMENT_PILOT_V01; },
    title: 'CFB Knockout Tournament', kind: 'knockout_bracket',
    desc: 'Predict the real winner of every matchup in this real 16-team knockout field.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // SIX_DEGREES and CHAIN_REACTION share the identical real bounded-chain
  // backend (tools/director_v04/relationship_chain.py) -- two real format
  // framings, never two implementations. Deliberately distinct hash/mode
  // keys from the EXISTING, unrelated "Six Degrees" (Coach Connections)
  // feature (startSixDegreesRound/ENABLE_ENGINE_SIX_DEGREES_V01) -- this is
  // a bounded, narrower, cross-league format, not that harder, unbounded
  // graph-pathfinding product.
  sixDegreesChain: {
    publicMode: 'six_degrees_cfb_nfl', hash: '#sixdegreeschainpilot',
    flagOn: function () { return ENABLE_ENGINE_SIX_DEGREES_CHAIN_PILOT_V01; },
    title: 'Six Degrees: College to NFL', kind: 'relationship_chain',
    desc: 'See a real player’s college. Guess the real NFL team that drafted him.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  chainReaction: {
    publicMode: 'chain_reaction_cfb_nfl', hash: '#chainreactionpilot',
    flagOn: function () { return ENABLE_ENGINE_CHAIN_REACTION_PILOT_V01; },
    title: 'Chain Reaction: College to NFL', kind: 'relationship_chain',
    desc: 'Follow the real chain from college to the NFL team that drafted him.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  chooseYourPathNfl: {
    publicMode: 'choose_your_path_nfl', hash: '#chooseyourpathpilot',
    flagOn: function () { return ENABLE_ENGINE_CHOOSE_YOUR_PATH_PILOT_V01; },
    title: 'Choose Your Path', kind: 'branch_state',
    desc: 'Pick a path at each step -- your choice determines the next real question.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  chooseYourPathCfb: {
    publicMode: 'choose_your_path_cfb', hash: '#chooseyourpathcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_CHOOSE_YOUR_PATH_PILOT_V01; },
    title: 'Choose Your Path: College Football', kind: 'branch_state',
    desc: 'Pick a path at each step -- your choice determines the next real question.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #2 -- see
  // tools/director_v04/guess_the_season.py's own module docstring.
  guessTheSeason: {
    publicMode: 'guess_the_season_nfl', hash: '#guesstheseasonpilot',
    flagOn: function () { return ENABLE_ENGINE_GUESS_THE_SEASON_PILOT_V01; },
    title: 'Guess the Season', kind: 'guess_the_season',
    desc: 'Read the real clues, then guess the real NFL season they all describe.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #3 -- see
  // tools/director_v04/head_to_head_duel.py's own module docstring.
  headToHeadDuelRushing: {
    publicMode: 'head_to_head_duel_nfl_rushing', hash: '#headtoheadduelrushingpilot',
    flagOn: function () { return ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01; },
    title: 'Rushing Duel', kind: 'pairwise_compare',
    desc: 'Tap whichever real player you think had more rushing yards that season.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  headToHeadDuelPassingTd: {
    publicMode: 'head_to_head_duel_nfl_passing_td', hash: '#headtoheadduelpassingtdpilot',
    flagOn: function () { return ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01; },
    title: 'Passing TD Duel', kind: 'pairwise_compare',
    desc: 'Tap whichever real quarterback you think threw more career passing touchdowns.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  headToHeadDuelCfbRushing: {
    publicMode: 'head_to_head_duel_cfb_rushing', hash: '#headtoheadduelcfbrushingpilot',
    flagOn: function () { return ENABLE_ENGINE_HEAD_TO_HEAD_DUEL_PILOT_V01; },
    title: 'CFB Rushing Duel', kind: 'pairwise_compare',
    desc: 'Tap whichever real CFB player you think has more career rushing yards.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #4 -- see
  // tools/director_v04/head_to_head_duel.py's own module docstring. Same
  // 'pairwise_compare' kind as HEAD_TO_HEAD_DUEL above -- reuses
  // renderPairwiseCompareBody verbatim; the real match_summary this
  // variant's packages carry is handled generically in
  // renderMechanicPilotCompleteSummary below.
  bestOfSevenDuel: {
    publicMode: 'best_of_seven_duel_nfl_qb', hash: '#bestofsevenduelpilot',
    flagOn: function () { return ENABLE_ENGINE_BEST_OF_SEVEN_DUEL_PILOT_V01; },
    title: 'QB Best of Seven', kind: 'pairwise_compare',
    desc: 'Tap whichever real quarterback had more in each of up to 7 real career categories.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #5 -- see
  // tools/director_v04/pick_the_impostor.py's own module docstring.
  pickTheImpostorNfl: {
    publicMode: 'pick_the_impostor_nfl', hash: '#picktheimpostornflpilot',
    flagOn: function () { return ENABLE_ENGINE_PICK_THE_IMPOSTOR_PILOT_V01; },
    title: 'Pick the Impostor', kind: 'pick_the_impostor',
    desc: '3 of these 4 real players were really on the same real NFL roster -- find the one that wasn\'t.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  pickTheImpostorCfb: {
    publicMode: 'pick_the_impostor_cfb', hash: '#picktheimpostorcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_PICK_THE_IMPOSTOR_PILOT_V01; },
    title: 'Pick the Impostor: College Football', kind: 'pick_the_impostor',
    desc: '3 of these 4 real players really played for the same real school -- find the one that didn\'t.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #6 -- see
  // tools/director_v04/pick_the_impostor.py's own module docstring. Same
  // 'pick_the_impostor' kind as PICK_THE_IMPOSTOR above -- reuses
  // renderPickTheImpostorBody verbatim, zero new client code.
  uniqueOneOut: {
    publicMode: 'unique_one_out_nfl', hash: '#uniqueoneoutpilot',
    flagOn: function () { return ENABLE_ENGINE_UNIQUE_ONE_OUT_PILOT_V01; },
    title: 'Unique One Out', kind: 'pick_the_impostor',
    desc: '3 of these 4 real players were really drafted in the same real NFL Draft class -- find the one that wasn\'t.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #7 -- see
  // tools/director_v04/missing_piece.py's own module docstring.
  missingPieceNfl: {
    publicMode: 'missing_piece_nfl', hash: '#missingpiecenflpilot',
    flagOn: function () { return ENABLE_ENGINE_MISSING_PIECE_PILOT_V01; },
    title: 'Missing Piece', kind: 'missing_piece',
    desc: '3 real players from the same real NFL roster are shown -- find the 4th real player who also belongs.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  missingPieceCfb: {
    publicMode: 'missing_piece_cfb', hash: '#missingpiececfbpilot',
    flagOn: function () { return ENABLE_ENGINE_MISSING_PIECE_PILOT_V01; },
    title: 'Missing Piece: College Football', kind: 'missing_piece',
    desc: '3 real players from the same real school roster are shown -- find the 4th real player who also belongs.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #8 -- see
  // tools/director_v04/before_after.py's own module docstring.
  beforeAfterNfl: {
    publicMode: 'before_after_nfl', hash: '#beforeafternflpilot',
    flagOn: function () { return ENABLE_ENGINE_BEFORE_AFTER_PILOT_V01; },
    title: 'Before & After', kind: 'before_after',
    desc: 'Tap whichever real team you think this real player played for FIRST.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  beforeAfterCfb: {
    publicMode: 'before_after_cfb', hash: '#beforeaftercfbpilot',
    flagOn: function () { return ENABLE_ENGINE_BEFORE_AFTER_PILOT_V01; },
    title: 'Before & After: College Football', kind: 'before_after',
    desc: 'Tap whichever real school you think this real player played for FIRST.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #9 -- see
  // tools/director_v04/sorting.py's own module docstring. Same generic
  // 'sorting' kind as STAT_LADDER above -- zero new renderer code.
  mapTheCareerNfl: {
    publicMode: 'map_the_career_nfl', hash: '#mapthecareernflpilot',
    flagOn: function () { return ENABLE_ENGINE_MAP_THE_CAREER_PILOT_V01; },
    title: 'Map the Career', kind: 'sorting',
    desc: 'Put these real teams in the order this real NFL player actually played for them.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  mapTheCareerCfb: {
    publicMode: 'map_the_career_cfb', hash: '#mapthecareercfbpilot',
    flagOn: function () { return ENABLE_ENGINE_MAP_THE_CAREER_PILOT_V01; },
    title: 'Map the Career: College Football', kind: 'sorting',
    desc: 'Put these real schools in the order this real CFB player actually played for them.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #10 -- see
  // tools/director_v04/career_path.py's own module docstring.
  careerPathNfl: {
    publicMode: 'career_path_nfl', hash: '#careerpathnflpilot',
    flagOn: function () { return ENABLE_ENGINE_CAREER_PATH_PILOT_V01; },
    title: 'Career Path', kind: 'career_path',
    desc: 'Read the real career path, then guess whichever real NFL player it belongs to.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  careerPathCfb: {
    publicMode: 'career_path_cfb', hash: '#careerpathcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_CAREER_PATH_PILOT_V01; },
    title: 'Career Path: College Football', kind: 'career_path',
    desc: 'Read the real career path, then guess whichever real CFB player it belongs to.',
    fallbackLabel: 'Play College Football Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #11 -- see
  // tools/director_v04/risk_it.py's own module docstring.
  riskIt: {
    publicMode: 'risk_it_nfl_draft', hash: '#riskitpilot',
    flagOn: function () { return ENABLE_ENGINE_RISK_IT_PILOT_V01; },
    title: 'Risk It', kind: 'risk_it', icon: 'flame',
    desc: 'Pick a real risk tier before you see the question -- a wrong answer costs a life.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- real per-season national passing-yards rank as
  // the recognizability proxy, see risk_it.py's own module docstring.
  riskItCfb: {
    publicMode: 'risk_it_cfb_passing', hash: '#riskitcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_RISK_IT_PILOT_V01; },
    title: 'Risk It (CFB)', kind: 'risk_it', icon: 'flame',
    desc: 'Pick a real risk tier before you see the question -- a wrong answer costs a life.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #12 -- see
  // tools/director_v04/wager_mode.py's own module docstring.
  wagerMode: {
    publicMode: 'wager_mode_mixed', hash: '#wagermodepilot',
    flagOn: function () { return ENABLE_ENGINE_WAGER_MODE_PILOT_V01; },
    title: 'Wager Mode', kind: 'wager_mode',
    desc: 'See only a real category, wager part of your balance, then answer the revealed real question.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #14 -- see
  // tools/director_v04/leaderboard_climb.py's own module docstring.
  leaderboardClimb: {
    publicMode: 'leaderboard_climb_nfl', hash: '#leaderboardclimbpilot',
    flagOn: function () { return ENABLE_ENGINE_LEADERBOARD_CLIMB_PILOT_V01; },
    title: 'Leaderboard Climb', kind: 'leaderboard_climb',
    desc: 'Climb a real leaderboard by tapping whichever real player ranks higher at each rung.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 15-Format Expansion pass (Part 2), format #15 (final of 15) -- see
  // tools/director_v04/blind_resume.py's own module docstring.
  blindResume: {
    publicMode: 'blind_resume_nfl_qb', hash: '#blindresumepilot',
    flagOn: function () { return ENABLE_ENGINE_BLIND_RESUME_PILOT_V01; },
    title: 'Blind Resume', kind: 'blind_resume', icon: 'mystery',
    desc: 'A real player\'s career passing resume is shown with the name hidden -- guess who it is.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- built on cfb_player_season_stats_real, real
  // career completions used in place of the (nonexistent for CFB) games
  // stat. Same kind='blind_resume' renderer as the NFL variant.
  blindResumeCfb: {
    publicMode: 'blind_resume_cfb_qb', hash: '#blindresumecfbpilot',
    flagOn: function () { return ENABLE_ENGINE_BLIND_RESUME_PILOT_V01; },
    title: 'Blind Resume (CFB)', kind: 'blind_resume', icon: 'mystery',
    desc: 'A real college player\'s career passing resume is shown with the name hidden -- guess who it is.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // double_or_nothing.py's own module docstring.
  doubleOrNothing: {
    publicMode: 'double_or_nothing_nfl_draft', hash: '#doubleornothingpilot',
    flagOn: function () { return ENABLE_ENGINE_DOUBLE_OR_NOTHING_PILOT_V01; },
    title: 'Double or Nothing', kind: 'double_or_nothing', icon: 'zap',
    desc: 'Bank your real points or risk them all on the next, harder real question.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
  // see double_or_nothing.py's own module docstring.
  doubleOrNothingCfb: {
    publicMode: 'double_or_nothing_cfb_passing', hash: '#doubleornothingcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_DOUBLE_OR_NOTHING_PILOT_V01; },
    title: 'Double or Nothing (CFB)', kind: 'double_or_nothing', icon: 'zap',
    desc: 'Bank your real points or risk them all on the next, harder real question.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // king_of_the_hill.py's own module docstring.
  kingOfTheHill: {
    publicMode: 'king_of_the_hill_nfl', hash: '#kingofthehillpilot',
    flagOn: function () { return ENABLE_ENGINE_KING_OF_THE_HILL_PILOT_V01; },
    title: 'King of the Hill', kind: 'king_of_the_hill', icon: 'shield',
    desc: 'Defend the real champion team-season against a gauntlet of real random challengers.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- reuses higher_lower.py's own already-certified
  // cfb_standings.total_wins data (FBS only). Same kind='king_of_the_hill'
  // renderer as the NFL variant.
  kingOfTheHillCfb: {
    publicMode: 'king_of_the_hill_cfb', hash: '#kingofthehillcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_KING_OF_THE_HILL_PILOT_V01; },
    title: 'King of the Hill (CFB)', kind: 'king_of_the_hill', icon: 'shield',
    desc: 'Defend the real champion college team-season against a gauntlet of real random challengers.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // fact_or_fake.py's own module docstring.
  factOrFake: {
    publicMode: 'fact_or_fake_nfl_draft', hash: '#factorfakepilot',
    flagOn: function () { return ENABLE_ENGINE_FACT_OR_FAKE_PILOT_V01; },
    title: 'Fact or Fake', kind: 'fact_or_fake', icon: 'search',
    desc: 'Read a real NFL history statement and decide if it’s true or been altered.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- real game-result statement, see
  // fact_or_fake.py's own module docstring.
  factOrFakeCfb: {
    publicMode: 'fact_or_fake_cfb_game', hash: '#factorfakecfbpilot',
    flagOn: function () { return ENABLE_ENGINE_FACT_OR_FAKE_PILOT_V01; },
    title: 'Fact or Fake (CFB)', kind: 'fact_or_fake', icon: 'search',
    desc: 'Read a real college football final score and decide if it’s true or been altered.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // guess_the_ranking.py's own module docstring.
  guessTheRanking: {
    publicMode: 'guess_the_ranking_nfl', hash: '#guesstherankingpilot',
    flagOn: function () { return ENABLE_ENGINE_GUESS_THE_RANKING_PILOT_V01; },
    title: 'Guess the Ranking', kind: 'guess_the_ranking', icon: 'barChart',
    desc: 'A real player is named -- guess their real rank on a real career leaderboard.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- self-contained real top-15 CFB career passing
  // yards query. Same kind='guess_the_ranking' renderer as the NFL variant.
  guessTheRankingCfb: {
    publicMode: 'guess_the_ranking_cfb', hash: '#guesstherankingcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_GUESS_THE_RANKING_PILOT_V01; },
    title: 'Guess the Ranking (CFB)', kind: 'guess_the_ranking', icon: 'barChart',
    desc: 'A real college player is named -- guess their real rank on a real career leaderboard.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // stat_target.py's own module docstring.
  statTarget: {
    publicMode: 'stat_target_nfl_rushing', hash: '#stattargetpilot',
    flagOn: function () { return ENABLE_ENGINE_STAT_TARGET_PILOT_V01; },
    title: 'Stat Target', kind: 'stat_target', icon: 'target',
    desc: 'Tap whichever real player’s real season total came closest to the target.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass (user request: "I want all these formats to be NFL
  // and CFB based not just nfl... for the formats already on the app
  // also") -- built on cfb_player_season_stats_real, see
  // tools/director_v04/stat_target.py's own module docstring for real
  // pool size/coverage. Reuses the exact same kind='stat_target' renderer
  // as the NFL variant -- only the underlying data source differs.
  statTargetCfb: {
    publicMode: 'stat_target_cfb_rushing', hash: '#stattargetcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_STAT_TARGET_PILOT_V01; },
    title: 'Stat Target (CFB)', kind: 'stat_target', icon: 'target',
    desc: 'Tap whichever real college player’s real season total came closest to the target.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // reverse_trivia.py's own module docstring.
  reverseTrivia: {
    publicMode: 'reverse_trivia_nfl_draft', hash: '#reversetriviapilot',
    flagOn: function () { return ENABLE_ENGINE_REVERSE_TRIVIA_PILOT_V01; },
    title: 'Reverse Trivia', kind: 'reverse_trivia', icon: 'sync',
    desc: 'A real player is named -- tap the 1 of 4 real statements that’s actually true about them.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- real season passing stat line, see
  // reverse_trivia.py's own module docstring.
  reverseTriviaCfb: {
    publicMode: 'reverse_trivia_cfb_passing', hash: '#reversetriviacfbpilot',
    flagOn: function () { return ENABLE_ENGINE_REVERSE_TRIVIA_PILOT_V01; },
    title: 'Reverse Trivia (CFB)', kind: 'reverse_trivia', icon: 'sync',
    desc: 'A real college player is named -- tap the 1 of 4 real statements that’s actually true about them.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // three_strikes.py's own module docstring.
  threeStrikes: {
    publicMode: 'three_strikes_nfl_draft', hash: '#threestrikespilot',
    flagOn: function () { return ENABLE_ENGINE_THREE_STRIKES_PILOT_V01; },
    title: 'Three Strikes', kind: 'three_strikes', icon: 'xMark',
    desc: 'Answer real questions of rising difficulty -- a wrong answer costs a strike.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- reuses risk_it.py's own new real CFB tiering,
  // see three_strikes.py's own module docstring.
  threeStrikesCfb: {
    publicMode: 'three_strikes_cfb_passing', hash: '#threestrikescfbpilot',
    flagOn: function () { return ENABLE_ENGINE_THREE_STRIKES_PILOT_V01; },
    title: 'Three Strikes (CFB)', kind: 'three_strikes', icon: 'xMark',
    desc: 'Answer real questions of rising difficulty -- a wrong answer costs a strike.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // mystery_roster.py's own module docstring.
  mysteryRoster: {
    publicMode: 'mystery_roster_nfl', hash: '#mysteryrosterpilot',
    flagOn: function () { return ENABLE_ENGINE_MYSTERY_ROSTER_PILOT_V01; },
    title: 'Mystery Roster', kind: 'mystery_roster', icon: 'lock',
    desc: 'Reveal real clues about a mystery real NFL team-season, or guess at any point.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- real leading-passer/leading-rusher+receiver/
  // class_year substitutes, see mystery_roster.py's own module docstring.
  mysteryRosterCfb: {
    publicMode: 'mystery_roster_cfb', hash: '#mysteryrostercfbpilot',
    flagOn: function () { return ENABLE_ENGINE_MYSTERY_ROSTER_PILOT_V01; },
    title: 'Mystery Roster (CFB)', kind: 'mystery_roster', icon: 'lock',
    desc: 'Reveal real clues about a mystery real college team-season, or guess at any point.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // draft_pick_ladder.py's own module docstring.
  draftPickLadder: {
    publicMode: 'draft_pick_ladder_nfl', hash: '#draftpickladderpilot',
    flagOn: function () { return ENABLE_ENGINE_DRAFT_PICK_LADDER_PILOT_V01; },
    title: 'Draft Pick Ladder', kind: 'draft_pick_ladder',
    desc: 'A real player is named -- guess their real overall draft pick number.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // category_roulette.py's own module docstring.
  categoryRoulette: {
    publicMode: 'category_roulette_mixed', hash: '#categoryroulettepilot',
    flagOn: function () { return ENABLE_ENGINE_CATEGORY_ROULETTE_PILOT_V01; },
    title: 'Category Roulette', kind: 'category_roulette',
    desc: 'Each round’s real category is shown immediately -- answer the real question.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // 75-Format Expansion, Wave 1 -- see tools/director_v04/
  // common_link.py's own module docstring.
  commonLink: {
    publicMode: 'common_link_nfl_draft', hash: '#commonlinkpilot',
    flagOn: function () { return ENABLE_ENGINE_COMMON_LINK_PILOT_V01; },
    title: 'Common Link', kind: 'common_link', icon: 'users',
    desc: '3 real players are named -- guess what real fact connects them.',
    fallbackLabel: 'Play NFL Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'quiz'; startQuizRound('', '', 10); },
  },
  // CFB retrofit pass -- real school/season/conference link types, see
  // common_link.py's own module docstring.
  commonLinkCfb: {
    publicMode: 'common_link_cfb_season', hash: '#commonlinkcfbpilot',
    flagOn: function () { return ENABLE_ENGINE_COMMON_LINK_PILOT_V01; },
    title: 'Common Link (CFB)', kind: 'common_link', icon: 'users',
    desc: '3 real college players are named -- guess what real fact connects them.',
    fallbackLabel: 'Play CFB Quiz Instead',
    fallback: function () { state.mechanicPilot = null; state.screen = 'cfbQuiz'; startCfbQuizRound('', '', 10); },
  },
  // 100-format Expansion Wave 2 -- one shared renderer, 15 genuinely
  // different server-side strategy state machines. No league reskins count
  // twice; every entry below maps to a unique variant/backend contract.
  bingoBlitz: { publicMode: 'bingo_blitz_mixed', hash: '#bingoblitzpilot', flagOn: function () { return true; }, title: 'Bingo Blitz', kind: 'strategy_arcade', icon: 'grid', desc: 'Claim a three-cell line on the board.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  territoryTakeover: { publicMode: 'territory_takeover_mixed', hash: '#territorytakeoverpilot', flagOn: function () { return true; }, title: 'Territory Takeover', kind: 'strategy_arcade', icon: 'flag', desc: 'Choose zones and win the territory battle.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  exactTen: { publicMode: 'exact_ten_mixed', hash: '#exacttenpilot', flagOn: function () { return true; }, title: 'Exact Ten', kind: 'strategy_arcade', icon: 'target', desc: 'Land on exactly 10 without busting.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  pyramidClimb: { publicMode: 'pyramid_climb_mixed', hash: '#pyramidclimbpilot', flagOn: function () { return true; }, title: 'Pyramid Climb', kind: 'strategy_arcade', icon: 'arrowUp', desc: 'Pick lanes and climb five levels.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  lockbox: { publicMode: 'lockbox_mixed', hash: '#lockboxpilot', flagOn: function () { return true; }, title: 'Lockbox', kind: 'strategy_arcade', icon: 'lock', desc: 'Open three locks and crack the vault.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  comboMeter: { publicMode: 'combo_meter_mixed', hash: '#combometerpilot', flagOn: function () { return true; }, title: 'Combo Meter', kind: 'strategy_arcade', icon: 'zap', desc: 'Build a scoring multiplier with a hot streak.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  checkpointRally: { publicMode: 'checkpoint_rally_mixed', hash: '#checkpointrallypilot', flagOn: function () { return true; }, title: 'Checkpoint Rally', kind: 'strategy_arcade', icon: 'flag', desc: 'Race forward and protect saved checkpoints.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  escalator: { publicMode: 'escalator_mixed', hash: '#escalatorpilot', flagOn: function () { return true; }, title: 'Escalator', kind: 'strategy_arcade', icon: 'arrowUp', desc: 'Risk one or two steps and reach the top.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  powerUp: { publicMode: 'power_up_mixed', hash: '#poweruppilot', flagOn: function () { return true; }, title: 'Power Up', kind: 'strategy_arcade', icon: 'zap', desc: 'Earn energy and spend it on a 50/50.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  categoryConquest: { publicMode: 'category_conquest_mixed', hash: '#categoryconquestpilot', flagOn: function () { return true; }, title: 'Category Conquest', kind: 'strategy_arcade', icon: 'trophy', desc: 'Capture every real trivia category.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  scoreboardSwing: { publicMode: 'scoreboard_swing_mixed', hash: '#scoreboardswingpilot', flagOn: function () { return true; }, title: 'Scoreboard Swing', kind: 'strategy_arcade', icon: 'barChart', desc: 'Race the opponent to 21.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  momentumBar: { publicMode: 'momentum_bar_mixed', hash: '#momentumbarpilot', flagOn: function () { return true; }, title: 'Momentum Bar', kind: 'strategy_arcade', icon: 'flame', desc: 'Push momentum to +8 before it collapses.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  timeoutTokens: { publicMode: 'timeout_tokens_mixed', hash: '#timeouttokenspilot', flagOn: function () { return true; }, title: 'Timeout Tokens', kind: 'strategy_arcade', icon: 'timer', desc: 'Manage skips and a double-score token.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  perfectSet: { publicMode: 'perfect_set_mixed', hash: '#perfectsetpilot', flagOn: function () { return true; }, title: 'Perfect Set', kind: 'strategy_arcade', icon: 'trophy', desc: 'Win two of three best-of-three sets.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  tripleOrTake: { publicMode: 'triple_or_take_mixed', hash: '#tripleortakepilot', flagOn: function () { return true; }, title: 'Triple or Take', kind: 'strategy_arcade', icon: 'grid', desc: 'Choose the size of each series and clear it to bank points.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  connectFour: { publicMode: 'connect_four_mixed', hash: '#connectfourpilot', flagOn: function () { return true; }, title: 'Connect Four', kind: 'strategy_arcade', icon: 'grid', desc: 'Drop four in a row before the opponent.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  ticTacToe: { publicMode: 'tic_tac_toe_mixed', hash: '#tictactoepilot', flagOn: function () { return true; }, title: 'Tic-Tac-Toe', kind: 'strategy_arcade', icon: 'grid', desc: 'Claim three squares in a row before the opponent.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  challengeFlag: { publicMode: 'challenge_flag_mixed', hash: '#challengeflagpilot', flagOn: function () { return true; }, title: 'Challenge Flag', kind: 'strategy_arcade', icon: 'flag', desc: 'Use replay challenges to overturn misses.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  extraPoint: { publicMode: 'extra_point_mixed', hash: '#extrapointpilot', flagOn: function () { return true; }, title: 'Extra Point', kind: 'strategy_arcade', icon: 'target', desc: 'Score touchdowns, then choose one or go for two.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  comebackMode: { publicMode: 'comeback_mode_mixed', hash: '#comebackmodepilot', flagOn: function () { return true; }, title: 'Comeback Mode', kind: 'strategy_arcade', icon: 'arrowUp', desc: 'Erase a 21-point deficit in six possessions.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  categoryDraft: { publicMode: 'category_draft_mixed', hash: '#categorydraftpilot', flagOn: function () { return true; }, title: 'Category Draft', kind: 'strategy_arcade', icon: 'grid', desc: 'Draft your categories under a two-use limit.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  threeAndOut: { publicMode: 'three_and_out_mixed', hash: '#threeandoutpilot', flagOn: function () { return true; }, title: 'Three & Out', kind: 'strategy_arcade', icon: 'xMark', desc: 'Convert every three-play drive or the run ends.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  pickYourPoison: { publicMode: 'pick_your_poison_mixed', hash: '#pickyourpoisonpilot', flagOn: function () { return true; }, title: 'Pick Your Poison', kind: 'strategy_arcade', icon: 'versus', desc: 'Choose between two categories before every question.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  secondChanceQueue: { publicMode: 'second_chance_queue_mixed', hash: '#secondchancequeuepilot', flagOn: function () { return true; }, title: 'Second Chance Queue', kind: 'strategy_arcade', icon: 'sync', desc: 'Defer the first miss and replay it at the end.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  coverageShell: { publicMode: 'coverage_shell_mixed', hash: '#coverageshellpilot', flagOn: function () { return true; }, title: 'Coverage Shell', kind: 'strategy_arcade', icon: 'shield', desc: 'Lock down short, middle, and deep zones.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  offenseDefense: { publicMode: 'offense_defense_mixed', hash: '#offensedefensepilot', flagOn: function () { return true; }, title: 'Offense / Defense', kind: 'strategy_arcade', icon: 'versus', desc: 'Alternate offense and defense snaps.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  fieldGoalRange: { publicMode: 'field_goal_range_mixed', hash: '#fieldgoalrangepilot', flagOn: function () { return true; }, title: 'Field Goal Range', kind: 'strategy_arcade', icon: 'target', desc: 'Build field position and decide when to kick.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  twoMinuteDrill: { publicMode: 'two_minute_drill_mixed', hash: '#twominutedrillpilot', flagOn: function () { return true; }, title: 'Two-Minute Drill', kind: 'strategy_arcade', icon: 'timer', desc: 'Choose tempo and beat the clock.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  categoryStreak: { publicMode: 'category_streak_mixed', hash: '#categorystreakpilot', flagOn: function () { return true; }, title: 'Category Streak', kind: 'strategy_arcade', icon: 'flame', desc: 'Build a two-answer streak in every category.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  perfectQuarter: { publicMode: 'perfect_quarter_mixed', hash: '#perfectquarterpilot', flagOn: function () { return true; }, title: 'Perfect Quarter', kind: 'strategy_arcade', icon: 'trophy', desc: 'Score on at least three of four two-question drives.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  redZoneLadder: { publicMode: 'red_zone_ladder_mixed', hash: '#redzoneladderpilot', flagOn: function () { return true; }, title: 'Red Zone Ladder', kind: 'strategy_arcade', icon: 'target', desc: 'Red Zone Ladder strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  driveBuilder: { publicMode: 'drive_builder_mixed', hash: '#drivebuilderpilot', flagOn: function () { return true; }, title: 'Drive Builder', kind: 'strategy_arcade', icon: 'grid', desc: 'Drive Builder strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  hotHandSwitch: { publicMode: 'hot_hand_switch_mixed', hash: '#hothandswitchpilot', flagOn: function () { return true; }, title: 'Hot Hand Switch', kind: 'strategy_arcade', icon: 'flame', desc: 'Hot Hand Switch strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  overtimeShootout: { publicMode: 'overtime_shootout_mixed', hash: '#overtimeshootoutpilot', flagOn: function () { return true; }, title: 'Overtime Shootout', kind: 'strategy_arcade', icon: 'versus', desc: 'Overtime Shootout strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  firstDownChain: { publicMode: 'first_down_chain_mixed', hash: '#firstdownchainpilot', flagOn: function () { return true; }, title: 'First Down Chain', kind: 'strategy_arcade', icon: 'arrowRight', desc: 'First Down Chain strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  blitzPackage: { publicMode: 'blitz_package_mixed', hash: '#blitzpackagepilot', flagOn: function () { return true; }, title: 'Blitz Package', kind: 'strategy_arcade', icon: 'zap', desc: 'Blitz Package strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  zoneControl: { publicMode: 'zone_control_mixed', hash: '#zonecontrolpilot', flagOn: function () { return true; }, title: 'Zone Control', kind: 'strategy_arcade', icon: 'grid', desc: 'Zone Control strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  playCaller: { publicMode: 'play_caller_mixed', hash: '#playcallerpilot', flagOn: function () { return true; }, title: 'Play Caller', kind: 'strategy_arcade', icon: 'football', desc: 'Play Caller strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  possessionArrow: { publicMode: 'possession_arrow_mixed', hash: '#possessionarrowpilot', flagOn: function () { return true; }, title: 'Possession Arrow', kind: 'strategy_arcade', icon: 'sync', desc: 'Possession Arrow strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  suddenDeath: { publicMode: 'sudden_death_mixed', hash: '#suddendeathpilot', flagOn: function () { return true; }, title: 'Sudden Death', kind: 'strategy_arcade', icon: 'xMark', desc: 'Sudden Death strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  scoreBank: { publicMode: 'score_bank_mixed', hash: '#scorebankpilot', flagOn: function () { return true; }, title: 'Score Bank', kind: 'strategy_arcade', icon: 'barChart', desc: 'Score Bank strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  audible: { publicMode: 'audible_mixed', hash: '#audiblepilot', flagOn: function () { return true; }, title: 'Audible', kind: 'strategy_arcade', icon: 'sync', desc: 'Audible strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  fourthDownDecision: { publicMode: 'fourth_down_decision_mixed', hash: '#fourthdowndecisionpilot', flagOn: function () { return true; }, title: 'Fourth Down Decision', kind: 'strategy_arcade', icon: 'flag', desc: 'Fourth Down Decision strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  seriesSweep: { publicMode: 'series_sweep_mixed', hash: '#seriessweeppilot', flagOn: function () { return true; }, title: 'Series Sweep', kind: 'strategy_arcade', icon: 'trophy', desc: 'Series Sweep strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  roadTo100: { publicMode: 'road_to_100_mixed', hash: '#roadto100pilot', flagOn: function () { return true; }, title: 'Road to 100', kind: 'strategy_arcade', icon: 'target', desc: 'Road to 100 strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  optionEraser: { publicMode: 'option_eraser_mixed', hash: '#optioneraserpilot', flagOn: function () { return true; }, title: 'Option Eraser', kind: 'strategy_arcade', icon: 'xMark', desc: 'Option Eraser strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  routeTree: { publicMode: 'route_tree_mixed', hash: '#routetreepilot', flagOn: function () { return true; }, title: 'Route Tree', kind: 'strategy_arcade', icon: 'arrowRight', desc: 'Route Tree strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  turnoverBattle: { publicMode: 'turnover_battle_mixed', hash: '#turnoverbattlepilot', flagOn: function () { return true; }, title: 'Turnover Battle', kind: 'strategy_arcade', icon: 'shield', desc: 'Turnover Battle strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  categoryLockout: { publicMode: 'category_lockout_mixed', hash: '#categorylockoutpilot', flagOn: function () { return true; }, title: 'Category Lockout', kind: 'strategy_arcade', icon: 'lock', desc: 'Category Lockout strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  hailMary: { publicMode: 'hail_mary_mixed', hash: '#hailmarypilot', flagOn: function () { return true; }, title: 'Hail Mary', kind: 'strategy_arcade', icon: 'football', desc: 'Hail Mary strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  movingTarget: { publicMode: 'moving_target_mixed', hash: '#movingtargetpilot', flagOn: function () { return true; }, title: 'Moving Target', kind: 'strategy_arcade', icon: 'target', desc: 'Moving Target strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  draftOrder: { publicMode: 'draft_order_mixed', hash: '#draftorderpilot', flagOn: function () { return true; }, title: 'Draft Order', kind: 'strategy_arcade', icon: 'arrowUp', desc: 'Draft Order strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },
  championshipRun: { publicMode: 'championship_run_mixed', hash: '#championshiprunpilot', flagOn: function () { return true; }, title: 'Championship Run', kind: 'strategy_arcade', icon: 'trophy', desc: 'Championship Run strategy challenge.', fallbackLabel: 'Back Home', fallback: function () { state.mechanicPilot=null; state.screen='home'; } },

};
var mechanicPilotCurrentModeKey = 'matching';
function mechanicPilotModeConfig(modeKey) {
  return ENGINE_MECHANIC_MODES[modeKey] || ENGINE_MECHANIC_MODES.matching;
}
function startMechanicPilotRound(modeKey, sourceModeId) {
  if (modeKey) mechanicPilotCurrentModeKey = modeKey;
  state.mechanicPilot = {
    modeKey: mechanicPilotCurrentModeKey, sourceModeId: sourceModeId || null, screen: ENGINE_GAME_SCREEN.LOADING, roundId: null, view: null,
    result: null, error: null, matchSelection: {}, gridActiveCell: null, rosterOpenSlot: null,
    // Real bug fix ("all the games do this when you get something wrong"):
    // the ERROR screen's "Try Again" button always called
    // loadMechanicPilotRound() unconditionally, even when the failure
    // happened on SUBMITTING an answer (after the player already invested
    // real effort -- clue reveals, a chosen answer) -- silently discarding
    // that in-flight round and starting a brand new one instead of
    // retrying the submission that actually failed. errorContext/
    // lastSubmission let the retry handler do the right thing for each
    // failure instead of always doing the more destructive one.
    errorContext: null, lastSubmission: null,
  };
  state.screen = 'mechanicPilot';
  renderAll();
  loadMechanicPilotRound();
}
function mechanicPilotFallback() {
  var modeKey = (state.mechanicPilot && state.mechanicPilot.modeKey) || mechanicPilotCurrentModeKey;
  mechanicPilotModeConfig(modeKey).fallback();
}
// Real bug fix ("all the games do this when you get something wrong"):
// the ERROR screen's single "Try Again" button used to call
// loadMechanicPilotRound() unconditionally -- correct when the failure
// was on loading a round in the first place, but WRONG when the failure
// was on SUBMITTING an answer: it silently discarded the player's
// already-answered round (which the server still has on record under
// s.roundId) and handed them an unrelated brand-new one instead of
// simply resubmitting the same real answer. Branches on the real context
// recorded at the moment each failure happened.
function mechanicPilotRetry() {
  var s = state.mechanicPilot;
  if (!s) return;
  if (s.errorContext === 'submit' && s.roundId && s.lastSubmission) {
    submitMechanicPilotAction(s.lastSubmission);
    return;
  }
  loadMechanicPilotRound();
}
function loadMechanicPilotRound() {
  var s = state.mechanicPilot;
  if (!s) return;
  var cfg = mechanicPilotModeConfig(s.modeKey);
  s.screen = ENGINE_GAME_SCREEN.LOADING; s.error = null; s.result = null; s.matchSelection = {};
  s.gridActiveCell = null; s.rosterOpenSlot = null;
  renderAll();
  enginePilotFetchJson('/v1/public/mechanics/round?mode=' + encodeURIComponent(cfg.publicMode))
    .then(function (data) {
      if (state.mechanicPilot !== s) return;
      s.roundId = data.round_id; s.view = data.view;
      s.screen = ENGINE_GAME_SCREEN.QUESTION_READY;
      renderAll();
    })
    .catch(function (err) {
      if (state.mechanicPilot !== s) return;
      s.errorContext = 'load';
      s.screen = ENGINE_GAME_SCREEN.ERROR; s.error = enginePilotUserFacingError(err);
      renderAll();
    });
}
function submitMechanicPilotAction(submission) {
  var s = state.mechanicPilot;
  if (!s || !s.roundId) return;
  s.lastSubmission = submission;
  s.screen = ENGINE_GAME_SCREEN.SUBMITTING;
  renderAll();
  enginePilotFetchJson('/v1/public/mechanics/round/' + encodeURIComponent(s.roundId) + '/submit', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission: submission }),
  }).then(function (data) {
    if (state.mechanicPilot !== s) return;
    s.result = data.result; s.view = data.view; s.matchSelection = {};
    s.gridActiveCell = null; s.rosterOpenSlot = null;
    // ROSTER_BUILD's FREE_SELECT flow (CAP_CHALLENGE) has no per-action
    // correct/incorrect concept -- select/deselect are just real,
    // reversible roster edits, not a question with a graded answer.
    // Forcing a full correct/incorrect pause + "Continue" tap after every
    // single select/deselect would be real, needless friction (the format
    // spec's own "freely select, swap, or remove" requirement implies a
    // fluid, non-modal interaction). Only the terminal submit_lineup
    // action -- a real, final, graded outcome -- gets the normal
    // ANSWERED-screen pause below.
    // BRANCH_STATE's root-choice step is the same real shape: picking a
    // path is navigation, not a graded answer (its result is
    // {advanced_to, leaf_question}, with no real correct/incorrect concept
    // at all) -- only the LEAF question afterward is genuinely graded.
    // RISK_IT's own "choose_tier" step is the same real navigation shape:
    // committing to a real risk tier before seeing the question is not
    // itself a graded answer (see risk_it.py's own module docstring) --
    // only the subsequent "answer" action is. WAGER_MODE's own
    // "place_wager" step is identical in shape (see wager_mode.py).
    // MYSTERY_ROSTER's own "reveal" step is the same real navigation
    // shape: revealing another real clue is not itself a graded answer --
    // only the subsequent "guess" action is (see mystery_roster.py).
    if (data.result && (data.result.action === 'select' || data.result.action === 'deselect' ||
        data.result.action === 'choose_tier' || data.result.action === 'place_wager' ||
        data.result.action === 'reveal' || data.result.action === 'skip' || data.result.action === 'vault' ||
        data.result.action === 'accept' ||
        data.result.advanced_to !== undefined)) {
      s.screen = ENGINE_GAME_SCREEN.QUESTION_READY;
      renderAll();
      return;
    }
    var wasCorrect = data.result && (data.result.correct === true || data.result.all_correct === true || data.result.exact_match === true);
    playSound(wasCorrect ? 'correct' : 'wrong');
    s.screen = ENGINE_GAME_SCREEN.ANSWERED;
    renderAll();
  }).catch(function (err) {
    if (state.mechanicPilot !== s) return;
    s.errorContext = 'submit';
    s.screen = ENGINE_GAME_SCREEN.ERROR; s.error = enginePilotUserFacingError(err);
    renderAll();
  });
}
function mechanicPilotAdvance() {
  var s = state.mechanicPilot;
  if (!s) return;
  var completed = s.view && (s.view.completed || s.view.ended || s.view.sequence_complete);
  if (completed) {
    // Section 9/10/22 fix: the last real result/view is still sitting on `s`
    // at this point (mechanicPilotAdvance only clears s.result on the
    // non-complete branch below) -- renderMechanicPilotCompleteSummary reads
    // it straight off s, no new fetch or state needed.
    finishMechanicPilotSession(mechanicPilotModeConfig(s.modeKey), s);
    s.screen = ENGINE_GAME_SCREEN.COMPLETE;
    renderAll();
    return;
  }
  s.screen = ENGINE_GAME_SCREEN.QUESTION_READY; s.result = null;
  renderAll();
}
// User request: "let's make sure that all game modes are connected to
// your Football score" -- same real gap as finishEnginePilotSession()
// above, for this shell's own 4 mechanics (Matching/Sorting/Higher-Lower/
// Elimination; all currently flag-off in production, but the same real
// gap regardless). Each mechanic has its own real "how well did you do"
// shape, so pct isn't one uniform formula: matching/sorting are real
// N-correct-of-N fractions; higher_lower/elimination are open-ended streaks
// with no fixed denominator, so they reuse the exact same streak-to-pct
// heuristic app.js's own legacy Higher or Lower mode already established
// (Math.min(100, streak * 10)) rather than inventing a second one.
function finishMechanicPilotSession(cfg, s) {
  var r = s.result || {}, v = s.view || {};
  var pct = null;
  if (cfg.kind === 'matching' && r.total_pairs) pct = 100 * r.correct_count / r.total_pairs;
  else if (cfg.kind === 'sorting' && r.total_items) pct = 100 * r.correct_positions / r.total_items;
  else if (cfg.kind === 'higher_lower') pct = Math.min(100, (v.streak != null ? v.streak : (r.streak || 0)) * 10);
  else if (cfg.kind === 'elimination') pct = Math.min(100, (v.survived_count != null ? v.survived_count : (r.survived_count || 0)) * 10);
  else if ((cfg.kind === 'comparison' || cfg.kind === 'knockout_bracket') && v.total_matchups) pct = 100 * v.correct_count / v.total_matchups;
  else if (cfg.kind === 'grid_constraint' && v.total_cells) pct = 100 * v.correct_count / v.total_cells;
  else if (cfg.kind === 'drive_progression') pct = v.mode === 'YARDAGE' ? Math.min(100, (v.field_position_yards || 0)) : (v.scored ? 100 : 0);
  else if (cfg.kind === 'roster_build' && v.slots_total) pct = 100 * (v.flow === 'FREE_SELECT' ? (v.submitted ? 1 : 0) : (v.picks_made || 0) / v.slots_total);
  else if (cfg.kind === 'relationship_chain' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'branch_state' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  // Real gap found and fixed this pass: guess_the_season shipped without a
  // branch here at all, so a completed Guess the Season round never
  // updated the player's rating -- same real r.correct-based pattern
  // branch_state above already established for a single-boolean result.
  else if (cfg.kind === 'guess_the_season' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'pairwise_compare' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'pick_the_impostor' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'missing_piece' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'before_after' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'career_path' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'risk_it' && v.completed) pct = Math.min(100, 100 * (v.score || 0) / ((v.round_count || 1) * 3));
  else if (cfg.kind === 'wager_mode' && v.completed) pct = Math.min(100, 100 * (v.balance || 0) / 1000);
  else if (cfg.kind === 'leaderboard_climb' && v.completed) pct = Math.min(100, 100 * (v.ladder_size - v.current_rank) / (v.ladder_size - 1 || 1));
  else if (cfg.kind === 'blind_resume' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'double_or_nothing' && v.completed) pct = Math.min(100, 100 * (v.points || 0) / 1600);
  else if (cfg.kind === 'king_of_the_hill' && v.completed) pct = Math.min(100, (v.consecutive_defenses || 0) * 10);
  else if (cfg.kind === 'fact_or_fake' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'guess_the_ranking' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'stat_target' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'reverse_trivia' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'three_strikes' && v.completed) pct = Math.min(100, 100 * (v.score || 0) / ((v.round_count || 1) * 3));
  else if (cfg.kind === 'mystery_roster' && v.completed) pct = Math.min(100, 100 * (v.score || 0) / ((v.round_count || 1) * 4));
  else if (cfg.kind === 'draft_pick_ladder' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'category_roulette' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'common_link' && r.correct !== undefined) pct = r.correct ? 100 : 0;
  else if (cfg.kind === 'strategy_arcade' && v.completed) {
    var totalAnswered = (v.correct_total || 0) + (v.wrong_total || 0);
    pct = totalAnswered ? 100 * (v.correct_total || 0) / totalAnswered : 0;
  }
  if (pct == null) return;
  pct = Math.max(0, Math.min(100, Math.round(pct)));
  updateRatingDrift(pct);
  // Close the long-standing parity gap between dynamic mechanic games and
  // legacy modes: a completed public format now feeds the same centralized
  // progression, season, personalization, achievements and analytics path.
  // sourceModeId is the discovery route (e.g. bingo_blitz); direct hash
  // launches fall back to the stable public mode id.
  if (typeof pushLeaderboard === 'function') {
    var completionMode = s.sourceModeId || cfg.publicMode || s.modeKey;
    pushLeaderboard(completionMode, {
      lastPct: pct,
      bestPct: pct,
      mechanicKind: cfg.kind,
      publicMode: cfg.publicMode
    });
  }
}
/* Section 9/10/22 fix: the COMPLETE screen used to render nothing but
   "Round Complete" for all four mechanics -- no final score, no streak
   reached, no survived count, no indication of why the round ended. Real
   defect found by actually reading this render path end to end (not
   assumed): every field used below already exists on s.result/s.view by
   the time this screen shows (the last real server response is never
   cleared before COMPLETE), so this is presentation-only, no new fetch,
   no backend change. */
function renderMechanicPilotCompleteSummary(cfg, s) {
  var r = s.result || {};
  var v = s.view || {};
  if (cfg.kind === 'strategy_arcade') {
    return '<p class="mode-desc"><strong>' + esc(v.result_label || 'Complete') + '</strong>' +
      ((v.correct_total || v.wrong_total) ? ' · ' + (v.correct_total || 0) + ' correct, ' + (v.wrong_total || 0) + ' missed.' : '') +
      '</p>';
  }
  if (cfg.kind === 'matching') {
    return '<p class="mode-desc">' + (r.correct_count != null ? r.correct_count + ' of ' + r.total_pairs + ' matched correctly.' : '') + '</p>';
  }
  if (cfg.kind === 'sorting') {
    return '<p class="mode-desc">' + (r.correct_positions != null ? r.correct_positions + ' of ' + r.total_items + ' in the correct spot.' : '') + '</p>';
  }
  if (cfg.kind === 'higher_lower') {
    var finalStreak = v.streak != null ? v.streak : r.streak;
    return '<p class="mode-desc">' + (finalStreak != null ? 'Final streak: ' + finalStreak + '.' : '') +
      (v.next_item === null && r.actual_direction ? ' ' + esc(String(r.revealed_next_label)) + ' was ' + esc(r.actual_direction) + ' — that ended the run.' : '') + '</p>';
  }
  if (cfg.kind === 'elimination') {
    var survived = v.survived_count != null ? v.survived_count : r.survived_count;
    return '<p class="mode-desc">' + (survived != null ? 'Survived ' + survived + ' round' + (survived === 1 ? '' : 's') + '.' : '') +
      (r.correct === false ? ' That one ended the run.' : '') + '</p>';
  }
  if (cfg.kind === 'comparison' || cfg.kind === 'knockout_bracket') {
    return '<p class="mode-desc">' + (v.total_matchups != null ? v.correct_count + ' of ' + v.total_matchups + ' real matchups predicted correctly.' : '') + '</p>' +
      renderBracketTreeBody(v, {});
  }
  if (cfg.kind === 'grid_constraint') {
    return '<p class="mode-desc">' + (v.correct_count != null ? v.correct_count + ' of ' + v.total_cells + ' cells correct.' : '') + '</p>';
  }
  if (cfg.kind === 'drive_progression') {
    return '<p class="mode-desc">' + (v.mode === 'YARDAGE'
      ? (v.scored ? 'Touchdown! ' + v.field_position_yards + ' real yards.' : 'Drive ended at ' + (v.field_position_yards || 0) + ' yards.')
      : (v.scored ? 'You scored with ' + v.downs_remaining + ' down(s) to spare.' : 'Turnover on downs.')) + '</p>';
  }
  if (cfg.kind === 'roster_build') {
    if (v.flow === 'FREE_SELECT') {
      return '<p class="mode-desc">' + (v.submitted ? 'Lineup submitted' + (v.budgeted ? ' -- real fictional cost within the cap.' : '.') : 'Lineup not completed.') + '</p>';
    }
    return '<p class="mode-desc">Roster complete: ' + (v.picks_made != null ? v.picks_made : v.slots_total) + ' of ' + v.slots_total + ' real slots filled.</p>';
  }
  if (cfg.kind === 'relationship_chain') {
    return '<p class="mode-desc">' + (r.full_chain ? 'Real chain: ' + r.full_chain.map(esc).join(' &rarr; ') + '.' : '') + '</p>';
  }
  if (cfg.kind === 'branch_state') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') + (r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'guess_the_season') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') + (r.canonical_answer ? 'The real season was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'pairwise_compare') {
    var pcSummary = '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.correct_label ? esc(r.correct_label) + ' had the real higher value.' : '') + '</p>';
    // BEST_OF_SEVEN_DUEL only: the real overall match outcome, computed
    // from real data alone at generation time (independent of the
    // player's own picks) -- present only on that variant's final round.
    if (r.match_summary) {
      var ms = r.match_summary;
      var matchLine = ms.winner === 'TIE'
        ? 'Real duel tied ' + ms.wins_a + '-' + ms.wins_b + ' across ' + ms.categories_played + ' real categories.'
        : (ms.winner === 'A' ? esc(ms.entity_a_label) : esc(ms.entity_b_label)) + ' won the real duel ' +
          Math.max(ms.wins_a, ms.wins_b) + '-' + Math.min(ms.wins_a, ms.wins_b) +
          ' across ' + ms.categories_played + ' real categories.';
      pcSummary += '<p class="mode-desc">' + matchLine + '</p>';
    }
    return pcSummary;
  }
  if (cfg.kind === 'pick_the_impostor') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real impostor was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'missing_piece') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real missing piece was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'before_after') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.correct_label ? esc(r.correct_label) + ' really came first.' : '') + '</p>';
  }
  if (cfg.kind === 'career_path') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'That real career path belonged to ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'risk_it') {
    return '<p class="mode-desc">' + (v.ended ? 'Run over -- out of real lives! ' : 'Run complete! ') +
      'Final score: ' + v.score + '.</p>';
  }
  if (cfg.kind === 'wager_mode') {
    return '<p class="mode-desc">' + (v.ended ? 'Run over -- balance hit 0! ' : 'Run complete! ') +
      'Final balance: ' + v.balance + '.</p>';
  }
  if (cfg.kind === 'leaderboard_climb') {
    var reachedTop = v.current_rank <= 1;
    return '<p class="mode-desc">' + (reachedTop ? 'You reached the top of the real leaderboard! ' : 'Climb over -- ') +
      'Final real rank reached: #' + v.current_rank + ' of ' + v.ladder_size + '.</p>';
  }
  if (cfg.kind === 'blind_resume') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'That real resume belonged to ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'double_or_nothing') {
    return '<p class="mode-desc">' + (v.banked ? 'You banked ' + v.points + ' real points! ' : 'Run over -- you risked it and lost. ') +
      'Final points: ' + v.points + '.</p>';
  }
  if (cfg.kind === 'king_of_the_hill') {
    return '<p class="mode-desc">' + (v.ended ? 'Run over -- ' : 'Out of real challengers -- ') +
      esc(v.champion) + ' ' + (v.ended ? 'was the real champion when you fell' : 'remains undefeated real champion') +
      '. Consecutive defenses: ' + v.consecutive_defenses + '.</p>';
  }
  if (cfg.kind === 'fact_or_fake') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'That statement was really ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'guess_the_ranking') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real rank was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'stat_target') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'Closest was really ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'reverse_trivia') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real true statement was: ' + esc(r.canonical_answer) : '') + '</p>';
  }
  if (cfg.kind === 'three_strikes') {
    return '<p class="mode-desc">' + (v.ended ? 'Run over -- out of real strikes! ' : 'Run complete! ') +
      'Final score: ' + v.score + '.</p>';
  }
  if (cfg.kind === 'mystery_roster') {
    return '<p class="mode-desc">Round complete! Final score: ' + v.score + '.</p>';
  }
  if (cfg.kind === 'draft_pick_ladder') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real answer was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'category_roulette') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real answer was ' + esc(r.canonical_answer) + '.' : '') + '</p>';
  }
  if (cfg.kind === 'common_link') {
    return '<p class="mode-desc">' + (r.correct ? 'Correct! ' : 'Not quite -- ') +
      (r.canonical_answer ? 'The real link was: ' + esc(r.canonical_answer) : '') + '</p>';
  }
  return '';
}
/* Section 6/7/21 fix: same persistent-title fix as enginePilotToolbarHtml
   above, for the Mechanic Pilot shell.
   Risk & Wager visual identity pass: upgraded to the same shared
   renderReadsShellHeader() every enginePilot format + Who Am I already
   use, instead of a bare title/exit bar -- brings mechanicPilot's 10
   formats to visual parity with the rest of the app in one place rather
   than a per-format patch. RISK_IT/THREE_STRIKES/DOUBLE_OR_NOTHING
   additionally surface their real score/lives/strikes/tier through the
   header's chip system (cfg.kind-gated since each format's view shape
   differs); every other kind just gets the plain title+exit header,
   unchanged in substance from before. */
function mechanicPilotToolbarHtml(cfg, s) {
  var v = s && s.view;
  var opts = { title: cfg ? cfg.title : '', icon: cfg && cfg.icon, exitAttr: 'data-mechanic-exit' };
  if (v && cfg) {
    if (cfg.kind === 'risk_it') {
      opts.score = v.score; opts.lives = v.lives; opts.livesTotal = 3;
      if (v.tier) opts.tier = { name: v.tier, points: v.points };
    } else if (cfg.kind === 'three_strikes') {
      opts.score = v.score; opts.streak = v.streak; opts.strikes = v.strikes; opts.strikesTotal = 3;
      if (v.tier) opts.tier = { name: v.tier, points: v.points };
    } else if (cfg.kind === 'double_or_nothing') {
      opts.score = v.points;
      if (v.tier) opts.tier = { name: v.tier };
    } else if (v.score != null) {
      opts.score = v.score;
    }
  }
  return renderReadsShellHeader(opts);
}

var _STADIUM_BROADCAST_KINDS = {
  draft_pick_ladder: 'draftladder',
  sorting: 'order',
  comparison: 'bracket',
  knockout_bracket: 'knockout',
  grid_constraint: 'connectiongrid',
  roster_build: 'roster',
  drive_progression: 'drive',
  risk_it: 'risk',
  double_or_nothing: 'double',
  fact_or_fake: 'review',
  three_strikes: 'strikes',
  wager_mode: 'wager',
  blind_resume: 'scout',
  king_of_the_hill: 'hill',
  guess_the_ranking: 'ranking',
  stat_target: 'target',
  pick_the_impostor: 'impostor',
  missing_piece: 'missing',
  career_path: 'journey',
  mystery_roster: 'mystery',
  common_link: 'link',
  higher_lower: 'momentum',
  elimination: 'survival',
  category_roulette: 'roulette',
  leaderboard_climb: 'climb',
  before_after: 'timeline',
  reverse_trivia: 'verify',
  relationship_chain: 'chain',
  guess_the_season: 'archive',
  pairwise_compare: 'duel',
  branch_state: 'path',
  strategy_arcade: 'strategy',
};
function mechanicPilotPanelClass(cfg, s) {
  var variant = cfg && _STADIUM_BROADCAST_KINDS[cfg.kind];
  if (!variant) return 'panel';
  var stateClass = s && s.screen === ENGINE_GAME_SCREEN.ANSWERED ? ' is-answered' : '';
  return 'panel stadium-game stadium-game--' + variant + stateClass;
}
function stadiumRoundBar(label, current, total) {
  var safeCurrent = Math.max(1, Number(current) || 1);
  var safeTotal = Math.max(safeCurrent, Number(total) || safeCurrent);
  var pct = Math.min(100, Math.round(100 * safeCurrent / safeTotal));
  return '<div class="stadium-round-bar"><span class="stadium-live-dot"></span>' +
    '<span class="stadium-round-label">' + esc(label) + '</span>' +
    '<span class="stadium-round-count">' + safeCurrent + ' / ' + safeTotal + '</span>' +
    '<span class="stadium-round-track"><span style="width:' + pct + '%"></span></span></div>';
}
function stadiumQuestionHtml(kicker, prompt) {
  return '<section class="stadium-question-card"><div class="stadium-question-kicker">' + esc(kicker) + '</div>' +
    '<div class="quiz-question stadium-question">' + esc(prompt || '') + '</div></section>';
}
function stadiumModeIntroHtml(kicker, headline, detail) {
  return '<div class="stadium-mode-intro"><span>' + esc(kicker) + '</span><strong>' + esc(headline) + '</strong>' +
    (detail ? '<em>' + esc(detail) + '</em>' : '') + '<i aria-hidden="true"></i></div>';
}
function renderStadiumResultMoment(cfg, s, wasCorrect) {
  if (!cfg || !_STADIUM_BROADCAST_KINDS[cfg.kind]) return '';
  var r = s.result || {}, v = s.view || {}, eyebrow = 'FINAL CALL', title = wasCorrect ? 'GOOD CALL' : 'NO GOOD', sub = '';
  if (cfg.kind === 'drive_progression') {
    eyebrow = 'DRIVE UPDATE';
    title = v.scored ? 'TOUCHDOWN' : (wasCorrect ? (r.yards_gained ? '+' + r.yards_gained + ' YARDS' : 'CHAINS MOVING') : 'DRIVE STALLED');
    sub = v.scored ? 'You finished the drive.' : (wasCorrect ? 'Keep marching.' : 'Regroup for the next snap.');
  } else if (cfg.kind === 'risk_it') {
    eyebrow = 'RISK RESULT';
    title = wasCorrect ? 'RISK CASHED' : 'LIFE LOST';
    sub = wasCorrect ? '+' + (r.points_earned || 0) + ' on the board' : 'That gamble did not hit.';
  } else if (cfg.kind === 'three_strikes') {
    eyebrow = 'DRIVE RESULT';
    title = wasCorrect ? 'CHAIN MOVING' : 'STRIKE';
    sub = wasCorrect ? '+' + (r.points_earned || 0) + ' points' : 'One light goes dark.';
  } else if (cfg.kind === 'double_or_nothing') {
    eyebrow = 'JUMBOTRON';
    if (r.action === 'bank') {
      title = 'LOCKED IN'; sub = (r.final_points || 0) + ' points secured';
    } else {
      title = wasCorrect ? 'DOUBLE!' : 'BUST';
      sub = wasCorrect ? (r.points || 0) + ' points now on the line' : 'The pot is gone.';
    }
  } else if (cfg.kind === 'fact_or_fake') {
    eyebrow = 'BOOTH REVIEW';
    title = wasCorrect ? 'CALL CONFIRMED' : 'CALL OVERTURNED';
    sub = r.canonical_answer ? 'The ruling: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'wager_mode') {
    eyebrow = 'WAGER RESULT';
    title = wasCorrect ? 'TICKET CASHED' : 'BET MISSED';
    sub = (wasCorrect ? '+' : '-') + (r.wager || 0) + ' from the balance';
  } else if (cfg.kind === 'blind_resume') {
    eyebrow = 'SCOUTING DEPARTMENT';
    title = wasCorrect ? 'PLAYER IDENTIFIED' : 'IDENTITY MISSED';
    sub = r.canonical_answer ? 'The file belonged to ' + r.canonical_answer : '';
  } else if (cfg.kind === 'king_of_the_hill') {
    eyebrow = 'TITLE FIGHT';
    title = wasCorrect ? (r.canonical_answer === 'champion' ? 'CHAMPION DEFENDS' : 'NEW CHAMPION') : 'DETHRONED';
    sub = r.winner_label ? r.winner_label + ' owns the hill' : '';
  } else if (cfg.kind === 'guess_the_ranking') {
    eyebrow = 'LEADERBOARD UPDATE';
    title = wasCorrect ? 'RANK LOCKED' : 'OFF THE BOARD';
    sub = r.canonical_answer ? 'Official rank: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'stat_target') {
    eyebrow = 'TARGET RESULT';
    title = wasCorrect ? 'BULLSEYE' : 'OFF TARGET';
    sub = r.canonical_answer ? 'Closest: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'pick_the_impostor') {
    eyebrow = 'SECURITY CHECK';
    title = wasCorrect ? 'IMPOSTOR FOUND' : 'WRONG SUSPECT';
    sub = r.canonical_answer ? 'The impostor: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'missing_piece') {
    eyebrow = 'BOARD COMPLETE';
    title = wasCorrect ? 'PERFECT FIT' : 'PIECE MISSED';
    sub = r.canonical_answer ? 'Missing piece: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'career_path') {
    eyebrow = 'TRANSACTION WIRE';
    title = wasCorrect ? 'PLAYER TRACKED' : 'PATH MISSED';
    sub = r.canonical_answer ? 'Career belonged to ' + r.canonical_answer : '';
  } else if (cfg.kind === 'mystery_roster') {
    eyebrow = 'ROSTER REVEAL';
    title = wasCorrect ? 'TEAM IDENTIFIED' : 'MYSTERY STANDS';
    sub = r.canonical_answer ? 'It was ' + r.canonical_answer : '';
  } else if (cfg.kind === 'common_link') {
    eyebrow = 'CONNECTION FOUND';
    title = wasCorrect ? 'LINK LOCKED' : 'LINK BROKEN';
    sub = r.canonical_answer ? r.canonical_answer : '';
  } else if (cfg.kind === 'higher_lower') {
    eyebrow = 'STREAK CHECK';
    title = wasCorrect ? 'STREAK ALIVE' : 'STREAK OVER';
    sub = r.actual_direction ? 'The next team was ' + r.actual_direction : '';
  } else if (cfg.kind === 'elimination') {
    eyebrow = 'SURVIVAL BOARD';
    title = wasCorrect ? 'ADVANCE' : 'ELIMINATED';
    sub = r.actual_membership == null ? '' : (r.actual_membership ? 'That team-season was a champion.' : 'That team-season was not a champion.');
  } else if (cfg.kind === 'category_roulette') {
    eyebrow = 'CATEGORY CALL';
    title = wasCorrect ? 'NAILED IT' : 'MISSED IT';
    sub = r.canonical_answer ? 'Answer: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'leaderboard_climb') {
    eyebrow = 'RANKING UPDATE';
    title = wasCorrect ? 'CLIMB ON' : 'CLIMB OVER';
    sub = wasCorrect && r.new_rank != null ? 'Now ranked #' + r.new_rank : (r.correct_label ? 'Higher: ' + r.correct_label : '');
  } else if (cfg.kind === 'before_after') {
    eyebrow = 'TIMELINE REVIEW';
    title = wasCorrect ? 'ORDER CONFIRMED' : 'ORDER REVERSED';
    sub = r.correct_label ? r.correct_label + ' came first' : '';
  } else if (cfg.kind === 'reverse_trivia') {
    eyebrow = 'FACT CHECK'; title = wasCorrect ? 'VERIFIED' : 'FALSE LEAD';
    sub = r.canonical_answer ? 'The true statement: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'relationship_chain') {
    eyebrow = 'CONNECTION CHECK'; title = wasCorrect ? 'CHAIN COMPLETE' : 'LINK MISSING';
    sub = r.canonical_answer ? 'Destination: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'guess_the_season') {
    eyebrow = 'ARCHIVE REVEAL'; title = wasCorrect ? 'YEAR FOUND' : 'WRONG SEASON';
    sub = r.canonical_answer ? 'The season: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'pairwise_compare') {
    eyebrow = 'DUEL RESULT'; title = wasCorrect ? 'WINNER PICKED' : 'UPSET';
    sub = r.canonical_answer ? 'Winner: ' + r.canonical_answer : '';
  } else if (cfg.kind === 'branch_state') {
    eyebrow = 'PATH RESULT'; title = wasCorrect ? 'ROUTE CLEARED' : 'ROADBLOCK';
    sub = r.canonical_answer ? 'Answer: ' + r.canonical_answer : '';
  }
  return '<div class="stadium-result stadium-result--' + (wasCorrect ? 'good' : 'bad') + '" aria-hidden="true">' +
    '<span class="stadium-result-sweep"></span><span class="stadium-result-eyebrow">' + esc(eyebrow) + '</span>' +
    '<strong class="stadium-result-title">' + esc(title) + '</strong>' +
    (sub ? '<span class="stadium-result-sub">' + esc(sub) + '</span>' : '') + '</div>';
}
/* UI/UX pass: this used to render 'Result: ' + JSON.stringify(s.result) --
   the raw backend response object -- directly as the player's feedback
   text (a real correct/wrong/canonical_mapping/notes payload shown
   verbatim). Replaced with real, mechanic-specific human copy, matching
   the same correct/wrong feedback shape every other mode already uses
   (see renderQuizSummary and friends in app.js). Never leaks a field name. */
function renderMechanicPilotFeedback(cfg, s) {
  var r = s.result || {};
  var wasCorrect = r.all_correct === true || r.exact_match === true || r.correct === true;
  var headline, detail;
  if (cfg.kind === 'matching') {
    headline = wasCorrect ? 'All matched correctly!' : 'Not quite.';
    detail = r.correct_count + ' of ' + r.total_pairs + ' matched correctly.';
  } else if (cfg.kind === 'sorting') {
    headline = wasCorrect ? 'Perfect order!' : 'Not quite.';
    detail = r.correct_positions + ' of ' + r.total_items + ' in the correct spot.';
    // STAT_LADDER rounds (sorting.py's real values_by_item_id) reveal the
    // real stat total per player as evidence, in real descending order --
    // TIMELINE_RIBBON/SORT_LIST_DEFAULT rounds have no values_by_item_id,
    // so this stays absent for them exactly as before. Plain text, no
    // markup: this whole `detail` string is esc()'d as one block by this
    // function's own return statement below, same as every other branch.
    if (r.values_by_item_id && r.canonical_order && s.lastSortLabels) {
      var labels = s.lastSortLabels;
      detail += ' -- ' + r.canonical_order.map(function (itemId) {
        return (labels[itemId] || itemId) + ': ' + String(r.values_by_item_id[itemId]);
      }).join(', ');
    }
  } else if (cfg.kind === 'higher_lower') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = esc(r.revealed_next_label) + ' was ' + esc(r.actual_direction) + '.';
  } else if (cfg.kind === 'elimination') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.actual_membership ? 'That one was real.' : 'That one wasn’t real.';
  } else if (cfg.kind === 'comparison' || cfg.kind === 'knockout_bracket') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = 'Real winner: ' + esc(r.real_winner) + ' (' + r.value_a + '-' + r.value_b + ').';
  } else if (cfg.kind === 'grid_constraint') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? 'Correct!' : 'Not a real match for both criteria.';
    detail = esc(r.row_label) + ' &times; ' + esc(r.col_label);
  } else if (cfg.kind === 'drive_progression') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? (r.yards_gained ? '+' + r.yards_gained + ' yards!' : 'Correct!') : 'Not quite.';
    detail = 'Real answer: ' + esc(r.canonical_answer) + '.';
  } else if (cfg.kind === 'roster_build') {
    wasCorrect = true; // a locked-in pick or a successful lineup submission -- never a "wrong answer" concept
    if (r.action === 'submit_lineup') {
      headline = 'Lineup submitted!';
      detail = r.total_spent != null ? 'Total fictional cost: $' + Math.round(r.total_spent).toLocaleString() + '.' : '';
    } else {
      headline = esc(r.display_name) + ' added at ' + esc(r.slot || r.position) + '.';
      detail = r.cost != null ? 'Cost: $' + Math.round(r.cost).toLocaleString() : '';
    }
  } else if (cfg.kind === 'relationship_chain') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = 'Real answer: ' + esc(r.canonical_answer) + '.';
  } else if (cfg.kind === 'branch_state') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'guess_the_season') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real season was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'pairwise_compare') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = (r.correct_label && r.value_a != null && r.value_b != null)
      ? esc(r.correct_label) + ' had the real higher value (' + r.value_a + ' vs ' + r.value_b + ').' : '';
  } else if (cfg.kind === 'pick_the_impostor') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real impostor was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'missing_piece') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real missing piece was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'before_after') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = (r.correct_label && r.season_a != null && r.season_b != null)
      ? esc(r.correct_label) + ' really came first (' + r.season_a + ' vs ' + r.season_b + ').' : '';
  } else if (cfg.kind === 'career_path') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'That real career path belonged to ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'risk_it') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? '+' + r.points_earned + (r.points_earned === 1 ? ' point!' : ' points!') : 'Not quite -- you lost a life.';
    detail = r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'wager_mode') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? '+' + r.wager + ' to your balance!' : '-' + r.wager + ' from your balance.';
    detail = r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'leaderboard_climb') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? 'Climbed to rank #' + r.new_rank + '!' : 'Climb over.';
    detail = (r.correct_label && r.value_a != null && r.value_b != null)
      ? esc(r.correct_label) + ' really ranks higher (' + r.value_a + ' vs ' + r.value_b + ').' : '';
  } else if (cfg.kind === 'blind_resume') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'That real resume belonged to ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'double_or_nothing') {
    if (r.action === 'bank') {
      wasCorrect = true;
      headline = 'Banked ' + r.final_points + ' points!';
      detail = '';
    } else {
      wasCorrect = r.correct === true;
      headline = wasCorrect ? 'Correct! Now at ' + r.points + ' points.' : 'Wrong -- you lost it all.';
      detail = r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '';
    }
  } else if (cfg.kind === 'king_of_the_hill') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? (r.canonical_answer === 'champion' ? 'Champion defends!' : 'New champion!') : 'Dethroned.';
    detail = (r.winner_label && r.champion_value != null && r.challenger_value != null)
      ? esc(r.winner_label) + ' really had more wins (' + r.champion_value + ' vs ' + r.challenger_value + ').' : '';
  } else if (cfg.kind === 'fact_or_fake') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'That statement was really ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'guess_the_ranking') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real rank was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'stat_target') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'Closest was really ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'reverse_trivia') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real true statement was: ' + esc(r.canonical_answer) : '';
  } else if (cfg.kind === 'three_strikes') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? '+' + r.points_earned + (r.points_earned === 1 ? ' point!' : ' points!') : 'Not quite -- you lost a strike.';
    detail = r.canonical_answer ? 'Real answer: ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'mystery_roster') {
    wasCorrect = r.correct === true;
    headline = wasCorrect ? '+' + r.points_earned + (r.points_earned === 1 ? ' point!' : ' points!') : 'Not quite.';
    detail = r.canonical_answer ? 'It was really the ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'draft_pick_ladder') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real answer was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'category_roulette') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real answer was ' + esc(r.canonical_answer) + '.' : '';
  } else if (cfg.kind === 'common_link') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.canonical_answer ? 'The real link was: ' + esc(r.canonical_answer) : '';
  } else {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = '';
  }
  // Same real .quiz-feedback/.feedback-good/.feedback-bad shell every
  // other mode in app.js already uses (e.g. the Engine Pilot render just
  // above this file's own line ~474) -- no parallel feedback style.
  return renderStadiumResultMoment(cfg, s, wasCorrect) + '<div class="quiz-feedback" aria-live="polite">' +
    '<span class="' + (wasCorrect ? 'feedback-good' : 'feedback-bad') + '">' +
    (wasCorrect ? icon('check') : icon('xMark')) + ' ' + esc(headline) + '</span>' +
    (detail ? ' ' + esc(detail) : '') + '</div>';
}
function renderStrategyArcadeBody(v, s) {
  var status = (v.status_items || []).map(function (it) {
    return '<div class="strategy-stat"><span>' + esc(String(it.label)) + '</span><strong>' + esc(String(it.value)) + '</strong></div>';
  }).join('');
  var boardCols = Math.max(1, Number(v.board_columns || 3));
  var board = (v.board || []).length ? '<div class="strategy-board' + (boardCols === 7 ? ' is-connect-four' : '') + '" style="grid-template-columns:repeat(' + boardCols + ',minmax(0,1fr))">' + v.board.map(function (cell) {
    var value = String(cell.value || 'OPEN');
    var cls = value === 'CLAIMED' || value === 'CAPTURED' || value === 'YOU' || value === 'OPEN' ? ' is-good' :
      (value === 'BURNT' || value === 'MISSED' || value === 'THEM' ? ' is-bad' : '');
    if (boardCols === 7) {
      var disc = value === 'YOU' ? '●' : (value === 'THEM' ? '○' : '·');
      return '<div class="strategy-cell strategy-disc' + cls + '" aria-label="' + esc(cell.label + ' ' + value) + '"><strong>' + disc + '</strong></div>';
    }
    return '<div class="strategy-cell' + cls + '"><span>' + esc(cell.label) + '</span><strong>' + esc(value) + '</strong></div>';
  }).join('') + '</div>' : '';
  var header = stadiumModeIntroHtml('STRATEGY ARCADE', v.title || 'Reads Strategy', v.goal_text || '') +
    (status ? '<div class="strategy-scoreboard">' + status + '</div>' : '') + board;
  if (v.phase === 'COMPLETE') {
    return header + stadiumQuestionHtml('FINAL', v.result_label || 'Round complete.');
  }
  if (v.phase === 'SELECT') {
    return header + stadiumQuestionHtml('MAKE YOUR MOVE', v.interaction_text || 'Choose your next move.') +
      '<div class="strategy-actions">' + (v.actions || []).map(function (a) {
        return '<button class="btn-primary strategy-action" data-mechanic-strategy-action="' + esc(a.id) + '">' + esc(a.label) + '</button>';
      }).join('') + '</div>';
  }
  return header +
    (v.selected_label ? '<div class="strategy-selection">LOCKED: <strong>' + esc(v.selected_label) + '</strong></div>' : '') +
    stadiumQuestionHtml(v.category || 'REAL FOOTBALL', v.prompt || '') +
    renderCandidateCardsHtml((v.options || []).map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-strategy-answer',
    });
}

function renderMechanicPilotBody(cfg, s) {
  var v = s.view;
  if (cfg.kind === 'matching') {
    var mapping = s.matchSelection;
    // Section 19/8 fix: same duplicate-prevention affordance the admin
    // mechanic-preview harness already established for this exact mechanic
    // (its own .match-right-chip.used) -- a right item already paired to a
    // DIFFERENT left item is shown dim/inert here too, instead of letting
    // the player silently assign the same team to two picks with no warning
    // until submit.
    var usedRightBy = {};
    Object.keys(mapping).forEach(function (leftId) { usedRightBy[mapping[leftId]] = leftId; });
    return '<div class="quiz-question">' + esc(v.prompt) + '</div>' +
      v.left_items.map(function (li) {
        var chosen = mapping[li.item_id];
        return '<div class="match-row' + (chosen ? ' paired' : '') + '"><div class="match-left">' + esc(li.label) + '</div>' +
          '<div class="match-right-list">' + v.right_items.map(function (ri) {
            var isChosenHere = chosen === ri.item_id;
            var usedElsewhere = !isChosenHere && usedRightBy[ri.item_id] !== undefined && usedRightBy[ri.item_id] !== li.item_id;
            return '<span class="match-right-chip' + (isChosenHere ? ' selected' : '') + (usedElsewhere ? ' used' : '') + '" data-match-left="' + esc(li.item_id) + '" data-match-right="' + esc(ri.item_id) + '">' + esc(ri.label) + '</span>';
          }).join('') + '</div></div>';
      }).join('') +
      '<div class="btn-row"><button class="btn-primary" data-match-submit' + (Object.keys(mapping).length < v.left_items.length ? ' disabled' : '') + '>Submit Matches</button></div>';
  }
  if (cfg.kind === 'sorting') {
    if (!s.sortOrder) s.sortOrder = v.items_shuffled.map(function (it) { return it.item_id; });
    if (!s.sortFormat) s.sortFormat = 'SORT_LIST_DEFAULT';
    var labelFor = function (id) { var it = v.items_shuffled.filter(function (x) { return x.item_id === id; })[0]; return it ? it.label : id; };
    // Reusable Game Format System pass: the SAME real sorting round/data
    // (s.sortOrder, the up/down mutation, the submit contract) playable in
    // either format -- TIMELINE_RIBBON is a pure alternate presentation,
    // never a second copy of the underlying game state (Section 16's own
    // "same knowledge, different format" requirement).
    var formatToggle = '<div class="chip-row">' +
      '<button class="chip-toggle' + (s.sortFormat === 'SORT_LIST_DEFAULT' ? ' active' : '') + '" data-mechanic-sort-format="SORT_LIST_DEFAULT">List</button>' +
      '<button class="chip-toggle' + (s.sortFormat === 'TIMELINE_RIBBON' ? ' active' : '') + '" data-mechanic-sort-format="TIMELINE_RIBBON">Timeline</button>' +
      '</div>';
    if (s.sortFormat === 'TIMELINE_RIBBON') {
      return stadiumModeIntroHtml('THE TIMELINE', 'PUT IT IN ORDER', cfg.title) +
        stadiumQuestionHtml('SEQUENCE CHECK', v.prompt) + formatToggle +
        '<div class="timeline-ribbon">' + s.sortOrder.map(function (id, i) {
          var atStart = i === 0, atEnd = i === s.sortOrder.length - 1;
          return '<div class="timeline-card">' +
            '<button class="btn-tiny" data-sort-up="' + i + '"' + (atStart ? ' disabled' : '') + '>&larr;</button>' +
            '<span class="timeline-card-label">' + esc(labelFor(id)) + '</span>' +
            '<button class="btn-tiny" data-sort-down="' + i + '"' + (atEnd ? ' disabled' : '') + '>&rarr;</button>' +
            '</div>';
        }).join('') + '</div>' +
        '<div class="btn-row"><button class="btn-primary" data-sort-submit>Submit Order</button></div>';
    }
    return stadiumModeIntroHtml('THE TIMELINE', 'PUT IT IN ORDER', cfg.title) +
      stadiumQuestionHtml('SEQUENCE CHECK', v.prompt) + formatToggle +
      s.sortOrder.map(function (id, i) {
        // Section 8 polish: the up/down click handler already no-ops safely
        // at the ends (app.js's bounds check), but the buttons themselves
        // looked identically active there -- disabling them at the actual
        // boundary makes "this is already first/last" visible, not just safe.
        var atTop = i === 0, atBottom = i === s.sortOrder.length - 1;
        return '<div class="sort-row"><span>' + (i + 1) + '. ' + esc(labelFor(id)) + '</span><span class="sort-controls">' +
          '<button class="btn-tiny" data-sort-up="' + i + '"' + (atTop ? ' disabled' : '') + '>Up</button>' +
          '<button class="btn-tiny" data-sort-down="' + i + '"' + (atBottom ? ' disabled' : '') + '>Down</button></span></div>';
      }).join('') +
      '<div class="btn-row"><button class="btn-primary" data-sort-submit>Submit Order</button></div>';
  }
  if (cfg.kind === 'higher_lower') {
    return '<div class="momentum-scorebug"><span>WIN STREAK</span><strong>' + (v.streak || 0) + '</strong></div>' +
      '<div class="momentum-matchup"><div class="momentum-team"><span>ON THE BOARD</span><strong>' + esc(v.current_item.label) + '</strong><em>' + esc(String(v.current_item.value)) + ' WINS</em></div>' +
      '<span class="momentum-vs">VS</span><div class="momentum-team is-unknown"><span>UP NEXT</span><strong>' + (v.next_item ? esc(v.next_item.label) : 'No more teams') + '</strong>' +
      '<em>' + (v.next_item && v.next_item.value !== undefined ? esc(String(v.next_item.value)) + ' WINS' : '? WINS') + '</em></div></div>' +
      stadiumQuestionHtml('MAKE THE CALL', 'Will the next team-season have more or fewer wins?') +
      // data-mechanic-hl-guess, deliberately NOT data-hl-guess -- that
      // attribute already belongs to the legacy, client-side higherLower
      // mode's own buttons (app.js), which fire a completely different
      // handler (submitHigherLowerGuess). Reusing it here would silently
      // call the wrong function whenever this screen is showing.
      (v.ended ? '' : '<div class="btn-row momentum-actions"><button class="btn-primary" data-mechanic-hl-guess="higher">Higher ↑</button><button class="btn-primary" data-mechanic-hl-guess="lower">Lower ↓</button></div>');
  }
  if (cfg.kind === 'elimination') {
    return '<div class="survival-scoreboard"><span>STILL STANDING</span><strong>' + (v.survived_count || 0) + '</strong><em>ONE MISS ENDS THE RUN</em></div>' +
      stadiumQuestionHtml('SURVIVE THE NEXT CALL', v.current_prompt || 'No more challenges remain.') +
      (v.ended ? '' : '<div class="btn-row survival-actions"><button class="btn-primary" data-elim-guess="true">True</button><button class="btn-primary" data-elim-guess="false">False</button></div>');
  }
  if (cfg.kind === 'comparison' || cfg.kind === 'knockout_bracket') {
    // Finish-10-Formats pass: KNOCKOUT_TOURNAMENT's real view shape
    // (rounds/picks_made/total_matchups/correct_count) is byte-identical to
    // COMPARISON_BRACKET's -- confirmed directly against mechanic_engine.py,
    // which routes both through the same _comparison_client_view/
    // _comparison_evaluate functions server-side. Reuses renderBracketTreeBody
    // verbatim; the only difference is the real field size (4/8/16 vs a
    // fixed 8), which that function already renders generically.
    return stadiumModeIntroHtml(cfg.kind === 'knockout_bracket' ? 'KNOCKOUT TOURNAMENT' : 'BRACKET DESK',
      'PICK THE WINNER', cfg.title) +
      '<div class="stadium-picks-count">PICKS MADE <strong>' + (v.picks_made || 0) + ' / ' + (v.total_matchups || 0) + '</strong></div>' +
      renderBracketTreeBody(v, s);
  }
  if (cfg.kind === 'grid_constraint') return renderConnectionGridBody(v, s);
  if (cfg.kind === 'drive_progression') return renderDriveProgressionBody(v, s);
  if (cfg.kind === 'roster_build') return renderRosterBuildBody(v, s);
  if (cfg.kind === 'relationship_chain') return renderRelationshipChainBody(v, s);
  if (cfg.kind === 'branch_state') return renderBranchStateBody(v, s);
  if (cfg.kind === 'guess_the_season') return renderGuessTheSeasonBody(v, s);
  if (cfg.kind === 'pairwise_compare') return renderPairwiseCompareBody(v, s);
  if (cfg.kind === 'pick_the_impostor') return renderPickTheImpostorBody(v, s);
  if (cfg.kind === 'missing_piece') return renderMissingPieceBody(v, s);
  if (cfg.kind === 'before_after') return renderBeforeAfterBody(v, s);
  if (cfg.kind === 'career_path') return renderCareerPathBody(v, s);
  if (cfg.kind === 'risk_it') return renderRiskItBody(v, s);
  if (cfg.kind === 'wager_mode') return renderWagerModeBody(v, s);
  if (cfg.kind === 'leaderboard_climb') return renderLeaderboardClimbBody(v, s);
  if (cfg.kind === 'blind_resume') return renderBlindResumeBody(v, s);
  if (cfg.kind === 'double_or_nothing') return renderDoubleOrNothingBody(v, s);
  if (cfg.kind === 'king_of_the_hill') return renderKingOfTheHillBody(v, s);
  if (cfg.kind === 'fact_or_fake') return renderFactOrFakeBody(v, s);
  if (cfg.kind === 'guess_the_ranking') return renderGuessTheRankingBody(v, s);
  if (cfg.kind === 'stat_target') return renderStatTargetBody(v, s);
  if (cfg.kind === 'reverse_trivia') return renderReverseTriviaBody(v, s);
  if (cfg.kind === 'three_strikes') return renderThreeStrikesBody(v, s);
  if (cfg.kind === 'mystery_roster') return renderMysteryRosterBody(v, s);
  if (cfg.kind === 'draft_pick_ladder') return renderDraftPickLadderBody(v, s);
  if (cfg.kind === 'category_roulette') return renderCategoryRouletteBody(v, s);
  if (cfg.kind === 'common_link') return renderCommonLinkBody(v, s);
  if (cfg.kind === 'strategy_arcade') return renderStrategyArcadeBody(v, s);
  return '';
}
/* ============================== Finish-10-Formats pass: 5 new
   Mechanic Pilot body renderers (KNOCKOUT_TOURNAMENT reuses
   renderBracketTreeBody above unchanged) ==============================
   Each follows the exact same real discipline every renderer above
   already established: render server-provided state verbatim, submit via
   submitMechanicPilotAction() (never decide correctness client-side), and
   reuse existing CSS primitives (.panel/.quiz-option/.btn-primary/
   .status-line/.chip-toggle) wherever the shape allows, adding only the
   handful of genuinely new classes each format's shape requires
   (.grid-board/.drive-meter/.roster-slot/.chain-node -- see reads.css). */

// CONNECTION_GRID: tap a cell to make it "active," type a real name, submit.
// Never renders a precomputed valid-answer list -- the server's view only
// ever carries the two real criteria LABELS per cell (see
// grid_constraint.py's own module docstring for why: a client-visible
// answer key would defeat the whole point of live server verification).
function renderConnectionGridBody(v, s) {
  if (!s.gridActiveCell) s.gridActiveCell = null;
  var rows = v.row_labels || [], cols = v.col_labels || [];
  var cellsByKey = {};
  (v.cells || []).forEach(function (c) { cellsByKey[c.row_index + ':' + c.col_index] = c; });
  var gridHtml = '<div class="grid-board" style="--grid-cols:' + cols.length + '">' +
    '<div class="grid-board-cell grid-board-corner"></div>' +
    cols.map(function (c) { return '<div class="grid-board-cell grid-board-header">' + esc(c) + '</div>'; }).join('') +
    rows.map(function (rowLabel, ri) {
      return '<div class="grid-board-cell grid-board-header">' + esc(rowLabel) + '</div>' +
        cols.map(function (colLabel, ci) {
          var key = ri + ':' + ci;
          var cell = cellsByKey[key];
          var answered = cell && cell.your_guess !== undefined;
          var cls = 'grid-board-cell grid-board-answer';
          if (answered) cls += cell.correct ? ' correct' : ' incorrect';
          else if (s.gridActiveCell === key) cls += ' selected';
          var label = answered ? esc(cell.your_guess) : (s.gridActiveCell === key ? 'Typing&hellip;' : 'Tap to answer');
          return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-mechanic-grid-cell="' + key + '"') + '>' + label + '</button>';
        }).join('');
    }).join('') +
    '</div>';
  var inputHtml = '';
  if (s.gridActiveCell) {
    var parts = s.gridActiveCell.split(':');
    inputHtml = '<div class="grid-answer-row">' +
      '<div class="mode-desc">' + esc(rows[parts[0]]) + ' &times; ' + esc(cols[parts[1]]) + '</div>' +
      '<input type="text" class="learn-filter-input" id="mechanic-grid-input" placeholder="Type a real player name" autocomplete="off">' +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-grid-submit>Submit</button>' +
      '<button class="btn-secondary" data-mechanic-grid-cancel>Cancel</button></div></div>';
  }
  return stadiumModeIntroHtml('CONNECTION BOARD', 'FIND THE LINK', 'One real player for each intersection') +
    '<div class="stadium-picks-count">CELLS FILLED <strong>' + (v.cells_answered || 0) + ' / ' + (v.total_cells || 9) +
    '</strong><span>' + (v.correct_count || 0) + ' correct</span></div>' + gridHtml + inputHtml;
}

// DRIVE_PROGRESSION: PERFECT_DRIVE (YARDAGE) and GOAL_LINE_STAND (DOWNS)
// share this one renderer but stay visually distinct per their real
// server-reported `mode`, matching the format spec's own explicit
// requirement -- a yardage meter for one, a downs counter for the other.
function renderDriveProgressionBody(v, s) {
  var statusHtml;
  if (v.mode === 'YARDAGE') {
    var pos = v.field_position_yards || 0, total = v.field_length_yards || 100;
    var pct = Math.min(100, Math.round(100 * pos / total));
    statusHtml = '<div class="broadcast-field" aria-label="' + pos + ' of ' + total + ' yards">' +
      '<div class="broadcast-field-endzone">END ZONE</div><div class="broadcast-field-lines"></div>' +
      '<div class="broadcast-field-drive" style="width:' + pct + '%"></div>' +
      '<div class="broadcast-field-ball" style="left:' + pct + '%"><span></span></div>' +
      '<div class="broadcast-field-score"><strong>' + pos + '</strong><span>YARDS</span></div></div>';
  } else {
    var downsLeft = v.downs_remaining != null ? v.downs_remaining : (v.downs_total || 4);
    var downsTotal = v.downs_total || 4;
    var boxes = [];
    for (var i = 0; i < downsTotal; i++) boxes.push('<span class="goal-line-down' + (i < downsLeft ? ' is-live' : '') + '"><b>' + (i + 1) + '</b></span>');
    statusHtml = '<div class="goal-line-board"><span class="goal-line-kicker">GOAL LINE STAND</span>' +
      '<strong>DOWN ' + Math.min(downsTotal, downsTotal - downsLeft + 1) + '</strong><div class="goal-line-downs">' + boxes.join('') + '</div></div>';
  }
  if (v.ended) {
    return statusHtml + '<div class="quiz-feedback" aria-live="polite">' +
      (v.scored ? '<span class="feedback-good">' + icon('check') + ' Touchdown!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Drive ended.</span>') +
      '</div>';
  }
  var optionsHtml = '<div class="quiz-options">' + (v.options || []).map(function (opt, i) {
    return '<button class="quiz-option" data-mechanic-drive-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
  }).join('') + '</div>';
  return statusHtml + stadiumQuestionHtml(v.mode === 'YARDAGE' ? 'NEXT PLAY' : 'MAKE THE STOP', v.prompt) + optionsHtml;
}

// ROSTER_BUILD: LINEUP_BUILDER (unbudgeted), AUCTION_DRAFT (SEQUENTIAL
// budgeted), CAP_CHALLENGE (FREE_SELECT budgeted) all share this renderer,
// branching on the server-reported real `flow`/`budgeted` fields -- never
// a client-side guess at which variant is active.
function renderRosterBuildBody(v, s) {
  var rosterIntro = stadiumModeIntroHtml(v.budgeted ? 'FRONT OFFICE · BUDGET LIVE' : 'ROSTER ROOM',
    v.budgeted ? 'BUILD YOUR SQUAD' : 'FILL THE LINEUP',
    (v.slots_total || v.roster_slots && v.roster_slots.length || 0) + ' roster spots');
  var budgetHtml = v.budgeted
    ? '<div class="budget-display">Budget remaining: <strong>$' + Math.round(v.remaining_budget).toLocaleString() +
      '</strong> / $' + Math.round(v.budget_total).toLocaleString() + '</div>'
    : '';
  if (v.flow === 'FREE_SELECT') {
    if (!s.rosterOpenSlot) s.rosterOpenSlot = null;
    var slotsHtml = '<div class="roster-slots">' + v.roster_slots.map(function (slot, i) {
      var picked = v.roster[i];
      var cls = 'roster-slot' + (picked ? ' roster-slot-filled' : '') + (s.rosterOpenSlot === i ? ' roster-slot-open' : '');
      var body = picked
        ? esc(picked.display_name) + (v.budgeted ? ' <span class="roster-slot-cost">$' + Math.round(picked.cost).toLocaleString() + '</span>' : '') +
          (v.submitted ? '' : ' <button class="btn-tiny" data-mechanic-roster-deselect="' + i + '">Remove</button>')
        : 'Tap to fill';
      return '<div class="' + cls + '"><div class="roster-slot-label">' + esc(slot) + '</div>' +
        '<div class="roster-slot-body" ' + (!picked && !v.submitted ? 'data-mechanic-roster-slot="' + i + '"' : '') + '>' + body + '</div></div>';
    }).join('') + '</div>';
    var candidatesHtml = '';
    if (s.rosterOpenSlot !== null && !v.submitted) {
      var cands = (v.pool_by_slot && v.pool_by_slot[String(s.rosterOpenSlot)]) || [];
      candidatesHtml = '<div class="roster-candidate-list">' + cands.slice(0, 30).map(function (p) {
        return '<button class="roster-candidate" data-mechanic-roster-candidate="' + esc(p.player_id) + '">' + esc(p.display_name) +
          (v.budgeted ? ' <span class="roster-slot-cost">$' + Math.round(p.cost).toLocaleString() + '</span>' : '') + '</button>';
      }).join('') + '</div>';
    }
    var allFilled = v.roster.every(function (r) { return r; });
    return rosterIntro + '<div class="stadium-picks-count">SPOTS FILLED <strong>' + v.slots_filled + ' / ' + v.slots_total + '</strong></div>' + budgetHtml +
      slotsHtml + candidatesHtml +
      (v.submitted ? '' : '<div class="btn-row"><button class="btn-primary" data-mechanic-roster-submit-lineup' +
        (allFilled ? '' : ' disabled') + '>Submit Lineup</button></div>');
  }
  // SEQUENTIAL flow (AUCTION_DRAFT / LINEUP_BUILDER): one slot at a time,
  // pick locks in immediately.
  var filledHtml = '<div class="roster-slots">' + v.roster.map(function (pick) {
    return '<div class="roster-slot roster-slot-filled"><div class="roster-slot-label">' + esc(pick.slot) + '</div>' +
      '<div class="roster-slot-body">' + esc(pick.display_name) +
      (v.budgeted ? ' <span class="roster-slot-cost">$' + Math.round(pick.cost).toLocaleString() + '</span>' : '') + '</div></div>';
  }).join('') + '</div>';
  if (v.completed) {
    return rosterIntro + '<div class="stadium-picks-count">ROSTER COMPLETE <strong>' + v.picks_made + ' / ' + v.slots_total + '</strong></div>' + budgetHtml + filledHtml;
  }
  var poolHtml = '<div class="roster-candidate-list">' + (v.remaining_pool || []).slice(0, 30).map(function (p) {
    return '<button class="roster-candidate" data-mechanic-roster-pick="' + esc(p.player_id) + '">' + esc(p.display_name) +
      (v.budgeted ? ' <span class="roster-slot-cost">$' + Math.round(p.cost).toLocaleString() + '</span>' : '') + '</button>';
  }).join('') + '</div>';
  return rosterIntro + '<div class="stadium-picks-count">ON THE CLOCK <strong>' + esc(v.current_slot) + '</strong><span>' + v.picks_made + ' / ' + v.slots_total + ' filled</span></div>' +
    budgetHtml + filledHtml + poolHtml;
}

// SIX_DEGREES / CHAIN_REACTION: a real, bounded 2-hop chain -- the start
// node is shown, the player types the real end-node name, never shown the
// full chain upfront (see relationship_chain.py's own module docstring).
function renderRelationshipChainBody(v, s) {
  return stadiumRoundBar('CONNECT THE DOTS', v.round_index + 1, v.round_count) +
    '<div class="connection-board"><span class="connection-kicker">STARTING POINT</span>' +
    '<strong class="connection-origin">' + esc(v.start_node.label) + '</strong>' +
    '<div class="connection-route" aria-hidden="true"><i></i><i></i><i></i></div>' +
    '<span class="connection-destination">YOUR DESTINATION</span></div>' +
    stadiumQuestionHtml('COMPLETE THE CHAIN', v.prompt) +
    '<div class="stadium-entry"><input type="text" class="learn-filter-input" id="mechanic-chain-input" placeholder="Type the real answer" autocomplete="off">' +
    '<button class="btn-primary" data-mechanic-chain-submit>Connect</button></div>';
}

// GUESS_THE_SEASON: same free-text-guess shape as RELATIONSHIP_CHAIN above
// (a real typed answer, not multiple choice) -- reuses the identical
// .learn-filter-input + Submit pattern rather than a third input style.
function renderGuessTheSeasonBody(v, s) {
  return stadiumRoundBar('ARCHIVE FILE', v.round_index + 1, v.round_count) +
    '<div class="archive-board"><div class="archive-stamp">SEASON <strong>????</strong></div>' +
    '<div class="archive-clues">' + v.clues.map(function (cl, i) {
      return '<div class="archive-clue"><span>CLUE ' + String(i + 1).padStart(2, '0') + '</span><strong>' + esc(cl.display_text) + '</strong></div>';
    }).join('') + '</div></div>' +
    stadiumQuestionHtml('NAME THE YEAR', 'Which real NFL season do these clues describe?') +
    '<div class="stadium-entry"><input type="text" class="learn-filter-input" id="mechanic-season-input" placeholder="e.g. 2019" ' +
    'inputmode="numeric" pattern="[0-9]*" maxlength="4" autocomplete="off">' +
    '<button class="btn-primary" data-mechanic-season-submit>Lock In</button></div>';
}

// HEAD_TO_HEAD_DUEL: reuses renderBinaryChoiceHtml (app.js) verbatim, its
// first real reuse site -- see visual_templates.py's own HEAD_TO_HEAD
// entry for the disclosed consolidation note this format fulfills.
function renderPairwiseCompareBody(v, s) {
  return stadiumRoundBar('HEAD TO HEAD', v.round_index + 1, v.round_count) +
    '<div class="duel-marquee"><span>PLAYER A</span><b>VS</b><span>PLAYER B</span></div>' +
    stadiumQuestionHtml('THE MATCHUP', v.prompt) +
    renderBinaryChoiceHtml(
      { code: 'A', label: v.entity_a.label },
      { code: 'B', label: v.entity_b.label },
      { dataAttr: 'data-mechanic-duel-choice' },
    );
}

// PICK_THE_IMPOSTOR: reuses renderCandidateCardsHtml (app.js), the same
// "equal candidate cards" component Odd College Out/One School Missing
// already use -- the click handler resolves the clicked card's index
// back to this round's real, already-shuffled item_id via the current
// view (see app.js's data-mechanic-impostor-pick handler).
function renderPickTheImpostorBody(v, s) {
  return stadiumRoundBar('IDENTITY CHECK', v.round_index + 1, v.round_count) +
    '<div class="impostor-scan"><span class="impostor-reticle"></span><strong>ONE DOESN’T BELONG</strong>' +
    '<span>SCAN THE GROUP. FLAG THE OUTLIER.</span></div>' +
    stadiumQuestionHtml('FIND THE IMPOSTOR', v.prompt) +
    renderCandidateCardsHtml(v.items.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-impostor-pick',
    });
}

// MISSING_PIECE: the real given group_members are shown as context (reuses
// .chain-node, the same real component GUESS_THE_SEASON's own clue list
// already uses -- zero new CSS), then the 4 real candidates below via
// renderCandidateCardsHtml, same as PICK_THE_IMPOSTOR.
function renderMissingPieceBody(v, s) {
  return stadiumRoundBar('COMPLETE THE BOARD', v.round_index + 1, v.round_count) +
    '<div class="missing-board">' + v.group_members.map(function (label) {
      return '<div class="missing-board-piece">' + esc(label) + '</div>';
    }).join('') + '<div class="missing-board-piece is-empty"><strong>?</strong><span>MISSING</span></div></div>' +
    stadiumQuestionHtml('FILL THE OPEN SLOT', v.prompt) +
    renderCandidateCardsHtml(v.items.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-missing-piece-pick',
    });
}

// BEFORE_AFTER: identical {choice: 'A'|'B'} submission shape to
// PAIRWISE_COMPARE, so this reuses renderBinaryChoiceHtml AND the same
// data-mechanic-duel-choice click handler verbatim -- zero new app.js
// plumbing needed for this format.
function renderBeforeAfterBody(v, s) {
  return stadiumRoundBar('CAREER TIMELINE', v.round_index + 1, v.round_count) +
    '<div class="timeline-faceoff"><span>THEN</span><i></i><span>NOW</span></div>' +
    stadiumQuestionHtml('WHICH CAME FIRST?', v.prompt) +
    renderBinaryChoiceHtml(
      { code: 'A', label: v.entity_a.label },
      { code: 'B', label: v.entity_b.label },
      { dataAttr: 'data-mechanic-duel-choice' },
    );
}

// CAREER_PATH: the inverse of MAP_THE_CAREER -- shows the real, already-
// ordered path (reuses .chain-node/.chain-connector) then 4 real
// candidate players (reuses renderCandidateCardsHtml), same as
// PICK_THE_IMPOSTOR/MISSING_PIECE. Zero new CSS.
function renderCareerPathBody(v, s) {
  return stadiumRoundBar('CAREER TRANSACTION WIRE', v.round_index + 1, v.round_count) +
    '<div class="career-route">' + v.path.map(function (label, i) {
      return '<div class="career-stop"><span>' + (i + 1) + '</span><strong>' + esc(label) + '</strong></div>';
    }).join('<div class="career-route-line"><i></i></div>') + '</div>' +
    stadiumQuestionHtml('NAME THE TRAVELER', 'Which player had this career path?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-career-path-pick',
    });
}

// RISK_IT: real 2-step round -- awaiting_tier=true shows the 3 real risk
// tiers (point value only, no question content, matching the format's
// own "commit before you see it" rule); awaiting_tier=false shows that
// tier's real question via renderCandidateCardsHtml, same as
// PICK_THE_IMPOSTOR/CAREER_PATH.
// Risk & Wager visual identity pass: score/lives moved into the shared
// shell header (mechanicPilotToolbarHtml) so this only needs the real
// round-progress line; the 3 plain .chip-toggle buttons became a real
// tier-select-grid (color/icon-coded LOW=green target/MEDIUM=gold zap/
// HIGH=red flame, same real point value, same data-mechanic-risk-tier
// attribute so app.js's click handler needs zero changes).
var _TIER_SELECT_META = {
  LOW: { icon: 'target', cls: 'low' }, MEDIUM: { icon: 'zap', cls: 'medium' }, HIGH: { icon: 'flame', cls: 'high' },
};
function renderRiskItBody(v, s) {
  var roundLine = stadiumRoundBar('LIVE · PICK YOUR PLAY', v.round_index + 1, v.round_count);
  // Real, found-and-fixed crash: the ANSWERED screen calls this body
  // renderer with whatever view the just-graded submission returned --
  // when a wrong answer used the player's last real life, that view is
  // already the round's own "completed" shape (score/lives/ended only,
  // no prompt/options), same as _risk_it_client_view's own real
  // completed branch. Rendering v.options.map(...) against that shape
  // threw, which the submit handler's catch turned into a generic
  // "Couldn't load" error on literally every game-ending wrong answer.
  // Same defensive-on-ended pattern HIGHER_LOWER/ELIMINATION already use.
  if (v.completed || v.ended) {
    return roundLine + stadiumQuestionHtml('FINAL WHISTLE', 'Run over — no more questions this round.');
  }
  if (v.awaiting_tier) {
    var tierOrder = ['LOW', 'MEDIUM', 'HIGH'];
    return roundLine +
      stadiumQuestionHtml('CHOOSE YOUR CALL', 'How aggressive do you want to be? Commit before the question is revealed.') +
      '<div class="tier-select-grid" role="group" aria-label="Choose a risk tier">' + tierOrder.map(function (tier) {
        var meta = _TIER_SELECT_META[tier];
        var pts = v.tier_points[tier];
        return '<button class="tier-card tier-card--' + meta.cls + '" data-mechanic-risk-tier="' + esc(tier) + '">' +
          '<span class="tier-card-icon">' + icon(meta.icon) + '</span>' +
          '<span class="tier-card-play">' + (tier === 'LOW' ? 'SAFE PLAY' : tier === 'MEDIUM' ? 'BALANCED' : 'DEEP SHOT') + '</span>' +
          '<span class="tier-card-name">' + esc(tier) + ' RISK</span>' +
          '<span class="tier-card-points">' + pts + (pts === 1 ? ' pt' : ' pts') + '</span>' +
          '</button>';
      }).join('') + '</div>';
  }
  return roundLine + stadiumQuestionHtml((v.tier || 'LIVE') + ' RISK', v.prompt) +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-risk-answer',
    });
}

// WAGER_MODE: real 2-step round -- awaiting_wager=true shows only the
// real category name plus a real numeric wager input (reuses
// .learn-filter-input, same free-text-input pattern GUESS_THE_SEASON's
// own year-guess input already established); awaiting_wager=false shows
// the revealed real question via renderCandidateCardsHtml.
function renderWagerModeStatusHtml(v) {
  return stadiumRoundBar('READS SPORTS DESK', v.round_index + 1, v.round_count) +
    '<div class="wager-scorebug"><span>BALANCE</span><strong>' + v.balance + '</strong>' +
    (v.wager ? '<em>' + v.wager + ' AT RISK</em>' : '<em>SET YOUR STAKE</em>') + '</div>';
}
function renderWagerModeBody(v, s) {
  if (v.awaiting_wager) {
    return renderWagerModeStatusHtml(v) +
      '<div class="wager-ticket"><span class="wager-ticket-label">CATEGORY REVEAL</span>' +
      '<strong>' + esc(v.category) + '</strong><span>How confident are you?</span>' +
      '<input type="text" class="learn-filter-input wager-input" id="mechanic-wager-input" placeholder="Enter wager" ' +
      'inputmode="numeric" pattern="[0-9]*" autocomplete="off">' +
      '<button class="btn-primary wager-submit" data-mechanic-wager-submit>Lock In Wager</button></div>';
  }
  return renderWagerModeStatusHtml(v) +
    stadiumQuestionHtml(v.category + ' · ' + v.wager + ' POINT WAGER', v.prompt) +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-wager-answer',
    });
}

// LEADERBOARD_CLIMB: identical {choice: 'A'|'B'} submission shape to
// PAIRWISE_COMPARE/BEFORE_AFTER, so this reuses renderBinaryChoiceHtml
// AND the existing data-mechanic-duel-choice click handler verbatim --
// zero new app.js plumbing needed for this format.
function renderLeaderboardClimbBody(v, s) {
  return stadiumRoundBar('CLIMB THE BOARD', v.ladder_size - v.current_rank + 1, v.ladder_size) +
    '<div class="climb-scoreboard"><span>CURRENT RANK</span><strong>#' + v.current_rank + '</strong><em>OF ' + v.ladder_size + '</em></div>' +
    stadiumQuestionHtml('PICK THE HIGHER RANKED PLAYER', 'Who ranks higher on this leaderboard?') +
    renderBinaryChoiceHtml(
      { code: 'A', label: v.entity_a.label },
      { code: 'B', label: v.entity_b.label },
      { dataAttr: 'data-mechanic-duel-choice' },
    );
}

// BLIND_RESUME: the real resume (career games/pass yards/pass TDs/
// interceptions) is shown as a stat block -- reuses .chain-node (the same
// real component GUESS_THE_SEASON/MISSING_PIECE already use for a fact
// list, zero new CSS) -- then 4 real named candidates via
// renderCandidateCardsHtml, same as PICK_THE_IMPOSTOR/CAREER_PATH.
function renderBlindResumeBody(v, s) {
  var r = v.resume;
  // CFB retrofit pass: cfb_player_season_stats_real has no real "games
  // played" column at all -- the CFB variant's resume carries
  // r.completions instead of r.games (a real, populated column), never
  // mislabeled as games. Presence of r.completions (not the mode key) is
  // the source of truth here so this stays correct even if a future
  // variant is added.
  var firstStat = (r.completions != null) ? { value: r.completions, label: 'COMPLETIONS' } : { value: r.games, label: 'GAMES' };
  var stats = [firstStat, { value: r.pass_yards, label: 'PASS YARDS' }, { value: r.pass_td, label: 'PASS TD' }, { value: r.interceptions, label: 'INT' }];
  return stadiumRoundBar('CONFIDENTIAL · SCOUT FILE', v.round_index + 1, v.round_count) +
    '<div class="scout-dossier"><div class="scout-dossier-head"><span>PLAYER 00</span><strong>IDENTITY REDACTED</strong></div>' +
    '<div class="scout-stat-grid">' + stats.map(function (stat) {
      return '<div class="scout-stat"><strong>' + esc(String(stat.value)) + '</strong><span>' + stat.label + '</span></div>';
    }).join('') + '</div></div>' +
    stadiumQuestionHtml('MAKE THE IDENTIFICATION', 'Whose career passing resume is this?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-blind-resume-pick',
    });
}

// DOUBLE_OR_NOTHING: the real question is always visible (no blind
// tier-commit like RISK_IT) -- can_bank=true (only once real points are
// banked-eligible, i.e. after at least one correct answer) additionally
// shows a real Bank button above the question, offering the genuine
// bank-or-risk-it-on-this-harder-question choice RISK_IT/WAGER_MODE
// don't pose.
// Risk & Wager visual identity pass: the real points pot -- the whole
// hook of this format -- gets its own glowing .pot-display treatment
// instead of being a clause in a plain status line, and Bank becomes a
// distinct gold "lock it in" CTA (.btn-bank) rather than a generic chip
// button. Tier now shown via the shared shell header, not repeated here.
function renderDoubleOrNothingBody(v, s) {
  var roundLine = stadiumRoundBar('LIVE · THE POT', v.round_index + 1, v.round_count);
  // Real, found-and-fixed crash: DOUBLE_OR_NOTHING has no lives budget --
  // a SINGLE wrong answer (or a bank) ends the run, so the ANSWERED
  // screen's view is the round's own completed shape (points/ended/
  // banked only, no prompt/options) on literally the most common way a
  // run ends. Rendering v.options.map(...) against that shape threw,
  // which the submit handler's catch turned into a generic "Couldn't
  // load" error. Same defensive-on-ended pattern HIGHER_LOWER/
  // ELIMINATION already use.
  if (v.completed) {
    return roundLine + '<div class="pot-display"><span class="pot-jumbotron-label">READS STADIUM</span><span class="pot-value">' + v.points + '</span>' +
      '<span class="pot-label">' + (v.banked ? 'points banked' : 'points on the line') + '</span></div>' +
      stadiumQuestionHtml('FINAL', (v.banked ? 'Banked!' : 'Run over') + ' — no more questions this round.');
  }
  return roundLine +
    '<div class="pot-display"><span class="pot-jumbotron-label">READS STADIUM</span><span class="pot-value">' + v.points + '</span><span class="pot-label">points on the line</span></div>' +
    (v.can_bank
      ? '<div class="btn-row"><button class="btn-primary btn-bank" data-mechanic-don-bank>' + icon('lock') + ' Lock In ' + v.points + ' Points</button></div>'
      : '') +
    stadiumQuestionHtml('DOUBLE IT OR WALK AWAY', v.prompt) +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-don-answer',
    });
}

// KING_OF_THE_HILL: identical {choice: 'champion'|'challenger'} submission
// shape to PAIRWISE_COMPARE/LEADERBOARD_CLIMB, so this reuses
// renderBinaryChoiceHtml AND the same data-mechanic-duel-choice click
// handler verbatim -- zero new app.js plumbing needed for this format.
// Compare & Rank visual identity pass: a real champion badge (shield +
// consecutive real defenses) instead of a plain status-line sentence --
// reads at a glance like a real title defense streak.
function renderKingOfTheHillBody(v, s) {
  return '<div class="hill-arena"><span class="hill-crown">' + icon('shield') + '</span>' +
    '<span class="hill-kicker">KING OF THE HILL</span><strong>' + v.consecutive_defenses + '</strong>' +
    '<span>CONSECUTIVE DEFENSE' + (v.consecutive_defenses === 1 ? '' : 'S') + '</span></div>' +
    stadiumQuestionHtml('TITLE DEFENSE', 'Which team-season had more wins?') +
    renderBinaryChoiceHtml(
      { code: 'champion', label: v.champion.label },
      { code: 'challenger', label: v.challenger.label },
      { dataAttr: 'data-mechanic-duel-choice' },
    );
}

// FACT_OR_FAKE: identical {choice: 'TRUE'|'FAKE'} submission shape to
// PAIRWISE_COMPARE/KING_OF_THE_HILL, so this reuses renderBinaryChoiceHtml
// AND the same data-mechanic-duel-choice click handler verbatim -- zero
// new app.js plumbing needed for this format.
function renderFactOrFakeBody(v, s) {
  return stadiumRoundBar('BOOTH REVIEW', v.round_index + 1, v.round_count) +
    '<div class="review-monitor"><span class="review-monitor-label">RULING ON THE FIELD</span>' +
    '<div class="quiz-question stadium-question">' + esc(v.statement) + '</div><span class="review-scanline"></span></div>' +
    renderBinaryChoiceHtml(
      { code: 'TRUE', label: 'TRUE' },
      { code: 'FAKE', label: 'FAKE' },
      { dataAttr: 'data-mechanic-duel-choice' },
    );
}

// Compare & Rank visual identity pass: a real vertical rank ladder
// (one row per real rank option) instead of a generic 2-column card
// grid -- reinforces "this is a real leaderboard position", not just an
// arbitrary multiple-choice list. Same data-mechanic-guess-the-ranking-
// pick="index" attribute renderCandidateCardsHtml used, so app.js's
// click handler needs zero changes.
function renderGuessTheRankingBody(v, s) {
  return stadiumRoundBar('NATIONAL LEADERBOARD', v.round_index + 1, v.round_count) +
    '<div class="ranking-feature"><span>WHERE DOES HE RANK?</span><strong>' + esc(v.label) + '</strong></div>' +
    '<div class="rank-ladder" role="group" aria-label="Pick a real rank">' + v.options.map(function (it, i) {
      return '<button class="rank-ladder-row" data-mechanic-guess-the-ranking-pick="' + i + '">' +
        '<span class="rank-ladder-place">' + (i + 1) + '</span><span class="rank-ladder-badge">' + esc(it.label) + '</span>' +
        '<span class="rank-ladder-label">LOCK THIS RANK</span></button>';
    }).join('') + '</div>';
}

// Compare & Rank visual identity pass: the real target number gets its
// own prominent badge (same glowing-number language as DOUBLE_OR_
// NOTHING's points pot) instead of living only inside the question
// sentence -- candidate cards below are unchanged.
function renderStatTargetBody(v, s) {
  return stadiumRoundBar('TARGET CHALLENGE', v.round_index + 1, v.round_count) +
    '<div class="target-lock"><span class="target-ring target-ring-one"></span><span class="target-ring target-ring-two"></span>' +
    '<div class="stat-target-badge"><span class="stat-target-value">' + v.target + '</span>' +
    '<span class="stat-target-label">RUSHING YARDS</span></div></div>' +
    stadiumQuestionHtml('CLOSEST WINS', 'Which player’s season total came closest?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-stat-target-pick',
    });
}

// REVERSE_TRIVIA: reuses renderCandidateCardsHtml, same as
// PICK_THE_IMPOSTOR/STAT_TARGET -- zero new CSS.
function renderReverseTriviaBody(v, s) {
  return stadiumRoundBar('FACT CHECK', v.round_index + 1, v.round_count) +
    '<div class="verify-subject"><span>PLAYER FILE</span><strong>' + esc(v.subject_name) + '</strong><em>ONE STATEMENT CHECKS OUT</em></div>' +
    stadiumQuestionHtml('FIND THE FACT', 'Which real statement is actually true?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-reverse-trivia-pick',
    });
}

// THREE_STRIKES: the real question is always shown directly (no blind
// tier-commit like RISK_IT) -- reuses renderCandidateCardsHtml.
// Risk & Wager visual identity pass: score/strikes/tier now live in the
// shared shell header, so this only needs the real round-progress line
// and question.
function renderThreeStrikesBody(v, s) {
  var strikes = Number(v.strikes || 0), strikeLamps = '';
  for (var lamp = 0; lamp < 3; lamp++) strikeLamps += '<span class="strike-lamp' + (lamp < strikes ? ' is-hit' : '') + '">X</span>';
  var roundLine = stadiumRoundBar('LIVE · STAY ALIVE', v.round_index + 1, v.round_count) +
    '<div class="strike-scoreboard"><div><span>STREAK</span><strong>' + (v.streak || 0) + '</strong></div>' +
    '<div class="strike-lamps" aria-label="' + strikes + ' of 3 strikes">' + strikeLamps + '</div></div>';
  // Real, found-and-fixed crash: same shape as RISK_IT above -- the
  // ANSWERED screen after a strike-costing wrong answer that used the
  // last real strike gets the round's own completed shape (score/streak/
  // strikes/ended only, no prompt/options). Rendering v.options.map(...)
  // against that shape threw, which the submit handler's catch turned
  // into a generic "Couldn't load" error.
  if (v.completed || v.ended) {
    return roundLine + stadiumQuestionHtml('FINAL WHISTLE', 'Run over — no more questions this round.');
  }
  return roundLine + stadiumQuestionHtml('KEEP THE DRIVE ALIVE', v.prompt) +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-three-strikes-answer',
    });
}

// MYSTERY_ROSTER: real clues revealed so far (reuses .chain-node, the
// same real component GUESS_THE_SEASON's own clue list already uses)
// plus a real Reveal button (only shown while clues remain) and the 4
// real candidate cards for guessing at any point.
function renderMysteryRosterBody(v, s) {
  var revealBtn = v.clues_revealed < v.max_clues
    ? '<div class="mystery-reveal-row" role="group" aria-label="Reveal another clue"><button class="btn-secondary mystery-reveal-btn" data-mechanic-mystery-reveal>Open Next File <span>' + (v.max_clues - v.clues_revealed) + ' left</span></button></div>'
    : '';
  return stadiumRoundBar('MYSTERY WAR ROOM · ' + v.score + ' PTS', v.round_index + 1, v.round_count) +
    '<div class="mystery-file-stack">' + v.clues.map(function (c, i) {
      return '<div class="mystery-file"><span>CLUE ' + (i + 1) + '</span><strong>' + esc(c) + '</strong></div>';
    }).join('') + '</div>' +
    revealBtn +
    stadiumQuestionHtml('MAKE YOUR CALL', 'Which team-season is hiding in these files?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-mystery-guess',
    });
}

// DRAFT_PICK_LADDER: reuses renderCandidateCardsHtml, same as
// PICK_THE_IMPOSTOR/THREE_STRIKES -- zero new CSS.
function renderDraftPickLadderBody(v, s) {
  return stadiumRoundBar('DRAFT ARCHIVE', v.round_index + 1, v.round_count) +
    stadiumModeIntroHtml('ON THE CLOCK', v.player_name, v.season + ' NFL DRAFT') +
    stadiumQuestionHtml('NAME THE PICK', 'What overall pick was ' + v.player_name + ' drafted with?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-draft-pick-ladder-pick',
    });
}

// CATEGORY_ROULETTE: reuses renderCandidateCardsHtml, same as
// PICK_THE_IMPOSTOR/DRAFT_PICK_LADDER -- zero new CSS.
function renderCategoryRouletteBody(v, s) {
  return stadiumRoundBar('THE NEXT CATEGORY IS IN', v.round_index + 1, v.round_count) +
    '<div class="roulette-reveal"><span>CATEGORY DRAWN</span><strong>' + esc(v.category) + '</strong><i aria-hidden="true"></i></div>' +
    stadiumQuestionHtml('YOUR QUESTION', v.prompt) +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-category-roulette-pick',
    });
}

// Story & Path visual identity pass: the 3 real named players are shown
// as a genuinely LINKED trio (a connector between each name) instead of
// 3 stacked plain rows shared with MYSTERY_ROSTER's clue list --
// visually reinforces this format's own name/premise -- then 4 real
// candidate statements via renderCandidateCardsHtml, same as
// PICK_THE_IMPOSTOR/MISSING_PIECE.
function renderCommonLinkBody(v, s) {
  var trioHtml = '<div class="broadcast-link-map" role="group" aria-label="The 3 linked players">' +
    v.names.map(function (name, i) {
      var node = '<div class="broadcast-link-node"><span>0' + (i + 1) + '</span><strong>' + esc(name) + '</strong></div>';
      return i < v.names.length - 1 ? node + '<div class="broadcast-link-line" aria-hidden="true"><i></i></div>' : node;
    }).join('') + '</div>';
  return stadiumRoundBar('CONNECTION DESK', v.round_index + 1, v.round_count) +
    trioHtml +
    stadiumQuestionHtml('FIND THE LINK', 'What connects these three players?') +
    renderCandidateCardsHtml(v.options.map(function (it) { return it.label; }), {
      dataAttr: 'data-mechanic-common-link-pick',
    });
}

// CHOOSE_YOUR_PATH: a small, fixed, pre-validated branch tree -- the root
// shows real choices; each leaf renders exactly like a normal multiple-
// choice question (same submit contract underneath, different node type).
function renderBranchStateBody(v, s) {
  if (v.choices) {
    return '<div class="path-board"><span>THE DECISION</span><strong>CHOOSE YOUR ROUTE</strong><div class="path-lines" aria-hidden="true"><i></i><i></i><i></i></div></div>' +
      stadiumQuestionHtml('AT THE FORK', v.prompt) +
      '<div class="path-options" role="group" aria-label="Choose a path">' + v.choices.map(function (c, i) {
        return '<button class="chip-toggle" data-mechanic-branch-choice="' + esc(c.choice_id) + '"><span>PATH ' + String.fromCharCode(65 + i) + '</span><strong>' + esc(c.label) + '</strong><b aria-hidden="true">&rarr;</b></button>';
      }).join('') + '</div>';
  }
  return '<div class="path-board path-board--question"><span>ROUTE SELECTED</span><strong>MAKE THE PLAY</strong></div>' +
    stadiumQuestionHtml('NEXT DECISION', v.prompt) +
    '<div class="quiz-options">' + (v.options || []).map(function (opt, i) {
      return '<button class="quiz-option" data-mechanic-branch-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') + '</div>';
}
// Reusable Game Format System pass: the real BRACKET_TREE renderer -- a
// real 8-entry single-elimination bracket, shown round by round (never a
// full zoomed tree on one screen -- mobile rule from the format spec).
// Generic over whatever real COMPARISON_BRACKET variant produced
// `view.rounds` (NFL/CFB team-season win totals today); every matchup
// still un-picked is tappable (data-mechanic-comparison-match/-side),
// gated to the FIRST round with any unpicked matchup so the player works
// through the bracket in real order without needing every round visible
// and interactive at once on a small screen.
function renderBracketTreeBody(v, s) {
  var rounds = v.rounds || [];
  var disabled = s.screen && s.screen !== ENGINE_GAME_SCREEN.QUESTION_READY;
  var firstIncompleteRound = rounds.findIndex(function (r) {
    return r.matchups.some(function (m) { return m.your_pick === undefined; });
  });
  return rounds.map(function (r, ri) {
    var isActive = ri === firstIncompleteRound;
    var matchupsHtml = r.matchups.map(function (m) {
      if (m.your_pick !== undefined) {
        return '<div class="bracket-matchup bracket-matchup-decided">' +
          '<span class="' + (m.entrant_a === m.real_winner ? 'feedback-good' : (m.your_pick === m.entrant_a ? 'feedback-bad' : '')) + '">' + esc(m.entrant_a) + '</span>' +
          '<span class="bracket-vs">vs</span>' +
          '<span class="' + (m.entrant_b === m.real_winner ? 'feedback-good' : (m.your_pick === m.entrant_b ? 'feedback-bad' : '')) + '">' + esc(m.entrant_b) + '</span>' +
          '<div class="status-line">Real winner: ' + esc(m.real_winner) + (m.correct ? ' -- you got it!' : '') + '</div></div>';
      }
      var tappable = isActive && !disabled;
      return '<div class="bracket-matchup">' +
        '<button class="quiz-option" ' + (tappable ? 'data-mechanic-comparison-match="' + esc(m.match_id) + '" data-mechanic-comparison-side="a"' : 'disabled') + '>' + esc(m.entrant_a) + '</button>' +
        '<span class="bracket-vs">vs</span>' +
        '<button class="quiz-option" ' + (tappable ? 'data-mechanic-comparison-match="' + esc(m.match_id) + '" data-mechanic-comparison-side="b"' : 'disabled') + '>' + esc(m.entrant_b) + '</button>' +
        '</div>';
    }).join('');
    return '<div class="bracket-round' + (isActive ? ' bracket-round-active' : '') + '">' +
      '<div class="encyc-subcategory-label">' + esc(r.round_label) + '</div>' + matchupsHtml + '</div>';
  }).join('');
}
function renderMechanicPilotScreen() {
  var s = state.mechanicPilot;
  var cfg = mechanicPilotModeConfig(s ? s.modeKey : mechanicPilotCurrentModeKey);
  var panelClass = mechanicPilotPanelClass(cfg, s);
  if (!cfg.flagOn()) return renderHome();
  if (!s) {
    return '<div class="' + panelClass + '"><h2 class="panel-title">' + esc(cfg.title) + '</h2>' +
      '<p class="mode-desc">' + esc(cfg.desc) + '</p>' +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-start>Start</button></div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.LOADING) {
    return '<div class="' + panelClass + '">' + mechanicPilotToolbarHtml(cfg, s) +
      '<div class="inline-loading" aria-live="polite"><span class="loading-spinner loading-spinner-sm"></span>Finding your next round&hellip;</div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.ERROR) {
    return '<div class="' + panelClass + '">' + mechanicPilotToolbarHtml(cfg, s) +
      '<p class="mode-desc" aria-live="assertive">' + esc(s.error) + '</p>' +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-retry>Try Again</button>' +
      '<button class="btn-secondary" data-mechanic-fallback>' + esc(cfg.fallbackLabel) + '</button></div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.COMPLETE) {
    // Creator "one approval, fully live" pass: a shared completion banner
    // (reusing styles.css's existing .grid-immaculate-banner/confetti-burst
    // treatment, already used elsewhere for a round-complete celebration)
    // applied ONCE here at the shared mechanicPilot shell level, so every
    // current and future format that routes through this shell gets a real
    // production-polish completion moment automatically -- no per-format
    // design pass needed.
    return '<div class="' + panelClass + '">' + mechanicPilotToolbarHtml(cfg, s) +
      '<div class="mechanic-complete-banner">' + brandWatermarkHtml() + '<div class="mechanic-complete-confetti"></div>' +
      icon('trophy') + ' <h2 class="complete-banner-text">Round Complete!</h2></div>' +
      renderMechanicPilotCompleteSummary(cfg, s) +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-start>Play Again</button>' +
      '<button class="btn-secondary" data-share="' + esc(s.modeKey) + '">' + icon('share') + ' Share</button>' +
      '<button class="btn-secondary" data-go="home">Home</button></div>' +
      postGameNextStepsHtml(null) + '</div>';
  }
  var answered = s.screen === ENGINE_GAME_SCREEN.ANSWERED;
  var submitting = s.screen === ENGINE_GAME_SCREEN.SUBMITTING;
  if (submitting) {
    return '<div class="' + panelClass + '">' + mechanicPilotToolbarHtml(cfg, s) + renderMechanicPilotBody(cfg, s) +
      '<div class="quiz-progress" aria-live="polite">Checking your answer&hellip;</div></div>';
  }
  // Real, found-and-fixed crash (systemic across most mechanicPilot
  // kinds, not just one format): the answer that just got graded can
  // ITSELF be the one that ends the round (last strike/life spent, one
  // wrong answer in DOUBLE_OR_NOTHING, or simply the final scheduled
  // round) -- every real *_client_view's own "completed" branch server-
  // side drops the question/options fields entirely at that point
  // (mechanic_engine.py, e.g. _fact_or_fake_client_view/
  // _risk_it_client_view). Calling renderMechanicPilotBody() against
  // that shape unconditionally threw (v.options.map on undefined, etc.),
  // and the submit handler's own catch turned that exception into a
  // generic "Couldn't load that -- please try again" error on what was
  // actually a normal, successful (if game-ending) answer. Skip the body
  // entirely once the round is already over -- renderMechanicPilotFeedback
  // (which reads s.result, always populated regardless of view shape)
  // still shows the real correct/wrong outcome, and Continue still
  // advances to the real completion screen exactly as before.
  var roundOver = s.view && (s.view.completed || s.view.ended || s.view.sequence_complete);
  return '<div class="' + panelClass + '">' + mechanicPilotToolbarHtml(cfg, s) +
    (answered && roundOver ? '' : renderMechanicPilotBody(cfg, s)) +
    (answered ? renderMechanicPilotFeedback(cfg, s) +
      '<button class="btn-primary" data-mechanic-next>Continue</button>' : '') +
    '</div>';
}
