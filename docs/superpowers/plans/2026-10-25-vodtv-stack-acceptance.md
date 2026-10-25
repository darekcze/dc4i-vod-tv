# Canonical #20–27 acceptance audit

This is an offline software audit of stacked draft PRs, NOT release completion.
Canonical roadmap is #17/#18–27 (per #28), not older parallel issues. Published
production remains1.2.19. No PR is merged or version bumped by this audit.

| Issue / draft PR | Implemented software and evidence | Explicitly not done / external gates |
|---|---|---|
| #20 / PR31 | Bounded synthetic XMLTV normalization/mapping/provenance/cache, rolling10-day timeline, guide/details labels and focus lifecycle; importer/model/generated Node+Python regressions | EPG.ovh public-cache redistribution rights, enabled real ingestion, real metadata accuracy, browser/device acceptance |
| #21 / PR32 | Profile Home rails, ordering/enabled settings, fresh/stale/empty states, live-data fallback on failed cache write, stable title/app focus; model/UI/generated tests | Rendered1920x1080, actual remote layout/performance and live-data QA |
| #22 / PR33 | Injected archive capability/transport contract, honest unverified state, bounds and lifecycle tests; existing live dispatch preserved | Actual provider archive media/seek/buffer verification; no archive flag treated as proof |
| #23 / PR34 | In-memory scheduler/quota/conflict/recovery/cancel and unavailable capability UI; individual/aggregate over-quota reconstruction tested | Real backend/storage selection, recording, restart persistence and playback acceptance; DVR remains unavailable |
| #24 / PR35 | Compatible foreground reminders, quiet/DST/profile/failure/expiry/cancel tests; strict generated reader and toast layering | Native background/system toast/wake, actual webOS visibility/focus behavior; browser/device acceptance |
| #25 / PR36 | Four exact official Netflix weekly outbound links, per-profile choice, launch feedback/focus, strict preferences; no feed | Redistribution-ready feed, integrated rankings, copied data/cache; real external browser launch/return |
| #26 / PR37 | Observed native progression with unique intervals, profile/session boundaries, legacy+custom Home affinity, runtime track policy; injected media/generated tests | Real media event timing/track support, strict audio filter/selection, dubbing proof, external-player watch reporting |
| #27 / current draft | Scoped metadata preference backup/preview/single-section import/undo; strict-reader audit, failed-write/corruption/profile tests and synthetic resource bounds | Full user-data backup, crash-persistent multi-key restore, actual migrations, TV quota/performance, overnight soak, browser/remote/release acceptance |

## Storage audit inventory

- homeRailsLayoutV1: strict read; malformed/type-invalid layout disables custom
  rails and prevents overwrite. First-use absent key defaults remain.
- homeRailsMetadataV1: bounded disposable cache; errors/malformed/expired data
  become missing. Live catalogue stays usable after failed persistence.
- recommendationOpensV1: strict read and size/type admission; opening a title
  preserves unreadable data. Explicit clear confirms write. Semantics remain opened.
- guideFavoritesV1 / guideSelectedGroupV1 / guideLastChannelV1: strict scoped
  reads on show; unreadable fields protected from writes; failures surfaced;
  favorite UI update waits for confirmed write. Account/provider state not exported.
- dc4iEpgRemindersV1 / dc4iReminderPrefsV1: existing strict adapter; legacy array
  preserved, confirmed mutations, foreground delivery, corrupt/read-failed pause.
- dc4iChartLinksV1: strict missing/corrupt distinction, unsupported/unreadable
  preferences cannot launch a fallback chart accidentally.
- playbackLearningV1: strict schema/size, separate per-profile records, confirmed
  writes, active clear/session/listener boundaries; no URL/account/title storage.
- settings: unreadable general settings cannot be overwritten by generic store;
  new learning/personalization fail closed. Legacy unrelated settings boot is not
  redesigned or fully schema-migrated. Corrupt recovery requires an authorized
  valid backup, not automatic deletion. No migration ledger or version change.
- Rich EPG/archive/DVR models use injected/in-memory boundaries, not newly
  provisioned storage services. Credentials/playlists remain existing user data.

## Reproducibility and rollback

Fixture builder archives clean committed HEAD; records project/upstream/brand
revisions, uses a distinct offline app ID and guarded empty config. Upstream
8cdea8940355685a82aac127fcdcf113a30684f6; brand
883e38088ace6257d06999d71d22c95c1ce71516. No production keys or fake key values.
Run all non-browser scripts/test_*.mjs, XMLTV/provenance/Kodi Python tests,
script test_offline_build.py against fixture, CLI ares-package --check, plus
Europe/Warsaw reminder suite. Exact head/counts are recorded in draft PR evidence.

Draft rollback: revert isolated feature/fix commit in a new reviewed revision;
do not reset/overwrite another worktree or main. Preference import Undo checks
same profile/unchanged value and is session-local; copied text is the durable
allowed-settings backup. Release rollback remains the existing verified matching
manifest/IPK Cloudflare deployment, preserving application ID and all user data.
No release rollback was executed or claimed tested here.

## Shared blockers and smallest next actions

1. Independent exact-head review and repair any findings; continue offline tests.
2. Environment maintainer must provision a trusted Chromium sandbox installation
   (current helper nobody:nogroup4755). Do not chown/chmod or bypass sandbox here.
   Then run actual1920x1080 browser/remote/textarea/focus and long-run synthetic QA.
3. Production packaging needs authorized existing private build config and source
   redistribution clearance. No private keys copied into this environment.
4. Real EPG/chart rights, archive/provider proof and authorized DVR backend remain
   separate gates. Unavailable capabilities stay unavailable meanwhile.
5. LG tests remain prohibited. Any later device acceptance requires explicit owner
   availability/authorization; ordinary TV browsing must not require a server.
6. No verified deploy credentials/runner; no paid Actions. Publication only after
   applicable requirements pass, with public catalog/IPK checks and rollback proof.
