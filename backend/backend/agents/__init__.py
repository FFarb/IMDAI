"""Agent implementations for the multi-agent system."""

from backend.agents.analyst_agent import analyst_agent
from backend.agents.critic_agent import critic_agent
from backend.agents.historian_agent import historian_agent
from backend.agents.promptsmith_agent import promptsmith_agent
from backend.agents.trend_agent import trend_agent
from backend.agents.vision_agent import vision_agent

__all__ = [
    "vision_agent",
    "trend_agent",
    "historian_agent",
    "analyst_agent",
    "promptsmith_agent",
    "critic_agent",
]
