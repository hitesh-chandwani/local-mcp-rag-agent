"use client";
import { useCallback, useRef, useState } from "react";
import { v4 as uuid } from "crypto";
import { sendMessage, streamMessage } from "@/lib/api";
import type { Message } from "@/types";

function genId() {
  return Math.random().toString(36).slice(2);
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef<string>(genId());
  const stopStreamRef = useRef<(() => void) | null>(null);

  const history = messages
    .filter((m) => !m.isStreaming)
    .map((m) => ({ role: m.role, content: m.content }));

  const send = useCallback(
    async (content: string, useStream = true) => {
      if (!content.trim() || loading) return;
      setError(null);
      setLoading(true);

      const userMsg: Message = {
        id: genId(),
        role: "user",
        content,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);

      if (useStream) {
        const assistantId = genId();
        setMessages((prev) => [
          ...prev,
          { id: assistantId, role: "assistant", content: "", isStreaming: true, timestamp: Date.now() },
        ]);

        const stop = streamMessage(
          content,
          history,
          (token) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + token } : m,
              ),
            );
          },
          () => {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, isStreaming: false } : m)),
            );
            setLoading(false);
          },
          (err) => {
            setError(err.message);
            setMessages((prev) => prev.filter((m) => m.id !== assistantId));
            setLoading(false);
          },
        );
        stopStreamRef.current = stop;
      } else {
        try {
          const result = await sendMessage(content, history, sessionId.current);
          const assistantMsg: Message = {
            id: genId(),
            role: "assistant",
            content: result.answer,
            sources: result.sources,
            toolCalls: result.tool_calls,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, assistantMsg]);
        } catch (err: unknown) {
          setError(err instanceof Error ? err.message : String(err));
        } finally {
          setLoading(false);
        }
      }
    },
    [loading, history],
  );

  const stop = useCallback(() => {
    stopStreamRef.current?.();
    stopStreamRef.current = null;
    setLoading(false);
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    sessionId.current = genId();
    setError(null);
  }, []);

  return { messages, loading, error, send, stop, clear };
}
