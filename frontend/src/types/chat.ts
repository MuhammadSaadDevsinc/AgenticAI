export type Role = 'user' | 'assistant' | 'system' | 'tool';

export type StepType = 
  | 'thinking'
  | 'tool_call_detected'
  | 'tool_executing'
  | 'tool_completed'
  | 'slack_sending'
  | 'slack_completed'
  | 'summarizing'
  | 'final_response'
  | 'error';

export interface ToolCallFunction {
  name: string;
  arguments: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: ToolCallFunction;
}

export interface SearchResultItem {
  title: string;
  url: string;
  content: string;
  score?: number;
  published_date?: string;
}

export interface SlackDeliveryRecord {
  channel: string;
  recipient: string;
  message_preview: string;
  status: 'success' | 'simulated' | 'error';
  ts?: string;
  error?: string;
}

export interface ToolExecutionRecord {
  id: string;
  tool_name: string;
  arguments: Record<string, any>;
  result?: any;
  status: 'running' | 'success' | 'error';
  execution_time_ms?: number;
  error_message?: string;
}

export interface AgentStepEvent {
  step_id: string;
  step_type: StepType;
  message: string;
  details?: Record<string, any>;
  timestamp: number;
}

export interface Message {
  id?: string;
  role: Role;
  content?: string;
  name?: string;
  tool_call_id?: string;
  tool_calls?: ToolCall[];
  sources?: SearchResultItem[];
  slack_deliveries?: SlackDeliveryRecord[];
  execution_steps?: AgentStepEvent[];
  tool_records?: ToolExecutionRecord[];
  suggested_follow_ups?: string[];
  duration_ms?: number;
  model_used?: string;
  isStreaming?: boolean;
}

export interface ChatRequestPayload {
  messages: Array<{
    role: Role;
    content?: string;
    name?: string;
    tool_call_id?: string;
    tool_calls?: ToolCall[];
  }>;
  enable_web_search: boolean;
  enable_slack: boolean;
  search_depth: 'basic' | 'advanced';
  max_results: number;
  model?: string;
}

export interface ChatResponsePayload {
  message: Message;
  execution_steps: AgentStepEvent[];
  sources: SearchResultItem[];
  tool_records: ToolExecutionRecord[];
  slack_deliveries: SlackDeliveryRecord[];
  suggested_follow_ups: string[];
  total_duration_ms: number;
  model_used: string;
}

export interface ChatSettings {
  enableWebSearch: boolean;
  enableSlack: boolean;
}
