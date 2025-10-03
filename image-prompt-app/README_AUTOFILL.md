# Autofill Research & One-Click Generation

This document describes the Autofill research workflow for the image prompt app. It covers
backend configuration, API usage, frontend behaviour, and testing guidelines.

## 1. Environment configuration

Create (or update) the backend `.env` file with the following variables:

```
OPENAI_API_KEY=sk-...
RESEARCH_PROVIDER=openai_web        # "openai_web" (Responses API with web tool) or "openai_only"
RESEARCH_TIMEOUT_S=45               # Request timeout in seconds
RESEARCH_MAX_SOURCES=8              # Max sources returned to the client
RESEARCH_AVOID_BRANDS=true          # Force brand filtering even if the request flag is false
RESEARCH_KIDS_SAFE=true             # Enforce kids-safe validation even if the request flag is false
```

### OpenAI web tool access

* The backend uses the official [OpenAI Responses API](https://platform.openai.com/docs/guides/responses)
  with the `web` tool when `RESEARCH_PROVIDER=openai_web` and the incoming flag `use_web` is true.
* If your key does not have access to the web tool the backend automatically retries without it,
  returns a `X-Autofill-Warning: openai_web_unavailable` response header, and logs a warning.
* To force non-web behaviour set `RESEARCH_PROVIDER=openai_only` or disable the flag in the request.

## 2. API endpoints

### `POST /api/autofill/research`

Runs research for a `{topic, audience, age}` triple and returns traits and master prompt data.

**Request body**
```json
{
  "topic": "baby safari minimal",
  "audience": "kids",
  "age": "0–2",
  "flags": {
    "use_web": true,
    "avoid_brands": true,
    "kids_safe": true
  }
}
```

**Response body**
```json
{
  "traits": {
    "palette": [{"hex": "#FFAA00", "weight": 0.18}, ...],
    "motifs": ["cloud", "moon", ...],
    "line_weight": "thin",
    "outline": "clean",
    "typography": ["rounded sans"],
    "composition": ["centered"],
    "audience": "kids",
    "age": "0–2",
    "mood": ["soft"],
    "negative": ["photo-realism", ...],
    "seed_examples": ["floating pastel safari icons", "baby giraffe"],
    "sources": [{"title": "Example", "url": "https://example.com"}]
  },
  "master_prompt_text": "... transparent background, no shadows ...",
  "master_prompt_json": { ... }
}
```

The response always contains the print-ready constraints in the `master_prompt_text` and a
canonical negative list. If the backend fell back to non-web mode the response includes the
`X-Autofill-Warning` header.

### `POST /api/autofill/one_click_generate`

Performs research and then immediately calls the existing `/api/image` endpoint with the
LLM-generated prompt. The `images_n` value controls how many PNGs are requested (default 4).

**Request body**
```json
{
  "topic": "baby safari minimal",
  "audience": "kids",
  "age": "0–2",
  "images_n": 4,
  "flags": {
    "use_web": true,
    "avoid_brands": true,
    "kids_safe": true
  }
}
```

**Response body**
```json
{
  "autofill": { ...same payload as /research... },
  "images": [
    {"image_path": "/images/20240101_0001.png", "prompt": {"positive": "...", ...}},
    {"image_path": "/images/20240101_0002.png", "prompt": {"positive": "...", ...}}
  ]
}
```

The response mirrors the `X-Autofill-Warning` header from the research step.

### Curl examples

```
# Research
curl -X POST http://localhost:8000/api/autofill/research \
  -H "Content-Type: application/json" \
  -d '{
        "topic": "baby safari minimal",
        "audience": "kids",
        "age": "0–2",
        "flags": {"use_web": true, "avoid_brands": true, "kids_safe": true}
      }'

# One-click generate
curl -X POST http://localhost:8000/api/autofill/one_click_generate \
  -H "Content-Type: application/json" \
  -d '{
        "topic": "baby safari minimal",
        "audience": "kids",
        "age": "0–2",
        "images_n": 4,
        "flags": {"use_web": true, "avoid_brands": true, "kids_safe": true}
      }'
```

## 3. Frontend behaviour

* The right sidebar now contains **Traits & Prompt** and **Autofill** tabs.
* The Autofill tab exposes inputs for topic, audience, and age range plus toggles for
  `Use web`, `Avoid brands`, and `Kids-safe` research.
* **Research & Fill** fetches traits, shows the palette, motifs, style metadata, master prompt text,
  JSON payload (collapsible), and source links. Palette chips and prompt blocks offer copy actions.
* **One-Click Generate** triggers research followed by `/api/image`. Generated PNGs are pushed
  to the gallery and listed in the panel. Users receive toast notifications for success, warnings,
  and failures.
* A banner reminds users that the output is an LLM draft and should be reviewed before production use.

## 4. Validation guardrails

Backend validation enforces the following rules:

* Palette: 5–7 unique HEX colours with weights normalised to ~1.0.
* Motifs: 8–12 lowercase generic tags. Brand names and kids-unsafe vocabulary are removed/rejected.
* Typography: up to 3 generic hints, no brand names.
* Composition: must be within the whitelist (`centered`, `single character`, `subtle lattice`,
  `grid`, `minimal frame`).
* Master prompt text must include: `transparent background`, `no shadows`, `no gradients`,
  `no textures`, `clean vector edges`, `centered standalone composition`.
* Mandatory negatives are enforced for both traits and prompt JSON.
* Source links are validated and truncated according to `RESEARCH_MAX_SOURCES`.

If validation fails the API returns `422` with a human-readable message describing the violation.

## 5. Testing

* **Backend**: `pytest` (runs validator, API, and one-click integration tests).
* **Frontend**: `pnpm test -- AutofillPanel` (Vitest + React Testing Library).

Run all tests from the `image-prompt-app/backend` or `frontend` directories respectively.

```
# Backend
cd image-prompt-app/backend
pytest

# Frontend
cd image-prompt-app/frontend
pnpm test -- --runInBand
```

## 6. Screenshots

After starting the frontend (`pnpm dev`) and backend (`uvicorn app:app --reload`), open the app and
capture the **Autofill** tab. Include palette chips, motifs, master prompt, and sources in the
screenshot for documentation or changelog purposes.

## 7. Limitations & notes

* The system relies on the OpenAI Responses API. Rate limits and model availability apply.
* When the web tool is unavailable the research falls back to model-only reasoning which may
  produce less diverse palettes. The warning header allows the UI to surface this to users.
* Brand filtering uses a curated keyword list. Always review the draft traits before publishing.
* Generated PNGs inherit the existing `/api/image` behaviour (DALL·E 3, 1–4 images per request).
* All prompts are designed for print-ready vector stickers: transparent background, no gradients,
  no shadows, no textures, and clean standalone compositions.
