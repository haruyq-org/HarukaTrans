from utils.path import resource_path
from config import config

import logging
import sys
import os

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[90m",
        logging.INFO: "\033[92m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
        logging.CRITICAL: "\033[95m"
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        color = self.COLORS.get(record.levelno, self.RESET)
        return f"{color}{formatted}{self.RESET}"

LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

FORMAT = "[%(asctime)s] [%(levelname)s | %(name)s] %(message)s"

LOG_PATH = resource_path("logs/app.log", no_meipass=True)

def Logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or __name__)
    log_level = LEVEL_MAP.get(config.LOG_LEVEL.upper())

    if logger.handlers:
        logger.setLevel(log_level)
        return logger
        
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter(FORMAT, "%H:%M:%S"))
    logger.addHandler(handler)
    
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(FORMAT, "%H:%M:%S"))
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger