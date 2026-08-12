// Reads Six Degrees -- public engine-backed game shell (v1.7, Part C).
//
// A SEPARATE small module from engine-game-ui.js (not shoehorned into it):
// the mechanic here is genuinely different -- a multi-step chain within one
// round, not one question per fetch -- even though it reuses the exact same
// design principles (named state model, never-trust-the-client answer
// validation, polished user-facing copy, no raw backend errors) v1.5
// established for Draft/Championship. Loaded the same way engine-game-ui.js
// is: before app.js, since app.js's own bootstrap reads this file's mode
// registry at its top level (see index.html).
//
// Real, checked content today (gateway/services/public_six_degrees.py's own
// module docstring): every certified puzzle is a two-NFL-team connection
// through a shared coach -- narrow, but 100% real, never fabricated. The
// public-facing copy below reflects that honestly ("Coach Connections"),
// never oversells it as a rich, varied "six degrees of separation" search
// experience the current certified content doesn't actually have.

var SIX_DEGREES_SCREEN = {
  LOADING: 'loading',
  STEP_READY: 'step',
  SUBMITTING: 'submitting',
  STEP_RESULT: 'step_result',   // just answered this step -- correct or not
  COMPLETE: 'complete',          // reached the end
  LOST: 'lost',                  // wrong answer, attempt over
  ERROR: 'error',
};

var SIX_DEGREES_ERROR_COPY = {
  NO_ELIGIBLE_GAME: "We couldn't find a new puzzle right now.",
  SERVICE_UNAVAILABLE: 'This game is temporarily unavailable.',
  INVALID_GAME_ID: "That puzzle expired — let's get you a new one.",
  CLIENT_TIMEOUT: "That took too long to load — check your connection and try again.",
};
var SIX_DEGREES_ERROR_DEFAULT = "Couldn't load that — please try again.";
function sixDegreesUserFacingError(err) {
  var code = err && err.code;
  return (code && SIX_DEGREES_ERROR_COPY[code]) || SIX_DEGREES_ERROR_DEFAULT;
}

var SIX_DEGREES_FETCH_TIMEOUT_MS = 10000;
function sixDegreesFetchJson(path, options) {
  var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
  var timeoutId = controller ? setTimeout(function () { controller.abort(); }, SIX_DEGREES_FETCH_TIMEOUT_MS) : null;
  var opts = options ? Object.assign({}, options) : {};
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
      var timeoutErr = new Error('Client-side fetch timeout after ' + SIX_DEGREES_FETCH_TIMEOUT_MS + 'ms.');
      timeoutErr.code = 'CLIENT_TIMEOUT';
      throw timeoutErr;
    }
    throw err;
  });
}

