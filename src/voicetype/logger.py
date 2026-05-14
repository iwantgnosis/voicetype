import logging
import os
import sys
from pathlib import Path

def setup_logging():
    log_dir = Path.home() / ".voicetype" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "voicetype.log"
    
    # Configure logging
    logger = logging.getLogger("voicetype")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("Logging initialized. Log file: %s", log_file)
    return logger

def get_logger(name):
    return logging.getLogger(f"voicetype.{name}")
