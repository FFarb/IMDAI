"""Agent-Promptsmith: Generates image prompts based on the master strategy."""
from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_openai_client

logger = logging.getLogger(__name__)


PROMPTSMITH_SYSTEM_PROMPT = """You are Agent-Promptsmith (The Creator).
Your goal is to write high-quality DALL-E 3 prompts for Print-on-Demand (POD) products.

Input:
- Master Strategy: The design plan.
- Critique Feedback: Feedback from previous iterations (if any).

Output:
A JSON object with a list of prompts.
Schema:
{
    "prompts": [
        {
            "positive": "The full DALL-E 3 prompt...",
            "negative": "Things to avoid..."
        }
    ]
}

MANDATORY POD CONSTRAINTS (Hardcoded):
- **Background:** ALWAYS "isolated on a pure white background" or "transparent background".
- **Style:** "Vector art", "flat design", "clean lines", "high contrast".
- **Composition:** "Centered", "no cutoff", "full subject visible".
- **Forbidden:** "Complex gradients", "photorealistic noise", "shadows", "text" (unless specified).

The prompt MUST include: "t-shirt design", "sticker design", "vector style", "white background".

Negative Prompts (Hardcoded):
- "photo", "realistic", "noise", "complex background", "text", "watermark", "cut off", "blurry", "low quality"
"""


def promptsmith_agent(state: AgentState) -> AgentState:
    """Generate image prompts based on the master strategy.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with current_prompts populated.
    """
    logger.info("Agent-Promptsmith generating prompts...")
    
    client = get_openai_client()
    if client is None:
        logger.error("OpenAI client not available")
        state["current_prompts"] = []
        return state
    
    # Build context
    context_parts = [
        f"**Master Strategy**:\n{state.get('master_strategy', '')}",
        f"\n**Number of Variants**: {state.get('variants', 1)}",
    ]
    
    # Include critique feedback if this is a refinement loop
    if state.get("critique_feedback"):
        context_parts.append(f"\n**Critique Feedback** (address these concerns):\n{state['critique_feedback']}")
        context_parts.append(f"\n**Iteration**: {state.get('iteration_count', 0) + 1} of {state.get('max_iterations', 3)}")
    
    context = "\n".join(context_parts)
    
    messages = [
        {"role": "system", "content": PROMPTSMITH_SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\nGenerate {state.get('variants', 1)} image generation prompt(s)."},
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=2000,
        )
        
        raw_text = response.choices[0].message.content if response.choices else ""
        
        # Parse prompts from response
        prompts = _parse_prompt_blocks(raw_text)
        state["current_prompts"] = prompts
        
        # Add to message history
        summary = f"Generated {len(prompts)} prompt(s)"
        if state.get("critique_feedback"):
            summary += f" (refinement iteration {state.get('iteration_count', 0) + 1})"
        
        state["messages"].append(
            SystemMessage(content=f"[Agent-Promptsmith] {summary}")
        )
        
        logger.info(f"Agent-Promptsmith generated {len(prompts)} prompts")
        
    except Exception as e:
        logger.error(f"Agent-Promptsmith failed: {e}", exc_info=True)
        state["current_prompts"] = []
    
    return state


PROMPT_BLOCK_RE = re.compile(
    r"^\s*PROMPT\s*(\d+)\s*:\s*(.*?)(?=^\s*PROMPT\s*\d+\s*:|\Z)", re.I | re.S | re.M
)


def _extract_section(block: str, title: str) -> str:
    """Extract a section from a prompt block."""
    pattern = re.compile(rf"{title}\s*[:\-]\s*(.*?)(?=\n[A-Z][a-z]*\s*[:\-]|\Z)", re.S | re.I)
    match = pattern.search(block)
    if match:
        return match.group(1).strip()
    return ""


def _parse_prompt_blocks(raw_text: str) -> list[dict]:
    """Parse prompt blocks from the raw text response."""
    prompts = []
    
    for match in PROMPT_BLOCK_RE.finditer(raw_text):
        block = match.group(2).strip()
        
        positive = _extract_section(block, "Positive") or block
        negative_section = _extract_section(block, "Negative")
        negative_terms = [term.strip() for term in re.split(r"[,\n]", negative_section) if term.strip()]
        notes = _extract_section(block, "Notes") or None
        
        prompts.append({
            "positive": positive,
            "negative": negative_terms,
            "notes": notes,
        })
    
    # Fallback: if no structured prompts found, treat entire text as one prompt
    if not prompts and raw_text.strip():
        prompts.append({
            "positive": raw_text.strip(),
            "negative": [],
            "notes": None,
        })
    
    return prompts


__all__ = ["promptsmith_agent"]
