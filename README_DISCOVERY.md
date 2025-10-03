# Discovery Reference Infrastructure

This document outlines the configuration required to run the discovery pipeline that powers the Reference column.

## Environment variables

Set the following environment variables (or edit `image-prompt-app/backend/.env`) before launching the backend service:

- `OPENVERSE_KEY` – API key for the [Openverse](https://wordpress.org/openverse/) API. Required to query Creative Commons imagery.
- `UNSPLASH_KEY` – Access key for the [Unsplash](https://unsplash.com/developers) API. Required for Unsplash search metadata.
- `GENERIC_SEARCH_KEY` – Token for the generic search provider (e.g., Serp-style APIs). Optional; leave empty to disable the adapter.
- `GENERIC_SEARCH_ENDPOINT` – HTTPS endpoint for the generic provider. Optional; ignored when `GENERIC_SEARCH_KEY` is blank.
- `DISCOVERY_RPS` – Per-adapter requests-per-second guard (default: `3`). Adjust to comply with provider rate limits.

> Tip: copy `.env.example` (if present) to `.env` and fill the values, or export them in your shell before running the backend.

## Backend setup

```bash
cd image-prompt-app/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

The FastAPI application exposes discovery endpoints under `http://127.0.0.1:8000/api/discover`. Refer to `discovery/router.py` for available routes.

## Frontend setup

```bash
cd image-prompt-app/frontend
npm install
npm run dev
```

The Vite dev server (default port `5173`) proxies API calls to the backend. Ensure both servers run concurrently to access the Discovery UI.

## Local uploads

The `/api/discover/{session_id}/local` endpoint accepts multipart uploads. Files are stored under `image-prompt-app/backend/data/discovery/local` and are only used for the active session. Clean up the directory periodically if disk usage grows.

## Troubleshooting

- 429 errors indicate provider rate limits — increase batching intervals or reduce `DISCOVERY_RPS`.
- Empty results often mean missing API keys. Verify the environment variables above.
- Thumbnail normalization stores cached previews under `image-prompt-app/backend/data/discovery/thumbs`.
