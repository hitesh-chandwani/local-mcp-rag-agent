"""
Load and validate MCP server configurations from mcp_servers.json.

Example mcp_servers.json:
{
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    {
      "name": "github",
      "transport": "sse",
      "url": "http://localhost:3001",
      "headers": { "Authorization": "Bearer ${GITHUB_TOKEN}" }
    }
  ]
}
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from ..core import get_logger, get_settings

logger = get_logger(__name__)

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _expand_env(obj: Any) -> Any:
    if isinstance(obj, str):
        def _replace(m: re.Match) -> str:
            var, _, default = m.group(1).partition(":")
            return os.environ.get(var.strip(), default.strip())
        return _ENV_PATTERN.sub(_replace, obj)
    if isinstance(obj, dict):
        return {k: _expand_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env(i) for i in obj]
    return obj


def load_mcp_config() -> List[Dict[str, Any]]:
    settings = get_settings()
    config_path = Path(settings.mcp_config_path)

    if not config_path.exists():
        logger.warning("mcp_config_not_found", path=str(config_path))
        return []

    with config_path.open() as f:
        raw = json.load(f)

    servers = _expand_env(raw.get("servers", []))
    logger.info("mcp_config_loaded", count=len(servers))
    return servers
