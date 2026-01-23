import os
import tempfile
import unittest
from datetime import datetime, timezone

from src.core.models import Episode
from src.services.rss_service import (
    load_episode_store,
    save_episode_store,
    upsert_episode,
    generate_feed_from_store,
)


class TestRssService(unittest.TestCase):
    def test_upsert_episode_orders_by_date(self):
        older = Episode(
            title="Older",
            audio_url="https://example.com/older.mp3",
            description="older",
            pub_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            file_size=1,
            link="https://example.com/feed.xml",
        )
        newer = Episode(
            title="Newer",
            audio_url="https://example.com/newer.mp3",
            description="newer",
            pub_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            file_size=2,
            link="https://example.com/feed.xml",
        )

        episodes = upsert_episode([older], newer)
        self.assertEqual(episodes[0].audio_url, newer.audio_url)
        self.assertEqual(episodes[1].audio_url, older.audio_url)

    def test_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store_path = os.path.join(tmp, "episodes.json")

            episode = Episode(
                title="Sample",
                audio_url="https://example.com/sample.mp3",
                description="sample",
                pub_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
                file_size=42,
                link="https://example.com/feed.xml",
            )

            save_episode_store(store_path, [episode])
            loaded = load_episode_store(store_path)

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].audio_url, episode.audio_url)
            self.assertEqual(loaded[0].file_size, episode.file_size)

    def test_feed_emits_clickable_links_via_content_encoded(self):
        with tempfile.TemporaryDirectory() as tmp:
            feed_path = os.path.join(tmp, "feed.xml")

            episode = Episode(
                title="Sample",
                audio_url="https://example.com/sample.mp3",
                description='<p>Summary</p><ul><li><a href="https://example.com/a">Headline</a></li></ul>',
                pub_date=datetime(2026, 2, 1, tzinfo=timezone.utc),
                file_size=42,
                link="https://example.com/feed.xml",
            )

            generate_feed_from_store([episode], feed_path)
            with open(feed_path, "r", encoding="utf-8") as f:
                xml = f.read()

            self.assertIn("<content:encoded><![CDATA[", xml)
            self.assertIn('<a href="https://example.com/a">Headline</a>', xml)
            # feedgen escapes HTML in <description>; we keep <description> plain text.
            self.assertNotIn("&lt;a", xml)


if __name__ == "__main__":
    unittest.main()
