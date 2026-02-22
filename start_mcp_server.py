#!/usr/bin/env python3
"""
Startup script for the Agentic Underwriting MCP Server
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_server import main as run_mcp_server

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting Agentic Underwriting MCP Server...")
    print("📡 Exposing tools:")
    print("  - get_property_risk_assessment")
    print("  - calculate_premium")
    print("  - search_underwriting_guidelines")
    print("  - submit_quote_for_underwriting")
    print("  - get_quote_status")
    print("  - get_human_review_status")
    print("📚 Available Resources:")
    print("  - underwriting://guidelines")
    print("🔗 Server will be available at stdio transport")
    print("🎯 Ready to serve underwriting tools to AI assistants!")
    
    try:
        asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
