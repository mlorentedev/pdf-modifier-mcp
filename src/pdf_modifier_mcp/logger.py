import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(name: str) -> logging.Logger:
    log_dir = Path.home() / ".pdf-modifier" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pdf-modifier.log"

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
