import unittest
from core.image_generator import create_image_prompt_for_topic, generate_featured_image_url, featured_image_html
from core.rewriter import html_to_clean_text
from core.llm_engine import SUPPORTED_PROVIDERS

class EngineTests(unittest.TestCase):
    def test_providers_contain_expected_models(self):
        self.assertIn("gemini", SUPPORTED_PROVIDERS)
        self.assertIn("groq", SUPPORTED_PROVIDERS)
        self.assertIn("cohere", SUPPORTED_PROVIDERS)
        self.assertIn("openai", SUPPORTED_PROVIDERS)
        self.assertIn("anthropic", SUPPORTED_PROVIDERS)
        self.assertIn("llama-3.3-70b-versatile", SUPPORTED_PROVIDERS["groq"]["models"])
        self.assertIn("gemini-2.5-flash", SUPPORTED_PROVIDERS["gemini"]["models"])

    def test_image_prompt_and_url_generation(self):
        prompt = create_image_prompt_for_topic("FastAPI Docker Microservices")
        self.assertIn("FastAPI Docker Microservices", prompt)
        url = generate_featured_image_url(prompt, width=1200, height=630)
        self.assertTrue(url.startswith("https://image.pollinations.ai/prompt/"))
        self.assertIn("width=1200", url)
        self.assertIn("height=630", url)
        html = featured_image_html(url)
        self.assertIn("<img", html)
        self.assertIn("featured-image-wrapper", html)

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
