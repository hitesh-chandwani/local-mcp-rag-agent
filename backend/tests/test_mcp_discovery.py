"""Tests for MCP config discovery."""
import json
import os
import tempfile

os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")

from backend.mcp.discovery import _expand_env, load_mcp_config


def test_expand_env_basic():
    os.environ["_TEST_VAR"] = "hello"
    result = _expand_env("prefix_${_TEST_VAR}_suffix")
    assert result == "prefix_hello_suffix"


def test_expand_env_default():
    result = _expand_env("${_NONEXISTENT_VAR:default_val}")
    assert result == "default_val"


def test_expand_env_nested():
    os.environ["_TEST_TOKEN"] = "secret"
    cfg = {"headers": {"Authorization": "Bearer ${_TEST_TOKEN}"}}
    expanded = _expand_env(cfg)
    assert expanded["headers"]["Authorization"] == "Bearer secret"


def test_load_mcp_config_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_CONFIG_PATH", str(tmp_path / "nonexistent.json"))
    from importlib import reload
    import backend.core.config as cfg_module
    cfg_module._get_settings_cached = None  # reset cache
    servers = load_mcp_config()
    assert servers == []


def test_load_mcp_config_valid(tmp_path, monkeypatch):
    config = {"servers": [{"name": "test", "transport": "sse", "url": "http://localhost:9999"}]}
    config_file = tmp_path / "mcp_servers.json"
    config_file.write_text(json.dumps(config))
    monkeypatch.setenv("MCP_CONFIG_PATH", str(config_file))

    from backend.core.config import get_settings
    # Re-create settings with new env
    from backend.mcp import discovery
    import importlib
    importlib.reload(discovery)
    from backend.mcp.discovery import load_mcp_config as fresh_load

    servers = fresh_load()
    assert len(servers) == 1
    assert servers[0]["name"] == "test"
