from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class MCPServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    transport: str = "stdio"
    enabled: bool = True
    search_tools: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MCPToolDefinition:
    name: str
    title: str | None = None
    description: str | None = None
    input_schema: dict[str, Any] = field(default_factory=dict)


class MCPClientError(RuntimeError):
    pass


def command_exists(command: str) -> bool:
    if not command:
        return False
    candidate = Path(command)
    if candidate.is_file():
        return True
    return shutil.which(command) is not None


def load_mcp_server_configs(path: str | Path | None = None) -> list[MCPServerConfig]:
    config_path = Path(path or cfg.VEDA_MCP_SERVER_CONFIG)
    if not config_path.exists():
        return []
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[MCP] Could not read server config %s: %s", config_path, exc)
        return []

    items = raw.get("servers", []) if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return []

    servers: list[MCPServerConfig] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        command = str(item.get("command") or "").strip()
        if not name or not command:
            continue
        args = [str(arg) for arg in item.get("args", []) if str(arg).strip()]
        env = {
            str(key): _expand_env_value(value)
            for key, value in (item.get("env", {}) or {}).items()
            if str(key).strip()
        }
        cwd = str(item.get("cwd") or "").strip() or None
        if cwd:
            cwd_path = Path(cwd)
            if not cwd_path.is_absolute():
                cwd = str((cfg.PROJECT_ROOT / cwd_path).resolve())
        search_tools = [str(name) for name in item.get("search_tools", []) if str(name).strip()]
        servers.append(MCPServerConfig(
            name=name,
            command=command,
            args=args,
            env=env,
            cwd=cwd,
            transport=str(item.get("transport") or "stdio").strip() or "stdio",
            enabled=bool(item.get("enabled", True)),
            search_tools=search_tools,
        ))
    return servers


def _expand_env_value(value: Any) -> str:
    text = str(value)
    pieces: list[str] = []
    idx = 0
    while idx < len(text):
        if text[idx] == "$":
            if idx + 1 < len(text) and text[idx + 1] == "{":
                end = text.find("}", idx + 2)
                if end != -1:
                    key = text[idx + 2:end]
                    pieces.append(os.getenv(key, ""))
                    idx = end + 1
                    continue
            end = idx + 1
            while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                end += 1
            if end > idx + 1:
                pieces.append(os.getenv(text[idx + 1:end], ""))
                idx = end
                continue
        pieces.append(text[idx])
        idx += 1
    return "".join(pieces)


class MCPStdioClient:
    def __init__(self, server: MCPServerConfig, *, timeout_s: int | None = None):
        self._server = server
        self._timeout_s = int(timeout_s or cfg.VEDA_MCP_TIMEOUT_S)
        self._proc: subprocess.Popen[str] | None = None
        self._stdout_queue: queue.Queue[Any] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None
        self._next_id = 1

    def __enter__(self) -> MCPStdioClient:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        if self._server.transport != "stdio":
            raise MCPClientError(f"Unsupported MCP transport: {self._server.transport}")
        if self._proc is not None:
            return
        command = [self._server.command, *self._server.args]
        env = os.environ.copy()
        env.update(self._server.env)
        self._proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=self._server.cwd or None,
            env=env,
        )
        self._reader_thread = threading.Thread(target=self._read_stdout, name=f"mcp-{self._server.name}-stdout", daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, name=f"mcp-{self._server.name}-stderr", daemon=True)
        self._reader_thread.start()
        self._stderr_thread.start()

    def initialize(self) -> dict[str, Any]:
        result = self.request("initialize", {
            "protocolVersion": cfg.VEDA_MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": cfg.VEDA_MCP_CLIENT_NAME,
                "version": "1.0.0",
            },
        })
        self.notify("notifications/initialized")
        return result

    def list_tools(self) -> list[MCPToolDefinition]:
        cursor: str | None = None
        tools: list[MCPToolDefinition] = []
        while True:
            params = {"cursor": cursor} if cursor else None
            result = self.request("tools/list", params)
            for tool in result.get("tools", []) or []:
                if not isinstance(tool, dict):
                    continue
                tools.append(MCPToolDefinition(
                    name=str(tool.get("name") or "").strip(),
                    title=str(tool.get("title") or "").strip() or None,
                    description=str(tool.get("description") or "").strip() or None,
                    input_schema=tool.get("inputSchema") or tool.get("input_schema") or {},
                ))
            cursor = str(result.get("nextCursor") or "").strip() or None
            if not cursor:
                break
        return [tool for tool in tools if tool.name]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        self._send(payload)
        deadline = time.monotonic() + self._timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MCPClientError(f"MCP request timed out: {self._server.name}:{method}")
            try:
                message = self._stdout_queue.get(timeout=remaining)
            except queue.Empty as exc:
                raise MCPClientError(f"MCP request timed out: {self._server.name}:{method}") from exc
            if message is None:
                raise MCPClientError(f"MCP server exited while waiting for {method}")
            if not isinstance(message, dict):
                continue
            if "id" not in message:
                continue
            if message.get("id") != request_id:
                logger.debug("[MCP] Ignoring out-of-order response from %s for id=%s", self._server.name, message.get("id"))
                continue
            if "error" in message:
                error = message["error"] or {}
                raise MCPClientError(f"{self._server.name}:{method}: {error}")
            result = message.get("result")
            if not isinstance(result, dict):
                return {}
            return result

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=1.0)
        except Exception:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()

    def _send(self, payload: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise MCPClientError("MCP client is not running.")
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self._proc.stdin.write(raw + "\n")
        self._proc.stdin.flush()

    def _read_stdout(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug("[MCP] Ignoring non-JSON stdout from %s: %s", self._server.name, line[:200])
                    continue
                if isinstance(parsed, list):
                    for item in parsed:
                        self._stdout_queue.put(item)
                else:
                    self._stdout_queue.put(parsed)
        finally:
            self._stdout_queue.put(None)

    def _read_stderr(self) -> None:
        proc = self._proc
        if proc is None or proc.stderr is None:
            return
        for line in proc.stderr:
            text = line.strip()
            if text:
                logger.debug("[MCP:%s] %s", self._server.name, text[:400])
