"""
Minimal A2A Client - Calls Translation Agent
"""

from a2a.client import A2AClient
import asyncio
import httpx 
from uuid import uuid4  
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message



async def call_translator(invoice_text: str):
    """Call the translation agent via A2A."""
    base_url = 'http://localhost:9998'
    
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


def run_call_translator(invoice_text: str):
    return asyncio.run(call_translator(invoice_text))



# if __name__ == "__main__":
#     result = asyncio.run(call_translator("""
# Automatic Zoom
# HafenLogistik GmbH 
# Am Kai 55, Hamburg, Deutschland 
 
# Rechnungsnummer: RE-2025-004 
# Rechnungsdatum: 02.05.2025 
# Bestellnummer: PO-1004 
 
# ------------------------------------------------- 
# Artikelcode | Beschreibung       | Menge | Preis | Gesamt 
# ------------------------------------------------- 
# SKU-301     | Transportkisten    | 40    | 25.00€| 1000.00€ 
# SKU-302     | Sicherheitswesten  | 60    | 10.00€| 600.00€ 
# ------------------------------------------------- 
# Zwischensumme: 1600.00€ 
# MwSt (10%): 160.00€ 
# Gesamtbetrag: 1760.00€ 
# """))
#     print(f"Translated text: {result}")












