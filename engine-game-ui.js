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
function enginePilotUserFacingError(err) {
  var code = err && err.code;
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
    desc: "A real Super Bowl champion's clues, revealed one at a time. Guess the team and season.",
    fallbackLabel: 'Play NFL Trivia Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
  },
  eraGauntlet: {
    apiMode: 'era_gauntlet_guess',
    icon: 'timeline',
    hash: '#eragauntletpilot',
    flagOn: function () { return ENABLE_ENGINE_ERA_GAUNTLET_PILOT_V01; },
    title: 'Era Gauntlet',
    desc: "Progress through real NFL history -- one real Super Bowl champion from each represented decade, oldest era first.",
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
    desc: "Pick a real NFL franchise and play through its real Super Bowl-winning offenses in chronological order, by college and position.",
    fallbackLabel: 'Play NFL Trivia Instead',
    fallback: function () { state.enginePilot = null; state.screen = 'quiz'; startQuizRound('Super Bowl History', '', 10); },
    sequential: true,
    needsFilterValue: true,
    filterParamName: 'franchise',
    // Real, verified list (sb_champion_offense_college.fetch_ordered_
    // candidates() called directly for each, this pass) -- every one of
    // these has 1+ real surviving stage after the standard duplicate-
    // question guard. Never invented; a franchise not on this list simply
    // isn't offered as a starting choice.
    franchiseChoices: [
      { value: 'cowboys', label: 'Dallas Cowboys' },
      { value: 'packers', label: 'Green Bay Packers' },
      { value: 'patriots', label: 'New England Patriots' },
      { value: 'steelers', label: 'Pittsburgh Steelers' },
      { value: '49ers', label: 'San Francisco 49ers' },
      { value: 'giants', label: 'New York Giants' },
      { value: 'chiefs', label: 'Kansas City Chiefs' },
      { value: 'broncos', label: 'Denver Broncos' },
      { value: 'raiders', label: 'Raiders (Oakland/LA)' },
      { value: 'dolphins', label: 'Miami Dolphins' },
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
var ENGINE_PILOT_FETCH_TIMEOUT_MS = 10000;
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
  };
  state.enginePilotPendingFranchise = null;
  state.screen = 'enginePilot';
  renderAll();
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
          s.screen = ENGINE_GAME_SCREEN.COMPLETE;
          renderAll();
          return;
        }
        s.screen = ENGINE_GAME_SCREEN.ERROR;
        s.error = enginePilotUserFacingError(game.error);
        renderAll();
        return;
      }
      s.current = game;
      s.pickedOption = null;
      s.answerResult = null;
      s.cluesRevealedCount = 1; // Three Clues / Era Gauntlet: each new question starts back at Clue 1 of 3
      s.screen = ENGINE_GAME_SCREEN.QUESTION_READY;
      renderAll();
    })
    .catch(function (err) {
      if (state.enginePilot !== s) return;
      s.screen = ENGINE_GAME_SCREEN.ERROR;
      s.error = enginePilotUserFacingError(err);
      renderAll();
    });
}
function pickEnginePilotAnswer(optionIndex) {
  var s = state.enginePilot;
  if (!s || s.screen !== ENGINE_GAME_SCREEN.QUESTION_READY || s.pickedOption !== null) return;
  var game = s.current;
  var chosenLabel = game.payload.options[optionIndex];
  s.pickedOption = optionIndex;
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
    playSound(result.correct ? 'correct' : 'wrong');
    s.screen = ENGINE_GAME_SCREEN.ANSWERED;
    renderAll();
  }).catch(function (err) {
    if (state.enginePilot !== s) return;
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
  if (s.roundIndex + 1 >= s.roundSize) { s.screen = ENGINE_GAME_SCREEN.COMPLETE; renderAll(); return; }
  s.roundIndex++;
  loadNextEnginePilotQuestion();
}
/* v1.8, Part E/F: POSITION_LINEUP visual template -- a real football
   position board (5 skill positions, then 5 grouped OL) instead of a plain
   question sentence. Purely presentational: the answer/options underneath
   are rendered exactly the same way regardless of visual_template (Part D's
   mechanic/template separation -- this function never touches answer
   validation). See tools/director_v02/visual_templates.py and
   tools/quiz_export/adapters/lineup.py for why OL is one grouped row of 5,
   not 5 individually-labeled slots. */
// Era Gauntlet's real timeline -- the exact same 7 real, fixed decade
// boundaries the adapter itself uses (sb_champion_offense_college.py's
// _ERAS: 1960s-2020s), not an invented visual. Section 7's own progress-
// should-match-the-mechanic instruction, and Section 10's timeline symbol.
var ERA_GAUNTLET_ERA_LABELS = ['1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'];
function renderEraGauntletTimelineHtml(stageIndex) {
  var markers = ERA_GAUNTLET_ERA_LABELS.map(function (label, i) {
    var cls = 'era-gauntlet-marker';
    if (i < stageIndex) cls += ' done';
    else if (i === stageIndex) cls += ' current';
    return '<div class="' + cls + '"><span class="era-gauntlet-dot"></span><span class="era-gauntlet-label">' + label + '</span></div>';
  }).join('<div class="era-gauntlet-connector"></div>');
  return '<div class="era-gauntlet-timeline" role="img" aria-label="Era ' + (stageIndex + 1) + ' of 7: ' +
    esc(ERA_GAUNTLET_ERA_LABELS[stageIndex] || '') + '">' + markers + '</div>';
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
function renderPositionLineupCollegeBoard(payload) {
  var positions = (payload && payload.positions) || [];
  var season = payload && payload.season;
  function cell(p) {
    return '<div class="lineup-cell"><div class="lineup-pos">' + esc(p.position) + '</div>' +
      '<div class="lineup-name">' + esc(p.college) + '</div></div>';
  }
  return '<div class="lineup-board">' +
    '<div class="lineup-board-eyebrow">' + icon('users') + ' Starting Offense (by college, names hidden)' +
    (season ? ' &middot; ' + esc(String(season)) : '') + '</div>' +
    '<div class="lineup-row-label">Skill Positions</div>' +
    '<div class="lineup-row">' + positions.map(cell).join('') + '</div>' +
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
var THREE_CLUES_PROMPT_RE = /^Exactly 3 real clues, 1 champion: (.+)\. Guess the Super Bowl-winning team AND season\.$/;
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
    return '<div class="panel">' +
      '<h2 class="panel-title">' + esc(cfg.title) + '</h2>' +
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
    return '<div class="panel">' + enginePilotToolbarHtml(cfg) + '<p class="mode-desc" aria-live="polite">Finding your next question&hellip;</p></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.ERROR) {
    // Part 11/43: s.error is always shell-owned, polished copy by this
    // point (see enginePilotUserFacingError) -- never a raw server string,
    // never an HTTP status code, never an internal error `code` like
    // GENERATION_BUSY shown as-is. aria-live="assertive" here (vs
    // "polite" elsewhere) since an error is worth interrupting for.
    return '<div class="panel">' + enginePilotToolbarHtml(cfg) +
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
          ' Super Bowl-winning stage' + (stageCount === 1 ? '' : 's') + ' -- ' + s.correctCount + ' / ' + stageCount + ' correct.';
      } else if (s.modeKey === 'eraGauntlet') {
        completeTitle = 'Gauntlet Complete';
        completeStat = 'You reached the end of the gauntlet -- ' + stageCount + ' real historical eras, ' +
          s.correctCount + ' / ' + stageCount + ' correct.';
      }
    }
    return '<div class="panel">' + enginePilotToolbarHtml(cfg) +
      '<h2 class="panel-title">' + esc(completeTitle) + '</h2>' +
      '<p class="mode-desc">' + completeStat + '</p>' +
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
  var panelCls = 'panel' + (s.modeKey === 'cfbUpset' ? ' upset-panel' : '');
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
    progressHtml = renderEraGauntletTimelineHtml(s.stageIndex);
  } else if (cfg.sequential && s.modeKey === 'franchiseMarathon') {
    franchiseLabel = (cfg.franchiseChoices.find(function (f) { return f.value === s.filterValue; }) || {}).label || s.filterValue;
    progressHtml = quizProgressRowHtml('Stage ' + (s.stageIndex + 1), null, null);
  } else {
    progressHtml = quizProgressRowHtml('Question ' + (s.roundIndex + 1) + ' of ' + s.roundSize, s.roundIndex, s.roundSize);
  }
  var headerOpts = { score: s.correctCount + ' correct', difficulty: game.difficulty };
  if (franchiseLabel) headerOpts.badge = franchiseLabel;
  return '<div class="' + panelCls + '">' + enginePilotToolbarHtml(cfg, headerOpts) +
    progressHtml +
    renderEnginePilotPromptHtml(game, s) +
    optionsHtml +
    // Part 9: real, visible feedback that a submission is in flight (not
    // just silently-disabled buttons) -- aria-live so it's announced.
    (submitting ? '<div class="quiz-progress" aria-live="polite">Checking your answer&hellip;</div>' : '') +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (s.answerResult.correct ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (s.answerResult.notes ? ' ' + esc(s.answerResult.notes) : '') + '</div>' +
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
};
var mechanicPilotCurrentModeKey = 'matching';
function mechanicPilotModeConfig(modeKey) {
  return ENGINE_MECHANIC_MODES[modeKey] || ENGINE_MECHANIC_MODES.matching;
}
function startMechanicPilotRound(modeKey) {
  if (modeKey) mechanicPilotCurrentModeKey = modeKey;
  state.mechanicPilot = { modeKey: mechanicPilotCurrentModeKey, screen: ENGINE_GAME_SCREEN.LOADING, roundId: null, view: null, result: null, error: null, matchSelection: {} };
  state.screen = 'mechanicPilot';
  renderAll();
  loadMechanicPilotRound();
}
function mechanicPilotFallback() {
  var modeKey = (state.mechanicPilot && state.mechanicPilot.modeKey) || mechanicPilotCurrentModeKey;
  mechanicPilotModeConfig(modeKey).fallback();
}
function loadMechanicPilotRound() {
  var s = state.mechanicPilot;
  if (!s) return;
  var cfg = mechanicPilotModeConfig(s.modeKey);
  s.screen = ENGINE_GAME_SCREEN.LOADING; s.error = null; s.result = null; s.matchSelection = {};
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
      s.screen = ENGINE_GAME_SCREEN.ERROR; s.error = enginePilotUserFacingError(err);
      renderAll();
    });
}
function submitMechanicPilotAction(submission) {
  var s = state.mechanicPilot;
  if (!s || !s.roundId) return;
  s.screen = ENGINE_GAME_SCREEN.SUBMITTING;
  renderAll();
  enginePilotFetchJson('/v1/public/mechanics/round/' + encodeURIComponent(s.roundId) + '/submit', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ submission: submission }),
  }).then(function (data) {
    if (state.mechanicPilot !== s) return;
    s.result = data.result; s.view = data.view; s.matchSelection = {};
    var wasCorrect = data.result && (data.result.correct === true || data.result.all_correct === true || data.result.exact_match === true);
    playSound(wasCorrect ? 'correct' : 'wrong');
    s.screen = ENGINE_GAME_SCREEN.ANSWERED;
    renderAll();
  }).catch(function (err) {
    if (state.mechanicPilot !== s) return;
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
    s.screen = ENGINE_GAME_SCREEN.COMPLETE;
    renderAll();
    return;
  }
  s.screen = ENGINE_GAME_SCREEN.QUESTION_READY; s.result = null;
  renderAll();
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
  return '';
}
/* Section 6/7/21 fix: same persistent-title fix as enginePilotToolbarHtml
   above, for the Mechanic Pilot shell. */
