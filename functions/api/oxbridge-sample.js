/**
 * GET /api/oxbridge-sample?k=oxbridge-samples/biology-sample.pdf
 * Serves free sample PDFs from R2 — no payment required.
 * Only serves keys under the oxbridge-samples/ prefix.
 */
export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const key = url.searchParams.get('k');

  if (!key || !key.startsWith('oxbridge-samples/')) {
    return new Response('Not found', { status: 404 });
  }

  // Prevent path traversal
  if (key.includes('..')) {
    return new Response('Bad request', { status: 400 });
  }

  const object = await env.LT_ANSWERS.get(key);
  if (!object) {
    return new Response('Sample not found', { status: 404 });
  }

  const filename = key.split('/').pop();
  return new Response(object.body, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `inline; filename="${filename}"`,
      'Cache-Control': 'public, max-age=86400',
    },
  });
}
