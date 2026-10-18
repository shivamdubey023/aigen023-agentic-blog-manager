import unittest
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core import database as db
from property_a_blog.blogger_client import finish_oauth, get_redirect_uri
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
                db.store_oauth_state("test-state", "test-verifier")
                self.assertEqual(db.consume_oauth_state("test-state"), "test-verifier")
                self.assertIsNone(db.consume_oauth_state("test-state"))
        finally:
            db.DB_PATH = original

class OAuthTests(unittest.TestCase):
    def test_redirect_uri_can_be_configured_for_local_development(self):
        with patch.dict(os.environ, {"GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8501/"}):
            self.assertEqual(get_redirect_uri(), "http://localhost:8501/")

    @patch("requests.get")
    @patch("property_a_blog.blogger_client.db.consume_oauth_state", return_value="test-verifier")
    @patch("property_a_blog.blogger_client.Flow.from_client_config")
    def test_oauth_identity_check_uses_bearer_access_token(self, flow_factory, _consume_state, get):
        credentials = SimpleNamespace(
            token="test-access-token",
            to_json=lambda: '{"token":"test-access-token"}',
        )
        flow = SimpleNamespace(
            oauth2session=SimpleNamespace(_client=SimpleNamespace(scope="openid")),
            credentials=credentials,
            fetch_token=Mock(),
        )
        flow_factory.return_value = flow
        response = Mock()
        response.json.return_value = {
            "email": "owner@example.com",
            "email_verified": True,
            "name": "Owner",
        }
        get.return_value = response
        session_state = {}

        result = finish_oauth(
            "authorization-code",
            "oauth-state",
            session_state,
            client_id="client-id",
            client_secret="client-secret",
        )

        self.assertIs(result, credentials)
        flow.fetch_token.assert_called_once_with(code="authorization-code")
        get.assert_called_once_with(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": "Bearer test-access-token"},
            timeout=15,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(session_state["google_user"]["email"], "owner@example.com")

if __name__ == "__main__":
    unittest.main()
