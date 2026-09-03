// Scheduled function (see netlify.toml) -- Dynamic Weekly Pick'em pass:
// one of two extra Saturday/Sunday CFB games/schedule/score refresh
// triggers during the real gameday window (see netlify.toml's own comment
// for why this is deliberately modest, not hourly/live). Same handler as
// trigger-refresh-cfb-games.js -- a distinct file only because Netlify
// scheduled functions are one schedule per function name.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_games');
