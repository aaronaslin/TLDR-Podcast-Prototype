import unittest

from src.rss_feed import _strip_html


class TestRssDescriptionLinks(unittest.TestCase):
    def test_strip_html_preserves_anchor_urls(self):
        html = '<p><b>Headlines</b></p><ul><li><a href="https://example.com/a">Item A</a></li></ul>'
        text = _strip_html(html)
        self.assertIn("Item A (https://example.com/a)", text)


if __name__ == "__main__":
    unittest.main()
