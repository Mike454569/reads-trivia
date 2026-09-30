// Engine vNext + Endless Mode
// Global cross-mode content memory, lightweight question QA, and a mixed-rule
// endless run built from the app's existing source-backed NFL/CFB banks.
var CONTENT_MEMORY_LIMIT = 120;
function contentMemoryKey(){return 'readsContentMemory__'+slugify(state.name||'guest');}
function getContentMemory(){var m=lsGet(contentMemoryKey(),[]);return Array.isArray(m)?m:[];}
function questionContentKey(q,league){return (league||'nfl')+':'+String(q&&q.id);}
function questionEntityKey(q){
  if(!q||!q.options||q.correctIndex==null)return '';
  return slugify(String(q.options[q.correctIndex]||''));
}
function rememberContentQuestion(q,league,mode){
  if(!q)return;
  var m=getContentMemory();
  m.push({key:questionContentKey(q,league),entity:questionEntityKey(q),category:q.category||'',league:league||'nfl',mode:mode||'',at:Date.now()});
  lsSet(contentMemoryKey(),m.slice(-CONTENT_MEMORY_LIMIT));
}
function recentContentSets(){
  var q={},e={},cat={}, rows=getContentMemory().slice(-60);
  rows.forEach(function(x){if(x.key)q[x.key]=true;if(x.entity)e[x.entity]=(e[x.entity]||0)+1;if(x.category)cat[x.category]=(cat[x.category]||0)+1;});
  return {questions:q,entities:e,categories:cat};
}
function contentMemoryAllows(q,league){
  var r=recentContentSets(), key=questionContentKey(q,league), ent=questionEntityKey(q);
  if(r.questions[key])return false;
  if(ent && (r.entities[ent]||0)>=2)return false;
  return true;
}
function endlessQuestionQuality(q,league){
  var score=100, reasons=[];
  if(!q||!q.question){return {score:0,reasons:['missing question']};}
  if(!Array.isArray(q.options)||q.options.length<2){return {score:0,reasons:['missing options']};}
  if(q.correctIndex<0||q.correctIndex>=q.options.length){return {score:0,reasons:['invalid answer']};}
  var seen={}, dup=false;
  q.options.forEach(function(o){var k=slugify(String(o));if(seen[k])dup=true;seen[k]=true;});
  if(dup){score-=45;reasons.push('duplicate options');}
  if(String(q.question).length<18){score-=20;reasons.push('thin prompt');}
  if(String(q.question).length>260){score-=10;reasons.push('overlong prompt');}
  if(!q.category){score-=8;reasons.push('missing category');}
  if(!q.difficulty){score-=5;reasons.push('missing difficulty');}
  if(!contentMemoryAllows(q,league)){score-=35;reasons.push('recent content');}
  return {score:Math.max(0,score),reasons:reasons};
}
function filterFreshQuestions(pool,league,minScore){
  var fresh=(pool||[]).filter(function(q){return endlessQuestionQuality(q,league).score>=(minScore||70);});
  return fresh.length>=10?fresh:(pool||[]).filter(function(q){return endlessQuestionQuality(q,league).score>=55;});
}

var ENDLESS_MECHANICS=[
  {id:'quick',label:'Quick Pick',desc:'Four choices. Keep moving.'},
  {id:'fifty',label:'50 / 50',desc:'Two choices. No hiding.'},
  {id:'double',label:'Double Down',desc:'Two choices. Double points.'},
  {id:'survival',label:'Survival',desc:'A miss costs two lives.'}
];
var ENDLESS={active:false,screen:'idle',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],mechanicIndex:0,league:'nfl',multiplier:1,correct:0,total:0,history:[]};

