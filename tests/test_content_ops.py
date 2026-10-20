import unittest
import os
import requests
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core import database as db
from core.stock_images import provider_status, search_stock_images
from property_a_blog.blogger_client import (
    _create_oauth_state,
    _read_oauth_state,
    finish_oauth,
    get_redirect_uri,
    start_oauth,
    update_live_post_navigation,
)
from property_a_blog.navigation import navigation_content, order_live_posts
from property_a_blog.seo_optimizer import affiliate_box, content_quality_checks, parse_headings, render_article

class SeoTests(unittest.TestCase):
    def test_toc_anchors_and_schema_are_rendered(self):
        body, schema = render_article("# Title\n\n## Install Python\n\nRun it.\n\n### Windows\n\nDetails.", "Title", "python install")
        self.assertIn('href="#install-python"', body)
        self.assertIn('id="install-python"', body)
        self.assertIn('"@type": "TechArticle"', body)
        self.assertIn("application/ld+json", body)

    def test_markdown_sections_paragraphs_nested_lists_and_tables_render_semantically(self):
        source = """# Guide

## Setup

Intro paragraph.

### Requirements

- Python
  - Version 3.11

1. Install it
2. Verify it

| Feature | Value |
| --- | --- |
| Runtime | Python |
"""
        body, _ = render_article(source, "Guide")
        self.assertIn("<h2", body)
        self.assertIn("<h3", body)
        self.assertIn("<p>Intro paragraph.</p>", body)
        self.assertIn("<ul>", body)
        self.assertIn("<ol>", body)
        self.assertIn('<div class="article-table-scroll"', body)
        self.assertIn("<thead>", body)
        self.assertIn("<th>Feature</th>", body)

    def test_images_preserve_alt_caption_and_safe_attribution(self):
        body, _ = render_article(
            '![OAuth sequence](https://images.pexels.com/photos/1/flow.png "Source: Pexels photographer")',
            "OAuth",
            include_toc=False,
        )
        self.assertIn('<figure class="article-figure">', body)
        self.assertIn('alt="OAuth sequence"', body)
        self.assertIn("<figcaption>Source: Pexels photographer</figcaption>", body)
        self.assertIn("https://images.pexels.com/photos/1/flow.png", body)

    def test_fenced_code_keeps_its_language_class(self):
        body, _ = render_article(
            "```python\nprint('ready')\n```",
            "Example",
            include_toc=False,
        )
        self.assertIn('<pre><code class="language-python">', body)
        self.assertIn("print('ready')", body)

    def test_renderer_removes_unsafe_html_and_url_attributes(self):
        body, _ = render_article(
            '<script>alert("unsafe")</script>\n\n'
            '<img src="javascript:alert(1)" onerror="alert(1)">\n\n'
            '[bad](javascript:alert%281%29)',
            "Safe",
            include_toc=False,
        )
        self.assertNotIn('<script>alert("unsafe")</script>', body.lower())
        self.assertNotIn("onerror", body.lower())
        self.assertNotIn('href="javascript:', body.lower())
        self.assertNotIn('src="javascript:', body.lower())

    def test_process_diagrams_are_accessible_distinct_and_mobile_scrollable(self):
        source = """```diagram title="Request flow"
Browser -> API -> Database
```

```diagram title="Build flow"
Source -> Deploy
```"""
        body, _ = render_article(source, "Flows", include_toc=False)
        self.assertEqual(body.count("<svg"), 2)
        self.assertIn('viewBox="0 0 ', body)
        self.assertIn('width="', body)
        self.assertIn('overflow-x:auto', body)
        self.assertIn("Browser then API then Database", body)
        self.assertNotEqual(
            body.split('id="diagram-title-')[1].split('"')[0],
            body.split('id="diagram-title-')[2].split('"')[0],
        )

    def test_invalid_diagram_specification_is_reported_as_a_warning(self):
        warnings = content_quality_checks(
            "Flow",
            "```diagram\nOnly one step\n```",
        )
        self.assertTrue(any("Diagram could not be rendered" in warning for warning in warnings))

    def test_diagram_wraps_long_labels_inside_nodes(self):
        body = render_article(
            "```diagram\nBrowser request validation -> API\n```",
            "Flow",
            include_toc=False,
        )[0]
        self.assertIn("<tspan", body)
        self.assertIn("Browser request", body)
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

    def test_quality_checks_flag_heading_level_jumps(self):
        warnings = content_quality_checks("Guide", "## Setup\n\n#### Advanced")
        self.assertTrue(any("skipping levels" in warning for warning in warnings))
        valid = content_quality_checks("Guide", "## Setup\n\n### Details\n\n## Next")
        self.assertFalse(any("skipping levels" in warning for warning in valid))
    def test_ebook_card_box_renders_instamojo_cta(self):
        from property_a_blog.seo_optimizer import ebook_card_box
        box = ebook_card_box(title="Code to Career", product_url="https://codetocareer52.myinstamojo.com/product/code-to-career")
        self.assertIn("Code to Career", box)
        self.assertIn("https://codetocareer52.myinstamojo.com/product/code-to-career", box)
        self.assertIn("Get eBook on Instamojo", box)

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
                with self.assertRaisesRegex(ValueError, "linked to a confirmed Blogger draft"):
                    db.delete_article(article_id, require_blogger_post=True)
                db.save_article(topic="Python", primary_keyword="python", title="Python guide",
                    markdown_body="# Python", article_id=article_id, blogger_post_id="post-1")
                db.save_article(topic="Python edited", primary_keyword="python", title="Python guide",
                    markdown_body="# Python edited", article_id=article_id)
                self.assertEqual(db.get_article(article_id)["blogger_post_id"], "post-1")
                self.assertTrue(db.delete_article(article_id, require_blogger_post=True))
                self.assertIsNone(db.get_article(article_id))
                db.store_oauth_state("test-state", "test-verifier")
                self.assertEqual(db.consume_oauth_state("test-state"), "test-verifier")
                self.assertIsNone(db.consume_oauth_state("test-state"))
        finally:
            db.DB_PATH = original

