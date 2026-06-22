"use client";
import { useEffect, useRef, useState } from "react";
import { Settings, Trash2, Bot } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { ConfigPanel } from "./ConfigPanel";
import { StatusBar } from "./StatusBar";
import { useChat } from "@/hooks/useChat";
import { clsx } from "clsx";

export function ChatInterface() {
  const { messages, loading, error, send, stop, clear } = useChat();
  const [panelOpen, setPanelOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <StatusBar />

      <div className="flex flex-1 overflow-hidden">
        {/* Chat area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface-1">
            <div className="flex items-center gap-2.5">
              <Bot className="w-5 h-5 text-accent" />
              <h1 className="text-sm font-semibold text-zinc-200">local-mcp-rag-agent</h1>
            </div>
            <div className="flex items-center gap-1.5">
              {messages.length > 0 && (
                <button
                  onClick={clear}
                  className="p-1.5 text-zinc-500 hover:text-zinc-300 rounded-md transition-colors"
                  title="Clear conversation"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setPanelOpen((o) => !o)}
                className={clsx(
                  "p-1.5 rounded-md transition-colors",
                  panelOpen ? "text-accent bg-accent/10" : "text-zinc-500 hover:text-zinc-300",
                )}
                title="Configuration"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-6 space-y-6">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-4 animate-fade-in">
                <div className="w-12 h-12 rounded-2xl bg-surface-2 border border-border flex items-center justify-center">
                  <Bot className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <p className="text-sm font-medium text-zinc-300">How can I help you?</p>
                  <p className="text-xs text-zinc-600 mt-1">
                    Ask questions about your documents or use connected MCP tools.
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-2 max-w-md">
                  {[
                    "What documents are in my knowledge base?",
                    "Summarize the key points from the uploaded files",
                    "List all available MCP tools",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => send(q)}
                      className="text-xs text-zinc-500 bg-surface-2 border border-border rounded-lg px-3 py-2 hover:text-zinc-300 hover:border-accent/40 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {error && (
              <div className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="px-5 pb-5 pt-3 border-t border-border bg-surface-1">
            <ChatInput onSend={send} onStop={stop} loading={loading} />
          </div>
        </div>

        {/* Config panel */}
        {panelOpen && (
          <div className="w-80 flex-shrink-0 animate-slide-up border-l border-border">
            <ConfigPanel onClose={() => setPanelOpen(false)} />
          </div>
        )}
      </div>
    </div>
  );
}
