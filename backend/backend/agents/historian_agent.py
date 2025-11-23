"""Agent-Historian: Retrieves similar historical prompts using RAG."""
from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState
from backend.rag import retrieve_similar_styles

logger = logging.getLogger(__name__)


def historian_agent(state: AgentState) -> AgentState:
    """Retrieve similar historical prompts/styles from the vector store.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with style_context populated.
    """
    logger.info("Agent-Historian searching for similar styles...")
    
    # Circuit Breaker
    if state.get("skip_research"):
        logger.info("Skipping Agent-Historian due to skip_research flag.")
        return state

    history_count = state.get("history_count", 3)
    if history_count == 0:
        logger.info("History count is 0, skipping retrieval.")
        state["style_context"] = []
        return state

    # Build search query from user brief and vision analysis
    query_parts = [state.get("user_brief", "")]
    
    if state.get("vision_analysis"):
        query_parts.append(state["vision_analysis"])
    
    query = " ".join(query_parts).strip()
    
    if not query:
        logger.warning("No query available for historian search")
        state["style_context"] = []
        return state
    
    try:
        # Retrieve similar styles from RAG
        use_smart_recall = state.get("use_smart_recall", True)
        similar_styles = retrieve_similar_styles(
            query, 
            k=history_count,
            filter_favorites=use_smart_recall
        )
        state["style_context"] = similar_styles
        
        # Format findings for message history
        if similar_styles:
            findings = f"Found {len(similar_styles)} similar styles:\n"
            for idx, style in enumerate(similar_styles, 1):
                findings += f"\n{idx}. **{style['name']}** (similarity: {style['similarity_score']:.2f})\n"
                findings += f"   - Style: {style['style']}\n"
                findings += f"   - Mood: {style['mood']}\n"
                findings += f"   - Lighting: {style['lighting']}\n"
        else:
            findings = "No similar styles found in the database."
        
        state["messages"].append(
            SystemMessage(content=f"[Agent-Historian] {findings}")
        )
        
        logger.info(f"Agent-Historian found {len(similar_styles)} similar styles")
        
    except Exception as e:
        logger.error(f"Agent-Historian failed: {e}", exc_info=True)
        state["style_context"] = []
    
    return state


__all__ = ["historian_agent"]
