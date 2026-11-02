# LG TV menu evidence method

[Polski](pl/LG-TV-EVIDENCE-METHOD.md) | [Executable capture runbook](LG-TV-CAPTURE.md)

## What this evidence establishes

On 2026-10-28 an existing paired SSAP connection to a physical LG OLED55G42LW produced a menu screenshot through `ssap://tv/executeOneShot`. The observed image was JPEG, 960 × 540 pixels. The television's installed-application inventory was also read and the 19 requested native application IDs below were resolved. These observations establish that the capture route and these IDs were available on that device at that time. They do not establish complete menu coverage, deep-link support, playback support, or the safety of replaying a remembered button sequence.

The original images, inventory, timestamps and capture receipts are private project evidence. This public document records the method and nonsecret app mapping. It intentionally makes no final claim about the number of verified menus in the ongoing audit. The public client and observed-plan runner have passed a dated physical-TV navigation/capture check, and same-URI HTTP retry recovery was observed. The owned-session wrapper and repeat launcher remain **NOT VERIFIED ON HARDWARE**. See the capture runbook for the exact scope and limits.

## Observed native identifiers

Recheck the current TV inventory before launch. Human names can change, and an installed ID is not a cross-device guarantee. The versioned [target registry](../scripts/lg-tv/targets.json) uses the same slugs as the capture records.

| Slug | Observed name | Native ID |
| --- | --- | --- |
| `disneyplus` | Disney+ | `com.disney.disneyplus-prod` |
| `netflix` | Netflix | `netflix` |
| `hbomax` | HBO Max | `com.wbd.stream` |
| `appletv` | Apple TV | `com.apple.appletv` |
| `player` | Player | `com.accedo.videa.tvn` |
| `stremio` | Stremio | `io.strem.tv` |
| `iptvsmartersplayer` | IPTV Smarters Player | `com.smarterstvplayers.net` |
| `smartiptv` | Smart IPTV | `siptv` |
| `primevideo` | Prime Video | `amazon` |
| `youtube` | YouTube AdFree | `youtube.leanback.v4` |
| `viki` | Rakuten Viki | `com.viki.lg` |
| `pilot` | WP Pilot | `pl.wp.pilot` |
| `skyshowtime` | SkyShowtime | `com.skyshowtime.tv` |
| `canalplus` | CANAL+ | `canalplus` |
| `megogo` | MEGOGO | `megogo.hd` |
| `cda` | CDA | `pl.cda` |
| `sweettv` | SWEET.TV | `sweet.tv` |
| `rakutentv` | Rakuten TV | `ui30` |
| `lgchannels` | LG Channels | `com.webos.app.lgchannels` |

The observed YouTube title was **YouTube AdFree**. This records its displayed label and ID; it does not certify its publisher, official status, subscription behavior or playback features.

## Six views per requested app

| View | Evidence needed |
| --- | --- |
| `home` | Actual main landing or navigation page |
| `settings` | Visible app settings menu, with no setting changed |
| `details` | Details for one identified title, without starting playback or purchasing |
| `recommendations` | A recommendation page or an explicitly identifiable recommendation section |
| `profiles` | Profile selector or profile menu, without editing a profile |
| `search` | Search entry page or search interface |

A login gate, loading screen, error or system overlay is evidence of that state. It is not a substitute for the requested menu. If one screen visibly combines categories, explain the relationship and link the same evidence explicitly; never duplicate a file to imply more independent captures.

## Collection and review protocol

1. Read the current foreground and display state and create an owned session receipt before changing the TV.
2. Resolve the exact app ID from the live inventory. Launch only the requested app and inspect its entry image. Apps may restore an earlier page.
3. Choose short navigation steps from observed focus. The plan runner checks session identity and foreground before input. It splits batches after `HOME`, `BACK` or `ENTER` and checks again before later buttons. Those checks do not establish the meaning of an `ENTER` press.
4. Require `returnValue: true` and an image URI for a capture. Download only from the configured local TV host, validate redirects, enforce limits and check image signatures and dimensions.
5. Record requested view, actual app ID, display state, timezone-aware time, SHA-256, dimensions and navigation steps. Keep the original manifest append-only.
6. Inspect the actual image. Record `verified`, `incorrect` or `blocked` in the separate review log. A verified `verified_view` correction can assign the observed category while preserving the raw request.
7. Record inaccessible or unresolved views as `not-installed`, `login-required`, `not-available`, `not-observed` or `error`, with a concrete observation. An unsuccessful search for a menu is only `not-observed`.
8. Restore the original app and display intent in the owning controller's cleanup path. Record cleanup failure separately from capture success.

The initial route exposed a useful distinction: a correct foreground app ID could coexist with a screen-off or screen-saver overlay. Temporarily enabling the panel produced the app image, and the earlier display-off intent was then restored. Always verify pixels as well as foreground state. A black image alone does not identify DRM as the cause.

## What may be published

Keep credentials, private addresses, stable computer IDs, profile/account details, screenshots, original inventories, raw manifests, action/session logs and embedded-image atlases outside this public repository. The ignored `private/` directory can hold local working evidence; it is not a backup or an access-control mechanism.

Version the reusable code, these mirrored runbooks, nonsecret app IDs and appropriately sanitized findings. Report verified menu coverage only from reviewed evidence in a dated private report. Distinguish observation from a design recommendation for DC4I VOD TV.
