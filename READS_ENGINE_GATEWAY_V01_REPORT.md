# Reads Engine Gateway v0.1 -- Report (Director v0.6)

Milestone: replace the manual package handoff with one clean local backend
service in front of Director/Game Factory/QA/generated packages.

    Reads/Admin -> Gateway -> Director -> Capability Registry -> Engine/Factory -> QA -> GeneratedGamePackage

## Framework chosen (Part B)

**FastAPI 0.128.8** (ASGI, via **uvicorn 0.39.0**, validation via
**pydantic 2.13.4**), the milestone's own preferred option. None of these
were previously installed in this environment -- installed explicitly via
`pip3 install --user` and pinned in `gateway/requirements.txt` (runtime) /
`gateway/requirements-dev.txt` (adds `pytest` for `gateway/tests/` only).
Not built on raw `http.server`, unlike all eight existing Engine servers
(see `READS_ENGINE_GATEWAY_AUDIT.md`). One Python-3.9 compatibility fix was
required: this project's Python (3.9) cannot evaluate the `X | None` union
syntax at runtime without an extra dependency, so `gateway/models.py` and
`gateway/auth.py` use `typing.Optional`/`Literal` instead -- keeps Part B's
"minimal dependencies" intact rather than adding `eval_type_backport`.

## `/v1` routes (Part D)

| Route | Auth | Purpose |
|---|---|---|
| `GET /v1/health` | none | Service liveness, no internals exposed |
| `GET /v1/capabilities` | none | The 3 genuinely registered capabilities, reshaped to hide adapter/module names |
| `POST /v1/games/preview` | admin token | Translate + validate only -- never generates |
| `POST /v1/games/generate` | admin token | Full pipeline: translate -> validate -> generate -> QA -> persist |
| `GET /v1/games/{package_id}` | admin token | Retrieve a previously generated, persisted package |

## Auth design (Part F)

Single shared secret, `READS_ENGINE_ADMIN_TOKEN`, read fresh from the
environment on every request (never cached, never hard-coded, never
logged, never echoed in any response -- confirmed by
`test_error_response_never_contains_token`), compared with
`hmac.compare_digest`. Missing-token-on-server and wrong-token both fail
closed as `401 UNAUTHORIZED`.

**`/v1/health` and `/v1/capabilities` are deliberately unauthenticated.**
Reasoning: both are pure read-only reflections of static configuration that
cost nothing to compute and reveal nothing this project hasn't already
published in its own public milestone reports -- the exact three
capabilities are already documented in `GAME_DIRECTOR_V03_REPORT.md` and
`GAME_DIRECTOR_V04_REPORT.md`. `/v1/games/{package_id}` **does** require
auth, even though it's a GET -- retrieved packages are generated-but-
unreviewed content (`review_status: GENERATED`, never auto-approved), kept
behind the same gate as generation rather than left world-readable.

## Package repository design (Part E)

Local filesystem, `gateway/storage/packages/` -- **deliberately separate**
from `generated_games/` (which holds the hand-reviewed v0.1-v0.4 milestone
deliverables) so nothing the Gateway generates during normal use or
automated testing can ever collide with or be confused for an already-
approved deliverable. Package IDs are validated against a strict
allowlist regex (`^GGP4?:[0-9a-f]{24}$`) **before** any path is
constructed -- confirmed to reject path-traversal-shaped IDs in both
automated tests and manual `curl` probing (both resolve to Starlette's own
routing 404 before even reaching the package lookup code, plus an
independent regex check inside it as defense-in-depth). Writes are atomic
(temp file + `Path.replace`). A package under an already-existing ID with
byte-identical content is treated as an idempotent no-op (deterministic
IDs make this the expected case for a repeated identical request); a
collision with *different* content under the same ID raises a hard
integrity error (should be mathematically unreachable given `package_id`
is a content hash). `review_status` is explicitly set to `"GENERATED"` on
every Gateway-stored package -- **a real bug was found and fixed** during
manual testing: the first implementation used `dict.setdefault()`, which
silently deferred to the `"UNREVIEWED"` value every Director v0.1-v0.5
`generate_fn` already stamps onto packages, meaning the Gateway's own
`review_status` contract never actually took effect. Fixed to an explicit
assignment; re-verified.

