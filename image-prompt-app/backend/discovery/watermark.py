"""Simple watermark heuristics."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def detect_watermark(image: Image.Image) -> bool:
    """Detect potential watermark by analyzing edge activity on borders."""
    grayscale = image.convert("L")
    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.asarray(edges, dtype=np.float32) / 255.0
    height, width = edge_arr.shape
    border = max(2, int(min(height, width) * 0.15))
    if border * 2 >= min(height, width):
        return False

    top = edge_arr[:border, :]
    bottom = edge_arr[-border:, :]
    left = edge_arr[:, :border]
    right = edge_arr[:, -border:]
    border_activity = np.concatenate([top.flatten(), bottom.flatten(), left.flatten(), right.flatten()])
    center = edge_arr[border:-border, border:-border]
    center_activity = center.mean() if center.size else 0.0
    border_mean = border_activity.mean() if border_activity.size else 0.0
    return border_mean > center_activity * 1.4 and border_mean > 0.12
