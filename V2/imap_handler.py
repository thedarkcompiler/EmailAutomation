import imaplib
import email
from email.header import decode_header
import ssl
import config


# ✅ Strato's REAL folder names
FOLDER_MAP = {
    "INBOX":     "INBOX",
    "Sent":      "Sent Items",
    "Drafts":    "Drafts",
    "Trash":     "Trash",
    "Spam":      "Spam",
    "Archive":   "Archive"
}


def connect_imap():
    """Connect to Strato IMAP server."""
    try:
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT, ssl_context=context)
        mail.login(config.EMAIL, config.PASSWORD)
        return mail
    except imaplib.IMAP4.error as e:
        print(f"IMAP connection error: {e}")
        return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None


def select_folder(mail, folder):
    """
    Select folder using Strato's real folder names.
    Returns (success: bool, selected_name: str)
    """
    # Translate display name to real Strato folder name
    real_name = FOLDER_MAP.get(folder, folder)

    variations = [
        real_name,
        f'"{real_name}"',  # ✅ Quoted - needed for "Sent Items" with space!
        folder,
        f'"{folder}"',
    ]

    for variant in variations:
        try:
            status, data = mail.select(variant)
            if status == "OK":
                print(f"✅ Selected folder: {variant}")
                return True, variant
            else:
                print(f"Failed variant '{variant}': status={status}")
        except Exception as e:
            print(f"Failed variant '{variant}': {e}")

    return False, None


def get_folders():
    """Get ALL real folder names from the server."""
    folders = []
    try:
        mail = connect_imap()
        if not mail:
            return []

        status, folder_list = mail.list()
        if status == "OK":
            for f in folder_list:
                decoded = f.decode()
                print(f"RAW FOLDER: {decoded}")
                # Parse folder name after last delimiter
                if '"."' in decoded:
                    folder_name = decoded.split('"."')[-1].strip().strip('"')
                elif '"/"' in decoded:
                    folder_name = decoded.split('"/"')[-1].strip().strip('"')
                elif "NIL" in decoded:
                    folder_name = decoded.split("NIL")[-1].strip().strip('"')
                else:
                    folder_name = decoded.split()[-1].strip().strip('"')
                folders.append(folder_name)
                print(f"PARSED FOLDER: {folder_name}")
        mail.logout()

    except Exception as e:
        print(f"Error fetching folders: {e}")

    return folders


def fetch_emails(folder="INBOX", limit=20):
    """
    Fetch emails from a folder.

    Args:
        folder (str): Display folder name (e.g. INBOX, Sent, Drafts)
        limit (int): Max number of emails to fetch

    Returns:
        list: List of email dictionaries
    """
    emails = []
    try:
        mail = connect_imap()
        if not mail:
            print("❌ Could not connect to IMAP server.")
            return []

        # ✅ Select folder with Strato name mapping
        success, selected = select_folder(mail, folder)

        if not success:
            print(f"❌ Could not select folder: {folder}")
            print("Available folders:")
            _, folder_list = mail.list()
            for f in folder_list:
                print(f"  {f.decode()}")
            mail.logout()
            return []

        # ✅ Search all emails
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print(f"❌ Search failed in folder: {selected}")
            mail.logout()
            return []

        email_ids = messages[0].split()

        if not email_ids:
            print(f"📭 No emails in {selected}")
            mail.logout()
            return []

        # Get last 'limit' emails newest first
        email_ids = email_ids[-limit:][::-1]
        print(f"📬 Found {len(email_ids)} emails in {selected}")

        for eid in email_ids:
            try:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK" or not msg_data or msg_data[0] is None:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # ✅ Decode safely
                subject = _decode_header_safe(msg.get("Subject", "(No Subject)"))
                sender  = _decode_header_safe(msg.get("From", "Unknown"))
                body    = _get_body(msg)

                emails.append({
                    "id":      eid,
                    "subject": subject,
                    "from":    sender,
                    "date":    msg.get("Date", ""),
                    "body":    body
                })

            except Exception as e:
                print(f"❌ Error reading email {eid}: {e}")
                continue

        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
    except Exception as e:
        print(f"Error fetching emails: {e}")

    return emails


def delete_email(email_id, folder="INBOX"):
    """Delete an email by ID."""
    try:
        mail = connect_imap()
        if not mail:
            return False, "Could not connect to IMAP server."

        success, _ = select_folder(mail, folder)
        if not success:
            return False, f"Could not select folder: {folder}"

        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
        mail.logout()
        return True, "Email deleted successfully."

    except Exception as e:
        return False, str(e)


def mark_as_read(email_id, folder="INBOX"):
    """Mark an email as read."""
    try:
        mail = connect_imap()
        if not mail:
            return False

        success, _ = select_folder(mail, folder)
        if not success:
            return False

        mail.store(email_id, "+FLAGS", "\\Seen")
        mail.logout()
        return True

    except Exception:
        return False


def mark_as_unread(email_id, folder="INBOX"):
    """Mark an email as unread."""
    try:
        mail = connect_imap()
        if not mail:
            return False

        success, _ = select_folder(mail, folder)
        if not success:
            return False

        mail.store(email_id, "-FLAGS", "\\Seen")
        mail.logout()
        return True

    except Exception:
        return False


def move_email(email_id, from_folder, to_folder):
    """Move an email from one folder to another."""
    try:
        mail = connect_imap()
        if not mail:
            return False, "Could not connect."

        success, _ = select_folder(mail, from_folder)
        if not success:
            return False, f"Could not select folder: {from_folder}"

        # Get real destination folder name
        real_dest = FOLDER_MAP.get(to_folder, to_folder)

        mail.copy(email_id, f'"{real_dest}"')
        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
        mail.logout()
        return True, f"Moved to {to_folder}"

    except Exception as e:
        return False, str(e)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _decode_header_safe(value):
    """Safely decode an email header string."""
    if not value:
        return ""
    try:
        parts   = decode_header(value)
        decoded = ""
        for part, encoding in parts:
            if isinstance(part, bytes):
                decoded += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded += str(part)
        return decoded.strip()
    except Exception:
        return str(value)


def _get_body(msg):
    """Extract plain text body from an email message."""
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                content_type        = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if (content_type == "text/plain"
                        and "attachment" not in content_disposition):
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        body    = part.get_payload(decode=True).decode(
                            charset, errors="ignore"
                        )
                        break
                    except Exception:
                        continue
        else:
            try:
                charset = msg.get_content_charset() or "utf-8"
                body    = msg.get_payload(decode=True).decode(
                    charset, errors="ignore"
                )
            except Exception:
                body = ""

    except Exception as e:
        print(f"Error getting body: {e}")

    return body