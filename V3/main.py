import json
from logging.handlers import TimedRotatingFileHandler
import smtplib
import ssl
import os
import logging
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from validator import validate_email
from filelock import FileLock, Timeout

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


handler = TimedRotatingFileHandler("mailer.log", when="midnight", interval=1, backupCount=7)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ========================
# Email configuration
# ========================
required_env = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SUBJECT",
    "SEND_DAY",
    "SEND_HOUR",
    "SEND_MINUTE",
    "MAX_RECIPIENTS"
]

missing = [
    key for key in required_env
    if not os.getenv(key)
]

if missing:
    raise RuntimeError(
        f"Missing environment variables: {missing}"
    )


SMTP_SERVER = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

EMAIL = os.getenv("SMTP_USER")
PASSWORD = os.getenv("SMTP_PASSWORD")

SUBJECT = os.getenv("SUBJECT")

SEND_DAY = int(os.getenv("SEND_DAY"))
SEND_HOUR = int(os.getenv("SEND_HOUR"))
SEND_MINUTE = int(os.getenv("SEND_MINUTE"))
MAX_RECIPIENTS = int(os.getenv("MAX_RECIPIENTS"))

# ========================
# Load recipients
# ========================
with open("recipients.json", "r") as f:
    recipients = json.load(f)

SENT_FILE = "sent.json"

if os.path.exists(SENT_FILE):
    try:
        with open(SENT_FILE, "r") as f:
            sent_history = json.load(f)
    except json.JSONDecodeError:
        logger.warning(
            "sent.json is invalid. Creating a new history file."
        )
        sent_history = {}
else:
    sent_history = {}

if len(recipients) > MAX_RECIPIENTS:
    raise RuntimeError(
        "Recipient limit exceeded"
    )

# ========================
# Load HTML template
# ========================
with open("email.html", "r", encoding="utf-8") as f:
    html = f.read()

def mask_email(email):
    user, domain = email.split("@")

    return (
        user[:2]
        + "***@"
        + domain
    )

def add_to_sent_history(email):
    sent_history[email] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("sent.json", "w") as f:
        json.dump(sent_history, f, indent=4)


def send_emails():
    # Logging the start of the email sending process
    logger.info("=" * 50)
    logger.info("Starting monthly email job.")

    try:
        context = ssl.create_default_context()

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30)
        server.login(EMAIL, PASSWORD)

        masked_email = mask_email(EMAIL)


        logger.info("Connected to SMTP server.")
        logger.info(f"Authenticated as {masked_email}")
    except Exception as e:
        logger.error(f"Failed to connect or login to SMTP server: {e}")
        return
    
    success = 0
    failed = 0

    for name, info in recipients.items():
        recipient = info.get("email")

        if recipient in sent_history:
            logger.info(f"Skipping {name} ({mask_email(recipient)}) - Already sent.")
            continue

        if not validate_email(recipient):
            logger.warning(
                f"Skipping invalid recipient: {recipient}"
            )
            failed += 1
            continue

        recipient = info["email"]

        msg = MIMEMultipart("alternative")
        msg["Subject"] = SUBJECT
        msg["From"] = EMAIL
        msg["To"] = recipient

        personalized_html = html.replace("{{name}}", name.title())

        msg.attach(MIMEText(personalized_html, "html"))

        try:
            server.sendmail(EMAIL, recipient, msg.as_string())
            add_to_sent_history(recipient)
            logger.info(f"Email sent to {name} ({mask_email(recipient)}) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            success += 1
        except Exception as e:
            logger.error(f"Failed to send email to {name} ({mask_email(recipient)}) - {e}")
            failed += 1

    # Logging the completion of the email sending process
    logger.info(f"Finished sending {len(recipients)} emails.")
    logger.info(f"Successful: {success}, Failed: {failed}")
    logger.info("=" * 50)

    server.quit()

# ========================
# Job lock protection
# ========================
lock = FileLock(
    os.path.join(BASE_DIR, "mailer.lock"),
    timeout=5
)

def locked_send_emails():

    try:
        logger.info("Trying to acquire email job lock...")

        with lock:
            logger.info("Lock acquired.")
            send_emails()

        logger.info("Lock released.")

    except Timeout:
        logger.warning(
            "Email job skipped: another instance is running."
        )

scheduler = BlockingScheduler()

# Every month on the 5th at 11:00
scheduler.add_job(
    locked_send_emails,
    trigger="cron",
    day=SEND_DAY,
    hour=SEND_HOUR,
    minute=SEND_MINUTE,
    id="monthly_email_job",
    max_instances=1,
    coalesce=True,
)

logger.info("Scheduler started...")
logger.info(f"Emails will be sent on day {SEND_DAY} at {SEND_HOUR}:{SEND_MINUTE:02d} every month.")
scheduler.start()