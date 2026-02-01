"""Конфигурация логирования для приложения."""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_file: Optional[str] = "logs/actions.log",
    level: int = logging.INFO,
    json_format: bool = False
) -> None:
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    if json_format:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


action_logger = logging.getLogger("actions")