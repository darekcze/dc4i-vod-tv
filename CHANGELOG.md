# Changelog - DC4I VOD TV

Technical application identifier: `com.dc4i.boringtv` (kept stable across upgrades).

## [1.2.2] - 2026-10-24

### Smarters Player LG Store mapping and detection
- Added LG Store catalog listing **1231221** from the user's [Smarters Player LG page](https://us.lgappstv.com/main/tvapp/detail?appId=1231221) as a *candidate*, not an assumed internal webOS launch ID. Public store ID and internal applicationManager ID are distinct concepts; LG does not publish general installed-app enumeration to ordinary third-party apps.
- The Smarters Player tile now stays visible in the DC4I Apps menu even if `getAppLoadStatus` is denied or all candidate IDs are unrecognized; such a tile is marked `sprawdź` (unverified), not misrepresented as an installed app.
- On selecting the tile or a film's Smarters action, DC4I checks candidate IDs and attempts webOS Application Manager launches one by one until it receives a confirmed successful launch, including testing `1231221` as requested. It remembers successful IDs on the TV and records non-sensitive diagnostics in `localStorage` (key: `vodNativeDiagnostics122`). Failure is reported instead of silently hiding the player.
- Installed-app title matching remains available where webOS permits it. Root not required.

### Stremio selected-title navigation
- Original button **Stremio - aplikacja** continues to attempt official Stremio movie/TV deep links with the IMDb identifier obtained from TMDB. An LG app can ignore the link even if webOS reports the launch succeeded.
- New button **Stremio Web (otwórz tytuł)** launches the official Stremio Web app at `https://web.stremio.com/#/detail/{type}/{IMDb}` for the chosen movie/series via the native webOS browser. This is a distinct web fallback, not the installed LG Stremio app. Stremio Web loads over HTTPS but actual login/player behavior on LG is device-dependent.
- Native Smarters Player has no publicly documented deep-link/search API. The app passes title hints but cannot force the proprietary player to search or play content.

