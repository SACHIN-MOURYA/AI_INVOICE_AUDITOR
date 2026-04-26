"""
RAG Subgraph - LangGraph implementation of RAG pipeline with Indexing
"""
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from pathlib import Path
import json
import sys
import os
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

# Add parent directory to path for imports
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Try relative imports first, fall back to absolute
try:
    from .retrieval_agent import RetrievalAgent
    from .generation_agent import GenerationAgent
    from .reflection_agent import ReflectionAgent
    from .indexing_agent import IndexingAgent
except ImportError:
    from agents.rag_agents.retrieval_agent import RetrievalAgent
    from agents.rag_agents.generation_agent import GenerationAgent
    from agents.rag_agents.reflection_agent import ReflectionAgent
    from agents.rag_agents.indexing_agent import IndexingAgent

# Define the state schema
class RAGState(TypedDict):
    """State for RAG workflow"""
    query: str
    retrieved_docs: List
    answer: str
    sources: List[str]
    evaluation: dict
    error: str
    indexing_completed: bool
    new_reports_indexed: int

class RAGGraph:
    """LangGraph-based RAG workflow with automatic indexing"""
    
    def __init__(self, retriever=None):
        self.indexing_agent = IndexingAgent()
        
        # Use retriever from indexing agent if not provided
        if retriever is None:
            retriever = self.indexing_agent.get_retriever()
        
        self.retrieval_agent = RetrievalAgent(retriever)
        self.generation_agent = GenerationAgent()
        self.reflection_agent = ReflectionAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow with indexing check"""
        
        # Create graph
        workflow = StateGraph(RAGState)
        
        # Add nodes
        workflow.add_node("check_indexing", self._check_indexing_node)
        workflow.add_node("indexing", self._indexing_node)
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("generation", self._generation_node)
        workflow.add_node("reflection", self._reflection_node)
        
        # Add edges
        workflow.add_edge(START, "check_indexing")
        workflow.add_conditional_edges(
            "check_indexing",
            self._should_index,
            {
                "index": "indexing",
                "skip": "retrieval"
            }
        )
        workflow.add_edge("indexing", "retrieval")
        workflow.add_edge("retrieval", "generation")
        workflow.add_edge("generation", "reflection")
        workflow.add_edge("reflection", END)
        
        # Compile
        return workflow.compile()
    
    def _check_indexing_node(self, state: RAGState) -> RAGState:
        """Node: Check if there are new reports to index"""
        print(f"[Check Indexing Node] Checking for new reports...")
        
        tracker_path = Path("./outputs/report_tracker.json")
        
        if not tracker_path.exists():
            state["indexing_completed"] = False
            state["new_reports_indexed"] = 0
            return state
        
        try:
            with open(tracker_path, 'r', encoding='utf-8') as f:
                tracker_data = json.load(f)
            
            total_reports = tracker_data.get("total_reports", 0)
            state["new_reports_indexed"] = total_reports
            
            if total_reports > 0:
                print(f"Found {total_reports} new reports to index")
            else:
                print("No new reports to index")
            
        except Exception as e:
            print(f"Error checking report tracker: {str(e)}")
            state["new_reports_indexed"] = 0
        
        state["indexing_completed"] = False
        return state
    
    def _should_index(self, state: RAGState) -> str:
        """Decision: Should we run indexing?"""
        if state.get("new_reports_indexed", 0) > 0:
            return "index"
        return "skip"
    
    def _indexing_node(self, state: RAGState) -> RAGState:
        """Node: Run indexing pipeline for new reports"""
        print(f"[Indexing Node] Processing {state['new_reports_indexed']} new reports...")
        
        try:
            # Run the indexing pipeline
            self.indexing_agent.run_indexing_pipeline()
            
            # Update retriever with newly indexed data
            new_retriever = self.indexing_agent.get_retriever()
            if new_retriever:
                self.retrieval_agent.retriever = new_retriever
                print("Retriever updated with new indexed data")
            
            state["indexing_completed"] = True
            print(f"Successfully indexed {state['new_reports_indexed']} reports")
            
        except Exception as e:
            print(f"Error during indexing: {str(e)}")
            state["error"] = f"Indexing error: {str(e)}"
            state["indexing_completed"] = False
        
        return state
    
    def _retrieval_node(self, state: RAGState) -> RAGState:
        """Node: Retrieve relevant documents"""
        print(f"[Retrieval Node] Processing query...")
        
        query = state.get("query", "")
        docs = self.retrieval_agent.retrieve(query)
        
        state["retrieved_docs"] = docs
        
        if not docs:
            state["error"] = "No relevant documents found"
        
        return state
    
    def _generation_node(self, state: RAGState) -> RAGState:
        """Node: Generate answer"""
        print(f"[Generation Node] Generating answer...")
        
        query = state.get("query", "")
        docs = state.get("retrieved_docs", [])
        
        if not docs:
            state["answer"] = "No relevant information found."
            state["sources"] = []
            return state
        
        answer = self.generation_agent.generate(query, docs)
        
        # Extract sources
        sources = list(set([
            doc.metadata.get('invoice_no') for doc in docs if doc.metadata.get('invoice_no')
        ]))
        
        state["answer"] = answer
        state["sources"] = sources
        
        return state
    
    def _reflection_node(self, state: RAGState) -> RAGState:
        """Node: Evaluate answer quality"""
        print(f"🔬 [Reflection Node] Evaluating quality...")
        
        query = state.get("query", "")
        answer = state.get("answer", "")
        docs = state.get("retrieved_docs", [])
        
        evaluation = self.reflection_agent.evaluate(query, answer, docs)
        
        state["evaluation"] = evaluation
        
        return state
    
    def invoke(self, query: str) -> dict:
        """Execute RAG workflow with automatic indexing"""
        print(f"\n{'=' * 60}")
        print(f"RAG Subgraph Execution (with Auto-Indexing)")
        print(f"{'=' * 60}")
        
        # Initialize state
        initial_state = {
            "query": query,
            "retrieved_docs": [],
            "answer": "",
            "sources": [],
            "evaluation": {},
            "error": "",
            "indexing_completed": False,
            "new_reports_indexed": 0
        }
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "query": final_state.get("query"),
            "answer": final_state.get("answer"),
            "sources": final_state.get("sources", []),
            "evaluation": final_state.get("evaluation"),
            "error": final_state.get("error", ""),
            "indexing_completed": final_state.get("indexing_completed", False),
            "new_reports_indexed": final_state.get("new_reports_indexed", 0)
        }
    
    def get_graph(self):
        """Return compiled graph for integration"""
        return self.graph


# if __name__ == "__main__":
#     rag_graph = RAGGraph()
#     query = "What is the total amount due for invoice INV-1001?"
#     result = rag_graph.invoke(query)
    
#     print("\nFinal Result:")
#     print(json.dumps(result, indent=2))

























