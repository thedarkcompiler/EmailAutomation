import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import config


def send_email(to, subject, body, attachments=None, cc=None, bcc=None):
    """
    Send an email via Strato SMTP server.
    
    Args:
        to (str or list): Recipient email(s)
        subject (str): Email subject
        body (str): Email body (HTML or plain text)
        attachments (list): List of file paths to attach
        cc (str or list): CC recipients
        bcc (str or list): BCC recipients
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Build message
        msg = MIMEMultipart("alternative")
        msg["From"] = config.EMAIL
        msg["To"] = to if isinstance(to, str) else ", ".join(to)
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
        if bcc:
            msg["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

        # Attach body (plain text + HTML fallback)
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(f"<html><body><p>{body}</p></body></html>", "html"))

        # Attach files if any
        if attachments:
            for filepath in attachments:
                if os.path.exists(filepath):
                    part = MIMEBase("application", "octet-stream")
                    with open(filepath, "rb") as f:
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(filepath)}"
                    )
                    msg.attach(part)

        # Build recipients list
        recipients = []
        if isinstance(to, list):
            recipients.extend(to)
        else:
            recipients.append(to)
        if cc:
            recipients.extend(cc if isinstance(cc, list) else [cc])
        if bcc:
            recipients.extend(bcc if isinstance(bcc, list) else [bcc])

        # Connect and send via SSL/TLS (port 465)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=context) as server:
            server.login(config.EMAIL, config.PASSWORD)
            server.sendmail(config.EMAIL, recipients, msg.as_string())

        return True, "Email sent successfully!"

    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check your email/password."
    except smtplib.SMTPConnectError:
        return False, "Could not connect to Strato SMTP server."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"