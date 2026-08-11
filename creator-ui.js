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
    capabilities: null, error: null,
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
    body: JSON.stringify({ request_text: s.requestText, puzzle_count: 5 }),
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

function creatorSupportBadgeHtml(status) {
  var cls = { SUPPORTED: 'good', SUPPORTED_WITH_LIMITATIONS: 'good', UNDERSTOOD_BUT_UNSUPPORTED: 'warn',
    MISSING_DATA: 'warn', UNSAFE: 'bad', UNKNOWN: 'warn' }[status] || 'warn';
  return '<span class="creator-badge creator-badge-' + cls + '">' + esc(status) + '</span>';
}

function creatorToolbarHtml(showBack) {
  return '<div class="mode-toolbar">' +
    (showBack ? '<button class="btn-tiny" data-creator-nav="home">&larr; Back</button>' : '') +
    '<button class="btn-tiny" data-creator-nav="queue">Review Queue</button>' +
    '<button class="btn-tiny" data-creator-nav="capabilities">Capabilities</button>' +
    '<button class="btn-tiny" data-creator-logout>Log Out</button>' +
    '<button class="btn-tiny" data-go="home">' + icon('close') + ' Exit</button>' +
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
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit</button></div>' +
      '<h2 class="panel-title">Game Creator</h2>' +
      '<p class="mode-desc">Admin only. Enter the Gateway admin token to continue. Kept only in this ' +
      'browser tab\'s session storage -- never written to source, never sent anywhere except this ' +
      'Gateway.</p>' +
      '<input type="password" id="creator-token-input" class="creator-input" placeholder="Admin token" autocomplete="off" />' +
      '<div class="btn-row"><button class="btn-primary" data-creator-auth-submit>Continue</button></div>' +
      '</div>';
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
        return '<div class="creator-queue-row">' +
          '<div><b>' + esc(p.game_title || p.package_id) + '</b> &middot; ' + esc(p.review_status) + ' &middot; QA ' + esc(p.qa_status) +
          ' &middot; ' + (p.question_count || 0) + ' questions</div>' +
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
    return '<div class="panel">' + creatorToolbarHtml(true) +
      '<p class="mode-desc" aria-live="polite">' + (s.screen === CREATOR_SCREEN.CHECKING ? 'Checking feasibility…' : 'Generating and QA-checking real puzzles…') + '</p></div>';
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
      html += '<div class="panel">' +
        '<h2 class="panel-title">Preview -- ' + esc(g.game_title || '') + '</h2>' +
        '<p class="mode-desc">QA: ' + esc(g.qa_status) + ' &middot; ' + (g.question_count || 0) + ' questions &middot; review status: ' + esc(g.review_status) + '</p>';
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
      (g.questions || []).forEach(function (q, i) {
        var payload = creatorQuestionAsPublicPayload(q);
        html += '<div class="creator-preview-question">' +
          '<div class="quiz-progress">Question ' + (i + 1) + ' &middot; ' + esc(q.difficulty || '') + '</div>' +
          renderEnginePilotPromptHtml({ payload: payload }) +
          '<div class="quiz-options">' + q.options.map(function (opt, oi) {
            return '<div class="quiz-option' + (oi === q.correctIndex ? ' correct' : '') + '" style="cursor:default;">' +
              String.fromCharCode(65 + oi) + '. ' + esc(opt) + '</div>';
          }).join('') + '</div>' +
          (q.notes ? '<div class="quiz-feedback">' + esc(q.notes) + '</div>' : '') +
          '</div>';
      });
      html += '</div>';
    }
    return html;
  }

  // HOME
  return '<div class="panel">' + creatorToolbarHtml(false) +
    '<h2 class="panel-title">Game Creator</h2>' +
    '<p class="mode-desc">Describe a game in plain English. This checks it against the real Director ' +
    'feasibility engine -- nothing here executes SQL, code, or a shell command from your text; it can ' +
    'only ever resolve to one of a fixed set of registered, pre-audited capabilities (Part C/L).</p>' +
    '<textarea id="creator-request-input" class="creator-textarea" rows="3" placeholder="e.g. Guess the NFL team from its starting offense, by position.">' + esc(s.requestText || '') + '</textarea>' +
    '<div class="btn-row"><button class="btn-primary" data-creator-check-feasibility>Check Feasibility</button></div>' +
    '</div>';
}
