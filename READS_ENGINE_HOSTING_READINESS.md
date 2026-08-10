# Reads Engine Gateway -- Hosting Readiness (Director v0.6, Part T)

Comparison only. **No account created, no resource deployed.** This
document exists so a future, explicitly-approved deployment milestone has
a real starting point instead of researching from zero.

## What this workload actually needs

- One always-on Python process (the Gateway; `uvicorn`, single worker is
  enough for the single-generation-job concurrency model this milestone
  chose).
- Persistent disk for the 1.65GB Engine SQLite file (`reads_football_v4.0.sqlite`) --
  this is the dominant sizing constraint. It must survive restarts/redeploys
  without being re-uploaded every time, and ideally supports a snapshot/backup
  mechanism.
- Modest additional persistent disk for `gateway/storage/packages/` (generated
  packages) and the two audit-log files -- these grow slowly (each
  generated package is tens of KB) and are not remotely comparable in size
  to the Engine database itself.
- Memory: SQLite itself is not memory-hungry for the query patterns this
  project uses (indexed lookups, small result sets -- see
  `PLAYER_FROM_CLUES_FEASIBILITY_REPORT.md`'s 4,506-row in-memory universe
  as the heaviest single operation observed, well under 100MB). A modest
  instance (512MB-1GB) is plausible; should be measured under real load
  before committing to a specific tier, not assumed.
- CPU: bursty, not sustained -- generation takes ~0.1-4s per request
  (see `GAME_DIRECTOR_V04_REPORT.md`), and the Gateway's own concurrency
  guard caps this at one job at a time. A single shared vCPU is plausible
  for this milestone's traffic profile; would need revisiting under real
  multi-user load.
- HTTPS -- required the moment this leaves `127.0.0.1`, non-negotiable per
  `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`.

## Options compared

| | Fly.io | Render | Railway | VPS (e.g. a $6-12/mo droplet) |
|---|---|---|---|---|
| Always-on process | Yes | Yes (paid tier; free tier sleeps) | Yes | Yes |
| Persistent disk for a 1.65GB file | Yes (Volumes) | Yes (Disks, paid tier) | Yes (Volumes) | Yes (it's just a disk) |
| Attaching persistent disk to app | Straightforward (`fly volumes create` + mount) | Straightforward | Straightforward | Trivial (already a filesystem) |
| HTTPS | Automatic (managed certs) | Automatic | Automatic | Manual (Caddy/nginx + Let's Encrypt, or a proxy service) |
| Deployment complexity | Low (`fly deploy`, Dockerfile or buildpack) | Low (git-push deploy) | Low (git-push deploy) | Highest (you own the whole box: OS updates, process supervision, firewall, reverse proxy, TLS renewal) |
| Backups | Volume snapshots (manual or scripted) | Disk snapshots (paid tier) | Volume snapshots | Fully manual (cron + off-box copy) |
| Cost class | Low ($ single digits-low tens/mo for this size) | Low-medium (persistent disk requires a paid plan) | Low-medium | Lowest raw compute cost, highest operational time cost |
| Scaling ceiling for this architecture | Vertical scaling straightforward; this Gateway's single-generation-job design doesn't benefit from horizontal scaling without redesigning the concurrency guard (a shared lock, not per-instance) | Same caveat | Same caveat | Same caveat, plus you manage it yourself |
| Process supervision | Built-in (platform restarts a crashed app) | Built-in | Built-in | Manual (systemd unit you write and maintain) |

## Recommendation

**Fly.io** as the safest *first staging* host for this specific
architecture, if/when a future milestone is explicitly approved to deploy:

- Persistent Volumes are a first-class, well-documented feature for exactly
  this shape of workload (one process, one large data file that must
  survive redeploys) -- more turnkey than a hand-rolled VPS setup, and the
  free/low tier is large enough to host a 1.65GB file + a small Python
  process without immediately needing a paid plan (verify current pricing
  at deploy time; not confirmed here since no account was created).
- Automatic HTTPS removes an entire category of the security gaps listed
  in `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md` (private/admin staging
  section) with near-zero configuration.
- Deployment complexity is low relative to a VPS, while still giving
  enough control (a real Dockerfile, real volume mounts) to run this
  exact Gateway process without restructuring it.
- The single-generation-job concurrency model this milestone chose
  (Part H) maps cleanly onto "one small always-on machine," which is
  exactly Fly.io's sweet spot -- it does not need, and would not benefit
  from, a platform built around horizontal auto-scaling.

**Render** is a reasonable second choice for the same reasons (persistent
disks, automatic HTTPS, low deploy complexity) if Fly.io's specific volume
model turns out not to fit; it was not chosen as the primary recommendation
only because persistent disks require a paid tier there, which is a real
cost consideration to weigh explicitly against Fly's volume-inclusive tiers
at actual deploy time.

**Plain VPS** is not recommended as the *first* staging host specifically
because of the security gaps `READS_ENGINE_GATEWAY_SECURITY_REVIEW.md`
already identifies (no TLS, no process supervision, no reverse proxy) --
every one of those becomes the deploying developer's manual responsibility
on a bare VPS, whereas Fly.io/Render solve most of them by default. A VPS
remains a reasonable *later* choice once those concerns have real answers
and cost optimization matters more than deployment simplicity.

## What this document deliberately does not do

No account was created on any of the above. No resource was provisioned.
No DNS, TLS certificate, or deployment configuration was written for any
specific host. This is a comparison to inform a future, separately-approved
deployment decision -- not a deployment.
