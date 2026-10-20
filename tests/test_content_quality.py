import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import index as api_module
from api.index import app
from core import database as db
from core.content_quality import run_quality_review


class ContentQualityEngineTests(unittest.TestCase):
    def test_exact_and_near_matches_are_review_flags_not_plagiarism_verdicts(self):
        source_text = (
            "A Python virtual environment isolates project dependencies from "
            "the packages installed for other applications on the same machine. "
            "This separation lets each project use tested library versions "
            "without changing tools used by unrelated applications."
        )
        near_text = source_text.replace("the same machine", "a single machine").replace(
            "This separation", "This setup"
        )
        report = run_quality_review(
            title="Python environments",
            markdown=f"{source_text}\n\n{near_text}",
            existing_articles=[{
                "id": 19,
                "title": "Setting up Python",
                "markdown_body": source_text,
            }],
        )

        originality = [item for item in report["findings"] if item["category"] == "originality"]
        self.assertTrue(any(item["title"] == "Exact passage match needs review" for item in originality))
        self.assertTrue(any(item["title"] == "Substantial passage overlap needs review" for item in originality))
        self.assertTrue(all("plagiarism" not in item["title"].casefold() for item in originality))
        self.assertEqual(report["checks"]["automated_plagiarism_verdict"], "never_provided")
        self.assertNotIn("score", report)

    def test_claims_and_generic_writing_are_flagged_without_claiming_fact_verification(self):
        report = run_quality_review(
            title="A specific tutorial",
            markdown=(
                "In today's fast-paced world, it is important to note that this "
                "tool is the only option and supports 100% of deployments in 2025."
            ),
        )
        categories = [item["category"] for item in report["findings"]]
        self.assertIn("writing", categories)
        self.assertIn("fact-check", categories)
        self.assertEqual(report["checks"]["fact_accuracy"], "not_verified")
        claim_finding = next(item for item in report["findings"] if item["category"] == "fact-check")
        self.assertIn("does not verify", claim_finding["evidence"])

    def test_citations_are_reported_without_fetching_or_asserting_relevance(self):
        report = run_quality_review(
            title="Reference review",
            markdown="The example uses a current service. [Reference](http://docs.example.test/guide).",
        )
        citation = report["citations"][0]
        self.assertEqual(citation["format_status"], "http_requires_review")
        self.assertEqual(citation["reachability"], "not_checked")
        self.assertEqual(citation["relevance"], "not_verified")

    def test_code_examples_and_ai_authorship_are_never_claimed_as_checked(self):
        report = run_quality_review(
            title="Example",
            markdown="```python\nprint('hello')\n```\n",
        )
        technical = [item for item in report["findings"] if item["category"] == "technical"]
        self.assertTrue(any(item["title"] == "Code examples were not executed" for item in technical))
        self.assertEqual(report["checks"]["code_execution"], "not_run")
        self.assertEqual(report["checks"]["ai_detection"], "not_run")


