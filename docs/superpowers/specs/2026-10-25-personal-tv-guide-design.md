# DC4I VOD TV Personal Guide, architecture and release series

Date: 2026-10-25. Status: user approved sequential full-release delivery. Existing v1.2.17 is the preserved baseline.

## Intent
Create a TV-first experience like TiViMate's channel browsing married to TMDB movie identities and Netflix-style personalized, explainable recommendations. Guide the viewer across live, upcoming and missed broadcasts, films and series, source apps and verified playable catch-up. Each version must ship independently with tests, release notes in EN/PL and LG installation.

## Approaches considered
1. TV-only monolith: simple and local, but large XMLTV downloads and large recommendation profiles risk webOS memory; EPG.ovh sends no browser CORS, and the TV may not expose a writable DVR location. Rejected.
2. Hybrid anonymous metadata feed plus TV-local credentials, preferences and playback (selected): cache non-sensitive EPG/ratings publicly by channel ID with TTL; preserve user-specific Xtream account, historical events and ranking state per profile on LG. A recording backend remains optional and separately authorized and verified.
3. Always-on private Mac Pro proxy: rejected because the TV must work with Mac Pro powered off.

## Navigation and screens
Keep menu: VOD | TV | IPTV | Filmy | Seriale | Szukaj | Aplikacje.
- TV/IPTV: channel groups, logo rows, EPG grid current/next and times, favorites, CH up/down, program recommendations, past/future EPG and player actions. Use verified channel identity and do not invent logos.
- Filmy/Seriale: grouped Xtream poster grid, ratings with attribution, metadata linked to TMDB, verified language/subtitles and original provider categories. Seasons/episodes remain navigable.
- Home: selected and reorderable now live, today, next week, missed today/week, favorites, films, series, Sci-Fi, Reality, Family, provider charts and continuing items; rankings by score and engagement, not random.
- Details: one canonical TMDB title, actual source badges, TV airing timeline, verified archive playback status, streaming service deep links when supported.

## Ranking, privacy and profiles
- Each existing profile gets isolated settings and action history. A click or opening a title is NOT proof of a completed watch. Do not invent Netflix history; mark such titles merely opened.
- Deterministic score 0-100: TMDB verified rating, genre affinity, number of votes/reliability, temporal (evening) preferences, popularity, local app actions. Capture explanation for each score.
- Strict rules: default Sci-Fi min 6.0/10, Horror min 9.0/10; hide horror overrides all rules; Romance/Family may receive evening bonus. All adjustable in Settings. Unrated titles cannot pose as 9/10.
- Region and production language are not proof of audio, dubbing or Polish subtitles. [PL] Xtream is a provider marker, not verified audio/subtitles; later versions must distinguish unknown track flags.
- Retain app ID com.dc4i.vodtv, current per-profile TV.store and playlist IndexedDB keys, no manual uninstall. Limit retained events, enable clearing and opt-out. Do not transmit passwords, usage history or user preferences to public cache.

## Sources and technical verification
- Xtream player_api.php for authorized channel/group/VOD data and private program lists.
- TMDB official discover and detail endpoints for identities, genre IDs, vote scores and source metadata.
- EPG.ovh: plar has past five + upcoming five days and pltv offers metadata such as year, genre and rating (some ratings inside program description, not XMLTV rating element). EPG.ovh lacks CORS for webOS app origins. Use only neutral public channel metadata cache with bounded expiry, never forward credentials.
- CatchUp: test actual archive URL, media type, codec, data and authorized recording rights. Timeshift needs controlled buffer and free-space thresholds.
- DVR: no unverified native LG system recording or proxy. Optional recording backend only after real output verified, quotas/retention/conflict controls and no private Mac dependency to browse.
- Notifications: foreground alerts initially, native scheduled background notifications only if verified with webOS on this LG.
- External Top 10: exact official or licensed chart only; TMDB popularity is separately labeled, never misrepresented as Netflix/Disney actual Top 10.

## Release sequence
| Version | Deliverable | Acceptance |
| --- | --- | --- |
| 1.2.18 | Profile preferences and deterministic recommendations | User-editable weights/rating thresholds/horror/time/history, explainable Home row, per-profile isolation, end-to-end LG release |
| 1.2.19 | TiViMate-like channel guide | Category sidebar, channel logos, now/next, favorite/switch action, remote tests |
| 1.2.20 | Rich EPG and sources | EPG.ovh channel mapping, metadata provenance, 10-day timeline, audio/subtitle confidence rules |
| 1.2.21 | Recommendation-led Home | Now, upcoming day/week, missed today/week, favorite genres, reorderable rows, cache and explainable list |
| 1.2.22 | CatchUp and Timeshift | Verified archive replay, pause/seek when supported, explicit failure and memory controls |
| 1.2.23 | DVR and schedules | Tested optional storage/recording service, quotas, conflicts, history and successful playback |
| 1.2.24 | Notifications | Reminders, app background feasibility, per-profile notification/quiet hours |
| 1.2.25 | External charts | Configured verified sources Top 10, platform rankings separated from TMDB popularity |
| 1.2.26 | Deeper learning and locales | Playback-derived taste model, time/day, language/audio/subtitle filtering only when verified |
| 1.2.27 | Stability and backup | Cold starts, E2E load testing, export/import, error/rollback, release readiness |

## Release 1.2.18 scope and definition of done
First complete deliverable: a real personalized Home row using current TMDB movies/series returned by the already configured source. Show a 0-100 match score and reason, never an invented film rating. Settings include recommendation on/off, favorite genre, minimum Sci-Fi/other/horror rating, horror hide/high-score, evening Family/Romance boost, local history learning and hide-opened behavior. Keep user language preference setting distinct from any unverified dubbed/subtitle track. Existing profiles isolate preferences. Source events distinguish opened vs watched. Release with Node and Chromium E2E, IPK + SHA, lg.darc.dev and in-place LG update, GitHub issue & EN/PL notes, rollback. No EPG cache or DVR changes in v1.2.18.
