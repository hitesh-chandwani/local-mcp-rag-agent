# Contributing to local-mcp-rag-agent

Thank you for your interest in contributing! This document explains how to get started, what we value, and the process for submitting changes.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/local-mcp-rag-agent.git`
3. Create a **feature branch**: `git checkout -b feat/my-feature`
4. Follow the local dev setup in the README

## Development Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install ruff mypy pytest pytest-asyncio
```

Run tests:
```bash
pytest tests/ -v
```

Lint + format:
```bash
ruff check . && ruff format .
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Code Style

- **Python**: `ruff` for linting/formatting; `mypy` for type-checking
- **TypeScript**: ESLint (Next.js config) + strict TypeScript
- Keep functions small and single-purpose
- No comments that merely restate what the code does
- New features should include at least one test

## Submitting a Pull Request

1. Make sure tests pass (`pytest`, `npm run type-check`)
2. Keep PRs focused — one feature or fix per PR
3. Write a clear description of *what* changed and *why*
4. Reference any related issues (`Closes #123`)

## Areas for Contribution

| Area | Ideas |
|---|---|
| **LLM providers** | Cohere, Mistral, Bedrock, Vertex AI adapters |
| **Vector stores** | Qdrant, Weaviate, Pinecone adapters |
| **Document parsers** | DOCX, CSV, audio transcription |
| **MCP examples** | GitHub, Linear, Jira, database MCP configs |
| **Agent strategies** | Chain-of-thought, plan-and-execute, multi-agent |
| **Tests** | Unit tests for retriever, chunker, MCP client |
| **UI** | Dark/light theme, conversation history, file manager |
| **Docs** | Tutorials, architecture diagrams |

## Reporting Issues

Please include:
- OS and Python/Node version
- Steps to reproduce
- Expected vs actual behaviour
- Relevant logs (with API keys redacted)

## Code of Conduct

Be respectful, constructive, and welcoming. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
