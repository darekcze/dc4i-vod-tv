# DC4I VODTV 1.2.19: TV-first Channel Guide

**Status:** user opted for sequential whole-release execution. This branch does not publish until v1.2.18 is verified and integrated.
**Baseline:** v1.2.17 on LG, existing Xtream account and TMDB ID mapper, per-profile store.

## Intent
IPTV must look and work like a TV guide: real groups, channels with provider logos, current/next broadcast details, time bar, favorites, remote focus, stream playback and safe return. Top menu remains VOD | TV | IPTV | Filmy | Seriale | Szukaj | Aplikacje. Existing TV tab remains native live TV; IPTV tab opens new group/channel guide.

## Approaches
1. Patch generic Xtream grid: faster but cannot provide group/channel/details panes, rejected.
2. Dedicated TV guide overlay, reusing Xtream catalog/API and player: SELECTED. No Mac Pro, credentials stay on LG; remote-first and regressions isolated.
3. Replace player/stream backend entirely: higher risk with webOS codecs and provider, defer.

## Functional contract
- Three columns: provider group sidebar, channel list with actual logos and favorite status, selected broadcast details with Now/Next progress and Watch.
- Include All channels and Favorites filters; provider groups keep their actual category IDs and labels. Unknown logo gets neutral fallback icon.
- Fetch EPG only for focused or visible channels using the user's private Xtream player_api with strict single-flight request queue, timeout and 5-minute cache. No bulk fetch across 20k channels.
- EPG absent => say program data unavailable, not fabricate film/rating. Future/past events are metadata, not guaranteed CatchUp.
- Select channel => focus EPG/details; Watch => existing Xtream player. Back to guide restores channel focus; favorites per TV profile.
- Preserve existing Filmy/Seriale catalogue, account data and app ID. Make no unverifiable Polish audio/subtitles or rating claims.
- Remote UI tested at 1920x1080. CH+/- keys may be intercepted by LG, D-pad and Page Up/Down are mandatory.

## Later versions
v1.2.20: normalized epg.ovh + Xtream channel mapping and TMDB enrichment, rights/CORS gate.
v1.2.21: Home TV/VOD/genre rows. v1.2.22 CatchUp/timeshift, v1.2.23 DVR, v1.2.24 reminders, v1.2.25 charts, v1.2.26 deep taste, v1.2.27 reliability.

## Acceptance
Unit tests on grouping, progress, Now/Next, stale fetch, missing channels/logos, favorites. Chromium keyboard tests and screenshots. Live LG install with unchanged app ID, preserved Xtream accounts, 33 Homebrew entries and hash verification. No public private credentials.
