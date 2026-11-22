import json
from uuid import uuid4
from langchain_core.tools import tool


@tool
def create_salesforce_allocation_case(order_number: str, block_code: str, quantity: int) -> str:
    """Create an Allocation Case in Salesforce for a blocked SAP order."""
    case_id = f"SF-ALLOC-{uuid4().hex[:6].upper()}"
    return json.dumps({
        "orderNumber": order_number,
        "caseId": case_id,
        "queue": "Global_Supply_Allocation",
        "blockCode": block_code,
        "allocatedQuantity": quantity,
        "status": "Allocation block processed successfully",
    })
