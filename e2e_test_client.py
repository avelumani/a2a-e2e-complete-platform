"""End-to-end A2A test client against Orchestrator (http://localhost:8000)."""

import asyncio
import json
from uuid import uuid4
import httpx

ORCHESTRATOR_URL = "http://localhost:8000"


async def send_a2a_message(text: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        card_resp = await client.get(f"{ORCHESTRATOR_URL}/a2a/.well-known/agent-card.json")
        card_resp.raise_for_status()
        card = card_resp.json()
        print("Discovered AgentCard:", card["name"], "| Skills:", [s["id"] for s in card["skills"]])

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": uuid4().hex,
                    "parts": [{"kind": "text", "text": text}],
                }
            },
        }
        res = await client.post(f"{ORCHESTRATOR_URL}/a2a", json=payload)
        res.raise_for_status()
        data = res.json()
        return data["result"]["artifacts"][-1]["parts"][0]["text"]


async def main() -> None:
    print("=== 1. Ownership Support Query ===")
    print(await send_a2a_message("Who maintains this agent?"))

    print("\n=== 2. Short SQS Notification (Orchestrator -> Triage -> Allocation) ===")
    short_msg = json.dumps({
        "orderNumber": "4500099001",
        "sourceIdentfier": "SAP-SQS",
        "deliveryBlockStatusCode": "Z1",
        "isAllocationBlock": True,
    })
    print(await send_a2a_message(short_msg))

    print("\n=== 3. Multi-Order SAP Payload (Orchestrator -> Triage -> Allocation + Credit) ===")
    full_msg = json.dumps({
        "orders": [
            {"orderNumber": "4500099002", "blockType": "RSF TR", "orderItemQuantity": 50, "customerId": "CUST-101"},
            {"orderNumber": "4500099003", "blockType": "CREDIT", "orderItemQuantity": 15, "customerId": "CUST-202"},
        ]
    })
    print(await send_a2a_message(full_msg))


if __name__ == "__main__":
    asyncio.run(main())
