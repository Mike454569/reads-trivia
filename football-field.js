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

  // ---- Football 101 Graphics Quality pass ----------------------------------
  // Real, structural fixes for the readability/touch-target problems a real
  // browser QA pass found (I-Formation's stacked QB/FB/RB assignment tags
  // landing inside the next player's own marker circle; Cover 3's "Deep
  // Third (Middle)" zone label sitting under the Free Safety dot; Mesh's
  // WR1/WR2 route labels running past the viewBox edge at x=6/x=94; player
  // touch targets measuring ~11px on a 320px phone because the tappable
  // region WAS the r=2.2 visible dot, with no separate hit area). None of
  // this existed before -- there was no collision-avoidance or
  // bounds-clamping logic anywhere in this renderer.

  function dist(ax, ay, bx, by) {
    return Math.sqrt((ax - bx) * (ax - bx) + (ay - by) * (ay - by));
  }

  // Touch targets: a separate, larger invisible hit circle per player,
  // decoupled from the small visible dot (kept small on purpose -- see
  // playerMarkerSVG's own comment -- to avoid crowding tightly-packed
  // groups like I-Formation's backfield). Sized toward a real ~44px
  // physical target where the diagram's own real player spacing allows it,
  // shrunk only as far as needed to avoid overlapping a neighbor's own hit
  // area -- "44px where practical," not a fixed value that ignores real
  // layouts. TARGET_HIT_RADIUS (6 viewBox units) approximates ~44px
  // diameter on a 430px-wide phone after container padding; narrower
  // phones get a smaller real target from the same fixed viewBox math, an
  // honest consequence of a fluid SVG, not a separate bug.
  var TARGET_HIT_RADIUS = 6;
  var HIT_RADIUS_SAFETY_MARGIN = 0.3;

  function hitRadiusFor(p, allRealPlayers, visibleRadius) {
    var maxRadius = TARGET_HIT_RADIUS;
    allRealPlayers.forEach(function (other) {
      if (other === p) return;
      var d = dist(p.x, p.y, other.x, other.y);
      var allowed = d / 2 - HIT_RADIUS_SAFETY_MARGIN;
      if (allowed < maxRadius) maxRadius = allowed;
    });
    return Math.max(visibleRadius, maxRadius);
  }

  // Label collision avoidance: a label's estimated half-width in viewBox
  // units (no real DOM text measurement is available at string-build time)
  // -- calibrated against the CSS's own ~1.7-2.2 unit font-size and this
  // font stack's typical glyph width, generous enough to avoid UNDER-
  // estimating (which would let text clip) at the cost of occasionally
  // over-padding a short label.
  var CHAR_WIDTH_ESTIMATE = 1.35;

  function clampLabelX(text, x) {
    var halfWidth = (text.length * CHAR_WIDTH_ESTIMATE) / 2;
    if (x - halfWidth < 1) return { x: Math.max(x, halfWidth + 1), anchor: halfWidth + 1 > 50 ? 'middle' : 'start', textX: halfWidth + 1 };
    if (x + halfWidth > 99) return { x: Math.min(x, 99 - halfWidth), anchor: 99 - halfWidth < 50 ? 'middle' : 'end', textX: 99 - halfWidth };
    return { x: x, anchor: 'middle', textX: x };
  }

  // Real bug this pass found and fixed before shipping: this used to check
  // against each player's own TOUCH hit-radius (hitRadiusFor(), up to 6
  // units for an isolated player with room to spare) -- correct for sizing
  // an invisible tap target, wrong for "does a label visually overlap a
  // marker," which is a much smaller, fixed real-estate question
  // independent of how generous that player's tap area is. Using the tap
  // radius here made an ISOLATED player (Cover 3's Free Safety, with no
  // real neighbor for 20+ units) act like a 7.5-unit-radius exclusion zone
  // for label placement, when visually there was plenty of real room just
  // a few units away. A small, fixed visual radius is the correct model
  // for a SHORT label's anchor point -- but a second real bug (found in
  // the same sweep, still on real diagrams: I-Formation's/Power's own
  // pulling-guard assignment tags, up to 34 characters long) is that a
  // POINT-radius check ignores the label's own real rendered WIDTH: a
  // long tag's anchor can sit far from every player while the text itself
  // -- half-width up to ~23 viewBox units for a full 34-character tag --
  // sweeps horizontally right across a nearby player anyway. Fixed by
  // checking a real axis-aligned text bounding box against each player's
  // small visual footprint (closest-point-on-rectangle-to-circle-center),
  // not a bare point-to-point distance.
  var LABEL_VISUAL_COLLISION_RADIUS = 3.6;
  var PLAYER_VISUAL_FOOTPRINT_RADIUS = 2.6;
  var LABEL_LINE_HALF_HEIGHT = 1.1;

  function labelCollidesWithPlayer(x, y, players, excludeId, textHalfWidth) {
    var halfW = textHalfWidth || 0;
    for (var i = 0; i < players.length; i++) {
      var pl = players[i];
      if (pl.id === excludeId) continue;
      if (halfW > 0) {
        // Closest point on the label's own bounding box to this player's
        // center, then a plain circle check from there -- correct
        // rectangle-vs-circle overlap, not an approximation that only
        // works for a single point.
        var closestX = Math.max(x - halfW, Math.min(pl.x, x + halfW));
        var closestY = Math.max(y - LABEL_LINE_HALF_HEIGHT, Math.min(pl.y, y + LABEL_LINE_HALF_HEIGHT));
        if (dist(closestX, closestY, pl.x, pl.y) < PLAYER_VISUAL_FOOTPRINT_RADIUS) return true;
      } else if (dist(x, y, pl.x, pl.y) < LABEL_VISUAL_COLLISION_RADIUS) {
        return true;
      }
    }
    return false;
  }

  function arrowMarkerDefs() {
    return '<defs>' +
      '<marker id="f101-arrow-route" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" class="f101-arrowhead-route" /></marker>' +
      '<marker id="f101-arrow-block" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" class="f101-arrowhead-block" /></marker>' +
      '<marker id="f101-arrow-ball" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" class="f101-arrowhead-ball" /></marker>' +
      '</defs>';
  }

  function playerMarkerSVG(p, opts, allRealPlayers, hitRadii) {
    var isGhost = !!p.ghost;
    var isActive = opts.activePlayerId === p.id;
    var cls = 'f101-player' + (isGhost ? ' f101-player-ghost' : '') + (isActive ? ' f101-player-active' : '');
    // Real-browser QA pass: 3.4/2.6 visually overlapped for any two players
    // less than ~7 units apart (common for stacked backfield personnel like
    // I-Formation's QB/FB/RB) -- shrunk so markers stay legible without
    // touching down to the closest real spacing used anywhere in the data
    // (RUN_TRAP's puller start is ~4.5 units from the guard it pulls from).
    var r = isGhost ? 1.8 : 2.2;
    var interactive = !isGhost;
    var attrs = 'class="' + cls + '" transform="translate(' + p.x + ',' + p.y + ')"' +
      (interactive ? ' tabindex="0" role="button" data-f101-player="' + esc(p.id) + '" aria-label="' +
        esc((p.role || p.label) + (isActive ? ', selected' : '')) + '"' : ' aria-hidden="true"');
    var g = '<g ' + attrs + '>';
    // Football 101 Graphics Quality pass: a separate, invisible, larger hit
    // area -- painted FIRST (so the visible dot still renders on top) and
    // sized per-player via hitRadiusFor() so it never overlaps a real
    // neighbor's own hit area. The visible dot's own size/look is
    // completely unchanged.
    if (interactive) {
      var hitR = (hitRadii && hitRadii[p.id]) || r;
      if (hitR > r) {
        g += '<circle r="' + hitR.toFixed(2) + '" class="f101-player-hit" fill="transparent" />';
      }
    }
    g += '<circle r="' + r + '" class="f101-player-dot" />' +
      '<text class="f101-player-label" text-anchor="middle" dy="0.32em">' + esc(p.label) + '</text>';
    if (opts.showResponsibilities && !isGhost && p.assignment) {
      var short = p.assignment.length > 34 ? p.assignment.slice(0, 33) + '…' : p.assignment;
      // Collision-aware placement (Football 101 Graphics Quality pass): try
      // below the player first (the original fixed offset); if that lands
      // inside another real player's own hit area. Real I-Formation case
      // this pass found: the QB is sandwiched between the OL row (above,
      // at the LOS) and the FB (below) -- a single fixed flip between +6.5/
      // -6.5 isn't enough to escape both, so this tries a real SEARCH:
      // below at increasing distance, then above at increasing distance,
      // falling back to the closest-below position only if every real
      // candidate still collides (a genuinely crowded group -- "Show
      // Responsibilities" is an opt-in toggle, not the default view, so an
      // occasional remaining overlap in an extreme case is an acceptable
      // real limitation, not silently pretending one doesn't exist).
      // Computed once, up front, so both the X-clamp and the Y-collision
      // search below use the SAME real anchor x and text half-width --
      // a real bug this pass found: checking collision at the player's own
      // (unclamped) x while rendering the label at a clamped x could let a
      // near-edge tag's search miss a collision the actually-rendered
      // position would have had, or vice versa.
      var tagClamp = clampLabelX(short, p.x);
      var tagHalfW = (short.length * CHAR_WIDTH_ESTIMATE) / 2;
      var tagY = 6.5;
      if (allRealPlayers) {
        var candidates = [6.5, 9, 11.5, 14, -6.5, -9, -11.5, -14];
        var found = false;
        for (var ci = 0; ci < candidates.length; ci++) {
          var candidateY = p.y + candidates[ci];
          if (candidateY < 1 || candidateY > 99) continue;
          if (!labelCollidesWithPlayer(tagClamp.x, candidateY, allRealPlayers, p.id, tagHalfW)) {
            tagY = candidates[ci];
            found = true;
            break;
          }
        }
        // No collision-free candidate found -- keep the original,
        // documented default rather than a further, riskier search.
      }
      // tagClamp (computed above) also fixes a real edge-clipping bug: a
      // player positioned near the field's own left/right edge (e.g. Mesh/
      // Four Verticals' wide WR1/WR2 at x=6/x=94) had its own assignment
      // tag run straight off the SVG edge, exactly like the route-label
      // clipping this pass separately fixed -- clampLabelX() was only ever
      // wired up for route/block/zone labels before this. `<text>` here
      // has no x attribute (it inherits the parent <g>'s own
      // translate(p.x,p.y)), so the clamp is expressed as an offset
      // relative to that origin, not an absolute coordinate.
      var tagXOffset = (tagClamp.textX - p.x).toFixed(2);
      g += '<text class="f101-player-tag" text-anchor="' + tagClamp.anchor + '" x="' + tagXOffset + '" y="' + tagY + '">' + esc(short) + '</text>';
    }
    g += '</g>';
    return g;
  }

  // Shared label-placement helper (Football 101 Graphics Quality pass):
  // clamps x to stay inside the viewBox (real fix for Mesh's WR1/WR2 route
  // labels running past x=6/x=94 off the field edge) and nudges y away from
  // any real player's own hit area if the label would otherwise land on
  // top of one -- tries progressively further offsets in the label's own
  // "away from the path" direction rather than a single fixed flip, since
  // route/block labels (unlike player tags) aren't anchored to one fixed
  // player position to flip around.
  function placeLabel(x, y, text, awayFromY, allRealPlayers) {
    var clamped = clampLabelX(text, x);
    var halfW = (text.length * CHAR_WIDTH_ESTIMATE) / 2;
    var finalY = y;
    if (allRealPlayers && labelCollidesWithPlayer(clamped.x, finalY, allRealPlayers, null, halfW)) {
      var direction = awayFromY >= y ? -1 : 1; // move further away from where the path is coming from
      // Real fix found in the same sweep as the player-tag search above:
      // 3 candidates (in only one direction, plus one fallback) weren't
      // enough for several real diagrams (Cover 4's "Deep Quarter"
      // labels vs. its own safeties, Power's pulling-guard block labels
      // vs. the QB/FB/RB backfield) -- widened to a real search across
      // both directions at increasing distance, same "keep the original
      // if truly nothing clears" fallback discipline.
      var nudges = [direction * 3, direction * 5, direction * 7, -direction * 3, -direction * 5, -direction * 7];
      for (var i = 0; i < nudges.length; i++) {
        var candidateY = Math.max(2, Math.min(98, y + nudges[i]));
        if (!labelCollidesWithPlayer(clamped.x, candidateY, allRealPlayers, null, halfW)) {
          finalY = candidateY;
          break;
        }
      }
    }
    return { x: clamped.x, y: finalY, anchor: clamped.anchor };
  }

  function routesSVG(diagram, opts, allRealPlayers) {
    if (!opts.showRoutes || !diagram.routes) return '';
    return diagram.routes.map(function (r) {
      var d = pathD(r.points);
      var last = r.points[r.points.length - 1];
      var labelSvg = '';
      if (r.label) {
        var prev = r.points.length > 1 ? r.points[r.points.length - 2] : last;
        var placed = placeLabel(last.x, last.y - 2, r.label, prev.y, allRealPlayers);
        labelSvg = '<text class="f101-route-label" x="' + placed.x + '" y="' + placed.y + '" text-anchor="' + placed.anchor + '">' + esc(r.label) + '</text>';
      }
      return '<path d="' + d + '" class="f101-route-path" marker-end="url(#f101-arrow-route)" />' + labelSvg;
    }).join('');
  }

  function blocksSVG(diagram, opts, allRealPlayers) {
    if (!opts.showBlocks) return '';
    var out = '';
    if (diagram.blocks) {
      out += diagram.blocks.map(function (b) {
        var d = pathD(b.points);
        var last = b.points[b.points.length - 1];
        var labelSvg = '';
        if (b.label) {
          var prev = b.points.length > 1 ? b.points[b.points.length - 2] : last;
          var placed = placeLabel(last.x, last.y - 2, b.label, prev.y, allRealPlayers);
          labelSvg = '<text class="f101-block-label" x="' + placed.x + '" y="' + placed.y + '" text-anchor="' + placed.anchor + '">' + esc(b.label) + '</text>';
        }
        return '<path d="' + d + '" class="f101-block-path" marker-end="url(#f101-arrow-block)" />' + labelSvg;
      }).join('');
    }
    if (diagram.ball_path) {
      out += '<path d="' + pathD(diagram.ball_path) + '" class="f101-ball-path" marker-end="url(#f101-arrow-ball)" />';
    }
    return out;
  }

  function coverageZonesSVG(diagram, opts, allRealPlayers) {
    if (!opts.showCoverage || !diagram.zones || !diagram.zones.length) return '';
    return diagram.zones.map(function (z) {
      // Real fix for Cover 3's "Deep Third (Middle)" label sitting under
      // the Free Safety marker: nudge the label toward the zone's own
      // outer edge (away from center, where a player is more likely to be
      // standing) if it collides, rather than leaving it dead-center.
      var placed = placeLabel(z.cx, z.cy, z.label, z.cy - z.ry, allRealPlayers);
      return '<ellipse cx="' + z.cx + '" cy="' + z.cy + '" rx="' + z.rx + '" ry="' + z.ry + '" class="f101-zone" />' +
        '<text x="' + placed.x + '" y="' + placed.y + '" class="f101-zone-label" text-anchor="' + placed.anchor + '" dy="0.32em">' + esc(z.label) + '</text>';
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
    // Computed once per render, shared by every label-placement/hit-area
    // decision below -- see hitRadiusFor()/labelCollidesWithPlayer()'s own
    // comments for why this needs the FULL player list, not just the one
    // player/label currently being placed. Touch-target sizing (hitRadii)
    // only ever needs REAL (interactive) players -- a ghost has no tap
    // target. Label AVOIDANCE deliberately also considers ghosts (real bug
    // this pass found: Cover 3's NB assignment tag rendered right on top
    // of a ghost reference marker -- faint/dashed, lower severity than
    // obscuring a real player, but still worth avoiding at effectively no
    // extra cost).
    var allRealPlayers = players.filter(function (p) { return !p.ghost; });
    var allPlayersForLabelAvoidance = players;
    var hitRadii = {};
    allRealPlayers.forEach(function (p) {
      hitRadii[p.id] = hitRadiusFor(p, allRealPlayers, 2.2);
    });
    return '<svg viewBox="0 0 ' + FIELD_W + ' ' + FIELD_H + '" class="f101-svg" role="img" ' +
      'aria-labelledby="f101-svg-title" aria-describedby="f101-svg-desc" preserveAspectRatio="xMidYMid meet">' +
      '<title id="f101-svg-title">' + esc(titleText) + '</title>' +
      '<desc id="f101-svg-desc">' + esc(descText) + '</desc>' +
      arrowMarkerDefs() +
      fieldBackgroundSVG(losY) +
      coverageZonesSVG(diagram, opts, allPlayersForLabelAvoidance) +
      blocksSVG(diagram, opts, allPlayersForLabelAvoidance) +
      routesSVG(diagram, opts, allPlayersForLabelAvoidance) +
      players.map(function (p) { return playerMarkerSVG(p, opts, allPlayersForLabelAvoidance, hitRadii); }).join('') +
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
