import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import ChatRequest, ChatResponse, SearchResponse
from .agent import execute_agent_loop
from .tools.slack_tool import send_slack_message, DESIGNATED_CHANNEL_ID
from .tools.tavily_tool import search_tavily
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("autonomous-research-agent")

app = FastAPI(
    title="Autonomous Research Assistant API",
    description="Backend service for Multi-step AI Research Agent using Groq Llama 70B, Tavily Search, and Slack Integration.",
    version="2.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint and configuration status."""
    return {
        "status": "healthy",
        "service": "Autonomous Research Assistant Backend (Day 2)",
        "has_groq_key": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip()),
        "has_tavily_key": bool(settings.TAVILY_API_KEY and settings.TAVILY_API_KEY.strip()),
        "has_slack_token": bool(settings.SLACK_BOT_TOKEN and settings.SLACK_BOT_TOKEN.strip()),
        "slack_designated_recipient": f"Mohsin Ali (Channel: {DESIGNATED_CHANNEL_ID})",
        "default_model": settings.GROQ_MODEL,
        "features": [
            "Groq Local Tool Calling",
            "Tavily Search Integration",
            "Slack SDK Integration (chat_postMessage to Mohsin Ali)",
            "Multi-Step Autonomous Chaining",
            "Synthesized Research Reports & References"
        ]
    }

@app.post("/api/slack/test")
async def test_slack_endpoint(payload: dict):
    """Direct endpoint to test posting message to Mohsin Ali on Slack."""
    message = payload.get("message", "Test message from Autonomous Research Assistant")
    token = payload.get("token")
    return send_slack_message(message=message, channel=DESIGNATED_CHANNEL_ID, token=token)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Execute the multi-step research agent loop.
    Parses user conversation, decides on tool calls, executes search, and returns synthesized report.
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages list cannot be empty.")
            
        logger.info(f"Received research chat request with {len(request.messages)} messages. Web Search: {request.enable_web_search}")
        response = await execute_agent_loop(request)
        return response
    except Exception as e:
        logger.error(f"Error handling chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=SearchResponse)
async def test_search_endpoint(payload: dict):
    """Direct search tool endpoint for testing."""
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required.")
        
    depth = payload.get("search_depth", "basic")
    max_results = payload.get("max_results", 5)
    custom_key = payload.get("api_key")
    
    return await search_tavily(
        query=query,
        search_depth=depth,
        max_results=max_results,
        api_key=custom_key
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
