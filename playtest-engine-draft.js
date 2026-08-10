/* ============================================================================
   TEMPORARY PLAYTEST INSTRUMENTATION -- Engine Draft questions only.

   Local human playtest logger for the 100 Engine-generated NFL Draft History
   questions (window.QUIZ_DATA_ENGINE_DRAFT, ids 500000-500099). Not part of
   the app's real feature set -- this file exists to let a developer evaluate
   how those 100 questions feel inside the real Reads UI, then gets deleted
   once the Engine Draft rollout has been played through.

   Design constraints (all deliberate):
   - Zero visible UI. Everything lives in localStorage + the dev console.
   - Zero network calls. Nothing is sent to Firebase, Netlify, or anywhere
     else -- this file makes no fetch/XHR/websocket calls of any kind.
   - Zero effect on gameplay. This file never *writes* app state, never
     changes scoring/deck-ordering/question-selection, and never touches
     window.QUIZ_DATA or window.QUIZ_DATA_ENGINE_DRAFT. It only wraps each
     mode's existing answer-handling function to *observe* (read-only) which
     question was just answered and whether it was correct, then calls the
     original function completely unchanged. Any error in this file is
     caught and swallowed so it can never break the real app, even if some
     future app.js refactor changes a function this expects to exist.
   - Only Engine Draft questions are logged (matched against the exact set
     of ids actually present in window.QUIZ_DATA_ENGINE_DRAFT at load time,
     not a guessed numeric range) -- hand-authored questions are never
     recorded here at all.

   Console commands: see the printed banner below, or window.EngineDraftPlaytest.
   ============================================================================ */
(function () {
  'use strict';

  var STORAGE_KEY = 'reads_engine_draft_playtest_log_v1';
  var MAX_ENTRIES = 2000; // generous cap so a long playtest session can't grow localStorage unbounded

  function engineIdSet() {
    var set = {};
    var arr = window.QUIZ_DATA_ENGINE_DRAFT;
    if (Array.isArray(arr)) {
      for (var i = 0; i < arr.length; i++) {
        if (arr[i] && typeof arr[i].id === 'number') set[arr[i].id] = true;
      }
    }
    return set;
  }

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

  function recordEncounter(question, mode, correct) {
    try {
      if (!question || typeof question.id !== 'number') return;
      if (!engineIdSet()[question.id]) return; // hand-authored question — not logged
      var entries = readLog();
      entries.push({
        id: question.id,
        question: question.question,
        category: question.category,
        difficulty: question.difficulty,
        correct: !!correct,
        mode: mode,
        timestamp: new Date().toISOString()
      });
      writeLog(entries);
    } catch (e) {
      // Never let playtest logging break gameplay.
    }
  }

  // ---- Wrap each mode's existing answer function. Read-only observation:
  // capture the question + "already answered?" guard state (mirroring each
  // function's own internal guard, where present) BEFORE calling the real
  // function, then call the real function completely unmodified. ----

  function wrap(fnName, getQuestion, alreadyAnsweredCheck, mode) {
    var original = window[fnName];
    if (typeof original !== 'function') return; // defensive — never throw if app.js shape changes
    window[fnName] = function (optionIndex) {
      try {
        var wasAlreadyAnswered = alreadyAnsweredCheck ? alreadyAnsweredCheck() : false;
        if (!wasAlreadyAnswered) {
          var q = getQuestion();
          if (q) recordEncounter(q, mode, optionIndex === q.correctIndex);
        }
      } catch (e) {
        // Never let playtest logging break gameplay.
      }
      return original.apply(this, arguments);
    };
  }

  function safeState(path) {
    try {
      var v = window.state;
      for (var i = 0; i < path.length; i++) { if (v == null) return undefined; v = v[path[i]]; }
      return v;
    } catch (e) { return undefined; }
  }

  wrap('pickQuizAnswer',
    function () { return typeof currentQuizQuestion === 'function' ? currentQuizQuestion() : null; },
    function () { return safeState(['quiz', 'answeredIndex']) !== null; },
    'quiz');

  wrap('pickDailyAnswer',
    function () { return typeof currentDailyQuestion === 'function' ? currentDailyQuestion() : null; },
    function () { return safeState(['daily', 'answeredIndex']) !== null; },
    'daily');

  wrap('pickStudyAnswer',
    function () { return typeof currentStudyQuestion === 'function' ? currentStudyQuestion() : null; },
    function () { return safeState(['study', 'answeredIndex']) !== null; },
    'study');

  wrap('registerSpeedAnswer',
    function () { return typeof currentSpeedQuestion === 'function' ? currentSpeedQuestion() : null; },
    function () { return safeState(['speed', 'answeredIndex']) !== null; },
    'speed');

  // IQ Test has no per-question re-answer guard (its own design: "no
  // feedback until the end"), so every call is a genuine new answer.
  wrap('answerIQQuestion',
    function () { return typeof currentIQQuestion === 'function' ? currentIQQuestion() : null; },
    null,
    'iq');

  // ---- Developer console helpers ----

  function summarize() {
    var entries = readLog();
    var byId = {}, byDifficulty = {}, byMode = {}, correctCount = 0;
    entries.forEach(function (e) {
      byId[e.id] = byId[e.id] || { id: e.id, question: e.question, count: 0 };
      byId[e.id].count++;
      byDifficulty[e.difficulty] = (byDifficulty[e.difficulty] || 0) + 1;
      byMode[e.mode] = (byMode[e.mode] || 0) + 1;
      if (e.correct) correctCount++;
    });
    var mostFrequent = Object.keys(byId).map(function (k) { return byId[k]; })
      .sort(function (a, b) { return b.count - a.count; })
      .slice(0, 10);
    var summary = {
      engineQuestionsSeen: entries.length,
      uniqueEngineQuestionsSeen: Object.keys(byId).length,
      correctRate: entries.length ? +(correctCount / entries.length * 100).toFixed(1) + '%' : 'n/a',
      byDifficulty: byDifficulty,
      byMode: byMode,
      mostFrequent: mostFrequent
    };
    console.log('%c[Engine Draft Playtest] Summary', 'font-weight:bold');
    console.log('Engine questions seen:', summary.engineQuestionsSeen);
    console.log('Unique Engine questions seen:', summary.uniqueEngineQuestionsSeen);
    console.log('Correct rate:', summary.correctRate);
    console.log('By difficulty:'); console.table(byDifficulty);
    console.log('By mode:'); console.table(byMode);
    console.log('Most frequently encountered:'); console.table(mostFrequent);
    return summary;
  }

  function exportJSON() {
    var json = JSON.stringify(readLog(), null, 2);
    console.log('%c[Engine Draft Playtest] Export (copy the JSON below)', 'font-weight:bold');
    console.log(json);
    return json;
  }

  function clearLog() {
    try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    console.log('[Engine Draft Playtest] Log cleared.');
  }

  window.EngineDraftPlaytest = {
    summarize: summarize,
    log: readLog,
    exportJSON: exportJSON,
    clear: clearLog
  };

  console.log(
    '%c[Engine Draft Playtest] instrumentation active — window.EngineDraftPlaytest.summarize() / .log() / .exportJSON() / .clear()',
    'color:#8a6d1a'
  );
})();
