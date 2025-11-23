"""Vectorizer tool for the POD Merch Swarm."""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class Vectorizer:
    """Vectorizes images using Potrace."""

    def __init__(self):
        self.binary = shutil.which("potrace")

    def vectorize(self, input_path: str | Path, output_path: str | Path) -> Path:
        """Vectorize an image to SVG.
        
        Args:
            input_path: Path to input image.
            output_path: Path to save SVG.
            
        Returns:
            Path to the SVG file.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input image not found: {input_path}")
            
        if not self.binary:
            raise RuntimeError("Potrace binary not found. Please install potrace.")
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create a temporary BMP file for potrace
            with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp_bmp:
                tmp_bmp_path = Path(tmp_bmp.name)
                
            # Preprocess image: Grayscale -> Threshold -> Bitmap
            logger.info(f"Preprocessing image for vectorization: {input_path}")
            img = cv2.imread(str(input_path))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            cv2.imwrite(str(tmp_bmp_path), thresh)
            
            # Run potrace
            logger.info(f"Vectorizing using Potrace: {tmp_bmp_path} -> {output_path}")
            subprocess.run(
                [
                    self.binary,
                    str(tmp_bmp_path),
                    "-s",  # SVG backend
                    "-o", str(output_path),
                ],
                check=True,
                capture_output=True
            )
            
            # Cleanup
            if tmp_bmp_path.exists():
                tmp_bmp_path.unlink()
                
            return output_path
            
        except Exception as e:
            logger.error(f"Vectorization failed: {e}")
            # Cleanup
            if 'tmp_bmp_path' in locals() and tmp_bmp_path.exists():
                tmp_bmp_path.unlink()
            raise
