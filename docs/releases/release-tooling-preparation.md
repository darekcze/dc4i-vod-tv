# Release tooling preparation (no release)

Based on browser-accepted UI revision b8a4c086ab6e098cdcebc41217bd575d755d7f28.
Separate report: actual Chrome156 QA26checks passed at1920x1080, disposable
profiles; preview y624–1056/height432, final scroll1746/1746; remote/PL/EN,
transaction/privacy/repeat/stale preview and Home/EPG smoke passed. No LG claim.
No UI/runtime code is changed by this tooling branch.

publish_vod_tv.py and test_vod_tv.py derive production ID/version from built
appinfo.json. Only com.dc4i.vodtv and numeric three-component versions are accepted;
fixture ID is rejected. Existing1.2.19 builds retain1.2.19 behavior. No new version
selected. Optional --release-version must equal built metadata, preventing drift.
This does not stamp new app/runtime versions: an eventual release version change
still needs its own reviewed consistent metadata/runtime-version change.

Safe staging command (after approved actual production inputs/package exist):
```
python3 publish_vod_tv.py --root /isolated/release-source --output-root /empty/sibling-stage --release-version X.Y.Z
python3 test_vod_tv.py --root /isolated/release-source --release-version X.Y.Z --offline
```
--app-dir can select built metadata explicitly. --root defaults to repository.
Without --output-root, publisher retains legacy source-root write behavior;
prefer isolated staging. Explicit output cannot equal/nest/contain source and
must be absent/empty. No deploy occurs. Isolated mode does not execute legacy
optional catalogue enrichment stages from the source tree;32 unrelated feed
entries are copied unchanged and tested semantically. Review enrichment needs
separately before any production release.

Smoke test --offline skips only the live TMDB request; normal structural/IPK/key
checks still apply. No real key was loaded for these tests. Network exception
logging now emits only exception class, never arbitrary message/query/header/body.
Synthetic sentinel tests cover API key/token/password/cookie/Authorization/userinfo.

Validation: python3 scripts/test_release_tooling.py (3 cases, including isolated
publisher subprocesses); py_compile shared helper/publisher/smoke. Synthetic
catalogue test uses obvious non-package bytes, never a candidate or fake key.
Preserves33 entries/32 unrelated, original source bytes unchanged, rejects
nonempty/source-root output, mismatched version, fixture identity and malformed
versions. Existing blocked production prerequisites/rights/secret-distribution
policy remain. No IPK, real API, merge, deployment or TV operation.

## Retained distribution assets repair

Isolated staging now preflights and copies trusted public packages/icons/browse/
manifests trees (existing dist preferred per tree, source tree fallback). Local
URLs in retained catalogue entries must resolve to those files or generated
routes; directory routes require index.html. Missing required assets fail closed
with an actionable local path, without fetching any URL. All source symlinks/
escaping paths are rejected; output stays contained. Source bytes are untouched.
Old packages are no longer pruned. Catalogue equality alone is not acceptance:
regressions assert package/icon/browse/CSS/old-package bytes, missing-reference
rejection before feed creation, escaping symlink rejection and33/32 preservation.
RED reproduced FileNotFoundError for the retained DStore package; GREEN full
3-case release-tooling suite and py_compile. No deploy/candidate or real key.
