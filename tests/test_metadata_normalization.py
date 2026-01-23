import unittest

from src.text_processor import normalize_metadata_text


class TestMetadataNormalization(unittest.TestCase):
    def test_possessive_missing_space(self):
        self.assertEqual(
            normalize_metadata_text("Nvidia’sweakness"),
            "Nvidia’s weakness",
        )
        self.assertEqual(
            normalize_metadata_text("Nvidia'sweakness"),
            "Nvidia's weakness",
        )

    def test_emoji_word_spacing(self):
        self.assertEqual(
            normalize_metadata_text("exodus👋"),
            "exodus 👋",
        )
        self.assertEqual(
            normalize_metadata_text("👋exodus"),
            "👋 exodus",
        )

    def test_collapse_whitespace(self):
        self.assertEqual(
            normalize_metadata_text("  A\n\tB  "),
            "A B",
        )


if __name__ == "__main__":
    unittest.main()
