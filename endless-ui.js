// Engine vNext — Endless Reads
// Mixed NFL/CFB survival mode using app.js's shared content-memory + QA layer.
// One source of truth: contentFingerprint/contentRepeatPenalty/questionQualityScore/
// rememberContentQuestion all live in app.js and are also used by Quiz/CFB/Daily.
var ENDLESS_MECHANICS=[
  {id:'quick',label:'Quick Pick',desc:'Four choices. Keep moving.'},
  {id:'fifty',label:'50 / 50',desc:'Two choices. No hiding.'},
  {id:'double',label:'Double Down',desc:'Two choices. Double points.'},
  {id:'survival',label:'Survival',desc:'A miss costs two lives.'}
];
var ENDLESS={active:false,screen:'idle',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],league:'nfl',multiplier:1,correct:0,total:0,history:[]};

function endlessDifficultyLevel(){
  var base=0, rating=getRating(), rs=rating?Number(rating.score)||100:100;
  if(rs>=135)base=2; else if(rs>=105)base=1;
  if(ENDLESS.index>=18)base++; else if(ENDLESS.index>=7)base+=1;
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
function endlessQuestionKey(q,league){return league+':'+String(q&&q.id);}
function endlessPickQuestion(){
  var league=endlessChooseLeague(), source=league==='cfb'?CFB:QUIZ, level=endlessDifficultyLevel(), names=endlessDifficultyNames(level);
  var pool=source.filter(function(q){return names.indexOf(q.difficulty)!==-1;});
  if(pool.length<20)pool=source.slice();
  pool=qualityFilteredQuestions(pool,league,names[0]).filter(function(q){return contentRepeatPenalty(q,league)<60;});
  if(!pool.length)pool=qualityFilteredQuestions(source,league,names[0]);
  var recent={};ENDLESS.history.slice(-30).forEach(function(x){recent[x.key]=true;});
  var candidates=pool.filter(function(q){return !recent[endlessQuestionKey(q,league)];});
  if(!candidates.length)candidates=pool;
  if(!candidates.length)return null;
  candidates.sort(function(a,b){return questionQualityScore(b,league,names[0])-questionQualityScore(a,league,names[0]);});
  var seed=hashStr((state.name||'guest')+'|'+Date.now()+'|'+ENDLESS.index);
  var top=candidates.slice(0,Math.min(16,candidates.length));
  var q=top[Math.abs(seed)%top.length], mech=endlessMechanic(), visible=q.options.map(function(_,i){return i;});
  if(mech.id==='fifty'||mech.id==='double'){
    var wrong=visible.filter(function(i){return i!==q.correctIndex;});
    visible=[q.correctIndex,wrong[Math.abs(seed>>3)%wrong.length]];
    visible=seededShuffle(visible,mulberry32(seed));
  }
  ENDLESS.league=league;ENDLESS.current=q;ENDLESS.visible=visible;ENDLESS.answered=null;
  rememberContentQuestion(q,league);
  return q;
}
function startEndlessMode(){
  if(typeof beginProgressSession==='function')beginProgressSession('endless');
  ENDLESS={active:true,screen:'question',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],league:'nfl',multiplier:1,correct:0,total:0,history:[]};
  state.screen='endless';lsSet('nflTriviaLastMode','endless');
  if(window.__fbSync&&window.__fbSync.logPlay)window.__fbSync.logPlay('endless');
  endlessPickQuestion();renderAll();
}
function answerEndless(i){
  if(!ENDLESS.active||ENDLESS.screen!=='question'||ENDLESS.answered!==null||!ENDLESS.current)return;
  var q=ENDLESS.current, mech=endlessMechanic(), good=i===q.correctIndex;
  ENDLESS.answered=i;ENDLESS.total++;
  if(typeof recordKnowledgeAnswer==='function')recordKnowledgeAnswer(ENDLESS.league,q.category||'General',good);
  if(good){
    ENDLESS.correct++;ENDLESS.streak++;ENDLESS.bestStreak=Math.max(ENDLESS.bestStreak,ENDLESS.streak);
    ENDLESS.multiplier=Math.min(5,1+Math.floor(ENDLESS.streak/3));
    ENDLESS.score+=100*(mech.id==='double'?2:1)*ENDLESS.multiplier;
    removeFromMissedPool(ENDLESS.league,q.id);
  }else{
    ENDLESS.lives-=mech.id==='survival'?2:1;ENDLESS.streak=0;ENDLESS.multiplier=1;
    addToMissedPool(ENDLESS.league,q.id);
  }
  ENDLESS.history.push({key:endlessQuestionKey(q,ENDLESS.league),good:good,mechanic:mech.id});
  playSound(good?'correct':'wrong');renderAll();
}
function nextEndless(){
  if(ENDLESS.answered===null)return;
  if(ENDLESS.lives<=0){finishEndless();return;}
  ENDLESS.index++;
  if(!endlessPickQuestion()){finishEndless();return;}
  renderAll();
}
function endlessBestKey(){return 'readsEndlessBest__'+slugify(state.name||'guest');}
function finishEndless(){
  if(ENDLESS.screen==='summary')return;
  ENDLESS.screen='summary';ENDLESS.active=false;
  var best=lsGet(endlessBestKey(),{score:0,questions:0,streak:0}), pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
  best={score:Math.max(best.score||0,ENDLESS.score),questions:Math.max(best.questions||0,ENDLESS.total),streak:Math.max(best.streak||0,ENDLESS.bestStreak),at:Date.now()};
  lsSet(endlessBestKey(),best);
  var st=state.stats.endless||(state.stats.endless={bestScore:0,bestStreak:0,bestQuestions:0,runs:0});
  st.bestScore=Math.max(st.bestScore||0,ENDLESS.score);st.bestStreak=Math.max(st.bestStreak||0,ENDLESS.bestStreak);st.bestQuestions=Math.max(st.bestQuestions||0,ENDLESS.total);st.runs=(st.runs||0)+1;
  lsSet('nflTriviaStats',state.stats);
  if(ENDLESS.total)updateRatingDrift(pct);
  pushLeaderboard('endless',{bestScore:st.bestScore,bestStreak:st.bestStreak,bestQuestions:st.bestQuestions,runs:st.runs,lastPct:pct});
  playSound('complete');renderAll();
}
function endlessHomeCardHtml(){
  var best=lsGet(endlessBestKey(),null);
  return '<button class="discover-card endless-home-card" data-endless-start><span class="discover-card-icon">'+icon('zap')+'</span><span><b>Endless Reads</b><small>NFL + College. Rules change every three questions. Difficulty climbs until your lives are gone.</small>'+(best?'<em>Best: '+Number(best.score||0).toLocaleString()+' pts · '+(best.questions||0)+' questions</em>':'<em>Start with 3 lives.</em>')+'</span>'+icon('arrowRight')+'</button>';
}
function endlessQualityBadge(q){return '<span class="endless-qa">QA '+questionQualityScore(q,ENDLESS.league,endlessDifficultyNames(endlessDifficultyLevel())[0])+'</span>';}
function renderEndlessScreen(){
  if(ENDLESS.screen==='summary'){
    var pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
    return '<div class="panel endless-panel">'+modeToolbarHtml('endless',true)+broadcastResultHtml('ENDLESS RUN OVER',ENDLESS.score.toLocaleString()+' PTS',ENDLESS.correct+'/'+ENDLESS.total+' correct · '+pct+'% · best streak '+ENDLESS.bestStreak,pct>=70)+'<div class="endless-summary-grid"><div><b>'+ENDLESS.total+'</b><span>Questions</span></div><div><b>'+ENDLESS.bestStreak+'</b><span>Best Streak</span></div><div><b>'+ENDLESS.score.toLocaleString()+'</b><span>Score</span></div><div><b>'+state.stats.endless.bestScore.toLocaleString()+'</b><span>All-Time Best</span></div></div><div class="btn-row"><button class="btn-primary" data-endless-start>Run It Back</button><button class="btn-secondary" data-go="leaderboard">Leaderboard</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
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
