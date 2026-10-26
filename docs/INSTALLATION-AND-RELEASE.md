# DC4I VOD TV Installation and Release Procedure

Status: historical installation procedure verified for version 1.2.4 on the real LG OLED55G42LW. The procedure has not yet been re-verified for package 1.2.19.

## Canonical machine and files

All paths below refer to the owner's Mac Pro.

- Service root: `/Volumes/AI-Hot/Services/LGWebOSRemote`
- Package directory: `/Volumes/AI-Hot/Services/LGWebOSRemote/packages`
- Official webOS CLI archive (macOS arm64): `/Volumes/AI-Hot/Services/LGWebOSRemote/tools/ares-cli-node-arm64.tar.gz`
- Archive SHA-256: `4e092cb53f9226cee5af775b60ba28817770899a4e2b3d20659d8a940fe0a7a4`
- Private device configuration: `/Volumes/AI-Hot/Services/LGWebOSRemote/.ares-home/.webos/tv/novacom-devices.json`
- Target device name: `LG_OLED55G42LW`
- App ID: `com.dc4i.vodtv`
- Local historical runbook: `/Volumes/AI-Hot/Services/LGWebOSRemote/INSTALL-DC4I-VODTV.md`

The private device configuration contains credentials. Never print it, copy it into a command, commit it, or include its values in logs or documentation.

## Standard installation procedure

Use the official CLI archive and the private device configuration. Do not substitute the separate `webos-cli-minimal` CLI just because it is already expanded.

Set the package path to the exact versioned IPK that was verified before installation:

```sh
ROOT='/Volumes/AI-Hot/Services/LGWebOSRemote'
IPK="$ROOT/packages/com.dc4i.vodtv_<VERSION>_all.ipk"

# Verify the package exists and record its checksum.
test -f "$IPK" || { echo "IPK not found: $IPK"; exit 1; }
shasum -a 256 "$IPK"

# Expand the documented official CLI into a temporary directory.
mkdir -p /tmp/dc4i-ares-cli
tar -xzf "$ROOT/tools/ares-cli-node-arm64.tar.gz" -C /tmp/dc4i-ares-cli
export HOME="$ROOT/.ares-home"
CLI='/tmp/dc4i-ares-cli/node_modules/@webos-tools/cli/bin'

# Check device reachability/authentication before attempting installation.
node "$CLI/ares-novacom.js" --device LG_OLED55G42LW --run 'id'

# Install only the specified package.
node "$CLI/ares-install.js" --device LG_OLED55G42LW "$IPK"
```

Use the exact release package path, for example `$ROOT/packages/com.dc4i.vodtv_1.2.19_all.ipk`, not a guessed filename. Confirm the package checksum against the canonical release record before installation.

## Scope controls

- Check whether the TV is reachable before starting. Do not infer that the TV is idle just because it is reachable.
- When the owner requests **installation only**, do not launch the app, navigate the TV UI, restart the TV, or perform interactive/device-side tests. Stop after the installer reports success.
- Only run `ares-launch`, `ares-launch --running`, installed-app listing, or other TV-side checks when the user explicitly authorizes that verification scope.
- Do not uninstall the existing app before an in-place update unless the app identity or a documented migration requires it. App ID is `com.dc4i.vodtv`; legacy `com.dc4i.boringtv` is a different identity.
- Keep temporary CLI expansion and large artifacts off the system disk wherever possible. The documented CLI extraction uses `/tmp`; remove it after the operation completes if no active process depends on it.

## Failure handling

If the connection check or installer stalls/fails:
1. Capture the process output, exit state, elapsed time and exact failing command, without printing credentials.
2. Check the target device's reachability and inspect the current process state.
3. Stop only the stalled process started for this operation; do not restart the TV or other shared services.
4. Diagnose the failing CLI path/configuration before trying again. Do not repeat the same failing command indefinitely and do not silently switch to a different CLI.
5. If a different procedure is necessary, document the reason and verify it before marking the procedure as proven.

## Verification and evidence labels

- **VERIFIED:** installer reports success for the exact package and target device.
- **NOT VERIFIED:** checksum, network reachability, file presence or a successful command startup alone.
- **DEVICE TEST NOT AUTHORIZED:** installation-only scope; no app launch or interactive testing was performed.

Historical evidence in `/Volumes/AI-Hot/Services/LGWebOSRemote/INSTALL-DC4I-VODTV.md` confirms version 1.2.4 was installed and launched successfully using this official CLI procedure. This historical evidence does not prove a future package is installed, and it does not count as verification of a later release.


## Unified Mac Pro installer (2026-10-26)

The owner's Mac Pro now has one shared script at `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`. It combines the preinstalled `webos-cli-minimal` path with the archive-based fallback, explicitly runs Node.js 20.19.4, reuses the private `.ares-home` configuration, checks the TV's SSH reachability, and installs an explicitly selected IPK. **Default is installation only; no launch, restart, wake-up or TV UI tests.** An optional `--launch` is required to open the app.

```sh
# Version already in the Mac Pro package directory:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --version 1.2.19

# Explicit absolute path to a locally built IPK:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --ipk /absolute/path/com.dc4i.vodtv_1.2.20_all.ipk

# Safe validation without contacting the TV:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --version 1.2.19 --dry-run
```

`--cli auto` (default) uses the already-installed minimal CLI; `--cli archive` forces a temporary unpack of the official archived CLI. No automatic retry or tool switching after an installation failure. `--launch` is explicit and may disrupt viewing, so do not use it without owner authorization.

**Evidence:** `bash -n` and `--dry-run` succeeded with both 1.2.19 and the locally present 1.2.20 package on 2026-10-26. **Live installation via this new wrapper has NOT been tested.** Historical successful direct CLI installation of 1.2.19 is separate evidence, not proof that this wrapper was used.
