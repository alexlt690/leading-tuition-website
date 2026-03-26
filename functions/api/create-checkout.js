/**
 * POST /api/create-checkout
 * Body: { papers: [{ak: "11-plus/school/file-mark-scheme.pdf", label: "School 2023 Maths"}] }
 * Creates a Stripe Checkout Session and returns { url }
 */

function toStripeForm(obj, prefix) {
  const parts = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}[${key}]` : key;
    if (Array.isArray(value)) {
      value.forEach((item, i) => {
        if (typeof item === 'object' && item !== null) {
          parts.push(...toStripeForm(item, `${fullKey}[${i}]`));
        } else {
          parts.push([`${fullKey}[${i}]`, String(item)]);
        }
      });
    } else if (typeof value === 'object' && value !== null) {
      parts.push(...toStripeForm(value, fullKey));
    } else {
      parts.push([fullKey, String(value)]);
    }
  }
  return parts;
}

export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    const { papers } = await request.json();

    if (!papers || papers.length === 0) {
      return json({ error: 'No papers selected' }, 400);
    }

    // Line items — £3 per paper
    const lineItems = papers.map(p => ({
      price_data: {
        currency: 'gbp',
        product_data: { name: p.label + ' — Answers' },
        unit_amount: 300,
      },
      quantity: 1,
    }));

    // Discount coupon
    let coupon = null;
    if (papers.length >= 3) coupon = 'MULTI20';
    else if (papers.length >= 2) coupon = 'MULTI10';

    // Metadata — store r2 keys + labels so webhook can save them
    const metadata = { count: String(papers.length) };
    papers.forEach((p, i) => {
      metadata[`r2_${i}`] = p.ak;
      metadata[`label_${i}`] = p.label.substring(0, 490); // Stripe 500 char limit
    });

    const sessionData = {
      mode: 'payment',
      success_url: 'https://www.leadingtuition.co.uk/purchase-confirmed?session_id={CHECKOUT_SESSION_ID}',
      cancel_url: 'https://www.leadingtuition.co.uk/resources/11-plus',
      line_items: lineItems,
      metadata,
      payment_intent_data: { metadata },
    };
    if (coupon) sessionData.discounts = [{ coupon }];

    const params = new URLSearchParams(toStripeForm(sessionData));

    const stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    const session = await stripeRes.json();

    if (!stripeRes.ok) {
      console.error('Stripe error:', session.error);
      return json({ error: session.error?.message || 'Stripe error' }, 500);
    }

    return json({ url: session.url });
  } catch (err) {
    console.error('create-checkout error:', err);
    return json({ error: 'Internal error' }, 500);
  }
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
