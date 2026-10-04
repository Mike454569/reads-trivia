// Scheduled Story Factory queue drain.
// Processes checkpointed micro-batches only; it does not harvest or deploy.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('story_process');
