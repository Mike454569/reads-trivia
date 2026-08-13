// Scheduled function (see netlify.toml) -- triggers the NFL player-GAME
// stats refresh (tools/data_refresh/nfl_player_game_stats_refresh.py).
// Master Knowledge Blueprint's top execution priority (game-grain stats,
// real canonical linkage to the `games` table). See
// netlify/functions/lib/refresh_shared.js for why this is a separate,
// individually-scheduled function rather than one function looping over
// every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_player_game_stats');
