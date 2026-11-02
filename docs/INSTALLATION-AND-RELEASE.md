# DC4I VOD TV Installation and Release Procedure

Status (2026-10-26): canonical executable installer VERIFIED on the real LG OLED55G42LW by successful in-place installation of 1.2.20 and independent read-only appinfo verification. Earlier 1.2.4 / 1.2.19 reports below are historical evidence.

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

## Standard HOME compatibility (2026-10-28)

On 2026-10-27 the owner's Mac Pro default profile at `/Users/czech` was configured with the existing LG device entry in `~/.webos/tv/novacom-devices.json` (mode 0600). The `~/.ssh/OLED55G42LW_webos_rsa` path is a symlink to the existing private key on mounted AI-Hot (not an additional private-key copy). The preexisting `.ares-home` profile remains intact as the private source/backup. Never publish the device registry or its secrets.

The canonical installer no longer modifies `HOME` (Git commit `8ed1646`); webOS CLI uses the caller's standard profile and checks registry/key readability. This resolves the known Codex session restriction on changing `HOME` without circumventing it. The edited Mac Pro installer passed `bash -n`, the CLI recognized `LG_OLED55G42LW` with unmodified `HOME=/Users/czech`, and the version 1.2.19 `--dry-run` passed. **A new live TV installation using the HOME-free revision has not yet been verified.** Do not conflate previous live installation of 1.2.20 with acceptance of this revised invocation.


## Standard installation procedure: scripts are canonical

**DO NOT recreate manual webOS CLI commands.** Use the version-controlled [installer script](../scripts/install-vodtv.sh), deployed on Mac Pro as `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`. It uses Node 20, a locally extracted CLI, private device credentials and an SSAP power-state probe. No secrets are committed or logged.

```sh
S='/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh'
# Normal install-only, no wake or launch:
bash "$S" --version 1.2.19

# Owner-approved recovery from Always Ready, install-only:
bash "$S" --ipk /absolute/path/com.dc4i.vodtv_1.2.20_all.ipk --wake-if-needed

# Safe checks, no TV navigation or launch:
bash "$S" --version 1.2.19 --dry-run   # offline
bash "$S" --check-only                  # read-only, no wake
bash "$S" --ipk /absolute/path/com.dc4i.vodtv_1.2.20_all.ipk --verify-only
```

`--wake-if-needed` authorizes a single WOL attempt using a verified ARP MAC, **only** when SSAP does not confirm Active. It does not send a Power-toggle, press Home/Back or launch an app. The lower-level [paired LG SSAP tool](../scripts/lg-ssap-probe.py) supports separately authorized `--action back` for an actual screen exit, but this is **not an automatic installer step**.

`--cli auto` (default) uses a verified local CLI cache if available, or extracts the official CLI archive to local temporary storage and removes its newly created extraction afterward. **Never execute Node CLI modules directly from the SMB-mounted AI-Hot tree.** `--cli minimal` is an explicit diagnostic override only. `--cli archive` always performs a fresh local extraction. The IPK itself may remain on AI-Hot or another mounted drive.

The installer validates package identity/version, performs bounded SSH and SSAP checks, reports stable nonzero error codes, terminates only its own timed-out processes, installs without launching by default, and verifies the installed version through read-only `appinfo.json`. Install command success alone is not enough for its final success report. A failed version verification does not authorize blindly retrying the install.

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

The owner's Mac Pro now has one shared script at `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`. It combines the preinstalled `webos-cli-minimal` path with the archive-based fallback, explicitly runs Node.js 20.19.4, uses the Mac Pro user's existing standard webOS CLI configuration (LG key linked to the private AI-Hot profile), checks the TV's SSH reachability, and installs an explicitly selected IPK. **Default is installation only; no launch, restart, wake-up or TV UI tests.** An optional `--launch` is required to open the app.

```sh
# Version already in the Mac Pro package directory:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --version 1.2.19

# Explicit absolute path to a locally built IPK:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --ipk /absolute/path/com.dc4i.vodtv_1.2.20_all.ipk

# Safe validation without contacting the TV:
/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --version 1.2.19 --dry-run
```

`--cli auto` (default) uses validated local CLI files or creates a temporary local extraction; `--cli archive` forces a fresh temporary extraction. No automatic retry or tool switching after an installation failure. `--launch` is explicit and may disrupt viewing, so do not use it without owner authorization.

**Evidence:** `bash -n` and `--dry-run` succeeded with both 1.2.19 and the locally present 1.2.20 package on 2026-10-26. At this historical checkpoint the wrapper had not yet been live-tested; superseded by the verified 1.2.20 deployment below. Historical successful direct CLI installation of 1.2.19 is separate evidence, not proof that this wrapper was used.


