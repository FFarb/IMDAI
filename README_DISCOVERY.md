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

## Feature Extractor v1

The discovery backend exposes a synchronous feature extractor used to derive palette, outline, fill, typography, motif and brand-risk signals from selected references.

- Extraction is triggered via `POST /api/discover/{session_id}/analyze` with body `{ "scope": "selected" }` (or `"all"`).
- Features are stored in SQLite (`discovery_features` table) and can be inspected through `GET /api/discover/{session_id}/features`.
- The extractor uses Pillow, NumPy, scikit-image and (optionally) OpenCLIP. Disable CLIP/OCR heuristics via `.env` flags `FEATURES_ENABLE_CLIP=false` and `OCR_ENABLE=false`.
- Palettes are returned as 6 HEX chips with normalized weights, outline metrics are normalized to `[0, 1]`, typography provides presence + coarse style, and motifs resolve to a curated vocabulary.

## Traits & Aggregation

Aggregated dataset traits are built from the analyzed feature set and respect reference star weights (★ → 1.5/2.0 multipliers).

- Invoke `GET /api/discover/{session_id}/traits` after running analysis; traits are persisted (`discovery_traits` table) and reused by the prompt autofill endpoint.
- Palettes are mode-filtered to 6 persistent colors. Motifs are TF-IDF ranked (≤ 12 entries) while discarding references with `brand_risk > 0.6`.
- Line weights and outlines are trimmed medians mapped to `thin/regular/bold` and `clean/rough`. Typography and composition hints surface only when supported by ≥30% of weighted references.
- Changing the selected set or star weights should mark traits as stale in the UI; re-run `/analyze` to refresh.

## Master Prompt Autofill

`POST /api/prompt/autofill` uses stored traits plus audience mode sliders to assemble a print-ready master prompt.

- Request shape: `{ "session_id": "…", "audience_modes": ["Baby"], "trait_weights": { "palette": 1.5, "motifs": 1.2, "line": 1.0, "type": 0.8, "comp": 1.0 } }`.
- Response contains `prompt_text` (guarded with transparent background / negative constraints) and `prompt_json` (structured payload consumed downstream).
- Audience modes enrich the mood line, trait weights adjust emphasis descriptors (e.g., balanced vs. strong focus on palette).
- The UI provides sliders and checkboxes to tweak these settings; mutations display a "Re-Autofill Prompt" banner until autofill is run again.

## How to test (unit/integration/UI/manual)

### Automated

- **Backend unit tests**: `pytest image-prompt-app/backend/tests/test_palette.py ...` (palette, outline, fill, typography, motifs, brand risk) target critical feature primitives with synthetic fixtures; coverage for `features.py` ≥ 70%.
- **Backend integration**: `pytest image-prompt-app/backend/tests/test_api_features_traits.py` provisions a session, uploads local references, runs `/analyze`, `/traits`, and `/api/prompt/autofill`, and asserts 200s plus guard-rail behaviour.
- **Frontend unit/smoke**: `npm run test` executes Vitest suites including `ReferenceSelectedList`, `TraitsPreview`, and `MasterPromptCard` components.

### Manual QA checklist

1. Launch backend (`uvicorn app:app --reload`) and frontend (`npm run dev`).
2. Search "baby safari minimal", select ≥8 references, apply ★★ to a subset.
3. Click **Analyze Selected** → verify progress banner and that Traits preview refreshes to 6 colors + 8–12 motifs + line/outline + typography/composition hints.
4. Toggle `Baby` and `Luxury-Inspired`, adjust trait weight sliders, click **Autofill Master Prompt**; confirm text/json outputs align with guard phrases.
5. Modify selection (add/remove/retoggle ★) → ensure "Traits outdated → Re-Analyze" banner appears, rerun analysis and observe updated traits.
6. Trigger generation (if available) and verify outputs maintain transparent background and lack gradients/shadows.
7. With `FEATURES_ENABLE_CLIP=false` and `OCR_ENABLE=false`, rerun analyze/autofill and check logs for absence of CLIP/OCR errors.
