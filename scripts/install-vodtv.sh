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
PACKAGE=''
CLI_SOURCE='auto'
usage() {
  cat <<'EOF'
Usage: install-vodtv.sh [--ipk /absolute/path/file.ipk | --version X.Y.Z] [--launch] [--dry-run] [--cli auto|minimal|archive]
Default: install only, never launch or test on TV.
--cli auto uses existing minimal CLI, falls back to official archive only when files are missing.
The script never uninstalls apps, wakes or reboots the TV.
EOF
}
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
while (($#)); do
 case "$1" in
  --ipk) (($# >= 2)) || die 'Missing --ipk argument'; PACKAGE="$2"; shift 2;;
  --version) (($# >= 2)) || die 'Missing --version argument'; [[ "$2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'Invalid version'; PACKAGE="$ROOT/packages/com.dc4i.vodtv_${2}_all.ipk"; shift 2;;
  --launch) LAUNCH=1; shift;;
  --dry-run) DRY_RUN=1; shift;;
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
# Non-disruptive connectivity check using existing, locally protected credential handler.
CHECK_OUTPUT="$(/usr/bin/expect "$ROOT/tv_ssh_authed.exp" 'echo TV_CONNECTION_OK' 2>&1)" || die 'TV SSH check failed (TV may be asleep or offline)'
[[ "$CHECK_OUTPUT" == *TV_CONNECTION_OK* && "$CHECK_OUTPUT" == *'REMOTE_SSH_EXIT 0'* ]] || die 'TV SSH check did not confirm success'
printf 'TV SSH reachable. Starting installation.\n'
# No automatic retries. A failed or stalled CLI must be diagnosed before another attempt.
"$NODE" "$CLI/ares-install.js" --device "$DEVICE" "$PACKAGE"
printf 'Installer returned success.\n'
if ((LAUNCH)); then
 printf 'Explicit --launch requested. Launching application.\n'
 "$NODE" "$CLI/ares-launch.js" --device "$DEVICE" "$APP_ID"
else
 printf 'Install-only completed. App was not launched.\n'
fi
