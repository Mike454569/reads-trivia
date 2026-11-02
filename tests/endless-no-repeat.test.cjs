// Run locally: node --test tests/endless-no-repeat.test.cjs
// No browser, API, backend database, paid providers, or network required.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const script = fs.readFileSync(path.join(__dirname, '..', 'endless-ui.js'), 'utf8');

function question(id, prompt) {
  return { id, question: prompt, category: 'General', difficulty: 'Easy',
    options: ['A', 'B', 'C', 'D'], correctIndex: 0 };
}
function context(nfl, cfb) {
  const ctx = {
    QUIZ: nfl, CFB: cfb, state: { name: 'test' }, window: {},
    getRating: () => null, hashStr: () => 1234,
    normName: v => String(v || '').toLowerCase().trim(),
    contentFingerprint: (q, l) => l + '|' + q.question.toLowerCase().trim(),
    contentRepeatPenalty: () => 0, questionQualityScore: () => 100,
    rememberContentQuestion: () => {}, seededShuffle: a => a,
    mulberry32: () => () => 0.5, endlessPlanEvent: () => null,
    endlessFavoriteTeamForLeague: () => null,
  };
  vm.createContext(ctx);
  vm.runInContext(script, ctx);
  return ctx;
}

test('does not replay the same question under a new ID', () => {
  const ctx = context([
    question(1, 'A real recognizable football trivia question?'),
    question(2, 'A real recognizable football trivia question?'),
    question(3, 'Another recognizable professional football question?'),
  ], []);
  const first = ctx.endlessPickQuestion();
  ctx.ENDLESS.history.push({fingerprint: ctx.endlessQuestionIdentity(first, ctx.ENDLESS.league)});
  const next = ctx.endlessPickQuestion();
  assert.ok(next);
  assert.notEqual(first.question, next.question);
});

test('switches leagues when one pool is exhausted', () => {
  const ctx = context([
    question(1, 'Another recognizable professional football question?')
  ], [
    question(2, 'A distinct recognizable college football question?')
  ]);
  ctx.ENDLESS.history.push({fingerprint: 'nfl|another recognizable professional football question?'});
  const result = ctx.endlessPickQuestion();
  assert.equal(result.id, 2);
  assert.equal(ctx.ENDLESS.league, 'cfb');
});

test('does not recycle content after both league pools run out', () => {
  const ctx = context([
    question(1, 'Another recognizable professional football question?')
  ], [
    question(2, 'A distinct recognizable college football question?')
  ]);
  ctx.ENDLESS.history.push({fingerprint: 'nfl|another recognizable professional football question?'});
  ctx.ENDLESS.history.push({fingerprint: 'cfb|a distinct recognizable college football question?'});
  assert.equal(ctx.endlessPickQuestion(), null);
});

test('rejects invalid answer lists rather than showing junk', () => {
  const bad = question(1, 'A question with invalid duplicated answer choices?');
  bad.options = ['same', 'same', 'C', 'D'];
  const ctx = context([bad], []);
  assert.equal(ctx.endlessPickQuestion(), null);
});
