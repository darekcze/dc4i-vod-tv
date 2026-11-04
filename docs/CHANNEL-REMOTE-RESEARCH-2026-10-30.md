# VODTV LG channel rocker integration and P0 release provenance
Date: 2026-10-30
Status: code candidate, NOT verified on physical LG; no TV install/production publish.

## Background and diagnosis
The 1.2.19 guide's PageUp/PageDown (33/34) implementation merely changed a page or moved focus, not the tuned IPTV stream. The player view did not dispatch CH+/CH-. Actual LG SSAP listApps on 2026-10-30 returned `com.dc4i.vodtv` **1.2.33**, whereas https://lg.darc.dev/manifests/dc4i-vodtv.manifest.json still declares **1.2.19**. GitHub main also identifies 1.2.19 as the last published release (later docs only). An installed version string alone does not identify the built source or IPK checksum. Do not install 1.2.19 over 1.2.33.

## Source repositories researched and adaptation
1. LG official Magic Remote documentation: https://webostv.developer.lge.com/develop/guides/magic-remote . Currently lists Channel +/- as **N/A for web apps**. Key events cannot be guaranteed on every firmware/model; any claim of physical CH support requires hardware test.
2. Apache-2.0: https://github.com/lennylxx/webos-iptv-player ; `src/navigation/key-handler.ts`, `src/config.ts`. Dedicated `channel_up` and `channel_down` actions, centralized key mapping, input-field bypass and per-view dispatch. Read and used as a behavioral reference, not pasted. If directly using any code, retain Apache-2.0 notices and applicable copyright.
3. https://github.com/sharktie/lg-iptv ; `js/core/dom.js`, `js/livetv/`. Includes PageUp/PageDown (33/34) aliases alongside 427/428, plus named `KeyboardEvent.key` aliases; the repository's `package.json` reports ISC license, but individual file headers and distribution permissions must be verified before directly copying more code. This patch independently implements a minimal event normalization rather than copying the source.
4. LG sample RemoteControl: https://github.com/webOS-TV-app-samples/RemoteControl demonstrates the proper `document.addEventListener('keydown', ...)` mechanism.

## Implemented in this branch
- Normalize 427/428, 33/34, key names ChannelUp/Down and PageUp/Down.
- Only intercept while IPTV guide is open or the Xtream player overlay is visible.
- For CH+: wrap forward to next channel in the selected guide group. For CH-: wrap backward. Preserve and update current selected channel, pagination and EPG selection. Start the stream through the existing `TV.xtream.guideWatch` path.
- Use capture phase and stop propagation only for handled channel events. No input-field interception, no global native TV channel changes, no playlist/account/password writes.
- Add deterministic no-TV tests, including empty list and wraparound.

## Remaining mandatory acceptance
1. Before any install, recover the exact 1.2.33 package or source revision, checksum and a restorable backup. Prefer read-only `ares-novacom`/SSH inspection of the installed app and package. Current Mac mini and Mac Pro package directories only contain releases through 1.2.19.
2. Rebase/merge this candidate with the source proven to be installed as 1.2.33, then create the next monotonically higher package version. Do not overwrite installed TV data or downgrade.
3. Test on the actual LG OLED55G42LW with a human physical CH+/CH- press while the app is foreground: log keyCode/key names without user content. An injected synthetic event or SSAP channel-up command is not proof that hardware delivers DOM keydown.
4. Check guide and player contexts, group wrap, favorites, provider stream playback, Back to guide, and selected/focused channel. If the OS reserves these buttons, provide D-pad fallback or another supported shortcut without claiming CH is fixed.
5. Diagnose TVP1/TVP2 EPG unavailable in the 2026-10-28 physical QA: distinguish missing Xtream provider data from channel-ID mapping, and add non-sensitive verified fallbacks (PR42 has offline provider-timeline fallback). Do not fabricate EPG or expose private Xtream credentials.
6. Run stack PR46's 56 offline checks, physical playback/EPG QA, public SHA-256 manifest/in-place install only after distribution rights review. GitHub issue #4 on the original TheBoringTV licensing remains open.

## Other proven improvement ideas to adapt next
- Per-view input action dispatcher, number-key direct channel selection, focus ownership between D-pad and Magic Remote, bounded diagnostics without IPTV secrets: `lennylxx/webos-iptv-player`.
- Channel order/hide/favorites and corrected EPG mappings, source time zones, local guide cache: both projects. Consider provider priority and verified provenance.
- Stream stall watchdog, reconnect with bounded retries, codec fallback and sound/subtitle diagnostics, local EPG provider testing: `lennylxx/webos-iptv-player`.
- Stream overlay and CSS fullscreen instead of Fullscreen API (hardware video-plane), source-aware engine selection: `sharktie/lg-iptv`. Test on OLED55G42LW, not just headless Chrome.
- Backup/export and in-place upgrade regression gate, release SHA-256, one artifact linked to source commit before public distribution.

No upstream source files or artwork were copied verbatim by this patch. Treat items above as implementation references with their respective licensing conditions.
