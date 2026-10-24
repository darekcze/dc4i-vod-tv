# Solution Vision

A branded, TV-first cross-streaming launcher/discovery application for LG webOS, with one Homebrew catalog URL and no TV-side key entry.

## Architecture
1. Upstream TheBoringTV checkout pinned by source SHA in the local workspace.
2. A reproducible corporate build layer constructs DC4I appinfo, UI strings, verified icon/splash derivatives from exact source, PL/EN, weather cities and root feature gates.
3. TMDB provides regional content metadata, ratings, watch providers and trailers. Continue-watching and watchlist stay local to the TV (per profile).
4. YouTube Trending optional. Only activate after API key is deployed safely to a server backend and tested, without embedding Google credentials in a public IPK.
5. Homebrew-compatible root JSON + versioned IPK with SHA256 at `lg.darc.dev`.

## Key quality criteria
- The app launches on a Developer Mode TV and does not pretend it can replace system Home.
- Navigation using arrows, Enter, Back and Magic Remote pointer has no hidden-root dead controls.
- Language switching updates UI and TMDB locale after reload.
- Exact official icon silhouette remains invariant. Snapshot visual tests cover 80/130/512 and 1920x1080.
- Every published catalogue hash and download URL matches binary, no leaked keys in Git.
- Key failures degrade gracefully without a missing-key blocking screen.

## Future iterations
Secure YouTube API, improved service matching for Poland, real-TV E2E validation and richer ratings/availability provenance.
