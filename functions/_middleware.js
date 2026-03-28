/**
 * Cloudflare Pages middleware
 * Strips known tracking query parameters (?trk=, ?utm_*) that cause
 * Google to index duplicate pages without a user-selected canonical.
 * Redirects to the clean URL with a 301.
 */

const TRACKING_PARAMS = ['trk', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'];

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const params = url.searchParams;

  const hasTracking = TRACKING_PARAMS.some(p => params.has(p));

  if (hasTracking) {
    TRACKING_PARAMS.forEach(p => params.delete(p));
    const cleanUrl = params.toString()
      ? `${url.origin}${url.pathname}?${params.toString()}`
      : `${url.origin}${url.pathname}`;
    return Response.redirect(cleanUrl, 301);
  }

  return context.next();
}
