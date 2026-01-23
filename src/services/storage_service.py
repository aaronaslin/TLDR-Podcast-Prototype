"""Storage service wrapper for uploads."""
from src.core.retry import retry
from src.gcs_upload import upload_to_gcs


def upload_file(local_path: str, gcs_key: str, content_type: str = "audio/mpeg", make_public: bool = True) -> str:
    return retry(lambda: upload_to_gcs(local_path, gcs_key, content_type=content_type, make_public=make_public))
