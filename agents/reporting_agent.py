"""
Reporting Agent - Generates concise audit reports using LLM
"""
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, TypedDict, Literal, List
from litellm import completion
from langgraph.graph import StateGraph, START, END
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]


class AgentState(TypedDict):
    extracted_invoice_data: Dict
    validation_result: Literal['Approved', 'Reject', 'human_review'] 
    human_response: None | Dict
    erp_data: Dict
    validation_report: List[str]
    audit_report: Dict
    report_saved: bool


class ReportingAgent:
    def __init__(self):
        # Load persona configuration
        config_path = Path(__file__).parent.parent / "configs" / "persona_reporting_agent.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.model = self.config['model']
        self.temperature = self.config['temperature']
        self.max_tokens = self.config['max_tokens']

        self.reports_dir = Path("./outputs/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Master report tracker file
        self.master_report_file = Path("./outputs") / "report_tracker.json"
    
    def generate_report(self, state: AgentState) -> AgentState:
        """Generate audit report using LLM based on validation results."""
        print("\n" + "="*60)
        print("[REPORT] Generating Audit Report")
        print("="*60 + "\n")
        
        extracted_data = state.get('extracted_invoice_data', {})
        validation_result = state.get('validation_result', 'human_review')
        validation_report = state.get('validation_report', [])
        erp_data = state.get('erp_data', {})
        human_response = state.get('human_response')
        
        # Build report generation prompt
        report_prompt = f"""You are an expert audit report generator. Create a comprehensive yet concise audit report for an invoice.

**Invoice Data:**
{json.dumps(extracted_data, indent=2)}

**ERP Data or internal data that used for verification when validation occurred:**
{json.dumps(erp_data, indent=2)}

**Validation Result:** {validation_result}

**Validation Report:**
{json.dumps(validation_report, indent=2)}

**Human Review Response:**
{json.dumps(human_response, indent=2) if human_response else "No human review provided either because all thing correct or rejected by system."}

Generate a professional audit report in the following JSON format:
{{
  "report_id": "RPT-[invoice_no]-[timestamp]",
  "invoice_number": "invoice number",
  "po_number": "PO number",
  "vendor_name": "vendor name",
  "report_date": "current date in YYYY-MM-DD format",
  "validation_status": "{validation_result}",
  "summary": "Brief summary of the audit findings (2-3 sentences)",
  "key_findings": [
    "Finding 1",
    "Finding 2"
  ],
  "discrepancies": [
    "List any discrepancies found, or empty array if none"
  ],
  "human_review_notes": "Notes from human review if applicable, otherwise null",
  "recommendation": "Final recommendation (Approve for payment / Reject / Hold for further review)",
  "total_amount": numeric_value,
  "currency": "currency code"
}}

Be precise and professional. Base your findings on the validation report."""

        try:
            response = completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional audit report generator. Create structured, accurate audit reports in JSON format."
                    },
                    {"role": "user", "content": report_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                metadata={'agent':"reporting_agent"}
            )
            
            report_str = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if report_str.startswith("```"):
                report_str = report_str.split("```")[1]
                if report_str.startswith("json"):
                    report_str = report_str[4:]
                report_str = report_str.strip()
            
            audit_report = json.loads(report_str)
            
            # Add metadata
            audit_report['generated_at'] = datetime.now().isoformat()
            audit_report['validation_details'] = validation_report
            
            print(f"[SUCCESS] Report generated: {audit_report.get('report_id', 'N/A')}")
            
            return {'audit_report': audit_report}
            
        except Exception as e:
            print(f"[ERROR] Report generation error: {e}")
            
            # Fallback report
            fallback_report = {
                "report_id": f"RPT-{extracted_data.get('invoice_no', 'UNKNOWN')}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "invoice_number": extracted_data.get('invoice_no'),
                "po_number": extracted_data.get('po_number'),
                "vendor_name": extracted_data.get('vendor_name'),
                "report_date": datetime.now().strftime('%Y-%m-%d'),
                "validation_status": validation_result,
                "summary": f"Audit completed with status: {validation_result}",
                "key_findings": validation_report,
                "discrepancies": [],
                "human_review_notes": str(human_response) if human_response else None,
                "recommendation": "No recommendation due to generation error",
                "total_amount": extracted_data.get('total_amount'),
                "currency": extracted_data.get('currency'),
                "generated_at": datetime.now().isoformat(),
                "validation_details": validation_report,
                "error": str(e)
            }
            
            return {'audit_report': fallback_report}
    
    def save_report(self, state: AgentState) -> AgentState:
        """Save the audit report as individual JSON file and update master tracker."""
        print("\n" + "="*60)
        print("[SAVE] Saving Audit Report")
        print("="*60 + "\n")
        
        audit_report = state.get('audit_report', {})
        
        if not audit_report:
            print("[ERROR] No audit report to save")
            return {'report_saved': False}
        
        try:
            # Generate unique filename
            report_id = audit_report.get('report_id', f"RPT-UNKNOWN-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            invoice_no = audit_report.get('invoice_number', 'UNKNOWN')
            filename = f"{invoice_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = self.reports_dir / filename
            
            # Save individual report
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(audit_report, f, indent=2, ensure_ascii=False)
            
            print(f"[SUCCESS] Individual report saved: {filename}")
            
            # Update master tracker
            self._update_master_tracker(report_id, filename, audit_report)
            
            return {'report_saved': True}
            
        except Exception as e:
            print(f"[ERROR] Report save error: {e}")
            return {'report_saved': False}
    
    def _update_master_tracker(self, report_id: str, filename: str, audit_report: Dict):
        """Update the master report tracker file."""
        try:
            # Load existing tracker or create new
            if self.master_report_file.exists():
                with open(self.master_report_file, 'r', encoding='utf-8') as f:
                    tracker = json.load(f)
            else:
                tracker = {
                    "created_at": datetime.now().isoformat(),
                    "total_reports": 0,
                    "reports": []
                }
            
            # Add new report entry
            tracker_entry = {
                "filename": filename,
                "generated_at": audit_report.get('generated_at'),
                "added_to_tracker_at": datetime.now().isoformat()
            }
            
            tracker['reports'].append(tracker_entry)
            tracker['total_reports'] = len(tracker['reports'])
            tracker['last_updated'] = datetime.now().isoformat()
            
            # Save updated tracker
            with open(self.master_report_file, 'w', encoding='utf-8') as f:
                json.dump(tracker, f, indent=2, ensure_ascii=False)
            
            print(f"[SUCCESS] Master tracker updated: {tracker['total_reports']} total reports")
            
        except Exception as e:
            print(f"[WARNING] Failed to update master tracker: {e}")
    
    def _build_graph(self):
        """Build the reporting workflow graph."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node('report_generator', self.generate_report)
        graph.add_node('report_saver', self.save_report)
        
        # Build workflow
        graph.add_edge(START, 'report_generator')
        graph.add_edge('report_generator', 'report_saver')
        graph.add_edge('report_saver', END)
        
        return graph.compile()
    
    def generate_audit_report(self, validation_state: AgentState) -> AgentState:
        """Main entry point - generate and save audit report."""
        print("\n" + "="*60)
        print("[START] Audit Report Generation Workflow")
        print("="*60 + "\n")
        
        graph = self._build_graph()
        
        # Initialize state with validation results
        initial_state: AgentState = {
            'extracted_invoice_data': validation_state.get('extracted_invoice_data', {}),
            'validation_result': validation_state.get('validation_result', 'human_review'),
            'validation_report': validation_state.get('validation_report', []),
            'erp_data': validation_state.get('erp_data', {}),
            'human_response': validation_state.get('human_response'),
            'audit_report': {},
            'report_saved': False
        }
        
        final_state = graph.invoke(initial_state)
        
        print("\n" + "="*60)
        print(f"[COMPLETE] Report Workflow Complete - Saved: {final_state.get('report_saved', False)}")
        print("="*60 + "\n")
        
        return final_state

   
# if __name__ == "__main__":
#     # Example usage
#     agent = ReportingAgent()
    
#     # Sample validation state
#     sample_validation_state: AgentState =  {
#   "invoice_data": "\nAutomatic Zoom\nGlobal Logistics Ltd \n12 Harbor Street, London, UK \n \nInvoice No: INV-1001 \nInvoice Date: 14 March 2025 \nPO Reference: PO-1001 \n \n---------------------------------------------------- \nItem Code | Description            | Qty | Unit | Total \n---------------------------------------------------- \nSKU-001   | Pallet Wrapping Film   | 50  | 12.00| 600.00 \nSKU-002   | Industrial Gloves      |120  | 3.50 | 420.00 \nSKU-003   | Safety Helmets         | 30  |15.00 | 450.00 \n---------------------------------------------------- \nSubtotal: $1470.00 \nTax (10%): $147.00 \nTotal: $1617.00 \n----------------------------------------------------  \n",
#   "extracted_invoice_data": {
#     "invoice_no": "INV-1001",
#     "invoice_date": "14 March 2025",
#     "po_number": "PO-1001",
#     "vendor_name": "Global Logistics Ltd",
#     "currency": "USD",
#     "subtotal": 1470.0,
#     "tax_amount": 147.0,
#     "total_amount": 1617.0,
#     "line_items": [
#       {
#         "item_code": "SKU-001",
#         "description": "Pallet Wrapping Film",
#         "qty": 50.0,
#         "unit_price": 12.0,
#         "total": 600.0
#       },
#       {
#         "item_code": "SKU-002",
#         "description": "Industrial Gloves",
#         "qty": 120.0,
#         "unit_price": 3.5,
#         "total": 420.0
#       },
#       {
#         "item_code": "SKU-003",
#         "description": "Safety Helmets",
#         "qty": 30.0,
#         "unit_price": 15.0,
#         "total": 450.0
#       }
#     ],
#     "raw_text": "\nAutomatic Zoom\nGlobal Logistics Ltd \n12 Harbor Street, London, UK \n \nInvoice No: INV-1001 \nInvoice Date: 14 March 2025 \nPO Reference: PO-1001 \n \n---------------------------------------------------- \nItem Code | Description            | Qty | Unit | Total \n---------------------------------------------------- \nSKU-001   | Pallet Wrapping Film   | 50  | 12.00| 600.00 \nSKU-002   | Industrial Gloves      |120  | 3.50 | 420.00 \nSKU-003   | Safety Helmets         | 30  |15.00 | 450.00 \n---------------------------------------------------- \nSubtotal: $1470.00 \nTax (10%): $147.00 \nTotal: $1617.00 \n----------------------------------------------------  \n"
#   },
#   "sufficient_data": True,
#   "erp_data": {
#     "po_number": "PO-1001",
#     "vendor_id": "VEND-001",
#     "line_items": [
#       {
#         "item_code": "SKU-001",
#         "description": "Pallet Wrapping Film",
#         "qty": 50.0,
#         "unit_price": 12.0,
#         "currency": "USD"
#       },
#       {
#         "item_code": "SKU-002",
#         "description": "Industrial Gloves",
#         "qty": 120.0,
#         "unit_price": 3.0,
#         "currency": "USD"
#       },
#       {
#         "item_code": "SKU-003",
#         "description": "Safety Helmets",
#         "qty": 30.0,
#         "unit_price": 15.0,
#         "currency": "USD"
#       }
#     ]
#   },
#   "validation_result": "human_review",
#   'human_response': {
#     'status': 'Approved',
#     'notes': 'The unit price discrepancy for Industrial Gloves is within acceptable tolerance'
#   },
#   "validation_report": [
#     "Currency Validation: Invoice currency (USD) matches ERP currency (USD) and is an accepted currency.",
#     "Line Item Validation:",
#     {
#       "item_code": "SKU-002",
#       "description": "Industrial Gloves",
#       "issue": "Unit price discrepancy. Invoice price: $3.50, ERP price: $3.00. Discrepancy is within the \u00b12% tolerance but requires review."
#     },
#     "Total Amount Validation:",
#     "Subtotal matches within tolerance ($1470.00).",
#     f"Tax amount matches (10% of subtotal, $147.00).",
#     "Total amount matches within tolerance ($1617.00)."
#   ]
# }
    
#     # Generate and save audit report
#     final_state = agent.generate_audit_report(sample_validation_state)


















