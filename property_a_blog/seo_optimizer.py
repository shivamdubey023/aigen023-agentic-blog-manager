"""SEO-safe rendering helpers for Blogger HTML payloads."""
from __future__ import annotations
import html, json, re, unicodedata
from datetime import date
from typing import Any
from urllib.parse import urlparse
import bleach
from bleach.css_sanitizer import CSSSanitizer
import markdown
from core.article_visuals import parse_flow_chains, render_flow_diagram

def slugify_heading(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-") or "section"

def parse_headings(markdown_text: str) -> list[dict[str, str]]:
    headings, used = [], {}
    fence_char = ""
    fence_length = 0
    for line in markdown_text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char, fence_length = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length:
                fence_char, fence_length = "", 0
            continue
        if fence_char:
            continue
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
        payload = (
            json.dumps(value, ensure_ascii=False)
            .replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        scripts.append('<script type="application/ld+json">' + payload + '</script>')
    return "\n".join(scripts) + "\n" + body


_ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS) | {
    "h1", "h2", "h3", "h4", "p", "div", "span", "figure", "figcaption",
    "img", "table", "caption", "thead", "tbody", "tfoot", "tr", "th", "td",
    "pre", "code", "hr", "br", "del", "ins", "sup", "sub", "details", "summary",
    "aside", "nav", "svg", "g", "rect", "line", "path", "defs", "marker",
    "title", "desc", "text", "tspan",
}
_ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "rel", "target"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "h1": {"id"}, "h2": {"id"}, "h3": {"id"}, "h4": {"id"},
    "div": {"class", "style"}, "span": {"class", "style"},
    "pre": {"class"}, "code": {"class"},
    "figure": {"class", "role", "aria-labelledby", "style"},
    "figcaption": {"class", "style"},
    "aside": {"class", "style"}, "nav": {"class", "aria-label", "style"},
    "p": {"class", "style"},
    "table": {"class", "style"}, "th": {"scope", "colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
    "svg": {"xmlns", "width", "height", "viewbox", "role", "aria-labelledby", "preserveaspectratio", "style"},
    "g": {"fill", "stroke", "stroke-width"},
    "rect": {"x", "y", "width", "height", "rx", "fill", "stroke", "stroke-width"},
    "line": {"x1", "y1", "x2", "y2", "stroke", "stroke-width", "marker-end"},
    "path": {"d", "fill", "stroke", "stroke-width"},
    "marker": {"id", "markerwidth", "markerheight", "refx", "refy", "orient", "markerunits"},
    "title": {"id"}, "desc": {"id"},
    "text": {"x", "y", "fill", "font-family", "font-size", "font-weight", "text-anchor", "dominant-baseline"},
    "tspan": {"x", "dy"},
}
_CSS_SANITIZER = CSSSanitizer(allowed_css_properties={
    "align-items", "background-color", "border", "border-radius",
    "box-shadow", "color", "display", "flex", "flex-basis", "flex-wrap", "font-family",
    "font-size", "font-weight", "gap", "justify-content", "line-height", "list-style",
    "margin", "max-height", "max-width", "object-fit", "overflow", "overflow-x", "padding",
    "position", "text-align", "text-decoration", "text-transform", "width",
})


def _allow_article_attribute(tag: str, name: str, value: str) -> bool:
    name = name.lower()
    if name not in _ALLOWED_ATTRIBUTES.get(tag, set()):
        return False
    if name == "marker-end":
        return bool(re.fullmatch(r"url\(#arrow-[a-z0-9-]+\)", value))
    if name == "id":
        return bool(re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,80}", value))
    if name == "xmlns":
        return value == "http://www.w3.org/2000/svg"
    if name in {"fill", "stroke"}:
        return bool(re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]{1,20}|none", value))
    if name in {"x", "y", "width", "height", "rx", "x1", "y1", "x2", "y2",
                "stroke-width", "font-size", "colspan", "rowspan", "markerwidth",
                "markerheight", "refx", "refy"}:
        return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", value))
    if name == "d":
        return bool(re.fullmatch(r"[MmLlHhVvCcSsQqTtAaZz0-9., +\-]+", value))
    if name in {"src", "href"}:
        if name == "href" and (value.startswith("#") or (not urlparse(value).scheme and not value.startswith("//"))):
            return True
        parsed = urlparse(value)
        allowed_schemes = {"https"} if tag == "img" else {"http", "https", "mailto"}
        return parsed.scheme in allowed_schemes and (parsed.scheme == "mailto" or bool(parsed.hostname))
    if name == "style":
        return True
    if name in {"aria-labelledby", "aria-label", "role", "scope", "rel", "target",
                "class", "loading", "preserveaspectratio", "orient", "markerunits",
                "font-family", "text-anchor", "dominant-baseline"}:
        return bool(re.fullmatch(r"[a-zA-Z0-9 _-]{1,180}", value))
    return True


def _render_diagram_fences(text: str) -> tuple[str, dict[str, str]]:
    diagrams: dict[str, str] = {}
    pattern = re.compile(
        r'(?ms)^```diagram(?:\s+title="([^"\n]{0,160})")?\s*\n(.*?)^\s*```\s*$'
    )

    def replace(match: re.Match[str]) -> str:
        specification = match.group(2).strip()
        caption = match.group(1) or "Process flow"
        index = len(diagrams)
        token = f"AIGEN023DIAGRAMTOKEN{index}END"
        try:
            diagrams[token] = render_flow_diagram(specification, caption, str(index))
        except ValueError:
            return match.group(0)
        return token

    return pattern.sub(replace, text), diagrams


def _prepare_image_figures(body: str) -> str:
    image_tag = re.compile(r"<img\b[^>]*>", re.I)

    def figure(match: re.Match[str]) -> str:
        image = match.group(1)
        title = re.search(r'\btitle=(["\'])(.*?)\1', image, re.I | re.S)
        caption = html.escape(html.unescape(title.group(2)).strip()) if title else ""
        opening = f'<figure class="article-figure">{image}'
        return f"{opening}<figcaption>{caption}</figcaption></figure>" if caption else f"{opening}</figure>"

    return re.sub(
        r"<p>\s*(<img\b[^>]*>)\s*</p>",
        figure,
        body,
        flags=re.I | re.S,
    )


def _sanitize_article_html(body: str) -> str:
    return bleach.clean(
        body,
        tags=_ALLOWED_TAGS,
        attributes=_allow_article_attribute,
        protocols={"http", "https", "mailto"},
        strip=True,
        strip_comments=True,
        css_sanitizer=_CSS_SANITIZER,
    )


def _wrap_responsive_tables(body: str) -> str:
    return re.sub(
        r"<table\b([^>]*)>(.*?)</table>",
        r'<div class="article-table-scroll" style="max-width:100%;overflow-x:auto;"><table\1>\2</table></div>',
        body,
        flags=re.I | re.S,
    )
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
                   ebook_html: str="", featured_image_html: str="", section_image_html: str="",
                   blog_url: str="https://aigen023.blogspot.com/") -> tuple[str,dict[str,Any]]:
    headings = parse_headings(markdown_text)
    text = markdown_text.strip()
    if include_toc and headings and not re.search(r"(?im)^##\s+table of contents\s*$",text):
        first = re.search(r"(?m)^#\s+.+$",text)
        toc = build_toc(headings)
        text = text[:first.end()] + "\n\n" + toc + text[first.end():] if first else toc + text
    text, diagrams = _render_diagram_fences(text)
    body = markdown.markdown(text, extensions=["extra","sane_lists","tables","fenced_code"])
    body = _add_heading_ids(body, headings)
    body = _prepare_image_figures(body)
    body = _sanitize_article_html(body)
    body = _wrap_responsive_tables(body)
    for token, diagram_html in diagrams.items():
        body = body.replace(token, f"</p>{_sanitize_article_html(diagram_html)}<p>")
    body = re.sub(r"<p>\s*</p>", "", body)
    schema = build_schema(title,description or f"Practical tutorial about {primary_keyword or title}.",primary_keyword,faq,blog_url)
    body = _inject_jsonld(body,schema)
    if featured_image_html:
        # Inject right after opening H1 if possible, else at the beginning
        featured_image_html = _sanitize_article_html(featured_image_html)
        h1_match = re.search(r"(<h1[^>]*>.*?</h1>)", body, flags=re.I|re.S)
        if h1_match:
            body = body[:h1_match.end()] + "\n" + featured_image_html + body[h1_match.end():]
        else:
            body = featured_image_html + "\n" + body
    if section_image_html:
        # Inject architectural diagram before the second H2 section
        section_image_html = _sanitize_article_html(section_image_html)
        h2_matches = list(re.finditer(r"(<h2[^>]*>.*?</h2>)", body, flags=re.I|re.S))
        if len(h2_matches) >= 2:
            target_h2 = h2_matches[1]
            body = body[:target_h2.start()] + "\n" + section_image_html + "\n" + body[target_h2.start():]
        elif h2_matches:
            target_h2 = h2_matches[0]
            body = body[:target_h2.start()] + "\n" + section_image_html + "\n" + body[target_h2.start():]
    if ebook_html:
        body += "\n" + _sanitize_article_html(ebook_html)
    if affiliate_html:
        body += "\n" + _sanitize_article_html(affiliate_html)
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
    if re.search(r"(?m)^#{2,6}\s*$", markdown_text):
        warnings.append("A section heading is empty.")
    if re.search(r"(?m)^#{5,6}\s+", markdown_text):
        warnings.append("Avoid heading levels deeper than H4; reorganize the section under a meaningful H2/H3.")
    heading_levels = [int(heading["level"]) for heading in parse_headings(markdown_text)]
    previous_level = 1
    skipped_heading_level = False
    for level in heading_levels:
        if level > previous_level + 1:
            skipped_heading_level = True
            break
        previous_level = level
    if skipped_heading_level:
        warnings.append("Check heading levels; use H2 for major sections and avoid skipping levels.")
    if re.search(r"(?m)^```diagram\b", markdown_text):
        for match in re.finditer(r'(?ms)^```diagram(?:\s+title="([^"\n]{0,160})")?\s*\n(.*?)^\s*```\s*$', markdown_text):
            try:
                parse_flow_chains(match.group(2).strip())
            except ValueError as exc:
                warnings.append(f"Diagram could not be rendered ({exc}); correct the flow or remove the diagram.")
    for match in re.finditer(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+[^)]*)?\)", markdown_text):
        if not match.group(1).strip():
            warnings.append("An article image is missing descriptive alternative text.")
        if not match.group(2).startswith("https://"):
            warnings.append("An article image uses an unsupported URL; use an HTTPS image source.")
    if re.search(r"\]\(\s*(?:javascript|data):", markdown_text, re.I):
        warnings.append("A link uses an unsafe URL scheme and will be removed from the rendered HTML.")
    anchors = set(re.findall(r"\]\(#([^)]+)\)", markdown_text))
    heading_anchors = {heading["anchor"] for heading in parse_headings(markdown_text)}
    if anchors - heading_anchors:
        warnings.append("A table-of-contents or internal anchor points to a heading that does not exist.")
    return warnings
