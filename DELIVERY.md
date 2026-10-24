# Delivery and Evidence | DC4I VOD TV

## Release channels
- Canonical TV source: https://lg.darc.dev/
- Installer catalogue: https://lg.darc.dev/api/apps.json
- Product info: https://lg.darc.dev/about.html
- Git source: https://github.com/darekcze/dc4i-vod-tv
- Cloudflare Pages project: `lg-webos-repo` (infrastructure project name retained)

## Test gate
- [x] Official owner-supplied PNG SHA256 checked against Mac Pro and uploaded image.
- [x] App display changed to DC4I VOD TV, technical ID retained for in-place update.
- [x] PL region, PL/EN UI setting, 40 European/US cities, root-only UI hidden by default.
- [x] JS syntax, IPK archive contents, TMDB configuration API 200.
- [ ] YouTube Data API backed by protected deployed service, real response and cache/quota test.
- [ ] Install/update on user's physical LG TV, hardware remote navigation, streaming app links.
- [ ] Confirm upstream distribution rights (repository license currently unspecified).
- [ ] Independent final visual acceptance of the new icon/splash.

## Remaining blockers
YouTube key is available privately at `private/youtube_api_key.txt` and was created on Google Cloud project `h0st-pl`. It MUST NOT be placed in a public package without API restrictions or a server-side proxy. Browser can still launch YouTube and TMDB trailer links independently from YouTube Data API.

## Rollback
Cloudflare Pages retains previous deployments. Current production is the source-of-truth. To revert, redeploy the previously verified Pages deployment and its matching manifest and binary, do not merely change version numbers. Local packages are kept under `private/` on AI-Hot.

## Change log
- 2026-10-24: official brand corrected; logo registry verified, product repo renamed, version 1.1.0 built, PL/EN UI and rooted gates added.

## 1.1.1 release evidence, 2026-10-24
- Package ID: `com.dc4i.boringtv`. Display name: DC4I VOD TV. Target version: `1.1.1`.
- Source: [Changelog](CHANGELOG.md) / [Polski](docs/pl/CHANGELOG.md).
- Added Polish weather condition and heading translations, one-time Warsaw migration, fixed coordinates for Warsaw and major European/US cities.
- Added TMDB provider checks for PL streaming (flatrate/free/ads), Available/Others/All filters, and fallback app buttons.
- Official Stremio webOS ID `io.strem.tv` known, native app handoff unverified on physical device.
- IPTV Smarters native app ID unknown. Candidate IDs probed but no unsupported tiles are shown without positive getAppLoadStatus. Tracking issue [#2](https://github.com/darekcze/dc4i-vod-tv/issues/2).
- Automated headless Chrome E2E: PASS for PL home boot, non-root UI, available-vs-others filter, fallback details, Warsaw and Polish weather.
- Local TMDB API: HTTP 200. webOS `.ipk` JS syntax checks and archive integrity: PASS.
- Catalogue and IPK SHA256 are rechecked after deployment; no physical LG TV test has been claimed.

## Release 1.2.0, product identity migration and neon logo
- Owner explicitly accepted a new package ID and required uninstall/reinstall from `com.dc4i.boringtv` to `com.dc4i.vodtv`.
- The exact earlier neon-generated DC4I VOD TV art is now source-controlled at `assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png`.
- LG webOS appicon 80x80, largeIcon 130x130, splash 1920x1080 and UI header generated from the approved neon art.
- Homebrew catalog switches to new ID and neon icon URL, retains other 31 applications. Older IPKs remain accessible by direct URL for rollback, not for in-place update.
- Package and manifest checksums must be verified on the public domain before marking complete; real LG TV launch remains pending.
