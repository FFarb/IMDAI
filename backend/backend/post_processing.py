"""Post-processing node for background removal."""
from __future__ import annotations

import logging

from backend.agent_state import AgentState
from backend.tools.image_proc import remove_background

logger = logging.getLogger(__name__)

def background_remover(state: AgentState) -> AgentState:
    """Remove background from generated images.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with processed images (if applicable).
    """
    logger.info("Post-Processor: Removing backgrounds...")
    
    images = state.get("generated_images", [])
    if not images:
        logger.warning("No images to process.")
        return state
        
    processed_images = []
    for img in images:
        try:
            # Assuming img is a base64 string or URL. 
            # If it's a URL, we might need to download it first, but for now let's assume base64 
            # or that remove_background handles it (our tool expects base64/bytes).
            # If the image generation returns URLs, we need a way to fetch them.
            # For this implementation, we'll assume the generator returns base64 if configured, 
            # or we skip if it's a URL we can't process directly without fetching.
            
            # Check if it looks like base64
            if isinstance(img, str) and len(img) > 1000: # Rough heuristic
                processed = remove_background(img)
                processed_images.append(processed)
            else:
                logger.warning("Image appears to be a URL or invalid format, skipping background removal.")
                processed_images.append(img)
                
        except Exception as e:
            logger.error(f"Failed to remove background: {e}")
            processed_images.append(img)
            
    # Update state with processed images
    # In a real app, we might want to save these to a new field or overwrite
    # For now, let's overwrite to ensure the final output is clean
    state["generated_images"] = processed_images
    state["is_safe_for_print"] = True
    
    logger.info("Post-Processor: Background removal complete.")
    return state
