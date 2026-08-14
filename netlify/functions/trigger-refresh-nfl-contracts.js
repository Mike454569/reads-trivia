// Scheduled function (see netlify.toml) -- triggers the NFL player
// contracts refresh (tools/data_refresh/nfl_contracts_refresh.py).
// Engine-gap-audit operation. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather than
// one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_contracts');