## Concurrency model / resource controls (Part H)

**Exactly one generation job at a time**, process-wide (a single
`threading.Lock` plus a one-worker `ThreadPoolExecutor`), the milestone's
own explicitly-endorsed safest option. A second concurrent request gets an
immediate, structured `429 GENERATION_BUSY` rather than queueing or
blocking. Verified under real concurrent load: 4 simultaneous requests -\>
exactly 1 succeeds, 3 get `GENERATION_BUSY` in ~25ms each
(`test_concurrent_generation_protected`, and manually reproduced with 5
simultaneous requests via `urllib`+`ThreadPoolExecutor`). A 45-second hard
wall-clock timeout wraps every generation call (observed worst case is
~3.5s for Player From Clues' full 4,506-player universe scan -- generous
headroom, not tuned to be barely-sufficient). Request bodies are capped at
32KB before any parsing occurs.

**Known, disclosed limitation:** `Future.result(timeout=...)` stops
*waiting* on a timeout but does not *cancel* the underlying thread. Given
`max_workers=1`, a genuinely hung generation call would occupy the one
worker indefinitely, and subsequent requests would queue behind it rather
than failing fast a second time. This is an acceptable trade-off for a
single-developer local tool (a real hang would be a bug worth debugging
directly, not routing around), disclosed here rather than silently
accepted -- see `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`.

## Registered capabilities (Part L)

All three verified through the Gateway, `preview -> generate -> QA ->
persist -> retrieve`, each with real Engine generation (not mocked):

1. `guess / NFL_DRAFT / DRAFTED_BY` -- generated, `qa_status: PASSED`, retrieved successfully.
2. `guess / NFL_CHAMPIONSHIP / TEAM_POSTSEASON_RESULT` -- same.
3. `identify_player_from_clues / NFL_PLAYER_IDENTITY / IDENTIFY_FROM_CLUES` -- same; every returned puzzle independently checked to have `final_candidate_count == 1` and >=3 clues.

No fourth capability was registered.

## Test counts / results (Part Q)

**25/25 automated tests pass** (`gateway/tests/test_gateway.py`, run via
`python3 -m pytest gateway/tests/`), covering every category the milestone
lists: health, capabilities (incl. no-Engine-internals-leaked check),
missing/invalid/valid admin token, malformed JSON, oversized request,
invalid spec (extra field), extra field at the outer request level,
invalid difficulty, excessive puzzle count, both/neither request_text-or-spec,
package path traversal, missing package, ambiguous-request clarification
(preview and generate), unsupported request, mixed-unsupported request,
real generation for all 3 capabilities, package retrieval, concurrent-
generation protection, and internal-exception sanitization. Real Engine
generation was used for the one-per-capability integration tests, per the
milestone's explicit instruction; mocks were used only for the internal-
exception-sanitization test (which needs a controlled failure to prove the
sanitization path, not real generation).

A real bug was caught by manual testing before the automated suite was
finalized: FastAPI's default validation-error response
(`{"detail": [...]}`) did not match this project's own error contract --
fixed by adding an explicit `RequestValidationError` handler
(`gateway/app.py`) so 400s from Pydantic validation now return the same
`{"error": {"code", "message", "request_id"}}` shape as every other error.

## Generation results per capability

See "Registered capabilities" above for pass/fail; concrete examples (from
manual testing against a live local instance): Draft package
`GGP:04b1c62bbe3183c7a6fca9ae` (5 questions), Championship package
`GGP:f07842f77d0d21540c92739f` (5 questions), Player From Clues package
`GGP4:9969147103dfe1d3a496af9b` (3 puzzles) -- all `qa_status: PASSED`,
all successfully retrieved via `GET /v1/games/{package_id}` afterward.

## Clarification behavior (Part M)

`"Make me some NFL player trivia."` through `POST /v1/games/preview`
returns `gate_status: "NEEDS_CLARIFICATION"`, `understood: {"competition":
"NFL"}`, `missing_fields: ["domain", "relationship_predicate"]`, and a real
`question` string -- the exact v0.3 clarification contract, unchanged.
Through `POST /v1/games/generate`, the same request produces `package_id:
null`, `status: "NEEDS_CLARIFICATION"` -- confirmed nothing is generated.

