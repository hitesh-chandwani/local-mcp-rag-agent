"use client";
import { Plug, PlugZap, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { MCPServer } from "@/types";
import { clsx } from "clsx";

interface Props {
  server: MCPServer;
  onRemove: (name: string) => void;
}

export function MCPServerCard({ server, onRemove }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <div
        className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-surface-3 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        {server.connected ? (
          <PlugZap className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        ) : (
          <Plug className="w-4 h-4 text-zinc-500 flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-zinc-200 truncate">{server.name}</p>
          <p className="text-xs text-zinc-500">{server.transport} · {server.tool_count ?? 0} tools</p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={(e) => { e.stopPropagation(); onRemove(server.name); }}
            className="p-1 text-zinc-500 hover:text-red-400 transition-colors rounded"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          {open ? <ChevronDown className="w-4 h-4 text-zinc-500" /> : <ChevronRight className="w-4 h-4 text-zinc-500" />}
        </div>
      </div>

      {open && server.tools && server.tools.length > 0 && (
        <div className="border-t border-border px-3 py-2 bg-surface-3">
          <p className="text-xs text-zinc-500 mb-1.5">Available tools</p>
          <div className="flex flex-wrap gap-1">
            {server.tools.map((t) => (
              <span key={t} className="text-xs font-mono text-zinc-400 bg-surface-2 px-1.5 py-0.5 rounded">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
