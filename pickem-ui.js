// Weekly Pick'em Player Experience pass -- real, public NFL/CFB slate
// screen. Own file (not folded into engine-game-ui.js) because Pick'em's
// real shape -- a whole week's slate of games, each independently
// picked/locked/graded -- doesn't fit that file's ENGINE_GAME_SCREEN
// one-question-at-a-time state machine. Reuses enginePilotFetchJson()
// as-is (already fully generic: only touches ENGINE_GATEWAY_BASE_URL, has
// zero engine-pilot-specific logic in its body) rather than writing a
// second fetch wrapper, and reuses app.js's real, existing CSS classes
// (.panel/.chip-row/.chip-toggle/.quiz-options/.quiz-option/.btn-row/
// .status-line/.quiz-feedback) exclusively -- no new visual language.
//
// getClientId() (app.js) is threaded into every fetch here -- this is the
// first real caller sending it to the Gateway (it previously only ever
// built a Firestore leaderboard doc ID client-side).
//
// Never reveals a score/winner before a game's real status is FINAL --
// the server (gateway/services/public_pickem.py -> mechanic_engine.py)
// already enforces this in the view it returns; this file never guesses
// or fills in a result on its own.

var PICKEM_SLATE_LABELS = {
  FEATURED: 'Featured', TOP25: 'Top 25', POWER4: 'Power Four', CONFERENCE: 'Conference', FULL: 'Full Slate',
};
var PICKEM_CONFERENCES = ['SEC', 'Big Ten', 'Big 12', 'ACC', 'Pac-12', 'American Athletic', 'Mountain West',
  'Conference USA', 'Mid-American', 'Sun Belt'];
var PICKEM_ERROR_COPY = {
  NO_ELIGIBLE_GAME: "No real games found for this slate/week yet.",
  INVALID_REQUEST: "That pick couldn't be saved — the game may already be locked.",
};
var PICKEM_OUTCOME_COPY = {
  CORRECT: 'Correct!', INCORRECT: 'Incorrect', TIE: 'Tie', VOID: 'Voided — game canceled',
  PENDING: 'Locked in — grades once final',
};

function pickemUserFacingError(err) {
  var code = err && err.code;
  return (code && PICKEM_ERROR_COPY[code]) || (code && typeof ENGINE_GAME_ERROR_COPY !== 'undefined' && ENGINE_GAME_ERROR_COPY[code]) ||
    (typeof ENGINE_GAME_ERROR_DEFAULT !== 'undefined' ? ENGINE_GAME_ERROR_DEFAULT : "Couldn't load that — please try again.");
}

function startPickemRound(league) {
  state.pickem = {
    league: league, screen: 'LOADING', season: null, week: null,
    slate: league === 'CFB' ? 'FEATURED' : 'FULL', conference: null,
    view: null, pendingPickGameId: null, lastPickError: null, error: null,
  };
  state.screen = 'pickem';
  renderAll();
  loadPickemView();
}

function pickemPath(s) {
  var base = '/v1/public/pickem/' + s.league.toLowerCase() + (s.season && s.week ? '/' + s.season + '/' + s.week : '');
  var params = ['client_id=' + encodeURIComponent(getClientId())];
  if (s.league === 'CFB') {
    params.push('slate=' + encodeURIComponent(s.slate));
    if (s.slate === 'CONFERENCE' && s.conference) params.push('conference=' + encodeURIComponent(s.conference));
  }
  return base + '?' + params.join('&');
}

function loadPickemView() {
  var s = state.pickem;
  if (!s) return;
  s.screen = 'LOADING';
  s.error = null;
  renderAll();
  enginePilotFetchJson(pickemPath(s)).then(function (result) {
    if (state.pickem !== s) return; // navigated away mid-flight
    s.season = result.season;
    s.week = result.week;
    if (result.slate) s.slate = result.slate; // echoes the server-resolved default (e.g. FEATURED) back
    s.view = result.view;
    s.screen = 'READY';
    renderAll();
  }).catch(function (err) {
    if (state.pickem !== s) return;
    s.error = { code: err && err.code, text: pickemUserFacingError(err) };
    s.screen = 'ERROR';
    renderAll();
  });
}

