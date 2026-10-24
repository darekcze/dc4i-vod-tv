// Cloudflare Pages advanced mode: JSON for Homebrew, visual catalogue for browsers.
// The optional HTTPS proxy is tightly restricted to checksum-verified filenames.
const WHITELIST = new Set(__ALLOWED_NAMES__);
const upstreams = ["http://dstore.net.swtest.ru/ipk/", "http://dstore4.ydns.eu/ipk/"];
const tvRegex = /web0s|webos|smarttv|smart-tv|hbbtv|hbchannel|lgtv|netcast|lg\.browser/i;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    if (pathname.startsWith("/source/ipk/")) {
      if (!["GET","HEAD"].includes(request.method)) return new Response("Method not allowed", {status:405});
      let filename;
      try { filename = decodeURIComponent(pathname.slice("/source/ipk/".length)); }
      catch { return new Response("Bad package name", {status:400}); }
      if (!WHITELIST.has(filename) || filename.includes("/") || filename.includes("\\")) {
        return new Response("Package not in verified catalogue", {status:404});
      }
      for (const origin of upstreams) {
        try {
          const remote = await fetch(origin + encodeURIComponent(filename), {
            method: request.method, headers: {"Accept":"application/octet-stream"},
            redirect:"follow", cf: {cacheTtl: 3600, cacheEverything:true}
          });
          if (!remote.ok) continue;
          const headers = new Headers({
            "Content-Type":"application/vnd.shana.informed.package",
            "Cache-Control":"public, max-age=3600",
            "Access-Control-Allow-Origin":"*",
            "X-Content-Type-Options":"nosniff",
            "Content-Disposition":"attachment; filename=\"webos-package.ipk\"; filename*=UTF-8''" + encodeURIComponent(filename)
          });
          const size = remote.headers.get("Content-Length");
          if (size && /^\d+$/.test(size)) headers.set("Content-Length",size);
          return new Response(request.method==="HEAD"?null:remote.body,{status:200,headers});
        } catch (err) { /* Try the second fixed DStore host. */ }
      }
      return new Response("Upstream DStore package unavailable",{status:502});
    }
    if (pathname==="/" || pathname==="/index.html") {
      const force=url.searchParams.get("view");
      const acceptsHtml=(request.headers.get("Accept")||"").includes("text/html");
      const ua=request.headers.get("User-Agent")||"";
      if (force==="web" || (force!=="repo" && acceptsHtml && !tvRegex.test(ua))) {
        return Response.redirect(new URL("/browse/",url),302);
      }
    }
    return env.ASSETS.fetch(request);
  }
};
