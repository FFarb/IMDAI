"""Agent-Marketer: Generates SEO and listing metadata for the final design."""
from __future__ import annotations

import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.agent_state import AgentState
from backend.openai_client import get_model

logger = logging.getLogger(__name__)

class ListingData(BaseModel):
    """SEO and listing metadata for POD products."""
    title: str = Field(description="SEO-optimized product title (50-60 chars).")
    description: str = Field(description="Compelling product description with keywords (150-200 words).")
    tags: str = Field(description="Comma-separated list of 15-30 high-traffic tags.")

SYSTEM_PROMPT = """You are Agent-Marketer (The SEO Specialist).
Your goal is to generate high-converting listing metadata for a Print-on-Demand (POD) product.

Input:
1. Master Strategy: The design concept, subject, and style.
2. Market Trends: The keywords and aesthetics that are trending.

Output:
A strict JSON object containing:
- **Title**: Catchy, keyword-rich, under 60 chars.
- **Description**: Persuasive copy highlighting the design's vibe and quality.
- **Tags**: 15-30 relevant tags, comma-separated. Mix broad and niche tags.

Focus on platforms like Redbubble, Etsy, and Teepublic.
"""

def marketer_agent(state: AgentState) -> AgentState:
    """Generate listing metadata based on the strategy.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with listing_data (dict).
    """
    logger.info("Agent-Marketer: Generating listing metadata...")
    
    master_strategy = state.get("master_strategy", {})
    market_trends = state.get("market_trends", "")
    
    # Format strategy for prompt
    strategy_str = "\n".join([f"{k}: {v}" for k, v in master_strategy.items()])
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
Design Strategy:
{strategy_str}

Market Trends:
{market_trends}
"""),
    ]
    
    # Use structured output
    model = get_model().with_structured_output(ListingData)
    
    try:
        listing: ListingData = model.invoke(messages)
        # Convert Pydantic model to dict for state storage
        state["listing_data"] = listing.model_dump()
        logger.info("Agent-Marketer: Listing data generated successfully.")
    except Exception as e:
        logger.error(f"Agent-Marketer failed to generate structured output: {e}")
        # Fallback
        state["listing_data"] = {
            "title": "New Design",
            "description": "A unique design.",
            "tags": "art, design, illustration"
        }
    
    return state

__all__ = ["marketer_agent"]
