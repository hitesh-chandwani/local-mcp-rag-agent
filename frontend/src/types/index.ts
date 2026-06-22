export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  sources?: string[];
  toolCalls?: ToolCall[];
  isStreaming?: boolean;
  timestamp: number;
}

export interface ToolCall {
  tool: string;
  arguments: Record<string, unknown>;
  result: unknown;
}

export interface MCPServer {
  name: string;
  transport: "sse" | "stdio";
  url?: string;
  command?: string;
  args?: string[];
  headers?: Record<string, string>;
  connected?: boolean;
  tool_count?: number;
  tools?: string[];
}

export interface HealthStatus {
  status: string;
  version: string;
  vector_db: string;
  llm_provider: string;
  mcp_servers: number;
  document_count: number;
}
