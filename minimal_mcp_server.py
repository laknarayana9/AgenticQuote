#!/usr/bin/env python3
"""
Minimal MCP Server for Agentic Underwriting System

This MCP server exposes basic underwriting tools that can be used by Claude, GPT, and other AI assistants.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from datetime import datetime

from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListToolsResult
)

logger = logging.getLogger(__name__)

# Simple MCP tools
TOOLS = [
    Tool(
        name="get_property_risk_assessment",
        description="Get basic risk assessment for a property address",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Property address to assess for risks"
                }
            }
        },
        handler=lambda address: {
            "address": address,
            "wildfire_risk": 0.3 if "fire" in address.lower() else 0.1,
            "flood_risk": 0.2 if "flood" in address.lower() else 0.05,
            "earthquake_risk": 0.1 if "california" in address.lower() else 0.05,
            "wind_risk": 0.15 if "coastal" in address.lower() else 0.08,
            "overall_risk": max([0.3, 0.2, 0.1, 0.05, 0.15, 0.08]),
            "assessment_date": datetime.now().isoformat(),
            "confidence": 0.85
        }
    ),
    
    Tool(
        name="calculate_premium",
        description="Calculate basic insurance premium",
        inputSchema={
            "type": "object",
            "properties": {
                "coverage_amount": {
                    "type": "number",
                    "description": "Insurance coverage amount in dollars"
                },
                "property_type": {
                    "type": "string",
                    "enum": ["single_family", "condo", "townhouse", "commercial"],
                    "description": "Type of property"
                }
            }
        },
        handler=lambda request: {
            "coverage_amount": request.get("coverage_amount", 100000),
            "property_type": request.get("property_type", "single_family")
        },
        result={
            "annual_premium": request.get("coverage_amount", 100000) * 0.002,
            "monthly_premium": (request.get("coverage_amount", 100000) * 0.002) / 12,
            "factors": {
                "base_rate": 0.002,
                "type_multiplier": {"single_family": 1.0, "condo": 0.8, "townhouse": 0.9, "commercial": 1.5}.get(request.get("property_type", "single_family"), 1.0),
                "property_type": request.get("property_type", "single_family")
            }
        }
    )
]

async def main():
    """Main entry point for the MCP server."""
    
    # Create server instance
    server = Server("agentic-underwriting")
    
    # Register tools
    for tool in TOOLS:
        server.add_tool(tool)
    
    # Add resources
    await server.add_resource(
        Resource(
            uri="underwriting://guidelines",
            name="Underwriting Guidelines",
            description="Comprehensive underwriting guidelines and best practices",
            mimeType="text/plain"
        )
    )
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                env="development"
            )
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🚀 Starting Minimal Agentic Underwriting MCP Server...")
    print("📡 Exposing tools:")
    for tool in TOOLS:
        print(f"  - {tool.name}")
    print("📚 Available Resources:")
    print("  - underwriting://guidelines")
    print("🔗 Server will be available at stdio transport")
    print("🎯 Ready to serve underwriting tools to AI assistants!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
