"""Image quality heuristics."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter, ImageStat


def evaluate_quality(image: Image.Image) -> tuple[float, bool]:
    """Return a quality score and busy background flag."""
    grayscale = image.convert("L")
    variance = ImageStat.Stat(grayscale).var[0]
    quality_score = max(0.0, min(1.0, variance / 5000.0))

    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.asarray(edges, dtype=np.float32) / 255.0
    busy_score = float(edge_arr.mean()) if edge_arr.size else 0.0
    busy_flag = busy_score > 0.25
    return quality_score, busy_flag
