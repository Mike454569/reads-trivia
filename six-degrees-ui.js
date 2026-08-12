// Reads Coach Connections v2 -- public engine-backed game shell.
//
// A SEPARATE small module from engine-game-ui.js (not shoehorned into it):
// the mechanic here is genuinely different -- a multi-step, open-ended
// graph chain within one round, not one question per fetch.
//
// v2 rebuild (real graph-driven generation replacing the old 23-puzzle
// graph_path_cache -- see gateway/services/public_coach_connections.py and
// coach_connections_graph.py's module docstrings for the full data story).
// Mechanic changed to match: free-text search/autocomplete instead of a
// fixed 4-option list (the certified graph supports far more real moves per
// node than 4 could ever represent), and progressive reveal -- only nodes
// the player has actually reached are ever shown, never a hidden future
// step. Every move is checked against the LIVE graph server-side, so more
// than one real path can finish the same puzzle.
//
// Filename/function names kept the same as v1 (startSixDegreesRound,
// renderSixDegreesScreen, state.sixDegrees, the data-sixdegrees-* hook
// prefix, state.screen === 'sixDegrees') so app.js's existing wiring
// (goToMode, the click/input/keydown delegates, ENGINE_DISCOVERY_ENTRIES)
// needed only the small, real routing changes described where they occur,
// not a repo-wide rename -- the mechanic is what changed, not the plumbing
// around it.

var SIX_DEGREES_SCREEN = {
  LOADING: 'loading',
  PLAYING: 'playing',   // covers in-progress, completed, and out-of-moves -- game.completed/game.out_of_moves (both real, server-computed) distinguish those, not separate client screen states that could drift out of sync with the server.
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
  var prevSeen = (state.sixDegrees && state.sixDegrees.seenGameIds) || [];
  state.sixDegrees = {
    screen: SIX_DEGREES_SCREEN.LOADING, game: null, error: null, reveal: null, gaveUp: false,
    seenGameIds: prevSeen, searchQuery: '', searchResults: [], searching: false,
    moveFeedback: null,
  };
  state.screen = 'sixDegrees';
  renderAll();
  loadSixDegreesGame();
}
function loadSixDegreesGame() {
  var s = state.sixDegrees;
  if (!s) return;
  s.screen = SIX_DEGREES_SCREEN.LOADING;
  s.error = null;
  s.reveal = null;
  s.gaveUp = false;
  s.searchQuery = '';
  s.searchResults = [];
  s.moveFeedback = null;
  renderAll();
  // Part 12 (replayability): exclude recently-served puzzles' (start,end)
  // pairs, same in-session "client sends back its own recent ids" pattern
  // engine-game-ui.js's seenGameIds already uses for Draft/Championship --
  // deliberately in-memory only (resets on reload), not a new persistent
  // mechanism.
  var exclude = s.seenGameIds.slice(-20).join(',');
  sixDegreesFetchJson('/v1/public/coach_connections/game' + (exclude ? '?exclude=' + encodeURIComponent(exclude) : ''))
    .then(function (game) {
      if (state.sixDegrees !== s) return;
      s.game = game;
      s.seenGameIds.push(game.game_id);
      s.screen = SIX_DEGREES_SCREEN.PLAYING;
      renderAll();
      sixDegreesFocusSearchInput();
    })
    .catch(function (err) {
      if (state.sixDegrees !== s) return;
      s.screen = SIX_DEGREES_SCREEN.ERROR;
      s.error = sixDegreesUserFacingError(err);
      renderAll();
    });
}

function sixDegreesFocusSearchInput() {
  var el = document.getElementById('sixdegrees-search-input');
  if (el) el.focus();
}

