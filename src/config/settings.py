"""Typed settings for the application."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    # Output
    output_dir: str = "data/output"
    episodes_store: str = "data/episodes.json"
    feed_file: str = "data/output/feed.xml"
    save_processed_text: bool = True

    # Runtime
    imap_server: str = "imap.gmail.com"
    log_level: str = "INFO"

    @staticmethod
    def load() -> "Settings":
        load_dotenv()
        return Settings(
            output_dir=os.getenv("OUTPUT_DIR", "data/output"),
            episodes_store=os.getenv("EPISODES_STORE", "data/episodes.json"),
            feed_file=os.getenv("FEED_FILE", "data/output/feed.xml"),
            save_processed_text=os.getenv("SAVE_PROCESSED_TEXT", "true").lower() == "true",
            imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
