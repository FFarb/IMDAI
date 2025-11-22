"""LangGraph workflow orchestration for the multi-agent system."""
from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from backend.agent_state import AgentState
from backend.agents import (
    analyst_agent,
    critic_agent,
    historian_agent,
    promptsmith_agent,
    trend_agent,
    vision_agent,
)
from backend.post_processing import background_remover

logger = logging.getLogger(__name__)


def should_refine(state: AgentState) -> Literal["refine", "process_images"]:
    """Decide whether to refine prompts or end the workflow.
    
    Args:
        state: Current agent state.
        
    Returns:
        "refine" if score < 7 and iterations < max, otherwise "process_images".
    """
    score = state.get("critique_score", 0.0)
    iteration = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    
    # If score is good enough, approve
    if score >= 7.0:
        logger.info(f"Prompts approved with score {score}/10")
        return "process_images"
    
    # If we've hit max iterations, stop even if score is low
    if iteration >= max_iterations:
        logger.warning(f"Max iterations ({max_iterations}) reached, stopping refinement")
        return "process_images"
    
    # Otherwise, refine
    logger.info(f"Score {score}/10 below threshold, refining (iteration {iteration + 1}/{max_iterations})")
    return "refine"


def increment_iteration(state: AgentState) -> AgentState:
    """Increment the iteration counter for refinement loops.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with incremented iteration_count.
    """
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for the multi-agent system.
    
    The workflow follows this structure:
    START → Vision → Trend → Historian → Analyst → Promptsmith → Critic → [Decision]
                                                                    ↓
                                                              [score >= 7?]
                                                               ↙        ↘
                                                            YES         NO
                                                             ↓           ↓
                                                      Remove BG    → Promptsmith (loop)
                                                             ↓
                                                            END
    
    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add agent nodes
    workflow.add_node("vision", vision_agent)
    workflow.add_node("trend", trend_agent)
    workflow.add_node("historian", historian_agent)
    workflow.add_node("analyst", analyst_agent)
    workflow.add_node("promptsmith", promptsmith_agent)
    workflow.add_node("critic", critic_agent)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("background_remover", background_remover)
    
    # Define the flow
    workflow.set_entry_point("vision")
    workflow.add_edge("vision", "trend") # [NEW]
    workflow.add_edge("trend", "historian") # [NEW]
    workflow.add_edge("historian", "analyst")
    workflow.add_edge("analyst", "promptsmith")
    workflow.add_edge("promptsmith", "critic")
    
    # Conditional edge: critic decides whether to refine or end
    workflow.add_conditional_edges(
        "critic",
        should_refine,
        {
            "refine": "increment",
            "process_images": "background_remover", # [MODIFIED]
        },
    )
    
    # After incrementing, go back to promptsmith
    workflow.add_edge("increment", "promptsmith")
    
    # End after background removal
    workflow.add_edge("background_remover", END)
    
    # Compile the graph
    return workflow.compile()


def run_workflow(
    user_brief: str,
    audience: str,
    age: str | None = None,
    visual_references: list[str] | None = None,
    variants: int = 1,
    images_per_prompt: int = 1,
    image_model: str = "dall-e-3",
    image_quality: str = "standard",
    image_size: str = "1024x1024",
    max_iterations: int = 3,
) -> AgentState:
    """Run the complete multi-agent workflow.
    
    Args:
        user_brief: User's description of what they want to create.
        audience: Target audience for the image.
        age: Age group for the audience.
        visual_references: List of base64 encoded images or URLs.
        variants: Number of prompt variants to generate.
        images_per_prompt: Number of images per prompt.
        image_model: Image generation model.
        image_quality: Image quality setting.
        image_size: Image size setting.
        max_iterations: Maximum refinement iterations.
        
    Returns:
        Final agent state with approved prompts.
    """
    logger.info("Starting multi-agent workflow...")
    
    # Initialize state
    initial_state: AgentState = {
        "user_brief": user_brief,
        "audience": audience,
        "age": age,
        "visual_references": visual_references or [],
        "vision_analysis": "",
        "style_context": [],
        "master_strategy": "",
        "market_trends": "",
        "current_prompts": [],
        "critique_feedback": "",
        "critique_score": 0.0,
        "is_safe_for_print": False,
        "generated_images": [],
        "messages": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "variants": variants,
        "images_per_prompt": images_per_prompt,
        "image_model": image_model,
        "image_quality": image_quality,
        "image_size": image_size,
    }
    
    # Create and run workflow
    workflow = create_workflow()
    final_state = workflow.invoke(initial_state)
    
    logger.info("Multi-agent workflow completed")
    return final_state


def stream_workflow(
    user_brief: str,
    audience: str,
    age: str | None = None,
    visual_references: list[str] | None = None,
    variants: int = 1,
    images_per_prompt: int = 1,
    image_model: str = "dall-e-3",
    image_quality: str = "standard",
    image_size: str = "1024x1024",
    max_iterations: int = 3,
):
    """Stream the multi-agent workflow execution.
    
    Yields state updates as each agent completes.
    
    Args:
        Same as run_workflow.
        
    Yields:
        Tuples of (node_name, state) for each agent step.
    """
    logger.info("Starting streaming multi-agent workflow...")
    
    # Initialize state
    initial_state: AgentState = {
        "user_brief": user_brief,
        "audience": audience,
        "age": age,
        "visual_references": visual_references or [],
        "vision_analysis": "",
        "style_context": [],
        "master_strategy": "",
        "market_trends": "",
        "current_prompts": [],
        "critique_feedback": "",
        "critique_score": 0.0,
        "is_safe_for_print": False,
        "generated_images": [],
        "messages": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "variants": variants,
        "images_per_prompt": images_per_prompt,
        "image_model": image_model,
        "image_quality": image_quality,
        "image_size": image_size,
    }
    
    # Create and stream workflow
    workflow = create_workflow()
    
    for output in workflow.stream(initial_state):
        # Output is a dict with node name as key
        for node_name, state in output.items():
            logger.info(f"Agent step completed: {node_name}")
            yield node_name, state


__all__ = ["create_workflow", "run_workflow", "stream_workflow"]