class StockImageTests(unittest.TestCase):
    @patch("core.stock_images.get_pexels_key", return_value="server-key")
    @patch("core.stock_images.requests.get")
    def test_pexels_results_are_normalized_and_use_only_provider_image_hosts(self, get, _key):
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.json.return_value = {"photos": [
            {
                "src": {
                    "large": "https://images.pexels.com/photos/1/large.jpg",
                    "medium": "https://images.pexels.com/photos/1/medium.jpg",
                },
                "alt": "A developer",
                "photographer": "Example",
                "photographer_url": "https://www.pexels.com/@example",
                "url": "https://www.pexels.com/photo/1",
            },
            {
                "src": {"large": "https://attacker.example/image.jpg"},
                "url": "https://www.pexels.com/photo/2",
                "photographer_url": "https://www.pexels.com/@example",
            },
        ]}
        get.return_value = response

        images = search_stock_images("python", "pexels")

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["photographer"], "Example")
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "server-key")

    @patch("core.stock_images.get_unsplash_key", return_value="")
    @patch("core.stock_images.requests.get")
    def test_missing_unsplash_key_fails_without_request(self, get, _key):
        with self.assertRaisesRegex(ValueError, "UNSPLASH_ACCESS_KEY"):
            search_stock_images("python", "unsplash")
        get.assert_not_called()

    @patch("core.stock_images.get_pexels_key", return_value="server-key")
    @patch("core.stock_images.requests.get")
    def test_pexels_rate_limit_is_reported_without_fallback(self, get, _key):
        response = Mock(status_code=429, ok=False)
        get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "quota or rate limit"):
            search_stock_images("python", "pexels")

    @patch("core.stock_images.get_pexels_key", return_value="server-key")
    @patch("core.stock_images.requests.get", side_effect=requests.Timeout)
    def test_stock_image_timeout_is_actionable(self, _get, _key):
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            search_stock_images("python", "pexels")

    @patch("core.stock_images.get_pexels_key", return_value="server-key")
    @patch("core.stock_images.requests.get")
    def test_malformed_provider_response_is_reported(self, get, _key):
        response = Mock(status_code=200, ok=True)
        response.json.side_effect = ValueError("not JSON")
        get.return_value = response
        with self.assertRaisesRegex(RuntimeError, "invalid response"):
            search_stock_images("python", "pexels")

    @patch("core.stock_images.get_unsplash_key", return_value="unsplash-secret")
    @patch("core.stock_images.get_pexels_key", return_value="")
    def test_provider_status_only_reports_presence(self, _pexels, _unsplash):
        self.assertEqual(provider_status(), {"pexels": False, "unsplash": True})

class NavigationTests(unittest.TestCase):
    def test_live_posts_are_ordered_by_published_time_and_drafts_are_excluded(self):
        posts = [
            {"id": "later", "status": "LIVE", "published": "2025-02-02T00:00:00Z"},
            {"id": "draft", "status": "DRAFT", "published": "2024-01-01T00:00:00Z"},
            {"id": "earlier", "status": "LIVE", "published": "2025-02-01T00:00:00Z"},
        ]
        ordered, skipped = order_live_posts(posts)
        self.assertEqual([post["id"] for post in ordered], ["earlier", "later"])
        self.assertEqual(skipped, [])

    def test_navigation_replacement_is_idempotent_and_preserves_article_body(self):
        posts = [
            {"id": "1", "title": "First <Guide>", "url": "https://blog.example/first"},
            {"id": "2", "title": "Second", "url": "https://blog.example/second"},
        ]
        body = "<p>Article body</p>"
        once = navigation_content(body, posts[0], posts[1])
        twice = navigation_content(once, posts[0], posts[1])
        self.assertEqual(once, twice)
        self.assertIn("<p>Article body</p>", twice)
        self.assertIn('rel="prev"', twice)
        self.assertIn('rel="next"', twice)
        self.assertIn("First &lt;Guide&gt;", twice)