function changePickemSlate(newSlate, conference) {
  var s = state.pickem;
  if (!s || s.league !== 'CFB') return;
  s.slate = newSlate;
  s.conference = newSlate === 'CONFERENCE' ? (conference || s.conference || PICKEM_CONFERENCES[0]) : null;
  loadPickemView();
}

function submitPickemPick(gameId, teamCode) {
  var s = state.pickem;
  if (!s || s.pendingPickGameId || !s.season || !s.week) return;
  s.pendingPickGameId = gameId;
  s.lastPickError = null;
  renderAll();
  enginePilotFetchJson('/v1/public/pickem/' + s.league.toLowerCase() + '/' + s.season + '/' + s.week + '/pick', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: getClientId(), game_id: gameId, predicted_winner: teamCode }),
  }).then(function () {
    if (state.pickem !== s) return;
    s.pendingPickGameId = null;
    loadPickemView();
  }).catch(function (err) {
    if (state.pickem !== s) return;
    s.pendingPickGameId = null;
    s.lastPickError = pickemUserFacingError(err);
    renderAll();
  });
}

// Section 8 (Pick'em completion): a real per-outcome breakdown computed
// from the actual per-game `outcome` field already in the view -- never a
// second server call, never fabricated. Used both for the completion
// banner/screen and (games.length && graded_count===0-safe) nowhere else.
function pickemOutcomeCounts(games) {
  var counts = { CORRECT: 0, INCORRECT: 0, TIE: 0, VOID: 0, PENDING: 0, unpicked: 0 };
  games.forEach(function (g) {
    if (!g.your_pick) { counts.unpicked++; return; }
    if (g.outcome && counts.hasOwnProperty(g.outcome)) counts[g.outcome]++;
  });
  return counts;
}

