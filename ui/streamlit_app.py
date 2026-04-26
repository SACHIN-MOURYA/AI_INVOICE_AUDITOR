"""
AI Invoice Auditor Dashboard
- 4-Tab Interface: Upload/Process, Human Review, RAG Chatbot, Reports
- Integrated with Google ADK Orchestrator
- Uses MonitorAgent for file watching
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import sys
import threading
import asyncio

# --- Imports ---
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "workflow"))
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))
from workflow.google_adk_orchestrator import run_orchestrator, process_human_review, get_orchestration_result
from agents.moniter_agent import MonitorAgent
from agents.rag_agents.rag_agent import RAGGraph

# --- Page Config ---
st.set_page_config(
    page_title="AI Invoice Auditor",
    page_icon="🤖",
    layout="wide"
)

# --- Custom Styles ---
def apply_custom_styles(dark_mode=False):
    """Inject theme-aware gradient background and UI styles."""
    bg_gradient = (
        "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)"
        if not dark_mode
        else "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
    )
    text_color = "#0f172a" if not dark_mode else "#f8fafc"
    card_bg = "rgba(255,255,255,0.85)" if not dark_mode else "rgba(30,41,59,0.85)"
    border_color = "#cbd5e1" if not dark_mode else "#334155"
    accent = "#2563eb" if not dark_mode else "#60a5fa"
    metric_bg = "rgba(226,232,240,0.6)" if not dark_mode else "rgba(51,65,85,0.6)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {bg_gradient};
            color: {text_color};
        }}
        .main {{
            padding: 1.5rem;
        }}
        /* Sidebar */
        div[data-testid="stSidebar"] {{
            background-color: {card_bg};
            border-right: 1px solid {border_color};
        }}
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(90deg, {accent} 0%, #3b82f6 100%);
            color: white;
            border: none;
            border-radius: 0.6rem;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(0,0.4,0,0.15);
        }}
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] button {{
            background: transparent;
            font-weight: 600 !important;
            border-bottom: 3px solid transparent;
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            color: {accent} !important;
            border-bottom: 3px solid {accent};
        }}
        /* Metrics */
        div[data-testid="stMetricValue"] {{
            color: {text_color} !important;
        }}
        div[data-testid="stMetric"] {{
            background-color: {metric_bg};
            border-radius: 0.8rem;
            padding: 0.6rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        /* Expanders */
        .stExpander {{
            background-color: {card_bg} !important;
            border-radius: 0.8rem;
            border: 1px solid {border_color};
            padding: 0.2rem;
        }}
        /* Dataframe tweaks */
        div[data-testid="stDataFrame"] {{
            border-radius: 0.6rem;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Persistent Queue File ---
NEW_INVOICES_QUEUE = Path("./data/new_invoices_queue.json")
HUMAN_REVIEW_FILE = Path("./outputs/human_review.json")
REPORTS_PATH = Path("./outputs/reports")

# --- Callback for Monitor Agent ---
def process_invoice_callback(file_path):
    """Add new invoice to queue file for Streamlit to pick up"""
    try:
        if NEW_INVOICES_QUEUE.exists():
            with open(NEW_INVOICES_QUEUE, 'r') as f:
                queue = json.load(f)
        else:
            queue = []
        if file_path not in queue:
            queue.append(file_path)
        NEW_INVOICES_QUEUE.parent.mkdir(parents=True, exist_ok=True)
        with open(NEW_INVOICES_QUEUE, 'w') as f:
            json.dump(queue, f)
    except Exception as e:
        print(f"Error adding to queue: {e}")

# --- Helper Functions ---
def load_human_review_queue():
    """Load human review queue from file"""
    if HUMAN_REVIEW_FILE.exists():
        try:
            with open(HUMAN_REVIEW_FILE, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            st.error(f"Error loading human review queue: {e}")
            return []
    return []

def load_reports():
    """Load all report files from outputs/reports"""
    reports = []
    if REPORTS_PATH.exists():
        report_files = sorted(list(REPORTS_PATH.glob("*.json")), key=lambda x: x.stat().st_mtime, reverse=True)
        for report_file in report_files:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    report_data['_filename'] = report_file.name
                    reports.append(report_data)
            except Exception as e:
                print(f"Error loading report {report_file.name}: {e}")
    return reports

def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# --- Initialize Session State ---
if 'monitor_started' not in st.session_state:
    st.session_state.monitor_started = False
    st.session_state.processed_results = []
    st.session_state.current_result = None
    st.session_state.chat_history = []
    st.session_state.rag_graph = None
    st.session_state.detected_files = []

# --- Start Monitor Agent ---
if not st.session_state.monitor_started:
    try:
        watch_path = Path("./data/incoming")
        watch_path.mkdir(parents=True, exist_ok=True)
        
        monitor = MonitorAgent(
            watch_path=str(watch_path),
            callback=process_invoice_callback
        )
        monitor_thread = threading.Thread(target=monitor.start, daemon=True)
        monitor_thread.start()
        st.session_state.monitor_started = True
    except Exception as e:
        st.error(f"Error starting monitor: {e}")

# --- Initialize RAG Graph ---
if st.session_state.rag_graph is None:
    try:
        st.session_state.rag_graph = RAGGraph()
    except Exception as e:
        print(f"Error initializing RAG graph: {e}")

# --- Header ---
st.title("📄 AI Invoice Auditor")
st.caption("Automated + Human-in-the-loop invoice validation system powered by Google ADK")
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ System Status")
    
    if st.session_state.monitor_started:
        st.success("✅ System Ready")
        st.success("📡 File Monitor Active")
        st.caption("📁 Watching: `./data/incoming/`")
    else:
        st.warning("⚠️ Monitor not started")

    # Dark Mode Toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=False)
    apply_custom_styles(dark_mode)

    st.markdown("---")
    
    # Metrics
    review_queue = load_human_review_queue()
    if review_queue:
        st.warning(f"⏸️ {len(review_queue)} awaiting review")
    else:
        st.info("✅ No pending reviews")
    
    reports = load_reports()
    st.metric("Total Reports", len(reports))
    
    # Check for queued files
    if NEW_INVOICES_QUEUE.exists():
        try:
            with open(NEW_INVOICES_QUEUE, 'r') as f:
                queued_files = json.load(f)
            if queued_files:
                st.info(f"📥 {len(queued_files)} file(s) detected")
                st.session_state.detected_files = queued_files
        except:
            pass
    
    st.markdown("---")
    st.info("💡 Upload invoices or drop them into `data/incoming/`")


# Main content - four tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload & Process", "⏸️ Human Review", "🤖 RAG Chatbot", "📋 Reports"])

# ==============================================================================
# TAB 1: Upload & Process Invoice
# ==============================================================================
with tab1:
    st.header("📤 Upload & Process Invoice")
    st.caption("Upload invoice files or process detected files from the watch folder")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose invoice file (PDF, DOCX, PNG, JPG)",
            type=['pdf', 'docx', 'png', 'jpg', 'jpeg'],
            key="invoice_uploader"
        )
        
        if uploaded_file:
            st.info(f"📄 Selected: **{uploaded_file.name}**")
            
            if st.button("🚀 Process Uploaded Invoice", type="primary", use_container_width=True):
                # Save file
                upload_path = Path("./data/incoming") / uploaded_file.name
                upload_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(upload_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Process through orchestrator
                with st.spinner("🔄 Processing invoice through orchestrator..."):
                    try:
                        result = run_orchestrator(str(upload_path))
                        st.session_state.current_result = result
                        st.session_state.processed_results.append(result)
                        
                        if result.get("success"):
                            st.success("✅ Processing Complete!")
                        else:
                            error_msg = result.get("error", "Unknown error")
                            st.error(f"❌ Processing failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error processing invoice: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                st.rerun()
    
    with col2:
        # Show detected files from monitor
        st.subheader("📁 Detected Files")
        
        if st.session_state.detected_files:
            for file_path in st.session_state.detected_files:
                file_name = Path(file_path).name
                st.write(f"• {file_name}")
            
            if st.button("🔄 Process All Detected", use_container_width=True):
                for file_path in st.session_state.detected_files:
                    if Path(file_path).exists():
                        with st.spinner(f"Processing {Path(file_path).name}..."):
                            try:
                                result = run_orchestrator(file_path)
                                st.session_state.processed_results.append(result)
                                st.session_state.current_result = result
                                
                                if not result.get("success"):
                                    st.error(f"Failed to process {Path(file_path).name}: {result.get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error: {e}")
                
                # Clear queue
                with open(NEW_INVOICES_QUEUE, 'w') as f:
                    json.dump([], f)
                st.session_state.detected_files = []
                st.success("✅ All files processed!")
                st.rerun()
        else:
            st.caption("No files detected yet")
    
    st.markdown("---")
    
    # Show current result
    if st.session_state.current_result:
        st.subheader("📋 Processing Result")
        result = st.session_state.current_result
        
        # Check for errors first
        if not result.get("success", True):
            st.error(f"❌ Processing Failed: {result.get('error', 'Unknown error')}")
            
            # Show what we have so far
            if result.get("extracted_text"):
                with st.expander("📄 Extracted Text (Before Error)"):
                    st.text_area("Extracted", result.get("extracted_text", "")[:1000], height=200, disabled=True)
            
            st.stop()
        
        # Status indicator
        status = result.get("validation_status", "unknown")
        if status is None:
            status = "processing"
        
        if status == "accepted":
            st.success(f"✅ Validation Status: **{status.upper()}**")
        elif status == "rejected":
            st.error(f"❌ Validation Status: **{status.upper()}**")
        elif status == "human_review":
            st.warning(f"⏸️ Validation Status: **PENDING HUMAN REVIEW**")
            st.info("👉 Go to **Human Review** tab to approve/reject")
        else:
            st.info(f"ℹ️ Validation Status: **{status.upper()}**")
        
        # Invoice Information
        col1, col2, col3, col4 = st.columns(4)
        
        info = result.get("invoice_info", {})
        with col1:
            st.metric("Invoice No", result.get("invoice_no") or info.get("invoice_no", "N/A"))
        with col2:
            st.metric("Vendor", info.get("vendor_name", "N/A"))
        with col3:
            st.metric("Subtotal", f"{info.get('currency', '$')} {result.get('subtotal', 0)}")
        with col4:
            st.metric("Total", f"{info.get('currency', '$')} {result.get('total', 0)}")
        
        # Line Items
        with st.expander("📦 Line Items", expanded=True):
            line_items = result.get("line_items", [])
            if line_items:
                df = pd.DataFrame(line_items)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No line items found")
        
        # Discrepancies
        with st.expander("⚠️ Discrepancies / Issues", expanded=True):
            discrepancies = result.get("discrepancies", [])
            if discrepancies:
                for disc in discrepancies:
                    if isinstance(disc, dict):
                        msg = disc.get("issue") or disc.get("message", str(disc))
                        item_code = disc.get("item_code", "")
                        desc = disc.get("description", "")
                        if item_code:
                            st.warning(f"**{item_code}** ({desc}): {msg}")
                        else:
                            st.warning(msg)
                    else:
                        st.warning(str(disc))
            else:
                st.success("✅ No discrepancies found")
        
        # Raw validation data
        with st.expander("🔍 Raw Validation Data"):
            st.json(result.get("validation_data", {}))


# ==============================================================================
# TAB 2: Human Review
# ==============================================================================
with tab2:
    st.header("⏸️ Human Review Queue")
    st.caption("Review and approve/reject invoices requiring manual verification")
    
    review_queue = load_human_review_queue()
    
    if review_queue:
        st.warning(f"⚠️ **{len(review_queue)} invoice(s) pending human review**")
        st.markdown("---")
        
        for idx, item in enumerate(review_queue):
            data = item.get("data", {})
            timestamp = item.get("timestamp", "Unknown")
            extracted = data.get("extracted_invoice_data", {})
            invoice_no = extracted.get("invoice_no", f"Unknown-{idx}")
            validation_report = data.get("validation_report", [])
            
            with st.expander(f"📄 **{invoice_no}** - Submitted: {timestamp}", expanded=True):
                # Invoice details
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Invoice No", invoice_no)
                with col2:
                    st.metric("Vendor", extracted.get("vendor_name", "N/A"))
                with col3:
                    subtotal = extracted.get("subtotal", 0)
                    currency = extracted.get("currency", "$")
                    st.metric("Subtotal", f"{currency} {subtotal}")
                with col4:
                    total = extracted.get("total_amount", 0)
                    st.metric("Total", f"{currency} {total}" if total else "N/A")
                
                # Line items
                st.subheader("📦 Line Items")
                line_items = extracted.get("line_items", [])
                if line_items:
                    df = pd.DataFrame(line_items)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No line items found")
                
                # Validation issues
                st.subheader("⚠️ Validation Issues (Why Human Review?)")
                if validation_report:
                    for report_item in validation_report:
                        if isinstance(report_item, dict):
                            item_code = report_item.get("item_code", "")
                            issue = report_item.get("issue", "")
                            desc = report_item.get("description", "")
                            st.error(f"**{item_code}** ({desc}): {issue}")
                        elif isinstance(report_item, str):
                            if "discrepancy" in report_item.lower() or "issue" in report_item.lower() or "review" in report_item.lower():
                                st.warning(report_item)
                            else:
                                st.info(report_item)
                else:
                    st.info("No specific validation issues listed")
                
                # ERP data comparison
                erp_data = data.get("erp_data", {})
                if erp_data:
                    with st.expander("📊 ERP Data Comparison"):
                        st.json(erp_data)
                
                st.markdown("---")
                st.subheader("🔧 Your Decision")
                
                # Decision form
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    decision = st.selectbox(
                        "Decision:",
                        ["approved", "rejected"],
                        key=f"decision_{invoice_no}_{idx}"
                    )
                    
                    reason = st.text_area(
                        "Reason / Notes:",
                        placeholder="Provide a reason for your decision...",
                        key=f"reason_{invoice_no}_{idx}",
                        height=100
                    )
                
                with col2:
                    st.write("")
                    st.write("")
                    st.write("")
                    if st.button("✅ Submit Decision", key=f"submit_{invoice_no}_{idx}", type="primary", use_container_width=True):
                        if reason.strip():
                            with st.spinner(f"Processing decision for {invoice_no}..."):
                                try:
                                    # Call async process_human_review
                                    result = run_async(process_human_review(invoice_no, decision, reason))
                                    
                                    if "Success" in result or "success" in result.lower():
                                        st.success(f"✅ {result}")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result}")
                                except Exception as e:
                                    st.error(f"❌ Error processing decision: {e}")
                        else:
                            st.warning("⚠️ Please provide a reason for your decision")
    
    else:
        st.success("✅ **No invoices awaiting review**")
        st.info("All invoices have been processed. New invoices requiring human review will appear here.")
        
        # Show recent history
        st.markdown("---")
        st.subheader("📜 Recent Processing History")
        if st.session_state.processed_results:
            for i, result in enumerate(reversed(st.session_state.processed_results[-5:])):
                invoice_no = result.get("invoice_no", "Unknown")
                status = result.get("validation_status", "unknown")
                st.write(f"• **{invoice_no}**: {status}")
        else:
            st.caption("No processing history yet")


# ==============================================================================
# TAB 3: RAG Chatbot
# ==============================================================================
with tab3:
    st.header("🤖 Invoice Query Assistant")
    st.caption("Ask questions about your processed invoices using RAG")
    
    # Check if RAG is available
    if st.session_state.rag_graph is None:
        st.warning("⚠️ RAG system not initialized. Processing some invoices first.")
    else:
        # Check for indexed reports
        reports = load_reports()
        
        if reports:
            # Stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📚 Indexed Reports", len(reports))
            with col2:
                approved = sum(1 for r in reports if r.get('validation_status', '').lower() == 'approved')
                st.metric("✅ Approved", approved)
            with col3:
                rejected = sum(1 for r in reports if r.get('validation_status', '').lower() == 'rejected')
                st.metric("❌ Rejected", rejected)
            
            st.markdown("---")
            
            # Chat history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history
            chat_container = st.container()
            with chat_container:
                for message in st.session_state.chat_history:
                    if message['role'] == 'user':
                        with st.chat_message("user", avatar="👤"):
                            st.write(message['content'])
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.write(message['content'])
                            if message.get('sources'):
                                with st.expander("📎 Sources"):
                                    st.caption(", ".join(message['sources']))
            
            # Chat input
            user_query = st.chat_input("Ask about your invoices... (e.g., What invoices were approved? Show me discrepancies)")
            
            if user_query:
                # Add user message
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_query
                })
                
                # Query RAG
                with st.spinner("🔍 Searching through invoices..."):
                    try:
                        rag_result = st.session_state.rag_graph.invoke(user_query)
                        answer = rag_result.get('answer', 'No answer found')
                        sources = rag_result.get('sources', [])
                        
                        # Add assistant response
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': answer,
                            'sources': sources
                        })
                    except Exception as e:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error querying RAG: {str(e)}",
                            'sources': []
                        })
                
                st.rerun()
            
            # Suggested questions
            st.markdown("---")
            st.subheader("💡 Suggested Questions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 Show all invoice summaries", use_container_width=True, key="q1"):
                    st.session_state.chat_history.append({'role': 'user', 'content': "Show all invoice summaries"})
                    try:
                        rag_result = st.session_state.rag_graph.invoke("Show all invoice summaries")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': rag_result.get('answer', 'No answer'),
                            'sources': rag_result.get('sources', [])
                        })
                    except Exception as e:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}", 'sources': []})
                    st.rerun()
                
                if st.button("💰 Total amounts by vendor", use_container_width=True, key="q2"):
                    st.session_state.chat_history.append({'role': 'user', 'content': "What are the total amounts by vendor?"})
                    try:
                        rag_result = st.session_state.rag_graph.invoke("What are the total amounts by vendor?")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': rag_result.get('answer', 'No answer'),
                            'sources': rag_result.get('sources', [])
                        })
                    except Exception as e:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}", 'sources': []})
                    st.rerun()
            
            with col2:
                if st.button("⚠️ Show all discrepancies", use_container_width=True, key="q3"):
                    st.session_state.chat_history.append({'role': 'user', 'content': "Show all discrepancies found in invoices"})
                    try:
                        rag_result = st.session_state.rag_graph.invoke("Show all discrepancies found in invoices")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': rag_result.get('answer', 'No answer'),
                            'sources': rag_result.get('sources', [])
                        })
                    except Exception as e:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}", 'sources': []})
                    st.rerun()
                
                if st.button("🏢 List all vendors", use_container_width=True, key="q4"):
                    st.session_state.chat_history.append({'role': 'user', 'content': "List all vendors from invoices"})
                    try:
                        rag_result = st.session_state.rag_graph.invoke("List all vendors from invoices")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': rag_result.get('answer', 'No answer'),
                            'sources': rag_result.get('sources', [])
                        })
                    except Exception as e:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}", 'sources': []})
                    st.rerun()
            
            # Clear chat
            if st.session_state.chat_history:
                st.markdown("---")
                if st.button("🗑️ Clear Chat History"):
                    st.session_state.chat_history = []
                    st.rerun()
        
        else:
            st.info("📭 No reports indexed yet. Process some invoices first to start querying!")
            st.caption("Once you process invoices and generate reports, you'll be able to ask questions about them here.")


# ==============================================================================
# TAB 4: Reports Archive
# ==============================================================================
with tab4:
    st.header("📋 Audit Reports Archive")
    st.caption("View all generated audit reports")
    
    reports = load_reports()
    
    if reports:
        st.success(f"📁 Found **{len(reports)}** audit report(s)")
        
        # Initialize selected report
        if 'selected_report' not in st.session_state:
            st.session_state.selected_report = None
        
        col_list, col_detail = st.columns([1, 2])
        
        with col_list:
            st.subheader("📑 Reports List")
            
            for i, report in enumerate(reports):
                invoice_no = report.get('invoice_number', 'Unknown')
                vendor = report.get('vendor_name', 'Unknown')
                status = report.get('validation_status', 'N/A').upper()
                generated_at = report.get('generated_at', '')
                
                # Parse timestamp
                if generated_at:
                    try:
                        dt = datetime.fromisoformat(generated_at)
                        date_str = dt.strftime("%b %d, %Y %H:%M")
                    except:
                        date_str = generated_at
                else:
                    date_str = "Unknown date"
                
                # Status indicator
                if status == 'APPROVED':
                    icon = "✅"
                elif status == 'REJECTED':
                    icon = "❌"
                else:
                    icon = "⚠️"
                
                button_label = f"{icon} {invoice_no}\n{vendor}\n{date_str}"
                
                if st.button(button_label, key=f"report_{i}", use_container_width=True):
                    st.session_state.selected_report = report
                    st.rerun()
        
        with col_detail:
            if st.session_state.selected_report:
                report = st.session_state.selected_report
                
                st.subheader("📄 Report Details")
                
                # Status badge
                status = report.get('validation_status', 'N/A').upper()
                if status == 'APPROVED':
                    st.success(f"✅ **{status}**")
                elif status == 'REJECTED':
                    st.error(f"❌ **{status}**")
                else:
                    st.warning(f"⚠️ **{status}**")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Invoice No", report.get('invoice_number', 'N/A'))
                with col2:
                    st.metric("PO Number", report.get('po_number', 'N/A'))
                with col3:
                    total = report.get('total_amount', 0)
                    currency = report.get('currency', '')
                    st.metric("Total", f"{currency} {total}")
                with col4:
                    st.metric("Vendor", report.get('vendor_name', 'N/A'))
                
                st.markdown("---")
                
                # Summary
                st.subheader("📝 Summary")
                st.write(report.get('summary', 'No summary available'))
                
                # Key Findings
                key_findings = report.get('key_findings', [])
                if key_findings:
                    st.subheader("🔍 Key Findings")
                    for finding in key_findings:
                        st.info(f"• {finding}")
                
                # Discrepancies
                discrepancies = report.get('discrepancies', [])
                with st.expander("⚠️ Discrepancies", expanded=len(discrepancies) > 0):
                    if discrepancies:
                        for disc in discrepancies:
                            st.warning(f"• {disc}")
                    else:
                        st.success("✅ No discrepancies found")
                
                # Recommendation
                st.subheader("💡 Recommendation")
                recommendation = report.get('recommendation', 'N/A')
                if 'approve' in recommendation.lower():
                    st.success(f"✅ {recommendation}")
                elif 'reject' in recommendation.lower():
                    st.error(f"❌ {recommendation}")
                else:
                    st.info(f"ℹ️ {recommendation}")
                
                # Validation Details
                validation_details = report.get('validation_details', [])
                if validation_details:
                    with st.expander("🔍 Validation Details"):
                        for detail in validation_details:
                            st.write(f"• {detail}")
                
                # Human Review Notes
                human_notes = report.get('human_review_notes')
                if human_notes:
                    st.subheader("👤 Human Review Notes")
                    st.info(human_notes)
                
                # Raw JSON
                with st.expander("🔧 Raw JSON Data"):
                    st.json(report)
            
            else:
                st.info("👈 Select a report from the list to view details")
    
    else:
        st.info("📭 No audit reports found")
        st.caption("Reports will appear here after processing invoices. Expected path: `outputs/reports/`")


# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>🤖 AI Invoice Auditor | Powered by Google ADK & LangGraph</div>",
    unsafe_allow_html=True
)
