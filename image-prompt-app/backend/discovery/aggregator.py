"""Aggregation utilities for deriving dataset-level traits."""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np

from .models import DatasetTraits, Feature, PaletteColor, Reference


def _to_rgb(hex_color: str) -> np.ndarray:
    value = hex_color.lstrip("#")
    return np.array([int(value[i : i + 2], 16) for i in range(0, 6, 2)], dtype=np.float32) / 255.0


def _weighted_trimmed_median(values: Sequence[tuple[float, float]], trim_ratio: float = 0.1) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values, key=lambda item: item[0])
    total_weight = sum(weight for _, weight in sorted_values)
    if total_weight == 0:
        return 0.0
    lower_cut = total_weight * trim_ratio
    upper_cut = total_weight * (1 - trim_ratio)
    trimmed: List[tuple[float, float]] = []
    accumulated = 0.0
    for value, weight in sorted_values:
        next_acc = accumulated + weight
        effective_weight = weight
        if next_acc <= lower_cut:
            accumulated = next_acc
            continue
        if accumulated < lower_cut:
            effective_weight -= lower_cut - accumulated
        if next_acc > upper_cut:
            effective_weight -= next_acc - upper_cut
        if effective_weight > 0:
            trimmed.append((value, effective_weight))
        accumulated = next_acc
        if accumulated >= upper_cut:
            break
    half = sum(weight for _, weight in trimmed) / 2.0
    running = 0.0
    for value, weight in trimmed:
        running += weight
        if running >= half:
            return value
    return trimmed[-1][0]


def _aggregate_palette(colors: List[np.ndarray], weights: List[float], size: int = 6) -> List[PaletteColor]:
    if not colors:
        return [PaletteColor(hex="#FFFFFF", weight=1.0)] * size
    arr = np.vstack(colors)
    w = np.asarray(weights, dtype=np.float32)
    w = np.clip(w, 1e-6, None)
    med = np.median(arr, axis=0)
    mad = np.median(np.abs(arr - med), axis=0) + 1e-6
    mask = np.all(np.abs(arr - med) <= 2.5 * mad, axis=1)
    arr = arr[mask]
    w = w[mask]
    if arr.size == 0:
        arr = np.vstack(colors)
        w = np.asarray(weights, dtype=np.float32)
    rng = np.random.default_rng(17)
    cluster_count = min(len(arr), size)
    centers = arr[rng.choice(len(arr), size=cluster_count, replace=False, p=w / w.sum())]
    for _ in range(10):
        distances = np.linalg.norm(arr[:, None, :] - centers[None, :, :], axis=2)
        labels = np.argmin(distances, axis=1)
        new_centers = centers.copy()
        for idx in range(cluster_count):
            mask = labels == idx
            if not np.any(mask):
                continue
            weight_slice = w[mask]
            weighted_points = arr[mask] * weight_slice[:, None]
            new_centers[idx] = weighted_points.sum(axis=0) / (weight_slice.sum() + 1e-6)
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    cluster_weights = np.zeros(cluster_count)
    for idx in range(cluster_count):
        mask = labels == idx
        if not np.any(mask):
            continue
        cluster_weights[idx] = w[mask].sum()
    total = cluster_weights.sum() or 1.0
    palette = [
        PaletteColor(
            hex="#" + "".join(f"{int(round(channel * 255)):02X}" for channel in centers[idx]),
            weight=float(cluster_weights[idx] / total),
        )
        for idx in range(cluster_count)
    ]
    palette.sort(key=lambda entry: entry.weight, reverse=True)
    if not palette:
        palette = [PaletteColor(hex="#FFFFFF", weight=1.0)]
    top = palette[0]
    while len(palette) < size:
        palette.append(PaletteColor(hex=top.hex, weight=0.0))
    return palette[:size]


def _map_line_weight(value: float) -> str:
    if value <= 0.33:
        return "thin"
    if value <= 0.66:
        return "regular"
    return "bold"


def _map_outline(value: float) -> str:
    return "clean" if value >= 0.55 else "rough"


def _build_typography_hints(features: Iterable[tuple[Feature, float]]) -> List[str]:
    total_weight = sum(weight for _, weight in features)
    if total_weight == 0:
        return []
    present_weight = sum(weight for feature, weight in features if feature.typography.present)
    presence_ratio = present_weight / total_weight
    if presence_ratio < 0.3:
        return []
    style_counter: Counter[str] = Counter()
    for feature, weight in features:
        if not feature.typography.present:
            continue
        style = feature.typography.style or "mixed"
        style_counter[style] += weight
    hints: List[str] = []
    for style, _ in style_counter.most_common():
        if style == "rounded":
            hints.append("rounded lettering accents")
        elif style == "block":
            hints.append("confident block typography")
        elif style == "script":
            hints.append("script-like calligraphy")
        elif style == "outline":
            hints.append("outline lettering details")
        else:
            hints.append("mixed typography flourishes")
    return hints


