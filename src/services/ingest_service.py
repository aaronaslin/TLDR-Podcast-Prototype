"""Email ingest service wrapper."""
from datetime import date
from typing import Optional
from src.core.models import Digest
from src.core.retry import retry
from src.email_ingest import get_latest_digest


def fetch_latest_digest(
    username: str,
    password: str,
    subject_filter: str,
    folder: str,
    search_by: str,
    imap_server: str,
    target_date: date | None = None,
) -> Optional[Digest]:
    result = retry(lambda: get_latest_digest(
        username=username,
        password=password,
        subject_filter=subject_filter,
        folder=folder,
        search_by=search_by,
        imap_server=imap_server,
        target_date=target_date,
    ))

    if not result:
        return None

    if isinstance(result, tuple):
        if len(result) == 3:
            body, received_at, subject = result
            return Digest(body=body, received_at=received_at, subject=subject)
        if len(result) == 2:
            body, received_at = result
            return Digest(body=body, received_at=received_at)

    return Digest(body=result)
