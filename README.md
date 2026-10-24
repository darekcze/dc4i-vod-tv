# DC4I LG webOS Homebrew Repository

Canonical TV repository: https://lg.darc.dev/

Homebrew Channel expects JSON at the root URL. A browser-friendly project page is at https://lg.darc.dev/about.html.

## DC4I BoringTV 1.0.0

- Identifier: com.dc4i.boringtv (installs alongside original)
- Market: Poland (PL), interface: Polish-first
- Artwork: the official DC4I transparent company logo
- TMDB v3: bundled and tested, no TV setup
- YouTube Trending: disabled until Google YouTube Data API v3 credentials become available
- Package (Cloudflare Pages): https://lg.darc.dev/packages/com.dc4i.boringtv_1.0.0_all.ipk
- SHA256: bf68342d9a164ce18a9f79329d14503ac32fe793347a09b385df3bc848ba5475

Package and catalog are deployed on Cloudflare Pages. The binary is intentionally **not committed to GitHub** as it embeds a client-side TMDB key. Anyone downloading the public IPK can extract that client key, so usage must be monitored and the key rotated if misused.

This personalized build is derived from the upstream project [theboringhumane/theboringtv-lgwebos](https://github.com/theboringhumane/theboringtv-lgwebos). It is not endorsed by LG or TMDB.

Reproducible local preparation scripts: build_dc4i.py, test_dc4i.py, publish_dc4i.py. They read a privately stored keys.js and do not write secrets to git-tracked plaintext files.

To release changes, build the app IPK, run test_dc4i.py, run publish_dc4i.py, and deploy dist via Cloudflare Pages. Test Homebrew and app startup on a real LG webOS TV before claiming end-to-end compatibility.
