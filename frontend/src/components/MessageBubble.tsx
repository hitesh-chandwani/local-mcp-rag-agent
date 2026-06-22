"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronDown, ChevronRight, Wrench, FileText } from "lucide-react";
import { useState } from "react";
import type { Message } from "@/types";
import { clsx } from "clsx";

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const [toolsOpen, setToolsOpen] = useState(false);

  return (
    <div className={clsx("flex gap-3 animate-fade-in", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={clsx(
          "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold mt-0.5",
          isUser ? "bg-accent text-white" : "bg-surface-2 text-zinc-400 border border-border",
        )}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Bubble */}
      <div
        className={clsx(
          "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-accent text-white rounded-tr-sm"
            : "bg-surface-2 text-zinc-200 rounded-tl-sm border border-border",
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <div className="prose prose-sm prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            </div>

            {/* Streaming cursor */}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-accent ml-0.5 animate-blink align-middle" />
            )}

            {/* Sources */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-border flex flex-wrap gap-1.5">
                {message.sources.map((s) => (
                  <span
                    key={s}
                    className="flex items-center gap-1 text-xs text-zinc-500 bg-surface-3 px-2 py-0.5 rounded"
                  >
                    <FileText className="w-3 h-3" />
                    {s}
                  </span>
                ))}
              </div>
            )}

            {/* Tool calls */}
            {message.toolCalls && message.toolCalls.length > 0 && (
              <div className="mt-2">
                <button
                  onClick={() => setToolsOpen((o) => !o)}
                  className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  <Wrench className="w-3 h-3" />
                  {message.toolCalls.length} tool call{message.toolCalls.length > 1 ? "s" : ""}
                  {toolsOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </button>
                {toolsOpen && (
                  <div className="mt-1.5 space-y-1.5">
                    {message.toolCalls.map((tc, i) => (
                      <div key={i} className="text-xs bg-surface-3 rounded p-2 border border-border">
                        <div className="font-mono text-accent">{tc.tool}</div>
                        <pre className="mt-1 text-zinc-400 overflow-x-auto text-[11px]">
                          {JSON.stringify(tc.arguments, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
