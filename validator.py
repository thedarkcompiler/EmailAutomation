import re
import os

EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$"

TRUE_VALUES = ("1", "true", "yes", "on")


def _flag(name: str) -> bool:
    return os.getenv(name, "true").strip().lower() in TRUE_VALUES


def _domains(name: str) -> set:
    return {
        domain.strip()
        for domain in os.getenv(name, "").lower().split(",")
        if domain.strip()
    }


def check_email(email: str):
    """
    Validate email format and domain rules.

    Returns (ok: bool, reason: str). When ok is True, reason is "".
    The reason describes exactly what failed and why, for logging/alerts.
    Rules are read from the environment on every call, so edits made
    through the web UI apply immediately.
    """
    if not email or not str(email).strip():
        return False, "address is empty"

    email = str(email).strip()
    match = re.match(EMAIL_REGEX, email)
    if not match:
        return False, (
            f"address '{email}' is not a valid email format "
            "(expected local@domain.tld)"
        )

    domain = match.group(1).lower()

    if _flag("BLOCKED_DOMAINS_ENABLED"):
        blocked = _domains("BLOCKED_DOMAINS")
        if domain in blocked:
            return False, (
                f"domain '{domain}' is on the BLOCKED list "
                "(blacklist is enforced)"
            )

    if _flag("ALLOWED_DOMAINS_ENABLED"):
        allowed = _domains("ALLOWED_DOMAINS")
        if domain not in allowed:
            shown = ", ".join(sorted(allowed)) if allowed else "(none configured)"
            return False, (
                f"domain '{domain}' is not in the ALLOWED list "
                f"(whitelist is enforced, allowed: {shown}). "
                "Add the domain in the web UI or turn the whitelist off."
            )

    return True, ""


def validate_email(email: str) -> bool:
    """Backwards-compatible boolean check."""
    return check_email(email)[0]
