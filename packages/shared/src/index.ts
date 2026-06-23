export type AgentType = "ceo" | "sales" | "research" | "buyer_finder" | "operations";
export type AgentStatus = "idle" | "working" | "paused" | "error";
export type MessageRole = "user" | "agent" | "system";
export type ProviderName = "ollama" | "openai" | "claude" | "openrouter";
export type TaskStatus = "pending" | "in_progress" | "completed" | "failed";
export type TaskPriority = "low" | "medium" | "high" | "critical";

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Agent {
  id: number;
  name: string;
  agent_type: AgentType;
  description: string | null;
  status: AgentStatus;
  model: string;
  provider: string;
  temperature: number;
  is_active: boolean;
  created_at: string;
  owner_id: number;
}

export interface Chat {
  id: number;
  title: string | null;
  agent_id: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  chat_id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ProviderStatus {
  name: string;
  status: "available" | "unavailable" | "error";
  default_model: string;
  model_count: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: "pending" | "in_progress" | "completed" | "failed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  assigned_to: number | null;
  assigned_agent: number | null;
  created_by: number;
  parent_task_id: number | null;
  due_date: string | null;
  completed_at: string | null;
  result: string | null;
  created_at: string;
  updated_at: string;
}
