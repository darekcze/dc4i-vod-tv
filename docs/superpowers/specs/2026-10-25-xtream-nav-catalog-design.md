# DC4I VODTV 1.2.16: navigation, Xtream search, persistence

User-approved main navigation: VOD | TV | IPTV | Filmy | Seriale | Szukaj | Aplikacje.
VOD is former Dla Ciebie recommendations. TV opens native webOS live TV. IPTV browses the user-configured Xtream playlist. Filmy and Seriale select corresponding Xtream catalog categories. Szukaj contains filters Wszystkie, VOD, TV, IPTV, Filmy, Seriale.

Search language selection: Polskie, Angielskie, Wszystkie języki. Default PL. Xtream language is inferred from [PL]/[POL] or [EN]/[ENG]/[UK]/[US]/[AU] in title/category names. Netflix/Prime regional VOD availability is independent of original production language. Exact match for languages outside known tags is not claimed.

Playlist credentials remain under existing per-profile application localStorage key dc4iXtreamPlaylistsV1, mirrored to dc4iXtreamAccountsBackupV1. Xtream catalog content can also be locally cached in IndexedDB (dc4i-vodtv-user-catalog-v1). Keep same com.dc4i.vodtv app ID and update in place, never uninstall, preserving the webOS origin storage. Deleting app data or uninstalling can still remove both local copies. No credentials or playlist data in IPK/repo.

EPG full-text indexing is separate future work; live Xtream channels are searchable now. Codec/provider streaming capability remains outside the app's control.

Verification: six search filter checks, seven menu labels, local PL/EN mock catalog results, 1920x1080 menu bounding boxes, package contents and public SHA-256 after deployment.
