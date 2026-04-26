"""
Basic A2A Server for Reporting Agent
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
from agents.reporting_agent import ReportingAgent


class ReportingAgentExecutor(AgentExecutor):
    """Reporting Agent Executor Implementation."""
    def __init__(self):
        self.reporter = ReportingAgent()

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute reporting request"""
        # Extract validation state JSON from the request message
        validation_state_json = ""
        for part in context.message.parts:
            # Part objects have a 'root' attribute that contains the actual data
            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                validation_state_json = part.root.text.strip()
                break
        
        print(f"Processing validation state for reporting...")
        
        try:
            # Parse validation state from JSON
            import json
            validation_state = json.loads(validation_state_json)
            
            # Generate audit report
            report_result = self.reporter.generate_audit_report(validation_state)
            
            # Convert result to JSON string
            result_json = json.dumps(report_result, indent=2)
            
            # Send result back
            await event_queue.enqueue_event(new_agent_text_message(result_json))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            await event_queue.enqueue_event(new_agent_text_message(error_msg))

    @override
    async def cancel( self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')


if __name__ == '__main__':
    # Define agent skill
    skill = AgentSkill(
        id='reporting_skill',
        name='Invoice Reporting',
        description='Reports text from invoices',
        tags=['invoice', 'reporting', 'text'],
        examples=['Report  text from invoice.pdf', 'Process invoice document']
    )

    # Define agent card
    agent_card = AgentCard(
        name='Reporting Agent',
        description='Invoice reporting service',
        url='http://localhost:9996/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )

    # Create request handler with executor
    request_handler = DefaultRequestHandler(
        agent_executor=ReportingAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    print("Starting A2A Server on http://localhost:9996")
    uvicorn.run(server.build(), host='0.0.0.0', port=9996)


