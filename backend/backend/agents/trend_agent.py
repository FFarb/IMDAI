"""Trend Agent: The Hunter.

Responsible for identifying current market trends and aesthetics for POD products.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from backend.agent_state import AgentState
from backend.tools.search import search_trends
from backend.openai_client import get_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Agent-Trend (The Hunter).
Your goal is to identify winning commercial trends for Print-on-Demand (POD) products (T-shirts, stickers, merch).

You will receive a user brief and search results about current trends.
Your output must be a concise summary of:
1.  **Winning Aesthetics:** What visual styles are selling right now? (e.g., "retro vaporwave", "minimalist line art", "distressed vintage").
2.  **Keywords:** High-volume search terms related to the topic.
3.  **Design Elements:** Specific imagery or motifs to include.

Focus on COMMERCIAL VIABILITY. What will people actually buy?
"""

def trend_agent(state: AgentState) -> AgentState:
    """Analyze trends based on the user brief.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with market_trends.
    """
    logger.info("Agent-Trend: Hunting for trends...")
    
    user_brief = state.get("user_brief", "")
    
    # 1. Perform Search
    # We'll search for t-shirt and sticker trends related to the topic
    queries = [
        f"trending {user_brief} t-shirt designs aesthetic",
        f"best selling {user_brief} stickers redbubble etsy",
        f"popular {user_brief} merch styles",
    ]
    
    search_results = ""
    for q in queries:
        results = search_trends(q, max_results=3)
        search_results += f"\nQuery: {q}\nResults:\n{results}\n"
        
    # 2. Analyze with LLM
    model = get_model()
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User Brief: {user_brief}\n\nMarket Research Data:\n{search_results}"),
    ]
    
    response = model.invoke(messages)
    market_trends = response.content
    
    logger.info("Agent-Trend: Analysis complete.")
    
    # Update state
    state["market_trends"] = str(market_trends)
    
    return state
