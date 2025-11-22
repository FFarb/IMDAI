"""Agent-Analyst: Synthesizes user input, vision analysis, and historical context into a master strategy."""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Agent-Analyst (The Strategist).
Your goal is to synthesize a "Master Strategy" for a Print-on-Demand (POD) product design.

Input:
1. User Brief: What the user wants.
2. Vision Analysis: Details of any reference images.
3. Historical Context: Similar past successful prompts.
4. Market Trends: Current winning aesthetics and keywords.

Output:
A comprehensive strategy document that includes:
- **Core Concept:** The central visual idea.
- **Commercial Angle:** Why this will sell (based on trends).
- **Visual Style:** The specific aesthetic (e.g., "Vector Art", "Kawaii", "Vintage Distressed").
- **Key Elements:** Mandatory visual components.
- **Color Palette:** Specific colors to use (limit to 4-5 for printability).
- **Composition:** How elements are arranged (must be isolated for t-shirts/stickers).

Constraints:
- PRIORITIZE COMMERCIAL VIABILITY.
- FAVOR VECTOR/FLAT STYLES over photorealism (better for print).
- KEEP IT SIMPLE. Complex gradients and shadows print poorly.
"""

def analyst_agent(state: AgentState) -> AgentState:
    """Synthesize a design strategy based on inputs and trends.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with master_strategy.
    """
    logger.info("Agent-Analyst: Synthesizing strategy...")
    
    user_brief = state.get("user_brief", "")
    vision_analysis = state.get("vision_analysis", "None")
    style_context = state.get("style_context", [])
    market_trends = state.get("market_trends", "No trend data available.")
    
    # Format context
    context_str = "\n".join([f"- {s['prompt']}" for s in style_context])
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
User Brief: {user_brief}

Vision Analysis:
{vision_analysis}

Market Trends:
{market_trends}

Historical Successful Prompts:
{context_str}
"""),
    ]
    
    model = get_model()
    response = model.invoke(messages)
    
    strategy = str(response.content)
    state["master_strategy"] = strategy
    
    logger.info("Agent-Analyst: Strategy created.")
    return state
