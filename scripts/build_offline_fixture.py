#!/usr/bin/env python3
"""Build a disposable, credential-free regression fixture, never a release.

Production builders remain unchanged. Inputs must be inspected local Git clones
of the repositories already named by build_dc4i.py/PROJECT.md. No network, keys,
IPK packaging or publishing is performed by this helper.
"""
import argparse
import io
import json
import secrets
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
window.KEYS = {TMDB_KEY: '', YT_KEY: ''};
window.fetch = function () { return Promise.reject(Error('Offline fixture: network disabled')); };
if (window.XMLHttpRequest) window.XMLHttpRequest.prototype.open = function () {
  throw Error('Offline fixture: network disabled');
};
if (typeof PalmSystem !== 'undefined') throw Error('Offline fixture cannot run on webOS');
"""

# The CSP blocks original parser-inserted application scripts. Only this nonce-
# authorized loader may start them, and only on a loopback HTTP browser origin.
# fetch/XHR stubs alone are not total network isolation; CSP adds resource limits.
BOOTSTRAP = """(function(){
var nonce=document.currentScript.nonce;
window.fetch=function(){return Promise.reject(Error('Offline fixture: network disabled'));};
if(window.XMLHttpRequest)window.XMLHttpRequest.prototype.open=function(){throw Error('Offline fixture: network disabled');};
document.addEventListener('DOMContentLoaded',function(){
 var loc=window.location;
 if('PalmSystem' in window || loc.protocol!=='http:' ||
    ['localhost','127.0.0.1','[::1]'].indexOf(loc.hostname)<0){
   document.body.textContent='Offline fixture refused: loopback browser only.';return;
 }
 var scripts=Array.prototype.slice.call(document.querySelectorAll('script[src]'));
 scripts.reduce(function(previous,original){return previous.then(function(){
   return new Promise(function(resolve,reject){var script=document.createElement('script');
     script.nonce=nonce;script.src=original.getAttribute('src');
     script.onload=resolve;script.onerror=reject;document.head.appendChild(script);
   });
 });},Promise.resolve()).catch(function(){document.body.textContent='Offline fixture script load failed.';});
});
})();"""

def archive(repo, revision, destination):
    data = subprocess.check_output(['git', '-C', str(repo), 'archive', revision])
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        # Never accept credential/configuration or device-specific files.
        assert not any(Path(m.name).name == 'keys.js' for m in tar.getmembers())
        tar.extractall(destination, filter='data')

def snapshot_project(root, output):
    sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']))
    archive(root, sha, output)
    return {'projectCommit': sha, 'workingTreeDirty': dirty, 'inputPolicy': 'committed-tree-only'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream-repo', type=Path, required=True)
    parser.add_argument('--brand-repo', type=Path, required=True)
    parser.add_argument('--output-parent', type=Path, required=True)
    args = parser.parse_args()
    # A new directory every run; never overwrite an existing build or user state.
    output = Path(tempfile.mkdtemp(prefix='vod-OFFLINE-DO-NOT-PUBLISH-', dir=args.output_parent))
    provenance = snapshot_project(ROOT, output)
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
    metadata = json.loads((app / 'appinfo.json').read_text())
    metadata.update(id='com.dc4i.vodtv.offlinefixture', title='DC4I VOD TV OFFLINE FIXTURE')
    (app / 'appinfo.json').write_text(json.dumps(metadata, indent=2) + '\n')
    nonce = secrets.token_hex(16)
    policy = ("default-src 'none'; script-src 'nonce-" + nonce + "'; "
              "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
              "connect-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'")
    index = app / 'index.html'
    html = index.read_text()
    assert html.count('<head>') == 1
    html = html.replace('<head>', '<head><meta http-equiv="Content-Security-Policy" content="' + policy + '">'
                        + '<script nonce="' + nonce + '">' + BOOTSTRAP + '</script>', 1)
    index.write_text(html)
    print('OFFLINE_FIXTURE_ROOT', output)
    (args.output_parent / 'vod-offline-latest.json').write_text(json.dumps({
        'root': str(output), 'upstream': UPSTREAM, 'brand': BRAND,
        'production': False, 'credentials': False, **provenance}, indent=2) + '\n')
    (output / 'fixture-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')

if __name__ == '__main__':
    main()