// Debounced, server-backed autocomplete -- deliberately NOT the synchronous
// TYPEAHEAD_CONFIGS/typeaheadMatches system used by Grid/Silhouette/Player
// Clues (those filter a small pool already loaded client-side; the graph
// here has hundreds of thousands of real nodes, which never ships to the
// browser -- see coach_connections_graph.py's module docstring on why the
// full relationship graph is never sent to the frontend). Debounce keeps
// this from firing a real request on every single keystroke.
var sixDegreesSearchDebounceHandle = null;
function sixDegreesOnSearchInput(value) {
  var s = state.sixDegrees;
  if (!s) return;
  s.searchQuery = value;
  if (sixDegreesSearchDebounceHandle) clearTimeout(sixDegreesSearchDebounceHandle);
  if (!value || value.trim().length < 2) {
    s.searchResults = [];
    s.searching = false;
    sixDegreesRenderSearchResultsOnly();
    return;
  }
  s.searching = true;
  sixDegreesSearchDebounceHandle = setTimeout(function () { sixDegreesRunSearch(value); }, 220);
}
function sixDegreesRunSearch(value) {
  var s = state.sixDegrees;
  if (!s || s.searchQuery !== value) return;
  sixDegreesFetchJson('/v1/public/coach_connections/search?q=' + encodeURIComponent(value.trim()))
    .then(function (resp) {
      if (state.sixDegrees !== s || s.searchQuery !== value) return;
      s.searchResults = resp.results || [];
      s.searching = false;
      sixDegreesRenderSearchResultsOnly();
    })
    .catch(function () {
      if (state.sixDegrees !== s) return;
      s.searchResults = [];
      s.searching = false;
      sixDegreesRenderSearchResultsOnly();
    });
}
// Writes directly into the results <div> rather than calling renderAll() --
// same "don't steal focus / rebuild the whole screen per keystroke"
// technique the existing typeahead system already uses (see its own module
// comment, above renderTypeahead in app.js).
function sixDegreesRenderSearchResultsOnly() {
  var listEl = document.getElementById('sixdegrees-search-results');
  if (!listEl) return;
  var s = state.sixDegrees;
  if (s.searching) {
    listEl.innerHTML = '<div class="typeahead-row" aria-disabled="true">Searching&hellip;</div>';
    listEl.classList.add('open');
    return;
  }
  if (!s.searchResults.length) {
    listEl.innerHTML = '';
    listEl.classList.remove('open');
    return;
  }
  listEl.innerHTML = s.searchResults.map(function (r, i) {
    return '<button type="button" role="option" class="typeahead-row' + (i === 0 ? ' active' : '') + '" ' +
      'data-sixdegrees-pick-type="' + esc(r.type) + '" data-sixdegrees-pick-id="' + esc(r.id) + '" data-sixdegrees-pick-name="' + esc(r.name) + '">' +
      esc(r.name) + ' <span class="typeahead-hint">' + esc(sixDegreesNodeTypeLabel(r.type)) + '</span></button>';
  }).join('');
  listEl.classList.add('open');
}
function sixDegreesNodeTypeLabel(type) {
  if (type === 'coach') return 'Coach';
  if (type === 'team') return 'Team';
  return 'Player';
}
function sixDegreesPickTopResult() {
  var s = state.sixDegrees;
  if (!s || !s.searchResults.length) return;
  var top = s.searchResults[0];
  submitSixDegreesMove(top.type, top.id, top.name);
}
function sixDegreesCloseSearch() {
  var s = state.sixDegrees;
  if (!s) return;
  s.searchResults = [];
  var listEl = document.getElementById('sixdegrees-search-results');
  if (listEl) { listEl.innerHTML = ''; listEl.classList.remove('open'); }
}

