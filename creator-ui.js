// Reads Engine Game Creator (v1.8, Part B/C/G/H/L/M/N) -- admin-only,
// in-app UI for describing a new game in plain English and seeing exactly
// what the real Director/Factory architecture does with it.
//
// Reached ONLY via a hidden route (#creator), never linked from the main
// nav/home grid -- same established pattern as the existing owner-only
// #stats page (see app.js, "mode-popularity stats (owner-only)"). Unlike
// #stats, this surface calls admin-gated Gateway routes that cost real
// compute and touch the Engine database, so it additionally requires the
// real admin token (gateway/auth.py's READS_ENGINE_ADMIN_TOKEN) before any
// Creator route is called -- entered by the operator into a plain text
// field each session, kept only in sessionStorage (cleared when the tab
// closes) and this file's own state, NEVER hardcoded in source, NEVER
// bundled into a build, NEVER sent anywhere except this Gateway's own
// Authorization header (Part L). A wrong or missing token simply gets a
// 401 from the Gateway -- there is no separate client-side auth check to
// bypass; the server is the only real gate.
//
// Every Creator action funnels through /v1/creator/* (gateway/app.py),
// which itself only ever calls tools/director_v02/feasibility.py and the
// SAME generation/QA/package pipeline every other Gateway caller already
// uses (gateway/services/creator.py's own module docstring) -- this file
// contains NO game logic, NO SQL, NO capability list of its own. It is a
// thin client over already-certified server behavior, exactly like
// engine-game-ui.js / six-degrees-ui.js are for player-facing modes.
//
// Part G ("preview using the SAME renderer players see"): the question
// preview below reuses renderEnginePilotPromptHtml/renderPositionLineupBoard
// from engine-game-ui.js verbatim, via a small shape-adapter
// (creatorQuestionAsPublicPayload) -- never a second, parallel renderer that
// could silently drift from what a real player actually sees.

var CREATOR_TOKEN_STORAGE_KEY = 'readsCreatorAdminToken';
var CREATOR_SCREEN = {
  AUTH: 'auth',
  HOME: 'home',
  CHECKING: 'checking',
  RESULT: 'result',
  GENERATING: 'generating',
  PREVIEW: 'preview',
  QUEUE: 'queue',
  CAPABILITIES: 'capabilities',
  ERROR: 'error',
};
var CREATOR_ERROR_COPY = {
  UNAUTHORIZED: 'That admin token was rejected by the Gateway.',
  RATE_LIMITED: 'Too many requests -- wait a moment and try again.',
  CLIENT_TIMEOUT: 'That took too long to load -- check the Gateway is running and try again.',
};
function creatorUserFacingError(err) {
  var code = err && err.code;
  return (code && CREATOR_ERROR_COPY[code]) || (err && err.message) || 'Something went wrong.';
}

function creatorToken() {
  try { return sessionStorage.getItem(CREATOR_TOKEN_STORAGE_KEY) || ''; }
  catch (e) { return ''; }
}
function creatorSetToken(token) {
  try { sessionStorage.setItem(CREATOR_TOKEN_STORAGE_KEY, token); } catch (e) { /* private browsing, etc -- non-fatal */ }
}
function creatorClearToken() {
  try { sessionStorage.removeItem(CREATOR_TOKEN_STORAGE_KEY); } catch (e) { /* non-fatal */ }
}

var CREATOR_FETCH_TIMEOUT_MS = 15000; // generation is slower than a public fetch -- real Director pipeline work.
function creatorFetchJson(path, options) {
  var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
  var timeoutId = controller ? setTimeout(function () { controller.abort(); }, CREATOR_FETCH_TIMEOUT_MS) : null;
  var opts = options ? Object.assign({}, options) : {};
  opts.headers = Object.assign({}, opts.headers, { 'Authorization': 'Bearer ' + creatorToken() });
  if (controller) opts.signal = controller.signal;
  return fetch(ENGINE_GATEWAY_BASE_URL + path, opts).then(function (res) {
    if (timeoutId) clearTimeout(timeoutId);
    if (!res.ok) {
      return res.json().catch(function () { return {}; }).then(function (body) {
        var err = new Error((body.error && body.error.message) || ('HTTP ' + res.status));
        err.code = body.error && body.error.code;
        throw err;
      });
    }
    return res.json();
  }).catch(function (err) {
    if (timeoutId) clearTimeout(timeoutId);
    if (err && err.name === 'AbortError') {
      var timeoutErr = new Error('Client-side fetch timeout.');
      timeoutErr.code = 'CLIENT_TIMEOUT';
      throw timeoutErr;
    }
    throw err;
  });
}

// The canonical initializer for state.creator -- called from app.js's own
// hash-routing bootstrap (the ONLY entry point into this screen, since
// #creator is never linked from the nav/home grid) BEFORE the first
// renderAll(), matching how every other hash-only screen with real
// sub-state (e.g. h2hLive) initializes itself. renderCreatorScreen() below
// is a pure render function and never mutates state itself.
function creatorInitialState() {
  return {
    screen: creatorToken() ? CREATOR_SCREEN.HOME : CREATOR_SCREEN.AUTH,
    requestText: '', feasibility: null, generated: null, queue: [], queueFilter: '',
    capabilities: null, error: null, formatQuery: '', formatCategory: 'All',
    guidedLeague: 'NFL', guidedTopic: 'General', guidedDifficulty: 'medium', guidedCount: 5,
    previewMode: 'player', editingQuestionIndex: null,
  };
}

function creatorSubmitToken(token) {
  creatorSetToken((token || '').trim());
  state.creator.screen = CREATOR_SCREEN.HOME;
  renderAll();
}

function creatorLogout() {
  creatorClearToken();
  state.creator = null;
  state.screen = 'home';
  renderAll();
}

function creatorGoHome() {
  var s = state.creator; if (!s) return;
  s.screen = CREATOR_SCREEN.HOME; s.error = null;
  renderAll();
}

