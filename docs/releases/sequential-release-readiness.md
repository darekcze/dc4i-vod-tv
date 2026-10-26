# Sequential release plan — no publication

First minimal candidate source: PR31 plus PR40 (e832b39), with reviewed release
tooling55d4490/daea1ea cherry-picked on codex/v1220-release-preparation. This avoids
shipping later-version features while claiming sequential version acceptance.
No actual production package/version selected or stamped yet; metadata remains1.2.19
until separately checked release-version update. Accepted full-stack UI b8a4c08
is untouched, and its browser result is not automatically coverage for this subset.

| Version | Proposed release notes / readiness | Genuine remaining gap |
|---|---|---|
|1.2.20|Rich guide timeline, XMLTV provenance/cache model; empty periods fall back to already-fetched bounded Xtream EPG. Source/Node tests exist; full-stack browser guide PASS.|Subset regression/build and final metadata1.2.20; credentials policy; source rights; public EPG.ovh ingestion/cache stays off|
|1.2.21|Home rails, profile order/enabled controls, stale/empty handling and stable remote focus. Full-stack Node/browser PASS.|Build sequentially on accepted .20; live recommendation quality/LG performance not proven|
|1.2.22|Honest archive capability states and injected seek/buffer/transport contract.|Real provider archive playback/seek/buffer unverified; cannot release as working CatchUp/timeshift|
|1.2.23|Scheduler/quota/conflict/recovery model and unavailable DVR notice.|No real recording backend/storage/restart/playable recording; not a usable DVR release|
|1.2.24|Per-profile in-app foreground reminders, quiet hours, DST/cancel/expiry/failure handling. Node/browser synthetic PASS.|No native background/system toast/wake; actual device behavior is local-task responsibility|
|1.2.25|Official Netflix weekly chart links with region/category selection, separate TMDB estimates. Browser desktop behavior PASS.|Links are not feeds/rankings; rights/feed access and actual webOS launch remain unverified|
|1.2.26|Observed native progression model, profile/privacy/seek boundaries, unknown track policy. Synthetic browser/Node PASS.|Real playback/track evidence and strict dubbed/subtitle filter not complete; original language is not proof|
|1.2.27|Scoped metadata export/import, preview/remote scroll, journal recovery, supported-schema fixtures and storage/resource hardening.26 browser checks PASS on b8a4c08.|Actual production migrations/long-run limits not proven; no credential/account backup or globally atomic cross-context storage|

All notes describe implemented scopes, not eight published releases. Do not bump
.22/.23 to imply archives/recording work; use explicitly unavailable capability
or defer those versions until real acceptance. Root chooses honest sequencing.

TMDB omission investigation: build_dc4i.py requires32-hex keys.js and copies it
into output. Generated config.js reads TMDB_KEY only from window.KEYS. Generated
app.js tmdb() builds api_key=C.TMDB_KEY; loadHome stops with missing-key boot
message. No supported per-profile/localStorage TMDB configuration found. Therefore
removing the embedded key is not regression-free and retaining user playlists does
not supply TMDB. Offline fixture is not a production substitute. No new proxy,
credentials acquisition or architectural change is proposed here.

Concrete next action: after informed credential-distribution decision, trusted local
release owner builds this minimal source in an isolated checkout, then makes a
reviewed consistent1.2.20 metadata/runtime-version update, runs scoped guide/build/
package checks, stages catalogue using reviewed isolated publisher and compares
32 unrelated entries plus all referenced asset bytes. Local task owns authorized
TV readiness/install tests. Root owns merge/publish; neither happened here.
