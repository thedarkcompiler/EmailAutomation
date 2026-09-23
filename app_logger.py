"""Logging setup: rotating file (mailer.log) + console stream."""
import logging
from logging.handlers import TimedRotatingFileHandler

import paths

_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"


def setup_logging():
    file_handler = TimedRotatingFileHandler(
        paths.LOG_FILE, when="midnight", interval=1, backupCount=7
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    logging.basicConfig(
        level=logging.INFO,
        format=_FORMAT,
        handlers=[file_handler, logging.StreamHandler()],
    )
