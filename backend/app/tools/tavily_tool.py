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
    Returns real search results or reports error without fake fallback data.
    """
    active_key = api_key or settings.TAVILY_API_KEY
    
    if not active_key or active_key.strip() == "":
        logger.warning("No Tavily API key provided.")
        return SearchResponse(
            query=query,
            results=[],
            error="Tavily API key is not configured. Deep web research could not be performed."
        )

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
                return SearchResponse(
                    query=query,
                    results=[],
                    error="Tavily API rate limit reached. Deep web research could not be performed."
                )
            elif response.status_code in [401, 403]:
                logger.warning(f"Tavily API auth error: {response.status_code}")
                return SearchResponse(
                    query=query,
                    results=[],
                    error=f"Tavily API authentication failed ({response.status_code}). Deep web research could not be performed."
                )
            else:
                logger.error(f"Tavily API returned status {response.status_code}: {response.text}")
                return SearchResponse(
                    query=query,
                    results=[],
                    error=f"Tavily API error ({response.status_code}). Deep web research could not be performed."
                )
                
    except httpx.RequestError as exc:
        logger.error(f"Network error querying Tavily API: {exc}")
        return SearchResponse(
            query=query,
            results=[],
            error=f"Network error connecting to Tavily: {str(exc)}. Deep web research could not be performed."
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_tavily: {e}")
        return SearchResponse(
            query=query,
            results=[],
            error=f"Unexpected search error: {str(e)}. Deep web research could not be performed."
        )