function startSixDegreesRound() {
  state.sixDegrees = { screen: SIX_DEGREES_SCREEN.LOADING, pickedIndex: null, lastResult: null, error: null };
  state.screen = 'sixDegrees';
  renderAll();
  loadSixDegreesGame();
}
function loadSixDegreesGame() {
  var s = state.sixDegrees;
  if (!s) return;
  s.screen = SIX_DEGREES_SCREEN.LOADING;
  s.error = null;
  renderAll();
  sixDegreesFetchJson('/v1/public/six_degrees/game')
    .then(function (game) {
      if (state.sixDegrees !== s) return;
      s.game = game;
      s.pickedIndex = null;
      s.lastResult = null;
      s.screen = SIX_DEGREES_SCREEN.STEP_READY;
      renderAll();
    })
    .catch(function (err) {
      if (state.sixDegrees !== s) return;
      s.screen = SIX_DEGREES_SCREEN.ERROR;
      s.error = sixDegreesUserFacingError(err);
      renderAll();
    });
}
function pickSixDegreesOption(optionIndex) {
  var s = state.sixDegrees;
  if (!s || s.screen !== SIX_DEGREES_SCREEN.STEP_READY || s.pickedIndex !== null) return;
  s.pickedIndex = optionIndex;
  s.screen = SIX_DEGREES_SCREEN.SUBMITTING;
  renderAll();
  sixDegreesFetchJson('/v1/public/six_degrees/answer', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: s.game.game_id, step_index: s.game.step_index, choice_index: optionIndex }),
  }).then(function (result) {
    if (state.sixDegrees !== s) return;
    s.lastResult = result;
    playSound(result.last_correct ? 'correct' : 'wrong');
    if (result.last_correct && !result.completed) {
      // Real bug found by actually tracing a live answer response: the
      // Gateway's answer contract already advances step_index/current/options
      // to the NEXT step in this same response (see public_six_degrees.py's
      // submit_public_six_degrees_answer() -> _public_step_view()). Assigning
      // it straight to s.game here (the old code) made the "Correct!"
      // celebration render on top of the WRONG question -- the one the
      // player hasn't attempted yet, with its buttons disabled and nothing
      // showing what was actually just answered. Stashing it as s.nextGame
      // instead, and only promoting it to s.game when the player clicks
      // "Next Move" (continueSixDegreesAfterStep, below), keeps the
      // STEP_RESULT screen showing the step that was actually just solved.
      s.nextGame = result;
      s.screen = SIX_DEGREES_SCREEN.STEP_RESULT;
    } else if (result.completed && result.last_correct) {
      s.screen = SIX_DEGREES_SCREEN.COMPLETE;
    } else {
      s.screen = SIX_DEGREES_SCREEN.LOST;
    }
    renderAll();
  }).catch(function (err) {
    if (state.sixDegrees !== s) return;
    s.screen = SIX_DEGREES_SCREEN.ERROR;
    s.error = sixDegreesUserFacingError(err);
    renderAll();
  });
}
function continueSixDegreesAfterStep() {
  var s = state.sixDegrees;
  if (!s) return;
  if (s.nextGame) { s.game = s.nextGame; s.nextGame = null; }
  s.pickedIndex = null;
  s.lastResult = null;
  s.screen = SIX_DEGREES_SCREEN.STEP_READY;
  renderAll();
}
function revealSixDegrees() {
  var s = state.sixDegrees;
  if (!s || !s.game) return;
  sixDegreesFetchJson('/v1/public/six_degrees/reveal', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: s.game.game_id }),
  }).then(function (reveal) {
    if (state.sixDegrees !== s) return;
    s.reveal = reveal;
    renderAll();
  }).catch(function () {
    // Reveal is a nice-to-have on an already-lost attempt -- a failure here
    // shouldn't block the player from exiting/retrying, so it fails silent
    // rather than routing to the shared ERROR screen.
  });
}
function sixDegreesFallback() {
  state.sixDegrees = null;
  state.screen = 'quiz';
  startQuizRound('', '', 10);
}
function sixDegreesToolbarHtml() {
  return '<div class="mode-toolbar">' +
    '<button class="btn-tiny" data-mode-exit>' + icon('close') + ' Exit to Home</button>' +
    '</div>';
}
function renderSixDegreesScreen() {
  if (!ENABLE_ENGINE_SIX_DEGREES_V01) return renderHome();
  var s = state.sixDegrees;
  if (!s) {
    return '<div class="panel">' +
      '<h2 class="panel-title">Coach Connections</h2>' +
      '<p class="mode-desc">Two NFL teams, one coach who led them both. Figure out the connection.</p>' +
      '<div class="btn-row"><button class="btn-primary" data-sixdegrees-start>Start</button></div>' +
      '</div>';
  }
  if (s.screen === SIX_DEGREES_SCREEN.LOADING) {
    return '<div class="panel">' + sixDegreesToolbarHtml() + '<p class="mode-desc" aria-live="polite">Finding a connection&hellip;</p></div>';
  }
  if (s.screen === SIX_DEGREES_SCREEN.ERROR) {
    return '<div class="panel">' + sixDegreesToolbarHtml() +
      '<p class="mode-desc" aria-live="assertive">' + esc(s.error) + '</p>' +
      '<div class="btn-row">' +
      '<button class="btn-primary" data-sixdegrees-retry>Try Again</button>' +
      '<button class="btn-secondary" data-sixdegrees-fallback>Play Quiz Instead</button>' +
      '</div></div>';
  }
  if (s.screen === SIX_DEGREES_SCREEN.COMPLETE) {
    return '<div class="panel">' + sixDegreesToolbarHtml() +
      '<h2 class="panel-title">' + icon('check') + ' Solved it!</h2>' +
      '<p class="summary-note">' + esc(s.game.start.name) + ' &rarr; ' + esc(s.game.end.name) + ' in ' + esc(String(s.game.par)) + ' move' + (s.game.par === 1 ? '' : 's') + '.</p>' +
      '<div class="btn-row"><button class="btn-primary" data-sixdegrees-start>Play Again</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  if (s.screen === SIX_DEGREES_SCREEN.LOST) {
    return '<div class="panel">' + sixDegreesToolbarHtml() +
      '<h2 class="panel-title">' + icon('xMark') + ' Not quite</h2>' +
      '<p class="mode-desc">The correct connection was <b>' + esc(s.lastResult.last_correct_name) + '</b>.</p>' +
      (s.reveal
        ? '<div class="summary-note">Full chain: ' + esc(s.reveal.solution_names.join(' → ')) + '</div>'
        : '<div class="btn-row"><button class="btn-secondary" data-sixdegrees-reveal>Show Full Answer</button></div>') +
      '<div class="btn-row">' +
      '<button class="btn-primary" data-sixdegrees-start>Play Again</button>' +
      '<button class="btn-secondary" data-go="home">Home</button>' +
      '</div></div>';
  }
  // STEP_READY, SUBMITTING, and STEP_RESULT all share the question layout --
  // same pattern engine-game-ui.js's own renderEnginePilotScreen() uses for
  // its analogous states.
  var game = s.game;
  var submitting = s.screen === SIX_DEGREES_SCREEN.SUBMITTING;
  var justAnswered = s.screen === SIX_DEGREES_SCREEN.STEP_RESULT;
  return '<div class="panel">' + sixDegreesToolbarHtml() +
    '<div class="quiz-progress">' + esc(game.start.name) + ' &rarr; ' + esc(game.end.name) + ' &middot; Move ' + (game.step_index + 1) + ' of ' + game.par + '</div>' +
    '<div class="quiz-question">Who connects to <b>' + esc(game.current.name) + '</b>?</div>' +
    '<div class="quiz-options">' +
    game.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (i === s.pickedIndex) {
        // STEP_RESULT is only ever reached via a CORRECT answer (a wrong
        // one routes straight to LOST, never here) -- so the picked option
        // is always the right one at this point, matching engine-game-ui.js's
        // own .correct convention rather than the in-flight-only .selected.
        if (submitting) cls += ' selected';
        else if (justAnswered) cls += ' correct';
      }
      return '<button class="' + cls + '" ' + (s.screen === SIX_DEGREES_SCREEN.STEP_READY ? 'data-sixdegrees-answer="' + i + '"' : 'disabled') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (submitting ? '<div class="quiz-progress" aria-live="polite">Checking your answer&hellip;</div>' : '') +
    (justAnswered
      ? '<div class="quiz-feedback" aria-live="polite"><span class="feedback-good">' + icon('check') + ' Correct! On to the next move.</span></div>' +
        '<button class="btn-primary" data-sixdegrees-continue>Next Move</button>'
      : '') +
    '</div>';
}
