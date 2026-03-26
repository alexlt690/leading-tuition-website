/**
 * GET /api/get-downloads?session_id=cs_xxx
 * Returns list of { label, downloadUrl } for the session.
 * downloadUrl points to /api/download?s={sessionId}&k={r2Key}
 */

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

  const downloads = stored.papers.map(p => ({
    label: p.label,
    downloadUrl: `/api/download?s=${encodeURIComponent(sessionId)}&k=${encodeURIComponent(p.r2_key)}`,
  }));

  return json({ downloads });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
