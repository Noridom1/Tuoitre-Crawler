import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def get_logger(
    name="crawler",
    log_dir="logs",
    level=logging.INFO,
    max_bytes=5 * 1024 * 1024,  # 5MB
    backup_count=5
):
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # ✅ Prevent double logging

    # ✅ Prevent duplicate handlers on re-import
    if logger.handlers:
        return logger

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    info_log_path = os.path.join(log_dir, f"{name}_{timestamp}.log")
    error_log_path = os.path.join(log_dir, f"{name}_{timestamp}_ERROR.log")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ===============================
    # INFO FILE HANDLER (FILE ONLY)
    # ===============================
    info_handler = RotatingFileHandler(
        info_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    # ===============================
    # ERROR FILE HANDLER (FILE ONLY)
    # ===============================
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # ✅ Register ONLY file handlers
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger
