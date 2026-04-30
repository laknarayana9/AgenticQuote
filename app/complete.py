"""
Minimal complete app implementation for test compatibility
"""

import logging
from fastapi import FastAPI
from app.main import app

logger = logging.getLogger(__name__)

def create_complete_app():
    """Create complete app for test compatibility"""
    return app

# Export app for direct import
__all__ = ["create_complete_app", "app"]
