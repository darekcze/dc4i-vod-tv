# DStore import and dual-mode LG webOS catalogue
Updated: 2026-10-24. Canonical repo: https://lg.darc.dev/.

## Design
- The machine-readable JSON is always available at /api/apps.json and /apps.json. Root / delivers JSON for Homebrew Channel and TV requests.
- Desktop and mobile web browsers that navigate to / are redirected to /browse/ by a Cloudflare Pages Worker. Explicit /browse/ always shows the responsive catalogue. Use ?view=repo or ?view=web at root to force either mode.
- The responsive website loads /api/apps.json and /catalog/dstore.json. No framework or bundle compilation is needed.
- The primary HTTPS download path is a checksum-pinned static Cloudflare Pages mirror of 31 imported IPKs, with binaries stored and published from AI-Hot. The old source-proxy remains limited to allowlisted files but is not used in manifests because it proved too slow. File names must match its build-time allowlist.
- The manifest includes SHA-256 and exact size. Homebrew should reject bytes that differ from the frozen snapshot.

## Provenance and limitations
Original source: http://dstore.net.swtest.ru/ipk/ (snapshot 2026-10-24).
166 unique IPK rows indexed. Only packages from a curated allowlist that pass a structural integrity check are included in the Homebrew feed. The remaining entries are listed in the browser with clear external/unverified labels.
The importer downloads into memory, parses ar/tar/appinfo and extracts raster icons, without executing IPKs or persisting their binaries on the Mac mini system disk.
SHA-256 comparison is not a publisher signature or a security audit. The original host serves HTTP and has a broken HTTPS certificate. Apps may be malicious, outdated, unlicensed or incompatible with the target TV. Root-required, exploit or downgrade apps are not automatically included. Do not confuse technical verification with code auditing.

## Source files
- scripts/import_dstore.py reads the source snapshot, builds data/dstore-index.json and data/dstore-verified.json.
- scripts/mirror_dstore.py downloads and checksum-validates selected IPKs to AI-Hot only.
- scripts/build_catalog.py merges current first-party manifest, imported apps, web frontend and Worker into dist.
- scripts/test_catalog.py checks JSON schema, identities, hashes, asset references and counts.
- web/index.html, web/catalog.css, web/catalog.js are the responsive catalogue source.
- web/worker.template.js is the Cloudflare Pages content-negotiation and verified package proxy.
- docs/DSTORE-CATALOG.md is this operational guide.

## Release process
1. Build and publish the DC4I first-party app, e.g. python3 publish_vod_tv.py.
2. Optionally update private/dstore-index-20261024.txt and re-run python3 scripts/import_dstore.py.
3. Run python3 scripts/mirror_dstore.py, python3 scripts/build_catalog.py and python3 scripts/test_catalog.py.
4. Deploy a preview to Cloudflare Pages, verify and deploy main with npx --no-install wrangler pages deploy dist --project-name lg-webos-repo --branch main.
5. Confirm /browse/ and /api/apps.json separately, run a package-proxy download/hash check. A real LG TV installation is required before claiming end-to-end compatibility.

Never commit private IPKs or secrets. The dist and private directories are gitignored. The Cloudflare Pages Worker may be subject to the free-tier usage limits.
