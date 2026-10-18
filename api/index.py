"""FastAPI application for NextGen Tech Notes — Multi-Model AI Agentic Blog Hub."""
from __future__ import annotations
import html
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import database as db
from core.env_config import (
    get_google_client_id, get_google_client_secret, get_google_redirect_uri,
    get_groq_key, get_gemini_key, get_cohere_key, get_openai_key, get_anthropic_key,
)
from core.image_generator import (
    create_image_prompt_for_topic, featured_image_html, generate_featured_image_url,
    generate_technical_diagram_url, section_image_html,
)
from core.llm_engine import SUPPORTED_PROVIDERS, generate_technical_article, resolve_key_for_provider
from core.rewriter import html_to_clean_text, rewrite_blog_for_adsense
from core.trending_topics import get_random_trending_topic, list_all_trending_topics
from property_a_blog.blogger_client import (
    BLOG_URL, create_draft, finish_oauth, get_credentials, list_blogs, list_posts,
    oauth_error_hint, search_console_report, start_oauth,
)
from property_a_blog.seo_optimizer import (
    affiliate_box, content_quality_checks, ebook_card_box, render_article,
)

# Initialize database
db.init_db()

app = FastAPI(
    title="NextGen Tech Notes AI Agentic Hub",
    description="Multi-model AI technical blogging automation, AdSense quality enhancer, and product monetization engine.",
    version="2.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class GenerateArticleRequest(BaseModel):
    provider: str = Field(default="groq", description="AI provider")
    model: Optional[str] = Field(default=None, description="Specific model ID")
    api_key: Optional[str] = Field(default="", description="Provider API key")
    topic: str = Field(..., min_length=2, description="Topic or title")
    primary_keyword: Optional[str] = Field(default="", description="Primary SEO keyword")
    audience: Optional[str] = Field(default="Working developer", description="Audience level")
    notes: Optional[str] = Field(default="", description="Technical notes & requirements")

class RewriteArticleRequest(BaseModel):
    provider: str = Field(default="groq")
    model: Optional[str] = None
    api_key: Optional[str] = ""
    original_title: str
    original_content: str
    primary_keyword: Optional[str] = ""
    extra_instructions: Optional[str] = ""

class ImageGenerateRequest(BaseModel):
    prompt: Optional[str] = ""
    topic: Optional[str] = ""
    width: Optional[int] = 1200
    height: Optional[int] = 630

class RenderArticleRequest(BaseModel):
    markdown_text: str
    title: str
    primary_keyword: Optional[str] = ""
    include_toc: Optional[bool] = True
    include_product: Optional[bool] = False
    product_id: Optional[int] = None
    ebook_url: Optional[str] = None
    ebook_title: Optional[str] = None
    ebook_price: Optional[str] = None
    affiliate_id: Optional[int] = None
    featured_image_url: Optional[str] = None
    section_image_url: Optional[str] = None

class SaveArticleRequest(BaseModel):
    topic: str
    primary_keyword: Optional[str] = ""
    title: str
    markdown_body: str
    rendered_html: Optional[str] = ""
    schema_json: Optional[Any] = None
    status: Optional[str] = "DRAFT"
    article_id: Optional[int] = None

class CreateBloggerDraftRequest(BaseModel):
    blog_id: str
    title: str
    rendered_html: str
    article_id: Optional[int] = None

class SaveAffiliateRequest(BaseModel):
    product_name: str
    keywords: list[str]
    tracking_url: str
    disclosure: str
    affiliate_id: Optional[int] = None

class SaveProductRequest(BaseModel):
    title: str
    url: str
    price: Optional[str] = ""
    description: Optional[str] = ""
    badge: Optional[str] = "Recommended Guide"
    product_id: Optional[int] = None

class AutopilotRequest(BaseModel):
    topic: Optional[str] = ""
    primary_keyword: Optional[str] = ""
    provider: Optional[str] = "groq"
    model: Optional[str] = None
    include_product: Optional[bool] = False
    product_id: Optional[int] = None
    include_affiliate: Optional[bool] = False
    affiliate_id: Optional[int] = None
    upload_to_blogger: Optional[bool] = False
    blog_id: Optional[str] = ""

# API Routes
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": "NextGen Tech Notes Agentic Blog Hub",
        "timestamp": db.utc_now(),
        "providers": list(SUPPORTED_PROVIDERS.keys()),
    }

