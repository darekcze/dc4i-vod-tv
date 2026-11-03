# Stack / PR40 integration checkpoint

Base: e307dbceddd9f5ca49a96a2bf87dec0e3461b1c1 (PR38).
PR40 source: e832b3908f018226b2ac6c69784dc3d112fabe6e.
Code revision tested: d2121f0f937658826ad85658f6610dfac35f3207.
The subsequent documentation commit changes no executable inputs.

Both PR40 commits cherry-picked without conflicts into an isolated branch.
Existing fetched provider EPG fills empty XMLTV timeline periods, with bounded
metadata-only rows and honest provenance/freshness. No additional network calls.

Actual verification: 56 commands passed, zero failures. 50 non-browser Node
suites; 14 Python cases (XMLTV7/provenance2/Kodi5); offline generated structure,
42 JS syntax checks, webOS CLI package check and Warsaw reminder run. Clean
committed-tree fixture built using existing pinned upstream/brand inputs;
no dependency installs or private configuration. Initial build attempt only
failed because output-parent directory was absent; creating it resolved that.

Main remotely verified: 6e4863a03a816f0f1614a0571b1aa48c33f245d9.
Production version remains1.2.19. Existing worktrees preserved.

Not run: actual browser, LG, live provider, production packaging/deployment.
Mac mini QA is paused/terminal:14 prior source tests, no fixture launch and no
pending automatic report. Cloud sandbox and denied official browser download
remain blocked; do not retry alternate downloads or bypass sandbox.

Permitted next QA route: existing authorized Mac mini Chrome, isolated checkout
of this integration branch; provide pinned brand source and existing webOS CLI,
build the offline fixture and execute1920x1080/remote/profile/import/privacy
checks against synthetic inputs. Preserve existing dirty worktrees. No LG access.

Browser QA reported preview clipped at1213px in1080px viewport. Fix: preview is
now the final focusable control, bounded to40vh with internal scrolling. OK enters
reading; Up/Down scroll to either end; Back exits reading, then closes normally.
Node regression failed before fix and passes after, including long PL/EN content.
Actual browser retest is still required; previous browser results do not validate
this revised layout. Transaction/preview-token logic is preserved.
