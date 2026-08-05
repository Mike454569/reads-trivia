/* ============================== sound ==============================
   Background music + sound effects. Every file this references is optional —
   if it's missing, playback just silently no-ops (same "graceful fallback"
   pattern as the Silhouette mode's real player photos).

   Background music is a shuffled PLAYLIST (MUSIC_PLAYLIST below), not a single
   looping file — it auto-advances to the next track when one ends, reshuffling
   once the whole list has played through, and never repeats the same track
   twice in a row. Only plays while the Home screen is showing; pauses the
   instant you go into a game mode.

   Sound effects (correct/wrong/complete) are real audio files sourced from a
   royalty-free pack the user provided (referee whistle / crowd cheer / stadium
   chant). The click sound is different: it tries assets/audio/click.mp3 first,
   and if that file isn't there, synthesizes a short click tone with the Web
   Audio API instead — no file required at all for that one.
*/
function soundLsGet(key, fallback) {
  try { var v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
  catch (e) { return fallback; }
}
function soundLsSet(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }

var SOUND_MUTE_KEY = 'nflTriviaMuted';
var soundMuted = soundLsGet(SOUND_MUTE_KEY, false);

var SFX_VOLUME = 0.6;
var BG_MUSIC_VOLUME = 0.32;
var CLICK_VOLUME = 0.5;

var SFX_FILES = {
  correct: 'assets/audio/bg-vishiv-crowd-cheering-in-stadium-435357.mp3',
  wrong: 'assets/audio/bg-framptones-referee-whistle-coach-whistle-sports-whistle-291816.mp3',
  complete: 'assets/audio/bg-stadium-chant-377307.mp3',
  boo: 'assets/audio/bg-olivia_parker-crowd-boo-disapproval-demo-309882.mp3'
};

var MUSIC_PLAYLIST = [
  'assets/audio/bg-astronautflute-the-marching-band-536193.mp3',
  'assets/audio/bg-luis-humanoide-marching-band-317665.mp3',
  'assets/audio/bg-nesrality-marching-music-america-first-by-john-philip-sousa-95389.mp3',
  'assets/audio/bg-nesrality-marching-music-anchor-and-star-by-john-philip-sousa-95390.mp3',
  'assets/audio/bg-nesrality-marching-music-bullets-and-bayonets-by-john-philip-sousa-95392.mp3',
  'assets/audio/bg-nesrality-marching-music-comrades-of-the-legion-by-john-philip-sousa-95393.mp3',
  'assets/audio/bg-nesrality-marching-music-marquette-university-march-by-john-philip-sousa-95385.mp3',
  'assets/audio/bg-nesrality-marching-music-on-the-campus-by-john-philip-sousa-99080.mp3',
  'assets/audio/bg-nesrality-marching-music-review-by-john-philip-sousa-95355.mp3',
  'assets/audio/bg-nesrality-marching-music-the-gladiator-by-john-philip-sousa-99124.mp3',
  'assets/audio/bg-nesrality-marching-music-the-glory-of-the-yankee-navy-by-john-philip-sousa-99089.mp3',
  'assets/audio/bg-nesrality-marching-music-the-high-school-cadets-by-john-philip-sousa-95375.mp3',
  'assets/audio/bg-nesrality-marching-music-the-stars-and-stripes-forever-by-john-philip-sousa-95379.mp3',
  'assets/audio/bg-nesrality-marching-music-the-volunteers-by-john-philip-sousa-99096.mp3',
  'assets/audio/bg-nesrality-marching-music-the-white-plume-by-john-philip-sousa-99126.mp3',
  'assets/audio/bg-nesrality-marching-music-the-wolverine-by-john-philip-sousa-95358.mp3',
  'assets/audio/bg-nesrality-marching-music-wisconsin-forward-forever-by-john-philip-sousa-99099.mp3',
  'assets/audio/bg-stereo-color-marching-band-485958.mp3',
  'assets/audio/bg-tech-oasis-marching-band-sound-marching-together-222550.mp3'
];

function sfxElement(name) {
  var el = new Audio(SFX_FILES[name]);
  el.volume = SFX_VOLUME;
  return el;
}
// The wrong-answer whistle file is a longer clip than needed for a quick
// "wrong" cue — cut it off after roughly one blast instead of letting the
// whole thing play out. (No audio-editing tooling available to actually trim
// the file itself, so this trims playback in code instead.)
var SFX_MAX_DURATION = { wrong: 900 };
// Only one correct/wrong/complete effect plays at a time — starting a new one
// (or advancing past the one currently playing, via stopSfx()) always cuts off
// whatever's already going, so a long crowd-cheer/whistle clip never bleeds
// into the next question.
var currentSfx = null;
function stopSfx() {
  if (currentSfx) { try { currentSfx.pause(); currentSfx.currentTime = 0; } catch (e) {} currentSfx = null; }
}
// Haptics — feature-detected (navigator.vibrate doesn't exist on iOS Safari
// at all, a long-standing WebKit limitation, not a bug here; it just silently
// no-ops there and still plays sound normally). Tied to the same soundMuted
// toggle as everything else in this file rather than a separate setting —
// someone muting the app is very plausibly also trying to keep the phone
// quiet/still, so haptics goes with it instead of surprising them anyway.
// Every call site is a plain finish/answer function already running from a
// real click, so the "must originate from a user gesture" requirement some
// browsers enforce for vibrate() is naturally satisfied here.
var HAPTIC_PATTERNS = { correct: 15, wrong: [15, 40, 15], complete: [20, 30, 20, 30, 40], boo: 200 };
function triggerHaptic(name) {
  if (!HAPTIC_PATTERNS[name] || !navigator.vibrate) return;
  try { navigator.vibrate(HAPTIC_PATTERNS[name]); } catch (e) {}
}
function playSound(name) {
  if (!SFX_FILES[name]) return;
  stopSfx();
  if (soundMuted) return;
  triggerHaptic(name);
  // Small delay so this doesn't perfectly overlap the click sound that just
  // fired on the same tap — otherwise the click gets buried under a loud
  // crowd-cheer/whistle clip starting in the same instant.
  setTimeout(function () {
    if (soundMuted) return;
    try {
      var el = sfxElement(name);
      currentSfx = el;
      if (SFX_MAX_DURATION[name]) {
        // Tied to the audio element's own reported playback position
        // (timeupdate), not a wall-clock timer — timeupdate can only fire
        // once real playback has actually progressed that far, so there's
        // no way to pause before anything started (unlike a setTimeout or a
        // 'playing'-event-triggered timer, both of which turned out to
        // sometimes make the browser drop the sound entirely instead of
        // just shortening it).
        var maxSec = SFX_MAX_DURATION[name] / 1000;
        el.addEventListener('timeupdate', function onTimeUpdate() {
          if (el.currentTime >= maxSec) {
            el.removeEventListener('timeupdate', onTimeUpdate);
            try { el.pause(); } catch (e2) {}
          }
        });
      }
      el.play().catch(function () {});
    } catch (e) {}
  }, 90);
}

/* click: real file if present, else a synthesized blip via Web Audio */
var clickAudioCtx = null;
function playClick() {
  if (soundMuted) return;
  try {
    var el = new Audio('assets/audio/click.mp3');
    el.volume = CLICK_VOLUME;
    el.addEventListener('error', function () { synthClick(); }, { once: true });
    el.play().catch(function () { synthClick(); });
  } catch (e) { synthClick(); }
}
function synthClick() {
  try {
    if (!clickAudioCtx) clickAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
    var ctx = clickAudioCtx;
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.value = 850;
    gain.gain.setValueAtTime(CLICK_VOLUME * 0.25, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.06);
  } catch (e) {}
}

/* background music playlist — shuffled, no immediate repeat, auto-advances */
var musicQueue = [];
function shuffleQueue() {
  var a = MUSIC_PLAYLIST.slice();
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}
function nextTrack() {
  if (musicQueue.length === 0) {
    musicQueue = shuffleQueue();
    // avoid immediately repeating whatever track just finished
    var el = bgMusicElement();
    if (el && musicQueue.length > 1 && el.dataset.currentSrc === musicQueue[0]) {
      musicQueue.push(musicQueue.shift());
    }
  }
  return musicQueue.shift();
}
function bgMusicElement() { return document.getElementById('bg-music'); }
function playNextTrack() {
  var el = bgMusicElement();
  if (!el || MUSIC_PLAYLIST.length === 0) return;
  var src = nextTrack();
  el.dataset.currentSrc = src;
  el.src = src;
  el.play().catch(function () {});
}
(function initBgMusic() {
  var el = bgMusicElement();
  if (!el) return;
  el.addEventListener('ended', playNextTrack);
})();

function syncBgMusic() {
  var el = bgMusicElement();
  if (!el) return;
  el.volume = BG_MUSIC_VOLUME;
  var shouldPlay = state.screen === 'home' && !soundMuted;
  if (shouldPlay) {
    if (el.paused) {
      if (!el.src) playNextTrack();
      else el.play().catch(function () {});
    }
  } else {
    if (!el.paused) el.pause();
  }
}
function toggleMute() {
  soundMuted = !soundMuted;
  soundLsSet(SOUND_MUTE_KEY, soundMuted);
  renderMuteButton();
  syncBgMusic();
}
// Duplicated (not reused from app.js's icon() helper) because sound.js loads
// and calls this once before app.js has run — no load-order dependency this way.
var MUTE_ICON_ON = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M16.5 8.5a5 5 0 0 1 0 7"/><path d="M19 6a9 9 0 0 1 0 12"/></svg>';
var MUTE_ICON_OFF = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z"/><path d="M17 9l5 6M22 9l-5 6"/></svg>';
function renderMuteButton() {
  var btn = document.getElementById('mute-toggle');
  if (!btn) return;
  btn.innerHTML = soundMuted ? MUTE_ICON_OFF : MUTE_ICON_ON;
  var label = soundMuted ? 'Sound off, click to unmute' : 'Sound on, click to mute';
  btn.title = label;
  btn.setAttribute('aria-label', label);
  btn.setAttribute('aria-pressed', soundMuted ? 'true' : 'false');
}
document.addEventListener('click', function (e) {
  if (e.target.closest('#mute-toggle')) { toggleMute(); return; }
  if (e.target.closest('button')) playClick();
});
renderMuteButton();

// Browsers block audio-with-sound until a real user gesture happens on the
// page — there's no way around that. This listens for the very first tap/
// click/keypress ANYWHERE, as early as possible, and immediately tries to
// start music right then (only actually plays if state.screen is 'home' at
// that moment) — the closest thing to "plays automatically on load" that's
// actually allowed.
function tryStartMusicOnFirstGesture() { syncBgMusic(); }
['pointerdown', 'keydown'].forEach(function (evt) {
  document.addEventListener(evt, tryStartMusicOnFirstGesture, { once: true, passive: true });
});

// Stop the music the instant the tab/app is backgrounded — phone screen
// locked, app switched away from, browser minimized, or the tab just loses
// focus on desktop. Covers all of those the same way: the Page Visibility API
// fires document.hidden = true for every one of them. Resumes automatically
// (if still on Home) when it becomes visible again.
document.addEventListener('visibilitychange', function () {
  var el = bgMusicElement();
  if (!el) return;
  if (document.hidden) { if (!el.paused) el.pause(); }
  else { syncBgMusic(); }
});
