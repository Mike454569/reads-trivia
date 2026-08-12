e# Reads backend — Netlify Functions

Two things live here, both server-side pieces that a plain static site can't
do on its own:

1. **`social-draft.js`** — the cloud twin of `reads-social-agent/` on your
   Mac, pushing a daily X post draft idea to your phone via ntfy.sh.
2. **`save-subscription.js` + `send-daily-push.js`** — real Web Push
   notifications ("today's Daily Challenge is live") sent to anyone who
   turns on notifications in the app's Settings screen.
3. **`trigger-refresh-nfl.js` / `trigger-refresh-cfb.js` / `trigger-refresh-nfl-games.js` / `trigger-refresh-cfb-games.js` / `trigger-refresh-nfl-draft.js`**
   (sharing `lib/refresh_shared.js`) — the real production scheduler for
   NFL/CFB roster, games/schedule/score, and NFL draft-picks refresh (see
   `gateway/services/admin_refresh.py` and `tools/data_refresh/`). Each
   fires one short HTTPS call to the Fly-hosted Gateway's admin refresh
   endpoints once a day, staggered 30 minutes apart starting 09:10 UTC (see
   the real current schedule in `netlify.toml`) because the Gateway only
   allows one refresh running at a time (single shared-CPU, 1GB-memory
   machine; each refresh backs up the full ~1.6GB Engine DB) -- five
   separate scheduled functions instead of one looping over all five
   datasets, since firing them back-to-back would only ever actually run
   the first one. The actual multi-minute refresh work runs on the Gateway
   itself (Netlify Functions can't reach the Engine database, which lives
   on Fly's persistent volume).

## Deploy workflow changed: git-based now, not drag-and-drop

The push notification pieces need real npm dependencies (`web-push`,
`@netlify/blobs`) — a manual drag-and-drop deploy doesn't run `npm install`,
only a Git-connected or CLI deploy does. This folder is already a git repo
with an initial commit. To finish connecting it:

1. **Create a new empty repo on GitHub** (github.com → New repository — do
   NOT initialize it with a README/gitignore, this folder already has both).
2. **Push this repo to it:**
   ```
   cd "nfl-trivia"
   git remote add origin <the URL GitHub gives you>
   git branch -M main
   git push -u origin main
   ```
3. **In Netlify:** Add new site → Import an existing project → connect to
   GitHub → pick this repo. Build command: leave blank. Publish directory:
   `.` (the repo root — that's where index.html already lives).
4. **If this replaces an existing drag-and-drop "Reads" site** rather than
   creating a new one: Site configuration → Build & deploy → Link repository,
   point it at the new GitHub repo. Keeps the same getreads.netlify.app URL
   and all your existing environment variables/leaderboard data.
5. From now on, deploys happen by pushing to GitHub (`git add -A && git
   commit -m "..." && git push`) instead of dragging the folder.

## Environment variables to set in Netlify

Site configuration → Environment variables → add all of these:

| Variable | Value |
|---|---|
| `NTFY_TOPIC` | Your chosen ntfy.sh topic name (see below) |
| `VAPID_PUBLIC_KEY` | See the chat where this was set up — also hardcoded in `app.js` (`VAPID_PUBLIC_KEY` constant), since public keys are meant to be public |
| `VAPID_PRIVATE_KEY` | See the chat where this was set up — **never commit this to git**, it only belongs in this environment variable |
| `READS_ENGINE_GATEWAY_BASE_URL` | `https://reads-football-gateway.fly.dev` (the live Gateway URL) |
| `READS_ENGINE_ADMIN_TOKEN` | The SAME admin token already set on the Gateway via `fly secrets set READS_ENGINE_ADMIN_TOKEN=...` — **never commit this to git**, copy it from wherever you originally generated it |

The VAPID keys are a matched pair generated specifically for this app.
Deliberately not written in this file (which is committed to git) — the
private key is a real secret and shouldn't sit in git history even in a
private repo. Don't regenerate these unless you have a reason to — the
public one the client already has must always match the private one the
server signs with, or push subscriptions silently stop working.

### ntfy.sh setup (for the X draft agent, not push notifications)

1. Pick a topic name — treat it like a private channel name, e.g.
   `reads-drafts-mn7k2x` (make up your own, not that one).
2. Install the ntfy app on your phone (free, iOS/Android), subscribe to that
   exact topic.
3. Set `NTFY_TOPIC` to it in Netlify (table above).

## Enabling push notifications (once deployed)

Open the app → Profile → Settings → Notifications → "Turn On Notifications".
That's the entire user-facing setup — no topic name or app install needed,
it's the browser's native permission prompt.

## Checking either one is working

Netlify dashboard → your site → Functions tab → pick the function → you'll
see invocation logs after each scheduled run (`social-draft` fires at
9:15am/5:15pm Central, `send-daily-push` at ~10:07am Central — see the
comments in `netlify.toml`). If an env var isn't set, the function logs a
warning and skips instead of erroring your deploy.

## Now that cloud drafting exists, what about the Mac version?

`reads-social-agent/` (the local LaunchAgent) still works fine and isn't
required to run alongside `social-draft.js` — but running both means two
drafts at roughly the same time. Once you've confirmed the cloud version is
reaching your phone, turn off the Mac one:
```
launchctl unload ~/Library/LaunchAgents/com.reads.socialdraft.plist
```
(Full removal instructions in `reads-social-agent/README.md`.)

## Content stays in sync manually

If you edit the playbook logic in `reads-social-agent/playbook_data.py`
(the Mac version), mirror the change in `social-draft.js` (the cloud
version) — they're independent copies, not shared code, since one's Python
and one's JS.
