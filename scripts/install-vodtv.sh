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
LOCAL_CLI="/tmp/dc4i-ares-cli/node_modules/@webos-tools/cli/bin"
ARCHIVE="$ROOT/tools/ares-cli-node-arm64.tar.gz"
CLI_SOURCE='auto'
CLI="$LOCAL_CLI"
PACKAGE=''
DRY_RUN=0
CHECK_ONLY=0
VERIFY_ONLY=0
LAUNCH=0
WAKE_IF_NEEDED=0
CLI_TMP=''
WOKE_BY_INSTALLER=0

usage() {
 cat <<'EOF'
Usage:
  install-vodtv.sh --check-only
  install-vodtv.sh --ipk /absolute/path/file.ipk --verify-only
  install-vodtv.sh --version X.Y.Z [--launch] [--cli auto|minimal|archive]
  install-vodtv.sh --ipk /absolute/path/file.ipk [--launch] [--cli auto|minimal|archive]
  install-vodtv.sh --version X.Y.Z --dry-run
  install-vodtv.sh --ipk /absolute/path/file.ipk --wake-if-needed
Default: install only, never launch, wake, reboot or interact with TV UI.
--cli auto: use a validated local CLI cache; otherwise extract the official archive
  into temporary LOCAL storage. Do not execute Node modules from SMB AI-Hot.
--cli minimal: explicitly run the network-mount CLI (diagnostic only, may stall).
--wake-if-needed: explicitly allow ONE ARP-addressed Wake-on-LAN action
  when paired SSAP does not report Active. No Power-toggle or Home key.
--check-only: read-only TV readiness check; no IPK or installer involved.
--verify-only: verify IPK identity and installed appinfo over SSH, never install/launch.
--dry-run: validate package and local tooling; no TV contact.
Known errors: exit 20=port unreachable, 21=SSH auth/timeout,
22=install timeout, 23=install failure, 24=power state not confirmed Active,
25=installed package metadata or read-only version verification failed.
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
  --verify-only) VERIFY_ONLY=1; shift;;
  --dry-run) DRY_RUN=1; shift;;
  --launch) LAUNCH=1; shift;;
  --wake-if-needed) WAKE_IF_NEEDED=1; shift;;
  -h|--help) usage; exit 0;;
  *) die "Unknown option: $1";;
 esac
done

[[ "$CLI_SOURCE" =~ ^(auto|minimal|archive)$ ]] || die 'Invalid --cli setting'
if ((WAKE_IF_NEEDED && DRY_RUN)); then die '--wake-if-needed cannot be used with --dry-run'; fi
if ((VERIFY_ONLY && (DRY_RUN || LAUNCH || WAKE_IF_NEEDED))); then die '--verify-only cannot be combined with --dry-run, --launch or --wake-if-needed'; fi
if ((CHECK_ONLY)); then
 ((DRY_RUN==0 && LAUNCH==0 && VERIFY_ONLY==0 && WAKE_IF_NEEDED==0)) || die '--check-only is strictly read-only; do not combine with --dry-run, --verify-only, --launch or --wake-if-needed'