class BloggerNavigationUpdateTests(unittest.TestCase):
    @patch("property_a_blog.blogger_client.blogger_service")
    def test_live_post_update_requires_confirmation_and_preserves_other_fields(self, service_factory):
        service = Mock()
        service_factory.return_value = service
        service.posts.return_value.get.return_value.execute.return_value = {
            "id": "post-1",
            "status": "LIVE",
            "title": "Existing title",
            "content": "<p>Before</p>",
        }
        service.posts.return_value.update.return_value.execute.return_value = {"id": "post-1"}

        with self.assertRaises(PermissionError):
            update_live_post_navigation(None, "blog-1", "post-1", "<p>After</p>")
        service_factory.assert_not_called()

        update_live_post_navigation(
            None,
            "blog-1",
            "post-1",
            "<p>After</p>",
            explicit_confirmation=True,
        )
        body = service.posts.return_value.update.call_args.kwargs["body"]
        self.assertEqual(body["title"], "Existing title")
        self.assertEqual(body["content"], "<p>After</p>")

    @patch("property_a_blog.blogger_client.blogger_service")
    def test_live_update_refuses_to_change_draft(self, service_factory):
        service = Mock()
        service_factory.return_value = service
        service.posts.return_value.get.return_value.execute.return_value = {"status": "DRAFT"}
        with self.assertRaisesRegex(PermissionError, "not LIVE"):
            update_live_post_navigation(
                None,
                "blog-1",
                "post-1",
                "<p>Navigation</p>",
                explicit_confirmation=True,
            )
        service.posts.return_value.update.assert_not_called()

class OAuthTests(unittest.TestCase):
    def test_redirect_uri_can_be_configured_for_local_development(self):
        with patch.dict(os.environ, {"GOOGLE_OAUTH_REDIRECT_URI": "http://localhost:8501/"}):
            self.assertEqual(get_redirect_uri(), "http://localhost:8501/")

    @patch("requests.get")
    @patch("property_a_blog.blogger_client.Flow.from_client_config")
    def test_oauth_identity_check_uses_bearer_access_token(self, flow_factory, get):
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
        state = _create_oauth_state("client-secret")
        session_state = {"oauth_state": state, "oauth_verifier": "a" * 50}

        result = finish_oauth(
            "authorization-code",
            state,
            session_state,
            client_id="client-id",
            client_secret="client-secret",
        )

        self.assertIs(result, credentials)
        flow.fetch_token.assert_called_once_with(code="authorization-code")
        self.assertEqual(flow_factory.call_args.kwargs["code_verifier"], "a" * 50)
        get.assert_called_once_with(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": "Bearer test-access-token"},
            timeout=15,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(session_state["google_user"]["email"], "owner@example.com")

    def test_oauth_state_is_signed_and_expiring(self):
        with patch("property_a_blog.blogger_client.time.time", return_value=1000):
            state = _create_oauth_state("client-secret")
        with patch("property_a_blog.blogger_client.time.time", return_value=1000):
            self.assertIsNone(_read_oauth_state(state, "client-secret"))
            with self.assertRaisesRegex(ValueError, "could not be verified"):
                _read_oauth_state(state + "tampered", "client-secret")
        with patch("property_a_blog.blogger_client.time.time", return_value=2000):
            with self.assertRaisesRegex(ValueError, "expired"):
                _read_oauth_state(state, "client-secret")

    def test_oauth_state_must_match_the_initiating_session(self):
        state = _create_oauth_state("client-secret")
        with self.assertRaisesRegex(ValueError, "does not match"):
            finish_oauth(
                "authorization-code",
                state,
                {},
                client_id="client-id",
                client_secret="client-secret",
            )

    @patch("property_a_blog.blogger_client.Flow.from_client_config")
    def test_oauth_start_keeps_pkce_state_out_of_sqlite(self, flow_factory):
        flow = SimpleNamespace(
            authorization_url=Mock(return_value=("https://accounts.google.com/auth", "unused")),
        )
        flow_factory.return_value = flow
        session_state = {}
        with patch("property_a_blog.blogger_client.db.store_oauth_state") as store_state:
            url = start_oauth(
                "client-id",
                "client-secret",
                session_state,
                redirect_uri="https://example.test/api/oauth/callback",
            )
        self.assertEqual(url, "https://accounts.google.com/auth")
        self.assertIn("oauth_state", session_state)
        self.assertIsNone(_read_oauth_state(session_state["oauth_state"], "client-secret"))
        self.assertEqual(session_state["oauth_verifier"], flow.code_verifier)
        self.assertNotIn(flow.code_verifier, session_state["oauth_state"])
        self.assertNotIn(flow.code_verifier, url)
        store_state.assert_not_called()

if __name__ == "__main__":
    unittest.main()
