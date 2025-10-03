"""Perceptual hash utilities."""
from __future__ import annotations

import numpy as np
from PIL import Image


def _dct_1d(vector: np.ndarray) -> np.ndarray:
    """Compute a 1D DCT (type-II) using FFT primitives."""
    n = vector.shape[0]
    extended = np.concatenate([vector, vector[::-1]])
    result = np.fft.fft(extended)
    factor = np.exp(-1j * np.pi * np.arange(n) / (2 * n))
    dct = np.real(factor * result[:n])
    dct[0] /= np.sqrt(2)
    return dct / np.sqrt(n)


def _dct_2d(matrix: np.ndarray) -> np.ndarray:
    """Compute a 2D DCT by applying 1D transforms across axes."""
    temp = np.apply_along_axis(_dct_1d, axis=0, arr=np.apply_along_axis(_dct_1d, axis=1, arr=matrix))
    return temp


def compute_phash(image: Image.Image) -> str:
    """Compute a 64-bit perceptual hash for an image."""
    gray = image.convert("L").resize((32, 32), Image.LANCZOS)
    matrix = np.asarray(gray, dtype=np.float32)
    dct = _dct_2d(matrix)
    low_freq = dct[:8, :8]
    flat = low_freq.flatten()
    median = np.median(flat[1:]) if flat.size > 1 else 0.0
    bits = ["0"]
    bits.extend("1" if value > median else "0" for value in flat[1:])
    bitstring = "".join(bits[:64])
    hash_int = int(bitstring, 2)
    return f"{hash_int:016x}"


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Return the Hamming distance between two hexadecimal hashes."""
    try:
        int_a = int(hash_a, 16)
        int_b = int(hash_b, 16)
    except ValueError:
        return 64
    return bin(int_a ^ int_b).count("1")
