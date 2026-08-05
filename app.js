// Bump both when shipping a change worth surfacing in the footer — APP_VERSION
// for any real feature/content change, CONTENT_UPDATED specifically when a
// question bank (data/*.js) changes, since that's the date players actually
// care about ("is the CFB bank still the old buggy one or the audited one").
var APP_VERSION = '2.2.0';
var CONTENT_UPDATED = 'Aug 4, 2026';
var SITE_URL = 'https://getreads.netlify.app/';

/* ============================== utilities ============================== */
function lsGet(key, fallback) {
  try { var v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
  catch (e) { return fallback; }
}
function lsSet(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}
// Hand-rolled inline SVG icon set (Feather/Lucide-style minimal line icons,
// 24x24, stroke=currentColor) — replaces emoji-as-icons across the app's
// utilitarian chrome (nav, header controls, mode cards, toolbars, feedback).
// Inline <svg> instead of an icon font/sprite sheet so there's zero external
// dependency and the icon always inherits `color` from its surrounding CSS.
// Emoji are kept everywhere else (badges, legends grade reactions, trivia
// content) — those are decorative/personality flourishes, not UI chrome.
var ICON_PATHS = {
  home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.04 1.56V21a2 2 0 0 1-4 0v-.09A1.7 1.7 0 0 0 9 19.35a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.65 15a1.7 1.7 0 0 0-1.56-1.04H3a2 2 0 0 1 0-4h.09A1.7 1.7 0 0 0 4.65 9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.65a1.7 1.7 0 0 0 1.04-1.56V3a2 2 0 0 1 4 0v.09a1.7 1.7 0 0 0 1.04 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.35 9a1.7 1.7 0 0 0 1.56 1.04H21a2 2 0 0 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1.04Z"/>',
  football: '<ellipse cx="12" cy="12" rx="9" ry="6" transform="rotate(-40 12 12)"/><path d="M8.5 15.5 15.5 8.5M9.8 14.2h1M10.6 13h1.2M11.5 11.7h1.2M12.3 10.5h1"/>',
  graduationCap: '<path d="M2 9 12 4l10 5-10 5-10-5Z"/><path d="M6 11.5V17c0 1.1 2.7 2 6 2s6-.9 6-2v-5.5"/><path d="M22 9v6"/>',
  trophy: '<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 5H4a1 1 0 0 0-1 1v1a4 4 0 0 0 4 4"/><path d="M17 5h3a1 1 0 0 1 1 1v1a4 4 0 0 1-4 4"/><path d="M12 14v3"/><path d="M8 21h8"/><path d="M9.5 17h5l1 4h-7l1-4Z"/>',
  helpCircle: '<circle cx="12" cy="12" r="9"/><path d="M9.2 9a2.8 2.8 0 1 1 3.9 2.6c-.8.4-1.1.9-1.1 1.9"/><path d="M12 17h.01"/>',
  volumeOn: '<path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/><path d="M19 6a9 9 0 0 1 0 12"/>',
  volumeOff: '<path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M17 9l5 6M22 9l-5 6"/>',
  close: '<path d="M5 5l14 14M19 5 5 19"/>',
  restart: '<path d="M3 11a9 9 0 1 1 2.6 6.4"/><path d="M3 17v-5h5"/>',
  share: '<circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="M8.3 10.7 15.7 6.3M8.3 13.3l7.4 4.4"/>',
  download: '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M4 19h16"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/>',
  check: '<path d="M4 12.5 9.5 18 20 6"/>',
  xMark: '<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>',
  flame: '<path d="M12 2c1 3-3 4-3 8a3 3 0 0 0 6 0c1.3 1 2 2.6 2 4.3A5.3 5.3 0 0 1 11.7 22 5.3 5.3 0 0 1 6.4 16.7C6.4 12 12 10 12 2Z"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/><path d="M12 2v3"/>',
  zap: '<path d="M12 2 4 14h7l-1 8 9-13h-7l1-7Z"/>',
  brain: '<path d="M12 4a3.5 3.5 0 0 0-3.5 3.5 3.5 3.5 0 0 0-2 6.2A3.5 3.5 0 0 0 9 19a3 3 0 0 0 3-3"/><path d="M12 4a3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1 2 6.2A3.5 3.5 0 0 1 15 19a3 3 0 0 1-3-3"/><path d="M12 4v12"/>',
  book: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  play: '<path d="M6 4.5v15l13-7.5-13-7.5Z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  sync: '<path d="M4 10a8 8 0 0 1 13.7-5.7L20 6.5"/><path d="M20 4v3.5h-3.5"/><path d="M20 14a8 8 0 0 1-13.7 5.7L4 17.5"/><path d="M4 20v-3.5h3.5"/>',
  flag: '<path d="M5 21V4"/><path d="M5 4h13l-3 4.5L18 13H5"/>',
  versus: '<circle cx="8" cy="8" r="3.2"/><path d="M2.5 20c0-3.6 2.5-6.2 5.5-6.2s5.5 2.6 5.5 6.2"/><circle cx="17.5" cy="9" r="2.6"/><path d="M15.2 20c.3-2.9 1.9-5 4.3-5.8"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  hofJacket: '<path d="M6 6H18V21H6Z"/><path d="M6 6 11 12"/><path d="M18 6 13 12"/><circle cx="9" cy="15" r="1.1"/>',
  cfpTrophy: '<path d="M12 3 8 9 12 15 16 9Z"/><path d="M10 15h4v3h-4Z"/><rect x="7" y="18" width="10" height="3" rx="1"/>',
  lombardiTrophy: '<ellipse cx="12" cy="6" rx="4" ry="2.6" transform="rotate(-25 12 6)"/><path d="M12 8.5v2.5"/><path d="M9 11h6l3 10H6Z"/>',
  arrowUp: '<path d="M12 20V4"/><path d="M5 11l7-7 7 7"/>',
  arrowDown: '<path d="M12 4v16"/><path d="M5 13l7 7 7-7"/>',
};
function icon(name, cls) {
  var body = ICON_PATHS[name] || '';
  return '<svg class="icon' + (cls ? ' ' + cls : '') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + body + '</svg>';
}
function slugify(s) { return (String(s).toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')) || 'player'; }
function shuffle(arr) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
function normName(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim(); }
function fmtTime(sec) { sec = Math.max(0, Math.ceil(sec)); var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }

// Shuffled-deck draw, shared by every mode that pulls a random subset out of a
// much bigger pool (quiz rounds, IQ tests, speed sessions, silhouette rounds).
// A fresh shuffle-and-slice each time lets the same handful of items cluster
// by chance; this instead persists a shuffled "deck" per pool (localStorage,
// keyed so different filters/categories get their own independent deck) and
// draws off the front of it, refilling with a new shuffle of whatever hasn't
// been seen yet once it runs low — so the full pool cycles once before
// anything repeats.
function drawNoRepeat(deckKey, ids, count) {
  var storKey = 'deck__' + deckKey;
  var idSet = {};
  ids.forEach(function (id) { idSet[id] = true; });
  var deck = lsGet(storKey, []).filter(function (id) { return idSet[id]; });
  if (deck.length < count) {
    var leftoverSet = {};
    deck.forEach(function (id) { leftoverSet[id] = true; });
    var refill = shuffle(ids.filter(function (id) { return !leftoverSet[id]; }));
    deck = deck.concat(refill);
  }
  var drawn = deck.slice(0, count);
  lsSet(storKey, deck.slice(count));
  return drawn;
}

/* ============================== data + state ============================== */
var QUIZ = window.QUIZ_DATA || [];
var GRID_PLAYERS = window.GRID_PLAYERS || [];
var GRID_CRITERIA = window.GRID_CRITERIA || { team: [], stat: [], all: [] };
var BLITZ_LISTS = window.BLITZ_LISTS || [];
var SILHOUETTE_PLAYERS = window.SILHOUETTE_PLAYERS || [];
var CFB = window.CFB_DATA || [];
var CFB_SPEED = window.CFB_SPEED_DATA || [];
var CFB_BLITZ_LISTS = window.CFB_BLITZ_LISTS || [];
var CFB_GRID_PLAYERS = window.CFB_GRID_PLAYERS || [];
var CFB_GRID_CRITERIA = window.CFB_GRID_CRITERIA || { team: [], stat: [], all: [] };

var DEFAULT_STATS = {
  quiz: { correctTotal: 0, questionsTotal: 0, roundsPlayed: 0, bestPct: 0 },
  grid: { bestScore: 0, gamesPlayed: 0, cleanSweeps: 0 },
  blitz: { bestMatched: 0, attempts: 0 },
  speed: { bestScore: 0, bestStreak: 0, sessionsPlayed: 0 },
  silhouette: { bestScore: 0, roundsPlayed: 0, bestQuick: 0 },
  iq: { bestIQ: 0, testsTaken: 0 },
  legends: { bestWins: 0, bestScore: 0, bestGrade: '', gamesPlayed: 0 },
  higherLower: { bestStreak: 0, gamesPlayed: 0 },
  cfbQuiz: { correctTotal: 0, questionsTotal: 0, roundsPlayed: 0, bestPct: 0 },
  cfbIq: { bestIQ: 0, testsTaken: 0 },
  cfbSpeed: { bestScore: 0, bestStreak: 0, sessionsPlayed: 0 },
  cfbBlitz: { bestMatched: 0, attempts: 0 },
  cfbGrid: { bestScore: 0, gamesPlayed: 0, cleanSweeps: 0 },
  daily: { completions: 0, correctTotal: 0, questionsTotal: 0, bestPct: 0 },
  cfbLegends: { bestWins: 0, bestScore: 0, bestGrade: '', gamesPlayed: 0 },
  h2h: { wins: 0, losses: 0, ties: 0, matchesPlayed: 0 }
};

var lastFocusedScreen = null; // tracks screen changes for renderAll()'s focus management

var state = {
  name: lsGet('nflTriviaName', ''),
  screen: 'home',
  rankedPref: lsGet('nflTriviaRankedPref', {}),
  leaderboardMode: 'quiz',
  leaderboardRange: 'all',
  leaderboardData: [],
  stats: Object.assign({}, DEFAULT_STATS, lsGet('nflTriviaStats', {})),
  quiz: { screen: 'setup', category: '', difficulty: '', roundSize: 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] },
  grid: null,
  blitz: null,
  speed: null,
  silhouette: null,
  iq: null,
  legends: null,
  higherLower: null,
  cfbQuiz: { screen: 'setup', category: '', difficulty: '', roundSize: 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] },
  cfbIq: null,
  cfbSpeed: null,
  cfbBlitz: null,
  cfbGrid: null,
  daily: null,
  cfbLegends: null,
  h2h: null,
  h2hLive: null,
  study: null,
  learn: null,
  introTest: null,
  // Non-null while the CURRENT session in some other mode (grid/blitz/
  // silhouette/legends) is being played specifically as today's Daily
  // Challenge — see dailyChallengeTypeForToday() and completeDailyChallengeFrom().
  // Holds one of the DAILY_CHALLENGE_TYPES entries, or null the rest of the time.
  dailyChallengeActive: null,
  // Same idea as dailyChallengeActive, but for a non-quiz-kind Head-to-Head
  // match currently being played inside another mode's own screen — see
  // h2hStartPlaying/h2hSubmitModeResult in the head-to-head section.
  h2hActive: null,
  // Transient UI state for the team-picker modal (screen: 'nfl'|'cfb',
  // filter: search text) — null while the modal's closed. The actual
  // favorite-team selections live in localStorage via getFavoriteTeams(),
  // not here, so they survive a refresh independent of this.
  teamPicker: null,
  settingsConfirmClear: false
};
// One-time migration: CFB 12-0 used to be "CFB 16-0" (a 16-game season —
// see the comment above the mode's code for why). Anyone who played it
// before that change may have a stored bestWins as high as 16, which would
// now render as an impossible negative-loss record (e.g. "15-(-3)") against
// the new 12-game max — clamp it down once so old data can't produce that.
if (state.stats.cfbLegends && state.stats.cfbLegends.bestWins > 12) state.stats.cfbLegends.bestWins = 12;

/* ============================== football rating ==============================
   A persistent, adaptive skill rating (separate from the one-off Football IQ Test
   score). Set once by a short blended NFL+CFB intro test the first time a name is
   entered, then nudged up/down by every subsequent game mode's result via a slow
   exponential moving average — one bad or lucky round barely moves it, but it
   drifts to reflect real performance over many sessions. Stored per name-slug so
   switching names doesn't carry someone else's rating along. */
var INTRO_TEST_SIZE = 16;
var RATING_DRIFT_ALPHA = 0.08;
function ratingKey() { return 'nflTriviaRating__' + slugify(state.name); }
// Unlike every other mode's leaderboard doc (keyed name+clientId, so each device
// gets its own row), the rating doc is keyed by NAME ONLY — one canonical value
// per person, shared across every device that plays under that name. See
// reconcileRating() below for how a second device adopts it.
function ratingDocId() { return 'rating__' + slugify(state.name); }
function getRating() { return state.name ? lsGet(ratingKey(), null) : null; }
function setRating(r) {
  if (!state.name) return;
  lsSet(ratingKey(), r);
  if (window.__fbSync && window.__fbSync.pushScore) {
    window.__fbSync.pushScore(ratingDocId(), { name: state.name, mode: 'rating', score: r.score, games: r.games || 0 });
  }
}
// Called whenever fresh leaderboard data arrives from Firebase. If another
// device has a more advanced rating for this same name (more games factored
// in), adopt it locally — this is what makes the rating survive a cache clear
// or a switch to a new device/browser. If THIS device is the one ahead, push
// it back up so the other device(s) catch up next time they sync.
function reconcileRating(list) {
  if (!state.name) return;
  var mySlug = slugify(state.name);
  var cloud = list.find(function (r) { return r.mode === 'rating' && slugify(r.name || '') === mySlug; });
  if (!cloud || typeof cloud.score !== 'number') return;
  var local = getRating();
  if (!local || (cloud.games || 0) > (local.games || 0)) {
    lsSet(ratingKey(), { score: cloud.score, games: cloud.games || 0 });
    pushRatingHistory(cloud.score);
    if (state.screen === 'introTest') { state.introTest = null; state.screen = 'home'; }
    renderAll();
  } else if ((local.games || 0) > (cloud.games || 0) && window.__fbSync && window.__fbSync.pushScore) {
    window.__fbSync.pushScore(ratingDocId(), { name: state.name, mode: 'rating', score: local.score, games: local.games || 0 });
  }
}
// Cross-device sync for per-mode stats/badges/streak — the same "one doc
// per name, no password" idea reconcileRating() above already used for
// Football Rating, extended to the rest of state.stats. Unlike rating
// (one number, "more games played" is unambiguously more advanced), stats
// is ~17 mode objects with their own bests/counts — merged field-by-field,
// taking whichever device's value is further along for each field
// independently, so playing on two devices never LOSES progress on either
// one. bestGrade (a letter, not a number) needs its own rank table since
// Math.max() on 'S' vs 'A+' doesn't mean anything.
var STAT_GRADE_RANK = { S: 11, 'A+': 10, A: 9, 'A-': 8, 'B+': 7, B: 6, 'B-': 5, 'C+': 4, C: 3, D: 2, F: 1 };
function betterGrade(a, b) { return (STAT_GRADE_RANK[b] || 0) > (STAT_GRADE_RANK[a] || 0) ? b : (a || ''); }
function mergeStats(local, cloud) {
  if (!cloud) return local;
  var merged = {};
  Object.keys(DEFAULT_STATS).forEach(function (mode) {
    var l = local[mode] || {}, c = cloud[mode] || {}, out = {};
    Object.keys(DEFAULT_STATS[mode]).forEach(function (field) {
      out[field] = field === 'bestGrade' ? betterGrade(l[field], c[field]) : Math.max(Number(l[field]) || 0, Number(c[field]) || 0);
    });
    merged[mode] = out;
  });
  return merged;
}
// Streak isn't a running total like the stats above — it's inherently tied
// to actual calendar dates (miss a day, it resets), so "bigger number" and
// "more advanced" aren't the same thing here. Whichever device played most
// recently is the authoritative one; only fall back to comparing counts if
// they somehow played on the exact same date.
function mergeStreak(local, cloud) {
  if (!cloud || !cloud.lastPlayedDate) return local;
  if (!local.lastPlayedDate || cloud.lastPlayedDate > local.lastPlayedDate) return cloud;
  if (cloud.lastPlayedDate === local.lastPlayedDate && (cloud.count || 0) > (local.count || 0)) return cloud;
  return local;
}
function pushProfileSnapshot() {
  if (!state.name || !window.__fbSync || !window.__fbSync.pushProfile) return;
  window.__fbSync.pushProfile(slugify(state.name), { name: state.name, stats: state.stats, streak: getStreak() });
}
// Called once whenever a name is set/entered (see saveName()) — a one-time
// fetch-and-merge, not a live listener like the leaderboard: nobody else
// needs to watch your personal stats update in real time, this only ever
// needs to run at the moment a device might be "catching up."
function pullProfileSnapshot() {
  if (!state.name || !window.__fbSync || !window.__fbSync.getProfile) return;
  window.__fbSync.getProfile(slugify(state.name)).then(function (cloud) {
    if (!cloud) return;
    var beforeStats = JSON.stringify(state.stats), beforeStreak = JSON.stringify(getStreak());
    state.stats = mergeStats(state.stats, cloud.stats);
    var mergedStreak = mergeStreak(getStreak(), cloud.streak);
    lsSet('nflTriviaStats', state.stats);
    lsSet(streakKey(), mergedStreak);
    if (JSON.stringify(state.stats) !== beforeStats || JSON.stringify(mergedStreak) !== beforeStreak) {
      pushProfileSnapshot(); // close the loop: cloud should reflect the merge too, not just this device
      renderAll();
    }
  }).catch(function (err) { console.warn('Profile pull failed', err); });
}
// Friends list — deliberately just a local list of names, not another
// synced collection: nobody needs to see who's on someone else's list, and
// a plain localStorage array sidesteps friend-request/accept flow entirely.
// What each friend row shows is real, already-live data pulled from systems
// built above: their Football Rating comes straight out of the shared
// leaderboard state.leaderboardData already keeps live via onSnapshot, and
// their streak comes from the same per-name profiles doc pushProfileSnapshot()
// already writes for cross-device sync — no new backend concept needed.
var FRIENDS_KEY = 'nflTriviaFriends';
function getFriends() { return lsGet(FRIENDS_KEY, []); }
function setFriends(list) { lsSet(FRIENDS_KEY, list); }
function addFriend(name) {
  name = (name || '').trim();
  if (!name) return;
  var list = getFriends();
  if (list.some(function (f) { return slugify(f) === slugify(name); })) return;
  list.push(name);
  setFriends(list);
  var input = document.getElementById('friend-name-input');
  if (input) input.value = '';
  loadFriendsData();
}
function removeFriend(name) {
  setFriends(getFriends().filter(function (f) { return slugify(f) !== slugify(name); }));
  renderAll();
}
function friendRatingFromLeaderboard(name) {
  var slug = slugify(name);
  var entry = (state.leaderboardData || []).find(function (r) { return r.mode === 'rating' && slugify(r.name || '') === slug; });
  return entry ? { score: entry.score, games: entry.games || 0 } : null;
}
// Not a live listener like the leaderboard (that would mean one Firestore
// subscription per friend, torn down/rebuilt every time the list changes) —
// just a one-time fetch each time the Friends screen is opened, matching how
// pullProfileSnapshot() already treats profile docs as "check when you look,
// not watch forever."
var friendsProfileCache = {};
var friendsLoading = false;
function loadFriendsData() {
  var friends = getFriends();
  if (!friends.length || !window.__fbSync || !window.__fbSync.getProfile) { renderAll(); return; }
  friendsLoading = true;
  renderAll();
  Promise.all(friends.map(function (name) {
    return window.__fbSync.getProfile(slugify(name)).then(function (profile) {
      friendsProfileCache[slugify(name)] = profile;
    }).catch(function () { friendsProfileCache[slugify(name)] = null; });
  })).then(function () {
    friendsLoading = false;
    renderAll();
  });
}
// Tracks how much the last updateRatingDrift() call actually moved the
// rating — read by each finish* function right after calling it, and shown
// on that round's share card. Reset to null at the top of every call so a
// Practice-mode round (which never calls updateRatingDrift at all) or a
// round played before any rating exists can't accidentally show a stale
// delta left over from a previous round.
var lastRatingDelta = null;
function updateRatingDrift(sessionPct) {
  lastRatingDelta = null;
  var r = getRating();
  if (!r) return;
  var before = r.score;
  sessionPct = Math.max(0, Math.min(100, sessionPct));
  var sessionScore = 60 + sessionPct;
  r.score = Math.round(r.score * (1 - RATING_DRIFT_ALPHA) + sessionScore * RATING_DRIFT_ALPHA);
  r.games = (r.games || 0) + 1;
  setRating(r);
  lastRatingDelta = r.score - before;
  pushRatingHistory(r.score);
}
function introTestPool() {
  var half = Math.floor(INTRO_TEST_SIZE / 2);
  var nfl = shuffle(QUIZ).slice(0, half);
  var cfb = shuffle(CFB).slice(0, INTRO_TEST_SIZE - half);
  return shuffle(nfl.concat(cfb));
}
function startIntroTest() {
  state.introTest = { screen: 'intro', queue: [], index: 0, answers: [] };
  state.screen = 'introTest';
  renderAll();
}
function beginIntroQuestions() {
  state.introTest.queue = introTestPool();
  state.introTest.screen = 'test';
  renderAll();
}
function currentIntroQuestion() { return state.introTest.queue[state.introTest.index]; }
function answerIntroQuestion(optionIndex) {
  var t = state.introTest, q = currentIntroQuestion();
  if (!q) return;
  t.answers.push({ correct: optionIndex === q.correctIndex });
  t.index++;
  if (t.index >= t.queue.length) finishIntroTest();
  else renderAll();
}
function finishIntroTest() {
  var t = state.introTest;
  var correct = t.answers.filter(function (a) { return a.correct; }).length;
  var total = t.answers.length;
  t.correct = correct;
  t.total = total;
  t.score = Math.round(60 + (correct / total) * 100);
  t.screen = 'result';
  setRating({ score: t.score, games: 1 });
  pushRatingHistory(t.score);
  renderAll();
}
function skipIntroTest() { state.introTest = null; state.screen = 'home'; if (!consumePendingLiveJoin()) renderAll(); }
function introTestDone() { state.introTest = null; state.screen = 'home'; if (!consumePendingLiveJoin()) renderAll(); }
function retakeIntroTest() { startIntroTest(); }
// Unlike quiz options/grid squares (fresh DOM nodes every render, so a CSS
// animation on their class just replays automatically), #rating-badge is a
// single persistent element that only gets its text mutated in place — so
// retriggering its pulse animation needs an explicit class toggle + reflow.
var lastShownRatingScore = null;
// Ring fill approximates where a score sits in its practical range (60-160,
// see updateRatingDrift's sessionScore = 60 + sessionPct) rather than any
// hard min/max the score can't leave, so it reads as "progress" without
// implying 160 is a hard ceiling. r=15.5 circumference (~97.4) at viewBox
// 36x36 matches the classic "SVG donut" technique.
function ratingRingSvg(score) {
  var pct = Math.max(0, Math.min(1, (score - 60) / 100));
  var circumference = 2 * Math.PI * 15.5;
  var offset = circumference * (1 - pct);
  return '<svg class="rating-ring" viewBox="0 0 36 36" aria-hidden="true">' +
    '<circle class="rating-ring-track" cx="18" cy="18" r="15.5" />' +
    '<circle class="rating-ring-fill" cx="18" cy="18" r="15.5" stroke-dasharray="' + circumference.toFixed(2) + '" stroke-dashoffset="' + offset.toFixed(2) + '" />' +
    '</svg>';
}
function renderRatingBadge() {
  var el = document.getElementById('rating-badge');
  if (!el) return;
  var r = getRating();
  if (!r) { el.style.display = 'none'; lastShownRatingScore = null; return; }
  el.style.display = '';
  el.innerHTML = ratingRingSvg(r.score) + '<span class="rating-badge-text">' + icon('football') + ' ' + r.score + '</span>';
  el.setAttribute('aria-label', 'Your Football Rating: ' + r.score);
  if (lastShownRatingScore !== null && lastShownRatingScore !== r.score) {
    el.classList.remove('rating-pulse');
    void el.offsetWidth; // force reflow so the animation restarts
    el.classList.add('rating-pulse');
    var delta = r.score - lastShownRatingScore;
    var pop = document.createElement('span');
    pop.className = 'rating-delta-pop ' + (delta > 0 ? 'up' : 'down');
    pop.textContent = (delta > 0 ? '+' : '') + delta;
    el.appendChild(pop);
    setTimeout(function () { if (pop.parentNode) pop.parentNode.removeChild(pop); }, 1300);
  }
  lastShownRatingScore = r.score;
}

/* ============================== streak ==============================
   A daily-play streak, deliberately tied to the Daily Challenge specifically
   (bumpStreak() is called from finishDailyChallenge(), not from every mode's
   finish function) — same pairing every real streak+daily-challenge feature
   uses elsewhere, and it means this needs zero changes to the 12 existing
   game modes. Local-only (not synced to Firebase) — purely a personal nudge
   shown on the Home screen and the Profile page. */
function pad2(n) { return (n < 10 ? '0' : '') + n; }
function dateStr(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
function todayStr() { return dateStr(new Date()); }
function daysAgoStr(n) { var d = new Date(); d.setDate(d.getDate() - n); return dateStr(d); }
function yesterdayStr() { return daysAgoStr(1); }
function daysBetween(a, b) { return Math.round((new Date(b) - new Date(a)) / 86400000); }
function streakKey() { return 'nflTriviaStreak__' + slugify(state.name); }
function getStreak() { return state.name ? lsGet(streakKey(), { count: 0, lastPlayedDate: '', graceUsedDate: '' }) : { count: 0, lastPlayedDate: '', graceUsedDate: '' }; }
// A streak grace is available once every 7 days (rolling from the last time
// one was actually used, not calendar-week-aligned) — survives exactly one
// missed day without resetting to 1. Missing 2+ days in a row, or missing a
// day while no grace is available, still resets normally. Not shown as an
// earnable/purchasable resource (this app has no points/currency economy to
// spend) — it's just a small, honest "one missed day won't wreck it" safety
// net, the way most real daily-streak products handle an off day.
function streakGraceAvailable(s) {
  if (!s.graceUsedDate) return true;
  return daysBetween(s.graceUsedDate, todayStr()) >= 7;
}
// Result set on state (see below) whenever bumpStreak() actually consumes a
// grace day — completeDailyChallengeFrom() and finishDailyChallenge() read
// this right after calling bumpStreak() so the result screen can say "streak
// saved" instead of the save happening invisibly.
var lastStreakGraceUsed = false;
function bumpStreak() {
  lastStreakGraceUsed = false;
  if (!state.name) return;
  var s = getStreak();
  var today = todayStr();
  if (s.lastPlayedDate === today) return;
  var gapDays = s.lastPlayedDate ? daysBetween(s.lastPlayedDate, today) : null;
  if (gapDays === 1 || !s.lastPlayedDate) {
    s.count = s.count + 1;
  } else if (gapDays === 2 && streakGraceAvailable(s)) {
    s.count = s.count + 1;
    s.graceUsedDate = today;
    lastStreakGraceUsed = true;
  } else {
    s.count = 1;
  }
  s.lastPlayedDate = today;
  lsSet(streakKey(), s);
}

/* ============================== daily challenge ==============================
   The one deliberate exception to "every round is freshly randomized" — a
   fixed 10-question set (5 NFL + 5 CFB, same blend as the intro test) that's
   IDENTICAL for every player on a given calendar date, via a tiny seeded PRNG
   instead of Math.random(). One attempt per day; always counts toward rating
   + leaderboard (no Practice variant, unlike every other mode). Reuses the
   already-eager QUIZ/CFB pools — no new data authoring needed. */
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function hashStr(s) {
  var h = 0;
  for (var i = 0; i < s.length; i++) { h = (Math.imul(31, h) + s.charCodeAt(i)) | 0; }
  return h;
}
function seededShuffle(arr, rng) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rng() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
var DAILY_SIZE = 10;
function dailyQuestionPool() {
  var rng = mulberry32(hashStr(todayStr()));
  var half = Math.floor(DAILY_SIZE / 2);
  var nfl = seededShuffle(QUIZ, rng).slice(0, half);
  var cfb = seededShuffle(CFB, rng).slice(0, DAILY_SIZE - half);
  return seededShuffle(nfl.concat(cfb), rng);
}
function dailyKey() { return 'nflTriviaDaily__' + slugify(state.name); }
function getDailyResult() { return state.name ? lsGet(dailyKey(), null) : null; }
function playedToday() { var r = getDailyResult(); return !!(r && r.date === todayStr()); }
// Which mode today's Daily Challenge routes into — deterministic per day (same
// seeded-hash pattern as dailyQuestionPool) so it's the same for everyone, but
// varies day to day across every mode type that makes sense as a quick daily
// pick: the classic 10-question quiz, Silhouette, either Immaculate Grid, either
// Blitz list pool, or a full 17-0/12-0 fantasy draft.
var DAILY_CHALLENGE_TYPES = [
  { id: 'quiz', mode: 'daily', label: 'Daily Quiz', desc: '10 mixed NFL + College Football questions, same for everyone today.' },
  { id: 'silhouette', mode: 'silhouette', label: 'Silhouette', desc: 'Guess 5 players from a silhouette and a ladder of clues.' },
  { id: 'grid', mode: 'grid', label: 'NFL Immaculate Grid', desc: 'A fresh 3x3 NFL grid — name a player for every square.' },
  { id: 'cfbGrid', mode: 'cfbGrid', label: 'CFB Immaculate Grid', desc: 'A fresh 3x3 college football grid — name a player for every square.' },
  { id: 'blitz', mode: 'blitz', label: 'NFL Blitz', desc: 'Type every correct answer you can before the clock runs out.' },
  { id: 'cfbBlitz', mode: 'cfbBlitz', label: 'CFB Blitz', desc: 'Type every correct college football answer before the clock runs out.' },
  { id: 'legends', mode: 'legends', label: '17-0', desc: 'Draft a 7-player fantasy team and see if it grades out as a perfect season.' },
  { id: 'cfbLegends', mode: 'cfbLegends', label: 'CFB 12-0', desc: 'Draft an 8-player college roster and see how your season plays out.' }
];
function dailyChallengeTypeForToday() {
  var rng = mulberry32(hashStr(todayStr() + '__dailyType'));
  return DAILY_CHALLENGE_TYPES[Math.floor(rng() * DAILY_CHALLENGE_TYPES.length)];
}
// Shared completion bookkeeping for every non-quiz daily type (the quiz type's
// own finishDailyChallenge() below calls this too, after its quiz-specific stat
// updates) — bumps the streak, records today's generic result, and pushes to
// the Daily Challenge leaderboard, regardless of which underlying mode was
// actually played. No-ops if this round wasn't today's designated daily type
// (i.e. the player just played that mode normally, not via the daily card).
function completeDailyChallengeFrom(typeId, label, pct) {
  if (!state.dailyChallengeActive || state.dailyChallengeActive.id !== typeId) return;
  state.dailyChallengeActive = null;
  var st = state.stats.daily;
  st.completions++;
  if (typeof pct === 'number' && Math.round(pct) > st.bestPct) st.bestPct = Math.round(pct);
  lsSet('nflTriviaStats', state.stats);
  bumpStreak();
  if (state.name) lsSet(dailyKey(), { date: todayStr(), type: typeId, label: label, graceUsed: lastStreakGraceUsed });
  pushLeaderboard('daily', { completions: st.completions, bestPct: st.bestPct });
}
// Loads a mode's data file (if not already loaded, same lazy-load path as
// goToMode) then runs startFn — used to route the Daily Challenge into
// whichever real mode today's type points at. Forces that mode's ranked
// preference to true for the duration of startFn so a daily run always
// counts, regardless of the player's usual Practice-mode toggle for it.
// Shared by startDailyIntoMode (below) and the Head-to-Head equivalent
// (startH2hIntoMode, see the head-to-head section) — both route into a real
// mode's own engine from a wrapper flow, so both need "load this mode's data
// file if it isn't already, then run" as a first step, same lazy-load path
// goToMode itself uses.
function loadModeDataThenRun(mode, run, onError) {
  var files = MODE_DATA_FILES[mode];
  var pending = files && files.filter(function (f) { return !loadedScripts[f]; });
  if (pending && pending.length) {
    var app = document.getElementById('app');
    if (app) app.innerHTML = '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading ' + esc(modeLabelFor(mode)) + '…</div></div>';
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      run();
    }).catch(function () {
      if (onError) onError();
      if (app) app.innerHTML = '<div class="panel">Couldn’t load this mode. Check your connection and try again. <button class="btn-secondary" data-go="home">Home</button></div>';
    });
    return;
  }
  refreshDataAliases();
  run();
}
// Forces mode's ranked preference to true for the duration of startFn (a
// daily/h2h run always counts, regardless of the player's usual Practice
// toggle for that mode) then restores whatever it was before.
function startModeRanked(mode, startFn) {
  var prevPref = state.rankedPref[mode];
  state.rankedPref[mode] = true;
  startFn();
  state.rankedPref[mode] = prevPref;
}
function startDailyIntoMode(mode, startFn) {
  loadModeDataThenRun(mode, function () { startModeRanked(mode, startFn); }, function () { state.dailyChallengeActive = null; });
}
function startDailyChallenge() {
  if (playedToday()) return;
  var today = dailyChallengeTypeForToday();
  state.dailyChallengeActive = today;
  if (today.id === 'quiz') {
    state.daily = { queue: dailyQuestionPool(), index: 0, correctCount: 0, answeredIndex: null, missed: [], screen: 'question' };
    state.screen = 'daily';
    renderAll();
    return;
  }
  if (today.id === 'blitz' || today.id === 'cfbBlitz') {
    startDailyIntoMode(today.mode, function () {
      var pool = today.id === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS;
      var rng = mulberry32(hashStr(todayStr() + '__dailyList'));
      var listId = pool[Math.floor(rng() * pool.length)].id;
      (today.id === 'blitz' ? startBlitz : startCfbBlitz)(listId, 90);
    });
    return;
  }
  startDailyIntoMode(today.mode, function () {
    if (today.id === 'silhouette') startSilhouetteRound(5);
    else if (today.id === 'grid') startGridRound();
    else if (today.id === 'cfbGrid') startCfbGridRound();
    else if (today.id === 'legends') startLegends();
    else if (today.id === 'cfbLegends') startCfbLegends();
  });
}
function currentDailyQuestion() { return state.daily.queue[state.daily.index]; }
function pickDailyAnswer(i) {
  var t = state.daily;
  if (t.answeredIndex !== null) return;
  t.answeredIndex = i;
  var q = currentDailyQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) t.correctCount++;
  else if (q) t.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i });
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextDailyQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  var t = state.daily;
  if (t.index + 1 >= t.queue.length) { finishDailyChallenge(); return; }
  t.index++;
  t.answeredIndex = null;
  renderAll();
}
function finishDailyChallenge() {
  var t = state.daily, st = state.stats.daily;
  var pct = Math.round(100 * t.correctCount / t.queue.length);
  st.correctTotal += t.correctCount;
  st.questionsTotal += t.queue.length;
  updateRatingDrift(pct);
  t.ratingDelta = lastRatingDelta;
  playSound(pct <= 60 ? 'boo' : 'complete');
  completeDailyChallengeFrom('quiz', t.correctCount + ' / ' + t.queue.length + ' correct', pct);
  t.screen = 'summary';
  renderAll();
}
function dailyChallengeCardHtml() {
  var already = playedToday();
  var streak = getStreak();
  var streakBit = streak.count > 0 ? ' &middot; ' + icon('flame', 'streak-flame') + ' ' + streak.count + '-day streak' : '';
  var badge = '<span class="daily-flame-badge">' + icon('flame') + '</span>';
  var eyebrow = '<div class="daily-card-eyebrow">Today</div>';
  var today = dailyChallengeTypeForToday();
  if (already) {
    var r = getDailyResult();
    var label = r.label || (r.correct + ' / ' + r.total + ' correct');
    var typeLabel = (DAILY_CHALLENGE_TYPES.find(function (t) { return t.id === (r.type || 'quiz'); }) || today).label;
    return '<div class="panel daily-card">' + eyebrow +
      '<div class="daily-card-title">' + badge + ' Daily Challenge &middot; ' + esc(typeLabel) + '</div>' +
      '<p class="mode-desc">' + icon('check') + ' Completed today — ' + esc(label) + streakBit + '. Come back tomorrow for a new one.</p>' +
      (r.graceUsed ? '<p class="mode-desc streak-saved-note">🛡️ You missed a day, but your streak survived — one grace day free every 7 days.</p>' : '') +
      '<button class="btn-secondary" data-go="daily">View Today’s Result</button>' +
      '</div>';
  }
  return '<div class="panel daily-card">' + eyebrow +
    '<div class="daily-card-title">' + badge + ' Daily Challenge &middot; ' + esc(today.label) + '</div>' +
    '<p class="mode-desc">' + esc(today.desc) + streakBit + '</p>' +
    '<button class="btn-primary" data-daily-start>Play Today’s Challenge</button>' +
    '</div>';
}
function renderDailyQuestion() {
  var t = state.daily, q = currentDailyQuestion();
  var answered = t.answeredIndex !== null;
  return '<div class="panel">' + modeToolbarHtml('daily') +
    '<div class="quiz-progress">Daily Challenge &middot; Question ' + (t.index + 1) + ' of ' + t.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-daily-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-daily-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderDailySummary() {
  var t = state.daily, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel">' +
    '<h2 class="panel-title">Daily Challenge Complete</h2>' +
    '<div class="summary-score">' + t.correctCount + ' / ' + t.queue.length + ' correct (' + pct + '%)</div>' +
    '<div class="summary-note">' + icon('flame') + ' ' + getStreak().count + '-day streak. Come back tomorrow for a new challenge.' + (state.name ? '' : ' Enter a name above to save this to the leaderboard.') + '</div>' +
    (lastStreakGraceUsed ? '<div class="summary-note streak-saved-note">🛡️ You missed a day, but your streak survived — one grace day free every 7 days.</div>' : '') +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-secondary" data-share="daily">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderDailyScreen() {
  if (!state.daily) {
    var r = getDailyResult();
    if (r && r.date === todayStr()) {
      var label = r.label || (r.correct + ' / ' + r.total + ' correct');
      var typeLabel = (DAILY_CHALLENGE_TYPES.find(function (t) { return t.id === (r.type || 'quiz'); }) || {}).label || 'Daily Quiz';
      return '<div class="panel"><h2 class="panel-title">' + icon('flame') + ' Daily Challenge &middot; ' + esc(typeLabel) + ' &middot; Complete</h2>' +
        '<div class="summary-score">' + esc(label) + '</div>' +
        '<div class="summary-note">Streak: ' + getStreak().count + ' day' + (getStreak().count === 1 ? '' : 's') + '. Come back tomorrow for a new one.</div>' +
        '<button class="btn-secondary" data-go="home">Home</button></div>';
    }
    var today = dailyChallengeTypeForToday();
    return '<div class="panel"><h2 class="panel-title">Daily Challenge &middot; ' + esc(today.label) + '</h2><p class="mode-desc">' + esc(today.desc) + '</p><button class="btn-primary" data-daily-start>Play Today’s Challenge</button></div>';
  }
  if (state.daily.screen === 'summary') return renderDailySummary();
  return renderDailyQuestion();
}

var blitzTimer = null, speedTimer = null, cfbSpeedTimer = null, cfbBlitzTimer = null;
function stopTimers() {
  if (blitzTimer) { clearInterval(blitzTimer); blitzTimer = null; }
  if (speedTimer) { clearInterval(speedTimer); speedTimer = null; }
  if (cfbSpeedTimer) { clearInterval(cfbSpeedTimer); cfbSpeedTimer = null; }
  if (cfbBlitzTimer) { clearInterval(cfbBlitzTimer); cfbBlitzTimer = null; }
}

/* ============================== nav ============================== */
function resetModeState(mode) {
  // Restarting or navigating back into a mode (the only two ways this gets
  // called for a mode other than the daily/h2h routing helpers, which call
  // that mode's own start function directly instead) means any in-progress
  // Daily Challenge or Head-to-Head round that was being played AS that mode
  // just got abandoned — clear the flag so a later, unrelated solo round in
  // this same mode can't get silently credited as finishing it.
  if (state.dailyChallengeActive && state.dailyChallengeActive.mode === mode) state.dailyChallengeActive = null;
  if (state.h2hActive && state.h2hActive.mode === mode) state.h2hActive = null;
  if (mode === 'quiz') state.quiz = { screen: 'setup', category: '', difficulty: '', roundSize: (state.quiz && state.quiz.roundSize) || 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] };
  else if (mode === 'grid') state.grid = null;
  else if (mode === 'blitz') state.blitz = null;
  else if (mode === 'speed') state.speed = null;
  else if (mode === 'higherLower') state.higherLower = null;
  else if (mode === 'silhouette') state.silhouette = null;
  else if (mode === 'iq') state.iq = null;
  else if (mode === 'legends') state.legends = null;
  else if (mode === 'cfbQuiz') state.cfbQuiz = { screen: 'setup', category: '', difficulty: '', roundSize: (state.cfbQuiz && state.cfbQuiz.roundSize) || 10, queue: [], index: 0, correctCount: 0, answeredIndex: null, missed: [] };
  else if (mode === 'cfbIq') state.cfbIq = null;
  else if (mode === 'cfbSpeed') state.cfbSpeed = null;
  else if (mode === 'cfbBlitz') state.cfbBlitz = null;
  else if (mode === 'cfbGrid') state.cfbGrid = null;
  else if (mode === 'daily') state.daily = null;
  else if (mode === 'cfbLegends') state.cfbLegends = null;
  else if (mode === 'h2h') state.h2h = null;
  else if (mode === 'h2hLive') { h2hLiveStopWatch(); state.h2hLive = null; }
  else if (mode === 'study') state.study = null;
  else if (mode === 'learn') state.learn = null;
  else if (mode === 'settings') state.settingsConfirmClear = false;
}
/* ============================== lazy data loading ==============================
   Only data/quiz.js (QUIZ) and data/cfb.js (CFB) load eagerly — they're needed
   immediately by the intro test every brand-new user hits, plus the Quiz/
   Speed/IQ modes that already reuse them. Every other mode's data file (the
   other ~75% of the app's 51k lines of data, cfb-speed.js alone is ~39% of
   it) loads on first entry into that specific mode instead. */
var MODE_DATA_FILES = {
  grid: ['data/grid.js'],
  higherLower: ['data/grid.js'],
  cfbGrid: ['data/cfb-grid.js'],
  blitz: ['data/blitz.js'],
  cfbBlitz: ['data/cfb-blitz.js'],
  silhouette: ['data/silhouette.js'],
  cfbSpeed: ['data/cfb-speed.js'],
  legends: ['data/legends.js', 'data/legends-meta.js'],
  cfbLegends: ['data/cfb-legends.js', 'data/cfb-legends-meta.js']
};
var loadedScripts = {};
var loadingScripts = {};
function loadScript(src) {
  if (loadedScripts[src]) return Promise.resolve();
  if (loadingScripts[src]) return loadingScripts[src];
  var p = new Promise(function (resolve, reject) {
    var el = document.createElement('script');
    el.src = src;
    el.onload = function () { loadedScripts[src] = true; resolve(); };
    el.onerror = function () { reject(new Error('Failed to load ' + src)); };
    document.body.appendChild(el);
  });
  loadingScripts[src] = p;
  return p;
}
// The top-level `var QUIZ = window.QUIZ_DATA || []`-style aliases (near the
// top of this file) are only captured once at parse time, so a data file
// that loads later needs this to re-point them at the now-populated
// window.* globals — plain top-level `var`s in one classic script are
// reassignable at any point, so this is safe to call any time.
function refreshDataAliases() {
  GRID_PLAYERS = window.GRID_PLAYERS || GRID_PLAYERS;
  GRID_CRITERIA = window.GRID_CRITERIA || GRID_CRITERIA;
  BLITZ_LISTS = window.BLITZ_LISTS || BLITZ_LISTS;
  SILHOUETTE_PLAYERS = window.SILHOUETTE_PLAYERS || SILHOUETTE_PLAYERS;
  CFB_SPEED = window.CFB_SPEED_DATA || CFB_SPEED;
  CFB_BLITZ_LISTS = window.CFB_BLITZ_LISTS || CFB_BLITZ_LISTS;
  CFB_GRID_PLAYERS = window.CFB_GRID_PLAYERS || CFB_GRID_PLAYERS;
  CFB_GRID_CRITERIA = window.CFB_GRID_CRITERIA || CFB_GRID_CRITERIA;
  LEGENDS_TEAMS = window.LEGENDS_TEAMS || LEGENDS_TEAMS;
  PLAYER_META = window.PLAYER_META || PLAYER_META;
  LEGENDS_DUOS = window.LEGENDS_DUOS || LEGENDS_DUOS;
  CFB_LEGENDS_TEAMS = window.CFB_LEGENDS_TEAMS || CFB_LEGENDS_TEAMS;
  CFB_PLAYER_META = window.CFB_PLAYER_META || CFB_PLAYER_META;
  CFB_LEGENDS_DUOS = window.CFB_LEGENDS_DUOS || CFB_LEGENDS_DUOS;
}
function enterMode(mode) {
  // Leaving an in-progress head-to-head match for anywhere else — stop its
  // live listener so it doesn't keep updating a screen nobody's looking at.
  if (state.screen === 'h2h' && mode !== 'h2h' && typeof h2hStopWatch === 'function') h2hStopWatch();
  if (state.screen === 'h2hLive' && mode !== 'h2hLive' && typeof h2hLiveStopWatch === 'function') h2hLiveStopWatch();
  stopTimers(); resetModeState(mode); state.screen = mode; renderAll();
  // "Continue where you left off" on Home reads this back — only real game
  // modes count, not navigational screens like leaderboard/profile/daily.
  if (LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).some(function (m) { return m.id === mode; })) {
    lsSet('nflTriviaLastMode', mode);
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay(mode);
  } else if (mode === 'h2h' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('h2h');
  } else if (mode === 'h2hLive' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('h2hLive');
  } else if (mode === 'learn' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('learn');
  } else if (mode === 'friends') {
    if (window.__fbSync && window.__fbSync.logPlay) window.__fbSync.logPlay('friends');
    loadFriendsData();
  } else if (mode === 'study' && window.__fbSync && window.__fbSync.logPlay) {
    window.__fbSync.logPlay('study');
  }
}
function modeLabelFor(id) {
  var m = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).find(function (x) { return x.id === id; });
  return m ? m.title : 'mode';
}
function goToMode(mode) {
  var files = MODE_DATA_FILES[mode];
  var pending = files && files.filter(function (f) { return !loadedScripts[f]; });
  if (pending && pending.length) {
    var app = document.getElementById('app');
    if (app) app.innerHTML = '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading ' + esc(modeLabelFor(mode)) + '…</div></div>';
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      enterMode(mode);
    }).catch(function () {
      if (app) app.innerHTML = '<div class="panel">Couldn’t load this mode’s data. Check your connection and try again. <button class="btn-secondary" data-go="home">Home</button></div>';
    });
    return;
  }
  // Data file(s) were already loaded by another mode/tab (e.g. Learn's
  // Heisman list also pulls in data/cfb-grid.js).
  if (files && files.length) refreshDataAliases();
  enterMode(mode);
}
function modeToolbarHtml(mode, ranked) {
  return (ranked === false ? '<div class="practice-pill">' + icon('graduationCap') + ' Practice — this round won’t be saved</div>' : '') +
    '<div class="mode-toolbar">' +
    '<button class="btn-tiny" data-report="' + mode + '">' + icon('flag') + ' Report</button>' +
    '<button class="btn-tiny" data-mode-restart="' + mode + '">' + icon('restart') + ' Restart</button>' +
    '<button class="btn-tiny" data-mode-exit>' + icon('close') + ' Exit to Home</button>' +
    '</div>';
}
// Practice-vs-Ranked: one shared "about to start" control (chip-row, same
// component as round-size/timer pickers) reused across all 12 existing game
// modes instead of a bespoke toggle per mode. state.rankedPref remembers
// each mode's last choice independently; absent/undefined defaults to
// Ranked (true) so existing users' behavior is unchanged until they opt in
// to Practice somewhere. Daily Challenge is deliberately exempt — it always
// counts, no toggle is rendered for it.
function rankedToggleHtml(mode) {
  var ranked = state.rankedPref[mode] !== false;
  return '<div class="chip-row">' +
    '<button class="chip-toggle' + (ranked ? ' active' : '') + '" data-ranked-toggle="' + mode + ':1">' + icon('target') + ' Ranked</button>' +
    '<button class="chip-toggle' + (!ranked ? ' active' : '') + '" data-ranked-toggle="' + mode + ':0">' + icon('graduationCap') + ' Practice</button>' +
    '</div>';
}
function setRankedPref(mode, ranked) {
  state.rankedPref[mode] = ranked;
  lsSet('nflTriviaRankedPref', state.rankedPref);
  renderAll();
}

// Lightweight "claim your name with a PIN" deterrent — see the comment above
// getNamePin/setNamePin in firebase-sync.js for what this is and isn't. hashStr
// is the same non-cryptographic hash already used to seed the daily-greeting
// RNG elsewhere in this file; good enough for "don't store the PIN in plain
// text next to it", not good enough to call this real security.
function pinHash(slug, pin) { return String(hashStr('reads-pin-v1:' + slug + ':' + pin)); }
function pinCacheKey(slug) { return 'nflTriviaPin__' + slug; }
var pendingNamePin = null; // { name, slug, mode: 'claim'|'verify' } while the PIN modal is open
function saveName(name) {
  name = (name || '').trim();
  if (!name) return;
  if (!window.__fbSync || !window.__fbSync.getNamePin) { finishSaveName(name); return; }
  var slug = slugify(name);
  var cached = lsGet(pinCacheKey(slug), null);
  window.__fbSync.getNamePin(slug).then(function (remoteHash) {
    if (!remoteHash) { openPinModal(name, slug, 'claim'); return; }
    if (cached && cached === remoteHash) { finishSaveName(name); return; }
    openPinModal(name, slug, 'verify');
  }).catch(function () {
    // Offline / sync unavailable — fall back to the old no-PIN behavior so
    // solo/offline play still works exactly like before this feature existed.
    finishSaveName(name);
  });
}
function finishSaveName(name) {
  state.name = name;
  lsSet('nflTriviaName', name);
  // The leaderboard snapshot (state.leaderboardData) almost always arrives
  // from Firestore before someone finishes typing their name — but
  // reconcileRating() bails out early with no name set, so a returning
  // player's cloud rating/stats sat there unused until now. Reconcile
  // immediately against whatever's already cached so a name typed on a new
  // device picks up their real rating right away instead of wrongly
  // launching the intro test and needing a refresh to fix itself.
  reconcileRating(state.leaderboardData);
  didInitialProfilePull = true;
  pullProfileSnapshot();
  if (!getRating()) { startIntroTest(); return; }
  if (!consumePendingLiveJoin()) renderAll();
}
function changeName() { state.name = ''; lsSet('nflTriviaName', ''); didInitialProfilePull = false; renderAll(); }

/* ============================== name PIN modal ============================== */
var pinTriggerEl = null;
function openPinModal(name, slug, mode) {
  pendingNamePin = { name: name, slug: slug, mode: mode };
  pinTriggerEl = document.activeElement;
  var titleEl = document.getElementById('pin-title');
  var contextEl = document.getElementById('pin-context');
  var inputEl = document.getElementById('pin-input');
  var errorEl = document.getElementById('pin-error');
  var skipBtn = document.getElementById('pin-skip');
  var submitBtn = document.getElementById('pin-submit');
  if (mode === 'claim') {
    if (titleEl) titleEl.textContent = 'Protect this name';
    if (contextEl) contextEl.textContent = '"' + name + '" is open. Set a 4-digit PIN so nobody else can play under your name and touch your leaderboard score — you\'ll enter it again next time you use this name on a new device.';
    if (skipBtn) skipBtn.style.display = '';
    if (submitBtn) submitBtn.textContent = 'Set PIN & Continue';
  } else {
    if (titleEl) titleEl.textContent = 'Enter PIN';
    if (contextEl) contextEl.textContent = '"' + name + '" already has a PIN set. Enter it to continue, or use a different name.';
    if (skipBtn) skipBtn.style.display = 'none';
    if (submitBtn) submitBtn.textContent = 'Continue';
  }
  if (inputEl) inputEl.value = '';
  if (errorEl) { errorEl.style.display = 'none'; errorEl.textContent = ''; }
  var modal = document.getElementById('pin-modal');
  var backdrop = document.getElementById('pin-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () { if (inputEl) inputEl.focus(); }, 0);
}
function closePinModal() {
  var modal = document.getElementById('pin-modal');
  var backdrop = document.getElementById('pin-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (pinTriggerEl && document.contains(pinTriggerEl)) pinTriggerEl.focus();
  pinTriggerEl = null;
  pendingNamePin = null;
}
function pinModalError(msg) {
  var errorEl = document.getElementById('pin-error');
  if (errorEl) { errorEl.textContent = msg; errorEl.style.display = ''; }
}
function pinModalSubmit() {
  if (!pendingNamePin) return;
  var inputEl = document.getElementById('pin-input');
  var pin = inputEl ? inputEl.value.trim() : '';
  if (!/^\d{4}$/.test(pin)) { pinModalError('Enter a 4-digit PIN.'); return; }
  var p = pendingNamePin;
  var hash = pinHash(p.slug, pin);
  if (p.mode === 'claim') {
    if (window.__fbSync && window.__fbSync.setNamePin) window.__fbSync.setNamePin(p.slug, hash);
    lsSet(pinCacheKey(p.slug), hash);
    closePinModal();
    finishSaveName(p.name);
    return;
  }
  // verify mode
  window.__fbSync.getNamePin(p.slug).then(function (remoteHash) {
    if (remoteHash !== hash) { pinModalError('Wrong PIN. Try again, or use a different name.'); return; }
    lsSet(pinCacheKey(p.slug), hash);
    var name = p.name;
    closePinModal();
    finishSaveName(name);
  }).catch(function () { pinModalError('Could not check that PIN — try again.'); });
}
function pinModalSkip() {
  if (!pendingNamePin) return;
  var name = pendingNamePin.name;
  closePinModal();
  finishSaveName(name);
}

function nameBarHtml() {
  return '<div class="name-bar">' +
    (state.name
      ? '<span>Playing as <b>' + esc(state.name) + '</b></span><button class="btn-secondary" data-go="profile">Stats</button><button class="btn-secondary" data-change-name>Change</button>'
      : '<input id="name-input" placeholder="Your name (for the leaderboard)" />' +
        '<button class="btn-primary" data-save-name>Save</button>') +
    '</div>';
}

/* ============================== home ============================== */
// Single source of truth for every mode's id/icon/title/description — drives the
// Home screen's mode-card grid AND the NFL/CFB dropdown-or-bottom-sheet picker
// (see openModeSheet), so the two never drift out of sync with each other.
// difficulty here is a per-MODE tag (how forgiving the format itself is —
// multiple-choice-with-feedback vs. open-recall-typing-with-no-hints, timed
// or not) — deliberately not called "Easy/Medium/Hard" so it can't be
// confused with Quiz's own internal per-QUESTION difficulty picker, which is
// a completely different, unrelated setting.
var LEAGUE_MODES = {
  nfl: [
    { id: 'quiz', icon: 'helpCircle', title: 'NFL Quiz', desc: '482 multiple-choice questions across 16 categories. Choose category, difficulty, and round length.', featured: true, difficulty: 'casual' },
    { id: 'grid', icon: 'grid', title: 'NFL Grid', desc: 'A freshly generated 3x3 grid every round. Name a player who satisfies both the row and the column.', featured: true, difficulty: 'hardcore' },
    { id: 'blitz', icon: 'timer', title: 'NFL Blitz', desc: 'Sporcle-style: type every correct answer you can before the clock runs out.', difficulty: 'hardcore' },
    { id: 'speed', icon: 'zap', title: 'NFL Speed', desc: 'Rapid-fire multiple choice against the clock. Build a streak for bonus points.', difficulty: 'competitive' },
    { id: 'silhouette', icon: 'search', title: 'NFL Silhouette', desc: 'A generic pose silhouette and a ladder of clues — guess the player using as few hints as you can.', difficulty: 'competitive' },
    { id: 'iq', icon: 'brain', title: 'NFL IQ Test', desc: '25 questions, no feedback until the end. Get a Football IQ score and a category breakdown.', featured: true, difficulty: 'competitive' },
    { id: 'legends', icon: 'trophy', title: '17-0', desc: 'Draft a 7-player team from real players\' real seasons (1999-2025) and see if it grades out as a perfect season.', difficulty: 'competitive' },
    { id: 'higherLower', icon: 'arrowUp', title: 'Higher or Lower', desc: 'Two real players, one real stat — guess higher or lower than the last one. Keep going until you miss.', difficulty: 'casual' }
  ],
  cfb: [
    { id: 'cfbQuiz', icon: 'graduationCap', title: 'College Football Quiz', desc: '456 CFB questions across 10 categories — Heisman, rivalries, coaches, bowls, and more.', featured: true, difficulty: 'casual' },
    { id: 'cfbGrid', icon: 'grid', title: 'CFB Immaculate Grid', desc: 'A freshly generated 3x3 grid of schools and All-America/Heisman criteria. Name a player who satisfies both the row and the column.', featured: true, difficulty: 'hardcore' },
    { id: 'cfbBlitz', icon: 'timer', title: 'CFB Blitz', desc: 'Sporcle-style college football: type every correct answer you can before the clock runs out.', difficulty: 'hardcore' },
    { id: 'cfbSpeed', icon: 'zap', title: 'CFB Speed Round', desc: 'Rapid-fire college football multiple choice against the clock. Build a streak for bonus points.', difficulty: 'competitive' },
    { id: 'cfbIq', icon: 'book', title: 'College Football IQ Test', desc: 'The IQ Test format, college edition. 25 questions, no feedback until the end.', featured: true, difficulty: 'competitive' },
    { id: 'cfbLegends', icon: 'trophy', title: 'CFB 12-0', desc: 'Draft an 8-player college roster (including a whole team DEFENSE) from real players\' and teams\' real seasons (1990-2025), then see how your 12-game regular season plays out — and where it lands you in the postseason.', difficulty: 'competitive' }
  ]
};
var LEAGUE_LABELS = { nfl: 'NFL Modes', cfb: 'College Football Modes' };

/* ============================== favorite team ==============================
   NFL team codes/names match GRID_TEAM_NAMES in data/grid.js exactly (all 32
   teams supported by NFL Grid's own team criteria). The CFB list is the same
   48 schools CFB_GRID_SCHOOL_CODES in data/cfb-grid.js supports, PLUS every
   other current Power 4 (SEC/Big Ten/Big 12/ACC) school not already in that
   48 — the picker itself is meant to cover every major program a real fan
   might pick, which is a bigger list than what CFB Grid's own criteria pool
   happens to include. The practical effect: the CFB Grid gameplay nudge
   (cfbGridWeightOf, see the CFB Grid section) only ever does anything for
   the original 48 — for a Power-4-only school outside that set, the nudge
   condition just never matches and buildCfbGridAttempt() falls back to
   normal weighted selection, same as having no favorite at all. Every other
   part of this feature (the picker, header accent, greeting, share-card
   tint, "Your Team" chip) works identically for all 73 schools regardless.
   Hardcoded here (not read from either data file) because this needs to work
   from a cold Home-screen load, before either lazy-loaded file has
   necessarily been fetched. Colors are each team/school's real, publicly-
   documented primary color (the same kind of value sports-reference sites
   list freely) — NOT logos. Deliberately no logo images anywhere in this
   feature: real NFL/NCAA team logos are trademarked, this repo has no logo
   assets, and fetching or embedding them for a publicly-shared app would be
   a real trademark risk with no clean fallback — color + team name carries
   the same identity without that risk. */
// `chant` is each team's real, distinctive rallying cry (not a generic "Go
// [Mascot]", which nearly every program has and doesn't say anything unique
// about it — "War Eagle", "Roll Tide" style phrases specific to that team's
// own culture/history) — deliberately included ONLY where I'm genuinely
// confident it's real and well-known, left off entirely otherwise rather
// than inventing a plausible-sounding one. Every render site treats a
// missing chant as "say nothing extra," never a placeholder.
var NFL_TEAMS = [
  { id: 'ARI', name: 'Arizona Cardinals', color: '#97233F', color2: '#000000' },
  { id: 'ATL', name: 'Atlanta Falcons', color: '#A71930', color2: '#000000' },
  { id: 'BAL', name: 'Baltimore Ravens', color: '#241773', color2: '#000000' },
  { id: 'BUF', name: 'Buffalo Bills', color: '#00338D', color2: '#C60C30' },
  { id: 'CAR', name: 'Carolina Panthers', color: '#0085CA', color2: '#101820' },
  { id: 'CHI', name: 'Chicago Bears', color: '#0B162A', color2: '#C83803', chant: 'Bear Down!' },
  { id: 'CIN', name: 'Cincinnati Bengals', color: '#FB4F14', color2: '#000000' },
  { id: 'CLE', name: 'Cleveland Browns', color: '#311D00', color2: '#FF3C00' },
  { id: 'DAL', name: 'Dallas Cowboys', color: '#041E42', color2: '#869397' },
  { id: 'DEN', name: 'Denver Broncos', color: '#FB4F14', color2: '#002244' },
  { id: 'DET', name: 'Detroit Lions', color: '#0076B6', color2: '#B0B7BC' },
  { id: 'GB', name: 'Green Bay Packers', color: '#203731', color2: '#FFB612', chant: 'Go Pack Go!' },
  { id: 'HOU', name: 'Houston Texans', color: '#03202F', color2: '#A71930' },
  { id: 'IND', name: 'Indianapolis Colts', color: '#002C5F' },
  { id: 'JAX', name: 'Jacksonville Jaguars', color: '#006778', color2: '#D7A22A' },
  { id: 'KC', name: 'Kansas City Chiefs', color: '#E31837', color2: '#FFB81C' },
  { id: 'LAC', name: 'Los Angeles Chargers', color: '#0080C6', color2: '#FFC20E' },
  { id: 'LAR', name: 'Los Angeles Rams', color: '#003594', color2: '#FFA300' },
  { id: 'LV', name: 'Las Vegas Raiders', color: '#000000', color2: '#A5ACAF' },
  { id: 'MIA', name: 'Miami Dolphins', color: '#008E97', color2: '#FC4C02' },
  { id: 'MIN', name: 'Minnesota Vikings', color: '#4F2683', color2: '#FFC62F', chant: 'Skol!' },
  { id: 'NE', name: 'New England Patriots', color: '#002244', color2: '#C60C30' },
  { id: 'NO', name: 'New Orleans Saints', color: '#D3BC8D', color2: '#101820', chant: 'Who Dat!' },
  { id: 'NYG', name: 'New York Giants', color: '#0B2265', color2: '#A71930' },
  { id: 'NYJ', name: 'New York Jets', color: '#125740' },
  { id: 'PHI', name: 'Philadelphia Eagles', color: '#004C54', color2: '#A5ACAF', chant: 'Fly Eagles Fly!' },
  { id: 'PIT', name: 'Pittsburgh Steelers', color: '#FFB612', color2: '#101820', chant: 'Here We Go!' },
  { id: 'SF', name: 'San Francisco 49ers', color: '#AA0000', color2: '#B3995D' },
  { id: 'SEA', name: 'Seattle Seahawks', color: '#002244', color2: '#69BE28' },
  { id: 'TB', name: 'Tampa Bay Buccaneers', color: '#D50A0A', color2: '#34302B' },
  { id: 'TEN', name: 'Tennessee Titans', color: '#0C2340', color2: '#C8102E' },
  { id: 'WAS', name: 'Washington Commanders', color: '#5A1414', color2: '#FFB612' }
];
var CFB_TEAMS = [
  { id: 'Notre Dame', name: 'Notre Dame', code: "ND", color: '#0C2340', color2: '#C99700', chant: 'Wake Up the Echoes!' },
  { id: 'Yale', name: 'Yale', code: "YALE", color: '#00356B' },
  { id: 'Alabama', name: 'Alabama', code: "BAMA", color: '#9E1B32', chant: 'Roll Tide!' },
  { id: 'Ohio State', name: 'Ohio State', code: "OSU", color: '#BB0000', color2: '#666666', chant: 'O-H! I-O!' },
  { id: 'Michigan', name: 'Michigan', code: "MICH", color: '#00274C', color2: '#FFCB05', chant: 'Go Blue!' },
  { id: 'Oklahoma', name: 'Oklahoma', code: "OU", color: '#841617', color2: '#F4E5C2', chant: 'Boomer Sooner!' },
  { id: 'Southern California', name: 'USC', code: "USC", color: '#990000', color2: '#FFC72C', chant: 'Fight On!' },
  { id: 'Princeton', name: 'Princeton', code: "PRIN", color: '#FF8F00' },
  { id: 'Harvard', name: 'Harvard', code: "HARV", color: '#A51C30' },
  { id: 'Nebraska', name: 'Nebraska', code: "NEB", color: '#E41C38', color2: '#F5F1E7', chant: 'Go Big Red!' },
  { id: 'Pittsburgh', name: 'Pittsburgh', code: "PITT", color: '#003594', color2: '#FFB81C' },
  { id: 'Texas', name: 'Texas', code: "TEX", color: '#BF5700', color2: '#FFFFFF', chant: 'Hook \'Em Horns!' },
  { id: 'Minnesota', name: 'Minnesota', code: "MINN", color: '#7A0019', color2: '#FFC62F', chant: 'Ski-U-Mah!' },
  { id: 'Penn State', name: 'Penn State', code: "PSU", color: '#041E42', color2: '#FFFFFF', chant: 'We Are... Penn State!' },
  { id: 'Army', name: 'Army', code: "ARMY", color: '#000000', color2: '#C4B581' },
  { id: 'LSU', name: 'LSU', code: "LSU", color: '#461D7C', color2: '#FDD023', chant: 'Geaux Tigers!' },
  { id: 'Stanford', name: 'Stanford', code: "STAN", color: '#8C1515' },
  { id: 'Penn', name: 'Penn', code: "PENN", color: '#011F5B' },
  { id: 'Georgia', name: 'Georgia', code: "UGA", color: '#BA0C2F', color2: '#000000', chant: 'Go Dawgs! Sic \'Em!' },
  { id: 'Illinois', name: 'Illinois', code: "ILL", color: '#E84A27', color2: '#13294B', chant: 'Oskee Wow-Wow!' },
  { id: 'Wisconsin', name: 'Wisconsin', code: "WISC", color: '#C5050C', chant: 'On Wisconsin!' },
  { id: 'Iowa', name: 'Iowa', code: "IOWA", color: '#FFCD00', color2: '#000000' },
  { id: 'Michigan State', name: 'Michigan State', code: "MSU", color: '#18453B', chant: 'Go Green! Go White!' },
  { id: 'Syracuse', name: 'Syracuse', code: "CUSE", color: '#F76900', color2: '#000E54' },
  { id: 'Florida', name: 'Florida', code: "UF", color: '#0021A5', color2: '#FA4616', chant: 'Gator Chomp!' },
  { id: 'Auburn', name: 'Auburn', code: "AUB", color: '#0C2340', color2: '#DD550C', chant: 'War Eagle!' },
  { id: 'Texas A&M', name: 'Texas A&M', code: "TAMU", color: '#500000', chant: 'Gig \'Em!' },
  { id: 'Florida State', name: 'Florida State', code: "FSU", color: '#782F40', color2: '#CEB888' },
  { id: 'Oklahoma State', name: 'Oklahoma State', code: "OKST", color: '#FF7300', color2: '#000000' },
  { id: 'TCU', name: 'TCU', code: "TCU", color: '#4D1979', chant: 'Riff Ram!' },
  { id: 'Colorado', name: 'Colorado', code: "COLO", color: '#000000', color2: '#CFB87C' },
  { id: 'Oregon', name: 'Oregon', code: "ORE", color: '#154733', color2: '#FEE123' },
  { id: 'Miami (FL)', name: 'Miami (FL)', code: "MIA", color: '#005030', color2: '#F47321', chant: 'The U!' },
  { id: 'UCLA', name: 'UCLA', code: "UCLA", color: '#2D68C4', color2: '#FFD100' },
  { id: 'Arkansas', name: 'Arkansas', code: "ARK", color: '#9D2235', color2: '#000000', chant: 'Woo Pig Sooie!' },
  { id: 'NC State', name: 'NC State', code: "NCST", color: '#CC0000' },
  { id: 'Texas Tech', name: 'Texas Tech', code: "TTU", color: '#CC0000', color2: '#000000' },
  { id: 'Arizona', name: 'Arizona', code: "ARIZ", color: '#AB0520', color2: '#0C234B', chant: 'Bear Down!' },
  { id: 'BYU', name: 'BYU', code: "BYU", color: '#002E5D' },
  { id: 'Clemson', name: 'Clemson', code: "CLEM", color: '#F56600', color2: '#522D80' },
  { id: 'Boston College', name: 'Boston College', code: "BC", color: '#98002E', color2: '#BC9B6A' },
  { id: 'Tennessee', name: 'Tennessee', code: "TENN", color: '#FF8200', color2: '#FFFFFF' },
  { id: 'Utah', name: 'Utah', code: "UTAH", color: '#CC0000' },
  { id: 'Kansas State', name: 'Kansas State', code: "KSU", color: '#512888', chant: 'EMAW!' },
  { id: 'Maryland', name: 'Maryland', code: "UMD", color: '#E03A3E', color2: '#000000' },
  { id: 'Baylor', name: 'Baylor', code: "BAY", color: '#154734', color2: '#FFB81C', chant: 'Sic \'Em Bears!' },
  { id: 'Georgia Tech', name: 'Georgia Tech', code: "GT", color: '#B3A369', color2: '#003057' },
  { id: 'Louisville', name: 'Louisville', code: "LOU", color: '#AD0000', color2: '#000000' },
  // The rest of the current Power 4 (SEC/Big Ten/Big 12/ACC) not already
  // covered above — see the header comment: these work everywhere in this
  // feature except the CFB Grid gameplay nudge, which only applies to the
  // original 48-school set CFB Grid's own criteria pool actually supports.
  { id: 'Kentucky', name: 'Kentucky', code: "UK", color: '#0033A0' },
  { id: 'Mississippi State', name: 'Mississippi State', code: "MSST", color: '#660000', chant: 'Hail State!' },
  { id: 'Missouri', name: 'Missouri', code: "MIZ", color: '#F1B82D', color2: '#000000', chant: 'M-I-Z... Z-O-U!' },
  { id: 'Ole Miss', name: 'Ole Miss', code: "MISS", color: '#CE1126', color2: '#14213D', chant: 'Hotty Toddy!' },
  { id: 'South Carolina', name: 'South Carolina', code: "SC", color: '#73000A', color2: '#000000' },
  { id: 'Vanderbilt', name: 'Vanderbilt', code: "VANDY", color: '#866D4B', color2: '#000000', chant: 'Anchor Down!' },
  { id: 'Indiana', name: 'Indiana', code: "IU", color: '#990000' },
  { id: 'Northwestern', name: 'Northwestern', code: "NW", color: '#4E2A84' },
  { id: 'Purdue', name: 'Purdue', code: "PUR", color: '#CEB888', color2: '#000000', chant: 'Boiler Up!' },
  { id: 'Rutgers', name: 'Rutgers', code: "RUTG", color: '#CC0033', color2: '#000000', chant: 'R-U Rah Rah!' },
  { id: 'Washington', name: 'Washington', code: "WASH", color: '#4B2E83', color2: '#FEC52E' },
  { id: 'Arizona State', name: 'Arizona State', code: "ASU", color: '#8C1D40', color2: '#FFC627', chant: 'Fork \'Em!' },
  { id: 'Cincinnati', name: 'Cincinnati', code: "CIN", color: '#E00122', color2: '#000000' },
  { id: 'Houston', name: 'Houston', code: "HOU", color: '#C8102E' },
  { id: 'Iowa State', name: 'Iowa State', code: "ISU", color: '#C8102E', color2: '#F1BE48' },
  { id: 'Kansas', name: 'Kansas', code: "KU", color: '#0051BA', color2: '#E8000D', chant: 'Rock Chalk Jayhawk!' },
  { id: 'UCF', name: 'UCF', code: "UCF", color: '#BA9B37', color2: '#000000' },
  { id: 'West Virginia', name: 'West Virginia', code: "WVU", color: '#002855', color2: '#EAAA00' },
  { id: 'California', name: 'California', code: "CAL", color: '#003262', color2: '#FDB515' },
  { id: 'Duke', name: 'Duke', code: "DUKE", color: '#003087' },
  { id: 'North Carolina', name: 'North Carolina', code: "UNC", color: '#7BAFD4', color2: '#13294B' },
  { id: 'SMU', name: 'SMU', code: "SMU", color: '#C8102E', color2: '#354CA1' },
  { id: 'Virginia', name: 'Virginia', code: "UVA", color: '#232D4B', color2: '#E57200', chant: 'Wahoowa!' },
  { id: 'Virginia Tech', name: 'Virginia Tech', code: "VT", color: '#630031', color2: '#CF4420' },
  { id: 'Wake Forest', name: 'Wake Forest', code: "WAKE", color: '#9E7E38', color2: '#000000' }
];
// Most teams are genuinely one-color for this app's purposes (a swatch dot
// doesn't need a school's full palette), but a few — Auburn's navy+orange
// chief among them — read as flatly wrong with just one. color2 is opt-in
// per team; a diagonal split reads clearly as "two-tone" even at swatch
// size, unlike a gradient blend which would just look muddy.
function teamSwatchStyle(t) {
  if (t.color2) return 'background: linear-gradient(135deg, ' + t.color + ' 50%, ' + t.color2 + ' 50%)';
  return 'background: ' + t.color;
}
function favoriteTeamsKey() { return 'nflTriviaFavoriteTeams'; }
function getFavoriteTeams() { return lsGet(favoriteTeamsKey(), { nfl: null, cfb: null, lastPicked: null }); }
function setFavoriteTeams(v) { lsSet(favoriteTeamsKey(), v); }
function favoriteTeamById(league, id) {
  var list = league === 'nfl' ? NFL_TEAMS : CFB_TEAMS;
  return list.find(function (t) { return t.id === id; }) || null;
}
// Two-step (NFL, then CFB) searchable picker, same accessible-dialog pattern
// as the rating/share/report modals — but its own body is re-rendered
// directly (renderTeamPickerBody) rather than through the main renderAll(),
// same reason the onboarding modal works this way: it's outside #app, and a
// full renderAll() would be pointless work just to update a few dozen list
// rows. Search re-renders on every keystroke, so — same as Learn's filter
// input and the main renderAll()'s name/game-input refocus block — the
// search box has to explicitly refocus + restore cursor position itself
// after every re-render, or the innerHTML replace would steal focus after
// the very first character typed.
var teamPickerTriggerEl = null;
function openTeamPicker() {
  state.teamPicker = { screen: 'nfl', filter: '' };
  teamPickerTriggerEl = document.activeElement;
  renderTeamPickerBody();
  var modal = document.getElementById('team-picker-modal');
  var backdrop = document.getElementById('team-picker-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
}
function closeTeamPicker() {
  var modal = document.getElementById('team-picker-modal');
  var backdrop = document.getElementById('team-picker-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (teamPickerTriggerEl && document.contains(teamPickerTriggerEl)) teamPickerTriggerEl.focus();
  teamPickerTriggerEl = null;
  state.teamPicker = null;
  renderAll(); // picking a team can change the header accent/home greeting
}
function renderTeamPickerBody() {
  var s = state.teamPicker;
  if (!s) return;
  var league = s.screen;
  var list = league === 'nfl' ? NFL_TEAMS : CFB_TEAMS;
  var current = getFavoriteTeams();
  var filter = s.filter.toLowerCase();
  var filtered = list.filter(function (t) { return !filter || t.name.toLowerCase().indexOf(filter) !== -1; });
  var body = document.getElementById('team-picker-body');
  if (!body) return;
  body.innerHTML =
    '<div class="team-picker-tabs" role="tablist">' +
    '<button class="team-picker-tab' + (league === 'nfl' ? ' active' : '') + '" role="tab" aria-selected="' + (league === 'nfl') + '" data-team-tab="nfl">NFL</button>' +
    '<button class="team-picker-tab' + (league === 'cfb' ? ' active' : '') + '" role="tab" aria-selected="' + (league === 'cfb') + '" data-team-tab="cfb">College Football</button>' +
    '</div>' +
    '<p class="mode-desc">Optional — used for a few personal touches around the app (and a light nudge in the random mix, never a hard filter). Change or clear it here anytime.</p>' +
    '<input id="team-picker-search" class="learn-filter-input" placeholder="Search teams…" value="' + esc(s.filter) + '" autocomplete="off" />' +
    '<div class="team-picker-list">' +
    (filtered.length ? filtered.map(function (t) {
      var active = current[league] === t.id;
      return '<button class="team-picker-row' + (active ? ' active' : '') + '" data-team-pick="' + league + ':' + esc(t.id) + '">' +
        '<span class="team-picker-swatch" style="' + teamSwatchStyle(t) + '"></span>' +
        '<span class="team-picker-row-text"><span>' + esc(t.name) + '</span>' + (t.chant ? '<span class="team-picker-chant">' + esc(t.chant) + '</span>' : '') + '</span>' +
        (active ? icon('check') : '') +
        '</button>';
    }).join('') : '<p class="mode-desc">No teams match “' + esc(s.filter) + '”.</p>') +
    '</div>' +
    '<div class="btn-row team-picker-actions">' +
    (current[league] ? '<button class="btn-secondary" data-team-clear="' + league + '">Clear</button>' : '') +
    '<button class="btn-primary" data-team-done>Done</button>' +
    '</div>';
  var input = document.getElementById('team-picker-search');
  if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
}
function teamPickerPick(league, id) {
  var current = getFavoriteTeams();
  current[league] = current[league] === id ? null : id; // clicking the already-active team unsets it
  // Whichever team you just touched becomes the "primary" one (see
  // primaryFavoriteTeam below) — otherwise picking a College team while an
  // NFL team was already set would silently keep showing the NFL color
  // everywhere, which reads as "picking a team didn't do anything."
  current.lastPicked = current[league] ? league : null;
  setFavoriteTeams(current);
  renderTeamPickerBody();
}
function teamPickerClear(league) {
  var current = getFavoriteTeams();
  current[league] = null;
  if (current.lastPicked === league) current.lastPicked = null;
  setFavoriteTeams(current);
  renderTeamPickerBody();
}
function teamPickerSetFilter(v) {
  if (!state.teamPicker) return;
  state.teamPicker.filter = v;
  renderTeamPickerBody();
}
function teamPickerSetTab(league) {
  if (!state.teamPicker || state.teamPicker.screen === league) return;
  state.teamPicker.screen = league;
  state.teamPicker.filter = '';
  renderTeamPickerBody();
}
// The one favorite team used for the header accent bar / share-card tint
// when both leagues are set — whichever one was picked/changed most
// recently (lastPicked, set in teamPickerPick above), so switching your
// College team actually shows up even if an NFL team was already set. Falls
// back to NFL-then-CFB only for an older stored value from before
// lastPicked existed, or if lastPicked's own team got cleared elsewhere.
function primaryFavoriteTeam() {
  var fav = getFavoriteTeams();
  if (fav.lastPicked && fav[fav.lastPicked]) return favoriteTeamById(fav.lastPicked, fav[fav.lastPicked]);
  if (fav.nfl) return favoriteTeamById('nfl', fav.nfl);
  if (fav.cfb) return favoriteTeamById('cfb', fav.cfb);
  return null;
}
// Sets both a plain hex custom property (for solid-color uses like the
// header bar / greeting text) and an "r,g,b" triplet (so CSS can build its
// own rgba() washes at whatever opacity a given spot needs — a background
// glow needs to be much more transparent than a border ever would) — same
// hex-parsing approach as hexToRgbaString/shadeHexColor in the share-card
// section, just exposed as CSS variables instead of used directly in canvas
// calls. body.has-fav-team drives the always-on bits (header bar, greeting);
// body.home-fav-theme additionally drives the fuller Home-screen wash
// (background glow, quick-action card accents) and is scoped to state.screen
// === 'home' specifically — everywhere else in the app stays exactly as
// themed by league (orange/teal), not by favorite team.
function hexToRgbTriplet(hex) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  return ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255);
}
// A fixed dark --accent-text (tuned for the app's own light-gold --accent)
// reads fine on gold but goes near-invisible on a dark team color like
// Auburn's navy — pickBadgeTextColor (already used for CFB Grid's team
// badges) picks white-or-dark per actual contrast instead. Blending color +
// color2 to their midpoint first, rather than testing color alone, is what
// keeps a two-tone badge/circle (icon sits roughly at the gradient's center)
// from picking a text color that only works against one end of it.
function blendedTeamTextColor(team) {
  var c1 = team.color.replace('#', ''), c2 = (team.color2 || team.color).replace('#', '');
  var mix = [0, 2, 4].map(function (i) {
    return Math.round((parseInt(c1.substr(i, 2), 16) + parseInt(c2.substr(i, 2), 16)) / 2)
      .toString(16).padStart(2, '0');
  }).join('');
  return pickBadgeTextColor(mix);
}
function relativeLuminance(r, g, b) {
  var lin = function (v) { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}
// A team color also gets used directly AS a foreground (rating-ring stroke,
// recommended-mode icons, the greeting text) against this app's near-black
// background — fine for a bright team color like Steelers gold, but a dark
// primary (Auburn navy, Ravens purple, half the league's navy/black
// helmets) goes nearly invisible there the same way the badge text did.
// Unlike blendedTeamTextColor (which picks BETWEEN white/dark for a color
// used as a background), this keeps the team's actual hue and just lightens
// it — mixing toward white a step at a time — until it clears a readable
// contrast ratio against the app background, so it still looks like "that
// team's color," just legible.
function readableOnDark(hex) {
  var r = parseInt(hex.substr(1, 2), 16), g = parseInt(hex.substr(3, 2), 16), b = parseInt(hex.substr(5, 2), 16);
  var bgL = 0.006; // ~relative luminance of this app's --bg (#0c110d)
  var contrast = function (L) { return (Math.max(L, bgL) + 0.05) / (Math.min(L, bgL) + 0.05); };
  var tries = 0;
  while (contrast(relativeLuminance(r, g, b)) < 3.2 && tries < 12) {
    r += (255 - r) * 0.16; g += (255 - g) * 0.16; b += (255 - b) * 0.16;
    tries++;
  }
  return '#' + [r, g, b].map(function (v) { return Math.round(v).toString(16).padStart(2, '0'); }).join('');
}
function applyFavoriteTeamAccent() {
  var team = primaryFavoriteTeam();
  var root = document.documentElement.style;
  root.setProperty('--fav-team-color', team ? team.color : '');
  // Falls back to the primary color when a team has no color2, so every
  // rule that blends both (the header bar, home-screen glow/border gradients
  // below) degrades to looking identical to a solid single color instead of
  // needing a separate "has two colors" branch in the CSS.
  root.setProperty('--fav-team-color-2', team ? (team.color2 || team.color) : '');
  root.setProperty('--fav-team-text', team ? blendedTeamTextColor(team) : '');
  root.setProperty('--fav-team-color-readable', team ? readableOnDark(team.color) : '');
  root.setProperty('--fav-team-color-2-readable', team ? readableOnDark(team.color2 || team.color) : '');
  if (team) {
    root.setProperty('--fav-team-color-rgb', hexToRgbTriplet(team.color));
    root.setProperty('--fav-team-color-2-rgb', hexToRgbTriplet(team.color2 || team.color));
  } else {
    root.setProperty('--fav-team-color-rgb', '');
    root.setProperty('--fav-team-color-2-rgb', '');
  }
  document.body.classList.toggle('has-fav-team', !!team);
  document.body.classList.toggle('home-fav-theme', !!team && state.screen === 'home');
}
// A few interchangeable templates rather than one fixed line, picked
// deterministically per day+name (same mulberry32/hashStr pattern as the
// Daily Challenge and recommendedModeHtml) so it's stable through a session
// but not the exact same sentence every single day.
var FAVORITE_TEAM_GREETINGS = ['What’s up, {team} fan?', 'Ready to roll, {team} fan?', 'Let’s go, {team}!', 'Hey there, {team} faithful.'];
// NFL_TEAMS' own id IS a real abbreviation already ('KC', 'SF', ...) so it
// doubles as team.code there; CFB_TEAMS carries an explicit code field since
// its id is the full school name instead.
function favoriteTeamBadgeHtml() {
  var team = primaryFavoriteTeam();
  if (!team) return '';
  return '<span class="fav-team-badge" style="' + teamSwatchStyle(team) + '">' + esc(team.code || team.id) + '</span>';
}
function favoriteTeamGreeting() {
  var team = primaryFavoriteTeam();
  if (!team || !state.name) return '';
  var rng = mulberry32(hashStr(todayStr() + '_greeting_' + state.name));
  var template = FAVORITE_TEAM_GREETINGS[Math.floor(rng() * FAVORITE_TEAM_GREETINGS.length)];
  var line = template.replace('{team}', team.name) + (team.chant ? ' ' + team.chant : '');
  return '<p class="fav-team-greeting">' + favoriteTeamBadgeHtml() + esc(line) + '</p>';
}
var TEAM_PROMPT_DISMISS_KEY = 'nflTriviaTeamPromptDismissed';
function teamPickerPromptCardHtml() {
  var fav = getFavoriteTeams();
  if (fav.nfl || fav.cfb) return '';
  if (!state.name || lsGet(TEAM_PROMPT_DISMISS_KEY, false)) return '';
  return '<div class="panel daily-card">' +
    '<div class="daily-card-title">' + icon('flag') + ' Got a team?</div>' +
    '<p class="mode-desc">Pick a favorite NFL and/or College team for a few personal touches around the app — totally optional, change it anytime from the header.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-team-picker-toggle>Pick My Teams</button>' +
    '<button class="btn-secondary" data-team-prompt-dismiss>Not Now</button>' +
    '</div></div>';
}
function dismissTeamPrompt() { lsSet(TEAM_PROMPT_DISMISS_KEY, true); renderAll(); }

var MODE_DIFFICULTY_LABEL = { casual: 'Casual', competitive: 'Competitive', hardcore: 'Hardcore' };
function modeCardHtml(m) {
  return '<button class="mode-card' + (m.featured ? ' featured' : '') + '" data-go="' + m.id + '">' +
    (m.difficulty ? '<span class="mode-difficulty mode-difficulty-' + m.difficulty + '">' + MODE_DIFFICULTY_LABEL[m.difficulty] + '</span>' : '') +
    '<div class="mode-icon">' + icon(m.icon) + '</div>' +
    '<div class="mode-title">' + esc(m.title) + '</div>' +
    '<div class="mode-desc">' + esc(m.desc) + '</div>' +
    '</button>';
}
function modeSectionHtml(league) {
  return '<h2 class="mode-section-title mode-section-title-' + league + '">' + esc(LEAGUE_LABELS[league]) + '</h2>' +
    '<div class="mode-grid mode-grid-' + league + '">' + LEAGUE_MODES[league].map(modeCardHtml).join('') + '</div>';
}
function continuePlayingCardHtml() {
  var last = lsGet('nflTriviaLastMode', null);
  if (!last || !LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).some(function (m) { return m.id === last; })) return '';
  return '<button class="continue-card" data-go="' + esc(last) + '">' +
    '<span class="continue-card-label">Continue where you left off</span>' +
    '<span class="continue-card-mode">' + icon('play') + ' ' + esc(modeLabelFor(last)) + '</span>' +
    '</button>';
}
// A mode's "times played" lives under a different key per mode (roundsPlayed,
// gamesPlayed, attempts, testsTaken, sessionsPlayed, completions) since each
// stats shape grew independently in DEFAULT_STATS — this just normalizes
// across all of them for the one thing recommendedModeHtml() needs to know.
function modeTimesPlayed(id) {
  var st = state.stats[id];
  if (!st) return 0;
  return st.roundsPlayed || st.gamesPlayed || st.attempts || st.testsTaken || st.sessionsPlayed || st.completions || 0;
}
// "Recommended for you" — deliberately deterministic per day+name (same
// seeded-PRNG pattern as the Daily Challenge) rather than Math.random(),
// so the suggestion doesn't change on every re-render/click and instead
// reads as a considered daily pick. Prioritizes modes never played at all
// (exploration); once everything's been tried at least once, falls back to
// whichever mode has been played the least (keeps rotation fresh).
function h2hCardHtml() {
  var st = state.stats.h2h || {};
  var recordBit = st.matchesPlayed ? (st.wins + '-' + st.losses + (st.ties ? '-' + st.ties : '')) : 'New';
  return '<button class="continue-card h2h-card" data-go="h2h">' +
    '<span class="continue-card-label">Challenge a friend &middot; ' + esc(recordBit) + '</span>' +
    '<span class="continue-card-mode">' + icon('versus') + ' Head-to-Head</span>' +
    '</button>';
}
function learnCardHtml() {
  return '<button class="continue-card learn-card" data-go="learn">' +
    '<span class="continue-card-label">Facts, history &amp; Hall of Famers</span>' +
    '<span class="continue-card-mode">' + icon('book') + ' Learn</span>' +
    '</button>';
}
function friendsCardHtml() {
  var count = getFriends().length;
  var label = count ? (count + ' friend' + (count === 1 ? '' : 's') + ' added') : 'See how they stack up';
  return '<button class="continue-card friends-card" data-go="friends">' +
    '<span class="continue-card-label">' + esc(label) + '</span>' +
    '<span class="continue-card-mode">' + icon('users') + ' Friends</span>' +
    '</button>';
}
function recommendedModeHtml() {
  if (!state.name) return '';
  var all = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  var last = lsGet('nflTriviaLastMode', null);
  var rng = mulberry32(hashStr(todayStr() + '_reco_' + state.name));
  var unplayed = seededShuffle(all.filter(function (m) { return modeTimesPlayed(m.id) === 0; }), rng);
  var pick, eyebrow;
  if (unplayed.length) {
    pick = unplayed[0];
    eyebrow = 'New to you';
  } else {
    var minPlays = Math.min.apply(null, all.map(function (m) { return modeTimesPlayed(m.id); }));
    var leastPlayed = seededShuffle(all.filter(function (m) { return modeTimesPlayed(m.id) === minPlays; }), rng);
    pick = leastPlayed[0];
    eyebrow = 'Keep it fresh';
  }
  if (!pick || pick.id === last) return '';
  return '<button class="recommend-card" data-go="' + pick.id + '">' +
    '<span class="recommend-card-icon">' + icon(pick.icon) + '</span>' +
    '<span class="recommend-card-text"><span class="recommend-card-label">' + esc(eyebrow) + ' &middot; Recommended</span>' +
    '<span class="recommend-card-mode">' + esc(pick.title) + '</span></span>' +
    '</button>';
}
function renderHome() {
  return '<div class="hero"><img src="assets/brand/reads-logo.jpg" alt="Reads" class="hero-logo" />' +
    '<h1 class="hero-tagline">NFL &amp; College Football trivia, 12 ways to play.</h1>' +
    favoriteTeamGreeting() +
    '<p>One adaptive Football Rating tracks how good you actually are — across every mode, every device.</p></div>' +
    teamPickerPromptCardHtml() +
    dailyChallengeCardHtml() +
    continuePlayingCardHtml() +
    h2hCardHtml() +
    h2hLiveCardHtml() +
    learnCardHtml() +
    friendsCardHtml() +
    studyCardHtml() +
    recommendedModeHtml() +
    modeSectionHtml('nfl') +
    modeSectionHtml('cfb') +
    '<button class="btn-secondary leaderboard-link" data-go="leaderboard">' + icon('trophy') + ' View Leaderboard</button>' +
    (getRating() ? '<button class="btn-secondary leaderboard-link" data-retake-intro>' + icon('restart') + ' Retake Intro Test (resets Football Rating)</button>' : '') ;
}

/* ============================== NFL/CFB mode picker (dropdown / bottom sheet) ==============================
   Same panel serves as a small anchored dropdown on desktop and a full-width
   slide-up bottom sheet on mobile — see #mode-sheet's media query in styles.css.
   Triggered by any [data-league-toggle] button (there are two: one in #top-nav
   for desktop, one in #bottom-nav for mobile — only one is ever visible at a
   time per the breakpoint, but both work identically). */
var modeSheetOpenLeague = null;
var modeSheetTriggerEl = null; // focus returns here on close — standard accessible-dialog pattern
function openModeSheet(league) {
  modeSheetOpenLeague = league;
  modeSheetTriggerEl = document.activeElement;
  var titleEl = document.getElementById('mode-sheet-title');
  var itemsEl = document.getElementById('mode-sheet-items');
  if (titleEl) titleEl.textContent = LEAGUE_LABELS[league];
  if (itemsEl) {
    var favTeam = favoriteTeamById(league, getFavoriteTeams()[league]);
    itemsEl.innerHTML =
      (favTeam ? '<button class="mode-sheet-your-team" data-team-picker-toggle><span class="team-picker-swatch" style="' + teamSwatchStyle(favTeam) + '"></span>Your team: ' + esc(favTeam.name) + (favTeam.chant ? ' — ' + esc(favTeam.chant) : '') + '</button>' : '') +
      LEAGUE_MODES[league].map(function (m) {
        return '<button class="mode-sheet-item" data-go="' + m.id + '"><span class="msi-icon">' + icon(m.icon) + '</span><span class="msi-text">' + esc(m.title) +
          '<span class="msi-desc">' + esc(m.desc) + '</span></span></button>';
      }).join('');
  }
  var sheet = document.getElementById('mode-sheet');
  var backdrop = document.getElementById('mode-sheet-backdrop');
  if (sheet) sheet.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    var isOpen = btn.dataset.leagueToggle === league;
    btn.classList.toggle('sheet-open', isOpen);
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
  // Move focus into the dialog once its open transition has started — the
  // close button is always present regardless of which league's items just
  // got rendered, so it's a reliable landing spot.
  setTimeout(function () {
    var closeBtn = document.getElementById('mode-sheet-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeModeSheet() {
  modeSheetOpenLeague = null;
  var sheet = document.getElementById('mode-sheet');
  var backdrop = document.getElementById('mode-sheet-backdrop');
  if (sheet) sheet.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    btn.classList.remove('sheet-open');
    btn.setAttribute('aria-expanded', 'false');
  });
  if (modeSheetTriggerEl && document.contains(modeSheetTriggerEl)) modeSheetTriggerEl.focus();
  modeSheetTriggerEl = null;
}
function toggleModeSheet(league) {
  if (modeSheetOpenLeague === league) closeModeSheet();
  else openModeSheet(league);
}

/* ============================== onboarding ==============================
   A short, dismissible 4-step walkthrough. Auto-opens once, the very first
   time the app is ever loaded on a device (tracked by ONBOARD_KEY in
   localStorage) — separate from name entry / the intro test, since a brand
   new visitor should understand what this app even is before either of
   those. Re-openable any time via the "?" button in the header — which is
   now CONTEXTUAL: while state.screen is an actual game mode, "?" shows a
   quick one-step tip for just that mode (reusing its own LEAGUE_MODES desc
   text) instead of the full walkthrough, so returning players don't have to
   sit through the whole intro again just to check a mode's rules. See
   contextualHelpSteps() and the help-toggle click handler below. The full
   walkthrough's final step's button is a real call-to-action (not just a
   "close" button) — worded and wired differently depending on where this
   person already is: straight into the intro test for a brand-new visitor,
   or into today's Daily Challenge for someone who already has a rating. A
   contextual mode tip's button always just says "Got it" and closes. */
var ONBOARD_KEY = 'nflTriviaOnboarded';
// A real, answerable question (id 15 in data/quiz.js — the '72 Dolphins'
// perfect season, eagerly loaded so it's always available here) rendered
// with the exact same quiz-option/feedback markup and classes as the real
// Quiz mode, so clicking an answer during onboarding IS the real interaction,
// not a mockup of it — "show, don't tell" in place of the old text-only step.
var ONBOARDING_SAMPLE_QID = 15;
function onboardingSampleQuestion() { return QUIZ.find(function (q) { return q.id === ONBOARDING_SAMPLE_QID; }); }
var ONBOARDING_STEPS = [
  {
    title: 'What is Reads?',
    body: 'NFL and College Football trivia with 12 game modes, built around one thing that follows you everywhere: your <b>Football Rating</b> — an adaptive number that tracks your real skill over time instead of resetting every round. It’s free, works right in your browser, and there’s no account to create — just pick a name.'
  },
  { title: 'Try a real question', type: 'sample' },
  {
    title: 'Pick your mode',
    body: '<div class="onboarding-modes">' +
      '<span class="onboarding-mode-chip">' + icon('helpCircle') + ' Quiz</span>' +
      '<span class="onboarding-mode-chip">' + icon('grid') + ' Grid</span>' +
      '<span class="onboarding-mode-chip">' + icon('timer') + ' Blitz</span>' +
      '<span class="onboarding-mode-chip">' + icon('zap') + ' Speed</span>' +
      '<span class="onboarding-mode-chip">' + icon('search') + ' Silhouette</span>' +
      '<span class="onboarding-mode-chip">' + icon('trophy') + ' 12-0/17-0</span>' +
      '</div>Straight trivia, a name-the-player grid, timed challenges, and a fantasy-style roster draft — every mode exists for both NFL and College Football. Every one of them also has a Practice option, for when you just want to play without it touching your rating.'
  },
  {
    title: 'Come back every day',
    body: 'A <b>Daily Challenge</b> drops every day — the same one for everyone, so it doubles as its own mini leaderboard. Complete it to build your streak, and don’t stress about one bad day: a grace day every week keeps your streak alive even if you miss.'
  },
  {
    title: 'Your rating goes with you',
    body: 'Save a name once and your Football Rating, stats, and leaderboard rank sync across every device you play on — same name, same progress, anywhere. The leaderboard itself can be filtered to today, this week, or all-time.'
  },
  {
    title: 'Save it to your Home Screen',
    body: '<div class="onboarding-install-list">' +
      '<div class="onboarding-install-row">' + icon('share', 'onboarding-install-icon') + '<div><b>iPhone / iPad (Safari)</b><br>Tap the Share icon, then “Add to Home Screen.”</div></div>' +
      '<div class="onboarding-install-row">' + icon('download', 'onboarding-install-icon') + '<div><b>Android (Chrome)</b><br>Tap the ⋮ menu, then “Add to Home screen” or “Install app.”</div></div>' +
      '<div class="onboarding-install-row">' + icon('download', 'onboarding-install-icon') + '<div><b>Desktop (Chrome/Edge)</b><br>Click the install icon in the address bar, or the ⋮ menu → “Install Reads…”</div></div>' +
      '</div>Installed, it opens full-screen like a real app — no browser bar — and solo play still works offline.'
  }
];
// A one-off single-step "walkthrough" for the contextual "?" case — see
// openOnboarding(steps) below, which accepts either this shape or the full
// ONBOARDING_STEPS array interchangeably.
function contextualHelpSteps(m) {
  return [{ title: m.title, body: '<div class="onboarding-modes"><span class="onboarding-mode-chip">' + icon(m.icon) + ' ' + esc(m.title) + '</span></div>' + esc(m.desc) }];
}
var onboardingActiveSteps = ONBOARDING_STEPS;
var onboardingIndex = 0;
var onboardingSampleAnswered = null;
var onboardingTriggerEl = null;
function onboardingCtaLabel() {
  if (onboardingActiveSteps !== ONBOARDING_STEPS) return 'Got it';
  return getRating() ? "Try Today's Challenge" : 'Start the Intro Test';
}
function renderOnboardingSample() {
  var q = onboardingSampleQuestion();
  // Safety fallback only — QUIZ loads eagerly before app.js ever runs, so
  // this should be unreachable in practice.
  if (!q) return '<p class="mode-desc">Real questions, real feedback — try any mode from Home to see for yourself.</p>';
  var answered = onboardingSampleAnswered !== null;
  return '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === onboardingSampleAnswered) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-onboarding-sample-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (onboardingSampleAnswered === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Not quite — it was ' + esc(q.options[q.correctIndex]) + '.</span>') + '</div>' +
        '<p class="mode-desc">That’s the whole loop — pick, get instant feedback, move on. Every mode builds on it a little differently.</p>'
      : '')
    ;
}
function onboardingPickSample(i) {
  if (onboardingSampleAnswered !== null) return;
  onboardingSampleAnswered = i;
  var q = onboardingSampleQuestion();
  playSound(q && i === q.correctIndex ? 'correct' : 'wrong');
  renderOnboardingStep();
}
function renderOnboardingStep() {
  var step = onboardingActiveSteps[onboardingIndex];
  var body = document.getElementById('onboarding-body');
  if (body) body.innerHTML = '<div class="onboarding-step-title" id="onboarding-title">' + esc(step.title) + '</div>' +
    '<div class="onboarding-step-body">' + (step.type === 'sample' ? renderOnboardingSample() : step.body) + '</div>';
  var dots = document.getElementById('onboarding-dots');
  if (dots) {
    dots.innerHTML = onboardingActiveSteps.length > 1 ? onboardingActiveSteps.map(function (_, i) {
      return '<span class="onboarding-dot' + (i === onboardingIndex ? ' active' : '') + '"></span>';
    }).join('') : '';
  }
  var nextBtn = document.getElementById('onboarding-next');
  if (nextBtn) nextBtn.textContent = onboardingIndex === onboardingActiveSteps.length - 1 ? onboardingCtaLabel() : 'Next';
}
function openOnboarding(steps) {
  onboardingActiveSteps = steps || ONBOARDING_STEPS;
  onboardingIndex = 0;
  onboardingSampleAnswered = null;
  onboardingTriggerEl = document.activeElement;
  renderOnboardingStep();
  var modal = document.getElementById('onboarding-modal');
  var backdrop = document.getElementById('onboarding-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var nextBtn = document.getElementById('onboarding-next');
    if (nextBtn) nextBtn.focus();
  }, 0);
}
function closeOnboarding() {
  // The sample question's crowd-cheer SFX has no max-duration cap (unlike
  // 'wrong') because in every other mode the next playSound() call cuts it
  // off naturally. Onboarding's sample question is answered exactly once —
  // nothing after it calls playSound() again — so without this, a correct
  // guess here just keeps the crowd noise playing indefinitely through the
  // rest of the walkthrough and beyond.
  if (typeof stopSfx === 'function') stopSfx();
  var modal = document.getElementById('onboarding-modal');
  var backdrop = document.getElementById('onboarding-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  lsSet(ONBOARD_KEY, true);
  if (onboardingTriggerEl && document.contains(onboardingTriggerEl)) onboardingTriggerEl.focus();
  onboardingTriggerEl = null;
}
// The CTA itself: for a returning visitor who already has a rating, jump
// straight into today's Daily Challenge. For a brand-new visitor, either
// start the intro test directly (if they already typed a name on a prior
// visit but never took it) or just land back on Home with the name field
// focused — saveName() already auto-starts the intro test the moment a name
// is saved with no existing rating, so this closes the loop naturally either
// way without duplicating that logic here. A contextual mode tip (see
// contextualHelpSteps above) skips all of this — "Got it" just closes.
function onboardingFinish() {
  closeOnboarding();
  if (onboardingActiveSteps !== ONBOARDING_STEPS) { renderAll(); return; }
  if (getRating()) { goToMode('daily'); return; }
  if (state.name) { startIntroTest(); return; }
  renderAll();
}
function onboardingNext() {
  if (typeof stopSfx === 'function') stopSfx();
  if (onboardingIndex >= onboardingActiveSteps.length - 1) { onboardingFinish(); return; }
  onboardingIndex++;
  renderOnboardingStep();
}

/* ============================== missed-question pool (for Study mode) ==============================
   A persisted, per-league, per-name log of question ids you've gotten wrong
   in Quiz or CFB Quiz — this is what Study mode below draws its round from,
   and grouping it by each question's own `category` field is also exactly
   how "weak categories" gets derived (see weakCategories) — no separate
   category-accuracy tracking needed, it falls straight out of the same log.
   A question is added the moment you miss it anywhere (pickQuizAnswer/
   pickCfbAnswer already call addToMissedPool below) and removed the moment
   you answer it correctly ANYWHERE, not just in Study mode itself — getting
   it right in a normal round "graduates" it out of your weak pool too, so
   Study mode isn't the only way to fix a weak spot. Capped at 200 entries
   (oldest dropped first) so this can't grow unbounded over months of play.
   Local-only, same as the streak/badges — not synced to Firebase. */
var MISSED_POOL_CAP = 200;
function missedPoolKey(league) { return 'nflTriviaMissedPool__' + league + '__' + slugify(state.name); }
function getMissedPool(league) { return state.name ? lsGet(missedPoolKey(league), []) : []; }
function addToMissedPool(league, id) {
  if (!state.name) return;
  var pool = getMissedPool(league);
  if (pool.indexOf(id) === -1) {
    pool.push(id);
    if (pool.length > MISSED_POOL_CAP) pool.shift();
    lsSet(missedPoolKey(league), pool);
  }
}
function removeFromMissedPool(league, id) {
  if (!state.name) return;
  var pool = getMissedPool(league);
  var idx = pool.indexOf(id);
  if (idx !== -1) { pool.splice(idx, 1); lsSet(missedPoolKey(league), pool); }
}
// Real signal, not a separate tracked stat: which categories show up most
// among your currently-missed questions. Naturally shrinks as questions get
// mastered (removed from the pool), so this always reflects your CURRENT
// weak spots, not a lifetime tally that never improves.
function weakCategories(league) {
  var pool = getMissedPool(league);
  var source = league === 'nfl' ? QUIZ : CFB;
  var counts = {};
  pool.forEach(function (id) {
    var q = source.find(function (qq) { return qq.id === id; });
    if (q) counts[q.category] = (counts[q.category] || 0) + 1;
  });
  return Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; }).map(function (cat) { return { category: cat, count: counts[cat] }; });
}

/* ============================== classic quiz ============================== */
function quizCategories() { return Array.from(new Set(QUIZ.map(function (q) { return q.category; }))).sort(); }
function quizDifficulties() { return Array.from(new Set(QUIZ.map(function (q) { return q.difficulty; }))).sort(); }
function quizPool(category, difficulty) {
  return QUIZ.filter(function (q) {
    return (!category || q.category === category) && (!difficulty || q.difficulty === difficulty);
  });
}
function currentQuizQuestion() {
  var id = state.quiz.queue[state.quiz.index];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startQuizRound(category, difficulty, roundSize) {
  var pool = quizPool(category, difficulty);
  var ids = drawNoRepeat('quiz_' + (category || 'all') + '_' + (difficulty || 'all'), pool.map(function (q) { return q.id; }), roundSize);
  state.quiz = { screen: 'question', category: category, difficulty: difficulty, roundSize: roundSize, queue: ids, index: 0, correctCount: 0, answeredIndex: null, missed: [], ranked: state.rankedPref.quiz !== false };
  renderAll();
}
function pickQuizAnswer(i) {
  if (state.quiz.answeredIndex !== null) return;
  state.quiz.answeredIndex = i;
  var q = currentQuizQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) { state.quiz.correctCount++; if (q) removeFromMissedPool('nfl', q.id); }
  else if (q) { state.quiz.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i }); addToMissedPool('nfl', q.id); }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextQuizQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  if (state.quiz.index + 1 >= state.quiz.queue.length) {
    state.quiz.screen = 'summary';
    finishQuizRound();
  } else {
    state.quiz.index++;
    state.quiz.answeredIndex = null;
  }
  renderAll();
}
function finishQuizRound() {
  var pct = Math.round(100 * state.quiz.correctCount / state.quiz.queue.length);
  if (state.quiz.ranked !== false) {
    var st = state.stats.quiz;
    st.correctTotal += state.quiz.correctCount;
    st.questionsTotal += state.quiz.queue.length;
    st.roundsPlayed++;
    if (pct > st.bestPct) st.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    state.quiz.ratingDelta = lastRatingDelta;
    pushLeaderboard('quiz', { correctTotal: st.correctTotal, questionsTotal: st.questionsTotal, roundsPlayed: st.roundsPlayed, bestPct: st.bestPct });
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}
function playQuizAgain() { startQuizRound(state.quiz.category, state.quiz.difficulty, state.quiz.roundSize); }
function quizBackToSetup() { state.quiz.screen = 'setup'; renderAll(); }

function renderQuizSetup() {
  var t = state.quiz;
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Quiz</h2>' +
    '<div class="field-row">' +
    '<label>Category<select id="quiz-cat"><option value="">All categories</option>' +
    quizCategories().map(function (c) { return '<option value="' + esc(c) + '"' + (t.category === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') +
    '</select></label>' +
    '<label>Difficulty<select id="quiz-diff"><option value="">All difficulties</option>' +
    quizDifficulties().map(function (d) { return '<option value="' + esc(d) + '"' + (t.difficulty === d ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('') +
    '</select></label>' +
    '</div>' +
    '<div class="chip-row">' +
    [5, 10, 20, 30].map(function (n) { return '<button class="chip-toggle' + (t.roundSize === n ? ' active' : '') + '" data-quiz-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    rankedToggleHtml('quiz') +
    '<button class="btn-primary" data-quiz-start>Start Round</button>' +
    '</div>';
}
function renderQuizQuestion() {
  var t = state.quiz, q = currentQuizQuestion();
  if (!q) return '<div class="panel">No questions match those filters. <button class="btn-secondary" data-quiz-setup>Change Filters</button></div>';
  var answered = t.answeredIndex !== null;
  return '<div class="panel">' + modeToolbarHtml('quiz', t.ranked) +
    '<div class="quiz-progress">Question ' + (t.index + 1) + ' of ' + t.queue.length + ' &middot; ' + esc(q.category) + ' &middot; ' + esc(q.difficulty) + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-quiz-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-quiz-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
// Shared by Quiz and CFB Quiz's result screens — both track missed questions
// in the exact same shape (see pickQuizAnswer/pickCfbAnswer), same idea as
// Blitz's inline "Missed:" list and Silhouette's, just with the correct
// answer shown alongside since these are multiple-choice, not free-typed.
function quizMissedReviewHtml(missed) {
  if (!missed.length) return '';
  return '<div class="quiz-missed-review">' +
    '<div class="quiz-missed-review-title">Review missed questions (' + missed.length + ')</div>' +
    missed.map(function (m) {
      return '<div class="quiz-missed-row">' +
        '<div class="quiz-missed-question">' + esc(m.question) + '</div>' +
        '<div class="quiz-missed-answer wrong">' + icon('xMark') + ' Your answer: ' + esc(m.options[m.pickedIndex]) + '</div>' +
        '<div class="quiz-missed-answer correct">' + icon('check') + ' Correct answer: ' + esc(m.options[m.correctIndex]) + '</div>' +
        '</div>';
    }).join('') +
    '</div>';
}
function renderQuizSummary() {
  var t = state.quiz, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel">' +
    '<h2 class="panel-title">Round Complete</h2>' +
    '<div class="summary-score">' + t.correctCount + ' / ' + t.queue.length + ' correct (' + pct + '%)</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-quiz-again>Play Again</button>' +
    '<button class="btn-secondary" data-share="quiz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-quiz-setup>Change Filters</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderQuizScreen() {
  var t = state.quiz;
  if (t.screen === 'question') return renderQuizQuestion();
  if (t.screen === 'summary') return renderQuizSummary();
  return renderQuizSetup();
}

/* ============================== college football quiz ============================== */
function cfbCategories() { return Array.from(new Set(CFB.map(function (q) { return q.category; }))).sort(); }
function cfbDifficulties() { return Array.from(new Set(CFB.map(function (q) { return q.difficulty; }))).sort(); }
function cfbPool(category, difficulty) {
  return CFB.filter(function (q) {
    return (!category || q.category === category) && (!difficulty || q.difficulty === difficulty);
  });
}
function currentCfbQuestion() {
  var id = state.cfbQuiz.queue[state.cfbQuiz.index];
  return CFB.find(function (q) { return q.id === id; });
}
function startCfbQuizRound(category, difficulty, roundSize) {
  var pool = cfbPool(category, difficulty);
  var ids = drawNoRepeat('cfbquiz_' + (category || 'all') + '_' + (difficulty || 'all'), pool.map(function (q) { return q.id; }), roundSize);
  state.cfbQuiz = { screen: 'question', category: category, difficulty: difficulty, roundSize: roundSize, queue: ids, index: 0, correctCount: 0, answeredIndex: null, missed: [], ranked: state.rankedPref.cfbQuiz !== false };
  renderAll();
}
function pickCfbAnswer(i) {
  if (state.cfbQuiz.answeredIndex !== null) return;
  state.cfbQuiz.answeredIndex = i;
  var q = currentCfbQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) { state.cfbQuiz.correctCount++; if (q) removeFromMissedPool('cfb', q.id); }
  else if (q) { state.cfbQuiz.missed.push({ question: q.question, options: q.options, correctIndex: q.correctIndex, pickedIndex: i }); addToMissedPool('cfb', q.id); }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextCfbQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  if (state.cfbQuiz.index + 1 >= state.cfbQuiz.queue.length) {
    state.cfbQuiz.screen = 'summary';
    finishCfbQuizRound();
  } else {
    state.cfbQuiz.index++;
    state.cfbQuiz.answeredIndex = null;
  }
  renderAll();
}
function finishCfbQuizRound() {
  var pct = Math.round(100 * state.cfbQuiz.correctCount / state.cfbQuiz.queue.length);
  if (state.cfbQuiz.ranked !== false) {
    var st = state.stats.cfbQuiz;
    st.correctTotal += state.cfbQuiz.correctCount;
    st.questionsTotal += state.cfbQuiz.queue.length;
    st.roundsPlayed++;
    if (pct > st.bestPct) st.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    state.cfbQuiz.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbQuiz', { correctTotal: st.correctTotal, questionsTotal: st.questionsTotal, roundsPlayed: st.roundsPlayed, bestPct: st.bestPct });
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}
function playCfbAgain() { startCfbQuizRound(state.cfbQuiz.category, state.cfbQuiz.difficulty, state.cfbQuiz.roundSize); }
function cfbBackToSetup() { state.cfbQuiz.screen = 'setup'; renderAll(); }

function renderCfbSetup() {
  var t = state.cfbQuiz;
  return '<div class="panel">' +
    '<h2 class="panel-title">College Football Quiz</h2>' +
    '<div class="field-row">' +
    '<label>Category<select id="cfb-cat"><option value="">All categories</option>' +
    cfbCategories().map(function (c) { return '<option value="' + esc(c) + '"' + (t.category === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') +
    '</select></label>' +
    '<label>Difficulty<select id="cfb-diff"><option value="">All difficulties</option>' +
    cfbDifficulties().map(function (d) { return '<option value="' + esc(d) + '"' + (t.difficulty === d ? ' selected' : '') + '>' + esc(d) + '</option>'; }).join('') +
    '</select></label>' +
    '</div>' +
    '<div class="chip-row">' +
    [5, 10, 20, 30].map(function (n) { return '<button class="chip-toggle' + (t.roundSize === n ? ' active' : '') + '" data-cfb-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    rankedToggleHtml('cfbQuiz') +
    '<button class="btn-primary" data-cfb-start>Start Round</button>' +
    '</div>';
}
function renderCfbQuestion() {
  var t = state.cfbQuiz, q = currentCfbQuestion();
  if (!q) return '<div class="panel">No questions match those filters. <button class="btn-secondary" data-cfb-setup>Change Filters</button></div>';
  var answered = t.answeredIndex !== null;
  return '<div class="panel">' + modeToolbarHtml('cfbQuiz', t.ranked) +
    '<div class="quiz-progress">Question ' + (t.index + 1) + ' of ' + t.queue.length + ' &middot; ' + esc(q.category) + ' &middot; ' + esc(q.difficulty) + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === t.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-cfb-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (t.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-cfb-next>' + (t.index + 1 >= t.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderCfbSummary() {
  var t = state.cfbQuiz, pct = Math.round(100 * t.correctCount / t.queue.length);
  return '<div class="panel">' +
    '<h2 class="panel-title">Round Complete</h2>' +
    '<div class="summary-score">' + t.correctCount + ' / ' + t.queue.length + ' correct (' + pct + '%)</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    quizMissedReviewHtml(t.missed) +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-again>Play Again</button>' +
    '<button class="btn-secondary" data-share="cfbQuiz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-cfb-setup>Change Filters</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbScreen() {
  var t = state.cfbQuiz;
  if (t.screen === 'question') return renderCfbQuestion();
  if (t.screen === 'summary') return renderCfbSummary();
  return renderCfbSetup();
}

/* ============================== study mode ==============================
   Not a real 13th game mode (not in LEAGUE_MODES, no leaderboard entry, no
   rating impact) — a small remedial-practice tool built entirely on top of
   the missed-question pool above: pulls a round from whichever league's
   pool you pick, reusing the exact same quiz-question/quiz-options/quiz-
   feedback markup Quiz/CFB Quiz already use. Answering correctly here (or
   anywhere else) removes a question from the pool — "mastering" it — so
   this naturally shrinks over time instead of being a fixed drill set.
   Deliberately not ranked: this is about fixing weak spots, not chasing a
   score, so it never touches Football Rating or the leaderboard. */
var STUDY_ROUND_SIZE = 15;
function studyQuestionIds(league) {
  var pool = getMissedPool(league);
  var rng = mulberry32(Math.floor(Math.random() * 2147483647));
  return seededShuffle(pool, rng).slice(0, STUDY_ROUND_SIZE);
}
function currentStudyQuestion() {
  var s = state.study;
  var id = s.queue[s.index];
  var source = s.league === 'nfl' ? QUIZ : CFB;
  return source.find(function (q) { return q.id === id; });
}
function startStudy(league) {
  var ids = studyQuestionIds(league);
  if (!ids.length) return;
  state.study = { screen: 'question', league: league, queue: ids, index: 0, correctCount: 0, masteredCount: 0, answeredIndex: null };
  state.screen = 'study';
  renderAll();
}
function pickStudyAnswer(i) {
  var s = state.study;
  if (s.answeredIndex !== null) return;
  s.answeredIndex = i;
  var q = currentStudyQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) {
    s.correctCount++;
    s.masteredCount++;
    removeFromMissedPool(s.league, q.id);
  }
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function nextStudyQuestion() {
  if (typeof stopSfx === 'function') stopSfx();
  var s = state.study;
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; renderAll(); return; }
  s.index++;
  s.answeredIndex = null;
  renderAll();
}
function renderStudySetup() {
  var nflPool = getMissedPool('nfl'), cfbPool = getMissedPool('cfb');
  var nflWeak = weakCategories('nfl').slice(0, 3), cfbWeak = weakCategories('cfb').slice(0, 3);
  if (!nflPool.length && !cfbPool.length) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('brain') + ' Study</h2>' +
      '<p class="mode-desc">Nothing to study yet — play a round of Quiz or CFB Quiz, and any question you miss shows up here so you can drill it later. Get it right anywhere and it’s marked mastered.</p>' +
      '</div>';
  }
  var leagueSectionHtml = function (label, league, pool, weak) {
    if (!pool.length) return '';
    return '<div class="about-section">' +
      '<h3 class="about-heading">' + esc(label) + ' — ' + pool.length + ' to review</h3>' +
      (weak.length ? '<p class="mode-desc">Weakest categories: ' + weak.map(function (w) { return esc(w.category) + ' (' + w.count + ')'; }).join(', ') + '</p>' : '') +
      '<button class="btn-primary" data-study-start="' + league + '">Study ' + Math.min(STUDY_ROUND_SIZE, pool.length) + ' Question' + (Math.min(STUDY_ROUND_SIZE, pool.length) === 1 ? '' : 's') + '</button>' +
      '</div>';
  };
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('brain') + ' Study</h2>' +
    '<p class="mode-desc">Every question you’ve missed in Quiz or CFB Quiz, ready to drill again. Doesn’t affect your Football Rating or the leaderboard — this is just for you.</p>' +
    leagueSectionHtml('NFL', 'nfl', nflPool, nflWeak) +
    leagueSectionHtml('College Football', 'cfb', cfbPool, cfbWeak) +
    '</div>';
}
function renderStudyQuestion() {
  var s = state.study, q = currentStudyQuestion();
  if (!q) return renderStudySetup();
  var answered = s.answeredIndex !== null;
  return '<div class="panel">' + modeToolbarHtml('study') +
    '<div class="quiz-progress">Study &middot; ' + (s.league === 'nfl' ? 'NFL' : 'College Football') + ' &middot; Question ' + (s.index + 1) + ' of ' + s.queue.length + ' &middot; ' + esc(q.category) + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-study-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (s.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct — mastered! It won’t show up here again unless you miss it later.</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect — still in your review pool.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-study-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderStudySummary() {
  var s = state.study;
  var remaining = getMissedPool(s.league).length;
  return '<div class="panel">' +
    '<h2 class="panel-title">Study Session Complete</h2>' +
    '<div class="summary-score">' + s.correctCount + ' / ' + s.queue.length + ' correct</div>' +
    '<div class="summary-note">' + s.masteredCount + ' question' + (s.masteredCount === 1 ? '' : 's') + ' mastered this session &middot; ' + remaining + ' still in your ' + (s.league === 'nfl' ? 'NFL' : 'College Football') + ' review pool.</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-study-start="' + s.league + '">Keep Studying</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderStudyScreen() {
  if (!state.study) return renderStudySetup();
  if (state.study.screen === 'summary') return renderStudySummary();
  if (state.study.screen === 'question') return renderStudyQuestion();
  return renderStudySetup();
}
function studyCardHtml() {
  if (!state.name) return '';
  var total = getMissedPool('nfl').length + getMissedPool('cfb').length;
  if (!total) return '';
  return '<button class="continue-card" data-go="study">' +
    '<span class="continue-card-label">' + total + ' question' + (total === 1 ? '' : 's') + ' to review</span>' +
    '<span class="continue-card-mode">' + icon('brain') + ' Study</span>' +
    '</button>';
}

/* ============================== immaculate grid ============================== */
// A light nudge, not a hard filter: unlike CFB Grid's weighted pick (see
// cfbGridWeightOf), NFL Grid's row selection is a plain shuffle, so the
// simplest way to bias it without restructuring that is a probabilistic
// force-include — most rounds behave exactly as before, but there's a real
// (not guaranteed) chance the favorite team's own criterion gets slotted in
// as one of the 3 rows instead of being left to a 3-in-32 shuffle draw.
var GRID_FAVORITE_TEAM_BIAS = 0.3;
function buildGridAttempt() {
  var teamCritPool = GRID_CRITERIA.team.slice();
  var favId = getFavoriteTeams().nfl;
  var rows;
  if (favId && Math.random() < GRID_FAVORITE_TEAM_BIAS) {
    var favCrit = teamCritPool.find(function (c) { return c.team === favId; });
    rows = favCrit ? [favCrit].concat(shuffle(teamCritPool.filter(function (c) { return c.team !== favId; })).slice(0, 2)) : shuffle(teamCritPool).slice(0, 3);
  } else {
    rows = shuffle(teamCritPool).slice(0, 3);
  }
  var usedIds = rows.map(function (c) { return c.id; });
  var restPool = shuffle(GRID_CRITERIA.all.filter(function (c) { return usedIds.indexOf(c.id) === -1; }));
  var cols = restPool.slice(0, 3);
  var cells = [], validCount = 0;
  for (var r = 0; r < 3; r++) {
    for (var c = 0; c < 3; c++) {
      var rowC = rows[r], colC = cols[c];
      var matches = GRID_PLAYERS.filter(function (p) { return rowC.test(p) && colC.test(p); });
      if (matches.length > 0) validCount++;
      cells.push({ r: r, c: c, matches: matches, guess: null, correct: null, points: 0 });
    }
  }
  return { rows: rows, cols: cols, cells: cells, validCount: validCount };
}
function buildGrid() {
  var best = null;
  for (var i = 0; i < 250; i++) {
    var attempt = buildGridAttempt();
    if (attempt.validCount === 9) return attempt;
    if (!best || attempt.validCount > best.validCount) best = attempt;
  }
  return best;
}
function startGridRound() {
  var g = buildGrid();
  state.grid = { rows: g.rows, cols: g.cols, cells: g.cells, usedPlayers: [], activeIndex: null, input: '', screen: 'board', answeredCount: 0, totalScore: 0, lastError: '', ranked: state.rankedPref.grid !== false };
  state.screen = 'grid';
  renderAll();
}
function selectGridCell(idx) {
  var g = state.grid;
  if (!g || g.screen !== 'board') return;
  if (g.cells[idx].correct !== null) return;
  g.activeIndex = idx;
  g.input = '';
  g.lastError = '';
  renderAll();
}
function submitGridGuess() {
  var g = state.grid;
  if (!g || g.activeIndex === null) return;
  var cell = g.cells[g.activeIndex];
  var norm = normName(g.input);
  if (!norm) return;
  var player = GRID_PLAYERS.find(function (p) { return normName(p.name) === norm; });
  if (player && g.usedPlayers.indexOf(player.name) !== -1) {
    g.lastError = 'Already used ' + player.name + ' on this board — try someone else.';
    renderAll();
    return;
  }
  g.lastError = '';
  var isMatch = !!player && cell.matches.some(function (m) { return m.name === player.name; });
  cell.guess = player ? player.name : g.input;
  cell.correct = isMatch;
  playSound(isMatch ? 'correct' : 'wrong');
  if (isMatch) {
    cell.points = Math.max(10, Math.round(100 / cell.matches.length));
    g.totalScore += cell.points;
    g.usedPlayers.push(player.name);
  } else {
    cell.points = 0;
  }
  g.answeredCount++;
  g.activeIndex = null;
  g.input = '';
  if (g.answeredCount >= 9) {
    g.screen = 'summary';
    finishGridRound();
  }
  renderAll();
}
function finishGridRound() {
  var g = state.grid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  if (g.ranked !== false) {
    var st = state.stats.grid;
    st.gamesPlayed++;
    if (g.totalScore > st.bestScore) st.bestScore = g.totalScore;
    if (correctCells === 9) st.cleanSweeps++;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correctCells / 9);
    g.ratingDelta = lastRatingDelta;
    pushLeaderboard('grid', { bestScore: st.bestScore, gamesPlayed: st.gamesPlayed, cleanSweeps: st.cleanSweeps });
  }
  completeDailyChallengeFrom('grid', correctCells + ' / 9 squares', 100 * correctCells / 9);
  h2hSubmitModeResult('grid', correctCells, 9);
  playSound('complete');
}

function renderGridSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Grid</h2>' +
    '<p class="mode-desc">Every round deals a brand-new 3x3 grid. Type a player who satisfies both the row and the column — one guess per square, and you can\'t reuse a player. Rarer correct answers score more.</p>' +
    rankedToggleHtml('grid') +
    '<button class="btn-primary" data-grid-start>Deal a New Grid</button>' +
    '</div>';
}
// Team/school badge colors are real per-team colors (32 NFL + 48 CFB), so a
// fixed white text color doesn't have reliable WCAG contrast — some (Rams
// gold, Chargers powder blue) are too light for white text to read well.
// Pick whichever of white/near-black actually contrasts better against each
// specific badge color, same relative-luminance formula WCAG itself uses.
function pickBadgeTextColor(hex) {
  hex = String(hex || '').replace('#', '');
  if (hex.length !== 6) return '#fff';
  var r = parseInt(hex.substr(0, 2), 16) / 255;
  var g = parseInt(hex.substr(2, 2), 16) / 255;
  var b = parseInt(hex.substr(4, 2), 16) / 255;
  var lin = function (v) { return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  var L = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  var contrastWithWhite = 1.05 / (L + 0.05);
  var contrastWithBlack = (L + 0.05) / 0.05;
  return contrastWithWhite >= contrastWithBlack ? '#ffffff' : '#0b1220';
}
// Grid scoring (Math.max(10, Math.round(100 / cell.matches.length)) in
// submitGridGuess/submitCfbGridGuess) IS already rarity-based — a square
// with only 3 possible correct players scores way more than one with 80 —
// but that was only ever surfaced as a bare point number, with nothing
// telling you WHY 47 points is impressive and 10 isn't. This turns the same
// pool-size math already being computed into an actual visible tier, live,
// the moment a square is answered — same idea as the real Immaculate
// Grid's rarity %, just tiered instead of a raw percentage since this pool
// size ranges from single digits to hundreds depending on the criteria.
function gridRarityTier(poolSize) {
  if (poolSize <= 3) return { label: 'Immaculate', cls: 'legendary' };
  if (poolSize <= 8) return { label: 'Rare', cls: 'rare' };
  if (poolSize <= 20) return { label: 'Uncommon', cls: 'uncommon' };
  return { label: 'Common', cls: 'common' };
}
function gridRarityTagHtml(poolSize) {
  var t = gridRarityTier(poolSize);
  return '<span class="grid-rarity rarity-' + t.cls + '">' + esc(t.label) + '</span>';
}
// A real 9/9 clean sweep is rare enough (this app tracks it as its own
// "Perfect Grid" badge already — see BADGES/cleanSweeps) that it deserves
// more than the same quiet summary screen as a 5/9. One big banner, one
// bigger confetti burst (double the size of the existing per-square burst
// via .grid-immaculate-confetti), one word.
function gridImmaculateBannerHtml(correctCells) {
  if (correctCells !== 9) return '';
  return '<div class="grid-immaculate-banner"><div class="grid-immaculate-confetti"></div>' + icon('trophy') + ' IMMACULATE!</div>';
}
function criteriaHeaderHtml(c) {
  if (c.type === 'team') {
    var color = (window.GRID_TEAM_COLORS && window.GRID_TEAM_COLORS[c.team]) || '#444';
    return '<div class="team-badge" style="background:' + color + ';color:' + pickBadgeTextColor(color) + '">' + esc(c.team) + '</div><div>' + esc(c.label) + '</div>';
  }
  if (c.type === 'school') {
    var schoolColor = (window.CFB_GRID_SCHOOL_COLORS && window.CFB_GRID_SCHOOL_COLORS[c.school]) || '#444';
    var schoolCode = (window.CFB_GRID_SCHOOL_CODES && window.CFB_GRID_SCHOOL_CODES[c.school]) || c.school;
    return '<div class="team-badge" style="background:' + schoolColor + ';color:' + pickBadgeTextColor(schoolColor) + '">' + esc(schoolCode) + '</div><div>' + esc(c.label) + '</div>';
  }
  return '<div>' + esc(c.label) + '</div>';
}
function renderGridBoard() {
  var g = state.grid;
  var html = '<div class="panel">' + modeToolbarHtml('grid', g.ranked) +
    '<h2 class="panel-title">NFL Grid &middot; ' + g.answeredCount + ' / 9 answered &middot; ' + g.totalScore + ' pts</h2>' +
    '<div class="grid-table">' +
    '<div class="grid-cell grid-corner"></div>';
  g.cols.forEach(function (c) { html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(c) + '</div>'; });
  for (var r = 0; r < 3; r++) {
    html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(g.rows[r]) + '</div>';
    for (var c = 0; c < 3; c++) {
      var idx = r * 3 + c, cell = g.cells[idx];
      var cls = 'grid-cell grid-square';
      var content = '';
      if (cell.correct === true) { cls += ' correct'; content = '<div class="grid-answer">' + esc(cell.guess) + '</div><div class="grid-points">+' + cell.points + '</div>' + gridRarityTagHtml(cell.matches.length); }
      else if (cell.correct === false) { cls += ' wrong'; content = '<div class="grid-answer">' + esc(cell.guess || '—') + '</div><div class="grid-points">' + icon('close') + '</div>'; }
      else if (g.activeIndex === idx) { cls += ' active'; content = '<div class="grid-hint">Type below ↓</div>'; }
      else { content = '<div class="grid-hint">Tap to answer</div>'; }
      html += '<button class="' + cls + '" data-grid-cell="' + idx + '" ' + (cell.correct !== null ? 'disabled' : '') + '>' + content + '</button>';
    }
  }
  html += '</div>';
  if (g.activeIndex !== null) {
    html += '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="grid-input" autocomplete="off" placeholder="Type a player name…" value="' + esc(g.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="grid-input-typeahead" />' +
      '<div id="grid-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-grid-submit>Submit</button>' +
      (g.lastError ? '<div class="grid-error" role="alert">' + esc(g.lastError) + '</div>' : '') +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderGridSummary() {
  var g = state.grid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  var html = '<div class="panel">' +
    '<h2 class="panel-title">Grid Complete</h2>' +
    gridImmaculateBannerHtml(correctCells) +
    '<div class="summary-score">' + correctCells + ' / 9 correct &middot; ' + g.totalScore + ' pts</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="grid-recap">';
  g.cells.forEach(function (cell) {
    var rowLabel = g.rows[cell.r].label, colLabel = g.cols[cell.c].label;
    var pool = cell.matches.map(function (m) { return m.name; });
    var poolText = pool.slice(0, 6).join(', ') + (pool.length > 6 ? ', +' + (pool.length - 6) + ' more' : '');
    html += '<div class="grid-recap-row ' + (cell.correct ? 'correct' : 'wrong') + '">' +
      '<b>' + esc(rowLabel) + ' × ' + esc(colLabel) + ':</b> your answer — ' + esc(cell.guess || '(none)') +
      '<div class="grid-recap-pool">' + gridRarityTagHtml(pool.length) + ' Valid answers (' + pool.length + '): ' + esc(poolText) + '</div></div>';
  });
  html += '</div><div class="btn-row">' +
    '<button class="btn-primary" data-grid-again>New Grid</button>' +
    '<button class="btn-secondary" data-share="grid">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
  return html;
}
function renderGridScreen() {
  if (!state.grid) return renderGridSetup();
  if (state.grid.screen === 'summary') return renderGridSummary();
  return renderGridBoard();
}

/* ============================== college football immaculate grid ============================== */
function weightedPickWithoutReplacement(items, weightFn, n) {
  var pool = items.slice();
  var picked = [];
  for (var k = 0; k < n && pool.length; k++) {
    var total = 0, i;
    for (i = 0; i < pool.length; i++) total += weightFn(pool[i]);
    var r = Math.random() * total, acc = 0, idx = pool.length - 1;
    for (i = 0; i < pool.length; i++) {
      acc += weightFn(pool[i]);
      if (r <= acc) { idx = i; break; }
    }
    picked.push(pool[idx]);
    pool.splice(idx, 1);
  }
  return picked;
}
// Weight every criterion — rows and columns alike — by how many players it actually
// matches, rather than a crude "this type is usually sparse" guess. Schools/awards/etc.
// with few matching players become proportionally less likely to get picked at all,
// so thin criteria (a newly-added school with 2 players, a rare award) still show up
// for variety but don't dominate and tank how often a fully solvable grid gets dealt.
// Memoized since CFB_GRID_PLAYERS/CFB_GRID_CRITERIA never change at runtime.
var cfbGridCriteriaWeight = null;
function cfbGridWeightOf(c) {
  if (!cfbGridCriteriaWeight) {
    cfbGridCriteriaWeight = {};
    CFB_GRID_CRITERIA.all.forEach(function (crit) {
      cfbGridCriteriaWeight[crit.id] = CFB_GRID_PLAYERS.filter(crit.test).length;
    });
  }
  var w = Math.min(1, (cfbGridCriteriaWeight[c.id] || 0) / 10) + 0.05;
  // A light nudge, not a hard filter (per the favorite-team feature's own
  // design goal): multiplies rather than replaces the existing depth-based
  // weight, so a favorite school with very few valid grid matches still
  // can't get force-picked into a mostly-broken grid — it's just noticeably
  // more likely to show up than any other equally-deep school would be.
  var favSchool = getFavoriteTeams().cfb;
  if (favSchool && c.type === 'school' && c.school === favSchool) w *= 6;
  return w;
}
function buildCfbGridAttempt() {
  var rows = weightedPickWithoutReplacement(CFB_GRID_CRITERIA.team, cfbGridWeightOf, 3);
  var usedIds = rows.map(function (c) { return c.id; });
  var restPool = CFB_GRID_CRITERIA.all.filter(function (c) { return usedIds.indexOf(c.id) === -1; });
  var cols = weightedPickWithoutReplacement(restPool, cfbGridWeightOf, 3);
  var cells = [], validCount = 0;
  for (var r = 0; r < 3; r++) {
    for (var c = 0; c < 3; c++) {
      var rowC = rows[r], colC = cols[c];
      var matches = CFB_GRID_PLAYERS.filter(function (p) { return rowC.test(p) && colC.test(p); });
      if (matches.length > 0) validCount++;
      cells.push({ r: r, c: c, matches: matches, guess: null, correct: null, points: 0 });
    }
  }
  return { rows: rows, cols: cols, cells: cells, validCount: validCount };
}
function buildCfbGrid() {
  var best = null;
  for (var i = 0; i < 1200; i++) {
    var attempt = buildCfbGridAttempt();
    if (attempt.validCount === 9) return attempt;
    if (!best || attempt.validCount > best.validCount) best = attempt;
  }
  return best;
}
function startCfbGridRound() {
  var g = buildCfbGrid();
  state.cfbGrid = { rows: g.rows, cols: g.cols, cells: g.cells, usedPlayers: [], activeIndex: null, input: '', screen: 'board', answeredCount: 0, totalScore: 0, lastError: '', ranked: state.rankedPref.cfbGrid !== false };
  state.screen = 'cfbGrid';
  renderAll();
}
function selectCfbGridCell(idx) {
  var g = state.cfbGrid;
  if (!g || g.screen !== 'board') return;
  if (g.cells[idx].correct !== null) return;
  g.activeIndex = idx;
  g.input = '';
  g.lastError = '';
  renderAll();
}
function submitCfbGridGuess() {
  var g = state.cfbGrid;
  if (!g || g.activeIndex === null) return;
  var cell = g.cells[g.activeIndex];
  var norm = normName(g.input);
  if (!norm) return;
  var player = CFB_GRID_PLAYERS.find(function (p) { return normName(p.name) === norm; });
  if (player && g.usedPlayers.indexOf(player.name) !== -1) {
    g.lastError = 'Already used ' + player.name + ' on this board — try someone else.';
    renderAll();
    return;
  }
  g.lastError = '';
  var isMatch = !!player && cell.matches.some(function (m) { return m.name === player.name; });
  cell.guess = player ? player.name : g.input;
  cell.correct = isMatch;
  playSound(isMatch ? 'correct' : 'wrong');
  if (isMatch) {
    cell.points = Math.max(10, Math.round(100 / cell.matches.length));
    g.totalScore += cell.points;
    g.usedPlayers.push(player.name);
  } else {
    cell.points = 0;
  }
  g.answeredCount++;
  g.activeIndex = null;
  g.input = '';
  if (g.answeredCount >= 9) {
    g.screen = 'summary';
    finishCfbGridRound();
  }
  renderAll();
}
function finishCfbGridRound() {
  var g = state.cfbGrid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  if (g.ranked !== false) {
    var st = state.stats.cfbGrid;
    st.gamesPlayed++;
    if (g.totalScore > st.bestScore) st.bestScore = g.totalScore;
    if (correctCells === 9) st.cleanSweeps++;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correctCells / 9);
    g.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbGrid', { bestScore: st.bestScore, gamesPlayed: st.gamesPlayed, cleanSweeps: st.cleanSweeps });
    completeDailyChallengeFrom('cfbGrid', correctCells + ' / 9 squares', 100 * correctCells / 9);
  }
  h2hSubmitModeResult('cfbGrid', correctCells, 9);
  playSound('complete');
}

function renderCfbGridSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">College Football Immaculate Grid</h2>' +
    '<p class="mode-desc">Every round deals a brand-new 3x3 grid of schools and All-America/Heisman criteria (1889-2025). Type a player who satisfies both the row and the column — one guess per square, and you can\'t reuse a player. Rarer correct answers score more.</p>' +
    rankedToggleHtml('cfbGrid') +
    '<button class="btn-primary" data-cfb-grid-start>Deal a New Grid</button>' +
    '</div>';
}
function renderCfbGridBoard() {
  var g = state.cfbGrid;
  var html = '<div class="panel">' + modeToolbarHtml('cfbGrid', g.ranked) +
    '<h2 class="panel-title">CFB Immaculate Grid &middot; ' + g.answeredCount + ' / 9 answered &middot; ' + g.totalScore + ' pts</h2>' +
    '<div class="grid-table">' +
    '<div class="grid-cell grid-corner"></div>';
  g.cols.forEach(function (c) { html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(c) + '</div>'; });
  for (var r = 0; r < 3; r++) {
    html += '<div class="grid-cell grid-header">' + criteriaHeaderHtml(g.rows[r]) + '</div>';
    for (var c = 0; c < 3; c++) {
      var idx = r * 3 + c, cell = g.cells[idx];
      var cls = 'grid-cell grid-square';
      var content = '';
      if (cell.correct === true) { cls += ' correct'; content = '<div class="grid-answer">' + esc(cell.guess) + '</div><div class="grid-points">+' + cell.points + '</div>' + gridRarityTagHtml(cell.matches.length); }
      else if (cell.correct === false) { cls += ' wrong'; content = '<div class="grid-answer">' + esc(cell.guess || '—') + '</div><div class="grid-points">' + icon('close') + '</div>'; }
      else if (g.activeIndex === idx) { cls += ' active'; content = '<div class="grid-hint">Type below ↓</div>'; }
      else { content = '<div class="grid-hint">Tap to answer</div>'; }
      html += '<button class="' + cls + '" data-cfb-grid-cell="' + idx + '" ' + (cell.correct !== null ? 'disabled' : '') + '>' + content + '</button>';
    }
  }
  html += '</div>';
  if (g.activeIndex !== null) {
    html += '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="cfb-grid-input" autocomplete="off" placeholder="Type a player name…" value="' + esc(g.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="cfb-grid-input-typeahead" />' +
      '<div id="cfb-grid-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-cfb-grid-submit>Submit</button>' +
      (g.lastError ? '<div class="grid-error" role="alert">' + esc(g.lastError) + '</div>' : '') +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderCfbGridSummary() {
  var g = state.cfbGrid;
  var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
  var html = '<div class="panel">' +
    '<h2 class="panel-title">Grid Complete</h2>' +
    gridImmaculateBannerHtml(correctCells) +
    '<div class="summary-score">' + correctCells + ' / 9 correct &middot; ' + g.totalScore + ' pts</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="grid-recap">';
  g.cells.forEach(function (cell) {
    var rowLabel = g.rows[cell.r].label, colLabel = g.cols[cell.c].label;
    var pool = cell.matches.map(function (m) { return m.name; });
    var poolText = pool.slice(0, 6).join(', ') + (pool.length > 6 ? ', +' + (pool.length - 6) + ' more' : '');
    html += '<div class="grid-recap-row ' + (cell.correct ? 'correct' : 'wrong') + '">' +
      '<b>' + esc(rowLabel) + ' × ' + esc(colLabel) + ':</b> your answer — ' + esc(cell.guess || '(none)') +
      '<div class="grid-recap-pool">' + gridRarityTagHtml(pool.length) + ' Valid answers (' + pool.length + '): ' + esc(poolText) + '</div></div>';
  });
  html += '</div><div class="btn-row">' +
    '<button class="btn-primary" data-cfb-grid-again>New Grid</button>' +
    '<button class="btn-secondary" data-share="cfbGrid">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
  return html;
}
function renderCfbGridScreen() {
  if (!state.cfbGrid) return renderCfbGridSetup();
  if (state.cfbGrid.screen === 'summary') return renderCfbGridSummary();
  return renderCfbGridBoard();
}

/* ============================== blitz ============================== */
function normalizeBlitzText(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim(); }
function startBlitz(listId, timerLen) {
  var list = BLITZ_LISTS.find(function (l) { return l.id === listId; });
  state.blitz = { listId: listId, list: list, timerLen: timerLen, screen: 'playing', endsAt: Date.now() + timerLen * 1000, timeLeft: timerLen, matched: [], input: '', lastFeedback: '', ranked: state.rankedPref.blitz !== false };
  state.screen = 'blitz';
  stopTimers();
  blitzTimer = setInterval(blitzTick, 250);
  renderAll();
}
function blitzTick() {
  if (!state.blitz || state.blitz.screen !== 'playing') return;
  var remain = (state.blitz.endsAt - Date.now()) / 1000;
  if (remain <= 0) { state.blitz.timeLeft = 0; endBlitz(); return; }
  state.blitz.timeLeft = remain;
  // Patch the timer text directly instead of a full renderAll() — a full
  // DOM rebuild 4x/sec was intermittently eating clicks/keystrokes on the
  // input and Add button.
  var timerEl = document.getElementById('blitz-timer-display');
  if (timerEl) timerEl.textContent = fmtTime(remain);
}
function submitBlitzGuess() {
  var b = state.blitz;
  if (!b || b.screen !== 'playing') return;
  var norm = normalizeBlitzText(b.input);
  if (!norm) return;
  var found = null;
  for (var i = 0; i < b.list.answers.length; i++) {
    var a = b.list.answers[i];
    if (b.matched.indexOf(a.answer) !== -1) continue;
    var candidates = [a.answer].concat(a.aliases || []);
    for (var j = 0; j < candidates.length; j++) {
      if (normalizeBlitzText(candidates[j]) === norm) { found = a; break; }
    }
    if (found) break;
  }
  if (found) {
    b.matched.push(found.answer);
    b.lastFeedback = 'correct';
    playSound('correct');
    if (b.matched.length >= b.list.answers.length) { b.input = ''; endBlitz(); return; }
  } else {
    b.lastFeedback = 'miss';
    playSound('wrong');
  }
  b.input = '';
  renderAll();
}
function endBlitz() {
  if (blitzTimer) { clearInterval(blitzTimer); blitzTimer = null; }
  state.blitz.screen = 'results';
  finishBlitzRound();
  renderAll();
}
function finishBlitzRound() {
  var b = state.blitz;
  var pct = 100 * b.matched.length / b.list.answers.length;
  if (b.ranked !== false) {
    var st = state.stats.blitz;
    st.attempts++;
    if (b.matched.length > st.bestMatched) st.bestMatched = b.matched.length;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    b.ratingDelta = lastRatingDelta;
    pushLeaderboard('blitz', { bestMatched: st.bestMatched, attempts: st.attempts });
    completeDailyChallengeFrom('blitz', b.matched.length + ' / ' + b.list.answers.length + ' found', pct);
    h2hSubmitModeResult('blitz', b.matched.length, b.list.answers.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderBlitzSetup() {
  var lists = BLITZ_LISTS;
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Blitz</h2>' +
    '<p class="mode-desc">Type every correct answer you can before time runs out. Nicknames and abbreviations count.</p>' +
    '<div class="blitz-list-picker">' +
    lists.map(function (l) {
      return '<button class="blitz-list-card" data-blitz-list="' + esc(l.id) + '"><b>' + esc(l.title) + '</b><div class="mode-desc">' + esc(l.prompt) + ' (' + l.answers.length + ' answers)</div></button>';
    }).join('') +
    '</div></div>';
}
function renderBlitzTimerPicker(listId) {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + esc(BLITZ_LISTS.find(function (l) { return l.id === listId; }).title) + '</h2>' +
    rankedToggleHtml('blitz') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-blitz-start="' + listId + '" data-blitz-timer="' + n + '">' + n + 's</button>'; }).join('') +
    '</div>' +
    '<button class="btn-secondary" data-blitz-setup>Back</button>' +
    '</div>';
}
function renderBlitzPlaying() {
  var b = state.blitz, total = b.list.answers.length;
  return '<div class="panel">' + modeToolbarHtml('blitz', b.ranked) +
    '<div class="blitz-header"><div class="blitz-title">' + esc(b.list.title) + '</div><div class="blitz-timer" id="blitz-timer-display">' + fmtTime(b.timeLeft) + '</div></div>' +
    '<div class="blitz-progress">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="blitz-input-row">' +
    '<input id="blitz-input" autocomplete="off" placeholder="Type an answer and hit Enter…" value="' + esc(b.input) + '" autofocus />' +
    '<button class="btn-primary" data-blitz-submit>Add</button>' +
    '</div>' +
    (b.lastFeedback === 'miss' ? '<div class="blitz-feedback wrong" aria-live="polite">Not a match — try again.</div>' : '') +
    '<div class="blitz-matched">' + b.matched.map(function (m) { return '<span class="blitz-chip">' + esc(m) + '</span>'; }).join('') + '</div>' +
    '</div>';
}
function renderBlitzResults() {
  var b = state.blitz, total = b.list.answers.length;
  var missed = b.list.answers.filter(function (a) { return b.matched.indexOf(a.answer) === -1; });
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Blitz Complete — ' + esc(b.list.title) + '</h2>' +
    '<div class="summary-score">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (a) { return esc(a.answer); }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you got every answer!</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-blitz-list="' + esc(b.listId) + '">Try Another List</button>' +
    '<button class="btn-secondary" data-share="blitz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderBlitzScreen() {
  var b = state.blitz;
  if (!b) return renderBlitzSetup();
  if (b.screen === 'pickTimer') return renderBlitzTimerPicker(b.listId);
  if (b.screen === 'playing') return renderBlitzPlaying();
  if (b.screen === 'results') return renderBlitzResults();
  return renderBlitzSetup();
}

/* ============================== college football blitz ============================== */
function startCfbBlitz(listId, timerLen) {
  var list = CFB_BLITZ_LISTS.find(function (l) { return l.id === listId; });
  state.cfbBlitz = { listId: listId, list: list, timerLen: timerLen, screen: 'playing', endsAt: Date.now() + timerLen * 1000, timeLeft: timerLen, matched: [], input: '', lastFeedback: '', ranked: state.rankedPref.cfbBlitz !== false };
  state.screen = 'cfbBlitz';
  stopTimers();
  cfbBlitzTimer = setInterval(cfbBlitzTick, 250);
  renderAll();
}
function cfbBlitzTick() {
  if (!state.cfbBlitz || state.cfbBlitz.screen !== 'playing') return;
  var remain = (state.cfbBlitz.endsAt - Date.now()) / 1000;
  if (remain <= 0) { state.cfbBlitz.timeLeft = 0; endCfbBlitz(); return; }
  state.cfbBlitz.timeLeft = remain;
  var timerEl = document.getElementById('cfb-blitz-timer-display');
  if (timerEl) timerEl.textContent = fmtTime(remain);
}
function submitCfbBlitzGuess() {
  var b = state.cfbBlitz;
  if (!b || b.screen !== 'playing') return;
  var norm = normalizeBlitzText(b.input);
  if (!norm) return;
  var found = null;
  for (var i = 0; i < b.list.answers.length; i++) {
    var a = b.list.answers[i];
    if (b.matched.indexOf(a.answer) !== -1) continue;
    var candidates = [a.answer].concat(a.aliases || []);
    for (var j = 0; j < candidates.length; j++) {
      if (normalizeBlitzText(candidates[j]) === norm) { found = a; break; }
    }
    if (found) break;
  }
  if (found) {
    b.matched.push(found.answer);
    b.lastFeedback = 'correct';
    playSound('correct');
    if (b.matched.length >= b.list.answers.length) { b.input = ''; endCfbBlitz(); return; }
  } else {
    b.lastFeedback = 'miss';
    playSound('wrong');
  }
  b.input = '';
  renderAll();
}
function endCfbBlitz() {
  if (cfbBlitzTimer) { clearInterval(cfbBlitzTimer); cfbBlitzTimer = null; }
  state.cfbBlitz.screen = 'results';
  finishCfbBlitzRound();
  renderAll();
}
function finishCfbBlitzRound() {
  var b = state.cfbBlitz;
  var pct = 100 * b.matched.length / b.list.answers.length;
  if (b.ranked !== false) {
    var st = state.stats.cfbBlitz;
    st.attempts++;
    if (b.matched.length > st.bestMatched) st.bestMatched = b.matched.length;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    b.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbBlitz', { bestMatched: st.bestMatched, attempts: st.attempts });
    completeDailyChallengeFrom('cfbBlitz', b.matched.length + ' / ' + b.list.answers.length + ' found', pct);
    h2hSubmitModeResult('cfbBlitz', b.matched.length, b.list.answers.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderCfbBlitzSetup() {
  var lists = CFB_BLITZ_LISTS;
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB Blitz</h2>' +
    '<p class="mode-desc">Type every correct answer you can before time runs out. Nicknames and abbreviations count.</p>' +
    '<div class="blitz-list-picker">' +
    lists.map(function (l) {
      return '<button class="blitz-list-card" data-cfb-blitz-list="' + esc(l.id) + '"><b>' + esc(l.title) + '</b><div class="mode-desc">' + esc(l.prompt) + ' (' + l.answers.length + ' answers)</div></button>';
    }).join('') +
    '</div></div>';
}
function renderCfbBlitzTimerPicker(listId) {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + esc(CFB_BLITZ_LISTS.find(function (l) { return l.id === listId; }).title) + '</h2>' +
    rankedToggleHtml('cfbBlitz') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-cfb-blitz-start="' + listId + '" data-cfb-blitz-timer="' + n + '">' + n + 's</button>'; }).join('') +
    '</div>' +
    '<button class="btn-secondary" data-cfb-blitz-setup>Back</button>' +
    '</div>';
}
function renderCfbBlitzPlaying() {
  var b = state.cfbBlitz, total = b.list.answers.length;
  return '<div class="panel">' + modeToolbarHtml('cfbBlitz', b.ranked) +
    '<div class="blitz-header"><div class="blitz-title">' + esc(b.list.title) + '</div><div class="blitz-timer" id="cfb-blitz-timer-display">' + fmtTime(b.timeLeft) + '</div></div>' +
    '<div class="blitz-progress">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="blitz-input-row">' +
    '<input id="cfb-blitz-input" autocomplete="off" placeholder="Type an answer and hit Enter…" value="' + esc(b.input) + '" autofocus />' +
    '<button class="btn-primary" data-cfb-blitz-submit>Add</button>' +
    '</div>' +
    (b.lastFeedback === 'miss' ? '<div class="blitz-feedback wrong" aria-live="polite">Not a match — try again.</div>' : '') +
    '<div class="blitz-matched">' + b.matched.map(function (m) { return '<span class="blitz-chip">' + esc(m) + '</span>'; }).join('') + '</div>' +
    '</div>';
}
function renderCfbBlitzResults() {
  var b = state.cfbBlitz, total = b.list.answers.length;
  var missed = b.list.answers.filter(function (a) { return b.matched.indexOf(a.answer) === -1; });
  return '<div class="panel">' +
    '<h2 class="panel-title">Blitz Complete — ' + esc(b.list.title) + '</h2>' +
    '<div class="summary-score">' + b.matched.length + ' / ' + total + ' found</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (a) { return esc(a.answer); }).join(', ') + '</div>' : '<div class="blitz-missed">Clean sweep — you got every answer!</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-blitz-list="' + esc(b.listId) + '">Try Another List</button>' +
    '<button class="btn-secondary" data-share="cfbBlitz">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbBlitzScreen() {
  var b = state.cfbBlitz;
  if (!b) return renderCfbBlitzSetup();
  if (b.screen === 'pickTimer') return renderCfbBlitzTimerPicker(b.listId);
  if (b.screen === 'playing') return renderCfbBlitzPlaying();
  if (b.screen === 'results') return renderCfbBlitzResults();
  return renderCfbBlitzSetup();
}

/* ============================== speed round ============================== */
function speedQueue() { var ids = QUIZ.map(function (q) { return q.id; }); return drawNoRepeat('speed', ids, ids.length); }
function currentSpeedQuestion() {
  var s = state.speed;
  var id = s.queue[s.qIndex % s.queue.length];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startSpeedRound(sessionLen) {
  state.speed = {
    sessionLen: sessionLen, qLen: 6, screen: 'playing',
    sessionEndsAt: Date.now() + sessionLen * 1000, qEndsAt: Date.now() + 6 * 1000,
    queue: speedQueue(), qIndex: 0, answeredIndex: null,
    score: 0, streak: 0, bestStreak: 0, correctCount: 0, totalCount: 0,
    sessionTimeLeft: sessionLen, qTimeLeft: 6, ranked: state.rankedPref.speed !== false
  };
  state.screen = 'speed';
  stopTimers();
  speedTimer = setInterval(speedTick, 200);
  renderAll();
}
function speedTick() {
  var s = state.speed;
  if (!s || s.screen !== 'playing') return;
  var now = Date.now();
  s.sessionTimeLeft = Math.max(0, (s.sessionEndsAt - now) / 1000);
  if (s.sessionTimeLeft <= 0) { endSpeedRound(); return; }
  s.qTimeLeft = Math.max(0, (s.qEndsAt - now) / 1000);
  if (s.answeredIndex === null && s.qTimeLeft <= 0) { registerSpeedAnswer(-1); return; }
  // Patch the timer/bar directly instead of a full renderAll() — a full DOM
  // rebuild 5x/sec was intermittently eating clicks on the answer buttons.
  var sessEl = document.getElementById('speed-session-timer');
  if (sessEl) sessEl.textContent = fmtTime(s.sessionTimeLeft);
  var barEl = document.getElementById('speed-qbar-fill');
  if (barEl) barEl.style.width = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen)) + '%';
}
function registerSpeedAnswer(optionIndex) {
  var s = state.speed;
  if (!s || s.screen !== 'playing' || s.answeredIndex !== null) return;
  s.answeredIndex = optionIndex;
  var q = currentSpeedQuestion();
  var correct = q && optionIndex === q.correctIndex;
  s.totalCount++;
  if (correct) {
    s.correctCount++;
    s.streak++;
    if (s.streak > s.bestStreak) s.bestStreak = s.streak;
    var mult = 1 + Math.floor(s.streak / 3) * 0.5;
    s.score += Math.round(20 * mult);
  } else {
    s.streak = 0;
  }
  playSound(correct ? 'correct' : 'wrong');
  renderAll();
  setTimeout(advanceSpeedQuestion, 550);
}
function advanceSpeedQuestion() {
  var s = state.speed;
  if (!s || s.screen !== 'playing') return;
  if (typeof stopSfx === 'function') stopSfx();
  if (Date.now() >= s.sessionEndsAt) return;
  s.qIndex++;
  if (s.qIndex >= s.queue.length) { s.queue = speedQueue(); s.qIndex = 0; }
  s.answeredIndex = null;
  s.qEndsAt = Date.now() + s.qLen * 1000;
  renderAll();
}
function endSpeedRound() {
  if (speedTimer) { clearInterval(speedTimer); speedTimer = null; }
  state.speed.screen = 'summary';
  finishSpeedRound();
  renderAll();
}
function finishSpeedRound() {
  var s = state.speed;
  var pct = s.totalCount > 0 ? 100 * s.correctCount / s.totalCount : 100;
  if (s.ranked !== false) {
    var st = state.stats.speed;
    st.sessionsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    if (s.bestStreak > st.bestStreak) st.bestStreak = s.bestStreak;
    lsSet('nflTriviaStats', state.stats);
    if (s.totalCount > 0) { updateRatingDrift(pct); s.ratingDelta = lastRatingDelta; }
    pushLeaderboard('speed', { bestScore: st.bestScore, bestStreak: st.bestStreak, sessionsPlayed: st.sessionsPlayed });
  }
  h2hSubmitModeResult('speed', s.correctCount, s.totalCount, s.score);
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderSpeedSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Speed</h2>' +
    '<p class="mode-desc">Rapid-fire multiple choice — about 6 seconds per question, non-stop until time runs out. Chain correct answers for a streak multiplier.</p>' +
    rankedToggleHtml('speed') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-speed-start="' + n + '">' + n + 's session</button>'; }).join('') +
    '</div></div>';
}
function renderSpeedPlaying() {
  var s = state.speed, q = currentSpeedQuestion();
  var answered = s.answeredIndex !== null;
  var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
  return '<div class="panel">' + modeToolbarHtml('speed', s.ranked) +
    '<div class="speed-header"><div>Session: <span id="speed-session-timer">' + fmtTime(s.sessionTimeLeft) + '</span></div><div>Score: ' + s.score + '</div><div>Streak: ' + s.streak + '</div></div>' +
    '<div class="speed-qbar"><div class="speed-qbar-fill" id="speed-qbar-fill" style="width:' + qPct + '%"></div></div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-speed-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderSpeedSummary() {
  var s = state.speed;
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Speed Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + s.correctCount + ' / ' + s.totalCount + ' correct &middot; best streak ' + s.bestStreak + '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-speed-start="' + s.sessionLen + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="speed">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderSpeedScreen() {
  if (!state.speed) return renderSpeedSetup();
  if (state.speed.screen === 'summary') return renderSpeedSummary();
  if (state.speed.screen === 'playing') return renderSpeedPlaying();
  return renderSpeedSetup();
}

/* ============================== higher or lower ==============================
   Real career honors already tracked per-player in GRID_PLAYERS — same
   fields the Learn tab's "Pro Bowl & All-Pro Selections" section reads, plus
   the 4 boolean "signature moment" flags every entry already carries.
   Classic "guess if the next one is higher or lower" format, endless streak
   until a miss — built specifically because this is one of the most viral,
   shareable trivia formats around, and this app already has real per-player
   numbers that support it honestly.

   Four selectable stat categories (HIGHER_LOWER_STATS below) rather than one
   fixed comparison — every one is either a real counted stat already on the
   data, or (Signature Moments) a plainly-labeled sum of four specific real
   boolean facts (MVP / Super Bowl win / Super Bowl MVP / Hall of Fame), not
   an invented or hidden formula. Picked once at the setup screen and fixed
   for the whole streak-run, same reasoning as not switching Quiz categories
   mid-round: comparing against a moving target isn't "higher or lower"
   anymore, it's a different game each time.

   CFB deliberately does NOT get a version of this: CFB_GRID_PLAYERS has no
   comparable numeric stat with real spread (years.length, the closest
   thing, tops out around 2-3 even for the best multi-time All-Americans —
   almost every comparison would be a coin-flip tie). This only exists
   where a real stat actually supports it, not invented to make the mode
   symmetric across leagues. */
var HIGHER_LOWER_STATS = [
  { id: 'combined', label: 'Career Pro Bowl + All-Pro selections', scoreFn: function (p) { return (p.proBowls || 0) + (p.allPro || 0); } },
  { id: 'proBowls', label: 'Career Pro Bowl selections', scoreFn: function (p) { return p.proBowls || 0; } },
  { id: 'allPro', label: 'Career All-Pro selections', scoreFn: function (p) { return p.allPro || 0; } },
  { id: 'moments', label: 'Signature career moments (MVP + Super Bowl win + Super Bowl MVP + Hall of Fame)', scoreFn: function (p) { return (p.mvp ? 1 : 0) + (p.sbChamp ? 1 : 0) + (p.sbMVP ? 1 : 0) + (p.hof ? 1 : 0); } }
];
function higherLowerStatConfig(statId) {
  return HIGHER_LOWER_STATS.find(function (s) { return s.id === statId; }) || HIGHER_LOWER_STATS[0];
}
function higherLowerPool(statId) {
  var cfg = higherLowerStatConfig(statId);
  return GRID_PLAYERS.filter(function (p) { return cfg.scoreFn(p) > 0; });
}
function higherLowerScore(p, statId) { return higherLowerStatConfig(statId).scoreFn(p); }
function higherLowerDrawPlayer(statId, usedNames) {
  var pool = higherLowerPool(statId).filter(function (p) { return usedNames.indexOf(p.name) === -1; });
  // Pool exhausted (334-651 players depending on the stat — a genuinely
  // absurd streak to reach any of those) — allow repeats rather than
  // dead-end an otherwise-still-going run.
  if (!pool.length) pool = higherLowerPool(statId);
  return pool[Math.floor(Math.random() * pool.length)];
}
// Remembered for the session (not persisted across visits) so re-starting
// after a loss defaults back to whatever stat you were just playing, same
// convenience as Quiz remembering its last round size.
var higherLowerStatPref = 'combined';
function setHigherLowerStat(statId) { higherLowerStatPref = statId; renderAll(); }
function startHigherLower() {
  var statId = higherLowerStatPref;
  var first = higherLowerDrawPlayer(statId, []);
  var second = higherLowerDrawPlayer(statId, [first.name]);
  state.higherLower = {
    screen: 'playing', stat: statId, current: first, next: second, streak: 0, revealedScore: null, lastCorrect: null,
    usedNames: [first.name, second.name], ranked: state.rankedPref.higherLower !== false
  };
  state.screen = 'higherLower';
  renderAll();
}
function submitHigherLowerGuess(direction) {
  var s = state.higherLower;
  if (!s || s.screen !== 'playing') return;
  var curScore = higherLowerScore(s.current, s.stat), nextScore = higherLowerScore(s.next, s.stat);
  // A tie always counts as correct — standard house rule for this format,
  // and the honest one: nothing in "higher or lower" was violated by a
  // dead-even comparison, so it shouldn't end the run either direction.
  var correct = curScore === nextScore || (direction === 'higher' ? nextScore > curScore : nextScore < curScore);
  s.lastCorrect = correct;
  s.revealedScore = nextScore;
  playSound(correct ? 'correct' : 'wrong');
  if (correct) { s.streak++; s.screen = 'reveal'; }
  else { s.screen = 'over'; finishHigherLower(); }
  renderAll();
}
function higherLowerContinue() {
  var s = state.higherLower;
  if (!s || s.screen !== 'reveal') return;
  s.current = s.next;
  s.next = higherLowerDrawPlayer(s.stat, s.usedNames);
  s.usedNames.push(s.next.name);
  s.revealedScore = null;
  s.lastCorrect = null;
  s.screen = 'playing';
  renderAll();
}
function finishHigherLower() {
  var s = state.higherLower;
  if (s.ranked !== false) {
    var st = state.stats.higherLower;
    st.gamesPlayed++;
    if (s.streak > st.bestStreak) st.bestStreak = s.streak;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(Math.min(100, s.streak * 10));
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('higherLower', { bestStreak: st.bestStreak, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('higherLower', s.streak + ' streak', Math.min(100, s.streak * 10));
  h2hSubmitModeResult('higherLower', s.streak, null);
}
function higherLowerPlayerLine(p) {
  return esc(p.position || '') + (p.college ? ' &middot; ' + esc(p.college) : '') + (p.teams && p.teams.length ? ' &middot; ' + esc(p.teams.join('/')) : '');
}
function renderHigherLowerSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">Higher or Lower</h2>' +
    '<p class="mode-desc">Two real NFL players, one real stat — see one player\'s total, guess whether the next player has more or fewer. Keep going until you miss — how long a streak can you build?</p>' +
    '<div class="chip-row">' +
    HIGHER_LOWER_STATS.map(function (st) { return '<button class="chip-toggle' + (higherLowerStatPref === st.id ? ' active' : '') + '" data-hl-stat="' + st.id + '">' + esc(st.label) + '</button>'; }).join('') +
    '</div>' +
    rankedToggleHtml('higherLower') +
    '<button class="btn-primary" data-hl-start>Start</button>' +
    '</div>';
}
function renderHigherLowerPlaying() {
  var s = state.higherLower;
  var revealing = s.screen === 'reveal';
  var statLabel = higherLowerStatConfig(s.stat).label;
  return '<div class="panel">' + modeToolbarHtml('higherLower', s.ranked) +
    '<h2 class="panel-title">Higher or Lower &middot; Streak: ' + s.streak + '</h2>' +
    '<div class="hl-card hl-card-current">' +
    '<div class="hl-name">' + esc(s.current.name) + '</div>' +
    '<div class="hl-line">' + higherLowerPlayerLine(s.current) + '</div>' +
    '<div class="hl-score">' + higherLowerScore(s.current, s.stat) + '</div>' +
    '<div class="hl-score-label">' + esc(statLabel) + '</div>' +
    '</div>' +
    '<div class="hl-vs">vs</div>' +
    '<div class="hl-card hl-card-next' + (revealing ? (s.lastCorrect ? ' correct' : ' wrong') : '') + '">' +
    '<div class="hl-name">' + esc(s.next.name) + '</div>' +
    '<div class="hl-line">' + higherLowerPlayerLine(s.next) + '</div>' +
    (revealing
      ? '<div class="hl-score">' + s.revealedScore + '</div><div class="hl-score-label">' + (s.lastCorrect ? icon('check') + ' Correct!' : icon('xMark') + ' Not quite') + '</div>'
      : '<div class="hl-score hl-score-hidden">?</div><div class="hl-score-label">More or fewer than ' + esc(s.current.name) + '?</div>') +
    '</div>' +
    (revealing
      ? '<button class="btn-primary hl-continue" data-hl-continue>Next Player</button>'
      : '<div class="hl-guess-row">' +
        '<button class="hl-guess-btn hl-lower" data-hl-guess="lower">' + icon('arrowDown') + ' Lower</button>' +
        '<button class="hl-guess-btn hl-higher" data-hl-guess="higher">' + icon('arrowUp') + ' Higher</button>' +
        '</div>') +
    '</div>';
}
function renderHigherLowerOver() {
  var s = state.higherLower;
  return '<div class="panel">' +
    '<h2 class="panel-title">Streak Over</h2>' +
    '<div class="summary-score">Final streak: ' + s.streak + '</div>' +
    '<div class="hl-card hl-card-next wrong">' +
    '<div class="hl-name">' + esc(s.next.name) + '</div>' +
    '<div class="hl-line">' + higherLowerPlayerLine(s.next) + '</div>' +
    '<div class="hl-score">' + s.revealedScore + '</div>' +
    '<div class="hl-score-label">vs ' + esc(s.current.name) + '\'s ' + higherLowerScore(s.current, s.stat) + '</div>' +
    '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-hl-start>Play Again</button>' +
    '<button class="btn-secondary" data-share="higherLower">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderHigherLowerScreen() {
  if (!state.higherLower) return renderHigherLowerSetup();
  if (state.higherLower.screen === 'over') return renderHigherLowerOver();
  return renderHigherLowerPlaying();
}

/* ============================== college football speed round ============================== */
function cfbSpeedQueue() { var ids = CFB_SPEED.map(function (q) { return q.id; }); return drawNoRepeat('cfbspeed', ids, ids.length); }
function currentCfbSpeedQuestion() {
  var s = state.cfbSpeed;
  var id = s.queue[s.qIndex % s.queue.length];
  return CFB_SPEED.find(function (q) { return q.id === id; });
}
function startCfbSpeedRound(sessionLen) {
  state.cfbSpeed = {
    sessionLen: sessionLen, qLen: 6, screen: 'playing',
    sessionEndsAt: Date.now() + sessionLen * 1000, qEndsAt: Date.now() + 6 * 1000,
    queue: cfbSpeedQueue(), qIndex: 0, answeredIndex: null,
    score: 0, streak: 0, bestStreak: 0, correctCount: 0, totalCount: 0,
    sessionTimeLeft: sessionLen, qTimeLeft: 6, ranked: state.rankedPref.cfbSpeed !== false
  };
  state.screen = 'cfbSpeed';
  stopTimers();
  cfbSpeedTimer = setInterval(cfbSpeedTick, 200);
  renderAll();
}
function cfbSpeedTick() {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing') return;
  var now = Date.now();
  s.sessionTimeLeft = Math.max(0, (s.sessionEndsAt - now) / 1000);
  if (s.sessionTimeLeft <= 0) { endCfbSpeedRound(); return; }
  s.qTimeLeft = Math.max(0, (s.qEndsAt - now) / 1000);
  if (s.answeredIndex === null && s.qTimeLeft <= 0) { registerCfbSpeedAnswer(-1); return; }
  var sessEl = document.getElementById('cfb-speed-session-timer');
  if (sessEl) sessEl.textContent = fmtTime(s.sessionTimeLeft);
  var barEl = document.getElementById('cfb-speed-qbar-fill');
  if (barEl) barEl.style.width = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen)) + '%';
}
function registerCfbSpeedAnswer(optionIndex) {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing' || s.answeredIndex !== null) return;
  s.answeredIndex = optionIndex;
  var q = currentCfbSpeedQuestion();
  var correct = q && optionIndex === q.correctIndex;
  s.totalCount++;
  if (correct) {
    s.correctCount++;
    s.streak++;
    if (s.streak > s.bestStreak) s.bestStreak = s.streak;
    var mult = 1 + Math.floor(s.streak / 3) * 0.5;
    s.score += Math.round(20 * mult);
  } else {
    s.streak = 0;
  }
  playSound(correct ? 'correct' : 'wrong');
  renderAll();
  setTimeout(advanceCfbSpeedQuestion, 550);
}
function advanceCfbSpeedQuestion() {
  var s = state.cfbSpeed;
  if (!s || s.screen !== 'playing') return;
  if (typeof stopSfx === 'function') stopSfx();
  if (Date.now() >= s.sessionEndsAt) return;
  s.qIndex++;
  if (s.qIndex >= s.queue.length) { s.queue = cfbSpeedQueue(); s.qIndex = 0; }
  s.answeredIndex = null;
  s.qEndsAt = Date.now() + s.qLen * 1000;
  renderAll();
}
function endCfbSpeedRound() {
  if (cfbSpeedTimer) { clearInterval(cfbSpeedTimer); cfbSpeedTimer = null; }
  state.cfbSpeed.screen = 'summary';
  finishCfbSpeedRound();
  renderAll();
}
function finishCfbSpeedRound() {
  var s = state.cfbSpeed;
  var pct = s.totalCount > 0 ? 100 * s.correctCount / s.totalCount : 100;
  if (s.ranked !== false) {
    var st = state.stats.cfbSpeed;
    st.sessionsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    if (s.bestStreak > st.bestStreak) st.bestStreak = s.bestStreak;
    lsSet('nflTriviaStats', state.stats);
    if (s.totalCount > 0) { updateRatingDrift(pct); s.ratingDelta = lastRatingDelta; }
    pushLeaderboard('cfbSpeed', { bestScore: st.bestScore, bestStreak: st.bestStreak, sessionsPlayed: st.sessionsPlayed });
  }
  h2hSubmitModeResult('cfbSpeed', s.correctCount, s.totalCount, s.score);
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderCfbSpeedSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB Speed Round</h2>' +
    '<p class="mode-desc">Rapid-fire college football multiple choice — about 6 seconds per question, non-stop until time runs out. Chain correct answers for a streak multiplier.</p>' +
    rankedToggleHtml('cfbSpeed') +
    '<div class="chip-row">' +
    [60, 90, 120].map(function (n) { return '<button class="chip-toggle" data-cfb-speed-start="' + n + '">' + n + 's session</button>'; }).join('') +
    '</div></div>';
}
function renderCfbSpeedPlaying() {
  var s = state.cfbSpeed, q = currentCfbSpeedQuestion();
  var answered = s.answeredIndex !== null;
  var qPct = Math.max(0, Math.min(100, 100 * s.qTimeLeft / s.qLen));
  return '<div class="panel">' + modeToolbarHtml('cfbSpeed', s.ranked) +
    '<div class="speed-header"><div>Session: <span id="cfb-speed-session-timer">' + fmtTime(s.sessionTimeLeft) + '</span></div><div>Score: ' + s.score + '</div><div>Streak: ' + s.streak + '</div></div>' +
    '<div class="speed-qbar"><div class="speed-qbar-fill" id="cfb-speed-qbar-fill" style="width:' + qPct + '%"></div></div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-cfb-speed-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderCfbSpeedSummary() {
  var s = state.cfbSpeed;
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB Speed Round Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + s.correctCount + ' / ' + s.totalCount + ' correct &middot; best streak ' + s.bestStreak + '</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-speed-start="' + s.sessionLen + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="cfbSpeed">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbSpeedScreen() {
  if (!state.cfbSpeed) return renderCfbSpeedSetup();
  if (state.cfbSpeed.screen === 'summary') return renderCfbSpeedSummary();
  if (state.cfbSpeed.screen === 'playing') return renderCfbSpeedPlaying();
  return renderCfbSpeedSetup();
}

/* ============================== silhouette ============================== */
var POSITION_LABELS = { QB: 'Quarterback', RB: 'Running Back', WR: 'Wide Receiver', TE: 'Tight End', C: 'Center', CB: 'Cornerback', DL: 'Defensive Line', DT: 'Defensive Tackle', DE: 'Defensive End', EDGE: 'Edge Rusher', LB: 'Linebacker', OG: 'Guard', OT: 'Tackle', OL: 'Offensive Line', S: 'Safety', K: 'Kicker' };
function expandPosition(position) {
  return String(position).split('/').map(function (tok) { tok = tok.trim(); return POSITION_LABELS[tok.toUpperCase()] || tok; }).join(' / ');
}
// Football player pictogram — "American Football Player" icon by Delapouite
// (game-icons.net), CC BY 3.0. Used here instead of a hand-drawn figure;
// attribution lives in the app footer and README.
var FOOTBALL_PLAYER_ICON_PATH = 'M256 41c-29.8 0-50.9 10.83-65.3 26.98C176.4 84.12 169 106 169 128c0 17.5 4.9 29.1 12.3 39h8.8l-7.1-38.2v-.8c0-7 3.8-13.2 8.6-17.3 4.9-4.2 10.8-7 17.6-9.2 1.9-.6 3.8-1.2 5.8-1.74V71h82v28.76c2 .54 3.9 1.14 5.8 1.74 6.8 2.2 12.7 5 17.6 9.2 4.8 4.1 8.6 10.3 8.6 17.3v.8l-7.1 38.2h8.8c7.4-9.9 12.3-21.5 12.3-39 0-22-7.4-43.88-21.7-60.02C306.9 51.83 285.8 41 256 41zm-23 48v14h46V89h-46zm-44.5 96 4.7 14h27.2l-3.4-14h-28.5zm46.9 0 3.4 14h34.4l3.4-14h-41.2zm59.6 0-3.4 14h27.2l4.7-14H295zm-121.5 11.9-27.3 3.9c-22.5 7.6-41.3 19-54.2 30-12.48 10.7-18.29 22-18.79 24.8l14.23 57L141.2 326l28.4-28.4 12.8 12.8-29 29 2.4 27.1 34-13.6c4.4-17.9 12-33.2 20.8-45.4 13.7-19 29.3-31.3 45.4-31.3 16.1 0 31.6 12.3 45.4 31.3 8.8 12.2 16.4 27.5 20.8 45.4l34 13.6 2.4-27.1-29-29 12.8-12.8 28.4 28.4 53.8-13.4 14.3-57.1c-.2-1.3-1.2-4.7-4.1-8.9-3.1-4.7-8.1-10.2-14.7-15.8-12.9-11-31.8-22.4-54.3-30l-27.3-3.9-10.2 30.6-.2.5c-5.7 11.2-16.9 18.1-29.6 22.5-12.8 4.4-27.6 6.5-42.5 6.5-14.9 0-29.7-2.1-42.5-6.5-12.7-4.4-23.9-11.3-29.6-22.5l-.2-.5-10.2-30.6zm25.6 20.1 1.1 3.2c2.5 4.7 9.2 9.8 19.3 13.3 3.1 1.1 6.4 2 9.9 2.8l-4.7-19.3h-25.6zm44 0 5.3 21.8c2.5.1 5.1.2 7.6.2s5.1-.1 7.6-.2l5.3-21.8h-25.8zm44.2 0-4.7 19.3c3.5-.8 6.8-1.7 9.9-2.8 10.1-3.5 16.8-8.6 19.3-13.3l1.1-3.2h-25.6zM256 294.2c-4.3 0-19.2 7.8-30.9 23.8-11.6 16.1-21.1 39.4-21.1 67.4 0 28.1 9.5 51.4 21.1 67.5 11.7 16 26.6 23.8 30.9 23.8 4.2 0 19.2-7.8 30.8-23.9 11.7-16.1 21.2-39.3 21.2-67.4 0-28-9.5-51.3-21.2-67.4-11.6-16-26.6-23.8-30.8-23.8zm-9 31.1h18v15.1h13.3v18H265v18h13.3v18H265v18.1h13.3v18H265v15.1h-18v-15.1h-13.4v-18H247v-18.1h-13.4v-18H247v-18h-13.4v-18H247v-15.1zm-165.66 4.3c-12.1 7.2-22.18 20.4-29.12 36.1C44.78 382.4 41 401.5 41 416c0 6.1 1.61 9.8 4.51 12.9 2.9 3.1 7.62 5.7 14.24 7.4 13.24 3.4 33.37 2.7 54.65-1.2 21.3-3.8 43.8-10.7 62.7-18.4 4-1.7 7.8-3.4 11.4-5.1-1.6-8.2-2.5-17-2.5-26.2 0-4 .2-8 .5-11.8l-87.16 34.8-9.7-14.8c8-8 19.86-19.8 29.46-31.4 4.8-5.7 9-11.4 11.9-16.3.8-1.3 1.1-2.3 1.7-3.5l-51.36-12.8zm349.36 0-51.4 12.8c.6 1.2.9 2.2 1.7 3.5 2.9 4.9 7.1 10.6 11.9 16.3 9.6 11.6 21.5 23.4 29.5 31.4l-9.7 14.8-87.2-34.8c.3 3.8.5 7.8.5 11.8 0 9.2-.9 18-2.5 26.2 3.6 1.7 7.4 3.4 11.4 5.1 18.9 7.7 41.4 14.6 62.7 18.4 21.3 3.9 41.4 4.6 54.7 1.2 6.6-1.7 11.3-4.3 14.2-7.4 2.9-3.1 4.5-6.8 4.5-12.9 0-14.5-3.8-33.6-11.2-50.3-7-15.7-17-28.9-29.1-36.1zm-237.6 99.8c-2.9 1.3-6 2.6-9.2 3.9-6.8 2.8-13.9 5.4-21.3 7.9l5.6 61.8h175.6l5.6-61.8c-7.4-2.5-14.5-5.1-21.3-7.9-3.2-1.3-6.3-2.6-9.2-3.9-4.5 13-10.6 24.5-17.5 34-13.8 19-29.3 31.3-45.4 31.3-16.1 0-31.7-12.3-45.4-31.3-6.9-9.5-13-21-17.5-34z';
function renderSilhouetteSvg(position, color) {
  return '<svg viewBox="0 0 512 512" class="silhouette-svg" preserveAspectRatio="xMidYMid meet"><path fill="' + color + '" d="' + FOOTBALL_PLAYER_ICON_PATH + '"/></svg>';
}
// Real per-player cutout, if one has been dropped in assets/silhouettes/<slug>.png
// (see assets/silhouettes/EXPECTED_FILENAMES.txt for the exact expected name per
// player). Rendered as an overlay on top of the generic pictogram; if the image
// 404s, onerror hides the <img> so the pictogram underneath shows through. If the
// image loads, onload hides the pictogram (previousElementSibling) instead — the
// two are never shown stacked/visible at the same time.
function renderSilhouetteStage(p, color) {
  var slug = slugify(p.name);
  return '<div class="silhouette-stage">' +
    renderSilhouetteSvg(p.position, color) +
    '<img class="silhouette-photo" src="assets/silhouettes/' + slug + '.png" alt="" ' +
    'onload="this.previousElementSibling.style.display=\'none\'" onerror="this.style.display=\'none\'" />' +
    '</div>';
}
function silhouetteAccoladesText(p) {
  var badges = [];
  if (p.hof) badges.push('Hall of Famer');
  if (p.mvp) badges.push('MVP winner');
  if (p.sbChamp) badges.push('Super Bowl champion');
  return badges.length ? badges.join(', ') : 'No Super Bowl rings, MVP awards, or Hall of Fame induction (yet)';
}
function silhouetteClues(p) {
  return [
    'Position: ' + expandPosition(p.position),
    'Drafted: ' + (p.draftDecade || 'Unknown'),
    'Team(s): ' + p.team,
    'Accolades: ' + silhouetteAccoladesText(p),
    'Signature move: ' + p.pose,
    'Recognition notes: ' + p.notes
  ];
}
function loadSilhouetteItem() {
  var s = state.silhouette, p = s.queue[s.index];
  s.currentClues = silhouetteClues(p);
  s.revealedCount = 0;
  s.itemState = 'guessing';
  s.input = '';
  s.lastWrong = false;
  s.lastPoints = 0;
}
function startSilhouetteRound(roundSize) {
  var size = Math.min(roundSize, SILHOUETTE_PLAYERS.length);
  var allNames = SILHOUETTE_PLAYERS.map(function (p) { return p.name; });
  var names = drawNoRepeat('silhouette', allNames, size);
  var pool = names.map(function (n) { return SILHOUETTE_PLAYERS.find(function (p) { return p.name === n; }); });
  state.silhouette = { roundSize: roundSize, queue: pool, index: 0, score: 0, results: [], screen: 'round', ranked: state.rankedPref.silhouette !== false };
  loadSilhouetteItem();
  state.screen = 'silhouette';
  renderAll();
}
function revealSilhouetteClue() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  if (s.revealedCount < s.currentClues.length) s.revealedCount++;
  renderAll();
}
function submitSilhouetteGuess() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  var norm = normName(s.input);
  if (!norm) return;
  var p = s.queue[s.index];
  if (normName(p.name) === norm) {
    var pts = Math.max(10, 100 - s.revealedCount * 20);
    s.score += pts;
    s.results.push({ name: p.name, correct: true, points: pts });
    s.lastPoints = pts;
    s.lastWrong = false;
    s.itemState = 'revealed';
    playSound('correct');
  } else {
    s.lastWrong = true;
    if (s.revealedCount < s.currentClues.length) s.revealedCount++;
    playSound('wrong');
  }
  s.input = '';
  renderAll();
}
function giveUpSilhouette() {
  var s = state.silhouette;
  if (!s || s.itemState !== 'guessing') return;
  s.results.push({ name: s.queue[s.index].name, correct: false, points: 0 });
  s.lastPoints = 0;
  s.lastWrong = false;
  s.itemState = 'revealed';
  renderAll();
}
function advanceSilhouette() {
  var s = state.silhouette;
  if (typeof stopSfx === 'function') stopSfx();
  if (s.index + 1 >= s.queue.length) { s.screen = 'summary'; finishSilhouetteRound(); renderAll(); return; }
  s.index++;
  loadSilhouetteItem();
  renderAll();
}
function finishSilhouetteRound() {
  var s = state.silhouette;
  var silCorrect = s.results.filter(function (r) { return r.correct; }).length;
  var pct = 100 * silCorrect / s.results.length;
  if (s.ranked !== false) {
    var st = state.stats.silhouette;
    st.roundsPlayed++;
    if (s.score > st.bestScore) st.bestScore = s.score;
    var quickGuesses = s.results.filter(function (r) { return r.correct && r.points >= 80; }).length;
    if (quickGuesses > st.bestQuick) st.bestQuick = quickGuesses;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('silhouette', { bestScore: st.bestScore, roundsPlayed: st.roundsPlayed, bestQuick: st.bestQuick });
    completeDailyChallengeFrom('silhouette', silCorrect + ' / ' + s.results.length + ' correct', pct);
    h2hSubmitModeResult('silhouette', silCorrect, s.results.length);
  }
  playSound(pct <= 60 ? 'boo' : 'complete');
}

function renderSilhouetteSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Silhouette</h2>' +
    '<p class="mode-desc">A generic pose silhouette for a real player from our pool — guess who it is. Wrong guesses (or asking for a hint) reveal a clue: position, draft info, college, a team they played for, then accolades. Fewer clues used = more points.</p>' +
    rankedToggleHtml('silhouette') +
    '<div class="chip-row">' +
    [5, 10].map(function (n) { return '<button class="chip-toggle" data-silhouette-start="' + n + '">' + n + ' players</button>'; }).join('') +
    '</div></div>';
}
function renderSilhouetteRound() {
  var s = state.silhouette, p = s.queue[s.index];
  var html = '<div class="panel">' + modeToolbarHtml('silhouette', s.ranked) +
    '<h2 class="panel-title">NFL Silhouette &middot; ' + (s.index + 1) + ' / ' + s.queue.length + ' &middot; ' + s.score + ' pts</h2>' +
    renderSilhouetteStage(p, s.itemState === 'revealed' ? '#d9a63c' : '#c9d3e6');
  if (s.itemState === 'revealed') {
    html += '<div class="silhouette-reveal">' + esc(p.name) + (s.lastPoints ? ' — +' + s.lastPoints + ' pts' : ' — no points') + '</div>' +
      '<button class="btn-primary" data-silhouette-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Silhouette') + '</button>';
  } else {
    html += '<div class="silhouette-clues">' +
      s.currentClues.slice(0, s.revealedCount).map(function (c) { return '<div class="silhouette-clue">' + esc(c) + '</div>'; }).join('') +
      '</div>' +
      (s.lastWrong ? '<div class="blitz-feedback wrong" aria-live="polite">Not quite — here\'s another clue.</div>' : '') +
      '<div class="grid-answer-box">' +
      '<div class="typeahead-wrap">' +
      '<input id="silhouette-input" autocomplete="off" placeholder="Who is it?" value="' + esc(s.input) + '" role="combobox" aria-expanded="false" aria-autocomplete="list" aria-controls="silhouette-input-typeahead" />' +
      '<div id="silhouette-input-typeahead" class="typeahead-list" role="listbox"></div>' +
      '</div>' +
      '<button class="btn-primary" data-silhouette-submit>Guess</button>' +
      '</div>' +
      '<div class="btn-row">' +
      '<button class="btn-secondary" data-silhouette-hint>Reveal a Clue</button>' +
      '<button class="btn-secondary" data-silhouette-giveup>Give Up</button>' +
      '</div>';
  }
  html += '</div>';
  return html;
}
function renderSilhouetteSummary() {
  var s = state.silhouette;
  var correctCount = s.results.filter(function (r) { return r.correct; }).length;
  // "Quick guess" matches the exact threshold finishSilhouetteRound() already
  // uses for st.bestQuick (points >= 80, i.e. correct with 0-1 clues
  // revealed) — this is that same definition surfaced per-round instead of
  // only ever showing up as a lifetime-best stat.
  var quickGuesses = s.results.filter(function (r) { return r.correct && r.points >= 80; });
  var missed = s.results.filter(function (r) { return !r.correct; });
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL Silhouette Round Complete</h2>' +
    '<div class="summary-score">' + s.score + ' pts &middot; ' + correctCount + ' / ' + s.queue.length + ' guessed</div>' +
    (quickGuesses.length ? '<div class="iq-insight">' + icon('zap') + ' ' + quickGuesses.length + ' quick guess' + (quickGuesses.length === 1 ? '' : 'es') + ' (1 clue or less): <b>' + quickGuesses.map(function (r) { return esc(r.name); }).join(', ') + '</b></div>' : '') +
    (missed.length ? '<div class="blitz-missed"><b>Missed:</b> ' + missed.map(function (r) { return esc(r.name); }).join(', ') + '</div>' : (s.queue.length ? '<div class="blitz-missed">Clean sweep — you got every player!</div>' : '')) +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-silhouette-start="' + s.roundSize + '">Play Again</button>' +
    '<button class="btn-secondary" data-share="silhouette">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderSilhouetteScreen() {
  if (!state.silhouette) return renderSilhouetteSetup();
  if (state.silhouette.screen === 'summary') return renderSilhouetteSummary();
  return renderSilhouetteRound();
}

/* ============================== football iq test ============================== */
var IQ_TEST_SIZE = 25;
function currentIQQuestion() {
  var s = state.iq;
  var id = s.queue[s.index];
  return QUIZ.find(function (q) { return q.id === id; });
}
function startIQTest() {
  var size = Math.min(IQ_TEST_SIZE, QUIZ.length);
  var queue = drawNoRepeat('iq', QUIZ.map(function (q) { return q.id; }), size);
  state.iq = { queue: queue, index: 0, answers: [], screen: 'test', ranked: state.rankedPref.iq !== false };
  state.screen = 'iq';
  renderAll();
}
function answerIQQuestion(i) {
  var s = state.iq;
  if (!s || s.screen !== 'test') return;
  var q = currentIQQuestion();
  s.answers.push({ category: q.category, correct: i === q.correctIndex });
  if (s.index + 1 >= s.queue.length) {
    s.screen = 'result';
    finishIQTest();
  } else {
    s.index++;
  }
  renderAll();
}
function iqTitle(iq) {
  if (iq >= 160) return 'Football Genius';
  if (iq >= 140) return 'Elite Analyst';
  if (iq >= 120) return 'Draft Room Ready';
  if (iq >= 100) return 'Solid Fan';
  if (iq >= 85) return 'Casual Watcher';
  if (iq >= 70) return 'Still Learning the Rules';
  return 'Needs a Football 101 Class';
}
function finishIQTest() {
  var s = state.iq;
  var correct = s.answers.filter(function (a) { return a.correct; }).length;
  var total = s.answers.length;
  var iq = Math.round(60 + (correct / total) * 100);
  s.correct = correct;
  s.total = total;
  s.iqScore = iq;
  if (s.ranked !== false) {
    var st = state.stats.iq;
    st.testsTaken++;
    if (iq > st.bestIQ) st.bestIQ = iq;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correct / total);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('iq', { bestIQ: st.bestIQ, testsTaken: st.testsTaken });
  }
  playSound(iq <= 60 ? 'boo' : 'complete');
}
// Shared by NFL/CFB IQ Test results — turns the flat per-category breakdown
// (already existed) into one readable "here's what actually moved your
// score" insight line, only when there's enough of a spread to say anything
// meaningful (needs at least 2 categories with a different hit rate, and at
// least 2 questions in each side so a single lucky/unlucky guess can't
// anoint a whole category as your "strongest"/"weakest").
function iqStrongestWeakest(breakdown) {
  var eligible = breakdown.filter(function (b) { return b.total >= 2; });
  if (eligible.length < 2) return null;
  var byPct = eligible.slice().sort(function (a, b) { return (b.correct / b.total) - (a.correct / a.total); });
  var best = byPct[0], worst = byPct[byPct.length - 1];
  if (best.correct / best.total === worst.correct / worst.total) return null;
  return { best: best, worst: worst };
}
function iqCategoryBreakdown(s) {
  var byCat = {};
  s.answers.forEach(function (a) {
    if (!byCat[a.category]) byCat[a.category] = { correct: 0, total: 0 };
    byCat[a.category].total++;
    if (a.correct) byCat[a.category].correct++;
  });
  return Object.keys(byCat).sort().map(function (cat) { return { category: cat, correct: byCat[cat].correct, total: byCat[cat].total }; });
}

function renderIQSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">NFL IQ Test</h2>' +
    '<p class="mode-desc">' + IQ_TEST_SIZE + ' questions pulled from every category, mixed difficulty. No right/wrong feedback until the end — just like a real test. Your score maps to a Football IQ from 60-160, plus a category-by-category breakdown.</p>' +
    rankedToggleHtml('iq') +
    '<button class="btn-primary" data-iq-start>Start Test</button>' +
    '</div>';
}
function renderIQTest() {
  var s = state.iq, q = currentIQQuestion();
  return '<div class="panel">' + modeToolbarHtml('iq', s.ranked) +
    '<div class="quiz-progress">Question ' + (s.index + 1) + ' of ' + s.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-iq-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderIQResult() {
  var s = state.iq;
  var breakdown = iqCategoryBreakdown(s);
  var insight = iqStrongestWeakest(breakdown);
  return '<div class="panel">' +
    '<h2 class="panel-title">Your Football IQ</h2>' +
    '<div class="iq-score">' + s.iqScore + '</div>' +
    '<div class="iq-title">' + esc(iqTitle(s.iqScore)) + '</div>' +
    '<div class="summary-score">' + s.correct + ' / ' + s.total + ' correct</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    (insight ? '<div class="iq-insight">Strongest: <b>' + esc(insight.best.category) + '</b> (' + insight.best.correct + '/' + insight.best.total + ') &middot; Weakest: <b>' + esc(insight.worst.category) + '</b> (' + insight.worst.correct + '/' + insight.worst.total + ')</div>' : '') +
    '<div class="iq-breakdown">' +
    breakdown.map(function (b) { return '<div class="iq-breakdown-row"><span>' + esc(b.category) + '</span><span>' + b.correct + ' / ' + b.total + '</span></div>'; }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-iq-start>Retake Test</button>' +
    '<button class="btn-secondary" data-share="iq">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderIQScreen() {
  if (!state.iq) return renderIQSetup();
  if (state.iq.screen === 'result') return renderIQResult();
  return renderIQTest();
}

/* ============================== intro test (football rating) ============================== */
function renderIntroIntro() {
  return '<div class="panel">' +
    '<h2 class="panel-title">' + icon('football') + ' Welcome, ' + esc(state.name) + '!</h2>' +
    '<p class="mode-desc">Before you dive in, answer ' + INTRO_TEST_SIZE + ' quick questions — a mix of NFL and College Football — to set your starting Football Rating. From here it drifts up or down a little based on how you do in every game mode you play, so it settles into a real skill rating over time instead of a one-off score.</p>' +
    '<button class="btn-primary" data-intro-begin>Start</button>' +
    '<p class="mode-desc" style="margin-top:10px;"><a href="#" data-intro-skip>Skip for now</a></p>' +
    '</div>';
}
function renderIntroQuestion() {
  var t = state.introTest, q = currentIntroQuestion();
  return '<div class="panel">' +
    '<div class="quiz-progress">Question ' + (t.index + 1) + ' of ' + t.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-intro-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderIntroResult() {
  var t = state.introTest;
  return '<div class="panel">' +
    '<h2 class="panel-title">Your Starting Football Rating</h2>' +
    '<div class="iq-score">' + t.score + '</div>' +
    '<div class="summary-score">' + t.correct + ' / ' + t.total + ' correct</div>' +
    '<div class="summary-note">This is your baseline — every game mode you play from here nudges it up or down a little based on how you do.</div>' +
    '<button class="btn-primary" data-intro-continue>Let\'s Play</button>' +
    '</div>';
}
function renderIntroScreen() {
  var t = state.introTest;
  if (t.screen === 'intro') return renderIntroIntro();
  if (t.screen === 'result') return renderIntroResult();
  return renderIntroQuestion();
}

/* ============================== college football iq test ============================== */
function currentCfbIQQuestion() {
  var s = state.cfbIq;
  var id = s.queue[s.index];
  return CFB.find(function (q) { return q.id === id; });
}
function startCfbIQTest() {
  var size = Math.min(IQ_TEST_SIZE, CFB.length);
  var queue = drawNoRepeat('cfbiq', CFB.map(function (q) { return q.id; }), size);
  state.cfbIq = { queue: queue, index: 0, answers: [], screen: 'test', ranked: state.rankedPref.cfbIq !== false };
  state.screen = 'cfbIq';
  renderAll();
}
function answerCfbIQQuestion(i) {
  var s = state.cfbIq;
  if (!s || s.screen !== 'test') return;
  var q = currentCfbIQQuestion();
  s.answers.push({ category: q.category, correct: i === q.correctIndex });
  if (s.index + 1 >= s.queue.length) {
    s.screen = 'result';
    finishCfbIQTest();
  } else {
    s.index++;
  }
  renderAll();
}
function cfbIqTitle(iq) {
  if (iq >= 160) return 'CFB Historian';
  if (iq >= 140) return 'Elite Analyst';
  if (iq >= 120) return 'Saturday Regular';
  if (iq >= 100) return 'Solid Fan';
  if (iq >= 85) return 'Casual Watcher';
  if (iq >= 70) return 'Still Learning the Rules';
  return 'Needs a CFB 101 Class';
}
function finishCfbIQTest() {
  var s = state.cfbIq;
  var correct = s.answers.filter(function (a) { return a.correct; }).length;
  var total = s.answers.length;
  var iq = Math.round(60 + (correct / total) * 100);
  s.correct = correct;
  s.total = total;
  s.iqScore = iq;
  if (s.ranked !== false) {
    var st = state.stats.cfbIq;
    st.testsTaken++;
    if (iq > st.bestIQ) st.bestIQ = iq;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(100 * correct / total);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbIq', { bestIQ: st.bestIQ, testsTaken: st.testsTaken });
  }
  playSound(iq <= 60 ? 'boo' : 'complete');
}
function cfbIqCategoryBreakdown(s) {
  var byCat = {};
  s.answers.forEach(function (a) {
    if (!byCat[a.category]) byCat[a.category] = { correct: 0, total: 0 };
    byCat[a.category].total++;
    if (a.correct) byCat[a.category].correct++;
  });
  return Object.keys(byCat).sort().map(function (cat) { return { category: cat, correct: byCat[cat].correct, total: byCat[cat].total }; });
}

function renderCfbIQSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">College Football IQ Test</h2>' +
    '<p class="mode-desc">' + IQ_TEST_SIZE + ' CFB questions pulled from every category, mixed difficulty. No right/wrong feedback until the end. Your score maps to a CFB IQ from 60-160, plus a category-by-category breakdown.</p>' +
    rankedToggleHtml('cfbIq') +
    '<button class="btn-primary" data-cfb-iq-start>Start Test</button>' +
    '</div>';
}
function renderCfbIQTest() {
  var s = state.cfbIq, q = currentCfbIQQuestion();
  return '<div class="panel">' + modeToolbarHtml('cfbIq', s.ranked) +
    '<div class="quiz-progress">Question ' + (s.index + 1) + ' of ' + s.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      return '<button class="quiz-option" data-cfb-iq-answer="' + i + '">' + String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div></div>';
}
function renderCfbIQResult() {
  var s = state.cfbIq;
  var breakdown = cfbIqCategoryBreakdown(s);
  var insight = iqStrongestWeakest(breakdown);
  return '<div class="panel">' +
    '<h2 class="panel-title">Your College Football IQ</h2>' +
    '<div class="iq-score">' + s.iqScore + '</div>' +
    '<div class="iq-title">' + esc(cfbIqTitle(s.iqScore)) + '</div>' +
    '<div class="summary-score">' + s.correct + ' / ' + s.total + ' correct</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    (insight ? '<div class="iq-insight">Strongest: <b>' + esc(insight.best.category) + '</b> (' + insight.best.correct + '/' + insight.best.total + ') &middot; Weakest: <b>' + esc(insight.worst.category) + '</b> (' + insight.worst.correct + '/' + insight.worst.total + ')</div>' : '') +
    '<div class="iq-breakdown">' +
    breakdown.map(function (b) { return '<div class="iq-breakdown-row"><span>' + esc(b.category) + '</span><span>' + b.correct + ' / ' + b.total + '</span></div>'; }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-iq-start>Retake Test</button>' +
    '<button class="btn-secondary" data-share="cfbIq">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbIQScreen() {
  if (!state.cfbIq) return renderCfbIQSetup();
  if (state.cfbIq.screen === 'result') return renderCfbIQResult();
  return renderCfbIQTest();
}

/* ============================== 17-0 legends draft ============================== */
var LEGENDS_TEAMS = window.LEGENDS_TEAMS || [];
var PLAYER_META = window.PLAYER_META || {};
var LEGENDS_DUOS = window.LEGENDS_DUOS || { legendary: [], elite: [] };
var CFB_LEGENDS_TEAMS = window.CFB_LEGENDS_TEAMS || [];
var CFB_PLAYER_META = window.CFB_PLAYER_META || {};
var CFB_LEGENDS_DUOS = window.CFB_LEGENDS_DUOS || { legendary: [], elite: [] };
var LEGENDS_SLOTS = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX'];
function legendsEligibleSlots(position) {
  if (position === 'QB') return ['QB'];
  if (position === 'RB') return ['RB1', 'RB2', 'FLEX'];
  if (position === 'WR') return ['WR1', 'WR2', 'FLEX'];
  if (position === 'TE') return ['TE', 'FLEX'];
  return [];
}
function legendsPlayerTeams(name) {
  var teams = [];
  LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (p.name === name && teams.indexOf(t.team) === -1) teams.push(t.team);
    });
  });
  return teams;
}
var LEGENDS_PERFECT_SCORE = null;
function legendsPerfectScore() {
  if (LEGENDS_PERFECT_SCORE !== null) return LEGENDS_PERFECT_SCORE;
  var byPos = { QB: [], RB: [], WR: [], TE: [] };
  LEGENDS_TEAMS.forEach(function (t) { t.players.forEach(function (p) { if (byPos[p.position]) byPos[p.position].push(p.fppg); }); });
  Object.keys(byPos).forEach(function (k) { byPos[k].sort(function (a, b) { return b - a; }); });
  var maxQB = byPos.QB[0] || 25, maxRB = byPos.RB[0] || 22, maxWR = byPos.WR[0] || 22, maxTE = byPos.TE[0] || 18;
  var maxFlex = Math.max(byPos.RB[1] || maxRB, byPos.WR[1] || maxWR, maxTE);
  LEGENDS_PERFECT_SCORE = maxQB + maxRB * 2 + maxWR * 2 + maxTE + maxFlex + 14;
  return LEGENDS_PERFECT_SCORE;
}
function legendsRollEntry() { return LEGENDS_TEAMS[Math.floor(Math.random() * LEGENDS_TEAMS.length)]; }
function legendsOpenSlotCount(slots, position) {
  return legendsEligibleSlots(position).filter(function (s) { return !slots[s]; }).length;
}
function legendsPickedNames(slots) {
  return LEGENDS_SLOTS.map(function (sl) { return slots[sl] && slots[sl].name; }).filter(Boolean);
}
function legendsRollHasLegalPick(entry, slots) {
  var picked = legendsPickedNames(slots);
  return entry.players.some(function (p) { return legendsOpenSlotCount(slots, p.position) > 0 && picked.indexOf(p.name) === -1; });
}
function legendsDoRoll(state_) {
  var entry = legendsRollEntry(), tries = 0;
  while (!legendsRollHasLegalPick(entry, state_.slots) && tries < 500) { entry = legendsRollEntry(); tries++; }
  state_.rolledEntry = entry;
}
function startLegends() {
  var slots = {};
  LEGENDS_SLOTS.forEach(function (s) { slots[s] = null; });
  state.legends = { screen: 'draft', round: 1, slots: slots, teamRerollUsed: false, yearRerollUsed: false, rolledEntry: null, ranked: state.rankedPref.legends !== false };
  legendsDoRoll(state.legends);
  state.screen = 'legends';
  renderAll();
}
function legendsPickPlayer(playerIdx) {
  var s = state.legends;
  if (!s || s.screen !== 'draft') return;
  var entry = s.rolledEntry, p = entry.players[playerIdx];
  if (legendsPickedNames(s.slots).indexOf(p.name) !== -1) return;
  var openSlots = legendsEligibleSlots(p.position).filter(function (sl) { return !s.slots[sl]; });
  if (!openSlots.length) return;
  var slot = openSlots[0];
  if (openSlots.length > 1 && openSlots.indexOf('FLEX') !== -1) {
    var nonFlex = openSlots.filter(function (sl) { return sl !== 'FLEX'; });
    if (nonFlex.length) slot = nonFlex[0];
  }
  s.slots[slot] = { name: p.name, position: p.position, fppg: p.fppg, team: entry.team, year: entry.year };
  if (s.round >= 7) {
    s.screen = 'result';
    finishLegends();
  } else {
    s.round++;
    legendsDoRoll(s);
  }
  renderAll();
}
function legendsRerollTeam() {
  var s = state.legends;
  if (!s || s.screen !== 'draft' || s.teamRerollUsed) return;
  s.teamRerollUsed = true;
  var current = s.rolledEntry.team;
  var options = LEGENDS_TEAMS.filter(function (t) { return t.team !== current && legendsRollHasLegalPick(t, s.slots); });
  s.rolledEntry = options.length ? options[Math.floor(Math.random() * options.length)] : s.rolledEntry;
  renderAll();
}
function legendsRerollYear() {
  var s = state.legends;
  if (!s || s.screen !== 'draft' || s.yearRerollUsed) return;
  s.yearRerollUsed = true;
  var current = s.rolledEntry;
  var options = LEGENDS_TEAMS.filter(function (t) { return t.team === current.team && t.year !== current.year && legendsRollHasLegalPick(t, s.slots); });
  if (!options.length) options = LEGENDS_TEAMS.filter(function (t) { return legendsRollHasLegalPick(t, s.slots); });
  s.rolledEntry = options.length ? options[Math.floor(Math.random() * options.length)] : s.rolledEntry;
  renderAll();
}
function legendsDuoMatch(list, a, b) {
  return list.some(function (pair) { return (pair[0] === a && pair[1] === b) || (pair[0] === b && pair[1] === a); });
}
function legendsCalcChemistry(picks) {
  var bonus = {}, log = [];
  picks.forEach(function (p) { bonus[p.name] = 0; });
  for (var i = 0; i < picks.length; i++) {
    for (var j = i + 1; j < picks.length; j++) {
      var a = picks[i], b = picks[j], pairBonus = 0, reasons = [];
      var metaA = PLAYER_META[a.name] || {}, metaB = PLAYER_META[b.name] || {};
      if (a.team === b.team && a.year === b.year) { pairBonus += 2; reasons.push('Same Team (+2)'); }
      if (metaA.college && metaA.college === metaB.college) { pairBonus += 2; reasons.push('Same College (+2)'); }
      if (metaA.draftYear && metaA.draftYear === metaB.draftYear) { pairBonus += 1; reasons.push('Same Draft (+1)'); }
      var teamsA = legendsPlayerTeams(a.name), teamsB = legendsPlayerTeams(b.name);
      if (teamsA.some(function (t) { return teamsB.indexOf(t) !== -1; })) { pairBonus += 1; reasons.push('Past Teammates (+1)'); }
      if (legendsDuoMatch(LEGENDS_DUOS.legendary, a.name, b.name)) { pairBonus += 2; reasons.push('Legendary Connection (+2)'); }
      else if (legendsDuoMatch(LEGENDS_DUOS.elite, a.name, b.name)) { pairBonus += 1; reasons.push('Elite Connection (+1)'); }
      if (pairBonus > 0) {
        bonus[a.name] += pairBonus;
        bonus[b.name] += pairBonus;
        log.push({ a: a.name, b: b.name, bonus: pairBonus, reasons: reasons });
      }
    }
  }
  return { bonus: bonus, log: log };
}
function legendsGrade(pct) {
  if (pct >= 0.95) return { grade: 'S', label: 'GOAT' };
  if (pct >= 0.88) return { grade: 'A+', label: 'Iconic' };
  if (pct >= 0.80) return { grade: 'A', label: 'Undisputed Champ' };
  if (pct >= 0.72) return { grade: 'A-', label: 'League Champ' };
  if (pct >= 0.64) return { grade: 'B+', label: 'Runner-Up' };
  if (pct >= 0.56) return { grade: 'B', label: '2nd Round Exit' };
  if (pct >= 0.48) return { grade: 'B-', label: 'First Round Exit' };
  if (pct >= 0.40) return { grade: 'C+', label: 'Missed Playoffs' };
  if (pct >= 0.32) return { grade: 'C', label: 'Mid' };
  if (pct >= 0.22) return { grade: 'D', label: 'Rebuilding' };
  return { grade: 'F', label: 'Toilet Bowl' };
}
function finishLegends() {
  var s = state.legends;
  var picks = LEGENDS_SLOTS.map(function (slot) { return Object.assign({ slot: slot }, s.slots[slot]); });
  var chem = legendsCalcChemistry(picks);
  var baseTotal = 0, finalTotal = 0;
  picks.forEach(function (p) {
    var b = chem.bonus[p.name] || 0;
    p.chemistry = b;
    p.finalFppg = p.fppg + b;
    baseTotal += p.fppg;
    finalTotal += p.finalFppg;
  });
  var perfect = legendsPerfectScore();
  var pct = Math.max(0, Math.min(1, finalTotal / perfect));
  var wins = Math.round(17 * pct);
  var losses = 17 - wins;
  var g = legendsGrade(pct);
  s.picks = picks;
  s.chemLog = chem.log;
  s.baseTotal = Math.round(baseTotal * 10) / 10;
  s.finalTotal = Math.round(finalTotal * 10) / 10;
  s.perfectScore = Math.round(perfect * 10) / 10;
  s.wins = wins;
  s.losses = losses;
  s.grade = g.grade;
  s.gradeLabel = g.label;
  if (s.ranked !== false) {
    var st = state.stats.legends;
    st.gamesPlayed++;
    if (wins > st.bestWins || (wins === st.bestWins && finalTotal > st.bestScore)) { st.bestWins = wins; st.bestScore = s.finalTotal; st.bestGrade = g.grade; }
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct * 100);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('legends', { bestWins: st.bestWins, bestRecord: st.bestWins + '-' + (17 - st.bestWins), bestScore: st.bestScore, bestGrade: st.bestGrade, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('legends', wins + '-' + losses + ' (' + g.grade + ')', pct * 100);
  h2hSubmitModeResult('legends', wins, 17);
  playSound(g.grade === 'F' ? 'boo' : 'complete');
}

function renderLegendsSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">17-0</h2>' +
    '<p class="mode-desc">Draft a 7-player fantasy team (QB, 2 RB, 2 WR, TE, FLEX) built entirely from real players\' real seasons, 1999-2025. Each round rolls a random notable team-season — pick one player into an open slot. You get 1 team re-roll and 1 year re-roll for the whole draft. After 7 rounds, real PPR points-per-game plus roster chemistry (teammates, same college, same draft class, iconic duos) decide your final grade and projected record.</p>' +
    rankedToggleHtml('legends') +
    '<button class="btn-primary" data-legends-start>Start Draft</button>' +
    '</div>';
}
function legendsSlotLabel(slot) { return slot.replace(/\d/, function (d) { return ' ' + d; }); }
function renderLegendsDraft() {
  var s = state.legends, entry = s.rolledEntry;
  var html = '<div class="panel">' + modeToolbarHtml('legends', s.ranked) +
    '<h2 class="panel-title">Round ' + s.round + ' of 7</h2>' +
    '<div class="legends-roll"><b>' + esc(entry.team) + '</b> &middot; ' + entry.year + '</div>' +
    '<div class="legends-slots">' +
    LEGENDS_SLOTS.map(function (slot) {
      var filled = s.slots[slot];
      return '<div class="legends-slot' + (filled ? ' filled' : '') + '"><div class="legends-slot-name">' + legendsSlotLabel(slot) + '</div>' +
        (filled ? '<div class="legends-slot-player">' + esc(filled.name) + '</div>' : '<div class="legends-slot-empty">open</div>') + '</div>';
    }).join('') +
    '</div>' +
    '<div class="legends-options">' +
    entry.players.map(function (p, i) {
      var alreadyPicked = legendsPickedNames(s.slots).indexOf(p.name) !== -1;
      var open = !alreadyPicked && legendsOpenSlotCount(s.slots, p.position) > 0;
      return '<button class="legends-option" ' + (open ? 'data-legends-pick="' + i + '"' : 'disabled') + '>' +
        '<div class="legends-option-name">' + esc(p.name) + (alreadyPicked ? ' (already drafted)' : '') + '</div>' +
        '<div class="legends-option-meta">' + p.position + ' &middot; ' + p.fppg + ' FPPG</div>' +
        '</button>';
    }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" ' + (s.teamRerollUsed ? 'disabled' : 'data-legends-reroll-team') + '>Re-roll Team' + (s.teamRerollUsed ? ' (used)' : '') + '</button>' +
    '<button class="btn-secondary" ' + (s.yearRerollUsed ? 'disabled' : 'data-legends-reroll-year') + '>Re-roll Year' + (s.yearRerollUsed ? ' (used)' : '') + '</button>' +
    '</div></div>';
  return html;
}
function renderLegendsResult() {
  var s = state.legends;
  return '<div class="panel">' +
    '<h2 class="panel-title">Your 17-0 Team</h2>' +
    '<div class="legends-grade">' + esc(s.grade) + '</div>' +
    '<div class="iq-title">' + esc(s.gradeLabel) + '</div>' +
    '<div class="summary-score">Projected record: ' + s.wins + '-' + s.losses + '</div>' +
    '<div class="summary-note">Base FPPG ' + s.baseTotal + ' + Chemistry = ' + s.finalTotal + ' (perfect-team ceiling: ' + s.perfectScore + ')</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="legends-roster">' +
    s.picks.map(function (p) {
      return '<div class="legends-roster-row"><span class="legends-roster-slot">' + legendsSlotLabel(p.slot) + '</span>' +
        '<span class="legends-roster-player">' + esc(p.name) + ' <i>(' + esc(p.team) + ' ' + p.year + ')</i></span>' +
        '<span class="legends-roster-score">' + p.fppg + (p.chemistry ? ' +' + p.chemistry : '') + ' = ' + Math.round(p.finalFppg * 10) / 10 + '</span></div>';
    }).join('') +
    '</div>' +
    (s.chemLog.length ? '<div class="legends-chem-log"><b>Chemistry:</b>' +
      s.chemLog.map(function (c) { return '<div class="legends-chem-row">' + esc(c.a) + ' + ' + esc(c.b) + ': ' + c.reasons.join(', ') + '</div>'; }).join('') +
      '</div>' : '<div class="legends-chem-log">No chemistry connections this time — a bit of a disconnected roster.</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-legends-start>Draft Again</button>' +
    '<button class="btn-secondary" data-share="legends">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderLegendsScreen() {
  if (!state.legends) return renderLegendsSetup();
  if (state.legends.screen === 'result') return renderLegendsResult();
  return renderLegendsDraft();
}

/* ============================== CFB 12-0 legends draft ==============================
   College football edition of 17-0, originally built from the user-provided
   CFB_16-0_Game_Template.xlsx spec (hence the old filename). Structurally
   mirrors the NFL legends* functions above (same roll -> pick -> chemistry ->
   grade loop), duplicated rather than shared — matches this codebase's
   existing per-league convention (quiz/cfbQuiz, iq/cfbIq, etc.) and is
   necessary here anyway since several strings differ (8 rounds not 7, "12-0"
   not "17-0", CFB-flavored grade labels). Two things are genuinely new, not
   just a port: an 8th roster slot (DEF: DL/LB/DB), and a real 12-game FBS
   regular season (not 17 like the NFL version) — the postseason (National
   Championship / Playoff round / bowl game) is then predicted FROM that
   regular-season record separately, via cfbLegendsPostseasonLabel() below,
   rather than being folded into the win count itself. */
var CFB_LEGENDS_SLOTS = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX', 'DEF'];
function cfbLegendsEligibleSlots(position) {
  if (position === 'QB') return ['QB'];
  if (position === 'RB') return ['RB1', 'RB2', 'FLEX'];
  if (position === 'WR') return ['WR1', 'WR2', 'FLEX'];
  if (position === 'TE') return ['TE', 'FLEX'];
  if (position === 'DEF') return ['DEF'];
  return [];
}
function cfbLegendsPlayerTeams(name) {
  var teams = [];
  CFB_LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (p.name === name && teams.indexOf(t.team) === -1) teams.push(t.team);
    });
  });
  return teams;
}
// Memoized only WITHIN a single draft, not across the whole page session --
// startCfbLegends() resets this to null every time a draft starts. It used
// to cache forever after the first call, which meant the very first draft
// played in a tab (sometimes racing a lazy data-file load, or a stale
// service-worker response before a fresh deploy fully took over) could lock
// in a wrong ceiling that then silently stuck around for every later draft
// in that same tab, no matter how many times the page was reloaded or the
// underlying data changed -- exactly the "ceiling says 203 but the file on
// disk says 139.5" bug this comment is here to prevent from recurring.
var CFB_LEGENDS_PERFECT_SCORE = null;
function cfbLegendsPerfectScore() {
  if (CFB_LEGENDS_PERFECT_SCORE !== null) return CFB_LEGENDS_PERFECT_SCORE;
  var byPos = { QB: [], RB: [], WR: [], TE: [], DEF: [] };
  CFB_LEGENDS_TEAMS.forEach(function (t) {
    t.players.forEach(function (p) {
      if (byPos[p.position]) byPos[p.position].push(p.fppg);
    });
  });
  Object.keys(byPos).forEach(function (k) { byPos[k].sort(function (a, b) { return b - a; }); });
  var maxQB = byPos.QB[0] || 25, maxRB = byPos.RB[0] || 22, maxWR = byPos.WR[0] || 22, maxTE = byPos.TE[0] || 18, maxDef = byPos.DEF[0] || 10;
  var maxFlex = Math.max(byPos.RB[1] || maxRB, byPos.WR[1] || maxWR, maxTE);
  CFB_LEGENDS_PERFECT_SCORE = maxQB + maxRB * 2 + maxWR * 2 + maxTE + maxFlex + maxDef;
  return CFB_LEGENDS_PERFECT_SCORE;
}
// Every team-year entry a slot is currently filled with is already tagged
// with its own `team` field (set in cfbLegendsPickPlayer below) — this is
// just the deduped list of schools on the board right now, used by the
// same-school roll bias in cfbLegendsRollEntry.
function cfbLegendsPickedSchools(slots) {
  var schools = [];
  CFB_LEGENDS_SLOTS.forEach(function (sl) {
    if (slots[sl] && slots[sl].team && schools.indexOf(slots[sl].team) === -1) schools.push(slots[sl].team);
  });
  return schools;
}
// Picks the NEXT team-season to roll from a persisted, shuffled, no-repeat
// deck of indices into CFB_LEGENDS_TEAMS (same drawNoRepeat() philosophy
// used everywhere else in this app for randomized draws, adapted here for
// one-at-a-time interactive rolls instead of a batch-drawn queue) — plain
// Math.random() over the flat array used to mean a team with more entries
// in the pool showed up proportionally more often, and nothing stopped the
// exact same team-year from being rolled twice in one draft. usedIds is
// this draft's own exclusion list (see cfbLegendsDoRoll) — entries still
// get consumed from the persisted cross-draft deck even when skipped for
// being used-this-draft, which is fine: they come back on the next reshuffle.
//
// Soft "team chemistry" bias: usedEntryIds excludes a team-YEAR entry from
// ever being rolled twice in the same draft by design (so "Same Team" — same
// team AND year — can never fire; that's intentional, you can't draft two
// starters off literally the same single roll). But with 69 programs spread
// across only 8 rolls per draft, landing on the SAME SCHOOL twice (a
// different year — the "Same School" bonus, which CAN fire) was rare enough
// by pure chance that chemistry barely ever showed up, capping most drafts
// well below the higher grades. Once at least one slot is filled, there's a
// real (not guaranteed — still needs to feel like a random roll, and it's
// only checked when a same-school option actually exists) chance the next
// roll deliberately favors a different team-year entry from a school already
// on the roster instead of the deck's plain draw order.
// 0.07 checked EVERY round from round 2 on (up to 7 independent chances in
// an 8-round draft) compounds a lot more than the flat number suggests —
// tuned against a 2000-draft simulation of the real 207-entry pool: raises
// "at least one same-school pair" from ~25% of drafts (the old, "impossible"-
// feeling baseline) to ~54%, roughly tripling the average chemistry points
// per draft, while a 3+-school stack stays rare (~2% of drafts) rather than
// routine. That's "noticeably more achievable," not "guaranteed every game."
var CFB_LEGENDS_SAME_SCHOOL_BIAS = 0.07;
function cfbLegendsRollEntry(usedIds, slots) {
  var storKey = 'deck__cfbLegends';
  var allIds = CFB_LEGENDS_TEAMS.map(function (_, i) { return i; });
  var deck = lsGet(storKey, []).filter(function (id) { return id < CFB_LEGENDS_TEAMS.length; });
  if (!deck.length) deck = shuffle(allIds);
  var pickedSchools = slots ? cfbLegendsPickedSchools(slots) : [];
  if (pickedSchools.length && Math.random() < CFB_LEGENDS_SAME_SCHOOL_BIAS) {
    var sameSchoolIds = deck.filter(function (id) {
      return usedIds.indexOf(id) === -1 && pickedSchools.indexOf(CFB_LEGENDS_TEAMS[id].team) !== -1;
    });
    if (sameSchoolIds.length) {
      var chosen = sameSchoolIds[Math.floor(Math.random() * sameSchoolIds.length)];
      deck.splice(deck.indexOf(chosen), 1);
      lsSet(storKey, deck);
      return { id: chosen, entry: CFB_LEGENDS_TEAMS[chosen] };
    }
  }
  var idx = deck.findIndex(function (id) { return usedIds.indexOf(id) === -1; });
  if (idx === -1) {
    deck = shuffle(allIds);
    idx = deck.findIndex(function (id) { return usedIds.indexOf(id) === -1; });
    if (idx === -1) idx = 0; // every single entry already used this draft (won't happen — pool is far bigger than 8 rounds)
  }
  var id = deck[idx];
  deck.splice(idx, 1);
  lsSet(storKey, deck);
  return { id: id, entry: CFB_LEGENDS_TEAMS[id] };
}
function cfbLegendsOpenSlotCount(slots, position) {
  return cfbLegendsEligibleSlots(position).filter(function (s) { return !slots[s]; }).length;
}
function cfbLegendsPickedNames(slots) {
  return CFB_LEGENDS_SLOTS.map(function (sl) { return slots[sl] && slots[sl].name; }).filter(Boolean);
}
function cfbLegendsRollHasLegalPick(entry, slots) {
  var picked = cfbLegendsPickedNames(slots);
  return entry.players.some(function (p) { return cfbLegendsOpenSlotCount(slots, p.position) > 0 && picked.indexOf(p.name) === -1; });
}
function cfbLegendsDoRoll(state_) {
  state_.usedEntryIds = state_.usedEntryIds || [];
  var picked = cfbLegendsRollEntry(state_.usedEntryIds, state_.slots), tries = 0;
  while (!cfbLegendsRollHasLegalPick(picked.entry, state_.slots) && tries < 500) {
    picked = cfbLegendsRollEntry(state_.usedEntryIds, state_.slots);
    tries++;
  }
  state_.rolledEntry = picked.entry;
  state_.rolledEntryId = picked.id;
  if (state_.usedEntryIds.indexOf(picked.id) === -1) state_.usedEntryIds.push(picked.id);
}
function startCfbLegends() {
  CFB_LEGENDS_PERFECT_SCORE = null;
  var slots = {};
  CFB_LEGENDS_SLOTS.forEach(function (s) { slots[s] = null; });
  state.cfbLegends = { screen: 'draft', round: 1, slots: slots, teamRerollUsed: false, yearRerollUsed: false, rolledEntry: null, rolledEntryId: null, usedEntryIds: [], ranked: state.rankedPref.cfbLegends !== false };
  cfbLegendsDoRoll(state.cfbLegends);
  state.screen = 'cfbLegends';
  renderAll();
}
function cfbLegendsPickPlayer(playerIdx) {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft') return;
  var entry = s.rolledEntry, p = entry.players[playerIdx];
  if (cfbLegendsPickedNames(s.slots).indexOf(p.name) !== -1) return;
  var openSlots = cfbLegendsEligibleSlots(p.position).filter(function (sl) { return !s.slots[sl]; });
  if (!openSlots.length) return;
  var slot = openSlots[0];
  if (openSlots.length > 1 && openSlots.indexOf('FLEX') !== -1) {
    var nonFlex = openSlots.filter(function (sl) { return sl !== 'FLEX'; });
    if (nonFlex.length) slot = nonFlex[0];
  }
  s.slots[slot] = { name: p.name, position: p.position, fppg: p.fppg, team: entry.team, year: entry.year };
  if (s.round >= 8) {
    s.screen = 'result';
    finishCfbLegends();
  } else {
    s.round++;
    cfbLegendsDoRoll(s);
  }
  renderAll();
}
// Both re-rolls index CFB_LEGENDS_TEAMS directly (not via the shared deck —
// each is used at most once per draft, a much smaller randomness surface
// than the 8 main per-round rolls) but still respect usedEntryIds so a
// re-roll can't land on a team-year already seen earlier this same draft;
// falls back to ignoring that exclusion only if literally nothing else
// qualifies, same "never leave the player with an illegal roll" guarantee
// the original code had.
function cfbLegendsIndexedTeams() { return CFB_LEGENDS_TEAMS.map(function (t, i) { return { t: t, i: i }; }); }
function cfbLegendsApplyReroll(s, options) {
  if (!options.length) return;
  var pick = options[Math.floor(Math.random() * options.length)];
  s.rolledEntry = pick.t;
  s.rolledEntryId = pick.i;
  if (s.usedEntryIds.indexOf(pick.i) === -1) s.usedEntryIds.push(pick.i);
}
function cfbLegendsRerollTeam() {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft' || s.teamRerollUsed) return;
  s.teamRerollUsed = true;
  var current = s.rolledEntry.team;
  var all = cfbLegendsIndexedTeams();
  var options = all.filter(function (o) { return o.t.team !== current && s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return o.t.team !== current && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  cfbLegendsApplyReroll(s, options);
  renderAll();
}
function cfbLegendsRerollYear() {
  var s = state.cfbLegends;
  if (!s || s.screen !== 'draft' || s.yearRerollUsed) return;
  s.yearRerollUsed = true;
  var current = s.rolledEntry;
  var all = cfbLegendsIndexedTeams();
  var options = all.filter(function (o) { return o.t.team === current.team && o.t.year !== current.year && s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return o.t.team === current.team && o.t.year !== current.year && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return s.usedEntryIds.indexOf(o.i) === -1 && cfbLegendsRollHasLegalPick(o.t, s.slots); });
  if (!options.length) options = all.filter(function (o) { return cfbLegendsRollHasLegalPick(o.t, s.slots); });
  cfbLegendsApplyReroll(s, options);
  renderAll();
}
// legendsDuoMatch (defined above, in the NFL legends section) is fully
// generic — just a list + two names — so it's reused here as-is rather than
// duplicated.
function cfbLegendsCalcChemistry(picks) {
  var bonus = {}, log = [];
  picks.forEach(function (p) { bonus[p.name] = 0; });
  for (var i = 0; i < picks.length; i++) {
    for (var j = i + 1; j < picks.length; j++) {
      var a = picks[i], b = picks[j], pairBonus = 0, reasons = [];
      var metaA = CFB_PLAYER_META[a.name] || {}, metaB = CFB_PLAYER_META[b.name] || {};
      if (a.team === b.team && a.year === b.year) { pairBonus += 2; reasons.push('Same Team (+2)'); }
      if (metaA.school && metaA.school === metaB.school) { pairBonus += 2; reasons.push('Same School (+2)'); }
      if (metaA.signingClass && metaA.signingClass === metaB.signingClass) { pairBonus += 1; reasons.push('Same Signing Class (+1)'); }
      var teamsA = cfbLegendsPlayerTeams(a.name), teamsB = cfbLegendsPlayerTeams(b.name);
      if (teamsA.some(function (t) { return teamsB.indexOf(t) !== -1; })) { pairBonus += 1; reasons.push('Past Teammates (+1)'); }
      if (legendsDuoMatch(CFB_LEGENDS_DUOS.legendary, a.name, b.name)) { pairBonus += 2; reasons.push('Legendary Connection (+2)'); }
      else if (legendsDuoMatch(CFB_LEGENDS_DUOS.elite, a.name, b.name)) { pairBonus += 1; reasons.push('Elite Connection (+1)'); }
      if (pairBonus > 0) {
        bonus[a.name] += pairBonus;
        bonus[b.name] += pairBonus;
        log.push({ a: a.name, b: b.name, bonus: pairBonus, reasons: reasons });
      }
    }
  }
  return { bonus: bonus, log: log };
}
// Same S-through-F thresholds as the NFL legendsGrade(), but with the
// CFB-flavored labels (including emoji) from the spreadsheet's own
// "4. Grading Scale" sheet.
// Grade is derived straight from the regular-season record (wins — the same
// number cfbLegendsPostseasonLabel below uses), not a separate pct-threshold
// scale, so the letter grade can never disagree with the actual postseason
// outcome shown right under it (e.g. a 6-6 team can't grade out "B-" while
// its own postseason line says it missed the 12-team field entirely — that
// mismatch is exactly what this was rebalanced to fix).
function cfbLegendsGrade(pct) {
  var wins = Math.round(12 * pct);
  if (wins >= 12) return { grade: 'S', label: 'GOAT 🐐' };
  if (wins === 11) return { grade: 'A+', label: 'Runner-Up 🤩' };
  if (wins === 10) return { grade: 'A-', label: 'Final Four' };
  if (wins === 9) return { grade: 'B+', label: 'Quarterfinalist' };
  if (wins === 8) return { grade: 'B-', label: 'First Round Exit' };
  if (wins === 7) return { grade: 'C+', label: 'Bubble Team' };
  if (wins === 6) return { grade: 'C-', label: 'Missed the Field' };
  if (wins === 5) return { grade: 'D+', label: 'Rebuilding' };
  if (wins === 4) return { grade: 'D', label: 'Rebuilding' };
  return { grade: 'F', label: 'Toilet Bowl 💩' };
}
// Real, lower-tier bowl names for the "missed the 12-team field" tier (see
// cfbLegendsPostseasonLabel below) — picked randomly per grade band so a
// weaker roster's capstone game varies playthrough to playthrough instead of
// always naming the exact same bowl.
var CFB_BOWL_NAMES = {
  'C+': ['Cotton Bowl', 'Alamo Bowl', 'Holiday Bowl'],
  C: ['Sun Bowl', 'Music City Bowl', 'Pinstripe Bowl'],
  D: ['Independence Bowl', 'Gasparilla Bowl', 'Birmingham Bowl'],
  F: ['New Mexico Bowl', 'Frisco Bowl', 'Bahamas Bowl']
};
function pickRandom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
// Postseason placement is predicted straight from the 12-game regular-season
// record — not from the roster grade — since that's how it actually works
// in real CFB: your record decides your seed/bowl, not some abstract quality
// score. 12-0 is the only unbeaten and wins it all; 11-1 and 10-2 are strong
// Playoff seeds that go deep; 9-3/8-4 are the bubble of the 12-team field;
// 7-5 and below missed the Playoff and play a real, record-appropriate bowl
// game instead (named from CFB_BOWL_NAMES above). Static and deterministic
// (aside from which bowl name), since this app's offline/static architecture
// has no runtime AI narration to draw on.
function cfbLegendsPostseasonLabel(wins) {
  if (wins >= 12) return '🏆 National Champions — the only unbeaten team in the country, and it showed. Won it all.';
  if (wins === 11) return '🥈 Runner-Up — made the National Championship Game and came up just short.';
  if (wins === 10) return 'Lost in the Semifinal of the 12-team Playoff';
  if (wins === 9) return 'Lost in the Quarterfinal of the 12-team Playoff';
  if (wins === 8) return 'Lost in the First Round of the 12-team Playoff';
  if (wins === 7) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES['C+']);
  if (wins === 6) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.C);
  if (wins === 5) return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.D);
  return 'Missed the 12-team field — capped the season at the ' + pickRandom(CFB_BOWL_NAMES.F);
}
// The spec's "fun one-line verdict" (sheet 5, step 6: 'Give the final grade
// and a fun one-line verdict, e.g. "Iconic 👑 — this squad is a problem"').
function cfbLegendsVerdict(grade, label) {
  var VERDICTS = {
    S: 'this roster doesn’t lose.',
    'A+': 'this squad is a problem.',
    'A-': 'one of the best rosters you can build.',
    'B+': 'so close to perfect, so far.',
    'B-': 'good roster, bad matchup.',
    'C+': 'a bubble team through and through.',
    'C-': 'a middling season, nothing more.',
    'D+': 'a rough year with a few bright spots.',
    D: 'this roster needs a lot more pieces.',
    F: 'an absolute disaster of a draft.'
  };
  return label + ' — ' + (VERDICTS[grade] || '');
}
function finishCfbLegends() {
  var s = state.cfbLegends;
  var picks = CFB_LEGENDS_SLOTS.map(function (slot) { return Object.assign({ slot: slot }, s.slots[slot]); });
  var chem = cfbLegendsCalcChemistry(picks);
  var baseTotal = 0, finalTotal = 0;
  picks.forEach(function (p) {
    var b = chem.bonus[p.name] || 0;
    p.chemistry = b;
    p.finalFppg = p.fppg + b;
    baseTotal += p.fppg;
    finalTotal += p.finalFppg;
  });
  var perfect = cfbLegendsPerfectScore();
  var pct = Math.max(0, Math.min(1, finalTotal / perfect));
  var wins = Math.round(12 * pct);
  var losses = 12 - wins;
  var g = cfbLegendsGrade(pct);
  s.picks = picks;
  s.chemLog = chem.log;
  s.baseTotal = Math.round(baseTotal * 10) / 10;
  s.finalTotal = Math.round(finalTotal * 10) / 10;
  s.perfectScore = Math.round(perfect * 10) / 10;
  s.wins = wins;
  s.losses = losses;
  s.grade = g.grade;
  s.gradeLabel = g.label;
  s.postseasonLabel = cfbLegendsPostseasonLabel(wins);
  s.verdict = cfbLegendsVerdict(g.grade, g.label);
  if (s.ranked !== false) {
    var st = state.stats.cfbLegends;
    st.gamesPlayed++;
    if (wins > st.bestWins || (wins === st.bestWins && finalTotal > st.bestScore)) { st.bestWins = wins; st.bestScore = s.finalTotal; st.bestGrade = g.grade; }
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct * 100);
    s.ratingDelta = lastRatingDelta;
    pushLeaderboard('cfbLegends', { bestWins: st.bestWins, bestRecord: st.bestWins + '-' + (12 - st.bestWins), bestScore: st.bestScore, bestGrade: st.bestGrade, gamesPlayed: st.gamesPlayed });
  }
  completeDailyChallengeFrom('cfbLegends', wins + '-' + losses + ' (' + g.grade + ')', pct * 100);
  h2hSubmitModeResult('cfbLegends', wins, 12);
  playSound(g.grade === 'F' ? 'boo' : 'complete');
}

function renderCfbLegendsSetup() {
  return '<div class="panel">' +
    '<h2 class="panel-title">CFB 12-0</h2>' +
    '<p class="mode-desc">Draft an 8-player college football roster (QB, 2 RB, 2 WR, TE, FLEX, and a whole team DEFENSE) built entirely from real players\' and teams\' real seasons, 1990-2025. Each round rolls a random FBS team-season — pick one player (or that team\'s defense) into an open slot. DEF comes from whatever team gets rolled that round, so you can pair any team\'s defense with an offense drafted from completely different teams. You get 1 team re-roll and 1 year re-roll for the whole draft. After 8 rounds, real fantasy points-per-game plus roster chemistry (teammates, same school, same signing class, iconic duos) decide your final grade and a projected 12-game regular-season record — which then determines your postseason: the College Football Playoff, or a bowl game if you fall short of it.</p>' +
    rankedToggleHtml('cfbLegends') +
    '<button class="btn-primary" data-cfb-legends-start>Start Draft</button>' +
    '</div>';
}
function renderCfbLegendsDraft() {
  var s = state.cfbLegends, entry = s.rolledEntry;
  var html = '<div class="panel">' + modeToolbarHtml('cfbLegends', s.ranked) +
    '<h2 class="panel-title">Round ' + s.round + ' of 8</h2>' +
    '<div class="legends-roll"><b>' + esc(entry.team) + '</b> &middot; ' + entry.year + '</div>' +
    '<div class="legends-slots">' +
    CFB_LEGENDS_SLOTS.map(function (slot) {
      var filled = s.slots[slot];
      return '<div class="legends-slot' + (filled ? ' filled' : '') + '"><div class="legends-slot-name">' + legendsSlotLabel(slot) + '</div>' +
        (filled ? '<div class="legends-slot-player">' + esc(filled.name) + '</div>' : '<div class="legends-slot-empty">open</div>') + '</div>';
    }).join('') +
    '</div>' +
    '<div class="legends-options">' +
    entry.players.map(function (p, i) {
      var alreadyPicked = cfbLegendsPickedNames(s.slots).indexOf(p.name) !== -1;
      var open = !alreadyPicked && cfbLegendsOpenSlotCount(s.slots, p.position) > 0;
      return '<button class="legends-option" ' + (open ? 'data-cfb-legends-pick="' + i + '"' : 'disabled') + '>' +
        '<div class="legends-option-name">' + esc(p.name) + (alreadyPicked ? ' (already drafted)' : '') + '</div>' +
        '<div class="legends-option-meta">' + p.position + ' &middot; ' + p.fppg + ' FPPG</div>' +
        '</button>';
    }).join('') +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" ' + (s.teamRerollUsed ? 'disabled' : 'data-cfb-legends-reroll-team') + '>Re-roll Team' + (s.teamRerollUsed ? ' (used)' : '') + '</button>' +
    '<button class="btn-secondary" ' + (s.yearRerollUsed ? 'disabled' : 'data-cfb-legends-reroll-year') + '>Re-roll Year' + (s.yearRerollUsed ? ' (used)' : '') + '</button>' +
    '</div></div>';
  return html;
}
function renderCfbLegendsResult() {
  var s = state.cfbLegends;
  return '<div class="panel">' +
    '<h2 class="panel-title">Your CFB 12-0 Team</h2>' +
    '<div class="legends-grade">' + esc(s.grade) + '</div>' +
    '<div class="iq-title">' + esc(s.verdict) + '</div>' +
    '<div class="summary-score">Regular season: ' + s.wins + '-' + s.losses + '</div>' +
    '<div class="summary-note">' + esc(s.postseasonLabel) + '</div>' +
    '<div class="summary-note">Base FPPG ' + s.baseTotal + ' + Chemistry = ' + s.finalTotal + ' (perfect-team ceiling: ' + s.perfectScore + ')</div>' +
    '<div class="summary-note">' + (state.name ? 'Saved to the leaderboard as ' + esc(state.name) + '.' : 'Enter a name above to save this to the leaderboard.') + '</div>' +
    '<div class="legends-roster">' +
    s.picks.map(function (p) {
      return '<div class="legends-roster-row"><span class="legends-roster-slot">' + legendsSlotLabel(p.slot) + '</span>' +
        '<span class="legends-roster-player">' + esc(p.name) + ' <i>(' + esc(p.team) + ' ' + p.year + ')</i></span>' +
        '<span class="legends-roster-score">' + p.fppg + (p.chemistry ? ' +' + p.chemistry : '') + ' = ' + Math.round(p.finalFppg * 10) / 10 + '</span></div>';
    }).join('') +
    '</div>' +
    (s.chemLog.length ? '<div class="legends-chem-log"><b>Chemistry:</b>' +
      s.chemLog.map(function (c) { return '<div class="legends-chem-row">' + esc(c.a) + ' + ' + esc(c.b) + ': ' + c.reasons.join(', ') + '</div>'; }).join('') +
      '</div>' : '<div class="legends-chem-log">No chemistry connections this time — a bit of a disconnected roster.</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-cfb-legends-start>Draft Again</button>' +
    '<button class="btn-secondary" data-share="cfbLegends">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderCfbLegendsScreen() {
  if (!state.cfbLegends) return renderCfbLegendsSetup();
  if (state.cfbLegends.screen === 'result') return renderCfbLegendsResult();
  return renderCfbLegendsDraft();
}

/* ============================== head-to-head ==============================
   Async head-to-head: two named players share a short room code (out-of-
   band — text, Discord, whatever) and each plays their own round on their
   own time rather than needing to be online together — whoever's result is
   higher once both have finished wins the match. Deliberately NOT truly
   live/simultaneous — see the project's H2H design notes for why async won
   out. One Firestore doc per match (games/nflTrivia/matches/{code}), read/
   written via window.__fbSync.getMatch/setMatch/watchMatch (firebase-
   sync.js). A head-to-head round always counts toward Football Rating and
   the underlying mode's normal stats, same as a solo round — plus a
   separate win/loss/tie record (state.stats.h2h) specific to head-to-head.

   Every game mode is available (H2H_MODES below). Two kinds:
   - kind: 'quiz' (Quiz/CFB Quiz) — the original design: both players get the
     IDENTICAL seeded question set (seeded from the match code itself, same
     mulberry32/seededShuffle pattern as the Daily Challenge), answered in
     this file's own quiz-style flow (h2hCurrentQuestion/h2hPickAnswer/etc).
   - kind: 'mode' or 'blitz' (everything else — Grid, Blitz, Silhouette,
     Speed, 17-0/12-0) — routes into that mode's own real engine instead of
     a bespoke H2H flow (startH2hIntoMode, mirroring startDailyIntoMode for
     the Daily Challenge), then that mode's own finish function reports back
     via h2hSubmitModeResult. These do NOT get an identical seeded challenge
     the way Quiz does — each player gets that mode's own normal randomness
     (Blitz is the one exception: the match creator picks a specific list,
     stored on the match doc, so both players do face the same list). Fully
     seeding Grid's board / Silhouette's player set / a Legends draft's rolls
     off the match code would make every mode perfectly fair head-to-head,
     but is real additional engineering per mode — this ships full mode
     coverage now; identical-challenge fairness for these is a possible
     later pass, not a blocker to having the mode available at all.
   IQ Test / CFB IQ Test are deliberately NOT included — they already reuse
   the exact same question pool as Quiz/CFB Quiz (so add nothing new to
   challenge a friend with) and their defining trait, no feedback until the
   very end, doesn't fit this file's always-immediate-feedback question flow
   without a second bespoke render path for no real benefit. */
var H2H_MODES = [
  { id: 'quiz', label: 'NFL Quiz', kind: 'quiz', pool: function () { return QUIZ; }, roundSizeOptions: [5, 10, 20], resultSuffix: 'correct' },
  { id: 'cfbQuiz', label: 'CFB Quiz', kind: 'quiz', pool: function () { return CFB; }, roundSizeOptions: [5, 10, 20], resultSuffix: 'correct' },
  { id: 'grid', label: 'NFL Grid', kind: 'mode', resultSuffix: 'squares' },
  { id: 'cfbGrid', label: 'CFB Grid', kind: 'mode', resultSuffix: 'squares' },
  { id: 'blitz', label: 'NFL Blitz', kind: 'blitz', resultSuffix: 'found' },
  { id: 'cfbBlitz', label: 'CFB Blitz', kind: 'blitz', resultSuffix: 'found' },
  { id: 'silhouette', label: 'Silhouette', kind: 'mode', roundSizeOptions: [5, 10], resultSuffix: 'correct' },
  { id: 'speed', label: 'NFL Speed', kind: 'mode', resultSuffix: 'points', usesPoints: true },
  { id: 'cfbSpeed', label: 'CFB Speed', kind: 'mode', resultSuffix: 'points', usesPoints: true },
  { id: 'legends', label: '17-0', kind: 'mode', resultSuffix: 'wins' },
  { id: 'cfbLegends', label: 'CFB 12-0', kind: 'mode', resultSuffix: 'wins' }
];
function h2hModeConfig(id) { return H2H_MODES.find(function (x) { return x.id === id; }); }
function h2hModeLabel(id) {
  var m = h2hModeConfig(id);
  return m ? m.label : id;
}
var H2H_CODE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // no 0/O/1/I/L — easy to read/type aloud
function generateH2HCode() {
  var s = '';
  for (var i = 0; i < 4; i++) s += H2H_CODE_CHARS[Math.floor(Math.random() * H2H_CODE_CHARS.length)];
  return s;
}
function h2hPool(mode) {
  var m = H2H_MODES.find(function (x) { return x.id === mode; });
  return m ? m.pool() : [];
}
function h2hQuestionIds(mode, code, roundSize) {
  var rng = mulberry32(hashStr(code));
  return seededShuffle(h2hPool(mode), rng).slice(0, roundSize).map(function (q) { return q.id; });
}
function h2hCurrentQuestion() {
  var s = state.h2h;
  var id = s.queue[s.index];
  return h2hPool(s.mode).find(function (q) { return q.id === id; });
}
function h2hMyCodes() { return lsGet('nflTriviaH2hCodes', []); }
function h2hRememberCode(code) {
  var list = h2hMyCodes();
  if (list.indexOf(code) === -1) { list.unshift(code); lsSet('nflTriviaH2hCodes', list.slice(0, 20)); }
}
function h2hAlreadyCounted(code) { return h2hMyCounted().indexOf(code) !== -1; }
function h2hMyCounted() { return lsGet('nflTriviaH2hCounted', []); }
function h2hMarkCounted(code) {
  var list = h2hMyCounted();
  if (list.indexOf(code) === -1) { list.push(code); lsSet('nflTriviaH2hCounted', list.slice(-50)); }
}
var h2hUnsub = null;
function h2hStopWatch() { if (h2hUnsub) { h2hUnsub(); h2hUnsub = null; } }
function h2hWatch(code) {
  h2hStopWatch();
  if (window.__fbSync && window.__fbSync.watchMatch) h2hUnsub = window.__fbSync.watchMatch(code, h2hOnMatchUpdate);
}
// Fires on every live update to the watched match doc (opponent joining,
// opponent finishing their round, etc). Auto-advances the lobby to the
// summary screen once both players have a finishedAt, and counts the
// win/loss/tie exactly once per match (h2hMarkCounted guards re-counting on
// a later update or a revisit). Silently skipped while s.screen === 'question'
// so an opponent finishing mid-way through YOUR round can't yank the screen
// out from under you.
function h2hOnMatchUpdate(match) {
  var s = state.h2h;
  if (!s || !match) return;
  s.match = match;
  h2hMaybeCountRecord();
  if (s.screen === 'lobby') {
    var slugs = Object.keys(match.players || {});
    var me = match.players[s.mySlug];
    var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
    var opp = oppSlug ? match.players[oppSlug] : null;
    if (me && me.finishedAt && opp && opp.finishedAt) s.screen = 'summary';
  }
  // Skip the re-render while actively mid-round — either the quiz-kind
  // question flow (state.h2h.screen === 'question') or a non-quiz mode's own
  // screen (state.h2hActive still set, since state.h2h.screen itself just
  // stays 'lobby' the whole time a non-quiz round is being played elsewhere)
  // — so an opponent's update landing at that exact moment can't yank focus
  // off an input or rebuild a board mid-guess out from under the player.
  if (s.screen !== 'question' && !state.h2hActive) renderAll();
}
// Compares two match-player records and returns >0 if `mine` did better,
// <0 if `opp` did, 0 for a tie. Prefers the `points` field (a raw-score
// tiebreak some modes report — see H2H_MODES' usesPoints) when both records
// have one, since plain correctCount/total isn't a fair comparator for a
// timed mode like Speed; falls back to correctCount for every other mode,
// and for any older match doc from before `points` existed.
function h2hCompareRecords(mine, opp) {
  if (mine.points != null && opp.points != null) return mine.points - opp.points;
  return mine.correctCount - opp.correctCount;
}
function h2hMaybeCountRecord() {
  var s = state.h2h, match = s && s.match;
  if (!match || h2hAlreadyCounted(s.code)) return;
  var slugs = Object.keys(match.players || {});
  if (slugs.length !== 2) return;
  var mine = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  if (!mine || !opp || !mine.finishedAt || !opp.finishedAt) return;
  var st = state.stats.h2h;
  st.matchesPlayed++;
  var diff = h2hCompareRecords(mine, opp);
  if (diff > 0) st.wins++;
  else if (diff < 0) st.losses++;
  else st.ties++;
  lsSet('nflTriviaStats', state.stats);
  pushLeaderboard('h2h', { wins: st.wins, losses: st.losses, ties: st.ties, matchesPlayed: st.matchesPlayed });
  h2hMarkCounted(s.code);
}
function h2hBackToMenu() {
  h2hStopWatch();
  state.h2hActive = null;
  state.h2h = { screen: 'menu', mode: 'quiz', roundSize: 10, listId: null, error: null };
  renderAll();
}
function h2hSetRoundSize(n) { state.h2h.roundSize = n; renderAll(); }
// Changing the mode on the create screen resets round-size/list to that
// mode's own defaults, and lazy-loads its data file if the create screen
// needs it up front (Blitz needs BLITZ_LISTS loaded to show list names —
// every other mode's data can still load lazily once the match actually
// starts, same as entering it from the home screen would).
function h2hSetMode(modeId) {
  var s = state.h2h, m = h2hModeConfig(modeId);
  if (!m) return;
  s.mode = modeId;
  s.roundSize = (m.roundSizeOptions && m.roundSizeOptions[0]) || 10;
  s.listId = null;
  if (m.kind === 'blitz') {
    s.loadingCreateData = true;
    renderAll();
    loadModeDataThenRun(modeId, function () {
      s.loadingCreateData = false;
      var lists = modeId === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS;
      s.listId = lists.length ? lists[0].id : null;
      renderAll();
    });
    return;
  }
  renderAll();
}
function h2hSetList(listId) { state.h2h.listId = listId; renderAll(); }
function h2hCreateMatch(mode) {
  var s = state.h2h;
  var code = generateH2HCode();
  var mySlug = slugify(state.name);
  var match = { mode: mode, roundSize: s.roundSize, listId: s.listId || null, status: 'waiting', players: {} };
  match.players[mySlug] = { name: state.name, correctCount: null, total: null, finishedAt: null };
  if (!window.__fbSync || !window.__fbSync.setMatch) return;
  window.__fbSync.setMatch(code, match, false).then(function () {
    h2hRememberCode(code);
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.mode = mode;
    s.screen = 'lobby';
    s.error = null;
    h2hWatch(code);
    renderAll();
  }).catch(function (err) {
    console.error('Create match failed', err);
    s.error = 'Could not create the match — check your connection and try again.';
    renderAll();
  });
}
function h2hJoinMatch(codeInput) {
  var s = state.h2h;
  var code = (codeInput || '').toUpperCase().trim();
  if (!code) return;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match) { s.error = 'No match found with that code.'; renderAll(); return; }
    var slugs = Object.keys(match.players || {});
    if (slugs.indexOf(mySlug) === -1 && slugs.length >= 2) { s.error = 'That match already has two players.'; renderAll(); return; }
    if (slugs.indexOf(mySlug) === -1) {
      match.players[mySlug] = { name: state.name, correctCount: null, total: null, finishedAt: null };
      match.status = 'active';
    }
    window.__fbSync.setMatch(code, match, false).then(function () {
      h2hRememberCode(code);
      s.code = code;
      s.match = match;
      s.mySlug = mySlug;
      s.mode = match.mode;
      s.roundSize = match.roundSize;
      s.listId = match.listId || null;
      s.screen = 'lobby';
      s.error = null;
      h2hWatch(code);
      renderAll();
    });
  }).catch(function (err) {
    console.error('Join match failed', err);
    s.error = 'Could not join — check your connection and try again.';
    renderAll();
  });
}
function h2hOpenExistingCode(code) {
  var s = state.h2h;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match) return;
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.mode = match.mode;
    s.roundSize = match.roundSize;
    s.listId = match.listId || null;
    var slugs = Object.keys(match.players || {});
    var me = match.players[mySlug];
    var oppSlug = slugs.filter(function (sl) { return sl !== mySlug; })[0];
    var opp = oppSlug ? match.players[oppSlug] : null;
    s.screen = (me && me.finishedAt && opp && opp.finishedAt) ? 'summary' : 'lobby';
    h2hWatch(code);
    renderAll();
  });
}
function h2hStartPlaying() {
  var s = state.h2h, m = h2hModeConfig(s.mode);
  h2hStopWatch();
  if (!m || m.kind === 'quiz') {
    s.queue = h2hQuestionIds(s.mode, s.code, s.roundSize);
    s.index = 0;
    s.correctCount = 0;
    s.answeredIndex = null;
    s.screen = 'question';
    renderAll();
    return;
  }
  // Non-quiz mode: hand off to that mode's own real screen/engine (same
  // pattern as the Daily Challenge's startDailyIntoMode) — h2hSubmitModeResult
  // (below) is what brings control back to the 'h2h' screen once that mode's
  // own finish function runs.
  state.h2hActive = { code: s.code, mode: s.mode };
  startH2hIntoMode(s.mode, s.listId, s.roundSize);
}
// Loads the target mode's data if needed, forces it ranked, then starts it
// with whatever config this match agreed on (a specific Blitz list; a
// Silhouette round size; nothing extra for Grid/Speed/Legends).
function startH2hIntoMode(mode, listId, roundSize) {
  loadModeDataThenRun(mode, function () {
    startModeRanked(mode, function () {
      if (mode === 'grid') startGridRound();
      else if (mode === 'cfbGrid') startCfbGridRound();
      else if (mode === 'blitz') startBlitz(listId, 90);
      else if (mode === 'cfbBlitz') startCfbBlitz(listId, 90);
      else if (mode === 'silhouette') startSilhouetteRound(roundSize || 5);
      else if (mode === 'speed') startSpeedRound(60);
      else if (mode === 'cfbSpeed') startCfbSpeedRound(60);
      else if (mode === 'legends') startLegends();
      else if (mode === 'cfbLegends') startCfbLegends();
    });
  }, function () { state.h2hActive = null; });
}
// The non-quiz-kind counterpart to h2hFinishRound above — called from each
// of those modes' own finish functions (finishGridRound, finishBlitzRound,
// etc.) once state.h2hActive confirms this specific round was played as a
// head-to-head match rather than a normal solo one. correctCount/total are
// always the "X out of Y" shown on the lobby/summary screens; points is an
// optional raw-score field (see h2hCompareRecords) for modes — just Speed —
// where a plain ratio doesn't fairly capture who did better.
function h2hSubmitModeResult(modeId, correctCount, total, points) {
  if (!state.h2hActive || state.h2hActive.mode !== modeId) return;
  state.h2hActive = null;
  var s = state.h2h;
  if (!s || !s.code) return;
  var match = s.match || { mode: modeId, status: 'active', players: {} };
  match.players = match.players || {};
  var rec = { name: state.name, correctCount: correctCount, total: total, finishedAt: Date.now() };
  if (points != null) rec.points = points;
  match.players[s.mySlug] = rec;
  var slugs = Object.keys(match.players);
  var allFinished = slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].finishedAt; });
  match.status = allFinished ? 'complete' : 'active';
  s.match = match;
  s.screen = 'summary';
  state.screen = 'h2h';
  if (window.__fbSync && window.__fbSync.setMatch) {
    window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Match result submit failed', err); });
  }
  h2hMaybeCountRecord();
  h2hWatch(s.code);
  renderAll();
}
function h2hPickAnswer(i) {
  var s = state.h2h;
  if (s.answeredIndex !== null) return;
  s.answeredIndex = i;
  var q = h2hCurrentQuestion();
  var isCorrect = q && i === q.correctIndex;
  if (isCorrect) s.correctCount++;
  playSound(isCorrect ? 'correct' : 'wrong');
  renderAll();
}
function h2hNextQuestion() {
  var s = state.h2h;
  if (s.index + 1 >= s.queue.length) { h2hFinishRound(); return; }
  s.index++;
  s.answeredIndex = null;
  renderAll();
}
// Counts like a completely normal solo round for rating + the underlying
// mode's own stats/leaderboard (state.stats.quiz / cfbQuiz) — a head-to-head
// match is still real trivia, not a side mode with its own scoring universe.
// The win/loss/tie record is a separate, additional thing tracked on top
// (see h2hMaybeCountRecord), not instead of the normal stats.
function h2hFinishRound() {
  var s = state.h2h;
  var pct = Math.round(100 * s.correctCount / s.queue.length);
  var st = state.stats[s.mode];
  st.correctTotal += s.correctCount;
  st.questionsTotal += s.queue.length;
  st.roundsPlayed++;
  if (pct > st.bestPct) st.bestPct = pct;
  lsSet('nflTriviaStats', state.stats);
  updateRatingDrift(pct);
  s.ratingDelta = lastRatingDelta;
  pushLeaderboard(s.mode, { bestPct: st.bestPct, correctTotal: st.correctTotal, roundsPlayed: st.roundsPlayed });

  var match = s.match || { mode: s.mode, roundSize: s.roundSize, status: 'active', players: {} };
  match.players = match.players || {};
  match.players[s.mySlug] = { name: state.name, correctCount: s.correctCount, total: s.queue.length, finishedAt: Date.now() };
  var slugs = Object.keys(match.players);
  var allFinished = slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].finishedAt; });
  match.status = allFinished ? 'complete' : 'active';
  s.match = match;
  if (window.__fbSync && window.__fbSync.setMatch) {
    window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Match result submit failed', err); });
  }
  s.screen = 'summary';
  playSound(pct >= 60 ? 'complete' : 'boo');
  h2hMaybeCountRecord();
  h2hWatch(s.code);
  renderAll();
}
function renderH2HMenu() {
  if (!state.name) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('versus') + ' Head-to-Head</h2>' +
      '<p class="mode-desc">Enter a name above, then come back here to challenge a friend.</p>' +
      '</div>';
  }
  var st = state.stats.h2h || {};
  var codes = h2hMyCodes();
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('versus') + ' Head-to-Head</h2>' +
    '<p class="mode-desc">Challenge a specific friend to the same question set and see who scores higher. Your record: ' + (st.wins || 0) + '-' + (st.losses || 0) + (st.ties ? '-' + st.ties : '') + '.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-go-create>Create Match</button>' +
    '<button class="btn-secondary" data-h2h-go-join>Join Match</button>' +
    '</div>' +
    (codes.length ? '<h3 class="mode-section-title" style="margin-top:20px;">Your matches</h3><div class="h2h-recent-list">' +
      codes.slice(0, 8).map(function (c) { return '<button class="btn-tiny" data-h2h-open-code="' + esc(c) + '">' + esc(c) + '</button>'; }).join('') +
      '</div>' : '') +
    '</div>';
}
function renderH2HCreate() {
  var s = state.h2h, m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var configHtml = '';
  if (m.kind === 'blitz') {
    if (s.loadingCreateData) {
      configHtml = '<p class="mode-desc">Loading lists…</p>';
    } else {
      var lists = s.mode === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS;
      configHtml = '<div class="field-row"><label>List<select id="h2h-list">' +
        lists.map(function (l) { return '<option value="' + esc(l.id) + '"' + (s.listId === l.id ? ' selected' : '') + '>' + esc(l.title) + '</option>'; }).join('') +
        '</select></label></div>';
    }
  } else if (m.roundSizeOptions) {
    configHtml = '<div class="chip-row">' +
      m.roundSizeOptions.map(function (n) { return '<button class="chip-toggle' + (s.roundSize === n ? ' active' : '') + '" data-h2h-roundsize="' + n + '">' + n + (m.kind === 'quiz' ? ' questions' : ' players') + '</button>'; }).join('') +
      '</div>';
  } else {
    configHtml = '<p class="mode-desc">No extra setup — both of you play a normal round of ' + esc(m.label) + '.</p>';
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Create a Match</h2>' +
    '<div class="field-row"><label>Mode<select id="h2h-mode">' +
    H2H_MODES.map(function (mm) { return '<option value="' + mm.id + '"' + (s.mode === mm.id ? ' selected' : '') + '>' + esc(mm.label) + '</option>'; }).join('') +
    '</select></label></div>' +
    configHtml +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-create' + (m.kind === 'blitz' && !s.listId ? ' disabled' : '') + '>Create &amp; Get Code</button>' +
    '</div>';
}
function renderH2HJoin() {
  var s = state.h2h;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Join a Match</h2>' +
    '<div class="field-row"><label>Match code<input id="h2h-code-input" maxlength="4" placeholder="e.g. 7F3K" autocomplete="off" autocapitalize="characters" style="text-transform:uppercase;" /></label></div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-join>Join</button>' +
    '</div>';
}
function renderH2HLobby() {
  var s = state.h2h, match = s.match || { players: {} };
  var m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var slugs = Object.keys(match.players || {});
  var me = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  var myDone = !!(me && me.finishedAt);
  var setupNote = m.kind === 'quiz' ? s.roundSize + ' questions, the exact same set for both of you.' :
    m.kind === 'blitz' ? 'Same list for both of you — ' + esc((s.mode === 'blitz' ? BLITZ_LISTS : CFB_BLITZ_LISTS).find(function (l) { return l.id === s.listId; }).title) + '.' :
    'Both of you play a normal round of ' + esc(m.label) + ' — whoever’s result is higher wins.';
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Head-to-Head &middot; ' + esc(h2hModeLabel(s.mode)) + '</h2>' +
    '<div class="h2h-code">' + esc(s.code) + '</div>' +
    '<p class="mode-desc">Share this code with whoever you’re playing — ' + setupNote + '</p>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + (myDone ? me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix : 'Not played yet') + '</span></div>' +
    '<div class="h2h-player-row"><span>' + (opp ? esc(opp.name) : 'Waiting for opponent to join…') + '</span><span>' + (opp && opp.finishedAt ? opp.correctCount + ' / ' + opp.total + ' ' + m.resultSuffix : opp ? 'Not played yet' : '') + '</span></div>' +
    '</div>' +
    (myDone
      ? '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + ' to finish…</p>'
      : '<button class="btn-primary" data-h2h-start-play>Start Playing</button>') +
    '</div>';
}
function renderH2HQuestion() {
  var s = state.h2h, q = h2hCurrentQuestion();
  var answered = s.answeredIndex !== null;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-exit>' + icon('close') + ' Exit to Home</button></div>' +
    '<div class="quiz-progress">Head-to-Head &middot; Question ' + (s.index + 1) + ' of ' + s.queue.length + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (answered) {
        if (i === q.correctIndex) cls += ' correct';
        else if (i === s.answeredIndex) cls += ' wrong';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-h2h-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (answered
      ? '<div class="quiz-feedback" aria-live="polite">' + (s.answeredIndex === q.correctIndex ? '<span class="feedback-good">' + icon('check') + ' Correct!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Incorrect.</span>') + (q.notes ? ' ' + esc(q.notes) : '') + '</div>' +
        '<button class="btn-primary" data-h2h-next>' + (s.index + 1 >= s.queue.length ? 'See Results' : 'Next Question') + '</button>'
      : '') +
    '</div>';
}
function renderH2HSummary() {
  var s = state.h2h, match = s.match || { players: {} };
  var m = h2hModeConfig(s.mode) || H2H_MODES[0];
  var slugs = Object.keys(match.players || {});
  var me = match.players[s.mySlug];
  var oppSlug = slugs.filter(function (sl) { return sl !== s.mySlug; })[0];
  var opp = oppSlug ? match.players[oppSlug] : null;
  var oppDone = !!(opp && opp.finishedAt);
  var diff = oppDone ? h2hCompareRecords(me, opp) : 0;
  var result = oppDone ? (diff > 0 ? 'win' : diff < 0 ? 'loss' : 'tie') : null;
  return '<div class="panel">' +
    '<h2 class="panel-title">Head-to-Head Result</h2>' +
    (!oppDone
      ? '<div class="summary-score">You scored ' + me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix + '</div>' +
        '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + ' to finish — check back later, or share the code again if they haven’t joined yet: <b>' + esc(s.code) + '</b></p>'
      : '<div class="h2h-result-banner h2h-result-' + result + '">' + (result === 'win' ? icon('trophy') + ' You Won!' : result === 'loss' ? 'You Lost' : 'Tie Game') + '</div>' +
        '<div class="h2h-players">' +
        '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + me.correctCount + ' / ' + me.total + ' ' + m.resultSuffix + '</span></div>' +
        '<div class="h2h-player-row"><span>' + esc(opp.name) + '</span><span>' + opp.correctCount + ' / ' + opp.total + ' ' + m.resultSuffix + '</span></div>' +
        '</div>') +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-back-menu>New Match</button>' +
    '<button class="btn-secondary" data-share="h2h">' + icon('share') + ' Share</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderH2HScreen() {
  if (!state.h2h) state.h2h = { screen: 'menu', mode: 'quiz', roundSize: 10, listId: null, error: null };
  var s = state.h2h;
  if (s.screen === 'create') return renderH2HCreate();
  if (s.screen === 'join') return renderH2HJoin();
  if (s.screen === 'lobby') return renderH2HLobby();
  if (s.screen === 'question') return renderH2HQuestion();
  if (s.screen === 'summary') return renderH2HSummary();
  return renderH2HMenu();
}

/* ============================== live head-to-head ==============================
   A second, separate H2H flow — the async version above is deliberately NOT
   simultaneous (see its own header comment for why). This one is: two
   players see the same question at the same moment and each other's result
   the instant both have answered. Scoped to kind:'quiz' H2H_MODES only (NFL
   Quiz / CFB Quiz) — those are the only modes with a discrete per-question
   flow that a live sync point actually fits; Grid/Blitz/Silhouette/Speed/
   Legends each run their own full-screen engine with no natural place to
   hook a live opponent-status check.

   There's no server/Cloud Function anywhere in this app, so nothing has
   sole authority over when the match advances to the next question — both
   clients independently watch the same Firestore match doc (same matches
   collection, same getMatch/setMatch/watchMatch bridge the async version
   uses, just tagged live:true) and derive the same next state from it.
   Whichever client gets there first writes the next index (or 'finished');
   the other, redundant write that follows is harmless — same "plain reads/
   writes, no transaction, fine at this app's scale" tradeoff firebase-
   sync.js already documents for matches in general. A per-question local
   timer (LIVE_QUESTION_SECONDS) keeps a round from ever stalling forever:
   on timeout, a client submits its own still-blank answer as "no pick" and
   also fills in a placeholder for the OPPONENT if theirs never arrived —
   covers a closed/backgrounded opponent tab, since nobody else could ever
   submit on their behalf otherwise. */
var H2H_LIVE_MODES = H2H_MODES.filter(function (m) { return m.kind === 'quiz'; });
var LIVE_QUESTION_SECONDS = 15;
var LIVE_REVEAL_MS = 2500;
var h2hLiveUnsub = null;
var h2hLiveTimerId = null;
var h2hLiveAdvanceScheduled = -1; // guards this client scheduling the same index's advance twice
function h2hLiveClearTimer() { if (h2hLiveTimerId) { clearTimeout(h2hLiveTimerId); h2hLiveTimerId = null; } }
function h2hLiveStopWatch() { if (h2hLiveUnsub) { h2hLiveUnsub(); h2hLiveUnsub = null; } h2hLiveClearTimer(); }
function h2hLiveWatch(code) {
  h2hLiveStopWatch();
  if (window.__fbSync && window.__fbSync.watchMatch) h2hLiveUnsub = window.__fbSync.watchMatch(code, h2hLiveOnMatchUpdate);
}
function h2hLiveInviteLink(code) { return SITE_URL + '#live=' + code; }
function h2hLiveOpponentSlug(match, mySlug) {
  var slugs = Object.keys(match.players || {});
  return slugs.filter(function (sl) { return sl !== mySlug; })[0] || null;
}
function h2hLiveBackToMenu() {
  h2hLiveStopWatch();
  h2hLiveAdvanceScheduled = -1;
  state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  renderAll();
}
function h2hLiveSetMode(modeId) {
  var s = state.h2hLive, m = h2hModeConfig(modeId);
  if (!s || !m || m.kind !== 'quiz') return;
  s.mode = modeId;
  s.roundSize = (m.roundSizeOptions && m.roundSizeOptions[0]) || 10;
  renderAll();
}
function h2hLiveSetRoundSize(n) { state.h2hLive.roundSize = n; renderAll(); }
function h2hLiveCreateMatch() {
  var s = state.h2hLive;
  var code = generateH2HCode();
  var mySlug = slugify(state.name);
  var match = { live: true, mode: s.mode, roundSize: s.roundSize, status: 'waiting', index: 0, players: {}, answers: {} };
  match.players[mySlug] = { name: state.name, ready: false };
  match.answers[mySlug] = {};
  if (!window.__fbSync || !window.__fbSync.setMatch) return;
  window.__fbSync.setMatch(code, match, false).then(function () {
    h2hRememberCode(code); // shares the async version's "your recent matches" list — live/async codes side by side is fine, both are just match docs
    s.code = code;
    s.match = match;
    s.mySlug = mySlug;
    s.screen = 'lobby';
    s.error = null;
    h2hLiveWatch(code);
    renderAll();
  }).catch(function (err) {
    console.error('Create live match failed', err);
    s.error = 'Could not create the match — check your connection and try again.';
    renderAll();
  });
}
function h2hLiveJoinMatch(codeInput) {
  var s = state.h2hLive;
  var code = (codeInput || '').toUpperCase().trim();
  if (!code) return;
  var mySlug = slugify(state.name);
  if (!window.__fbSync || !window.__fbSync.getMatch) return;
  window.__fbSync.getMatch(code).then(function (match) {
    if (!match || !match.live) { s.error = 'No live match found with that code.'; s.screen = 'join'; renderAll(); return; }
    var slugs = Object.keys(match.players || {});
    if (slugs.indexOf(mySlug) === -1 && slugs.length >= 2) { s.error = 'That match already has two players.'; s.screen = 'join'; renderAll(); return; }
    if (slugs.indexOf(mySlug) === -1) {
      match.players[mySlug] = { name: state.name, ready: false };
      match.answers = match.answers || {};
      match.answers[mySlug] = {};
    }
    window.__fbSync.setMatch(code, match, false).then(function () {
      h2hRememberCode(code);
      s.code = code;
      s.match = match;
      s.mySlug = mySlug;
      s.mode = match.mode;
      s.roundSize = match.roundSize;
      s.screen = 'lobby';
      s.error = null;
      h2hLiveWatch(code);
      renderAll();
    });
  }).catch(function (err) {
    console.error('Join live match failed', err);
    s.error = 'Could not join — check your connection and try again.';
    s.screen = 'join';
    renderAll();
  });
}
function h2hLiveSetReady() {
  var s = state.h2hLive, match = s.match;
  if (!match || !match.players[s.mySlug]) return;
  match.players[s.mySlug].ready = true;
  s.match = match;
  window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Ready-up failed', err); });
  renderAll();
}
function h2hLiveQueue(s) { return h2hQuestionIds(s.mode, s.code, s.roundSize); }
function h2hLiveCurrentQuestion(s) {
  var queue = h2hLiveQueue(s);
  var id = queue[s.match.index];
  return h2hPool(s.mode).find(function (q) { return q.id === id; });
}
function h2hLiveScore(match, slug) {
  var a = (match.answers && match.answers[slug]) || {};
  var correct = 0, total = 0;
  Object.keys(a).forEach(function (k) { total++; if (a[k].correct) correct++; });
  return { correct: correct, total: total };
}
function h2hLivePickAnswer(i) {
  var s = state.h2hLive, match = s.match;
  if (!match) return;
  var idx = match.index;
  match.answers = match.answers || {};
  match.answers[s.mySlug] = match.answers[s.mySlug] || {};
  if (match.answers[s.mySlug][idx] !== undefined) return;
  var q = h2hLiveCurrentQuestion(s);
  var correct = !!(q && i === q.correctIndex);
  match.answers[s.mySlug][idx] = { choice: i, correct: correct };
  s.match = match;
  playSound(correct ? 'correct' : 'wrong');
  h2hLiveClearTimer();
  window.__fbSync.setMatch(s.code, match, true).catch(function (err) { console.error('Live answer submit failed', err); });
  renderAll();
}
// One local timer per question, (re)started the moment that question
// becomes current (see h2hLiveOnMatchUpdate) — fires LIVE_QUESTION_SECONDS
// later and force-fills any still-missing answer (mine and/or the
// opponent's) so a slow or vanished opponent can never stall the round.
function h2hLiveStartQuestionTimer() {
  h2hLiveClearTimer();
  var s = state.h2hLive;
  var code = s.code, idx = s.match.index;
  h2hLiveTimerId = setTimeout(function () {
    var cs = state.h2hLive;
    if (!cs || cs.code !== code || !cs.match || cs.match.index !== idx) return;
    var match = cs.match;
    match.answers = match.answers || {};
    var oppSlug = h2hLiveOpponentSlug(match, cs.mySlug);
    var changed = false;
    match.answers[cs.mySlug] = match.answers[cs.mySlug] || {};
    if (match.answers[cs.mySlug][idx] === undefined) { match.answers[cs.mySlug][idx] = { choice: -1, correct: false }; changed = true; }
    if (oppSlug) {
      match.answers[oppSlug] = match.answers[oppSlug] || {};
      if (match.answers[oppSlug][idx] === undefined) { match.answers[oppSlug][idx] = { choice: -1, correct: false }; changed = true; }
    }
    cs.match = match;
    renderAll();
    if (changed) window.__fbSync.setMatch(code, match, true).catch(function (err) { console.error('Live timeout submit failed', err); });
  }, LIVE_QUESTION_SECONDS * 1000);
}
// Runs on every client once both players have answered the current
// question — schedules (once per index, per client) the write that moves
// the match to the next question after a short reveal pause. Both clients
// do this independently and land on the identical next value, so the
// redundant second write is a harmless no-op rather than a conflict.
function h2hLiveMaybeScheduleAdvance() {
  var s = state.h2hLive, match = s.match;
  if (!match || match.status === 'finished') return;
  var idx = match.index;
  if (h2hLiveAdvanceScheduled === idx) return;
  var slugs = Object.keys(match.players || {});
  if (slugs.length !== 2) return;
  var bothAnswered = slugs.every(function (sl) { return match.answers && match.answers[sl] && match.answers[sl][idx] !== undefined; });
  if (!bothAnswered) return;
  h2hLiveAdvanceScheduled = idx;
  var code = s.code;
  setTimeout(function () {
    var cs = state.h2hLive;
    if (!cs || cs.code !== code || !cs.match || cs.match.index !== idx) return; // stale — already moved on
    var m = cs.match;
    var queue = h2hLiveQueue(cs);
    if (idx + 1 >= queue.length) m.status = 'finished';
    else m.index = idx + 1;
    cs.match = m;
    window.__fbSync.setMatch(code, m, true).catch(function (err) { console.error('Live advance failed', err); });
  }, LIVE_REVEAL_MS);
}
function h2hLiveMaybeCountRecord() {
  var s = state.h2hLive, match = s && s.match;
  if (!match || match.status !== 'finished' || h2hAlreadyCounted(s.code)) return;
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  if (!oppSlug) return;
  var mine = h2hLiveScore(match, s.mySlug), opp = h2hLiveScore(match, oppSlug);
  var st = state.stats.h2h;
  st.matchesPlayed++;
  var diff = mine.correct - opp.correct;
  if (diff > 0) st.wins++;
  else if (diff < 0) st.losses++;
  else st.ties++;
  lsSet('nflTriviaStats', state.stats);
  pushLeaderboard('h2h', { wins: st.wins, losses: st.losses, ties: st.ties, matchesPlayed: st.matchesPlayed });
  h2hMarkCounted(s.code);
  // Counts toward the underlying mode's own stats/rating too, same as a
  // normal solo round — mirrors h2hFinishRound's identical reasoning above.
  if (mine.total > 0) {
    var pct = Math.round(100 * mine.correct / mine.total);
    var modeSt = state.stats[s.mode];
    modeSt.correctTotal += mine.correct;
    modeSt.questionsTotal += mine.total;
    modeSt.roundsPlayed++;
    if (pct > modeSt.bestPct) modeSt.bestPct = pct;
    lsSet('nflTriviaStats', state.stats);
    updateRatingDrift(pct);
    pushLeaderboard(s.mode, { bestPct: modeSt.bestPct, correctTotal: modeSt.correctTotal, roundsPlayed: modeSt.roundsPlayed });
  }
}
function h2hLiveOnMatchUpdate(match) {
  var s = state.h2hLive;
  if (!s || !match) return;
  var prevIndex = s.match ? s.match.index : -1;
  var prevStatus = s.match ? s.match.status : null;
  s.match = match;
  if (s.screen === 'lobby') {
    var slugs = Object.keys(match.players || {});
    if (slugs.length === 2 && slugs.every(function (sl) { return match.players[sl].ready; })) {
      if (match.status !== 'active') {
        match.status = 'active';
        window.__fbSync.setMatch(s.code, match, true).catch(function () {});
      }
      s.screen = 'playing';
    }
  }
  if (s.screen === 'playing') {
    if (match.status === 'finished') {
      h2hLiveClearTimer();
      s.screen = 'summary';
      h2hLiveMaybeCountRecord();
    } else {
      if (match.index !== prevIndex || prevStatus !== 'active') { h2hLiveAdvanceScheduled = -1; h2hLiveStartQuestionTimer(); }
      h2hLiveMaybeScheduleAdvance();
    }
  }
  renderAll();
}
function h2hLiveShareLink(link, btn) {
  if (navigator.share) { navigator.share({ title: 'Reads — Live Match', text: 'Join my live trivia match on Reads:', url: link }).catch(function () {}); return; }
  copyTextToClipboard(link, btn);
}
function h2hLiveCardHtml() {
  return '<button class="continue-card h2h-live-card" data-go="h2hLive">' +
    '<span class="continue-card-label">Both online now &middot; real-time</span>' +
    '<span class="continue-card-mode">' + icon('versus') + ' Live Match</span>' +
    '</button>';
}
function renderH2HLiveMenu() {
  if (!state.name) {
    return '<div class="panel">' +
      '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
      '<h2 class="panel-title">' + icon('versus') + ' Live Match</h2>' +
      '<p class="mode-desc">Enter a name above, then come back here to start a live match.</p>' +
      '</div>';
  }
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('versus') + ' Live Match</h2>' +
    '<p class="mode-desc">Both of you answer the same questions at the same time and see each other’s results the instant you’re both done — needs you both online right now. For playing on your own schedule, use Head-to-Head from Home instead.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-live-go-create>Create Match</button>' +
    '<button class="btn-secondary" data-h2h-live-go-join>Join Match</button>' +
    '</div>' +
    '</div>';
}
function renderH2HLiveCreate() {
  var s = state.h2hLive, m = h2hModeConfig(s.mode) || H2H_LIVE_MODES[0];
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Create a Live Match</h2>' +
    '<div class="field-row"><label>Mode<select id="h2h-live-mode">' +
    H2H_LIVE_MODES.map(function (mm) { return '<option value="' + mm.id + '"' + (s.mode === mm.id ? ' selected' : '') + '>' + esc(mm.label) + '</option>'; }).join('') +
    '</select></label></div>' +
    '<div class="chip-row">' +
    m.roundSizeOptions.map(function (n) { return '<button class="chip-toggle' + (s.roundSize === n ? ' active' : '') + '" data-h2h-live-roundsize="' + n + '">' + n + ' questions</button>'; }).join('') +
    '</div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-live-create>Create &amp; Get Code</button>' +
    '</div>';
}
function renderH2HLiveJoin() {
  var s = state.h2hLive;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Join a Live Match</h2>' +
    '<div class="field-row"><label>Match code<input id="h2h-live-code-input" maxlength="4" placeholder="e.g. 7F3K" autocomplete="off" autocapitalize="characters" style="text-transform:uppercase;" /></label></div>' +
    (s.error ? '<p class="mode-desc h2h-error" role="alert">' + esc(s.error) + '</p>' : '') +
    '<button class="btn-primary" data-h2h-live-join>Join</button>' +
    '</div>';
}
function renderH2HLiveLobby() {
  var s = state.h2hLive, match = s.match || { players: {} };
  var me = match.players[s.mySlug];
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var link = h2hLiveInviteLink(s.code);
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-back-menu>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">Live Match &middot; ' + esc(h2hModeLabel(s.mode)) + '</h2>' +
    '<div class="h2h-code">' + esc(s.code) + '</div>' +
    '<p class="mode-desc">Send this link to whoever you’re playing — one tap and they’re in.</p>' +
    '<div class="btn-row"><button class="btn-secondary" data-h2h-live-share-link="' + esc(link) + '">' + icon('share') + ' Share Invite Link</button></div>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + (me && me.ready ? icon('check') + ' Ready' : 'Not ready') + '</span></div>' +
    '<div class="h2h-player-row"><span>' + (opp ? esc(opp.name) : 'Waiting for opponent to join…') + '</span><span>' + (opp ? (opp.ready ? icon('check') + ' Ready' : 'Not ready') : '') + '</span></div>' +
    '</div>' +
    (opp && me && !me.ready ? '<button class="btn-primary" data-h2h-live-ready>I’m Ready</button>' :
      me && me.ready ? '<p class="mode-desc">Waiting on ' + (opp ? esc(opp.name) : 'your opponent') + '…</p>' : '') +
    '</div>';
}
function renderH2HLivePlaying() {
  var s = state.h2hLive, match = s.match;
  if (!match) return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading…</div></div>';
  var idx = match.index;
  var q = h2hLiveCurrentQuestion(s);
  if (!q) return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading…</div></div>';
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var myAnswer = match.answers && match.answers[s.mySlug] && match.answers[s.mySlug][idx];
  var oppAnswer = oppSlug && match.answers && match.answers[oppSlug] && match.answers[oppSlug][idx];
  var answered = myAnswer !== undefined;
  var revealed = answered && oppAnswer !== undefined;
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-h2h-live-exit>' + icon('close') + ' Exit to Home</button></div>' +
    '<div class="quiz-progress">Live &middot; Question ' + (idx + 1) + ' of ' + s.roundSize + '</div>' +
    '<div class="quiz-question">' + esc(q.question) + '</div>' +
    '<div class="quiz-options">' +
    q.options.map(function (opt, i) {
      var cls = 'quiz-option';
      if (revealed) {
        if (i === q.correctIndex) cls += ' correct';
        else if (myAnswer.choice === i) cls += ' wrong';
      } else if (answered && myAnswer.choice === i) {
        cls += ' selected';
      }
      return '<button class="' + cls + '" ' + (answered ? 'disabled' : 'data-h2h-live-answer="' + i + '"') + '>' +
        String.fromCharCode(65 + i) + '. ' + esc(opt) + '</button>';
    }).join('') +
    '</div>' +
    (revealed
      ? '<div class="quiz-feedback" aria-live="polite">' + (myAnswer.correct ? '<span class="feedback-good">' + icon('check') + ' You got it!</span>' : '<span class="feedback-bad">' + icon('xMark') + ' Missed it.</span>') +
        ' ' + esc(opp ? opp.name : 'Opponent') + (oppAnswer.correct ? ' got it too.' : ' missed it.') + '</div>'
      : answered
      ? '<p class="mode-desc" aria-live="polite">Waiting on ' + esc(opp ? opp.name : 'your opponent') + '…</p>'
      : '') +
    '</div>';
}
function renderH2HLiveSummary() {
  var s = state.h2hLive, match = s.match || { players: {} };
  var oppSlug = h2hLiveOpponentSlug(match, s.mySlug);
  var opp = oppSlug ? match.players[oppSlug] : null;
  var mine = h2hLiveScore(match, s.mySlug);
  var oppScore = oppSlug ? h2hLiveScore(match, oppSlug) : { correct: 0, total: 0 };
  var diff = mine.correct - oppScore.correct;
  var result = diff > 0 ? 'win' : diff < 0 ? 'loss' : 'tie';
  return '<div class="panel">' +
    '<h2 class="panel-title">Live Match Result</h2>' +
    '<div class="h2h-result-banner h2h-result-' + result + '">' + (result === 'win' ? icon('trophy') + ' You Won!' : result === 'loss' ? 'You Lost' : 'Tie Game') + '</div>' +
    '<div class="h2h-players">' +
    '<div class="h2h-player-row"><span>' + esc(state.name) + ' (you)</span><span>' + mine.correct + ' / ' + mine.total + ' correct</span></div>' +
    '<div class="h2h-player-row"><span>' + esc(opp ? opp.name : 'Opponent') + '</span><span>' + oppScore.correct + ' / ' + oppScore.total + ' correct</span></div>' +
    '</div>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-h2h-live-back-menu>New Match</button>' +
    '<button class="btn-secondary" data-go="home">Home</button>' +
    '</div></div>';
}
function renderH2HLiveScreen() {
  if (!state.h2hLive) state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  var s = state.h2hLive;
  if (s.screen === 'create') return renderH2HLiveCreate();
  if (s.screen === 'join') return renderH2HLiveJoin();
  if (s.screen === 'lobby') return renderH2HLiveLobby();
  if (s.screen === 'playing') return renderH2HLivePlaying();
  if (s.screen === 'summary') return renderH2HLiveSummary();
  return renderH2HLiveMenu();
}

/* ============================== share cards ==============================
   One shared card-render + share pipeline for every mode's result screen,
   rather than 14 bespoke ones. Renders an offscreen canvas (text/shapes
   only, no image assets drawn onto it — so this has zero cross-origin/
   canvas-tainting risk and, unlike Firebase sync or the service worker,
   works even over file://) and hands it to the OS's native share sheet via
   the Web Share API where supported (the only path that gives Instagram a
   real, working target — Instagram has no web share-intent of its own).
   Falls back to a small modal (download / share-to-X / share-app-to-
   Facebook) on desktop/unsupported browsers. */
// Formats how much this round moved the Football Rating, for both the
// canvas card and the share text — '' (omitted entirely) for Practice
// rounds or anyone without a rating yet, since ratingDelta is only ever set
// by updateRatingDrift() actually running (see the finish* functions).
function shareRatingLine(delta) {
  if (delta == null) return '';
  var r = getRating();
  if (!r) return '';
  return '🏈 Rating ' + (delta > 0 ? '+' : '') + delta + ' (now ' + r.score + ')';
}
function shareConfigFor(mode) {
  if (mode === 'quiz' || mode === 'cfbQuiz') {
    var t = state[mode];
    var pct = Math.round(100 * t.correctCount / t.queue.length);
    var label = mode === 'quiz' ? 'NFL Quiz' : 'CFB Quiz';
    var rl = shareRatingLine(t.ratingDelta);
    return { title: label, headline: pct + '%', sub: t.correctCount + ' / ' + t.queue.length + ' correct', detail: rl,
      shareText: 'I scored ' + pct + '% on ' + label + ' in Reads! 🏈' + (rl ? ' ' + rl : '') };
  }
  if (mode === 'daily') {
    var d = state.daily;
    var pct2 = Math.round(100 * d.correctCount / d.queue.length);
    var streakN = getStreak().count;
    var streakBit = streakN ? ('🔥 ' + streakN + '-day streak') : '';
    var rlD = shareRatingLine(d.ratingDelta);
    return { title: 'Daily Challenge', headline: pct2 + '%', sub: d.correctCount + ' / ' + d.queue.length + ' correct', detail: [streakBit, rlD].filter(Boolean).join(' · '),
      shareText: 'I scored ' + pct2 + '% on today’s Daily Challenge in Reads!' + (streakBit ? ' ' + streakBit : '') + (rlD ? ' ' + rlD : '') };
  }
  if (mode === 'grid' || mode === 'cfbGrid') {
    var g = state[mode];
    var correctCells = g.cells.filter(function (c) { return c.correct; }).length;
    var label2 = mode === 'grid' ? 'NFL Grid' : 'CFB Grid';
    var rlG = shareRatingLine(g.ratingDelta);
    var sweepBit = correctCells === 9 ? 'Clean sweep!' : '';
    return { title: label2, headline: correctCells + '/9', sub: g.totalScore + ' points', detail: [sweepBit, rlG].filter(Boolean).join(' · '),
      shareText: 'I got ' + correctCells + '/9 on the ' + label2 + ' in Reads (' + g.totalScore + ' pts)!' + (rlG ? ' ' + rlG : '') };
  }
  if (mode === 'blitz' || mode === 'cfbBlitz') {
    var b = state[mode], total = b.list.answers.length;
    var label3 = mode === 'blitz' ? 'NFL Blitz' : 'CFB Blitz';
    var rlB = shareRatingLine(b.ratingDelta);
    var bSweepBit = b.matched.length === total ? 'Clean sweep!' : '';
    return { title: label3, headline: b.matched.length + '/' + total, sub: b.list.title, detail: [bSweepBit, rlB].filter(Boolean).join(' · '),
      shareText: 'I found ' + b.matched.length + '/' + total + ' on "' + b.list.title + '" in Reads ' + label3 + '!' + (rlB ? ' ' + rlB : '') };
  }
  if (mode === 'speed' || mode === 'cfbSpeed') {
    var s = state[mode];
    var label4 = mode === 'speed' ? 'NFL Speed' : 'CFB Speed';
    var rlS = shareRatingLine(s.ratingDelta);
    return { title: label4, headline: s.score + ' pts', sub: s.correctCount + ' / ' + s.totalCount + ' correct', detail: ['Best streak: ' + s.bestStreak, rlS].filter(Boolean).join(' · '),
      shareText: 'I scored ' + s.score + ' points on ' + label4 + ' in Reads! Best streak: ' + s.bestStreak + (rlS ? ' ' + rlS : '') };
  }
  if (mode === 'silhouette') {
    var sil = state.silhouette;
    var silCorrectCount = sil.results.filter(function (r) { return r.correct; }).length;
    var rlSil = shareRatingLine(sil.ratingDelta);
    return { title: 'NFL Silhouette', headline: sil.score + ' pts', sub: silCorrectCount + ' / ' + sil.queue.length + ' guessed', detail: rlSil,
      shareText: 'I scored ' + sil.score + ' points on NFL Silhouette in Reads!' + (rlSil ? ' ' + rlSil : '') };
  }
  if (mode === 'higherLower') {
    var hl = state.higherLower;
    var rlHl = shareRatingLine(hl.ratingDelta);
    return { title: 'Higher or Lower', headline: String(hl.streak), sub: hl.streak === 1 ? 'player' : 'players', detail: rlHl,
      shareText: 'I built a ' + hl.streak + '-player streak on Higher or Lower in Reads! Can you beat it?' + (rlHl ? ' ' + rlHl : '') };
  }
  if (mode === 'iq' || mode === 'cfbIq') {
    var iq = state[mode];
    var label5 = mode === 'iq' ? 'Football IQ Test' : 'College Football IQ Test';
    var titleFn = mode === 'iq' ? iqTitle : cfbIqTitle;
    var rlIq = shareRatingLine(iq.ratingDelta);
    return { title: label5, headline: String(iq.iqScore), sub: titleFn(iq.iqScore), detail: [iq.correct + ' / ' + iq.total + ' correct', rlIq].filter(Boolean).join(' · '),
      shareText: 'My ' + label5 + ' score in Reads: ' + iq.iqScore + ' (' + titleFn(iq.iqScore) + ')' + (rlIq ? ' ' + rlIq : '') };
  }
  if (mode === 'legends' || mode === 'cfbLegends') {
    var l = state[mode];
    var label6 = mode === 'legends' ? '17-0' : 'CFB 12-0';
    var rlL = shareRatingLine(l.ratingDelta);
    var recordLabel6 = mode === 'cfbLegends' ? 'Regular season' : 'Projected record';
    var postseasonBit6 = mode === 'cfbLegends' ? l.postseasonLabel : '';
    return { title: label6, headline: l.grade, sub: l.gradeLabel, detail: [recordLabel6 + ': ' + l.wins + '-' + l.losses, postseasonBit6, rlL].filter(Boolean).join(' · '),
      shareText: 'My ' + label6 + ' team graded out ' + l.grade + ' (' + l.gradeLabel + ') in Reads! ' + recordLabel6 + ' ' + l.wins + '-' + l.losses + (postseasonBit6 ? ' — ' + postseasonBit6 : '') + (rlL ? ' ' + rlL : '') };
  }
  if (mode === 'h2h') {
    var h = state.h2h, hMatch = h.match || { players: {} };
    var hSlugs = Object.keys(hMatch.players || {});
    var hMe = hMatch.players[h.mySlug] || { correctCount: h.correctCount, total: h.queue.length };
    var hOppSlug = hSlugs.filter(function (sl) { return sl !== h.mySlug; })[0];
    var hOpp = hOppSlug ? hMatch.players[hOppSlug] : null;
    var hOppDone = !!(hOpp && hOpp.finishedAt);
    var hRl = shareRatingLine(h.ratingDelta);
    var hResult = !hOppDone ? '' : (hMe.correctCount > hOpp.correctCount ? 'Won' : hMe.correctCount < hOpp.correctCount ? 'Lost' : 'Tied') + ' vs ' + hOpp.name;
    return { title: 'Head-to-Head', headline: hMe.correctCount + '/' + hMe.total, sub: hResult || 'Waiting on opponent', detail: hRl,
      shareText: 'Head-to-Head in Reads: ' + hMe.correctCount + '/' + hMe.total + (hResult ? ' — ' + hResult : '') + '!' + (hRl ? ' ' + hRl : '') };
  }
  return null;
}
// Strokes one of the app's own SVG icons (ICON_PATHS) onto a canvas 2D
// context — extracts each <path d="..."> from the markup string and draws
// it via Path2D, so the share card uses the literal same trophy/etc glyph
// as the rest of the UI instead of a separately-drawn one-off. (x, y) is
// the icon's top-left in canvas space; size is the rendered width/height —
// ICON_PATHS is authored on a 24x24 viewBox, so scale = size / 24.
function svgAttr(tag, name) {
  var m = tag.match(new RegExp(name + '="([^"]+)"'));
  return m ? parseFloat(m[1]) : 0;
}
function drawIconPath(ctx, name, x, y, size, color) {
  var html = ICON_PATHS[name];
  if (!html) return;
  var tags = html.match(/<[a-z]+[^>]*\/>/g) || [];
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(size / 24, size / 24);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  tags.forEach(function (tag) {
    if (tag.indexOf('<path') === 0) {
      var d = tag.match(/d="([^"]+)"/);
      if (d) ctx.stroke(new Path2D(d[1]));
    } else if (tag.indexOf('<circle') === 0) {
      ctx.beginPath();
      ctx.arc(svgAttr(tag, 'cx'), svgAttr(tag, 'cy'), svgAttr(tag, 'r'), 0, Math.PI * 2);
      ctx.stroke();
    } else if (tag.indexOf('<rect') === 0) {
      ctx.strokeRect(svgAttr(tag, 'x'), svgAttr(tag, 'y'), svgAttr(tag, 'width'), svgAttr(tag, 'height'));
    } else if (tag.indexOf('<ellipse') === 0) {
      ctx.beginPath();
      ctx.ellipse(svgAttr(tag, 'cx'), svgAttr(tag, 'cy'), svgAttr(tag, 'rx'), svgAttr(tag, 'ry'), 0, 0, Math.PI * 2);
      ctx.stroke();
    }
  });
  ctx.restore();
}
function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
// Lightens (positive percent) or darkens (negative) a "#rrggbb" hex color by
// blending it toward white/black — used to build the share card's gradient
// bar from a single favorite-team color without needing 3 hand-picked shades
// per team the way the fixed brand-orange gradient below has.
function shadeHexColor(hex, percent) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  var r = (num >> 16) & 255, g = (num >> 8) & 255, b = num & 255;
  var t = percent < 0 ? 0 : 255, p = Math.abs(percent);
  return 'rgb(' + (Math.round((t - r) * p) + r) + ',' + (Math.round((t - g) * p) + g) + ',' + (Math.round((t - b) * p) + b) + ')';
}
function hexToRgbaString(hex, alpha) {
  hex = hex.replace('#', '');
  if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
  var num = parseInt(hex, 16);
  return 'rgba(' + ((num >> 16) & 255) + ',' + ((num >> 8) & 255) + ',' + (num & 255) + ',' + alpha + ')';
}
// format: 'square' (1080x1080, X/general-purpose) or 'story' (1080x1920,
// Instagram/Snapchat Stories). The header (logo/brand, divider) and footer
// pill stay pinned to their same distance from the top/bottom regardless of
// format — only the vertical CENTER of the layout (where the glow, title,
// big headline number, sub/detail lines sit) moves to the middle of
// whatever's left between them, so a story card doesn't just look like a
// square card with a huge empty gap stretched into the bottom.
function drawShareCard(ctx, cfg, format) {
  var W = 1080, H = format === 'story' ? 1920 : 1080, FONT = '-apple-system, "Segoe UI", Helvetica, Arial, sans-serif';
  var midY = format === 'story' ? 1000 : 500;
  // A favorite team (if set) themes the glow/bars/headline-number/team line —
  // the one thing on this card that's actually personal to whoever's sharing
  // it. The corner "READS" brand mark deliberately stays brand-orange either
  // way, so the card still reads as this app's no matter whose team color
  // is on it. rawAccent/rawAccent2 are the team's true colors (used for the
  // bar and swatch dot, where staying faithful to the team matters more than
  // contrast); accent/accent2 run through readableOnDark first — the same
  // fix already applied to the on-screen rating ring/greeting text — because
  // a dark team color (Ravens purple, Auburn navy, Saints black) used
  // straight as the giant headline number's fill was otherwise nearly
  // invisible against this card's own dark background. That was the actual
  // bug behind "doesn't look like my team" — the color was there, just
  // unreadable, not more personalized so much as broken.
  var fav = primaryFavoriteTeam();
  var rawAccent = fav ? fav.color : '#d9a63c';
  var rawAccent2 = fav ? (fav.color2 || fav.color) : shadeHexColor(rawAccent, -0.2);
  var accent = readableOnDark(rawAccent);
  var accent2 = readableOnDark(rawAccent2);

  // Subtle top-to-bottom gradient instead of a flat fill — reads as a lot
  // less "placeholder" than a single flat navy rectangle.
  var bgGrad = ctx.createLinearGradient(0, 0, 0, H);
  bgGrad.addColorStop(0, '#101a34');
  bgGrad.addColorStop(1, '#080d18');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  // Soft spotlight glow centered behind the headline stat — draws the eye
  // straight to the number instead of every element competing at equal
  // visual weight. Stronger + wider, and a touch more opaque when a favorite
  // team is set, so the theming actually reads at a glance instead of being
  // a barely-there tint.
  var glow = ctx.createRadialGradient(W / 2, midY, 40, W / 2, midY, 520);
  glow.addColorStop(0, hexToRgbaString(accent, fav ? 0.30 : 0.20));
  glow.addColorStop(1, hexToRgbaString(accent, 0));
  ctx.fillStyle = glow;
  ctx.fillRect(0, 0, W, H);

  // Two-tone bar when the team actually has a second color (Auburn's navy
  // into orange, etc.) instead of the old single-color-faded-into-itself
  // gradient, which flattened every two-tone team down to looking like a
  // solid-color program.
  var barGrad = ctx.createLinearGradient(0, 0, W, 0);
  barGrad.addColorStop(0, shadeHexColor(rawAccent, 0.35));
  barGrad.addColorStop(0.5, rawAccent);
  barGrad.addColorStop(1, rawAccent2);
  ctx.fillStyle = barGrad;
  ctx.fillRect(0, 0, W, 18);
  ctx.fillRect(0, H - 18, W, 18);

  ctx.textBaseline = 'alphabetic';
  ctx.textAlign = 'left';
  drawIconPath(ctx, 'zap', 60, 64, 42, '#d9a63c');
  ctx.fillStyle = '#d9a63c';
  ctx.font = '800 44px ' + FONT;
  ctx.fillText('READS', 116, 112);
  ctx.fillStyle = '#9aa8c2';
  ctx.font = '600 26px ' + FONT;
  ctx.fillText('NFL & CFB Trivia', 116, 150);
  ctx.strokeStyle = 'rgba(238,242,248,0.1)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(60, 192); ctx.lineTo(W - 60, 192); ctx.stroke();

  // Favorite-team identity line — a two-tone swatch dot (same visual idea as
  // the team picker's diagonal-split swatch) plus the team's real name and,
  // if it has one, its chant. This is the part that actually says "this is
  // MY team's card" instead of leaving color as the only, easy-to-miss tell.
  if (fav) {
    var dotR = 12, dotCX = 60 + dotR, dotCY = 192 + 42;
    ctx.save();
    ctx.beginPath(); ctx.arc(dotCX, dotCY, dotR, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = rawAccent; ctx.fillRect(dotCX - dotR, dotCY - dotR, dotR, dotR * 2);
    ctx.fillStyle = rawAccent2; ctx.fillRect(dotCX, dotCY - dotR, dotR, dotR * 2);
    ctx.restore();
    ctx.strokeStyle = 'rgba(238,242,248,0.35)';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(dotCX, dotCY, dotR, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#eef2f8';
    ctx.font = '700 30px ' + FONT;
    ctx.textAlign = 'left';
    ctx.fillText(fav.name + (fav.chant ? '  ·  ' + fav.chant : ''), dotCX + dotR + 18, dotCY + 10);
  }

  ctx.textAlign = 'center';
  ctx.fillStyle = '#eef2f8';
  ctx.font = '700 42px ' + FONT;
  ctx.fillText(cfg.title, W / 2, midY - 220);

  // Headline number auto-shrinks if a longer value (e.g. a big Speed-round
  // point total) would otherwise run past the card's edges — short values
  // (percentages, grades, streak counts) still get the full, bold size this
  // card is built around.
  var headlineFont = 160;
  ctx.font = '800 ' + headlineFont + 'px ' + FONT;
  var maxHeadlineWidth = W - 160;
  while (ctx.measureText(cfg.headline).width > maxHeadlineWidth && headlineFont > 70) {
    headlineFont -= 8;
    ctx.font = '800 ' + headlineFont + 'px ' + FONT;
  }
  ctx.fillStyle = accent;
  ctx.fillText(cfg.headline, W / 2, midY);

  ctx.fillStyle = '#eef2f8';
  ctx.font = '600 46px ' + FONT;
  ctx.fillText(cfg.sub, W / 2, midY + 90);
  if (cfg.detail) {
    ctx.fillStyle = '#9aa8c2';
    ctx.font = '500 34px ' + FONT;
    ctx.fillText(cfg.detail, W / 2, midY + 152);
  }

  // Footer name/date as a soft pill chip rather than bare text floating at
  // the bottom — a small thing that makes the whole card feel considered
  // rather than assembled from four independent fillText calls. Border picks
  // up the team's raw color at low opacity so the theming carries all the
  // way to the bottom of the card, not just the middle.
  var footerText = (state.name ? state.name + ' — ' : '') + todayStr();
  ctx.font = '600 30px ' + FONT;
  var footerWidth = ctx.measureText(footerText).width;
  var footerX = W / 2 - footerWidth / 2 - 28, footerY = H - 98, footerW = footerWidth + 56, footerH = 54;
  ctx.fillStyle = 'rgba(238,242,248,0.06)';
  roundRectPath(ctx, footerX, footerY, footerW, footerH, 27);
  ctx.fill();
  ctx.strokeStyle = hexToRgbaString(rawAccent, 0.45);
  ctx.lineWidth = 1.5;
  roundRectPath(ctx, footerX, footerY, footerW, footerH, 27);
  ctx.stroke();
  ctx.fillStyle = '#c3cbdc';
  ctx.fillText(footerText, W / 2, H - 63);
}
function shareResultCard(mode) {
  var cfg = shareConfigFor(mode);
  if (!cfg) return;
  // Every share path (native share sheet, copy-text, Share to X) reads
  // cfg.shareText — appending the site link once, here, means whoever
  // receives it has something to tap through and play themselves instead
  // of just seeing a score with no way to act on it.
  cfg.shareText = cfg.shareText + ' Play at ' + SITE_URL;
  var canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = 1080;
  var ctx = canvas.getContext('2d');
  drawShareCard(ctx, cfg);
  canvas.toBlob(function (blob) {
    var file = null;
    if (blob) { try { file = new File([blob], 'reads-result.png', { type: 'image/png' }); } catch (e) { file = null; } }
    if (file && navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      navigator.share({ files: [file], title: cfg.title, text: cfg.shareText, url: SITE_URL }).catch(function () {});
    } else {
      openShareModal(canvas.toDataURL('image/png'), cfg);
    }
  }, 'image/png');
}
var shareTriggerEl = null;
var shareCurrentCfg = null;
// 'square' (1080x1080 — X/general) or 'story' (1080x1920 — Instagram/Snap
// Stories). Only the modal fallback path gets a choice — the native
// navigator.share() branch in shareResultCard() shares whatever the OS
// share sheet was opened with (square) and closes immediately, so there's
// no UI moment to offer a toggle there anyway.
var shareCurrentFormat = 'square';
function renderShareCard(format) {
  if (!shareCurrentCfg) return;
  var canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = format === 'story' ? 1920 : 1080;
  drawShareCard(canvas.getContext('2d'), shareCurrentCfg, format);
  var img = document.getElementById('share-preview');
  if (img) img.src = canvas.toDataURL('image/png');
  shareCurrentFormat = format;
  document.querySelectorAll('[data-share-format]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.shareFormat === format);
  });
}
function openShareModal(dataUrl, cfg) {
  shareCurrentCfg = cfg;
  shareCurrentFormat = 'square';
  shareTriggerEl = document.activeElement;
  var img = document.getElementById('share-preview');
  if (img) img.src = dataUrl;
  document.querySelectorAll('[data-share-format]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.shareFormat === 'square');
  });
  var fbBtn = document.getElementById('share-facebook');
  if (fbBtn) fbBtn.style.display = (location.protocol === 'http:' || location.protocol === 'https:') ? '' : 'none';
  var modal = document.getElementById('share-modal');
  var backdrop = document.getElementById('share-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('share-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeShareModal() {
  var modal = document.getElementById('share-modal');
  var backdrop = document.getElementById('share-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (shareTriggerEl && document.contains(shareTriggerEl)) shareTriggerEl.focus();
  shareTriggerEl = null;
  shareCurrentCfg = null;
  shareCurrentFormat = 'square';
}
/* ============================== report a problem ==============================
   A lightweight flag button (in the shared modeToolbarHtml(), next to Restart/
   Exit) that writes straight to a Firestore review queue — see submitReport()
   in firebase-sync.js and the hidden #reports route (renderReportsScreen())
   for how it's reviewed. Auto-captures the exact question being shown where
   the mode has one (quiz-style modes only — CURRENT_QUESTION_GETTERS), so a
   report doesn't depend on the player typing out which question they meant. */
var CURRENT_QUESTION_GETTERS = {
  quiz: currentQuizQuestion, cfbQuiz: currentCfbQuestion, daily: currentDailyQuestion,
  speed: currentSpeedQuestion, cfbSpeed: currentCfbSpeedQuestion,
  iq: currentIQQuestion, cfbIq: currentCfbIQQuestion, study: currentStudyQuestion
};
function currentQuestionContext(mode) {
  var getter = CURRENT_QUESTION_GETTERS[mode];
  if (!getter) return null;
  try {
    var q = getter();
    return q ? { id: q.id, text: q.question } : null;
  } catch (e) { return null; }
}
var reportTriggerEl = null;
var reportCurrentMode = null;
var reportCategory = 'Wrong answer';
function openReportModal(mode) {
  reportCurrentMode = mode;
  reportCategory = 'Wrong answer';
  reportTriggerEl = document.activeElement;
  var ctx = currentQuestionContext(mode);
  var contextEl = document.getElementById('report-context');
  if (contextEl) {
    contextEl.textContent = ctx ? ('Reporting: ' + modeLabelFor(mode) + ' — “' + ctx.text + '”') : ('Reporting a problem in ' + modeLabelFor(mode) + '.');
  }
  document.querySelectorAll('#report-category-row .chip-toggle').forEach(function (btn, i) {
    btn.classList.toggle('active', i === 0);
  });
  var noteEl = document.getElementById('report-note');
  if (noteEl) noteEl.value = '';
  var confirmEl = document.getElementById('report-confirm');
  if (confirmEl) confirmEl.style.display = 'none';
  var submitBtn = document.getElementById('report-submit');
  if (submitBtn) { submitBtn.style.display = ''; submitBtn.disabled = false; submitBtn.textContent = 'Send Report'; }
  var modal = document.getElementById('report-modal');
  var backdrop = document.getElementById('report-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('report-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeReportModal() {
  var modal = document.getElementById('report-modal');
  var backdrop = document.getElementById('report-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (reportTriggerEl && document.contains(reportTriggerEl)) reportTriggerEl.focus();
  reportTriggerEl = null;
  reportCurrentMode = null;
}
function setReportCategory(cat) {
  reportCategory = cat;
  document.querySelectorAll('#report-category-row .chip-toggle').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.reportCategory === cat);
  });
}
function submitReport() {
  if (!reportCurrentMode) return;
  var noteEl = document.getElementById('report-note');
  var note = noteEl ? noteEl.value.trim() : '';
  var ctx = currentQuestionContext(reportCurrentMode);
  var payload = {
    mode: reportCurrentMode,
    modeLabel: modeLabelFor(reportCurrentMode),
    category: reportCategory,
    note: note,
    questionId: ctx ? ctx.id : null,
    questionText: ctx ? ctx.text : null,
    reporterName: state.name || null
  };
  var submitBtn = document.getElementById('report-submit');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }
  if (window.__fbSync && window.__fbSync.submitReport) window.__fbSync.submitReport(payload);
  var confirmEl = document.getElementById('report-confirm');
  if (confirmEl) confirmEl.style.display = '';
  if (submitBtn) submitBtn.style.display = 'none';
  setTimeout(closeReportModal, 1400);
}
function renderReportsScreen() {
  var reports = (window.__fbSync && window.__fbSync.reports) || [];
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Reported Questions</h2>' +
    '<p class="mode-desc">' + reports.length + ' report' + (reports.length === 1 ? '' : 's') + '. Hidden page, not linked anywhere in the app.</p>';
  if (!reports.length) {
    html += '<p class="mode-desc">Nothing reported yet.</p>';
  } else {
    html += '<div class="reports-list">' + reports.map(function (r) {
      return '<div class="report-row">' +
        '<div class="report-row-top"><b>' + esc(r.modeLabel || r.mode || 'Unknown mode') + '</b><span class="report-row-cat">' + esc(r.category || '') + '</span></div>' +
        (r.questionText ? '<div class="report-row-question">' + esc(r.questionText) + '</div>' : '') +
        (r.note ? '<div class="report-row-note">' + esc(r.note) + '</div>' : '') +
        '<div class="report-row-meta">' + esc(r.reporterName || 'Anonymous') + '</div>' +
        '</div>';
    }).join('') + '</div>';
  }
  html += '</div>';
  return html;
}
function shareDownloadImage() {
  var img = document.getElementById('share-preview');
  if (!img || !img.src) return;
  var a = document.createElement('a');
  a.href = img.src;
  a.download = shareCurrentFormat === 'story' ? 'reads-result-story.png' : 'reads-result.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
function shareToX() {
  if (!shareCurrentCfg) return;
  var url = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(shareCurrentCfg.shareText);
  window.open(url, '_blank', 'noopener');
}
function shareToFacebook() {
  var url = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(location.href);
  window.open(url, '_blank', 'noopener');
}
function shareCopyConfirm(btn) {
  if (!btn) return;
  var original = btn.innerHTML;
  btn.innerHTML = icon('check') + ' Copied!';
  setTimeout(function () { btn.innerHTML = original; }, 1600);
}
function shareCopyText() {
  if (!shareCurrentCfg) return;
  var btn = document.getElementById('share-copy');
  var text = shareCurrentCfg.shareText;
  // navigator.clipboard requires a secure context (http(s)/localhost) — not
  // available over file://, so this falls back to the older
  // execCommand('copy')-via-hidden-textarea trick, which works everywhere.
  if (navigator.clipboard && navigator.clipboard.writeText && (location.protocol === 'https:' || location.protocol === 'http:')) {
    navigator.clipboard.writeText(text).then(function () { shareCopyConfirm(btn); }).catch(function () { shareCopyTextFallback(text, btn); });
  } else {
    shareCopyTextFallback(text, btn);
  }
}
// Same copy-to-clipboard approach as shareCopyText(), just for an arbitrary
// string (the contact email on the Privacy Policy page) instead of the
// current share card's text — same secure-context check, same
// execCommand('copy') fallback for http/file:// contexts.
function copyTextToClipboard(text, btn) {
  if (navigator.clipboard && navigator.clipboard.writeText && (location.protocol === 'https:' || location.protocol === 'http:')) {
    navigator.clipboard.writeText(text).then(function () { shareCopyConfirm(btn); }).catch(function () { shareCopyTextFallback(text, btn); });
  } else {
    shareCopyTextFallback(text, btn);
  }
}
function shareCopyTextFallback(text, btn) {
  try {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    shareCopyConfirm(btn);
  } catch (e) {}
}

/* ============================== leaderboard ============================== */
// Two different people typing the same display name (very likely with common
// first names in a friend group) would otherwise write to the exact same
// Firestore doc (slugify("Mike")) and silently overwrite each other's scores.
// A random ID generated once per browser and persisted locally keeps each
// device's leaderboard entry distinct even when names collide, without
// requiring unique names or accounts.
function getClientId() {
  var id = lsGet('nflTriviaClientId', null);
  if (!id) {
    id = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
    lsSet('nflTriviaClientId', id);
  }
  return id;
}
function pushLeaderboard(mode, fields) {
  if (!state.name) return;
  var docId = slugify(state.name) + '_' + getClientId() + '__' + mode;
  var payload = Object.assign({ name: state.name, mode: mode }, fields);
  if (window.__fbSync && window.__fbSync.pushScore) window.__fbSync.pushScore(docId, payload);
  // Every finish* function that changes state.stats already calls this
  // right after — reusing it as the one choke point for pushProfileSnapshot()
  // too means cross-device stats sync doesn't need its own call bolted onto
  // all ~17 finish functions individually.
  pushProfileSnapshot();
}
// True once this device has done its one-time cross-device stats/streak
// pull for the current name — applyLeaderboard fires on every leaderboard
// change (could be fairly often with several people playing), but the pull
// itself only needs to happen once Firebase first actually connects, not
// on every subsequent update. saveName() resets this so switching names
// mid-session (Change Name) still gets its own pull.
var didInitialProfilePull = false;
window.__triviaSync = {
  applyLeaderboard: function (list) {
    state.leaderboardData = list;
    reconcileRating(list);
    if (!didInitialProfilePull && state.name) { didInitialProfilePull = true; pullProfileSnapshot(); }
    if (state.screen === 'leaderboard') renderAll();
  }
};

var LEADERBOARD_MODES = [
  { id: 'rating', label: 'Football Rating', sortKey: 'score', cols: [['score', 'Rating'], ['games', 'Games Played']] },
  { id: 'daily', label: 'Daily Challenge', sortKey: 'completions', cols: [['completions', 'Days Completed'], ['bestPct', 'Best %']] },
  { id: 'quiz', label: 'NFL Quiz', sortKey: 'bestPct', cols: [['bestPct', 'Best %'], ['correctTotal', 'Total Correct'], ['roundsPlayed', 'Rounds']] },
  { id: 'grid', label: 'NFL Grid', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['cleanSweeps', 'Clean Sweeps'], ['gamesPlayed', 'Games']] },
  { id: 'blitz', label: 'NFL Blitz', sortKey: 'bestMatched', cols: [['bestMatched', 'Best Matched'], ['attempts', 'Attempts']] },
  { id: 'speed', label: 'NFL Speed', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestStreak', 'Best Streak'], ['sessionsPlayed', 'Sessions']] },
  { id: 'silhouette', label: 'NFL Silhouette', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestQuick', 'Best Quick Guesses'], ['roundsPlayed', 'Rounds']] },
  { id: 'iq', label: 'NFL IQ Test', sortKey: 'bestIQ', cols: [['bestIQ', 'Best IQ'], ['testsTaken', 'Tests Taken']] },
  { id: 'higherLower', label: 'Higher or Lower', sortKey: 'bestStreak', cols: [['bestStreak', 'Best Streak'], ['gamesPlayed', 'Runs']] },
  { id: 'legends', label: '17-0', sortKey: 'bestWins', cols: [['bestRecord', 'Best Record'], ['bestGrade', 'Best Grade'], ['gamesPlayed', 'Drafts']] },
  { id: 'cfbQuiz', label: 'CFB Quiz', sortKey: 'bestPct', cols: [['bestPct', 'Best %'], ['correctTotal', 'Total Correct'], ['roundsPlayed', 'Rounds']] },
  { id: 'cfbIq', label: 'CFB IQ', sortKey: 'bestIQ', cols: [['bestIQ', 'Best IQ'], ['testsTaken', 'Tests Taken']] },
  { id: 'cfbSpeed', label: 'CFB Speed Round', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['bestStreak', 'Best Streak'], ['sessionsPlayed', 'Sessions']] },
  { id: 'cfbBlitz', label: 'CFB Blitz', sortKey: 'bestMatched', cols: [['bestMatched', 'Best Matched'], ['attempts', 'Attempts']] },
  { id: 'cfbGrid', label: 'CFB Immaculate Grid', sortKey: 'bestScore', cols: [['bestScore', 'Best Score'], ['cleanSweeps', 'Clean Sweeps'], ['gamesPlayed', 'Games']] },
  { id: 'cfbLegends', label: 'CFB 12-0', sortKey: 'bestWins', cols: [['bestRecord', 'Best Record'], ['bestGrade', 'Best Grade'], ['gamesPlayed', 'Drafts']] },
  { id: 'h2h', label: 'Head-to-Head', sortKey: 'wins', cols: [['wins', 'Wins'], ['losses', 'Losses'], ['ties', 'Ties']] }
];
// "Today"/"This Week" reads each row's updatedAt (a Firestore serverTimestamp
// set on every pushScore() — see firebase-sync.js) rather than any separate
// per-period snapshot: since pushScore always writes the player's CURRENT
// best for that mode (merged into one persistent doc per name+device+mode,
// not a new doc per round), this really means "players who've touched this
// mode within the window, showing their current best" — an honest, useful
// "who's active lately" view, not a true period-reset leaderboard (that would
// need storing per-round history, real added backend complexity for a nice-
// to-have). Labeled clearly in the UI so it doesn't overclaim what it is.
var LEADERBOARD_RANGES = [
  { id: 'all', label: 'All-Time' },
  { id: 'week', label: 'This Week' },
  { id: 'today', label: 'Today' }
];
function leaderboardTimestampMs(row) {
  var ts = row.updatedAt;
  if (!ts) return null;
  if (typeof ts.toMillis === 'function') return ts.toMillis();
  if (typeof ts.seconds === 'number') return ts.seconds * 1000;
  return null;
}
function leaderboardRowInRange(row, range) {
  if (range === 'all') return true;
  var ms = leaderboardTimestampMs(row);
  if (ms == null) return false; // no timestamp yet (e.g. optimistic local echo before the server round-trip resolves serverTimestamp()) — excluded rather than guessed
  var windowMs = range === 'today' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
  return (Date.now() - ms) < windowMs;
}
// Relative-time formatting for the "top of the week" callout and the
// activity feed below — both just need a rough "how long ago", not a full
// date/time display.
function formatRelativeTime(ms) {
  var s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  if (s < 60) return 'just now';
  var m = Math.round(s / 60);
  if (m < 60) return m + 'm ago';
  var h = Math.round(m / 60);
  if (h < 24) return h + 'h ago';
  var d = Math.round(h / 24);
  return d + 'd ago';
}
// A special callout above the table specifically for the This Week view —
// same underlying data as the table's own #1 row, just given the visual
// weight an actual "this week's leader" deserves instead of blending into
// the rest of the list.
function leaderboardTopOfWeekHtml(mode, rows) {
  if (state.leaderboardRange !== 'week' || !rows.length) return '';
  var leader = rows[0];
  return '<div class="leaderboard-top-of-week">' + icon('trophy') +
    ' <b>' + esc(leader.name) + '</b> is on top of the week in ' + esc(mode.label) + ' — ' +
    mode.cols.map(function (c) { return esc(c[1]) + ' ' + esc(leader[c[0]] != null ? leader[c[0]] : 0); }).join(', ') +
    '</div>';
}
// Derived entirely from state.leaderboardData's existing updatedAt field
// (already written by pushScore()/serverTimestamp() for the week/today
// leaderboard filter above) rather than a new Firestore collection — a
// genuine live "the app is alive" feed without adding new backend schema,
// security rules, or write paths. Global across every mode (not scoped to
// whichever leaderboard tab is open), newest first, capped at 8.
function recentActivityHtml() {
  var withTime = state.leaderboardData
    .map(function (r) { return { row: r, ms: leaderboardTimestampMs(r) }; })
    .filter(function (x) { return x.ms != null; })
    .sort(function (a, b) { return b.ms - a.ms; })
    .slice(0, 8);
  if (!withTime.length) return '';
  return '<div class="leaderboard-activity">' +
    '<h3 class="mode-section-title">Recent Activity</h3>' +
    withTime.map(function (x) {
      var m = LEADERBOARD_MODES.find(function (mm) { return mm.id === x.row.mode; });
      var mainCol = m && m.cols[0];
      var valueBit = mainCol && x.row[mainCol[0]] != null ? ' — ' + esc(mainCol[1]) + ' ' + esc(x.row[mainCol[0]]) : '';
      return '<div class="leaderboard-activity-row"><b>' + esc(x.row.name) + '</b> played ' + esc(m ? m.label : x.row.mode) + valueBit + ' <span class="leaderboard-activity-time">' + formatRelativeTime(x.ms) + '</span></div>';
    }).join('') +
    '</div>';
}
function renderLeaderboard() {
  var mode = LEADERBOARD_MODES.find(function (m) { return m.id === state.leaderboardMode; });
  var mySlug = state.name ? slugify(state.name) : null;
  var allRanked = state.leaderboardData.filter(function (r) { return r.mode === mode.id && leaderboardRowInRange(r, state.leaderboardRange); })
    .sort(function (a, b) { return (b[mode.sortKey] || 0) - (a[mode.sortKey] || 0); });
  var rows = allRanked.slice(0, 25);
  var myFullRank = mySlug ? allRanked.findIndex(function (r) { return slugify(r.name) === mySlug; }) : -1;
  var html = '<div class="panel">' +
    '<h2 class="panel-title">' + icon('trophy') + ' Leaderboard</h2>' +
    '<div class="chip-row">' +
    LEADERBOARD_MODES.map(function (m) { return '<button class="chip-toggle' + (state.leaderboardMode === m.id ? ' active' : '') + '" data-leaderboard-mode="' + m.id + '">' + esc(m.label) + '</button>'; }).join('') +
    '</div>' +
    '<div class="chip-row leaderboard-range-row">' +
    LEADERBOARD_RANGES.map(function (r) { return '<button class="chip-toggle' + (state.leaderboardRange === r.id ? ' active' : '') + '" data-leaderboard-range="' + r.id + '">' + esc(r.label) + '</button>'; }).join('') +
    '</div>' +
    leaderboardTopOfWeekHtml(mode, rows);
  if (!rows.length) {
    html += '<p class="mode-desc">No scores yet for ' + esc(mode.label) + (state.leaderboardRange === 'all' ? '' : ' (' + esc(LEADERBOARD_RANGES.find(function (r) { return r.id === state.leaderboardRange; }).label) + ')') + '. Play a round to be the first on the board!</p>';
  } else {
    html += '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>#</th><th>Name</th>' + mode.cols.map(function (c) { return '<th>' + esc(c[1]) + '</th>'; }).join('') + '</tr></thead><tbody>';
    rows.forEach(function (r, i) {
      var isMe = mySlug && slugify(r.name) === mySlug;
      html += '<tr class="' + (isMe ? 'leaderboard-row-me' : '') + '"><td>' + (i + 1) + '</td><td>' + esc(r.name) + (isMe ? ' <span class="leaderboard-you-tag">You</span>' : '') + '</td>' + mode.cols.map(function (c) { return '<td>' + esc(r[c[0]] != null ? r[c[0]] : 0) + '</td>'; }).join('') + '</tr>';
    });
    html += '</tbody></table></div>';
    if (myFullRank >= 25) {
      var myRow = allRanked[myFullRank];
      html += '<div class="leaderboard-my-rank">Your rank: <b>#' + (myFullRank + 1) + '</b> of ' + allRanked.length + ' &middot; ' +
        mode.cols.map(function (c) { return esc(c[1]) + ' ' + esc(myRow[c[0]] != null ? myRow[c[0]] : 0); }).join(' &middot; ') +
        '</div>';
    }
  }
  html += recentActivityHtml();
  html += '</div>';
  return html;
}

/* ============================== mode-popularity stats (owner-only) ==============================
   The whole "analytics" story for this app, by deliberate choice over a
   third-party tool (Plausible/GA/etc — see the decision recorded in project
   memory): a single shared Firestore counter doc (games/nflTrivia/analytics/
   playCounts), incremented once per real mode entry via
   window.__fbSync.logPlay() in enterMode(). No per-user tracking, no
   external script.
   This app has no real auth/admin-role system at all (every device signs in
   anonymously, same as everyone else), so "viewable only by you" can't mean
   real access control without adding a login system just for this — out of
   proportion for a friend-group trivia app. Instead this screen is reachable
   only via a hidden route (visit the site with #stats in the URL) and isn't
   linked from anywhere in the UI, so regular players won't stumble onto it.
   See the hash check near the bottom of this file (search "#stats"). */
function renderStatsScreen() {
  var counts = (window.__fbSync && window.__fbSync.playCounts) || {};
  var all = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  var rows = all.map(function (m) { return { id: m.id, title: m.title, n: counts[m.id] || 0 }; })
    .sort(function (a, b) { return b.n - a.n; });
  var total = counts.total || 0;
  var maxN = Math.max.apply(null, rows.map(function (r) { return r.n; }).concat([1]));
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Mode Popularity</h2>' +
    '<p class="mode-desc">How many times each mode has been opened, across everyone who’s played &mdash; ' + total + ' total. Hidden page, not linked anywhere in the app.</p>' +
    '<div class="stats-bars">' +
    rows.map(function (r) {
      var pct = Math.round(100 * r.n / maxN);
      return '<div class="stats-bar-row">' +
        '<div class="stats-bar-label">' + esc(r.title) + '</div>' +
        '<div class="stats-bar-track"><div class="stats-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<div class="stats-bar-value">' + r.n + '</div>' +
        '</div>';
    }).join('') +
    '</div>' +
    '</div>';
  return html;
}

/* ============================== about ==============================
   Trust-signal page: what this app is, how the question banks were
   actually built (honestly — some modes have been through a much deeper
   fact-check pass than others; this doesn't claim otherwise), what data is
   stored, and how to flag a bad question. Linked from the footer only. */
function renderAbout() {
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">About Reads</h2>' +
    '<div class="about-section">' +
    '<p class="mode-desc">Reads is free NFL and College Football trivia — 12 game modes, a live shared leaderboard, and one adaptive Football Rating that follows you across every mode and device. No accounts, no passwords — just a name.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">How the questions are made</h3>' +
    '<p class="mode-desc">Every question bank started from real research — spreadsheets of Heisman winners, national champions, coaching records, career and single-season statistical leaders, bowl history, and rivalries, cross-checked against primary sources rather than written from memory. Wrong-answer options are deliberately pulled from that same real data (other real winners, other real years, other real players) instead of invented — so a wrong answer is still a true fact, just not the one being asked about.</p>' +
    '<p class="mode-desc">The College Football Quiz and IQ Test banks went through a full audit pass: every question was checked for factual accuracy, contradictory or duplicate answer options were found and fixed, near-duplicate questions were removed, and roughly 150 new questions were generated fresh from a dedicated verified reference workbook. The other banks are held to the same real-data-only standard but haven’t all been through that exact same line-by-line review yet — which is exactly what the report link below is for.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Your data</h3>' +
    '<p class="mode-desc">Your name, scores, and Football Rating sync to a shared Firestore database so the leaderboard and rating work across devices — that’s the only place any of it goes. Your streak and a few other stats stay local to your device only. No third-party analytics, no ad trackers. Full details: <button class="link-btn" data-go="privacy">Privacy Policy</button>.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Found a bad question?</h3>' +
    '<p class="mode-desc">Every mode has a ' + icon('flag') + ' Report button next to Restart/Exit while you’re playing — flag it and it goes straight into a review queue.</p>' +
    '</div>' +
    '</div>';
}
/* ============================== push notifications ==============================
   Real Web Push (arrives even when the app/tab isn't open), not a locally
   scheduled notification — the actual sending happens server-side, once a
   day, from netlify/functions/send-daily-push.js. This half just handles
   the browser's subscribe/unsubscribe dance and hands the resulting
   PushSubscription to the backend to store.

   VAPID_PUBLIC_KEY is safe to ship in client code — it's the whole point of
   a public key. Its private counterpart lives only in Netlify's env vars,
   used server-side to sign outgoing pushes so browsers can verify they
   really came from this app's backend and not something else that got
   hold of a subscription endpoint. */
var VAPID_PUBLIC_KEY = 'BEQcgDnLWmFofJ7DLYv7z_DJYRcY58jiM4X_CEf2gCRRKx0N1Wu2QTLF0hSNG8Vn4l8bT0Oi3bzrWNscEDmSuC0';
var PUSH_ENABLED_KEY = 'nflTriviaPushEnabled';
function pushSupported() { return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window; }
function pushEnabledLocally() { return lsGet(PUSH_ENABLED_KEY, false); }
// PushManager wants the VAPID public key as a raw Uint8Array, not the
// base64url string it's distributed as everywhere else (URL, env vars) —
// this is the standard conversion, same one every Web Push guide uses.
function urlBase64ToUint8Array(base64String) {
  var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  var rawData = atob(base64);
  var outputArray = new Uint8Array(rawData.length);
  for (var i = 0; i < rawData.length; i++) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}
function enablePushNotifications() {
  if (!pushSupported()) { alert("This browser doesn't support push notifications."); return Promise.resolve(); }
  return Notification.requestPermission().then(function (permission) {
    if (permission !== 'granted') return;
    return navigator.serviceWorker.ready.then(function (reg) {
      return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) });
    }).then(function (sub) {
      return fetch('/.netlify/functions/save-subscription', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sub)
      });
    }).then(function () {
      lsSet(PUSH_ENABLED_KEY, true);
      renderAll();
    });
  }).catch(function (err) { console.warn('Push subscribe failed', err); });
}
function disablePushNotifications() {
  if (!pushSupported()) return Promise.resolve();
  return navigator.serviceWorker.ready.then(function (reg) {
    return reg.pushManager.getSubscription();
  }).then(function (sub) {
    if (!sub) return;
    return fetch('/.netlify/functions/save-subscription', {
      method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sub)
    }).then(function () { return sub.unsubscribe(); });
  }).then(function () {
    lsSet(PUSH_ENABLED_KEY, false);
    renderAll();
  }).catch(function (err) { console.warn('Push unsubscribe failed', err); });
}
function togglePushNotifications() {
  return pushEnabledLocally() ? disablePushNotifications() : enablePushNotifications();
}

/* ============================== settings ==============================
   Reachable from Profile → Settings — one place for the preferences that
   were previously scattered (sound only in the header, ranked/practice only
   on each mode's own setup screen, favorite teams only behind the header
   gear icon). Doesn't duplicate any storage/logic of its own — every
   control here calls the exact same functions those original entry points
   already used (toggleMute, openTeamPicker, setModeRankedPref/rankedToggleHtml,
   clearAllUserData), so there's exactly one source of truth for each
   setting regardless of where it's changed from. */
function settingsClearDataSectionHtml() {
  if (!state.settingsConfirmClear) {
    return '<button class="btn-secondary" data-settings-clear-ask>' + icon('xMark') + ' Clear My Data</button>';
  }
  return '<div class="settings-clear-confirm">' +
    '<p class="mode-desc">This erases your name, Football Rating, streak, badges, favorite teams, and every local stat on THIS device. It can’t be undone. Your leaderboard/rating entry on other devices (if any) isn’t affected until they also clear.</p>' +
    '<div class="btn-row">' +
    '<button class="btn-primary" data-settings-clear-confirm>Yes, Clear Everything</button>' +
    '<button class="btn-secondary" data-settings-clear-cancel>Cancel</button>' +
    '</div></div>';
}
function renderSettings() {
  var fav = getFavoriteTeams();
  var nflTeam = fav.nfl ? favoriteTeamById('nfl', fav.nfl) : null;
  var cfbTeam = fav.cfb ? favoriteTeamById('cfb', fav.cfb) : null;
  var allModes = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb);
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="profile">' + icon('home') + ' Back to Profile</button><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Settings</h2>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Sound</h3>' +
    '<p class="mode-desc">Background music and correct/wrong/complete sound effects (haptics on mobile follow the same switch).</p>' +
    '<button class="btn-secondary" data-settings-mute-toggle>' + (typeof soundMuted !== 'undefined' && soundMuted ? icon('volumeOff') + ' Sound is Off — Turn On' : icon('volumeOn') + ' Sound is On — Turn Off') + '</button>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Notifications</h3>' +
    '<p class="mode-desc">' + (pushSupported() ? "A daily nudge when today's Daily Challenge is live — nothing else, and you can turn it off any time." : "Your browser doesn't support push notifications.") + '</p>' +
    (pushSupported() ? '<button class="btn-secondary" data-settings-push-toggle>' + (pushEnabledLocally() ? icon('volumeOff') + ' Notifications On — Turn Off' : icon('volumeOn') + ' Turn On Notifications') + '</button>' : '') +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Favorite Teams</h3>' +
    '<p class="mode-desc">' +
    (nflTeam || cfbTeam ? ('NFL: <b>' + esc(nflTeam ? nflTeam.name : 'Not set') + '</b> &middot; College: <b>' + esc(cfbTeam ? cfbTeam.name : 'Not set') + '</b>') : 'Not set yet — used for a few personal touches around the app and a light nudge in the random mix.') +
    '</p>' +
    '<button class="btn-secondary" data-team-picker-toggle>' + icon('settings') + ' Change Teams</button>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Ranked vs. Practice, per mode</h3>' +
    '<p class="mode-desc">Ranked rounds count toward your Football Rating, stats, and the leaderboard; Practice rounds don’t. Each mode remembers its own choice — change any of them here, or from that mode’s own start screen.</p>' +
    '<div class="settings-ranked-grid">' +
    allModes.map(function (m) { return '<div class="settings-ranked-row"><span>' + esc(m.title) + '</span>' + rankedToggleHtml(m.id) + '</div>'; }).join('') +
    '</div>' +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">Your Data</h3>' +
    '<p class="mode-desc">Full details on what’s stored and where: <button class="link-btn" data-go="privacy">Privacy Policy</button>.</p>' +
    settingsClearDataSectionHtml() +
    '</div>' +

    '<div class="about-section">' +
    '<h3 class="about-heading">More</h3>' +
    '<div class="btn-row">' +
    '<button class="btn-secondary" data-go="about">' + icon('helpCircle') + ' About & How Questions Are Made</button>' +
    '</div>' +
    '</div>' +
    '</div>';
}
function settingsClearDataAsk() { state.settingsConfirmClear = true; renderAll(); }
function settingsClearDataCancel() { state.settingsConfirmClear = false; renderAll(); }
function clearAllUserData() {
  var keys = [];
  for (var i = 0; i < localStorage.length; i++) {
    var k = localStorage.key(i);
    if (k && k.indexOf('nflTrivia') === 0) keys.push(k);
  }
  keys.forEach(function (k) { localStorage.removeItem(k); });
  location.reload();
}
/* ============================== privacy policy ==============================
   A real, specific policy — not boilerplate — describing exactly what this
   app collects and where it goes, since Firebase + real names makes this
   worth getting right. Linked from the footer and from the About page. */
function renderPrivacy() {
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Privacy Policy</h2>' +
    '<p class="mode-desc">Last updated ' + CONTENT_UPDATED + '. Reads is a small, free trivia app built for a group of friends — this policy describes exactly what it collects and why, not generic legal boilerplate.</p>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">What Reads collects</h3>' +
    '<p class="mode-desc">There are no accounts, passwords, or email addresses required to play. The only thing you provide is a display name. Once you\'ve entered one, playing a round can send the following to a shared Firebase/Firestore database (a Google Cloud product):</p>' +
    '<ul class="privacy-list">' +
    '<li>Your name, exactly as you typed it.</li>' +
    '<li>Your scores and stats per game mode (best %, rounds played, etc.), used to build the leaderboard.</li>' +
    '<li>Your Football Rating and how many games it\'s based on.</li>' +
    '<li>If you play Head-to-Head: the match result (both players\' names and scores) is visible to whoever you\'re matched with.</li>' +
    '<li>If you use the Report button: the flagged question, your optional note, and your name (if you\'ve set one).</li>' +
    '</ul>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">What stays on your device only</h3>' +
    '<p class="mode-desc">Your daily-challenge streak, your Football Rating history (used for the little sparkline on your profile), which onboarding screens you\'ve seen, your practice/ranked preferences, and the shuffled-question "deck" that avoids repeats — none of this ever leaves your browser\'s local storage.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Who can see it</h3>' +
    '<p class="mode-desc">The leaderboard, Football Rating board, and Head-to-Head results are intentionally shared and visible to anyone playing the app — that\'s the point of a live leaderboard. The Report queue lives at a hidden, unlisted page rather than behind a real login (this app has no account system to gate it with), so treat it as unlisted, not private. There\'s no ad tracking, no third-party analytics, and nothing is sold or shared outside this Firebase project.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">How you connect</h3>' +
    '<p class="mode-desc">The app signs your browser in to Firebase anonymously (a random device-level ID with no personal info attached) so it\'s allowed to read and write the shared data above. That anonymous ID, not your name, is what Firebase/Google sees at the infrastructure level.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Deleting your data</h3>' +
    '<p class="mode-desc">Clearing your browser\'s site data/local storage removes everything stored on your device. There\'s no self-service delete button for the shared leaderboard/rating/report data yet — email the address below and it\'ll be removed by hand.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Changes</h3>' +
    '<p class="mode-desc">If what this app collects changes, this page gets updated and the date at the top will change.</p>' +
    '</div>' +
    '<div class="about-section">' +
    '<h3 class="about-heading">Questions</h3>' +
    '<p class="mode-desc">Email us about this policy or your data:</p>' +
    '<div class="contact-email-row">' +
    '<a class="contact-email" href="mailto:readstrivia@gmail.com">readstrivia@gmail.com</a>' +
    '<button class="btn-tiny" data-copy-email="readstrivia@gmail.com">' + icon('copy') + ' Copy</button>' +
    '</div>' +
    '</div>' +
    '</div>';
}

/* ============================== learn ==============================
   A browsable reference section — NFL/CFB facts, history, stat leaders,
   Hall of Famers — deliberately NOT another quiz/game mode, just filterable
   lists. Ships with 8 sections, all sourced from data this app already has
   verified for its game modes (CFB_GRID_PLAYERS, GRID_PLAYERS, plus the
   existing CFB/QUIZ trivia banks for the two Trivia Almanac sections)
   rather than authoring new content — see LEARN_SECTIONS below for exactly
   which field backs which section.

   The two "Trivia Almanac" sections reuse this app's own 456-question CFB
   quiz bank and 482-question NFL quiz bank (CFB/QUIZ, already loaded eagerly
   at startup for the Quiz modes) as fact cards instead of tables — each
   question's correct option plus its `notes` field reads as a standalone
   fact ("Q, A, and why"), which doesn't fit a table's fixed columns the way
   the roster-stat sections do. dataFiles is deliberately [] for these two:
   CFB/QUIZ are core assets loaded via a <script> tag in index.html, not via
   loadScript(), so listing them here would just re-fetch and re-run an
   already-loaded file for no reason.

   Two honesty notes baked into the section choices themselves (found while
   designing this, not something to quietly paper over):
   - CFB_GRID_PLAYERS' `years` field is a player's All-America SELECTION
     year(s), not a dedicated Heisman-year or championship-year field —
     Archie Griffin, the only 2x Heisman winner, has years:[1974] only, not
     [1974, 1975]. Sections that show a year label it "AA Year," not
     "Heisman Year," and the natChamp section doesn't imply the year shown
     is when the title was actually won.
   - Pro Football Hall of Fame status is tracked as two separate booleans
     (CFB_GRID_PLAYERS.hof, 52 true; GRID_PLAYERS.hof, 158 true) for the
     same real honor, curated independently with no guaranteed overlap.
     v1's Hall of Fame section sources GRID_PLAYERS only rather than
     merging both pools with no dedup guarantee — a real "not done yet,"
     not an oversight. */
var LEARN_SECTIONS = [
  { id: 'cfbHeisman', league: 'cfb', icon: 'trophy', title: 'Heisman Trophy Winners',
    desc: 'Every Heisman winner tracked in the CFB player pool.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbMultiAA', league: 'cfb', icon: 'graduationCap', title: 'Multi-Time All-Americans',
    desc: 'Players named a consensus All-American more than once.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbNatChamp', league: 'cfb', icon: 'cfpTrophy', title: 'National Champions',
    desc: 'Players who were on a national championship roster.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'cfbAwards', league: 'cfb', icon: 'zap', title: 'Position Award Winners',
    desc: 'Maxwell, Outland, Lombardi, and 14 more national position awards.', dataFiles: ['data/cfb-grid.js'] },
  { id: 'nflHof', league: 'nfl', icon: 'hofJacket', title: 'Pro Football Hall of Fame',
    desc: 'Every Hall of Famer tracked in the NFL player pool.', dataFiles: ['data/grid.js'] },
  { id: 'nflDecorated', league: 'nfl', icon: 'target', title: 'Pro Bowl & All-Pro Selections',
    desc: 'Every player with at least one Pro Bowl or All-Pro nod.', dataFiles: ['data/grid.js'] },
  { id: 'cfbTrivia', league: 'cfb', icon: 'brain', title: 'CFB Trivia Almanac',
    desc: '456 real facts across Heisman history, coaches, rivalries, and more.', dataFiles: [] },
  { id: 'nflTrivia', league: 'nfl', icon: 'lombardiTrophy', title: 'NFL Trivia Almanac',
    desc: '482 real facts across Super Bowl history, records, and more.', dataFiles: [] }
];
function learnSectionById(id) { return LEARN_SECTIONS.find(function (s) { return s.id === id; }); }
function learnMatchesFilter(filter, searchBlob) {
  return !filter || normName(searchBlob).indexOf(normName(filter)) !== -1;
}
function learnEmptyRow(filter) {
  return '<tr><td colspan="5" class="mode-desc">No matches for "' + esc(filter) + '".</td></tr>';
}
// Category chips, added alongside the free-text filter so each section can
// also be narrowed by whatever grouping actually fits its data — position
// for the roster-stat sections, award name for cfbAwards, and the trivia
// bank's own `category` field for the two Trivia Almanac sections. Every
// section keeps its own `categories()` getter (same "duplicate per-section
// code" convention as the rest of this file) since what counts as a
// "category" genuinely differs per section; learnInCategory()/
// learnCategoryChips() are the only shared plumbing.
function learnUniqueSorted(arr) {
  var seen = {}, out = [];
  arr.forEach(function (v) { if (v && !seen[v]) { seen[v] = true; out.push(v); } });
  return out.sort();
}
function learnInCategory(selected, itemCats) {
  return !selected || itemCats.indexOf(selected) !== -1;
}
function learnCategoryChips(categories, selected) {
  if (!categories.length) return '';
  return '<div class="chip-row learn-chip-row">' +
    '<button class="chip-toggle' + (!selected ? ' active' : '') + '" data-learn-cat="">All</button>' +
    categories.map(function (c) {
      return '<button class="chip-toggle' + (c === selected ? ' active' : '') + '" data-learn-cat="' + esc(c) + '">' + esc(c) + '</button>';
    }).join('') +
    '</div>';
}

function learnCfbHeismanPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.heisman === true; }); }
function learnCfbHeismanCategories() {
  var pos = [];
  learnCfbHeismanPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbHeismanYear(p) { return p.heismanYear || p.years[0]; }
function learnCfbHeismanRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbHeismanPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return (learnCfbHeismanYear(a) || 0) - (learnCfbHeismanYear(b) || 0) || a.name.localeCompare(b.name); });
}
function renderLearnCfbHeisman() {
  var rows = learnCfbHeismanRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Year</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      var pos = p.positions.join('/');
      // Position shown both next to the name (so it's visible without
      // scrolling right on narrow screens) and in its own column.
      return '<tr><td>' + esc(p.name) + (pos ? ' <span class="learn-pos-tag">(' + esc(pos) + ')</span>' : '') + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(pos || '—') + '</td><td>' + (learnCfbHeismanYear(p) || '—') + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbMultiAAPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.multiAA === true; }); }
function learnCfbMultiAACategories() {
  var pos = [];
  learnCfbMultiAAPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbMultiAARows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbMultiAAPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return b.years.length - a.years.length || (a.years[0] || 0) - (b.years[0] || 0) || a.name.localeCompare(b.name); });
}
function renderLearnCfbMultiAA() {
  var rows = learnCfbMultiAARows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Selection Years</th><th>Times</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.years.slice().sort().join(', ')) + '</td><td>' + p.years.length + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbNatChampPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.natChamp === true; }); }
function learnCfbNatChampCategories() {
  var pos = [];
  learnCfbNatChampPool().forEach(function (p) { pos = pos.concat(p.positions); });
  return learnUniqueSorted(pos);
}
function learnCfbNatChampRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbNatChampPool()
    .filter(function (p) { return learnInCategory(cat, p.positions); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ')); })
    .sort(function (a, b) { return a.name.localeCompare(b.name); });
}
function renderLearnCfbNatChamp() {
  var rows = learnCfbNatChampRows();
  return '<p class="mode-desc">Players who were on a national championship roster at some point in their career. The AA Year column is their All-America selection year(s) for context — not necessarily the same season as the title.</p>' +
    '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>AA Year(s)</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.years.join(', ')) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnCfbAwardsPool() { return CFB_GRID_PLAYERS.filter(function (p) { return p.awards && p.awards.length > 0; }); }
function learnCfbAwardsCategories() {
  var aw = [];
  learnCfbAwardsPool().forEach(function (p) { aw = aw.concat(p.awards); });
  return learnUniqueSorted(aw);
}
function learnCfbAwardsRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnCfbAwardsPool()
    .filter(function (p) { return learnInCategory(cat, p.awards); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + p.schools.join(' ') + ' ' + p.awards.join(' ')); })
    .sort(function (a, b) { return a.awards.slice().sort()[0].localeCompare(b.awards.slice().sort()[0]) || a.name.localeCompare(b.name); });
}
function renderLearnCfbAwards() {
  var rows = learnCfbAwardsRows();
  return '<p class="mode-desc">17 real national position awards (Maxwell, Outland Trophy, Lombardi, Walter Camp, Davey O\'Brien, Jim Thorpe, Butkus, and more) — sorted by award. AA Year is their All-America selection year for context, not necessarily the same season as the award.</p>' +
    '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>School</th><th>Position</th><th>Award(s)</th><th>AA Year</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.schools.join(', ')) + '</td><td>' + esc(p.positions.join('/') || '—') + '</td><td>' + esc(p.awards.join(', ')) + '</td><td>' + (p.years[0] || '—') + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnEmptyCard(filter) {
  return '<p class="mode-desc">No matches for "' + esc(filter) + '".</p>';
}
function learnTriviaCategories(pool) {
  return learnUniqueSorted(pool.map(function (q) { return q.category; }));
}
function learnTriviaRows(pool) {
  var filter = state.learn.filter, cat = state.learn.category;
  return pool.filter(function (q) { return q.question && q.options && q.options.length; })
    .filter(function (q) { return learnInCategory(cat, [q.category]); })
    .filter(function (q) {
      return learnMatchesFilter(filter, q.category + ' ' + q.question + ' ' + (q.options[q.correctIndex] || '') + ' ' + (q.notes || ''));
    })
    .sort(function (a, b) { return a.category.localeCompare(b.category) || a.id - b.id; });
}
function renderLearnTriviaCards(rows) {
  return '<div class="learn-fact-list">' +
    (rows.length ? rows.map(function (q) {
      return '<div class="learn-fact-card">' +
        '<span class="learn-pill">' + esc(q.category) + '</span>' +
        '<div class="learn-fact-q">' + esc(q.question) + '</div>' +
        '<div class="learn-fact-a">' + esc(q.options[q.correctIndex]) + '</div>' +
        (q.notes ? '<div class="learn-fact-notes">' + esc(q.notes) + '</div>' : '') +
        '</div>';
    }).join('') : learnEmptyCard(state.learn.filter)) +
    '</div>';
}
function renderLearnCfbTrivia() {
  var rows = learnTriviaRows(CFB);
  return '<p class="mode-desc">' + rows.length + ' CFB facts across Heisman history, national championships, coaches, rivalries, and more — search by team, player, or topic.</p>' +
    renderLearnTriviaCards(rows);
}
function renderLearnNflTrivia() {
  var rows = learnTriviaRows(QUIZ);
  return '<p class="mode-desc">' + rows.length + ' NFL facts across Super Bowl history, franchise records, coaches, and more — search by team, player, or topic.</p>' +
    renderLearnTriviaCards(rows);
}

function learnNflHofPool() { return GRID_PLAYERS.filter(function (p) { return p.hof === true; }); }
function learnNflHofCategories() {
  return learnUniqueSorted(learnNflHofPool().map(function (p) { return p.position; }));
}
function learnNflHofRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnNflHofPool()
    .filter(function (p) { return learnInCategory(cat, [p.position]); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + (p.college || '') + ' ' + p.teams.join(' ')); })
    .sort(function (a, b) { return a.name.localeCompare(b.name); });
}
function learnDraftLabel(p) {
  if (!p.draft) return '—';
  if (p.draft.round === 0) return 'Undrafted, ' + p.draft.year;
  return p.draft.round ? 'Round ' + p.draft.round + ', ' + p.draft.year : '—';
}
function renderLearnNflHof() {
  var rows = learnNflHofRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>Position</th><th>College</th><th>Teams</th><th>Draft</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.position || '—') + '</td><td>' + esc(p.college || '—') + '</td><td>' + esc(p.teams.join(', ')) + '</td><td>' + esc(learnDraftLabel(p)) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnNflDecoratedPool() { return GRID_PLAYERS.filter(function (p) { return (p.proBowls || 0) > 0 || (p.allPro || 0) > 0; }); }
function learnNflDecoratedCategories() {
  return learnUniqueSorted(learnNflDecoratedPool().map(function (p) { return p.position; }));
}
function learnNflDecoratedRows() {
  var filter = state.learn.filter, cat = state.learn.category;
  return learnNflDecoratedPool()
    .filter(function (p) { return learnInCategory(cat, [p.position]); })
    .filter(function (p) { return learnMatchesFilter(filter, p.name + ' ' + (p.college || '') + ' ' + p.teams.join(' ')); })
    .sort(function (a, b) { return ((b.proBowls || 0) + (b.allPro || 0)) - ((a.proBowls || 0) + (a.allPro || 0)) || (b.proBowls || 0) - (a.proBowls || 0) || a.name.localeCompare(b.name); });
}
function learnBadges(p) {
  var b = [];
  if (p.mvp) b.push('MVP');
  if (p.sbChamp) b.push('SB Champ');
  if (p.sbMVP) b.push('SB MVP');
  return b.length ? b.map(function (x) { return '<span class="learn-pill">' + esc(x) + '</span>'; }).join(' ') : '—';
}
function renderLearnNflDecorated() {
  var rows = learnNflDecoratedRows();
  return '<div class="table-scroll"><table class="leaderboard-table"><thead><tr><th>Player</th><th>Position</th><th>Pro Bowls</th><th>All-Pro</th><th>Also</th></tr></thead><tbody>' +
    (rows.length ? rows.map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td>' + esc(p.position || '—') + '</td><td>' + (p.proBowls || 0) + '</td><td>' + (p.allPro || 0) + '</td><td>' + learnBadges(p) + '</td></tr>';
    }).join('') : learnEmptyRow(state.learn.filter)) +
    '</tbody></table></div>';
}

function learnSectionCategories(id) {
  return id === 'cfbHeisman' ? learnCfbHeismanCategories() :
    id === 'cfbMultiAA' ? learnCfbMultiAACategories() :
    id === 'cfbNatChamp' ? learnCfbNatChampCategories() :
    id === 'cfbAwards' ? learnCfbAwardsCategories() :
    id === 'nflHof' ? learnNflHofCategories() :
    id === 'nflDecorated' ? learnNflDecoratedCategories() :
    id === 'cfbTrivia' ? learnTriviaCategories(CFB) :
    id === 'nflTrivia' ? learnTriviaCategories(QUIZ) : [];
}
function learnSectionCardHtml(s) {
  return '<button class="mode-card" data-learn-open="' + s.id + '">' +
    '<div class="mode-icon">' + (s.image ? '<img src="' + esc(s.image) + '" alt="" />' : icon(s.icon)) + '</div>' +
    '<div class="mode-title">' + esc(s.title) + '</div>' +
    '<div class="mode-desc">' + esc(s.desc) + '</div>' +
    '</button>';
}
function renderLearnMenu() {
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Learn</h2>' +
    '<p class="mode-desc">Browse real NFL and College Football facts pulled straight from this app\'s own verified player data — Hall of Famers, Heisman winners, national champions, and more.</p>' +
    '<div class="mode-grid">' + LEARN_SECTIONS.map(learnSectionCardHtml).join('') + '</div>' +
    '</div>';
}
function renderLearnSectionDetail() {
  var s = learnSectionById(state.learn.sectionId);
  if (!s) return renderLearnMenu();
  var body =
    s.id === 'cfbHeisman' ? renderLearnCfbHeisman() :
    s.id === 'cfbMultiAA' ? renderLearnCfbMultiAA() :
    s.id === 'cfbNatChamp' ? renderLearnCfbNatChamp() :
    s.id === 'cfbAwards' ? renderLearnCfbAwards() :
    s.id === 'nflHof' ? renderLearnNflHof() :
    s.id === 'nflDecorated' ? renderLearnNflDecorated() :
    s.id === 'cfbTrivia' ? renderLearnCfbTrivia() :
    s.id === 'nflTrivia' ? renderLearnNflTrivia() : '';
  return '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' Back</button></div>' +
    '<h2 class="panel-title">' + esc(s.title) + '</h2>' +
    '<input id="learn-filter-input" class="learn-filter-input" placeholder="Filter by name, school, or team…" value="' + esc(state.learn.filter) + '" />' +
    learnCategoryChips(learnSectionCategories(s.id), state.learn.category) +
    body +
    '</div>';
}
function renderLearnScreen() {
  if (!state.learn) state.learn = { screen: 'menu', sectionId: null, filter: '', category: '', loadingSection: null, loadError: null };
  var s = state.learn;
  if (s.loadingSection) {
    var section = learnSectionById(s.loadingSection);
    return '<div class="panel loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading ' + esc(section ? section.title : 'section') + '…</div></div>';
  }
  if (s.loadError) {
    return '<div class="panel"><div class="mode-toolbar"><button class="btn-tiny" data-learn-back>' + icon('close') + ' Back</button></div>' +
      '<p class="mode-desc">Couldn’t load this section. Check your connection and try again.</p></div>';
  }
  return s.screen === 'section' ? renderLearnSectionDetail() : renderLearnMenu();
}
function learnBackToMenu() {
  state.learn = { screen: 'menu', sectionId: null, filter: '', category: '', loadingSection: null, loadError: null };
  renderAll();
}
function openLearnSection(id) {
  var s = state.learn, section = learnSectionById(id);
  if (!section) return;
  var pending = section.dataFiles.filter(function (f) { return !loadedScripts[f]; });
  if (pending.length) {
    s.loadingSection = id;
    s.loadError = null;
    renderAll();
    Promise.all(pending.map(loadScript)).then(function () {
      refreshDataAliases();
      s.loadingSection = null;
      s.screen = 'section';
      s.sectionId = id;
      s.filter = '';
      s.category = '';
      renderAll();
    }).catch(function () {
      s.loadingSection = null;
      s.loadError = id;
      renderAll();
    });
    return;
  }
  s.screen = 'section';
  s.sectionId = id;
  s.filter = '';
  s.category = '';
  renderAll();
}

/* ============================== friends ==============================
   No accounts, no requests to accept — just a local list of names you're
   tracking, matched against the same shared leaderboard/profile data every
   other cross-device feature this session already built (see
   pushProfileSnapshot()/pullProfileSnapshot() above). */
function renderFriendsScreen() {
  var friends = getFriends();
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">' + icon('users') + ' Friends</h2>' +
    '<p class="mode-desc">Add friends by the exact name they play under to see their Football Rating and streak. No accounts — just names.</p>' +
    '<div class="field-row"><input id="friend-name-input" placeholder="Friend’s name" autocomplete="off" maxlength="40" />' +
    '<button class="btn-primary" data-friend-add>Add</button></div>';
  if (!friends.length) {
    html += '<p class="mode-desc">No friends added yet.</p>';
  } else if (friendsLoading) {
    html += '<div class="loading-panel" aria-busy="true"><div class="loading-spinner"></div><div class="loading-text">Loading friends…</div></div>';
  } else {
    html += '<div class="friends-list">' + friends.map(friendRowHtml).join('') + '</div>';
  }
  html += '</div>';
  return html;
}
function friendRowHtml(name) {
  var slug = slugify(name);
  var rating = friendRatingFromLeaderboard(name);
  var profile = friendsProfileCache[slug];
  var streakCount = profile && profile.streak ? (profile.streak.count || 0) : 0;
  var statsBits = [];
  if (rating) statsBits.push(icon('football') + ' ' + rating.score + ' rating');
  else statsBits.push('No rating yet');
  if (streakCount > 0) statsBits.push(icon('flame') + ' ' + streakCount + '-day streak');
  return '<div class="friend-row">' +
    '<div class="friend-info"><div class="friend-name">' + esc(name) + '</div>' +
    '<div class="friend-stats">' + statsBits.join(' &middot; ') + '</div></div>' +
    '<button class="btn-tiny" data-friend-remove="' + esc(name) + '">' + icon('close') + ' Remove</button>' +
    '</div>';
}

/* ============================== profile ==============================
   A personal stats page — state.stats has been write-only until now (every
   finish* function updates it, nothing reads it back for display). Reuses
   LEADERBOARD_MODES' existing label/cols config against state.stats instead
   of state.leaderboardData, so the per-mode column definitions live in one
   place rather than being duplicated for this screen. */
/* ============================== achievement badges ==============================
   Computed live from state.stats/getStreak() every time the Profile page
   renders — no separate "earned badges" data to keep in sync, a badge is
   just a threshold check against data every mode already tracks. */
var BADGES = [
  { id: 'perfectGrid', icon: '🔲', title: 'Perfect Grid', desc: 'Clean-swept the NFL Immaculate Grid (9/9).', check: function (st) { return (st.grid.cleanSweeps || 0) > 0; } },
  { id: 'perfectCfbGrid', icon: '🔲', title: 'CFB Perfect Grid', desc: 'Clean-swept the CFB Immaculate Grid (9/9).', check: function (st) { return (st.cfbGrid.cleanSweeps || 0) > 0; } },
  { id: 'blitzMaster', icon: '⏱️', title: 'Blitz Master', desc: 'Matched 20+ answers in a single NFL Blitz round.', check: function (st) { return (st.blitz.bestMatched || 0) >= 20; } },
  { id: 'cfbBlitzMaster', icon: '⏱️', title: 'CFB Blitz Master', desc: 'Matched 20+ answers in a single CFB Blitz round.', check: function (st) { return (st.cfbBlitz.bestMatched || 0) >= 20; } },
  { id: 'speedDemon', icon: '⚡', title: 'Speed Demon', desc: 'Built a 10+ answer streak in NFL Speed.', check: function (st) { return (st.speed.bestStreak || 0) >= 10; } },
  { id: 'cfbSpeedDemon', icon: '⚡', title: 'CFB Speed Demon', desc: 'Built a 10+ answer streak in CFB Speed.', check: function (st) { return (st.cfbSpeed.bestStreak || 0) >= 10; } },
  { id: 'genius', icon: '🧠', title: 'Football Genius', desc: 'Scored 140+ on the Football IQ Test.', check: function (st) { return (st.iq.bestIQ || 0) >= 140; } },
  { id: 'cfbGenius', icon: '📚', title: 'CFB Genius', desc: 'Scored 140+ on the College Football IQ Test.', check: function (st) { return (st.cfbIq.bestIQ || 0) >= 140; } },
  { id: 'sharpshooter', icon: '🎯', title: 'Sharpshooter', desc: '90%+ on an NFL Quiz round.', check: function (st) { return (st.quiz.bestPct || 0) >= 90; } },
  { id: 'cfbSpecialist', icon: '🎓', title: 'CFB Specialist', desc: 'Played 20+ rounds across every College Football mode combined.', check: function (st) {
    return (st.cfbQuiz.roundsPlayed || 0) + (st.cfbGrid.gamesPlayed || 0) + (st.cfbBlitz.attempts || 0) + (st.cfbSpeed.sessionsPlayed || 0) + (st.cfbIq.testsTaken || 0) + (st.cfbLegends.gamesPlayed || 0) >= 20;
  } },
  { id: 'perfectSeason', icon: '🏆', title: 'Perfect Season', desc: 'Drafted a 17-0 team that actually went 17-0.', check: function (st) { return (st.legends.bestWins || 0) >= 17; } },
  { id: 'perfect12', icon: '🏆', title: 'Perfect 12-0', desc: 'Drafted a CFB 12-0 team that actually went undefeated and won the National Championship.', check: function (st) { return (st.cfbLegends.bestWins || 0) >= 12; } },
  { id: 'sharpEye', icon: '🕵️', title: 'Sharp Eye', desc: '5+ quick guesses (few clues used) in one Silhouette round.', check: function (st) { return (st.silhouette.bestQuick || 0) >= 5; } },
  { id: 'onFire', icon: '🔥', title: 'On Fire', desc: 'Hit a 7-day Daily Challenge streak.', check: function (st, streak) { return streak.count >= 7; } },
  { id: 'dailyGrinder', icon: '📅', title: 'Daily Grinder', desc: 'Completed 10+ Daily Challenges.', check: function (st) { return (st.daily.completions || 0) >= 10; } },
  { id: 'rivalry', icon: '⚔️', title: 'Got Next', desc: 'Won a Head-to-Head match against a friend.', check: function (st) { return (st.h2h.wins || 0) >= 1; } },
  { id: 'higherLowerStreak', icon: '📈', title: 'On a Heater', desc: 'Built a 15+ player streak in Higher or Lower.', check: function (st) { return (st.higherLower.bestStreak || 0) >= 15; } }
];
function earnedBadges() {
  var st = state.stats, streak = getStreak();
  return BADGES.filter(function (b) { return b.check(st, streak); });
}

/* ============================== rating history (sparkline) ==============================
   A capped local-only history of Football Rating values, appended every time
   it actually changes (updateRatingDrift, plus the one-time intro-test
   seed) — not synced to Firebase, purely a personal "how has this moved"
   visual on the Profile page. */
var RATING_HISTORY_MAX = 20;
function ratingHistoryKey() { return 'nflTriviaRatingHistory__' + slugify(state.name); }
function getRatingHistory() { return state.name ? lsGet(ratingHistoryKey(), []) : []; }
function pushRatingHistory(score) {
  if (!state.name) return;
  var h = getRatingHistory();
  h.push(score);
  if (h.length > RATING_HISTORY_MAX) h = h.slice(h.length - RATING_HISTORY_MAX);
  lsSet(ratingHistoryKey(), h);
}
function ratingSparklineSvg(history) {
  if (!history || history.length < 2) return '';
  var w = 160, h = 40, pad = 4;
  var min = Math.min.apply(null, history), max = Math.max.apply(null, history);
  var range = max - min || 1;
  var points = history.map(function (v, i) {
    var x = pad + (i / (history.length - 1)) * (w - pad * 2);
    var y = h - pad - ((v - min) / range) * (h - pad * 2);
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
  return '<svg class="rating-sparkline" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none" aria-hidden="true">' +
    '<polyline points="' + points + '" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>';
}

function renderProfile() {
  var r = getRating();
  var streak = getStreak();
  var html = '<div class="panel">' +
    '<div class="mode-toolbar"><button class="btn-tiny" data-go="settings">' + icon('settings') + ' Settings</button><button class="btn-tiny" data-go="home">' + icon('close') + ' Exit to Home</button></div>' +
    '<h2 class="panel-title">Your Profile</h2>' +
    (state.name ? '<p class="mode-desc">Playing as <b>' + esc(state.name) + '</b></p>' : '<p class="mode-desc">Enter a name above to start tracking a profile.</p>');
  if (r) {
    var sparkline = ratingSparklineSvg(getRatingHistory());
    html += '<div class="profile-headline-row">' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('football') + ' ' + r.score + '</div><div class="profile-headline-label">Football Rating &middot; ' + (r.games || 0) + ' games</div>' + sparkline + '</div>' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('flame') + ' ' + streak.count + '</div><div class="profile-headline-label">Day' + (streak.count === 1 ? '' : 's') + ' streak</div></div>' +
      '</div>';
  }
  var earned = earnedBadges();
  html += '<div class="profile-badges-title">Badges (' + earned.length + ' / ' + BADGES.length + ')</div>' +
    '<div class="profile-badges-grid">' +
    BADGES.map(function (b) {
      var got = earned.indexOf(b) !== -1;
      return '<div class="profile-badge' + (got ? ' earned' : '') + '" title="' + esc(b.desc) + '">' +
        '<div class="profile-badge-icon">' + (got ? b.icon : '🔒') + '</div>' +
        '<div class="profile-badge-title">' + esc(b.title) + '</div>' +
        '</div>';
    }).join('') +
    '</div>';
  html += '</div>';
  html += '<div class="profile-mode-grid">' + profileModeCardsHtml() + '</div>';
  return html;
}
// Shared by the full Profile page and the tappable Football Rating popup
// (openRatingModal below) — both show the same per-mode breakdown that
// feeds the one drifting rating, just in different containers.
function profileModeCardsHtml() {
  return LEADERBOARD_MODES.filter(function (m) { return m.id !== 'rating'; }).map(function (m) {
    var st = state.stats[m.id] || {};
    // bestRecord (17-0 / CFB 12-0) is only ever computed at leaderboard-push
    // time from bestWins, never stored in state.stats itself — derive it
    // here the same way rather than showing a stale/blank value. The two
    // modes have different regular-season lengths (17 games NFL, 12 games CFB).
    var getVal = function (key) {
      if (key === 'bestRecord' && st.bestRecord == null && st.bestWins != null) {
        var perfectGames = m.id === 'cfbLegends' ? 12 : 17;
        return st.bestWins + '-' + (perfectGames - st.bestWins);
      }
      return st[key] != null ? st[key] : 0;
    };
    return '<div class="profile-mode-card">' +
      '<div class="profile-mode-title">' + esc(m.label) + '</div>' +
      m.cols.map(function (c) { return '<div class="profile-mode-stat"><span>' + esc(c[1]) + '</span><b>' + esc(getVal(c[0])) + '</b></div>'; }).join('') +
      '</div>';
  }).join('');
}
var ratingModalTriggerEl = null;
function openRatingModal() {
  var r = getRating();
  if (!r) return;
  ratingModalTriggerEl = document.activeElement;
  var streak = getStreak();
  var sparkline = ratingSparklineSvg(getRatingHistory());
  var summary = document.getElementById('rating-modal-summary');
  if (summary) {
    summary.innerHTML = '<div class="profile-headline-row">' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('football') + ' ' + r.score + '</div><div class="profile-headline-label">Football Rating &middot; ' + (r.games || 0) + ' games</div>' + sparkline + '</div>' +
      '<div class="profile-headline"><div class="profile-headline-value">' + icon('flame') + ' ' + streak.count + '</div><div class="profile-headline-label">Day' + (streak.count === 1 ? '' : 's') + ' streak</div></div>' +
      '</div>';
  }
  var breakdown = document.getElementById('rating-modal-breakdown');
  if (breakdown) breakdown.innerHTML = profileModeCardsHtml();
  var modal = document.getElementById('rating-modal');
  var backdrop = document.getElementById('rating-backdrop');
  if (modal) modal.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  setTimeout(function () {
    var closeBtn = document.getElementById('rating-close');
    if (closeBtn) closeBtn.focus();
  }, 0);
}
function closeRatingModal() {
  var modal = document.getElementById('rating-modal');
  var backdrop = document.getElementById('rating-backdrop');
  if (modal) modal.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (ratingModalTriggerEl && document.contains(ratingModalTriggerEl)) ratingModalTriggerEl.focus();
  ratingModalTriggerEl = null;
}

/* ============================== render ============================== */
function renderAll() {
  var app = document.getElementById('app');
  if (!app) return;
  var html = nameBarHtml();
  if (state.screen === 'home') html += renderHome();
  else if (state.screen === 'quiz') html += renderQuizScreen();
  else if (state.screen === 'grid') html += renderGridScreen();
  else if (state.screen === 'blitz') html += renderBlitzScreen();
  else if (state.screen === 'speed') html += renderSpeedScreen();
  else if (state.screen === 'higherLower') html += renderHigherLowerScreen();
  else if (state.screen === 'silhouette') html += renderSilhouetteScreen();
  else if (state.screen === 'iq') html += renderIQScreen();
  else if (state.screen === 'legends') html += renderLegendsScreen();
  else if (state.screen === 'cfbQuiz') html += renderCfbScreen();
  else if (state.screen === 'cfbIq') html += renderCfbIQScreen();
  else if (state.screen === 'cfbSpeed') html += renderCfbSpeedScreen();
  else if (state.screen === 'cfbBlitz') html += renderCfbBlitzScreen();
  else if (state.screen === 'cfbGrid') html += renderCfbGridScreen();
  else if (state.screen === 'cfbLegends') html += renderCfbLegendsScreen();
  else if (state.screen === 'leaderboard') html += renderLeaderboard();
  else if (state.screen === 'profile') html += renderProfile();
  else if (state.screen === 'settings') html += renderSettings();
  else if (state.screen === 'daily') html += renderDailyScreen();
  else if (state.screen === 'introTest') html += renderIntroScreen();
  else if (state.screen === 'stats') html += renderStatsScreen();
  else if (state.screen === 'about') html += renderAbout();
  else if (state.screen === 'privacy') html += renderPrivacy();
  else if (state.screen === 'reports') html += renderReportsScreen();
  else if (state.screen === 'h2h') html += renderH2HScreen();
  else if (state.screen === 'learn') html += renderLearnScreen();
  else if (state.screen === 'friends') html += renderFriendsScreen();
  else if (state.screen === 'h2hLive') html += renderH2HLiveScreen();
  else if (state.screen === 'study') html += renderStudyScreen();
  app.innerHTML = html;
  renderRatingBadge();
  applyFavoriteTeamAccent();
  if (typeof syncBgMusic === 'function') syncBgMusic();

  var specificFocusHandled = false;
  var nameInput = document.getElementById('name-input');
  if (nameInput) { nameInput.focus(); specificFocusHandled = true; }
  var gridInput = document.getElementById('grid-input');
  if (gridInput) { gridInput.focus(); gridInput.setSelectionRange(gridInput.value.length, gridInput.value.length); specificFocusHandled = true; }
  var cfbGridInput = document.getElementById('cfb-grid-input');
  if (cfbGridInput) { cfbGridInput.focus(); cfbGridInput.setSelectionRange(cfbGridInput.value.length, cfbGridInput.value.length); specificFocusHandled = true; }
  var blitzInput = document.getElementById('blitz-input');
  if (blitzInput) { blitzInput.focus(); blitzInput.setSelectionRange(blitzInput.value.length, blitzInput.value.length); specificFocusHandled = true; }
  var cfbBlitzInput = document.getElementById('cfb-blitz-input');
  if (cfbBlitzInput) { cfbBlitzInput.focus(); cfbBlitzInput.setSelectionRange(cfbBlitzInput.value.length, cfbBlitzInput.value.length); specificFocusHandled = true; }
  var silhouetteInput = document.getElementById('silhouette-input');
  if (silhouetteInput) { silhouetteInput.focus(); silhouetteInput.setSelectionRange(silhouetteInput.value.length, silhouetteInput.value.length); specificFocusHandled = true; }
  // The Learn filter box re-renders the whole table on every keystroke
  // (see the 'input' listener above) — without this, the innerHTML replace
  // would steal focus after the very first character typed.
  var learnFilterInput = document.getElementById('learn-filter-input');
  if (learnFilterInput) { learnFilterInput.focus(); learnFilterInput.setSelectionRange(learnFilterInput.value.length, learnFilterInput.value.length); specificFocusHandled = true; }

  // Move focus to the new screen's content on real navigation (mode A -> mode
  // B), so screen-reader users get announced into the new panel instead of
  // focus silently falling back to <body> (innerHTML replacement destroys
  // whatever was previously focused). Deliberately skipped when a specific
  // input above already claimed focus, and only fires on an actual screen
  // change — not on every re-render within the same mode (e.g. answering a
  // quiz question), which would be disruptive rather than helpful.
  if (!specificFocusHandled && state.screen !== lastFocusedScreen) {
    app.focus({ preventScroll: true });
  }
  lastFocusedScreen = state.screen;

  var navScreenMatch = function (btn) { btn.classList.toggle('active', btn.dataset.go === state.screen); };
  document.querySelectorAll('#top-nav [data-go], #bottom-nav [data-go]').forEach(navScreenMatch);
  var currentLeague = LEAGUE_MODES.nfl.some(function (m) { return m.id === state.screen; }) ? 'nfl'
    : LEAGUE_MODES.cfb.some(function (m) { return m.id === state.screen; }) ? 'cfb' : null;
  document.querySelectorAll('[data-league-toggle]').forEach(function (btn) {
    btn.classList.toggle('active', btn.dataset.leagueToggle === currentLeague);
  });
}

/* ============================== typeahead ==============================
   A custom-styled autocomplete dropdown, replacing the browser's native
   <input list="..."> datalist for the three modes that search a real player
   pool (NFL/CFB Grid, Silhouette). Datalist's suggestion popup can't be
   restyled at all in Safari/Firefox and only minimally in Chrome, so no
   amount of CSS was ever going to make it look like the rest of this app —
   it was always going to read as a bare OS control. Deliberately NOT wired
   through renderAll() (which would steal focus and rebuild the whole screen
   on every keystroke — the same reason state.grid.input etc. are tracked
   silently below with an early `return`) — this writes directly into its
   own small sibling <div>, same technique the team-picker/Learn filter
   searches already use for a live-updating list. */
var TYPEAHEAD_CONFIGS = {
  'grid-input': {
    pool: function () { return GRID_PLAYERS; },
    exclude: function () { return state.grid ? state.grid.usedPlayers : []; },
    onPick: function (name) { state.grid.input = name; submitGridGuess(); }
  },
  'cfb-grid-input': {
    pool: function () { return CFB_GRID_PLAYERS; },
    exclude: function () { return state.cfbGrid ? state.cfbGrid.usedPlayers : []; },
    onPick: function (name) { state.cfbGrid.input = name; submitCfbGridGuess(); }
  },
  'silhouette-input': {
    pool: function () { return SILHOUETTE_PLAYERS; },
    exclude: function () { return []; },
    onPick: function (name) { state.silhouette.input = name; submitSilhouetteGuess(); }
  }
};
var typeaheadActiveIndex = -1;
function typeaheadListEl(inputId) { return document.getElementById(inputId + '-typeahead'); }
function typeaheadMatches(inputId, query) {
  var cfg = TYPEAHEAD_CONFIGS[inputId];
  var norm = normName(query);
  if (!cfg || !norm) return [];
  var excluded = cfg.exclude();
  return cfg.pool().filter(function (p) {
    return normName(p.name).indexOf(norm) !== -1 && excluded.indexOf(p.name) === -1;
  }).slice(0, 8);
}
// Plain case-insensitive indexOf against the real (non-normalized) name —
// matching itself uses normName so "Ja'Marr" still matches a query typed
// without the apostrophe, but that's overkill for just deciding where to
// draw a <mark>: worst case for the rare name where the two disagree is a
// suggestion with no highlight, not a wrong or broken one.
function typeaheadHighlight(name, query) {
  var q = query.trim();
  var idx = q ? name.toLowerCase().indexOf(q.toLowerCase()) : -1;
  if (idx === -1) return esc(name);
  return esc(name.slice(0, idx)) + '<mark>' + esc(name.slice(idx, idx + q.length)) + '</mark>' + esc(name.slice(idx + q.length));
}
function renderTypeahead(inputId) {
  var listEl = typeaheadListEl(inputId);
  var inputEl = document.getElementById(inputId);
  if (!listEl || !inputEl) return;
  var query = inputEl.value;
  var matches = typeaheadMatches(inputId, query);
  if (!matches.length) { listEl.innerHTML = ''; listEl.classList.remove('open'); inputEl.setAttribute('aria-expanded', 'false'); typeaheadActiveIndex = -1; return; }
  typeaheadActiveIndex = 0;
  listEl.innerHTML = matches.map(function (p, i) {
    return '<button type="button" role="option" class="typeahead-row' + (i === 0 ? ' active' : '') + '" data-typeahead-pick="' + esc(p.name) + '">' + typeaheadHighlight(p.name, query) + '</button>';
  }).join('');
  listEl.classList.add('open');
  inputEl.setAttribute('aria-expanded', 'true');
}
function closeTypeahead(inputId) {
  var listEl = typeaheadListEl(inputId);
  var inputEl = document.getElementById(inputId);
  if (listEl) { listEl.innerHTML = ''; listEl.classList.remove('open'); }
  if (inputEl) inputEl.setAttribute('aria-expanded', 'false');
  typeaheadActiveIndex = -1;
}
function typeaheadMove(inputId, delta) {
  var listEl = typeaheadListEl(inputId);
  if (!listEl) return false;
  var rows = listEl.querySelectorAll('.typeahead-row');
  if (!rows.length) return false;
  typeaheadActiveIndex = (typeaheadActiveIndex + delta + rows.length) % rows.length;
  rows.forEach(function (r, i) { r.classList.toggle('active', i === typeaheadActiveIndex); });
  rows[typeaheadActiveIndex].scrollIntoView({ block: 'nearest' });
  return true;
}
// Enter should commit whichever suggestion is highlighted when the dropdown
// is open (standard combobox behavior), but fall through to the existing
// submit-whatever-was-typed flow when it's closed/empty — e.g. someone
// pastes/types an exact name and hits Enter before any matches render.
function typeaheadPickActive(inputId) {
  var listEl = typeaheadListEl(inputId);
  if (!listEl || !listEl.classList.contains('open')) return false;
  var rows = listEl.querySelectorAll('.typeahead-row');
  if (!rows.length || typeaheadActiveIndex < 0) return false;
  var name = rows[typeaheadActiveIndex].dataset.typeaheadPick;
  closeTypeahead(inputId);
  TYPEAHEAD_CONFIGS[inputId].onPick(name);
  return true;
}

/* ============================== events ============================== */
document.addEventListener('click', function (e) {
  var t = e.target.closest('[data-go], [data-change-name], [data-save-name], ' +
    '[data-quiz-roundsize], [data-quiz-start], [data-quiz-answer], [data-quiz-next], [data-quiz-again], [data-quiz-setup], ' +
    '[data-study-start], [data-study-answer], [data-study-next], ' +
    '[data-grid-start], [data-grid-cell], [data-grid-submit], [data-grid-again], ' +
    '[data-blitz-list], [data-blitz-start], [data-blitz-submit], [data-blitz-setup], ' +
    '[data-speed-start], [data-speed-answer], [data-leaderboard-mode], [data-leaderboard-range], ' +
    '[data-hl-start], [data-hl-guess], [data-hl-continue], [data-hl-stat], ' +
    '[data-silhouette-start], [data-silhouette-submit], [data-silhouette-hint], [data-silhouette-giveup], [data-silhouette-next], ' +
    '[data-iq-start], [data-iq-answer], ' +
    '[data-legends-start], [data-legends-pick], [data-legends-reroll-team], [data-legends-reroll-year], ' +
    '[data-cfb-legends-start], [data-cfb-legends-pick], [data-cfb-legends-reroll-team], [data-cfb-legends-reroll-year], ' +
    '[data-cfb-roundsize], [data-cfb-start], [data-cfb-answer], [data-cfb-next], [data-cfb-again], [data-cfb-setup], ' +
    '[data-cfb-iq-start], [data-cfb-iq-answer], ' +
    '[data-cfb-speed-start], [data-cfb-speed-answer], ' +
    '[data-cfb-blitz-list], [data-cfb-blitz-start], [data-cfb-blitz-submit], [data-cfb-blitz-setup], ' +
    '[data-cfb-grid-start], [data-cfb-grid-cell], [data-cfb-grid-submit], [data-cfb-grid-again], ' +
    '[data-intro-begin], [data-intro-answer], [data-intro-skip], [data-intro-continue], [data-retake-intro], ' +
    '[data-daily-start], [data-daily-answer], [data-daily-next], ' +
    '[data-ranked-toggle], ' +
    '[data-share], #share-close, #share-backdrop, #share-download, #share-x, #share-facebook, #share-copy, [data-share-format], ' +
    '[data-report], #report-close, #report-backdrop, #report-submit, [data-report-category], [data-copy-email], ' +
    '#rating-badge, #rating-close, #rating-backdrop, ' +
    '#pin-close, #pin-backdrop, #pin-submit, #pin-skip, ' +
    '#team-picker-toggle, #team-picker-close, #team-picker-backdrop, [data-team-tab], [data-team-pick], [data-team-clear], [data-team-done], [data-team-picker-toggle], [data-team-prompt-dismiss], ' +
    '[data-settings-mute-toggle], [data-settings-push-toggle], [data-settings-clear-ask], [data-settings-clear-confirm], [data-settings-clear-cancel], ' +
    '[data-h2h-go-create], [data-h2h-go-join], [data-h2h-back-menu], [data-h2h-roundsize], [data-h2h-create], ' +
    '[data-h2h-join], [data-h2h-open-code], [data-h2h-start-play], [data-h2h-answer], [data-h2h-next], [data-h2h-exit], ' +
    '[data-h2h-live-go-create], [data-h2h-live-go-join], [data-h2h-live-back-menu], [data-h2h-live-roundsize], [data-h2h-live-create], ' +
    '[data-h2h-live-join], [data-h2h-live-ready], [data-h2h-live-share-link], [data-h2h-live-answer], [data-h2h-live-exit], ' +
    '[data-learn-open], [data-learn-back], [data-learn-cat], ' +
    '[data-friend-add], [data-friend-remove], ' +
    '[data-typeahead-pick], ' +
    '[data-league-toggle], #mode-sheet-close, #mode-sheet-backdrop, ' +
    '#help-toggle, #onboarding-next, #onboarding-skip, #onboarding-backdrop, [data-onboarding-sample-answer], ' +
    '[data-mode-restart], [data-mode-exit]');
  if (!t) return;

  if (t.id === 'help-toggle') {
    var helpMode = LEAGUE_MODES.nfl.concat(LEAGUE_MODES.cfb).find(function (x) { return x.id === state.screen; });
    openOnboarding(helpMode ? contextualHelpSteps(helpMode) : null);
    return;
  }
  if (t.dataset.onboardingSampleAnswer !== undefined) { onboardingPickSample(parseInt(t.dataset.onboardingSampleAnswer, 10)); return; }
  if (t.id === 'onboarding-next') { onboardingNext(); return; }
  if (t.id === 'onboarding-skip' || t.id === 'onboarding-backdrop') { closeOnboarding(); return; }
  if (t.dataset.share !== undefined) { shareResultCard(t.dataset.share); return; }
  if (t.id === 'share-close' || t.id === 'share-backdrop') { closeShareModal(); return; }
  if (t.id === 'share-download') { shareDownloadImage(); return; }
  if (t.id === 'share-x') { shareToX(); return; }
  if (t.id === 'share-facebook') { shareToFacebook(); return; }
  if (t.id === 'share-copy') { shareCopyText(); return; }
  if (t.dataset.shareFormat !== undefined) { if (t.dataset.shareFormat !== shareCurrentFormat) renderShareCard(t.dataset.shareFormat); return; }
  if (t.dataset.report !== undefined) { openReportModal(t.dataset.report); return; }
  if (t.id === 'report-close' || t.id === 'report-backdrop') { closeReportModal(); return; }
  if (t.dataset.reportCategory !== undefined) { setReportCategory(t.dataset.reportCategory); return; }
  if (t.id === 'report-submit') { submitReport(); return; }
  if (t.id === 'rating-badge') { openRatingModal(); return; }
  if (t.id === 'rating-close' || t.id === 'rating-backdrop') { closeRatingModal(); return; }
  if (t.id === 'pin-close' || t.id === 'pin-backdrop') { closePinModal(); return; }
  if (t.id === 'pin-submit') { pinModalSubmit(); return; }
  if (t.id === 'pin-skip') { pinModalSkip(); return; }
  if (t.id === 'team-picker-toggle' || t.dataset.teamPickerToggle !== undefined) { openTeamPicker(); return; }
  if (t.dataset.teamPromptDismiss !== undefined) { dismissTeamPrompt(); return; }
  if (t.dataset.settingsMuteToggle !== undefined) { toggleMute(); renderAll(); return; }
  if (t.dataset.settingsPushToggle !== undefined) { togglePushNotifications(); return; }
  if (t.dataset.settingsClearAsk !== undefined) { settingsClearDataAsk(); return; }
  if (t.dataset.settingsClearConfirm !== undefined) { clearAllUserData(); return; }
  if (t.dataset.settingsClearCancel !== undefined) { settingsClearDataCancel(); return; }
  if (t.id === 'team-picker-close' || t.id === 'team-picker-backdrop' || t.dataset.teamDone !== undefined) { closeTeamPicker(); return; }
  if (t.dataset.teamTab !== undefined) { teamPickerSetTab(t.dataset.teamTab); return; }
  if (t.dataset.teamPick !== undefined) { var tp = t.dataset.teamPick.split(':'); teamPickerPick(tp[0], tp.slice(1).join(':')); return; }
  if (t.dataset.teamClear !== undefined) { teamPickerClear(t.dataset.teamClear); return; }
  if (t.dataset.copyEmail !== undefined) { copyTextToClipboard(t.dataset.copyEmail, t); return; }
  if (t.dataset.h2hGoCreate !== undefined) { state.h2h.screen = 'create'; state.h2h.error = null; renderAll(); return; }
  if (t.dataset.h2hGoJoin !== undefined) { state.h2h.screen = 'join'; state.h2h.error = null; renderAll(); return; }
  if (t.dataset.h2hBackMenu !== undefined) { h2hBackToMenu(); return; }
  if (t.dataset.h2hRoundsize !== undefined) { h2hSetRoundSize(parseInt(t.dataset.h2hRoundsize, 10)); return; }
  if (t.dataset.h2hCreate !== undefined) {
    var h2hModeSel = document.getElementById('h2h-mode');
    h2hCreateMatch(h2hModeSel ? h2hModeSel.value : state.h2h.mode);
    return;
  }
  if (t.dataset.h2hJoin !== undefined) {
    var h2hCodeInput = document.getElementById('h2h-code-input');
    h2hJoinMatch(h2hCodeInput ? h2hCodeInput.value : '');
    return;
  }
  if (t.dataset.h2hOpenCode !== undefined) { h2hOpenExistingCode(t.dataset.h2hOpenCode); return; }
  if (t.dataset.h2hStartPlay !== undefined) { h2hStartPlaying(); return; }
  if (t.dataset.h2hAnswer !== undefined) { h2hPickAnswer(parseInt(t.dataset.h2hAnswer, 10)); return; }
  if (t.dataset.h2hNext !== undefined) { h2hNextQuestion(); return; }
  if (t.dataset.h2hExit !== undefined) { h2hStopWatch(); goToMode('home'); return; }
  if (t.dataset.h2hLiveGoCreate !== undefined) { state.h2hLive.screen = 'create'; state.h2hLive.error = null; renderAll(); return; }
  if (t.dataset.h2hLiveGoJoin !== undefined) { state.h2hLive.screen = 'join'; state.h2hLive.error = null; renderAll(); return; }
  if (t.dataset.h2hLiveBackMenu !== undefined) { h2hLiveBackToMenu(); return; }
  if (t.dataset.h2hLiveRoundsize !== undefined) { h2hLiveSetRoundSize(parseInt(t.dataset.h2hLiveRoundsize, 10)); return; }
  if (t.dataset.h2hLiveCreate !== undefined) { h2hLiveCreateMatch(); return; }
  if (t.dataset.h2hLiveJoin !== undefined) {
    var h2hLiveCodeInput = document.getElementById('h2h-live-code-input');
    h2hLiveJoinMatch(h2hLiveCodeInput ? h2hLiveCodeInput.value : '');
    return;
  }
  if (t.dataset.h2hLiveReady !== undefined) { h2hLiveSetReady(); return; }
  if (t.dataset.h2hLiveShareLink !== undefined) { h2hLiveShareLink(t.dataset.h2hLiveShareLink, t); return; }
  if (t.dataset.h2hLiveAnswer !== undefined) { h2hLivePickAnswer(parseInt(t.dataset.h2hLiveAnswer, 10)); return; }
  if (t.dataset.h2hLiveExit !== undefined) { h2hLiveStopWatch(); goToMode('home'); return; }
  if (t.dataset.learnOpen !== undefined) { openLearnSection(t.dataset.learnOpen); return; }
  if (t.dataset.learnBack !== undefined) { learnBackToMenu(); return; }
  if (t.dataset.learnCat !== undefined) { state.learn.category = t.dataset.learnCat; renderAll(); return; }
  if (t.dataset.friendAdd !== undefined) { var friendInput = document.getElementById('friend-name-input'); addFriend(friendInput ? friendInput.value : ''); return; }
  if (t.dataset.friendRemove !== undefined) { removeFriend(t.dataset.friendRemove); return; }
  if (t.dataset.typeaheadPick !== undefined) {
    var taListEl = t.closest('.typeahead-list');
    var taInputId = taListEl ? taListEl.id.replace(/-typeahead$/, '') : null;
    if (taInputId && TYPEAHEAD_CONFIGS[taInputId]) { closeTypeahead(taInputId); TYPEAHEAD_CONFIGS[taInputId].onPick(t.dataset.typeaheadPick); }
    return;
  }
  if (t.dataset.leagueToggle !== undefined) { toggleModeSheet(t.dataset.leagueToggle); return; }
  if (t.id === 'mode-sheet-close' || t.id === 'mode-sheet-backdrop') { closeModeSheet(); return; }
  if (t.dataset.go !== undefined) { closeModeSheet(); goToMode(t.dataset.go); return; }
  if (t.dataset.changeName !== undefined) { changeName(); return; }
  if (t.dataset.saveName !== undefined) { saveName(document.getElementById('name-input').value); return; }

  if (t.dataset.introBegin !== undefined) { beginIntroQuestions(); return; }
  if (t.dataset.introAnswer !== undefined) { answerIntroQuestion(parseInt(t.dataset.introAnswer, 10)); return; }
  if (t.dataset.introSkip !== undefined) { e.preventDefault(); skipIntroTest(); return; }
  if (t.dataset.introContinue !== undefined) { introTestDone(); return; }
  if (t.dataset.retakeIntro !== undefined) { retakeIntroTest(); return; }

  if (t.dataset.dailyStart !== undefined) { startDailyChallenge(); return; }
  if (t.dataset.dailyAnswer !== undefined) { pickDailyAnswer(parseInt(t.dataset.dailyAnswer, 10)); return; }
  if (t.dataset.dailyNext !== undefined) { nextDailyQuestion(); return; }

  if (t.dataset.rankedToggle !== undefined) {
    var parts = t.dataset.rankedToggle.split(':');
    setRankedPref(parts[0], parts[1] === '1');
    return;
  }

  if (t.dataset.quizRoundsize !== undefined) { state.quiz.roundSize = parseInt(t.dataset.quizRoundsize, 10); renderAll(); return; }
  if (t.dataset.quizStart !== undefined) {
    var cat = document.getElementById('quiz-cat'), diff = document.getElementById('quiz-diff');
    startQuizRound(cat ? cat.value : '', diff ? diff.value : '', state.quiz.roundSize);
    return;
  }
  if (t.dataset.quizAnswer !== undefined) { pickQuizAnswer(parseInt(t.dataset.quizAnswer, 10)); return; }
  if (t.dataset.quizNext !== undefined) { nextQuizQuestion(); return; }
  if (t.dataset.studyStart !== undefined) { startStudy(t.dataset.studyStart); return; }
  if (t.dataset.studyAnswer !== undefined) { pickStudyAnswer(parseInt(t.dataset.studyAnswer, 10)); return; }
  if (t.dataset.studyNext !== undefined) { nextStudyQuestion(); return; }
  if (t.dataset.quizAgain !== undefined) { playQuizAgain(); return; }
  if (t.dataset.quizSetup !== undefined) { quizBackToSetup(); return; }

  if (t.dataset.gridStart !== undefined) { startGridRound(); return; }
  if (t.dataset.gridCell !== undefined) { selectGridCell(parseInt(t.dataset.gridCell, 10)); return; }
  if (t.dataset.gridSubmit !== undefined) { submitGridGuess(); return; }
  if (t.dataset.gridAgain !== undefined) { startGridRound(); return; }

  if (t.dataset.cfbGridStart !== undefined) { startCfbGridRound(); return; }
  if (t.dataset.cfbGridCell !== undefined) { selectCfbGridCell(parseInt(t.dataset.cfbGridCell, 10)); return; }
  if (t.dataset.cfbGridSubmit !== undefined) { submitCfbGridGuess(); return; }
  if (t.dataset.cfbGridAgain !== undefined) { startCfbGridRound(); return; }

  if (t.dataset.blitzList !== undefined) { state.blitz = { listId: t.dataset.blitzList, screen: 'pickTimer' }; state.screen = 'blitz'; renderAll(); return; }
  if (t.dataset.blitzStart !== undefined) { startBlitz(t.dataset.blitzStart, parseInt(t.dataset.blitzTimer, 10)); return; }
  if (t.dataset.blitzSubmit !== undefined) { submitBlitzGuess(); return; }
  if (t.dataset.blitzSetup !== undefined) { state.blitz = null; renderAll(); return; }

  if (t.dataset.speedStart !== undefined) { startSpeedRound(parseInt(t.dataset.speedStart, 10)); return; }
  if (t.dataset.speedAnswer !== undefined) { registerSpeedAnswer(parseInt(t.dataset.speedAnswer, 10)); return; }
  if (t.dataset.hlStat !== undefined) { setHigherLowerStat(t.dataset.hlStat); return; }
  if (t.dataset.hlStart !== undefined) { startHigherLower(); return; }
  if (t.dataset.hlGuess !== undefined) { submitHigherLowerGuess(t.dataset.hlGuess); return; }
  if (t.dataset.hlContinue !== undefined) { higherLowerContinue(); return; }

  if (t.dataset.leaderboardMode !== undefined) { state.leaderboardMode = t.dataset.leaderboardMode; renderAll(); return; }
  if (t.dataset.leaderboardRange !== undefined) { state.leaderboardRange = t.dataset.leaderboardRange; renderAll(); return; }

  if (t.dataset.silhouetteStart !== undefined) { startSilhouetteRound(parseInt(t.dataset.silhouetteStart, 10)); return; }
  if (t.dataset.silhouetteSubmit !== undefined) { submitSilhouetteGuess(); return; }
  if (t.dataset.silhouetteHint !== undefined) { revealSilhouetteClue(); return; }
  if (t.dataset.silhouetteGiveup !== undefined) { giveUpSilhouette(); return; }
  if (t.dataset.silhouetteNext !== undefined) { advanceSilhouette(); return; }

  if (t.dataset.iqStart !== undefined) { startIQTest(); return; }
  if (t.dataset.iqAnswer !== undefined) { answerIQQuestion(parseInt(t.dataset.iqAnswer, 10)); return; }

  if (t.dataset.legendsStart !== undefined) { startLegends(); return; }
  if (t.dataset.legendsPick !== undefined) { legendsPickPlayer(parseInt(t.dataset.legendsPick, 10)); return; }
  if (t.dataset.legendsRerollTeam !== undefined) { legendsRerollTeam(); return; }
  if (t.dataset.legendsRerollYear !== undefined) { legendsRerollYear(); return; }

  if (t.dataset.cfbLegendsStart !== undefined) { startCfbLegends(); return; }
  if (t.dataset.cfbLegendsPick !== undefined) { cfbLegendsPickPlayer(parseInt(t.dataset.cfbLegendsPick, 10)); return; }
  if (t.dataset.cfbLegendsRerollTeam !== undefined) { cfbLegendsRerollTeam(); return; }
  if (t.dataset.cfbLegendsRerollYear !== undefined) { cfbLegendsRerollYear(); return; }

  if (t.dataset.cfbRoundsize !== undefined) { state.cfbQuiz.roundSize = parseInt(t.dataset.cfbRoundsize, 10); renderAll(); return; }
  if (t.dataset.cfbStart !== undefined) {
    var cfbCat = document.getElementById('cfb-cat'), cfbDiff = document.getElementById('cfb-diff');
    startCfbQuizRound(cfbCat ? cfbCat.value : '', cfbDiff ? cfbDiff.value : '', state.cfbQuiz.roundSize);
    return;
  }
  if (t.dataset.cfbAnswer !== undefined) { pickCfbAnswer(parseInt(t.dataset.cfbAnswer, 10)); return; }
  if (t.dataset.cfbNext !== undefined) { nextCfbQuestion(); return; }
  if (t.dataset.cfbAgain !== undefined) { playCfbAgain(); return; }
  if (t.dataset.cfbSetup !== undefined) { cfbBackToSetup(); return; }

  if (t.dataset.cfbIqStart !== undefined) { startCfbIQTest(); return; }
  if (t.dataset.cfbIqAnswer !== undefined) { answerCfbIQQuestion(parseInt(t.dataset.cfbIqAnswer, 10)); return; }

  if (t.dataset.cfbSpeedStart !== undefined) { startCfbSpeedRound(parseInt(t.dataset.cfbSpeedStart, 10)); return; }
  if (t.dataset.cfbSpeedAnswer !== undefined) { registerCfbSpeedAnswer(parseInt(t.dataset.cfbSpeedAnswer, 10)); return; }

  if (t.dataset.cfbBlitzList !== undefined) { state.cfbBlitz = { listId: t.dataset.cfbBlitzList, screen: 'pickTimer' }; state.screen = 'cfbBlitz'; renderAll(); return; }
  if (t.dataset.cfbBlitzStart !== undefined) { startCfbBlitz(t.dataset.cfbBlitzStart, parseInt(t.dataset.cfbBlitzTimer, 10)); return; }
  if (t.dataset.cfbBlitzSubmit !== undefined) { submitCfbBlitzGuess(); return; }
  if (t.dataset.cfbBlitzSetup !== undefined) { state.cfbBlitz = null; renderAll(); return; }

  if (t.dataset.modeRestart !== undefined) { stopTimers(); resetModeState(t.dataset.modeRestart); renderAll(); return; }
  if (t.dataset.modeExit !== undefined) { goToMode('home'); return; }
});

// Mobile keyboard polish: on a touch/coarse-pointer device (matchMedia guard
// so desktop mouse users never get an unwanted scroll-jump), nudge a just-
// focused game-answer input into view once the on-screen keyboard has had a
// moment to animate in. 'focus' doesn't bubble, so this needs the capture
// phase. Works alongside interactive-widget=resizes-content in index.html
// (which shrinks the layout viewport instead of letting the keyboard just
// overlay it) rather than replacing it — belt and suspenders, since browser
// support for that meta value still varies.
var MOBILE_KEYBOARD_INPUT_IDS = ['grid-input', 'cfb-grid-input', 'blitz-input', 'cfb-blitz-input', 'silhouette-input'];
document.addEventListener('focus', function (e) {
  if (MOBILE_KEYBOARD_INPUT_IDS.indexOf(e.target.id) === -1) return;
  if (!window.matchMedia || !window.matchMedia('(pointer: coarse)').matches) return;
  var el = e.target;
  setTimeout(function () { el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, 250);
}, true);
// blur fires (and a click-delegate handler runs closeTypeahead itself once a
// pick is actually made) before a tap on a suggestion button's own click
// event has a chance to fire — closing the list immediately here would
// remove it from the DOM mid-tap and the pick would silently do nothing.
// Delaying long enough for that click to land, then closing only if nothing
// else already did, is the standard fix for this exact race.
document.addEventListener('blur', function (e) {
  if (!TYPEAHEAD_CONFIGS[e.target.id]) return;
  setTimeout(function () { closeTypeahead(e.target.id); }, 200);
}, true);

document.addEventListener('input', function (e) {
  if (e.target.id === 'grid-input') { state.grid.input = e.target.value; renderTypeahead('grid-input'); return; }
  if (e.target.id === 'cfb-grid-input') { state.cfbGrid.input = e.target.value; renderTypeahead('cfb-grid-input'); return; }
  if (e.target.id === 'blitz-input') { state.blitz.input = e.target.value; return; }
  if (e.target.id === 'cfb-blitz-input') { state.cfbBlitz.input = e.target.value; return; }
  if (e.target.id === 'silhouette-input') { state.silhouette.input = e.target.value; renderTypeahead('silhouette-input'); return; }
  // Unlike the inputs above (which only read their value on submit, no
  // re-render per keystroke), the Learn filter box needs to narrow the
  // table live as you type — see renderAll()'s focus-preservation block
  // for the matching refocus step this requires.
  if (e.target.id === 'learn-filter-input') { state.learn.filter = e.target.value; renderAll(); return; }
  if (e.target.id === 'team-picker-search') { teamPickerSetFilter(e.target.value); return; }
});

document.addEventListener('change', function (e) {
  if (e.target.id === 'quiz-cat') { state.quiz.category = e.target.value; return; }
  if (e.target.id === 'quiz-diff') { state.quiz.difficulty = e.target.value; return; }
  if (e.target.id === 'cfb-cat') { state.cfbQuiz.category = e.target.value; return; }
  if (e.target.id === 'cfb-diff') { state.cfbQuiz.difficulty = e.target.value; return; }
  if (e.target.id === 'h2h-mode') { h2hSetMode(e.target.value); return; }
  if (e.target.id === 'h2h-list') { h2hSetList(e.target.value); return; }
  if (e.target.id === 'h2h-live-mode') { h2hLiveSetMode(e.target.value); return; }
});

// Keeps Tab cycling inside an open modal instead of escaping to whatever's
// behind the backdrop (standard WAI-ARIA dialog pattern) — Shift+Tab off the
// first focusable element wraps to the last, and Tab off the last wraps back
// to the first. Called from the keydown handler below, once per open dialog.
function trapTabKey(e, container) {
  var focusables = container.querySelectorAll('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])');
  if (!focusables.length) return;
  var first = focusables[0], last = focusables[focusables.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}
document.addEventListener('keydown', function (e) {
  var modeSheetEl = document.getElementById('mode-sheet');
  var onboardingModalEl = document.getElementById('onboarding-modal');
  var shareModalEl = document.getElementById('share-modal');
  var reportModalEl = document.getElementById('report-modal');
  var ratingModalEl = document.getElementById('rating-modal');
  var teamPickerModalEl = document.getElementById('team-picker-modal');
  var pinModalEl = document.getElementById('pin-modal');
  if (e.key === 'Escape' && TYPEAHEAD_CONFIGS[e.target.id] && typeaheadListEl(e.target.id) && typeaheadListEl(e.target.id).classList.contains('open')) {
    closeTypeahead(e.target.id);
    return;
  }
  if (e.key === 'Escape' && modeSheetOpenLeague) { closeModeSheet(); return; }
  if (e.key === 'Escape' && onboardingModalEl && onboardingModalEl.classList.contains('open')) { closeOnboarding(); return; }
  if (e.key === 'Escape' && shareModalEl && shareModalEl.classList.contains('open')) { closeShareModal(); return; }
  if (e.key === 'Escape' && reportModalEl && reportModalEl.classList.contains('open')) { closeReportModal(); return; }
  if (e.key === 'Escape' && ratingModalEl && ratingModalEl.classList.contains('open')) { closeRatingModal(); return; }
  if (e.key === 'Escape' && teamPickerModalEl && teamPickerModalEl.classList.contains('open')) { closeTeamPicker(); return; }
  if (e.key === 'Escape' && pinModalEl && pinModalEl.classList.contains('open')) { closePinModal(); return; }
  if (e.key === 'Tab') {
    if (modeSheetEl && modeSheetEl.classList.contains('open')) { trapTabKey(e, modeSheetEl); return; }
    if (onboardingModalEl && onboardingModalEl.classList.contains('open')) { trapTabKey(e, onboardingModalEl); return; }
    if (shareModalEl && shareModalEl.classList.contains('open')) { trapTabKey(e, shareModalEl); return; }
    if (reportModalEl && reportModalEl.classList.contains('open')) { trapTabKey(e, reportModalEl); return; }
    if (ratingModalEl && ratingModalEl.classList.contains('open')) { trapTabKey(e, ratingModalEl); return; }
    if (teamPickerModalEl && teamPickerModalEl.classList.contains('open')) { trapTabKey(e, teamPickerModalEl); return; }
    if (pinModalEl && pinModalEl.classList.contains('open')) { trapTabKey(e, pinModalEl); return; }
    return;
  }
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && TYPEAHEAD_CONFIGS[e.target.id]) {
    if (typeaheadMove(e.target.id, e.key === 'ArrowDown' ? 1 : -1)) e.preventDefault();
    return;
  }
  if (e.key !== 'Enter') return;
  if (e.target.id === 'grid-input') { if (!typeaheadPickActive('grid-input')) submitGridGuess(); }
  else if (e.target.id === 'cfb-grid-input') { if (!typeaheadPickActive('cfb-grid-input')) submitCfbGridGuess(); }
  else if (e.target.id === 'blitz-input') { submitBlitzGuess(); }
  else if (e.target.id === 'cfb-blitz-input') { submitCfbBlitzGuess(); }
  else if (e.target.id === 'silhouette-input') { if (!typeaheadPickActive('silhouette-input')) submitSilhouetteGuess(); }
  else if (e.target.id === 'name-input') { saveName(e.target.value); }
  else if (e.target.id === 'pin-input') { pinModalSubmit(); }
  else if (e.target.id === 'friend-name-input') { addFriend(e.target.value); }
});

/* ============================== init ============================== */
// Grid/CFB-Grid/Silhouette datalists are (re)built once their data file
// loads — see goToMode's lazy-load branch above — not unconditionally here,
// since GRID_PLAYERS/CFB_GRID_PLAYERS/SILHOUETTE_PLAYERS are empty until then.
var footerVersionEl = document.getElementById('footer-version');
if (footerVersionEl) footerVersionEl.textContent = 'Reads v' + APP_VERSION + ' · Questions last updated ' + CONTENT_UPDATED;

// A live-match invite link (see h2hLiveInviteLink) looks like
// https://getreads.netlify.app/#live=7F3K — captured and cleared from the
// URL immediately so refreshing or re-sharing the plain page URL later
// can't re-trigger a join. Consumed right here if this device already has a
// name (the common case — a friend who already plays tapping another
// friend's link), or later via consumePendingLiveJoin() from saveName()/
// introTestDone()/skipIntroTest() if this is a brand-new visitor who still
// has to pick a name and take the intro test first.
var pendingLiveJoinCode = null;
var liveHashMatch = /^#live=([A-Za-z0-9]{4})$/.exec(location.hash);
if (liveHashMatch) {
  pendingLiveJoinCode = liveHashMatch[1].toUpperCase();
  history.replaceState(null, '', location.pathname + location.search);
}
function consumePendingLiveJoin() {
  if (!pendingLiveJoinCode || !state.name) return false;
  var code = pendingLiveJoinCode;
  pendingLiveJoinCode = null;
  state.screen = 'h2hLive';
  state.h2hLive = { screen: 'menu', mode: 'quiz', roundSize: 10, code: null, match: null, mySlug: null, error: null };
  h2hLiveJoinMatch(code);
  return true;
}

var HIDDEN_ROUTES = { '#stats': 'stats', '#reports': 'reports' };
if (HIDDEN_ROUTES[location.hash]) {
  state.screen = HIDDEN_ROUTES[location.hash];
  renderAll();
} else if (state.name && !getRating()) { startIntroTest(); } else if (!consumePendingLiveJoin()) { renderAll(); }
if (!HIDDEN_ROUTES[location.hash] && !lsGet(ONBOARD_KEY, false) && !pendingLiveJoinCode) { openOnboarding(); }

// Splash screen: shown by default in index.html, fades out shortly after load
// regardless of Firebase connection state (so a slow/broken connection never
// leaves someone staring at it) — purely a branded loading moment, not a
// blocking gate on anything.
setTimeout(function () {
  var splash = document.getElementById('splash-screen');
  if (!splash) return;
  splash.classList.add('splash-hidden');
  setTimeout(function () { splash.style.display = 'none'; }, 550);
}, 1300);

// Service workers require http(s) (or localhost) — this silently no-ops over
// file://, same documented limitation as the shared leaderboard sync. No need
// to warn about it; solo play already works fully offline without it.
if ('serviceWorker' in navigator && (location.protocol === 'http:' || location.protocol === 'https:')) {
  navigator.serviceWorker.register('sw.js').catch(function () {});
}
