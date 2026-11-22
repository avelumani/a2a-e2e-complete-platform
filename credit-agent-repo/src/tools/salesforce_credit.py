import json
from uuid import uuid4
from langchain_core.tools import tool


@tool
def create_salesforce_credit_case(order_number: str, customer_id: str, block_code: str) -> str:
    """Create a Credit Review Case in Salesforce for a credit-blocked SAP order."""
    case_id = f"SF-CRED-{uuid4().hex[:6].upper()}"
    return json.dumps({
        "orderNumber": order_number,
        "caseId": case_id,
        "queue": "Enterprise_Credit_Risk",
        "customerId": customer_id,
        "blockCode": block_code,
        "status": "Credit hold routed to Credit Risk review",
    })
