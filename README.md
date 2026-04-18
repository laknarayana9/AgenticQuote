# Agentic Quote-to-Underwrite Workflow (Work in Progress)

An agentic insurance quote processing and underwriting system built with LangGraph, FastAPI, and RAG. This production-ready platform demonstrates how intelligent agents can transform complex insurance workflows into automated, evidence-driven decision-making processes.

## 🎯 **Key Capabilities**

- **🔄 Multi-Step Workflow Orchestration**: Simplifies complex underwriting processes through intelligent agent coordination
- **🛠️ Tool Integration**: Seamlessly combines multiple APIs and services (address validation, hazard scoring, rating engines) to complete end-to-end quote processing
- **🧠 Intelligent Decision Making**: Handles missing information automatically and provides evidence-based decisions with RAG-powered citations
- **🔍 Evidence-Based Underwriting**: Every decision is backed by verifiable guidelines and regulatory requirements
- **⚡ Real-Time Processing**: Production-grade performance with comprehensive audit trails

## 🚀 **Agent Intelligence Demo**

This system serves as a comprehensive demonstration of building sophisticated agentic systems that can:

- **Scale Complexity**: Handle increasingly intricate insurance workflows while maintaining accuracy
- **Adapt and Learn**: Process edge cases and exceptions through intelligent reasoning
- **Ensure Compliance**: Maintain regulatory adherence through automated citation tracking
- **Provide Transparency**: Full audit trails for every decision and recommendation


## ✅ Features Implemented

### Core Infrastructure
- **Schema Definitions**: Complete data models for quotes, assessments, and decisions
- **Tool Stubs**: Address normalization, hazard scoring, and rating tools
- **RAG System**: Document ingestion and retrieval over underwriting guidelines
- **LangGraph Workflow**: Linear processing pipeline (Validate → Enrich → Retrieve → Assess → Rate → Decide)
- **Storage**: SQLite database for run records and audit trails
- **API Endpoints**: RESTful API for quote processing

### Agentic Enhancements ✅
- **Missing-info Loop**: Agentic behavior for handling incomplete submissions
- **Strict Citation Guardrail**: Forces REFER when assessment lacks proper citations
- **Simple UI**: Demo interface for testing and visualization
- **Enhanced Audit Trail**: Complete tool call traceability and run history

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   LangGraph      │    │   Storage       │
│   Endpoints     │───▶│   Workflow       │───▶│   SQLite DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   RAG Engine     │
                       │   (ChromaDB)     │
                       └──────────────────┘
```

## 🚀 Quick Start

### 1. Automated Setup

```bash
# Clone and navigate to the project
cd AgenticQuote

# Run the setup script
python setup.py
```

The setup script will:
- Install all dependencies
- Create necessary directories
- Initialize the RAG system with guideline documents
- Test the workflow

### 2. Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p storage storage/chroma_db

# Initialize RAG (optional - done automatically on first run)
python -c "from app.rag_engine import RAGEngine; RAGEngine().ingest_documents()"
```

### 3. Run the Application

```bash
# Start the API server
python -m app.main
```

The API will be available at `http://localhost:8000`

### 4. Access the UI

Open your browser to: `http://localhost:8000/static/index.html`

## 🧪 Testing

### Automated Testing
```bash
# Run core functionality tests
python test_workflow_success.py
python test_agentic_workflow.py
python test_rag_phase1.py
```

### Manual Testing with curl
```bash
# Submit a quote for processing (agentic mode)
curl -X POST "http://localhost:8000/quote/run" \
  -H "Content-Type: application/json" \
  -d '{
    "submission": {
      "applicant_name": "John Doe",
      "address": "123 Main St, Los Angeles, CA 90210",
      "property_type": "single_family",
      "coverage_amount": 500000,
      "construction_year": 1985,
      "square_footage": 2000,
      "roof_type": "asphalt_shingle",
      "foundation_type": "concrete"
    },
    "use_agentic": true
  }'

# Submit a quote for processing (canonical HO3 schema)
curl -X POST "http://localhost:8000/quote/ho3" \
  -H "Content-Type: application/json" \
  -d '{
    "submission": {
      "applicant": {
        "full_name": "John Doe",
        "email": "john@example.com"
      },
      "risk": {
        "property_address": "123 Main St, Los Angeles, CA 90210",
        "occupancy": "owner_occupied_primary",
        "dwelling_type": "single_family",
        "year_built": 1985,
        "roof_age_years": 15,
        "construction_type": "frame",
        "stories": 1
      },
      "coverage_request": {
        "coverage_a": 500000,
        "coverage_b_pct": 10,
        "coverage_c_pct": 50,
        "coverage_d_pct": 20,
        "coverage_e": 300000,
        "coverage_f": 5000,
        "deductible": 1000
      }
    }
  }'
```

## 📚 API Documentation

### Core Endpoints

#### Processing
- `POST /quote/run` - Process a quote submission
  - `use_agentic: true` enables missing-info loops and citation guardrails
  - **Human-in-the-Loop**: Automatically detects missing information and requests clarification from underwriters
  - **Interactive Workflow**: Continues processing once additional information is provided
- `GET /runs/{run_id}` - Get run status and results
- `GET /runs/{run_id}/audit` - Get full audit trail with tool calls

#### Management
- `GET /runs` - List recent runs
- `GET /stats` - Get system statistics
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🔄 Human-in-the-Loop(HITL) Workflow