class ContentQualityApiTests(unittest.TestCase):
    def setUp(self):
        self.auth_environment_patch = patch.dict(os.environ, {
            "VERCEL": "1",
        }, clear=True)
        self.auth_environment_patch.start()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "quality-test.db"
        self.db_path_patch = patch.object(db, "DB_PATH", self.database_path)
        self.db_path_patch.start()
        db.init_db()
        self.client = TestClient(app)

    def tearDown(self):
        self.db_path_patch.stop()
        self.temp_dir.cleanup()
        self.auth_environment_patch.stop()

    def save_article(self, article_id=None, markdown=None, meta_description=None):
        return self.client.post("/api/articles", json={
            "topic": "Python testing",
            "primary_keyword": "Python testing",
            "title": "Testing Python examples",
            "meta_description": meta_description,
            "markdown_body": markdown or (
                "## Verify the installation\n\n"
                "Run the following command and compare the output with the expected result.\n\n"
                "```bash\npython --version\n```\n\n"
                "The reference is [Python documentation](https://docs.python.org/3/)."
            ),
            "article_id": article_id,
        })

    def test_report_revisions_and_human_approval_are_persisted_and_content_bound(self):
        saved = self.save_article()
        self.assertEqual(saved.status_code, 200)
        article_id = saved.json()["id"]

        unconfirmed = self.client.post(
            f"/api/articles/{article_id}/review",
            json={"decision": "APPROVED", "confirmed": False},
        )
        self.assertEqual(unconfirmed.status_code, 400)

        reviewed = self.client.post(
            f"/api/articles/{article_id}/quality-check",
            json={"sources": [{
                "url": "https://docs.python.org/3/",
                "excerpt": "Python documentation describes how to run a Python interpreter.",
            }]},
        )
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(len(self.client.get(f"/api/articles/{article_id}/quality-reports").json()), 1)

        approved = self.client.post(
            f"/api/articles/{article_id}/review",
            json={"decision": "APPROVED", "confirmed": True, "notes": "Reviewed manually."},
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.json()["decision"], "APPROVED")
        self.assertEqual(self.client.get(f"/api/articles/{article_id}").json()["status"], "DRAFT")
        self.assertEqual(
            self.client.get(f"/api/articles/{article_id}/review").json()["status"],
            "APPROVED",
        )

        updated = self.save_article(article_id, "# Revised article\n\nUpdated draft content.")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/articles/{article_id}/review").json()["status"],
            "NEEDS_REVIEW",
        )
        stale_approval = self.client.post(
            f"/api/articles/{article_id}/review",
            json={"decision": "APPROVED", "confirmed": True},
        )
        self.assertEqual(stale_approval.status_code, 409)
        fresh_report = self.client.post(f"/api/articles/{article_id}/quality-check", json={})
        self.assertEqual(fresh_report.status_code, 200)
        changes_requested = self.client.post(
            f"/api/articles/{article_id}/review",
            json={"decision": "CHANGES_REQUESTED", "notes": "Check current API behavior."},
        )
        self.assertEqual(changes_requested.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/articles/{article_id}/review").json()["status"],
            "CHANGES_REQUESTED",
        )
        self.assertEqual(
            [revision["revision_number"] for revision in self.client.get(
                f"/api/articles/{article_id}/revisions"
            ).json()],
            [2, 1],
        )

    def test_quality_request_bounds_and_unknown_articles(self):
        invalid_id = self.client.post("/api/articles/99999/quality-check", json={})
        self.assertEqual(invalid_id.status_code, 404)

        saved = self.save_article()
        article_id = saved.json()["id"]
        too_many_sources = self.client.post(
            f"/api/articles/{article_id}/quality-check",
            json={"sources": [
                {"url": f"https://source.example/{index}", "excerpt": "source excerpt"}
                for index in range(11)
            ]},
        )
        self.assertEqual(too_many_sources.status_code, 422)

    def test_meta_description_is_rendered_saved_and_invalidates_review(self):
        description = "A practical guide to testing Python examples with reproducible local steps."
        saved = self.save_article(meta_description=description)
        article_id = saved.json()["id"]
        article = self.client.get(f"/api/articles/{article_id}").json()
        self.assertEqual(article["meta_description"], description)
        revision = self.client.get(f"/api/articles/{article_id}/revisions").json()[0]
        self.assertEqual(revision["meta_description"], description)

        rendered = self.client.post("/api/render", json={
            "title": "Testing Python examples",
            "meta_description": description,
            "markdown_text": "## Test\n\nA useful example.",
        })
        self.assertEqual(rendered.status_code, 200)
        self.assertEqual(rendered.json()["schema"]["techArticle"]["description"], description)

        self.client.post(f"/api/articles/{article_id}/quality-check", json={})
        approved = self.client.post(
            f"/api/articles/{article_id}/review",
            json={"decision": "APPROVED", "confirmed": True},
        )
        self.assertEqual(approved.status_code, 200)
        changed = self.save_article(
            article_id,
            markdown=article["markdown_body"],
            meta_description="A revised description for the same Python testing article.",
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/articles/{article_id}/review").json()["status"],
            "NEEDS_REVIEW",
        )

    def test_deployed_api_starts_and_keeps_article_features_without_login_configuration(self):
        client = TestClient(app)
        self.assertEqual(client.get("/api/health").status_code, 200)
        self.assertEqual(client.get("/api/articles").status_code, 200)
        self.assertEqual(client.get("/api/providers").status_code, 200)

        saved = self.save_article()
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(client.get(f"/api/articles/{saved.json()['id']}").status_code, 200)

        self.assertEqual(client.get("/api/auth/status").status_code, 404)
        self.assertEqual(client.post("/api/auth/login", json={"password": "unused"}).status_code, 404)
        self.assertEqual(client.post("/api/auth/logout").status_code, 404)

    def test_google_token_headers_are_ignored_and_oauth_callback_does_not_return_tokens(self):
        token = "server-only-test-google-token"
        client = TestClient(app)
        with patch.object(api_module, "get_credentials", return_value=None) as credentials_loader:
            status = client.get(
                "/api/oauth/status",
                headers={"X-Google-Token": token, "X-Google-User": '{"email":"attacker@example.test"}'},
            )
        self.assertEqual(status.status_code, 200)
        self.assertNotIn(token, status.text)
        credentials_loader.assert_called_once_with({})

        state = "signed-state-for-test"
        verifier = "test-pkce-verifier-that-is-long-enough-for-validation"

        def start_oauth(_client_id, _client_secret, session, **_kwargs):
            session["oauth_state"] = state
            session["oauth_verifier"] = verifier
            return "https://accounts.google.com/o/oauth2/auth"

        def finish_oauth(_code, _state, session, **_kwargs):
            session["google_api_token"] = {"token": token}
            session["google_user"] = {"email": "owner@example.test"}
            return object()

        with (
            patch.object(api_module, "get_google_client_id", return_value="client-id"),
            patch.object(api_module, "get_google_client_secret", return_value="server-secret"),
            patch.object(api_module, "start_oauth", side_effect=start_oauth),
            patch.object(api_module, "finish_oauth", side_effect=finish_oauth),
        ):
            start = client.get("/api/oauth/url")
            self.assertEqual(start.status_code, 200)
            cookie_headers = start.headers.get_list("set-cookie")
            self.assertTrue(any("aigen_google_oauth_state" in header for header in cookie_headers))
            pkce_cookie = next(header for header in cookie_headers if "aigen_google_oauth_pkce" in header)
            self.assertIn("httponly", pkce_cookie.lower())
            self.assertIn("samesite=lax", pkce_cookie.lower())
            self.assertNotIn(verifier, start.text)
            callback = client.get(
                f"/api/oauth/callback?code=private-code&state={state}",
                follow_redirects=False,
            )
        self.assertEqual(callback.status_code, 303)
        self.assertNotIn(token, callback.text)
        self.assertIn("aigen_google_oauth_state", callback.headers.get("set-cookie", ""))
        self.assertIn("max-age=0", callback.headers.get("set-cookie", "").lower())

    def test_oauth_callback_rejects_missing_or_mismatched_browser_state(self):
        client = TestClient(app)
        with patch.object(api_module, "finish_oauth") as finish:
            callback = client.get(
                "/api/oauth/callback?code=private-code&state=state-from-url",
                follow_redirects=False,
            )
        self.assertEqual(callback.status_code, 303)
        self.assertIn("oauth_error=connection_failed", callback.headers["location"])
        finish.assert_not_called()

    def test_oauth_status_identifies_incomplete_saved_credentials(self):
        client = TestClient(app)
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(None, {})),
            patch.object(api_module, "get_google_client_id", return_value="client-id"),
            patch.object(api_module, "get_google_client_secret", return_value="client-secret"),
            patch.object(api_module.db, "get_system_credential", return_value='{"token":"partial"}'),
        ):
            response = client.get("/api/oauth/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["connection_state"], "reconnect_required")
        self.assertFalse(response.json()["connected"])
        self.assertNotIn("partial", response.text)

    def test_navigation_preview_uses_only_live_posts_and_real_neighbor_urls(self):
        posts = [
            {
                "id": "later",
                "title": "Later article",
                "url": "https://blog.example/later",
                "status": "LIVE",
                "published": "2025-02-02T00:00:00Z",
            },
            {
                "id": "draft",
                "title": "Unpublished draft",
                "url": "",
                "status": "DRAFT",
                "published": "2025-02-03T00:00:00Z",
            },
            {
                "id": "earlier",
                "title": "Earlier article",
                "url": "https://blog.example/earlier",
                "status": "LIVE",
                "published": "2025-02-01T00:00:00Z",
            },
        ]
        client = TestClient(app)
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "list_posts", return_value=posts),
        ):
            response = client.get("/api/blogger/navigation/preview?blog_id=blog-id")
        self.assertEqual(response.status_code, 200)
        sequence = response.json()["posts"]
        self.assertEqual([post["id"] for post in sequence], ["earlier", "later"])
        self.assertIsNone(sequence[0]["previous"])
        self.assertEqual(sequence[0]["next"]["url"], "https://blog.example/later")
        self.assertEqual(sequence[1]["previous"]["url"], "https://blog.example/earlier")
        self.assertIsNone(sequence[1]["next"])

    def test_generation_never_attaches_an_unselected_vault_item(self):
        client = TestClient(app)
        payload = {
            "topic": "Python deployment basics",
            "provider": "groq",
            "model": api_module.SUPPORTED_PROVIDERS["groq"]["default_model"],
            "include_affiliate": True,
        }
        with patch.object(api_module, "generate_technical_article") as generate:
            affiliate_response = client.post("/api/autopilot", json=payload)
            self.assertEqual(affiliate_response.status_code, 400)
            self.assertIn("Select a relevant affiliate", affiliate_response.json()["detail"])
            generate.assert_not_called()

        payload.update(include_affiliate=False, include_product=True)
        with patch.object(api_module, "generate_technical_article") as generate:
            product_response = client.post("/api/autopilot", json=payload)
            self.assertEqual(product_response.status_code, 400)
            self.assertIn("Select a relevant product", product_response.json()["detail"])
            generate.assert_not_called()

