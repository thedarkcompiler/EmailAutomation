"""Settings (.env) and recipients persistence + validation."""
import os
import re

from dotenv import dotenv_values

import mailer
import paths

DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
TRUE_VALUES = ("1", "true", "yes", "on")

FIELD_RANGES = {
    "SMTP_PORT": (1, 65535),
    "MAX_RECIPIENTS": (1, 1000000),
    "SEND_DAY": (1, 28),
    "SEND_HOUR": (0, 23),
    "SEND_MINUTE": (0, 59),
}


# -----------------------------
# .env persistence
# -----------------------------
def load_env():
    if os.path.exists(paths.ENV_FILE):
        data = dict(dotenv_values(paths.ENV_FILE))
    else:
        data = {}
    data.setdefault("ALLOWED_DOMAINS_ENABLED", "true")
    data.setdefault("BLOCKED_DOMAINS_ENABLED", "true")
    return data


def split_domains(value):
    return [d.strip() for d in (value or "").split(",") if d.strip()]


def to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _quote(value):
    if value is None:
        return ""
    value = str(value)
    if any(c in value for c in ('"', "#", "\n")) or value != value.strip():
        return '"' + value.replace('"', '\\"') + '"'
    return value


def save_env(payload):
    lines = [
        "# SMTP settings",
        f"SMTP_HOST={_quote(payload['SMTP_HOST'])}",
        f"SMTP_PORT={payload['SMTP_PORT']}",
        f"SMTP_USER={_quote(payload['SMTP_USER'])}",
        f"SMTP_PASSWORD={_quote(payload['SMTP_PASSWORD'])}",
        f"NOTIFY_EMAIL={_quote(payload.get('NOTIFY_EMAIL', ''))}",
        "",
        "# Email content",
        f"SUBJECT={_quote(payload['SUBJECT'])}",
        "",
        "# Schedule (monthly cron job)",
        f"SEND_DAY={payload['SEND_DAY']}",
        f"SEND_HOUR={payload['SEND_HOUR']}",
        f"SEND_MINUTE={payload['SEND_MINUTE']}",
        "",
        "# Limits",
        f"MAX_RECIPIENTS={_quote(payload['MAX_RECIPIENTS'])}",
        f"SKIP_SENT={'true' if payload.get('SKIP_SENT', True) else 'false'}",
        "",
        "# Domain validation (comma-separated, lowercase)",
        f"ALLOWED_DOMAINS_ENABLED={'true' if payload['ALLOWED_DOMAINS_ENABLED'] else 'false'}",
        f"ALLOWED_DOMAINS={_quote(','.join(payload['ALLOWED_DOMAINS']))}",
        f"BLOCKED_DOMAINS_ENABLED={'true' if payload['BLOCKED_DOMAINS_ENABLED'] else 'false'}",
        f"BLOCKED_DOMAINS={_quote(','.join(payload['BLOCKED_DOMAINS']))}",
        "",
    ]
    with open(paths.ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def apply_to_environ(payload):
    """Push a saved settings payload into os.environ for the live process."""
    for key, value in payload.items():
        if isinstance(value, list):
            value = ",".join(value)
        elif isinstance(value, bool):
            value = "true" if value else "false"
        os.environ[key] = str(value)


# -----------------------------
# Validation
# -----------------------------
def validate_settings(payload):
    errors = []
    for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SUBJECT"):
        if not str(payload.get(key, "")).strip():
            errors.append(f"{key} must not be empty.")
    for key, (lo, hi) in FIELD_RANGES.items():
        try:
            n = int(payload[key])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{key} must be a whole number.")
            continue
        if not lo <= n <= hi:
            errors.append(f"{key} must be between {lo} and {hi}.")
    for key in ("ALLOWED_DOMAINS", "BLOCKED_DOMAINS"):
        for d in payload.get(key) or []:
            if not DOMAIN_RE.match(d):
                errors.append(f"Invalid domain in {key}: {d}")
    return errors


def validate_recipients(recipients):
    errors = []
    if not isinstance(recipients, dict) or not recipients:
        errors.append("At least one recipient is required.")
        return errors
    emails_seen = set()
    for key, info in recipients.items():
        if isinstance(info, dict):
            name = str(info.get("name") or "").strip()
            email = str(info.get("email") or "").strip().lower()
        else:
            # plain-string entries: key is the name, value is the email
            name = str(key).strip()
            email = str(info).strip().lower()
        if not name:
            errors.append(f"'{key}': name must not be empty.")
        if not email:
            errors.append(f"'{key}': email must not be empty.")
        elif not EMAIL_RE.match(email):
            errors.append(f"'{key}': invalid email '{email}'.")
        elif email in emails_seen:
            errors.append(f"Duplicate email: {email}.")
        else:
            emails_seen.add(email)
    return errors


def save_recipients(recipients):
    mailer.save_recipients(recipients)


# -----------------------------
# State assembly
# -----------------------------
def state_payload(next_run_iso, run_state):
    env = load_env()
    sent = mailer.load_sent_history()
    recipients = mailer.load_recipients()
    return {
        "settings": {
            "SMTP_HOST": env.get("SMTP_HOST") or "",
            "SMTP_PORT": to_int(env.get("SMTP_PORT"), 465),
            "SMTP_USER": env.get("SMTP_USER") or "",
            "SMTP_PASSWORD": env.get("SMTP_PASSWORD") or "",
            "NOTIFY_EMAIL": env.get("NOTIFY_EMAIL") or "",
            "SUBJECT": env.get("SUBJECT") or "",
            "MAX_RECIPIENTS": to_int(env.get("MAX_RECIPIENTS"), 1000),
            "SKIP_SENT": (env.get("SKIP_SENT") or "true").lower() in TRUE_VALUES,
            "SEND_DAY": to_int(env.get("SEND_DAY"), 5),
            "SEND_HOUR": to_int(env.get("SEND_HOUR"), 11),
            "SEND_MINUTE": to_int(env.get("SEND_MINUTE"), 0),
            "ALLOWED_DOMAINS_ENABLED": (env.get("ALLOWED_DOMAINS_ENABLED") or "true").lower() in TRUE_VALUES,
            "BLOCKED_DOMAINS_ENABLED": (env.get("BLOCKED_DOMAINS_ENABLED") or "true").lower() in TRUE_VALUES,
            "ALLOWED_DOMAINS": split_domains(env.get("ALLOWED_DOMAINS")),
            "BLOCKED_DOMAINS": split_domains(env.get("BLOCKED_DOMAINS")),
        },
        "recipients": [
            # accept both {"name": ..., "email": ...} objects and plain
            # "email string" values so hand-edited entries are never dropped
            ({"name": info.get("name") or key, "email": info.get("email") or ""}
             if isinstance(info, dict)
             else {"name": key, "email": str(info).strip()})
            for key, info in recipients.items()
        ],
        "sent_count": len(sent),
        "total_recipients": len(recipients),
        "running": run_state["running"],
        "last_run": run_state["last_run"],
        "next_run": next_run_iso(),
    }