function endlessDifficultyLevel(){
  var base=0;
  if(ENDLESS.index>=18)base=2; else if(ENDLESS.index>=7)base=1;
  if(ENDLESS.streak>=8)base++;
  return Math.min(2,base);
}
function endlessDifficultyNames(level){return level===0?['Easy','Medium']:level===1?['Medium','Hard']:['Hard','Expert'];}
function endlessChooseLeague(){
  var profile=typeof personalizationLeagueProfile==='function'?personalizationLeagueProfile():null;
  if(ENDLESS.index%2===1)return ENDLESS.league==='nfl'?'cfb':'nfl';
  if(profile&&profile.nfl.avg!=null&&profile.cfb.avg!=null)return profile.nfl.avg<=profile.cfb.avg?'nfl':'cfb';
  return ENDLESS.index%2?'cfb':'nfl';
}
function endlessMechanic(){return ENDLESS_MECHANICS[Math.floor(ENDLESS.index/3)%ENDLESS_MECHANICS.length];}
function endlessPickQuestion(){
  var league=endlessChooseLeague(), source=league==='cfb'?CFB:QUIZ, level=endlessDifficultyLevel(), names=endlessDifficultyNames(level);
  var pool=source.filter(function(q){return names.indexOf(q.difficulty)!==-1;});
  if(pool.length<20)pool=source.slice();
  pool=filterFreshQuestions(pool,league,70);
  if(!pool.length)pool=source.slice();
  var recentRun={};ENDLESS.history.slice(-25).forEach(function(x){recentRun[x.key]=true;});
  var candidates=pool.filter(function(q){return !recentRun[questionContentKey(q,league)];});
  if(!candidates.length)candidates=pool;
  var seed=hashStr((state.name||'guest')+'|'+Date.now()+'|'+ENDLESS.index);
  var q=candidates[Math.abs(seed)%candidates.length];
  var mech=endlessMechanic(), visible=q.options.map(function(_,i){return i;});
  if(mech.id==='fifty'||mech.id==='double'){
    var wrong=visible.filter(function(i){return i!==q.correctIndex;});
    visible=[q.correctIndex,wrong[Math.abs(seed>>3)%wrong.length]];
    visible=seededShuffle(visible,mulberry32(seed));
  }
  ENDLESS.league=league;ENDLESS.current=q;ENDLESS.visible=visible;ENDLESS.answered=null;ENDLESS.mechanicIndex=0;
}
function startEndlessMode(){
  if (typeof beginProgressSession === 'function') beginProgressSession('endless');
  ENDLESS={active:true,screen:'question',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],mechanicIndex:0,league:'nfl',multiplier:1,correct:0,total:0,history:[]};
  state.screen='endless'; lsSet('nflTriviaLastMode','endless');
  if(window.__fbSync&&window.__fbSync.logPlay)window.__fbSync.logPlay('endless');
  endlessPickQuestion(); renderAll();
}
function answerEndless(i){
  if(!ENDLESS.active||ENDLESS.screen!=='question'||ENDLESS.answered!==null)return;
  var q=ENDLESS.current, mech=endlessMechanic(), good=i===q.correctIndex;
  ENDLESS.answered=i;ENDLESS.total++;
  rememberContentQuestion(q,ENDLESS.league,'endless');
  if(typeof recordKnowledgeAnswer==='function')recordKnowledgeAnswer(ENDLESS.league,q.category||'General',good);
  if(good){
    ENDLESS.correct++;ENDLESS.streak++;ENDLESS.bestStreak=Math.max(ENDLESS.bestStreak,ENDLESS.streak);
    ENDLESS.multiplier=Math.min(5,1+Math.floor(ENDLESS.streak/3));
    var base=100*(mech.id==='double'?2:1);ENDLESS.score+=base*ENDLESS.multiplier;
  }else{
    ENDLESS.lives-=mech.id==='survival'?2:1;ENDLESS.streak=0;ENDLESS.multiplier=1;
  }
  ENDLESS.history.push({key:questionContentKey(q,ENDLESS.league),good:good,mechanic:mech.id});
  playSound(good?'correct':'wrong'); renderAll();
}
function nextEndless(){
  if(ENDLESS.answered===null)return;
  if(ENDLESS.lives<=0){finishEndless();return;}
  ENDLESS.index++; endlessPickQuestion(); renderAll();
}
function endlessBestKey(){return 'readsEndlessBest__'+slugify(state.name||'guest');}
function recordEndlessPersonalization(pct){
  if(!state.name || typeof getPersonalizationState!=='function') return;
  var p=getPersonalizationState();
  p.playEvents.push({mode:'endless',league:'mixed',at:Date.now(),pct:pct});
  setPersonalizationState(p,true);
  if(typeof checkWeeklyPersonalGoals==='function')checkWeeklyPersonalGoals();
  if(typeof checkWeeklyRetentionReward==='function')checkWeeklyRetentionReward();
}
function finishEndless(){
  ENDLESS.screen='summary';ENDLESS.active=false;
  var best=lsGet(endlessBestKey(),{score:0,questions:0});
  if(ENDLESS.score>(best.score||0))lsSet(endlessBestKey(),{score:ENDLESS.score,questions:ENDLESS.total,streak:ENDLESS.bestStreak,at:Date.now()});
  if(state.name){
    var pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
    updateRatingDrift(pct);
    recordEndlessPersonalization(pct);
    if(typeof awardProgressEvent==='function')awardProgressEvent('ENDLESS_FINISH',Math.min(150,25+ENDLESS.total*3),{score:ENDLESS.score,questions:ENDLESS.total});
  }
  playSound('complete');renderAll();
}
function endlessHomeCardHtml(){
  var best=lsGet(endlessBestKey(),null);
  return '<section class="endless-home-card"><div><span class="dashboard-eyebrow">SIGNATURE MODE</span><h3>Endless Reads</h3><p>One run. NFL + CFB. Rules change every three questions. Difficulty climbs until you run out of lives.</p>'+(best?'<small>Best: '+best.score.toLocaleString()+' pts · '+best.questions+' questions</small>':'<small>Your first run starts with 3 lives.</small>')+'</div><button class="btn-primary" data-endless-start>Go Endless</button></section>';
}
function endlessQualityBadge(q){
  var qa=endlessQuestionQuality(q,ENDLESS.league);
  return '<span class="endless-qa">QA '+qa.score+'</span>';
}
function renderEndlessScreen(){
  if(ENDLESS.screen==='summary'){
    var pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
    return '<div class="panel endless-panel">'+modeToolbarHtml('endless',true)+broadcastResultHtml('ENDLESS RUN OVER',ENDLESS.score.toLocaleString()+' PTS',ENDLESS.correct+'/'+ENDLESS.total+' correct · '+pct+'% · best streak '+ENDLESS.bestStreak,pct>=70)+'<div class="endless-summary-grid"><div><b>'+ENDLESS.total+'</b><span>Questions</span></div><div><b>'+ENDLESS.bestStreak+'</b><span>Best Streak</span></div><div><b>'+ENDLESS.score.toLocaleString()+'</b><span>Score</span></div></div><div class="btn-row"><button class="btn-primary" data-endless-start>Run It Back</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  var q=ENDLESS.current;if(!q)return '<div class="panel">Building your run…</div>';
  var mech=endlessMechanic(),answered=ENDLESS.answered!==null;
  return '<div class="panel endless-panel">'+modeToolbarHtml('endless',true)+
    '<div class="endless-scorebar"><span>❤️ '+Math.max(0,ENDLESS.lives)+'</span><span>🔥 '+ENDLESS.streak+'</span><span>×'+ENDLESS.multiplier+'</span><strong>'+ENDLESS.score.toLocaleString()+' PTS</strong></div>'+
    '<div class="endless-rule"><span>'+esc(mech.label)+'</span><b>'+esc(mech.desc)+'</b>'+endlessQualityBadge(q)+'</div>'+
    '<div class="quiz-progress">QUESTION '+(ENDLESS.index+1)+' · '+ENDLESS.league.toUpperCase()+' · '+esc(q.category)+' · '+esc(q.difficulty)+'</div>'+
    '<section class="stadium-question-card"><div class="quiz-question stadium-question">'+esc(q.question)+'</div></section>'+
    '<div class="quiz-options">'+ENDLESS.visible.map(function(i){var cls='quiz-option';if(answered){if(i===q.correctIndex)cls+=' correct';else if(i===ENDLESS.answered)cls+=' wrong';}return '<button class="'+cls+'" '+(answered?'disabled':'data-endless-answer="'+i+'"')+'><span class="broadcast-option-letter">'+String.fromCharCode(65+i)+'</span><span>'+esc(q.options[i])+'</span></button>';}).join('')+'</div>'+
    (answered?'<div class="quiz-feedback">'+(ENDLESS.answered===q.correctIndex?'<span class="feedback-good">'+icon('check')+' Correct.</span>':'<span class="feedback-bad">'+icon('xMark')+' Missed it. '+Math.max(0,ENDLESS.lives)+' lives left.</span>')+(q.notes?' '+esc(q.notes):'')+'</div><button class="btn-primary" data-endless-next>'+(ENDLESS.lives<=0?'See Run Results':'Keep Going')+'</button>':'')+'</div>';
}
