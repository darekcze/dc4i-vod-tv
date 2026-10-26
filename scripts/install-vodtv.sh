#!/bin/bash
# DC4I VOD TV: install a versioned IPK on LG OLED55G42LW.
# Automatic recovery from Always Ready, no app launch unless --launch is supplied.
set -Eeuo pipefail

ROOT='/Volumes/AI-Hot/Services/LGWebOSRemote'
NODE='/Users/czech/.nvm/versions/node/v20.19.4/bin/node'
LOCAL_CLI='/tmp/dc4i-ares-cli/node_modules/@webos-tools/cli/bin'
DEVICE='LG_OLED55G42LW'
APP='com.dc4i.vodtv'
PROBE="$ROOT/tools/lg_ssap_probe.py"
PACKAGE=''
DRY=0
LAUNCH=0
NO_WAKE=0
TMP=''

usage() {
 echo 'Usage: install-vodtv.sh --version 1.2.20 | --ipk /absolute/file.ipk [--dry-run] [--no-wake] [--launch]'
 echo 'Default: wake once if needed, wait briefly for readiness, install only, verify installed version.'
}
error() { echo "ERROR: $*" >&2; exit 1; }
while (($#)); do
 case "$1" in
  --version) (($#>1)) || error 'Missing version'; [[ "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || error 'Invalid version'; PACKAGE="$ROOT/packages/${APP}_${2}_all.ipk"; shift 2;;
  --ipk) (($#>1)) || error 'Missing IPK'; PACKAGE="$2"; shift 2;;
  --dry-run) DRY=1; shift;;
  --no-wake) NO_WAKE=1; shift;;
  --launch) LAUNCH=1; shift;;
  --help|-h) usage; exit 0;;
  *) error "Unknown option: $1";;
 esac
done
[[ "$PACKAGE" = /* && -f "$PACKAGE" ]] || { usage; error 'Specify an existing absolute IPK path'; }
[[ -x "$NODE" && -f "$PROBE" ]] || error 'Required Node runtime or LG probe missing'
[[ -d "$ROOT/.ares-home" ]] || error 'Private webOS device configuration missing'

cleanup() { [[ -z "$TMP" ]] || rm -rf "$TMP"; }
trap cleanup EXIT

# Explicit time bounds: terminate only our own process group if it hangs.
bounded() {
 local limit="$1"; shift
 /usr/bin/python3 - "$limit" "$@" <<'PY'
import os,signal,subprocess,sys
p=subprocess.Popen(sys.argv[2:],start_new_session=True)
try:
    result=p.wait(timeout=int(sys.argv[1]))
except subprocess.TimeoutExpired:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL)
        p.wait()
    print('ERROR: command timed out',file=sys.stderr)
    sys.exit(124)
sys.exit(result)
PY
}

# Read-only, pre-paired SSAP state query. WOL runs only when Active is not confirmed.
active() {
 local output
 output="$(bounded 6 /usr/bin/python3 "$PROBE" --action state --timeout 2 2>&1)" || return 1
 [[ "$output" == *'"state": "Active"'* ]]
}

if ((DRY)); then
 shasum -a 256 "$PACKAGE"
 echo 'DRY_RUN_OK: no TV contact'
 exit 0
fi

if ! active; then
 ((NO_WAKE==0)) || error 'TV not ready; --no-wake prevents recovery'
 echo 'TV in standby or unavailable. Sending one Wake-on-LAN.'
 # This helper derives the device MAC from LAN ARP; no power-toggle or app launch.
 bounded 8 /usr/bin/python3 "$PROBE" --wake-first --action state --timeout 3 || true
 ready=0
 for _ in 1 2 3 4; do
  if active; then ready=1; break; fi
  sleep 2
 done
 ((ready)) || error 'TV did not become ready after Wake-on-LAN; installation skipped'
fi
echo 'TV ready.'

# Use local files for the Node CLI: loading node_modules from network AI-Hot can stall.
CLI="$LOCAL_CLI"
if [[ ! -f "$CLI/ares-install.js" ]]; then
 TMP="$(mktemp -d "${TMPDIR:-/tmp/}dc4i-ares-cli.XXXXXX")"
 tar -xzf "$ROOT/tools/ares-cli-node-arm64.tar.gz" -C "$TMP"
 CLI="$TMP/node_modules/@webos-tools/cli/bin"
fi
export HOME="$ROOT/.ares-home"
[[ -f "$CLI/ares-install.js" ]] || error 'webOS installer unavailable'
[[ -f "$CLI/ares-launch.js" || "$LAUNCH" = 0 ]] || error 'webOS launcher unavailable'

# Confirm the IPK package identity and version before modifying the device.
control="$(/usr/bin/ar -p "$PACKAGE" control.tar.gz | tar -xzOf - control)" || error 'Invalid IPK'
pkg="$(printf '%s\n' "$control" | awk -F ': ' '$1=="Package"{print $2;exit}')"
version="$(printf '%s\n' "$control" | awk -F ': ' '$1=="Version"{print $2;exit}')"
[[ "$pkg" == "$APP" && "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || error 'Unexpected IPK package or version'

echo "Installing $APP $version..."
bounded 120 "$NODE" "$CLI/ares-install.js" --device "$DEVICE" "$PACKAGE" || error 'Install failed or timed out'

# Read-only confirmation, without launching the TV app.
check="$(bounded 10 /usr/bin/expect "$ROOT/tv_ssh_authed.exp" "cat /media/developer/apps/usr/palm/applications/$APP/appinfo.json" 2>&1)" || error 'Installed, but readback failed'
# Extract appinfo JSON from mixed Expect output without printing credentials.
VERSION="$version" APP_ID="$APP" CHECK="$check" /usr/bin/python3 - <<'PY'
import json,os,sys
text=os.environ['CHECK']
start=text.find('{')
end=text.rfind('}')
try: data=json.loads(text[start:end+1])
except (ValueError,TypeError): sys.exit('ERROR: invalid appinfo readback')
if data.get('id')!=os.environ['APP_ID'] or data.get('version')!=os.environ['VERSION']:
    sys.exit('ERROR: installed version mismatch')
print('INSTALLED_VERSION_VERIFIED',data['version'])
PY
if ((LAUNCH)); then
 bounded 30 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" "$APP" || error 'Optional app launch failed'
else
 echo 'DONE: install-only, app not launched.'
fi
