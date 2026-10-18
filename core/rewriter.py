"""Blog Rewriter & AdSense Quality Engine."""
from __future__ import annotations
import html
import re
from typing import Any
from core.llm_engine import generate_technical_article

def html_to_clean_text(html_content: str) -> str:
    """Convert HTML content into plain readable text while preserving core structure."""
    if not html_content:
        return ""
    text = re.sub(r"(?is)<script.*?>.*?</script>", "", html_content)
    text = re.sub(r"(?is)<style.*?>.*?</style>", "", text)
    # Convert headings to markdown-like hints
    text = re.sub(r"(?i)<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n\n## \1\n\n", text)
    # Convert list items
    text = re.sub(r"(?i)<li[^>]*>(.*?)</li>", r"\n* \1", text)
    # Convert code blocks
    text = re.sub(r"(?i)<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"\n```\n\1\n```\n", text)
    # Replace paragraphs and breaks
    text = re.sub(r"(?i)<p[^>]*>", "\n\n", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def rewrite_blog_for_adsense(
    *,
    provider: str = "gemini",
    model: str | None = None,
    api_key: str,
    original_title: str,
    original_content_html_or_md: str,
    primary_keyword: str = "",
    extra_instructions: str = "",
) -> str:
    """
    Take an existing blog post and rewrite/expand it to satisfy
    Google AdSense content quality standards and Google Search E-E-A-T.
    """
    clean_original = html_to_clean_text(original_content_html_or_md)
    if len(clean_original) > 12000:
        clean_original = clean_original[:12000] + "\n...(truncated original)"

    enhancement_prompt = f"""You are an expert technical editor upgrading an existing article for NextGen Tech Notes (https://aigen023.blogspot.com/) to qualify for Google AdSense and organic search dominance.

Original Title: {original_title}
Target Keyword: {primary_keyword or original_title}
Editorial Guidance:
- Transform this post from a potentially thin, generic, or outdated article into an exhaustive, hands-on master guide (1,400 to 2,200 words).
- Add modern environment prerequisites (Python/Django/Node versions, OS compatibility).
- Replace vague descriptions with complete, syntax-highlighted, production-ready code examples.
- Include common failure modes with representative terminal traceback snippets, clear troubleshooting steps, and verification procedures.
- Incorporate a dedicated FAQ section with 3-4 high-intent user questions and crisp answers.
- Add official documentation reference recommendations.
- Keep the narrative clear, professional, and authoritative. Do not invent fake claims or real run metrics.

Original Content to Rewrite:
\"\"\"
{clean_original}
\"\"\"

Additional Instructions: {extra_instructions or 'Maximize practical depth, code clarity, and clear step-by-step structure.'}

Output Markdown format only with a single H1 header at the top.
"""

    return generate_technical_article(
        provider=provider,
        model=model,
        api_key=api_key,
        topic=original_title,
        primary_keyword=primary_keyword or original_title,
        notes=enhancement_prompt,
    )
