// Football 101 Interactive Redesign: the one reusable SVG football-field
// renderer every formation/front/coverage/pass-concept/run-concept diagram
// goes through (see data/football-diagrams.js's data-driven library and
// tools/learn/build_football_diagrams.py's generator). Deliberately DOM-free
// and side-effect-free -- every exported function takes plain data in and
// returns a plain string or object out, so it is trivially testable without
// a browser (see gateway/tests or a plain `osascript -l JavaScript` harness)
// and reusable later by game modes exactly as the redesign brief asks for,
// without dragging in this app's own render/click-delegation plumbing.
//
// Lazy-loaded (see LEARN_SECTIONS' footballEncyclopedia entry in app.js)
// only when Football 101 is actually opened -- never part of the initial
// page load.
(function (root) {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  var FIELD_W = 100, FIELD_H = 100;

  function pathD(points) {
    if (!points || !points.length) return '';
    return points.map(function (p, i) { return (i === 0 ? 'M ' : 'L ') + p.x + ' ' + p.y; }).join(' ');
  }

  // ---- Field background: one LOS-centered schematic, reused by every
  // diagram regardless of side (offense fills y>los, defense fills y<los --
  // see data/football-diagrams.js's module docstring for the coordinate
  // system this assumes). ----
  function fieldBackgroundSVG(losY) {
    var lines = '';
    for (var y = 10; y < 100; y += 10) {
      if (y === losY) continue;
      lines += '<line x1="0" y1="' + y + '" x2="100" y2="' + y + '" class="f101-yardline" />';
    }
    // Hash marks -- purely decorative/orientation, not gameplay-load-bearing.
    var hashes = '';
    for (var hy = 5; hy < 100; hy += 5) {
      hashes += '<line x1="34" y1="' + hy + '" x2="37" y2="' + hy + '" class="f101-hash" />';
      hashes += '<line x1="63" y1="' + hy + '" x2="66" y2="' + hy + '" class="f101-hash" />';
    }
    return '<rect x="0" y="0" width="100" height="100" class="f101-field-bg" />' +
      lines + hashes +
      '<line x1="0" y1="' + losY + '" x2="100" y2="' + losY + '" class="f101-los" />';
  }

  function arrowMarkerDefs() {
    return '<defs>' +
      '<marker id="f101-arrow-route" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" class="f101-arrowhead-route" /></marker>' +
      '<marker id="f101-arrow-block" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" class="f101-arrowhead-block" /></marker>' +
      '<marker id="f101-arrow-ball" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" class="f101-arrowhead-ball" /></marker>' +
      '</defs>';
  }

  function playerMarkerSVG(p, opts) {
    var isGhost = !!p.ghost;
    var isActive = opts.activePlayerId === p.id;
    var cls = 'f101-player' + (isGhost ? ' f101-player-ghost' : '') + (isActive ? ' f101-player-active' : '');
    var r = isGhost ? 2.6 : 3.4;
    var interactive = !isGhost;
    var attrs = 'class="' + cls + '" transform="translate(' + p.x + ',' + p.y + ')"' +
      (interactive ? ' tabindex="0" role="button" data-f101-player="' + esc(p.id) + '" aria-label="' +
        esc((p.role || p.label) + (isActive ? ', selected' : '')) + '"' : ' aria-hidden="true"');
    var g = '<g ' + attrs + '>' +
      '<circle r="' + r + '" class="f101-player-dot" />' +
      '<text class="f101-player-label" text-anchor="middle" dy="0.32em">' + esc(p.label) + '</text>';
    if (opts.showResponsibilities && !isGhost && p.assignment) {
      var short = p.assignment.length > 34 ? p.assignment.slice(0, 33) + '…' : p.assignment;
      g += '<text class="f101-player-tag" text-anchor="middle" y="6.5">' + esc(short) + '</text>';
    }
    g += '</g>';
    return g;
  }

  function routesSVG(diagram, opts) {
    if (!opts.showRoutes || !diagram.routes) return '';
    return diagram.routes.map(function (r) {
      var d = pathD(r.points);
      var last = r.points[r.points.length - 1];
      var labelSvg = r.label
        ? '<text class="f101-route-label" x="' + last.x + '" y="' + (last.y - 2) + '" text-anchor="middle">' + esc(r.label) + '</text>'
        : '';
      return '<path d="' + d + '" class="f101-route-path" marker-end="url(#f101-arrow-route)" />' + labelSvg;
    }).join('');
  }

  function blocksSVG(diagram, opts) {
    if (!opts.showBlocks) return '';
    var out = '';
    if (diagram.blocks) {
      out += diagram.blocks.map(function (b) {
        var d = pathD(b.points);
        var last = b.points[b.points.length - 1];
        var labelSvg = b.label
          ? '<text class="f101-block-label" x="' + last.x + '" y="' + (last.y - 2) + '" text-anchor="middle">' + esc(b.label) + '</text>'
          : '';
        return '<path d="' + d + '" class="f101-block-path" marker-end="url(#f101-arrow-block)" />' + labelSvg;
      }).join('');
    }
    if (diagram.ball_path) {
      out += '<path d="' + pathD(diagram.ball_path) + '" class="f101-ball-path" marker-end="url(#f101-arrow-ball)" />';
    }
    return out;
  }

  function coverageZonesSVG(diagram, opts) {
    if (!opts.showCoverage || !diagram.zones || !diagram.zones.length) return '';
    return diagram.zones.map(function (z) {
      return '<ellipse cx="' + z.cx + '" cy="' + z.cy + '" rx="' + z.rx + '" ry="' + z.ry + '" class="f101-zone" />' +
        '<text x="' + z.cx + '" y="' + z.cy + '" class="f101-zone-label" text-anchor="middle" dy="0.32em">' + esc(z.label) + '</text>';
    }).join('');
  }

  /**
   * Pure: diagram data + a small options object in, one <svg>...</svg>
   * string out. opts: { showResponsibilities, showRoutes, showBlocks,
   * showCoverage, activePlayerId }.
   */
  function renderDiagramSVG(diagram, opts) {
    opts = opts || {};
    var losY = diagram.los_y != null ? diagram.los_y : 50;
    var players = diagram.players || [];
    var titleText = diagram.display_name || diagram.id;
    var descText = diagram.description || '';
    return '<svg viewBox="0 0 ' + FIELD_W + ' ' + FIELD_H + '" class="f101-svg" role="img" ' +
      'aria-labelledby="f101-svg-title" aria-describedby="f101-svg-desc" preserveAspectRatio="xMidYMid meet">' +
      '<title id="f101-svg-title">' + esc(titleText) + '</title>' +
      '<desc id="f101-svg-desc">' + esc(descText) + '</desc>' +
      arrowMarkerDefs() +
      fieldBackgroundSVG(losY) +
      coverageZonesSVG(diagram, opts) +
      blocksSVG(diagram, opts) +
      routesSVG(diagram, opts) +
      players.map(function (p) { return playerMarkerSVG(p, opts); }).join('') +
      '</svg>';
  }

  /**
   * Pure: looks up a diagram player's real position-level context from
   * LEARN_ENCYCLOPEDIA.concepts (POSITIONS domain) when available, combined
   * with THIS diagram's own concrete assignment for that alignment/play --
   * never fabricates a fact neither source actually states.
   */
  function describePlayer(diagram, playerId, encyclopediaConcepts) {
    var p = (diagram.players || []).find(function (x) { return x.id === playerId; });
    if (!p) return null;
    var pos = (encyclopediaConcepts && p.position_ref) ? encyclopediaConcepts[p.position_ref] : null;
    var fields = (pos && pos.fields) || {};
    return {
      id: p.id,
      label: p.label,
      role: p.role || p.label,
      assignment: p.assignment || null,
      coreResponsibilities: fields.core_responsibilities || null,
      evaluationTraits: fields.evaluation_traits || null,
      commonMisread: fields.common_misread || null,
      sourceUrl: fields.source || null,
      verified: !!pos,
    };
  }

  // ---- Test Me: generates one real, data-derived multiple-choice question
  // per diagram. Every fact quoted (counts, labels, route names, assignment
  // text) is read directly off the diagram object itself or a sibling in
  // the same category -- nothing here is invented, matching this app's
  // real-data-only discipline. Reuses the SAME quiz-option shape/contract
  // (`question`, `options`, `correctIndex`) the rest of the app's quiz
  // modes already use, so app.js can render it with the exact existing
  // .quiz-question/.quiz-options/.quiz-option markup instead of a second
  // quiz engine. ----
  function shuffle(arr, seed) {
    var a = arr.slice();
    var s = seed || 1;
    for (var i = a.length - 1; i > 0; i--) {
      s = (s * 9301 + 49297) % 233280;
      var j = Math.floor((s / 233280) * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function realPlayers(diagram) { return (diagram.players || []).filter(function (p) { return !p.ghost; }); }

  // Two players can share the same role label (e.g. Four Verticals' two
  // slot receivers are both "Slot / F Receiver") -- a multiple-choice
  // question can never offer the same visible option twice, so pick
  // distractors whose role TEXT hasn't already been used, not just whose
  // player id differs.
  function pickDistinctDistractors(candidates, usedText, count) {
    var out = [];
    for (var i = 0; i < candidates.length && out.length < count; i++) {
      var text = candidates[i].role || candidates[i].label;
      if (usedText.indexOf(text) !== -1) continue;
      usedText.push(text);
      out.push(candidates[i]);
    }
    return out;
  }

  function widestPlayer(diagram) {
    var players = realPlayers(diagram);
    var best = null, bestDist = -1;
    players.forEach(function (p) {
      var dist = Math.abs(p.x - 50);
      if (dist > bestDist) { bestDist = dist; best = p; }
    });
    return best;
  }

  function countByRoleMatch(diagram, patterns) {
    return realPlayers(diagram).filter(function (p) {
      return patterns.some(function (re) { return re.test(p.role || ''); });
    }).length;
  }

  var DB_PATTERNS = [/Cornerback/, /Safety/, /Nickel/, /Dime/];
  var DL_PATTERNS = [/Defensive End/, /Tackle/, /Nose/, /3-Technique/];

  function generateTestMeQuestion(diagram, category, siblings, seed) {
    siblings = (siblings || []).filter(function (d) { return d.id !== diagram.id; });
    var name = diagram.display_name || diagram.id;

    if (category === 'formation') {
      var wp = widestPlayer(diagram);
      if (!wp) return null;
      var wpText = wp.role || wp.label;
      var others = pickDistinctDistractors(shuffle(realPlayers(diagram).filter(function (p) { return p.id !== wp.id; }), seed), [wpText], 3);
      if (others.length < 1) return null;
      var options = shuffle([wp].concat(others), seed + 1).map(function (p) { return p.role || p.label; });
      return {
        question: 'In the ' + name + ', which player is aligned widest from the ball (the biggest split)?',
        options: options,
        correctIndex: options.indexOf(wpText),
      };
    }

    if (category === 'front') {
      var dbCount = countByRoleMatch(diagram, DB_PATTERNS);
      var pool = [dbCount];
      siblings.forEach(function (s) { pool.push(countByRoleMatch(s, DB_PATTERNS)); });
      var uniquePool = shuffle(Array.from(new Set(pool)), seed).slice(0, 4);
      if (uniquePool.indexOf(dbCount) === -1) uniquePool[0] = dbCount;
      uniquePool = shuffle(uniquePool, seed + 2);
      return {
        question: 'How many defensive backs (cornerbacks, safeties, nickel/dime defenders) are on the field in the ' + name + '?',
        options: uniquePool.map(String),
        correctIndex: uniquePool.indexOf(dbCount),
      };
    }

    if (category === 'coverage') {
      if (diagram.man_coverage) {
        var manOptions = ['Man coverage', 'Zone coverage'];
        return { question: 'Is ' + name + ' primarily man coverage or zone coverage?', options: manOptions, correctIndex: 0 };
      }
      var deep = (diagram.zones || []).length;
      var deepPool = [deep];
      siblings.filter(function (s) { return !s.man_coverage; }).forEach(function (s) { deepPool.push((s.zones || []).length); });
      var uniqueDeep = shuffle(Array.from(new Set(deepPool)), seed).slice(0, 4);
      if (uniqueDeep.indexOf(deep) === -1) uniqueDeep[0] = deep;
      uniqueDeep = shuffle(uniqueDeep, seed + 3);
      return {
        question: 'How many deep zones does ' + name + ' divide the field into?',
        options: uniqueDeep.map(String),
        correctIndex: uniqueDeep.indexOf(deep),
      };
    }

    if (category === 'pass_concept') {
      var routes = diagram.routes || [];
      var labeled = routes.filter(function (r) { return r.label; });
      if (!labeled.length) return null;
      var pick = labeled[Math.floor((seed % labeled.length + labeled.length) % labeled.length)];
      var runner = realPlayers(diagram).find(function (p) { return p.id === pick.player; });
      if (!runner) return null;
      var runnerText = runner.role || runner.label;
      var distractors = pickDistinctDistractors(shuffle(realPlayers(diagram).filter(function (p) { return p.id !== runner.id; }), seed), [runnerText], 3);
      if (distractors.length < 1) return null;
      var pcOptions = shuffle([runner].concat(distractors), seed + 4).map(function (p) { return p.role || p.label; });
      return {
        question: 'In ' + name + ', which player runs the "' + pick.label + '" route?',
        options: pcOptions,
        correctIndex: pcOptions.indexOf(runnerText),
      };
    }

    if (category === 'run_concept') {
      var blockCount = (diagram.blocks || []).length;
      var rcPool = [blockCount];
      siblings.forEach(function (s) { rcPool.push((s.blocks || []).length); });
      var uniqueRc = shuffle(Array.from(new Set(rcPool)), seed).slice(0, 4);
      if (uniqueRc.indexOf(blockCount) === -1) uniqueRc[0] = blockCount;
      uniqueRc = shuffle(uniqueRc, seed + 5);
      return {
        question: 'How many blocking assignments are diagrammed for ' + name + '?',
        options: uniqueRc.map(String),
        correctIndex: uniqueRc.indexOf(blockCount),
      };
    }

    return null;
  }

  root.FootballField = {
    renderDiagramSVG: renderDiagramSVG,
    describePlayer: describePlayer,
    generateTestMeQuestion: generateTestMeQuestion,
  };
})(typeof window !== 'undefined' ? window : this);