## Historical sleeping-TV readiness regression (superseded), 2026-10-26

Canonical executable: `scripts/install-vodtv.sh` in Git; deployed Mac Pro copy: `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`.

The LG OLED55G42LW was reported by its owner to be sleeping. Its SSH port 9922 **still accepted TCP** (0.032 seconds), and an authenticated SSH echo also succeeded (approximately 0.8 seconds). Therefore, a successful TCP or SSH preflight **does not prove the TV is active**.

The installer now provides a read-only `--check-only` mode and runs a bounded `getPowerState` SSAP query *before* SSH authentication, package hashing, CLI preparation, or installation. If an `Active` state cannot be confirmed within 4 seconds, it returns exit code 24 without installing or launching. No wake-on-LAN or screen control is used.

Verified on Mac Pro while user reported standby:

- `/bin/bash -n /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`: PASS
- `/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --check-only`: exit 24, **4.32 seconds**, `POWER_STATE_TIMEOUT`, no installation
- `/bin/bash /Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh --version 1.2.19 --dry-run`: exit 0, **2.25 seconds**, no TV contact; SHA-256 matches previously recorded release value
- No app installation, launch, reboot, wake action, or TV UI test was performed.

Interpretation: a power-state API timeout cannot distinguish standby from an unavailable API; fail-closed behavior prevents unexpected installations. This was the status of the earlier implementation and is superseded by the successful 1.2.20 installation with the paired SSAP probe and local CLI. If the power-state API does not return `Active` even while the owner confirms the TV is on, diagnose that reader rather than silently bypassing the safety gate.

## Current verified release and Always Ready recovery (2026-10-26)

- **Device:** LG OLED55G42LW, `com.dc4i.vodtv`.
- **Before:** installed `1.2.19`, read from `/media/developer/apps/usr/palm/applications/com.dc4i.vodtv/appinfo.json` via authorized SSH.
- **Candidate:** local development `com.dc4i.vodtv_1.2.20_all.ipk`, control metadata `Package: com.dc4i.vodtv`, `Version: 1.2.20`, SHA-256 `1b55b18bbcc7f05640e010714c7d002513abb6b6c5029da19c1315005811d0b3`.
- **Execution:** Mac Pro `install-vodtv.sh --ipk <local-1.2.20-ipk> --wake-if-needed`, using the cached local CLI `/tmp/dc4i-ares-cli/node_modules/@webos-tools/cli/bin`.
- **Result:** official installer printed `Success`, script reported `INSTALL_SUCCESS`, exit code `0` (approx. 14.19 s). Independent SSH readback and the new `--verify-only` command both confirmed `com.dc4i.vodtv` version **1.2.20**. **No application launch, playback testing, reboot or user-data reset.** This verifies installation only, not app-level runtime acceptance.
- **Canonical Git scripts:** `scripts/install-vodtv.sh` and `scripts/lg-ssap-probe.py`; Mac Pro deployment at `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh` and `.../tools/lg_ssap_probe.py`.

### Confirmed failure mechanisms and mitigations

1. **LG Always Ready after the first Power Off:** device may still accept TCP 9922 and SSH commands, even when standard webOS interfaces are not yet ready. Port reachability alone is insufficient.
2. **Stale wake hardware address:** the paired LGWebOSRemote configuration's MAC did not match the LAN ARP MAC for the same TV. A WOL packet using that stored MAC did not achieve observable readiness; WOL addressed to the ARP MAC enabled a successful paired WSS registration and the `getPowerState` response `Active`.
3. **Legacy power-state reader:** `source/lgtv.py ... getPowerState` timed out in the tested standby state. The new standalone standard-library probe, `scripts/lg-ssap-probe.py`, reused the existing paired LG client key without re-pairing and successfully reported `Active`.
4. **Always Ready screen exit:** with explicit authorization, the paired probe successfully sent the Back button via LG's pointer-input socket. Opening the pointer WSS while the primary SSAP WSS was still active timed out; first close the primary SSAP connection, then open the returned pointer socket and allow a brief flush before closing. This control action is not necessary for routine non-interactive installations and is never performed by default.
5. **SMB-hosted Node runtime failure:** webOS CLI 3.2.6 executed from `/Volumes/AI-Hot/.../webos-cli-minimal/node_modules` stalled while loading its many network filesystem dependencies. A diagnostic Node process showed `U` wait state before reaching its SSH test. Direct `ssh2` on Mac Pro authenticated and ran `id` in about 540 ms once loaded. The *same* official CLI running from local `/tmp/dc4i-ares-cli` installed 1.2.20 successfully. **This was the decisive fix**, rather than merely changing `HOME`.
6. **Access boundaries:** `luna-send-pub` was denied for power-state and screen-on methods on the developer user; this was not bypassed. The screen wake used the owner's already-paired SSAP/WebSocket control surface. No privilege escalation was performed.
7. **Bounded failure:** an explicit `--allow-always-ready` troubleshooting attempt with the old SMB-loaded CLI timed out after 20 s, and another after 45 s, without changing the installed version. This unsuccessful bypass option was removed from the canonical script. The normal installer uses a bounded operation and does not blindly retry.

