// Offline regression for the NFL static bank. Run: node --test tests/quiz-content-quality.test.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const data = fs.readFileSync(path.join(__dirname,'..','data','quiz.js'),'utf8');
const first=data.indexOf('[',data.indexOf('window.')),last=data.lastIndexOf(']');
const questions=JSON.parse(data.slice(first,last+1).replace(/,\s*([}\]])/g,'$1'));
const byId=new Map(questions.map(q=>[q.id,q]));

test('home-stadium Super Bowl question never claims Rams were first', () => {
  const q=byId.get(29);
  assert.ok(q);
  assert.match(q.question,/Super Bowl LVI/);
  assert.doesNotMatch(q.question,/first.*(home|own).*stadium/i);
  assert.equal(q.options[q.correctIndex],'Los Angeles Rams');
  assert.match(q.notes,/Tampa Bay/);
});

test('added historic Super Bowl questions have explanatory notes', () => {
  const ids=[1,2,3,4,5,6,7,9,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34];
  for(const id of ids)assert.ok(byId.get(id)?.notes?.trim(), 'missing explanation for '+id);
});

test('all NFL answers have a single valid selectable choice', () => {
  for(const q of questions){
    assert.ok(Array.isArray(q.options)&&q.options.length===4,'wrong option count '+q.id);
    assert.ok(Number.isInteger(q.correctIndex)&&q.correctIndex>=0&&q.correctIndex<4,'invalid answer '+q.id);
    assert.equal(new Set(q.options.map(x=>x.toLowerCase().trim())).size,4,'duplicate options '+q.id);
  }
});

test('every built-in NFL question has a real explanation', () => {
  for (const q of questions) {
    assert.ok(typeof q.notes === 'string' && q.notes.trim().length >= 15,
      'missing or insufficient explanation for NFL question ' + q.id);
  }
});

test('corrected playoff questions have accurate, non-leading premises', () => {
  assert.match(byId.get(51).question, /18 consecutive regular-season/);
  assert.match(byId.get(200).question, /two first-half interceptions/);
  assert.doesNotMatch(byId.get(200).question, /pick-six/);
  assert.match(byId.get(223).question, /rallied from 20 points down/);
  assert.match(byId.get(226).notes, /third-largest comeback/);
  assert.match(byId.get(229).notes, /Frank Wycheck/);
});
