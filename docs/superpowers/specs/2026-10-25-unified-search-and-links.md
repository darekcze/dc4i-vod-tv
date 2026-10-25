# DC4I VODTV: unified title search and direct links, 25 Oct 2026

## Goal
TV users should always see selected, verified VOD subscriptions separately from voluntary searches in YouTube, Kodi, Plex, Stremio and Smarters Player. Use the same five actions and names in Search and movie/TV details. Preserve owner-approved branding and personal dedication.

## Chosen approach (incremental)
A shared view module renders exactly five focusable TV remote controls and dispatches each through the already existing integration: YouTube native search, Kodi TMDB handoff (or title search when no identifier), Plex Web search, Stremio app search/detail link and IPTVSmartersPlayer title hint. Context labels say 'Szukaj w:' rather than falsely implying all five are certified streaming sources. This avoids inventing discovery APIs for Plex/Smarters. Details VOD buttons still depend exclusively on TMDB providers configured for the user's region and selected service preferences.

## UX
1. Search: display available VOD title cards and provider labels, or exactly `Brak w wybranych serwisach` when no selected service provides streaming. Place `Szukaj w:` and the five focusable controls below results. Empty title queries cannot be sent blindly; message explains that input is required.
2. Details: only known selected-country and selected-service VOD buttons appear at the top. If none: `Brak w wybranych serwisach`. Below, a distinct `Szukaj w:` toolbar with same five actions; retain trailer and watchlist.
3. Links in quick settings: repo `https://lg.darc.dev/browse/`, website and clickable logo `https://www.dc4i.com/labs`.
4. EN/PL labels and nonempty terms preserved. Avoid asserting playback for native apps without documented deep links.

## Acceptance
Versioned IPK and public Homebrew manifest consistent. Tests for identical five labels/actions in both contexts, empty provider result, available VOD badges, links and TV remote navigation. Keep 32 unrelated apps and Kodi config. LG install and smoke verification.
