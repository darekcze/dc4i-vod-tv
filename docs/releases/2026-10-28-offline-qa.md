# DC4I VOD TV: repeatable full-stack offline QA (2026-10-28)

Parent issue: #17. Application source: daea1ea0c50bca415e2e738df08ee2f491698f98, from stacked PR #43. This QA runner adds no product source changes.

## Verified observations

- Initial run against a fresh worktree: 39 PASS, 17 FAIL. Every failure was caused by absent generated build/dc4i-vodtv files, not by a demonstrated application defect.
- Restored the existing provenance-pinned, synthetic, no-secrets fixture: **56 PASS, 0 FAIL**.
- Coverage: 50 Node.js suites, XMLTV, provenance, Kodi, release tooling, offline build verification, Warsaw reminder time-zone.
- Private machine-readable evidence: Services/QA-Workspaces/vodtv-audit-20261028-complete.json on Mac mini AI-Hot.
- No real credentials, LG device, provider API calls, install, distribution, or Cloudflare publish.

## Repeatable command

Requires the existing marked offline fixture with OFFLINE_FIXTURE_ONLY.txt, fixture-provenance.json and build/dc4i-vodtv/appinfo.json using identity com.dc4i.vodtv.offlinefixture.

    python3 scripts/test_fullstack_offline_qa.py
    python3 scripts/run_fullstack_offline_qa.py \
      --fixture /Volumes/AI-Hot/Services/QA-Workspaces/DC4I-VOD-FIXTURES-20261026/vod-OFFLINE-DO-NOT-PUBLISH-0a21vtw5 \
      --scratch-root /Volumes/AI-Hot/Services/QA-Workspaces \
      --receipt /Volumes/AI-Hot/Services/QA-Workspaces/vodtv-offline-qa-next-unique-run.json

Use a new receipt filename each time. The runner fails closed if provenance is wrong, the fixture is not synthetic, or the receipt already exists. It copies only non-private sources to disposable scratch, replaces only the fixture build, runs the pinned 56 checks and deletes scratch. Receipts contain statuses, timings and output digests, not full output.

Regenerate the fixture if application files change.

## Still blocked for commercial/release acceptance

- #4: upstream TheBoringTV redistribution/commercial rights are unverified (no repository-wide LICENSE found).
- #29: owner previously explicitly deferred physical LG tests. Offline QA is not live TV acceptance.
- Production credential-distribution architecture, real version stamping, IPK integrity, in-place data preservation and provider playback require their own review.
- Hosted CI is not established. 56/56 local PASS is not release approval.

Polish translation: docs/pl/releases/2026-10-28-offline-qa.md.
