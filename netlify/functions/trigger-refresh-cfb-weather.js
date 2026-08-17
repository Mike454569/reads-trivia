// Scheduled function (see netlify.toml) -- triggers the CFB game weather
// refresh (tools/data_refresh/cfb_weather_refresh.py). Engine-gap-audit
// operation, continuation -- CFBD-key-dependent AND Patreon Tier 1+
// dependent (unblocked only after the user upgraded their subscription and
// regenerated their API key; see that script's own module docstring).
// Defaults to a current-season-only refresh so a weekly schedule stays
// cheap on CFBD's metered API. See netlify/functions/lib/refresh_shared.js
// for why this is a separate, individually-scheduled function rather than
// one function looping over every dataset.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_weather');
