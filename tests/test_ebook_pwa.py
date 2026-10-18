import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app


class EbookPwaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_installable_storefront_assets_are_served(self):
        page = self.client.get("/ebook/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('/ebook/manifest.webmanifest', page.text)
        self.assertIn('/static/ebook/app.js', page.text)

        manifest_response = self.client.get("/ebook/manifest.webmanifest")
        self.assertEqual(manifest_response.status_code, 200)
        manifest = json.loads(manifest_response.text)
        self.assertEqual(manifest["start_url"], "/ebook/")
        self.assertEqual(manifest["scope"], "/ebook/")
        self.assertTrue(any(icon["sizes"] == "192x192" for icon in manifest["icons"]))

        worker = self.client.get("/ebook/service-worker.js")
        self.assertEqual(worker.status_code, 200)
        self.assertEqual(worker.headers["service-worker-allowed"], "/ebook/")
        self.assertIn("nextgen-books-v1", worker.text)
        for icon in ("/static/ebook/icon-192.png", "/static/ebook/icon-512.png",
                     "/static/ebook/apple-touch-icon.png"):
            self.assertEqual(self.client.get(icon).status_code, 200)

    @patch("api.index.db.list_products")
    def test_public_catalog_returns_only_safe_product_fields_and_https_links(self, list_products):
        list_products.return_value = [
            {
                "id": 7,
                "title": "Python Guide",
                "url": "https://store.example/python",
                "price": "₹499",
                "description": "A practical guide.",
                "badge": "Featured",
                "private_note": "not for public display",
            },
            {"id": 8, "title": "Unsafe", "url": "javascript:alert(1)"},
        ]

        response = self.client.get("/api/ebook/catalog")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "products": [{
                "id": 7,
                "title": "Python Guide",
                "url": "https://store.example/python",
                "price": "₹499",
                "description": "A practical guide.",
                "badge": "Featured",
            }],
        })


if __name__ == "__main__":
    unittest.main()
