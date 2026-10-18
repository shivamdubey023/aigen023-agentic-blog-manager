import unittest
from core import database as db
from property_a_blog.seo_optimizer import affiliate_box, content_quality_checks, parse_headings, render_article

class SeoTests(unittest.TestCase):
    def test_toc_anchors_and_schema_are_rendered(self):
        body, schema = render_article("# Title\n\n## Install Python\n\nRun it.\n\n### Windows\n\nDetails.", "Title", "python install")
        self.assertIn('href="#install-python"', body)
        self.assertIn('id="install-python"', body)
        self.assertIn('"@type": "TechArticle"', body)
        self.assertIn("application/ld+json", body)
    def test_duplicate_headings_get_unique_anchors(self):
        headings = parse_headings("## Setup\n\n## Setup")
        self.assertEqual([x["anchor"] for x in headings], ["setup", "setup-2"])
    def test_affiliate_box_discloses_and_qualifies_link(self):
        box = affiliate_box("Example", "https://example.com/?ref=abc", "We may earn a commission.")
        self.assertIn('rel="sponsored nofollow noopener"', box)
        self.assertIn("Affiliate disclosure", box)
    def test_quality_checks_are_warnings_not_exception(self):
        warnings = content_quality_checks("Short", "# Short\n\nTiny")
        self.assertTrue(any("words" in x.lower() for x in warnings))

class DatabaseTests(unittest.TestCase):
    def test_schema_initializes_and_article_roundtrips(self):
        import tempfile
        from pathlib import Path
        original = db.DB_PATH
        try:
            with tempfile.TemporaryDirectory() as folder:
                db.DB_PATH = Path(folder) / "test.db"
                db.init_db()
                article_id = db.save_article(topic="Python", primary_keyword="python", title="Python guide",
                    markdown_body="# Python", status="DRAFT")
                saved = db.get_article(article_id)
                self.assertEqual(saved["title"], "Python guide")
                self.assertEqual(saved["status"], "DRAFT")
        finally:
            db.DB_PATH = original

if __name__ == "__main__":
    unittest.main()
