# IMDAI - POD Merch Swarm (macOS Installation Guide)

A specialized AI system for creating **commercial-ready Print-on-Demand (POD) designs**. Powered by a multi-agent swarm that hunts trends, generates vector-optimized prompts, and auto-processes images for t-shirts, stickers, and merch.

## Key Features

- 🔍 **Trend Hunting** - Agent-Trend searches live market data for winning aesthetics and bestsellers
- 🎨 **POD-Optimized Prompts** - Hardcoded constraints for vector art, white backgrounds, and clean printable designs
- ✂️ **Auto-Background Removal** - Post-processing node strips backgrounds using `rembg` for transparent PNGs
- 🤖 **Multi-Agent Collaboration** - Vision → Trend → Historian → Analyst → Promptsmith → Critic workflow
- 🔄 **Quality Refinement Loop** - Automatic iteration until designs meet commercial standards

## Prerequisites for macOS

- **Python 3.11 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download from nodejs.org](https://nodejs.org/)
- **OpenAI API Key** - Get one from [platform.openai.com](https://platform.openai.com/api-keys)

## Quick Start (macOS)

### 1. Make Scripts Executable

After extracting the zip file, open Terminal and navigate to the project directory:

```bash
cd path/to/IMDAI-expiremental\ version
chmod +x install_mac.sh start_mac.sh
```

### 2. Run Installation

```bash
./install_mac.sh
```

This script will:
- Check for Python 3.11+ and Node.js 18+
- Create a Python virtual environment in `backend/venv`
- Install all Python dependencies
- Install all npm dependencies
- Create a template `.env` file

### 3. Configure Your API Key

Edit the `.env` file in the `backend` directory:

```bash
nano backend/.env
# or use your preferred text editor
```

Replace `your-api-key-here` with your actual OpenAI API key:

```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Save and exit (Ctrl+X, then Y, then Enter if using nano).

### 4. Start the Application

```bash
./start_mac.sh
```

This will start both servers:
- **Frontend**: http://localhost:5173
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

The script will run both servers and display their logs. Press **Ctrl+C** to stop both servers.

## Using the App

1. **Brief** – Set topic, audience, age range, depth (1–5), prompt variants (1–5), and images per prompt (1–4). Click **Generate** for the full pipeline or trigger individual stages.
2. **Research Board** – Inspect fetched references, motifs, palette, typography, mood, hooks, and notes extracted from live search.
3. **Assembled Prompts** – Edit synthesized prompts, adjust negative tags, copy or locally save prompts, and request per-prompt image runs.
4. **Gallery** – Review generated images, request variations, regenerate, copy prompts, or download assets.

## Troubleshooting

### Installation Issues

**Python not found:**
```bash
# Install Python via Homebrew
brew install python@3.11
```

**Node.js not found:**
```bash
# Install Node.js via Homebrew
brew install node
```

**Permission denied when running scripts:**
```bash
chmod +x install_mac.sh start_mac.sh
```

### Runtime Issues

**Backend fails to start:**
- Check `backend.log` for error details
- Ensure your OPENAI_API_KEY is valid
- Make sure port 8000 is not already in use

**Frontend fails to start:**
- Check `frontend.log` for error details
- Make sure port 5173 is not already in use
- Try deleting `frontend/node_modules` and running `./install_mac.sh` again

**API Key errors:**
- Verify your API key is correctly set in `backend/.env`
- Ensure there are no extra spaces or quotes around the key
- Check that your OpenAI account has credits available

### Viewing Logs

Logs are written to the project root directory:
```bash
# View backend logs
tail -f backend.log

# View frontend logs
tail -f frontend.log
```

## Manual Installation (Alternative)

If the automated scripts don't work, you can install manually:

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create and edit .env file
echo "OPENAI_API_KEY=your-key-here" > .env
nano .env  # Edit with your actual key
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Manual Start
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Tech Stack

- **Backend**: FastAPI, Pydantic v2, LangGraph, LangChain
- **Frontend**: React, Vite, TypeScript
- **AI Models**: GPT-4o (chat), DALL-E 3 (image generation)
- **POD Tools**: `duckduckgo-search` (trend hunting), `rembg` (background removal)
- **Vector DB**: ChromaDB (RAG for historical prompts)

## API Overview

- `POST /api/generate` orchestrates every stage. Payload fields:
  - `mode`: `full`, `research_only`, `synthesis_only`, or `images_only`
  - `topic`, `audience`, `age`, `depth`, `variants`, `images_per_prompt`
  - Optional `research` and `synthesis` objects to reuse prior outputs
  - Optional `selected_prompt_index` when `mode="images_only"`
- `GET /api/health` reports service readiness and API key presence

## Storage System

The application uses a two-tier storage system:
- **RAG System**: All generated images are automatically saved for learning
- **Library**: Only user-approved images are saved to the permanent library
- Images are stored in the `data` directory

## Support

For issues or questions, please refer to the documentation files:
- `STORAGE_SYSTEM.md` - Details about the storage architecture
- `README_MULTIAGENT.md` - Multi-agent system documentation
- `PHASE3_SUMMARY.md` - Latest feature updates

---

With a single click you can now move from market insights to production-ready images, without juggling separate tools or redundant toggles.
