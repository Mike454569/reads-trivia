// Scheduled function (see netlify.toml) -- Pick'em Automation pass: the CFP
// window (restricted to Jan 1-20 via netlify.toml's own day/month fields),
// covering the real semifinal and championship games -- same reasoning as
// trigger-refresh-cfb-games-gameday-3's December bowl-season window.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_games');
