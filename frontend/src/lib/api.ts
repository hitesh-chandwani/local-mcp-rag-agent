import type { MCPServer, HealthStatus, Message } from "@/types";

const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendMessage(
  query: string,
  history: Array<{ role: string; content: string }>,
  sessionId?: string,
) {
  return request<{
    session_id: string;
    answer: string;
    sources: string[];
    tool_calls: Array<{ tool: string; arguments: Record<string, unknown>; result: unknown }>;
    iterations: number;
  }>("/chat", {
    method: "POST",
    body: JSON.stringify({ query, history, session_id: sessionId }),
  });
}

export function streamMessage(
  query: string,
  history: Array<{ role: string; content: string }>,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
) {
  const controller = new AbortController();

  fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, history, stream: true }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`API ${res.status}`);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) { onDone(); break; }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") { onDone(); return; }
            try {
              const parsed = JSON.parse(data);
              if (parsed.token) onToken(parsed.token);
            } catch { /* skip */ }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError(err);
    });

  return () => controller.abort();
}

// ── Ingest ────────────────────────────────────────────────────────────────────

export async function ingestText(text: string, source: string) {
  return request<{ source: string; chunks: number; ids: string[] }>("/ingest/text", {
    method: "POST",
    body: JSON.stringify({ text, source }),
  });
}

export async function ingestFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/ingest/file`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  return res.json();
}

export async function clearDocuments() {
  return request<{ message: string }>("/documents", { method: "DELETE" });
}

// ── MCP ───────────────────────────────────────────────────────────────────────

export async function listMCPServers(): Promise<MCPServer[]> {
  return request("/mcp/servers");
}

export async function addMCPServer(config: MCPServer) {
  return request<{ message: string; tools: number }>("/mcp/servers", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

export async function removeMCPServer(name: string) {
  return request<{ message: string }>(`/mcp/servers/${name}`, { method: "DELETE" });
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthStatus> {
  return request("/health");
}