else
 [[ -n "$PACKAGE" ]] || { usage; die 'Specify --version or --ipk'; }
 [[ "$PACKAGE" = /* && "$PACKAGE" == *.ipk ]] || die 'IPK must be an absolute .ipk path'
 [[ -f "$PACKAGE" ]] || die "IPK not found: $PACKAGE"
fi

cleanup() {
 local previous_exit=$?
 trap - EXIT
 # Restore the prior black-screen state only when THIS run sent Wake-on-LAN.
 # This also applies to failed installations. Do not change an already-active TV.
 if ((WOKE_BY_INSTALLER)); then
  printf 'Restoring TV black-screen state after installer wake...\n'
  local output
  output="$(run_bounded 8 26 26 /usr/bin/python3 "$ROOT/tools/lg_ssap_probe.py" --action screen-off --timeout 3 2>&1)" || true
  if [[ "$output" == *'SCREEN_OFF_RESPONSE {"returnValue": true}'* ]]; then
   printf 'TV_SCREEN_RESTORED\n'
  else
   printf 'WARNING: TV screen restore not confirmed; previous exit=%s\n' "$previous_exit" >&2
  fi
 fi
 if [[ -n "$CLI_TMP" && -d "$CLI_TMP" ]]; then rm -rf "$CLI_TMP"; fi
 exit "$previous_exit"
}
trap cleanup EXIT

prepare_cli() {
 [[ -x "$NODE" ]] || die "Node 20 runtime not available: $NODE"
 [[ -d "$ROOT/.ares-home" ]] || die 'Private CLI configuration is missing'
 export HOME="$ROOT/.ares-home"
 if [[ "$CLI_SOURCE" == "minimal" ]]; then
  CLI="$MINIMAL"
  printf 'WARNING: explicit network-mount CLI may stall on SMB module loading.\n'
 elif [[ "$CLI_SOURCE" == "auto" && -f "$LOCAL_CLI/ares-install.js" && -f "$MINIMAL/ares-install.js" ]] && cmp -s "$LOCAL_CLI/ares-install.js" "$MINIMAL/ares-install.js" && cmp -s "${LOCAL_CLI%/bin}/package.json" "${MINIMAL%/bin}/package.json"; then
  CLI="$LOCAL_CLI"
  printf 'Using previously verified local CLI cache.\n'
 else
  [[ -f "$ARCHIVE" ]] || die "CLI archive not found: $ARCHIVE"
  if ((DRY_RUN)); then
   printf 'DRY RUN: would extract official CLI archive to a new local temporary directory.\n'
   return 0
  fi
  CLI_TMP="$(mktemp -d "${TMPDIR:-/tmp/}dc4i-ares-cli.XXXXXX")"
  tar -xzf "$ARCHIVE" -C "$CLI_TMP"
  CLI="$CLI_TMP/node_modules/@webos-tools/cli/bin"
  printf 'Using official CLI extracted to local temporary storage.\n'
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
 printf 'TV SSH port reachable. Checking paired SSAP power state (read-only).\n'
 local probe="$ROOT/tools/lg_ssap_probe.py"
 [[ -f "$probe" ]] || fail 24 "Paired SSAP power probe is missing: $probe"
 local power_result
 power_result="$(/usr/bin/python3 "$probe" --action state --timeout 2 2>&1)" || true
 # Do not treat open TCP/SSH as proof of an awake TV.
 if [[ "$power_result" != *'"state": "Active"'* ]] && ((WAKE_IF_NEEDED)); then
  printf 'TV not confirmed Active. Trying one authorized Wake-on-LAN using verified LAN ARP MAC.\n'
  power_result="$(/usr/bin/python3 "$probe" --wake-first --action state --timeout 3 2>&1)" || true
  if [[ "$power_result" == *WAKE_PACKET_SENT_TO_LAN_MAC* ]]; then WOKE_BY_INSTALLER=1; fi
  if [[ "$power_result" != *'"state": "Active"'* ]]; then
   # A double Power Off can take a few seconds to recover; wait only for readiness.
   for attempt in 1 2 3; do
    sleep 2
    power_result="$(/usr/bin/python3 "$probe" --action state --timeout 2 2>&1)" || true
    if [[ "$power_result" == *'"state": "Active"'* ]]; then
     printf 'TV became ready after Wake-on-LAN (check %s).\n' "$attempt"
     break
    fi
   done
  fi
 fi
 if [[ "$power_result" != *'"state": "Active"'* ]]; then
  fail 24 "TV Active state not confirmed by paired SSAP ($power_result). Installation skipped. Wake with the remote if necessary."
 fi
 printf 'TV POWER_STATE=Active verified through paired SSAP.\n'
 printf 'Checking SSH authentication.\n'
 local ssh_result
 ssh_result="$(run_bounded 12 21 21 /usr/bin/expect "$ROOT/tv_ssh_authed.exp" 'echo TV_CONNECTION_OK' 2>&1)" || fail 21 'TV SSH authentication failed/timed out. Installation skipped.'
 [[ "$ssh_result" == *TV_CONNECTION_OK* && "$ssh_result" == *'REMOTE_SSH_EXIT 0'* ]] || fail 21 'TV SSH not authenticated. Installation skipped.'
 printf 'TV_READY\n'
}


verify_package_identity() {
 local control_text pkg_id
 control_text="$(/usr/bin/ar -p "$PACKAGE" control.tar.gz | tar -xzOf - control)" || fail 25 "Cannot read Debian IPK control metadata."
 pkg_id="$(printf '%s\n' "$control_text" | /usr/bin/awk -F ': ' '$1=="Package" {print $2;exit}')"
 EXPECTED_VERSION="$(printf '%s\n' "$control_text" | /usr/bin/awk -F ': ' '$1=="Version" {print $2;exit}')"
 [[ "$pkg_id" == "$APP_ID" && "$EXPECTED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 25 "Incorrect IPK identity/version; expected $APP_ID."
 printf 'IPK_IDENTITY_OK package=%s version=%s\n' "$pkg_id" "$EXPECTED_VERSION"
}

verify_installed_version() {
 local remote_cmd verification
 remote_cmd="grep -E '\"(id|version)\"' /media/developer/apps/usr/palm/applications/$APP_ID/appinfo.json"
 verification="$(run_bounded 10 25 25 /usr/bin/expect "$ROOT/tv_ssh_authed.exp" "$remote_cmd" 2>&1)" || fail 25 "Install command passed, but post-install read-only appinfo verification failed."
 if [[ "$verification" != *'REMOTE_SSH_EXIT 0'* || "$verification" != *"\"id\": \"$APP_ID\""* || "$verification" != *"\"version\": \"$EXPECTED_VERSION\""* ]]; then
  fail 25 "Installer returned success but device appinfo does not confirm $APP_ID version $EXPECTED_VERSION. Do not blindly retry."
 fi
 printf 'INSTALLED_VERSION_VERIFIED package=%s version=%s\n' "$APP_ID" "$EXPECTED_VERSION"
}

if ((VERIFY_ONLY)); then
 verify_package_identity
 verify_installed_version
 printf 'VERIFY_ONLY_OK: no install or launch performed.\n'
 exit 0
fi

if ((DRY_RUN)); then
 verify_package_identity
 [[ -x "$NODE" ]] || die "Node runtime missing: $NODE"
 [[ -f "$ARCHIVE" || -f "$LOCAL_CLI/ares-install.js" || -f "$MINIMAL/ares-install.js" ]] || die 'No existing CLI/archive available'
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
verify_package_identity
printf 'Package: %s\nCLI: %s\nNode: %s\n' "$PACKAGE" "$CLI" "$("$NODE" --version)"
shasum -a 256 "$PACKAGE"
INSTALL_DEADLINE=120
if ((WAKE_IF_NEEDED)); then INSTALL_DEADLINE=45; fi
printf 'Installing on %s (%s-second bound).\n' "$DEVICE" "$INSTALL_DEADLINE"
run_bounded "$INSTALL_DEADLINE" 22 23 "$NODE" "$CLI/ares-install.js" --device "$DEVICE" "$PACKAGE" || fail "$?" 'Installation timed out or failed; inspect this result before retry.'
printf 'INSTALL_SUCCESS\n'
verify_installed_version
if ((LAUNCH)); then
 printf 'Explicit --launch requested; launching %s\n' "$APP_ID"
 run_bounded 30 22 23 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" "$APP_ID" || fail "$?" 'Launch failed.'
 local_running="$(run_bounded 15 22 23 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" --running 2>&1)" || fail 23 'Launch returned success, but running-state query failed; do not blindly retry.'
 [[ "$local_running" == *"$APP_ID"* ]] || fail 23 'Launch returned success, but application is not confirmed running.'
 printf 'APP_RUNNING_VERIFIED package=%s\n' "$APP_ID"
else
 printf 'Install-only completed; TV app not launched.\n'
fi
