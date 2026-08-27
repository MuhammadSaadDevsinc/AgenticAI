import json
import time
import uuid
import logging
from typing import List, Optional, Dict, Any
from groq import AsyncGroq
from .schemas import (
    Message,
    ToolCall,
    ToolCallFunction,
    ChatRequest,
    ChatResponse,
    AgentStepEvent,
    SearchResultItem,
    ToolExecutionRecord,
    SlackDeliveryRecord
)
from .tools.tavily_tool import TAVILY_SEARCH_TOOL_SCHEMA, search_tavily
from .tools.slack_tool import SLACK_POST_MESSAGE_TOOL_SCHEMA, send_slack_message, DESIGNATED_CHANNEL_ID
from .config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are an Autonomous Research Assistant powered by high-performance tool-calling models.
Your goal is to provide helpful, accurate answers and research reports. You have access to tools, but should decide smartly when to use them.

Available Tools:
1. `tavily_search`: Use ONLY when the user asks for real-time info, current events, facts, or research on a topic that requires web data. Do NOT use for general knowledge, creative questions, or things you already know confidently.
2. `slack_post_message`: Send research summaries or briefings directly to Mohsin Ali (Member ID: {DESIGNATED_CHANNEL_ID}, Mohsin.A@devsinc.com).

Strict Rules & Policies:
- WHEN TO SEARCH: Only call `tavily_search` if the question genuinely requires live/current data you cannot answer from your own training. For general knowledge, fiction, creative content, or explanations — answer directly WITHOUT searching.
- WHEN TO USE SLACK: ONLY invoke `slack_post_message` if the user's message EXPLICITLY contains words like: send, message, text, notify, tell, inform Mohsin / Slack. If not mentioned, never call it.
- DESIGNATED SLACK RECIPIENT: When Slack is requested, ONLY text Mohsin Ali (Member ID: {DESIGNATED_CHANNEL_ID}). Do NOT message anyone else.
- NO EMAIL / GMAIL: Do not create or offer email capabilities.
- SLACK FORMATTING: When composing Slack messages, DO NOT USE MARKDOWN HEADERS (#, ##, ###), horizontal lines (---), or citation tags. Use clean plain text with simple bullet points (•) and *bold* section titles.
- TOPIC RELEVANCE: Always respond to the exact topic requested in the user's prompt. Never fabricate research topics.

Response Format:
- For direct questions (no research needed): answer naturally and clearly without a formal structure.
- For research reports (when you searched the web), use:
  - **Executive Summary**
  - **Key Findings & Breakdown**
  - **Analysis & Impact**
  - **References** (as clickable Markdown links)
"""

async def execute_agent_loop(request: ChatRequest) -> ChatResponse:
    """
    Advanced multi-step autonomous agent execution loop supporting sequential
    and parallel tool calling (Tavily Search + Slack SDK).
    """
    start_time = time.time()
    steps: List[AgentStepEvent] = []
    all_sources: List[SearchResultItem] = []
    tool_records: List[ToolExecutionRecord] = []
    slack_deliveries: List[SlackDeliveryRecord] = []
    
    active_groq_key = request.custom_groq_api_key or settings.GROQ_API_KEY
    active_model = request.model or settings.GROQ_MODEL
    
    steps.append(AgentStepEvent(
        step_id=str(uuid.uuid4()),
        step_type="thinking",
        message="Analyzing user inquiry and planning multi-step workflow...",
        timestamp=time.time()
    ))
    
    # If no Groq API key is present, return clean error response
    if not active_groq_key or active_groq_key.strip() == "":
        return ChatResponse(
            message=Message(
                role="assistant",
                content="⚠️ **Configuration Error**: `GROQ_API_KEY` is not set in `.env`. Please add your Groq API key to start using the assistant."
            ),
            execution_steps=steps,
            sources=[],
            tool_records=[],
            slack_deliveries=[],
            suggested_follow_ups=[],
            total_duration_ms=(time.time() - start_time) * 1000,
            model_used=active_model or settings.GROQ_MODEL
        )
        
    groq_client = AsyncGroq(api_key=active_groq_key)
    
    # Build initial message history
    groq_messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in request.messages:
        msg_dict: Dict[str, Any] = {"role": msg.role, "content": msg.content or ""}
        if msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id
        if msg.name:
            msg_dict["name"] = msg.name
        if msg.tool_calls:
            msg_dict["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        groq_messages.append(msg_dict)
        
    # Always register both tools with the model so Groq never rejects a generated tool call.
    # Governance (when to actually execute each tool) is enforced by the system prompt and
    # by the execution logic below — not by withholding schemas from the API.
    available_tools = [TAVILY_SEARCH_TOOL_SCHEMA, SLACK_POST_MESSAGE_TOOL_SCHEMA]
    tools_param = available_tools
    
    # Build toggle context for the system prompt addendum
    toggle_context = []
    if not request.enable_web_search:
        toggle_context.append("- Web Search is currently DISABLED by the user. Do NOT call `tavily_search`.")
    if not request.enable_slack:
        toggle_context.append("- Slack notifications are currently DISABLED by the user. Do NOT call `slack_post_message`.")
    
    if toggle_context:
        toggle_note = "\n\n[CURRENT SESSION CONSTRAINTS]\n" + "\n".join(toggle_context)
        groq_messages[0]["content"] = SYSTEM_PROMPT + toggle_note
    
    max_turns = 5
    turn_count = 0
    final_content = ""
    
    try:
        while turn_count < max_turns:
            turn_count += 1
            
            # Model candidates in order of preference
            model_candidates = [
                active_model,
                "qwen/qwen3.8-27b",
                "openai/gpt-oss-20b",
                "qwen/qwen3.6-27b"
            ]
            unique_candidates = list(dict.fromkeys(model_candidates))
            
            response = None
            last_err = None
            for candidate in unique_candidates:
                try:
                    create_kwargs: Dict[str, Any] = {
                        "model": candidate,
                        "messages": groq_messages,
                        "temperature": 0.3,
                        "max_tokens": 2500,
                    }
                    if tools_param:
                        create_kwargs["tools"] = tools_param
                    response = await groq_client.chat.completions.create(**create_kwargs)
                    active_model = candidate
                    break
                except Exception as err:
                    last_err = err
                    err_str = str(err).lower()
                    if (
                        "model_not_found" in err_str
                        or "does not exist" in err_str
                        or "decommissioned" in err_str
                        or "not supported" in err_str
                        or "404" in err_str
                        or "tool_use_failed" in err_str
                        or "tool choice" in err_str
                        or "model output" in err_str
                    ):
                        logger.info(f"Model {candidate} returned ({err}), trying next verified candidate...")
                        continue
                    else:
                        raise err
                        
            if response is None:
                if last_err:
                    raise last_err
                raise RuntimeError("No available Groq model could process the request.")
                
            choice = response.choices[0]
            response_msg = choice.message

            
            # Check if LLM wants to invoke tools
            if response_msg.tool_calls and len(response_msg.tool_calls) > 0:
                # Add assistant message with tool calls to conversation history
                assistant_tool_msg = {
                    "role": "assistant",
                    "content": response_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response_msg.tool_calls
                    ]
                }
                groq_messages.append(assistant_tool_msg)
                
                # Execute each tool call
                for tc in response_msg.tool_calls:
                    fn_name = tc.function.name
                    fn_args_raw = tc.function.arguments
                    tc_id = tc.id
                    
                    try:
                        fn_args = json.loads(fn_args_raw)
                    except Exception:
                        fn_args = {"query": fn_args_raw, "message": fn_args_raw}
                        
                    tool_rec = ToolExecutionRecord(
                        id=tc_id,
                        tool_name=fn_name,
                        arguments=fn_args,
                        status="running"
                    )
                    tool_start = time.time()
                    tool_output_str = ""

                    # ─── HARD TOGGLE ENFORCEMENT ──────────────────────────────────
                    # Even if the model generated a tool call, we enforce the user's
                    # toggle settings here at execution time. The model receives a
                    # clear "tool disabled" feedback and must respond with plain text.
                    if fn_name == "tavily_search" and not request.enable_web_search:
                        logger.info("tavily_search blocked: web search toggle is OFF.")
                        tool_rec.status = "error"
                        tool_rec.error_message = "Web search is disabled by the user."
                        tool_records.append(tool_rec)
                        tool_output_str = json.dumps({
                            "error": "Web search is currently disabled. Answer from your own knowledge instead."
                        })
                        groq_messages.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": fn_name,
                            "content": tool_output_str
                        })
                        continue

                    if fn_name == "slack_post_message" and not request.enable_slack:
                        logger.info("slack_post_message blocked: Slack toggle is OFF.")
                        tool_rec.status = "error"
                        tool_rec.error_message = "Slack notifications are disabled by the user."
                        tool_records.append(tool_rec)
                        tool_output_str = json.dumps({
                            "error": "Slack notifications are currently disabled by the user. Do not send the message."
                        })
                        groq_messages.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": fn_name,
                            "content": tool_output_str
                        })
                        continue
                    # ──────────────────────────────────────────────────────────────

                    if fn_name == "tavily_search":
                        search_query = fn_args.get("query", "")
                        steps.append(AgentStepEvent(
                            step_id=str(uuid.uuid4()),
                            step_type="tool_call_detected",
                            message=f"Agent scheduled web search for query: \"{search_query}\"",
                            details={"tool": fn_name, "query": search_query},
                            timestamp=time.time()
                        ))
                        steps.append(AgentStepEvent(
                            step_id=str(uuid.uuid4()),
                            step_type="tool_executing",
                            message=f"Executing Tavily search for: \"{search_query}\"...",
                            details={"depth": request.search_depth},
                            timestamp=time.time()
                        ))
                        
                        search_res = await search_tavily(
                            query=search_query,
                            search_depth=request.search_depth,
                            max_results=request.max_results,
                            api_key=settings.TAVILY_API_KEY
                        )

                        all_sources.extend(search_res.results)
                        duration = (time.time() - tool_start) * 1000
                        tool_rec.status = "success"
                        tool_rec.result = {
                            "count": len(search_res.results),
                            "answer": search_res.answer,
                            "is_mock": search_res.is_mock,
                            "results": [r.model_dump() for r in search_res.results]
                        }
                        tool_rec.execution_time_ms = duration
                        tool_records.append(tool_rec)

                        steps.append(AgentStepEvent(
                            step_id=str(uuid.uuid4()),
                            step_type="tool_completed",
                            message=f"Retrieved {len(search_res.results)} research sources in {duration:.0f}ms.",
                            details={"sources_count": len(search_res.results)},
                            timestamp=time.time()
                        ))

                        tool_output_str = json.dumps({
                            "query": search_query,
                            "answer": search_res.answer,
                            "results": [r.model_dump() for r in search_res.results]
                        }, ensure_ascii=False)

                    elif fn_name == "slack_post_message":
                        msg_text = fn_args.get("message", "")
                        target_ch = DESIGNATED_CHANNEL_ID

                        steps.append(AgentStepEvent(
                            step_id=str(uuid.uuid4()),
                            step_type="slack_sending",
                            message=f"Dispatching notification to Mohsin Ali on Slack ({target_ch})...",
                            details={"channel": target_ch, "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)"},
                            timestamp=time.time()
                        ))

                        slack_res = send_slack_message(
                            message=msg_text,
                            channel=target_ch,
                            token=settings.SLACK_BOT_TOKEN
                        )

                        duration = (time.time() - tool_start) * 1000
                        tool_rec.status = "success" if slack_res.get("status") in ["success", "simulated"] else "error"
                        tool_rec.result = slack_res
                        tool_rec.execution_time_ms = duration
                        tool_records.append(tool_rec)

                        slack_deliv = SlackDeliveryRecord(
                            channel=target_ch,
                            recipient="Mohsin Ali (Mohsin.A@devsinc.com)",
                            message_preview=slack_res.get("message_preview", msg_text[:120]),
                            status=slack_res.get("status", "success"),
                            ts=slack_res.get("ts"),
                            error=slack_res.get("error")
                        )
                        slack_deliveries.append(slack_deliv)

                        if slack_res.get("status") in ["success", "simulated"]:
                            steps.append(AgentStepEvent(
                                step_id=str(uuid.uuid4()),
                                step_type="slack_completed",
                                message=f"Slack message delivered to Mohsin Ali ({target_ch}).",
                                details={"status": slack_res.get("status"), "ts": slack_res.get("ts")},
                                timestamp=time.time()
                            ))
                        else:
                            steps.append(AgentStepEvent(
                                step_id=str(uuid.uuid4()),
                                step_type="error",
                                message=f"Slack delivery alert: {slack_res.get('error')}",
                                details=slack_res,
                                timestamp=time.time()
                            ))

                        tool_output_str = json.dumps(slack_res, ensure_ascii=False)
                    else:
                        tool_output_str = json.dumps({"error": f"Unknown tool: {fn_name}"})
                        tool_rec.status = "error"
                        tool_rec.error_message = f"Unknown tool: {fn_name}"
                        tool_records.append(tool_rec)

                    # Append role "tool" response message to history
                    groq_messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": fn_name,
                        "content": tool_output_str
                    })

                steps.append(AgentStepEvent(
                    step_id=str(uuid.uuid4()),
                    step_type="summarizing",
                    message="Synthesizing multi-step results and preparing report...",
                    timestamp=time.time()
                ))
                # Continue loop to allow next tool calling or final synthesis
                continue
            else:
                # LLM finished all tool actions and provided final synthesis
                final_content = response_msg.content or ""
                break

        steps.append(AgentStepEvent(
            step_id=str(uuid.uuid4()),
            step_type="final_response",
            message="Autonomous workflow completed successfully.",
            timestamp=time.time()
        ))

        return ChatResponse(
            message=Message(
                role="assistant",
                content=final_content
            ),
            execution_steps=steps,
            sources=all_sources,
            tool_records=tool_records,
            slack_deliveries=slack_deliveries,
            suggested_follow_ups=[],
            total_duration_ms=(time.time() - start_time) * 1000,
            model_used=active_model
        )

    except Exception as e:
        logger.error(f"Error during agent multi-step loop: {e}", exc_info=True)
        steps.append(AgentStepEvent(
            step_id=str(uuid.uuid4()),
            step_type="error",
            message=f"Agent execution encountered an error: {str(e)}",
            details={"error": str(e)},
            timestamp=time.time()
        ))
        return ChatResponse(
            message=Message(
                role="assistant",
                content=f"⚠️ The AI model encountered an issue processing this request.\n\n**Error**: {str(e)}\n\nPlease try again or rephrase your query."
            ),
            execution_steps=steps,
            sources=all_sources,
            tool_records=tool_records,
            slack_deliveries=slack_deliveries,
            suggested_follow_ups=[],
            total_duration_ms=(time.time() - start_time) * 1000,
            model_used=active_model or settings.GROQ_MODEL
        )
