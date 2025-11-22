"""Image processing tools."""
from __future__ import annotations

import io
import logging
import base64
from typing import Union

from rembg import remove
from PIL import Image

logger = logging.getLogger(__name__)

def remove_background(image_data: Union[str, bytes]) -> str:
    """Remove background from an image.
    
    Args:
        image_data: Base64 encoded string or bytes of the image.
        
    Returns:
        Base64 encoded string of the image with background removed (PNG).
    """
    try:
        # Convert input to bytes if it's a base64 string
        if isinstance(image_data, str):
            # Strip header if present
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]
            input_bytes = base64.b64decode(image_data)
        else:
            input_bytes = image_data
            
        # Process with rembg
        output_bytes = remove(input_bytes)
        
        # Convert back to base64 string
        output_b64 = base64.b64encode(output_bytes).decode("utf-8")
        return output_b64
        
    except Exception as e:
        logger.error(f"Background removal failed: {e}")
        # Return original if failed, or raise? 
        # For now, let's re-raise to handle it in the node
        raise e
