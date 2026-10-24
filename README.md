# DC4I LG webOS Homebrew Repository

Canonical TV repository: https://lg.darc.dev/

Homebrew Channel expects JSON at the root URL. A browser-friendly project page is at https://lg.darc.dev/about.html.

## DC4I VOD TV 1.1.1

- Identifier: com.dc4i.boringtv (installs alongside original)
- Market: Poland (PL), interface: Polish-first
- Artwork: the official DC4I transparent company logo
- TMDB v3: bundled and tested, no TV setup
- YouTube Trending: disabled until Google YouTube Data API v3 credentials become available
- Package (Cloudflare Pages): https://lg.darc.dev/packages/com.dc4i.boringtv_1.1.1_all.ipk
- SHA256: e99af2d95e5a34e24efbdd3eecc69130d2f39350feb0e5844519a0312e606527

Package and catalog are deployed on Cloudflare Pages. The binary is intentionally **not committed to GitHub** as it embeds a client-side TMDB key. Anyone downloading the public IPK can extract that client key, so usage must be monitored and the key rotated if misused.

This personalized build is derived from the upstream project [theboringhumane/theboringtv-lgwebos](https://github.com/theboringhumane/theboringtv-lgwebos). It is not endorsed by LG or TMDB.

Reproducible local preparation scripts: build_dc4i.py (base), build_vod_tv.py (branding and PL/EN), test_vod_tv.py, publish_vod_tv.py. They read a privately stored keys.js and do not write secrets to git-tracked plaintext files.

To release changes, build the app IPK, run test_vod_tv.py, run publish_vod_tv.py, and deploy dist via Cloudflare Pages. Test Homebrew and app startup on a real LG webOS TV before claiming end-to-end compatibility.

## Multiplatform webOS repository

- Browser interface: https://lg.darc.dev/browse/
- Homebrew Channel feed: https://lg.darc.dev/ (JSON for TVs) or https://lg.darc.dev/api/apps.json
- DStore import and operational details: docs/DSTORE-CATALOG.md

## Version history and known issues

- [Changelog](CHANGELOG.md) and [Polish changelog](docs/pl/CHANGELOG.md)
- [Delivery evidence](DELIVERY.md) and [Project charter](PROJECT.md)
- Stremio and IPTV Smarters handoff needs real LG TV validation.