## Unsupported behavior (Part N)

`"...players favorite foods."` -> `package_id: null`, `BLOCKED_NO_TRANSLATION`
via generate. The mixed request (`"...both a QB's team and his favorite
food."`) -> `package_id: null`, `status: "UNDERSTOOD_BUT_UNSUPPORTED"`, with
the `reason` field explicitly naming both the unsupported football-guessing
part and the no-data "favorite food" part -- confirmed neither half is
silently dropped or partially fulfilled.

## Package persistence / retrieval

Confirmed end to end: a package generated via `POST /v1/games/generate` is
immediately retrievable via `GET /v1/games/{package_id}` with identical
content. A well-formed-but-nonexistent ID returns a structured
`PACKAGE_NOT_FOUND` (404); a malformed/path-traversal-shaped ID is rejected
before ever reaching filesystem code.

## CORS behavior (Part P)

`gateway/config.py`'s `DEV_CORS_ORIGINS` is an explicit local-development
allowlist (`localhost`/`127.0.0.1` on ports 8934 and 8000) -- **never**
`Access-Control-Allow-Origin: *` (unlike the existing `game_director_api.py`,
see `READS_ENGINE_GATEWAY_AUDIT.md`). The eventual production origin,
`https://reads.football`, is documented (`PRODUCTION_ORIGIN_DOCUMENTED_NOT_ENABLED`)
but not enabled -- deliberately not reachable from that origin yet.

## Browser integration result (Parts O, R)

**Full local loop passed end to end**, using a real headless-Chrome browser
(Playwright) against a live static file server and a live Gateway process:

1. `tools/gateway_dev_client.py` (a local Python harness -- **not** browser
   JS, since authenticating a generation request from real browser code
   would require embedding `READS_ENGINE_ADMIN_TOKEN` client-side, which
   this milestone explicitly forbids) called the running Gateway's
   `POST /v1/games/generate` with the real admin token from the
   environment, generated a real 5-puzzle Player From Clues package
   (`GGP4:3729ee0bb1de9d131e12ebfb`), and wrote it to
   `data/player-from-clues-gateway-dev.js` using the exact same conversion
   function `tools/export_player_from_clues_frontend.py` already uses for
   the static baseline (reused, not duplicated).
2. With a new, **default-off** flag (`ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01`
   in `app.js`) turned on for this test only, the real browser loaded Reads,
   navigated to the existing hidden `#clues` route, and the **exact same,
   unmodified v0.5 renderer** played the Gateway-produced package: confirmed
   by object identity (`window.PLAYER_CLUES_PACKAGE === window.PLAYER_FROM_CLUES_GATEWAY_DEV`),
   not just matching IDs.
3. Played puzzle 1 to a **correct** answer (verified the "correct!" reveal
   text). Played puzzle 2 with progressive clue reveal (clue count
   increased by exactly 1 per reveal) and an **incorrect** guess (verified
   the wrong-answer feedback banner appeared and did not end the puzzle).
   Played through all 5 Gateway-produced puzzles to a real completion
   screen (`"1 / 5 identified"`).
4. Confirmed no Engine internals (`sqlite`, `.py`, SQL text, the Gateway's
   own URL) appear anywhere in the browser-loaded package JSON.
5. Confirmed the admin token string never appears anywhere in the loaded
   page content.
6. Reverted the dev flag back to `false` and re-confirmed (separately, in a
   fresh browser instance) that the app falls back to the exact original
   static baseline package (`GGP4:7b4a6260b92fc2a0d6902e56`) -- the v0.5
   integration is completely unaffected by this milestone's changes when
   the new flag is off, which is its default.

Console errors: same single pre-existing, unrelated `click.mp3` 404 already
disclosed in `PLAYER_FROM_CLUES_V01_FRONTEND_REPORT.md` -- zero errors
attributable to this milestone's code.

## Security findings

Full detail in `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`. Summary:
**safe for local development** (the only stage this milestone targets);
**not yet safe for private/admin staging** (needs TLS, process supervision,
token rotation story, rate limiting beyond the concurrency guard); **not
safe, and not close, for public internet exposure** (needs real auth, a
reverse proxy/WAF, abuse protection, resource isolation, secrets
management, backups -- none of which this milestone built, correctly, per
its own restrictions).

