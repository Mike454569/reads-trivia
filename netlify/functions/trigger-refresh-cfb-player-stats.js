// Scheduled function (see netlify.toml) -- triggers the CFB player-season
// stats refresh (tools/data_refresh/cfb_player_season_stats_refresh.py).
// Football Knowledge Expansion operation: extends cfb_player_season_stats_real
// back to 2014 and keeps it current, from the same real, already-approved
// SPORTSDATAVERSE_CFB source. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather
// than one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_player_stats');
