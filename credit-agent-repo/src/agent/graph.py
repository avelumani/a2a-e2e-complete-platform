import json
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from src.a2a_core.observability import get_langfuse_callbacks
from src.agent.config import OPENAI_MODEL, USE_MOCK_LLM
from src.tools.salesforce_credit import create_salesforce_credit_case


class CreditState(TypedDict):
    raw_input: str
    output: str


def credit_node(state: CreditState) -> dict[str, str]:
    payload = json.loads(state["raw_input"])
    res = create_salesforce_credit_case.invoke({
        "order_number": str(payload.get("orderNumber", "UNKNOWN")),
        "customer_id": str(payload.get("customerId", "CUST-DEFAULT")),
        "block_code": str(payload.get("deliveryBlockStatusCode") or payload.get("blockType") or "CREDIT"),
    })
    return {"output": res}


def build_graph():
    if not USE_MOCK_LLM:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        return create_react_agent(
            llm,
            tools=[create_salesforce_credit_case],
            prompt="Extract orderNumber, customerId, and block code, call create_salesforce_credit_case, and return its JSON verbatim.",
        )
    builder = StateGraph(CreditState)
    builder.add_node("credit", credit_node)
    builder.add_edge(START, "credit")
    builder.add_edge("credit", END)
    return builder.compile()


graph = build_graph()


async def run_credit(user_text: str, metadata: dict) -> str:
    callbacks = get_langfuse_callbacks("credit-agent", session_id=metadata.get("message_id"))
    config = {"callbacks": callbacks} if callbacks else {}
    if not USE_MOCK_LLM:
        res = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]}, config=config)
        return res["messages"][-1].content
    res = await graph.ainvoke({"raw_input": user_text, "output": ""}, config=config)
    return res["output"]
