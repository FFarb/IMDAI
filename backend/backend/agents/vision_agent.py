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

Your role is to analyze reference images uploaded by users and extract detailed semantic descriptions.

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
    
    if not visual_references:
        logger.info("No visual references provided, skipping vision analysis")
        state["vision_analysis"] = ""
        return state
    
    logger.info(f"Agent-Vision analyzing {len(visual_references)} reference images...")
    
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
            "text": f"Analyze these {len(visual_references)} reference images for image generation:\n\n"
            f"User Brief: {state.get('user_brief', '')}\n"
            f"Target Audience: {state.get('audience', '')}\n"
            f"Age Group: {state.get('age', 'all ages')}\n\n"
            "Provide a detailed visual analysis.",
        }
    ]
    
    # Add images
    for idx, img_data in enumerate(visual_references):
        # Handle both base64 and URL formats
        if img_data.startswith("http"):
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": img_data},
            })
        else:
            # Assume base64 encoded
            # Check if it already has the data URI prefix
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
