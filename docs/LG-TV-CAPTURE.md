# LG TV capture runbook

[Polski](pl/LG-TV-CAPTURE.md) | [Evidence method and native IDs](LG-TV-EVIDENCE-METHOD.md)

## Scope and validation status

Use the executable tools in `scripts/lg-tv/` to inspect an existing paired LG webOS TV connection, collect menu screenshots, review their actual content, and generate a private UI atlas. The tools run on an authorized Mac with access to the television's LAN.

The SSAP capture route and native application identification were exercised on a physical LG OLED55G42LW on 2026-10-28. This does not establish complete coverage of the six menus in every app.

On 2026-10-28 an authorized physical-TV execution of the public client and `run_plan.py`, using explicit `--host`, completed six steps: three separate button batches interleaved with three captures and foreground checks. This exercises continued input across calls; it is not a general performance benchmark. Physical connection counts were not instrumented during that run; offline tests check reuse of one pointer connection.

A separate live image transfer also recovered on the second GET of the same URI and recorded `download_attempts: 2` with a valid image. That confirms the observed transfer-recovery path, not the intended menu category.

The owned-session wrapper `capture_session.py` and repeat-kit launcher remain **NOT VERIFIED ON HARDWARE**. Their 19-entry dry run validated 38 steps without TV contact or file creation. Full six-view collection still requires observed navigation and visual review.

This procedure is a synchronous local toolset. It creates no daemon, scheduler, separate job queue, or replacement for the project's AIOS operations.

## Version-controlled files

| File | Purpose |
| --- | --- |
| [lg_tv.py](../scripts/lg-tv/lg_tv.py) | Existing pairing, state/inventory, launch, buttons, captures, visual reviews, sessions and reviewed replay flows |
| [run_plan.py](../scripts/lg-tv/run_plan.py) | Short observed-navigation batches inside an already active session |
| [capture_session.py](../scripts/lg-tv/capture_session.py) | Own one session, run supplied plans, and attempt restoration in a cleanup path |
| [build_atlas.py](../scripts/lg-tv/build_atlas.py) | HTML/Markdown atlas, separate app pages, coverage table and summary |
| [targets.json](../scripts/lg-tv/targets.json) | Nonsecret app names, stable slugs and observed native IDs |
| [tests](../scripts/lg-tv/tests/) | Offline regression tests using fake devices and temporary files |

The repository ignores `tools/`; keep maintained source here under `scripts/lg-tv/`. The service's existing `tools/` directory remains a runtime dependency, not the canonical source of this new toolset.

## Prerequisites and private configuration

Require Python 3.9 or newer on macOS, including standard-library `zoneinfo` and `fcntl`. Use a computer already authorized for the local TV network. Select one controller for the full audit, even when two Macs are available.

The existing LGWebOSRemote root must contain:

- `.config/lgtv/config.json`, with the selected paired profile.
- `source/LGTV/payload.py`, exposing the existing `hello_data` manifest.
- `tools/lg_ssap_probe.py`, exposing `WS` and `query`.

The repository also has [scripts/lg-ssap-probe.py](../scripts/lg-ssap-probe.py). The active service uses an underscore-named copy. The new client intentionally keeps that established service dependency. A fresh repository checkout alone is not a fully configured TV controller. Do not copy credentials into the repository, silently create pairing, or replace the existing helper during an evidence run.

The public scripts have no default private TV address. Supply `--host` or set `LGTV_HOST` from private configuration. Use `--device` when the existing profile differs from the default model/profile hint. `--root` is optional when the existing configured root can be detected; pass it explicitly when several copies exist.

Run commands from the repository root. Prepare a fresh private output directory:

```bash
CAPTURE_TOOLS="$PWD/scripts/lg-tv"
CAPTURE_ROOT='/path/to/existing/LGWebOSRemote'
CAPTURE_RUN="$PWD/private/lg-tv-captures/manual-001"
CAPTURE_SESSION="$CAPTURE_RUN/session.json"
: "${LGTV_HOST:?Set LGTV_HOST locally from the private TV configuration}"
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --help
python3 -B "$CAPTURE_TOOLS/capture_session.py" --help
```

Keep `CAPTURE_RUN` under ignored `private/` or another verified private location outside the public checkout. Do not place it beside public source files. Do not repurpose `HOME` or `CODEX_HOME`.

