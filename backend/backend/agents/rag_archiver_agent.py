"""RAG-Archiver: Automatically saves all generations to RAG system for learning."""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState
from backend.database.store import Generation, Strategy, get_db
from backend.rag import index_strategy

logger = logging.getLogger(__name__)


def rag_archiver_agent(state: AgentState) -> AgentState:
    """Save all generated assets to RAG system for learning (not to library).
    
    This agent automatically indexes every generation into the RAG system
    so the AI can learn from all outputs. User-approved items will be
    moved to the library separately via explicit UI actions.

    Args:
        state: Current agent state.

    Returns:
        Updated state.
    """
    logger.info("Agent-RAG-Archiver indexing generations...")

    generated_images = state.get("generated_images", [])
    if not generated_images:
        logger.warning("No images to archive to RAG.")
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

        # Create a new Strategy entry for this run (not marked as favorite yet)
        strategy = Strategy(name=strategy_name, is_favorite=False)
        strategy.set_data(strategy_data)
        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        # Index strategy into RAG immediately for learning
        try:
            if strategy_data:
                doc_id = index_strategy(
                    strategy_id=str(strategy.id),
                    strategy_name=strategy_name,
                    strategy_data=strategy_data
                )
                strategy.embedding_id = doc_id
                logger.info(f"Indexed strategy {strategy.id} to RAG with ID {doc_id}")
        except Exception as e:
            logger.error(f"Failed to index strategy {strategy.id}: {e}")

        # 2. Save each generation to database (but NOT to file library)
        prompts = state.get("current_prompts", [])
        generation_ids = []
        
        for idx, img_data in enumerate(generated_images):
            # Generate a unique, timezone-aware ID for this generation
            gen_id = int(datetime.now(timezone.utc).timestamp() * 1000) + idx

            # Prepare metadata for this generation
            prompt_text = ""
            if idx < len(prompts):
                prompt_text = prompts[idx].get("positive", "")

            # Create Generation record in the DB (image stored as base64 in metadata)
            generation = Generation(
                id=gen_id,
                strategy_id=strategy.id,
                prompt_text=prompt_text,
                image_path="",  # No file path yet - only saved when user approves
                rating=0,
            )
            
            # Store the base64 image data in generation metadata for later retrieval
            generation.metadata_json = {
                "image_b64": img_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "settings": {
                    "model": state.get("image_model"),
                    "size": state.get("image_size"),
                    "quality": state.get("image_quality"),
                },
                "user_brief": state.get("user_brief"),
                "strategy": strategy_data,
            }
            
            db.add(generation)
            generation_ids.append(gen_id)

        db.commit()

        # Store generation IDs in state for frontend to reference
        state["generation_ids"] = generation_ids
        
        msg = f"Indexed {len(generated_images)} generations to RAG system"
        state["messages"].append(SystemMessage(content=f"[Agent-RAG-Archiver] {msg}"))
        logger.info(msg)

    except Exception as e:
        logger.error(f"Agent-RAG-Archiver failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    return state
