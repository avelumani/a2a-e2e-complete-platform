import uvicorn
from src.a2a_core.protocol import AgentCard, AgentInterface, AgentSkill, create_a2a_app
from src.agent.config import PORT, PUBLIC_URL
from src.agent.graph import run_orchestrator

card = AgentCard(
    name="order-orchestrator-agent",
    description="Entry-point A2A orchestrator delegating SAP order blocks to Triage.",
    supported_interfaces=[AgentInterface(url=f"{PUBLIC_URL}/a2a")],
    skills=[
        AgentSkill(id="chat", name="Chat", description="General conversation", tags=["chat"]),
        AgentSkill(
            id="sqs-order-notification",
            name="Order block orchestration",
            description="Delegates short queue notifications and full order payloads to Triage Agent.",
            tags=["orchestration", "sap", "a2a"],
        ),
        AgentSkill(id="squad", name="Squad Info", description="Get agent owner/squad info", tags=["support"]),
    ],
)

app = create_a2a_app(card=card, handler=run_orchestrator)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
