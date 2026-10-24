# Instrukcje dla agentów | DC4I VOD TV

1. Najpierw przeczytaj DC4I-BRAND-001 w Notion, PROJECT.md i DELIVERY.md.
2. Do identyfikacji aplikacji używaj neonowego logo DC4I VOD TV zatwierdzonego przez przewodniczącego (assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png). Logo korporacyjne DC4I to osobny zasób. Używaj oryginalnego monogramu D z trzema ścieżkami oraz C z profilem twarzy, nie generuj nowej geometrii. SHA256 źródła 3f8624833ca1eb1609bb42013bfc703d185b59207778afab6802a0723a5e8771.
3. Obowiązuje nowy identyfikator `com.dc4i.vodtv` od wersji 1.2.0, stary `com.dc4i.boringtv` dotyczy tylko archiwalnych wydań. Odinstalowanie i ponowna instalacja są zatwierdzone.
4. Nigdy nie publikuj kluczy API w Git, Notion i logach. Plik YouTube na AI-Hot w `private/`; nie dodawaj nieograniczonych kluczy Google do publicznego pakietu.
5. Uruchom `python3 build_vod_tv.py`, wykonaj pakietowanie webOS CLI, `python3 test_vod_tv.py`, `python3 publish_vod_tv.py`.
6. Nie pokazuj w UI martwych kontrolek wymagających roota. Weryfikuj PL/EN, miasta Europy i USA, pilot, rzeczywistą instalację.
7. Repo publiczne, baza wiedzy Notion, dokumentacja techniczna po angielsku i kompletna polska kopia w docs/pl. Działaj na istniejącym AIOS, bez dodatkowych kolejnych schedulerów.
