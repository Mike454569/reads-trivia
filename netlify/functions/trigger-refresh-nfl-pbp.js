// Scheduled function (see netlify.toml) -- triggers the NFL play-by-play
// refresh (tools/data_refresh/nfl_pbp_refresh.py). Engine-gap-audit
// operation -- the largest single dataset in this Gateway (1.28M+ rows
// across 1999-present), scheduled WEEKLY (not daily, see netlify.toml)
// given its real backup/download/parse cost on a shared-CPU 1GB machine.
// See netlify/functions/lib/refresh_shared.js for why this is a separate,
// individually-scheduled function rather than one function looping over
// every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_pbp');
