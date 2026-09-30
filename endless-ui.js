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
var ENDLESS={active:false,screen:'idle',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],league:'nfl',multiplier:1,correct:0,total:0,history:[],isNewBest:false,lastEvent:null};

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
function endlessNextMechanic(){
  return ENDLESS_MECHANICS[(Math.floor(ENDLESS.index/3)+1)%ENDLESS_MECHANICS.length];
}
function endlessQuestionsUntilRuleChange(){
  return 3-(ENDLESS.index%3);
}
function endlessMomentumPct(){
  return Math.min(100,Math.max(8,ENDLESS.streak*12+ENDLESS.multiplier*8));
}
function endlessQuestionNumber(){return ENDLESS.index+1;}
function endlessStage(){
  var n=endlessQuestionNumber();
  if(n>=30)return {id:'sudden',label:'SUDDEN DEATH',desc:'One miss ends the run.',multiplier:3};
  if(n>=20)return {id:'primetime',label:'PRIME TIME',desc:'The questions tighten up.',multiplier:1};
  if(n>=10)return {id:'redzone',label:'RED ZONE',desc:'Pressure is climbing.',multiplier:1};
  return {id:'drive',label:'OPENING DRIVE',desc:'Build the run.',multiplier:1};
}
function endlessSpecialEvent(){
  var n=endlessQuestionNumber();
  if(n>=30)return {id:'sudden',label:'SUDDEN DEATH',desc:'Triple points. One miss ends it.',scoreMult:3,restore:false};
  if(n%10===0)return {id:'checkpoint',label:'CHECKPOINT',desc:ENDLESS.lives<3?'Get it right to win back a life.':'Protect the perfect stack.',scoreMult:2,restore:ENDLESS.lives<3};
  if(n%5===0)return {id:'clutch',label:'CLUTCH QUESTION',desc:'Double points. Make it count.',scoreMult:2,restore:false};
  return null;
}
function endlessBestChase(){
  var best=lsGet(endlessBestKey(),null), bestScore=best?Number(best.score)||0:0, gap=Math.max(0,bestScore-ENDLESS.score);
  if(!bestScore)return '<span>SET THE STANDARD</span><b>First run sets your personal best</b>';
  if(gap===0)return '<span>PERSONAL BEST</span><b>You are at the mark right now</b>';
  return '<span>PB CHASE</span><b>'+gap.toLocaleString()+' pts to your best</b>';
}
function endlessEventHtml(){
  var ev=endlessSpecialEvent(), stage=endlessStage();
  return '<div class="endless-stage-row stage-'+stage.id+'">' +
    '<div class="endless-stage-copy"><span>'+esc(stage.label)+'</span><b>'+esc(stage.desc)+'</b></div>' +
    '<div class="endless-best-chase">'+endlessBestChase()+'</div>' +
    (ev?'<div class="endless-event-card event-'+ev.id+'"><span>'+esc(ev.label)+'</span><b>'+esc(ev.desc)+'</b></div>':'') +
    '</div>';
}
function endlessRunStatusHtml(){
  var left=endlessQuestionsUntilRuleChange(), next=endlessNextMechanic(), difficulty=endlessDifficultyNames(endlessDifficultyLevel())[0];
  return '<div class="endless-run-status">' +
    '<div class="endless-momentum"><div><span>MOMENTUM</span><b>'+(ENDLESS.streak>=8?'ON FIRE':ENDLESS.streak>=4?'HEATING UP':ENDLESS.streak?'BUILDING':'FRESH RUN')+'</b></div>' +
    '<div class="endless-momentum-track"><i style="width:'+endlessMomentumPct()+'%"></i></div></div>' +
    '<div class="endless-run-chip"><span>NEXT RULE</span><b>'+esc(next.label)+' · '+left+' Q'+(left===1?'':'S')+'</b></div>' +
    '<div class="endless-run-chip"><span>DIFFICULTY</span><b>'+esc(difficulty)+'</b></div>' +
    '</div>';
}
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
  ENDLESS={active:true,screen:'question',score:0,lives:3,streak:0,bestStreak:0,index:0,answered:null,current:null,visible:[],league:'nfl',multiplier:1,correct:0,total:0,history:[],isNewBest:false,lastEvent:null};
  state.screen='endless';lsSet('nflTriviaLastMode','endless');
  if(window.__fbSync&&window.__fbSync.logPlay)window.__fbSync.logPlay('endless');
  endlessPickQuestion();renderAll();
}
function answerEndless(i){
  if(!ENDLESS.active||ENDLESS.screen!=='question'||ENDLESS.answered!==null||!ENDLESS.current)return;
  var q=ENDLESS.current, mech=endlessMechanic(), good=i===q.correctIndex;
  ENDLESS.answered=i;ENDLESS.total++;
  if(typeof recordKnowledgeAnswer==='function')recordKnowledgeAnswer(ENDLESS.league,q.category||'General',good);
  var event=endlessSpecialEvent(), eventMult=event?event.scoreMult:1, restored=false;
  if(good){
    ENDLESS.correct++;ENDLESS.streak++;ENDLESS.bestStreak=Math.max(ENDLESS.bestStreak,ENDLESS.streak);
    ENDLESS.multiplier=Math.min(5,1+Math.floor(ENDLESS.streak/3));
    ENDLESS.score+=100*(mech.id==='double'?2:1)*ENDLESS.multiplier*eventMult;
    if(event&&event.restore&&ENDLESS.lives<3){ENDLESS.lives++;restored=true;}
    removeFromMissedPool(ENDLESS.league,q.id);
  }else{
    if(event&&event.id==='sudden')ENDLESS.lives=0;
    else ENDLESS.lives-=mech.id==='survival'?2:1;
    ENDLESS.streak=0;ENDLESS.multiplier=1;
    addToMissedPool(ENDLESS.league,q.id);
  }
  ENDLESS.lastEvent=event?{id:event.id,label:event.label,good:good,restored:restored,scoreMult:eventMult}:null;
  ENDLESS.history.push({key:endlessQuestionKey(q,ENDLESS.league),good:good,mechanic:mech.id,event:event&&event.id});
  playSound(good?'correct':'wrong');renderAll();
}
function nextEndless(){
  if(ENDLESS.answered===null)return;
  if(ENDLESS.lives<=0){finishEndless();return;}
  ENDLESS.index++;ENDLESS.lastEvent=null;
  if(!endlessPickQuestion()){finishEndless();return;}
  renderAll();
}
function endlessBestKey(){return 'readsEndlessBest__'+slugify(state.name||'guest');}
function finishEndless(){
  if(ENDLESS.screen==='summary')return;
  ENDLESS.screen='summary';ENDLESS.active=false;
  var best=lsGet(endlessBestKey(),{score:0,questions:0,streak:0}), pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
  ENDLESS.isNewBest=ENDLESS.score>(best.score||0);
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
function renderEndlessScreen(){
  if(ENDLESS.screen==='summary'){
    var pct=ENDLESS.total?Math.round(100*ENDLESS.correct/ENDLESS.total):0;
    return '<div class="panel endless-panel">'+modeToolbarHtml('endless',true)+(ENDLESS.isNewBest?'<div class="endless-record-burst"><span>NEW PERSONAL BEST</span><b>'+ENDLESS.score.toLocaleString()+' PTS</b></div>':'')+broadcastResultHtml('ENDLESS RUN OVER',ENDLESS.score.toLocaleString()+' PTS',ENDLESS.correct+'/'+ENDLESS.total+' correct · '+pct+'% · best streak '+ENDLESS.bestStreak,pct>=70)+'<div class="endless-summary-grid"><div><b>'+ENDLESS.total+'</b><span>Questions</span></div><div><b>'+ENDLESS.bestStreak+'</b><span>Best Streak</span></div><div><b>'+ENDLESS.score.toLocaleString()+'</b><span>Score</span></div><div><b>'+state.stats.endless.bestScore.toLocaleString()+'</b><span>All-Time Best</span></div></div><div class="btn-row"><button class="btn-primary" data-endless-start>Run It Back</button><button class="btn-secondary" data-go="leaderboard">Leaderboard</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  var q=ENDLESS.current;if(!q)return '<div class="panel">Building your run…</div>';
  var mech=endlessMechanic(),answered=ENDLESS.answered!==null;
  return '<div class="panel endless-panel">'+modeToolbarHtml('endless',true)+
    '<div class="endless-scorebar"><span class="endless-stat-pill">❤️ <b>'+Math.max(0,ENDLESS.lives)+'</b><small>LIVES</small></span><span class="endless-stat-pill">🔥 <b>'+ENDLESS.streak+'</b><small>STREAK</small></span><span class="endless-stat-pill">×<b>'+ENDLESS.multiplier+'</b><small>MULTI</small></span><strong>'+ENDLESS.score.toLocaleString()+' <small>PTS</small></strong></div>'+endlessEventHtml()+endlessRunStatusHtml()+
    '<div class="endless-rule"><span>'+esc(mech.label)+'</span><b>'+esc(mech.desc)+'</b><em>RULE '+(Math.floor(ENDLESS.index/3)%ENDLESS_MECHANICS.length+1)+' / '+ENDLESS_MECHANICS.length+'</em></div>'+
    '<div class="quiz-progress">QUESTION '+(ENDLESS.index+1)+' · '+ENDLESS.league.toUpperCase()+' · '+esc(q.category)+' · '+esc(q.difficulty)+'</div>'+
    '<section class="stadium-question-card"><div class="quiz-question stadium-question">'+esc(q.question)+'</div></section>'+
    '<div class="quiz-options">'+ENDLESS.visible.map(function(i){var cls='quiz-option';if(answered){if(i===q.correctIndex)cls+=' correct';else if(i===ENDLESS.answered)cls+=' wrong';}return '<button class="'+cls+'" '+(answered?'disabled':'data-endless-answer="'+i+'"')+'><span class="broadcast-option-letter">'+String.fromCharCode(65+i)+'</span><span>'+esc(q.options[i])+'</span></button>';}).join('')+'</div>'+
    (answered?'<div class="quiz-feedback endless-answer-feedback">'+(ENDLESS.answered===q.correctIndex?'<span class="feedback-good">'+icon('check')+' Correct.</span>':'<span class="feedback-bad">'+icon('xMark')+' '+(ENDLESS.lives<=0?'Run over.':Math.max(0,ENDLESS.lives)+' lives left.')+'</span>')+(ENDLESS.lastEvent&&ENDLESS.lastEvent.good&&ENDLESS.lastEvent.scoreMult>1?' <strong>×'+ENDLESS.lastEvent.scoreMult+' event bonus.</strong>':'')+(ENDLESS.lastEvent&&ENDLESS.lastEvent.restored?' <strong>Life restored.</strong>':'')+(q.notes?' '+esc(q.notes):'')+'</div><button class="btn-primary" data-endless-next>'+(ENDLESS.lives<=0?'See Run Results':'Keep Going')+'</button>':'')+'</div>';
}
