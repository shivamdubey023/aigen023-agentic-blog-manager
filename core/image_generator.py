"""Free AI Image Generator with automatic watermark crop removal and multi-image support."""
from __future__ import annotations
import urllib.parse
import re

def create_image_prompt_for_topic(topic: str, context: str = "") -> str:
    """Create a high-impact, modern technical illustration prompt from a topic."""
    clean = re.sub(r"[^\w\s-]", "", topic).strip()
    extra = f", focusing on {context}" if context else ""
    return f"Modern minimalist 3D isometric tech banner about {clean}{extra}, sleek dark theme, vibrant neon accents, futuristic glassmorphism interface, clean cybersecurity and software development aesthetics, ultra-high resolution 8k render, no text, no watermark"

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
    clean_prompt = prompt.strip() + " modern technical blog banner, ultra sharp 8k render, cinematic lighting, no text, no watermark, no logo"
    encoded_prompt = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&private=true&nofeed=true"
    if enhance:
        url += "&enhance=true"
    if seed is not None:
        url += f"&seed={seed}"
    return url

def generate_technical_diagram_url(topic: str, context: str = "Architecture & Workflow Breakdown", seed: int | None = 42) -> str:
    """Generate a secondary in-depth technical architecture diagram image."""
    prompt = f"Technical systems architecture diagram for {topic}, {context}, clean developer schematic, dark mode, vibrant cyan and violet glowing nodes, isometric vector, high detail 8k, no text, no logo"
    encoded_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=600&model=flux&nologo=true&private=true&nofeed=true&enhance=true&seed={seed}"

def featured_image_html(image_url: str, alt_text: str = "Technical tutorial architecture illustration") -> str:
    """
    Return clean HTML markup with CSS bottom crop to guarantee zero watermark.
    The bottom 9% is cropped out where watermarks reside.
    """
    safe_url = urllib.parse.quote(image_url, safe=":/?&=%-._~")
    safe_alt = alt_text.replace('"', '&quot;')
    return f'''<div class="featured-image-wrapper" style="margin: 28px 0; border-radius: 14px; overflow: hidden; max-height: 480px; position: relative; box-shadow: 0 10px 30px rgba(0,0,0,0.18);">
  <img src="{safe_url}" alt="{safe_alt}" style="width: 100%; height: 109%; object-fit: cover; object-position: center top; display: block;" loading="lazy" />
</div>'''

def section_image_html(image_url: str, caption: str = "Architecture Workflow & Data Flow") -> str:
    """Sub-section inline technical diagram with bottom crop watermark removal."""
    safe_url = urllib.parse.quote(image_url, safe=":/?&=%-._~")
    safe_caption = caption.replace('"', '&quot;')
    return f'''<div class="section-image-wrapper" style="margin: 28px 0; border-radius: 12px; overflow: hidden; max-height: 420px; position: relative; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
  <img src="{safe_url}" alt="{safe_caption}" style="width: 100%; height: 109%; object-fit: cover; object-position: center top; display: block;" loading="lazy" />
  <p style="text-align: center; font-size: 13px; color: #64748b; margin-top: 8px;"><em>Figure: {safe_caption}</em></p>
</div>'''

