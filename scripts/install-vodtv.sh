#!/bin/bash
# DC4I VOD TV: shared Mac Pro LG installer. Install only by default.
set -Eeuo pipefail
ROOT='/Volumes/AI-Hot/Services/LGWebOSRemote'
DEVICE='LG_OLED55G42LW'
APP_ID='com.dc4i.vodtv'
NODE='/Users/czech/.nvm/versions/node/v20.19.4/bin/node'
MINIMAL="$ROOT/tools/webos-cli-minimal/node_modules/@webos-tools/cli/bin"
ARCHIVE="$ROOT/tools/ares-cli-node-arm64.tar.gz"
CLI="$MINIMAL"
LAUNCH=0
DRY_RUN=0
CHECK_ONLY=0
PACKAGE=''
CLI_SOURCE='auto'
TV_HOST='192.168.1.60'
TV_PORT=9922
CONNECT_TIMEOUT=2
SSH_TIMEOUT=12
INSTALL_TIMEOUT=120
usage() {
  cat <<'EOF'
Usage: install-vodtv.sh [--ipk /absolute/path/file.ipk | --version X.Y.Z] [--launch] [--dry-run] [--check-only] [--cli auto|minimal|archive]
Default: install only, never launch or test on TV.
--cli auto uses existing minimal CLI, falls back to official archive only when files are missing.
The script never uninstalls apps, wakes or reboots the TV.
Offline/sleeping TV: fast non-disruptive TCP+SSH+read-only power-state preflight and actionable error.
--check-only: perform device readiness checks, never install or launch (supply --version or --ipk).
Power-state API must report Active; unavailable/standby -> exit before installation.
Exit codes: 20=TV TCP unavailable, 21=SSH failed, 22=installer timeout, 23=installer failed, 24=TV not ready (power state).
EOF
}
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
fail() { local code="$1"; shift; printf 'ERROR [%s]: %s\n' "$code" "$*" >&2; exit "$code"; }
while (($#)); do
 case "$1" in
  --ipk) (($# >= 2)) || die 'Missing --ipk argument'; PACKAGE="$2"; shift 2;;
  --version) (($# >= 2)) || die 'Missing --version argument'; [[ "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'Invalid version'; PACKAGE="$ROOT/packages/com.dc4i.vodtv_${2}_all.ipk"; shift 2;;
  --launch) LAUNCH=1; shift;;
  --dry-run) DRY_RUN=1; shift;;
  --check-only) CHECK_ONLY=1; shift;;
  --cli) (($# >= 2)) || die 'Missing --cli argument'; CLI_SOURCE="$2"; shift 2;;
  -h|--help) usage; exit 0;;
  *) die "Unknown argument: $1";;
 esac
done
[[ -n "$PACKAGE" ]] || { usage; die 'Specify --ipk or --version'; }
[[ "$PACKAGE" = /* ]] || die 'IPK path must be absolute'
[[ "$PACKAGE" == *.ipk ]] || die 'Expected .ipk file'
[[ -f "$PACKAGE" ]] || die "Package not found: $PACKAGE"
[[ -x "$NODE" ]] || die "Node 20 not found: $NODE"
[[ -d "$ROOT/.ares-home" ]] || die 'Private webOS configuration missing'
[[ "$CLI_SOURCE" =~ ^(auto|minimal|archive)$ ]] || die 'Invalid CLI source'
export HOME="$ROOT/.ares-home"
PREPARED_ARCHIVE=0
cleanup() {
 if ((PREPARED_ARCHIVE)); then
   rm -rf "$CLI_TMP"
 fi
}
trap cleanup EXIT
if [[ "$CLI_SOURCE" == archive ]] || { [[ "$CLI_SOURCE" == auto ]] && [[ ! -f "$MINIMAL/ares-install.js" ]]; }; then
 [[ -f "$ARCHIVE" ]] || die "CLI archive missing: $ARCHIVE"
 CLI_TMP="$(mktemp -d "${TMPDIR:-/tmp/}dc4i-ares-cli.XXXXXX")"
 PREPARED_ARCHIVE=1
 tar -xzf "$ARCHIVE" -C "$CLI_TMP"
 CLI="$CLI_TMP/node_modules/@webos-tools/cli/bin"
fi
[[ -f "$CLI/ares-install.js" ]] || die "Installer missing: $CLI"
if ((LAUNCH)); then [[ -f "$CLI/ares-launch.js" ]] || die 'Launcher missing'; fi
printf 'Device: %s\nPackage: %s\nCLI: %s\nNode: %s\n' "$DEVICE" "$PACKAGE" "$CLI" "$("$NODE" --version)"
shasum -a 256 "$PACKAGE"
if ((DRY_RUN)); then
 printf 'DRY RUN: would check SSH reachability and install package. Launch: %s\n' "$LAUNCH"
 exit 0
fi
# Fast, non-disruptive TCP probe. Do not wake or control the TV.
if ! /usr/bin/python3 - "$TV_HOST" "$TV_PORT" "$CONNECT_TIMEOUT" <<'PY'
import socket, sys
host, port, timeout = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
try:
    with socket.create_connection((host, port), timeout=timeout):
        pass
except (OSError, TimeoutError):
    sys.exit(1)
PY
then
 fail 20 "TV SSH port is unreachable within ${CONNECT_TIMEOUT}s. TV may be asleep/offline or network is unavailable. No installation attempted; wake TV manually and rerun."
fi
# Bound SSH authentication and installation separately. Never echo credentials.
# Python subprocess timeout terminates the entire process group, preventing orphan CLI.
run_bounded() {
 local seconds="$1" timeout_code="$2" error_code="$3"; shift 3
 /usr/bin/python3 - "$seconds" "$timeout_code" "$error_code" "$@" <<'PY'
import os, signal, subprocess, sys
seconds, timeout_code, error_code = map(int, sys.argv[1:4])
command = sys.argv[4:]
p = subprocess.Popen(command, start_new_session=True)
try:
    code = p.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
    print("ERROR: operation timed out; process group stopped", file=sys.stderr)
    sys.exit(timeout_code)
sys.exit(0 if code == 0 else error_code)
PY
}
printf 'TV SSH port reachable. Checking authenticated connection.\n'
# Existing Expect script validates SSH and reports REMOTE_SSH_EXIT 0.
CHECK_OUTPUT="$(run_bounded "$SSH_TIMEOUT" 21 21 /usr/bin/expect "$ROOT/tv_ssh_authed.exp" 'echo TV_CONNECTION_OK' 2>&1)" || fail 21 "TV reachable but authenticated SSH failed or timed out. No installation attempted."
[[ "$CHECK_OUTPUT" == *TV_CONNECTION_OK* && "$CHECK_OUTPUT" == *'REMOTE_SSH_EXIT 0'* ]] || fail 21 'TV SSH authentication did not confirm success. No installation attempted.'
# SSH may remain reachable while LG webOS is in standby. Query power state
# through the already-paired, read-only SSAP API before starting any installation.
# A timeout or unsupported response means UNKNOWN, not proof of sleep.
REMOTE_PY="$ROOT/.venv/bin/python3"
REMOTE_CLI="$ROOT/source/lgtv.py"
[[ -x "$REMOTE_PY" && -f "$REMOTE_CLI" ]] || fail 24 'LG power-state reader is missing. No installation attempted.'
POWER_RESULT="$(/usr/bin/python3 - "$ROOT" <<'PY'
import json, os, subprocess, sys
root = sys.argv[1]
cmd = [root + '/.venv/bin/python3', root + '/source/lgtv.py',
       '--name', 'LG_OLED55G42LW', '--ssl', 'getPowerState']
env = dict(os.environ, XDG_CONFIG_HOME=root + '/.config')
try:
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=4)
except subprocess.TimeoutExpired:
    print('POWER_STATE_TIMEOUT')
    sys.exit(24)
except OSError:
    print('POWER_STATE_READER_ERROR')
    sys.exit(24)
state = None
for line in proc.stdout.splitlines():
    try:
        item = json.loads(line)
    except (ValueError, TypeError):
        continue
    payload = item.get('payload', {}) if isinstance(item, dict) else {}
    if not isinstance(payload, dict):
        continue
    state = payload.get('state') or payload.get('powerState')
    if state is not None:
        break
if not isinstance(state, str):
    print('POWER_STATE_UNAVAILABLE')
    sys.exit(24)
state = state.strip()
print('POWER_STATE=' + state)
if state.casefold() != 'active':
    sys.exit(24)
PY
)" || fail 24 "TV is not confirmed active ($POWER_RESULT). It may be sleeping or power-state API unavailable. No installation attempted."
printf '%s\n' "$POWER_RESULT"
if ((CHECK_ONLY)); then
 printf 'CHECK_ONLY_OK: TV responds to SSH and reports active power state. Nothing installed or launched.\n'
 exit 0
fi
printf 'TV SSH authenticated. Installing package (max %ss).\n' "$INSTALL_TIMEOUT"
# No automatic retries. The installer has a hard deadline and no launch by default.
run_bounded "$INSTALL_TIMEOUT" 22 23 "$NODE" "$CLI/ares-install.js" --device "$DEVICE" "$PACKAGE" || fail "$?" 'Installation failed or timed out. Check TV state and CLI diagnostics before retrying.'
printf 'Installer returned success.\n'
if ((LAUNCH)); then
 printf 'Explicit --launch requested. Launching application.\n'
 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" "$APP_ID"
else
 printf 'Install-only completed. App was not launched.\n'
fi
