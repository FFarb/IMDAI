"""Agent-Promptsmith: Generates image prompts based on the master strategy."""
from __future__ import annotations

import logging
import json

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List

from backend.agent_state import AgentState
from backend.openai_client import get_model

logger = logging.getLogger(__name__)

class PromptVariant(BaseModel):
    """A single prompt variant."""
    angle: str = Field(description="The conceptual angle (e.g., 'Minimalist', 'Action', 'Close-up').")
    positive_prompt: str = Field(description="The full positive prompt string.")
    negative_prompt: List[str] = Field(description="List of negative keywords.")

class PromptList(BaseModel):
    """List of prompt variants."""
    prompts: List[PromptVariant]

def promptsmith_agent(state: AgentState) -> AgentState:
    """Generate image prompts based on the master strategy.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with current_prompts populated.
    """
    logger.info("Agent-Promptsmith generating prompts...")
    
    strategy = state.get("master_strategy", {})
    
    # Robust handling if strategy is string (legacy or error)
    if isinstance(strategy, str):
        try:
            strategy = json.loads(strategy)
        except json.JSONDecodeError:
            logger.warning("Master strategy is a raw string. Using as core_subject.")
            strategy = {"core_subject": strategy}
            
    # Extract fields with defaults
    subject = strategy.get("core_subject", "A generic design")
    style = strategy.get("visual_style", "Vector art, flat style")
    colors = strategy.get("color_palette", [])
    if isinstance(colors, list):
        colors = ", ".join(colors)
    composition = strategy.get("composition", "Centered, isolated")
    
    variants_count = state.get("variants", 1)
    
    SYSTEM_PROMPT = f"""You are Agent-Promptsmith (The Technical Prompt Engineer).
Your goal is to convert a Design Strategy into {variants_count} DISTINCT, PRODUCTION-READY image prompts.

Input Strategy:
- Subject: {subject}
- Style: {style}
- Colors: {colors}
- Composition: {composition}

Directives:
1. **Distinct Variations**: If variants > 1, each prompt MUST explore a different angle (e.g., "Minimalist", "Detailed", "Action Pose", "Abstract").
2. **Production Rules**:
   - NO photorealism.
   - NO complex shading.
   - WHITE background (#FFFFFF).
   - VECTOR lines only.
3. **Output**: A JSON list of prompts.
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Generate {variants_count} distinct prompt variants based on the strategy."),
    ]
    
    # Use structured output
    model = get_model().with_structured_output(PromptList)
    
    try:
        result: PromptList = model.invoke(messages)
        prompts = []
        for p in result.prompts:
            prompts.append({
                "positive": p.positive_prompt,
                "negative": p.negative_prompt,
                "angle": p.angle
            })
        state["current_prompts"] = prompts
        logger.info(f"Agent-Promptsmith generated {len(prompts)} distinct prompts.")
    except Exception as e:
        logger.error(f"Agent-Promptsmith failed to generate structured output: {e}")
        # Fallback to simple template
        positive_prompt = f"{subject}, {style}, {colors}, {composition}, white background, vector style"
        negative_prompt = ["3d", "photo", "shading"]
        prompts = []
        for i in range(variants_count):
            prompts.append({
                "positive": positive_prompt,
                "negative": negative_prompt,
                "angle": "Fallback"
            })
        state["current_prompts"] = prompts
    
    # Add to message history
    summary = f"Assembled {len(prompts)} prompt(s) from strategy."
    state["messages"].append(
        SystemMessage(content=f"[Agent-Promptsmith] {summary}")
    )
    
    return state
