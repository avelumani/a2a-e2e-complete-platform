import uvicorn
from src.a2a_core.protocol import AgentCard, AgentInterface, AgentSkill, create_a2a_app
from src.agent.config import PORT, PUBLIC_URL
from src.agent.graph import run_triage

card = AgentCard(
    name="order-triage-agent",
    description="Classifies SAP order blocks and routes them via A2A to Allocation or Credit.",
    supported_interfaces=[AgentInterface(url=f"{PUBLIC_URL}/a2a")],
    skills=[
        AgentSkill(
            id="triage-order-block",
            name="Triage Order Block",
            description="Routes ALLOCATION/RSF TR blocks to Allocation Agent and CREDIT blocks to Credit Agent.",
            tags=["triage", "routing", "sap"],
        )
    ],
)

app = create_a2a_app(card=card, handler=run_triage)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
