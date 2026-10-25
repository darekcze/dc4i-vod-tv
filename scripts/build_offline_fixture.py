#!/usr/bin/env python3
"""Build a disposable, credential-free regression fixture, never a release.

Production builders remain unchanged. Inputs must be inspected local Git clones
of the repositories already named by build_dc4i.py/PROJECT.md. No network, keys,
IPK packaging or publishing is performed by this helper.
"""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

UPSTREAM = '8cdea8940355685a82aac127fcdcf113a30684f6'
BRAND = '883e38088ace6257d06999d71d22c95c1ce71516'
ROOT = Path(__file__).resolve().parents[1]
EMPTY_KEYS = """// OFFLINE REGRESSION FIXTURE ONLY. NO CREDENTIALS. DO NOT PACKAGE.
if (typeof PalmSystem !== 'undefined') throw Error('Offline fixture cannot run on webOS');
window.KEYS = {TMDB_KEY: '', YT_KEY: ''};
window.fetch = function () { return Promise.reject(Error('Offline fixture: network disabled')); };
if (window.XMLHttpRequest) window.XMLHttpRequest.prototype.open = function () {
  throw Error('Offline fixture: network disabled');
};
"""

def archive(repo, revision, destination):
    data = subprocess.check_output(['git', '-C', str(repo), 'archive', revision])
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        # Never accept credential/configuration or device-specific files.
        assert not any(Path(m.name).name == 'keys.js' for m in tar.getmembers())
        tar.extractall(destination, filter='data')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-repo', type=Path, required=True)
    parser.add_argument('--brand-repo', type=Path, required=True)
    parser.add_argument('--output-parent', type=Path, required=True)
    args = parser.parse_args()
    # A new directory every run; never overwrite an existing build or user state.
    output = Path(tempfile.mkdtemp(prefix='vod-OFFLINE-DO-NOT-PUBLISH-', dir=args.output_parent))
    archive(ROOT, 'HEAD', output)
    for name in ['browser_path.mjs', 'e2e_vod_tv.mjs', 'e2e_xtream_v1214.mjs',
                 'e2e_xtream_v1215.mjs', 'e2e_guide.mjs',
                 'test_personalization_browser.mjs', 'test_panel_layout.py']:
        shutil.copy2(ROOT / 'scripts' / name, output / 'scripts' / name)
    marker = output / 'OFFLINE_FIXTURE_ONLY.txt'
    marker.write_text('Credential-free local regression fixture. NOT a production build.\n'
                      'DO NOT package, publish, deploy or install. Upstream redistribution license unverified.\n')
    upstream = output / 'build/theboringtv'
    upstream.mkdir(parents=True)
    archive(args.upstream_repo, UPSTREAM, upstream)
    (upstream / 'keys.js').write_text(EMPTY_KEYS)
    brand = output / 'branding/dc4i-transparent.png'
    brand.parent.mkdir()
    brand.write_bytes(subprocess.check_output(['git', '-C', str(args.brand_repo),
                     'show', BRAND + ':public/brand/dc4i-transparent.png']))
    builder = output / 'build_dc4i.py'
    code = builder.read_text()
    guard = "assert keys.exists() and re.search(r'[a-f0-9]{32}', keys.read_text(), re.I), 'TMDB key missing'"
    assert code.count(guard) == 1, 'Production build guard changed: review required'
    # Only the disposable fixture copy uses this explicit empty-key gate.
    code = code.replace(guard, "assert (ROOT/'OFFLINE_FIXTURE_ONLY.txt').is_file()\n"
                        + 'assert keys.read_text() == ' + repr(EMPTY_KEYS))
    code = code.replace("print('TMDB_PRESENT',True, 'YOUTUBE_OPTIONAL', True)",
                        "print('OFFLINE_FIXTURE_NO_TMDB_CREDENTIAL_OR_API_CHECK')")
    builder.write_text(code)
    (output / 'private').mkdir()
    subprocess.run([sys.executable, str(output / 'build_vod_tv.py')], cwd=output, check=True)
    app = output / 'build/dc4i-vodtv'
    shutil.copy2(marker, app / marker.name)
    assert (app / 'keys.js').read_text() == EMPTY_KEYS
    # Keep regression metadata intact, but fail safely if someone loads it on TV.
    print('OFFLINE_FIXTURE_ROOT', output)
    (args.output_parent / 'vod-offline-latest.json').write_text(json.dumps({
        'root': str(output), 'upstream': UPSTREAM, 'brand': BRAND,
        'production': False, 'credentials': False}, indent=2) + '\n')

if __name__ == '__main__':
    main()
