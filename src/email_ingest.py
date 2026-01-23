"""
Email ingestion module for fetching digest emails via IMAP.
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import date, timedelta


def _decode_subject(value: str | None) -> str | None:
    if not value:
        return None
    parts = []
    for chunk, encoding in decode_header(value):
        if isinstance(chunk, bytes):
            try:
                parts.append(chunk.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(str(chunk))
    subject = "".join(parts).strip()
    return subject or None


def _imap_date(d: date) -> str:
    """Format a Python date as an IMAP date string (e.g., 21-Jan-2026)."""
    return d.strftime("%d-%b-%Y")


def get_latest_digest(
    username,
    password,
    subject_filter,
    folder="inbox",
    search_by="subject",
    imap_server="imap.gmail.com",
    target_date: date | None = None,
):
    """
    Fetch the latest email matching the filter from Gmail inbox.
    
    Args:
        username (str): Email account username
        password (str): Email account password (or app-specific password)
        subject_filter (str): Subject line or sender to filter emails
        folder (str): Gmail folder/label to search (default: "inbox")
        search_by (str): Search by "subject" or "from" (default: "subject")
        
    Returns:
        tuple: (Email body text, datetime object, subject str) or None if no matching emails found
    """
    mail = None
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select(f'"{folder}"')

        # Search for emails with specific subject or sender.
        # If target_date is provided, narrow results to that calendar day using
        # SINCE (inclusive) and BEFORE (exclusive).
        search_by_from = search_by.lower() == "from"
        base = f'FROM "{subject_filter}"' if search_by_from else f'SUBJECT "{subject_filter}"'
        if target_date:
            next_day = target_date + timedelta(days=1)
            criteria = f'({base} SINCE "{_imap_date(target_date)}" BEFORE "{_imap_date(next_day)}")'
        else:
            criteria = f'({base})'

        status, messages = mail.search(None, criteria)
        
        email_ids = messages[0].split()

        if not email_ids:
            return None

        # Fetch the latest email from the (optionally date-filtered) results.
        latest_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                email_date = parsedate_to_datetime(msg.get('Date'))
                subject = _decode_subject(msg.get('Subject'))
                body = ""
                
                if msg.is_multipart():
                    # Default placeholders
                    html_content = None
                    text_content = None
                    
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            html_content = part.get_payload(decode=True).decode()
                        elif content_type == "text/plain":
                            text_content = part.get_payload(decode=True).decode()
                    
                    # Prefer HTML content so we can parse links later
                    body = html_content if html_content else text_content
                else:
                    body = msg.get_payload(decode=True).decode()
                
                return body, email_date, subject
        
        return None
    
    except imaplib.IMAP4.abort as e:
        print(f"IMAP connection error: {e}")
        return None
    except Exception as e:
        print(f"Error fetching email: {e}")
        return None
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass  # Connection already closed
