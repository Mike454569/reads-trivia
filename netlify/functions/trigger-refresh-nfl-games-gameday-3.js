// Scheduled function (see netlify.toml) -- Dynamic Weekly Pick'em pass:
// one of three extra Sunday NFL games/schedule/score refresh triggers
// during the real gameday window (this one lands just after midnight UTC
// Monday, covering real Sunday/Monday-night-adjacent kickoffs). Same
// handler as trigger-refresh-nfl-games.js -- see
// trigger-refresh-nfl-games-gameday-1.js.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_games');
