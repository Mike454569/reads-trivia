/* ============================================================================
   TEMPORARY PLAYTEST INSTRUMENTATION -- Player From Clues (Director v0.5) only.

   Local human playtest logger for the 25 Engine-generated Player From Clues
   puzzles (window.PLAYER_FROM_CLUES_V01). Not part of the app's real feature
   set -- exists to let a developer evaluate how these puzzles feel inside the
   real Reads UI. Modeled directly on playtest-engine-draft.js -- same
   constraints, same console API shape, same "wrap from the outside, never
   modify app.js" technique.

   Design constraints (all deliberate, matching playtest-engine-draft.js):
   - Zero visible UI. Everything lives in localStorage + the dev console.
   - Zero network calls. Nothing is sent to Firebase, Netlify, or anywhere
     else -- this file makes no fetch/XHR/websocket calls of any kind.
   - Zero effect on gameplay. This file never *writes* app state, never
     changes clue order/answer validation/puzzle selection. It only wraps
     submitPlayerCluesGuess and givePlayerCluesUp to *observe* (read-only)
     whether a new result was recorded, then calls the original function
     completely unchanged. Any error in this file is caught and swallowed so
     it can never break the real app, even if a future app.js refactor
     changes a function this expects to exist.
   - app.js has zero knowledge of this file's existence (no direct call into
     it anywhere in app.js) -- deleting this line + file from index.html
     removes playtest logging with no other change required.

   Console commands: see the printed banner below, or window.PlayerCluesPlaytest.
   ============================================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'reads_player_clues_playtest_log_v1';
  var MAX_ENTRIES = 2000; // generous cap so a long playtest session can't grow localStorage unbounded

  function readLog() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      var parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function writeLog(entries) {
    try {
      if (entries.length > MAX_ENTRIES) entries = entries.slice(entries.length - MAX_ENTRIES);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
    } catch (e) {
      // localStorage full/unavailable — playtest logging degrades silently,
      // never affects the real app.
    }
  }

  function puzzleDifficulty(puzzleId) {
    try {
      var pkg = window.PLAYER_FROM_CLUES_V01;
      var puzzle = pkg && pkg.puzzles && pkg.puzzles.find(function (p) { return p.id === puzzleId; });
      return (puzzle && puzzle.difficulty != null) ? puzzle.difficulty : null;
    } catch (e) {
      return null;
    }
  }

  function recordResult(entry) {
    try {
      if (!entry || typeof entry.id !== 'number') return;
      var entries = readLog();
      entries.push({
        puzzleId: entry.id,
        cluesRevealed: entry.cluesRevealed,
        correct: !!entry.correct,
        difficulty: puzzleDifficulty(entry.id),
        completedAt: new Date().toISOString()
      });
      writeLog(entries);
    } catch (e) {
      // Never let playtest logging break gameplay.
    }
  }

  // ---- Wrap submitPlayerCluesGuess / givePlayerCluesUp. Read-only
  // observation: a puzzle only "completes" (worth logging) when a new entry
  // appears in state.playerClues.results after calling the real function --
  // a wrong guess that just reveals another clue does NOT push a results
  // entry, so it's correctly not logged as a completion. ----

  function wrap(fnName) {
    var original = window[fnName];
    if (typeof original !== 'function') return; // defensive — never throw if app.js shape changes
    window[fnName] = function () {
      var beforeLen = -1;
      try {
        var s = window.state && window.state.playerClues;
        beforeLen = s && Array.isArray(s.results) ? s.results.length : -1;
      } catch (e) {}
      var ret = original.apply(this, arguments);
      try {
        var s2 = window.state && window.state.playerClues;
        if (s2 && Array.isArray(s2.results) && s2.results.length > beforeLen) {
          recordResult(s2.results[s2.results.length - 1]);
        }
      } catch (e) {
        // Never let playtest logging break gameplay.
      }
      return ret;
    };
  }

  wrap('submitPlayerCluesGuess');
  wrap('givePlayerCluesUp');

  // ---- Developer console helpers ----

  function summarize() {
    var entries = readLog();
    var byPuzzle = {}, byDifficulty = {}, correctCount = 0, cluesTotal = 0;
    entries.forEach(function (e) {
      byPuzzle[e.puzzleId] = byPuzzle[e.puzzleId] || { puzzleId: e.puzzleId, count: 0 };
      byPuzzle[e.puzzleId].count++;
      byDifficulty[e.difficulty] = (byDifficulty[e.difficulty] || 0) + 1;
      if (e.correct) correctCount++;
      cluesTotal += e.cluesRevealed || 0;
    });
    var summary = {
      puzzlesSeen: entries.length,
      uniquePuzzlesSeen: Object.keys(byPuzzle).length,
      correctRate: entries.length ? +(correctCount / entries.length * 100).toFixed(1) + '%' : 'n/a',
      avgCluesRevealed: entries.length ? +(cluesTotal / entries.length).toFixed(2) : 'n/a',
      byDifficulty: byDifficulty
    };
    console.log('%c[Player From Clues Playtest] Summary', 'font-weight:bold');
    console.log('Puzzles seen:', summary.puzzlesSeen);
    console.log('Unique puzzles seen:', summary.uniquePuzzlesSeen);
    console.log('Correct rate:', summary.correctRate);
    console.log('Avg clues revealed:', summary.avgCluesRevealed);
    console.log('By difficulty:'); console.table(byDifficulty);
    return summary;
  }

  function exportJSON() {
    var json = JSON.stringify(readLog(), null, 2);
    console.log('%c[Player From Clues Playtest] Export (copy the JSON below)', 'font-weight:bold');
    console.log(json);
    return json;
  }

  function clearLog() {
    try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    console.log('[Player From Clues Playtest] Log cleared.');
  }

  window.PlayerCluesPlaytest = {
    summarize: summarize,
    log: readLog,
    exportJSON: exportJSON,
    clear: clearLog
  };

  console.log(
    '%c[Player From Clues Playtest] instrumentation active — window.PlayerCluesPlaytest.summarize() / .log() / .exportJSON() / .clear()',
    'color:#8a6d1a'
  );
})();
