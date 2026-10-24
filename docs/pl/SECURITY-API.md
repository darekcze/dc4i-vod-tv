# Bezpieczeństwo integracji API

TMDB v3: konto właściciela w themoviedb.org/settings/api. Poprzedni klucz klienta jest wbudowany do pakietu, z którego może być odczytany. Monitorować zużycie i docelowo przenieść do backendu.

Google YouTube Data API v3: klucz wygenerowany w projekcie `h0st-pl` i odczytany z Chrome na Mac Pro. Zapisany trwale tylko w `/Volumes/AI-Hot/Services/dc4i-vod-tv/private/youtube_api_key.txt` (chmod 600). Nie umieszczać go w Notion, Git ani publicznym IPK.

YouTube Trending pozostaje funkcją opcjonalną, dopóki klucz nie zostanie podłączony do chronionego backendu i nie przejdzie testu API z limitem zapytań. Zwiastuny TMDB i otwieranie YouTube mogą działać bez Data API.
