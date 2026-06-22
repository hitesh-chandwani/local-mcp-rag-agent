"use client";
import { KeyboardEvent, useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { ArrowUp, Square } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  onSend: (value: string) => void;
  onStop: () => void;
  loading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, loading, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const val = ref.current?.value?.trim();
    if (!val) return;
    onSend(val);
    if (ref.current) ref.current.value = "";
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex items-end gap-2 bg-surface-2 border border-border rounded-xl px-4 py-3 focus-within:border-accent/50 transition-colors">
      <TextareaAutosize
        ref={ref}
        minRows={1}
        maxRows={8}
        placeholder="Ask anything… (Shift+Enter for newline)"
        onKeyDown={onKey}
        disabled={disabled || loading}
        className="flex-1 bg-transparent resize-none text-sm text-zinc-200 placeholder-zinc-600 outline-none leading-relaxed"
      />

      <button
        onClick={loading ? onStop : submit}
        disabled={disabled}
        className={clsx(
          "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all",
          loading
            ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
            : "bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed",
        )}
      >
        {loading ? <Square className="w-3.5 h-3.5" /> : <ArrowUp className="w-4 h-4" />}
      </button>
    </div>
  );
}
