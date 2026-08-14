// Scheduled function (see netlify.toml) -- triggers the CFB All-America
// selections refresh (tools/data_refresh/cfb_all_america_import.py).
// Engine-gap-audit operation -- 137 years of mostly-static historical
// selections plus at most one new year per season, scheduled MONTHLY (not
// daily, see netlify.toml) since re-scraping the full range more often
// than that has no real benefit and is needlessly heavy on Wikipedia's
// servers. See netlify/functions/lib/refresh_shared.js for why this is a
// separate, individually-scheduled function rather than one function
// looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_all_america');
