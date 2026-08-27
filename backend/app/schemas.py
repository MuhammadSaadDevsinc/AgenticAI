from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class ToolCallFunction(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: ToolCallFunction

class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class SearchResultItem(BaseModel):
    title: str
    url: str
    content: str
    score: Optional[float] = None
    published_date: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem] = []
    answer: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    is_mock: bool = False
    error: Optional[str] = None

class ToolExecutionRecord(BaseModel):
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    status: Literal["running", "success", "error"] = "running"
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None

class SlackDeliveryRecord(BaseModel):
    channel: str
    recipient: str = "Mohsin Ali (Mohsin.A@devsinc.com)"
    message_preview: str
    status: Literal["success", "simulated", "error"]
    ts: Optional[str] = None
    error: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    enable_web_search: bool = True
    enable_slack: bool = True
    search_depth: Literal["basic", "advanced"] = "basic"
    max_results: int = Field(default=5, ge=1, le=10)
    custom_groq_api_key: Optional[str] = None
    custom_tavily_api_key: Optional[str] = None
    custom_slack_token: Optional[str] = None
    model: Optional[str] = None

class AgentStepEvent(BaseModel):
    step_id: str
    step_type: Literal[
        "thinking",
        "tool_call_detected",
        "tool_executing",
        "tool_completed",
        "slack_sending",
        "slack_completed",
        "summarizing",
        "final_response",
        "error"
    ]
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float

class ChatResponse(BaseModel):
    message: Message
    execution_steps: List[AgentStepEvent] = []
    sources: List[SearchResultItem] = []
    tool_records: List[ToolExecutionRecord] = []
    slack_deliveries: List[SlackDeliveryRecord] = []
    suggested_follow_ups: List[str] = []
    total_duration_ms: float
    model_used: str
