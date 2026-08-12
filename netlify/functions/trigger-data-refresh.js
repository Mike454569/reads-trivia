// Scheduled function (see netlify.toml) — the real production trigger for
// the NFL/CFB roster refresh built in gateway/services/admin_refresh.py +
// tools/data_refresh/{nfl_refresh,cfb_refresh}.py. This function does NOT
// do the actual refresh work itself (it has no access to the ~1.6GB Engine
// DB — that lives on the Fly-hosted Gateway's persistent volume, a
// completely different runtime from Netlify Functions). It only fires two
// short HTTPS calls that tell the Gateway to start its own background
// refresh job, then returns — matching the same "kick off, then poll
// status separately" contract gateway/services/admin_refresh.py's module
// docstring describes (a real refresh run can take minutes, well past any
// single function invocation's budget).
//
// Requires two env vars in Netlify (Site configuration -> Environment
// variables — see netlify/README.md):
//   READS_ENGINE_GATEWAY_BASE_URL — e.g. https://reads-football-gateway.fly.dev
//   READS_ENGINE_ADMIN_TOKEN — the SAME admin token already set as a Fly
//     secret for the Gateway (`fly secrets set READS_ENGINE_ADMIN_TOKEN=...`).
//     Never hardcoded here, never logged.
const LEAGUES = ['nfl', 'cfb'];

exports.handler = async () => {
  const baseUrl = process.env.READS_ENGINE_GATEWAY_BASE_URL;
  const token = process.env.READS_ENGINE_ADMIN_TOKEN;
  if (!baseUrl || !token) {
    console.error('READS_ENGINE_GATEWAY_BASE_URL/READS_ENGINE_ADMIN_TOKEN not set — see netlify/README.md');
    return { statusCode: 200, body: 'Refresh trigger not configured, skipped.' };
  }

  const results = {};
  for (const league of LEAGUES) {
    try {
      const res = await fetch(`${baseUrl}/v1/admin/refresh/${league}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const body = await res.json().catch(() => ({}));
      results[league] = { httpStatus: res.status, ...body };
      if (!res.ok) {
        // Never include the token in a log line — body/status only.
        console.error(`Refresh trigger for ${league} failed`, res.status, body);
      }
    } catch (err) {
      results[league] = { error: String(err) };
      console.error(`Refresh trigger for ${league} threw`, err);
    }
  }

  return { statusCode: 200, body: JSON.stringify(results) };
};
