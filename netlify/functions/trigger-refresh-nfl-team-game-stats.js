// Scheduled function (see netlify.toml) -- triggers the NFL team-game
// boxscore refresh (tools/data_refresh/nfl_team_game_stats_refresh.py).
// Direct user request: a real boxscore for every game, for in-depth
// specific-game questions. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather
// than one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_team_game_stats');
