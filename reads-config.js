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
  // Final Go-Live Operation: real, deployed, verified production Gateway
  // (https://reads-football-gateway.fly.dev/v1/health and /v1/ready both
  // confirmed live). All five pilots below are now ON -- each mode was
  // individually canary-verified end-to-end against this exact production
  // Gateway (real fetch, real answer validation, no leakage) before this
  // flip. Server-side kill switches (READS_PUBLIC_GAME_ENABLED,
  // READS_PUBLIC_SIX_DEGREES_ENABLED) remain available in gateway/fly.toml
  // as an independent rollback layer if any of these need to come back
  // down without a frontend redeploy.
  //
  // Production Integrity Fix Pass (2026-08-31): this file's flags were
  // correct -- the Gateway really had been deployed and canary-verified
  // as claimed above -- but nothing was monitoring it, and the volume
  // silently filled to 100% at some point after that, taking every one of
  // these public modes down with a generic error for real visitors with
  // no alert firing. Fixed and independently re-verified externally this
  // pass (see PRODUCTION_STATUS.md at the repo root); flags below left
  // unchanged since the underlying capability is real. The concrete
  // lesson: "canary-verified once" is not the same as "monitored" -- see
  // PRODUCTION_STATUS.md's Remaining Risks for the CI/alerting gap.
  engineGatewayBaseUrl: 'https://reads-football-gateway.fly.dev',
  enableEngineDraftPilot: true,
  enableEngineChampionshipPilot: true,
  // v1.7, Part C: same fail-closed pattern.
  enableEngineSixDegrees: true,
  // v1.8, Part F/O: same fail-closed pattern.
  enableEngineLineupPilot: true,
  // CFB data enrichment operation: same fail-closed pattern.
  // The first CFB engine mode -- see gateway/services/public_game.py's
  // cfb_heisman_guess entry.
  enableEngineHeismanPilot: true,

  // Public-readiness punch-list closure pass: real, tested modes wired
  // into the frontend -- each flag only flips to true after being
  // individually canary-verified (real fetch + real answer validation)
  // against this exact production Gateway, matching this file's own
  // established rollout discipline.
  // Creator stress test / discovery pass: lineupCollege/nflGameResult/
  // cfbGameResult/nflGameBoxscore were real, server-certified, already-
  // built modes that had sat OFF with zero frontend entry point since the
  // punch-list pass -- canary-verified end-to-end against production this
  // pass (real fetch + real answer validation for all four) and flipped
  // on. The same real candidate-survey + canary-verification discipline
  // was applied to the 4 brand-new public modes below before their flags
  // went to true.
  enableEngineLineupCollegePilot: true,
  enableEngineNflGameResultPilot: true,
  enableEngineCfbGameResultPilot: true,
  enableEngineNflGameBoxscorePilot: true,
  enableEngineMatchingPilot: false,
  enableEngineSortingPilot: false,
  enableEngineHigherLowerPilot: false,
  enableEngineEliminationPilot: false,
  // Creator stress test / discovery pass: the first 4 modes promoted
  // straight from Creator-only to public certification -- real candidate
  // surveys (gateway/services/public_game.py) + real canary verification
  // against production (fetch + answer validation) before this flip.
  enableEngineOffenseCollegePilot: true,
  enableEngineSbChampionOffenseCollegePilot: true,
  enableEngineCfbRankingPilot: true,
  enableEngineCfbUpsetPilot: true,

  // Weekly Pick'em Player Experience pass: deployed and canary-verified
  // against this exact production Gateway (all CFB slate variants +
  // conference filters return correct, deduplicated counts; NFL slate
  // correct; no score/winner leakage before FINAL, correctly shown after;
  // pick submission persists across slate-view switches for the same
  // client_id+game_id; locked/kicked-off games correctly reject new picks
  // with 400 INVALID_REQUEST) before this flip -- matching this file's own
  // established rollout discipline.
  enablePickem: true,

  // Public Mode Wiring pass (Pass 2.5): 8 real backend capabilities newly
  // certified public this pass (gateway/services/public_game.py's own
  // PUBLIC_MODES entries carry the real candidate surveys). Left OFF here
  // pending local verification + real production canary, matching this
  // file's own established rollout discipline (flip only after each mode
  // is individually canary-verified against production).
  enableEngineCfbRivalryPilot: false,
  enableEngineCfbRivalryLookupPilot: false,
  enableEngineCfbSpotTheFakePilot: false,
  enableEngineCfbThreeCluesPilot: false,
  enableEngineEraGauntletPilot: false,
  enableEngineCfbOddCollegeOutPilot: false,
  enableEngineCfbOneSchoolMissingPilot: false,
  enableEngineFranchiseMarathonPilot: false,
};
