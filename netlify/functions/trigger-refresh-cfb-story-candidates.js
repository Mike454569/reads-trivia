// Scheduled CFB-specific Story Factory harvest.
// Candidate collection is separate from verification/promotion; sensitive
// stories remain manual-only downstream.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_story_candidates');
