// Shared helper for the four trigger-refresh-*.js scheduled functions.
// Deliberately NOT itself a Netlify function (no exports.handler, lives in
// a subdirectory) -- Netlify only auto-deploys handler-exporting files
// directly inside netlify/functions/ as invokable functions, so this stays
// a plain, imported library module.
//
// Why four separate scheduled functions instead of one looping over all
// four datasets: gateway/services/admin_refresh.py enforces a GLOBAL (not
// per-dataset) concurrency guard -- only one refresh runs at a time on the
// Gateway, a real capacity constraint (single shared-CPU, 1GB-memory
// machine; each refresh backs up the full ~1.6GB Engine DB). Firing all
// four trigger calls back-to-back from one function would only ever
// actually run the FIRST one -- each POST returns immediately (the real
// work is backgrounded), so the 2nd/3rd/4th calls would arrive while the
// 1st is still running and get ALREADY_RUNNING every single day. Spacing
// four separate scheduled invocations 10 minutes apart (see netlify.toml)
// instead gives each a real, comfortable window -- a full refresh has
// measured at 130-200s in practice, well under that gap.
async function triggerRefresh(datasetKey) {
  const baseUrl = process.env.READS_ENGINE_GATEWAY_BASE_URL;
  const token = process.env.READS_ENGINE_ADMIN_TOKEN;
  if (!baseUrl || !token) {
    console.error('READS_ENGINE_GATEWAY_BASE_URL/READS_ENGINE_ADMIN_TOKEN not set — see netlify/README.md');
    return { statusCode: 200, body: 'Refresh trigger not configured, skipped.' };
  }
  try {
    const res = await fetch(`${baseUrl}/v1/admin/refresh/${datasetKey}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      // Never include the token in a log line — body/status only.
      console.error(`Refresh trigger for ${datasetKey} failed`, res.status, body);
    }
    return { statusCode: 200, body: JSON.stringify({ httpStatus: res.status, ...body }) };
  } catch (err) {
    console.error(`Refresh trigger for ${datasetKey} threw`, err);
    return { statusCode: 200, body: JSON.stringify({ error: String(err) }) };
  }
}

module.exports = { triggerRefresh };
