"""SEO-safe rendering helpers for Blogger HTML payloads."""
from __future__ import annotations
import html, json, re, unicodedata
from datetime import date
from typing import Any
import markdown

def slugify_heading(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-") or "section"

def parse_headings(markdown_text: str) -> list[dict[str, str]]:
    headings, used = [], {}
    for line in markdown_text.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*#*\s*$", line)
        if not match: continue
        title, base = match.group(2).strip(), slugify_heading(match.group(2).strip())
        used[base] = used.get(base, 0) + 1
        headings.append({"title":title,"anchor":base if used[base] == 1 else f"{base}-{used[base]}","level":str(len(match.group(1)))})
    return headings

def build_toc(headings: list[dict[str, str]]) -> str:
    if not headings: return ""
    lines = ["## Table of Contents", ""]
    for h in headings:
        lines.append("  " * max(0, int(h["level"]) - 2) + f'- [{h["title"]}](#{h["anchor"]})')
    return "\n".join(lines) + "\n\n"

def _add_heading_ids(body: str, headings: list[dict[str, str]]) -> str:
    by_title = {}
    for item in headings: by_title.setdefault(item["title"], []).append(item["anchor"])
    def replace(match):
        level, inner = match.group(1), match.group(2)
        plain = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        anchors = by_title.get(plain, [])
        anchor = anchors.pop(0) if anchors else slugify_heading(plain)
        return f'<h{level} id="{html.escape(anchor, quote=True)}">{inner}</h{level}>'
    return re.sub(r"<h([2-4])>(.*?)</h\1>", replace, body, flags=re.I|re.S)

def build_schema(title: str, description: str, keywords: str, faq: list[dict[str, str]]|None=None,
                 blog_url: str="https://aigen023.blogspot.com/") -> dict[str, Any]:
    # Do not invent publication dates or claim the homepage is the article URL.
    # Blogger assigns the actual URL and publication timestamp after a draft is published.
    article = {"@context":"https://schema.org","@type":"TechArticle","headline":title[:110],
      "description":description[:300],"keywords":keywords,
      "publisher":{"@type":"Organization","name":"NextGen Tech Notes"}}
    result = {"techArticle":article}
    valid = [x for x in (faq or []) if x.get("question","").strip() and x.get("answer","").strip()]
    if valid:
        result["faqPage"] = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
          {"@type":"Question","name":x["question"],"acceptedAnswer":{"@type":"Answer","text":x["answer"]}} for x in valid]}
    return result

def _inject_jsonld(body: str, schema: dict[str, Any]) -> str:
    scripts = []
    for value in schema.values():
        payload = json.dumps(value, ensure_ascii=False).replace("</", "<\\\\/")
        scripts.append('<script type="application/ld+json">' + payload + '</script>')
    return "\\n".join(scripts) + "\\n" + body
def affiliate_box(product_name: str, tracking_url: str, disclosure: str) -> str:
    url = html.escape(tracking_url.strip(), quote=True)
    if not url.startswith(("https://","http://")): raise ValueError("Affiliate URL must begin with http:// or https://")
    return ('<aside class="affiliate-recommendation"><p><strong>Affiliate disclosure:</strong> '
      + html.escape(disclosure.strip()) + '</p><p><a href="' + url
      + '" rel="sponsored nofollow noopener" target="_blank">' + html.escape(product_name.strip())
      + '</a></p></aside>')

