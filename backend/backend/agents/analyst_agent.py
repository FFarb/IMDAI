"""Agent-Analyst: Synthesizes user input, vision analysis, and historical context into a master strategy."""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_openai_client
from backend.prompts import RESEARCH_SYSTEM_PROMPT_QUICK, RESEARCH_USER_PROMPT_QUICK

logger = logging.getLogger(__name__)


ANALYST_SYSTEM_PROMPT = """You are Agent-Analyst, the strategic brain of the image generation system.

Your role is to synthesize multiple sources of information into a comprehensive Master Strategy for image generation.

You will receive:
1. **User Brief**: The original user request
2. **Vision Analysis**: Detailed analysis of reference images (if provided)
3. **Historical Context**: Similar successful prompts from the past
4. **Target Audience**: Who the image is for

Your task is to create a Master Strategy that:
- Identifies the core visual concept and intent
- Extracts key stylistic elements from references and historical context
- Defines the mood, atmosphere, and emotional tone
- Specifies technical requirements (composition, lighting, color)
- Provides clear direction for prompt generation

Be concise but comprehensive. Focus on actionable insights that will guide prompt creation."""


def analyst_agent(state: AgentState) -> AgentState:
    """Synthesize user input, vision analysis, and historical context into a master strategy.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with master_strategy populated.
    """
    logger.info("Agent-Analyst synthesizing master strategy...")
    
    client = get_openai_client()
    if client is None:
        logger.error("OpenAI client not available")
        state["master_strategy"] = ""
        return state
    
    # Build context from all available information
    context_parts = [
        f"**User Brief**: {state.get('user_brief', '')}",
        f"**Target Audience**: {state.get('audience', '')}",
        f"**Age Group**: {state.get('age', 'all ages')}",
    ]
    
    if state.get("vision_analysis"):
        context_parts.append(f"\n**Vision Analysis**:\n{state['vision_analysis']}")
    
    if state.get("style_context"):
        context_parts.append("\n**Historical Context** (similar successful styles):")
        for idx, style in enumerate(state["style_context"], 1):
            context_parts.append(f"\n{idx}. {style['name']}")
            context_parts.append(f"   Style: {style['style']}")
            context_parts.append(f"   Mood: {style['mood']}")
            context_parts.append(f"   Lighting: {style['lighting']}")
            context_parts.append(f"   Details: {style['details']}")
    
    context = "\n".join(context_parts)
    
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\nCreate a comprehensive Master Strategy for image generation."},
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
        )
        
        strategy = response.choices[0].message.content if response.choices else ""
        state["master_strategy"] = strategy
        
        # Add to message history
        state["messages"].append(
            SystemMessage(content=f"[Agent-Analyst] {strategy}")
        )
        
        logger.info(f"Agent-Analyst completed strategy: {strategy[:100]}...")
        
    except Exception as e:
        logger.error(f"Agent-Analyst failed: {e}", exc_info=True)
        state["master_strategy"] = ""
    
    return state


__all__ = ["analyst_agent"]
