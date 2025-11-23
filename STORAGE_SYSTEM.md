# Two-Tier Storage System Implementation

## Overview
Implemented a two-tier storage system to fix UI crashes and provide better control over what gets saved to the permanent library.

## Architecture

### Tier 1: RAG System (Automatic)
- **Purpose**: Learning and AI improvement
- **Storage**: Database + ChromaDB embeddings
- **Trigger**: Automatic on every generation
- **Location**: `backend/data/pod_swarm.db` + ChromaDB
- **Agent**: `rag_archiver_agent.py`

**What gets stored:**
- Strategy metadata (JSON)
- Generation metadata (prompt, settings, etc.)
- Base64 image data (temporary, in database)
- Embeddings for RAG retrieval

### Tier 2: Library (User-Approved Only)
- **Purpose**: Permanent file storage for approved designs
- **Storage**: Structured file system
- **Trigger**: Explicit user action ("Save to Library" button)
- **Location**: `backend/data/library/{date}/{strategy}/{generation_id}/`
- **Endpoint**: `/api/library/approve`

**What gets stored:**
- `preview.png` - The generated image
- `metadata.json` - Full generation metadata
- `master.png` - Upscaled version (if user upscales)
- `vector.svg` - Vectorized version (if user vectorizes)

## Key Changes

### Backend

1. **New Agent: `rag_archiver_agent.py`**
   - Replaces old `archiver_agent.py` in the workflow
   - Saves all generations to database + RAG automatically
   - Stores base64 images in database metadata (temporary)
   - Does NOT save to file system

2. **Database Model Updates (`store.py`)**
   - Added `metadata_json_str` field to `Generation` model
   - Added `metadata_json` property for easy access
   - Stores temporary data like base64 images before approval

3. **Library API (`library.py`)**
   - New `/api/library/approve` endpoint
   - Moves generation from RAG to permanent file library
   - Decodes base64 image and saves to disk
   - Marks strategy as favorite
   - Updates learning system

4. **Workflow Updates (`graph.py`)**
   - Replaced `archiver_agent` with `rag_archiver_agent`
   - Returns `generation_ids` in response for frontend tracking

### Frontend

1. **Removed Autosave Feature**
   - Deleted autosave UI controls
   - Removed automatic image downloads
   - **Reason**: Prevented localStorage crashes from large base64 data

2. **Added Approval UI (`GalleryGrid.tsx`)**
   - "💾 Save to Library" button for each image
   - Shows saving state and success confirmation
   - Calls `/api/library/approve` endpoint
   - Visual feedback: "Saving..." → "✅ Saved to Library"

3. **Type Updates (`pipeline.ts`)**
   - Added `generation_ids` to `AgentGenerateResponse`
   - Enables tracking which generations can be approved

## User Flow

### Before (Causing Crashes)
1. User generates images
2. System tries to save large base64 images to localStorage
3. **CRASH**: localStorage quota exceeded
4. All images saved to library automatically

### After (Fixed)
1. User generates images
2. Images stored in RAG system (database only)
3. User sees images in gallery with "Save to Library" buttons
4. User clicks button to approve specific images
5. Approved images saved to permanent file library
6. Strategy marked as favorite and indexed for learning

## Benefits

1. **No More Crashes**: Base64 images never touch localStorage
2. **User Control**: Only approved designs go to library
3. **Learning**: All generations indexed for AI improvement
4. **Clean Library**: Only high-quality, user-approved content
5. **Efficient Storage**: Temporary data in DB, permanent data on disk

## API Endpoints

### POST `/api/library/approve`
Approve a generation and save to library.

**Request:**
```json
{
  "generation_id": 1732388421000,
  "action_type": "saved"  // or "upscaled", "vectorized"
}
```

**Response:**
```json
{
  "success": true,
  "generation_id": 1732388421000,
  "folder_path": "C:\\...\\data\\library\\2025-11-23\\strategy-name\\1732388421000",
  "preview_path": "C:\\...\\preview.png"
}
```

### GET `/api/library`
Get library structure for browsing saved items.

## Database Schema

### Generation Model
```python
class Generation(Base):
    id: int  # Unique generation ID
    strategy_id: int  # FK to Strategy
    prompt_text: str  # The prompt used
    image_path: str  # Empty until approved, then file path
    rating: int  # 0-5 stars
    actions_taken: str  # "saved,upscaled,vectorized"
    metadata_json_str: str  # JSON with base64 image + settings
```

## Migration Notes

- Old `archiver_agent.py` still exists for backward compatibility
- New workflow uses `rag_archiver_agent.py`
- Database will auto-create new `metadata_json_str` column on first run
- Existing library files are unaffected