@app.get("/api/providers")
def get_providers():
    """Return available AI models and report which have keys in .env."""
    configured = {
        "groq": bool(get_groq_key()),
        "gemini": bool(get_gemini_key()),
        "cohere": bool(get_cohere_key()),
        "openai": bool(get_openai_key()),
        "anthropic": bool(get_anthropic_key()),
    }
    return {
        "providers": SUPPORTED_PROVIDERS,
        "configured": configured,
        "recommended": "groq" if configured["groq"] else ("gemini" if configured["gemini"] else "groq"),
    }

@app.get("/api/trending")
def get_trending_topics():
    """Return trending tech topics designed to rank and produce high AdSense CPC."""
    return {
        "topics": list_all_trending_topics(),
        "random_suggestion": get_random_trending_topic(),
    }

@app.post("/api/autopilot")
def run_autopilot(req: AutopilotRequest, request: Request):
    """
    One-click autonomous agent loop:
    1. Selects or takes a trending topic.
    2. Generates humanized 1,500+ word technical tutorial with real code.
    3. Creates permanent AI featured cover banner and architecture workflow diagram.
    4. Injects TOC, TechArticle & FAQPage Schema, and optional product / affiliate card.
    5. Saves draft to database and optionally creates a Blogger draft!
    """
    chosen_provider = req.provider or "groq"
    if not resolve_key_for_provider(chosen_provider):
        if resolve_key_for_provider("groq"):
            chosen_provider = "groq"
        elif resolve_key_for_provider("gemini"):
            chosen_provider = "gemini"
        elif resolve_key_for_provider("cohere"):
            chosen_provider = "cohere"

    if not req.topic:
        suggested = get_random_trending_topic()
        topic = suggested["topic"]
        keyword = suggested["keyword"]
    else:
        topic = req.topic
        keyword = req.primary_keyword or req.topic

    try:
        # 1. Generate humanized article
        draft = generate_technical_article(
            provider=chosen_provider,
            model=req.model,
            topic=topic,
            primary_keyword=keyword,
            audience="Working developer",
            notes="Write in a natural, opinionated human voice with deep technical rigor. Include clear prerequisites, full reproducible code, a realistic failure traceback with fix, verification checklist, and an FAQ section.",
        )
        title_match = re.search(r"(?m)^#\s+(.+)$", draft)
        title = title_match.group(1).strip() if title_match else topic

        # 2. Generate free featured banner & architecture diagram (no watermarks)
        img_prompt = create_image_prompt_for_topic(topic)
        featured_image_url = generate_featured_image_url(img_prompt)
        diagram_image_url = generate_technical_diagram_url(topic)
        
        img_html = featured_image_html(featured_image_url, alt_text=title)
        diagram_html = section_image_html(diagram_image_url, caption=f"Architecture & Execution Workflow for {topic}")

        # 3. Product / eBook card (optional)
        product_snippet = ""
        if req.include_product:
            prod = None
            if req.product_id:
                prod = db.get_product(req.product_id)
            if not prod:
                prods = db.list_products()
                prod = prods[0] if prods else None
            if prod:
                product_snippet = ebook_card_box(
                    title=prod["title"],
                    product_url=prod["url"],
                    price=prod.get("price") or "Special Offer",
                    tagline=prod.get("description") or "Recommended comprehensive developer resource.",
                )

        # 4. Affiliate snippet (optional)
        affiliate_snippet = ""
        if req.include_affiliate:
            aff = None
            if req.affiliate_id:
                affs = db.list_affiliates()
                aff = next((a for a in affs if a["id"] == req.affiliate_id), None)
            if not aff:
                affs = db.list_affiliates()
                aff = affs[0] if affs else None
            if aff:
                affiliate_snippet = affiliate_box(
                    product_name=aff["product_name"],
                    tracking_url=aff["tracking_url"],
                    disclosure=aff["disclosure_snippet"],
                )

        # 5. Render HTML with schema, TOC, and dual illustrations
        rendered, schema = render_article(
            draft,
            title,
            keyword,
            include_toc=True,
            ebook_html=product_snippet,
            affiliate_html=affiliate_snippet,
            featured_image_html=img_html,
            section_image_html=diagram_html,
        )

        # 6. Save to database
        article_id = db.save_article(
            topic=topic,
            primary_keyword=keyword,
            title=title,
            markdown_body=draft,
            rendered_html=rendered,
            schema_json=schema,
            status="DRAFT",
        )

        blogger_res = None
        if req.upload_to_blogger and req.blog_id:
            creds, _ = resolve_current_credentials(request)
            if creds:
                blogger_res = create_draft(creds, req.blog_id, title, rendered)

        warnings = content_quality_checks(title, draft)
        word_count = len(re.findall(r"\b[\w'-]+\b", draft))

        return {
            "success": True,
            "article_id": article_id,
            "title": title,
            "topic": topic,
            "keyword": keyword,
            "word_count": word_count,
            "image_url": featured_image_url,
            "diagram_url": diagram_image_url,
            "markdown": draft,
            "rendered_html": rendered,
            "warnings": warnings,
            "blogger_result": blogger_res,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Autopilot generation failed: {str(exc)}")

@app.post("/api/generate")
def generate_article(req: GenerateArticleRequest):
    provider = req.provider or "groq"
    key = resolve_key_for_provider(provider, req.api_key)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"Missing API key for {provider}. Add it to your .env file or settings.",
        )
    try:
        draft = generate_technical_article(
            provider=provider,
            model=req.model,
            api_key=key,
            topic=req.topic,
            primary_keyword=req.primary_keyword or req.topic,
            audience=req.audience or "Working developer",
            notes=req.notes or "",
        )
        title_match = re.search(r"(?m)^#\s+(.+)$", draft)
        extracted_title = title_match.group(1).strip() if title_match else req.topic
        warnings = content_quality_checks(extracted_title, draft)
        word_count = len(re.findall(r"\b[\w'-]+\b", draft))

        return {
            "title": extracted_title,
            "markdown": draft,
            "word_count": word_count,
            "warnings": warnings,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(exc)}")

