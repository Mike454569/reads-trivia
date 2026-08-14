// Scheduled function (see netlify.toml) -- triggers the NFL passer rating
// computation (tools/data_refresh/nfl_passer_rating_compute.py). Derived
// only, no external download -- scheduled AFTER nfl_player_stats' own
// slot each day so real pass_interceptions data is fresh before this
// computes ratings from it. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather than
// one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_passer_rating');
