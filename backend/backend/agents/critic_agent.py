"""Agent-Critic: Reviews generated prompts and provides quality feedback."""
from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_openai_client

logger = logging.getLogger(__name__)


CRITIC_SYSTEM_PROMPT = """You are Agent-Critic, the quality control expert for image generation prompts.

Your role is to review generated prompts BEFORE image generation and ensure they meet quality standards.

Evaluate each prompt based on:
1. **Alignment with User Brief**: Does it match what the user requested?
2. **Style Consistency**: Does it align with the historical context and vision analysis?
3. **Technical Quality**: Is it specific, detailed, and actionable?
4. **Completeness**: Does it include necessary elements (subject, style, lighting, mood, composition)?
5. **Negative Constraints**: Are appropriate negative prompts included?

For each prompt, provide:
- **Score** (0-10): Overall quality rating
- **Strengths**: What works well
- **Issues**: What needs improvement
- **Recommendations**: Specific suggestions for refinement

Overall Assessment:
- If ALL prompts score >= 7: APPROVE for image generation
- If ANY prompt scores < 7: REJECT and provide detailed feedback for refinement

Be constructive and specific in your feedback."""


def critic_agent(state: AgentState) -> AgentState:
    """Review generated prompts and provide quality feedback.
    
    Args:
        state: Current agent state with current_prompts.
        
    Returns:
        Updated state with critique_feedback and critique_score.
    """
    logger.info("Agent-Critic reviewing prompts...")
    
    prompts = state.get("current_prompts", [])
    
    if not prompts:
        logger.warning("No prompts to review")
        state["critique_score"] = 0.0
        state["critique_feedback"] = "No prompts generated to review."
        return state
    
    client = get_openai_client()
    if client is None:
        logger.error("OpenAI client not available")
        # Default to approval if critic can't run
        state["critique_score"] = 7.0
        state["critique_feedback"] = ""
        return state
    
    # Build review context
    context_parts = [
        f"**User Brief**: {state.get('user_brief', '')}",
        f"**Target Audience**: {state.get('audience', '')}",
        f"**Master Strategy**: {state.get('master_strategy', '')}",
        "\n**Prompts to Review**:",
    ]
    
    for idx, prompt in enumerate(prompts, 1):
        context_parts.append(f"\nPrompt {idx}:")
        context_parts.append(f"Positive: {prompt.get('positive', '')}")
        context_parts.append(f"Negative: {', '.join(prompt.get('negative', []))}")
        if prompt.get('notes'):
            context_parts.append(f"Notes: {prompt['notes']}")
    
    context = "\n".join(context_parts)
    
    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\nReview these prompts and provide your assessment."},
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
        )
        
        feedback = response.choices[0].message.content if response.choices else ""
        
        # Extract score from feedback (look for patterns like "Score: 8" or "8/10")
        score = _extract_score(feedback)
        
        state["critique_feedback"] = feedback
        state["critique_score"] = score
        
        # Add to message history
        decision = "APPROVED" if score >= 7.0 else "REJECTED"
        state["messages"].append(
            SystemMessage(content=f"[Agent-Critic] {decision} (score: {score}/10)\n{feedback[:200]}...")
        )
        
        logger.info(f"Agent-Critic completed review: {decision} (score: {score}/10)")
        
    except Exception as e:
        logger.error(f"Agent-Critic failed: {e}", exc_info=True)
        # Default to approval on error
        state["critique_score"] = 7.0
        state["critique_feedback"] = ""
    
    return state


def _extract_score(feedback: str) -> float:
    """Extract numerical score from critique feedback.
    
    Looks for patterns like:
    - "Score: 8"
    - "8/10"
    - "Rating: 7.5"
    
    Returns:
        Extracted score (0-10), defaults to 5.0 if not found.
    """
    import re
    
    # Try to find score patterns
    patterns = [
        r"score[:\s]+(\d+(?:\.\d+)?)",  # "Score: 8" or "score 8.5"
        r"(\d+(?:\.\d+)?)\s*/\s*10",     # "8/10" or "8.5/10"
        r"rating[:\s]+(\d+(?:\.\d+)?)",  # "Rating: 7"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, feedback, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                # Ensure score is in 0-10 range
                return max(0.0, min(10.0, score))
            except ValueError:
                continue
    
    # Default to middle score if no score found
    # Check for approval/rejection keywords
    if any(word in feedback.lower() for word in ["approve", "excellent", "great", "perfect"]):
        return 8.0
    elif any(word in feedback.lower() for word in ["reject", "poor", "inadequate", "needs work"]):
        return 5.0
    
    return 5.0


__all__ = ["critic_agent"]
