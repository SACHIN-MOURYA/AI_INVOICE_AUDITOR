"""
Minimal A2A Client - Calls Validation Agent
"""

from a2a.client import A2AClient
import asyncio
import httpx  # HTTP client for making async API requests
from uuid import uuid4  # Generate unique identifiers for messages and requests
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (  
    Message,  # Message structure for A2A communication
)


async def call_validator(invoice_text: str):
    """Call the validation agent via A2A."""
    base_url = 'http://localhost:9997'
    
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
                {'kind': 'text', 'text': invoice_text}
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

def run_call_validator(invoice_text: str):
    return asyncio.run(call_validator(invoice_text))

# Usage
# if __name__ == "__main__":
#     sample_invoice = """
# Automatic Zoom
# Global Logistics Ltd 
# 12 Harbor Street, London, UK 
 
# Invoice No: INV-1001 
# Invoice Date: 14 March 2025 
# PO Reference: PO-1001 
 
# ---------------------------------------------------- 
# Item Code | Description            | Qty | Unit | Total 
# ---------------------------------------------------- 
# SKU-001   | Pallet Wrapping Film   | 50  | 12.00| 600.00 
# SKU-002   | Industrial Gloves      |120  | 3.50 | 420.00 
# SKU-003   | Safety Helmets         | 30  |15.00 | 450.00 
# ---------------------------------------------------- 
# Subtotal: $1470.00 
# Tax (10%): $147.00 
# Total: $1617.00 
# ----------------------------------------------------  
# """
#     result = asyncio.run(call_validator(sample_invoice))
#     print(f"Validation result: {result}")












