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
