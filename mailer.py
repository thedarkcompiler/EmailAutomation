"""
Email sending service.

All logic that actually talks to the SMTP server lives here. It is called by
the web server (for scheduled runs, manual "send now", and test emails).

Settings are always read fresh from os.environ, so changes made through the
web UI (which rewrites .env and os.environ) take effect on the next run.

Every failure path produces a structured report (see build_report) that is
emailed to NOTIFY_EMAIL: what happened, the exact error, likely causes and
suggested fixes, plus a snapshot of the active configuration.
"""
import json
import os
import socket
import smtplib
import ssl
import sys
import logging
import platform
import tempfile
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from filelock import FileLock, Timeout

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(BASE_DIR, "email.html")
RECIPIENTS_FILE = os.path.join(BASE_DIR, "recipients.json")
SENT_FILE = os.path.join(BASE_DIR, "sent.json")
LOCK_FILE = os.path.join(BASE_DIR, "mailer.lock")

logger = logging.getLogger("mailer")

TRUE_VALUES = ("1", "true", "yes", "on")


def _safe_int(value, default):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


# -----------------------------
# Config
# -----------------------------
def load_config():
    """Read all runtime settings from the environment."""
    return {
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": _safe_int(os.getenv("SMTP_PORT"), 465),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "subject": os.getenv("SUBJECT", ""),
        "send_day": _safe_int(os.getenv("SEND_DAY"), 5),
        "send_hour": _safe_int(os.getenv("SEND_HOUR"), 11),
        "send_minute": _safe_int(os.getenv("SEND_MINUTE"), 0),
        "max_recipients": _safe_int(os.getenv("MAX_RECIPIENTS"), 1000),
        "skip_sent": os.getenv("SKIP_SENT", "true").strip().lower() in TRUE_VALUES,
        "notify_email": os.getenv("NOTIFY_EMAIL", ""),
    }


def config_snapshot(config):
    """Redacted snapshot of the active settings, for alert emails."""
    pw = str(config.get("smtp_password", ""))
    pw_masked = (pw[:2] + "*" * 8 + pw[-2:]) if len(pw) > 6 else ("***" if pw else "(empty)")
    return (
        f"  SMTP host:    {config.get('smtp_host') or '(not set)'}\n"
        f"  SMTP port:    {config.get('smtp_port')}\n"
        f"  SMTP user:    {config.get('smtp_user') or '(not set)'}\n"
        f"  SMTP pass:    {pw_masked}\n"
        f"  From (same as user)\n"
        f"  Subject:      {config.get('subject') or '(not set)'}\n"
        f"  Notify to:    {config.get('notify_email') or '(not set)'}\n"
        f"  Max recipients: {config.get('max_recipients')}\n"
        f"  Skip already-sent: {config.get('skip_sent')}"
    )


# -----------------------------
# Error classification & reporting
# -----------------------------
def classify_smtp_error(exc):
    """Turn a low-level SMTP/SSL/timeout exception into a human explanation."""
    msg = str(exc)

    if isinstance(exc, socket.timeout):
        return (
            "Connection timed out while talking to the SMTP server.",
            [
                "The server may be slow or down.",
                "A firewall/network rule may be blocking the port.",
                "Check that SMTP_HOST and SMTP_PORT point to the right server "
                "(465 = implicit SSL, 587 = STARTTLS).",
            ],
        )
    if isinstance(exc, ssl.SSLError):
        return (
            f"TLS handshake failed: {msg}",
            [
                "The server may not support implicit SSL on this port "
                "(use 465 for SMTP_SSL).",
                "A proxy or firewall may be intercepting the connection.",
            ],
        )
    if isinstance(exc, (socket.gaierror, socket.herror)):
        return (
            f"Could not resolve/connect to SMTP host: {msg}",
            [
                "SMTP_HOST may be a typo or misspelled.",
                "DNS may be failing on this machine.",
                "The server may be unreachable from your network.",
            ],
        )
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        code = exc.args[0] if exc.args else "unknown"
        return (
            f"SMTP authentication was rejected by the server "
            f"(code {code}): {msg}",
            [
                "The password / app password is wrong or has expired.",
                "The provider may require an APP password (e.g. Strato/Google), "
                "not the normal account password.",
                "The account may need 2FA, or the mail user may be locked.",
            ],
        )
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        return (
            f"The server refused the recipient address: {msg}",
            [
                "The mailbox may not exist or is rejecting mail.",
                "The provider may be blocking sending to that domain.",
            ],
        )
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return (
            "The server closed the connection unexpectedly.",
            [
                "Too many rapid connections — try again in a minute.",
                "The provider may rate-limit or temporarily ban the account.",
            ],
        )
    return (
        f"SMTP error: {msg}",
        ["Check SMTP_HOST, SMTP_PORT, credentials in the web UI and retry."],
    )


