# Reads Engine Gateway -- Audit of Existing Servers (Director v0.6, Part A)

Analysis only, written before any Gateway implementation. Every file below
was read in full (or, for the six smallest/most clearly out-of-scope ones,
surveyed by route list + docstring, noted per-file) in
`Reads_Football_Data_Engine_v4.0/`.

## Inventory

Eight independent Python processes, **all** built directly on stdlib
`http.server` (`HTTPServer`/`ThreadingHTTPServer` + `BaseHTTPRequestHandler`),
**all** bound to `127.0.0.1` only (not exposed beyond localhost -- the one
thing every one of them gets right), **no shared code between any of
them** -- each is a standalone script with its own hand-rolled JSON
response helper.

| File | Port | Routes (sample) | Classification |
|---|---|---|---|
| `api_server.py` | 8787 | `/health`, `/modes`, `/daily`, `/random`, `/graph/*`, `/six-degrees`, `/factory/capabilities`, `/factory/analyze`, `/factory/preview`, `/factory/publish`, `/answer`, `/attempt` | **PARTIALLY_REUSABLE** |
| `game_director_api.py` | 8800 | `/v3/director/examples`, `/preview`, `/interpret`, `/publish` | **PROTOTYPE_ONLY** |
| `production_api.py` | 8793 | `/v2.1/entitlement`, `/sync`, `/funnel`, `/account`, `/session`, `/ranked/*`, `/track` | **REDUNDANT** (out of scope) |
| `autonomous_api.py` | 8801 | `/v3.1/discover`, `/memory`, `/direct`, `/certify` | **REDUNDANT** |
| `community_api.py` | 8789 | `/v1/community/trending`, `/creators`, `/following`, `/saved`, `/creator`, `/create`, `/review` | **REDUNDANT** |
| `growth_api.py` | 8794 | `/v2.2/seo/page`, `/growth/metrics`, `/referral`, `/share/*`, `/track` | **REDUNDANT** |
| `live_admin_api.py` | 8792 | `/v2/live/feeds`, `/alerts`, `/queue`, `/events`, `/slate`, `/outbox`, `/run` | **REDUNDANT** |
| `quality_api.py` | 8795 | `/v2.3/health`, `/graph/query`, `/audit`, `/daily/certify`, `/release/certify` | **REDUNDANT** |
| `retention_api.py` | 8788 | `/v1/feed`, `/streak`, `/event`, `/ranked/result`, `/challenge` | **REDUNDANT** |

None are classified `BROKEN` outright (that would require running and
proving failure, out of scope for an audit-only step) except where a
specific route is already confirmed broken by this project's own prior
work (see `game_director_api.py` below). None are classified `REUSABLE`
outright -- every one has at least one disqualifying issue (see findings).

## Findings

### Authentication

**Zero of the eight servers implement any authentication.** Every route on
every port is fully open to any process that can reach `127.0.0.1` on that
port -- no token, no password, no allowlist. This is the single most
important finding motivating Part F of this milestone.

### CORS

Inconsistent and, where present, wrong for what a real Gateway needs:
- `game_director_api.py`: `Access-Control-Allow-Origin: *` -- wide open,
  exactly what Part P says not to do for an authenticated endpoint.
- `api_server.py`, `production_api.py`, and the rest: **no CORS headers at
  all** -- not a deliberate security boundary, just an omission (a browser
  cross-origin `fetch()` against these would fail on the CORS preflight,
  which is accidental protection, not designed protection).

### Database access patterns

Every server opens its own raw `sqlite3.connect()` (per-request in most,
once per process in a couple) against the same 1.65GB
`reads_football_v4.0.sqlite`, with zero coordination between processes.
If all eight of these plus a new Gateway ran simultaneously, that's up to
nine independent connection pools hitting one file with no shared
concurrency control. This project's own Director v0.2+ work has never
needed more than one connection at a time (see `tools/quiz_export/engine.py`),
and the new Gateway inherits that discipline (Part H: one generation job at
a time) rather than trying to retrofit coordination onto the seven
out-of-scope legacy servers, which this milestone explicitly does not
touch or delete.

### Error formats

Inconsistent, and at least one actively unsafe pattern:
- `production_api.py` returns `{"error": str(e)}` for *any* uncaught
  exception -- this leaks raw Python exception text (which can include
  internal variable values, file paths, or SQL fragments) directly to the
  client. This is precisely the anti-pattern Part I's "do not expose stack
  traces to clients" rule exists to prevent, and it's disclosed here as a
  concrete example of what the new Gateway must not do, not something to
  copy.
- Others (`api_server.py`) return a flat `{"error": "not found"}` string
  with no error code, no request ID -- not structured enough to build a
  real client integration against.

### Timeout / resource behavior

**None** of the eight servers implement any request timeout, generation
timeout, candidate-scan cap, or concurrency limit. A slow or unbounded
query against the 1.65GB database would simply block that server's thread
(or, for the `HTTPServer`-based ones, the entire single-threaded process)
indefinitely.

### Duplicated routes / no shared foundation

`/health`-equivalent endpoints exist independently in `api_server.py`
(`/health`) and `quality_api.py` (`/v2.3/health`) with zero shared
implementation. Every server reinvents its own `sendj`/JSON-response
helper. This is the concrete evidence behind the prompt's framing --
"eight unrelated public servers" is accurate, not editorializing.

### The one already-confirmed-broken route

`game_director_api.py`'s `/v3/director/publish` calls `game_director.publish()`,
which this project's earlier architecture-assessment milestone (prior to
Director v0.1) already empirically confirmed is broken -- it calls a
nonexistent `game_factory.build_mode()`. This is not re-verified here
(already proven); it's cited as the reason `game_director_api.py` cannot
be classified any better than `PROTOTYPE_ONLY`, and as independent
confirmation that this project was right to build its own
translate/validate/generate pipeline (`tools/director_v02/`,
`tools/director_v04/`) rather than route through the old `game_director.py`
prototype's `publish()` path.

### `api_server.py`'s Factory routes specifically

`/factory/capabilities`, `/factory/analyze`, `/factory/preview` call
`game_factory` directly -- bypassing this project's own
translator/validator/capability-registry layer entirely (no schema
validation, no allowlist enforcement, no clarification handling, no audit
logging). `/factory/publish` calls `game_factory.publish()` (a different
function from the broken `game_director.publish()` above, not previously
exercised or verified by this project) against the live `puzzle_catalog`/
`daily_puzzles` production tables -- exactly the kind of auto-publish path
this whole Director arc (v0.1 onward) has deliberately avoided building on
top of. **Not reused.**

## Conclusion -- what the new Gateway does and does not do

The new Gateway (`gateway/`, Part C) is a **single new process** that:
- Does **not** import or shell out to any of these eight legacy servers.
- Does **not** delete or modify any of them (explicit restriction --
  "do not delete prototype Engine servers yet").
- Calls this project's own, already-proven, in-process Python modules
  directly: `tools.director_v02.translator`, `.validator`, `.registry`,
  `.pipeline`, `.audit_log`, and `tools.director_v04.player_from_clues` --
  the exact code path already verified end-to-end in Director v0.2-v0.5.
- Is the **first** of these nine total localhost processes to implement
  admin authentication, structured errors, request timeouts, and a
  single-generation-job concurrency guard.

This directly satisfies "the final design should expose one Gateway
process, not eight unrelated public servers" -- the Gateway is additive
(a ninth process, for now), not a replacement for the other eight, whose
fate is out of scope for this infrastructure-only milestone.
