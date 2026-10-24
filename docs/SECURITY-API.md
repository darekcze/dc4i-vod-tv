# API and Security Operations

The user authorized use of TMDB API v3 and a Google Cloud YouTube Data API v3 key. Keep local keys confidential and make TV installation frictionless.

## Sources
- TMDB: account owner at https://www.themoviedb.org/settings/api
- YouTube: Google Cloud project `h0st-pl`, https://console.cloud.google.com/apis/credentials?project=h0st-pl
- Private retained file: `/Volumes/AI-Hot/Services/dc4i-vod-tv/private/youtube_api_key.txt`, mode 0600, no values in Git or Notion.

## Packaging
Current TMDB v3 key is embedded in the client package. Anyone downloading that client binary can extract the key, so monitor quotas and consider migration to a Cloudflare Pages Function with a secret. Do **not** add unrestricted Google credentials to a public IPK.

## YouTube
The key has been recovered and stored. Deployment/binding to protected backend and a successful API health check are pending. The TV application must disable the YouTube Trending row gracefully if that backend is unavailable. YouTube app launch/trailers via TMDB do not require YouTube Data API v3.

## Release policy
A Key's existence does not prove correct API scope or response. Only mark 'YouTube integration complete' after 200 from videos.list in PL region, redacted telemetry and quota-aware backend cache, and after confirming that Git and public IPK contain no raw YouTube credential.
