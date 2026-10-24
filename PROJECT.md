# DC4I VOD TV | Project Charter

**Project ID:** dc4i-vod-tv
**Owner:** DC4I / Chairman
**Status:** Prototype release (TV hardware validation pending)
**Repo:** https://github.com/darekcze/dc4i-vod-tv
**Delivery:** https://lg.darc.dev/
**Canonical Notion record:** https://app.notion.com/p/403522ca403c812d9ffbf5a031d5e026
**Canonical brand standard:** DC4I-BRAND-001, https://app.notion.com/p/3fb522ca403c81199c9bff92c1e84098

## Purpose
An LG webOS television application to discover and evaluate films and series across multiple VOD providers. It displays TMDB-based recommendations and ratings, provider availability, details, trailers, watchlist and installed-app entry points. It should minimize steps on the TV.

## Identity
The display name is **DC4I VOD TV**. Since release **1.2.0**, the technical package ID is `com.dc4i.vodtv`. The former `com.dc4i.boringtv` is legacy (1.1.1 and earlier); uninstall it before installing the new ID. This breaking change was expressly approved by the Chairman.

## Engineering and operations
- Build/source and large temporary files live on Mac mini AI-Hot: `/Volumes/AI-Hot/Services/dc4i-vod-tv`.
- Homebrew catalog and binary delivered by Cloudflare Pages project `lg-webos-repo`, domain `lg.darc.dev`.
- Build inputs from upstream TheBoringTV at commit `8cdea8940355685a82aac127fcdcf113a30684f6`, then deterministic DC4I layers.
- Core assets and all project instructions are versioned in Git. Private keys and built archives are NOT committed.
- Canonical engineering docs in English, Polish full mirror in `docs/pl/`.

## Goals and WBS
- G-VOD-BUSINESS: Single TV-first VOD discovery experience with useful ratings, provider availability and deep links.
- G-VOD-TECH: Compatible webOS IPK and Homebrew manifest, PL/EN UI, visually approved brand, correct persistence, optional API integrations.
- G-VOD-OPS: Secure credential handling, reproducible build and rollback, zero impact on existing AIOS services.
- WBS-01 Brand + product rename (owner-approved).
- WBS-02 TV navigation/PL-EN language + location settings.
- WBS-03 TMDB/YouTube integration and secure backend.
- WBS-04 Deployment + integration/real-device QA.
- WBS-05 Documentation and AIOS registration.

## Scope boundaries
- No rooting or firmware modification; no replacing system Home on a non-rooted device.
- Root-only quick controls are hidden unless the authorized local service responds.
- YouTube Data API key is stored privately; no personal key is included in the public IPK until a server-side proxy or restrictions are verified.
- Old service deep-link limits remain. Actual TV installation and regional app IDs are unverified until tested on hardware.
- Upstream repo currently declares no repository-wide GitHub license. Confirm redistribution permission independently; preserve attribution.

## Work contract
Preserve Project `dc4i-vod-tv`, Goals, WBS, ChangeIDs and Tasks across Git/Notion/AIOS. Use existing AIOS dispatcher and Runtime-v3, do not create independent queues/runners. Public releases require tests and documented evidence.
