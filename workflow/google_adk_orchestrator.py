from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm
from google.adk.tools import FunctionTool

import sys
import json
import traceback
from pathlib import Path
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]
sys.path.insert(0, str(Path(__file__).parent))



# A2A Clients - Import async versions
from a_2_a.extractor_agent_a2a_client import call_extractor as async_call_extractor
from a_2_a.translation_agent_a2a_client import call_translator as async_call_translator
from a_2_a.validation_agent_a2a_client import call_validator as async_call_validator
from a_2_a.reporting_agent_a2a_client import call_reporter as async_call_reporter

# ---- Global Variables for Frontend ----
# Store orchestration results for UI access
orchestration_result = {
    "invoice_no": None,
    "validation_status": None,
    "invoice_info": {},
    "invoice_data": None,
    "line_items": [],
    "subtotal": None,
    "total": None,
    "tax_amount": None,
    "discrepancies": [],
    "extracted_text": None,
    "translated_text": None,
    "validation_data": None,
    "validation_report": [],
    "erp_data": {},
    "sufficient_data": False,
    "report_data": None
}

async def call_extractor(file_path: str) -> str:
    """Call the extractor agent via A2A to extract text from invoice files.
    
    Args:
        file_path: Full path to the invoice PDF file
        
    Returns:
        Extracted text from the invoice
    """
    global orchestration_result
    
    # Convert relative path to absolute if needed
    from pathlib import Path
    path_obj = Path(file_path)
    if not path_obj.is_absolute():
        # Try relative to project root
        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        if full_path.exists():
            file_path = str(full_path)
        else:
            file_path = str(path_obj.resolve())
    
    print(f"[Tool] Calling extractor with: {file_path}")
    result = await async_call_extractor(file_path)
    orchestration_result["extracted_text"] = result
    print(f"[Tool] Extractor returned {len(result)} characters")
    return result

async def call_translator(invoice_data: str) -> str:
    """Call the translation agent via A2A to translate invoice text to English.
    
    Args:
        invoice_data: Raw extracted invoice text
        
    Returns:
        Translated invoice text in English
    """
    global orchestration_result
    print(f"[Tool] Calling translator...")
    result = await async_call_translator(invoice_data)
    orchestration_result["translated_text"] = result
    print(f"[Tool] Translator completed")
    return result

async def call_validator(translated_data: str) -> str:
    """Call the validation agent via A2A to validate translated invoice data.
    
    Args:
        translated_data: Translated invoice text
        
    Returns:
        Validation result as JSON string
    """
    global orchestration_result
    print(f"[Tool] Calling validator...")
    result = await async_call_validator(translated_data)
    
    # Parse and store validation result for frontend
    try:
        validation_json = json.loads(result) if isinstance(result, str) else result
        
        # Store complete validation data
        orchestration_result["validation_data"] = validation_json
        
        # Extract key information from validation response
        if isinstance(validation_json, dict):
            # Validation status
            orchestration_result["validation_status"] = validation_json.get("validation_result", "unknown")
            
            # Store invoice raw data
            orchestration_result["invoice_data"] = validation_json.get("invoice_data", "")
            
            # Extract structured invoice data
            extracted = validation_json.get("extracted_invoice_data", {})
            if extracted:
                orchestration_result["invoice_no"] = extracted.get("invoice_no")
                orchestration_result["invoice_info"] = {
                    "invoice_no": extracted.get("invoice_no"),
                    "invoice_date": extracted.get("invoice_date"),
                    "po_number": extracted.get("po_number"),
                    "vendor_name": extracted.get("vendor_name"),
                    "currency": extracted.get("currency"),
                    "tax_amount": extracted.get("tax_amount"),
                    "total_amount": extracted.get("total_amount")
                }
                orchestration_result["line_items"] = extracted.get("line_items", [])
                orchestration_result["subtotal"] = extracted.get("subtotal")
                orchestration_result["total"] = extracted.get("total_amount")
                orchestration_result["tax_amount"] = extracted.get("tax_amount")
            
            # Store ERP data
            orchestration_result["erp_data"] = validation_json.get("erp_data", {})
            
            # Store sufficient data flag
            orchestration_result["sufficient_data"] = validation_json.get("sufficient_data", False)
            
            # Extract and categorize discrepancies from validation report
            validation_report = validation_json.get("validation_report", [])
            discrepancies = []
            
            for item in validation_report:
                if isinstance(item, dict):
                    # It's a structured discrepancy with issue details
                    discrepancies.append({
                        "item_code": item.get("item_code", ""),
                        "description": item.get("description", ""),
                        "issue": item.get("issue", ""),
                        "message": item.get("issue", "")
                    })
                elif isinstance(item, str):
                    # Check if it's a meaningful discrepancy message
                    lower_item = item.lower()
                    if any(keyword in lower_item for keyword in [
                        "discrepancy", "issue", "error", "mismatch", "missing",
                        "exceeds", "beyond tolerance", "required", "review"
                    ]):
                        if 'No' not in item() or 'no critical issue' not  in item().lower():
                            discrepancies.append({"message": item})
            
            orchestration_result["discrepancies"] = discrepancies
            orchestration_result["validation_report"] = validation_report
            
            print(f"[Tool] Parsed validation result:")
            print(f"  - Status: {orchestration_result['validation_status']}")
            print(f"  - Invoice No: {orchestration_result['invoice_no']}")
            print(f"  - Discrepancies found: {len(discrepancies)}")
            
    except json.JSONDecodeError as e:
        print(f"[Tool] JSON parsing error: {e}")
        orchestration_result["validation_status"] = "error"
        orchestration_result["discrepancies"] = [{"message": f"Failed to parse validation result: {str(e)}"}]
    except Exception as e:
        print(f"[Tool] Error parsing validation result: {e}")
        traceback.print_exc()
        orchestration_result["validation_status"] = "error"
        orchestration_result["discrepancies"] = [{"message": f"Error processing validation: {str(e)}"}]
    
    print(f"[Tool] Validator completed")
    return result

