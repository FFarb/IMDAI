# IMDAI Multi-Agent System

This document describes the new multi-agent architecture for IMDAI.

## Architecture Overview

The system has been refactored from a linear pipeline to an **Event-Driven Multi-Agent System** using LangGraph.

### Agent Swarm

1. **Agent-Vision (The Eye)** - Analyzes uploaded reference images using GPT-4o Vision
2. **Agent-Historian (The Memory)** - Retrieves similar historical prompts using RAG (ChromaDB)
3. **Agent-Analyst (The Brain)** - Synthesizes all inputs into a master strategy
4. **Agent-Promptsmith (The Creator)** - Generates image prompts based on strategy
5. **Agent-Critic (Quality Control)** - Reviews prompts and triggers refinement loops

### Workflow

```
START → Vision → Historian → Analyst → Promptsmith → Critic → [Decision]
                                                          ↓
                                                    [score >= 7?]
                                                     ↙        ↘
                                                  YES         NO
                                                   ↓           ↓
                                                  END    → Promptsmith (loop)
```

The Critic agent scores prompts 0-10. If score < 7, it loops back to Promptsmith with feedback (max 3 iterations).

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies:
- `langgraph` - State graph orchestration
- `langchain-openai` - OpenAI integration
- `langchain-core` - Core abstractions
- `chromadb` - Vector database for RAG
- `pillow` - Image processing

### 2. Seed the Vector Database

The Historian agent requires a seeded ChromaDB database:

```bash
cd backend
python seed_db.py
```

This will:
- Create a ChromaDB collection at `backend/.chromadb/`
- Embed all presets from `presets.json`
- Enable semantic search for similar styles

### 3. Start the Backend

```bash
cd backend
uvicorn backend.app:app --reload
```

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Usage

### Legacy Pipeline (Backward Compatible)

```typescript
const response = await generatePipeline({
  topic: "A cyberpunk city at night",
  audience: "gamers",
  variants: 2,
  mode: "full"
});
```

### Multi-Agent System

```typescript
const response = await generatePipeline({
  topic: "A cyberpunk city at night",
  audience: "gamers",
  variants: 2,
  mode: "full",
  use_agents: true,  // Enable multi-agent system
  visual_references: [base64Image1, base64Image2],  // Optional
  max_iterations: 3  // Max refinement loops
});
```

### Streaming (Real-time Agent Updates)

```typescript
for await (const event of streamAgentPipeline({
  topic: "A cyberpunk city at night",
  audience: "gamers",
  use_agents: true,
  visual_references: [base64Image]
})) {
  if (event.type === 'agent_step') {
    console.log(`${event.agent_name}: ${event.data?.message}`);
  }
}
```

## Response Format

### Multi-Agent Response

```json
{
  "agent_system": {
    "vision_analysis": "...",
    "style_context": [...],
    "master_strategy": "...",
    "critique_score": 8.5,
    "iteration_count": 1
  },
  "prompts": [
    {
      "positive": "...",
      "negative": [...],
      "notes": "..."
    }
  ],
  "images": [[...]]
}
```

## Key Features

### 1. Vision Analysis
Upload reference images to guide generation. Agent-Vision extracts:
- Lighting direction and quality
- Composition and framing
- Mood and atmosphere
- Color palette
- Artistic style

### 2. RAG-Powered Style Retrieval
Agent-Historian searches the vector database for similar successful prompts, providing historical context.

### 3. Quality Refinement Loop
Agent-Critic reviews prompts before image generation. Low-quality prompts trigger automatic refinement with specific feedback.

### 4. Real-time Streaming
Watch agents collaborate in real-time via Server-Sent Events. See what each agent is thinking and doing.

## File Structure

```
backend/
├── backend/
│   ├── agent_state.py          # Shared state schema
│   ├── rag.py                  # ChromaDB RAG implementation
│   ├── graph.py                # LangGraph workflow
│   ├── generate.py             # API endpoints (legacy + agents)
│   └── agents/
│       ├── vision_agent.py
│       ├── historian_agent.py
│       ├── analyst_agent.py
│       ├── promptsmith_agent.py
│       └── critic_agent.py
├── seed_db.py                  # Database seeder script
└── .chromadb/                  # Vector database storage

frontend/
├── src/
│   ├── api/
│   │   └── generate.ts         # API client with streaming
│   └── types/
│       └── pipeline.ts         # TypeScript types
```

## Configuration

### Environment Variables

Ensure `OPENAI_API_KEY` is set in `backend/.env`:

```
OPENAI_API_KEY=sk-...
```

### Agent Parameters

Adjust in `backend/backend/graph.py`:
- `max_iterations` - Maximum refinement loops (default: 3)
- Critic approval threshold - Score >= 7.0 (configurable in `graph.py`)

## Troubleshooting

### "Vector store is empty"
Run `python backend/seed_db.py` to populate the database.

### "Streaming requires use_agents=true"
Streaming only works with the multi-agent system. Set `use_agents: true` in the request.

### ChromaDB errors
Delete `backend/.chromadb/` and re-run `seed_db.py`.

## Next Steps

- [ ] Add frontend UI for image upload
- [ ] Add "Thought Chain" visualization
- [ ] Add "Refine" button for manual refinement
- [ ] Expand preset database with more styles
- [ ] Add agent performance metrics