def build_report(kind, what, exc=None, detail_lines=None, causes=None, suggestions=None):
    """
    Build a detailed multi-line report for an alert email.

    kind:        'scheduled' | 'manual' | 'test' | 'server'
    what:        short description of what failed
    exc:         exception instance (optional)
    detail_lines: extra lines (e.g. per-recipient failures)
    causes:      list of likely causes
    suggestions: list of suggested fixes
    """
    now = datetime.now()
    tb_text = ""
    if exc is not None and isinstance(exc, BaseException):
        tb_text = traceback.format_exception_only(type(exc), exc)[0].strip()
        if exc.__traceback__ is not None:
            tb_text += "\n" + "".join(traceback.format_tb(exc.__traceback__)).strip()
            if len(tb_text) > 3000:
                tb_text = "...(truncated)...\n" + tb_text[-3000:]

    lines = []
    lines.append(f"What failed : {what}")
    lines.append(f"When        : {now.strftime('%Y-%m-%d %H:%M:%S %z') or now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Trigger     : {kind} run")
    lines.append(f"Machine     : {platform.node()} ({sys.platform}, Python {platform.python_version()})")
    lines.append(f"Project dir : {BASE_DIR}")
    if tb_text:
        lines.append("")
        lines.append("Exception :")
        lines.append(tb_text)

    config = load_config()
    lines.append("")
    lines.append("Active settings (password redacted):")
    lines.append(config_snapshot(config))

    if detail_lines:
        lines.append("")
        lines.append("Details:")
        lines.extend(f"  - {d}" for d in detail_lines[:25])
        if len(detail_lines) > 25:
            lines.append(f"  ... and {len(detail_lines) - 25} more (see mailer.log)")

    if causes:
        lines.append("")
        lines.append("Likely causes:")
        lines.extend(f"  {i}. {c}" for i, c in enumerate(causes, 1))

    if suggestions:
        lines.append("")
        lines.append("Suggested fixes:")
        lines.extend(f"  {i}. {s}" for i, s in enumerate(suggestions, 1))

    lines.append("")
    lines.append(f"Full log: {os.path.join(BASE_DIR, 'mailer.log')}")
    return "\n".join(lines)


def alert(title, report):
    """
    Email the configured NOTIFY_EMAIL about a failure.

    Best-effort: never raises, never alerts about the alert itself.
    """
    config = load_config()
    to = (config.get("notify_email") or "").strip()
    if not to:
        logger.info("Alert not sent: NOTIFY_EMAIL is not set.\n%s", report)
        return False
    try:
        server = _connect(config)
    except Exception as e:
        logger.error(
            "Alert could not be delivered because SMTP is unavailable: %s", e
        )
        logger.info("Unsent alert report:\n%s", report)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ALERT] {title}"
    msg["From"] = config["smtp_user"]
    msg["To"] = to
    msg.attach(MIMEText(report, "plain"))
    try:
        server.sendmail(config["smtp_user"], to, msg.as_string())
        logger.info(f"Alert email sent to {mask_email(to)}: {title}")
        return True
    except Exception as e:
        logger.error(f"Alert email to {mask_email(to)} failed: {e}")
        return False
    finally:
        try:
            server.quit()
        except Exception:
            pass


def test_alert():
    """Send a one-off alert email so the user can verify NOTIFY_EMAIL works."""
    report = build_report(
        "test",
        "This is a manual test alert (requested from the web UI).",
        detail_lines=["No error occurred — you received this on purpose."],
        suggestions=[
            "No action needed. If you are reading this, error alerts are working.",
            "Future failures will use the same format.",
        ],
    )
    return alert("Test alert — email notifications are working", report)


# -----------------------------
# Data helpers
# -----------------------------
def load_recipients():
    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.error("recipients.json is not a JSON object, ignoring it.")
            return {}
        return data
    except FileNotFoundError:
        logger.error(f"recipients.json not found at {RECIPIENTS_FILE}")
        return {}
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Could not read recipients.json: {e}")
        return {}


def load_sent_history():
    if not os.path.exists(SENT_FILE):
        return {}
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"sent.json invalid ({e}), starting fresh.")
        return {}


def save_sent_history(history):
    """Atomically write sent.json so a crash can't corrupt it."""
    _atomic_write_json(SENT_FILE, history)


def _atomic_write_json(path, data):
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def save_recipients(recipients):
    _atomic_write_json(RECIPIENTS_FILE, recipients)


def load_template():
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Template not found at {TEMPLATE_FILE}")
        return ""
    except OSError as e:
        logger.error(f"Could not read template: {e}")
        return ""


def mask_email(email):
    try:
        user, domain = str(email).split("@")
        return (user[:2] if user else "?") + "***@" + domain
    except (ValueError, AttributeError):
        return "***"


