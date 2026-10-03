// Scheduled Story Factory harvest. This triggers the complete safe funnel:
// candidate harvest -> triage -> non-sensitive high-confidence promotion ->
// question generation -> review-assistant suggestions. Sensitive/legal stories
// remain review-only; this function never bypasses those server-side gates.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('story_candidates');
