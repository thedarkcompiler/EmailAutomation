import re
import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_DOMAINS = set(
    os.getenv("ALLOWED_DOMAINS", "")
    .lower()
    .split(",")
)

BLOCKED_DOMAINS = set(
    domain.strip().lower()
    for domain in os.getenv("BLOCKED_DOMAINS", "").split(",")
    if domain.strip()
)


EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"


def validate_email(email: str) -> bool:
    """
    Validate email format and allowed domain.
    """

    if not email:
        return False

    match = re.match(EMAIL_REGEX, email)

    if not match:
        return False

    domain = match.group(1).lower()

    if domain in BLOCKED_DOMAINS:
        return False
    
    if domain not in ALLOWED_DOMAINS:
        return False

    return True