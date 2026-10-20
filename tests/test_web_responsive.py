import re
import unittest

from fastapi.testclient import TestClient

from api.index import app


class ResponsiveWebAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_homepage_has_mobile_navigation_for_every_application_tab(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', response.text)

        mobile_navigation = re.search(
            r'<nav class="mobile-bottom-nav".*?</nav>',
            response.text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(mobile_navigation)
        tab_ids = re.findall(r'data-tab="([^"]+)"', mobile_navigation.group(0))
        self.assertEqual(
            tab_ids,
            [
                "tab-autopilot",
                "tab-rewriter",
                "tab-generator",
                "tab-editor",
                "tab-images",
                "tab-monetize",
                "tab-blogger",
            ],
        )
        for tab_id in tab_ids:
            self.assertIn(f'id="{tab_id}"', response.text)

    def test_responsive_stylesheet_is_served(self):
        response = self.client.get("/static/css/style.css")

        self.assertEqual(response.status_code, 200)
        self.assertIn("@media (max-width: 768px)", response.text)
        self.assertIn("@media (max-width: 360px)", response.text)
        self.assertIn("env(safe-area-inset-bottom)", response.text)
        self.assertIn("@media (prefers-reduced-motion: reduce)", response.text)

    def test_editor_exposes_quality_review_without_an_owner_login_gate(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('<div id="app-wrapper">', page.text)
        self.assertNotIn("owner-login", page.text)
        for control in (
            'id="editor-meta-description"',
            'id="btn-quality-check"',
            'id="btn-quality-approve"',
            'id="btn-quality-request-changes"',
            'id="btn-quality-history"',
            'id="btn-quality-revisions"',
            'id="btn-insert-diagram"',
            'id="editor-internal-link"',
            'id="internal-link-preview"',
            'id="btn-preview-navigation"',
        ):
            self.assertIn(control, page.text)

        script = self.client.get("/static/js/app.js")
        self.assertEqual(script.status_code, 200)
        self.assertNotIn("localStorage.getItem('google_api_token')", script.text)
        self.assertNotIn("X-Google-Token", script.text)

    def test_vault_has_separate_responsive_product_and_affiliate_workspaces(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        for element in (
            'id="tab-monetize"',
            'id="product-form"',
            'id="affiliate-form"',
            'id="products-table-container"',
            'id="affiliates-table-container"',
            'id="ebook-live-preview"',
            'id="vault-product-count"',
            'id="vault-affiliate-count"',
            'href="/ebook/"',
        ):
            self.assertIn(element, page.text)

        script = self.client.get("/static/js/app.js")
        self.assertEqual(script.status_code, 200)
        self.assertIn("trigger_keywords_list", script.text)
        self.assertIn("Products could not be loaded", script.text)
        self.assertIn("Affiliate recommendations could not be loaded", script.text)

        stylesheet = self.client.get("/static/css/style.css")
        self.assertIn(".vault-hero", stylesheet.text)
        self.assertIn(".vault-item", stylesheet.text)


if __name__ == "__main__":
    unittest.main()