function creatorCheckFeasibility(text) {
  var s = state.creator; if (!s) return;
  s.requestText = text;
  s.screen = CREATOR_SCREEN.CHECKING;
  renderAll();
  creatorFetchJson('/v1/creator/feasibility', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_text: text }),
  }).then(function (result) {
    s.feasibility = result;
    s.generated = null;
    s.screen = CREATOR_SCREEN.RESULT;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}

function creatorGenerate() {
  var s = state.creator; if (!s) return;
  s.screen = CREATOR_SCREEN.GENERATING;
  renderAll();
  creatorFetchJson('/v1/creator/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_text: s.requestText, puzzle_count: s.guidedCount || 5, difficulty: s.guidedDifficulty || 'medium' }),
  }).then(function (result) {
    s.generated = result;
    s.screen = CREATOR_SCREEN.PREVIEW;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}

function creatorSetReview(packageId, reviewStatus) {
  var s = state.creator; if (!s) return;
  creatorFetchJson('/v1/creator/review', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ package_id: packageId, review_status: reviewStatus }),
  }).then(function (result) {
    if (s.generated && s.generated.package_id === packageId) s.generated.review_status = result.review_status;
    var row = s.queue.find(function (p) { return p.package_id === packageId; });
    if (row) row.review_status = result.review_status;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}

function creatorLoadQueue(filter) {
  var s = state.creator; if (!s) return;
  s.queueFilter = filter || '';
  s.screen = CREATOR_SCREEN.QUEUE;
  renderAll();
  var qs = filter ? ('?review_status=' + encodeURIComponent(filter)) : '';
  creatorFetchJson('/v1/creator/queue' + qs).then(function (result) {
    s.queue = result.packages;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}

function creatorLoadCapabilities() {
  var s = state.creator; if (!s) return;
  s.screen = CREATOR_SCREEN.CAPABILITIES;
  renderAll();
  creatorFetchJson('/v1/creator/capabilities').then(function (result) {
    s.capabilities = result.capabilities;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}

// Part G: reshapes ONE internal question (full package shape, including
// correctIndex/notes -- fine here, this view is admin-only) into the exact
// public payload shape renderEnginePilotPromptHtml() (engine-game-ui.js)
// already renders for real players -- so the Creator's preview is
// guaranteed to look like what a player would actually see, not a
// hand-maintained approximation of it.
function creatorQuestionAsPublicPayload(q) {
  return {
    prompt: q.question, options: q.options,
    visual_template: q.visual_template || 'DEFAULT_MULTIPLE_CHOICE',
    visual_payload: q.visual_payload || null,
  };
}

// UI/UX Upgrade Pass: real examples of requests that map onto capabilities
// already confirmed GENERATION_VERIFIED in production (not aspirational
// copy) -- so clicking one and hitting Check Feasibility genuinely
// demonstrates SUPPORTED / SUPPORTED_WITH_LIMITATIONS, not a dead end.
var CREATOR_EXAMPLE_PROMPTS = [
  'Guess the NFL team from its starting offense, by position.',
  'Give me an NFL game and make me guess who led it in rushing yards.',
  'Which team was ranked in the AP Top 25 this week?',
  'Make me guess which NFL All-Pro attended this college.',
  'Give me a real NFL Draft pick and make me guess the team.',
];
function creatorUseExample(text) {
  var s = state.creator; if (!s) return;
  s.requestText = text;
  renderAll();
  var el = document.getElementById('creator-request-input');
  if (el) el.focus();
}

function creatorGuidedPrompt() {
  var s=state.creator||{};
  var league=s.guidedLeague||'NFL', topic=s.guidedTopic||'General', diff=s.guidedDifficulty||'medium';
  var topicCopy={
    'General':'mixed football knowledge', 'Draft':'draft history', 'History':'football history',
    'Players':'players and careers', 'Teams':'teams and seasons', 'Stats':'player and team statistics',
    'Awards':'awards and honors', 'Games':'real game results and performances'
  };
  return 'Make me a '+league+' trivia game about '+(topicCopy[topic]||topic.toLowerCase())+'. Use '+diff+' difficulty.';
}
function creatorGuidedBuild() {
  var s=state.creator;if(!s)return;
  s.requestText=creatorGuidedPrompt();
  creatorCheckFeasibility(s.requestText);
}
function creatorSetGuided(field,value) {
  var s=state.creator;if(!s)return;
  if(field==='league')s.guidedLeague=value;
  else if(field==='topic')s.guidedTopic=value;
  else if(field==='difficulty')s.guidedDifficulty=value;
  else if(field==='count')s.guidedCount=Math.max(1,Math.min(25,parseInt(value,10)||5));
  renderAll();
}
function creatorTogglePreviewMode(mode){ if(!state.creator)return; state.creator.previewMode=mode==='admin'?'admin':'player'; renderAll(); }
function creatorEditQuestion(index){ if(!state.creator)return; state.creator.editingQuestionIndex=(state.creator.editingQuestionIndex===index?null:index); renderAll(); }
function creatorSaveQuestionRevision(index){
  var s=state.creator,g=s&&s.generated;if(!g||!g.package_id||!g.questions)return;
  var q=g.questions[index];if(!q)return;
  var promptEl=document.getElementById('creator-edit-question-'+index);
  var notesEl=document.getElementById('creator-edit-notes-'+index);
  var opts=[]; for(var oi=0;oi<(q.options||[]).length;oi++){var el=document.getElementById('creator-edit-option-'+index+'-'+oi);opts.push(el?el.value:q.options[oi]);}
  var correctEl=document.getElementById('creator-edit-correct-'+index);
  var replacement={question:promptEl?promptEl.value:q.question,options:opts,correctIndex:correctEl?parseInt(correctEl.value,10):q.correctIndex,notes:notesEl?notesEl.value:(q.notes||''),difficulty:q.difficulty||'medium'};
  s.screen=CREATOR_SCREEN.GENERATING;renderAll();
  creatorFetchJson('/v1/creator/question/revise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({package_id:g.package_id,question_index:index,replacement:replacement})})
    .then(function(result){s.generated=result;s.editingQuestionIndex=null;s.previewMode='player';s.screen=CREATOR_SCREEN.PREVIEW;renderAll();})
    .catch(function(err){s.error=creatorUserFacingError(err);s.screen=CREATOR_SCREEN.ERROR;renderAll();});
}
function creatorRegeneratePackage(){
  var s=state.creator;if(!s||!s.requestText)return;
  var count=(s.generated&&s.generated.question_count)||s.guidedCount||5;
  s.screen=CREATOR_SCREEN.GENERATING;renderAll();
  creatorFetchJson('/v1/creator/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request_text:s.requestText,puzzle_count:count,difficulty:s.guidedDifficulty||'medium',seed:'creator-refresh-'+Date.now()})})
    .then(function(result){s.generated=result;s.previewMode='player';s.screen=CREATOR_SCREEN.PREVIEW;renderAll();})
    .catch(function(err){s.error=creatorUserFacingError(err);s.screen=CREATOR_SCREEN.ERROR;renderAll();});
}

function creatorGuidedBuilderHtml(){
  var s=state.creator||{}; var topics=['General','Draft','History','Players','Teams','Stats','Awards','Games'];
  return '<section class="creator-guided-card"><div class="creator-compose-head"><div><span class="dashboard-eyebrow">GUIDED BUILDER</span><h2>Build it without writing a prompt</h2></div><span class="creator-step-chip">Fast path</span></div>'+
    '<div class="creator-guided-grid">'+
      '<label><span>League</span><select data-creator-guided="league"><option'+(s.guidedLeague==='NFL'?' selected':'')+'>NFL</option><option'+(s.guidedLeague==='CFB'?' selected':'')+'>CFB</option><option'+(s.guidedLeague==='Mixed'?' selected':'')+'>Mixed</option></select></label>'+
      '<label><span>Topic</span><select data-creator-guided="topic">'+topics.map(function(x){return '<option'+(s.guidedTopic===x?' selected':'')+'>'+esc(x)+'</option>';}).join('')+'</select></label>'+
      '<label><span>Difficulty</span><select data-creator-guided="difficulty"><option value="easy"'+(s.guidedDifficulty==='easy'?' selected':'')+'>Easy</option><option value="medium"'+(s.guidedDifficulty==='medium'?' selected':'')+'>Medium</option><option value="hard"'+(s.guidedDifficulty==='hard'?' selected':'')+'>Hard</option></select></label>'+
      '<label><span>Questions</span><select data-creator-guided="count">'+[5,10,15,20,25].map(function(n){return '<option value="'+n+'"'+(Number(s.guidedCount)===n?' selected':'')+'>'+n+'</option>';}).join('')+'</select></label>'+
    '</div><div class="creator-guided-preview"><small>Creator will ask:</small><b>'+esc(creatorGuidedPrompt())+'</b></div>'+
    '<button class="btn-primary" data-creator-guided-build>'+icon('zap')+' Check Guided Build</button></section>';
}

function creatorQuestionEditorHtml(q,index){
  return '<div class="creator-question-editor">'+
    '<label>Question<textarea id="creator-edit-question-'+index+'">'+esc(q.question||'')+'</textarea></label>'+
    '<div class="creator-edit-options">'+(q.options||[]).map(function(opt,oi){return '<label>Option '+String.fromCharCode(65+oi)+'<input id="creator-edit-option-'+index+'-'+oi+'" value="'+esc(opt)+'"></label>';}).join('')+'</div>'+
    '<label>Correct answer<select id="creator-edit-correct-'+index+'">'+(q.options||[]).map(function(opt,oi){return '<option value="'+oi+'"'+(oi===q.correctIndex?' selected':'')+'>'+String.fromCharCode(65+oi)+' · '+esc(opt)+'</option>';}).join('')+'</select></label>'+
    '<label>Notes<textarea id="creator-edit-notes-'+index+'">'+esc(q.notes||'')+'</textarea></label>'+
    '<div class="btn-row"><button class="btn-primary" data-creator-question-save="'+index+'">Save as New Version</button><button class="btn-secondary" data-creator-question-edit="'+index+'">Cancel</button></div>'+
    '<small>The original package stays untouched. This creates a new QA-validated package ID.</small></div>';
}
// Format Picker pass: the user's own real gap report -- "I want it to
// give me options when you make a game mode ... without having to use a
// keyword or sum bs like that." Every entry with a taxonomyId+variant
// below calls POST /v1/creator/format/generate directly (see
// gateway.services.creator.generate_direct()'s own docstring) -- no
// text, no regex bridge, no collision risk, real and already-tested for
// every entry (live-verified this pass via generate_direct() and the
// real HTTP route, matching gateway/tests/test_creator_format_picker.py's
// own coverage). The 3 schedule-driven entries (Weekly Pick'em/Fantasy
// Draft/Confidence Pick) have no taxonomyId -- they need a real
// (league, season, week) resolution generate_direct() deliberately
// doesn't duplicate (see its own docstring) -- so those 3 alone still
// fall back to creatorUseExample()'s text-fill flow. To add a format
// landing later, append one object here; nothing else changes.
var CREATOR_FORMAT_CATALOG = [
  { category: 'Matching & Sorting', title: 'Matching', desc: 'Pair up real players/picks.', taxonomyId: 'MATCHING', variant: 'NFL_DRAFT_CLASS_MATCH' },
  { category: 'Matching & Sorting', title: 'Timeline Order', desc: 'Put real picks/years in order.', taxonomyId: 'SORTING_TIMELINE', variant: 'NFL_DRAFT_PICK_ORDER' },
  { category: 'Matching & Sorting', title: 'Stat Ladder', desc: 'Rank real players by a real career stat.', taxonomyId: 'SORTING_TIMELINE', variant: 'NFL_CAREER_PASSING_TD_LADDER' },
  { category: 'Matching & Sorting', title: 'Map the Career', desc: 'Order the real teams a player actually played for.', taxonomyId: 'SORTING_TIMELINE', variant: 'NFL_PLAYER_CAREER_TEAM_ORDER' },
  { category: 'Compare & Rank', title: 'Head to Head Duel', desc: 'Two real players, one real stat -- who’s higher?', taxonomyId: 'PAIRWISE_COMPARE', variant: 'NFL_CAREER_PASSING_TD_DUEL' },
  { category: 'Compare & Rank', title: 'Best of Seven Duel', desc: 'A real multi-category showdown between two real QBs.', taxonomyId: 'PAIRWISE_COMPARE', variant: 'NFL_CAREER_QB_BEST_OF_SEVEN' },
  { category: 'Compare & Rank', title: 'Leaderboard Climb', desc: 'Climb a real leaderboard one real rung at a time.', taxonomyId: 'LEADERBOARD_CLIMB', variant: 'NFL_CAREER_PASSING_YARDS_CLIMB' },
  { category: 'Compare & Rank', title: 'Higher or Lower', desc: 'A real streak of higher/lower stat guesses.', taxonomyId: 'HIGHER_LOWER_STREAK', variant: 'NFL_TEAM_SEASON_WINS' },
  { category: 'Compare & Rank', title: 'Comparison Bracket', desc: 'Real teams face off through a real bracket.', taxonomyId: 'COMPARISON_BRACKET', variant: 'NFL_TEAM_SEASON_WINS_BRACKET' },
  { category: 'Compare & Rank', title: 'King of the Hill', desc: 'Defend the real champion against a gauntlet of real challengers.', taxonomyId: 'KING_OF_THE_HILL', variant: 'NFL_TEAM_SEASON_WINS_KING_OF_THE_HILL' },
  { category: 'Compare & Rank', title: 'King of the Hill (CFB)', desc: 'Defend the real college champion against a gauntlet of real challengers.', taxonomyId: 'KING_OF_THE_HILL', variant: 'CFB_TEAM_SEASON_WINS_KING_OF_THE_HILL' },
  { category: 'Compare & Rank', title: 'Guess the Ranking', desc: 'Name a real player, guess their real rank on a real leaderboard.', taxonomyId: 'GUESS_THE_RANKING', variant: 'NFL_CAREER_PASSING_YARDS_RANKING' },
  { category: 'Compare & Rank', title: 'Guess the Ranking (CFB)', desc: 'Name a real college player, guess their real rank on a real leaderboard.', taxonomyId: 'GUESS_THE_RANKING', variant: 'CFB_CAREER_PASSING_YARDS_RANKING' },
  { category: 'Compare & Rank', title: 'Stat Target', desc: 'Tap whichever real player’s real total came closest to the target.', taxonomyId: 'STAT_TARGET', variant: 'NFL_SEASON_RUSHING_YARDS_TARGET' },
  { category: 'Compare & Rank', title: 'Stat Target (CFB)', desc: 'Tap whichever real college player’s real total came closest to the target.', taxonomyId: 'STAT_TARGET', variant: 'CFB_SEASON_RUSHING_YARDS_TARGET' },
  { category: 'Spot the Odd One', title: 'Pick the Impostor', desc: '3 real players share a fact -- find the 1 that doesn’t.', taxonomyId: 'PICK_THE_IMPOSTOR', variant: 'NFL_TEAM_ROSTER_IMPOSTOR' },
  { category: 'Spot the Odd One', title: 'Unique One Out', desc: 'Same shape, real NFL Draft class membership.', taxonomyId: 'PICK_THE_IMPOSTOR', variant: 'NFL_DRAFT_CLASS_ONE_OUT' },
  { category: 'Spot the Odd One', title: 'Missing Piece', desc: 'Find the real 4th player who also belongs.', taxonomyId: 'MISSING_PIECE', variant: 'NFL_TEAM_ROSTER_MISSING_PIECE' },
  { category: 'Spot the Odd One', title: 'Blind Resume', desc: 'A real career stat line, name hidden -- whose is it?', taxonomyId: 'BLIND_RESUME', variant: 'NFL_QB_CAREER_BLIND_RESUME' },
  { category: 'Spot the Odd One', title: 'Blind Resume (CFB)', desc: 'A real college career stat line, name hidden -- whose is it?', taxonomyId: 'BLIND_RESUME', variant: 'CFB_QB_CAREER_BLIND_RESUME' },
  { category: 'True or False', title: 'Fact or Fake', desc: 'Read a real statement and decide if it’s true or been altered.', taxonomyId: 'FACT_OR_FAKE', variant: 'NFL_DRAFT_FACT_OR_FAKE' },
  { category: 'True or False', title: 'Fact or Fake (CFB)', desc: 'Read a real college football score and decide if it’s true or been altered.', taxonomyId: 'FACT_OR_FAKE', variant: 'CFB_GAME_RESULT_FACT_OR_FAKE' },
  { category: 'True or False', title: 'Reverse Trivia', desc: 'A real player is named -- pick the 1 of 4 real facts that’s true about them.', taxonomyId: 'REVERSE_TRIVIA', variant: 'NFL_DRAFT_REVERSE_TRIVIA' },
  { category: 'True or False', title: 'Reverse Trivia (CFB)', desc: 'A real college player is named -- pick the 1 of 4 real facts that’s true about them.', taxonomyId: 'REVERSE_TRIVIA', variant: 'CFB_SEASON_PASSING_REVERSE_TRIVIA' },
  { category: 'Build a Team', title: 'Lineup Builder', desc: 'Build a real skill-position lineup.', taxonomyId: 'ROSTER_BUILD', variant: 'NFL_2010S_OFFENSE_BUILDER' },
  { category: 'Build a Team', title: 'Auction Draft', desc: 'Draft real players against a fictional budget.', taxonomyId: 'ROSTER_BUILD', variant: 'NFL_AUCTION_DRAFT' },
  { category: 'Build a Team', title: 'Cap Challenge', desc: 'Build a real roster under a real salary cap.', taxonomyId: 'ROSTER_BUILD', variant: 'NFL_CAP_CHALLENGE' },
  { category: 'Build a Team', title: 'Lineup Grid', desc: 'Guess the real team from its real starting lineup.', taxonomyId: 'POSITION_LINEUP_GRID', variant: 'NFL_OFFENSE_LINEUP_COLLEGE_TEAM_ONLY' },
  { category: 'Risk & Wager', title: 'Risk It', desc: 'Pick a real risk tier before you see the question.', taxonomyId: 'RISK_IT', variant: 'NFL_DRAFT_RISK_IT' },
  { category: 'Risk & Wager', title: 'Risk It (CFB)', desc: 'Pick a real risk tier before you see the question.', taxonomyId: 'RISK_IT', variant: 'CFB_SEASON_PASSING_RISK_IT' },
  { category: 'Risk & Wager', title: 'Wager Mode', desc: 'Wager fictional points on a real category before it’s revealed.', taxonomyId: 'WAGER_MODE', variant: 'WAGER_MODE_MIXED' },
  { category: 'Risk & Wager', title: 'Double or Nothing', desc: 'Bank your points or risk them all doubling on a harder real question.', taxonomyId: 'DOUBLE_OR_NOTHING', variant: 'NFL_DRAFT_DOUBLE_OR_NOTHING' },
  { category: 'Risk & Wager', title: 'Double or Nothing (CFB)', desc: 'Bank your points or risk them all doubling on a harder real question.', taxonomyId: 'DOUBLE_OR_NOTHING', variant: 'CFB_SEASON_PASSING_DOUBLE_OR_NOTHING' },
  { category: 'Risk & Wager', title: 'Three Strikes', desc: 'Answer real questions of rising difficulty -- a wrong answer costs a strike.', taxonomyId: 'THREE_STRIKES', variant: 'NFL_DRAFT_THREE_STRIKES' },
  { category: 'Risk & Wager', title: 'Three Strikes (CFB)', desc: 'Answer real questions of rising difficulty -- a wrong answer costs a strike.', taxonomyId: 'THREE_STRIKES', variant: 'CFB_SEASON_PASSING_THREE_STRIKES' },
  { category: 'Brackets & Tournaments', title: 'Knockout Tournament', desc: 'A real single-elimination bracket.', taxonomyId: 'KNOCKOUT_BRACKET', variant: 'NFL_TEAM_SEASON_WINS_KNOCKOUT_16' },
  { category: 'Brackets & Tournaments', title: 'Elimination', desc: 'Survive a real sequence of stat guesses -- one miss and you’re out.', taxonomyId: 'ELIMINATION_SURVIVAL', variant: 'NFL_SUPER_BOWL_CHAMPION_SURVIVAL' },
  { category: 'Story & Path', title: 'Choose Your Path', desc: 'Branch through a real topic tree.', taxonomyId: 'BRANCH_STATE', variant: 'NFL_TOPIC_PATH' },
  { category: 'Story & Path', title: 'Career Path', desc: 'Read a real career path, then guess the real player.', taxonomyId: 'CAREER_PATH', variant: 'NFL_PLAYER_CAREER_PATH_IDENTIFY' },
  { category: 'Story & Path', title: 'Mystery Roster', desc: 'Reveal real clues about a mystery real team-season, or guess anytime.', taxonomyId: 'MYSTERY_ROSTER', variant: 'NFL_TEAM_SEASON_MYSTERY_ROSTER' },
  { category: 'Story & Path', title: 'Mystery Roster (CFB)', desc: 'Reveal real clues about a mystery real college team-season, or guess anytime.', taxonomyId: 'MYSTERY_ROSTER', variant: 'CFB_TEAM_SEASON_MYSTERY_ROSTER' },
  { category: 'Matching & Sorting', title: 'Draft Pick Ladder', desc: 'A real player is named -- guess their real overall draft pick number.', taxonomyId: 'DRAFT_PICK_LADDER', variant: 'NFL_DRAFT_PICK_LADDER' },
  { category: 'Mixed Trivia', title: 'Category Roulette', desc: 'Each round’s real category is shown immediately -- answer the real question.', taxonomyId: 'CATEGORY_ROULETTE', variant: 'CATEGORY_ROULETTE_MIXED' },
  { category: 'Story & Path', title: 'Common Link', desc: '3 real players are named -- guess what real fact connects them.', taxonomyId: 'COMMON_LINK', variant: 'NFL_DRAFT_COMMON_LINK' },
  { category: 'Story & Path', title: 'Common Link (CFB)', desc: '3 real college players are named -- guess what real fact connects them.', taxonomyId: 'COMMON_LINK', variant: 'CFB_SEASON_COMMON_LINK' },
  { category: 'Story & Path', title: 'Before & After', desc: 'Which real team did this real player play for FIRST?', taxonomyId: 'BEFORE_AFTER', variant: 'NFL_TEAM_CHANGE_BEFORE_AFTER' },
  { category: 'Story & Path', title: 'Guess the Season', desc: 'Identify the real season from real clues.', taxonomyId: 'GUESS_THE_SEASON', variant: 'NFL_SUPER_BOWL_SEASON' },
  { category: 'Story & Path', title: 'Connection Grid', desc: 'A real 3x3 grid of real team/round intersections.', taxonomyId: 'GRID_CONSTRAINT_BOARD', variant: 'NFL_TEAM_DRAFT_ROUND_GRID' },
  { category: 'Story & Path', title: 'Six Degrees', desc: 'Connect two real players through real teammates.', taxonomyId: 'RELATIONSHIP_CHAIN', variant: 'CFB_SCHOOL_TO_NFL_TEAM_CHAIN' },
  { category: 'Drives', title: 'Perfect Drive', desc: 'Answer real questions to drive down the real field.', taxonomyId: 'DRIVE_PROGRESSION', variant: 'NFL_DRAFT_PERFECT_DRIVE' },
  { category: 'Drives', title: 'Goal Line Stand', desc: 'Real 4-down trivia from the real goal line.', taxonomyId: 'DRIVE_PROGRESSION', variant: 'NFL_DRAFT_GOAL_LINE_STAND' },
  { category: 'Strategy Arcade', title: 'Bingo Blitz', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'BINGO_BLITZ' },
  { category: 'Strategy Arcade', title: 'Territory Takeover', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TERRITORY_TAKEOVER' },
  { category: 'Strategy Arcade', title: 'Exact Ten', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'EXACT_TEN' },
  { category: 'Strategy Arcade', title: 'Pyramid Climb', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'PYRAMID_CLIMB' },
  { category: 'Strategy Arcade', title: 'Lockbox', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'LOCKBOX' },
  { category: 'Strategy Arcade', title: 'Combo Meter', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'COMBO_METER' },
  { category: 'Strategy Arcade', title: 'Checkpoint Rally', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CHECKPOINT_RALLY' },
  { category: 'Strategy Arcade', title: 'Escalator', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'ESCALATOR' },
  { category: 'Strategy Arcade', title: 'Power Up', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'POWER_UP' },
  { category: 'Strategy Arcade', title: 'Category Conquest', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CATEGORY_CONQUEST' },
  { category: 'Strategy Arcade', title: 'Scoreboard Swing', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'SCOREBOARD_SWING' },
  { category: 'Strategy Arcade', title: 'Momentum Bar', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'MOMENTUM_BAR' },
  { category: 'Strategy Arcade', title: 'Timeout Tokens', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TIMEOUT_TOKENS' },
  { category: 'Strategy Arcade', title: 'Perfect Set', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'PERFECT_SET' },
  { category: 'Strategy Arcade', title: 'Triple or Take', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TRIPLE_OR_TAKE' },
  { category: 'Strategy Arcade', title: 'Connect Four', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CONNECT_FOUR' },
  { category: 'Strategy Arcade', title: 'Tic-Tac-Toe', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TIC_TAC_TOE' },
  { category: 'Strategy Arcade', title: 'Challenge Flag', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CHALLENGE_FLAG' },
  { category: 'Strategy Arcade', title: 'Extra Point', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'EXTRA_POINT' },
  { category: 'Strategy Arcade', title: 'Comeback Mode', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'COMEBACK_MODE' },
  { category: 'Strategy Arcade', title: 'Category Draft', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CATEGORY_DRAFT' },
  { category: 'Strategy Arcade', title: 'Three & Out', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'THREE_AND_OUT' },
  { category: 'Strategy Arcade', title: 'Pick Your Poison', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'PICK_YOUR_POISON' },
  { category: 'Strategy Arcade', title: 'Second Chance Queue', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'SECOND_CHANCE_QUEUE' },
  { category: 'Strategy Arcade', title: 'Coverage Shell', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'COVERAGE_SHELL' },
  { category: 'Strategy Arcade', title: 'Offense / Defense', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'OFFENSE_DEFENSE' },
  { category: 'Strategy Arcade', title: 'Field Goal Range', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'FIELD_GOAL_RANGE' },
  { category: 'Strategy Arcade', title: 'Two-Minute Drill', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TWO_MINUTE_DRILL' },
  { category: 'Strategy Arcade', title: 'Category Streak', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CATEGORY_STREAK' },
  { category: 'Strategy Arcade', title: 'Perfect Quarter', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'PERFECT_QUARTER' },
  { category: 'Strategy Arcade', title: 'Red Zone Ladder', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'RED_ZONE_LADDER' },
  { category: 'Strategy Arcade', title: 'Drive Builder', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'DRIVE_BUILDER' },
  { category: 'Strategy Arcade', title: 'Hot Hand Switch', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'HOT_HAND_SWITCH' },
  { category: 'Strategy Arcade', title: 'Overtime Shootout', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'OVERTIME_SHOOTOUT' },
  { category: 'Strategy Arcade', title: 'First Down Chain', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'FIRST_DOWN_CHAIN' },
  { category: 'Strategy Arcade', title: 'Blitz Package', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'BLITZ_PACKAGE' },
  { category: 'Strategy Arcade', title: 'Zone Control', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'ZONE_CONTROL' },
  { category: 'Strategy Arcade', title: 'Play Caller', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'PLAY_CALLER' },
  { category: 'Strategy Arcade', title: 'Possession Arrow', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'POSSESSION_ARROW' },
  { category: 'Strategy Arcade', title: 'Sudden Death', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'SUDDEN_DEATH' },
  { category: 'Strategy Arcade', title: 'Score Bank', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'SCORE_BANK' },
  { category: 'Strategy Arcade', title: 'Audible', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'AUDIBLE' },
  { category: 'Strategy Arcade', title: 'Fourth Down Decision', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'FOURTH_DOWN_DECISION' },
  { category: 'Strategy Arcade', title: 'Series Sweep', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'SERIES_SWEEP' },
  { category: 'Strategy Arcade', title: 'Road to 100', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'ROAD_TO_100' },
  { category: 'Strategy Arcade', title: 'Option Eraser', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'OPTION_ERASER' },
  { category: 'Strategy Arcade', title: 'Route Tree', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'ROUTE_TREE' },
  { category: 'Strategy Arcade', title: 'Turnover Battle', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'TURNOVER_BATTLE' },
  { category: 'Strategy Arcade', title: 'Category Lockout', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CATEGORY_LOCKOUT' },
  { category: 'Strategy Arcade', title: 'Hail Mary', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'HAIL_MARY' },
  { category: 'Strategy Arcade', title: 'Moving Target', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'MOVING_TARGET' },
  { category: 'Strategy Arcade', title: 'Draft Order', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'DRAFT_ORDER' },
  { category: 'Strategy Arcade', title: 'Championship Run', desc: 'A distinct server-authoritative strategy format built on real mixed football trivia.', taxonomyId: 'STRATEGY_ARCADE', variant: 'CHAMPIONSHIP_RUN' },
  { category: 'Live & Weekly', title: 'Weekly Pick’em', desc: 'Pick real winners for this week’s real NFL slate.', phrase: 'Give me the NFL weekly pick’em.' },
  { category: 'Live & Weekly', title: 'Fantasy Draft', desc: 'A real live-style fantasy draft.', phrase: 'Give me a fantasy draft with NFL players.' },
  { category: 'Live & Weekly', title: 'Confidence Pick', desc: 'Rank your real picks by confidence for real points.', phrase: 'Give me a confidence pick game for this week’s NFL games.' },
];
function creatorGenerateDirect(taxonomyId, variant) {
  var s = state.creator; if (!s) return;
  s.screen = CREATOR_SCREEN.GENERATING;
  renderAll();
  creatorFetchJson('/v1/creator/format/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ taxonomy_id: taxonomyId, variant: variant }),
  }).then(function (result) {
    s.generated = result;
    s.screen = CREATOR_SCREEN.PREVIEW;
    renderAll();
  }).catch(function (err) {
    s.error = creatorUserFacingError(err);
    s.screen = CREATOR_SCREEN.ERROR;
    renderAll();
  });
}
function creatorPickFormat(index) {
  var entry = CREATOR_FORMAT_CATALOG[index];
  if (!entry) return;
  if (entry.taxonomyId) { creatorGenerateDirect(entry.taxonomyId, entry.variant); return; }
  creatorUseExample(entry.phrase);
}
function creatorFormatCategories() {
  var seen={All:true}, out=['All'];
  CREATOR_FORMAT_CATALOG.forEach(function(entry){
    if(!seen[entry.category]){seen[entry.category]=true;out.push(entry.category);}
  });
  return out;
}
function creatorFormatMatches(entry, query, category) {
  if(category && category!=='All' && entry.category!==category) return false;
  query=String(query||'').trim().toLowerCase();
  if(!query) return true;
  return [entry.title,entry.desc,entry.category,entry.taxonomyId,entry.variant].filter(Boolean).join(' ').toLowerCase().indexOf(query)!==-1;
}
function creatorSetFormatCategory(category) {
  if(!state.creator)return;
  state.creator.formatCategory=category||'All';
  renderAll();
}
function creatorSetFormatQuery(query) {
  if(!state.creator)return;
  state.creator.formatQuery=query||'';
  renderAll();
  setTimeout(function(){
    var el=document.getElementById('creator-format-search');
    if(el){el.focus();try{el.setSelectionRange(el.value.length,el.value.length);}catch(e){}}
  },0);
}
function renderCreatorFormatPickerHtml() {
  var s=state.creator||{}, query=s.formatQuery||'', category=s.formatCategory||'All';
  var rows=CREATOR_FORMAT_CATALOG.map(function(entry,index){return {entry:entry,index:index};})
    .filter(function(row){return creatorFormatMatches(row.entry,query,category);});
  var cats=creatorFormatCategories();
  return '<section class="creator-library">'+
    '<div class="creator-library-head"><div><span class="dashboard-eyebrow">FORMAT LIBRARY</span><h3>Choose a proven mechanic</h3><p>Search the catalog or narrow by family. Direct formats generate immediately.</p></div><div class="creator-library-count"><b>'+rows.length+'</b><span>shown</span></div></div>'+
    '<div class="creator-library-controls">'+
      '<div class="creator-search-wrap">'+icon('search')+'<input id="creator-format-search" value="'+esc(query)+'" placeholder="Search formats, mechanics, variants…" autocomplete="off"></div>'+
      '<div class="creator-category-strip">'+cats.map(function(cat){return '<button class="'+(category===cat?'active':'')+'" data-creator-format-category="'+esc(cat)+'">'+esc(cat)+'</button>';}).join('')+'</div>'+
    '</div>'+
    (rows.length?'<div class="creator-format-grid">'+rows.map(function(row){
      var e=row.entry, direct=!!e.taxonomyId;
      return '<article class="creator-format-card">'+
        '<div class="creator-format-card-top"><span class="creator-format-category">'+esc(e.category)+'</span><span class="creator-format-type">'+(direct?'DIRECT':'GUIDED')+'</span></div>'+
        '<h4>'+esc(e.title)+'</h4><p>'+esc(e.desc)+'</p>'+
        '<div class="creator-format-meta">'+
          (e.taxonomyId?'<span>'+esc(e.taxonomyId)+'</span>':'<span>Natural language</span>')+
          (e.variant?'<span>'+esc(e.variant.replace(/_/g,' '))+'</span>':'')+
        '</div>'+
        '<button class="'+(direct?'btn-primary':'btn-secondary')+'" data-creator-format-pick="'+row.index+'">'+(direct?'Generate':'Use Prompt')+'</button>'+
      '</article>';
    }).join('')+'</div>':'<div class="creator-empty-state"><b>No formats match that search.</b><span>Try another term or switch back to All.</span></div>')+
  '</section>';
}
function creatorSupportBadgeHtml(status) {
  var cls = { SUPPORTED: 'good', SUPPORTED_WITH_LIMITATIONS: 'good', UNDERSTOOD_BUT_UNSUPPORTED: 'warn',
    MISSING_DATA: 'warn', UNSAFE: 'bad', UNKNOWN: 'warn' }[status] || 'warn';
  return '<span class="creator-badge creator-badge-' + cls + '">' + esc(status) + '</span>';
}

function creatorToolbarHtml(showBack) {
  var screen=(state.creator&&state.creator.screen)||CREATOR_SCREEN.HOME;
  return '<div class="creator-topbar">'+
    '<div class="creator-brand"><span class="creator-brand-mark">R</span><div><b>Reads Creator</b><small>Engine Workspace</small></div></div>'+
    '<div class="creator-topnav">'+
      '<button class="'+(screen===CREATOR_SCREEN.HOME?'active':'')+'" data-creator-nav="home">'+icon('zap')+' Create</button>'+
      '<button class="'+(screen===CREATOR_SCREEN.QUEUE?'active':'')+'" data-creator-nav="queue">'+icon('list')+' Review</button>'+
      '<button class="'+(screen===CREATOR_SCREEN.CAPABILITIES?'active':'')+'" data-creator-nav="capabilities">'+icon('layers')+' Capabilities</button>'+
    '</div>'+
    '<div class="creator-top-actions">'+
      (showBack?'<button class="btn-tiny" data-creator-nav="home">&larr; Creator</button>':'')+
      '<button class="btn-tiny" data-creator-logout>Log Out</button>'+
      '<button class="btn-tiny" data-go="home">'+icon('close')+' Exit</button>'+
    '</div>'+
  '</div>';
}

function renderCreatorScreen() {
  var s = state.creator;
  if (!s) {
    // Defensive only -- app.js's hash bootstrap always creates state.creator
    // before routing here (see creatorInitialState()). Render the same auth
    // gate a fresh visit would see, without mutating state mid-render.
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit</button></div>' +
      '<h2 class="panel-title">Game Creator</h2>' +
      '<p class="mode-desc">Reload this page to continue.</p></div>';
  }

  if (s.screen === CREATOR_SCREEN.AUTH) {
    return '<div class="creator-auth-shell">' +
      '<div class="creator-auth-card">' +
      '<button class="btn-tiny creator-auth-exit" data-go="home">' + icon('close') + ' Exit</button>' +
      '<div class="creator-auth-mark">R</div>' +
      '<span class="dashboard-eyebrow">OWNER WORKSPACE</span><h2>Reads Creator</h2>' +
      '<p>Build, inspect and review real engine-generated football games from one private workspace.</p>' +
      '<label class="creator-auth-label">Gateway admin token</label>' +
      '<input type="password" id="creator-token-input" class="creator-input" placeholder="Enter token" autocomplete="off" />' +
      '<button class="btn-primary creator-auth-submit" data-creator-auth-submit>Enter Creator ' + icon('arrowRight') + '</button>' +
      '<small>Stored only for this browser tab and sent only to your Reads Gateway.</small>' +
      '</div></div>';
  }

  if (s.screen === CREATOR_SCREEN.ERROR) {
    return '<div class="panel">' + creatorToolbarHtml(true) +
      '<p class="mode-desc" aria-live="assertive">' + esc(s.error) + '</p>' +
      '<div class="btn-row"><button class="btn-primary" data-creator-nav="home">Back to Creator Home</button></div>' +
      '</div>';
  }

  if (s.screen === CREATOR_SCREEN.QUEUE) {
    var filters = ['', 'GENERATED', 'REVIEWED', 'APPROVED', 'REJECTED'];
    return '<div class="panel">' + creatorToolbarHtml(true) +
      '<h2 class="panel-title">Review Queue</h2>' +
      '<div class="chip-row">' + filters.map(function (f) {
        return '<button class="chip-toggle' + (s.queueFilter === f ? ' active' : '') + '" data-creator-queue-filter="' + esc(f) + '">' + esc(f || 'All') + '</button>';
      }).join('') + '</div>' +
      (s.queue.length ? s.queue.map(function (p) {
        // Same real question_count/puzzle_count shape mismatch as the
        // PREVIEW screen above -- a stored identify_player_from_clues
        // package's real count lives in puzzle_count, not question_count.
        var pCount = (p.question_count != null) ? p.question_count : (p.puzzle_count != null ? p.puzzle_count : 0);
        var pLabel = (p.question_count == null && p.puzzle_count != null) ? 'puzzles' : 'questions';
        return '<div class="creator-queue-row">' +
          '<div><b>' + esc(p.game_title || p.package_id) + '</b> &middot; ' + esc(p.review_status) + ' &middot; QA ' + esc(p.qa_status) +
          ' &middot; ' + pCount + ' ' + pLabel + '</div>' +
          '<div class="mode-desc">' + esc((p.requested_description || '').slice(0, 140)) + '</div>' +
          '<div class="btn-row">' +
          '<button class="btn-tiny" data-creator-review="APPROVED" data-creator-package-id="' + esc(p.package_id) + '">Approve</button>' +
          '<button class="btn-tiny" data-creator-review="REJECTED" data-creator-package-id="' + esc(p.package_id) + '">Reject</button>' +
          '</div></div>';
      }).join('') : '<p class="mode-desc">No packages yet in this filter.</p>') +
      '</div>';
  }

  if (s.screen === CREATOR_SCREEN.CAPABILITIES) {
    return '<div class="panel">' + creatorToolbarHtml(true) +
      '<h2 class="panel-title">Registered Capabilities</h2>' +
      '<p class="mode-desc">What is already real and generatable today -- see the Feasibility Engine ' +
      '(Part C) for how a new request maps onto this list.</p>' +
      (s.capabilities || []).map(function (c) {
        return '<div class="creator-queue-row"><b>' + esc(c.category) + '</b> ' + creatorSupportBadgeHtml(c.support_status) +
          '<div class="mode-desc">' + esc(c.mechanic) + ' / ' + esc(c.domain) + ' / ' + esc(c.relationship_predicate) + '</div>' +
          (c.known_limitations.length ? '<ul class="creator-limitations">' + c.known_limitations.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('') + '</ul>' : '') +
          '</div>';
      }).join('') +
      '</div>';
  }

  if (s.screen === CREATOR_SCREEN.CHECKING || s.screen === CREATOR_SCREEN.GENERATING) {
    return '<div class="panel loading-panel" aria-busy="true">' +
      '<div class="loading-spinner"></div>' +
      '<div class="loading-text" aria-live="polite">' + (s.screen === CREATOR_SCREEN.CHECKING ? 'Checking feasibility…' : 'Generating and QA-checking real puzzles…') + '</div></div>';
  }

  // Format Picker pass: a direct taxonomy_id round (creatorGenerateDirect(),
  // POST /v1/creator/format/generate) has no feasibility step at all --
  // it's always SUPPORTED by construction (generate_direct()'s own
  // docstring) -- and its response shape (round_id/taxonomy_id/view) is
  // completely different from the legacy package shape (package_id/
  // questions/puzzles) the block below renders. Handled as its own
  // branch, entirely separate from the Feasibility panel, rather than
  // forcing it through logic that assumes a feasibility result exists.
  if (s.screen === CREATOR_SCREEN.PREVIEW && s.generated && s.generated.round_id) {
    var rg = s.generated;
    var html2 = '<div class="panel">' + creatorToolbarHtml(true) +
      '<h2 class="panel-title">Generated -- ' + esc(rg.taxonomy_id) + '</h2>' +
      '<p class="mode-desc">Round ID: <code>' + esc(rg.round_id) + '</code>' +
      (rg.format_id ? ' &middot; format: ' + esc(rg.format_id) : '') + '</p>' +
      '<p class="mode-desc">This is a real, freshly generated, fully playable round -- generated straight ' +
      'from an explicit taxonomy_id + variant, no natural-language parsing involved. The raw client-safe ' +
      'view below is exactly what a real player’s client would receive (server-authoritative; nothing ' +
      'hidden-until-answered is shown here that wouldn’t also be hidden from a real player).</p>' +
      '<div class="btn-row">' +
      '<button class="btn-primary" data-creator-review="APPROVED" data-creator-package-id="' + esc(rg.round_id) + '">Approve</button>' +
      '<button class="btn-secondary" data-creator-review="REJECTED" data-creator-package-id="' + esc(rg.round_id) + '">Reject</button>' +
      '</div>' +
      '<div class="creator-queue-row"><pre style="white-space:pre-wrap;word-break:break-word;margin:0;">' +
      esc(JSON.stringify(rg.view, null, 2)) + '</pre></div>' +
      '</div>';
    return html2;
  }

  if (s.screen === CREATOR_SCREEN.RESULT || s.screen === CREATOR_SCREEN.PREVIEW) {
    var f = s.feasibility;
    var html = '<div class="panel">' + creatorToolbarHtml(true) +
      '<h2 class="panel-title">Feasibility</h2>' +
      '<p class="mode-desc"><i>' + esc(s.requestText) + '</i></p>' +
      '<div class="btn-row">' + creatorSupportBadgeHtml(f.support_status) + '</div>' +
      '<p class="mode-desc">' + esc(f.reason || '') + '</p>';
    if (f.clarifying_question) html += '<p class="mode-desc"><b>Clarifying question:</b> ' + esc(f.clarifying_question) + '</p>';
    if (f.closest_supported_capability) html += '<p class="mode-desc">Closest supported capability: ' + esc(JSON.stringify(f.closest_supported_capability)) + '</p>';
    if (f.known_limitations && f.known_limitations.length) {
      html += '<ul class="creator-limitations">' + f.known_limitations.map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('') + '</ul>';
    }
    var canGenerate = f.support_status === 'SUPPORTED' || f.support_status === 'SUPPORTED_WITH_LIMITATIONS';
    if (canGenerate && s.screen === CREATOR_SCREEN.RESULT) {
      html += '<div class="btn-row"><button class="btn-primary" data-creator-generate>Generate 5 Real Puzzles</button></div>';
    }
    html += '</div>';

    if (s.screen === CREATOR_SCREEN.PREVIEW && s.generated) {
      var g = s.generated;
      // Real bug found this pass: the 'guess' mechanic's result shape uses
      // questions/question_count, but 'identify_player_from_clues' (NFL/CFB
      // Who Am I) uses puzzles/puzzle_count instead -- this block only ever
      // read the former, so a real, successfully-generated 5-puzzle Who Am I
      // package always displayed as "0 questions" with an empty preview,
      // even though gateway/services/creator.py had genuinely produced real
      // content. Never guess which shape a mechanic uses -- read whichever
      // of the two real fields the response actually populated.
      var items = g.questions || g.puzzles || [];
      var itemCount = (g.question_count != null) ? g.question_count : ((g.puzzle_count != null) ? g.puzzle_count : items.length);
      var itemLabel = g.puzzles ? 'puzzles' : 'questions';
      html += '<div class="panel creator-preview-shell">' +
        '<div class="creator-preview-head"><div><span class="dashboard-eyebrow">PLAYER PREVIEW</span><h2 class="panel-title">' + esc(g.game_title || 'Generated Game') + '</h2></div><div class="creator-preview-toggle"><button class="'+(s.previewMode!=='admin'?'active':'')+'" data-creator-preview-mode="player">Player View</button><button class="'+(s.previewMode==='admin'?'active':'')+'" data-creator-preview-mode="admin">Admin View</button></div></div>' +
        '<div class="btn-row"><button class="btn-secondary" data-creator-regenerate>'+icon('restart')+' Regenerate Fresh Version</button></div>' +
        '<p class="mode-desc">QA: ' + esc(g.qa_status) + ' &middot; ' + itemCount + ' ' + itemLabel + ' &middot; review status: ' + esc(g.review_status) + '</p>';
      if (g.package_id) {
        html += '<div class="btn-row">' +
          '<button class="btn-primary" data-creator-review="APPROVED" data-creator-package-id="' + esc(g.package_id) + '">Approve</button>' +
          '<button class="btn-secondary" data-creator-review="REJECTED" data-creator-package-id="' + esc(g.package_id) + '">Reject</button>' +
          '</div>' +
          '<p class="mode-desc">Approving marks this sample reviewed internally -- it does NOT make a new mode ' +
          'publicly playable by itself. Exposing a capability to real, unauthenticated players is always a ' +
          'separate, deliberate code change (gateway/config.py\'s PUBLIC_MODE_ALLOWLIST), never an automatic ' +
          'result of an admin approving one sample here.</p>';
      }
      if (g.puzzles) {
        // identify_player_from_clues preview: no options/correctIndex exists
        // for this mechanic (it's a progressive clue chain, not multiple
        // choice) -- admin-only view, so showing the real answer alongside
        // its real ordered clues (not hidden, unlike the player-facing
        // renderer) is the honest, useful admin review surface.
        g.puzzles.forEach(function (p, i) {
          html += '<div class="creator-preview-question">' +
            '<div class="quiz-progress">Puzzle ' + (i + 1) + ' of ' + g.puzzles.length + '</div>' +
            '<div class="silhouette-clues">' + p.clues.map(function (c) {
              return '<div class="silhouette-clue">' + esc(c.display_text) + '</div>';
            }).join('') + '</div>' +
            '<div class="quiz-feedback"><b>Answer:</b> ' + esc(p.answer.display_name) + '</div>' +
            '</div>';
        });
      } else {
        items.forEach(function (q, i) {
          var payload = creatorQuestionAsPublicPayload(q);
          html += '<div class="creator-preview-question">' +
            '<div class="creator-preview-question-head"><div class="quiz-progress">Question ' + (i + 1) + ' &middot; ' + esc(q.difficulty || '') + '</div>' +
            '<button class="btn-tiny" data-creator-question-edit="' + i + '">' + (s.editingQuestionIndex === i ? 'Close editor' : 'Edit') + '</button></div>' +
            (s.previewMode === 'admin' ? '<div class="creator-admin-question-meta"><b>Correct:</b> ' + esc(q.options[q.correctIndex] || '') + (q.notes ? '<br><b>Notes:</b> ' + esc(q.notes) : '') + '</div>' : '') +
            '<div class="creator-player-preview">' + renderEnginePilotPromptHtml({ payload: payload }) +
            '<div class="quiz-options">' + q.options.map(function (opt, oi) {
              return '<div class="quiz-option' + (s.previewMode === 'admin' && oi === q.correctIndex ? ' correct' : '') + '" style="cursor:default;">' +
                String.fromCharCode(65 + oi) + '. ' + esc(opt) + '</div>';
            }).join('') + '</div></div>' +
            (s.editingQuestionIndex === i ? creatorQuestionEditorHtml(q, i) : '') +
            '</div>';
        });
      }
      html += '</div>';
    }
    return html;
  }

  // HOME
  var directCount = CREATOR_FORMAT_CATALOG.filter(function (x) { return !!x.taxonomyId; }).length;
  var guidedCount = CREATOR_FORMAT_CATALOG.length - directCount;
  return '<div class="creator-workspace">' + creatorToolbarHtml(false) +
    '<section class="creator-hero">' +
      '<div><span class="dashboard-eyebrow">GAME FACTORY</span><h1>Build football games without fighting the engine.</h1><p>Describe an idea in plain English or jump straight into a proven format. Reads handles feasibility, generation, QA and review.</p></div>' +
      '<div class="creator-hero-stats"><span><b>' + CREATOR_FORMAT_CATALOG.length + '</b>Formats</span><span><b>' + directCount + '</b>Direct</span><span><b>' + guidedCount + '</b>Guided</span></div>' +
    '</section>' +
    '<section class="creator-compose-card">' +
      '<div class="creator-compose-head"><div><span class="dashboard-eyebrow">DESCRIBE IT</span><h2>What do you want to build?</h2></div><span class="creator-step-chip">1 · Describe</span></div>' +
      '<textarea id="creator-request-input" class="creator-textarea creator-prompt-box" rows="4" placeholder="Example: Give me a game where I rank NFL quarterbacks by career passing touchdowns.">' + esc(s.requestText || '') + '</textarea>' +
      '<div class="creator-compose-footer"><div class="creator-example-row">' + CREATOR_EXAMPLE_PROMPTS.slice(0, 3).map(function (ex) { return '<button data-creator-example="' + esc(ex) + '">' + esc(ex) + '</button>'; }).join('') + '</div>' +
      '<button class="btn-primary creator-check-btn" data-creator-check-feasibility>' + icon('zap') + ' Check & Build</button></div>' +
    '</section>' +
    creatorGuidedBuilderHtml() +
    '<div class="creator-divider"><span>OR START FROM A PROVEN FORMAT</span></div>' +
    renderCreatorFormatPickerHtml() +
    '</div>';
}