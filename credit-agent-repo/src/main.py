import uvicorn
from src.a2a_core.protocol import AgentCard, AgentInterface, AgentSkill, create_a2a_app
from src.agent.config import PORT, PUBLIC_URL
from src.agent.graph import run_credit

card = AgentCard(
    name="credit-agent",
    description="Evaluates SAP credit blocks and creates Salesforce Credit Review Cases.",
    supported_interfaces=[AgentInterface(url=f"{PUBLIC_URL}/a2a")],
    skills=[
        AgentSkill(
            id="process-credit-block",
            name="Process Credit Block",
            description="Reviews customer credit exposure and creates a Salesforce Credit Case.",
            tags=["sap", "credit", "salesforce"],
        )
    ],
)

app = create_a2a_app(card=card, handler=run_credit)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