async def call_reporter(validation_data: str):
    """Call the reporting agent via A2A to generate a report.
    
    Args:
        validation_data: Validation result data
        
    Returns:
        Report generation result
    """
    global orchestration_result
    print(f"[Tool] Calling reporter...")
    result = await async_call_reporter(validation_data)
    orchestration_result["report_data"] = result
    print(f"[Tool] Reporter completed")
    return result

def save_for_human_review(execution_data: dict) -> str:
    """Save execution data for human review when validation requires manual inspection.
    
    Args:
        execution_data: Data that needs human review
        
    Returns:
        Confirmation message
    """
    import json
    import os
    from datetime import datetime
    
    print(f"[Tool] Saving for human review...")
    
    # Define the output file path
    output_dir = Path(__file__).parent.parent / "outputs"
    output_file = output_dir / "human_review.json"
    
    # Ensure the outputs directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp to the execution data
    review_item = {
        "timestamp": datetime.now().isoformat(),
        "data": execution_data
    }
    
    # Load existing data or create new list
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                review_queue = json.load(f)
                if not isinstance(review_queue, list):
                    review_queue = [review_queue]  # Convert to list if it's not
            except json.JSONDecodeError:
                review_queue = []
    else:
        review_queue = []
    
    # Append new review item
    review_queue.append(review_item)
    
    # Save back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(review_queue, f, indent=2, ensure_ascii=False)
    
    print(f"[Tool] Saved to {output_file} (Total items: {len(review_queue)})")
    return f"Execution data saved for human review. Total pending reviews: {len(review_queue)}"

# ---- LLM Model ----

