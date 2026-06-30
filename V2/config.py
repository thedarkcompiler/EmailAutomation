# config.py
import os

# Server config
SMTP_HOST = "smtp.strato.de"
SMTP_PORT = 465
IMAP_HOST = "imap.strato.de"
IMAP_PORT = 993

# ✅ Load from environment variables (never hardcode!)
EMAIL    = os.environ.get("STRATO_EMAIL",    "")
PASSWORD = os.environ.get("STRATO_PASSWORD", "")

# App settings
APP_NAME    = "StratoMail"
APP_VERSION = "1.0.0"
MAX_EMAILS  = 50
TIMEOUT     = 30