// Scheduled function (see netlify.toml) -- triggers the CFB play-by-play
// refresh (tools/data_refresh/cfb_pbp_refresh.py). Engine-gap-audit
// operation, continuation -- CFBD-key-dependent, defaults to a
// current-season-only refresh (see that script's own target_seasons
// comment) so a weekly schedule stays cheap on CFBD's metered free tier;
// the real 2002-2025 historical backfill already imported is never
// re-swept by this schedule. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather than
// one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_pbp');
