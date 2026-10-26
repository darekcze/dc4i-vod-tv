#!/bin/bash
# DC4I VOD TV: canonical Mac Pro webOS installer. Install-only by default.
set -Eeuo pipefail

ROOT='/Volumes/AI-Hot/Services/LGWebOSRemote'
DEVICE='LG_OLED55G42LW'
APP_ID='com.dc4i.vodtv'
TV_HOST='192.168.1.60'
TV_PORT=9922
NODE='/Users/czech/.nvm/versions/node/v20.19.4/bin/node'
MINIMAL="$ROOT/tools/webos-cli-minimal/node_modules/@webos-tools/cli/bin"
ARCHIVE="$ROOT/tools/ares-cli-node-arm64.tar.gz"
CLI_SOURCE='auto'
CLI="$MINIMAL"
PACKAGE=''
DRY_RUN=0
CHECK_ONLY=0
LAUNCH=0
ALLOW_ALWAYS_READY=0
CLI_TMP=''

usage() {
 cat <<'EOF'
Usage:
  install-vodtv.sh --check-only
  install-vodtv.sh --version X.Y.Z [--launch] [--cli auto|minimal|archive]
  install-vodtv.sh --ipk /absolute/path/file.ipk [--launch] [--cli auto|minimal|archive]
  install-vodtv.sh --version X.Y.Z --dry-run
  install-vodtv.sh --ipk /absolute/path/file.ipk --allow-always-ready
Default: install only, never launch, wake, reboot or interact with TV UI.
--check-only: read-only TV readiness check; no IPK or installer involved.
--dry-run: validate package and local tooling; no TV contact.
--allow-always-ready: explicit owner-approved single background install attempt
  when power-state API is unavailable; SSH auth must still succeed.
  A short (20s) installer deadline applies. Not valid with --launch.
Known errors: exit 20=port unreachable, 21=SSH auth/timeout,
22=install timeout, 23=install failure, 24=power state not confirmed Active.
EOF
}
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
fail() { local code="$1"; shift; printf 'ERROR [%s]: %s\n' "$code" "$*" >&2; exit "$code"; }

