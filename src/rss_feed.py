"""
RSS feed generation module for podcast publishing.
"""
from datetime import datetime
from feedgen.feed import FeedGenerator
from src.config import Config
import os
import re
import html as _html

from bs4 import BeautifulSoup


def _strip_html(value: str) -> str:
    """Best-effort HTML -> plain text for RSS/iTunes summary fields."""
    if not value:
        return ""
    # Preserve link destinations for clients that only display <description>.
    # Convert: <a href="URL">Text</a> -> "Text (URL)" before stripping tags.
    try:
        soup = BeautifulSoup(value, "html.parser")
        for a in soup.find_all("a"):
            href = (a.get("href") or "").strip()
            label = a.get_text(" ", strip=True)
            if href and label:
                a.replace_with(f"{label} ({href})")
            elif href:
                a.replace_with(href)
            else:
                a.replace_with(label)
        text = soup.get_text(" ", strip=True)
    except Exception:
        # Fallback: strip tags and unescape entities.
        text = re.sub(r"<[^>]+>", " ", value)

    text = _html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def create_or_update_rss_feed(episodes, output_file='feed.xml'):
    """
    Create or update RSS feed with podcast episodes.
    
    Args:
        episodes (list): List of episode dictionaries with keys:
                        - title (str)
                        - audio_url (str)
                        - description (str)
                        - pub_date (datetime)
                        - duration (int, optional): Duration in seconds
                        - file_size (int, optional): File size in bytes
                        - link (str, optional): Episode URL
        output_file (str): Path where RSS feed XML should be saved
        
    Returns:
        str: Path to the generated RSS feed file
    """
    fg = FeedGenerator()
    
    # Podcast metadata
    fg.title(Config.PODCAST_TITLE)
    fg.description(Config.PODCAST_DESCRIPTION)
    if Config.PODCAST_EMAIL:
        fg.author({'name': Config.PODCAST_AUTHOR, 'email': Config.PODCAST_EMAIL})
    else:
        fg.author({'name': Config.PODCAST_AUTHOR})

    # RSS requires at least one link
    feed_url = Config.RSS_FEED_URL or 'https://example.com/feed.xml'
    fg.link(href=feed_url, rel='alternate')
    fg.link(href=feed_url, rel='self')
    fg.language('en')
    
    if Config.PODCAST_IMAGE_URL:
        fg.image(Config.PODCAST_IMAGE_URL)
    
    # Load podcast extension for iTunes tags
    fg.load_extension('podcast')
    
    # Set podcast-level (channel) iTunes metadata
    fg.podcast.itunes_author(Config.PODCAST_AUTHOR)
    fg.podcast.itunes_category('Technology')
    if Config.PODCAST_IMAGE_URL:
        fg.podcast.itunes_image(Config.PODCAST_IMAGE_URL)
    fg.podcast.itunes_explicit('no')
    if Config.PODCAST_OWNER and Config.PODCAST_EMAIL:
        fg.podcast.itunes_owner(Config.PODCAST_OWNER, Config.PODCAST_EMAIL)
    
    # Add episodes
    for episode in episodes:
        fe = fg.add_entry()
        
        # Use audio URL as unique ID
        fe.id(episode['audio_url'])
        fe.title(episode['title'])
        # feedgen escapes HTML inside <description>. To support clickable links in podcast
        # show notes, we publish HTML via <content:encoded> (CDATA) and keep <description>
        # as a plain-text fallback.
        raw_description = episode.get('description', '') or ''
        plain_description = _strip_html(raw_description)
        fe.description(plain_description)
        if raw_description:
            fe.content(raw_description, type='CDATA')
        fe.published(episode['pub_date'])
        
        # Add episode link (use RSS feed URL if not provided)
        episode_link = episode.get('link', Config.RSS_FEED_URL)
        fe.link(href=episode_link)
        
        # Add audio enclosure with proper file size
        file_size = episode.get('file_size', 0)
        fe.enclosure(episode['audio_url'], file_size, 'audio/mpeg')
        
        # iTunes metadata for the episode
        fe.podcast.itunes_author(Config.PODCAST_AUTHOR)
        fe.podcast.itunes_explicit('no')
        if plain_description:
            fe.podcast.itunes_summary(plain_description)
        
        # Optional duration field
        if 'duration' in episode:
            fe.podcast.itunes_duration(episode['duration'])
    
    # Generate RSS XML
    fg.rss_file(output_file, pretty=True)
    
    return output_file


# TODO: Add validation for episode data
# TODO: Add support for reading existing feed and appending
# TODO: Add iTunes-specific tags for better podcast support