### Verification checklist

- `bash -n` for `install-vodtv.sh`: PASS
- `python3 -m py_compile` for `lg_ssap_probe.py`: PASS
- `--dry-run` with version 1.2.19: PASS, no TV contact
- `--verify-only` with IPK 1.2.20: PASS, exact package ID and device version
- `--check-only --wake-if-needed`: correctly rejected, preventing a nominally read-only check from waking the TV
- Live install of 1.2.20: PASS via locally executed CLI and installed-version readback
- Full two-stage TV Power Off, waking from deep standby and app UI behavior: **NOT TESTED** under this installation-only authorization

Source on LG's Always Ready behavior: [LG support](https://www.lg.com/us/support/help-library/lg-tv-how-to-use-the-always-ready-function--20153870949064).

## Double Power Off recovery verification (2026-10-26)

Owner switched LG OLED55G42LW off twice so the panel was black. Tested with the canonical Mac Pro installer and the already-paired LG SSAP/Wake-on-LAN helper.

- Initial `install-vodtv.sh --version 1.2.19 --wake-if-needed` attempted one WOL, but immediately returned code 24 because paired SSAP was not yet ready (`websocket closed by TV`). **No installation occurred on that attempt.**
- A follow-up read-only SSAP check reported `Active` shortly afterward.
- Re-running the same existing installer installed **1.2.19** successfully (installer `Success`, exit 0, exact installed-version readback, about 16 s).
- Restoring **1.2.20** with `--ipk /Users/czech/Documents/Codex/2026-10-26/task/vod-release/private/com.dc4i.vodtv_1.2.20_all.ipk --wake-if-needed` also succeeded (WOL recovery, installer `Success`, exit 0, installed-version readback, about 12 s).
- Final installed version: **1.2.20**. No app launch, channel switching, restart or user-data reset.
- Small improvement to the existing canonical installer: after one WOL, if SSAP still does not report `Active`, retry *only the read-only readiness check* up to three times with 2-second pauses. Never blindly retry installation. Preserve all existing functionality and CLI selection.
- Updated script passed `bash -n`, and `--verify-only` reconfirmed installed version 1.2.20 (exit 0). **The new waiting loop has not itself been exercised by another double-Power-Off cycle**; the pre-fix observation validates why this mitigation is needed.

This is an installation runbook, not a request to test application playback or disturb the TV.

## Restore screen after installer wake (2026-10-26)

Owner-approved policy: If `install-vodtv.sh --wake-if-needed` sends Wake-on-LAN to recover a sleeping LG, restore the black-screen state after the installation or after a failure. An already-active TV, on which the installer sends no wake packet, must be left untouched. This is built into the canonical installer cleanup trap and preserves the original install error status. Do not send a Power-toggle or launch the VOD application.

The paired [LG SSAP helper](../scripts/lg-ssap-probe.py) supports `--action screen-off`, calling the existing LG `ssap://com.webos.service.tvpower/power/turnOffScreen` endpoint with `standbyMode: active`. A live call on the LG OLED55G42LW returned `SCREEN_OFF_RESPONSE {"returnValue": true}`, and the subsequent read-only `--action state` returned `"state": "Screen Off"`. This demonstrates an actual black panel, but does **not** establish that every deeper double-Power-Off behavior is equivalent. It deliberately targets the owner's requested visibly-off state using one command.

Safety: The restore action occurs only if this invocation observed `WAKE_PACKET_SENT_TO_LAN_MAC`. Restore is bounded to 8 seconds and reports `TV_SCREEN_RESTORED` or a warning. No additional full application installation was performed solely to test the cleanup trigger: its logic has passed Bash syntax checks, but the complete wake-install-restore transaction remains to be tested in a subsequent authorized version installation. The TV was left in `Screen Off` according to the verified power-state API.
