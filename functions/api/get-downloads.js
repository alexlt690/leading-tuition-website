/**
 * GET /api/get-downloads?session_id=cs_xxx
 * Returns list of { label, downloadUrl, isBundle } for the session.
 * For normal purchases downloadUrl points to /api/download.
 * For bundle purchases downloadUrl is the Google Drive folder link (from env vars).
 */

const BUNDLE_ENV_KEYS = {
  'bundle/11-plus':     'DRIVE_11_PLUS',
  'bundle/13-plus':     'DRIVE_13_PLUS',
  'bundle/pre-11-plus': 'DRIVE_PRE_11_PLUS',
};

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const sessionId = url.searchParams.get('session_id');

  if (!sessionId) {
    return json({ error: 'Missing session_id' }, 400);
  }

  const stored = await env.LT_PURCHASES.get(`session:${sessionId}`, 'json');

  if (!stored) {
    return json({ error: 'not_found' }, 404);
  }

  const downloads = stored.papers.map(p => {
    const envKey = BUNDLE_ENV_KEYS[p.r2_key];
    if (envKey) {
      // Bundle purchase — return the Google Drive folder link directly
      return {
        label: p.label,
        downloadUrl: env[envKey] || null,
        isBundle: true,
      };
    }
    // Regular per-paper purchase
    return {
      label: p.label,
      downloadUrl: `/api/download?s=${encodeURIComponent(sessionId)}&k=${encodeURIComponent(p.r2_key)}`,
      isBundle: false,
    };
  });

  return json({ downloads });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
