
"""
Indexing Agent - Simple FAISS indexing with Bedrock embeddings
"""
import json
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_aws import BedrockEmbeddings
from typing import TypedDict

class InvoiceMetadata(TypedDict):
    new_report: list[str]
    docs: list[Document]
    

class IndexingAgent:
    def __init__(self):
        # Initialize COHERE embeddings

        self.embeddings = BedrockEmbeddings(model_id='amazon.titan-embed-text-v1')
        
        self.vector_store_path = Path("./data/faiss_index")
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.invoice_data_path = Path("./data/invoices")
        
        # Load existing index or create new
        index_file = self.vector_store_path / "index.faiss"
        if index_file.exists():
            self.vector_store = FAISS.load_local(
                str(self.vector_store_path), 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"Loaded existing FAISS index")
        else:
            self.vector_store = None
            print(f"New FAISS index will be created")
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
    
    
    
    def load_report_tracker(self) -> dict:
        """Load report tracker JSON file"""
        tracker_path = Path("./outputs/report_tracker.json")
        if not tracker_path.exists():
            return {"total_reports": 0, "reports": []}
        
        with open(tracker_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_report_tracker(self, data: dict):
        """Save report tracker JSON file"""
        tracker_path = Path("./outputs/report_tracker.json")
        with open(tracker_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def clear_report_tracker(self):
        """Clear report tracker to empty state"""
        empty_tracker = {
            "total_reports": 0,
            "reports": []
        }
        self.save_report_tracker(empty_tracker)
        print("Report tracker cleared")
    
    def report_path_loader_node(self, state: InvoiceMetadata) -> InvoiceMetadata:
        """
        Node 1: Load report tracker and extract filenames
        Returns list of report file paths
        """
        print("=== Report Path Loader Node ===")
        tracker_data = self.load_report_tracker()
        
        if tracker_data["total_reports"] == 0:
            print("No new reports to index")
            return {"new_report": [], "docs": []}
        
        report_files = []
        reports_dir = Path("./outputs/reports")
        
        for report in tracker_data["reports"]:
            filename = report["filename"]
            report_path = reports_dir / filename
            
            if report_path.exists():
                report_files.append(str(report_path))
                print(f"Found report: {filename}")
            else:
                print(f"Warning: Report file not found: {filename}")
        
        print(f"Total reports to process: {len(report_files)}")
        return {"new_report": report_files, "docs": []}
    
    def document_node(self, state: InvoiceMetadata) -> InvoiceMetadata:
        """
        Node 2: Create Document objects from report files
        Extracts text content and metadata from each JSON file
        """
        print("\n=== Document Creation Node ===")
        report_files = state["new_report"]
        documents = []
        
        for report_path in report_files:
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                # Create text content from the report data
                text_content = self._create_text_from_report(report_data)
                
                # Create metadata
                metadata = {
                    "source": report_path,
                    "report_id": report_data.get("report_id", "Unknown"),
                    "invoice_number": report_data.get("invoice_number", "Unknown"),
                    "vendor_name": report_data.get("vendor_name", "Unknown"),
                    "report_date": report_data.get("report_date", "Unknown"),
                    "validation_status": report_data.get("validation_status", "Unknown"),
                    "total_amount": report_data.get("total_amount", 0),
                    "currency": report_data.get("currency", "Unknown"),
                    "generated_at": report_data.get("generated_at", "Unknown")
                }
                
                # Create Document object
                doc = Document(page_content=text_content, metadata=metadata)
                documents.append(doc)
                print(f"Created document for: {metadata['invoice_number']}")
                
            except Exception as e:
                print(f"Error processing {report_path}: {str(e)}")
        
        print(f"Total documents created: {len(documents)}")
        return {"new_report": report_files, "docs": documents}
    
    def _create_text_from_report(self, report_data: dict) -> str:
        """Create searchable text content from report JSON"""
        parts = []
        
        # Add main fields
        parts.append(f"Report ID: {report_data.get('report_id', 'Unknown')}")
        parts.append(f"Invoice Number: {report_data.get('invoice_number', 'Unknown')}")
        parts.append(f"PO Number: {report_data.get('po_number', 'Unknown')}")
        parts.append(f"Vendor Name: {report_data.get('vendor_name', 'Unknown')}")
        parts.append(f"Report Date: {report_data.get('report_date', 'Unknown')}")
        parts.append(f"Validation Status: {report_data.get('validation_status', 'Unknown')}")
        parts.append(f"Total Amount: {report_data.get('total_amount', 0)} {report_data.get('currency', '')}")
        
        # Add summary
        if report_data.get('summary'):
            parts.append(f"\nSummary: {report_data['summary']}")
        
        # Add key findings
        if report_data.get('key_findings'):
            parts.append("\nKey Findings:")
            for finding in report_data['key_findings']:
                parts.append(f"- {finding}")
        
        # Add discrepancies
        if report_data.get('discrepancies'):
            parts.append("\nDiscrepancies:")
            if len(report_data['discrepancies']) == 0:
                parts.append("- No discrepancies found")
            else:
                for discrepancy in report_data['discrepancies']:
                    parts.append(f"- {discrepancy}")
        
        # Add recommendation
        if report_data.get('recommendation'):
            parts.append(f"\nRecommendation: {report_data['recommendation']}")
        
        # Add validation details
        if report_data.get('validation_details'):
            parts.append("\nValidation Details:")
            for detail in report_data['validation_details']:
                parts.append(f"- {detail}")
        
        # Add human review notes if present
        if report_data.get('human_review_notes'):
            parts.append(f"\nHuman Review Notes: {report_data['human_review_notes']}")
        
        return "\n".join(parts)
    
    def indexing_agent_node(self, state: InvoiceMetadata) -> InvoiceMetadata:
        """
        Node 3: Create embeddings and add to FAISS index
        Processes one document at a time and saves index
        """
        print("\n=== Indexing Agent Node ===")
        documents = state["docs"]
        
        if not documents:
            print("No documents to index")
            return state
        
        # Split documents into chunks
        all_chunks = []
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            all_chunks.extend(chunks)
            print(f"Split document {doc.metadata['invoice_number']} into {len(chunks)} chunks")
        
        print(f"Total chunks to index: {len(all_chunks)}")
        
        # Create or update FAISS index
        if self.vector_store is None:
            # Create new index with first batch
            print("Creating new FAISS index...")
            self.vector_store = FAISS.from_documents(all_chunks, self.embeddings)
        else:
            # Add to existing index
            print("Adding to existing FAISS index...")
            self.vector_store.add_documents(all_chunks)
        
        # Save index to disk
        self.vector_store.save_local(str(self.vector_store_path))
        print(f"FAISS index saved to {self.vector_store_path}")
        
        # Clear report tracker
        self.clear_report_tracker()
        
        print("Indexing completed successfully!")
        return state
    
    def run_indexing_pipeline(self):
        """
        Run the complete indexing pipeline:
        1. Load report tracker and get file paths
        2. Create Document objects from reports
        3. Create embeddings and add to FAISS index
        4. Clear report tracker
        """
        print("\n" + "="*50)
        print("STARTING INDEXING PIPELINE")
        print("="*50 + "\n")
        
        # Initialize state
        state: InvoiceMetadata = {"new_report": [], "docs": []}
        
        # Step 1: Load report paths
        state = self.report_path_loader_node(state)
        
        if not state["new_report"]:
            print("\nNo reports to process. Pipeline complete.")
            return
        
        # Step 2: Create documents
        state = self.document_node(state)
        
        # Step 3: Index documents
        state = self.indexing_agent_node(state)
        
        print("\n" + "="*50)
        print("INDEXING PIPELINE COMPLETED")
        print("="*50 + "\n")
    
    def get_retriever(self):
        """Get FAISS retriever"""
        if self.vector_store is None:
            return None
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 50})
        return retriever


# # Example usage
# if __name__ == "__main__":
#     agent = IndexingAgent()
#     agent.run_indexing_pipeline()
