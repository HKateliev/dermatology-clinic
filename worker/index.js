// Dependency-free Cloudflare Worker. Build-time placeholders are replaced by
// build_worker.py; neither an asset binding nor filesystem access is required.
const assets = __EGO_ASSETS__;
const redirects = __EGO_REDIRECTS__;
const security = __EGO_SECURITY__;
const build = __EGO_BUILD__;
const decoded = new Map();
function bytes(entry) {
  if (!decoded.has(entry.etag)) decoded.set(entry.etag, Uint8Array.from(atob(entry.data), c => c.charCodeAt(0)));
  return decoded.get(entry.etag);
}
function baseHeaders() {
  const headers = new Headers(security);
  headers.set('Cache-Control', 'public, max-age=0, must-revalidate');
  return headers;
}
function redirect(location) {
  const headers = baseHeaders();
  headers.set('Location', location);
  return new Response(null, {status: 301, headers});
}
export default {
  async fetch(request) {
    const headers = baseHeaders();
    if (!['GET', 'HEAD'].includes(request.method)) {
      headers.set('Allow', 'GET, HEAD');
      return new Response(null, {status: 405, headers});
    }
    let url, pathname;
    try {
      url = new URL(request.url);
      pathname = decodeURIComponent(url.pathname);
    } catch {
      return new Response('Bad request', {status: 400, headers});
    }
    if (build.mode === 'production' && url.origin !== build.origin) {
      return redirect(build.origin + url.pathname + url.search);
    }
    if (Object.hasOwn(redirects, pathname)) return redirect(redirects[pathname] + url.search);
    if (pathname.endsWith('/index.html') && Object.hasOwn(assets, pathname.slice(0, -10))) return redirect(pathname.slice(0, -10) + url.search);
    if (!pathname.endsWith('/') && Object.hasOwn(assets, pathname + '/')) return redirect(pathname + '/' + url.search);
    const found = Object.hasOwn(assets, pathname);
    const entry = found ? assets[pathname] : assets['/404/'];
    if (!entry) return new Response('Not found', {status: 404, headers});
    headers.set('Content-Type', entry.type);
    headers.set('ETag', entry.etag);
    if (!found || entry.noindex || build.mode === 'preview') headers.set('X-Robots-Tag', 'noindex, follow');
    if (found && pathname.startsWith('/assets/')) headers.set('Cache-Control', 'public, max-age=86400');
    const matches = (request.headers.get('If-None-Match') || '').split(',').map(value => value.trim());
    if (found && (matches.includes(entry.etag) || matches.includes('*'))) return new Response(null, {status: 304, headers});
    return new Response(request.method === 'HEAD' ? null : bytes(entry), {status: found ? 200 : 404, headers});
  }
};
