# 1.2.21 Home rails — first offline increment

Canonical issue #21 and approved personal-TV-guide design; stacked on #20.
Use executing-plans and test-driven-development. Existing autonomy authorizes
implementation and draft PR without another approval. No release or TV operations.

Architecture: pure row model wraps the existing deterministic recommendation
engine for canonical TMDB candidates. Airing rows are separately labeled metadata,
never playback promises. Calendar boundaries are local and DST-aware. A bounded
cache port is bound by the caller to existing per-profile TV.store; no global
profile key, credentials, URLs, histories or network calls enter cached metadata.

- [x] RED/GREEN configurable ordered/enabled sections, now/today/week/missed buckets,
  canonical film/series/genre ranking explanations and source attribution.
- [x] RED/GREEN cold-start TTL/cache whitelist, bounds and separate profile ports.
- [ ] EN/PL draft notes, focused regression, stacked draft PR for review.
- [ ] Next increment: actual Home rows/settings/remote integration using these
  contracts, with no unverified playback and no redesign.

Do not claim complete #21: real browser/performance QA, source coverage and release
acceptance remain open. Existing profiles/playlists/history and version1.2.19 stay.
