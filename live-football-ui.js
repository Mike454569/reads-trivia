// Live Football Layer v1
// Uses the already-public Weekly Pick'em view as the single source of truth
// for current-week schedules and FINAL scores. The Gateway only exposes
// winner/score after a game is actually FINAL, so this layer never invents
// or guesses live results. Browser refreshes are lightweight reads of that
// existing public surface; they do not trigger the heavy Engine DB refresh.
var LIVE_FOOTBALL = {
  nfl: null, cfb: null, loading: false, error: null, fetchedAt: 0,
  challenge: null, refreshTimer: null
};
var LIVE_FOOTBALL_REFRESH_MS = 3 * 60 * 1000;

function liveFootballLeaguePath(league) {
  var path = '/v1/public/pickem/' + league.toLowerCase() + '?client_id=' + encodeURIComponent(getClientId());
  if (league === 'CFB') path += '&slate=FULL';
  return path;
}
function liveFootballFetchLeague(league) {
  return enginePilotFetchJson(liveFootballLeaguePath(league));
}
function liveFootballMaybeRefresh(force) {
  if (!ENABLE_PICKEM_V01 || LIVE_FOOTBALL.loading) return;
  if (!force && LIVE_FOOTBALL.fetchedAt && Date.now() - LIVE_FOOTBALL.fetchedAt < LIVE_FOOTBALL_REFRESH_MS) return;
  LIVE_FOOTBALL.loading = true;
  LIVE_FOOTBALL.error = null;
  Promise.all([liveFootballFetchLeague('NFL'), liveFootballFetchLeague('CFB')]).then(function (rows) {
    LIVE_FOOTBALL.nfl = rows[0];
    LIVE_FOOTBALL.cfb = rows[1];
    LIVE_FOOTBALL.fetchedAt = Date.now();
    LIVE_FOOTBALL.loading = false;
    liveFootballMarkNewFinals();
    if (state && (state.screen === 'home' || state.screen === 'liveFootball')) renderAll();
    liveFootballScheduleRefresh();
  }).catch(function (err) {
    LIVE_FOOTBALL.loading = false;
    LIVE_FOOTBALL.error = err && err.message ? err.message : 'Latest football results are temporarily unavailable.';
    if (state && state.screen === 'liveFootball') renderAll();
    liveFootballScheduleRefresh();
  });
}
function liveFootballScheduleRefresh() {
  if (LIVE_FOOTBALL.refreshTimer) clearTimeout(LIVE_FOOTBALL.refreshTimer);
  LIVE_FOOTBALL.refreshTimer = setTimeout(function () {
    if (state && (state.screen === 'home' || state.screen === 'liveFootball' || state.screen === 'pickem')) {
      liveFootballMaybeRefresh(true);
    }
  }, LIVE_FOOTBALL_REFRESH_MS);
}
function liveFootballRows() {
  var out = [];
  [['NFL', LIVE_FOOTBALL.nfl], ['CFB', LIVE_FOOTBALL.cfb]].forEach(function (pair) {
    var league = pair[0], packet = pair[1];
    var view = packet && packet.view;
    (view && view.games || []).forEach(function (g) {
      out.push(Object.assign({ league: league, season: packet.season, week: packet.week }, g));
    });
  });
  return out;
}
function liveFootballFinals() {
  return liveFootballRows().filter(function (g) { return g.status === 'FINAL'; }).sort(function (a,b) {
    return new Date(b.kickoff || 0).getTime() - new Date(a.kickoff || 0).getTime();
  });
}
function liveFootballUpcomingCount() {
  return liveFootballRows().filter(function (g) { return g.status !== 'FINAL' && g.status !== 'CANCELED'; }).length;
}
function liveFootballFavoriteMatch(g) {
  if (!state || !state.name) return false;
  var fav = getFavoriteTeams();
  var id = g.league === 'CFB' ? fav.cfb : fav.nfl;
  if (!id) return false;
  var team = favoriteTeamById(g.league === 'CFB' ? 'cfb' : 'nfl', id);
  var needles = [id, team && team.name].filter(Boolean).map(slugify);
  var hay = [g.home_team_code, g.away_team_code, g.home_team, g.away_team].filter(Boolean).map(slugify);
  return needles.some(function (n) { return hay.indexOf(n) !== -1; });
}
function liveFootballOrderedFinals() {
  return liveFootballFinals().slice().sort(function (a,b) {
    var af = liveFootballFavoriteMatch(a) ? 1 : 0, bf = liveFootballFavoriteMatch(b) ? 1 : 0;
    if (af !== bf) return bf - af;
    return new Date(b.kickoff || 0).getTime() - new Date(a.kickoff || 0).getTime();
  });
}
function liveFootballSeenKey() { return 'readsLiveFootballSeenFinals'; }
function liveFootballMarkNewFinals() {
  var ids = liveFootballFinals().map(function (g) { return g.league + ':' + g.game_id; });
  var seen = lsGet(liveFootballSeenKey(), []);
  var seenSet = {}; seen.forEach(function (id) { seenSet[id] = true; });
  LIVE_FOOTBALL.newFinalCount = ids.filter(function (id) { return !seenSet[id]; }).length;
}
function liveFootballAcknowledgeFinals() {
  var ids = liveFootballFinals().map(function (g) { return g.league + ':' + g.game_id; });
  lsSet(liveFootballSeenKey(), ids.slice(-100));
  LIVE_FOOTBALL.newFinalCount = 0;
}
function liveFootballFreshnessText() {
  if (!LIVE_FOOTBALL.fetchedAt) return 'Not checked yet';
  var mins = Math.max(0, Math.round((Date.now() - LIVE_FOOTBALL.fetchedAt) / 60000));
  return mins < 1 ? 'Checked just now' : 'Checked ' + mins + 'm ago';
}
function liveFootballResultLine(g) {
  return g.away_team + ' ' + g.away_score + ' · ' + g.home_team + ' ' + g.home_score;
}
function liveFootballFinalCardHtml(g, compact) {
  var winnerName = g.winner === g.home_team_code ? g.home_team : g.winner === g.away_team_code ? g.away_team : 'Tie';
  return '<article class="live-final-card' + (liveFootballFavoriteMatch(g) ? ' favorite' : '') + '">' +
    '<div class="live-final-top"><span>' + esc(g.league) + ' · WEEK ' + esc(String(g.week)) + '</span><b>FINAL</b></div>' +
    '<div class="live-final-matchup"><div><span>' + esc(g.away_team) + '</span><strong>' + esc(String(g.away_score)) + '</strong></div>' +
    '<div><span>' + esc(g.home_team) + '</span><strong>' + esc(String(g.home_score)) + '</strong></div></div>' +
    '<small>' + esc(winnerName) + ' won' + (liveFootballFavoriteMatch(g) ? ' · Your team' : '') +
      (g.your_pick && g.outcome ? ' · Pick’em: ' + esc(PICKEM_OUTCOME_COPY[g.outcome] || g.outcome) : '') + '</small>' +
    (!compact ? '<button class="btn-tiny" data-live-game-challenge="' + esc(g.league + ':' + g.game_id) + '">Quiz me on this final</button>' : '') +
    '</article>';
}
function liveFootballHomeHtml() {
  if (!ENABLE_PICKEM_V01) return '';
  var finals = liveFootballOrderedFinals();
  var newCount = Number(LIVE_FOOTBALL.newFinalCount) || 0;
  return '<section class="live-football-home">' +
    '<div class="dashboard-section-head"><div><span class="dashboard-eyebrow">LIVE FOOTBALL</span><h3>What just happened</h3></div>' +
    '<span>' + (newCount ? newCount + ' new final' + (newCount === 1 ? '' : 's') : liveFootballFreshnessText()) + '</span></div>' +
    (LIVE_FOOTBALL.loading && !LIVE_FOOTBALL.fetchedAt ? '<div class="live-football-loading">Checking the latest NFL + CFB slates…</div>' :
      finals.length ? '<div class="live-final-grid">' + finals.slice(0,3).map(function (g) { return liveFootballFinalCardHtml(g, true); }).join('') + '</div>' :
      '<p class="mode-desc">No finals are available in the current NFL/CFB slates yet. Reads checks again automatically.</p>') +
    '<div class="btn-row"><button class="btn-primary" data-live-football-open>Open Live Football</button>' +
    (finals.length ? '<button class="btn-secondary" data-live-challenge-start>Play Postgame 5</button>' : '') + '</div></section>';
}
function openLiveFootballHub() {
  LIVE_FOOTBALL.challenge = null;
  state.screen = 'liveFootball';
  liveFootballAcknowledgeFinals();
  liveFootballMaybeRefresh(false);
  renderAll();
}
function liveFootballChallengePool(singleKey) {
  var finals = liveFootballOrderedFinals();
  if (singleKey) {
    var p = singleKey.split(':'), league = p.shift(), gid = p.join(':');
    finals = finals.filter(function (g) { return g.league === league && String(g.game_id) === gid; });
  }
  return finals.slice(0, singleKey ? 1 : 5).map(function (g) {
    var options = [
      { code:g.away_team_code, label:g.away_team },
      { code:g.home_team_code, label:g.home_team }
    ];
    return {
      key:g.league + ':' + g.game_id,
      league:g.league,
      question:'Who won this ' + g.league + ' game?',
      context:liveFootballResultLine(g),
      options:options,
      correctCode:g.winner,
      notes:liveFootballResultLine(g)
    };
  });
}
function startLiveFootballChallenge(singleKey) {
  var q = liveFootballChallengePool(singleKey);
  if (!q.length) return;
  LIVE_FOOTBALL.challenge = { questions:q, index:0, correct:0, answered:null, screen:'question', awarded:false };
  state.screen = 'liveFootball';
  renderAll();
}
function answerLiveFootballChallenge(code) {
  var c=LIVE_FOOTBALL.challenge;
  if(!c || c.screen!=='question' || c.answered!==null) return;
  var q=c.questions[c.index];
  c.answered=code;
  var good=code===q.correctCode;
  if(good)c.correct++;
  if(typeof recordKnowledgeAnswer==='function') recordKnowledgeAnswer(q.league==='CFB'?'cfb':'nfl','Live Results',good);
  playSound(good?'correct':'wrong');
  renderAll();
}
function liveFootballChallengeClaimKey(c) {
  return 'readsLiveFootballChallengeClaims__' + slugify(state.name || 'guest');
}
function awardLiveFootballChallenge(c) {
  if (!state.name || c.awarded) return;
  var ids=c.questions.map(function(q){return q.key;}).sort().join('|');
  var claims=lsGet(liveFootballChallengeClaimKey(c),[]);
  if(claims.indexOf(ids)!==-1){c.awarded=true;return;}
  claims.push(ids); lsSet(liveFootballChallengeClaimKey(c),claims.slice(-60)); c.awarded=true;
  var xp=25, seasonId=footballSeasonIdForDate(), eventId='live_postgame_'+hashStr(ids);
  if(activeAuthUid && window.__fbSync && window.__fbSync.awardProgress){
    window.__fbSync.awardProgress(profileDocId(),eventId,{type:'LIVE_POSTGAME_COMPLETED',source:'live_football',gameIds:ids},xp,seasonId)
      .then(function(result){if(!result||!result.duplicate)applyProgressAwardLocally(xp,seasonId);pushSeasonLeaderboardSnapshot();pushProfileSnapshot();renderAll();}).catch(function(){});
  } else {
    applyProgressAwardLocally(xp,seasonId); pushSeasonLeaderboardSnapshot(); pushProfileSnapshot();
  }
}
function nextLiveFootballChallenge() {
  var c=LIVE_FOOTBALL.challenge;
  if(!c || c.answered===null)return;
  c.index++;
  c.answered=null;
  if(c.index>=c.questions.length){c.screen='summary';awardLiveFootballChallenge(c);}
  renderAll();
}
function liveFootballChallengeHtml() {
  var c=LIVE_FOOTBALL.challenge;
  if(!c)return '';
  if(c.screen==='summary'){
    var pct=Math.round(100*c.correct/c.questions.length);
    return '<div class="panel live-postgame-challenge"><div class="mode-toolbar"><button class="btn-tiny" data-live-challenge-close>' + icon('close') + ' Back to Live Hub</button></div>' +
      '<span class="dashboard-eyebrow">POSTGAME 5</span><h2 class="panel-title">Final whistle. How much did you catch?</h2>' +
      '<div class="summary-score">'+c.correct+' / '+c.questions.length+' correct ('+pct+'%)</div><div class="daily-reads-reward"><b>+25 XP</b><span>Live Football bonus</span></div>' +
      '<div class="btn-row"><button class="btn-primary" data-live-challenge-start>Play Latest Finals</button><button class="btn-secondary" data-go="home">Home</button></div></div>';
  }
  var q=c.questions[c.index], answered=c.answered!==null;
  return '<div class="panel live-postgame-challenge"><div class="mode-toolbar"><button class="btn-tiny" data-live-challenge-close>' + icon('close') + ' Back to Live Hub</button></div>' +
    '<div class="quiz-progress">POSTGAME · '+(c.index+1)+' of '+c.questions.length+' · '+esc(q.league)+'</div>' +
    '<div class="live-challenge-context">'+esc(q.context)+'</div><div class="quiz-question">'+esc(q.question)+'</div>' +
    '<div class="quiz-options">'+q.options.map(function(o){
      var cls='quiz-option';
      if(answered){if(o.code===q.correctCode)cls+=' correct';else if(o.code===c.answered)cls+=' wrong';}
      return '<button class="'+cls+'" '+(answered?'disabled':'data-live-challenge-answer="'+esc(o.code)+'"')+'>'+esc(o.label)+'</button>';
    }).join('')+'</div>' +
    (answered?'<div class="quiz-feedback">'+(c.answered===q.correctCode?'<span class="feedback-good">'+icon('check')+' Got it.</span>':'<span class="feedback-bad">'+icon('xMark')+' Missed it.</span>')+' '+esc(q.notes)+'</div><button class="btn-primary" data-live-challenge-next>'+(c.index+1>=c.questions.length?'Finish':'Next Final')+'</button>':'')+'</div>';
}
function renderLiveFootballScreen() {
  if (LIVE_FOOTBALL.challenge) return liveFootballChallengeHtml();
  var finals=liveFootballOrderedFinals(), favFinal=finals.find(liveFootballFavoriteMatch);
  return '<div class="panel live-football-hub"><div class="mode-toolbar"><button class="btn-tiny" data-go="home">'+icon('close')+' Exit to Home</button><button class="btn-tiny" data-live-football-refresh>'+icon('restart')+' Refresh</button></div>' +
    '<span class="dashboard-eyebrow">LIVE FOOTBALL</span><h2 class="panel-title">Saturday + Sunday, inside Reads</h2>' +
    '<p class="mode-desc">Current-week NFL and CFB results from the same real game feed that grades Pick’em. Scores only appear after the Gateway marks a game FINAL.</p>' +
    '<div class="live-hub-meta"><span>'+liveFootballFreshnessText()+'</span><span>'+finals.length+' finals</span><span>'+liveFootballUpcomingCount()+' upcoming/active</span></div>' +
    (favFinal?'<div class="live-favorite-spotlight"><span>YOUR TEAM</span><b>'+esc(liveFootballResultLine(favFinal))+'</b><button class="btn-tiny" data-live-game-challenge="'+esc(favFinal.league+':'+favFinal.game_id)+'">Postgame challenge</button></div>':'') +
    (LIVE_FOOTBALL.error?'<div class="quiz-feedback">'+esc(LIVE_FOOTBALL.error)+'</div>':'') +
    (finals.length?'<div class="live-final-grid live-final-grid-full">'+finals.map(function(g){return liveFootballFinalCardHtml(g,false);}).join('')+'</div>':'<p class="mode-desc">No finals yet in the current slates. Reads will refresh this screen automatically.</p>') +
    '<div class="btn-row">'+(finals.length?'<button class="btn-primary" data-live-challenge-start>Play Postgame 5</button>':'')+'<button class="btn-secondary" data-go="pickem_nfl">NFL Pick’em</button><button class="btn-secondary" data-go="pickem_cfb">CFB Pick’em</button></div></div>';
}
