"""Discovery adapters package."""

from .generic import GenericAdapter
from .local import LocalAdapter
from .openverse import OpenverseAdapter
from .unsplash import UnsplashAdapter

__all__ = [
    "GenericAdapter",
    "LocalAdapter",
    "OpenverseAdapter",
    "UnsplashAdapter",
]
