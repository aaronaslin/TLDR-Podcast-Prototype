"""Main pipeline orchestration."""
import logging
import os
import html
from datetime import date
from datetime import datetime, timezone
from pathlib import Path

from src.config import Config
from src.config.settings import Settings
from src.core.models import Episode
from src.services.ingest_service import fetch_latest_digest
from src.services.tts_service import generate_audio
from src.services.storage_service import upload_file
from src.services.rss_service import (
    load_episode_store,
    save_episode_store,
    upsert_episode,
    generate_feed_from_store,
)
from src.text_processor import (
    clean_html_content,
    clean_text_for_tts,
    extract_show_note_links,
    normalize_metadata_text,
)

logger = logging.getLogger(__name__)


def _format_episode_timestamp_for_filename(dt: datetime) -> str:
    """Format a timestamp for filenames without changing the calendar date.

    We intentionally *do not* convert to UTC here. Podcast hosting/clients don't
    care about the filename timezone, but humans do: the filename should reflect
    the digest email's date as received.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y%m%d_%H%M%S")


def run_pipeline(target_date: date | None = None) -> str:
    settings = Settings.load()

    # Validate configuration
    Config.validate()
    logger.info("Configuration validated")

    logger.info("Fetching latest digest email")
    digest = fetch_latest_digest(
        username=Config.EMAIL_USERNAME,
        password=Config.EMAIL_PASSWORD,
        subject_filter=Config.EMAIL_SUBJECT_FILTER,
        folder=Config.EMAIL_FOLDER,
        search_by=Config.EMAIL_SEARCH_BY,
        imap_server=settings.imap_server,
        target_date=target_date,
    )

    if not digest or not digest.body:
        raise ValueError("No matching emails found.")

    # The episode description/show notes should lead with the email subject.
    # (The audio content is the full read-out; it should not be duplicated into metadata.)
    email_subject_raw = (digest.subject or "").strip() or Config.EMAIL_SUBJECT_FILTER
    email_subject = normalize_metadata_text(email_subject_raw)

    # Process text
    logger.info("Processing and cleaning text")
    if "<html" in digest.body.lower() or "<body" in digest.body.lower():
        cleaned_text = clean_html_content(digest.body)
    else:
        cleaned_text = digest.body

    tts_text = clean_text_for_tts(cleaned_text, verbose=True)
    logger.info("Text processed (%s characters)", len(tts_text))

    # Build show notes: clickable headline links for podcast description metadata.
    show_note_links = []
    if "<html" in cleaned_text.lower() or "<body" in cleaned_text.lower():
        try:
            show_note_links = extract_show_note_links(cleaned_text)
        except Exception:
            logger.exception("Failed to extract show note links")
            show_note_links = []

    # Save processed text for inspection
    if settings.save_processed_text:
        Path(settings.output_dir).mkdir(exist_ok=True)
        with open(os.path.join(settings.output_dir, "processed_text.txt"), "w") as f:
            f.write(tts_text)
        logger.info("Processed text saved")

    # Determine episode date.
    # Keep the email's own timezone for naming (so the filename date matches the email date).
    episode_date = digest.received_at or datetime.now(timezone.utc)
    if episode_date.tzinfo is None:
        episode_date = episode_date.replace(tzinfo=timezone.utc)

    timestamp = _format_episode_timestamp_for_filename(episode_date)
    audio_filename = f"digest_{timestamp}.mp3"
    audio_path = os.path.join(settings.output_dir, audio_filename)

    # Episode description/show notes HTML. RSS will publish this as <content:encoded>.
    description_parts = [f"<p><b>{html.escape(email_subject)}</b></p>"]
    if show_note_links:
        items = []
        for link in show_note_links:
            text = html.escape(link.get("text", "").strip())
            url = html.escape(link.get("url", "").strip(), quote=True)
            if not text or not url:
                continue
            items.append(f'<li><a href="{url}">{text}</a></li>')
        if items:
            description_parts.append("<p><b>Headlines</b></p>")
            description_parts.append("<ul>" + "".join(items) + "</ul>")
    episode_description = "".join(description_parts)

    # Idempotency: if this episode already exists, skip TTS and upload (unless forced)
    episodes = load_episode_store(settings.episodes_store)
    expected_audio_url = f"https://storage.googleapis.com/{Config.GCS_BUCKET_NAME}/episodes/{audio_filename}"
    if (not Config.FORCE_REGENERATE) and any(e.audio_url == expected_audio_url for e in episodes):
        logger.info("Episode already exists for %s, skipping generation", timestamp)

        existing_title = f"Daily Digest - {episode_date.strftime('%B %d, %Y')}: {email_subject}"

        # Ensure metadata (description/show notes) stays current even when audio generation is skipped.
        updated = False
        for e in episodes:
            if e.audio_url == expected_audio_url:
                if e.title != existing_title:
                    e.title = existing_title
                    updated = True
                if e.description != episode_description:
                    e.description = episode_description
                    updated = True
                break
        if updated:
            save_episode_store(settings.episodes_store, episodes)

        rss_file = generate_feed_from_store(episodes, settings.feed_file)
        feed_url = upload_file(rss_file, "feed.xml", content_type="application/rss+xml")
        if not feed_url:
            raise ValueError("Failed to upload RSS feed")
        logger.info("RSS feed uploaded: %s", feed_url)
        return feed_url

    if Config.FORCE_REGENERATE and any(e.audio_url == expected_audio_url for e in episodes):
        logger.info("FORCE_REGENERATE enabled; overwriting existing episode for %s", timestamp)

    # Generate audio
    logger.info("Generating audio")
    generate_audio(tts_text, audio_path, email_date=episode_date)
    logger.info("Audio generated: %s", audio_path)

    # Upload audio
    logger.info("Uploading audio")
    audio_url = upload_file(audio_path, f"episodes/{audio_filename}")
    if not audio_url:
        raise ValueError("Failed to upload audio")
    logger.info("Audio uploaded: %s", audio_url)

    # Episode metadata
    file_size = os.path.getsize(audio_path)
    episode_title = f"Daily Digest - {episode_date.strftime('%B %d, %Y')}: {email_subject}"
    episode = Episode(
        title=episode_title,
        audio_url=audio_url,
        description=episode_description,
        pub_date=episode_date,
        file_size=file_size,
        link=Config.RSS_FEED_URL,
    )

    # Update episode store
    logger.info("Updating episode store")
    episodes = upsert_episode(episodes, episode)
    save_episode_store(settings.episodes_store, episodes)

    # Generate feed from store
    logger.info("Generating RSS feed")
    rss_file = generate_feed_from_store(episodes, settings.feed_file)

    # Upload feed
    logger.info("Uploading RSS feed")
    feed_url = upload_file(rss_file, "feed.xml", content_type="application/rss+xml")
    if not feed_url:
        raise ValueError("Failed to upload RSS feed")
    logger.info("RSS feed uploaded: %s", feed_url)

    return feed_url
