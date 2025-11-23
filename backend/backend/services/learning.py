"""Learning service for the POD Merch Swarm."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from backend.database.store import Generation, Strategy, get_db
from backend.rag import index_strategy

logger = logging.getLogger(__name__)


class LearningService:
    """Service to handle system learning from user actions."""

    @staticmethod
    def mark_success(generation_id: int, action_type: str, db: Session) -> bool:
        """Mark a generation as successful based on user action.
        
        Args:
            generation_id: ID of the generation.
            action_type: Type of action ("upscaled", "vectorized", "saved").
            db: Database session.
            
        Returns:
            True if successful, False otherwise.
        """
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"Generation {generation_id} not found")
            return False
            
        # Update generation
        generation.add_action(action_type)
        
        # If this is a positive action, mark strategy as favorite and index it
        if action_type in ["upscaled", "vectorized", "saved"]:
            strategy = generation.strategy
            if not strategy.is_favorite:
                strategy.is_favorite = True
                logger.info(f"Marked strategy {strategy.id} ({strategy.name}) as favorite")
                
                # Index into RAG
                try:
                    strategy_data = strategy.get_data()
                    # Ensure we have enough data to index
                    if strategy_data:
                        doc_id = index_strategy(
                            strategy_id=str(strategy.id),
                            strategy_name=strategy.name,
                            strategy_data=strategy_data
                        )
                        strategy.embedding_id = doc_id
                        logger.info(f"Indexed strategy {strategy.id} to RAG with ID {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to index strategy {strategy.id}: {e}")
        
        db.commit()
        return True

    @staticmethod
    def get_successful_strategies(db: Session, limit: int = 10) -> list[Strategy]:
        """Get a list of successful strategies."""
        return db.query(Strategy).filter(Strategy.is_favorite == True).order_by(Strategy.created_at.desc()).limit(limit).all()
