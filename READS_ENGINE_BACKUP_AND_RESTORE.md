# Reads Engine Gateway -- Backup & Restore (Director v0.7, Part N)

Covers the three things staging actually needs to survive a bad day: the
Engine SQLite database, generated game packages, and the configuration/
version metadata needed to stand the service back up from nothing. A real
local backup + restore drill was performed this milestone against a
disposable copy -- results at the bottom, not just a plan.

## 1. Engine SQLite database

**Frequency:** staging is read-mostly (Part E: the Gateway's entire
generation path was verified to perform zero writes to the Engine
database) and the database only changes when a new Engine snapshot is
deliberately imported -- a daily backup cadence is more than sufficient;
there is no continuous-write workload to protect against data loss between
backups.

**Destination model:** off the same disk the live database lives on
(never a same-volume snapshot only) -- for the Fly.io target recommended in
`READS_ENGINE_HOSTING_READINESS.md`, Fly Volumes' own snapshot feature plus
a periodic copy to object storage (or simply downloaded to a operator's
machine, given this project's current scale) are both reasonable; no
specific provider was configured this milestone (nothing was deployed).

**SQLite-safe procedure:** use SQLite's own online backup API
(`sqlite3.Connection.backup()` in Python, equivalent to the `.backup`
command in the `sqlite3` CLI) -- **never** a raw filesystem `cp` of a
database that might be open elsewhere. The online backup API is
WAL-aware and produces a consistent snapshot even if a connection is open
against the source, unlike a naive file copy which can capture a
torn/inconsistent write. This project's Engine database is confirmed to
use `journal_mode=wal` (established earlier in this project's history),
which makes this distinction concrete, not theoretical.

**Retention:** not prescribed numerically here (this project has no
production traffic yet to size retention against) -- the operationally
important rule is "at least one verified-restorable backup always exists
before importing a new Engine snapshot," which the drill below exercises.

**Checksum verification:** SHA-256 of the backup file, recorded alongside
the backup, checked again after any transfer/download before trusting the
file for a restore.

## 2. Generated game packages

Simpler than the database: `gateway/storage/packages/` (or wherever
`READS_ENGINE_PACKAGES_DIR` points) holds only small, atomically-written,
immutable-once-written JSON files (see `gateway/services/packages.py` --
temp file + `Path.replace`, and package IDs are content hashes, so a file
never needs to be edited in place). A plain recursive file copy/sync is
sufic ient and safe -- no special point-in-time consistency concern the way
a live database has, since nothing here is ever modified after creation.

## 3. Configuration / schema / version metadata

What's needed to stand the service back up from nothing, none of which is
itself a "backup" in the traditional sense (it's either already in version
control or belongs in a secrets manager, never in a backup artifact
alongside real data):

- `gateway/requirements.txt` -- exact pinned dependency versions (already in version control).
- `.env.example` -- the full list of required configuration names (already in version control; real values belong in a secrets manager, per `READS_ENGINE_STAGING_V01_REPORT.md`'s secrets section, never in a backup file).
- The Engine's own `database_version` value (currently `"4.0.0"`, readable via `SELECT value FROM meta WHERE key='database_version'` -- also surfaced by `GET /v1/ready`) -- recorded alongside each database backup so a future restore can confirm it restored the version it meant to.

## Restore procedure

1. Provision a fresh `READS_ENGINE_DIR` location (a new persistent volume,
   or a fresh local directory for a drill).
2. Copy the Engine's Python modules into it (these don't change with a
   database backup/restore -- they're versioned separately, currently by
   hand, matching how this whole project has managed Engine code all
   along).
3. Restore the backed-up `reads_football_v4.0.sqlite` into that same
   directory (required alongside the modules -- see
   `tools/quiz_export/engine.py`'s docstring on why they're coupled).
4. Verify the checksum matches the recorded one from backup time.
5. Point `READS_ENGINE_DIR` at the restored location and start the
   Gateway.
6. Confirm `GET /v1/ready` reports `"ready": true` with the expected
   `database_version` and row counts.
7. Generate at least one real package through at least one capability to
   confirm the restored data is genuinely usable, not merely present.

## Recovery verification -- this milestone's actual drill

Performed locally this session against a **disposable copy**, never
touching the canonical Engine database:

1. Used `sqlite3.Connection.backup()` (Python stdlib, the WAL-safe online
   backup API described above) to back up the real 1.65GB
   `reads_football_v4.0.sqlite` into the session scratchpad directory.
   **Result:** backup completed, byte size and SHA-256 recorded (see
   `READS_ENGINE_STAGING_V01_REPORT.md`'s backup-drill section for the
   exact numbers -- this file documents the procedure; that one documents
   this specific run's evidence, since it's the artifact that already
   aggregates every other test result from this milestone).
2. Ran `PRAGMA quick_check` against the backup -- **passed (`ok`)**.
3. Compared `draft_facts` row count and `meta.database_version` between the
   live database and the backup -- **matched exactly**.
4. Assembled a disposable, fresh `READS_ENGINE_DIR` (Engine `.py` modules
   copied in, the restored `.sqlite` file placed alongside them, per the
   restore procedure above).
5. Started a fresh Gateway process with `READS_ENGINE_DIR` pointed at that
   disposable directory (a completely different filesystem location from
   the canonical Engine directory, confirmed by path).
6. Called `GET /v1/ready` against it -- **reported ready**, with the
   correct `database_version` and row count.
7. Called `POST /v1/games/generate` for the Draft capability against it --
   **produced a real, QA-passing package**, proving the restored data is
   not just present but genuinely generation-capable.

The canonical Engine database's mtime and checksum were confirmed
unchanged before and after this entire drill.
