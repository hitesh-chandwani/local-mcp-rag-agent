"use client";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthStatus } from "@/types";
import { clsx } from "clsx";

export function StatusBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetch = () =>
      getHealth()
        .then((h) => { setHealth(h); setError(false); })
        .catch(() => setError(true));

    fetch();
    const id = setInterval(fetch, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-4 px-4 py-1.5 border-b border-border text-xs text-zinc-600">
      <div className="flex items-center gap-1.5">
        <span className={clsx("w-1.5 h-1.5 rounded-full", error ? "bg-red-500" : "bg-emerald-500")} />
        <span>{error ? "Backend offline" : "Connected"}</span>
      </div>
      {health && (
        <>
          <span>LLM: {health.llm_provider}</span>
          <span>DB: {health.vector_db}</span>
          <span>{health.document_count} docs</span>
          <span>{health.mcp_servers} MCP servers</span>
          <span className="ml-auto">v{health.version}</span>
        </>
      )}
    </div>
  );
}
