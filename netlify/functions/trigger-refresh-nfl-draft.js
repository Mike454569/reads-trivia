// Scheduled function (see netlify.toml) -- triggers the NFL draft-picks
// refresh (tools/data_refresh/nfl_draft_refresh.py). Historical Engine
// Enrichment operation: draft_facts had no automatic refresh anywhere in
// this repo before this and was capped at 2024 -- this closes that gap.
// See netlify/functions/lib/refresh_shared.js for why this is a separate,
// individually-scheduled function rather than one function looping over
// every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_draft');
