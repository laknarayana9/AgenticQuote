# MCP Server for Agentic Underwriting System

This document describes the MCP (Model Context Protocol) server implementation for the Agentic Quote-to-Underwrite system.

## Overview

The MCP server exposes the underwriting tools and capabilities as AI-accessible tools that can be used by Claude, GPT, and other AI assistants. This positions your system as a specialized tool provider in the AI ecosystem.

## Architecture

```
┌─────────────────┐
│  AI Assistant  │
│   (Claude/GPT)  │
├─────────────────┤
│               │
│     MCP Server  │
│   (stdio)      │
├─────────────────┤
│               │
│  Your System   │
│   (Python)      │
└─────────────────┘
```

## Available Tools

### 1. get_property_risk_assessment
- **Purpose**: Get comprehensive risk assessment for a property address
- **Input**: `address` (string) - Property address to assess
- **Output**: Hazard scores for wildfire, flood, earthquake, and wind risks
- **Use Case**: AI assistants can quickly assess property risk before quoting

### 2. calculate_premium
- **Purpose**: Calculate insurance premium based on multiple factors
- **Input**: Coverage amount, property type, construction year, hazard scores
- **Output**: Detailed premium calculation with all factors
- **Use Case**: AI assistants can perform complex premium calculations

### 3. search_underwriting_guidelines
- **Purpose**: Search underwriting guidelines using RAG
- **Input**: `query` (string) - Search query
- **Output**: Relevant guideline chunks with citations
- **Use Case**: AI assistants can access underwriting knowledge base

### 4. submit_quote_for_underwriting
- **Purpose**: Submit quote for comprehensive AI underwriting analysis
- **Input**: Complete quote submission data
- **Output**: Full workflow analysis with decision and premium
- **Use Case**: AI assistants can run the complete agentic workflow

### 5. get_quote_status
- **Purpose**: Get current status and details of a submitted quote
- **Input**: `quote_id` (string) - Unique quote identifier
- **Output**: Complete quote status with workflow state and decision
- **Use Case**: AI assistants can check quote processing status

### 6. get_human_review_status
- **Purpose**: Get human review status for quotes requiring manual underwriter review
- **Input**: `quote_id` (string) - Unique quote identifier
- **Output**: Review status, reviewer info, and decision details
- **Use Case**: AI assistants can check human review workflow status

## Available Resources

### underwriting://guidelines
- **Type**: Text resource
- **Content**: Comprehensive underwriting guidelines and best practices
- **Use Case**: AI assistants can access the knowledge base

## Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start MCP Server
```bash
python start_mcp_server.py
```

### 3. Configure Claude Desktop (or other MCP client)
Add to your MCP client configuration:
```json
{
  "mcpServers": [
    {
      "command": "python /path/to/mcp_server.py",
      "env": {
        "PYTHONPATH": "/path/to/your/project"
      }
    }
  ]
}
```

### 4. Use in AI Assistants
Once configured, AI assistants can:
- Access property risk assessment tools
- Calculate complex premiums with multiple factors
- Search underwriting guidelines for best practices
- Submit quotes for full agentic analysis
- Check quote status and human review status
- Access comprehensive underwriting knowledge base

## Benefits

### For AI Ecosystem
- **Specialized Tools**: Your underwriting expertise is now available to AI assistants
- **Knowledge Base**: RAG-powered guidelines search and retrieval
- **Workflow Integration**: Complete agentic quote processing
- **Risk Assessment**: Comprehensive property risk analysis

### For Your Organization
- **Innovation Leadership**: Position as an AI tool provider
- **Revenue Opportunities**: Monetize specialized underwriting capabilities
- **Competitive Advantage**: Unique AI-powered underwriting solution
- **Scalability**: Serve multiple AI assistants simultaneously

## Technical Details

### Server Implementation
- **Protocol**: MCP (Model Context Protocol)
- **Transport**: stdio (command-line friendly)
- **Framework**: Python-based with async/await patterns
- **Database Integration**: Full access to existing SQLite database
- **Error Handling**: Comprehensive error handling and logging

### Security Considerations
- **Authentication**: Add authentication for production use
- **Rate Limiting**: Implement usage quotas per client
- **Audit Logging**: Log all tool calls and responses
- **Input Validation**: Validate all input parameters

## Future Enhancements

### Planned Features
- **Real-time Notifications**: Webhook support for quote status updates
- **Batch Processing**: Handle multiple quotes simultaneously
- **Advanced Analytics**: Usage statistics and performance metrics
- **Multi-tenant**: Support multiple insurance companies
- **API Integration**: Connect with external insurance systems

---

This MCP server transforms your underwriting system into an AI-accessible tool provider, enabling powerful new capabilities and use cases.
