"""FastAPI application for NextGen Tech Notes — Multi-Model AI Agentic Blog Hub."""
from __future__ import annotations
import json
import hmac
import re
from urllib.parse import urlparse
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Path as ApiPath, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core import database as db
from core.content_quality import content_fingerprint, run_quality_review
from core.env_config import (
    get_google_client_id, get_google_client_secret, get_google_redirect_uri,
    get_groq_key, get_gemini_key, get_cohere_key, get_openai_key, get_anthropic_key,
)
from core.image_renderer import featured_image_html, section_image_html
from core.image_generation import generate_pollinations_image
from core.llm_engine import SUPPORTED_PROVIDERS, generate_technical_article, resolve_key_for_provider
from core.stock_images import IMAGE_PROVIDERS, provider_status as image_provider_status, search_stock_images
from core.rewriter import html_to_clean_text, rewrite_blog_for_adsense
from core.trending_topics import get_random_trending_topic, list_all_trending_topics
from property_a_blog.blogger_client import (
    BLOG_URL, CredentialLoadError, create_draft, finish_oauth, get_credentials, get_post, list_blogs, list_posts,
    oauth_error_hint, search_console_report, start_oauth, update_live_post_navigation,
    publish_draft, update_existing_draft, update_live_post_content, verify_post,
)
from property_a_blog.navigation import navigation_content, order_live_posts
from property_a_blog.seo_optimizer import (
    affiliate_box, content_quality_checks, ebook_card_box, render_article,
    search_description_or_generate,
)

# Initialize database
db.init_db()

app = FastAPI(
    title="NextGen Tech Notes AI Agentic Hub",
    description="Multi-model AI technical blogging automation, AdSense quality enhancer, and product monetization engine.",
    version="2.2.0",
)

# Request Models
class GenerateArticleRequest(BaseModel):
    provider: str = Field(..., description="AI provider selected by the user")
    model: str = Field(..., min_length=1, description="Specific model ID selected by the user")
    topic: str = Field(..., min_length=2, description="Topic or title")
    primary_keyword: Optional[str] = Field(default="", description="Primary SEO keyword")
    audience: Optional[str] = Field(default="Working developer", description="Audience level")
    notes: Optional[str] = Field(default="", description="Technical notes & requirements")

class RewriteArticleRequest(BaseModel):
    provider: str
    model: str = Field(..., min_length=1, description="Specific model ID selected by the user")
    original_title: str
    original_content: str
    primary_keyword: Optional[str] = ""
    extra_instructions: Optional[str] = ""

class ImageGenerateRequest(BaseModel):
    prompt: Optional[str] = Field(default="", max_length=500)
    topic: Optional[str] = Field(default="", max_length=500)
    width: Optional[int] = Field(default=768, ge=1, le=768)
    height: Optional[int] = Field(default=512, ge=1, le=768)

class ImageSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=120)
    provider: str

class RenderArticleRequest(BaseModel):
    markdown_text: str = Field(..., max_length=100000)
    title: str = Field(..., max_length=500)
    meta_description: Optional[str] = Field(default="", max_length=300)
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
    topic: str = Field(..., max_length=500)
    primary_keyword: Optional[str] = Field(default="", max_length=500)
    title: str = Field(..., min_length=1, max_length=500)
    meta_description: Optional[str] = Field(default=None, max_length=300)
    markdown_body: str = Field(..., min_length=1, max_length=100000)
    rendered_html: Optional[str] = Field(default="", max_length=500000)
    schema_json: Optional[Any] = None
    status: Optional[str] = None
    article_id: Optional[int] = None
    include_toc: bool = True
    product_id: Optional[int] = None
    affiliate_id: Optional[int] = None

class QualitySourceRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048)
    excerpt: str = Field(..., min_length=1, max_length=10000)
    title: Optional[str] = Field(default="", max_length=300)

class QualityCheckRequest(BaseModel):
    sources: list[QualitySourceRequest] = Field(default_factory=list, max_length=10)

class ReviewDecisionRequest(BaseModel):
    decision: Literal["APPROVED", "CHANGES_REQUESTED"]
    notes: str = Field(default="", max_length=2000)
    confirmed: bool = False

class CreateBloggerDraftRequest(BaseModel):
    blog_id: str
    article_id: Optional[int] = None
    confirmed: bool = False

class BloggerPostActionRequest(BaseModel):
    blog_id: str = Field(..., min_length=1, max_length=200)
    post_id: str = Field(..., min_length=1, max_length=200)
    article_id: Optional[int] = Field(default=None, ge=1)
    confirmed: bool = False

class SyncNavigationRequest(BaseModel):
    blog_id: str
    confirmed: bool = False

class SaveAffiliateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    keywords: list[str] = Field(..., min_length=1, max_length=30)
    tracking_url: str = Field(..., min_length=1, max_length=2048)
    disclosure: str = Field(..., min_length=1, max_length=500)
    affiliate_id: Optional[int] = None
    description: str = Field(default="", max_length=500)
    image_url: str = Field(default="", max_length=2048)
    category: str = Field(default="", max_length=100)
    price: str = Field(default="", max_length=60)
    cta_text: str = Field(default="View product", max_length=80)
    placement: Literal["inline", "product_card", "article_end"] = "article_end"
    is_active: bool = True

class SaveProductRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=2048)
    price: Optional[str] = Field(default="", max_length=60)
    description: str = Field(..., min_length=1, max_length=500)
    badge: Optional[str] = Field(default="Recommended Guide", max_length=80)
    product_id: Optional[int] = None
    image_url: str = Field(default="", max_length=2048)
    keywords: list[str] = Field(default_factory=list, max_length=30)
    cta_text: str = Field(default="Get the guide", max_length=80)
    is_active: bool = True

class AutopilotRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="User-selected topic to generate")
    primary_keyword: Optional[str] = ""
    provider: str = Field(..., description="AI provider selected by the user")
    model: str = Field(..., min_length=1, description="Model selected by the user")
    include_product: Optional[bool] = False
    product_id: Optional[int] = None
    include_affiliate: Optional[bool] = False
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
    }

@app.get("/api/trending")
def get_trending_topics():
    """Return curated topic ideas without claiming trend or keyword metrics."""
    return {
        "topics": list_all_trending_topics(),
        "random_suggestion": get_random_trending_topic(),
        "source": "Curated suggestions; not validated against Search Console or keyword tools.",
        "metrics_available": False,
    }

@app.post("/api/autopilot")
def run_autopilot(req: AutopilotRequest):
    """
    Generate a locally stored, user-directed article:
    1. Requires a user-selected topic and AI provider.
    2. Generates a technical tutorial for the selected topic.
    3. Adds TOC, structured data, and optional product / affiliate card.
    4. Saves a local draft. Image selection and Blogger draft creation are separate actions.
    """
    topic = (req.topic or "").strip()
    chosen_provider = req.provider.strip()
    if len(topic) < 2:
        raise HTTPException(status_code=400, detail="Choose and confirm an article topic before generating.")
    if not chosen_provider:
        raise HTTPException(status_code=400, detail="Select an AI provider before generating.")
    if chosen_provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {chosen_provider}.")
    model = req.model.strip()
    if model not in SUPPORTED_PROVIDERS[chosen_provider]["models"]:
        raise HTTPException(status_code=400, detail="Choose a supported model for the selected provider.")
    selected_product = None
    if req.include_product:
        if not req.product_id:
            raise HTTPException(status_code=400, detail="Select a relevant product or turn off product insertion.")
        selected_product = db.get_product(req.product_id)
        if not selected_product or not selected_product.get("is_active", 1):
            raise HTTPException(status_code=404, detail="The selected product is no longer available.")
    selected_affiliate = None
    if req.include_affiliate:
        if not req.affiliate_id:
            raise HTTPException(status_code=400, detail="Select a relevant affiliate recommendation or turn it off.")
        selected_affiliate = next(
            (item for item in db.list_affiliates(active_only=True) if item["id"] == req.affiliate_id),
            None,
        )
        if not selected_affiliate:
            raise HTTPException(status_code=404, detail="The selected affiliate recommendation is no longer available.")
    if not resolve_key_for_provider(chosen_provider):
        raise HTTPException(
            status_code=400,
            detail=f"No API key is configured for {chosen_provider}. Configure it or choose another provider.",
        )
    keyword = (req.primary_keyword or "").strip() or topic

    try:
        # 1. Generate the selected topic with the selected provider only.
        draft = generate_technical_article(
            provider=chosen_provider,
            model=model,
            topic=topic,
            primary_keyword=keyword,
            audience="Working developer",
            notes="Explain assumptions and label unverified details. Do not invent test results, citations, or personal experience.",
        )
        title_match = re.search(r"(?m)^#\s+(.+)$", draft)
        title = title_match.group(1).strip() if title_match else topic

        # 2. Product / eBook card (optional)
        product_snippet = ""
        if selected_product:
            product_snippet = ebook_card_box(
                title=selected_product["title"],
                product_url=selected_product["url"],
                price=selected_product.get("price") or "",
                tagline=selected_product.get("description") or "",
                cover_image_url=selected_product.get("image_url") or "",
                cta_text=selected_product.get("cta_text") or "Get the guide",
            )

        # 3. Affiliate snippet (optional)
        affiliate_snippet = ""
        if selected_affiliate:
            affiliate_snippet = affiliate_box(
                product_name=selected_affiliate["product_name"],
                tracking_url=selected_affiliate["tracking_url"],
                disclosure=selected_affiliate["disclosure_snippet"],
                description=selected_affiliate.get("description") or "",
                image_url=selected_affiliate.get("image_url") or "",
                category=selected_affiliate.get("category") or "",
                price=selected_affiliate.get("price") or "",
                cta_text=selected_affiliate.get("cta_text") or "View product",
            )

        # 4. Render HTML with schema and TOC. Images are explicitly chosen later.
        meta_description = search_description_or_generate("", draft, title)
        rendered, schema = render_article(
            draft,
            title,
            keyword,
            description=meta_description,
            include_toc=True,
            ebook_html=product_snippet,
            affiliate_html=affiliate_snippet,
            affiliate_placement=selected_affiliate.get("placement", "article_end") if selected_affiliate else "article_end",
            affiliate_keywords=selected_affiliate.get("trigger_keywords_list", []) if selected_affiliate else [],
        )

        # 5. Save to database.
        article_id = db.save_article(
            topic=topic,
            primary_keyword=keyword,
            title=title,
            markdown_body=draft,
            rendered_html=rendered,
            schema_json=schema,
            status="DRAFT",
            meta_description=meta_description,
            include_toc=True,
            product_id=selected_product["id"] if selected_product else None,
            affiliate_id=selected_affiliate["id"] if selected_affiliate else None,
        )

        warnings = content_quality_checks(title, draft)
        word_count = len(re.findall(r"\b[\w'-]+\b", draft))

        return {
            "success": True,
            "article_id": article_id,
            "title": title,
            "topic": topic,
            "keyword": keyword,
            "word_count": word_count,
            "markdown": draft,
            "rendered_html": rendered,
            "warnings": warnings,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Autopilot generation failed: {str(exc)}")

@app.post("/api/generate")
def generate_article(req: GenerateArticleRequest):
    provider = req.provider.strip()
    if not provider:
        raise HTTPException(status_code=400, detail="Select an AI provider before generating.")
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}.")
    model = req.model.strip()
    if model not in SUPPORTED_PROVIDERS[provider]["models"]:
        raise HTTPException(status_code=400, detail="Choose a supported model for the selected provider.")
    key = resolve_key_for_provider(provider)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"No server-side API key is configured for {provider}. Add it to the deployment environment or choose another provider.",
        )
    try:
        draft = generate_technical_article(
            provider=provider,
            model=model,
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
    provider = req.provider.strip()
    if not provider:
        raise HTTPException(status_code=400, detail="Select an AI provider before rewriting.")
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}.")
    model = req.model.strip()
    if model not in SUPPORTED_PROVIDERS[provider]["models"]:
        raise HTTPException(status_code=400, detail="Choose a supported model for the selected provider.")
    key = resolve_key_for_provider(provider)
    if not key:
        raise HTTPException(
            status_code=400,
            detail=f"No server-side API key is configured for {provider}. Add it to the deployment environment or choose another provider.",
        )
    try:
        rewritten = rewrite_blog_for_adsense(
            provider=provider,
            model=model,
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
    topic = (req.topic or "").strip() or (req.prompt or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Enter the article topic for a relevant featured image.")
    try:
        return generate_pollinations_image(
            topic,
            width=req.width or 768,
            height=req.height or 512,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/api/images/providers")
def get_image_provider_status():
    return {"configured": image_provider_status()}

@app.post("/api/images/search")
def search_images(req: ImageSearchRequest):
    provider = req.provider.strip().lower()
    if provider not in IMAGE_PROVIDERS:
        raise HTTPException(status_code=400, detail="Choose Pexels or Unsplash.")
    try:
        images = search_stock_images(req.query, provider)
        return {"provider": provider, "images": images}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

def _article_labels(topic: str, keyword: str) -> list[str]:
    labels = []
    for value in (keyword, topic):
        for candidate in re.split(r"[,|]", value or ""):
            label = re.sub(r"\s+", " ", candidate).strip()
            if label and label.casefold() not in {existing.casefold() for existing in labels}:
                labels.append(label[:100])
            if len(labels) == 10:
                return labels
    return labels

def _render_article_with_options(
    *,
    markdown_text: str,
    title: str,
    keyword: str,
    description: str,
    include_toc: bool,
    product_id: int | None,
    affiliate_id: int | None,
    featured_image_html: str = "",
    section_image_html: str = "",
    extra_ebook_html: str = "",
) -> tuple[str, dict[str, Any], str]:
    product_snippet = ""
    if product_id is not None:
        product = db.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="The selected product is no longer available.")
        product_snippet = ebook_card_box(
            title=product["title"],
            product_url=product["url"],
            price=product.get("price") or "",
            tagline=product.get("description") or "",
            cover_image_url=product.get("image_url") or "",
            cta_text=product.get("cta_text") or "Get the guide",
        )

    affiliate_snippet = ""
    affiliate_placement = "article_end"
    affiliate_keywords: list[str] = []
    if affiliate_id is not None:
        affiliate = next((item for item in db.list_affiliates() if item["id"] == affiliate_id), None)
        if not affiliate:
            raise HTTPException(status_code=404, detail="The selected affiliate link is no longer available.")
        affiliate_snippet = affiliate_box(
            affiliate["product_name"],
            affiliate["tracking_url"],
            affiliate["disclosure_snippet"],
            description=affiliate.get("description") or "",
            image_url=affiliate.get("image_url") or "",
            category=affiliate.get("category") or "",
            price=affiliate.get("price") or "",
            cta_text=affiliate.get("cta_text") or "View product",
        )
        affiliate_placement = affiliate.get("placement") or "article_end"
        affiliate_keywords = affiliate.get("trigger_keywords_list", [])

    search_description = search_description_or_generate(description, markdown_text, title)
    rendered, schema = render_article(
        markdown_text,
        title,
        keyword or title,
        description=search_description,
        include_toc=include_toc,
        ebook_html=product_snippet or extra_ebook_html,
        affiliate_html=affiliate_snippet,
        affiliate_placement=affiliate_placement,
        affiliate_keywords=affiliate_keywords,
        featured_image_html=featured_image_html,
        section_image_html=section_image_html,
    )
    return rendered, schema, search_description

@app.post("/api/render")
def render_post(req: RenderArticleRequest):
    if req.include_product and req.product_id is None and not req.ebook_url:
        raise HTTPException(status_code=400, detail="Select a saved product before enabling product insertion.")
    try:
        featured = featured_image_html(req.featured_image_url) if req.featured_image_url else ""
        section = (
            section_image_html(req.section_image_url, caption="Architecture & Technical Workflow")
            if req.section_image_url
            else ""
        )
        external_product = ""
        if req.include_product and req.product_id is None and req.ebook_url:
            external_product = ebook_card_box(
                title=req.ebook_title or "Code to Career — The Python Fresher to Job-Ready Developer",
                product_url=req.ebook_url,
                price=req.ebook_price or "View details",
            )
        rendered, schema, description = _render_article_with_options(
            markdown_text=req.markdown_text,
            title=req.title.strip(),
            keyword=req.primary_keyword or req.title,
            description=req.meta_description or "",
            include_toc=req.include_toc if req.include_toc is not None else True,
            product_id=req.product_id if req.include_product else None,
            affiliate_id=req.affiliate_id,
            featured_image_html=featured,
            section_image_html=section,
            extra_ebook_html=external_product,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    warnings = content_quality_checks(req.title, req.markdown_text)

    return {
        "rendered_html": rendered,
        "schema": schema,
        "meta_description": description,
        "include_toc": req.include_toc if req.include_toc is not None else True,
        "product_id": req.product_id if req.include_product else None,
        "affiliate_id": req.affiliate_id,
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

@app.delete("/api/articles/{article_id}")
def delete_single_article(article_id: int, confirmed: bool = False):
    if not confirmed:
        raise HTTPException(status_code=400, detail="Confirm local article deletion explicitly.")
    try:
        deleted = db.delete_article(article_id, require_blogger_post=True)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found.")
    return {"success": True, "message": "Local article copy deleted; the Blogger draft was not changed."}

@app.post("/api/articles")
def save_single_article(req: SaveArticleRequest):
    try:
        existing = db.get_article(req.article_id) if req.article_id is not None else None
        status = req.status or (existing["status"] if existing else "DRAFT")
        keyword = (req.primary_keyword or "").strip() or req.topic.strip()
        description = search_description_or_generate(
            req.meta_description or "",
            req.markdown_body,
            req.title,
        )
        rendered, schema, description = _render_article_with_options(
            markdown_text=req.markdown_body,
            title=req.title.strip(),
            keyword=keyword,
            description=description,
            include_toc=req.include_toc,
            product_id=req.product_id,
            affiliate_id=req.affiliate_id,
        )
        aid = db.save_article(
            topic=req.topic,
            primary_keyword=keyword,
            title=req.title.strip(),
            meta_description=description,
            markdown_body=req.markdown_body,
            rendered_html=rendered,
            schema_json=schema,
            status=status,
            article_id=req.article_id,
            include_toc=req.include_toc,
            product_id=req.product_id,
            affiliate_id=req.affiliate_id,
        )
        return {
            "id": aid,
            "meta_description": description,
            "rendered_html": rendered,
            "schema": schema,
            "message": f"Article #{aid} saved successfully.",
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not save the article.") from exc

@app.post("/api/articles/{article_id}/quality-check")
def run_article_quality_check(
    req: QualityCheckRequest,
    article_id: int = ApiPath(..., ge=1),
):
    article = db.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    if len(article["title"]) > 500 or len(article["markdown_body"]) > 100000:
        raise HTTPException(status_code=413, detail="Article exceeds the quality review size limit.")
    report = run_quality_review(
        title=article["title"],
        markdown=article["markdown_body"],
        meta_description=article["meta_description"],
        primary_keyword=article["primary_keyword"],
        existing_articles=db.list_articles(limit=100),
        source_material=[source.model_dump() for source in req.sources],
        exclude_article_id=article_id,
    )
    try:
        report_id = db.save_quality_report(
            article_id,
            article["title"],
            article["markdown_body"],
            report,
            article["meta_description"],
        )
    except ValueError as exc:
        status_code = 404 if not db.get_article(article_id) else 409
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    stored_report = db.list_quality_reports(article_id, limit=1)[0]
    return {
        "id": report_id,
        "article_id": article_id,
        "content_hash": stored_report["content_hash"],
        "created_at": stored_report["created_at"],
        "report": report,
    }

@app.get("/api/articles/{article_id}/quality-reports")
def get_article_quality_reports(article_id: int = ApiPath(..., ge=1), limit: int = 20):
    article = db.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    current_hash = content_fingerprint(
        article["title"],article["markdown_body"],article["meta_description"]
    )
    reports = db.list_quality_reports(article_id, limit=limit)
    for report in reports:
        report["is_current"] = report["content_hash"] == current_hash
    return reports

@app.get("/api/articles/{article_id}/revisions")
def get_article_revisions(article_id: int = ApiPath(..., ge=1), limit: int = 20):
    if not db.get_article(article_id):
        raise HTTPException(status_code=404, detail="Article not found.")
    return db.list_article_revisions(article_id, limit=limit)

@app.get("/api/articles/{article_id}/review")
def get_article_review(article_id: int = ApiPath(..., ge=1)):
    status = db.get_article_review_status(article_id)
    if status["status"] == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Article not found.")
    return status

@app.post("/api/articles/{article_id}/review")
def record_article_review(
    req: ReviewDecisionRequest,
    article_id: int = ApiPath(..., ge=1),
):
    if not db.get_article(article_id):
        raise HTTPException(status_code=404, detail="Article not found.")
    if req.decision == "APPROVED" and not req.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Explicitly confirm that you reviewed and approve this saved draft.",
        )
    try:
        return db.save_review_decision(article_id, req.decision, req.notes)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

# Products Vault Routes (My Products / Instamojo Books)
def _require_https_url(value: str, label: str, *, optional: bool = False) -> str:
    value = value.strip()
    if optional and not value:
        return value
    try:
        parsed = urlparse(value)
        valid = parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(status_code=422, detail=f"{label} must be a valid HTTPS URL.")
    return value


@app.get("/api/products")
def list_all_products():
    return db.list_products()

@app.get("/api/ebook/catalog")
def get_ebook_catalog():
    """Public, non-sensitive catalog used by the installable eBook storefront."""
    catalog = []
    for product in db.list_products():
        url = str(product.get("url") or "").strip()
        if not product.get("is_active", 1) or not url.startswith("https://"):
            continue
        catalog.append({
            "id": product["id"],
            "title": product["title"],
            "url": url,
            "price": product.get("price") or "",
            "description": product.get("description") or "",
            "badge": product.get("badge") or "Digital guide",
            "image_url": product.get("image_url") or "",
            "cta_text": product.get("cta_text") or "Get the guide",
        })
    return {"products": catalog}

@app.post("/api/products")
def save_single_product(req: SaveProductRequest):
    try:
        _require_https_url(req.url, "Checkout URL")
        _require_https_url(req.image_url, "Product image URL", optional=True)
        pid = db.save_product(
            title=req.title,
            url=req.url,
            price=req.price or "",
            description=req.description or "",
            badge=req.badge or "Recommended Guide",
            product_id=req.product_id,
            image_url=req.image_url,
            keywords=[word.strip() for word in req.keywords if word.strip()],
            cta_text=req.cta_text,
            is_active=req.is_active,
        )
        return {"id": pid, "message": "Product saved successfully."}
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/api/products/{product_id}")
def delete_single_product(product_id: int):
    try:
        deleted = db.delete_product(product_id)
        return {"success": deleted}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

# Affiliate Vault Routes
@app.get("/api/affiliates")
def list_all_affiliates():
    return db.list_affiliates()

@app.post("/api/affiliates")
def create_affiliate(req: SaveAffiliateRequest):
    try:
        _require_https_url(req.tracking_url, "Affiliate URL")
        _require_https_url(req.image_url, "Product image URL", optional=True)
        keywords = list(dict.fromkeys(word.strip() for word in req.keywords if word.strip()))
        if not keywords:
            raise HTTPException(status_code=422, detail="Add at least one relevant keyword.")
        aid = db.save_affiliate(
            req.product_name,
            keywords,
            req.tracking_url,
            req.disclosure,
            req.affiliate_id,
            description=req.description,
            image_url=req.image_url,
            category=req.category,
            price=req.price,
            cta_text=req.cta_text,
            placement=req.placement,
            is_active=req.is_active,
        )
        return {"id": aid, "message": "Affiliate entry saved."}
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/api/affiliates/{affiliate_id}")
def delete_single_affiliate(affiliate_id: int):
    try:
        deleted = db.delete_affiliate(affiliate_id)
        return {"success": deleted}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

# Blogger & OAuth Routes
def resolve_current_credentials(request: Optional[Request] = None) -> tuple[Any, dict[str, Any]]:
    try:
        creds = get_credentials({})
    except CredentialLoadError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    user_str = db.get_system_credential("google_user")
    try:
        user = json.loads(user_str) if user_str else {}
    except (TypeError, json.JSONDecodeError):
        user = {}
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
def get_oauth_url(request: Request, response: Response, redirect_uri: str = ""):
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on the server.",
        )

    target_redirect = get_canonical_callback_url(request, redirect_uri)

    dummy_session: dict[str, Any] = {}
    auth_url = start_oauth(client_id, client_secret, dummy_session, redirect_uri=target_redirect)
    response.set_cookie(
        "aigen_google_oauth_state",
        dummy_session["oauth_state"],
        max_age=900,
        path="/api/oauth",
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "aigen_google_oauth_pkce",
        dummy_session["oauth_verifier"],
        max_age=900,
        path="/api/oauth",
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "url": auth_url,
        "redirect_uri": target_redirect,
        "instruction": f"Add '{target_redirect}' to Authorized redirect URIs in Google Cloud Console.",
    }

def _oauth_result_redirect(request: Request, result: str) -> RedirectResponse:
    response = RedirectResponse(url=f"/?oauth_{result}", status_code=303)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.delete_cookie(
        "aigen_google_oauth_state",
        path="/api/oauth",
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        "aigen_google_oauth_pkce",
        path="/api/oauth",
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
        httponly=True,
        samesite="lax",
    )
    return response

@app.get("/api/oauth/callback")
def handle_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    target_redirect = get_canonical_callback_url(request)
    expected_state = request.cookies.get("aigen_google_oauth_state", "")
    code_verifier = request.cookies.get("aigen_google_oauth_pkce", "")
    if not expected_state or not code_verifier or not state or not hmac.compare_digest(expected_state, state):
        return _oauth_result_redirect(request, "error=connection_failed")
    if error:
        return _oauth_result_redirect(request, "error=consent_not_completed")
    if not client_id or not client_secret:
        return _oauth_result_redirect(request, "error=configuration_missing")
    try:
        dummy_session: dict[str, Any] = {"oauth_state": state, "oauth_verifier": code_verifier}
        creds = finish_oauth(code, state, dummy_session, client_id=client_id, client_secret=client_secret, redirect_uri=target_redirect)
        return _oauth_result_redirect(request, "success=1")
    except Exception:
        return _oauth_result_redirect(request, "error=connection_failed")

@app.get("/api/oauth/status")
def oauth_status(request: Request):
    credential_error = ""
    reconnect_required = False
    try:
        creds, user = resolve_current_credentials(request)
    except HTTPException as exc:
        creds = None
        credential_error = str(exc.detail)
        reconnect_required = "reconnect" in credential_error.casefold() or "incomplete" in credential_error.casefold()
        user_value = db.get_system_credential("google_user")
        try:
            user = json.loads(user_value) if user_value else {}
        except (TypeError, json.JSONDecodeError):
            user = {}
    configured = bool(get_google_client_id() and get_google_client_secret())
    saved_credential = db.get_system_credential("google_api_token")
    if creds and getattr(creds, "valid", False):
        connection_state = "connected"
    elif not configured:
        connection_state = "not_configured"
    elif reconnect_required:
        connection_state = "reconnect_required"
    elif credential_error:
        connection_state = "temporarily_unavailable"
    elif saved_credential:
        connection_state = "reconnect_required"
    else:
        connection_state = "not_connected"
    public_user = {
        key: value
        for key in ("email", "name")
        if isinstance((value := user.get(key)), str)
    }
    return {
        "connected": connection_state == "connected",
        "connection_state": connection_state,
        "user": public_user,
        "configured": configured,
        "configured_redirect_uri": get_canonical_callback_url(request),
        "error": credential_error,
    }

@app.post("/api/oauth/disconnect")
def disconnect_google():
    db.delete_system_credential("google_api_token")
    db.delete_system_credential("google_user")
    return {"success": True, "connection_state": "not_connected"}

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

@app.get("/api/blogger/navigation/preview")
def preview_blogger_navigation(request: Request, blog_id: str):
    if not blog_id.strip():
        raise HTTPException(status_code=400, detail="Select a Blogger blog before previewing navigation.")
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        ordered, skipped = order_live_posts(list_posts(creds, blog_id, limit=500))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not preview Blogger navigation: {exc}") from exc
    sequence = []
    for index, post in enumerate(ordered):
        previous = ordered[index - 1] if index > 0 else None
        following = ordered[index + 1] if index + 1 < len(ordered) else None
        sequence.append({
            "id": str(post.get("id") or ""),
            "title": str(post.get("title") or "Untitled post"),
            "url": str(post.get("url") or ""),
            "previous": {
                "title": str(previous.get("title") or "Untitled post"),
                "url": str(previous.get("url") or ""),
            } if previous else None,
            "next": {
                "title": str(following.get("title") or "Untitled post"),
                "url": str(following.get("url") or ""),
            } if following else None,
        })
    return {"posts": sequence, "skipped_missing_published_date": skipped}

@app.post("/api/blogger/draft")
def upload_blogger_draft(req: CreateBloggerDraftRequest, request: Request):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Review the article and explicitly confirm Blogger draft creation.")
    if not req.article_id:
        raise HTTPException(status_code=400, detail="Save the article locally before creating a Blogger draft.")
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    article = db.get_article(req.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Save the article locally before creating a Blogger draft.")
    if article.get("blogger_post_id"):
        raise HTTPException(status_code=409, detail="This article is already linked to a Blogger post.")
    try:
        # Avoid a second draft after a lost response when the first draft is still discoverable by title.
        existing_posts = list_posts(creds, req.blog_id, limit=500)
        if any(str(post.get("title", "")).strip().casefold() == article["title"].strip().casefold()
               for post in existing_posts):
            raise HTTPException(
                status_code=409,
                detail="A Blogger post with this exact title already exists. Inspect Blogger before retrying.",
            )
        rendered, schema, description = _render_article_with_options(
            markdown_text=article["markdown_body"],
            title=article["title"],
            keyword=article["primary_keyword"],
            description=article.get("meta_description") or "",
            include_toc=bool(article.get("include_toc", 1)),
            product_id=article.get("product_id"),
            affiliate_id=article.get("affiliate_id"),
        )
        labels = _article_labels(article["topic"], article["primary_keyword"])
        created = create_draft(
            creds,
            req.blog_id,
            article["title"],
            rendered,
            labels=labels,
        )
        post_id = created.get("id", "")
        post_url = created.get("url", "")
        if not post_id:
            raise RuntimeError("Blogger did not return a post ID; inspect Blogger before attempting another draft.")
        db.save_article(
            topic=article["topic"],
            primary_keyword=article["primary_keyword"],
            title=article["title"],
            meta_description=description,
            markdown_body=article["markdown_body"],
            rendered_html=rendered,
            schema_json=schema,
            status="DRAFT",
            article_id=req.article_id,
            blogger_post_id=post_id,
            blogger_blog_id=req.blog_id,
            blogger_post_url=post_url,
            include_toc=bool(article.get("include_toc", 1)),
            product_id=article.get("product_id"),
            affiliate_id=article.get("affiliate_id"),
        )
        # Persist the returned ID before verifying so an uncertain read cannot cause a duplicate retry.
        try:
            verified_post = get_post(creds, req.blog_id, post_id)
        except Exception:
            return {
                "success": True,
                "post_id": post_id,
                "url": str(post_url or ""),
                "verified": False,
                "verification": {},
                "message": (
                    "Blogger created the draft and the local post link was saved, "
                    "but read-back verification failed. Inspect Blogger before retrying."
                ),
            }
        verification = verify_post(
            verified_post,
            title=article["title"],
            rendered_html=rendered,
            status="DRAFT",
            labels=labels,
        )
        return {
            "success": True,
            "post_id": post_id,
            "url": str(verified_post.get("url") or post_url),
            "verified": all(verification.values()),
            "verification": verification,
            "message": (
                "Blogger draft created and verified."
                if all(verification.values())
                else "Blogger returned a post, but verification was incomplete. Inspect it before retrying."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Blogger draft creation failed: {str(exc)}") from exc

@app.post("/api/blogger/posts/update")
def update_blogger_post(req: BloggerPostActionRequest, request: Request):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Explicitly confirm the Blogger post update.")
    if not req.article_id:
        raise HTTPException(status_code=400, detail="Select a saved article linked to this Blogger post.")
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    article = db.get_article(req.article_id)
    if not article or article.get("blogger_post_id") != req.post_id or article.get("blogger_blog_id") != req.blog_id:
        raise HTTPException(status_code=409, detail="The saved article is not linked to this Blogger post.")
    try:
        rendered, schema, description = _render_article_with_options(
            markdown_text=article["markdown_body"],
            title=article["title"],
            keyword=article["primary_keyword"],
            description=article.get("meta_description") or "",
            include_toc=bool(article.get("include_toc", 1)),
            product_id=article.get("product_id"),
            affiliate_id=article.get("affiliate_id"),
        )
        existing = get_post(creds, req.blog_id, req.post_id)
        status = str(existing.get("status") or "").upper()
        if status == "DRAFT":
            updated = update_existing_draft(
                creds, req.blog_id, req.post_id, article["title"], rendered,
                explicit_confirmation=True,
            )
        elif status == "LIVE":
            updated = update_live_post_content(
                creds, req.blog_id, req.post_id, article["title"], rendered,
                explicit_confirmation=True,
            )
        else:
            raise HTTPException(status_code=409, detail="Only an existing Blogger draft or live post can be updated.")
        verified = get_post(creds, req.blog_id, req.post_id)
        verification = verify_post(
            verified,
            title=article["title"],
            rendered_html=rendered,
            status=status,
        )
        if all(verification.values()):
            db.save_article(
                topic=article["topic"],
                primary_keyword=article["primary_keyword"],
                title=article["title"],
                meta_description=description,
                markdown_body=article["markdown_body"],
                rendered_html=rendered,
                schema_json=schema,
                status=article["status"],
                article_id=req.article_id,
                blogger_post_id=req.post_id,
                blogger_blog_id=req.blog_id,
                blogger_post_url=str(verified.get("url") or article.get("blogger_post_url") or ""),
                include_toc=bool(article.get("include_toc", 1)),
                product_id=article.get("product_id"),
                affiliate_id=article.get("affiliate_id"),
            )
        return {
            "success": all(verification.values()),
            "status": status,
            "url": str(verified.get("url") or ""),
            "verification": verification,
            "message": "Blogger update verified." if all(verification.values()) else (
                "Blogger returned an update, but verification was incomplete. Inspect the post before retrying."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Blogger update could not be confirmed: {str(exc)}") from exc

@app.post("/api/blogger/posts/verify")
def verify_blogger_post(req: BloggerPostActionRequest, request: Request):
    if not req.article_id:
        raise HTTPException(status_code=400, detail="Select a saved article linked to this Blogger post.")
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    article = db.get_article(req.article_id)
    if not article or article.get("blogger_post_id") != req.post_id or article.get("blogger_blog_id") != req.blog_id:
        raise HTTPException(status_code=409, detail="The saved article is not linked to this Blogger post.")
    try:
        post = get_post(creds, req.blog_id, req.post_id)
        verification = verify_post(
            post,
            title=article["title"],
            rendered_html=article["rendered_html"],
            status="LIVE" if article["status"] == "PUBLISHED" else "DRAFT",
            labels=_article_labels(article["topic"], article["primary_keyword"]),
        )
        return {
            "success": all(verification.values()),
            "url": str(post.get("url") or article.get("blogger_post_url") or ""),
            "verification": verification,
            "message": (
                "Blogger post matches the saved article."
                if all(verification.values())
                else "Blogger post differs from the saved article; inspect the verification details before updating."
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Blogger post verification could not be completed.") from exc

@app.post("/api/blogger/posts/publish")
def publish_blogger_post(req: BloggerPostActionRequest, request: Request):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Explicitly confirm publishing this Blogger draft.")
    if not req.article_id:
        raise HTTPException(status_code=400, detail="Select a saved article linked to this Blogger draft.")
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    article = db.get_article(req.article_id)
    if not article or article.get("blogger_post_id") != req.post_id or article.get("blogger_blog_id") != req.blog_id:
        raise HTTPException(status_code=409, detail="The saved article is not linked to this Blogger draft.")
    try:
        publish_draft(creds, req.blog_id, req.post_id, explicit_confirmation=True)
        published = get_post(creds, req.blog_id, req.post_id)
        verification = verify_post(
            published,
            title=article["title"],
            rendered_html=article["rendered_html"],
            status="LIVE",
        )
        if not all(verification.values()):
            return {
                "success": False,
                "verification": verification,
                "message": "Blogger publish was requested but could not be fully verified. Inspect the post before retrying.",
            }
        db.save_article(
            topic=article["topic"],
            primary_keyword=article["primary_keyword"],
            title=article["title"],
            meta_description=article["meta_description"],
            markdown_body=article["markdown_body"],
            rendered_html=article["rendered_html"],
            schema_json=article.get("schema_json", "{}"),
            status="PUBLISHED",
            article_id=req.article_id,
            blogger_post_id=req.post_id,
            blogger_blog_id=req.blog_id,
            blogger_post_url=str(published.get("url") or article.get("blogger_post_url") or ""),
            include_toc=bool(article.get("include_toc", 1)),
            product_id=article.get("product_id"),
            affiliate_id=article.get("affiliate_id"),
        )
        return {
            "success": True,
            "url": str(published.get("url") or ""),
            "verification": verification,
            "message": "Blogger post is live and verified.",
        }
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=f"Blogger publish could not be confirmed: {str(exc)}") from exc

@app.post("/api/blogger/navigation/sync")
def sync_blogger_navigation(req: SyncNavigationRequest, request: Request):
    if not req.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm that live Blogger post content may be updated with previous/next links.",
        )
    creds, _ = resolve_current_credentials(request)
    if not creds:
        raise HTTPException(status_code=401, detail="Google account not connected.")
    try:
        posts, skipped = order_live_posts(list_posts(creds, req.blog_id, limit=500))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load Blogger posts for navigation: {exc}") from exc

    updated = 0
    unchanged = 0
    errors = []
    for index, post in enumerate(posts):
        previous = posts[index - 1] if index > 0 else None
        next_post = posts[index + 1] if index + 1 < len(posts) else None
        desired = navigation_content(str(post.get("content") or ""), previous, next_post)
        if desired == str(post.get("content") or ""):
            unchanged += 1
            continue
        try:
            update_live_post_navigation(
                creds,
                req.blog_id,
                str(post["id"]),
                desired,
                explicit_confirmation=True,
            )
            updated += 1
        except Exception as exc:
            errors.append({
                "post_id": str(post.get("id") or ""),
                "title": str(post.get("title") or "")[:200],
                "error": str(exc)[:300],
            })
    return {
        "success": not errors,
        "total_live": len(posts) + len(skipped),
        "updated": updated,
        "unchanged": unchanged,
        "skipped_missing_published_date": skipped,
        "errors": errors,
        "message": (
            "Navigation synchronization completed."
            if not errors
            else "Navigation synchronization was partial; inspect the per-post errors before retrying."
        ),
    }

@app.get("/api/search-console")
def get_search_console(request: Request, days: int = 28):
    creds, _ = resolve_current_credentials(request)
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
EBOOK_DIR = STATIC_DIR / "ebook"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/ebook", include_in_schema=False)
def redirect_ebook_app():
    return RedirectResponse("/ebook/", status_code=308)

@app.get("/ebook/", include_in_schema=False)
def serve_ebook_app():
    return FileResponse(EBOOK_DIR / "index.html")

@app.get("/ebook/manifest.webmanifest", include_in_schema=False)
def serve_ebook_manifest():
    return FileResponse(
        EBOOK_DIR / "manifest.webmanifest",
        media_type="application/manifest+json",
    )

@app.get("/ebook/service-worker.js", include_in_schema=False)
def serve_ebook_service_worker():
    return FileResponse(
        EBOOK_DIR / "service-worker.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/ebook/"},
    )

@app.get("/")
def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Agentic Blog Bot API running. Static frontend not found.</h2>")
