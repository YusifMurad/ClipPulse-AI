# Reference: REST API

The backend is a Flask app. All responses are JSON unless noted.

Base URL: `http://localhost:5555`

## Health

```
GET /api/health
→ { "status": "ok" }
```

## Settings

```
GET /api/settings
→ { "has_api_key": true, "api_key_masked": "AQ.Ab8...BiGg", "language": "en", ... }
```

```
POST /api/settings
Content-Type: application/json
{ "api_key": "YOUR_KEY", "language": "en", "clip_count": 3 }
```

> The API key is stored server-side in `backend/config/settings.json` and is **never**
> returned in full — only a masked value. `config/` is git-ignored.

## Generate clips (API key auth)

```
POST /api/v1/keys/create
{ "email": "you@example.com", "plan": "free" }
→ { "api_key": "cf_xxxxx" }
```

```
POST /api/v1/generate
Headers: X-API-Key: cf_xxxxx
{ "url": "https://youtube.com/watch?v=xxx", "clip_count": 3 }
```

## Jobs & downloads

- `GET /api/job/<job_id>` — job status / clips list
- `GET /api/download/<job_id>/<filename>` — download an MP4
- `GET /api/thumbnail/<job_id>/<filename>` — generated cover JPG
- `POST /api/cleanup` — wipe the output directory
