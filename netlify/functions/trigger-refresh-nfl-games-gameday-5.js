// Scheduled function (see netlify.toml) -- Pick'em Automation pass: the
// Monday Night Football window (fires ~11pm ET Monday / after typical MNF
// end), closing the same real gap trigger-refresh-nfl-games-gameday-4
// closes for Thursday. Same handler as trigger-refresh-nfl-games.js.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('nfl_games');
