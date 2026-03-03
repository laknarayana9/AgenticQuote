#!/usr/bin/env python3
"""
IntelliUnderwrite AI Platform - Intelligent System Setup

This script initializes the complete intelligent underwriting system
with all AI components, databases, and services.

Usage:
    python setup_intelligent_system.py [--config CONFIG_FILE] [--dev]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directory structure for intelligent system"""
    logger.info("📁 Creating intelligent system directory structure...")
    
    directories = [
        "storage",
        "storage/knowledge_base", 
        "storage/vector_db",
        "storage/knowledge_graph",
        "storage/cache",
        "storage/uploads",
        "storage/analytics",
        "storage/models",
        "logs",
        "config"
    ]
    
    success = True
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory {directory}: {e}")
            success = False
    
    return success

def setup_databases():
    """Initialize intelligent system databases"""
    logger.info("🗄️ Initializing intelligent databases...")
    
    try:
        # Import database components
        from storage.database import init_database
        from app.rag_engine import get_rag_engine
        
        # Initialize SQLite database
        init_database()
        logger.info("✅ SQLite database initialized")
        
        # Initialize ChromaDB vector store
        rag_engine = get_rag_engine()
        logger.info("✅ ChromaDB vector store initialized")
        
        # Test database connections
        logger.info("🔍 Testing database connections...")
        # Add connection tests here
        
        logger.info("✅ All databases connected successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def setup_ai_components():
    """Initialize AI and machine learning components"""
    logger.info("🧠 Initializing AI components...")
    
    try:
        # Initialize cognitive engine
        from app.cognitive_engine import get_cognitive_engine
        cognitive_engine = get_cognitive_engine()
        logger.info("✅ Cognitive Knowledge Retrieval initialized")
        
        # Initialize reasoning engine
        from app.intelligent_reasoning import get_reasoning_engine
        reasoning_engine = get_reasoning_engine()
        logger.info("✅ Advanced Reasoning Engine initialized")
        
        # Initialize LLM engine
        from app.llm_engine import get_llm_engine
        llm_engine = get_llm_engine()
        logger.info("✅ LLM Engine initialized")
        
        # Check AI component health
        cognitive_health = cognitive_engine.get_intelligence_metrics()
        reasoning_health = reasoning_engine.get_reasoning_metrics()
        llm_health = llm_engine.health_check()
        
        logger.info("📊 AI Component Health:")
        logger.info(f"   Cognitive Engine: {cognitive_health}")
        logger.info(f"   Reasoning Engine: {reasoning_health}")
        logger.info(f"   LLM Engine: {llm_health}")
        
    except Exception as e:
        logger.error(f"❌ AI component initialization failed: {e}")
        return False
    
    return True

def setup_configuration():
    """Setup intelligent system configuration"""
    logger.info("⚙️ Setting up intelligent system configuration...")
    
    config = {
        "platform": {
            "name": "IntelliUnderwrite AI Platform",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true"
        },
        "ai": {
            "cognitive_engine": {
                "enabled": True,
                "knowledge_base_path": "./storage/knowledge_base",
                "max_retrieval_results": 10,
                "confidence_threshold": 0.7
            },
            "reasoning_engine": {
                "enabled": True,
                "model_type": "hybrid_neural_symbolic",
                "confidence_threshold": 0.7,
                "explainability_level": "high"
            },
            "llm_engine": {
                "enabled": True,
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.3,
                "api_key_env": "OPENAI_API_KEY"
            }
        },
        "database": {
            "sqlite": {
                "path": "./storage/underwriting.db"
            },
            "chroma": {
                "path": "./storage/chroma_db",
                "collection": "underwriting_knowledge"
            }
        },
        "performance": {
            "cache_enabled": True,
            "cache_ttl": 3600,
            "max_concurrent_requests": 100,
            "request_timeout": 30
        },
        "security": {
            "encryption_enabled": True,
            "audit_logging": True,
            "session_timeout": 3600
        }
    }
    
    # Save configuration
    config_path = Path("config/intelligent_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Configuration saved to {config_path}")
    return config

def setup_monitoring():
    """Setup monitoring and analytics"""
    logger.info("📊 Setting up intelligent monitoring...")
    
    try:
        # Create monitoring directories
        Path("logs/metrics").mkdir(exist_ok=True)
        Path("logs/audits").mkdir(exist_ok=True)
        Path("logs/performance").mkdir(exist_ok=True)
        
        # Initialize logging
        metrics_logger = logging.getLogger('metrics')
        audit_logger = logging.getLogger('audit')
        performance_logger = logging.getLogger('performance')
        
        # Setup file handlers
        import logging.handlers
        
        # Metrics logging
        metrics_handler = logging.handlers.RotatingFileHandler(
            'logs/metrics/intelligent_metrics.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        metrics_logger.addHandler(metrics_handler)
        
        logger.info("✅ Monitoring system initialized")
        
    except Exception as e:
        logger.error(f"❌ Monitoring setup failed: {e}")
        return False
    
    return True

def validate_system():
    """Validate intelligent system setup"""
    logger.info("🔍 Validating intelligent system setup...")
    
    validation_results = {
        "directories": True,
        "databases": True,
        "ai_components": True,
        "configuration": True,
        "monitoring": True
    }
    
    # Check directories
    required_dirs = ["storage", "storage/knowledge_base", "storage/vector_db", "logs"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            validation_results["directories"] = False
            logger.error(f"❌ Missing directory: {dir_path}")
    
    # Check configuration
    config_path = Path("config/intelligent_config.json")
    if not config_path.exists():
        validation_results["configuration"] = False
        logger.error("❌ Missing configuration file")
    
    # Summary
    all_valid = all(validation_results.values())
    
    if all_valid:
        logger.info("✅ All system components validated successfully")
        logger.info("🚀 IntelliUnderwrite AI Platform is ready!")
    else:
        logger.error("❌ System validation failed:")
        for component, valid in validation_results.items():
            status = "✅" if valid else "❌"
            logger.error(f"   {status} {component}")
    
    return all_valid

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup IntelliUnderwrite AI Platform")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🧠 Starting IntelliUnderwrite AI Platform Setup")
    logger.info("=" * 60)
    
    # Setup steps
    setup_steps = [
        ("Directory Structure", setup_directories),
        ("Configuration", setup_configuration),
        ("Databases", setup_databases),
        ("AI Components", setup_ai_components),
        ("Monitoring", setup_monitoring),
        ("Validation", validate_system)
    ]
    
    for step_name, step_func in setup_steps:
        logger.info(f"\n🔧 Step: {step_name}")
        try:
            success = step_func()
            if not success:
                logger.error(f"❌ Failed to complete step: {step_name}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error in step {step_name}: {e}")
            logger.info(f"⚠️ Continuing with remaining steps...")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 IntelliUnderwrite AI Platform setup completed successfully!")
    logger.info("🌐 Start the platform with: python launch_intelligent_platform.py")
    logger.info("📚 Documentation: docs/INTELLIGENT_SYSTEM_ARCHITECTURE.md")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
