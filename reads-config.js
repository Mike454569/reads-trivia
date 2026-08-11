// Reads Engine runtime configuration (v1.4, Parts 12/29/30).
//
// A small, separate, git-tracked file specifically so enabling/disabling
// an engine-backed pilot mode, or repointing the frontend at a different
// Gateway, is a one-file edit -- never a change inside app.js's actual
// logic. Loaded via a <script> tag in index.html BEFORE app.js, so app.js
// can read window.READS_CONFIG at its own top-level init (see app.js's
// ENABLE_ENGINE_DRAFT_PILOT_V01 / ENABLE_ENGINE_CHAMPIONSHIP_PILOT_V01 /
// ENGINE_GATEWAY_BASE_URL declarations).
//
// NEVER put a secret in this file. It is served as a plain static asset to
// every visitor's browser exactly like app.js itself -- anything written
// here is fully public. No admin token. No database path. No credential of
// any kind belongs here, ever.
//
// Fails closed by design (Part 13): if this file fails to load at all (404,
// blocked, network error), app.js's own fallback treats every pilot as OFF
// and the Gateway URL as unset -- see app.js's `READS_CONFIG` read, which
// never assumes `window.READS_CONFIG` exists.
//
// This exact committed file is the LOCAL DEVELOPMENT default: both pilots
// OFF, Gateway URL pointing at a typical local `uvicorn gateway.app:app
// --port 8850` run. A real deployment ships its OWN version of this file
// (same filename, different values, e.g. a real https:// Gateway hostname)
// -- see READS_ENGINE_V14_IMPLEMENTATION_REPORT.md's deployment runbook.
window.READS_CONFIG = {
  engineGatewayBaseUrl: 'http://localhost:8850',
  enableEngineDraftPilot: false,
  enableEngineChampionshipPilot: false,
  // v1.7, Part C: same fail-closed pattern, default OFF.
  enableEngineSixDegrees: false,
  // v1.8, Part F/O: same fail-closed pattern, default OFF.
  enableEngineLineupPilot: false,
};
