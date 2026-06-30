# logger.py
import logging
import os
from datetime import datetime

LOG_DIR  = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"stratomail_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("StratoMail")
    logger.setLevel(logging.DEBUG)

    # ✅ File handler - saves all logs
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # ✅ Console handler - only warnings+
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# Global logger
log = setup_logger()




# In any file:
# from logger import log

# log.info("Fetching emails...")
# log.warning("Folder not found, trying fallback...")
# log.error(f"SMTP failed: {e}")
# log.debug(f"Connected to {config.IMAP_HOST}")