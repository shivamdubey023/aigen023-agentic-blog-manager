"""FastAPI application for NextGen Tech Notes — Multi-Model AI Agentic Blog Hub."""
from __future__ import annotations
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
from core.image_generator import create_image_prompt_for_topic, featured_image_html, generate_featured_image_url
from core.llm_engine import SUPPORTED_PROVIDERS, generate_technical_article
from core.rewriter import html_to_clean_text, rewrite_blog_for_adsense
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
    description="Multi-model AI technical blogging, SEO optimization, and monetization platform.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to resolve API keys from request or environment
def resolve_api_key(provider: str, passed_key: str | None = None) -> str:
    if passed_key and passed_key.strip():
        return passed_key.strip()
    env_keys = {
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "groq": ["GROQ_API_KEY"],
        "cohere": ["COHERE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
    }
    for env_var in env_keys.get(provider.lower(), []):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val
    return ""

# Request Models
class GenerateArticleRequest(BaseModel):
    provider: str = Field(default="gemini", description="AI provider")
    model: Optional[str] = Field(default=None, description="Specific model ID")
    api_key: Optional[str] = Field(default="", description="Provider API key")
    topic: str = Field(..., min_length=2, description="Topic or title")
    primary_keyword: Optional[str] = Field(default="", description="Primary SEO keyword")
    audience: Optional[str] = Field(default="Working developer", description="Audience level")
    notes: Optional[str] = Field(default="", description="Technical notes & requirements")

class RewriteArticleRequest(BaseModel):
    provider: str = Field(default="gemini")
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
    include_ebook: Optional[bool] = False
    ebook_url: Optional[str] = "https://codetocareer52.myinstamojo.com/product/code-to-career"
    ebook_title: Optional[str] = "Code to Career — The Python Fresher to Job-Ready Developer"
    ebook_price: Optional[str] = "₹499"
    affiliate_id: Optional[int] = None
    featured_image_url: Optional[str] = None

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
    """Return available AI models and their configuration."""
    configured = {}
    for prov in SUPPORTED_PROVIDERS:
        key = resolve_api_key(prov)
        configured[prov] = bool(key)
    return {
        "providers": SUPPORTED_PROVIDERS,
        "configured": configured,
    }

@app.post("/api/generate")
def generate_article(req: GenerateArticleRequest):
    key = resolve_api_key(req.provider, req.api_key)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"Missing API key for {req.provider}. Provide in Settings or request.",
        )
    try:
        draft = generate_technical_article(
            provider=req.provider,
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
    key = resolve_api_key(req.provider, req.api_key)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"Missing API key for {req.provider}.",
        )
    try:
        rewritten = rewrite_blog_for_adsense(
            provider=req.provider,
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

    ebook_snippet = ""
    if req.include_ebook:
        ebook_snippet = ebook_card_box(
            title=req.ebook_title or "Code to Career — The Python Fresher to Job-Ready Developer",
            product_url=req.ebook_url or "https://codetocareer52.myinstamojo.com/product/code-to-career",
            price=req.ebook_price or "₹499",
        )

    img_snippet = ""
    if req.featured_image_url:
        img_snippet = featured_image_html(req.featured_image_url)

    rendered, schema = render_article(
        req.markdown_text,
        req.title,
        req.primary_keyword or req.title,
        include_toc=req.include_toc if req.include_toc is not None else True,
        affiliate_html=affiliate_snippet,
        ebook_html=ebook_snippet,
        featured_image_html=img_snippet,
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

# Blogger & OAuth Routes
SESSION_CREDENTIALS: dict[str, Any] = {}

@app.get("/api/oauth/url")
def get_oauth_url():
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in server environment.")
    dummy_session: dict[str, Any] = {}
    auth_url = start_oauth(client_id, client_secret, dummy_session)
    return {"url": auth_url}

@app.get("/api/oauth/callback")
def handle_oauth_callback(code: str = "", state: str = ""):
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return HTMLResponse("<h3>Missing Google OAuth credentials.</h3>", status_code=400)
    try:
        dummy_session: dict[str, Any] = {}
        creds = finish_oauth(code, state, dummy_session, client_id=client_id, client_secret=client_secret)
        SESSION_CREDENTIALS["creds"] = creds
        SESSION_CREDENTIALS["user"] = dummy_session.get("google_user", {})
        # Redirect back to app
        return RedirectResponse(url="/?oauth_success=1")
    except Exception as exc:
        return HTMLResponse(f"<h3>OAuth error: {html.escape(str(exc))}</h3>", status_code=500)

@app.get("/api/oauth/status")
def oauth_status():
    creds = SESSION_CREDENTIALS.get("creds")
    user = SESSION_CREDENTIALS.get("user", {})
    return {
        "connected": bool(creds and getattr(creds, "valid", False)),
        "user": user,
    }

@app.get("/api/blogger/blogs")
def get_blogger_blogs():
    creds = SESSION_CREDENTIALS.get("creds")
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected. Please authenticate first.")
    try:
        blogs = list_blogs(creds)
        return {"blogs": blogs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/blogger/posts")
def get_blogger_posts(blog_id: str, limit: int = 50):
    creds = SESSION_CREDENTIALS.get("creds")
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        posts = list_posts(creds, blog_id, limit=limit)
        return {"posts": posts}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/blogger/draft")
def upload_blogger_draft(req: CreateBloggerDraftRequest):
    creds = SESSION_CREDENTIALS.get("creds")
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