model = LiteLlm(model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0", temperature=0)



# ---- Orchestrator Agent ----
orchestrator = Agent(
    model=model,
    name="invoice_orchestrator",
    instruction="""You are an invoice processing orchestrator that coordinates multiple specialized agents.

Your workflow MUST follow these exact steps:
1. First, call call_extractor with the file path to extract text from the invoice
2. Then, call call_translator with the extracted text to translate it to English
3. Next, call call_validator with the translated text to validate the invoice data
4. Finally:
   - If validation status is "accepted" or "rejected", call call_reporter with validation data
   - If validation status is "human_review", call save_for_human_review with the execution data

Always execute all steps in order. Pass the output from each step to the next step.""",
    description="Orchestrates invoice processing through extraction, translation, validation, and reporting",
    tools=[
        FunctionTool(call_extractor),
        FunctionTool(call_translator),
        FunctionTool(call_validator),
        FunctionTool(call_reporter),
        FunctionTool(save_for_human_review)
    ]
)



def run_orchestrator(invoice_path: str) -> dict:
    """Run the invoice processing orchestrator.
    
    Args:
        invoice_path: Path to the invoice file
        
    Returns:
        dict: Orchestration result containing invoice_no, validation_status, 
              invoice_info, line_items, subtotal, total, discrepancies
    """
    global orchestration_result
    
    # Reset the global result for new processing
    orchestration_result = {
        "invoice_no": None,
        "validation_status": None,
        "invoice_info": {},
        "invoice_data": None,
        "line_items": [],
        "subtotal": None,
        "total": None,
        "tax_amount": None,
        "discrepancies": [],
        "extracted_text": None,
        "translated_text": None,
        "validation_data": None,
        "validation_report": [],
        "erp_data": {},
        "sufficient_data": False,
        "report_data": None,
        "file_path": invoice_path,
        "success": False,
        "error": None
    }
    
    print("=" * 80)
    print("INVOICE PROCESSING ORCHESTRATOR")
    print("=" * 80)
    print(f"\nProcessing: {invoice_path}")
    print("-" * 80)
    
    # Simple direct execution
    from google.adk.apps import App
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService, Session
    from google.genai.types import Content, Part
    
    # Create app with the orchestrator
    app = App(
        name="invoice_processor",
        root_agent=orchestrator
    )
    
    # Create session service
    session_service = InMemorySessionService()
    
    # Create and register session
    user_id = "user_001"
    session_id = "session_001"
    
    session = session_service.create_session_sync(
        app_name=app.name,
        user_id=user_id,
        session_id=session_id
    )
    
    # Create runner
    runner = Runner(
        app=app,
        session_service=session_service
    )
    
    # Create request
    user_message = Content(
        parts=[Part(text=f"Process invoice from path: {invoice_path}")],
        role="user"
    )
    
    # Execute
    print("\n[Starting orchestration...]\n")
    try:
        for event in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            # Print agent responses
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(part.text)
        
        print("\n" + "=" * 80)
        print("PROCESSING COMPLETE")
        print("=" * 80)
        orchestration_result["success"] = True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        orchestration_result["success"] = False
        orchestration_result["error"] = str(e)
    
    return orchestration_result.copy()


def get_orchestration_result() -> dict:
    """Get the current orchestration result.
    
    Returns:
        dict: The current orchestration result
    """
    global orchestration_result
    return orchestration_result.copy()


async def process_human_review(invoice_no: str, review_decision: str, reason_note: str = ""):
    """Process a human review decision for a specific invoice.
    
    Args:
        invoice_no: Invoice number to process
        review_decision: Decision made by human reviewer ("accepted", "rejected")
        reason_note: Optional reason or notes for the decision
        
    Returns:
        Result message indicating success or failure
    """
    import json
    from pathlib import Path
    
    print(f"\n[Human Review] Processing invoice {invoice_no}...")
    print(f"[Human Review] Decision: {review_decision}")
    print(f"[Human Review] Notes: {reason_note}")
    
    output_file = Path(__file__).parent.parent / "outputs" / "human_review.json"
    
    # Check if file exists
    if not output_file.exists():
        print(f"❌ No human review file found at {output_file}")
        return "Error: Human review file not found"
    
    # Read the human review queue
    with open(output_file, 'r', encoding='utf-8-sig') as f:
        try:
            review_queue = json.load(f)
            if not isinstance(review_queue, list):
                print("❌ Invalid human review data format.")
                return "Error: Invalid data format"
        except json.JSONDecodeError as e:
            print(f"❌ Error reading human review data: {e}")
            return f"Error: Cannot read review data - {e}"
    
    # Find the invoice and process it
    updated_queue = []
    found = False
    invoice_data = None
    
    for item in review_queue:
        data = item.get("data", {})
        extracted_invoice = data.get("extracted_invoice_data", {})
        current_invoice_no = extracted_invoice.get("invoice_no")
        
        if current_invoice_no == invoice_no:
            found = True
            invoice_data = data
            
            # Add human response to the data
            from datetime import datetime
            data["human_response"] = {
                "status": review_decision,
                "notes": reason_note
            }
            
            # Update validation result based on human decision
            if review_decision.lower() in ["accepted", "approved"]:
                data["validation_result"] = "accepted"
            elif review_decision.lower() == "rejected":
                data["validation_result"] = "rejected"
            
            print(f"✓ Found invoice {invoice_no} in review queue")
            print(f"✓ Updated with human decision: {review_decision}")
            
            # Don't add to updated queue (remove from review list)
        else:
            # Keep other items in the queue
            updated_queue.append(item)
    
    if not found:
        print(f"❌ Invoice {invoice_no} not found in human review queue")
        return f"Error: Invoice {invoice_no} not found"
    
    # Save the updated queue (with the processed item removed)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(updated_queue, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Removed invoice from review queue")
    print(f"✓ Remaining items in queue: {len(updated_queue)}")
    
    # Call the reporter agent with the updated data
    print(f"\n[Human Review] Calling reporter agent to generate final report...")
    try:
        # Convert the data to JSON string for the reporter
        validation_data_json = json.dumps(invoice_data, indent=2)
        result = await call_reporter(validation_data_json)
        print(f"✓ Report generated successfully")
        return f"Success: Invoice {invoice_no} processed and report generated. {result}"
    except Exception as e:
        print(f"❌ Error calling reporter: {e}")
        import traceback
        traceback.print_exc()
        return f"Partial success: Invoice processed but report generation failed: {str(e)}"


# if __name__ == "__main__":
#     import asyncio
    
#     print("=" * 80)
#     print("TESTING HUMAN REVIEW PROCESSING")
#     print("=" * 80)
    
#     # Test the process_human_review function
#     result = asyncio.run(process_human_review("INV-1001", "accepted", "acceptable."))
    
#     print("\n" + "=" * 80)
#     print(f"RESULT: {result}")
#     print("=" * 80)

# if __name__ == "__main__":
#     import asyncio
    
#     print("=" * 80)
#     print("TESTING INVOICE ORCHESTRATOR")
#     print("=" * 80)
    
#     # Test the run_orchestrator function with a sample invoice path
#     test_invoice_path = r"C:\Users\sachin.mourya\Desktop\AI_INVOICE_AUDITOR\data\incoming\INV_ES_003.pdf"
#     run_orchestrator(test_invoice_path)