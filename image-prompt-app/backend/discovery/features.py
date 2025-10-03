"""Feature extraction primitives for discovery references."""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from functools import lru_cache
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from PIL import Image
from skimage import feature as skfeature
from skimage import filters, measure, morphology

from .models import CompositionFeature, Feature, PaletteColor, TypographyFeature

_FEATURES_ENABLE_CLIP = os.getenv("FEATURES_ENABLE_CLIP", "false").lower() == "true"
_OCR_ENABLE = os.getenv("OCR_ENABLE", "false").lower() == "true"

_CURATED_MOTIF_VOCAB: Tuple[str, ...] = (
    "animals",
    "clouds",
    "stars",
    "hearts",
    "bows",
    "cars",
    "flowers",
    "butterflies",
    "rainbows",
    "sparkles",
    "planets",
    "moons",
    "suns",
    "crowns",
    "fruits",
    "balloons",
    "leaves",
    "abstract-shapes",
    "geometric",
    "pastel",
    "vibrant",
    "cool-tones",
    "warm-tones",
    "neutral",
    "monochrome",
    "minimal",
    "playful",
    "luxury",
)

_BRAND_KEYWORDS = {
    "disney",
    "marvel",
    "pixar",
    "nike",
    "adidas",
    "lego",
    "starbucks",
    "coca",
    "coke",
    "cocacola",
    "apple",
    "google",
    "facebook",
    "instagram",
    "hello",
    "kitty",
    "pokemon",
    "harry",
    "potter",
    "batman",
    "superman",
    "dc",
    "minecraft",
    "fortnite",
    "barbie",
}

@lru_cache(maxsize=1)
def _rng() -> np.random.Generator:
    """Shared random generator for deterministic palette extraction."""

    return np.random.default_rng(42)


