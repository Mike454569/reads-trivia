// Shared live leaderboard sync via Firebase Firestore.
//
// Reuses the same Firebase project as ../draft-app/firebase-sync.js (it's
// the same owner's project), but writes to its own collection so this app's
// scores never collide with the draft app's separate trivia leaderboard.
//
// This module talks to app.js (a plain classic script, loaded before this
// one) through a small bridge on window:
//   window.__triviaSync.applyLeaderboard(list)   <- defined by app.js, called here
//   window.__fbSync.pushScore(docId, data)        <- defined here, called by app.js
//   window.__fbSync.logPlay(mode)                 <- defined here, called by app.js
//   window.__fbSync.submitReport(payload)          <- defined here, called by app.js
//   window.__fbSync.getMatch(code)                 <- defined here, called by app.js (Promise)
//   window.__fbSync.setMatch(code, data, merge)     <- defined here, called by app.js
//   window.__fbSync.watchMatch(code, cb)            <- defined here, called by app.js (returns unsubscribe)
//   window.__fbSync.pushProfile(nameSlug, data)     <- defined here, called by app.js
//   window.__fbSync.getProfile(nameSlug)            <- defined here, called by app.js (Promise)
//   window.__fbSync.getNamePin(nameSlug)            <- defined here, called by app.js (Promise)
//   window.__fbSync.setNamePin(nameSlug, pinHash)   <- defined here, called by app.js
//   window.__fbSync.status                        <- 'connecting' | 'live' | 'offline'
//
// pushProfile/getProfile back cross-device sync for per-mode stats/badges/
// streak (see pushProfileSnapshot()/pullProfileSnapshot() in app.js) — the
// same "one doc per name, no password" idea the rating sync above already
// used, just extended to the rest of state.stats. One doc per name (not
// per-device, unlike the leaderboard), fetched once (not a live listener —
// unlike the leaderboard, nobody else needs to watch your stats update in
// real time) and merged field-by-field client-side, taking whichever
// device's value is further along for each stat independently.
//
// getMatch/setMatch/watchMatch back the async Head-to-Head mode (see the
// "head-to-head" section of app.js): one Firestore doc per match, keyed by
// a short room code the two players share out-of-band (text/Discord/etc).
// Deliberately plain reads/writes, no transaction — at this app's scale
// (a handful of friends), two people racing to join the same open slot in
// the same instant isn't a real risk, and a transaction would be a lot of
// complexity for a scenario that won't happen in practice.
//
// getNamePin/setNamePin back the lightweight "claim your name with a PIN"
// deterrent (see saveName() in app.js): one doc per name slug holding a weak
// client-side hash of a 4-digit PIN, not a real password. This is an honest
// soft deterrent, not real security — nothing here is enforced by Firestore
// rules, so anyone determined enough to open devtools could still write
// under a claimed name. It exists to stop the actual reported problem
// (someone casually typing a friend's name in the UI to mess with their
// leaderboard score), not a motivated attacker.
//
// logPlay() is the whole "analytics" story for this app, by deliberate
// choice over a third-party tool (Plausible/GA): one shared Firestore doc
// with a Firestore increment() counter per mode ID, no external script, no
// per-user tracking, no vendor account. Not gated behind real auth (this
// app has no admin/owner role at all) — see renderStatsScreen() in app.js
// for how it's viewed, and its comment for why "hidden route" is an
// appropriate amount of access control here.
//
// Local file (file://) use still works for solo play — every mode plays
// fully offline — but browsers block ES-module script loading over file://,
// so the sync dot just stays disconnected and scores don't share across
// devices. Serve this folder over http(s) (e.g. drag the whole nfl-trivia/
// folder into Netlify) to get the real live cross-device leaderboard.

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';
import { getFirestore, doc, getDoc, setDoc, addDoc, collection, onSnapshot, serverTimestamp, increment } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

var FIREBASE_CONFIG = {
  apiKey: "AIzaSyCYqKRGm2LSeTjxx1tpApm37TqBhOf2rIw",
  authDomain: "fantasy-draft-cheat-code.firebaseapp.com",
  projectId: "fantasy-draft-cheat-code",
  storageBucket: "fantasy-draft-cheat-code.firebasestorage.app",
  messagingSenderId: "962005341051",
  appId: "1:962005341051:web:0b63279d989350083023de"
};

var GAME_ID = 'nflTrivia';

var statusEl = document.getElementById('sync-status');
var dotEl = document.getElementById('sync-dot');
var labelEl = document.getElementById('sync-label');
function setStatus(s) {
  window.__fbSync.status = s;
  if (!statusEl) return;
  var label = s === 'live' ? 'Live' : s === 'offline' ? 'Offline' : 'Connecting…';
  var title = s === 'live' ? 'Connected — scores sync to everyone playing'
    : s === 'offline' ? 'No connection — scores are only saved on this device until it reconnects'
    : 'Connecting to shared leaderboard…';
  if (dotEl) dotEl.className = 'sync-dot-' + s;
  if (labelEl) labelEl.textContent = label;
  statusEl.title = title;
}