@app.post("/api/rewrite")
def rewrite_article(req: RewriteArticleRequest):
    provider = req.provider or "groq"
    key = resolve_key_for_provider(provider, req.api_key)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"Missing API key for {provider}. Add it to your .env file.",
        )
    try:
        rewritten = rewrite_blog_for_adsense(
            provider=provider,
            model=req.model,
            api_key=key,
            original_title=req.original_title,
            original_content_html_or_md=req.original_content,
            primary_keyword=req.primary_keyword or req.original_title,
            extra_instructions=req.extra_instructions or "",
        )
        title_match = re.search(r"(?m)^#\s+(.+)$", rewritten)
        extracted_title = title_match.group(1).strip() if title_match else req.original_title
        warnings = content_quality_checks(extracted_title, rewritten)
        word_count = len(re.findall(r"\b[\w'-]+\b", rewritten))

        return {
            "title": extracted_title,
            "markdown": rewritten,
            "word_count": word_count,
            "warnings": warnings,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(exc)}")

@app.post("/api/generate-image")
def generate_image(req: ImageGenerateRequest):
    prompt = req.prompt.strip() if req.prompt else ""
    if not prompt and req.topic:
        prompt = create_image_prompt_for_topic(req.topic)
    elif not prompt:
        prompt = "Modern 3D isometric cybersecurity and coding architecture, dark background with vibrant cyan and violet neon"

    url = generate_featured_image_url(prompt, width=req.width or 1200, height=req.height or 630)
    html_snippet = featured_image_html(url, alt_text=prompt[:100])
    return {
        "prompt": prompt,
        "image_url": url,
        "html_snippet": html_snippet,
    }

@app.post("/api/render")
def render_post(req: RenderArticleRequest):
    affiliate_snippet = ""
    if req.affiliate_id:
        affiliates = db.list_affiliates()
        target = next((a for a in affiliates if a["id"] == req.affiliate_id), None)
        if target:
            affiliate_snippet = affiliate_box(
                target["product_name"], target["tracking_url"], target["disclosure_snippet"]
            )

    product_snippet = ""
    if req.include_product:
        if req.product_id:
            p = db.get_product(req.product_id)
            if p:
                product_snippet = ebook_card_box(
                    title=p["title"],
                    product_url=p["url"],
                    price=p.get("price") or "₹499",
                    tagline=p.get("description") or "Recommended comprehensive guide.",
                )
        elif req.ebook_url:
            product_snippet = ebook_card_box(
                title=req.ebook_title or "Code to Career — The Python Fresher to Job-Ready Developer",
                product_url=req.ebook_url or "https://codetocareer52.myinstamojo.com/product/code-to-career",
                price=req.ebook_price or "₹499",
            )

    img_snippet = ""
    if req.featured_image_url:
        img_snippet = featured_image_html(req.featured_image_url)

    diag_snippet = ""
    if req.section_image_url:
        diag_snippet = section_image_html(req.section_image_url, caption="Architecture & Technical Workflow")

    rendered, schema = render_article(
        req.markdown_text,
        req.title,
        req.primary_keyword or req.title,
        include_toc=req.include_toc if req.include_toc is not None else True,
        affiliate_html=affiliate_snippet,
        ebook_html=product_snippet,
        featured_image_html=img_snippet,
        section_image_html=diag_snippet,
    )
    warnings = content_quality_checks(req.title, req.markdown_text)

    return {
        "rendered_html": rendered,
        "schema": schema,
        "warnings": warnings,
        "word_count": len(re.findall(r"\b[\w'-]+\b", req.markdown_text)),
    }