def ebook_card_box(
    title: str = "Code to Career — The Python Fresher to Job-Ready Developer",
    product_url: str = "https://codetocareer52.myinstamojo.com/product/code-to-career",
    price: str = "₹499",
    tagline: str = "Fast-track from beginner to an interview-ready, high-earning Python developer.",
    cover_image_url: str = "https://storeassets.im-cdn.com/media-manager/demostores/RUANbj2YRQm8vlaCVWuH_hero-banner_1440x650_webp.png",
    bullet_points: list[str] | None = None,
) -> str:
    """Generate a responsive, high-converting eBook CTA banner for Instamojo / Cashfree sales."""
    url = html.escape(product_url.strip(), quote=True)
    t = html.escape(title.strip())
    p = html.escape(price.strip())
    tag = html.escape(tagline.strip())
    bullets = bullet_points or [
        "Hands-on production projects & code repositories",
        "Step-by-step interview preparation & architecture breakdowns",
        "Instant digital download with free lifetime updates",
    ]
    bullet_items = "".join(f'<li style="margin-bottom:6px;">✓ {html.escape(b)}</li>' for b in bullets)

    return f'''<!-- Instamojo eBook CTA Box -->
<div class="instamojo-ebook-card" style="margin: 32px 0; padding: 24px; border: 2px solid #4f46e5; border-radius: 16px; background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #ffffff; box-shadow: 0 10px 30px -5px rgba(79, 70, 229, 0.3); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">
    <div style="flex: 1 1 300px;">
      <span style="display: inline-block; padding: 4px 12px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; background: #fbbf24; color: #000000; border-radius: 20px; margin-bottom: 12px;">★ Recommended Resource</span>
      <h3 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 800; line-height: 1.3; color: #ffffff;">{t}</h3>
      <p style="margin: 0 0 14px 0; font-size: 15px; color: #cbd5e1; line-height: 1.5;">{tag}</p>
      <ul style="list-style: none; padding: 0; margin: 0 0 18px 0; font-size: 14px; color: #94a3b8;">
        {bullet_items}
      </ul>
      <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
        <span style="font-size: 24px; font-weight: 900; color: #34d399;">{p}</span>
        <a href="{url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 12px 28px; background: #4f46e5; color: #ffffff; text-decoration: none; font-weight: 700; font-size: 15px; border-radius: 8px; transition: background 0.2s; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);">
          Get eBook on Instamojo &rarr;
        </a>
      </div>
    </div>
  </div>
</div>
<!-- End eBook CTA Box -->'''

def render_article(markdown_text: str, title: str, primary_keyword: str="", *, include_toc: bool=True,
                   description: str="", faq: list[dict[str,str]]|None=None, affiliate_html: str="",
                   ebook_html: str="", featured_image_html: str="",
                   blog_url: str="https://aigen023.blogspot.com/") -> tuple[str,dict[str,Any]]:
    headings = parse_headings(markdown_text)
    text = markdown_text.strip()
    if include_toc and headings and not re.search(r"(?im)^##\s+table of contents\s*$",text):
        first = re.search(r"(?m)^#\s+.+$",text)
        toc = build_toc(headings)
        text = text[:first.end()] + "\n\n" + toc + text[first.end():] if first else toc + text
    body = markdown.markdown(text, extensions=["extra","sane_lists","tables","fenced_code"])
    body = _add_heading_ids(body, headings)
    schema = build_schema(title,description or f"Practical tutorial about {primary_keyword or title}.",primary_keyword,faq,blog_url)
    body = _inject_jsonld(body,schema)
    if featured_image_html:
        # Inject right after opening H1 if possible, else at the beginning
        h1_match = re.search(r"(<h1[^>]*>.*?</h1>)", body, flags=re.I|re.S)
        if h1_match:
            body = body[:h1_match.end()] + "\n" + featured_image_html + body[h1_match.end():]
        else:
            body = featured_image_html + "\n" + body
    if ebook_html:
        body += "\n" + ebook_html
    if affiliate_html:
        body += "\n" + affiliate_html
    return body,schema

def content_quality_checks(title: str, markdown_text: str) -> list[str]:
    """Review flags, not proof of E-E-A-T or AdSense compliance."""
    warnings=[]
    words=len(re.findall(r"\b[\w'-]+\b",markdown_text))
    if not title.strip(): warnings.append("Add a specific, descriptive title.")
    if words<1200: warnings.append(f"Draft has {words} words; aim for depth appropriate to the topic (1200+ when warranted).")
    if len(re.findall(r"(?m)^\x60\x60\x60",markdown_text))%2: warnings.append("A fenced code block appears unclosed.")
    if not re.search(r"(?im)^#{2,3}\s+",markdown_text): warnings.append("Add useful H2/H3 sections.")
    if not re.search(r"(?i)\b(test|reproduce|verify|expected output|traceback)\b",markdown_text): warnings.append("Add reproducible verification steps or expected output where appropriate.")
    if not re.search(r"(?i)\b(source|documentation|reference|official docs)\b",markdown_text): warnings.append("Add relevant, checked references; never fabricate citations.")
    return warnings
