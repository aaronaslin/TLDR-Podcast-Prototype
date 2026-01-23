"""RSS service wrapper and episode store handling."""
import json
import os
from datetime import datetime, timezone
from typing import List

from src.core.models import Episode
from src.rss_feed import create_or_update_rss_feed


def load_episode_store(store_path: str) -> List[Episode]:
    if not os.path.exists(store_path):
        return []
    with open(store_path, "r") as f:
        data = json.load(f)
    return [Episode.from_dict(item) for item in data]


def save_episode_store(store_path: str, episodes: List[Episode]) -> None:
    os.makedirs(os.path.dirname(store_path), exist_ok=True)
    with open(store_path, "w") as f:
        json.dump([e.to_dict() for e in episodes], f, indent=2)


def upsert_episode(episodes: List[Episode], new_episode: Episode) -> List[Episode]:
    updated = [e for e in episodes if e.audio_url != new_episode.audio_url]
    updated.append(new_episode)
    # Sort newest first
    updated.sort(key=lambda e: e.pub_date, reverse=True)
    return updated


def generate_feed_from_store(episodes: List[Episode], output_file: str) -> str:
    # Convert to dicts for feedgen
    episode_dicts = [
        {
            "title": e.title,
            "audio_url": e.audio_url,
            "description": e.description,
            "pub_date": _ensure_tz(e.pub_date),
            "file_size": e.file_size,
            "link": e.link,
        }
        for e in episodes
    ]
    return create_or_update_rss_feed(episode_dicts, output_file)


def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
