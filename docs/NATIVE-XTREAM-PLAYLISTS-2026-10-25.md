# DC4I VOD TV, Native Xtream Codes IPTV (LG webOS)

## Release
- Final build: `com.dc4i.vodtv` version **1.2.15** (25 October 2026).
- Source: `src/vod-xtream.js`, `src/vod-xtream.css`.
- Build chain: `python3 build_vod_tv.py`; `python3 scripts/repack_v1214_xtream.py`; `python3 scripts/repack_v1215_navigation.py`; `python3 test_vod_tv.py`.
- The IPK must **not** contain user Xtream server URL, username, or password. No Mac Pro/Mac mini service is used by the final app.

## User flow
1. Open the **IPTV** tab.
2. Choose **Dodaj playlistę**, enter label, Xtream provider base URL, username and password.
3. Select **Sprawdź połączenie** or **Zapisz**. The app calls the provider `player_api.php` directly.
4. Browse Live TV, channel groups, movies, series; search and filter by type and category.
5. Selecting a series retrieves `get_series_info` on demand and shows seasons/episodes. Selecting live TV, a movie or episode opens native HTML5 media playback.
6. Use Magic Remote pointer or D-pad and OK to focus input fields; Back returns from player to catalog.
7. Saved profiles live in the app's per-profile web storage, not in the IPK.

## Provider API and transport
- Direct Xtream `player_api.php` actions used: `get_live_categories`, `get_vod_categories`, `get_series_categories`, `get_live_streams`, `get_vod_streams`, `get_series`, and per-title `get_series_info`.
- Requests are made sequentially due to account's maximum of one concurrent connection.
- Supports provider stream URLs `/live/{user}/{password}/{id}.m3u8`, `/movie/.../{id}.{ext}`, `/series/.../{episode}.{ext}`.
- Provider currently exposes HTTP. The Xtream login/password are therefore unencrypted in transit. All personal credentials must remain private. Do not collect access details in public analytics or issue trackers.
- CORS checked against real provider using multiple Origins: HTTP 200 and compatible `Access-Control-Allow-Origin`.

## Real TV acceptance (OLED55G42LW, 192.168.1.60)
- 1.2.14 installed and launched via webOS CLI. Direct account configured using paired webOS DevTools without hardcoding secrets; index sync completed **145,699 records**.
- TVP Info HD native playback **1920x1080**, `readyState=4`, progressing playback, no decoder error.
- First matching Matrix film native playback **3840x2160**, `readyState=4`, progressing playback, no decoder error.
- Breaking Bad series query yielded 9 matching listings; first selection loaded **62 episodes**, and an episode played at **1280x720**, `readyState=4`.
- Temporary Mac Pro proof-of-concept server on port 18774 terminated. With this port closed, TV app reloaded, local account remained present and provider catalog resynced successfully with 145,699 records. Thus no Mac Pro proxy dependency.
- 1.2.15 adds verified D-pad focus and native input handling. Headless Chromium tests cover catalog sync, search, playback actions, storage across reload, and remote focus. Run physical-TV regression after installing 1.2.15.

## Important limits
- LG documentation says packaged-app web storage can be cleared in certain updates or after app removal/reset. This local-only solution cannot promise persistence across all firmware updates. See official webOS Developer FAQ on web storage.
- TV playback depends on provider source, codecs, account limits and content rights. Test examples do not validate every stream.
- `com.webos.service.unifiedsearch`/`search.json` on commercial webOS TV remains separately unverified. Do not claim global LG Search indexing.
- No root privileges are required.
- Apps/streams from user-provided providers are not redistributed by DC4I.

## Security and private configuration
The paired remote/config and personal Xtream credentials remain in `/Volumes/AI-Hot/Services/LGWebOSRemote/private/` on Mac Pro. The one-time provisioning script remains in `tools/xtream-lab` on Mac Pro, separate from this repository. Never commit, log, or publish these credentials.

## Regressions and QA
- `python3 test_vod_tv.py`
- `node scripts/e2e_vod_tv.mjs`
- `node scripts/e2e_xtream_v1215.mjs`
- `python3 scripts/test_catalog.py` after publishing combined catalog.
