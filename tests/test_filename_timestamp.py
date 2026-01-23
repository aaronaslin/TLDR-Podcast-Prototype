import unittest
from datetime import datetime, timedelta, timezone

from src.core.pipeline import _format_episode_timestamp_for_filename


class TestFilenameTimestamp(unittest.TestCase):
    def test_keeps_email_local_date(self):
        # 2025-01-16 23:30:00 -08:00 is 2025-01-17 07:30:00Z.
        # Filename must keep 20250116 (email's local date), not 20250117.
        pacific = timezone(timedelta(hours=-8))
        dt = datetime(2025, 1, 16, 23, 30, 0, tzinfo=pacific)
        self.assertTrue(_format_episode_timestamp_for_filename(dt).startswith("20250116_"))


if __name__ == "__main__":
    unittest.main()
