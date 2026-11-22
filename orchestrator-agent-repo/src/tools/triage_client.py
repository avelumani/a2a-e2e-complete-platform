import json
from langchain_core.tools import tool
from src.a2a_core.protocol import A2ARemoteClient
from src.agent.config import SQUAD_NAME, TRIAGE_AGENT_URL

triage_remote = A2ARemoteClient(TRIAGE_AGENT_URL)


@tool
def get_agent_owner() -> str:
    """Get owner and support contact details for this Orchestrator agent."""
    return json.dumps({
        "squad": SQUAD_NAME,
        "slack": "#o2c-orchestrator-support",
        "oncall": "o2c-oncall@example.com",
    })


@tool
async def delegate_to_triage_agent(raw_order_payload: str) -> str:
    """Forward the raw SAP order block JSON verbatim over A2A to the Triage Agent repository."""
    return await triage_remote.send_text(raw_order_payload)