while (($#)); do
 case "$1" in
  --version)
   (($# >= 2)) || die 'Missing --version argument'
   [[ -z "$PACKAGE" && "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'Invalid/duplicate version'
   PACKAGE="$ROOT/packages/com.dc4i.vodtv_${2}_all.ipk"
   shift 2;;
  --ipk)
   (($# >= 2)) || die 'Missing --ipk argument'
   [[ -z "$PACKAGE" ]] || die 'Specify only one package'
   PACKAGE="$2"; shift 2;;
  --cli) (($# >= 2)) || die 'Missing --cli value'; CLI_SOURCE="$2"; shift 2;;
  --check-only) CHECK_ONLY=1; shift;;
  --dry-run) DRY_RUN=1; shift;;
  --launch) LAUNCH=1; shift;;
  --allow-always-ready) ALLOW_ALWAYS_READY=1; shift;;
  -h|--help) usage; exit 0;;
  *) die "Unknown option: $1";;
 esac
done

[[ "$CLI_SOURCE" =~ ^(auto|minimal|archive)$ ]] || die 'Invalid --cli setting'
if ((ALLOW_ALWAYS_READY && LAUNCH)); then die '--allow-always-ready cannot be used with --launch'; fi
if ((CHECK_ONLY)); then
 ((DRY_RUN==0 && LAUNCH==0)) || die '--check-only cannot be combined with --dry-run or --launch'
else
 [[ -n "$PACKAGE" ]] || { usage; die 'Specify --version or --ipk'; }
 [[ "$PACKAGE" = /* && "$PACKAGE" == *.ipk ]] || die 'IPK must be an absolute .ipk path'
 [[ -f "$PACKAGE" ]] || die "IPK not found: $PACKAGE"
fi

cleanup() {
 if [[ -n "$CLI_TMP" && -d "$CLI_TMP" ]]; then rm -rf "$CLI_TMP"; fi
}
trap cleanup EXIT

prepare_cli() {
 [[ -x "$NODE" ]] || die "Node 20 runtime not available: $NODE"
 [[ -d "$ROOT/.ares-home" ]] || die 'Private CLI configuration is missing'
 export HOME="$ROOT/.ares-home"
 if [[ "$CLI_SOURCE" == archive || ( "$CLI_SOURCE" == auto && ! -f "$MINIMAL/ares-install.js" ) ]]; then
  [[ -f "$ARCHIVE" ]] || die "CLI archive not found: $ARCHIVE"
  if ((DRY_RUN)); then
   printf 'DRY RUN: would extract official CLI archive to a temporary directory\n'
   return 0
  fi
  CLI_TMP="$(mktemp -d "${TMPDIR:-/tmp/}dc4i-ares-cli.XXXXXX")"
  tar -xzf "$ARCHIVE" -C "$CLI_TMP"
  CLI="$CLI_TMP/node_modules/@webos-tools/cli/bin"
 fi
 [[ -f "$CLI/ares-install.js" ]] || die "Installer not found: $CLI"
 if ((LAUNCH)); then [[ -f "$CLI/ares-launch.js" ]] || die 'Launcher is missing'; fi
}

run_bounded() {
 local seconds="$1" timeout_code="$2" error_code="$3"; shift 3
 /usr/bin/python3 - "$seconds" "$timeout_code" "$error_code" "$@" <<'PY'
import os, signal, subprocess, sys
seconds, timeout_code, error_code = map(int, sys.argv[1:4])
p = subprocess.Popen(sys.argv[4:], start_new_session=True)
try:
    exit_code = p.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
    print("Timed out; installer process group terminated", file=sys.stderr)
    sys.exit(timeout_code)
sys.exit(0 if exit_code == 0 else error_code)
PY
}

check_tv() {
 /usr/bin/python3 - "$TV_HOST" "$TV_PORT" <<'PY' || fail 20 'TV not reachable on SSH (possibly sleeping/offline). No installation attempted.'
import socket,sys
try:
    with socket.create_connection((sys.argv[1],int(sys.argv[2])),timeout=2):
        pass
except OSError:
    sys.exit(1)
PY
 printf 'TV SSH port reachable. Checking actual power state (read-only).\n'
 # SSH remains reachable on this LG even in standby. SSAP getPowerState is required.
 local power_result
 power_result="$(/usr/bin/python3 - "$ROOT" <<'PY'
import json, os, subprocess, sys
root = sys.argv[1]
cmd = [root+'/.venv/bin/python3',root+'/source/lgtv.py',
       '--name','LG_OLED55G42LW','--ssl','getPowerState']
env = dict(os.environ,XDG_CONFIG_HOME=root+'/.config')
try:
    proc=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=4)
except subprocess.TimeoutExpired:
    print('POWER_STATE_TIMEOUT');sys.exit(24)
except OSError:
    print('POWER_READER_UNAVAILABLE');sys.exit(24)
state=None
for line in proc.stdout.splitlines():
    try:
        message=json.loads(line)
    except (TypeError,ValueError):
        continue
    payload=message.get('payload',{}) if isinstance(message,dict) else {}
    if isinstance(payload,dict):
        state=payload.get('state') or payload.get('powerState')
        if state is not None:break
if not isinstance(state,str):
    print('POWER_STATE_UNKNOWN');sys.exit(24)
print('POWER_STATE='+state.strip())
if state.strip().casefold()!='active':
    sys.exit(24)
PY
 )" || {
  if ((ALLOW_ALWAYS_READY)); then
   printf 'POWER_UNCONFIRMED (%s). Explicit --allow-always-ready: trying one bounded, non-interactive installation via SSH.\n' "$power_result"
  else
   fail 24 "TV active state not confirmed ($power_result). It may be sleeping or power API unavailable. Installation skipped."
  fi
 }
 if [[ "$power_result" == POWER_STATE=Active ]]; then
  printf '%s\n' "$power_result"
 else
  ((ALLOW_ALWAYS_READY)) || fail 24 "TV not confirmed active ($power_result). Installation skipped."
 fi
 printf 'Checking SSH authentication.\n'
 local ssh_result
 ssh_result="$(run_bounded 12 21 21 /usr/bin/expect "$ROOT/tv_ssh_authed.exp" 'echo TV_CONNECTION_OK' 2>&1)" || fail 21 'TV SSH authentication failed/timed out. Installation skipped.'
 [[ "$ssh_result" == *TV_CONNECTION_OK* && "$ssh_result" == *'REMOTE_SSH_EXIT 0'* ]] || fail 21 'TV SSH not authenticated. Installation skipped.'
 printf 'TV_READY\n'
}

if ((DRY_RUN)); then
 prepare_cli
 printf 'Package: %s\n' "$PACKAGE"
 shasum -a 256 "$PACKAGE"
 printf 'DRY_RUN_OK: no TV contact; launch requested: %s\n' "$LAUNCH"
 exit 0
fi

check_tv
if ((CHECK_ONLY)); then
 printf 'CHECK_ONLY_OK: no install or launch performed.\n'
 exit 0
fi

prepare_cli
printf 'Package: %s\nCLI: %s\nNode: %s\n' "$PACKAGE" "$CLI" "$("$NODE" --version)"
shasum -a 256 "$PACKAGE"
INSTALL_DEADLINE=120
if ((ALLOW_ALWAYS_READY)); then INSTALL_DEADLINE=20; fi
printf 'Installing on %s (%s-second bound).\n' "$DEVICE" "$INSTALL_DEADLINE"
run_bounded "$INSTALL_DEADLINE" 22 23 "$NODE" "$CLI/ares-install.js" --device "$DEVICE" "$PACKAGE" || fail "$?" 'Installation timed out or failed; inspect this result before retry.'
printf 'INSTALL_SUCCESS\n'
if ((LAUNCH)); then
 printf 'Explicit --launch requested; launching %s\n' "$APP_ID"
 run_bounded 30 22 23 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" "$APP_ID" || fail "$?" 'Launch failed.'
else
 printf 'Install-only completed; TV app not launched.\n'
fi
