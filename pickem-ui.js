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
    seasonRecord: null,
  };
  state.screen = 'pickem';
  renderAll();
  loadPickemView();
  loadPickemSeasonRecord();
}

// User request: "keep a record of your pick em's throughout the season so
// u can compete with other users." A season record aggregates every real
// concluded week (heavier than the single-week view above), so it's
// fetched once per round start and again after a pick actually changes it
// -- never on every loadPickemView() slate-switch, which doesn't affect
// the season total at all. Pushed to the same existing Firestore
// leaderboard every other mode already uses (app.js's pushLeaderboard) --
// no new cross-device sync mechanism.
function loadPickemSeasonRecord() {
  var s = state.pickem;
  if (!s) return;
  enginePilotFetchJson('/v1/public/pickem/' + s.league.toLowerCase() + '/record?client_id=' + encodeURIComponent(getClientId())).then(function (record) {
    if (state.pickem !== s) return;
    s.seasonRecord = record;
    if (record.total_graded) {
      // Whole-number percentage (0-100), matching every other leaderboard
      // mode's own bestPct convention (e.g. finishQuizRound() in app.js) --
      // the backend's win_pct is a 0-1 fraction, only converted here.
      pushLeaderboard(s.league === 'NFL' ? 'pickemNfl' : 'pickemCfb', {
        winPct: Math.round(record.win_pct * 100), correctCount: record.total_correct,
        gradedCount: record.total_graded, weeksPlayed: record.weeks_played,
      });
    }
    applyPickemWeeksToRating(s.league, record.season, record.per_week);
    renderAll();
  }).catch(function () {
    // Real, non-critical background fetch -- the weekly slate above is
    // still fully playable without a season record, so this fails silently
    // rather than surfacing a second error banner on top of loadPickemView()'s.
  });
}

// User request: "let's make sure that all game modes are connected to
// your Football score." Pick'em's real shape doesn't fit a single "session
// just ended" moment the way trivia does -- picks grade asynchronously as
// real games conclude over hours/days, and this same season record gets
// re-fetched every time the Pick'em screen loads. Counting every fetch
// would apply the same real week's result to rating over and over. Fixed
// by tracking which real (league, season, week) results have already been
// applied, in localStorage, and only feeding NEWLY concluded weeks --
// each real week's own graded_count/correct_count contributes exactly
// once, the same real-quiz-accuracy semantics as every other mode.
function pickemRatedWeeksKey(league, season) { return 'nflTriviaPickemRatedWeeks__' + league + '__' + season; }
function applyPickemWeeksToRating(league, season, perWeek) {
  if (!perWeek || !perWeek.length) return;
  var key = pickemRatedWeeksKey(league, season);
  var already = lsGet(key, []);
  var alreadySet = {};
  already.forEach(function (w) { alreadySet[w] = true; });
  var newlyRated = already.slice();
  perWeek.forEach(function (w) {
    if (alreadySet[w.week] || !w.graded_count) return;
    updateRatingDrift(100 * w.correct_count / w.graded_count);
    newlyRated.push(w.week);
  });
  if (newlyRated.length !== already.length) lsSet(key, newlyRated);
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
    loadPickemSeasonRecord();
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
    renderPickemSeasonRecordHtml(s) +
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

// Season-long record display -- real, aggregated win/loss across every
// concluded real week (loadPickemSeasonRecord() above), not this week's
// slate alone. Hidden until at least one real week has been graded so a
// brand-new player never sees a hollow "0-0" line.
function renderPickemSeasonRecordHtml(s) {
  var r = s.seasonRecord;
  if (!r || !r.total_graded) return '';
  var pct = Math.round(r.win_pct * 100);
  // "correct/graded" rather than a "W-L" record -- graded_count includes
  // real TIE outcomes (mechanic_engine.py), which aren't losses; this
  // stays accurate without needing a 3rd tie-count field from the backend.
  return '<div class="status-line">' + icon('trophy') + ' Season record: ' + r.total_correct + '/' + r.total_graded +
    ' correct (' + pct + '%) across ' + r.weeks_played + ' week' + (r.weeks_played === 1 ? '' : 's') + '</div>';
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

// Real bug fix: this used to be `new Date(g.kickoff).toLocaleString(...)`
// unconditionally. When the server sent a date-only value ('2026-09-13',
// no real time-of-day -- the shape every kickoff used to be sent in before
// this fix), JS parses that as UTC MIDNIGHT, and toLocaleString() then
// renders it in the BROWSER'S LOCAL timezone -- for every real US
// timezone (all behind UTC), that rolls the displayed calendar day back
// by one whenever local midnight hasn't yet reached the next UTC day
// (e.g. a real Sunday game showed as "today" on Saturday evening). The
// server now sends a real, honest `kickoff_has_time` flag alongside every
// game (tools/director_v04/weekly_pickem.py) -- true only when the value
// actually carries a genuine time-of-day. When true, real local-time
// conversion is correct and wanted (a player should see kickoff in THEIR
// own local time). When false, this renders the real calendar date using
// UTC-based date parts (never local getters), so a fake attached midnight
// can never shift the real day, and never fabricates a clock time that
// was never real to begin with.
function formatPickemKickoff(kickoffRaw, hasTime) {
  if (!kickoffRaw) return '';
  var d = new Date(kickoffRaw);
  if (isNaN(d.getTime())) return '';
  if (hasTime) {
    return d.toLocaleString([], { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  }
  // Date-only real value -- format the real calendar date from UTC parts
  // only (a local getter here would reintroduce the exact same
  // day-rollback bug this function exists to fix).
  var weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return weekdays[d.getUTCDay()] + ', ' + months[d.getUTCMonth()] + ' ' + d.getUTCDate();
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

  var kickoffText = formatPickemKickoff(g.kickoff, g.kickoff_has_time);
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
