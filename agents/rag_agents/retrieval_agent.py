
"""
Retrieval Agent - Simple retrieval using FAISS retriever
"""

class RetrievalAgent:
    def __init__(self, retriever):
        self.retriever = retriever
    
    def retrieve(self, query: str):
        """Retrieve relevant documents for query"""
        if self.retriever is None:
            print("No documents indexed yet")
            return []
        
        print(f"Retrieving relevant chunks...")
        try:
            docs = self.retriever.get_relevant_documents(query)
            print(f"Retrieved {len(docs)} relevant chunks")
            return docs
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []
