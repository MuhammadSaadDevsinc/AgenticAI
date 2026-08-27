import asyncio
from app.schemas import ChatRequest, Message
from app.agent import execute_agent_loop
from app.tools.slack_tool import send_slack_message, DESIGNATED_CHANNEL_ID
from app.tools.tavily_tool import search_tavily

async def run_day2_tests():
    print("==================================================")
    print("🚀 DAY 2 OBJECTIVES VERIFICATION SUITE")
    print("==================================================")
    
    print("\n--- 1. Testing Slack Integration & Recipient Restriction ---")
    print(f"Designated Channel/Recipient ID: {DESIGNATED_CHANNEL_ID} (Mohsin Ali)")
    slack_res = send_slack_message(
        message="*Test Verification*: Day 2 Slack SDK Integration for Mohsin Ali.",
        channel=DESIGNATED_CHANNEL_ID
    )
    print(f"Slack Tool Result: status={slack_res.get('status')}, recipient={slack_res.get('recipient')}")
    assert slack_res.get("recipient") == "Mohsin Ali (Mohsin.A@devsinc.com)", "Recipient must be Mohsin Ali"
    
    print("\n--- 2. Testing Tavily Web Search Tool ---")
    search_res = await search_tavily(query="Solid-state battery 2026 breakthroughs", max_results=2)
    print(f"Query: {search_res.query}")
    print(f"Discovered Sources: {len(search_res.results)}")
    assert len(search_res.results) > 0, "Should return search results"
    
    print("\n--- 3. Testing Multi-Step Autonomous Workflow (Search + Slack Delivery) ---")
    request = ChatRequest(
        messages=[
            Message(
                role="user",
                content="Research solid-state battery energy density in 2026 and message the briefing to Mohsin Ali on Slack."
            )
        ],
        enable_web_search=True,
        enable_slack=True,
        search_depth="basic",
        max_results=2
    )
    
    response = await execute_agent_loop(request)
    print(f"Model used: {response.model_used}")
    print(f"Total duration: {response.total_duration_ms:.2f}ms")
    print(f"Execution steps ({len(response.execution_steps)}):")
    for step in response.execution_steps:
        print(f"  [{step.step_type}] {step.message}")
        
    print(f"\nDiscovered sources count: {len(response.sources)}")
    print(f"Tool execution records count: {len(response.tool_records)}")
    print(f"Slack deliveries count: {len(response.slack_deliveries)}")
    for d in response.slack_deliveries:
        print(f"  -> Delivered to: {d.recipient} ({d.channel}) [Status: {d.status}]")
        
    print(f"\nSuggested follow-ups: {response.suggested_follow_ups}")
    assert len(response.execution_steps) >= 3, "Should record multiple reasoning and tool steps"
    assert response.message.content, "Should produce complete final research report"
    print("\n✅ All Day 2 Tests Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_day2_tests())
