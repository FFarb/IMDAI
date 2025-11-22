"""Trend Agent: The Hunter.

Responsible for identifying current market trends and aesthetics for POD products.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from backend.agent_state import AgentState
from backend.tools.search import search_trends, search_images
from backend.openai_client import get_model
import requests
import base64
from io import BytesIO

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
    
    # Circuit Breaker
    if state.get("skip_research"):
        logger.info("Skipping Agent-Trend due to skip_research flag.")
        return state

    user_brief = state.get("user_brief", "")
    trend_count = state.get("trend_count", 3)
    
    if trend_count == 0:
        logger.info("Trend count is 0, skipping search.")
        state["market_trends"] = "Trend search disabled."
        state["trend_references"] = []
        return state
    
    # 1. Perform Search
    # We'll search for t-shirt and sticker trends related to the topic
    queries = [
        f"trending {user_brief} t-shirt designs aesthetic",
        f"best selling {user_brief} stickers redbubble etsy",
        f"popular {user_brief} merch styles",
    ]
    
    search_results = ""
    for q in queries:
        results = search_trends(q, max_results=trend_count)
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
    
    # 3. Visual Trend Hunting
    logger.info("Agent-Trend: Hunting for visual trends...")
    trend_references = []
    
    # Use the first query for image search as it's usually the most relevant
    image_query = queries[0]
    image_urls = search_images(image_query, max_results=trend_count)
    
    for url in image_urls:
        try:
            # Download image
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Convert to base64
                img_bytes = BytesIO(response.content)
                b64_data = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                mime_type = response.headers.get('content-type', 'image/jpeg')
                trend_references.append(f"data:{mime_type};base64,{b64_data}")
        except Exception as e:
            logger.warning(f"Failed to download trend image {url}: {e}")
            continue

    # Update state
    state["market_trends"] = str(market_trends)
    state["trend_references"] = trend_references
    
    return state
