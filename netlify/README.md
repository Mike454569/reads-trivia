# Reads X draft — cloud version (works away from your Mac)

This is the cloud twin of `reads-social-agent/` on your Mac — same playbook
data, same logic, but it runs on Netlify's servers on a fixed schedule, so
it fires whether or not your Mac is on. It pushes the draft straight to your
phone via [ntfy.sh](https://ntfy.sh) — free, no account, no API keys.

## One-time setup (do this before it'll actually reach your phone)

1. **Pick a topic name.** This is like a private channel name — anyone who
   knows it can subscribe and see your drafts, so pick something not easily
   guessable, e.g. `reads-drafts-mn7k2x` (not literally that one — make up
   your own).
2. **Install the ntfy app** on your phone (free, iOS App Store / Google Play
   — search "ntfy"). Open it, tap "+", subscribe to the exact topic name
   you picked.
3. **Add the environment variable in Netlify:** on your Reads site in the
   Netlify dashboard → Site configuration → Environment variables → Add a
   variable → name it `NTFY_TOPIC`, value = the topic name you picked.
4. **Deploy** — drag the `nfl-trivia` folder to Netlify like always. The
   `netlify.toml` + `netlify/functions/social-draft.js` in this deploy is
   what registers the scheduled function; Netlify picks it up automatically
   without any extra build step (no npm dependencies to install).

That's it. It'll fire at 9:15am and 5:15pm Central (see the comment in
`netlify.toml` for why it's :15 not :15/:45, and the DST caveat).

## Checking it's working

Netlify dashboard → your site → Functions tab → `social-draft` → you'll see
invocation logs after each scheduled run. If `NTFY_TOPIC` isn't set, the
function logs a warning and skips sending (won't error your deploy).

## Now that this exists, what about the Mac version?

`reads-social-agent/` (the local LaunchAgent) still works fine and isn't
required to run alongside this — but running both means two drafts /
notifications at roughly the same time. Once you've confirmed the cloud
version is reaching your phone, turn off the Mac one:
```
launchctl unload ~/Library/LaunchAgents/com.reads.socialdraft.plist
```
(Instructions to fully remove it are in `reads-social-agent/README.md`.)

## Content stays in sync manually

If you edit the playbook logic in `reads-social-agent/playbook_data.py`
(the Mac version), mirror the change in `social-draft.js` (the cloud
version) — they're independent copies, not shared code, since one's Python
and one's JS.