function renderPickemScreen() {
  var s = state.pickem;
  if (!s) return '';
  var leagueTitle = s.league === 'NFL' ? "NFL Pick'em" : "CFB Pick'em";
  if (s.screen === 'LOADING') {
    return '<div class="panel loading-panel" aria-busy="true">' +
      renderReadsShellHeader({ icon: 'versus', title: leagueTitle }) +
      '<div class="status-line">Loading this week\'s slate…</div></div>';
  }
  if (s.screen === 'ERROR') {
    return '<div class="panel">' + renderReadsShellHeader({ icon: 'versus', title: leagueTitle }) +
      '<div class="quiz-feedback">' + esc(s.error.text) + '</div>' +
      '<div class="btn-row"><button class="btn-primary" data-pickem-retry>Try Again</button>' +
      '<button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  var v = s.view;
  var allGraded = v.game_count > 0 && v.graded_count === v.game_count;
  var headerOpts = {
    icon: 'versus',
    title: leagueTitle + ' · ' + esc(String(v.season)) + ', Week ' + esc(String(v.week)),
    score: v.picks_made + '/' + v.game_count + ' picked',
  };
  if (v.graded_count > 0) headerOpts.badge = v.correct_count + '/' + v.graded_count + ' correct';
  if (s.league === 'CFB') headerOpts.difficulty = PICKEM_SLATE_LABELS[s.slate];
  var header = '<div class="panel">' + renderReadsShellHeader(headerOpts) +
    (s.league === 'CFB' ? renderPickemSlateChips(s) : '') +
    (s.lastPickError ? '<div class="quiz-feedback">' + esc(s.lastPickError) + '</div>' : '') +
    (allGraded ? renderPickemCompletionSummary(v) : '') +
    '</div>';
  var cards = v.games.map(function (g) { return pickemGameCardHtml(g, s); }).join('');
  return header + cards + '<div class="btn-row"><button class="btn-secondary" data-go="home">Exit to Home</button></div>';
}

// Section 8: shown once every game on the current slate view has a real
// final grade (VOID counts as graded -- mechanic_engine.py already treats
// it as terminal). This is per-SLATE-VIEW, not per-week -- switching to a
// narrower/wider slate recomputes it from that view's own games, which is
// the same "always derived from the current real view, never cached"
// discipline weekly_pickem.py itself already follows.
function renderPickemCompletionSummary(v) {
  var counts = pickemOutcomeCounts(v.games);
  return '<div class="pickem-complete">' +
    '<div class="pickem-complete-title">' + icon('check') + ' Slate graded</div>' +
    '<div class="pickem-complete-stats">' +
    '<span class="pickem-complete-stat pickem-complete-good">' + counts.CORRECT + ' correct</span>' +
    '<span class="pickem-complete-stat pickem-complete-bad">' + counts.INCORRECT + ' incorrect</span>' +
    (counts.TIE ? '<span class="pickem-complete-stat">' + counts.TIE + ' tie</span>' : '') +
    (counts.VOID ? '<span class="pickem-complete-stat">' + counts.VOID + ' void</span>' : '') +
    (counts.unpicked ? '<span class="pickem-complete-stat">' + counts.unpicked + ' not picked</span>' : '') +
    '</div></div>';
}

function renderPickemSlateChips(s) {
  var chips = ['FEATURED', 'TOP25', 'POWER4', 'CONFERENCE', 'FULL'].map(function (slate) {
    return '<button class="chip-toggle' + (s.slate === slate ? ' active' : '') + '" data-pickem-slate="' + slate + '">' +
      esc(PICKEM_SLATE_LABELS[slate]) + '</button>';
  }).join('');
  var confPicker = '';
  if (s.slate === 'CONFERENCE') {
    confPicker = '<div class="chip-row">' + PICKEM_CONFERENCES.map(function (c) {
      return '<button class="chip-toggle' + (s.conference === c ? ' active' : '') + '" data-pickem-conference="' + esc(c) + '">' +
        esc(c) + '</button>';
    }).join('') + '</div>';
  }
  return '<div class="chip-row">' + chips + '</div>' + confPicker;
}

// Section: Weekly Pick'em real matchup presentation. Reuses the shared
// binary-choice component (app.js) instead of a bespoke Pick'em-only
// component -- a Pick'em pick IS a two-sided selection, the same shape
// nflGameResult/cfbGameResult already use, just persisted server-side
// instead of graded inline. data-pickem-game/data-pickem-team stay as the
// two data attributes the existing click handler already reads -- this is
// a presentation change only, zero click-wiring/state-shape change.
function pickemGameCardHtml(g, s) {
  var isFinal = g.status === 'FINAL';
  var isLocked = isFinal || ['IN_PROGRESS', 'POSTPONED', 'CANCELED'].indexOf(g.status) >= 0;
  var disabled = isLocked || s.pendingPickGameId === g.game_id;

  function side(code, label, isHome) {
    var st = 'default';
    if (g.your_pick === code) st = isFinal ? (g.winner === code ? 'correct' : 'wrong') : 'selected';
    else if (isFinal && g.winner === code) st = 'correct';
    return {
      code: code, label: label,
      sublabel: isHome ? 'Home' : 'Away',
      reveal: isFinal ? String(isHome ? g.home_score : g.away_score) : null,
      state: st,
    };
  }

  var kickoffText = g.kickoff ? new Date(g.kickoff).toLocaleString([], { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '';
  var statusChip = isFinal
    ? '<span class="pickem-status-chip pickem-status-final">' + icon('check') + ' FINAL</span>'
    : isLocked
      ? '<span class="pickem-status-chip pickem-status-locked">' + icon('lock') + ' Locked</span>'
      : '<span class="pickem-status-chip">' + icon('timer') + ' ' + esc(kickoffText) + '</span>';

  var outcomeText = g.your_pick && g.outcome ? PICKEM_OUTCOME_COPY[g.outcome] : null;
  var outcome = outcomeText ? '<div class="quiz-feedback">' + esc(outcomeText) + '</div>' : '';

  return '<div class="panel pickem-game-card">' +
    '<div class="pickem-game-status-row">' + statusChip + '</div>' +
    renderBinaryChoiceHtml(
      side(g.away_team_code, g.away_team, false),
      side(g.home_team_code, g.home_team, true),
      { dataAttr: 'data-pickem-team', disabled: disabled, extraAttrs: 'data-pickem-game="' + esc(g.game_id) + '"' }
    ) +
    outcome +
    '</div>';
}
