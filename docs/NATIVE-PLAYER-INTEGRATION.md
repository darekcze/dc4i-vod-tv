# DC4I VOD TV 1.2.1: LG native-player handoff

## Purpose
The user has installed **Stremio** and **IPTV Smarters Player** on their LG TV. Stremio was already listed in the DC4I launcher, but Smarters Player did not appear because the previous candidates omitted a documented LG app ID.

## App discovery
- **Stremio**: primary LG application ID `io.strem.tv`. The previous app tile was already working according to the user.
- **IPTV Smarters Player**: `com.iptvsmarters.app`, listed in [Snap One IP Control Guide](https://help.snapone.com/sb-v4-ig/Content/Topics/IP%20Control%20Guide.htm) and [RTI LG IP integration driver](https://driverstore.uat.rticontrol.com/driver/lg-ip). This is a credible app ID for the same name, but **not yet independently confirmed for this specific LG installation**.
- Detect installed IDs with the official [webOS Application Manager getAppLoadStatus](https://webostv.developer.lge.com/develop/references/application-manager) service. Resolve immediately on the first positive candidate instead of waiting on unknown IDs. When root helper lists real installed apps, use the actual ID and title; optionally try `listLaunchPoints` if allowed on the firmware.
- Present an optional app tile only if positively detected. No root privilege is required.
- If the native app isn't detected, do not silently launch an arbitrary app. Report the remaining unresolved ID and keep issue #2 open.

## Opening a selected title
- Buttons **Open Stremio** and **Open IPTV Smarters Player** appear in every movie/series details view, whether or not TMDB lists a streaming service in Poland.
- **Stremio:** request IMDb ID from TMDB `external_ids` (attached to the existing movie/TV details fetch; if missing, perform one extra lookup). Build official URLs:
  - Movie: `stremio:///detail/movie/tt0133093/tt0133093`
  - TV series: `stremio:///detail/series/tt0944947`
  - If IMDb ID is unavailable: `stremio:///search?search=<URI-encoded title>`
  - Launch the installed Stremio application with a `contentTarget` URI and title hint. This follows the [Stremio deep-link specification](https://stremio.github.io/stremio-addon-sdk/deep-links.html), but Stremio explicitly notes platform support varies. **Not yet verified on LG webOS**.
- **Smarters Player:** the website [smartersplayer.tv](https://smartersplayer.tv/en) documents a native LG player, local/remote playlist configuration and catalog discovery, but no public webOS title-search launch/deep-link contract. DC4I sends best-effort `search`, `searchQuery` and `title` parameters through the official webOS applicationManager `launch` API. These parameters may be ignored, leaving the player on its normal home screen; the user can search their own playlist.
- IPTV Smarters Player is a player, **not a source of films or licenses**. Title availability depends on lawful playlists supplied by the user, and TMDB availability is not proof of a Smarters catalog entry.

## Verification
- Native-player unit tests: resolve on first successful app ID despite hanging invalid IDs; inspect fallback launch payloads; detect an installed app by title; verify IMDb movie/series URLs and query fallback.
- Chrome E2E: actions are visible for streaming-available **and** unavailable titles; Polish weather and search navigation remain working.
- Real LG app ID, actual Stremio direct handoff and Smarters' response to search parameters are pending physical-TV acceptance. Track [#2](https://github.com/darekcze/dc4i-vod-tv/issues/2) and [#3](https://github.com/darekcze/dc4i-vod-tv/issues/3).

No TV-side API credential entry, no additional subscription, and no rooting was introduced.

## Addendum 1.2.2, LG Store listing and known platform limits
- The user's LG Apps Store listing number **1231221** is associated with [Smarters Player](https://us.lgappstv.com/main/tvapp/detail?appId=1231221). It is not a confirmed system launcher ID. Trial as candidate only.
- LG's [applicationManager](https://webostv.developer.lge.com/develop/references/application-manager) needs an internal app ID to launch a program. The [LG developer forum](https://forum.webostv.developer.lge.com/t/how-to-get-applist/8616) confirms that ordinary third-party TV apps cannot freely enumerate installed applications.
- Force the Smarters tile to remain visible. An unconfirmed tile is marked 'sprawdź'; first successful webOS launch is cached, negative error codes are stored on the TV under `vodNativeDiagnostics122` (no keys or playlists included).
- Stremio native deep-link handling on LG is not established. Provide a separate browser-based alternative to the title in the official Stremio Web SPA. Browser navigation and content playback depend on login/TV support.
- No unrestricted root/control APIs, third-party tampering, illegal content provision or streaming-account scraping.

## Authoritative 2026-10-24 runtime observation (v1.2.4)
Source: an authorized LG OLED55G42LW returned 67 `launchPoints` over WebSocket `ssap://com.webos.applicationManager/listLaunchPoints` using klattimer/LGWebOSRemote.
- Requested application `IPTVSmartersPlayer`: exact internal ID **`com.smarterstvplayers.net`**
- Different product `IPTVSmartersPro`: `com.iptvsmarters.app` (must NOT launch for this request)
- `Stremio`: `io.strem.tv`
- `DC4I VOD TV`: `com.dc4i.vodtv`
The store catalog ID `1231221` is not the launch ID. Only the observed native ID is used in current app code. The full, sensitive device inventory (67 apps) and paired client key are saved locally under AI-Hot `private/lgremote-output/` and `private/lgremote-config/`, never in Git.
LGWebOSRemote is a Python CLI for a computer, NOT a webOS Homebrew Channel IPK. Upstream MIT license: https://github.com/klattimer/LGWebOSRemote/blob/master/LICENSE