def _build_composition_hints(features: Iterable[tuple[Feature, float]]) -> List[str]:
    total_weight = sum(weight for _, weight in features)
    if total_weight == 0:
        return []
    centered_weight = sum(weight for feature, weight in features if feature.composition.centered)
    grid_weight = sum(weight for feature, weight in features if feature.composition.grid)
    symmetry_score = (
        sum(feature.composition.symmetry * weight for feature, weight in features) / total_weight
    )
    hints: List[str] = []
    if centered_weight >= total_weight * 0.5:
        hints.append("centered")
    if symmetry_score >= 0.65:
        hints.append("symmetrical balance")
    if grid_weight >= total_weight * 0.4:
        hints.append("subtle lattice")
    return hints


def aggregate_traits(
    session_id: str,
    selected_refs: Sequence[Reference],
    features_by_ref: Mapping[str, Feature],
    weights: Mapping[str, float] | None = None,
    audience_modes: Sequence[str] | None = None,
) -> DatasetTraits:
    if not selected_refs:
        raise ValueError("No selected references available for aggregation")
    weight_map = {ref.id: max(ref.weight, 0.5) for ref in selected_refs}
    features: List[tuple[Feature, float]] = []
    for ref in selected_refs:
        feature = features_by_ref.get(ref.id)
        if not feature:
            continue
        features.append((feature, weight_map.get(ref.id, 1.0)))
    if not features:
        raise ValueError("No extracted features available for aggregation")

    palette_colors: List[np.ndarray] = []
    palette_weights: List[float] = []
    palette_weight_factor = weights.get("palette", 1.0) if weights else 1.0
    for feature, ref_weight in features:
        for entry in feature.palette:
            palette_colors.append(_to_rgb(entry.hex))
            contribution = entry.weight * ref_weight * palette_weight_factor
            palette_weights.append(contribution)
    aggregated_palette = _aggregate_palette(palette_colors, palette_weights, size=6)

    motif_counter: Counter[str] = Counter()
    doc_freq: Counter[str] = Counter()
    tfidf: Counter[str] = Counter()
    total_tag_weight = 0.0
    doc_total = 0
    motif_weight_factor = weights.get("motifs", 1.0) if weights else 1.0
    for feature, ref_weight in features:
        if feature.brand_risk > 0.6:
            continue
        tags = [tag for tag in feature.motifs if tag]
        if not tags:
            continue
        doc_total += 1
        unique_tags = set(tags)
        doc_freq.update(unique_tags)
        counts = Counter(tags)
        tag_weight = ref_weight * len(tags) * motif_weight_factor
        total_tag_weight += tag_weight
        for tag, count in counts.items():
            tf = count / len(tags)
            scaled = tf * ref_weight * motif_weight_factor
            tfidf[tag] += scaled
            motif_counter[tag] += ref_weight * count * motif_weight_factor
    scored_motifs: List[str] = []
    for tag, score in tfidf.items():
        idf = math.log((doc_total + 1) / (doc_freq[tag] + 1)) + 1.0
        freq_ratio = (motif_counter[tag] / total_tag_weight) if total_tag_weight else 0.0
        if freq_ratio < 0.08:
            continue
        scored_motifs.append((tag, score * idf))
    scored_motifs.sort(key=lambda item: item[1], reverse=True)
    motifs = [tag for tag, _ in scored_motifs[:12]]

    line_weight_factor = weights.get("line", 1.0) if weights else 1.0
    line_values = [
        (feature.line_weight, ref_weight * line_weight_factor)
        for feature, ref_weight in features
    ]
    line_median = _weighted_trimmed_median(line_values)
    outline_values = [
        (feature.outline_clarity, ref_weight * line_weight_factor)
        for feature, ref_weight in features
    ]
    outline_median = _weighted_trimmed_median(outline_values)

    typography_factor = weights.get("type", 1.0) if weights else 1.0
    typography_hints = _build_typography_hints(
        (feature, ref_weight * typography_factor) for feature, ref_weight in features
    )
    composition_factor = weights.get("comp", 1.0) if weights else 1.0
    composition_hints = _build_composition_hints(
        (feature, ref_weight * composition_factor) for feature, ref_weight in features
    )

    return DatasetTraits(
        session_id=session_id,
        palette=aggregated_palette,
        motifs=motifs,
        line_weight=_map_line_weight(line_median),
        outline=_map_outline(outline_median),
        typography=typography_hints,
        composition=composition_hints,
        audience_modes=list(audience_modes or []),
    )
