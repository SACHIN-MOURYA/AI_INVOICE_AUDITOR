"""
Minimal A2A Client - Calls Extractor Agent
"""

from a2a.client import A2AClient
import asyncio
import httpx  # HTTP client for making async API requests
from uuid import uuid4  # Generate unique identifiers for messages and requests
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (  
    Message,  # Message structure for A2A communication
)


async def call_extractor(file_path: str):
    """Call the extractor agent via A2A."""
    base_url = 'http://localhost:9999'
    
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
                {'kind': 'text', 'text': file_path}
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

def run_call_extractor(file_path: str):
    return asyncio.run(call_extractor(file_path))

# Usage
# if __name__ == "__main__":
#     result = asyncio.run(call_extractor("/home/labuser/Desktop/AI_INVOICE_AUDITOR/data/incoming/INV_DE_004.pdf"))
#     print(f"Extracted text: {result}")










