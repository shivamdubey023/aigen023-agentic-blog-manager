import unittest
from unittest.mock import patch
from core.image_renderer import featured_image_html
from core.rewriter import html_to_clean_text
from core.llm_engine import SUPPORTED_PROVIDERS, generate_technical_article

class EngineTests(unittest.TestCase):
    def test_providers_contain_expected_models(self):
        self.assertIn("gemini", SUPPORTED_PROVIDERS)
        self.assertIn("groq", SUPPORTED_PROVIDERS)
        self.assertIn("cohere", SUPPORTED_PROVIDERS)
        self.assertIn("openai", SUPPORTED_PROVIDERS)
        self.assertIn("anthropic", SUPPORTED_PROVIDERS)
        for provider in SUPPORTED_PROVIDERS.values():
            self.assertIn(provider["default_model"], provider["models"])

    @patch("core.llm_engine.resolve_key_for_provider", return_value="selected-key")
    @patch("core.llm_engine._call_gemini")
    @patch("core.llm_engine._call_groq", side_effect=RuntimeError("quota exceeded"))
    def test_generation_does_not_switch_provider_after_selected_provider_fails(
        self, groq_call, gemini_call, _resolve_key
    ):
        with self.assertRaisesRegex(RuntimeError, "quota exceeded"):
            generate_technical_article(
                provider="groq",
                model=SUPPORTED_PROVIDERS["groq"]["default_model"],
                topic="Python database migrations",
            )
        groq_call.assert_called_once()
        gemini_call.assert_not_called()

    @patch("core.llm_engine.resolve_key_for_provider", return_value="")
    @patch("core.llm_engine._call_groq")
    def test_generation_with_missing_provider_key_fails_without_api_call(self, groq_call, _resolve_key):
        with self.assertRaisesRegex(ValueError, "No API key is configured for groq"):
            generate_technical_article(provider="groq", topic="Python database migrations")
        groq_call.assert_not_called()

    @patch("core.llm_engine.resolve_key_for_provider", return_value="selected-key")
    @patch("core.llm_engine._call_groq", return_value="# Descriptive title\n\nArticle body.")
    def test_article_generation_prompt_requests_structured_verifiable_markdown(self, groq_call, _resolve_key):
        result = generate_technical_article(
            provider="groq",
            model=SUPPORTED_PROVIDERS["groq"]["default_model"],
            topic="Python database migrations",
        )
        self.assertIn("# Descriptive title", result)
        user_prompt = groq_call.call_args.args[3]
        self.assertIn("meaningful", user_prompt)
        self.assertIn("Markdown tables", user_prompt)
        self.assertIn("do not invent citations", user_prompt)
        self.assertIn("```diagram", user_prompt)

    def test_image_renderer_requires_https_and_escapes_alt_text(self):
        html = featured_image_html(
            "https://images.pexels.com/photos/example.jpg",
            alt_text='Photo of "Python" & APIs',
        )
        self.assertIn("<img", html)
        self.assertIn("featured-image-wrapper", html)
        self.assertIn("&quot;Python&quot; &amp; APIs", html)
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            featured_image_html("http://example.com/photo.jpg")

    def test_html_cleaner_for_rewriter(self):
        dirty_html = "<h1>Old Title</h1><p>This is a paragraph with <a href='https://example.com'>link</a>.</p><pre><code>code block</code></pre>"
        cleaned = html_to_clean_text(dirty_html)
        self.assertIn("Old Title", cleaned)
        self.assertIn("This is a paragraph with link.", cleaned)
        self.assertIn("code block", cleaned)
        self.assertNotIn("<h1>", cleaned)
        self.assertNotIn("<p>", cleaned)

if __name__ == "__main__":
    unittest.main()
