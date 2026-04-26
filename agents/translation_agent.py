"""
Translation Agent - Translates invoices into English Formated Text using LLM
"""

import os
import yaml
from pathlib import Path
from litellm import completion
from langgraph.graph import StateGraph, START, END 
from typing import TypedDict

import litellm
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]




class AgentState(TypedDict):
    invoice_data: str 
    output_data: str 

class TranslationAgent:
    def __init__(self):
        # Load persona configuration
        config_path = Path(__file__).parent.parent / "configs" / "persona_translation_agent.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.model = self.config['model']
        self.temperature = self.config['temperature']
        self.max_tokens = self.config['max_tokens']
    
    def translate_raw_text(self, state: AgentState):
        """Translate raw text to English using unified prompt"""
        try:
            invoice_text = state.get('invoice_data', '')
            
            if not invoice_text:
                return {"output_data": ""}
            
            # Use unified translation prompt
            prompt = self.config['unified_translation_prompt'].format(text=invoice_text)
            
            # Make single LLM call
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.config['system_prompt']},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                metadata={
                    'agent':"translation"
                }
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {"output_data": translated_text}
                
        except Exception as e:
            print(f"❌ Translation error: {str(e)}")
            # Fail-safe: return original text if translation fails
            return {"output_data": state.get('invoice_data', '')}
    
    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node('translator', self.translate_raw_text)
        graph.add_edge(START, 'translator')
        graph.add_edge('translator', END)
        return graph.compile()

    def translation_agent(self, raw_text: str):
        graph = self._build_graph()
        initial_state: AgentState = {
            'invoice_data': raw_text,
            'output_data': ''
        }
        final_state = graph.invoke(initial_state)
        return {
            'translated_text': final_state['output_data']
        }