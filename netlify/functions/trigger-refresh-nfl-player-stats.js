// Scheduled function (see netlify.toml) -- triggers the NFL player-season
// stats refresh (tools/data_refresh/nfl_player_stats_refresh.py).
// Historical Engine Enrichment operation: player_season_stats had zero
// rows before this -- the hard blocker on any real 17-0 candidate
// generation. See netlify/functions/lib/refresh_shared.js for why this is
// a separate, individually-scheduled function rather than one function
// looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_player_stats');
