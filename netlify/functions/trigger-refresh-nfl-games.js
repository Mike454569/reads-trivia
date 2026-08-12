// Scheduled function (see netlify.toml) -- triggers the NFL games/schedule/
// score refresh. See netlify/functions/lib/refresh_shared.js for why this
// is a separate, individually-scheduled function rather than one function
// looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_games');