# -----------------------------
# SMTP helpers
# -----------------------------
def _connect(config):
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(
        config["smtp_host"],
        config["smtp_port"],
        context=context,
        timeout=30,
    )
    server.login(config["smtp_user"], config["smtp_password"])
    return server


def _build_message(config, recipient, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = config["subject"]
    msg["From"] = config["smtp_user"]
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))
    return msg


# -----------------------------
# Public operations
# -----------------------------
def send_all():
    """
    Send to every recipient not yet in sent.json.
    Returns a summary dict.
    """
    from validator import check_email  # local import to avoid cycle at module load

    config = load_config()
    recipients = load_recipients()
    sent = load_sent_history()

    result = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

    if not recipients:
        detail = (
            f"No recipients found in {RECIPIENTS_FILE}. The job connected to "
            "nothing and sent nothing."
        )
        report = build_report(
            "scheduled",
            "Email job had no recipients to send to.",
            detail_lines=[detail],
            causes=[
                "recipients.json is missing, empty, or not valid JSON.",
                "The file may be corrupted (an earlier save was interrupted).",
            ],
            suggestions=[
                "Open the web UI → Recipients and add entries, then Save.",
                "Check mailer.log for the underlying file error.",
            ],
        )
        alert("Email job: no recipients found", report)
        return result

    if len(recipients) > config["max_recipients"]:
        raise RuntimeError(
            f"Recipient limit exceeded: {len(recipients)} recipients found, "
            f"but MAX_RECIPIENTS is {config['max_recipients']}."
        )

    try:
        server = _connect(config)
    except Exception as e:
        logger.error(f"Failed to connect/login to SMTP server: {e}")
        what, causes = classify_smtp_error(e)
        report = build_report(
            "scheduled",
            "Email job could not connect to / authenticate with the SMTP server.",
            exc=e,
            detail_lines=[what],
            causes=causes,
            suggestions=[
                "Verify SMTP_HOST / SMTP_PORT / SMTP_USER / password in the web UI.",
                "For Strato: SMTP user is the full mailbox address and the port is 465.",
                "Retry once it is fixed: web UI → Send now.",
            ],
        )
        alert("Email job: SMTP connection failed", report)
        result["errors"].append(what)
        return result

    html = load_template()
    if not html:
        server.quit()
        report = build_report(
            "scheduled",
            "Email job aborted: the email template (email.html) could not be read.",
            detail_lines=[f"Expected file: {TEMPLATE_FILE}"],
            causes=["The template file is missing or unreadable."],
            suggestions=[
                "Restore email.html in the project directory and re-run.",
            ],
        )
        alert("Email job: template missing", report)
        result["errors"].append("Template missing")
        return result

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        for name, info in recipients.items():
            email = info.get("email") if isinstance(info, dict) else None

            if not isinstance(email, str) or not email.strip():
                logger.error(f"Recipient '{name}' has no usable email address.")
                result["failed"] += 1
                result["errors"].append(
                    f"Recipient '{name}': entry is malformed (missing 'email')."
                )
                continue

            if email in sent and config["skip_sent"]:
                logger.info(f"Skipping {name} ({mask_email(email)}) - already sent.")
                result["skipped"] += 1
                continue

            ok, reason = check_email(email)
            if not ok:
                logger.warning(f"Skipping {name} ({email}) - {reason}")
                result["failed"] += 1
                result["errors"].append(
                    f"Recipient '{name}' ({email}) was rejected: {reason}."
                )
                continue

            msg = _build_message(config, email, html)
            try:
                server.sendmail(config["smtp_user"], email, msg.as_string())
                sent[email] = now
                try:
                    save_sent_history(sent)
                except OSError as se:
                    logger.error(
                        f"Email was sent to {email} but sent.json could not be "
                        f"updated: {se}"
                    )
                    result["errors"].append(
                        f"Recipient '{name}': email delivered, but the sent history "
                        f"could not be saved ({se}). It will be sent again next run."
                    )
                logger.info(f"Email sent to {name} ({mask_email(email)}) at {now}")
                result["success"] += 1
            except Exception as e:
                logger.error(f"Failed to send to {name} ({mask_email(email)}): {e}")
                result["failed"] += 1
                result["errors"].append(
                    f"Recipient '{name}' ({email}): server rejected the send — {e}"
                )
    finally:
        try:
            server.quit()
        except Exception:
            pass

    logger.info(
        f"Run complete. sent={result['success']} "
        f"failed={result['failed']} skipped={result['skipped']}"
    )
    if result["failed"]:
        causes, suggestions = _summarize_failures(result["errors"])
        report = build_report(
            "scheduled",
            f"Email job finished with {result['failed']} of {len(recipients)} "
            f"recipients FAILED (sent {result['success']}, "
            f"skipped {result['skipped']}).",
            detail_lines=result["errors"],
            causes=causes,
            suggestions=suggestions,
        )
        alert(f"Email job: {result['failed']} of {len(recipients)} sends failed", report)
    return result


