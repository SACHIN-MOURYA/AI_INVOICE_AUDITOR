# AI Invoice Auditor

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, multi-agent AI system for automated invoice auditing, validation, and reporting. Built with Google ADK, LangChain, and agent-to-agent (A2A) communication protocols.

## 🚀 Features

- **Intelligent Document Extraction**: Extract text and data from PDF, DOCX, and image invoices using advanced OCR and LLM processing
- **Multi-language Support**: Automatic translation of invoice content for global operations
- **ERP Integration**: Real-time validation against enterprise resource planning systems
- **Automated Reporting**: Generate comprehensive audit reports with discrepancy detection
- **Human-in-the-Loop Review**: Interactive dashboard for manual review and approval workflows
- **RAG-Powered Q&A**: Retrieval-augmented generation chatbot for invoice-related queries
- **Real-time Monitoring**: File system monitoring for automatic processing of new invoices
- **Modular Agent Architecture**: Scalable design with specialized agents for extraction, validation, translation, and reporting

## 🏗️ Architecture

The system employs a sophisticated multi-agent architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Extractor     │    │   Translator    │    │   Validator     │
│   Agent         │───▶│   Agent         │───▶│   Agent         │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Reporter      │
                    │   Agent         │
                    │                 │
                    └─────────────────┘
```

### Core Components

- **Agent-to-Agent (A2A) Communication**: Decentralized agent coordination using JSON-RPC
- **Google ADK Orchestrator**: Workflow management and agent lifecycle
- **MCP Tools**: Model Context Protocol for tool integration
- **RAG System**: Vector-based retrieval for intelligent Q&A
- **Streamlit Dashboard**: User-friendly web interface
- **Mock ERP**: Simulated enterprise system for testing

## 📋 Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for cloning the repository)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AI_INVOICE_AUDITOR
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirement.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory with necessary API keys and configurations:
   ```env
   # Example configuration
   GOOGLE_API_KEY=your_google_api_key
   LANGFUSE_PUBLIC_KEY=your_langfuse_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret
   ```

## 🚀 Usage

### Quick Start

1. **Start the complete system:**
   ```bash
   python main.py
   ```

   This will launch all services:
   - Mock ERP API (http://localhost:8001)
   - Extractor Agent (http://localhost:9999)
   - Translation Agent (http://localhost:9998)
   - Validation Agent (http://localhost:9997)
   - Reporting Agent (http://localhost:9996)
   - Streamlit Dashboard (http://localhost:8501)

2. **Access the dashboard:**
   Open your browser and navigate to http://localhost:8501

### Manual Service Startup

If you prefer to start services individually:

```bash
# Start Mock ERP
python mock_erp/app.py

# Start individual agents
python a_2_a/extractor_agent_a2a_server.py
python a_2_a/translation_agent_a2a_server.py
python a_2_a/validation_agent_a2a_server.py
python a_2_a/reporting_agent_a2a_server.py

# Start dashboard
streamlit run ui/streamlit_app.py --server.port=8501
```

## 📖 Dashboard Features

### 1. Upload & Process
- Upload invoice files (PDF, DOCX, PNG)
- Automatic processing through the agent pipeline
- Real-time status updates

### 2. Human Review
- Review processed invoices
- Manual validation and corrections
- Approval workflow management

### 3. RAG Chatbot
- Natural language queries about invoices
- Context-aware responses using vector retrieval
- Historical data access

### 4. Reports
- View generated audit reports
- Export functionality
- Discrepancy summaries

## ⚙️ Configuration

### Agent Personas

Configure agent behavior through YAML files in `configs/`:

- `persona_extraction_agent.yaml`: Extraction agent settings
- `persona_reporting_agent.yaml`: Reporting agent settings
- `persona_translation_agent.yaml`: Translation agent settings
- `rules.yaml`: Validation rules and thresholds

### Example Configuration

```yaml
# persona_extraction_agent.yaml
model: "gpt-4"
temperature: 0.1
max_tokens: 4000
extraction_prompt: "Extract invoice data accurately..."
```

## 🔧 Development

### Project Structure

```
AI_INVOICE_AUDITOR/
├── main.py                    # Main entry point
├── requirement.txt           # Python dependencies
├── a_2_a/                    # Agent-to-agent communication
├── agents/                   # Core agent implementations
│   ├── rag_agents/          # RAG system components
├── configs/                  # Configuration files
├── data/                     # Data storage and indices
├── mcp_tools/               # MCP server tools
├── mock_erp/                # Mock ERP system
├── outputs/                  # Generated reports and data
├── ui/                      # Streamlit dashboard
└── workflow/                # Orchestration logic
```

### Adding New Agents

1. Create agent implementation in `agents/`
2. Add A2A client/server in `a_2_a/`
3. Update orchestrator in `workflow/google_adk_orchestrator.py`
4. Add configuration in `configs/`

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/
```

## 📊 Monitoring & Logging

- **Langfuse Integration**: AI model performance tracking
- **File Monitoring**: Automatic processing of new invoices
- **Audit Trails**: Complete processing history
- **Error Handling**: Comprehensive error reporting and recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints for new functions
- Include comprehensive docstrings
- Write unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google ADK for agent orchestration
- LangChain for LLM integration
- Streamlit for the dashboard framework
- Open-source community for various tools and libraries

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in `docs/`
- Contact the development team

---

**Built with ❤️ using cutting-edge AI technologies**
