"""System and user prompt templates for the ReAct agent."""

SYSTEM_PROMPT = """\
You are a helpful AI assistant with two capabilities:

1. **RAG (Document Search)** – You can search a local knowledge base of ingested documents.
2. **MCP Tools** – You can call external tools exposed by connected MCP servers.

## Instructions
- Always think step-by-step before answering.
- If the answer can be found in the document context, cite the source.
- If a tool is needed, call it using the provided function definitions.
- If neither documents nor tools are relevant, answer from your general knowledge and say so.
- Be concise. Avoid unnecessary filler sentences.
- If you're unsure, say so rather than hallucinating.

## Response format
Respond in plain text (or Markdown when formatting helps readability).
When citing a document, use: [source: <filename>]
"""


def build_rag_prompt(query: str, context: str) -> str:
    if not context:
        return query
    return f"""\
Use the following retrieved document excerpts to answer the question.
If the answer isn't in the documents, say so.

---
{context}
---

Question: {query}
"""


def build_react_prompt(
    query: str,
    context: str,
    iteration: int,
    previous_thoughts: str = "",
) -> str:
    base = f"Question: {query}\n"
    if context:
        base += f"\nRelevant document context:\n{context}\n"
    if previous_thoughts:
        base += f"\nPrevious reasoning:\n{previous_thoughts}\n"
    base += f"\n(Reasoning step {iteration}) Think carefully, then respond or call a tool."
    return base