### Verification / known limits
- Automated Node mock tests: visible Smarters tile without verified ID, successful launch via `1231221`, correct error/diagnostic when no candidate works, IMDb movie/series links, browser fallback URL, mock LG launch results.
- Headless Chrome TV E2E: tile visible, both Stremio modes and Smarters controls, Poland streaming filters, Polish weather.
- IPK / manifest SHA256, 32-app repository retention, legacy 1.2.1 and 1.2.0 packages retained for rollback.
- **Real LG pairing and native-app acceptance remain unverified**, tracked in issues [#2](https://github.com/darekcze/dc4i-vod-tv/issues/2) and [#3](https://github.com/darekcze/dc4i-vod-tv/issues/3). No content sources are provided by these third-party players.

## [1.2.1] - 2026-10-24

### Native LG player integration
- Add evidence-backed LG IPTV Smarters app ID `com.iptvsmarters.app` as the first native-app candidate. Identified in Snap One and RTI LG IP-control reference lists. Positive app installation must still be confirmed by `getAppLoadStatus` on the actual TV.
- Fix the optional player probe: it now immediately accepts the first installed ID instead of waiting for all invalid/hanging IDs to complete, which previously hid valid native Smarters installs.
- Allow display-name-based identification from real installed app lists; try `listLaunchPoints` as an optional, permission-dependent fallback when other probes fail. No rooting required.
- Make **Open Stremio** and **Open IPTV Smarters Player** available from every searched title's details, not just those without Polish streaming availability.
- Stremio: resolve IMDb metadata via TMDB `external_ids`, compose official Stremio movie/series details links, fall back to a title search link. LG webOS handling of launch params is unverified.
- Smarters: pass experimental search/title hints through LG's `applicationManager.launch` while opening the native player. The publisher does not document a webOS title/deep-link API, so searching/opening a specific film is not guaranteed.
- Preserve the package ID `com.dc4i.vodtv` introduced in 1.2.0. This release is an in-place update for existing 1.2.0 installations.

### Quality
- New automated Node tests for Smarters discovery, stuck invalid IDs, Stremio IMDb links and search payloads. Chrome TV-sized tests cover buttons both when Poland has a streaming offer and when it does not.
- Existing neon app branding, 32-app Homebrew catalog and 1.2.0 rollback package retained.
- Real LG device acceptance for Smarters and Stremio remains pending, see issues #2 and #3.
- Source and limitations: [native player integration](docs/NATIVE-PLAYER-INTEGRATION.md).

## [1.2.0] - 2026-10-24

### Breaking identity change, authorized by product owner
- New **DC4I VOD TV** LG webOS app ID: `com.dc4i.vodtv`, replacing historical `com.dc4i.boringtv`.
- webOS treats the new ID as a separate app. **Uninstall versions 1.1.x or earlier, then install 1.2.0** from the same Homebrew Channel repository `https://lg.darc.dev/`.
- New downloadable package name `com.dc4i.vodtv_1.2.0_all.ipk`; catalog entry and manifest renamed to `dc4i-vodtv.manifest.json`.
- Previous builds remain archived as rollback downloads but are no longer the active Homebrew catalog entry.

### Neon branding
- Replaced the previous corporate white-background icon and splash with the exact visual of the **Neon DC4I VOD TV** graphic approved by the Chairman, retrieved from the earlier image-generation message in this conversation.
- Versioned app artwork: `assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.webp` (SHA256 `fe7aa367fb1b4f83593a5a647f4dc4a7693ec0888c8e8a046cec02667781f840`), plus PNG source, LG 80/130px icons, splash, branded navbar.
- Preserved DC4I corporate-logo standard separately from the product's neon icon.

### Retained behavior and validation
- Polish/English UI, Polish weather, Warszawa and European/US city picker, region-aware TMDB search, Stremio and IPTV Smarters launch candidates.
- Updated build/test/publish scripts to new technical identity and generated build path.
- Tests verify the new appinfo ID, neon image pixels, archive contents, browser UI, TMDB API and manifest binary hash. Hardware LG acceptance remains open.

## [1.1.1] - 2026-10-24

### Added
- TV-first TMDB search now defaults to titles with verified `flatrate`, `free`, or `ads` streaming-provider offers for the selected country (Poland by default). Added **Available / Others / All** filters, 4 concurrent provider checks and a six-hour cache.
- Titles without a TV streaming offer can open their details and choose **Open Stremio** or **Open IPTV Smarters Player**, using the apps installed on the LG TV. This is an app launch, not a guarantee of title availability or automatic playback.
- Native Stremio detection via LG webOS application ID `io.strem.tv`; exploratory IPTV Smarters candidate probes, not a confirmed vendor ID. Entries display only when `getAppLoadStatus` confirms installation on a non-rooted TV.
- Default weather city **Warsaw / Warszawa**, with deterministic coordinates. Added/preferred London, Paris, Berlin, Rome, Madrid, New York, San Francisco, Los Angeles plus the remaining Europe/US choices carried from 1.1.0.
- Hardware-independent Chrome E2E tests covering the Poland filter, other-results fallback, Polish weather labels and non-root UI visibility.

### Fixed
- Translated weather condition codes and detailed forecast labels to Polish, while retaining English when UI language is EN.
- One-time migration from saved `weatherCity=auto` to Warsaw on first upgrade, preserving an explicit choice of Auto afterward. Previously IP geolocation could report Tomaszów Mazowiecki.
- Geocoding ambiguity in locations such as New York. Preferred cities have fixed coordinates; other cities are filtered by country when geocoding.
- Avoided serial app-id probing that could delay startup for up to 30 seconds; optional native-app probes complete within a bounded time.
- Homebrew publication workflow updates the DC4I VOD TV package while keeping the other applications in the multi-app catalog.

### Validation
- JS syntax checks and webOS IPK archive integrity.
- TMDB API test: HTTP 200.
- Headless Chromium 1920×1080 mocked-provider tests: regional streaming filter, fallback buttons, Warsaw, Polish cloudy-weather and root-only UI concealment.
- Deployment URL / SHA256 / Homebrew catalog: see DELIVERY.md for live release verification.

### Known limitations / follow-ups
- No LG hardware pairing was available to verify IPTV Smarters' actual app ID. The guessed candidates must not be treated as verified; issue [#2](https://github.com/darekcze/dc4i-vod-tv/issues/2).
- Official Stremio app ID is known, but whether its webOS build consumes the documented deep-link search parameter requires TV testing; issue [#3](https://github.com/darekcze/dc4i-vod-tv/issues/3).
- TMDB streaming availability can lag real provider catalogs. Results are metadata estimates, not authoritative live confirmations.
- YouTube Data API secret exists locally but protected backend integration is still pending.
- Upstream TheBoringTV has no clearly declared repository-wide license; redistribution terms need confirmation before broader commercial publication; issue [#4](https://github.com/darekcze/dc4i-vod-tv/issues/4).

## [1.1.0] - 2026-10-24
- First full DC4I VOD TV branded release with canonical circuit-D/profile-C monogram, navy/cyan icon and splash, PL/EN language controls, 40 Europe/US city entries, non-root controls hidden by default, and TMDB key preconfigured.
- Technical app identifier retained from DC4I BoringTV for an in-place upgrade.
- Released in Homebrew Channel via `https://lg.darc.dev/`; distributed alongside the DStore app catalog.

## [1.0.1] - 2026-10-24
- Earlier DC4I BoringTV name, Polish region, initial localization, optional YouTube Trending disabled without API key.

## Source attribution
- [TheBoringTV LG webOS source](https://github.com/theboringhumane/theboringtv-lgwebos), pinned commit `8cdea8940355685a82aac127fcdcf113a30684f6`.
- [DC4I approved monogram and asset rules](https://app.notion.com/p/3fb522ca403c81199c9bff92c1e84098).

## [1.2.4] - 2026-10-24

### Correct IPTV Smarters Player identity from a real LG TV
- Paired with the owner's LG OLED55G42LW through [klattimer/LGWebOSRemote](https://github.com/klattimer/LGWebOSRemote), using the authorized TV pairing popup.
- **Evidence: 67 launch points returned** from webOS `ssap://com.webos.applicationManager/listLaunchPoints`. The real IPTVSmartersPlayer is `com.smarterstvplayers.net`. The separate IPTVSmartersPro is `com.iptvsmarters.app` and Stremio is `io.strem.tv`.
- Replaced all tentative Smarters launcher IDs with the confirmed `com.smarterstvplayers.net`, cleared previously cached wrong launch IDs, and corrected app-tile/root discovery so the Pro variant never matches.
- LG Store catalog number 1231221 is not an internal launch ID. Native title search in IPTVSmartersPlayer remains unverified; the external player can only open its own catalog unless it implements deep-linking.
- Saved the full 67-entry inventory as private JSON and CSV under `private/lgremote-output`, excluded from Git. Both Mac mini and Mac Pro have the MIT-licensed desktop LGWebOSRemote tool installed on AI-Hot.
- No additional webOS app is necessary to inspect installed programs. This is a computer-side command-line tool, not an IPK package for Homebrew Channel.

### Validation
- Unit tests exclude launching `com.iptvsmarters.app` when IPTVSmartersPlayer is selected; app-info and IPK tests; 1920x1080 Chrome simulated tests; live deployment checks pending.
- The app ID stays `com.dc4i.vodtv` and updates v1.2.3 in-place.

## [1.2.3] - 2026-10-24
- Fixed Search cards appearing unresponsive: Search overlay now hides when opening details, and restores when returning.
- Prevented launching the wrong product (Smarters Player Pro, LG Store #950615). The requested IPTV Smarters Player listing is #1231221; only this unverified candidate is tried until the actual internal webOS ID is obtained.
- Stremio Web remains the confirmed working route to selected titles on the user's LG. Native Stremio and IPTV Smarters lack confirmed external title deep-link support.

## [Catalog update] - 2026-10-25

- Added official Kodi 21.0 Omega for LG webOS (org.xbmc.kodi, ARM, native, no root).
- Download uses Kodi Foundation official mirror; the 92.6 MB binary is not committed to Git or copied into Cloudflare Pages (static asset limit).
- Verified SHA-256 b8ac326df8ad7cf0b52e4f816ab7c39c95410254b1bc3b9b3d024035ecec58ff on Mac Pro and Mac mini.
- Installed and launched Kodi on LG OLED55G42LW (192.168.1.60) using ares-install and ares-launch.
- Kodi webOS 21.0 differs from macOS Kodi 21.3 ARM64 DMG.
- Stremio native webOS deep-link support remains unverified despite successful app launch.
