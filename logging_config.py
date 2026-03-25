"""
Centralized logging configuration for Agentic Underwriting System

Provides consistent logging setup across all components with:
- Structured log format
- Multiple output handlers
- Log levels configuration
- Correlation ID support for workflow tracing
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    Setup centralized logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/underwriting.log)
        enable_console: Enable console output
        enable_file: Enable file output
    """
    
    # Create logs directory if needed
    if enable_file and not log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"underwriting_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure formatters
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure handlers
    handlers = []
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
    
    if enable_file and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels for noisy components
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info("🔧 Logging system initialized")
    logger.info(f"📊 Log level: {level}")
    if enable_file and log_file:
        logger.info(f"📁 Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_workflow_step(step_name: str, run_id: str, details: dict, level: str = "INFO") -> None:
    """
    Log a workflow step with correlation ID
    
    Args:
        step_name: Name of the workflow step
        run_id: Unique run identifier for correlation
        details: Dictionary of step details
        level: Log level (INFO, DEBUG, WARNING, ERROR)
    """
    logger = logging.getLogger(__name__)
    
    # Format details for logging
    details_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
    message = f"[{run_id}] {step_name}: {details_str}"
    
    getattr(logger, level.lower())(message)


def log_performance(operation: str, duration_ms: float, run_id: Optional[str] = None, details: Optional[dict] = None) -> None:
    """
    Log performance metrics
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        run_id: Optional run ID for correlation
        details: Additional performance details
    """
    logger = logging.getLogger(__name__)
    
    message_parts = [f"⏱️ {operation}: {duration_ms:.2f}ms"]
    
    if run_id:
        message_parts.append(f"[{run_id}]")
    
    if details:
        details_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
        message_parts.append(f"({details_str})")
    
    logger.info(" ".join(message_parts))


def log_error(operation: str, error: Exception, run_id: Optional[str] = None, context: Optional[dict] = None) -> None:
    """
    Log error with context
    
    Args:
        operation: Operation where error occurred
        error: Exception instance
        run_id: Optional run ID for correlation
        context: Additional context information
    """
    logger = logging.getLogger(__name__)
    
    message_parts = [f"❌ {operation}: {str(error)}"]
    
    if run_id:
        message_parts.append(f"[{run_id}]")
    
    if context:
        context_str = ", ".join([f"{k}: {v}" for k, v in context.items()])
        message_parts.append(f"Context: {context_str}")
    
    logger.error(" ".join(message_parts))


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()
