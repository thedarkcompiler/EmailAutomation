"""Shared filesystem paths for the whole project."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
LOG_FILE = os.path.join(BASE_DIR, "mailer.log")
