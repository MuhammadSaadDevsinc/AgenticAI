import asyncio
from app.schemas import ChatRequest, Message
from app.agent import execute_agent_loop
from app.tools.tavily_tool import search_tavily

async def run_tests():
    print("--- 1. Testing Tavily Search Tool ---")
    search_res = await search_tavily(query="Autonomous AI Agent Architecture", max_results=3)
    print(f"Query: {search_res.query}")
    print(f"Results Count: {len(search_res.results)}")
    print(f"Is Mock/Fallback: {search_res.is_mock}")
    assert len(search_res.results) > 0, "Should return at least 1 search result"
    
    print("\n--- 2. Testing Multi-Step Agent Execution Loop ---")
    chat_req = ChatRequest(
        messages=[
            Message(role="user", content="Research the state of autonomous AI research agents in 2026.")
        ],
        enable_web_search=True,
        search_depth="basic",
        max_results=3
    )
    
    chat_res = await execute_agent_loop(chat_req)
    print(f"Model used: {chat_res.model_used}")
    print(f"Total duration: {chat_res.total_duration_ms:.2f}ms")
    print(f"Execution steps recorded: {len(chat_res.execution_steps)}")
    for step in chat_res.execution_steps:
        print(f"  [{step.step_type}] {step.message}")
    print(f"Suggested follow-ups: {chat_res.suggested_follow_ups}")
    assert chat_res.message.content, "Should return response content"
    assert len(chat_res.execution_steps) > 0, "Should record execution steps"
    print("\n✅ All Backend Tests Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