## Read-only preflight and app inventory

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" status
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" apps
```

These commands check the existing connection and retrieve current state/inventory; they do not launch apps. The inventory is saved privately in `installed-apps.json`. Compare requested apps with it before launching. The committed target registry is a dated discovery aid, not a promise that an app remains installed, supports the same menus, or accepts a deep link.

The paired TLS connection uses the existing local configuration. Connection setup is retried at most three times for transport errors. An explicit pairing rejection stops immediately. A transport error after a command closes the socket without replaying the command, because the TV may already have applied it. Unreachable does not prove that the TV is asleep.

The client keeps the primary SSAP connection and one validated pointer connection for its lifetime. Later button batches reuse that pointer; failed sends discard it without replay, and client cleanup closes both connections. Reconnection is only considered for a new explicit command.

The image transfer has a separate bounded retry: after one successful `executeOneShot`, a timeout or reset/abort may repeat the HTTP GET once, using the same validated image URI after 0.6 seconds. Both attempts enforce the local TV host and redirect checks. HTTP response errors, connection refusal, invalid images and foreign redirects are not retried. The receipt records `download_attempts`; the SSAP capture and navigation commands are never replayed by this retry.

## Manual observed navigation

Use this mode while a human or assistant inspects screenshots between short batches. Start a session before enabling the display or changing the foreground app:

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" begin --session "$CAPTURE_SESSION"
```

The receipt records initial foreground and display state. `Screen Off` and `Screen Saver` may require temporary display activation. A foreground app ID alone does not prove that the captured image shows the app.

A plan contains an exact installed app ID and one to forty observed steps:

```json
{
  "schema_version": 1,
  "app_slug": "disneyplus",
  "app_id": "com.disney.disneyplus-prod",
  "steps": [
    {"launch": "com.disney.disneyplus-prod", "wait": 12},
    {"capture": "home", "note": "Entry screen, pending visual review."}
  ]
}
```

Save that JSON privately as `entry-plan.json`, then run:

```bash
python3 -B "$CAPTURE_TOOLS/run_plan.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_RUN/entry-plan.json"
```

The step whitelist is `launch`, `keys`, `capture`, or standalone `wait`. Launch and keys can specify a bounded settle `wait`; keys can specify `interval`. Waits are limited to 30 seconds. Unknown fields, different launch targets and unsupported buttons are rejected. `--plan-json` is an alternative input for small literal JSON plans.

The runner requires the same active session and checks foreground before input. It splits button batches after `HOME`, `BACK`, or `ENTER` and checks again before later buttons. This guards the target app; it does not prove focus or the meaning of a selected control. Inspect the image before choosing `ENTER`. Do not use a speculative button sequence around play, purchase, subscription, sign-out, profile editing or setting toggles.

Launching can resume a previous page. A fixed wait is not evidence that a home screen loaded. Captures begin as `unreviewed`, regardless of the requested filename/view.

