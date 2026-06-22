import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "local-mcp-rag-agent",
  description: "Local-first RAG agent with MCP tool support",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-surface text-zinc-200 antialiased">{children}</body>
    </html>
  );
}
