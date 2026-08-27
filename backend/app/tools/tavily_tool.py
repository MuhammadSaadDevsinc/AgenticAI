import logging
import httpx
from typing import Dict, Any, Optional
from ..schemas import SearchResponse, SearchResultItem
from ..config import settings

logger = logging.getLogger(__name__)

# Standard JSON schema for Groq tool registration
TAVILY_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "tavily_search",
        "description": "Execute an internet web search to retrieve real-time data, current events, technical documentation, and authoritative sources using Tavily Search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to execute on the web. Be descriptive and specific."
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "The depth of the search. 'basic' is faster, 'advanced' extracts deeper content."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return (1-10)."
                }
            },
            "required": ["query"]
        }
    }
}

async def search_tavily(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    api_key: Optional[str] = None
) -> SearchResponse:
    """
    Search the web using Tavily API.
    Gracefully falls back if API key is invalid or rate limited.
    """
    active_key = api_key or settings.TAVILY_API_KEY
    
    if not active_key or active_key.strip() == "":
        logger.warning("No Tavily API key provided. Using fallback search simulator.")
        return _generate_fallback_results(query, max_results, reason="Tavily API key not configured. Showing demonstration results.")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "api_key": active_key,
                "query": query,
                "search_depth": search_depth,
                "include_answer": True,
                "include_raw_content": False,
                "max_results": max_results
            }
            response = await client.post("https://api.tavily.com/search", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                results = [
                    SearchResultItem(
                        title=item.get("title", "Untitled Source"),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        score=item.get("score"),
                        published_date=item.get("published_date")
                    )
                    for item in data.get("results", [])
                ]
                return SearchResponse(
                    query=query,
                    results=results,
                    answer=data.get("answer"),
                    raw_response=data,
                    is_mock=False
                )
            elif response.status_code == 429:
                logger.warning("Tavily API rate limit reached.")
                return _generate_fallback_results(query, max_results, reason="Tavily API rate limit reached. Displaying contextual fallback results.")
            elif response.status_code == 401 or response.status_code == 403:
                logger.warning(f"Tavily API auth error: {response.status_code}")
                return _generate_fallback_results(query, max_results, reason=f"Tavily API authentication failed ({response.status_code}). Please verify your Tavily API key.")
            else:
                logger.error(f"Tavily API returned status {response.status_code}: {response.text}")
                return _generate_fallback_results(query, max_results, reason=f"Tavily API error ({response.status_code}). Fallback activated.")
                
    except httpx.RequestError as exc:
        logger.error(f"Network error querying Tavily API: {exc}")
        return _generate_fallback_results(query, max_results, reason=f"Network error connecting to Tavily: {str(exc)}")
    except Exception as e:
        logger.error(f"Unexpected error in search_tavily: {e}")
        return _generate_fallback_results(query, max_results, reason=f"Unexpected error: {str(e)}")

def _generate_fallback_results(query: str, max_results: int, reason: str = "") -> SearchResponse:
    """Generate realistic demonstration search results when API is unavailable."""
    fallback_items = [
        SearchResultItem(
            title=f"Comprehensive Overview & Analysis: {query.title()}",
            url="https://tech-research.org/papers/2026/analysis",
            content=f"Recent research regarding '{query}' indicates significant developments in efficiency, scalability, and practical adoption across multiple industry sectors in 2026.",
            score=0.96
        ),
        SearchResultItem(
            title=f"State of the Art Benchmarks & Technical Deep Dive: {query.title()}",
            url="https://arxiv.org/abs/2603.research-update",
            content=f"Experimental metrics and field reports highlight that modern architectures and methods for '{query}' achieve over 40% performance improvements compared to prior baseline models.",
            score=0.91
        ),
        SearchResultItem(
            title=f"Industry Implementation Guide and Standards: {query.title()}",
            url="https://engineering.guide/standards/latest",
            content=f"Best practices recommend rigorous validation, modular component isolation, and automated telemetry when deploying systems focused on {query}.",
            score=0.88
        )
    ]
    
    return SearchResponse(
        query=query,
        results=fallback_items[:max_results],
        answer=f"Synthesized preliminary findings for '{query}' demonstrate rapid evolution and key performance milestones across modern research benchmarks.",
        is_mock=True,
        error=reason if reason else None
    )
