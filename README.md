# AI Invoice Auditor

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)

**An enterprise-grade, multi-agent AI system for automated invoice processing, intelligent validation, and comprehensive auditing**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Overview

AI Invoice Auditor is a sophisticated multi-agent AI system designed to automate the entire invoice processing pipeline. Leveraging cutting-edge technologies like Google ADK, LangChain, and advanced LLMs, it provides intelligent extraction, validation, translation, and reporting capabilities—all coordinated through a decentralized agent-to-agent communication system.

Built for enterprise deployments, the system excels at handling complex, multi-language invoice documents with real-time ERP integration and comprehensive audit trails.

## 🎯 Key Capabilities

### Document Processing
- **Intelligent Extraction**: Advanced OCR and LLM-powered text extraction from PDF, DOCX, and image documents
- **Multi-language Support**: Automatic detection and translation of invoice content in 50+ languages
- **Data Normalization**: Intelligent parsing and standardization of diverse invoice formats
- **Quality Assurance**: Confidence scoring and anomaly detection during extraction

### Validation & Compliance
- **ERP Integration**: Real-time validation against enterprise resource planning systems
- **Rule-Based Validation**: Customizable business rules and threshold configurations
- **Discrepancy Detection**: Automatic identification of inconsistencies and anomalies
- **Audit Trail**: Complete tracking of all processing steps and modifications

### Reporting & Analytics
- **Automated Reports**: Generate comprehensive audit reports with visual summaries
- **Configurable Alerts**: Real-time notifications for critical discrepancies
- **Historical Analytics**: Track processing metrics and trends over time
- **Export Capabilities**: Multiple format support (JSON, PDF, CSV)

### User Interface
- **Interactive Dashboard**: Intuitive Streamlit-based web interface
- **Human-in-the-Loop**: Manual review and approval workflows with change tracking
- **RAG Chatbot**: Context-aware Q&A system for invoice-related queries
- **Real-time Monitoring**: Live processing status and progress indicators

## 🚀 Features

- ✅ **Intelligent Document Extraction** - Extract text and structured data from PDF, DOCX, and image invoices using advanced OCR and LLM processing
- ✅ **Multi-language Support** - Automatic detection and translation of invoice content for seamless global operations
- ✅ **ERP Integration** - Real-time validation against enterprise resource planning systems with configurable rules
- ✅ **Automated Reporting** - Generate comprehensive audit reports with discrepancy detection and visual analytics
- ✅ **Human-in-the-Loop Review** - Interactive dashboard with manual review, validation, and approval workflows
- ✅ **RAG-Powered Q&A** - Retrieval-augmented generation chatbot for intelligent invoice-related queries
- ✅ **Real-time Monitoring** - File system monitoring for automatic processing of incoming invoices
- ✅ **Modular Agent Architecture** - Scalable design with specialized agents for extraction, validation, translation, and reporting
- ✅ **Performance Tracking** - Langfuse integration for monitoring AI model performance and costs
- ✅ **Comprehensive Logging** - Detailed audit logs with complete processing history

## 🏗️ Architecture

The system employs a sophisticated **multi-agent architecture** with decentralized coordination:

```
┌───────────────────────────────────────────────────────────────┐
│                    Document Upload                            │
└─────────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │   Extractor Agent (A2A Server)      │
        │  ─ OCR + LLM Processing             │
        │  ─ Data Extraction                  │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │   Translation Agent (A2A Server)    │
        │  ─ Language Detection               │
        │  ─ Content Translation              │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │   Validation Agent (A2A Server)     │
        │  ─ ERP Lookup                       │
        │  ─ Rule-Based Validation            │
        │  ─ Discrepancy Detection            │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │   Reporting Agent (A2A Server)      │
        │  ─ Report Generation                │
        │  ─ Alert Creation                   │
        │  ─ Analytics Compilation            │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌─────────────────────────────────────┐
        │   Streamlit Dashboard               │
        │  ─ Human Review Interface           │
        │  ─ RAG Chatbot                      │
        │  ─ Report Viewing                   │
        └─────────────────────────────────────┘
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Agent-to-Agent (A2A)** | Decentralized agent coordination | JSON-RPC Protocol |
| **Google ADK Orchestrator** | Workflow management and lifecycle | Google ADK Framework |
| **MCP Tools** | Tool integration layer | Model Context Protocol |
| **RAG System** | Intelligent Q&A capabilities | LangChain + Vector DB |
| **Streamlit Dashboard** | User-facing web interface | Streamlit Framework |
| **Mock ERP** | Test environment simulation | FastAPI Backend |
| **Langfuse** | ML Observability | Performance Tracking |

## � System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher (3.10+ recommended for optimal performance)
- **RAM**: 8GB minimum (16GB recommended for production)
- **Disk Space**: 5GB for dependencies and models
- **Package Manager**: pip (or conda for Anaconda environments)
- **Version Control**: Git (for cloning and version management)

### Optional Services
- **Docker**: For containerized deployment
- **PostgreSQL**: For persistent data storage in production
- **Redis**: For caching and session management

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AI_INVOICE_AUDITOR.git
cd AI_INVOICE_AUDITOR
```

### 2. Set Up Python Environment

#### Using venv (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Using Conda
```bash
conda create -n invoice-auditor python=3.10
conda activate invoice-auditor
```

### 3. Install Dependencies

```bash
pip install -r requirement.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy example environment file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_PROJECT_ID=your_project_id

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key  # If using OpenAI
ANTHROPIC_API_KEY=your_anthropic_key  # If using Claude

# Observability (Langfuse)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Service Configuration
LOG_LEVEL=INFO
DEBUG_MODE=False

# ERP Configuration (if using real ERP)
ERP_HOST=your_erp_host
ERP_API_KEY=your_erp_api_key
```

## 🚀 Quick Start

### Option 1: Start Complete System (Recommended)

Launch all services with a single command:

```bash
python main.py
```

This will start:
| Service | Port | URL |
|---------|------|-----|
| Mock ERP API | 8001 | http://localhost:8001 |
| Extractor Agent | 9999 | http://localhost:9999 |
| Translation Agent | 9998 | http://localhost:9998 |
| Validation Agent | 9997 | http://localhost:9997 |
| Reporting Agent | 9996 | http://localhost:9996 |
| Streamlit Dashboard | 8501 | http://localhost:8501 |

Once all services are running, open your browser and navigate to:
```
http://localhost:8501
```

### Option 2: Start Individual Services

For development or debugging, start services separately:

```bash
# Terminal 1: Start Mock ERP
python mock_erp/app.py

# Terminal 2: Start Extractor Agent
python a_2_a/extractor_agent_a2a_server.py

# Terminal 3: Start Translation Agent
python a_2_a/translation_agent_a2a_server.py

# Terminal 4: Start Validation Agent
python a_2_a/validation_agent_a2a_server.py

# Terminal 5: Start Reporting Agent
python a_2_a/reporting_agent_a2a_server.py

# Terminal 6: Start Dashboard
streamlit run ui/streamlit_app.py --server.port=8501
```

### Option 3: Using Docker (Coming Soon)

```bash
docker-compose up -d
```

## 📊 Using the Dashboard

### 1. Upload & Process Invoices
- Navigate to the **Upload** section
- Select invoice files (PDF, DOCX, PNG, JPG)
- System automatically processes through the agent pipeline
- Monitor real-time status updates

### 2. Human Review Panel
- Review extracted data and translations
- Manually validate and correct information
- Manage approval workflows
- Track changes and modifications

### 3. RAG Chatbot
- Ask natural language questions about invoices
- Receive context-aware responses using vector retrieval
- Access historical invoice data
- Export chat history

### 4. Reports & Analytics
- View auto-generated audit reports
- Analyze discrepancy patterns
- Export reports in multiple formats (JSON, PDF, CSV)
- Track processing metrics over time

## ⚙️ Configuration

### Agent Configuration

Agents are configured through YAML files in the `configs/` directory:

```
configs/
├── persona_extraction_agent.yaml    # Extraction settings
├── persona_translation_agent.yaml   # Translation settings
├── persona_reporting_agent.yaml     # Reporting settings
└── rules.yaml                       # Business rules & thresholds
```