function submitSixDegreesMove(nodeType, nodeId, name) {
  var s = state.sixDegrees;
  if (!s || !s.game || s.game.completed || s.game.out_of_moves) return;
  sixDegreesCloseSearch();
  s.searchQuery = '';
  s.moveFeedback = { pending: true, name: name };
  renderAll();
  sixDegreesFetchJson('/v1/public/coach_connections/move', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: s.game.game_id, node_type: nodeType, node_id: nodeId }),
  }).then(function (result) {
    if (state.sixDegrees !== s) return;
    s.game = result;
    s.moveFeedback = result.last_move || null;
    playSound((result.last_move && result.last_move.accepted) ? 'correct' : 'wrong');
    renderAll();
    if (!result.completed && !result.out_of_moves) sixDegreesFocusSearchInput();
  }).catch(function (err) {
    if (state.sixDegrees !== s) return;
    s.screen = SIX_DEGREES_SCREEN.ERROR;
    s.error = sixDegreesUserFacingError(err);
    renderAll();
  });
}

function giveUpSixDegrees() {
  var s = state.sixDegrees;
  if (!s || !s.game || s.game.completed) return;
  s.gaveUp = true;
  renderAll();
  revealSixDegrees();
}
function revealSixDegrees() {
  var s = state.sixDegrees;
  if (!s || !s.game) return;
  sixDegreesFetchJson('/v1/public/coach_connections/reveal', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: s.game.game_id }),
  }).then(function (reveal) {
    if (state.sixDegrees !== s) return;
    s.reveal = reveal;
    renderAll();
  }).catch(function () {
    // Reveal is a nice-to-have once a player's out of moves -- a failure
    // here shouldn't block them from exiting/retrying, so it fails silent
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

function sixDegreesEdgeLabel(edge) {
  var pred = {
    PLAYED_FOR: 'played for', COACHED_TEAM_IN_SEASON: 'coached', DRAFTED_BY: 'drafted by',
    WORE_NUMBER: 'wore a number with', TEAMMATE_OF: 'teammate of',
    PLAYED_UNDER: 'played under', COACHED_PLAYER: 'coached',
  }[edge.predicate] || edge.predicate.toLowerCase().replace(/_/g, ' ');
  var season = edge.season_start === edge.season_end ? edge.season_start : (edge.season_start + '–' + edge.season_end);
  return pred + (season ? ' (' + season + ')' : '');
}

function renderSixDegreesScreen() {
  if (!ENABLE_ENGINE_SIX_DEGREES_V01) return renderHome();
  var s = state.sixDegrees;
  if (!s) {
    return '<div class="panel">' +
      '<h2 class="panel-title">Coach Connections</h2>' +
      '<p class="mode-desc">Connect two NFL people through real career history — coaches, players, and teams. Search for who links each step.</p>' +
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
  var game = s.game;
  var completed = game.completed;
  var outOfMoves = game.out_of_moves || s.gaveUp;

  // Progressive reveal: only nodes the player has actually reached render as
  // solid pills; the target is always shown by name (that's the puzzle
  // prompt itself -- "get to this person"), but nothing about HOW to reach
  // it is ever implied here or by the server.
  // Once completed, the last discovered node IS the target -- rendering a
  // separate Target pill after it would show the same name twice (real bug
  // caught in a live playthrough screenshot). Only append the Target pill
  // while it's still un-reached.
  var chainHtml = '<div class="sixdeg-path">' +
    game.discovered.map(function (node, i) {
      var label = i === 0 ? 'Start' : (completed && i === game.discovered.length - 1 ? 'Target' : ('Step ' + i));
      var isCurrent = i === game.discovered.length - 1;
      return '<span class="sixdeg-path-node' + (isCurrent ? ' sixdeg-path-current' : '') + '"><b>' + label + '</b>' + esc(node.name) + '</span>' +
        (i < game.discovered.length - 1 ? '<span class="sixdeg-path-arrow">&rarr;</span>' : '');
    }).join('') +
    (completed ? '' :
      '<span class="sixdeg-path-arrow">&rarr;</span>' +
      '<span class="sixdeg-path-node sixdeg-path-end"><b>Target</b>' + esc(game.end.name) + '</span>') +
    '</div>';

  var edgesHtml = game.edges_found.length
    ? '<ul class="summary-note sixdeg-edges">' + game.edges_found.map(function (e) {
        return '<li>' + sixDegreesEdgeLabel(e) + '</li>';
      }).join('') + '</ul>'
    : '';

  if (completed) {
    return '<div class="panel">' + sixDegreesToolbarHtml() +
      '<h2 class="panel-title">' + icon('check') + ' Connected!</h2>' +
      chainHtml +
      '<p class="summary-note">' + esc(game.start.name) + ' &rarr; ' + esc(game.end.name) + ' in ' + game.moves_made + ' move' + (game.moves_made === 1 ? '' : 's') + ' (par ' + game.par + ', ' + game.difficulty + ').</p>' +
      edgesHtml +
      '<div class="btn-row"><button class="btn-primary" data-sixdegrees-start>Play Again</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  if (outOfMoves) {
    var outOfMovesReason = s.gaveUp
      ? ('You gave up before reaching ' + esc(game.end.name) + '.')
      : ('You used all ' + game.max_moves + ' moves without reaching ' + esc(game.end.name) + '.');
    return '<div class="panel">' + sixDegreesToolbarHtml() +
      '<h2 class="panel-title">' + icon('xMark') + ' ' + (s.gaveUp ? 'Gave up' : 'Out of moves') + '</h2>' +
      chainHtml +
      '<p class="mode-desc">' + outOfMovesReason + '</p>' +
      (s.reveal
        ? '<div class="summary-note">One real path: ' + esc(s.reveal.solution_names.join(' → ')) + '</div>'
        : '<div class="btn-row"><button class="btn-secondary" data-sixdegrees-reveal>Show a Solution</button></div>') +
      '<div class="btn-row">' +
      '<button class="btn-primary" data-sixdegrees-start>Play Again</button>' +
      '<button class="btn-secondary" data-go="home">Home</button>' +
      '</div></div>';
  }

  var feedback = s.moveFeedback;
  var feedbackHtml = '';
  if (feedback && feedback.pending) {
    feedbackHtml = '<div class="quiz-progress" aria-live="polite">Checking ' + esc(feedback.name) + '&hellip;</div>';
  } else if (feedback && feedback.accepted) {
    feedbackHtml = '<div class="quiz-feedback" aria-live="polite"><span class="feedback-good">' + icon('check') + ' ' + esc(feedback.node_name) + ' — ' + esc(sixDegreesEdgeLabel({ predicate: feedback.predicate, season_start: null, season_end: null })) + '</span></div>';
  } else if (feedback && feedback.accepted === false && feedback.reason === 'NOT_CONNECTED') {
    feedbackHtml = '<div class="quiz-feedback" aria-live="polite"><span class="feedback-bad">' + icon('xMark') + ' Not directly connected — try another real link from ' + esc(game.discovered[game.discovered.length - 1].name) + '.</span></div>';
  }

  return '<div class="panel">' + sixDegreesToolbarHtml() +
    chainHtml +
    '<div class="quiz-progress">Move ' + game.moves_made + ' of ' + game.max_moves + ' &middot; par ' + game.par + ' &middot; ' + esc(game.difficulty) + '</div>' +
    '<div class="quiz-question">Who or what connects to <b>' + esc(game.discovered[game.discovered.length - 1].name) + '</b>?</div>' +
    '<div class="grid-answer-box">' +
    '<div class="typeahead-wrap">' +
    '<input id="sixdegrees-search-input" autocomplete="off" placeholder="Search a player, coach, or team&hellip;" value="' + esc(s.searchQuery) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="sixdegrees-search-results" />' +
    '<div id="sixdegrees-search-results" class="typeahead-list" role="listbox"></div>' +
    '</div>' +
    '</div>' +
    feedbackHtml +
    '<div class="btn-row"><button class="btn-secondary" data-sixdegrees-giveup>Give Up &amp; Reveal</button></div>' +
    '</div>';
}
