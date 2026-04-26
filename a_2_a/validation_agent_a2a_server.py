
"""
Basic A2A Server for Validation Agent
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
from agents.validation_agent import ValidationAgent


class ValidationAgentExecutor(AgentExecutor):
    """Validation Agent Executor Implementation."""
    def __init__(self):
        self.validator = ValidationAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute validation request"""
        # Extract file path from the request message
        invoice_text = ""
        for part in context.message.parts:
            # Part objects have a 'root' attribute that contains the actual data
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                invoice_text = part.root.text.strip()
                break

        try:
            # Perform validation
            validation_result = self.validator.validate_invoice_agent(invoice_text)
            # Convert result to JSON string
            import json
            result_json = json.dumps(validation_result, indent=2, ensure_ascii=True)
            # Send result back
            await event_queue.enqueue_event(new_agent_text_message(result_json))
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}"
            print(f"[ERROR] Validation failed: {traceback.format_exc()}")
            await event_queue.enqueue_event(new_agent_text_message(error_msg))

    @override
    async def cancel( self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')


if __name__ == '__main__':
    # Define agent skill
    skill = AgentSkill(
        id='validation_skill',
        name='Invoice Validation',
        description='Validates invoice data against ERP records',
        tags=['invoice', 'validation', 'erp'],
        examples=['Validate invoice data from invoice.pdf', 'Check invoice against ERP records']
    )

    # Define agent card
    agent_card = AgentCard(
        name='Validation Agent',
        description='Invoice validation service',
        url='http://localhost:9997/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    # Create request handler with executor
    request_handler = DefaultRequestHandler(
        agent_executor=ValidationAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("Starting A2A Server on http://localhost:9997")
    uvicorn.run(server.build(), host='0.0.0.0', port=9997)
