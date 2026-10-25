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
- [x] Install/update to 1.2.12 on physical LG TV and confirm app launch, package ID, manifest, and catalog network access.
- [ ] Final hands-on TV remote navigation and per-provider playback acceptance; a package install does not prove every external player works.
- [ ] Confirm upstream distribution rights (repository license currently unspecified).
- [ ] Independent final visual acceptance of the new icon/splash.

## Remaining blockers
YouTube key is available privately at `private/youtube_api_key.txt` and was created on Google Cloud project `h0st-pl`. It MUST NOT be placed in a public package without API restrictions or a server-side proxy. Browser can still launch YouTube and TMDB trailer links independently from YouTube Data API.

## 1.2.12 release verification (2026-10-25)
- Public Homebrew catalog is the update source: `https://lg.darc.dev/api/apps.json`. Production manifest includes `releaseDate`, `published_at`, exact IPK size and SHA-256.
- Cloudflare Pages: `lg-webos-repo`, production deployed on `main`. Previous deployment can be restored if needed. Backed up preceding manifest and Pages Worker in `private/release-backups/2026-10-25-pre-1212`.
- Production tested by direct HTTPS requests and TV-local HTTP call. Homebrew has 33 items, other 32 unchanged.
- IPK SHA-256: `27830bcc55553374149b924eb91bb748c6ccc545dc8129c7cd7bb0269d219466`.
- LG OLED55G42LW: Ares install succeeded, launched app 1.2.12; TV-side HTTP to published API returned 1.2.12.
- Chrome real-origin version check returned `current` / `Aktualna`. Automatic installer is not implied by a version check.

## 1.2.13 unified search release, 2026-10-25

- LG webOS package `com.dc4i.vodtv_1.2.13_all.ipk` was published to Cloudflare Pages `lg-webos-repo` and installed/launched on LG OLED55G42LW. The TV's installed appinfo reported version 1.2.13. Public Homebrew feed (`/api/apps.json`) returned the same version and retained 33 package entries.
- Quick panel targets: logo and Website open `https://www.dc4i.com/labs`; App repo opens `https://lg.darc.dev/browse/`. Both public URLs responded HTTP 200 in host verification.
- Both search and title details include exactly YouTube, Kodi, Plex, Stremio, and Smarters Player below selected-service VOD results. No offer means `Brak w wybranych serwisach`.
- Kodi Title Handoff 0.1.2 deployed on the TV. Its private catalog stays on the TV. Tested `search-empty` and an actual native Kodi selection dialog for Breaking Bad.
- E2E Chromium 1920x1080 smoke tested Search and Details with a mocked TMDB provider/offers response; static and unit tests verified actions. Not all third-party apps guarantee search/deep-link support, especially Smarters.
- IPK SHA-256: `27cfd23565fe1f2671f804610f8cf8d71ea773e58fbee99c959dc19741352ee4` (matched production download). Previous production deployment is available for rollback.

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

## 1.2.1 native LG app detection and search handoff
- Credible published LG IPTV Smarters ID: `com.iptvsmarters.app`; native device validation still pending.
- Native-app probe returns the first confirmed installed ID, avoiding the earlier Promise.all timeout suppression.
- Stremio movie/series metadata links rely on TMDB external IMDb IDs. Title handoff via webOS appManager `contentTarget` is attempted, not verified on a physical LG.
- Smarters app launch passes best-effort title search hints only, since the vendor does not document webOS title deep-link support.
- Search details buttons now appear for all movie/series titles, irrespective of provider availability in Poland.
- Node mocked Luna tests + headless Chrome TV browser acceptance required; see docs/NATIVE-PLAYER-INTEGRATION.md.

## 1.2.2 diagnostic player release
- TV tile for Smarters Player persists even if getAppLoadStatus cannot confirm its internal ID. Catalog ID 1231221 is tested only as an unverified launch ID, never assumed to be the installed app's true ID.
- Stremio native and Stremio Web controls are intentionally separate. Native may ignore contentTarget; browser can open the Stremio Web title route. The latter is not native playback.
- Node tests: detection failures, launch ID trials, persistent diagnostics, web route, movie/TV IMDb URLs. Chrome E2E: pinned Smarters tile and all details buttons.
- Hardware acceptance is NOT done; do not close issue #2 or #3 until confirmed by the user's LG television.

## 1.2.15 native IPTV verification (2026-10-25)
- IPK built and hashed, existing TMDB and external search unchanged. Playlists configured on TV, not embedded in IPK.
- Xtream CORS verified. 145,699 live/VOD/series records loaded on actual LG G4. HD TVP Info, one 4K film and one HD series episode played through native video element.
- Mac Pro local proxy on TCP 18774 disabled, and TV resynced the provider directly after app page reload.
- LG D-pad input-focus regression added in 1.2.15 after successful hardware v1.2.14 playback.
- Known limitation: packaged webOS app storage may be cleared by updates or app removal. No cloud backup of personal Xtream credentials.
- Systemwide LG Search indexing was not verified.
