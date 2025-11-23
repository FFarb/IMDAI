"""Upscaler tool for the POD Merch Swarm."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class Upscaler:
    """Upscales images using RealESRGAN or PIL fallback."""

    def __init__(self):
        self.binary = shutil.which("realesrgan-ncnn-vulkan") or shutil.which("realesrgan")

    def upscale(self, input_path: str | Path, output_path: str | Path, scale: int = 4) -> Path:
        """Upscale an image.
        
        Args:
            input_path: Path to input image.
            output_path: Path to save upscaled image.
            scale: Upscaling factor (default: 4).
            
        Returns:
            Path to the upscaled image.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input image not found: {input_path}")
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.binary:
            try:
                logger.info(f"Upscaling using RealESRGAN: {input_path} -> {output_path}")
                subprocess.run(
                    [
                        self.binary,
                        "-i", str(input_path),
                        "-o", str(output_path),
                        "-s", str(scale),
                    ],
                    check=True,
                    capture_output=True
                )
                return output_path
            except subprocess.CalledProcessError as e:
                logger.warning(f"RealESRGAN failed: {e}. Falling back to PIL.")
        else:
            logger.warning("RealESRGAN binary not found. Using PIL fallback.")
            
        # Fallback to PIL
        try:
            with Image.open(input_path) as img:
                # Calculate new size
                new_size = (img.width * scale, img.height * scale)
                
                # Resize using LANCZOS
                upscaled = img.resize(new_size, resample=Image.Resampling.LANCZOS)
                
                # Save
                upscaled.save(output_path)
                logger.info(f"Upscaled using PIL: {input_path} -> {output_path}")
                
                return output_path
        except Exception as e:
            logger.error(f"PIL upscaling failed: {e}")
            raise
