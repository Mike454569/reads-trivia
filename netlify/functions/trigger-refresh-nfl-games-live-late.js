// Live Football Layer v1: one late Sunday-night settlement pass.
// Reuses the same guarded heavy refresh as every other NFL games trigger.
const { triggerRefresh } = require('./lib/refresh_shared');
exports.handler = async () => triggerRefresh('nfl_games');
