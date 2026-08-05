// Scheduled function (see netlify.toml) — sends "today's Daily Challenge is
// live" as a real push notification to every browser that's subscribed,
// once a day. This is deliberately the broad/simple version: everyone
// subscribed gets the same message at the same time, because there's no
// server-side record of any individual's streak/last-active state to
// target a "your streak is about to break" message at just them — that
// would need the cross-device profile sync work to exist first (so a
// user's real streak data lives somewhere this function could read it).
//
// Requires VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY env vars in Netlify (same
// keys the client uses to subscribe — see subscribeToPush() in app.js).
// Uses the `web-push` npm package to handle the actual Web Push protocol
// (VAPID JWT signing + per-message payload encryption) rather than hand-
// rolling that cryptography.
const webpush = require('web-push');
const { getStore } = require('@netlify/blobs');

exports.handler = async () => {
  const publicKey = process.env.VAPID_PUBLIC_KEY;
  const privateKey = process.env.VAPID_PRIVATE_KEY;
  if (!publicKey || !privateKey) {
    console.error('VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY not set — see netlify/README.md');
    return { statusCode: 200, body: 'VAPID keys not configured, skipped.' };
  }
  webpush.setVapidDetails('mailto:readstrivia@gmail.com', publicKey, privateKey);

  const store = getStore('push-subscriptions');
  const { blobs } = await store.list();
  if (!blobs.length) {
    return { statusCode: 200, body: 'No subscribers yet.' };
  }

  const payload = JSON.stringify({
    title: 'Reads',
    body: "Today's Daily Challenge is live — go get your rating in.",
    url: '/'
  });

  let sent = 0, removed = 0;
  await Promise.all(blobs.map(async ({ key }) => {
    const sub = await store.get(key, { type: 'json' });
    if (!sub) return;
    try {
      await webpush.sendNotification(sub, payload);
      sent++;
    } catch (err) {
      // 404/410 = the browser un-registered this subscription (uninstalled,
      // cleared site data, etc.) — Web Push's own way of saying "stop
      // sending here," so clean it up instead of retrying it forever.
      if (err.statusCode === 404 || err.statusCode === 410) {
        await store.delete(key);
        removed++;
      } else {
        console.error('Push failed for', key, err.statusCode, err.body);
      }
    }
  }));

  return { statusCode: 200, body: `Sent ${sent}, removed ${removed} stale subscriptions.` };
};