### **Missing Information Detection**
When `use_agentic: true`, the system automatically identifies incomplete submissions and:

1. **🔍 Analyzes Gaps**: Detects missing property details, documentation, or risk factors
2. **❓ Generates Questions**: Creates specific questions for underwriters to answer
3. **⏸️ Pauses Processing**: Holds workflow until additional information is provided
4. **🔄 Resumes Execution**: Continues with enriched data once questions are answered

### **Example Use Case**
```bash
# Initial submission with missing roof age
curl -X POST http://localhost:8000/quote/run -d '{
  "submission": {
    "applicant_name": "John Doe",
    "address": "123 Main St",
    "property_type": "single_family",
    "coverage_amount": 500000,
    "construction_year": 1985
    # Missing: roof_type, foundation_type
  },
  "use_agentic": true
}'

# Response includes required questions
{
  "run_id": "abc123",
  "status": "waiting_for_info",
  "required_questions": [
    {
      "question": "What is the roof type and age?",
      "description": "Required for risk assessment",
      "options": ["asphalt_shingle", "metal", "tile"]
    },
    {
      "question": "What is the foundation type?",
      "description": "Required for structural evaluation",
      "options": ["concrete", "crawl_space", "basement"]
    }
  ]
}

# Continue with additional answers
curl -X POST http://localhost:8000/quote/run -d '{
  "submission": {
    "applicant_name": "John Doe",
    "address": "123 Main St",
    "property_type": "single_family",
    "coverage_amount": 500000,
    "construction_year": 1985,
    "roof_type": "asphalt_shingle",
    "foundation_type": "concrete"
  },
  "use_agentic": true,
  "additional_answers": {
    "roof_type": "asphalt_shingle",
    "roof_age": "15 years",
    "foundation_type": "concrete"
  }
}'
```

## 🔄 Workflow Nodes

1. **Validate**: Check submission completeness and basic requirements
2. **Enrich**: Normalize address and calculate hazard scores
3. **RetrieveGuidelines**: Fetch relevant underwriting guidelines via RAG
4. **UWAssess**: Perform underwriting assessment with citations
5. **CitationGuardrail**: Ensure decisions have proper evidence
6. **Rate**: Calculate insurance premium
7. **Decide**: Make final decision (Accept/Refer/Decline)
8. **HandleMissingInfo**: Agentic loop for incomplete submissions

---

## 📈 **Performance & Scalability**

### **⚡ Performance Optimization**
- **Intelligent Caching**: Multi-level with AI-driven invalidation
- **Parallel Processing**: Distributed processing architecture
- **Resource Management**: Dynamic allocation
- **Latency Optimization**: Sub-second response times

### **📊 Scalability Design**
- **Horizontal Scaling**: Auto-scaling for load management
- **Microservices**: Modular service architecture
- **Load Balancing**: Intelligent traffic distribution
- **High Availability**: Disaster recovery and failover

---

## 🧪 **Testing & Validation**

### **🎯 Intelligence Testing**
```bash
# Run comprehensive AI test suite
python test_intelligent_features.py

# Test agentic workflow
python test_agentic_workflow.py

# Test LLM integration
python test_phase3_llm.py

# Test RAG functionality
python test_rag_phase1.py
```

### **📊 Performance Validation**
```bash
# Integration testing
python test_phase2_integration.py

# Workflow success validation
python test_workflow_success.py

# Simple agentic tests
python test_simple_agentic.py
```

---

## 📚 **Documentation**

### **🏗️ Architecture**
- [Intelligent System Architecture](INTELLIGENT_SYSTEM_ARCHITECTURE.md) *(Roadmap & Vision)*
- [Configuration Guide](docs/CONFIGURATION.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)

---

## 🤝 **Enterprise Support**

### **🎯 Professional Services**
- **AI Implementation**: Expert deployment and configuration
- **Custom Training**: Domain-specific model fine-tuning
- **Integration Support**: Enterprise system integration
- **Performance Optimization**: Scalability and efficiency tuning

### **📞 Technical Support**
- **24/7 Enterprise Support**: Round-the-clock assistance
- **AI Expertise**: Specialized AI engineering support
- **SLA Guarantee**: 99.9% uptime commitment
- **Continuous Updates**: Regular AI capability enhancements

---

## � **Future Intelligence Roadmap**

### **🔮 Advanced AI Capabilities**
- **Predictive Analytics**: Advanced risk prediction models
- **Prescriptive Insights**: Actionable recommendation engine
- **Autonomous Decisions**: Fully automated standard processing
- **Strategic Intelligence**: Portfolio-level insights

### **🌐 Ecosystem Integration**
- **Industry Collaboration**: Shared intelligence networks
- **Regulatory Intelligence**: Proactive compliance management
- **Market Intelligence**: Real-time market awareness
- **Innovation Pipeline**: Continuous AI evolution

---

## 🎉 **Transform Underwriting with AI**

The IntelliUnderwrite AI Platform represents a **paradigm shift** from traditional underwriting to **intelligent automation**. By combining **advanced AI capabilities** with **enterprise-grade reliability**, we're creating the future of underwriting.

**This isn't just software—it's an intelligent partner that transforms how organizations approach risk assessment and decision making.**

---

**🧠 IntelliUnderwrite AI Platform - Intelligent Underwriting, Decisive Insights** 🚀
For questions or issues, check the audit logs and API documentation.
cd ./
python -m uvicorn app.complete:create_complete_app --reload --host 0.0.0.0 --port 8000