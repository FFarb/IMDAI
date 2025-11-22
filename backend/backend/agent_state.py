"""Agent state schema for the multi-agent system."""
from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Shared state schema for all agents in the workflow.
    
    This state is passed between agents and updated as the workflow progresses.
    Each agent reads from and writes to this state.
    """
    
    # User inputs
    user_brief: str
    """The original user input describing what they want to create."""
    
    audience: str
    """Target audience for the image."""
    
    age: str | None
    """Age group for the audience."""
    
    visual_references: list[str]
    """Base64 encoded images or URLs uploaded by the user."""
    
    # Agent outputs
    vision_analysis: str
    """Analysis from Agent-Vision describing the uploaded images."""
    
    style_context: list[dict]
    """Retrieved historical prompts/styles from Agent-Historian (RAG)."""
    
    master_strategy: str
    """Synthesized strategy from Agent-Analyst."""
    
    current_prompts: list[dict]
    """Generated prompt candidates from Agent-Promptsmith."""
    
    critique_feedback: str
    """Feedback from Agent-Critic."""
    
    critique_score: float
    """Quality score (0-10) from Agent-Critic."""
    
    generated_images: list[str]
    """List of generated image URLs."""
    
    # Workflow control
    messages: list[BaseMessage]
    """Chat history between agents for context."""
    
    iteration_count: int
    """Number of refinement loops (Critic -> Promptsmith)."""
    
    max_iterations: int
    """Maximum allowed refinement iterations to prevent infinite loops."""
    
    # Generation parameters
    variants: int
    """Number of prompt variants to generate."""
    
    images_per_prompt: int
    """Number of images to generate per prompt."""
    
    image_model: str
    """Image generation model to use."""
    
    image_quality: str
    """Image quality setting."""
    
    image_size: str
    """Image size setting."""


__all__ = ["AgentState"]