## Hosting recommendation

Full detail in `READS_ENGINE_HOSTING_READINESS.md`. **Fly.io** recommended
as the safest first staging host if/when a future milestone is approved to
deploy -- persistent Volumes fit the 1.65GB SQLite file well, automatic
HTTPS closes a major security gap by default, and its single-always-on-
machine model matches this Gateway's intentionally non-distributed,
single-generation-job design. No account was created; nothing was
provisioned.

## Exact files created

**Gateway core:**
- `gateway/__init__.py`, `gateway/app.py`, `gateway/config.py`,
  `gateway/errors.py`, `gateway/auth.py`, `gateway/models.py`
- `gateway/services/__init__.py`, `gateway/services/generation.py`,
  `gateway/services/packages.py`, `gateway/services/audit.py`
- `gateway/requirements.txt`, `gateway/requirements-dev.txt`
- `gateway/tests/__init__.py`, `gateway/tests/conftest.py`, `gateway/tests/test_gateway.py`

**Dev-loop / integration:**
- `tools/gateway_dev_client.py`
- `data/player-from-clues-gateway-dev.js` (placeholder by default; overwritten by the harness)

**Documentation:**
- `READS_ENGINE_GATEWAY_AUDIT.md`
- `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`
- `READS_ENGINE_HOSTING_READINESS.md`
- `READS_ENGINE_GATEWAY_V01_REPORT.md` (this file)

**Generated during testing (not milestone deliverables, disclosed for
completeness):** `gateway/storage/packages/*.json`, `gateway/storage/gateway_audit_log.jsonl`,
`gateway/storage/test_packages/*.json` (test-only), `gateway/storage/test_gateway_audit_log.jsonl` (test-only).

## Exact files modified

- `tools/director_v02/pipeline.py` -- added `translate_and_validate()` (factored
  out of `run()`, enabling preview-without-generation), and three new
  **optional, default-`None`** parameters to `run()`: `spec` (bypass the
  translator with a caller-supplied structured spec, re-validated through
  the exact same `validator.validate_translation()` every translator output
  already goes through), `question_count_override`, `difficulty_override`
  (both re-checked against each capability's own registry bounds before
  taking effect). Re-verified byte-identical/deterministic output for all
  three capabilities' existing v0.2-v0.5 test packages after this change.
- `app.js` -- added `ENABLE_PLAYER_FROM_CLUES_GATEWAY_DEV_V01` (default
  `false`) and a small data-source swap inside the existing
  `initPlayerCluesPackage()` (Part O) -- no other change to any existing
  render/state function.
- `index.html` -- one additive `<script src="data/player-from-clues-gateway-dev.js">`
  tag, same eager-load pattern as every other local-only data file.

**Not modified:** any of the eight existing Engine servers (`api_server.py`,
`game_director_api.py`, and the six unrelated-subsystem servers --
inspected only, per `READS_ENGINE_GATEWAY_AUDIT.md`), `game_factory.py`,
`game_director.py`, any `tools/quiz_export/` file, `tools/director_v04/player_from_clues.py`,
`data/player-from-clues-v01.js` (the static baseline), `data/quiz.js` (the
582-question pool), `styles.css`, `firebase-sync.js`, `sw.js`,
`netlify.toml`, and every prior milestone's generated package or report.

---

> **Can Reads now communicate with the Football Warehouse through one
> local versioned Gateway and request a verified generated game without
> directly accessing Engine internals?**

**YES.** Verified end to end this milestone, with a real browser: a local
Python client (standing in for a trusted local admin tool -- never browser
JavaScript, which would have required exposing the admin token) requested
a game through `POST /v1/games/generate` on the one new Gateway process;
the Gateway routed that request through the exact same
translate-\>validate-\>capability-registry-\>Engine-\>QA pipeline already
proven in Director v0.2-v0.5; the resulting `GeneratedGamePackage` was
persisted and independently retrievable; and the existing, completely
unmodified Player From Clues renderer played it in a real browser --
correct answer, incorrect answer, progressive clue reveal, and full
completion all confirmed -- with no SQLite access from the browser, no
Engine internals (table names, module names, file paths) ever reaching
client-visible code, and no admin secret anywhere in client-side
JavaScript or loaded page content.
