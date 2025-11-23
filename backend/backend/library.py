"""Library endpoints for the POD Merch Swarm."""
from __future__ import annotations

import base64
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.store import Generation, get_db
from backend.services.learning import LearningService
from backend.utils.files import FileManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/library", tags=["library"])


class ActionRequest(BaseModel):
    """Request to mark a generation as successful."""
    generation_id: int
    action_type: str  # "upscaled", "vectorized", "saved"


class ApproveRequest(BaseModel):
    """Request to approve a generation and save it to library."""
    generation_id: int
    action_type: str = "saved"  # "saved", "upscaled", "vectorized"


@router.get("")
def get_library() -> dict[str, Any]:
    """Get the structured library of generated assets."""
    try:
        structure = FileManager.get_library_structure()
        return {"data": structure}
    except Exception as e:
        logger.error(f"Failed to get library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
def mark_action(req: ActionRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Mark a generation as successful based on user action."""
    try:
        success = LearningService.mark_success(req.generation_id, req.action_type, db)
        if not success:
            raise HTTPException(status_code=404, detail="Generation not found")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Failed to mark action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
def approve_generation(req: ApproveRequest, db: Session = Depends(get_db)) -> dict:
    """Approve a generation and save it to the file library.
    
    This moves the generation from RAG-only storage to the permanent library.
    """
    try:
        # Get generation from database
        generation = db.query(Generation).filter(Generation.id == req.generation_id).first()
        if not generation:
            raise HTTPException(status_code=404, detail=f"Generation {req.generation_id} not found")
        
        # Get metadata which contains the base64 image
        metadata = generation.metadata_json
        if not metadata or "image_b64" not in metadata:
            raise HTTPException(status_code=400, detail="Generation has no image data")
        
        # Get strategy info
        strategy = generation.strategy
        if not strategy:
            raise HTTPException(status_code=400, detail="Generation has no associated strategy")
        
        strategy_data = strategy.get_data()
        strategy_name = strategy.name
        
        # Create folder structure for this generation
        folder_path = FileManager.create_generation_folder(strategy_name, req.generation_id)
        
        # Save preview image (decode base64)
        preview_path = folder_path / "preview.png"
        try:
            img_bytes = base64.b64decode(metadata["image_b64"])
            with open(preview_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            logger.error(f"Failed to save preview image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
        
        # Update generation record with file path
        generation.image_path = str(preview_path)
        
        # Save metadata file
        file_metadata = {
            "strategy_id": strategy.id,
            "generation_id": req.generation_id,
            "prompt": generation.prompt_text,
            "timestamp": metadata.get("timestamp"),
            "settings": metadata.get("settings", {}),
            "user_brief": metadata.get("user_brief"),
            "strategy": strategy_data,
        }
        FileManager.save_assets(folder_path, None, file_metadata)
        
        # Mark as success in learning system (this also indexes to RAG if not already)
        LearningService.mark_success(req.generation_id, req.action_type, db)
        
        logger.info(f"Approved generation {req.generation_id} and saved to library at {folder_path}")
        
        return {
            "success": True,
            "generation_id": req.generation_id,
            "folder_path": str(folder_path),
            "preview_path": str(preview_path),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve generation: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
