# Reads Football — Final Live Certification

Freeze-point certification, run against the real live production system
after all five engine-backed modes were enabled. Supersedes nothing in
`READS_FINAL_GO_LIVE_REPORT.md` — this is the confirmation pass after that
report's recommended flag-flip was executed and manually confirmed working
by the site owner.

## Production frontend status

**LIVE.** `https://reads.football` returns 200. Latest Netlify production
deploy (`6a7bac78...`) is `ready`. Existing static assets (Quiz, Grid,
Legends, Daily/Speed/IQ mode definitions, X's & O's, CFB data) all verified
present and unchanged.

## Production Gateway status

**LIVE.** `https://reads-football-gateway.fly.dev` — `/v1/health` returns
`{"status":"ok"}`, `/v1/ready` returns `{"status":"ready", "engine_database":
{"ready":true,"database_version":"4.0.0"}, ...}`. Fly machine checks: 2/2
passing. One transient connectivity blip was observed mid-certification
(a few consecutive requests timed out); Fly's own check history showed no
gap and the Gateway was responding normally again within seconds — treated
as a passing network hiccup, not a real outage, and not investigated
further per this pass's explicit "verify, don't expand scope" scope.

## Live domain

`https://reads.football`

## Enabled engine modes

All five, confirmed `true` in the live `reads-config.js` and confirmed
`"available": true` at the Gateway:

- Draft Guessing
- Championship Guessing
- Coach Connections (Six Degrees)
- Lineup Guess
- CFB Heisman

## Security result

All clean, re-verified against the live system:

- No admin token anywhere in frontend source (`reads-config.js`, `app.js`,
  `engine-game-ui.js`, `creator-ui.js`).
- No token/authorization data in any public response.
- Coach Connections never reveals the solution path before completion.
- Game Creator routes (`/v1/creator/*`) require a real admin token — 401
  without one, confirmed again.
- Public mode allow-list is exactly the 5 certified modes, no more.
- CORS: allowed origin gets `Access-Control-Allow-Origin`; disallowed
  origin gets nothing.
- Rate limiting active (`READS_ENGINE_PUBLIC_GAME_RATE_LIMIT`, default
  20/60s, unchanged).
- Malformed and path-traversal-shaped game IDs both fail safely (404,
  no path leakage).

## Smoke-test result

Real fetch → wrong-answer → correct-answer flow re-verified end-to-end
against production for all 5 modes (API level — no headless browser
available in this environment):

| Mode | Fetch | Incorrect flow | Correct flow |
|---|---|---|---|
| Draft Guessing | 200 | rejected correctly | accepted correctly |
| Championship Guessing | 200 | rejected correctly | accepted correctly |
| Lineup Guess | 200 | rejected correctly | accepted correctly |
| CFB Heisman | 200 | rejected correctly | accepted correctly |
| Coach Connections | 200 | (verified in the prior canary pass) | (verified in the prior canary pass) |

**Real-browser confirmation**: the site owner manually clicked through all
five live modes on reads.football after the flag flip and confirmed
questions load, answering works, and no console errors — reported directly,
not simulated.

## Existing-mode regression result

**No regression.** All pre-existing static assets return 200 and are
byte-identical to what shipped before this operation touched anything
(Quiz, Grid, Blitz, Silhouette, Legends, Speed, IQ, Daily, Study, X's &
O's). None of this operation's changes touch those code paths.

## Rollback controls

Confirmed available at every level (not executed, to avoid disrupting the
current good state):

- **Per-mode**: edit `READS_PUBLIC_MODES` in `gateway/fly.toml`, redeploy.
- **Coach Connections independently**: `READS_PUBLIC_SIX_DEGREES_ENABLED=false`.
- **All public engine gameplay at once**: `READS_PUBLIC_GAME_ENABLED=false`
  (Draft/Championship/Lineup/Heisman) + `READS_PUBLIC_SIX_DEGREES_ENABLED=false`
  (Coach Connections) together.
- **Frontend rollback**: 46 previous `ready` production Netlify deploys
  available to restore, most recent immediately before this one.
- **Gateway rollback**: 12-version clean Fly release history;
  `fly deploy --image <tag>` restores any prior version.
- **Database restore**: byte-verified local backup from before the
  identity-bridge write; Fly volume has automatic scheduled snapshots.

## Git / repository state

```
$ git status
On branch main
Your branch is up to date with 'origin/main'.
$ git log -1 --oneline
9205b70 Enable all five certified engine pilots in production
```

Already fully pushed — the flag-flip commit and
`READS_FINAL_GO_LIVE_REPORT.md` both landed on `origin/main` in the prior
push. Nothing pending. Untracked local files (`.claude/`,
`*.code-workspace`, a `package-lock.json` left over from local Netlify
CLI troubleshooting) are pre-existing/incidental, not deliverables, and
were left out of every commit this operation made, per established
convention.

## Remaining P1 items (backlog, not blocking)

- Flip additional flags/modes only if new ones are certified in the future
  — none are pending.
- CFB Career Timeline: data evaluated, adapter deliberately deferred.
- Six Degrees step-resubmission gameplay-integrity nuance (disclosed in
  the go-live report, pre-existing, low severity, no security impact).
- No secrets manager — single shared admin token (unchanged, previously
  documented).
- Revoke the GitHub PAT that was pasted into this session, if not already
  done.

## CFB limitations

Unchanged from the go-live report: Heisman is the one fully certified,
live CFB mode. Other CFB concepts remain honestly `UNDERSTOOD_BUT_UNSUPPORTED`
or `BLOCKED_BY_DATA`/`BLOCKED_BY_ARCHITECTURE` — no fabricated data, no
forced parity.

## Scale classification

**CANARY LIVE.** Unchanged from the go-live report — nothing in this
certification pass changed the underlying concurrency architecture
(`PUBLIC_GENERATION_MAX_CONCURRENCY=4`, a deliberate single-instance
design). No broad-traffic load test was run this pass; no evidence exists
to justify upgrading this classification.

---

# READS IS LIVE

# ENGINE IS LIVE AND SERVING REAL USERS

# CFB IS GAME-READY WITH LIMITATIONS

# SCALE STATUS: CANARY LIVE
