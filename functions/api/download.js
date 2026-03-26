/**
 * GET /api/download?s={sessionId}&k={r2Key}
 * Verifies session is valid in KV, then streams the PDF from R2.
 */

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const sessionId = url.searchParams.get('s');
  const r2Key = url.searchParams.get('k');

  if (!sessionId || !r2Key) {
    return new Response('Bad request', { status: 400 });
  }

  // Verify session exists and hasn't expired
  const stored = await env.LT_PURCHASES.get(`session:${sessionId}`, 'json');
  if (!stored) {
    return new Response(
      '<html><body style="font-family:sans-serif;padding:2rem"><h2>Link expired</h2><p>This download link has expired (48-hour limit). Please <a href="/contact">contact us</a> if you need help.</p></body></html>',
      { status: 410, headers: { 'Content-Type': 'text/html' } }
    );
  }

  // Verify the requested key is in the purchased papers
  const allowed = stored.papers.some(p => p.r2_key === r2Key);
  if (!allowed) {
    return new Response('Forbidden', { status: 403 });
  }

  // Fetch from R2
  const object = await env.LT_ANSWERS.get(r2Key);
  if (!object) {
    return new Response('File not found — it may not have been uploaded yet.', { status: 404 });
  }

  const filename = r2Key.split('/').pop();

  return new Response(object.body, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Cache-Control': 'private, no-store',
    },
  });
}
