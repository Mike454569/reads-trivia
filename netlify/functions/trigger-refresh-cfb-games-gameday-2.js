// Scheduled function (see netlify.toml) -- Dynamic Weekly Pick'em pass:
// one of two extra Saturday/Sunday CFB games/schedule/score refresh
// triggers during the real gameday window. Same handler as
// trigger-refresh-cfb-games.js -- see trigger-refresh-cfb-games-gameday-1.js.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_games');
