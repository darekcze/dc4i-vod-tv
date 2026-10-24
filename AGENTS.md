# Agent Operating Instructions | DC4I VOD TV

1. **Read first:** [DC4I-BRAND-001](https://app.notion.com/p/3fb522ca403c81199c9bff92c1e84098), [project Notion](https://app.notion.com/p/403522ca403c812d9ffbf5a031d5e026), PROJECT.md, DELIVERY.md.
2. Preserve exact approved circuit-D + profile-C logo geometry. Asset: `assets/brand/DC4I_Official_Circuit_Profile_2026-10-24.png`, SHA256 `3f8624833ca1eb1609bb42013bfc703d185b59207778afab6802a0723a5e8771`. Never substitute the neon wordmark or AI-regenerated approximation.
3. Preserve app id `com.dc4i.boringtv` so Homebrew upgrades rather than duplicates. Display `DC4I VOD TV`.
4. Never write API key values to Git, Notion, issue comments, logs or public-facing URLs. Gitignores: `build/`, `private/`, `dist/`. Cloudflare Pages encrypted secret bindings are preferred when permitted. Local YouTube key is in `private/youtube_api_key.txt`, read-only for owner.
5. The owner wants no TV-side API typing. Never put unusable missing-key warnings into the public UI. TMDB is available; YouTube Data API integration must be tested independently before marking complete.
6. Default region Poland. Provide PL/EN language setting and weather city entries for Europe/US; exclude Asia-specific city presets. Hide root-only features for normal Developer Mode devices.
7. Build: `python3 build_vod_tv.py`; package with `npm exec --yes --package=@webos-tools/cli -- ares-package build/dc4i-boringtv -o private --no-minify`; verify with `python3 test_vod_tv.py`; generate catalogue with `python3 publish_vod_tv.py`.
8. Preview at 1920x1080 using a server bound to localhost, test remote navigation, PL/EN, root/nonroot settings and loading states. Do not claim real LG hardware testing based on Chrome alone.
9. Deploy Cloudflare Pages project `lg-webos-repo` only after passing smoke tests; check `https://lg.darc.dev/`, `/api/apps.json`, app IPK SHA256 and logo. Avoid use of paid GitHub Actions; no paid model subagents or extra schedulers.
10. Preserve all user-approved assets/decisions, create a rollback path and keep a bilingual English/Polish Git documentation mirror. Read source license and avoid unverified claims.
