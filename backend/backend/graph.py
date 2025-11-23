"""LangGraph workflow orchestration for the multi-agent system."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from backend.agent_state import AgentState
from backend.agents import (
    analyst_agent,
    critic_agent,
    generator_agent,
    historian_agent,
    marketer_agent,
    promptsmith_agent,
    rag_archiver_agent,
    trend_agent,
    vision_agent,
)
from backend.post_processing import background_remover
from backend.tools.upscaler import Upscaler
from backend.tools.vectorizer import Vectorizer

logger = logging.getLogger(__name__)


def upscaler_node(state: AgentState) -> AgentState:
    """Upscale an image.
    
    Expects 'target_image' path in state.
    """
    target = state.get("target_image")
    if not target:
        return state
        
    upscaler = Upscaler()
    try:
        output_path = Path(target).parent / "master.png"
        upscaler.upscale(target, output_path)
        # In a real scenario, we'd update state or DB
    except Exception as e:
        logger.error(f"Upscaling failed: {e}")
    return state


def vectorizer_node(state: AgentState) -> AgentState:
    """Vectorize an image.
    
    Expects 'target_image' path in state.
    """
    target = state.get("target_image")
    if not target:
        return state
        
    vectorizer = Vectorizer()
    try:
        output_path = Path(target).parent / "vector.svg"
        vectorizer.vectorize(target, output_path)
    except Exception as e:
        logger.error(f"Vectorization failed: {e}")
    return state

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
    workflow.add_node("generator", generator_agent) # [NEW]
    workflow.add_node("background_remover", background_remover)
    workflow.add_node("marketer", marketer_agent)
    workflow.add_node("rag_archiver", rag_archiver_agent) # [NEW] - Saves to RAG, not library
    
    # Production nodes (not auto-run, connected to endpoints)
    workflow.add_node("upscaler", upscaler_node) 
    workflow.add_node("vectorizer", vectorizer_node)
    
    # Define the flow
    workflow.set_entry_point("vision")
    workflow.add_edge("vision", "trend")
    workflow.add_edge("trend", "historian")
    workflow.add_edge("historian", "analyst")
    workflow.add_edge("analyst", "promptsmith")
    workflow.add_edge("promptsmith", "critic")
    
    # Conditional edge: critic decides whether to refine or end
    workflow.add_conditional_edges(
        "critic",
        should_refine,
        {
            "refine": "increment",
            "process_images": "generator", # [MODIFIED] -> Goes to generator first
        },
    )
    
    # After incrementing, go back to promptsmith
    workflow.add_edge("increment", "promptsmith")
    
    # Generation flow
    workflow.add_edge("generator", "background_remover")
    workflow.add_edge("background_remover", "marketer")
    workflow.add_edge("marketer", "rag_archiver")
    workflow.add_edge("rag_archiver", END)
    
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
    trend_count: int = 3,
    history_count: int = 3,
    skip_research: bool = False,
    provided_strategy: dict | None = None,
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
        "master_strategy": {},
        "market_trends": "",
        "trend_references": [],
        "listing_data": {},
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
        "trend_count": trend_count,
        "history_count": history_count,
        "skip_research": skip_research,
        "provided_strategy": provided_strategy,
        "use_smart_recall": True,
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
    trend_count: int = 3,
    history_count: int = 3,
    skip_research: bool = False,
    provided_strategy: dict | None = None,
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
        "master_strategy": {},
        "market_trends": "",
        "trend_references": [],
        "listing_data": {},
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
        "trend_count": trend_count,
        "history_count": history_count,
        "skip_research": skip_research,
        "provided_strategy": provided_strategy,
        "use_smart_recall": True,
    }
    
    # Create and stream workflow
    workflow = create_workflow()
    
    for output in workflow.stream(initial_state):
        # Output is a dict with node name as key
        for node_name, state in output.items():
            logger.info(f"Agent step completed: {node_name}")
            yield node_name, state


__all__ = ["create_workflow", "run_workflow", "stream_workflow"]
