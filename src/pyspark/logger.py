"""
Centralized logging factory for the Insurance Policy Lifecycle pipeline.
"""

import logging
import os
import sys
from config import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    """Create a logger that writes to both file and stdout."""
    log_path = os.path.join(LOGS_DIR, f"{name}.log")
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        stream_handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger