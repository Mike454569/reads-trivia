// Live Football Layer v1: one late Saturday-night settlement pass.
// Reuses the same guarded heavy refresh as every other CFB games trigger.
const { triggerRefresh } = require('./lib/refresh_shared');
exports.handler = async () => triggerRefresh('cfb_games');
