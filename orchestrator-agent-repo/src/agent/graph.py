import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from src.a2a_core.observability import get_langfuse_callbacks
from src.agent.config import OPENAI_MODEL, SQUAD_NAME, USE_MOCK_LLM
from src.agent.prompts import get_system_prompt
from src.tools.triage_client import delegate_to_triage_agent, get_agent_owner, triage_remote


class OrchestratorState(TypedDict):
    user_text: str
    reply: str


async def orchestrator_node(state: OrchestratorState) -> dict[str, str]:
    text = state["user_text"].strip()
    if not text.startswith("{"):
        if any(k in text.lower() for k in ("owner", "maintains", "squad", "help")):
            owner = json.loads(get_agent_owner.invoke({}))
            return {
                "reply": f"Maintained by {owner['squad']} (Slack: {owner['slack']}, On-call: {owner['oncall']})."
            }
        return {"reply": "Order Orchestrator ready. Send a short SQS order JSON or full SAP order payload."}

    parsed = json.loads(text)
    is_short = "isAllocationBlock" in parsed and "orders" not in parsed and "items" not in parsed

    triage_raw = await triage_remote.send_text(text)
    if is_short:
        return {"reply": triage_raw}

    triage_data = json.loads(triage_raw)
    results = triage_data.get("results", [])
    lines = []
    ok = 0
    for item in results:
        cid = item.get("caseId", "N/A")
        if cid != "N/A":
            ok += 1
        lines.append(f"Order {item.get('orderNumber', 'UNKNOWN')} - Case ID: {cid} - Status: {item.get('status', '')}")
    lines.append(f"{ok} of {len(results)} orders processed successfully")
    return {"reply": "\n".join(lines)}


def build_graph():
    if not USE_MOCK_LLM:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        return create_react_agent(
            llm,
            tools=[get_agent_owner, delegate_to_triage_agent],
            prompt=get_system_prompt(SQUAD_NAME),
        )
    builder = StateGraph(OrchestratorState)
    builder.add_node("orchestrate", orchestrator_node)
    builder.add_edge(START, "orchestrate")
    builder.add_edge("orchestrate", END)
    return builder.compile()


graph = build_graph()


async def run_orchestrator(user_text: str, metadata: dict) -> str:
    callbacks = get_langfuse_callbacks("order-orchestrator-agent", session_id=metadata.get("message_id"))
    config = {"callbacks": callbacks} if callbacks else {}
    if not USE_MOCK_LLM:
        res = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]}, config=config)
        return res["messages"][-1].content
    res = await graph.ainvoke({"user_text": user_text, "reply": ""}, config=config)
    return res["reply"]
