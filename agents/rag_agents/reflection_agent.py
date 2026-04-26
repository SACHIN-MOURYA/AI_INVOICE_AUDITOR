"""
Reflection Agent - Evaluate answer quality using RAG Triad
"""
from litellm import completion
import re
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

class ReflectionAgent:
    def __init__(self):
        self.model = "bedrock/cohere.command-r-plus-v1:0"  # Fixed model name
    
    def evaluate(self, query: str, answer: str, retrieved_docs: list) -> dict:
        """Evaluate using RAG Triad: Relevance, Groundedness, Context Relevance"""
        print(f"Evaluating answer quality (RAG Triad)...")
        
        context = "\n".join([doc.page_content[:200] for doc in retrieved_docs[:3]])
        
        prompt = f"""Evaluate this RAG system response on a scale of 1-5 for each criterion:
        Question: {query}
        Answer: {answer}
        Context: {context[:500]}
        
        Rate each:
        1. RELEVANCE (1-5): Does answer address the question?
        2. GROUNDEDNESS (1-5): Is answer supported by context?
        3. CONTEXT_RELEVANCE (1-5): Is context relevant to question?
        
        Format:
        RELEVANCE: X
        GROUNDEDNESS: X
        CONTEXT_RELEVANCE: X"""
        
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
                metadata={
                    'agent':"rag_reflection_agent"
                }
            )
            
            eval_text = response.choices[0].message.content
            scores = self._parse_scores(eval_text)
            
            print(f"Scores - Relevance: {scores['relevance']}, Groundedness: {scores['groundedness']}, Context: {scores['context_relevance']}")
            
            return scores
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            return {'relevance': 0, 'groundedness': 0, 'context_relevance': 0}
    
    def _parse_scores(self, text: str) -> dict:
        """Parse scores from evaluation"""
        scores = {}
        
        relevance = re.search(r'RELEVANCE:\s*(\d)', text)
        groundedness = re.search(r'GROUNDEDNESS:\s*(\d)', text)
        context_rel = re.search(r'CONTEXT_RELEVANCE:\s*(\d)', text)
        
        scores['relevance'] = int(relevance.group(1)) if relevance else 3
        scores['groundedness'] = int(groundedness.group(1)) if groundedness else 3
        scores['context_relevance'] = int(context_rel.group(1)) if context_rel else 3
        
        return scores