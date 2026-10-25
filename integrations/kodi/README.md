# DC4I Kodi Title Handoff

The local Kodi service `service.dc4i.handoff` v0.1.2 is installed on the owner's LG webOS TV. It indexes movies and series from their authorized XCUI/Xtream catalog. The actual private index (`catalog.json`) and access credentials are **not included in this repository**.

- `service.py`: accepts TMDB-ID launches, local JSON-RPC requests, and title-only searches from the VODTV application.
- `catalog_search.py`: diacritic-insensitive search across configured movie/series names. Opens a Kodi-native selection dialog, then dispatches the selected item to the configured XCUI player.
- `tests/test_catalog_search.py`: offline search matching tests.

To package locally, create `service.dc4i.handoff-X.Y.Z.zip` with addon.xml, service.py, catalog_search.py and the **locally built private catalog.json** under `service.dc4i.handoff/`. Install using Kodi's Install from zip file, then disable unknown sources again. Never distribute the generated private catalog or user credentials. The service listens only on `127.0.0.1:18761` on Kodi's own host.

Native app-manager launch params: `{dc4i:{action:'search',title:'...'}}` for text search and `{dc4i:{type:'movie',tmdb:'603',title:'...'}}` for exact title playback. A webOS app may not be able to hold Kodi and VODTV running simultaneously, hence Kodi's startup parameter path is supported.

Only legally accessed data sources configured by the user are used. Direct playback remains dependent on the provider and its permissions.
