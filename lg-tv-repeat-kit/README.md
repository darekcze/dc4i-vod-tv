# Repeat streaming entry checkpoints

[Polski](README.pl.md)

This versioned kit quickly launches selected installed apps and records one entry checkpoint per app using the canonical `capture_session.py`. It contains 19 exact app mappings and one plan per app.

**An entry checkpoint is not a verified home menu.** It may show a profile selector, sign-in gate, loading screen, error, or a restored page. The plan requests the `home` category as an initial filing label; the image remains `unreviewed` until inspected. Use a verified review and, when appropriate, `--verified-view` to classify what is visible.

The kit does not collect all six menu categories automatically. Full home/settings/details/recommendations/profiles/search documentation still requires the installed skill, observed navigation, and visual review. No credentials are bundled and no pairing is created.

## Requirements and files

Use the existing configured TV controller, Python 3.9 or newer, and the matching canonical directory containing `capture_session.py`, `lg_tv.py` and `run_plan.py`. The wrapper retains its existing pairing and helper dependencies.

- `repeat_streaming_entries.py`: thin launcher, with no TV client of its own.
- `targets.json`: exact 19-app registry from the observed inventory.
- `plans/<slug>.json`: launch, wait 12 seconds, capture an unreviewed entry checkpoint.

Keep generated evidence in ignored `private/` or another verified private location outside the repository. The source and nonsecret app plans may be versioned. Use one TV controller. Recheck the installed inventory before a repeat; a dated ID mapping does not prove present availability.

## Preview without contacting the TV

`--tools` defaults to `../scripts/lg-tv` relative to this kit. Pass it explicitly if your layout differs. Run the examples from the `lg-tv-repeat-kit` directory, or invoke the launcher by its full path. See the [capture runbook](../docs/LG-TV-CAPTURE.md) for setup and review.

```bash
python3 -B repeat_streaming_entries.py \
  --tools /path/to/dc4i-vod-tv/scripts/lg-tv \
  --output /private/path/entry-check-001 \
  --apps disneyplus,netflix \
  --dry-run
```

The launcher passes `--dry-run` to the wrapper, which validates the selected plans without reading pairing configuration, contacting the TV or creating the output/session. A dry run does not establish hardware readiness. Omit `--apps` to validate all 19 plans.

## Run a new collection

Set `LGTV_HOST` locally from private configuration, or pass `--host`. Use a new output path for every execution, including after a successful restored session.

```bash
python3 -B repeat_streaming_entries.py \
  --tools /path/to/dc4i-vod-tv/scripts/lg-tv \
  --root /path/to/existing/LGWebOSRemote \
  --device LG_OLED55G42LW \
  --output /private/path/entry-check-001 \
  --apps disneyplus,netflix
```

Omit `--root` only when the wrapper can detect the correct existing configuration. Omit `--apps` for all apps. Available exact slugs are:

`disneyplus,netflix,hbomax,appletv,player,stremio,iptvsmartersplayer,smartiptv,primevideo,youtube,viki,pilot,skyshowtime,canalplus,megogo,cda,sweettv,rakutentv,lgchannels`

The launcher rejects unknown or repeated slugs and existing output directories. It reserves the new run directory and executes the wrapper with a new `RUN/session.json` and repeated `--plan` arguments. It does not adopt an old session or retry failed mutations. The wrapper owns restoration and preserves its session identity checks, foreground checks, local lock and cleanup rules.

## Review and retry

Inspect the images and the wrapper's `session-runs/` summary. Confirm the session receipt reports restoration. A successful file write alone is not proof of the intended menu, and a 12-second wait may be insufficient for an app to load.

If a plan fails, the wrapper stops the run and attempts owned-session restoration. Keep the failed run and inspect the actual TV and receipt state before retrying. Use a new output directory and `--apps` for the affected subset. Do not bypass a `needs_restore` receipt or a changed session identity.

The original capture manifest remains intact. Apply reviews with the canonical client's `review` command, then generate a private atlas with `build_atlas.py`. Use `--language en` or `--language pl` and language-specific notes as needed.

This launcher is **NOT VERIFIED ON HARDWARE** until its own authorized run succeeds. Offline validation verifies plan wiring and argument handling only.
