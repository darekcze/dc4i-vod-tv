# DC4I VODTV 1.2.19 Channel Guide Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:executing-plans or subagent-driven-development; RED/GREEN each task.

**Goal:** Grouped channel guide with logos, now/next, favorite and playback, fully verified on LG.
**Architecture:** Pure guide model + bounded Xtream EPG adapter + three-pane remote-compatible view; existing Xtream catalogue and player remain responsible for account credentials and media playback.
**Tech Stack:** webOS TV JavaScript, Node tests, Python release patches, Chromium E2E, Homebrew IPK, Git.
**Spec:** docs/superpowers/specs/2026-10-25-channel-guide-design.md

## Global Constraints
Keep com.dc4i.vodtv, per-profile data and no Mac Pro dependency. Release 1.2.19 only after 1.2.18. Do not claim all-channel EPG, confirmed subtitles/CatchUp/recording. Do not log credentials/stream URLs.

## Review Focus
- Duplicate or missing provider category IDs; no misassignment of channel to groups.
- Missing logo/EPG, invalid dates, stale async response from prior selection.
- Single-connection provider rate limit; queue API requests.
- Profile isolation for favorite and last channel; upgrade retains them.
- Play/back to guide focus and D-pad at 1920x1080.

### Task 1: Group and EPG model
**Files:** src/vod-guide-model.js; scripts/test_guide_model.mjs.
**Interfaces:** DC4IGuideModel.group(records,categories,favorites), nowNext(events,now), progress(event,now).
- [ ] Write failing unit tests for grouping/empty icon/priority/favorites/duration/clock.
- [ ] Run tests, expect FAIL.
- [ ] Implement pure model; rerun tests, expect PASS.
- [ ] Commit scoped files.

### Task 2: Private Xtream EPG bridge
**Files:** src/vod-xtream.js (interface), scripts/patch_v1219_guide.py, scripts/test_guide_epg.mjs.
**Interfaces:** TV.xtream.ensureCatalog(), TV.xtream.guideEpg(id), TV.xtream.openGuideChannel(channel).
- [ ] RED test: single-flight queue, cache TTL, empty/errors/no secrets.
- [ ] GREEN implement via existing account request and private catalogue, no new proxy or keys.
- [ ] Commit and verify.

### Task 3: Three-column guide
**Files:** src/vod-channel-guide.js, src/vod-channel-guide.css, scripts/test_guide_ui.mjs, scripts/e2e_guide.mjs, scripts/patch_v1219_guide.py.
**Interfaces:** TV.addView('guide'), TV.store('guideFavoritesV1'), top IPTV routes to guide.
- [ ] RED test: remote focus, groups logos, Now/Next, favorites, Watch, Back.
- [ ] GREEN implement view and test 1920x1080 screenshot, failure states.
- [ ] Commit with acceptance evidence.

### Task 4: Release and physical LG
**Files:** build_vod_tv.py, publish_vod_tv.py, test_vod_tv.py, scripts/repack_v126.py, EN/PL CHANGELOG, DELIVERY, manifests.
- [ ] After v1.2.18 merges, verify integration and version 1.2.19.
- [ ] RED version/payload tests, then GREEN build, Node E2E and IPK.
- [ ] Independent final review, GitHub #19, release notes and rollback.
- [ ] Cloudflare Pages manifest/IPK SHA, preserve other 32 apps, LG in-place install and actual guide QA.
- [ ] Push final release only after verification; report gaps honestly.
