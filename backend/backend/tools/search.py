"""Search tool using DuckDuckGo."""
from __future__ import annotations

import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

def search_trends(query: str, max_results: int = 5) -> str:
    """Search for current market trends.
    
    Args:
        query: Search query string.
        max_results: Number of results to return.
        
    Returns:
        Formatted string of search results.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return "No trend data found."
            
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. {r['title']}: {r['body']}")
            
        return "\n".join(formatted)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error retrieving trends: {str(e)}"
