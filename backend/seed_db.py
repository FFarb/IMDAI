"""Seeder script to populate the ChromaDB vector store with presets."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.rag import seed_presets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Seed the vector store with presets from presets.json."""
    # Path to presets.json (in the root directory)
    presets_path = Path(__file__).parent.parent / "presets.json"
    
    if not presets_path.exists():
        logger.error(f"Presets file not found: {presets_path}")
        logger.error("Please ensure presets.json exists in the root directory")
        return 1
    
    logger.info(f"Seeding vector store from: {presets_path}")
    
    try:
        count = seed_presets(presets_path)
        logger.info(f"✓ Successfully seeded {count} presets to vector store")
        logger.info("Vector store is ready for use!")
        return 0
    except Exception as e:
        logger.error(f"✗ Failed to seed vector store: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
