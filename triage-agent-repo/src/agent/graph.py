import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from src.a2a_core.observability import get_langfuse_callbacks
from src.agent.config import OPENAI_MODEL, USE_MOCK_LLM
from src.tools.downstream_clients import (
    allocation_remote,
    credit_remote,
    route_to_allocation_agent,
    route_to_credit_agent,
)

ALLOCATION_CODES = {"ALLOCATION", "ALLOCATION_BLOCK", "RSF TR", "Z1"}
CREDIT_CODES = {"CREDIT", "CREDIT_BLOCK", "C1"}


class TriageState(TypedDict):
    raw_input: str
    orders: list[dict]
    is_short: bool
    results: list[dict]
    final_output: str


def enrich_node(state: TriageState) -> dict:
    payload = json.loads(state["raw_input"])
    is_short = "isAllocationBlock" in payload and "orders" not in payload and "items" not in payload
    if is_short:
        enriched = {
            "orderNumber": payload["orderNumber"],
            "sourceIdentfier": payload.get("sourceIdentfier", "SAP"),
            "deliveryBlockStatusCode": payload.get("deliveryBlockStatusCode", "ALLOCATION"),
            "isAllocationBlock": payload["isAllocationBlock"],
            "orderItemQuantity": 25,
            "customerId": "CUST-9001",
        }
        return {"orders": [enriched], "is_short": True}
    return {"orders": payload.get("orders", [payload]), "is_short": False}


async def route_node(state: TriageState) -> dict:
    results = []
    for order in state["orders"]:
        code = str(order.get("blockType") or order.get("deliveryBlockStatusCode") or "").upper()
        if order.get("isAllocationBlock") is True or code in ALLOCATION_CODES:
            res = json.loads(await allocation_remote.send_text(json.dumps(order)))
            res["routedTo"] = "allocation-agent"
            results.append(res)
        elif code in CREDIT_CODES:
            res = json.loads(await credit_remote.send_text(json.dumps(order)))
            res["routedTo"] = "credit-agent"
            results.append(res)
        else:
            results.append({
                "orderNumber": order.get("orderNumber", "UNKNOWN"),
                "caseId": "N/A",
                "routedTo": "none",
                "status": f"Not routed: unsupported block type '{code}'",
            })
    return {"results": results}


def format_node(state: TriageState) -> dict:
    if state["is_short"]:
        first = state["results"][0]
        return {
            "final_output": json.dumps({
                "receiptId": f"RCPT-{first['orderNumber']}",
                "orderNumber": first["orderNumber"],
                "routedTo": first["routedTo"],
                "caseId": first["caseId"],
                "status": first["status"],
            })
        }
    return {"final_output": json.dumps({"results": state["results"]})}


def build_graph():
    if not USE_MOCK_LLM:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        return create_react_agent(
            llm,
            tools=[route_to_allocation_agent, route_to_credit_agent],
            prompt=(
                "You are the Order Triage Agent. Route ALLOCATION, ALLOCATION_BLOCK, RSF TR, or "
                "isAllocationBlock=true orders to route_to_allocation_agent, and CREDIT orders to "
                "route_to_credit_agent. Return JSON {'results': [...]}."
            ),
        )
    builder = StateGraph(TriageState)
    builder.add_node("enrich", enrich_node)
    builder.add_node("route", route_node)
    builder.add_node("format", format_node)
    builder.add_edge(START, "enrich")
    builder.add_edge("enrich", "route")
    builder.add_edge("route", "format")
    builder.add_edge("format", END)
    return builder.compile()


graph = build_graph()


async def run_triage(user_text: str, metadata: dict) -> str:
    callbacks = get_langfuse_callbacks("order-triage-agent", session_id=metadata.get("message_id"))
    config = {"callbacks": callbacks} if callbacks else {}
    if not USE_MOCK_LLM:
        res = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]}, config=config)
        return res["messages"][-1].content
    res = await graph.ainvoke(
        {
            "raw_input": user_text,
            "orders": [],
            "is_short": False,
            "results": [],
            "final_output": "",
        },
        config=config,
    )
    return res["final_output"]
