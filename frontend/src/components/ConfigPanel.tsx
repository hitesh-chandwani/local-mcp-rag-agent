"use client";
import { useState, useRef } from "react";
import { Plus, RefreshCw, Upload, Trash2, X, Server } from "lucide-react";
import { MCPServerCard } from "./MCPServerCard";
import { useMCPServers } from "@/hooks/useMCPServers";
import { ingestFile, clearDocuments } from "@/lib/api";
import type { MCPServer } from "@/types";
import { clsx } from "clsx";

interface Props {
  onClose: () => void;
}

export function ConfigPanel({ onClose }: Props) {
  const { servers, loading, error, refresh, add, remove } = useMCPServers();
  const [tab, setTab] = useState<"mcp" | "docs">("mcp");
  const [addOpen, setAddOpen] = useState(false);
  const [newServer, setNewServer] = useState<Partial<MCPServer>>({ transport: "sse" });
  const [addError, setAddError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleAdd = async () => {
    if (!newServer.name) { setAddError("Name is required"); return; }
    setAddError(null);
    try {
      await add(newServer as MCPServer);
      setNewServer({ transport: "sse" });
      setAddOpen(false);
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const results = await Promise.all(Array.from(files).map((f) => ingestFile(f)));
      const totalChunks = results.reduce((sum, r) => sum + r.chunks, 0);
      setUploadMsg(`Ingested ${results.length} file(s) → ${totalChunks} chunks`);
    } catch (err: unknown) {
      setUploadMsg(`Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleClear = async () => {
    if (!confirm("Clear all ingested documents?")) return;
    await clearDocuments();
    setUploadMsg("All documents cleared");
  };

  return (
    <div className="flex flex-col h-full bg-surface-1 border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className="text-sm font-semibold text-zinc-200">Configuration</h2>
        <button onClick={onClose} className="p-1 text-zinc-500 hover:text-zinc-300 rounded transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {(["mcp", "docs"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={clsx(
              "flex-1 py-2.5 text-xs font-medium transition-colors",
              tab === t ? "text-accent border-b-2 border-accent" : "text-zinc-500 hover:text-zinc-300",
            )}
          >
            {t === "mcp" ? "MCP Servers" : "Documents"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tab === "mcp" && (
          <>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAddOpen((o) => !o)}
                className="flex items-center gap-1.5 text-xs text-accent hover:text-accent-hover transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Server
              </button>
              <button
                onClick={refresh}
                disabled={loading}
                className="ml-auto p-1 text-zinc-500 hover:text-zinc-300 rounded transition-colors disabled:opacity-50"
              >
                <RefreshCw className={clsx("w-3.5 h-3.5", loading && "animate-spin")} />
              </button>
            </div>

            {addOpen && (
              <div className="bg-surface-2 border border-border rounded-lg p-3 space-y-2 animate-slide-up">
                <p className="text-xs font-medium text-zinc-300">New MCP Server</p>
                <input
                  placeholder="Name (e.g. github)"
                  value={newServer.name ?? ""}
                  onChange={(e) => setNewServer((s) => ({ ...s, name: e.target.value }))}
                  className="w-full bg-surface-3 border border-border rounded px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 outline-none focus:border-accent/50"
                />
                <select
                  value={newServer.transport}
                  onChange={(e) => setNewServer((s) => ({ ...s, transport: e.target.value as "sse" | "stdio" }))}
                  className="w-full bg-surface-3 border border-border rounded px-3 py-1.5 text-xs text-zinc-200 outline-none focus:border-accent/50"
                >
                  <option value="sse">SSE (HTTP)</option>
                  <option value="stdio">stdio (local process)</option>
                </select>
                {newServer.transport === "sse" ? (
                  <input
                    placeholder="URL (e.g. http://localhost:3001)"
                    value={newServer.url ?? ""}
                    onChange={(e) => setNewServer((s) => ({ ...s, url: e.target.value }))}
                    className="w-full bg-surface-3 border border-border rounded px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 outline-none focus:border-accent/50"
                  />
                ) : (
                  <input
                    placeholder="Command (e.g. npx @modelcontextprotocol/server-filesystem)"
                    value={newServer.command ?? ""}
                    onChange={(e) => setNewServer((s) => ({ ...s, command: e.target.value }))}
                    className="w-full bg-surface-3 border border-border rounded px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 outline-none focus:border-accent/50"
                  />
                )}
                {addError && <p className="text-xs text-red-400">{addError}</p>}
                <div className="flex gap-2">
                  <button onClick={handleAdd} className="flex-1 py-1.5 bg-accent text-white text-xs rounded hover:bg-accent-hover transition-colors">
                    Connect
                  </button>
                  <button onClick={() => setAddOpen(false)} className="flex-1 py-1.5 bg-surface-3 text-zinc-400 text-xs rounded hover:text-zinc-200 transition-colors">
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {error && <p className="text-xs text-red-400">{error}</p>}

            {servers.length === 0 && !loading && (
              <div className="flex flex-col items-center gap-2 py-8 text-zinc-600">
                <Server className="w-8 h-8" />
                <p className="text-xs text-center">No MCP servers connected.<br />Add one to extend the agent with tools.</p>
              </div>
            )}

            {servers.map((s) => (
              <MCPServerCard key={s.name} server={s} onRemove={remove} />
            ))}
          </>
        )}

        {tab === "docs" && (
          <>
            <div>
              <p className="text-xs text-zinc-400 mb-2">
                Upload files to the local knowledge base. Supported: .txt, .md, .pdf, .html
              </p>
              <input
                ref={fileRef}
                type="file"
                multiple
                accept=".txt,.md,.pdf,.html"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className={clsx(
                  "flex items-center justify-center gap-2 w-full py-3 border-2 border-dashed border-border rounded-lg text-xs text-zinc-500 cursor-pointer hover:border-accent/50 hover:text-zinc-300 transition-colors",
                  uploading && "opacity-50 pointer-events-none",
                )}
              >
                <Upload className="w-4 h-4" />
                {uploading ? "Uploading…" : "Click or drop files here"}
              </label>
            </div>

            {uploadMsg && (
              <p className={clsx("text-xs", uploadMsg.startsWith("Error") ? "text-red-400" : "text-emerald-400")}>
                {uploadMsg}
              </p>
            )}

            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-400 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear all documents
            </button>
          </>
        )}
      </div>
    </div>
  );
}
