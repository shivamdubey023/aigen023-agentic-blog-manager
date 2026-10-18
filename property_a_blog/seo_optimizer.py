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
    scripts = [f'<script type="application/ld+json">{json.dumps(v,ensure_ascii=False).replace("</","<\\/")}</script>' for v in schema.values()]
    return "\n".join(scripts) + "\n" + body

def affiliate_box(product_name: str, tracking_url: str, disclosure: str) -> str:
    url = html.escape(tracking_url.strip(), quote=True)
    if not url.startswith(("https://","http://")): raise ValueError("Affiliate URL must begin with http:// or https://")
    return ('<aside class="affiliate-recommendation"><p><strong>Affiliate disclosure:</strong> '
      + html.escape(disclosure.strip()) + '</p><p><a href="' + url
      + '" rel="sponsored nofollow noopener" target="_blank">' + html.escape(product_name.strip())
      + '</a></p></aside>')

def render_article(markdown_text: str, title: str, primary_keyword: str="", *, include_toc: bool=True,
                   description: str="", faq: list[dict[str,str]]|None=None, affiliate_html: str="",
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
    if affiliate_html: body += "\n" + affiliate_html
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
