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
