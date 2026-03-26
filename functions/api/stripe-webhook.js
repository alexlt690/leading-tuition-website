/**
 * POST /api/stripe-webhook
 * Stripe sends checkout.session.completed here.
 * Verifies signature, stores purchase in KV with 48hr TTL.
 */

const TTL_SECONDS = 172800; // 48 hours

async function verifySignature(body, sigHeader, secret) {
  const parts = {};
  sigHeader.split(',').forEach(part => {
    const [k, ...v] = part.split('=');
    parts[k.trim()] = v.join('=');
  });

  const timestamp = parts['t'];
  const sig = parts['v1'];
  if (!timestamp || !sig) return false;

  // Reject events older than 5 minutes (replay protection)
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - parseInt(timestamp)) > 300) return false;

  const payload = `${timestamp}.${body}`;
  const encoder = new TextEncoder();

  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const sigBytes = await crypto.subtle.sign('HMAC', key, encoder.encode(payload));
  const expected = Array.from(new Uint8Array(sigBytes))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  return expected === sig;
}

export async function onRequestPost(context) {
  const { request, env } = context;

  const body = await request.text();
  const sigHeader = request.headers.get('stripe-signature');

  if (!sigHeader) {
    return new Response('Missing signature', { status: 400 });
  }

  const valid = await verifySignature(body, sigHeader, env.STRIPE_WEBHOOK_SECRET);
  if (!valid) {
    return new Response('Invalid signature', { status: 400 });
  }

  let event;
  try {
    event = JSON.parse(body);
  } catch {
    return new Response('Invalid JSON', { status: 400 });
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const meta = session.metadata || {};
    const count = parseInt(meta.count || '0', 10);

    if (count > 0) {
      const papers = [];
      for (let i = 0; i < count; i++) {
        const r2Key = meta[`r2_${i}`];
        const label = meta[`label_${i}`] || `Paper ${i + 1}`;
        if (r2Key) papers.push({ r2_key: r2Key, label });
      }

      if (papers.length > 0) {
        const record = {
          papers,
          created: Math.floor(Date.now() / 1000),
          email: session.customer_details?.email || null,
        };

        await env.LT_PURCHASES.put(
          `session:${session.id}`,
          JSON.stringify(record),
          { expirationTtl: TTL_SECONDS }
        );
      }
    }
  }

  return new Response('OK', { status: 200 });
}
