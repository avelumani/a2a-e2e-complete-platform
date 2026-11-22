import uvicorn
from src.a2a_core.protocol import AgentCard, AgentInterface, AgentSkill, create_a2a_app
from src.agent.config import PORT, PUBLIC_URL
from src.agent.graph import run_allocation

card = AgentCard(
    name="allocation-agent",
    description="Resolves SAP inventory allocation blocks and creates Salesforce Allocation Cases.",
    supported_interfaces=[AgentInterface(url=f"{PUBLIC_URL}/a2a")],
    skills=[
        AgentSkill(
            id="process-allocation-block",
            name="Process Allocation Block",
            description="Allocates inventory and creates a Salesforce Case for ALLOCATION / RSF TR blocks.",
            tags=["sap", "allocation", "salesforce"],
        )
    ],
)

app = create_a2a_app(card=card, handler=run_allocation)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
