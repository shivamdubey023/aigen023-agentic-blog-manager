"""Free AI Image Generator using Pollinations.ai (zero API key required)."""
from __future__ import annotations
import urllib.parse
import re

def create_image_prompt_for_topic(topic: str) -> str:
    """Create a high-impact, modern technical illustration prompt from a topic."""
    clean = re.sub(r"[^\w\s-]", "", topic).strip()
    return f"Modern minimalist 3D isometric tech banner about {clean}, sleek dark theme, vibrant neon accents, futuristic glassmorphism interface, clean cybersecurity and software development aesthetics, ultra-high resolution 8k render"

def generate_featured_image_url(
    prompt: str,
    *,
    width: int = 1200,
    height: int = 630,
    seed: int | None = None,
    model: str = "flux",
    enhance: bool = True,
) -> str:
    """
    Generate a direct, free image URL using Pollinations.ai.
    Zero signup, zero API keys, and instantaneous delivery.
    """
    encoded_prompt = urllib.parse.quote(prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true"
    if enhance:
        url += "&enhance=true"
    if seed is not None:
        url += f"&seed={seed}"
    return url

def featured_image_html(image_url: str, alt_text: str = "Featured tutorial illustration") -> str:
    """Return standard responsive HTML markup for a blog post header image."""
    safe_url = urllib.parse.quote(image_url, safe=":/?&=%-._~")
    safe_alt = alt_text.replace('"', '&quot;')
    return f'''<div class="featured-image-wrapper" style="margin: 20px 0; text-align: center; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 30px rgba(0,0,0,0.12);">
  <img src="{safe_url}" alt="{safe_alt}" style="width: 100%; max-height: 520px; object-fit: cover; display: block;" loading="lazy" />
</div>'''
