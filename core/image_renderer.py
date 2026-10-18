"""Render externally hosted image markup for article previews and Blogger HTML."""
from __future__ import annotations

from html import escape
from urllib.parse import quote, urlparse


def _safe_image_url(image_url: str) -> str:
    parsed = urlparse(image_url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Article image URLs must use HTTPS.")
    return quote(image_url.strip(), safe=":/?&=%-._~")


def featured_image_html(
    image_url: str,
    alt_text: str = "Technical tutorial illustration",
) -> str:
    safe_url = _safe_image_url(image_url)
    safe_alt = escape(alt_text, quote=True)
    return f'''<div class="featured-image-wrapper" style="margin: 28px 0; border-radius: 14px; overflow: hidden; max-height: 480px; position: relative;">
  <img src="{safe_url}" alt="{safe_alt}" style="width: 100%; object-fit: cover; display: block;" loading="lazy" />
</div>'''


def section_image_html(
    image_url: str,
    caption: str = "Architecture Workflow & Data Flow",
) -> str:
    safe_url = _safe_image_url(image_url)
    safe_caption = escape(caption, quote=True)
    return f'''<div class="section-image-wrapper" style="margin: 28px 0; border-radius: 12px; overflow: hidden; max-height: 420px; position: relative;">
  <img src="{safe_url}" alt="{safe_caption}" style="width: 100%; object-fit: cover; display: block;" loading="lazy" />
  <p style="text-align: center; font-size: 13px;"><em>Figure: {safe_caption}</em></p>
</div>'''