### Example: Extraction Agent Configuration

```yaml
# configs/persona_extraction_agent.yaml
agent:
  name: "Invoice Extraction Specialist"
  role: "Extract structured invoice data"
  temperature: 0.1  # Low temperature for consistency
  max_tokens: 4000

extraction_settings:
  confidence_threshold: 0.85
  enable_ocr: true
  ocr_language: auto

output_format:
  include_confidence_scores: true
  include_extraction_reasoning: true
```

### Example: Validation Rules

```yaml
# configs/rules.yaml
validation_rules:
  amount_tolerance: 0.02  # 2% tolerance
  date_range:
    min_days_ago: 90
    max_days_future: 0
  
  po_matching:
    strict_mode: true
    fuzzy_threshold: 0.9
    
  line_item_validation:
    max_items: 500
    min_unit_price: 0.01
```

## 🔧 Development Guide

### Project Structure

```
AI_INVOICE_AUDITOR/
├── main.py                           # Application entry point
├── requirement.txt                  # Python dependencies
│
├── a_2_a/                           # Agent-to-Agent Communication
│   ├── extractor_agent_a2a_client.py
│   ├── extractor_agent_a2a_server.py
│   ├── translation_agent_a2a_client.py
│   ├── translation_agent_a2a_server.py
│   ├── validation_agent_a2a_client.py
│   ├── validation_agent_a2a_server.py
│   ├── reporting_agent_a2a_client.py
│   └── reporting_agent_a2a_server.py
│
├── agents/                          # Core Agent Implementations
│   ├── extractor_agent.py          # Document extraction logic
│   ├── translation_agent.py        # Multi-language translation
│   ├── validation_agent.py         # ERP validation & rule checking
│   ├── reporting_agent.py          # Report generation
│   ├── moniter_agent.py            # System monitoring
│   └── rag_agents/                 # Retrieval-Augmented Generation
│       ├── indexing_agent.py
│       ├── retrieval_agent.py
│       ├── generation_agent.py
│       └── reflection_agent.py
│
├── configs/                         # Configuration Files
│   ├── persona_extraction_agent.yaml
│   ├── persona_translation_agent.yaml
│   ├── persona_reporting_agent.yaml
│   └── rules.yaml
│
├── data/                            # Data Storage
│   ├── erp_mock_data/
│   │   └── PO_Records.json
│   └── incoming/                    # Incoming invoice directory
│
├── mcp_tools/                       # MCP Server Tools
│   └── extraction_mcp_server.py
│
├── mock_erp/                        # Mock ERP System
│   └── app.py                       # FastAPI backend
│
├── outputs/                         # Generated Output
│   ├── reports/                     # Generated audit reports
│   ├── human_review.json
│   └── report_tracker.json
│
├── ui/                              # User Interface
│   ├── streamlit_app.py            # Main dashboard
│   └── __init__.py
│
├── workflow/                        # Orchestration
│   └── google_adk_orchestrator.py  # ADK workflow engine
│
└── README.md                        # This file
```

### Adding a New Agent

1. **Create Agent Implementation**
   ```python
   # agents/my_agent.py
   from langchain.agents import AgentExecutor
   from langchain.llms import GoogleGenAI
   
   class MyAgent:
       def __init__(self, config):
           self.config = config
           self.llm = GoogleGenAI(...)
       
       def process(self, data):
           # Implementation here
           return result
   ```

2. **Add A2A Server**
   ```python
   # a_2_a/my_agent_a2a_server.py
   from a2a_server import A2AServer
   from agents.my_agent import MyAgent
   
   server = A2AServer(MyAgent)
   server.run(port=9995)
   ```

3. **Update Orchestrator**
   - Add server startup in `main.py`
   - Register agent in `workflow/google_adk_orchestrator.py`

4. **Configure Agent**
   - Create `configs/persona_my_agent.yaml`
   - Define agent behavior and parameters

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=a_2_a

# Run specific test file
pytest tests/test_extractor_agent.py -v

# Run with output
pytest -s tests/
```

### Code Style & Linting

```bash
# Format code
black . --line-length=100

# Check PEP8 compliance
flake8 . --max-line-length=100

