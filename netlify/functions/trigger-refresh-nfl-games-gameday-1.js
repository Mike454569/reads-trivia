// Scheduled function (see netlify.toml) -- Dynamic Weekly Pick'em pass:
// one of three extra Sunday NFL games/schedule/score refresh triggers
// during the real gameday window (see netlify.toml's own comment for why
// this is deliberately modest, not hourly/live). Same handler as
// trigger-refresh-nfl-games.js -- a distinct file only because Netlify
// scheduled functions are one schedule per function name.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_games');
