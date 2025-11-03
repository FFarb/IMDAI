# IMDAI Image Prompt App

A focused workspace for turning a single brief into sellable vector prompt ideas and ready-to-render image outputs. The app runs a three-stage pipeline – **Research → Synthesis → Images** – powered by OpenAI's Responses and Images APIs.

## What Changed

- One-click pipeline that captures research insights, assembles up to five prompt variants, and renders images for each prompt.
- Dedicated modes for **research-only**, **synthesis-only**, or **images-only** reruns without repeating the whole flow.
- Strict JSON contracts enforced through the OpenAI Responses API with `response_format.type="json_schema"`.
- Consistent `input_text` content parts for all Responses API calls and image generation via `gpt-image-1` at `1536x1024`.

## Tech Stack

- **Backend**: FastAPI, Pydantic v2, httpx, python-dotenv, OpenAI SDK ≥ 1.50
- **Frontend**: React, Vite, TypeScript
- **AI Models**: `gpt-4.1-nano` (Responses API with optional `web_search`), `gpt-image-1` (Images API)

## Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key with access to the Responses and Images APIs (`OPENAI_API_KEY`)

## Quick Start

### 1. Configure Environment

The backend reads `OPENAI_API_KEY` from environment variables. Create an `.env` file inside `image-prompt-app/backend/` with:

```bash
OPENAI_API_KEY=sk-your-key-here
```

A sample file is provided as `.env.example` if you prefer to copy it.

### 2. Install Dependencies

#### Cross-platform helpers (Windows batch files included)

At the repository root:

```bash
./setup_env.bat    # Windows
```

For macOS/Linux or manual control:

```bash
cd image-prompt-app/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit OPENAI_API_KEY

cd ../frontend
npm install
```

### 3. Run in Development

From the repository root you can start both servers on Windows with:

```bash
./start_dev.bat
```

Or launch them manually:

```bash
# Backend
cd image-prompt-app/backend
source venv/bin/activate
uvicorn app:app --reload

# Frontend (in a second terminal)
cd image-prompt-app/frontend
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies requests to the FastAPI backend at `http://127.0.0.1:8000`.

## Using the App

1. **Brief** – Set topic, audience, age range, depth (1–5), prompt variants (1–5), and images per prompt (1–4). Click **Generate** for the full pipeline or trigger individual stages.
2. **Research Board** – Inspect fetched references, motifs, palette, typography, mood, hooks, and notes extracted from live search.
3. **Assembled Prompts** – Edit synthesized prompts, adjust negative tags, copy or locally save prompts, and request per-prompt image runs.
4. **Gallery** – Review generated images (URLs or base64 payloads), request variations, regenerate, copy prompts, or download assets.

Errors such as a missing API key return clear 400 responses, and downstream API failures surface as 502s with short explanations. Toast notifications in the UI highlight successes and actionable errors.

## API Overview

- `POST /api/generate` orchestrates every stage. Payload fields:
  - `mode`: `full`, `research_only`, `synthesis_only`, or `images_only`
  - `topic`, `audience`, `age`, `depth`, `variants`, `images_per_prompt`
  - Optional `research` and `synthesis` objects to reuse prior outputs
  - Optional `selected_prompt_index` when `mode="images_only"`
- `GET /api/health` reports service readiness and API key presence.

## Tests

Backend tests ensure the health endpoint works and that `/api/generate` rejects requests when the API key is missing. Run them with:

```bash
cd image-prompt-app/backend
pytest
```

---

With a single click you can now move from market insights to production-ready images, without juggling separate tools or redundant toggles.
