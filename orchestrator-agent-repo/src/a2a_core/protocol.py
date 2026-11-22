"""Self-contained A2A (Agent-to-Agent) v0.3 Server & Remote Client library."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("a2a.core")


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


class AgentInterface(BaseModel):
    url: str
    protocol_binding: str = "JSONRPC"
    protocol_version: str = "0.3"


class AgentCapabilities(BaseModel):
    streaming: bool = False
    push_notifications: bool = False


class AgentCard(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    supported_interfaces: list[AgentInterface]
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    default_input_modes: list[str] = Field(default_factory=lambda: ["text", "text/plain"])
    default_output_modes: list[str] = Field(default_factory=lambda: ["text", "text/plain"])
    skills: list[AgentSkill] = Field(default_factory=list)


AgentHandler = Callable[[str, dict[str, Any]], Awaitable[str]]


def create_a2a_app(card: AgentCard, handler: AgentHandler) -> FastAPI:
    """Create a standalone A2A-compliant FastAPI service."""
    app = FastAPI(title=card.name, version=card.version)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "agent": card.name}

    @app.get("/a2a/.well-known/agent-card.json")
    @app.get("/.well-known/agent-card.json")
    async def get_agent_card() -> JSONResponse:
        return JSONResponse(
            content=card.model_dump(),
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    @app.post("/a2a")
    async def handle_jsonrpc(request: Request) -> JSONResponse:
        body = await request.json()
        rpc_id = body.get("id", str(uuid4()))
        method = body.get("method")
        params = body.get("params", {})

        if method != "message/send":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unsupported method '{method}'. Expected 'message/send'.",
                    },
                },
            )

        message = params.get("message", {})
        parts = message.get("parts", [])
        user_text = "\n".join(
            p.get("text", "") for p in parts if p.get("kind") == "text" or "text" in p
        ).strip()

        metadata = {
            "preferred_llm": request.headers.get("X-Preferred-LLM", ""),
            "message_id": message.get("messageId", str(uuid4())),
            "trace_id": request.headers.get("X-Trace-Id", ""),
        }

        try:
            reply_text = await handler(user_text, metadata)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "id": f"task-{uuid4().hex[:12]}",
                        "contextId": f"ctx-{uuid4().hex[:12]}",
                        "kind": "task",
                        "status": {
                            "state": "completed",
                            "message": {
                                "role": "agent",
                                "messageId": uuid4().hex,
                                "parts": [{"kind": "text", "text": reply_text}],
                            },
                        },
                        "artifacts": [
                            {
                                "artifactId": f"art-{uuid4().hex[:8]}",
                                "name": f"{card.name}-result",
                                "parts": [{"kind": "text", "text": reply_text}],
                            }
                        ],
                    },
                }
            )
        except Exception as exc:
            logger.exception("Execution error in %s: %s", card.name, exc)
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32000, "message": str(exc)},
                },
            )

    return app


class A2ARemoteClient:
    """Discovers another repository's A2A AgentCard over HTTP and invokes its /a2a endpoint."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def discover(self) -> AgentCard:
        url = f"{self.base_url}/a2a/.well-known/agent-card.json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return AgentCard.model_validate(resp.json())

    async def send_text(self, text: str, preferred_llm: str | None = None) -> str:
        card = await self.discover()
        rpc_url = (
            card.supported_interfaces[0].url
            if card.supported_interfaces
            else f"{self.base_url}/a2a"
        )
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": uuid4().hex,
                    "parts": [{"kind": "text", "text": text}],
                }
            },
        }
        headers = {"Content-Type": "application/json"}
        if preferred_llm:
            headers["X-Preferred-LLM"] = preferred_llm

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(rpc_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        if "error" in data:
            raise RuntimeError(f"A2A Error from {card.name}: {data['error']}")

        result = data.get("result", {})
        artifacts = result.get("artifacts", [])
        if artifacts:
            return "".join(p.get("text", "") for p in artifacts[-1].get("parts", []))
        parts = result.get("status", {}).get("message", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