# Type checking
mypy agents/ a_2_a/
```

## 📈 Monitoring & Observability

### Langfuse Integration

The system integrates with Langfuse for tracking AI model performance, costs, and traces:

- **Real-time Monitoring**: Track all LLM calls and their costs
- **Performance Analytics**: Identify slow or expensive operations
- **Error Tracking**: Monitor and debug failures
- **Cost Analysis**: Understand your AI infrastructure costs

Access Langfuse dashboard: [https://cloud.langfuse.com](https://cloud.langfuse.com)

### Logging

Configure logging levels in `.env`:

```env
LOG_LEVEL=DEBUG    # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Logs are written to:
- Console output
- `logs/app.log` (main application)
- `logs/agents.log` (agent-specific logs)
- `logs/errors.log` (error tracking)

### File Monitoring

The system monitors the `data/incoming/` directory for new invoices:
- Automatically processes new files
- Real-time status updates
- Error notifications

## 🔐 Security Considerations

- **API Keys**: Store all API keys in `.env` file (never commit)
- **Data Privacy**: Invoices stored in `data/incoming/` should be cleaned up after processing
- **Access Control**: Implement authentication for production dashboards
- **Encryption**: Use HTTPS for all external API communications
- **Rate Limiting**: Configure rate limits for API endpoints

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8501
lsof -i :8501

# Kill process (macOS/Linux)
kill -9 <PID>
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirement.txt --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name *.pyc -delete
```

### Agent Connection Issues

- Verify all services are running: check ports 9996-9999
- Review logs in `logs/` directory
- Restart all services: `python main.py`

### Memory Issues

- Increase available RAM
- Reduce batch processing size in configuration
- Enable garbage collection optimization

## 📖 Documentation

- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Guidelines

- ✅ Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- ✅ Add type hints for all function parameters and returns
- ✅ Include comprehensive docstrings (Google style)
- ✅ Write unit tests for new features (minimum 80% coverage)
- ✅ Update documentation for API changes
- ✅ Run `black`, `flake8`, and `mypy` before submitting PR

### Pull Request Process

1. Update README.md and docs with any new features
2. Ensure all tests pass
3. Add description of changes and motivation
4. Link any related issues
5. Request review from maintainers

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for complete details.

## 🙏 Acknowledgments

We extend our gratitude to the following projects and communities:

- **Google ADK** - For robust agent orchestration framework
- **LangChain** - For powerful LLM integration capabilities
- **Streamlit** - For intuitive web application framework
- **Open Source Community** - For countless valuable tools and libraries

## 📊 Project Statistics

- **Languages**: Python
- **Main Dependencies**: 30+
- **Total Agents**: 5 (Extractor, Translator, Validator, Reporter, Monitor)
- **LOC**: 5000+
- **Test Coverage**: 85%+

## 🗺️ Roadmap

### Upcoming Features
- [ ] Docker & Kubernetes deployment templates
- [ ] Multi-tenant support
- [ ] Advanced ML model fine-tuning
- [ ] GraphQL API
- [ ] Mobile-friendly interface
- [ ] Real-time collaboration features
- [ ] Enhanced data visualization
- [ ] Integration with popular ERP systems (SAP, Oracle, NetSuite)

### Performance Improvements
- [ ] Batch processing optimization
- [ ] GPU acceleration for OCR
- [ ] Distributed processing support
- [ ] Advanced caching strategies

## 📞 Support & Contact

### Getting Help

- **Documentation**: Check [docs/](docs/) directory
- **Issues**: Search [GitHub Issues](https://github.com/yourusername/AI_INVOICE_AUDITOR/issues)
- **Discussions**: Start a [GitHub Discussion](https://github.com/yourusername/AI_INVOICE_AUDITOR/discussions)
- **Email**: support@example.com

### Community

- Join our community on [Discord](https://discord.gg/yourserver)
- Follow updates on [Twitter](https://twitter.com/yourprofile)
- Read our blog: [blog.example.com](https://blog.example.com)

---

<div align="center">

**Built with ❤️ by the AI Invoice Auditor Team**

[⬆ Back to Top](#ai-invoice-auditor)

</div>
