// Scheduled function (see netlify.toml) -- Pick'em Automation pass: a real
// gap the audit for that pass found -- CFB bowl season and CFP games occur
// on many different weekdays through December and early January, not just
// Saturdays, but the existing 2 gameday triggers only cover the Saturday
// window. Restricted to December (via netlify.toml's own month field) so
// this stays a real bowl-season boost, not a year-round extra daily
// refresh. Triggers the free/unlimited cfbfastR games/schedule/score
// refresh (cfb_games) -- NOT the metered CFBD-backed cfb_games_postseason
// dataset, so this adds no cost against that API's paid tier. Same handler
// as trigger-refresh-cfb-games.js.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_games');
