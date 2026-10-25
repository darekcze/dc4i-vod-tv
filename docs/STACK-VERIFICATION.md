# Offline stack verification checklist

No merge/release, network/provider/device calls, installs or sandbox changes.
Run from a clean review checkout; do not reset or overwrite concurrent work.
Production stays1.2.19. Browser diagnosis belongs to the separate environment
investigation; these commands do not launch a browser or claim runtime acceptance.

## Reviewed stack checkpoints

| PR | Remote branch | Checkpoint SHA |
|---|---|---|
|30|codex/cloud-test-portability-20261025|3fa11660d5254fa9c52d7def901737948e85e300|
|31|codex/v1220-epg-offline|ac99d8f9065866975308aec118105daa7a4ba75f|
|32|codex/v1221-home-rails|d4adf8912542b723f1ae5436dbb6514558c46c45|
|33|codex/v1222-archive-capabilities|de59fc8c3fc4fd4231df73e379222748809832de|
|34|codex/v1223-dvr-contracts|8f9ddf9d220de3219c9851a5be13bc583c82e550|
|35|codex/v1224-foreground-reminders|f439b9fb0def0c7e2ad2da607b2084f06bc87415|
|36|codex/v1225-official-chart-links|7fb457321bed09639739af1f09d1404053256ddb|
|37|codex/v1226-playback-learning|a563922842471689f12f723dd6975e2153a3ccf2|
|38|codex/v1227-hardening|Current review HEAD: resolve with git rev-parse HEAD and compare fixture projectCommit; exact validated SHA is in PR38 evidence.|

A checkpoint is not proof that remote heads never changed. Read-only confirmation:

```sh
git status --short
git rev-parse HEAD
git ls-remote https://github.com/darekcze/dc4i-vod-tv.git 'refs/heads/codex/*'
```

## Reproduce the full safe suite

Prerequisites already provisioned: Python/Pillow, Node, pinned local upstream
checkout8cdea8940355685a82aac127fcdcf113a30684f6, brand checkout
883e38088ace6257d06999d71d22c95c1ce71516, webOS CLI3.2.6. No keys required.
Stop if missing; do not install or fetch credentials as part of this checklist.
Builder uses committed HEAD only; uncommitted changes are excluded.

```sh
CHECK_DIR="$(mktemp -d /workspace/scratch/vod-check-XXXXXX)"
python3 scripts/build_offline_fixture.py \
  --upstream-repo /workspace/scratch/vod-upstream-source \
  --brand-repo /workspace/scratch/vod-brand-source \
  --output-parent "$CHECK_DIR"
python3 - "$CHECK_DIR/vod-offline-latest.json" <<'PY'
import json, os, pathlib, subprocess, sys
manifest = pathlib.Path(sys.argv[1])
info = json.loads(manifest.read_text())
assert info['production'] is False and info['credentials'] is False
assert info['workingTreeDirty'] is False
assert info['projectCommit'] == subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], text=True).strip()
root = pathlib.Path(info['root'])
commands = [['node', str(p.relative_to(root))]
    for p in sorted((root/'scripts').glob('test_*.mjs')) if 'browser' not in p.name]
commands += [
    ['python3', 'scripts/test_xmltv_metadata.py'],
    ['python3', 'scripts/test_offline_provenance.py'],
    ['python3', '-m', 'unittest', 'discover', '-s', 'integrations/kodi/service.dc4i.handoff/tests'],
    ['python3', 'scripts/test_offline_build.py', str(root)],
    ['/workspace/scratch/vod-tools/node_modules/.bin/ares-package', '--check', str(root/'build/dc4i-vodtv')]]
results = []
for command in commands:
    run = subprocess.run(command, cwd=root, text=True, capture_output=True,
        env=dict(os.environ, APPDATA='/workspace/scratch/vod-cli-state'))
    results.append({'command':command, 'exit':run.returncode,
                    'stdout':run.stdout, 'stderr':run.stderr})
run = subprocess.run(['node','scripts/test_reminders.mjs'], cwd=root,
    text=True, capture_output=True, env=dict(os.environ, TZ='Europe/Warsaw'))
results.append({'command':['TZ=Europe/Warsaw','node','scripts/test_reminders.mjs'],
                'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
(manifest.parent/'results.json').write_text(json.dumps(results, indent=2))
failed = [r for r in results if r['exit']]
print(info['projectCommit'], len(results), 'commands;', len(failed), 'failed')
for result in failed:
    print(result['command'], result['stdout'], result['stderr'])
sys.exit(bool(failed))
PY
```

Expected current inventory:49 non-browser Node suites,14 Python cases,
generated structure/approved branding/42 JS syntax, CLI check, extra Warsaw run:
55 commands. Retain actual results.json and projectCommit, not just this count.
No IPK packaging/install/publish occurs. Fixture identity is explicitly offline;
never distribute fixture output as a production app.

## Final review gates

- [ ] PR38 sanitized value preview and storage/backup changes independently reviewed.
- [ ] Exact current head passes all commands above with clean provenance.
- [ ] Actual browser/remote/textarea/focus/reload and long-run tests after safe
  environment availability is established by the separate investigation.
- [ ] Applicable source rights/provider/archive/DVR/media/track gates resolved.
- [ ] Authorized production inputs, matching package/catalog checks and rollback
  evidence; TV acceptance remains prohibited until separately authorized.
- [ ] No claim of full#20–27 completion based on offline checks alone.
