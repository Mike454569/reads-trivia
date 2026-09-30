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
  let body, sub, meta = {};
  try {
    body = JSON.parse(event.body);
    sub = body && body.subscription ? body.subscription : body;
    meta = body && body.meta ? body.meta : {};
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
  await store.setJSON(key, {
    subscription: sub,
    meta: {
      name: String(meta.name || '').slice(0, 80),
      updatedAt: Number(meta.updatedAt) || Date.now(),
      localDate: meta.localDate || null,
      dailyDone: !!meta.dailyDone,
      streak: Number(meta.streak) || 0,
      comebackGap: Number(meta.comebackGap) || 0,
      comebackMode: meta.comebackMode || null,
      weeklyHabitCurrent: Number(meta.weeklyHabitCurrent) || 0,
      weeklyHabitTarget: Number(meta.weeklyHabitTarget) || 5,
      missionsOpen: Number(meta.missionsOpen) || 0,
      rivalName: meta.rivalName || null,
      rivalGap: Number(meta.rivalGap) || 0,
      prefs: Object.assign({ daily:true, rivals:true, missions:true, comeback:true }, meta.prefs || {})
    }
  });
  return { statusCode: 200, body: JSON.stringify({ ok: true }) };
};
