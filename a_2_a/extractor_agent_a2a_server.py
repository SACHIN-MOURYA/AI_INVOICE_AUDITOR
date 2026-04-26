




"""
Basic A2A Server for Extractor Agent
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
from agents.extractor_agent import ExtractorAgent


class ExtractorAgentExecutor(AgentExecutor):
    """Extractor Agent Executor Implementation."""

    def __init__(self):
        self.extractor = ExtractorAgent()

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute extraction request."""
        # Extract file path from the request message
        file_path = ""
        for part in context.message.parts:
            # Part objects have a 'root' attribute that contains the actual data
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                file_path = part.root.text.strip()
                break
        
        print(f"Processing: {file_path}")
        
        try:
            # Perform extraction
            extracted_text = self.extractor.extraction_agent(file_path)
            result = f"Extracted {len(extracted_text)} characters:\n{extracted_text[:500]}..."
            
            # Send result back
            await event_queue.enqueue_event(new_agent_text_message(result))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_msg))

    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')


if __name__ == '__main__':
    # Define agent skill
    skill = AgentSkill(
        id='extractor_skill',
        name='Invoice Extraction',
        description='Extracts text from invoices',
        tags=['invoice', 'extraction', 'text'],
        examples=['Extract text from invoice.pdf', 'Process invoice document']
    )

    # Define agent card
    agent_card = AgentCard(
        name='Extractor Agent',
        description='Invoice extraction service',
        url='http://localhost:9999/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    # Create request handler with executor
    request_handler = DefaultRequestHandler(
        agent_executor=ExtractorAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("Starting A2A Server on http://localhost:9999")
    uvicorn.run(server.build(), host='0.0.0.0', port=9999)