function mechanicPilotToolbarHtml(cfg) {
  return (cfg ? '<div class="quiz-progress">' + esc(cfg.title) + '</div>' : '') +
    '<div class="mode-toolbar"><button class="btn-tiny" data-mechanic-exit>' + icon('close') + ' Exit to Home</button></div>';
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
  } else if (cfg.kind === 'higher_lower') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = esc(r.revealed_next_label) + ' was ' + esc(r.actual_direction) + '.';
  } else if (cfg.kind === 'elimination') {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = r.actual_membership ? 'That one was real.' : 'That one wasn’t real.';
  } else {
    headline = wasCorrect ? 'Correct!' : 'Not quite.';
    detail = '';
  }
  // Same real .quiz-feedback/.feedback-good/.feedback-bad shell every
  // other mode in app.js already uses (e.g. the Engine Pilot render just
  // above this file's own line ~474) -- no parallel feedback style.
  return '<div class="quiz-feedback" aria-live="polite">' +
    '<span class="' + (wasCorrect ? 'feedback-good' : 'feedback-bad') + '">' +
    (wasCorrect ? icon('check') : icon('xMark')) + ' ' + esc(headline) + '</span>' +
    (detail ? ' ' + esc(detail) : '') + '</div>';
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
    var labelFor = function (id) { var it = v.items_shuffled.filter(function (x) { return x.item_id === id; })[0]; return it ? it.label : id; };
    return '<div class="quiz-question">' + esc(v.prompt) + '</div>' +
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
    return '<div class="status-line">Streak: ' + (v.streak || 0) + '</div>' +
      '<div class="hl-compare"><span>' + esc(v.current_item.label) + '</span><span class="hl-value">' + esc(String(v.current_item.value)) + '</span></div>' +
      '<div class="hl-compare"><span>' + (v.next_item ? esc(v.next_item.label) : '(no more real items)') + '</span>' +
      '<span class="' + (v.next_item && v.next_item.value !== undefined ? 'hl-value' : 'hl-hidden') + '">' + (v.next_item && v.next_item.value !== undefined ? esc(String(v.next_item.value)) : '?') + '</span></div>' +
      // data-mechanic-hl-guess, deliberately NOT data-hl-guess -- that
      // attribute already belongs to the legacy, client-side higherLower
      // mode's own buttons (app.js), which fire a completely different
      // handler (submitHigherLowerGuess). Reusing it here would silently
      // call the wrong function whenever this screen is showing.
      (v.ended ? '' : '<div class="btn-row"><button class="btn-primary" data-mechanic-hl-guess="higher">Higher</button><button class="btn-primary" data-mechanic-hl-guess="lower">Lower</button></div>');
  }
  if (cfg.kind === 'elimination') {
    return '<div class="status-line">Survived: ' + (v.survived_count || 0) + '</div>' +
      '<div class="quiz-question">' + esc(v.current_prompt || '(no more real items)') + '</div>' +
      (v.ended ? '' : '<div class="btn-row"><button class="btn-primary" data-elim-guess="true">True</button><button class="btn-primary" data-elim-guess="false">False</button></div>');
  }
  return '';
}
function renderMechanicPilotScreen() {
  var s = state.mechanicPilot;
  var cfg = mechanicPilotModeConfig(s ? s.modeKey : mechanicPilotCurrentModeKey);
  if (!cfg.flagOn()) return renderHome();
  if (!s) {
    return '<div class="panel"><h2 class="panel-title">' + esc(cfg.title) + '</h2>' +
      '<p class="mode-desc">' + esc(cfg.desc) + '</p>' +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-start>Start</button></div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.LOADING) {
    return '<div class="panel">' + mechanicPilotToolbarHtml(cfg) + '<p class="mode-desc" aria-live="polite">Finding your next round&hellip;</p></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.ERROR) {
    return '<div class="panel">' + mechanicPilotToolbarHtml(cfg) +
      '<p class="mode-desc" aria-live="assertive">' + esc(s.error) + '</p>' +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-retry>Try Again</button>' +
      '<button class="btn-secondary" data-mechanic-fallback>' + esc(cfg.fallbackLabel) + '</button></div></div>';
  }
  if (s.screen === ENGINE_GAME_SCREEN.COMPLETE) {
    return '<div class="panel">' + mechanicPilotToolbarHtml(cfg) + '<h2 class="panel-title">Round Complete</h2>' +
      renderMechanicPilotCompleteSummary(cfg, s) +
      '<div class="btn-row"><button class="btn-primary" data-mechanic-start>Play Again</button>' +
      '<button class="btn-secondary" data-go="home">Home</button></div>' +
      postGameNextStepsHtml(null) + '</div>';
  }
  var answered = s.screen === ENGINE_GAME_SCREEN.ANSWERED;
  var submitting = s.screen === ENGINE_GAME_SCREEN.SUBMITTING;
  if (submitting) {
    return '<div class="panel">' + mechanicPilotToolbarHtml(cfg) + renderMechanicPilotBody(cfg, s) +
      '<div class="quiz-progress" aria-live="polite">Checking your answer&hellip;</div></div>';
  }
  return '<div class="panel">' + mechanicPilotToolbarHtml(cfg) + renderMechanicPilotBody(cfg, s) +
    (answered ? renderMechanicPilotFeedback(cfg, s) +
      '<button class="btn-primary" data-mechanic-next>Continue</button>' : '') +
    '</div>';
}
