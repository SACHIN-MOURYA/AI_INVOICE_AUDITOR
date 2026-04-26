"""
Validation Agent - Invoice Data Validation + Business Validation
"""
import yaml
from pathlib import Path
from typing import TypedDict, Dict, List, Any, Literal
from litellm import completion
import requests
from langgraph.graph import StateGraph, START, END 
import json
import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

class AgentState(TypedDict):
    invoice_data: str
    extracted_invoice_data: Dict
    sufficient_data: bool
    erp_data: Dict
    validation_result: Literal['Approved', 'Reject', 'human_review'] 
    validation_report: List[str]



class ValidationAgent:
    def __init__(self):
        # Load rules
        rules_path = Path(__file__).parent.parent / "configs" / "rules.yaml"
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        
        self.erp_url = "http://localhost:8001"
        self.tolerances = self.rules['tolerances']
        self.required_fields = self.rules['required_fields']
        self.accepted_currencies = self.rules['accepted_currencies']
        
        # Load model configuration from rules
        self.config = self.rules
        self.model = self.rules.get('model', 'bedrock/cohere.command-r-plus-v1:0')
        self.temperature = self.rules.get('temperature', 0.1)
        self.max_tokens = self.rules.get('max_tokens', 500)
    
    def extract_structured_data(self, state: AgentState) -> AgentState:
        """Extract structured invoice data using LLM."""
        print(f"Extracting structured data using LLM...")

        try:
            text = state.get('invoice_data', '')
            prompt = self.config["extraction_prompt"].format(text=text)
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.config["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                metadata={'agent':"validation_agent"}

            )

            json_str = response.choices[0].message.content.strip()

            # Clean markdown if present
            if json_str.startswith("```"):
                # Split by ``` and get the content between markers
                parts = json_str.split("```")
                if len(parts) >= 2:
                    json_str = parts[1]
                    # Remove language identifier if present
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                    elif json_str.startswith("JSON"):
                        json_str = json_str[4:]
                json_str = json_str.strip()
            
            # Remove any leading/trailing whitespace and newlines
            json_str = json_str.strip()
            
            # Find the actual JSON object boundaries
            start_idx = json_str.find('{')
            end_idx = json_str.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx + 1]
            
            print(f"DEBUG: Cleaned JSON string:\n{json_str[:200]}...")  # Print first 200 chars for debugging
            
            data = json.loads(json_str)
            data["raw_text"] = text

            print("Extracted Structured Invoice:", data)
            state['extracted_invoice_data'] = data
            return state

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            try:
                print(f"Problematic JSON string: {json_str[:500]}")
            except:
                print("Could not print JSON string")
            state['extracted_invoice_data'] = {}
            state['validation_report'] = [f"JSON parsing error: {e}"]
            state['validation_result'] = 'Reject'
            return state
        except Exception as e:
            print(f"LLM extraction error: {e}")
            import traceback
            traceback.print_exc()
            state['extracted_invoice_data'] = {}
            state['validation_report'] = [f"Extraction error: {e}"]
            state['validation_result'] = 'Reject'
            return state

    def data_validation(self, state: AgentState) -> AgentState:
        """Validate extracted invoice data has required fields."""
        data = state.get('extracted_invoice_data', {})
        
        if not data or not data.get('invoice_no') or not data.get('po_number'):
            return {
                'sufficient_data': False,
                'validation_result': 'Reject',
                'validation_report': ["Missing required invoice data (invoice number or PO number)."]
            }
        
        return {'sufficient_data': True}
    
    def route_for_invoice_sufficient_data(self, state: AgentState) -> str:
        """Route based on whether sufficient data was extracted."""
        return 'erp_fetcher' if state.get('sufficient_data', False) else END

    def tool_erp_data(self, state: AgentState) -> AgentState:
        """Fetch ERP data for the invoice PO number."""
        invoice_data = state.get('extracted_invoice_data', {})
        po_number = invoice_data.get('po_number', '')

        if not po_number:
            print("[WARNING] No PO number found for ERP lookup.")
            return {
                'erp_data': {},
                'validation_report': ["No PO number available for ERP lookup."],
                'validation_result': 'Reject'
            }
        
        try:
            print(f"[INFO] Fetching ERP data for PO: {po_number}")
            # Call the specific PO endpoint to get actual data
            response = requests.get(f"{self.erp_url}/po/{po_number}")
            response.raise_for_status()
            
            erp_data = response.json()
            
            print(f"[SUCCESS] ERP data fetched successfully")
            print("ERP Data:", erp_data)
            return {'erp_data': erp_data}
            
        except Exception as e:
            print(f"[ERROR] ERP fetch error: {e}")
            return {
                'erp_data': {},
                'validation_report': [f"Failed to fetch ERP data: {str(e)}"],
                'validation_result': 'Reject'
            }

    def validate_invoice_data(self, state: AgentState) -> AgentState:
        """
        Validate invoice against ERP using LLM-powered analysis.
        
        Validation checks:
        1. Currency matches and is accepted
        2. Line items exist in ERP with matching quantities/prices (within tolerance)
        3. Total amount matches (within tolerance)
        
        Results:
        - Approved: All checks pass
        - Reject: Critical mismatches beyond tolerance
        - human_review: Minor discrepancies within tolerance
        """
        invoice_data = state.get('extracted_invoice_data', {})
        erp_data = state.get('erp_data', {})
        
        if not erp_data:
            return {
                'validation_result': 'Reject',
                'validation_report': ["No ERP data available for validation."]
            }
        
        print("🔍 Running LLM-powered validation...")
        
        validation_prompt = f"""You are an expert invoice validation agent. Validate the invoice data against ERP data and business rules.

**Invoice Data:**
{json.dumps(invoice_data, indent=2)}

**ERP Data (Expected) or this data is used to validate invoice data**
{json.dumps(erp_data, indent=2)}

**Business Rules:**
- Accepted Currencies: {', '.join(self.accepted_currencies)}
- Quantity Tolerance: ±{self.tolerances.get('quantity_percentage', 5)}%
- Price Tolerance: ±{self.tolerances.get('price_percentage', 2)}%
- Total Amount Tolerance: ±${self.tolerances.get('total_amount_absolute', 10)}
- must have exact match of invoice number in invoice with erp invoice number or invoice no
- same number of line item as given in erp data

**Validation Steps:**
1. **check po number and invoive no is matched excatly with erp data this is must if any of the thing in invoice_no or po_number not matched or null in invoice data reject completly 
2. **Currency Validation**: Check if invoice currency is accepted and matches ERP currency
3. **Total Amount Validation**: Verify total amount matches ERP total within tolerance
4. **Equal line item**: invoice have same count of line item as ERP 



**Decision Rules:**
- **Approved**: All validations pass with no critical issues
- **Reject**: Any of these critical issues found:
  - Total amount mismatch beyond tolerance
  - subtotal or tax mismatches beyond tolerance
  - Missing required fields invoice number, PO number and line items compare to erp
- **human_review**:
  - if line_items have minor quantity/price discrepancies within tolerance
  - if line_items partially match but not fully
  - if currency mismatch but accepted currency
  - if total amount mismatch is within tolerance
  - Minor discrepancies within tolerance that need human attention
  - Missing non-critical fields
  - Currency not accepted or mismatch


Provide your response in the following JSON format:
{{
  "validation_result": "Approved" | "Reject" | "human_review",
  "validation_report": [
    "highlight any discrepancies or issues any if have been found"
  ]
}}

Be thorough and specific in your validation report."""

        try:
            response = completion(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a precise invoice validation expert. Analyze invoice data against ERP data and provide structured validation results in JSON format only."
                    },
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                metadata={'agent':"validation_agent"}
            )
            
            result_str = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if result_str.startswith("```"):
                parts = result_str.split("```")
                if len(parts) >= 2:
                    result_str = parts[1]
                    if result_str.startswith("json") or result_str.startswith("JSON"):
                        result_str = result_str[4:]
                result_str = result_str.strip()
            
            # Find the actual JSON object boundaries
            start_idx = result_str.find('{')
            end_idx = result_str.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                result_str = result_str[start_idx:end_idx + 1]
            
            result = json.loads(result_str)
            validation_result = result.get('validation_result', 'human_review')
            validation_report = result.get('validation_report', [])
            
            # Log result
            print(f"[RESULT] Validation Result: {validation_result}")
            
            return {
                'validation_result': validation_result,
                'validation_report': validation_report
            }
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing error in validation: {e}")
            print(f"Problematic JSON: {result_str[:500]}")
            return {
                'validation_result': 'human_review',
                'validation_report': [
                    f"JSON parsing error: {str(e)}",
                    "Manual review required"
                ]
            }
        except Exception as e:
            print(f"[ERROR] LLM validation error: {e}")
            return {
                'validation_result': 'human_review',
                'validation_report': [
                    f"Validation error: {str(e)}",
                    "Manual review required"
                ]
            }
    
    def _build_graph(self):
        """Build the validation workflow graph."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node('extractor', self.extract_structured_data)
        graph.add_node('data_validator', self.data_validation)
        graph.add_node('erp_fetcher', self.tool_erp_data)
        graph.add_node('validator', self.validate_invoice_data)

        # Build workflow
        graph.add_edge(START, 'extractor')
        graph.add_edge('extractor', 'data_validator')
        graph.add_conditional_edges(
            'data_validator', 
            self.route_for_invoice_sufficient_data, 
            {'erp_fetcher': 'erp_fetcher', END: END}
        )
        graph.add_edge('erp_fetcher', 'validator')
        graph.add_edge('validator', END)

        return graph.compile() 
    
    def validate_invoice_agent(self, raw_text: str) -> AgentState:
        """Main entry point - validate invoice from raw text."""
        print("\n" + "="*60)
        print("[START] Invoice Validation Workflow")
        print("="*60 + "\n")
        
        graph = self._build_graph()
        initial_state: AgentState = {
            'invoice_data': raw_text,
            'extracted_invoice_data': {},
            'sufficient_data': False,
            'erp_data': {},
            'validation_result': 'human_review',
            'validation_report': []
        }
        
        final_state = graph.invoke(initial_state)
        
        print("\n" + "="*60)
        print(f"[COMPLETE] Workflow Complete: {final_state.get('validation_result', 'Unknown')}")
        print("="*60 + "\n")
        
        return final_state
    

# if __name__ == "__main__":
#     agent = ValidationAgent()
    
#     sample_invoice_text = """

# 'HafenLogistik GmbH  \nAm Kai 55, Hamburg, Deutschland  \nInvoice Number: RE-2025-004  \nDate: 02.05.2025 
#  \nPurchase Order Number: PO-1004  \n-------------------------------------------------
#      \nItem Code | Description | Quantity | Price | Total  \n
#      -------------------------------------------------  \nSKU-301 | Transport Crates | 40 | 25.00€ | 1000.00€  \nSKU-302 | Safety Vests | 60 | 10.00€ | 600.00€  \n------------
#      -------------------------------------  \nSubtotal: 1600.00€  \nVAT (10%): 160.00€  \nTotal Amount: 1760.00€  \n...
# """ 
#     result = agent.validate_invoice_agent(sample_invoice_text)
#     print("Final Validation State:", json.dumps(result, indent=2))
