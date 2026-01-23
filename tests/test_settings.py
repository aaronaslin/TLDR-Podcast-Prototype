import os
import unittest

from src.config.settings import Settings


class TestSettings(unittest.TestCase):
    def test_settings_defaults(self):
        settings = Settings.load()
        self.assertTrue(settings.output_dir)
        self.assertTrue(settings.feed_file)

    def test_log_level_default(self):
        settings = Settings.load()
        self.assertTrue(settings.log_level)


if __name__ == "__main__":
    unittest.main()