window.__fbSync = {
  status: 'connecting',
  pushScore: function () { /* no-op until Firebase finishes initializing below */ },
  logPlay: function () { /* no-op until Firebase finishes initializing below */ },
  submitReport: function () { console.warn('Report not sent — not connected.'); },
  getMatch: function () { return Promise.reject(new Error('Not connected')); },
  setMatch: function () { return Promise.reject(new Error('Not connected')); },
  watchMatch: function () { return function () {}; },
  pushProfile: function () { /* no-op until Firebase finishes initializing below */ },
  getProfile: function () { return Promise.reject(new Error('Not connected')); },
  getNamePin: function () { return Promise.reject(new Error('Not connected')); },
  setNamePin: function () { /* no-op until Firebase finishes initializing below */ }
};
setStatus('connecting');

if (FIREBASE_CONFIG.apiKey === 'PASTE_ME') {
  console.warn('firebase-sync.js: FIREBASE_CONFIG is still a placeholder — shared sync is disabled. This device will keep working locally.');
  setStatus('offline');
} else {
  try {
    var app = initializeApp(FIREBASE_CONFIG, 'nfl-trivia');
    var auth = getAuth(app);
    var db = getFirestore(app);
    var scoresCol = collection(db, 'games', GAME_ID, 'leaderboard');
    var analyticsDoc = doc(db, 'games', GAME_ID, 'analytics', 'playCounts');
    var reportsCol = collection(db, 'games', GAME_ID, 'reports');
    var matchesCol = collection(db, 'games', GAME_ID, 'matches');
    var profilesCol = collection(db, 'games', GAME_ID, 'profiles');
    var namePinsCol = collection(db, 'games', GAME_ID, 'namePins');

    window.__fbSync.getNamePin = function (nameSlug) {
      return getDoc(doc(namePinsCol, nameSlug)).then(function (snap) {
        return snap.exists() ? snap.data().pinHash : null;
      });
    };
    window.__fbSync.setNamePin = function (nameSlug, pinHash) {
      setDoc(doc(namePinsCol, nameSlug), { pinHash: pinHash, updatedAt: serverTimestamp() }).catch(function (err) {
        console.error('Name PIN save failed', err);
      });
    };

    window.__fbSync.pushProfile = function (nameSlug, data) {
      var payload = Object.assign({}, data, { updatedAt: serverTimestamp() });
      setDoc(doc(profilesCol, nameSlug), payload).catch(function (err) {
        console.error('Profile push failed', err);
      });
    };
    window.__fbSync.getProfile = function (nameSlug) {
      return getDoc(doc(profilesCol, nameSlug)).then(function (snap) {
        return snap.exists() ? snap.data() : null;
      });
    };

    window.__fbSync.getMatch = function (code) {
      return getDoc(doc(matchesCol, code)).then(function (snap) {
        return snap.exists() ? snap.data() : null;
      });
    };
    window.__fbSync.setMatch = function (code, data, merge) {
      return setDoc(doc(matchesCol, code), data, { merge: !!merge });
    };
    window.__fbSync.watchMatch = function (code, cb) {
      return onSnapshot(doc(matchesCol, code), function (snap) {
        cb(snap.exists() ? snap.data() : null);
      }, function (err) {
        console.error('Match watch failed', err);
      });
    };

    window.__fbSync.pushScore = function (docId, data) {
      var payload = Object.assign({}, data, { updatedAt: serverTimestamp() });
      setDoc(doc(scoresCol, docId), payload, { merge: true }).catch(function (err) {
        console.error('Score push failed', err);
      });
    };

    window.__fbSync.playCounts = {};
    window.__fbSync.logPlay = function (mode) {
      var payload = {};
      payload[mode] = increment(1);
      payload.total = increment(1);
      setDoc(analyticsDoc, payload, { merge: true }).catch(function (err) {
        console.error('Play log failed', err);
      });
    };

    window.__fbSync.reports = [];
    window.__fbSync.submitReport = function (payload) {
      var data = Object.assign({}, payload, { createdAt: serverTimestamp() });
      addDoc(reportsCol, data).catch(function (err) {
        console.error('Report submit failed', err);
      });
    };

    onAuthStateChanged(auth, function (user) {
      if (!user) return;
      onSnapshot(scoresCol, function (snap) {
        setStatus('live');
        var list = snap.docs.map(function (d) { return Object.assign({ id: d.id }, d.data()); });
        if (window.__triviaSync) window.__triviaSync.applyLeaderboard(list);
      }, function (err) {
        console.error('Leaderboard listen failed', err);
        setStatus('offline');
      });
      onSnapshot(analyticsDoc, function (snap) {
        window.__fbSync.playCounts = snap.data() || {};
      }, function (err) {
        console.error('Play-count listen failed', err);
      });
      onSnapshot(reportsCol, function (snap) {
        var list = snap.docs.map(function (d) { return Object.assign({ id: d.id }, d.data()); });
        list.sort(function (a, b) {
          var at = a.createdAt && a.createdAt.toMillis ? a.createdAt.toMillis() : 0;
          var bt = b.createdAt && b.createdAt.toMillis ? b.createdAt.toMillis() : 0;
          return bt - at;
        });
        window.__fbSync.reports = list;
      }, function (err) {
        console.error('Reports listen failed', err);
      });
    });

    signInAnonymously(auth).catch(function (err) {
      console.error('Sync auth failed', err);
      setStatus('offline');
    });

    window.addEventListener('offline', function () { setStatus('offline'); });
    window.addEventListener('online', function () { setStatus('connecting'); });
  } catch (err) {
    console.error('Firebase init failed', err);
    setStatus('offline');
  }
}
