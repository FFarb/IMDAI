"""Agent-Generator: Generates images from approved prompts."""
from __future__ import annotations

import logging
import base64
import requests
from io import BytesIO

from langchain_core.messages import SystemMessage

from backend.agent_state import AgentState
from backend.openai_client import get_openai_client

logger = logging.getLogger(__name__)


def generator_agent(state: AgentState) -> AgentState:
    """Generate images from approved prompts.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with generated_images populated.
    """
    logger.info("Agent-Generator generating images...")
    
    prompts = state.get("current_prompts", [])
    if not prompts:
        logger.warning("No prompts available for generation.")
        return state
        
    client = get_openai_client()
    if not client:
        logger.error("OpenAI client not available.")
        return state
        
    generated_images = []
    
    # Get generation parameters
    model = state.get("image_model", "dall-e-3")
    size = state.get("image_size", "1024x1024")
    quality = state.get("image_quality", "standard")
    n = state.get("images_per_prompt", 1)
    
    for idx, prompt in enumerate(prompts):
        positive_prompt = prompt.get("positive")
        if not positive_prompt:
            continue
            
        logger.info(f"Generating image for prompt {idx+1}/{len(prompts)}...")
        
        try:
            response = client.images.generate(
                model=model,
                prompt=positive_prompt,
                size=size,
                quality=quality,
                n=n,
                response_format="b64_json"
            )
            
            for item in response.data:
                if item.b64_json:
                    generated_images.append(item.b64_json)
                elif item.url:
                    # Download URL if b64 not provided (though we requested it)
                    try:
                        resp = requests.get(item.url)
                        resp.raise_for_status()
                        b64_str = base64.b64encode(resp.content).decode("utf-8")
                        generated_images.append(b64_str)
                    except Exception as e:
                        logger.error(f"Failed to download image from URL: {e}")
                        
        except Exception as e:
            logger.error(f"Image generation failed for prompt {idx}: {e}")
            
    state["generated_images"] = generated_images
    
    state["messages"].append(
        SystemMessage(content=f"[Agent-Generator] Generated {len(generated_images)} images.")
    )
    
    logger.info(f"Agent-Generator completed. Generated {len(generated_images)} images.")
    return state
