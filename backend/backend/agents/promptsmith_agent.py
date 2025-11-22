"""Agent-Promptsmith: Generates image prompts based on the master strategy."""
from __future__ import annotations

import logging
import json

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState

logger = logging.getLogger(__name__)

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
    
    # Construct the "Jailbreak" prompt dynamically
    positive_prompt = f"""
[Technical Specification]
Subject: {subject}
Style: {style}
Colors: {colors}
Composition: {composition}

[Production Rules]
- NO photorealism.
- NO complex shading.
- WHITE background (#FFFFFF).
- VECTOR lines only.

[Direct Instruction]
"I need an exact visual representation of this specification. Do not enhance. Do not add details. Do not make it 'creative'. Render exactly as specified for a vector file."
""".strip()

    # Hardcoded negative prompt (strengthened)
    negative_prompt = ["3d render", "octane render", "shadows", "blur", "gradients", "noise", "photo", "skin texture"]
    
    # Handle variants
    # Since this is deterministic, variants will be identical unless we introduce noise.
    # For now, we produce identical strict prompts as requested.
    variants_count = state.get("variants", 1)
    prompts = []
    for _ in range(variants_count):
        prompts.append({
            "positive": positive_prompt,
            "negative": negative_prompt
        })
        
    state["current_prompts"] = prompts
    
    # Add to message history
    summary = f"Assembled {len(prompts)} prompt(s) from strategy."
    state["messages"].append(
        SystemMessage(content=f"[Agent-Promptsmith] {summary}")
    )
    
    logger.info(f"Agent-Promptsmith assembled {len(prompts)} prompts")
    
    return state
