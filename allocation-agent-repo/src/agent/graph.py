import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from src.a2a_core.observability import get_langfuse_callbacks
from src.agent.config import OPENAI_MODEL, USE_MOCK_LLM
from src.tools.salesforce_allocation import create_salesforce_allocation_case


class AllocationState(TypedDict):
    raw_input: str
    output: str


def allocation_node(state: AllocationState) -> dict[str, str]:
    payload = json.loads(state["raw_input"])
    res = create_salesforce_allocation_case.invoke({
        "order_number": str(payload.get("orderNumber", "UNKNOWN")),
        "block_code": str(payload.get("deliveryBlockStatusCode") or payload.get("blockType") or "ALLOCATION"),
        "quantity": int(payload.get("orderItemQuantity", 10)),
    })
    return {"output": res}


def build_graph():
    if not USE_MOCK_LLM:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        return create_react_agent(
            llm,
            tools=[create_salesforce_allocation_case],
            prompt="Extract orderNumber, block code, and orderItemQuantity, call create_salesforce_allocation_case, and return its JSON verbatim.",
        )
    builder = StateGraph(AllocationState)
    builder.add_node("allocate", allocation_node)
    builder.add_edge(START, "allocate")
    builder.add_edge("allocate", END)
    return builder.compile()


graph = build_graph()


async def run_allocation(user_text: str, metadata: dict) -> str:
    callbacks = get_langfuse_callbacks("allocation-agent", session_id=metadata.get("message_id"))
    config = {"callbacks": callbacks} if callbacks else {}
    if not USE_MOCK_LLM:
        res = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]}, config=config)
        return res["messages"][-1].content
    res = await graph.ainvoke({"raw_input": user_text, "output": ""}, config=config)
    return res["output"]
