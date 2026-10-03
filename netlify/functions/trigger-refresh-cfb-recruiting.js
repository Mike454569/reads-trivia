// Scheduled function (see netlify.toml) -- refreshes the current CFB recruiting
// class from CFBD. Kept separate because the Gateway enforces one refresh at a
// time; see lib/refresh_shared.js for the shared trigger contract.
const { triggerRefresh } = require('./lib/refresh_shared');

exports.handler = async () => triggerRefresh('cfb_recruiting');
