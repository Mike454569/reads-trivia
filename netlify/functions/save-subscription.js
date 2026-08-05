// Called from the client (see subscribeToPush() in app.js) right after the
// browser hands back a PushSubscription — stores it in Netlify Blobs so
// send-daily-push.js has something to iterate over later. Keyed by the
// subscription's own endpoint URL (unique per browser install), so
// re-subscribing (e.g. after clearing site data) just overwrites the old
// entry instead of piling up duplicates.
const { getStore } = require('@netlify/blobs');
const crypto = require('crypto');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST' && event.httpMethod !== 'DELETE') {
    return { statusCode: 405, body: 'Method not allowed' };
  }
  let sub;
  try {
    sub = JSON.parse(event.body);
  } catch (e) {
    return { statusCode: 400, body: 'Invalid JSON' };
  }
  if (!sub || !sub.endpoint) {
    return { statusCode: 400, body: 'Missing subscription endpoint' };
  }

  const store = getStore('push-subscriptions');
  // Blob keys can't contain arbitrary URL characters reliably across every
  // backend Netlify Blobs might use — hashing the endpoint into a short,
  // filesystem/key-safe id sidesteps that instead of trying to sanitize the
  // raw URL.
  const key = crypto.createHash('sha256').update(sub.endpoint).digest('hex');

  if (event.httpMethod === 'DELETE') {
    await store.delete(key);
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }
  await store.setJSON(key, sub);
  return { statusCode: 200, body: JSON.stringify({ ok: true }) };
};
