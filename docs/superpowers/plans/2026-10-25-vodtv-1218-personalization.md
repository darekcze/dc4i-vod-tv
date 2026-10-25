# DC4I VODTV v1.2.18 Personalization Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: use Superpowers subagent-driven-development or executing-plans, TDD per task, and an independent review if available.

**Goal:** Deliver the first complete user-visible personalized recommendation feature on the owner's LG webOS VODTV without disturbing existing Xtream accounts.

**Architecture:** Pure, deterministic browser-compatible scoring engine receives existing TMDB home cards enriched with their genre and rating data. Settings use the existing profile-aware TV.store. A new home row uses the scores and recent in-app actions; all results are explicitly suggestions, never verified watched items.

**Tech Stack:** ES2018 webOS JS, Node assertions, Chromium CDP, Python patch chain and packaging, Git, Cloudflare Pages, LG ares CLI.

**Spec:** docs/superpowers/specs/2026-10-25-personal-tv-guide-design.md

## Global Constraints
- Preserve com.dc4i.vodtv and all current saved Xtream user data and approved branding.
- Use existing TMDB configuration and region, no new API key or paid feed.
- Version exactly 1.2.18, EN + PL Release Notes. No fabricated ratings or audio-track claims.
- Public Homebrew catalog retains other 32 apps unchanged. No Mac Pro dependency.
- Every test is RED before implementation and GREEN after. All base tests must pass.
- Private files, API keys, household history stay out of Git and Cloudflare public manifest.

## Review Focus
1. Profile switching and history/config isolation.
2. Missing rating or genre must not be assigned a fabricated rating.
3. Hide-horror is a hard rule even when title is 10/10.
4. Home and Settings remote navigation stay usable at 1920x1080 and on cold start.
5. In-place update preserves Xtream account keys; no clearing data or uninstall.

### Task 1: Pure scoring and history
**Files:** create src/vod-recommendations.js, scripts/test_recommender.mjs.
**Interfaces:** window.DC4IRecommender.defaults, .score(item,settings,history,now), .rank(candidates,settings,history,now), .record(history,item,action,now).
- [ ] RED: Node test Sci-Fi >=6, horror >=9, hide horror, 18:00-23:00 romance/family boost, unknown scores, history, genre preference, deterministic sorting. Expected feature missing.
- [ ] GREEN: minimal pure implementation, run test and unrelated baseline. Score always 0-100 with reason; opened not watched.
- [ ] Commit on isolated branch.

### Task 2: Home data, settings and first recommendation row
**Files:** scripts/patch_v1218_personalization.py, build_vod_tv.py, scripts/test_personalization_integration.mjs, generated files under ignored build/.
**Interfaces:** TV.homeCandidates() returns existing genuine TMDB-backed hero/base titles, TV.addSetting controls per profile, TV.addRow provider shows scored nonempty row. Profile-aware TV.store('recommendationOpensV1') keeps at most 150 events.
- [ ] RED: integration test checks 1.2.18 patch, on-screen settings and matching row; initially fails on v1.2.17.
- [ ] GREEN: expose vote_average, vote_count, genre_ids, popularity and id, track in-app title opens separately from watched, add settings: recommendation on/off, favorite genre, Sci-Fi minimum, horror minimum and hide, other minimum, evening bonus, local learning and hide-opened.
- [ ] Re-run full Node suite plus build. Commit.

### Task 3: LG 1920x1080 E2E
**Files:** scripts/test_personalization_browser.mjs (and supporting smoke script).
**Interfaces:** visible personalized row with real TMDB fixture IDs and scores, persisted per profile.
- [ ] RED: browser checks seeded Sci-Fi/Horror/Family fixtures and saves settings in a default profile. Missing row/settings fails.
- [ ] GREEN: remote navigation, home row reason, cold-start cache, user settings persist and are not shared across profiles, no blank cards.
- [ ] Full existing E2E and home panel geometry regressions. Commit.

### Task 4: Release and physical LG acceptance
**Files:** publish_vod_tv.py, scripts/repack_v126.py, test_vod_tv.py, CHANGELOG.md, docs/pl/CHANGELOG.md, DELIVERY.md, README.md and manifests.
- [ ] RED: version packaging check expects 1.2.18, old version fails.
- [ ] GREEN: source build+IPK repack+manifest QA, no private credentials in public Git/asset, 33 app catalog (32 unchanged).
- [ ] Deploy lg.darc.dev via existing Cloudflare Pages project; HEAD/GET endpoints 200, SHA-256 matches.
- [ ] Use existing LG ares-install in place, ares-launch, verify physical appinfo 1.2.18 and new recommendation JS, report any hardware gaps truthfully.
- [ ] EN and PL release notes, Git commit + push and issue update, public release trace and rollback.
