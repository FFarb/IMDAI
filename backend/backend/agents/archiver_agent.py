'''Agent-Archiver: Saves generated assets and metadata.'''
from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState
from backend.database.store import Generation, Strategy, get_db
from backend.utils.files import FileManager

logger = logging.getLogger(__name__)


def archiver_agent(state: AgentState) -> AgentState:
    """Save generated assets and metadata to the file system and database.

    Args:
        state: Current agent state.

    Returns:
        Updated state.
    """
    logger.info("Agent-Archiver saving assets...")

    generated_images = state.get("generated_images", [])
    if not generated_images:
        logger.warning("No images to archive.")
        return state

    # Get a database session
    db = next(get_db())

    try:
        # 1. Create/Get Strategy
        strategy_data = state.get("master_strategy", {})
        if isinstance(strategy_data, str):
            # Legacy string handling
            import json
            try:
                strategy_data = json.loads(strategy_data)
            except Exception:
                strategy_data = {"raw": strategy_data}

        strategy_name = strategy_data.get("core_subject", "Untitled Strategy")

        # For now we always create a new Strategy entry for this run
        strategy = Strategy(name=strategy_name, is_favorite=False)
        strategy.set_data(strategy_data)
        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        # 2. Save each generation
        prompts = state.get("current_prompts", [])
        for idx, img_data in enumerate(generated_images):
            # Generate a unique, timezone‑aware ID for this generation
            gen_id = int(datetime.now(timezone.utc).timestamp() * 1000) + idx

            # Create folder structure for this generation
            folder_path = FileManager.create_generation_folder(strategy_name, gen_id)

            # Save preview image (decode base64)
            preview_path = folder_path / "preview.png"
            try:
                img_bytes = base64.b64decode(img_data)
                with open(preview_path, "wb") as f:
                    f.write(img_bytes)
            except Exception as e:
                logger.error(f"Failed to save preview image: {e}")
                continue

            # Prepare metadata for this generation
            prompt_text = ""
            if idx < len(prompts):
                prompt_text = prompts[idx].get("positive", "")

            metadata: dict[str, Any] = {
                "strategy_id": strategy.id,
                "generation_id": gen_id,
                "prompt": prompt_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "settings": {
                    "model": state.get("image_model"),
                    "size": state.get("image_size"),
                    "quality": state.get("image_quality"),
                },
                "user_brief": state.get("user_brief"),
                "strategy": strategy_data,
            }

            # Save assets (metadata only, as preview is already written).
            FileManager.save_assets(folder_path, None, metadata)

            # Create Generation record in the DB
            generation = Generation(
                id=gen_id,
                strategy_id=strategy.id,
                prompt_text=prompt_text,
                image_path=str(preview_path),
                rating=0,
            )
            db.add(generation)

        db.commit()

        msg = f"Archived {len(generated_images)} generations to {folder_path.parent}"
        state["messages"].append(SystemMessage(content=f"[Agent-Archiver] {msg}"))
        logger.info(msg)

    except Exception as e:
        logger.error(f"Agent-Archiver failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    return state
