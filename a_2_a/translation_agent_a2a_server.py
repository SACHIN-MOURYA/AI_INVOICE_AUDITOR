"""
Basic A2A Server for Translation Agent
"""

import uvicorn
import sys
from pathlib import Path
from typing_extensions import override

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

sys.path.insert(0, str(Path(__file__).parent.parent ))
from agents.translation_agent import TranslationAgent


class TranslationAgentExecutor(AgentExecutor):
    """Translation Agent Executor Implementation."""
    def __init__(self):
        self.translator = TranslationAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute translation request"""
        # Extract file path from the request message
        invoice_text = ""
        for part in context.message.parts:
            # Part objects have a 'root' attribute that contains the actual data
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                invoice_text = part.root.text.strip()
                break
        
        print(f"Processing: {invoice_text}")
        
        try:
            # Perform translation
            translation_result = self.translator.translation_agent(invoice_text)
            translated_text = translation_result.get('translated_text', '')
            
            # Send result back
            await event_queue.enqueue_event(new_agent_text_message(translated_text))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_msg))

    @override
    async def cancel( self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')


if __name__ == '__main__':
    # Define agent skill
    skill = AgentSkill(
        id='translation_skill',
        name='Invoice Translation',
        description='Translates text from invoices',
        tags=['invoice', 'translation', 'text'],
        examples=['Translate text from invoice.pdf', 'Process invoice document']
    )

    # Define agent card
    agent_card = AgentCard(
        name='Translation Agent',
        description='Invoice translation service',
        url='http://localhost:9998/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    # Create request handler with executor
    request_handler = DefaultRequestHandler(
        agent_executor=TranslationAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("Starting A2A Server on http://localhost:9998")
    uvicorn.run(server.build(), host='0.0.0.0', port=9998)
