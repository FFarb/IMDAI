"""Agent-Analyst: Synthesizes user input, vision analysis, and historical context into a master strategy."""
from __future__ import annotations

import logging
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.agent_state import AgentState
from backend.openai_client import get_model

logger = logging.getLogger(__name__)

class DesignStrategy(BaseModel):
    """Structured design strategy for POD products."""
    core_subject: str = Field(description="The central visual subject (e.g. 'A samurai cat').")
    visual_style: str = Field(description="The specific aesthetic (e.g. 'Ukiyo-e woodblock print, vector style').")
    color_palette: List[str] = Field(description="List of 4-6 specific hex codes or color names.")
    composition: str = Field(description="How elements are arranged (e.g. 'Centered, isolated, circular framing').")
    mood: str = Field(description="The emotional tone (e.g. 'Stoic, determined').")
    technical_constraints: List[str] = Field(description="List of technical rules (e.g. 'No gradients', 'Thick outlines').")
    commercial_hook: str = Field(description="Why this design will sell based on trends.")
    reference_blending_instructions: str = Field(description="How to blend User Refs (Subject) vs Trend Refs (Style).")

SYSTEM_PROMPT = """You are Agent-Analyst (The Commercial Art Director).
Your goal is to synthesize a "Master Strategy" for a Print-on-Demand (POD) product design.

Input:
1. User Brief: What the user wants.
2. Vision Analysis: Details of any reference images.
3. Historical Context: Similar past successful prompts.
4. Market Trends: Current winning aesthetics and keywords.

Output:
A strict JSON blueprint defining the design strategy.

Constraints & Best Practices:
- **Focus on clean separability:** The design MUST be suitable for background removal (isolated subject).
- **Limit color palettes:** Use 4-6 distinct colors for screen printing compatibility.
- **Style:** Avoid complex lighting effects. Prefer flat, cel-shaded, or vector styles.
- **Commercial Viability:** Ensure the design has a clear hook for the target audience.

**Blending Strategy:**
- If User Refs exist: "Keep user composition/subject, adopt trend colors/shading."
- If NO User Refs: "Fully adopt trend style and subject suggestions."
"""

def analyst_agent(state: AgentState) -> AgentState:
    """Synthesize a design strategy based on inputs and trends.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with master_strategy (dict).
    """
    logger.info("Agent-Analyst: Synthesizing strategy...")
    
    # Circuit Breaker
    if state.get("skip_research"):
        logger.info("Skipping Agent-Analyst due to skip_research flag.")
        if state.get("provided_strategy"):
            logger.info("Using provided strategy.")
            state["master_strategy"] = state["provided_strategy"]
        return state

    user_brief = state.get("user_brief", "")
    vision_analysis = state.get("vision_analysis", "None")
    style_context = state.get("style_context", [])
    market_trends = state.get("market_trends", "No trend data available.")
    
    # Format context
    context_str = "\n".join([f"- {s.get('name', 'Unknown')}: {s.get('style', '')} - {s.get('subject', '')}" for s in style_context])
    
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
    
    # Use structured output
    model = get_model().with_structured_output(DesignStrategy)
    
    try:
        strategy: DesignStrategy = model.invoke(messages)
        # Convert Pydantic model to dict for state storage
        state["master_strategy"] = strategy.model_dump()
        logger.info("Agent-Analyst: Strategy created successfully.")
    except Exception as e:
        logger.error(f"Agent-Analyst failed to generate structured output: {e}")
        # Fallback to a default empty strategy or basic dict to prevent crash
        state["master_strategy"] = {
            "core_subject": user_brief,
            "visual_style": "Vector art",
            "color_palette": ["#000000", "#FFFFFF"],
            "composition": "Centered",
            "mood": "Neutral",
            "technical_constraints": ["No gradients"],
            "commercial_hook": "N/A",
            "reference_blending_instructions": "Standard style."
        }
    
    return state
