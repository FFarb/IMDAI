"""Agent-Vision: Analyzes uploaded reference images using GPT-4o Vision."""
from __future__ import annotations

import base64
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_openai_client

logger = logging.getLogger(__name__)


VISION_SYSTEM_PROMPT = """You are Agent-Vision, an expert visual analyst for image generation.
    
Your role is to analyze reference images uploaded by users (Primary Directive) and market trend images (Style Suggestion).

**Analysis Protocol:**
1. **User References (Primary)**: Analyze these for Subject, Composition, and Core Intent. These are the "Anchor".
2. **Trend References (Secondary)**: Analyze these for Color Palette, Vibe, and Finishing Style. These are the "Varnish".
3. **Comparative Synthesis**: Explicitly advise how to blend them.
   - "Keep the user's [Subject/Composition] but adopt the [Color/Texture] from trends."

Focus on:
- **Lighting**: Direction, quality, color temperature, shadows
- **Composition**: Framing, perspective, focal points, rule of thirds
- **Mood**: Emotional tone, atmosphere, energy
- **Color Palette**: Dominant colors, color harmony, saturation
- **Style**: Artistic style, rendering technique, visual influences
- **Subject**: Main subjects, their positioning, and relationships

Provide a concise but comprehensive analysis that will help other agents create accurate image prompts."""


def vision_agent(state: AgentState) -> AgentState:
    """Analyze uploaded reference images using GPT-4o Vision.
    
    Args:
        state: Current agent state containing visual_references.
        
    Returns:
        Updated state with vision_analysis populated.
    """
    visual_references = state.get("visual_references", [])
    trend_references = state.get("trend_references", [])
    
    # Circuit Breaker
    if state.get("skip_research"):
        logger.info("Skipping Agent-Vision due to skip_research flag.")
        return state
    
    if not visual_references and not trend_references:
        logger.info("No visual references provided, skipping vision analysis")
        state["vision_analysis"] = ""
        return state
    
    logger.info(f"Agent-Vision analyzing {len(visual_references)} user refs and {len(trend_references)} trend refs...")
    
    client = get_openai_client()
    if client is None:
        logger.error("OpenAI client not available")
        state["vision_analysis"] = ""
        return state
    
    # Prepare messages with images
    messages = [
        SystemMessage(content=VISION_SYSTEM_PROMPT),
    ]
    
    # Build human message with images
    content_parts: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": f"Analyze these images for image generation:\n\n"
            f"User Brief: {state.get('user_brief', '')}\n"
            f"Target Audience: {state.get('audience', '')}\n"
            f"Age Group: {state.get('age', 'all ages')}\n\n"
            f"There are {len(visual_references)} User References (Primary) and {len(trend_references)} Trend References (Secondary).\n"
            "Provide a detailed comparative visual analysis.",
        }
    ]
    
    # Add User Images
    for idx, img_data in enumerate(visual_references):
        # Handle both base64 and URL formats
        if img_data.startswith("http"):
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_data},
            })
        else:
            # Assume base64 encoded
            if not img_data.startswith("data:"):
                img_data = f"data:image/jpeg;base64,{img_data}"
            
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_data},
            })

    # Add Trend Images
    for idx, img_data in enumerate(trend_references):
        # Handle both base64 and URL formats
        if img_data.startswith("http"):
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_data},
            })
        else:
            # Assume base64 encoded
            if not img_data.startswith("data:"):
                img_data = f"data:image/jpeg;base64,{img_data}"
            
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_data},
            })
    
    messages.append(HumanMessage(content=content_parts))
    
    try:
        # Call GPT-4o Vision
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": m.type, "content": m.content} for m in messages],
            max_tokens=1000,
        )
        
        analysis = response.choices[0].message.content if response.choices else ""
        state["vision_analysis"] = analysis
        
        # Add to message history
        state["messages"].append(
            SystemMessage(content=f"[Agent-Vision] {analysis}")
        )
        
        logger.info(f"Agent-Vision completed analysis: {analysis[:100]}...")
        
    except Exception as e:
        logger.error(f"Agent-Vision failed: {e}", exc_info=True)
        state["vision_analysis"] = ""
    
    return state


__all__ = ["vision_agent"]
