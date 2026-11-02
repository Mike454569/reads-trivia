#!/usr/bin/env node
// Offline static-bank quality audit. No network, database, deployments, or API calls.
// Usage: node tools/audit_static_trivia.cjs
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const banks = [['NFL','data/quiz.js'],['CFB','data/cfb.js']];
const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9 ]+/g,' ').replace(/\s+/g,' ').trim();
function loadBank(file) {
  const raw = fs.readFileSync(path.join(root,file),'utf8');
  const start = raw.indexOf('[', raw.indexOf('window.'));
  const end = raw.lastIndexOf(']');
  if(start < 0 || end <= start) throw new Error('Missing array in '+file);
  // Existing JS banks are JSON-shaped with some trailing commas.
  return JSON.parse(raw.slice(start,end+1).replace(/,\s*([}\]])/g,'$1'));
}
function audit(league, rows) {
  const issues=[], prompts=new Map(), clusters=new Map(), categories={};
  const stop = new Set(['the','of','a','and','to','in','is','was','which','who','what','when','where','did','for','with','from','on','at','his','her','their','team','player','nfl','cfb','college','football','season']);
  for(const q of rows) {
    const p=norm(q.question), options=Array.isArray(q.options)?q.options.map(norm):[];
    categories[q.category]=(categories[q.category]||0)+1;
    const add=(type,detail)=>issues.push({id:q.id,type,detail});
    if(p.length<14) add('SHORT_PROMPT',q.question);
    if(p.length>220) add('LONG_PROMPT',q.question);
    if(!options.length || options.some(x=>!x) || new Set(options).size!==options.length || !Number.isInteger(q.correctIndex) || q.correctIndex<0 || q.correctIndex>=options.length) add('INVALID_CHOICES',q.question);
    if(/\b(all|none) of the above\b/i.test(q.options?.[q.correctIndex]||'')) add('WEAK_CORRECT_ANSWER',q.question);
    if(!String(q.notes||'').trim()) add('MISSING_EXPLANATION',q.question);
    const answer=options[q.correctIndex]||'';
    if(answer.length>=9&&p.includes(answer)&&!/(which (?:year|season|game)|which of these|how many)/i.test(q.question)) add('POSSIBLE_ANSWER_LEAK',q.question);
    if(prompts.has(p)) add('EXACT_REPEAT','Matches '+prompts.get(p)); else prompts.set(p,q.id);
    // Same answer and high overlap signals fact reuse; this is a review flag,
    // not automatic deletion (one player can support distinct legitimate facts).
    const tokens=new Set(p.split(' ').filter(x=>x.length>3&&!stop.has(x)));
    const key=(q.category||'')+'|'+answer;
    if(!clusters.has(key))clusters.set(key,[]);
    clusters.get(key).push({id:q.id,tokens,prompt:q.question});
  }
  for(const entries of clusters.values()){
    for(let i=0;i<entries.length;i++)for(let j=i+1;j<entries.length;j++){
      const a=entries[i],b=entries[j],both=[...a.tokens].filter(t=>b.tokens.has(t)).length;
      const similarity=both/Math.max(1,new Set([...a.tokens,...b.tokens]).size);
      if(similarity>=0.55&&both>=2)issues.push({id:b.id,type:'POSSIBLE_SAME_FACT',detail:'Similar to #'+a.id+' ('+similarity.toFixed(2)+')'});
    }
  }
  return {league,questions:rows.length,categories,flags:issues.length,byType:Object.fromEntries([...new Set(issues.map(x=>x.type))].sort().map(type=>[type,issues.filter(x=>x.type===type).length])),examples:issues.slice(0,30)};
}
const results=banks.map(([name,file])=>audit(name,loadBank(file)));
console.log(JSON.stringify(results,null,2));
// This audit is informational, so existing copy concerns do not fail builds.
// Data-shape failures, however, must stop an offline review.
if(results.some(r=>r.byType.INVALID_CHOICES || r.byType.EXACT_REPEAT))process.exitCode=1;
