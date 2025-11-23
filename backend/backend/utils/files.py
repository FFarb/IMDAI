"""File management utilities for the POD Merch Swarm."""
from __future__ import annotations

import datetime
import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "library"


class FileManager:
    """Manages file organization for generated assets."""

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to a filename-friendly slug."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    @staticmethod
    def create_generation_folder(strategy_name: str, generation_id: str | int) -> Path:
        """Create a structured folder for a generation.
        
        Structure: data/library/{YYYY-MM-DD}/{strategy_name_slug}/{generation_id}/
        """
        today = datetime.date.today().isoformat()
        slug = FileManager.slugify(strategy_name)
        
        folder_path = DATA_DIR / today / slug / str(generation_id)
        folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path

    @staticmethod
    def save_assets(
        folder_path: Path,
        preview_path: str | Path | None,
        metadata: dict[str, Any],
        master_path: str | Path | None = None,
        vector_path: str | Path | None = None
    ):
        """Save assets to the structured folder."""
        folder_path = Path(folder_path)
        
        # Copy preview image, skip copying when source already matches destination
        if preview_path:
            source_preview = Path(preview_path)
            dest_preview = folder_path / "preview.png"
            if source_preview.exists():
                if dest_preview.exists() and source_preview.samefile(dest_preview):
                    logger.debug("Preview already resides at target path, skipping copy.")
                else:
                    shutil.copy2(source_preview, dest_preview)

        # Copy master (upscaled) image if exists
        if master_path:
            source_master = Path(master_path)
            dest_master = folder_path / "master.png"
            if source_master.exists():
                if dest_master.exists() and source_master.samefile(dest_master):
                    logger.debug("Master already resides at target path, skipping copy.")
                else:
                    shutil.copy2(source_master, dest_master)

        # Copy vector if exists
        if vector_path:
            source_vector = Path(vector_path)
            dest_vector = folder_path / "vector.svg"
            if source_vector.exists():
                if dest_vector.exists() and source_vector.samefile(dest_vector):
                    logger.debug("Vector already resides at target path, skipping copy.")
                else:
                    shutil.copy2(source_vector, dest_vector)
            
        # Save metadata
        with open(folder_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(f"Saved assets to {folder_path}")

    @staticmethod
    def get_library_structure() -> dict[str, Any]:
        """Get the current library structure for the UI."""
        structure = {}
        
        if not DATA_DIR.exists():
            return structure
            
        for date_dir in sorted(DATA_DIR.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
                
            structure[date_dir.name] = {}
            
            for strategy_dir in sorted(date_dir.iterdir()):
                if not strategy_dir.is_dir():
                    continue
                    
                structure[date_dir.name][strategy_dir.name] = []
                
                for gen_dir in sorted(strategy_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if not gen_dir.is_dir():
                        continue
                        
                    # Load metadata to get details
                    meta_file = gen_dir / "metadata.json"
                    meta = {}
                    if meta_file.exists():
                        try:
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                        except Exception:
                            pass
                            
                    structure[date_dir.name][strategy_dir.name].append({
                        "id": gen_dir.name,
                        "path": str(gen_dir),
                        "preview": str(gen_dir / "preview.png") if (gen_dir / "preview.png").exists() else None,
                        "has_master": (gen_dir / "master.png").exists(),
                        "has_vector": (gen_dir / "vector.svg").exists(),
                        "metadata": meta
                    })
                    
        return structure