# Content Repository Routes
@app.get("/api/articles")
def list_all_articles():
    return db.list_articles()

@app.get("/api/articles/{article_id}")
def get_single_article(article_id: int):
    article = db.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.post("/api/articles")
def save_single_article(req: SaveArticleRequest):
    try:
        aid = db.save_article(
            topic=req.topic,
            primary_keyword=req.primary_keyword or req.topic,
            title=req.title,
            markdown_body=req.markdown_body,
            rendered_html=req.rendered_html or "",
            schema_json=req.schema_json or {},
            status=req.status or "DRAFT",
            article_id=req.article_id,
        )
        return {"id": aid, "message": f"Article #{aid} saved successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# Products Vault Routes (My Products / Instamojo Books)
@app.get("/api/products")
def list_all_products():
    return db.list_products()

@app.post("/api/products")
def save_single_product(req: SaveProductRequest):
    try:
        pid = db.save_product(
            title=req.title,
            url=req.url,
            price=req.price or "",
            description=req.description or "",
            badge=req.badge or "Recommended Guide",
            product_id=req.product_id,
        )
        return {"id": pid, "message": "Product saved successfully."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/api/products/{product_id}")
def delete_single_product(product_id: int):
    deleted = db.delete_product(product_id)
    return {"success": deleted}

# Affiliate Vault Routes
@app.get("/api/affiliates")
def list_all_affiliates():
    return db.list_affiliates()

@app.post("/api/affiliates")
def create_affiliate(req: SaveAffiliateRequest):
    try:
        aid = db.save_affiliate(
            req.product_name,
            req.keywords,
            req.tracking_url,
            req.disclosure,
            req.affiliate_id,
        )
        return {"id": aid, "message": "Affiliate entry saved."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/api/affiliates/{affiliate_id}")
def delete_single_affiliate(affiliate_id: int):
    deleted = db.delete_affiliate(affiliate_id)
    return {"success": deleted}

# Blogger & OAuth Routes
SESSION_CREDENTIALS: dict[str, Any] = {}

def resolve_current_credentials(request: Optional[Request] = None) -> tuple[Any, dict[str, Any]]:
    token_override = None
    user = {}
    if request:
        token_hdr = request.headers.get("x-google-token")
        if token_hdr and token_hdr.strip() and token_hdr != "null" and token_hdr != "undefined":
            token_override = token_hdr.strip()
        elif "blogger_token" in request.cookies:
            token_override = request.cookies.get("blogger_token")

        user_hdr = request.headers.get("x-google-user")
        if user_hdr and user_hdr.strip() and user_hdr != "null":
            try:
                user = json.loads(user_hdr)
            except Exception:
                pass
        elif "blogger_user" in request.cookies:
            try:
                user = json.loads(request.cookies.get("blogger_user", "{}"))
            except Exception:
                pass

    dummy = {"google_api_token": SESSION_CREDENTIALS.get("token")}
    creds = get_credentials(dummy, token_override=token_override)
    if not user:
        user_str = db.get_system_credential("google_user")
        if user_str:
            try:
                user = json.loads(user_str)
            except Exception:
                user = {}
    if not user:
        user = SESSION_CREDENTIALS.get("user", {})
    return creds, user

def get_canonical_callback_url(request: Request, passed_redirect: str = "") -> str:
    if passed_redirect and passed_redirect.strip():
        return passed_redirect.strip()
    env_redirect = get_google_redirect_uri()
    if env_redirect and "streamlit" not in env_redirect.lower() and "your-app" not in env_redirect.lower():
        return env_redirect
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    if host.startswith("localhost") or host.startswith("127.0.0.1"):
        return f"{proto}://{host}/api/oauth/callback"
    return f"https://{host}/api/oauth/callback"

@app.get("/api/oauth/url")
def get_oauth_url(request: Request, redirect_uri: str = ""):
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Missing Google client_id or client_secret in .env.")

    target_redirect = get_canonical_callback_url(request, redirect_uri)

    dummy_session: dict[str, Any] = {}
    auth_url = start_oauth(client_id, client_secret, dummy_session, redirect_uri=target_redirect)
    SESSION_CREDENTIALS["target_redirect"] = target_redirect
    return {
        "url": auth_url,
        "redirect_uri": target_redirect,
        "instruction": f"Add '{target_redirect}' to Authorized redirect URIs in Google Cloud Console.",
    }

@app.get("/api/oauth/callback")
def handle_oauth_callback(request: Request, code: str = "", state: str = ""):
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    target_redirect = SESSION_CREDENTIALS.get("target_redirect") or get_canonical_callback_url(request)
    if not client_id or not client_secret:
        return HTMLResponse("<h3>Missing Google OAuth credentials in .env.</h3>", status_code=400)
    try:
        dummy_session: dict[str, Any] = {}
        creds = finish_oauth(code, state, dummy_session, client_id=client_id, client_secret=client_secret, redirect_uri=target_redirect)
        token_data = dummy_session.get("google_api_token")
        user_data = dummy_session.get("google_user", {})
        SESSION_CREDENTIALS["creds"] = creds
        SESSION_CREDENTIALS["token"] = token_data
        SESSION_CREDENTIALS["user"] = user_data

        token_json_str = json.dumps(token_data)
        user_json_str = json.dumps(user_data)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Authenticating Blogger...</title>
  <style>
    body {{ background: #0b0f19; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
    .card {{ text-align: center; background: #111827; padding: 36px 48px; border-radius: 16px; border: 1px solid #1f2937; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }}
    .spinner {{ width: 40px; height: 40px; border: 3px solid #374151; border-top-color: #6366f1; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
</head>
<body>
  <div class="card">
    <div class="spinner"></div>
    <h3 style="margin: 0 0 8px 0;">Google Blogger Connected!</h3>
    <p style="color: #94a3b8; font-size: 14px; margin: 0;">Synchronizing serverless session...</p>
  </div>
  <script>
    try {{
      localStorage.setItem('google_api_token', {json.dumps(token_json_str)});
      localStorage.setItem('google_user', {json.dumps(user_json_str)});
    }} catch(e) {{
      console.error(e);
    }}
    setTimeout(function() {{
      window.location.href = '/?oauth_success=1';
    }}, 400);
  </script>
</body>
</html>"""
        response = HTMLResponse(content=html_content, status_code=200)
        response.set_cookie(key="blogger_token", value=token_json_str, max_age=30*86400, httponly=False, samesite="lax")
        response.set_cookie(key="blogger_user", value=user_json_str, max_age=30*86400, httponly=False, samesite="lax")
        return response
    except Exception as exc:
        return HTMLResponse(f"<h3>OAuth error: {html.escape(str(exc))}</h3><p>Redirect URI used: <code>{target_redirect}</code></p>", status_code=500)

@app.get("/api/oauth/status")
def oauth_status(request: Request):
    creds, user = resolve_current_credentials(request)
    return {
        "connected": bool(creds and getattr(creds, "valid", False)),
        "user": user,
        "configured_redirect_uri": get_google_redirect_uri(),
    }

@app.get("/api/blogger/blogs")
def get_blogger_blogs(request: Request):
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected. Please authenticate first.")
    try:
        blogs = list_blogs(creds)
        return {"blogs": blogs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/blogger/posts")
def get_blogger_posts(request: Request, blog_id: str, limit: int = 50):
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        posts = list_posts(creds, blog_id, limit=limit)
        return {"posts": posts}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/blogger/draft")
def upload_blogger_draft(req: CreateBloggerDraftRequest, request: Request):
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        created = create_draft(creds, req.blog_id, req.title, req.rendered_html)
        post_id = created.get("id", "")
        post_url = created.get("url", "")
        if req.article_id:
            art = db.get_article(req.article_id)
            if art:
                db.save_article(
                    topic=art["topic"],
                    primary_keyword=art["primary_keyword"],
                    title=req.title,
                    markdown_body=art["markdown_body"],
                    rendered_html=req.rendered_html,
                    status="DRAFT",
                    article_id=req.article_id,
                    blogger_post_id=post_id,
                    blogger_blog_id=req.blog_id,
                )
        return {"success": True, "post_id": post_id, "url": post_url}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Blogger upload failed: {str(exc)}")

@app.get("/api/search-console")
def get_search_console(days: int = 28):
    creds = SESSION_CREDENTIALS.get("creds")
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        start = date.today() - timedelta(days=days)
        end = date.today() - timedelta(days=3)
        report = search_console_report(creds, start, end, site_url=BLOG_URL, dimensions=["date", "query"], row_limit=500)
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# Serve Frontend static directory
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Agentic Blog Bot API running. Static frontend not found.</h2>")
