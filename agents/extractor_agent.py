"""
Extractor Agent - Extracts data from PDF, DOCX, PNG invoices using LLM with FastMCP
"""
import yaml
import json
from pathlib import Path
from litellm import completion
from typing import TypedDict
from langgraph.graph import START, END, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

class Agent(TypedDict):
    path: str
    content: str | None

class ExtractorAgent:
    def __init__(self):
        # Load persona configuration
        config_path = Path(__file__).parent.parent / "configs" / "persona_extraction_agent.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.model = self.config['model']
        self.temperature = self.config['temperature']
        self.max_tokens = self.config['max_tokens']
        
        # MCP server configuration
        self.mcp_server_script = Path(__file__).parent.parent / "mcp_tools" / "extraction_mcp_server.py"

    async def _call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Call MCP tool via stdio transport."""
        server_params = StdioServerParameters(
            command="python",
            args=[str(self.mcp_server_script)],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the tool
                result = await session.call_tool(tool_name, arguments)
                
                # Extract text from result
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return ""

    def _run_async(self, coro):
        """Run async coroutine, handling existing event loop."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, we need to run in a thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            # No event loop running, use asyncio.run
            return asyncio.run(coro)

    def tool_node(self, state: Agent) -> Agent:
        """Extract text using FastMCP tools."""
        file_path = state['path']
        print(f"Extracting raw text from: {file_path}")

        try:
            # Determine which MCP tool to use based on file extension
            if file_path.endswith('.pdf'):
                tool_name = "extract_pdf_text"
            elif file_path.endswith('.docx'):
                tool_name = "extract_docx_text"
            elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                print("Using OCR (Tesseract)...")
                tool_name = "extract_image_text_ocr"
            else:
                raise ValueError("Unsupported file format")
            
            # Call MCP tool asynchronously
            text = self._run_async(self._call_mcp_tool(tool_name, {"file_path": file_path}))
            
            print(f"Extracted: {text[:200]}...")  # Preview
            return {"path": file_path, "content": text}
            
        except Exception as e:
            print(f"MCP tool extraction error: {e}")
            raise

    def extraction_agent(self, file_path: str) -> str:
        """Extract raw text from invoice file using LangGraph with MCP tools."""
        graph = StateGraph(Agent)
        graph.add_node("tool_node", self.tool_node)
        graph.add_edge(START, "tool_node")
        graph.add_edge("tool_node", END)
        app = graph.compile()
        state = {"path": file_path, "content": None}
        result = app.invoke(state)
        return result["content"]

# if __name__ == "__main__":
#     # Example usage
#     agent = ExtractorAgent()
#     sample_file = "data\\incoming\\INV_DE_004.pdf"  # Update with actual file path
#     extracted_text = agent.extraction_agent(sample_file)
#     print("Final Extracted Text:")
#     print(extracted_text)