The runner leaves session ownership with the audit controller. Finish even after a failed step:

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" end --session "$CAPTURE_SESSION"
```

Verify the receipt's `restored` status and final display/foreground information. Restoration covers the original app and display on/off intent. It does not reconstruct an internal submenu, focus, history or playback position.

## Repeating known plans with owned cleanup

For an already observed collection of plans, prefer the session wrapper. It validates all input plans before TV actions, owns its new session, and attempts restoration in a cleanup path. It must not take over an existing active session.

```bash
CAPTURE_PLAN="$CAPTURE_RUN/entry-plan.json"
CAPTURE_RUN="$PWD/private/lg-tv-captures/repeat-001"
CAPTURE_SESSION="$CAPTURE_RUN/session.json"
python3 -B "$CAPTURE_TOOLS/capture_session.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_PLAN" --dry-run
python3 -B "$CAPTURE_TOOLS/capture_session.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_PLAN"
```

Use a fresh output run and session path for each execution. An existing receipt is rejected even when its status is `restored`. Repeat `--plan` for additional plans. A dry run is local validation only and does not prove connectivity or hardware behavior. Plans are repeatable instructions, not deterministic UI guarantees: dynamic recommendations, app updates, loading and remembered focus can alter the result.

The separate `lg_tv.py flow` format accepts only reviewed schema-1 replay recipes. Its `--resume` replays navigation from the initial launch and skips only existing capture writes with matching hashes. It does not resume at an arbitrary button position or certify image content. Inspect actual UI before retrying a timed-out mutation.

## Quick entry checkpoint batch

The [versioned repeat kit](../lg-tv-repeat-kit/README.md) supplies one entry plan for each of the 19 requested apps. From the repository root, collect a selected subset in a fresh private run:

```bash
python3 -B lg-tv-repeat-kit/repeat_streaming_entries.py --root "$CAPTURE_ROOT" --output "$PWD/private/lg-tv-captures/entry-001" --apps disneyplus,netflix
```

Add `--dry-run` for local validation; omit `--apps` to select all 19. The launcher uses the canonical session wrapper and its cleanup. An entry checkpoint may show profiles, sign-in, loading or a restored page; it is not confirmed home coverage. The six-view atlas still requires observed navigation and visual review.

## Review, reclassification and atlas

Each image has an adjacent JSON receipt and an append-only `manifest.jsonl` entry. Retain the actual foreground ID, requested view, timezone-aware time, dimensions, SHA-256, display state and explicit capture return status.

Use six review categories: `home`, `settings`, `details`, `recommendations`, `profiles`, and `search`. Verify the pixels, not the intended navigation. A loading screen or sign-in gate is not a home menu. An app can combine categories; document that visibly supported relationship.

Visual review states are `verified`, `incorrect` and `blocked`. Review records may provide `verified_view` to correct a requested category after inspection. The atlas applies that override only when the review is verified and the value is one of the six allowed views. The original capture manifest remains unchanged.

Availability records use `not-installed`, `login-required`, `not-available`, `not-observed`, or `error`. Record uncertainty as `not-observed`; do not conclude that a menu is absent because it was not found.

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --output "$CAPTURE_RUN" review --capture-id CAPTURE_ID --status verified --verified-view profiles --note 'Entry image shows the profile selector, not the requested home view.'
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --output "$CAPTURE_RUN" mark-status --app-slug example --view all --status login-required --note 'Observed sign-in gate; other menus remain inaccessible.'
python3 -B "$CAPTURE_TOOLS/build_atlas.py" --input "$CAPTURE_RUN" --output "$CAPTURE_RUN/atlas" --apps "$CAPTURE_TOOLS/targets.json" --language en
```

Use `--language en` or `--language pl` for atlas headings, view labels and default status explanations. Source observations are preserved as written. For complete bilingual reports, keep separate private notes files and pass `--notes "$CAPTURE_RUN/app-notes.en.json"` or `--notes "$CAPTURE_RUN/app-notes.pl.json"`, with separate output directories. The coverage CSV retains stable machine-readable status codes.

For a smaller request, supply a run-specific filtered targets file. Optional private `app-notes.json` adds per-app summaries, observations and limitations. Keep personal identifiers out of any public summary.

The atlas contains HTML, Markdown, separate app pages, a coverage CSV and a machine-readable summary. Open the HTML and review the matrix before reporting completion. A count of files or successful launches is not a count of verified views. Final menu coverage belongs in the private audit report; this runbook makes no completion claim.

## Failure handling, rollback and tests

Stop after an unexpected app, registration rejection, invalid capture response or changed session identity. Record the observed error and inspect current state. Never reset, re-pair, restart or wake an unreachable TV as an automatic repair.

A partial session startup attempts restoration of its own receipt. Failed restoration leaves `needs_restore`; retain it and retry `end` only after checking connectivity. Do not delete a receipt to make a new run appear clean. Stop only processes owned by this task.

No app package or production service is changed by installing this source. Rollback of the tool change is removal/reversion of these new source files. Operational cleanup is restoration of the owned session, not deletion of evidence.

```bash
python3 -B -m unittest discover -s scripts/lg-tv/tests -v
```

The current public suite passes 68 offline tests, including pointer reuse, cleanup and single-SSAP-call image-transfer retry checks. Hardware observations and their limits are described in the validation section above. Tests use fake devices and temporary files. Public code, plans without private data, runbooks and app IDs may be versioned. Screenshots, profile/account data, original inventories, pairing files, run manifests, action/session logs and embedded-image atlases remain private.