def _summarize_failures(errors):
    """Derive likely causes + fixes from the collected per-recipient errors."""
    causes, suggestions = [], []
    text = "\n".join(errors)
    if "not in the ALLOWED list" in text or "whitelist" in text:
        causes.append(
            "One or more addresses failed the whitelist (ALLOWED_DOMAINS)."
        )
        suggestions.append(
            "Add the missing domains in the web UI → Domain rules → Whititelist, "
            "or remove the wrong recipient entries."
        )
    if "on the BLOCKED list" in text:
        causes.append("One or more addresses hit the blacklist (BLOCKED_DOMAINS).")
        suggestions.append("Remove the domain from the blacklist if it is legitimate.")
    if "not a valid email format" in text:
        causes.append("One or more addresses are not valid email addresses.")
        suggestions.append("Fix or delete the broken entries in web UI → Recipients.")
    if "malformed" in text:
        causes.append("One or more recipient entries are missing their email field.")
        suggestions.append("Re-add those recipients in the web UI.")
    if "server rejected the send" in text:
        causes.append(
            "The SMTP server refused delivery to one or more addresses "
            "(bad mailbox, provider block, or rate limit)."
        )
        suggestions.append(
            "Check the exact server message in mailer.log; try those addresses "
            "individually with Send test email."
        )
    if "could not be saved" in text:
        causes.append("sent.json could not be written (disk full? permissions?).")
        suggestions.append(
            "Check free disk space and write permissions on the project folder."
        )
    if not causes:
        causes.append("See the details above for the per-recipient messages.")
        suggestions.append("Inspect mailer.log for the full server responses.")
    return causes, suggestions


def send_test(address):
    """Send a single test email to the given address (bypasses domain rules)."""
    from validator import check_email

    config = load_config()

    try:
        server = _connect(config)
    except Exception as e:
        logger.error(f"Test email: connection failed: {e}")
        what, causes = classify_smtp_error(e)
        report = build_report(
            "test",
            f"Test email to {address} could not be sent: SMTP connection failed.",
            exc=e,
            detail_lines=[what],
            causes=causes,
            suggestions=[
                "Fix SMTP_HOST / port / credentials in the web UI and retry.",
            ],
        )
        alert("Test email: SMTP connection failed", report)
        return {"ok": False, "error": what}

    test_config = dict(config)
    test_config["subject"] = f"[TEST] {config['subject'] or 'Test email'}"

    html = load_template().replace("{{name}}", "Test Recipient")

    ok, reason = check_email(address)
    note = f" (note: {reason})" if not ok else ""

    try:
        msg = _build_message(test_config, address, html)
        server.sendmail(config["smtp_user"], address, msg.as_string())
        logger.info(f"Test email sent to {mask_email(address)}{note}")
        return {"ok": True, "note": note.strip()}
    except Exception as e:
        logger.error(f"Test email failed for {address}: {e}")
        what, causes = classify_smtp_error(e)
        report = build_report(
            "test",
            f"Test email to {address} failed while sending.",
            exc=e,
            detail_lines=[what, f"Target address: {address}"]
            + (["Domain rule note: " + reason] if not ok else []),
            causes=causes,
            suggestions=[
                "Verify the target address exists.",
                "Check the provider's spam/relay rules for the From address.",
            ],
        )
        alert(f"Test email to {address} failed", report)
        return {"ok": False, "error": what}
    finally:
        try:
            server.quit()
        except Exception:
            pass


def clear_sent_history():
    """Reset sent.json so the next run re-sends to everyone."""
    save_sent_history({})
    logger.info("Sent history cleared.")
    return True


# -----------------------------
# Lock (prevents overlapping runs, e.g. scheduled + manual)
# -----------------------------
def run_with_lock(func, *args, timeout=5):
    """Run func under a file lock so two jobs can't overlap.

    Any unhandled exception is caught and reported via an alert email that
    includes the full traceback.
    """
    lock = FileLock(LOCK_FILE, timeout=timeout)
    try:
        with lock:
            try:
                return func(*args)
            except Exception as e:
                logger.exception(f"Job crashed: {e}")
                report = build_report(
                    "scheduled",
                    f"Email job CRASHED before completing: {type(e).__name__}: {e}",
                    exc=e,
                    suggestions=[
                        "Fix the underlying issue, then run again from the web UI.",
                        "Check mailer.log for context around the crash.",
                    ],
                )
                alert(f"Email job crashed: {type(e).__name__}", report)
                return {"ok": False, "error": f"{type(e).__name__}: {e}", "crashed": True}
    except Timeout:
        logger.warning("Job skipped: another instance is running.")
        return {"skipped": True, "reason": "another instance is running"}
