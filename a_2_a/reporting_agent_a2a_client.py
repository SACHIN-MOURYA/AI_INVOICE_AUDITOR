"""
Minimal A2A Client - Calls Reporting Agent
"""

from a2a.client import A2AClient
import asyncio
import httpx  # HTTP client for making async API requests
from uuid import uuid4  # Generate unique identifiers for messages and requests
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (  
    Message,  # Message structure for A2A communication
)


async def call_reporter(validation_state_json: str):
    """Call the reporting agent via A2A."""
    base_url = 'http://localhost:9996'
    
    # Create httpx client with longer timeout for extraction tasks
    timeout = httpx.Timeout(300.0, connect=60.0)  # 5 minutes total, 1 minute connect
    
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        # Initialize A2ACardResolver to fetch and resolve the agent's card
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        
        agent_card = await resolver.get_agent_card()
        
        # Initialize the A2A client with the resolved agent card
        factory = ClientFactory(config=ClientConfig(httpx_client=httpx_client))
        client = factory.create(card=agent_card)
        
        print('Client initialized.')
        
        # Create message
        my_msg = Message(
            role='user',
            parts=[
                {'kind': 'text', 'text': validation_state_json}
            ],
            message_id=uuid4().hex,
        )
        
        # Send the message and wait for the complete response
        response = client.send_message(request=my_msg)
        
        result_text = ""
        async for res in response:
            print(f"Response: {res}")
            # Extract text from response parts
            for part in res.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    result_text += part.root.text
        
        return result_text

def run_call_reporter(validation_state_json):
    import json
    return asyncio.run(call_reporter(json.dumps(validation_state_json)))


# # Usage
# if __name__ == '__main__':
#     import json
    
#     # Sample validation state from validation agent
#     sample_validation_state = {
#   "invoice_data": "\nAutomatic Zoom\nGlobal Logistics Ltd \n12 Harbor Street, London, UK \n \nInvoice No: INV-1001 \nInvoice Date: 14 March 2025 \nPO Reference: PO-1001 \n \n---------------------------------------------------- \nItem Code | Description            | Qty | Unit | Total \n---------------------------------------------------- \nSKU-001   | Pallet Wrapping Film   | 50  | 12.00| 600.00 \nSKU-002   | Industrial Gloves      |120  | 3.50 | 420.00 \nSKU-003   | Safety Helmets         | 30  |15.00 | 450.00 \n---------------------------------------------------- \nSubtotal: $1470.00 \nTax (10%): $147.00 \nTotal: $1617.00 \n----------------------------------------------------  \n",
#   "extracted_invoice_data": {
#     "invoice_no": "INV-1001",
#     "invoice_date": "14 March 2025",
#     "po_number": "PO-1001",
#     "vendor_name": "Global Logistics Ltd",
#     "currency": "USD",
#     "subtotal": 1470.0,
#     "tax_amount": 147.0,
#     "total_amount": 1617.0,
#     "line_items": [
#       {
#         "item_code": "SKU-001",
#         "description": "Pallet Wrapping Film",
#         "qty": 50.0,
#         "unit_price": 12.0,
#         "total": 600.0
#       },
#       {
#         "item_code": "SKU-002",
#         "description": "Industrial Gloves",
#         "qty": 120.0,
#         "unit_price": 3.5,
#         "total": 420.0
#       },
#       {
#         "item_code": "SKU-003",
#         "description": "Safety Helmets",
#         "qty": 30.0,
#         "unit_price": 15.0,
#         "total": 450.0
#       }
#     ],
#     "raw_text": "\nAutomatic Zoom\nGlobal Logistics Ltd \n12 Harbor Street, London, UK \n \nInvoice No: INV-1001 \nInvoice Date: 14 March 2025 \nPO Reference: PO-1001 \n \n---------------------------------------------------- \nItem Code | Description            | Qty | Unit | Total \n---------------------------------------------------- \nSKU-001   | Pallet Wrapping Film   | 50  | 12.00| 600.00 \nSKU-002   | Industrial Gloves      |120  | 3.50 | 420.00 \nSKU-003   | Safety Helmets         | 30  |15.00 | 450.00 \n---------------------------------------------------- \nSubtotal: $1470.00 \nTax (10%): $147.00 \nTotal: $1617.00 \n----------------------------------------------------  \n"
#   },
#   "sufficient_data": True,
#   "erp_data": {
#     "po_number": "PO-1001",
#     "vendor_id": "VEND-001",
#     "line_items": [
#       {
#         "item_code": "SKU-001",
#         "description": "Pallet Wrapping Film",
#         "qty": 50.0,
#         "unit_price": 12.0,
#         "currency": "USD"
#       },
#       {
#         "item_code": "SKU-002",
#         "description": "Industrial Gloves",
#         "qty": 120.0,
#         "unit_price": 3.0,
#         "currency": "USD"
#       },
#       {
#         "item_code": "SKU-003",
#         "description": "Safety Helmets",
#         "qty": 30.0,
#         "unit_price": 15.0,
#         "currency": "USD"
#       }
#     ]
#   },
#   "validation_result": "human_review",
#   'human_response': {
#     'status': 'Approved',
#     'notes': 'The unit price discrepancy for Industrial Gloves is within acceptable tolerance'
#   },
#   "validation_report": [
#     "Currency Validation: Invoice currency (USD) matches ERP currency (USD) and is an accepted currency.",
#     "Line Item Validation:",
#     {
#       "item_code": "SKU-002",
#       "description": "Industrial Gloves",
#       "issue": "Unit price discrepancy. Invoice price: $3.50, ERP price: $3.00. Discrepancy is within the \u00b12% tolerance but requires review."
#     },
#     "Total Amount Validation:",
#     "Subtotal matches within tolerance ($1470.00).",
#     f"Tax amount matches (10% of subtotal, $147.00).",
#     "Total amount matches within tolerance ($1617.00)."
#   ]
# }
    
#     # Convert to JSON string
#     validation_json = json.dumps(sample_validation_state)
    
#     result = asyncio.run(call_reporter(validation_json))
#     print("Final Report Result:")
#     print(result)





















