"use client";
import { useCallback, useEffect, useState } from "react";
import { listMCPServers, addMCPServer, removeMCPServer } from "@/lib/api";
import type { MCPServer } from "@/types";

export function useMCPServers() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listMCPServers();
      setServers(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const add = useCallback(async (config: MCPServer) => {
    setError(null);
    await addMCPServer(config);
    await refresh();
  }, [refresh]);

  const remove = useCallback(async (name: string) => {
    setError(null);
    await removeMCPServer(name);
    setServers((prev) => prev.filter((s) => s.name !== name));
  }, []);

  return { servers, loading, error, refresh, add, remove };
}
