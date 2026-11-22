from langchain_core.tools import tool
from src.a2a_core.protocol import A2ARemoteClient
from src.agent.config import ALLOCATION_AGENT_URL, CREDIT_AGENT_URL

allocation_remote = A2ARemoteClient(ALLOCATION_AGENT_URL)
credit_remote = A2ARemoteClient(CREDIT_AGENT_URL)


@tool
async def route_to_allocation_agent(order_json: str) -> str:
    """Route ALLOCATION, ALLOCATION_BLOCK, or RSF TR order JSON to Allocation Agent."""
    return await allocation_remote.send_text(order_json)


@tool
async def route_to_credit_agent(order_json: str) -> str:
    """Route CREDIT block order JSON to Credit Agent."""
    return await credit_remote.send_text(order_json)
