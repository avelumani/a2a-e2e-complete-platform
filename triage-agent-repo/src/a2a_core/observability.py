"""Optional Langfuse callback factory for LangGraph ainvoke tracing."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("a2a.langfuse")


def get_langfuse_callbacks(agent_name: str, session_id: str | None = None) -> list[Any]:
    """Return a Langfuse CallbackHandler if valid keys are configured, else empty list."""
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    sk = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "")

    if not pk or not sk or "replace-me" in pk or "replace-me" in sk:
        return []

    try:
        from langfuse.callback import CallbackHandler

        handler = CallbackHandler(
            public_key=pk,
            secret_key=sk,
            host=host or None,
            trace_name=agent_name,
            session_id=session_id,
            tags=["a2a", "order-management", agent_name],
        )
        return [handler]
    except Exception as exc:
        logger.warning("Langfuse callback init skipped: %s", exc)
        return []
