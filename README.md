# LG Homebrew Repository (darc.dev)

Custom Homebrew Channel catalog including [TheBoringTV](https://github.com/theboringhumane/theboringtv-lgwebos).

Add `https://lg.darc.dev/` as a repository in Homebrew Channel. Direct manifest: `https://lg.darc.dev/api/apps.json`.

## Packaging and limitations
Current app version: 0.25.0. SHA256: `e6202f08692ca273cc233e0b119df9a3403674261ce7effc75dbc72473ad7e68`.
The .ipk was built from the upstream source without including personal API keys. TMDB and YouTube features require user configuration; consult upstream README. Normal app use does not require root, replacing the LG home screen does.

Files: `api/apps.json`, `manifests/`, `packages/`, `icons/`. Regenerate metadata with `python3 generate.py`.
This is an unofficial third-party build. Test on your TV at your own risk.
