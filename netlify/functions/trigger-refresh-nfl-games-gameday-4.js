// Scheduled function (see netlify.toml) -- Pick'em Automation pass: a real
// gap the audit for that pass found -- the existing 3 gameday triggers
// only cover the Sunday window (afternoon/evening/late ET), leaving
// Thursday Night Football and Monday Night Football to rely on the once-
// daily 10:10 UTC run alone. This is the Thursday Night Football window
// (fires ~11pm ET Thursday / after typical TNF end). Same handler as
// trigger-refresh-nfl-games.js -- a distinct file only because Netlify
// scheduled functions are one schedule per function name.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_games');
