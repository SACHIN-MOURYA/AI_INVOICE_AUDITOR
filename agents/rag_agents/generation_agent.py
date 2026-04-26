"""
Generation Agent - Generate answers using LLM
"""
from litellm import completion
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

class GenerationAgent:
    def __init__(self):
        self.model = "bedrock/cohere.command-r-plus-v1:0"
    
    def generate(self, query: str, retrieved_docs: list) -> str:
        """Generate answer from retrieved documents"""
        if not retrieved_docs:
            return "No relevant information found. Please process some invoices first."
        
        print(f"Generating answer...")
        
        # Create context from retrieved docs
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Create prompt
        prompt = f"""Based on the following invoice information, answer the question.
        Context:
        {context}      
        Question: {query}
        Answer:"""
        
        try:
            response = completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
                metadata={
                    'agent':"rag_generation_agent"
                }
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"Answer generated")
            return answer
            
        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error generating answer: {e}"






