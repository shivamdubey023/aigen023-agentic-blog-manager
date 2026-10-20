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

    def test_render_and_save_use_the_same_server_renderer_and_persist_editor_options(self):
        product_id = db.save_product(
            title="Selected Python guide",
            url="https://products.example.test/python",
            description="A selected guide.",
        )
        markdown = "## Installation\n\nInstall Python using the official installer."
        preview = self.client.post("/api/render", json={
            "markdown_text": markdown,
            "title": "Python setup",
            "include_toc": False,
            "include_product": True,
            "product_id": product_id,
        })
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["product_id"], product_id)
        self.assertFalse(preview.json()["include_toc"])
        self.assertIn("Selected Python guide", preview.json()["rendered_html"])

        saved = self.client.post("/api/articles", json={
            "topic": "Python setup",
            "primary_keyword": "Python",
            "title": "Python setup",
            "markdown_body": markdown,
            "rendered_html": "<script>must not be trusted</script>",
            "include_toc": False,
            "product_id": product_id,
        })
        self.assertEqual(saved.status_code, 200, saved.text)
        article = self.client.get(f"/api/articles/{saved.json()['id']}").json()
        self.assertFalse(article["include_toc"])
        self.assertEqual(article["product_id"], product_id)
        self.assertIn("Selected Python guide", article["rendered_html"])
        self.assertNotIn("<script>", article["rendered_html"])
        self.assertEqual(
            db.list_article_revisions(article["id"])[0]["product_id"],
            product_id,
        )
        self.assertFalse(db.list_article_revisions(article["id"])[0]["include_toc"])

    def test_pollinations_generation_endpoint_handles_valid_and_failed_provider_results(self):
        generated = {
            "image_url": "https://image.pollinations.ai/prompt/example",
            "width": 768,
            "height": 512,
            "provider": "Pollinations AI",
            "hosting": "provider-hosted",
            "warning": "Not mirrored to durable storage.",
        }
        with patch.object(api_module, "generate_pollinations_image", return_value=generated) as generator:
            response = self.client.post("/api/generate-image", json={"topic": "Python API design"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), generated)
        generator.assert_called_once_with("Python API design", width=768, height=512)

        with patch.object(
            api_module,
            "generate_pollinations_image",
            side_effect=RuntimeError("Pollinations rate limit reached."),
        ):
            limited = self.client.post("/api/generate-image", json={"topic": "Python API design"})
        self.assertEqual(limited.status_code, 502)
        self.assertIn("rate limit", limited.json()["detail"])

    def test_blogger_draft_creation_persists_id_and_verifies_returned_post(self):
        saved_article = self.client.post("/api/articles", json={
            "topic": "Python setup",
            "primary_keyword": "Python",
            "title": "Python setup",
            "markdown_body": "## Install\n\nInstall the runtime.",
        })
        self.assertEqual(saved_article.status_code, 200, saved_article.text)
        article_id = saved_article.json()["id"]
        html = db.get_article(article_id)["rendered_html"]
        post = {
            "id": "post-42",
            "url": "https://blog.example.test/python-setup",
            "title": "Python setup",
            "content": html,
            "status": "DRAFT",
            "labels": ["Python", "Python setup"],
        }
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "list_posts", return_value=[]),
            patch.object(api_module, "create_draft", return_value=post) as create,
            patch.object(api_module, "get_post", return_value=post),
        ):
            response = self.client.post("/api/blogger/draft", json={
                "blog_id": "blog-1",
                "article_id": article_id,
                "confirmed": True,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["verified"], response.json())
        create.assert_called_once()
        self.assertEqual(create.call_args.kwargs["labels"], ["Python", "Python setup"])
        saved = db.get_article(article_id)
        self.assertEqual(saved["blogger_post_id"], "post-42")
        self.assertEqual(saved["blogger_post_url"], post["url"])

    def test_publish_requires_confirmation_before_google_access(self):
        with patch.object(api_module, "resolve_current_credentials") as credentials_loader:
            response = self.client.post("/api/blogger/posts/publish", json={
                "blog_id": "blog-1",
                "post_id": "post-1",
                "article_id": 1,
                "confirmed": False,
            })
        self.assertEqual(response.status_code, 400)
        credentials_loader.assert_not_called()

    def test_verify_blogger_post_reads_and_compares_the_linked_post(self):
        saved = self.save_article()
        article_id = saved.json()["id"]
        article = db.get_article(article_id)
        db.save_article(
            topic=article["topic"],
            primary_keyword=article["primary_keyword"],
            title=article["title"],
            markdown_body=article["markdown_body"],
            rendered_html=article["rendered_html"],
            article_id=article_id,
            blogger_post_id="post-verify",
            blogger_blog_id="blog-1",
        )
        post = {
            "id": "post-verify",
            "url": "https://blog.example.test/verified",
            "title": article["title"],
            "content": article["rendered_html"],
            "status": "DRAFT",
            "labels": ["Python testing"],
        }
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "get_post", return_value=post) as retrieve,
        ):
            response = self.client.post("/api/blogger/posts/verify", json={
                "blog_id": "blog-1",
                "post_id": "post-verify",
                "article_id": article_id,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["success"])
        retrieve.assert_called_once()

    def test_confirmed_publish_is_read_back_verified_before_local_status_changes(self):
        saved = self.save_article()
        article_id = saved.json()["id"]
        article = db.get_article(article_id)
        live_post = {
            "id": "post-published",
            "url": "https://blog.example.test/published",
            "title": article["title"],
            "content": article["rendered_html"],
            "status": "LIVE",
        }
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "publish_draft") as publish,
            patch.object(api_module, "get_post", return_value=live_post),
        ):
            response = self.client.post("/api/blogger/posts/publish", json={
                "blog_id": "blog-1",
                "post_id": "post-published",
                "article_id": article_id,
                "confirmed": True,
            })
        self.assertEqual(response.status_code, 409)
        publish.assert_not_called()

        db.save_article(
            topic=article["topic"],
            primary_keyword=article["primary_keyword"],
            title=article["title"],
            markdown_body=article["markdown_body"],
            rendered_html=article["rendered_html"],
            article_id=article_id,
            blogger_post_id="post-published",
            blogger_blog_id="blog-1",
        )
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "publish_draft") as publish,
            patch.object(api_module, "get_post", return_value=live_post),
        ):
            response = self.client.post("/api/blogger/posts/publish", json={
                "blog_id": "blog-1",
                "post_id": "post-published",
                "article_id": article_id,
                "confirmed": True,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["success"])
        self.assertEqual(db.get_article(article_id)["status"], "PUBLISHED")
        self.assertEqual(db.get_article(article_id)["blogger_post_url"], live_post["url"])
        publish.assert_called_once()

    def test_live_post_update_requires_confirmed_local_link_and_verifies_result(self):
        saved = self.save_article()
        article_id = saved.json()["id"]
        article = db.get_article(article_id)
        db.save_article(
            topic=article["topic"],
            primary_keyword=article["primary_keyword"],
            title=article["title"],
            markdown_body=article["markdown_body"],
            rendered_html=article["rendered_html"],
            article_id=article_id,
            blogger_post_id="post-live",
            blogger_blog_id="blog-1",
            blogger_post_url="https://blog.example.test/live",
        )
        live_post = {
            "id": "post-live",
            "url": "https://blog.example.test/live",
            "title": article["title"],
            "content": article["rendered_html"],
            "status": "LIVE",
        }
        with (
            patch.object(api_module, "resolve_current_credentials", return_value=(object(), {})),
            patch.object(api_module, "get_post", side_effect=[live_post, live_post]),
            patch.object(api_module, "update_live_post_content") as update,
        ):
            response = self.client.post("/api/blogger/posts/update", json={
                "blog_id": "blog-1",
                "post_id": "post-live",
                "article_id": article_id,
                "confirmed": True,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["success"])
        update.assert_called_once()

    def test_google_disconnect_removes_only_saved_google_credentials(self):
        db.save_system_credential("google_api_token", '{"token":"test-token"}')
        db.save_system_credential("google_user", '{"email":"owner@example.test"}')
        db.save_system_credential("other_integration", "keep")
        response = self.client.post("/api/oauth/disconnect")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(db.get_system_credential("google_api_token"))
        self.assertIsNone(db.get_system_credential("google_user"))
        self.assertEqual(db.get_system_credential("other_integration"), "keep")

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
                connection.execute("""CREATE TABLE article_revisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    revision_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    meta_description TEXT NOT NULL DEFAULT '',
                    markdown_body TEXT NOT NULL,
                    rendered_html TEXT NOT NULL DEFAULT '',
                    reason TEXT NOT NULL DEFAULT 'saved',
                    created_at TEXT NOT NULL,
                    UNIQUE(article_id, revision_number)
                )""")
                cursor = connection.execute(
                    """INSERT INTO articles
                    (topic,primary_keyword,title,markdown_body,blogger_post_id,blogger_blog_id,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?)""",
                    ("Python","Python","Existing draft","# Existing draft","legacy-post","legacy-blog","2025-01-01","2025-01-01"),
                )
                connection.execute(
                    """INSERT INTO article_revisions
                    (article_id,revision_number,title,markdown_body,created_at)
                    VALUES(?,?,?,?,?)""",
                    (cursor.lastrowid,1,"Existing draft","# Existing revision","2025-01-01"),
                )
                connection.commit()
            finally:
                connection.close()
            with patch.object(db, "DB_PATH", database_path):
                db.init_db()
                saved = db.get_article(1)
                self.assertEqual(saved["markdown_body"], "# Existing draft")
                self.assertEqual(saved["meta_description"], "")
                self.assertEqual(saved["blogger_post_id"], "legacy-post")
                self.assertEqual(saved["blogger_blog_id"], "legacy-blog")
                self.assertEqual(saved["include_toc"], 1)
                db.save_article(
                    topic=saved["topic"],
                    primary_keyword=saved["primary_keyword"],
                    title=saved["title"],
                    markdown_body=saved["markdown_body"],
                    meta_description="An existing draft with preserved content.",
                    article_id=1,
                )
                self.assertEqual(db.get_article(1)["meta_description"], "An existing draft with preserved content.")
                revisions = db.list_article_revisions(1)
                self.assertEqual([revision["revision_number"] for revision in revisions], [2, 1])
                self.assertEqual(revisions[-1]["markdown_body"], "# Existing revision")
                self.assertEqual(revisions[-1]["include_toc"], 1)
                self.assertIsNone(revisions[-1]["product_id"])


if __name__ == "__main__":
    unittest.main()