def _image_to_array(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    return arr.reshape(-1, 3)


def _rgb_to_hex(rgb: Sequence[float]) -> str:
    rgb_clamped = np.clip(np.asarray(rgb), 0.0, 1.0)
    return "#" + "".join(f"{int(round(channel * 255)):02X}" for channel in rgb_clamped)


def _hex_to_rgb(hex_value: str) -> np.ndarray:
    value = hex_value.lstrip("#")
    return np.array([int(value[i : i + 2], 16) for i in range(0, 6, 2)], dtype=np.float32) / 255.0


def _kmeans(points: np.ndarray, k: int, sample_weights: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Lightweight weighted k-means implementation for palette clustering."""

    if len(points) < k:
        k = max(1, len(points))
    rng = _rng()
    initial_idx = rng.choice(len(points), size=k, replace=False, p=sample_weights / sample_weights.sum())
    centers = points[initial_idx]
    for _ in range(12):
        distances = np.linalg.norm(points[:, None, :] - centers[None, :, :], axis=2)
        labels = np.argmin(distances, axis=1)
        new_centers = centers.copy()
        for idx in range(k):
            mask = labels == idx
            if not np.any(mask):
                new_centers[idx] = centers[idx]
                continue
            weight_slice = sample_weights[mask]
            weighted_points = points[mask] * weight_slice[:, None]
            new_centers[idx] = weighted_points.sum(axis=0) / (weight_slice.sum() + 1e-8)
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    cluster_weights = np.zeros(k)
    for idx in range(k):
        mask = labels == idx
        if not np.any(mask):
            continue
        cluster_weights[idx] = sample_weights[mask].sum()
    cluster_weights /= cluster_weights.sum() if cluster_weights.sum() else 1.0
    return centers, cluster_weights


def extract_palette(image: Image.Image, k: int = 6) -> List[PaletteColor]:
    """Extract a dominant color palette using weighted k-means."""

    pixels = _image_to_array(image)
    if pixels.size == 0:
        return [PaletteColor(hex="#000000", weight=1.0)]
    # Weight darker and mid-tone pixels slightly higher to avoid blown highlights dominating
    luminance = pixels @ np.array([0.299, 0.587, 0.114])
    weights = np.clip(1.0 - np.abs(luminance - 0.5), 0.35, 1.0)
    centers, cluster_weights = _kmeans(pixels, k, weights)
    palette = [
        PaletteColor(hex=_rgb_to_hex(color), weight=float(weight))
        for color, weight in zip(centers, cluster_weights)
    ]
    palette.sort(key=lambda item: item.weight, reverse=True)
    # Enforce 5-7 entries by trimming minor clusters or splitting dominant ones
    if len(palette) > 7:
        palette = palette[:7]
    elif len(palette) < 5:
        while len(palette) < 5 and palette:
            duplicated = PaletteColor(hex=palette[len(palette) - 1].hex, weight=palette[len(palette) - 1].weight * 0.5)
            palette.append(duplicated)
    total = sum(item.weight for item in palette)
    if total == 0:
        total = 1.0
    normalized = [PaletteColor(hex=item.hex, weight=item.weight / total) for item in palette]
    return normalized


def measure_outline(image: Image.Image) -> Tuple[float, float]:
    """Return a heuristic outline thickness and clarity score."""

    gray = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    edges = skfeature.canny(gray, sigma=1.0)
    dilated = morphology.binary_dilation(edges, morphology.disk(2))
    # Estimate line weight via density of dilated edge pixels
    line_weight = float(np.clip(dilated.mean() * 1.6, 0.0, 1.0))
    closed = morphology.binary_closing(edges, morphology.disk(1))
    discontinuity = np.logical_xor(closed, edges)
    noise = morphology.binary_opening(edges, morphology.disk(1))
    clarity = 1.0 - min(1.0, (discontinuity.mean() * 4.0) + (noise.mean() * 1.5))
    clarity = float(np.clip(clarity, 0.0, 1.0))
    return line_weight, clarity


def measure_fill_ratio(image: Image.Image) -> float:
    """Calculate filled area ratio using Otsu thresholding."""

    gray = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    if gray.std() < 1e-3:
        return 0.0
    threshold = filters.threshold_otsu(gray)
    darker = gray < threshold
    lighter = gray >= threshold
    # Choose the mask with higher contrast coverage as fill
    dark_ratio = darker.mean()
    light_ratio = lighter.mean()
    ratio = dark_ratio if dark_ratio > light_ratio else light_ratio
    return float(np.clip(ratio, 0.0, 1.0))


def _detect_text_regions(gray: np.ndarray) -> List[measure.RegionProperties]:
    blurred = filters.gaussian(gray, sigma=1.0)
    threshold = filters.threshold_otsu(blurred)
    binary = blurred < threshold
    binary = morphology.remove_small_objects(binary, min_size=30)
    labeled = measure.label(binary.astype(int))
    regions: List[measure.RegionProperties] = []
    for region in measure.regionprops(labeled):
        area_ratio = region.area / binary.size
        if area_ratio < 0.0005 or area_ratio > 0.15:
            continue
        aspect = region.major_axis_length / max(region.minor_axis_length, 1.0)
        if aspect < 1.3 and region.eccentricity < 0.2:
            continue
        regions.append(region)
    return regions


def detect_typography(image: Image.Image) -> TypographyFeature:
    """Identify whether typography exists and provide a coarse style hint."""

    gray = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    regions = _detect_text_regions(gray)
    if not regions:
        heuristic = TypographyFeature(present=False, style=None)
    else:
        rounded = sum(1 for region in regions if region.eccentricity < 0.6)
        sharp = len(regions) - rounded
        rounded_ratio = rounded / len(regions)
        sharp_ratio = sharp / len(regions)
        if rounded_ratio > 0.6:
            style = "rounded"
        elif sharp_ratio > 0.6:
            style = "block"
        else:
            style = "mixed"
        heuristic = TypographyFeature(present=True, style=style)

    if not _OCR_ENABLE:
        return heuristic

    try:
        import pytesseract  # type: ignore

        text = pytesseract.image_to_string(image)
        if text.strip():
            if heuristic.present:
                return heuristic
            return TypographyFeature(present=True, style="mixed")
    except Exception:
        pass
    return heuristic


def _shape_motifs(mask: np.ndarray) -> Counter:
    counter: Counter = Counter()
    labeled = measure.label(mask.astype(int))
    for region in measure.regionprops(labeled):
        if region.area < 80:
            continue
        circularity = 4 * math.pi * region.area / max(region.perimeter ** 2, 1.0)
        aspect = region.major_axis_length / max(region.minor_axis_length, 1.0)
        convex_ratio = region.area / max(region.convex_area, region.area)
        if circularity > 0.6 and convex_ratio > 0.9 and aspect < 1.3:
            counter["clouds"] += 1
        elif circularity < 0.3 and aspect < 2.0:
            counter["stars"] += 1
        elif convex_ratio > 0.95 and 0.8 < aspect < 1.3 and circularity > 0.45:
            counter["hearts"] += 1
        elif aspect > 2.8:
            counter["bows"] += 1
        elif 1.3 <= aspect <= 3.0 and convex_ratio > 0.8:
            counter["cars"] += 1
    return counter


def detect_motifs(image: Image.Image) -> List[str]:
    """Infer motif tags using simple heuristics with optional CLIP enrichment."""

    arr = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    gray = arr.mean(axis=2)
    motif_counter: Counter = Counter()
    if arr.size == 0:
        return []

    # Color tonality heuristics
    mean_color = arr.reshape(-1, 3).mean(axis=0)
    saturation = np.std(arr.reshape(-1, 3), axis=1).mean()
    if mean_color.mean() > 0.7:
        motif_counter["pastel"] += 2
    if saturation > 0.18:
        motif_counter["vibrant"] += 1
    if mean_color[2] > mean_color[0] + 0.05:
        motif_counter["cool-tones"] += 1
    if mean_color[0] > mean_color[2] + 0.05:
        motif_counter["warm-tones"] += 1
    if abs(mean_color[0] - mean_color[1]) < 0.05 and abs(mean_color[1] - mean_color[2]) < 0.05:
        motif_counter["neutral"] += 1
    if np.std(mean_color) < 0.03:
        motif_counter["monochrome"] += 1

    # Structural motifs via binary masks
    binary = gray < filters.threshold_otsu(gray) if gray.std() > 1e-3 else gray > 0.5
    binary = morphology.binary_dilation(binary, morphology.disk(1))
    motif_counter.update(_shape_motifs(binary))

    # Additional heuristics for playful vs luxury moods
    edge_density = skfeature.canny(gray, sigma=1.0).mean()
    if edge_density > 0.1:
        motif_counter["playful"] += 1
    if edge_density < 0.05 and mean_color.mean() < 0.6:
        motif_counter["luxury"] += 1

    # Clip enrichment placeholder (degrades gracefully when disabled)
    if _FEATURES_ENABLE_CLIP:
        try:
            import open_clip  # type: ignore
            import torch  # type: ignore

            model, preprocess, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
            model.eval()
            with torch.no_grad():
                input_tensor = preprocess(image).unsqueeze(0)
                image_features = model.encode_image(input_tensor)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                texts = open_clip.tokenize(list(_CURATED_MOTIF_VOCAB))
                text_features = model.encode_text(texts)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                logits = (image_features @ text_features.T).softmax(dim=-1)[0]
                for idx, value in enumerate(logits):
                    motif_counter[_CURATED_MOTIF_VOCAB[idx]] += float(value.item())
        except Exception:
            # Fail silently and rely on heuristics
            pass

    ranked = [motif for motif, _ in motif_counter.most_common(12)]
    filtered = [motif for motif in ranked if motif in _CURATED_MOTIF_VOCAB]
    if len(filtered) < 8:
        # pad with neutral tags to satisfy minimum requirement
        for motif in ("minimal", "abstract-shapes", "sparkles", "flowers", "butterflies"):
            if motif not in filtered:
                filtered.append(motif)
            if len(filtered) >= 8:
                break
    return filtered[:12]


def detect_composition(image: Image.Image) -> CompositionFeature:
    """Return spatial composition traits such as centeredness and symmetry."""

    resized = image.resize((128, 128))
    arr = np.asarray(resized.convert("L"), dtype=np.float32) / 255.0
    total = arr.sum() + 1e-6
    yy, xx = np.indices(arr.shape)
    cx = (xx * arr).sum() / total
    cy = (yy * arr).sum() / total
    dist = math.hypot(cx - arr.shape[1] / 2.0, cy - arr.shape[0] / 2.0)
    centered = dist < arr.shape[0] * 0.08
    flipped = np.fliplr(arr)
    numerator = np.sum((arr - arr.mean()) * (flipped - flipped.mean()))
    denominator = math.sqrt(np.sum((arr - arr.mean()) ** 2) * np.sum((flipped - flipped.mean()) ** 2)) + 1e-6
    symmetry = float(np.clip(numerator / denominator, 0.0, 1.0))

    sobel_h = filters.sobel_h(arr)
    sobel_v = filters.sobel_v(arr)
    grid_strength = float((np.abs(sobel_h).mean() + np.abs(sobel_v).mean()) / 2.0)
    grid = grid_strength > 0.12
    return CompositionFeature(centered=centered, symmetry=symmetry, grid=grid)


def estimate_brand_risk(image: Image.Image, metadata: Dict[str, str | None]) -> float:
    """Estimate potential brand infringement risk using metadata and visual cues."""

    text = " ".join(
        [str(value).lower() for value in metadata.values() if value]
    )
    tokens = re.findall(r"[a-z0-9]+", text)
    hits = sum(1 for token in tokens if token in _BRAND_KEYWORDS)
    risk = 0.0
    if hits:
        risk = min(1.0, 0.4 + 0.15 * hits)

    # Visual heuristics: extremely high contrast centered logos indicate higher risk
    arr = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
    contrast = arr.max() - arr.min()
    if contrast > 0.85:
        risk += 0.2
    edge_density = skfeature.canny(arr, sigma=1.0).mean()
    if edge_density < 0.02 and contrast > 0.6:
        risk += 0.1
    return float(np.clip(risk, 0.0, 1.0))


def build_feature(reference_id: str, image: Image.Image, metadata: Dict[str, str | None]) -> Feature:
    """High level helper that extracts all configured features."""

    palette = extract_palette(image)
    line_weight, outline_clarity = measure_outline(image)
    fill_ratio = measure_fill_ratio(image)
    typography = detect_typography(image)
    motifs = detect_motifs(image)
    composition = detect_composition(image)
    brand_risk = estimate_brand_risk(image, metadata)
    return Feature(
        reference_id=reference_id,
        palette=palette,
        line_weight=line_weight,
        outline_clarity=outline_clarity,
        fill_ratio=fill_ratio,
        typography=typography,
        motifs=motifs,
        composition=composition,
        brand_risk=brand_risk,
    )