class ContentQualityMigrationTests(unittest.TestCase):
    def test_existing_article_database_migrates_without_losing_drafts(self):
        with tempfile.TemporaryDirectory() as folder:
            database_path = Path(folder) / "legacy.db"
            connection = sqlite3.connect(database_path)
            try:
                connection.execute("""CREATE TABLE articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL DEFAULT '',
                    primary_keyword TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL DEFAULT '',
                    markdown_body TEXT NOT NULL DEFAULT '',
                    rendered_html TEXT NOT NULL DEFAULT '',
                    schema_json TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'DRAFT',
                    blogger_post_id TEXT NOT NULL DEFAULT '',
                    blogger_blog_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    published_at TEXT NOT NULL DEFAULT ''
                )""")
                connection.execute(
                    """INSERT INTO articles
                    (topic,primary_keyword,title,markdown_body,created_at,updated_at)
                    VALUES(?,?,?,?,?,?)""",
                    ("Python","Python","Existing draft","# Existing draft","2025-01-01","2025-01-01"),
                )
                connection.commit()
            finally:
                connection.close()
            with patch.object(db, "DB_PATH", database_path):
                db.init_db()
                saved = db.get_article(1)
                self.assertEqual(saved["markdown_body"], "# Existing draft")
                self.assertEqual(saved["meta_description"], "")
                db.save_article(
                    topic=saved["topic"],
                    primary_keyword=saved["primary_keyword"],
                    title=saved["title"],
                    markdown_body=saved["markdown_body"],
                    meta_description="An existing draft with preserved content.",
                    article_id=1,
                )
                self.assertEqual(db.get_article(1)["meta_description"], "An existing draft with preserved content.")
                self.assertEqual(db.list_article_revisions(1)[0]["revision_number"], 1)


if __name__ == "__main__":
    unittest.main()
