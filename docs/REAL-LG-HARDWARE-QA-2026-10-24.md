# DC4I VOD TV | Real LG Hardware QA | 2026-10-24

## Scope and evidence

- Device: LG OLED55G42LW, local network address `192.168.1.60`.
- Tested installed app: `com.dc4i.vodtv` version `1.2.4`.
- Test host: Mac Pro, authorized LGWebOSRemote pairing plus webOS Developer Mode `ares` commands.
- App inspector: Chrome DevTools Protocol attached to the **actual TV's Chromium 120** running `file:///media/developer/apps/usr/palm/applications/com.dc4i.vodtv/index.html`.
- Local evidence: `/Volumes/AI-Hot/Services/LGWebOSRemote/results/real-lg-cdp-{home,search,details,apps,end_home}.png`. Screenshots and remote pairing credentials are stored privately, not committed.
- Replayable QA script: `/Volumes/AI-Hot/Services/LGWebOSRemote/results/test_dc4i_keyhandler_real_tv.mjs`. Command output ended with `REAL_LG_NATIVE_WEBOS_KEYHANDLER_ALL_TESTS_PASS`.

## Confirmed on hardware

| Scenario | Evidence | Status |
| --- | --- | --- |
| Installed app starts and remains in foreground | App inspector + `getForegroundAppInfo` | PASS |
| Home navigation: LEFT/RIGHT/UP/DOWN and hero title cycling | Actual TV Chromium DOM focus and title changed after synthetic `keydown` | PASS |
| OK opens Search | `TV.view() === 'search'`; TV inspector screenshot | PASS |
| Live TMDB Trending fetched on TV | Cards shown in search | PASS |
| Text search for **Matrix** | Real TMDB response with 16 matching cards, one identified as `Matrix` 1999 | PASS |
| LEFT/RIGHT between results | DOM focus moved between `Matrix` and `Matrix Reaktywacja` | PASS |
| OK on Matrix search result | Details overlay shown, search hidden, real TMDB metadata/cover loaded | PASS |
| Provider and actions | Prime Video + `Stremio - aplikacja`, `Stremio Web`, `Smarters Player`, watchlist | PASS |
| BACK details -> search -> home | View states and overlay visibility changed correctly | PASS |
| Apps tab, Smarters tile, arrows between tiles, BACK | 18 native/shortcut tiles, correct Smarters tile displayed | PASS |
| Quick settings, directional focus and BACK | Panel open/down/back | PASS |
| Weather open/back | Polish loading status, panel transitions | PASS |
| User-chosen film passed to Stremio launcher | DC4I details button clicked with **Matrix** (IMDb `tt0133093`); LG reported `io.strem.tv` foreground | PASS, app launch only |
| User-chosen film passed to IPTV Smarters launcher | DC4I details button clicked with **Matrix**; LG reported **`com.smarterstvplayers.net`**, not Smarters Pro | PASS, app launch only |

**Test-method distinction:** synthetic `KeyboardEvent('keydown')` was dispatched within the application **on the physical TV** through the authorized webOS Inspector, exercising the same JS keyboard navigation code as the remote. A separate physical remote emulation through LGWebOSRemote's pointer socket sent RIGHT, but the TV frequently delivered `keyup` without `keydown`; therefore the entire hardware remote's actual buttons cannot be certified from this run. In one earlier run a RIGHT pointer press changed hero selection. When Netflix was unexpectedly in the foreground, DC4I `document.visibilityState` became `hidden` and stopped receiving events. Tests require checking the current foreground app.

## Unverified / constraints

- Native Stremio **selected movie details** are not independently confirmed. LG reported a successful launch to `io.strem.tv`, but its implementation may ignore `contentTarget`.
- IPTV Smarters Player **selected movie search/playback** is not independently confirmed. Proper installed app ID `com.smarterstvplayers.net` launches, but its webOS app's `search`/`searchQuery`/`title` contract is not documented.
- User previously reported that **Stremio Web** opens a selected title correctly; this flow is distinct from the native Stremio app.
- Native Stremio and Smarters application views are not exposed by webOS `ares-inspect` for inspection; the TV's privileged screenshot API returned `Denied method call`. Do not claim content navigation is proven or attempt privilege bypass.
- Physical Magic Remote keypress reliability needs a separate human-triggered acceptance run. The DOM keyboard handler path was proven, not the raw wireless remote hardware path.
- The weather feed was observed in Polish as loading and view/back worked; the actual forecast content was not rechecked in this hardware run.

## Findings and follow-up

1. No further DC4I navigation code defect was found in the 1.2.4 Search -> Matrix -> Details -> Search -> Home route.
2. External-player launch route is correctly bound to the requested applications, including exact on-device Smarters ID `com.smarterstvplayers.net`. Do not regress by substituting `com.iptvsmarters.app` (different Smarters **Pro** product).
3. **One remaining product limitation:** third-party native apps must implement a public title/deep-link contract to open a selected movie. Do not advertise verified native direct playback. Stremio Web remains the working user-reported alternative.
4. Keep issue #2 (Smarters title contract) and #3 (native Stremio deep-link) open until the native app itself proves correct title navigation.
5. Consider testing a native **Magic Remote button press** during a live interactive acceptance when the user is at the TV. Do not infer hardware validation solely from CDP synthetic keys.

Status: **1.2.4 real LG installation, DC4I navigation JS, real TMDB title details, and native external app launch all PASS. Native target-title navigation and complete physical remote hardware verification remain unverified.** No new code release was required by this QA result.
