# Changelog - DC4I VOD TV

Technical application identifier: `com.dc4i.boringtv` (kept stable across upgrades).

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
