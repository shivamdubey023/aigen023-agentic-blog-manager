# Project structure

## Runtime architecture

This is a Vercel-hosted FastAPI application with a plain HTML/CSS/JavaScript frontend. Vercel routes browser requests to static assets or to the Python function; browser code calls same-origin `/api/...` endpoints. Production does not start a persistent web server or require Streamlit.

```text
.
├── .github/
│   ├── copilot-instructions.md (existing; not modified by this work)
│   └── workflows/
│       └── validate.yml
├── api/
│   └── index.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── content_quality.py
│   ├── env_config.py
│   ├── image_generation.py
│   ├── image_renderer.py
│   ├── article_visuals.py
│   ├── llm_engine.py
│   ├── rewriter.py
│   ├── stock_images.py
│   └── trending_topics.py
├── docs/
│   ├── CONTENT_QUALITY.md
│   ├── DEVELOPMENT_RULES.md
│   └── PROJECT_STRUCTURE.md
├── property_a_blog/
│   ├── __init__.py
│   ├── blogger_client.py
│   ├── navigation.py
│   └── seo_optimizer.py
├── static/
│   ├── css/style.css
│   ├── ebook/
│   │   ├── app.css
│   │   ├── app.js
│   │   ├── index.html
│   │   ├── manifest.webmanifest
│   │   ├── service-worker.js
│   │   └── icons (SVG and PNG)
│   ├── index.html
│   └── js/app.js
├── tests/
│   ├── test_api_and_engine.py
│   ├── test_content_ops.py
│   ├── test_content_quality.py
│   ├── test_ebook_pwa.py
│   └── test_web_responsive.py
├── .devcontainer/devcontainer.json
├── .gitignore
├── app.py
├── push_to_vercel.ps1
├── README.md
├── requirements.txt
├── requirements-dev.txt
└── vercel.json
```

## Responsibilities and entry points

| Location | Responsibility |
| --- | --- |
| `vercel.json` | Vercel build targets and URL routing. `api/index.py` is the Python function; `static/**` is deployed as static assets. |
| `api/index.py` | FastAPI application, Pydantic request models, HTTP endpoints, OAuth callback, and static page handlers. Saves and renders article Markdown server-side; validates HTTPS checkout, affiliate, and image URLs; exposes product/affiliate CRUD and separate confirmed Blogger create/update/publish actions. `db.init_db()` runs at import/startup. |
| `static/index.html` | Main content-operations UI and semantic form/navigation markup. |
| `static/css/style.css` | Main responsive visual system and layout. |
| `static/js/app.js` | Main browser UI behavior, same-origin API calls, editing, integration interactions, and manual product/affiliate library forms. It attempts Pollinations image generation when a generated draft is opened in the editor; failures are visible and do not discard the draft. No build step or frontend package manager is configured. |
| `static/ebook/` | Separate installable eBook storefront/PWA, catalog client, manifest, icons, and offline app-shell worker. Only active owned products with HTTPS checkout URLs appear in its catalog. |
| `core/llm_engine.py` | Supported AI providers, model selection, key resolution, and server-side article generation. |
| `core/content_quality.py` | Bounded, deterministic text-overlap, writing, citation-format, claim-cue, SEO, and code-review heuristics. It does not fetch sources, verify facts, execute code, or infer authorship. |
| `core/rewriter.py` | AI-assisted rewriting and HTML-to-text conversion. |
| `property_a_blog/seo_optimizer.py` | Shared Markdown-to-Blogger HTML rendering, headings/TOC, safe HTML sanitization, responsive tables, image figures, SVG diagram insertion, schema, affiliate/product blocks, and editorial warnings. |
| `core/article_visuals.py` | Deterministic self-contained SVG diagrams from user-authored process steps; no external image-generation service. |
| `core/database.py` | SQLite schema and additive migrations, article/revision settings, Blogger IDs/URLs, quality reports, human review decisions, queue records, products, affiliates, and server-side credentials. |
| `core/env_config.py` | Environment and local `.env` configuration accessors. |
| `core/image_generation.py` | Pollinations AI request, response/image validation, and provider-hosted URL warning. It does not mirror images into durable storage. |
| `core/stock_images.py`, `core/image_renderer.py` | Pexels/Unsplash search validation and safe image markup. |
| `property_a_blog/blogger_client.py` | Google OAuth with signed, expiring state/PKCE verification, Blogger API operations, and Search Console report adapter. |
| `property_a_blog/navigation.py` | Ordering live posts and building idempotent previous/next navigation. |
| `tests/` | `unittest` tests for business logic, SQLite, quality-review persistence, API-backed PWA responses, responsive web navigation, and mocked integrations. |
| `app.py` | Legacy Streamlit dashboard. It is not a Vercel entry point; its queue batch controls, CSV export, date-range report UI, and some repost/settings workflows have not all been migrated to the browser application. It has no owner login; keep any separately hosted instance behind platform-level access protection. |
| `.github/workflows/validate.yml` | CI for Python compilation/tests and JavaScript syntax checks. |

## Request and integration flow

1. Vercel matches `/static/(.*)` to the static deployment and `/api/(.*)` to `api/index.py`.
2. Other paths, including `/`, `/ebook/`, and unknown URLs, reach FastAPI through the catch-all route. `/` and the eBook routes have explicit handlers; unknown routes receive FastAPI's 404 response.
3. The browser uses same-origin `/api/...` requests. FastAPI validates request models and calls the existing `core/` or `property_a_blog/` logic.
4. Integrations use server environment variables. The browser must not receive AI provider credentials.

Notable API groups include `/api/health`, `/api/providers`, `/api/trending`, `/api/generate`, `/api/autopilot`, `/api/rewrite`, `/api/render`, `/api/images/*`, `/api/articles`, `/api/articles/{id}/quality-check`, `/api/articles/{id}/quality-reports`, `/api/articles/{id}/revisions`, `/api/articles/{id}/review`, `/api/products`, `/api/affiliates`, `/api/oauth/*`, `/api/blogger/*` (including separately confirmed draft creation, update, and publish actions), and `/api/search-console`. All API routes are unauthenticated at the application layer. A public deployment exposes drafts and mutation/publishing operations; platform-level access protection is required before production use.

The current main UI does not expose the legacy Streamlit queue-management workflow, and there are no queue API routes. AdSense reporting is not implemented. Do not present either as available functionality.

## Configuration and persistence

Canonical environment variables read by the application:

- `CONTENT_OPS_DB`: optional SQLite file path for local development.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`: Google OAuth configuration.
- `GROQ_API_KEY`, `GEMINI_API_KEY`, `COHERE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`: optional server-side AI credentials.
- `PEXELS_API_KEY`, `UNSPLASH_ACCESS_KEY`: optional server-side stock-image credentials.

Local development uses `content_ops.db` in the repository directory unless `CONTENT_OPS_DB` is set. Vercel deployments default to `/tmp/content_ops.db`; this filesystem is ephemeral and instance-local, so the database is **not durable production storage**. Saved OAuth credentials and settings have the same limitation; the short-lived OAuth state is browser-bound and is not stored in SQLite. No persistent database service is configured; do not assume that data survives deployments or another function instance.

The application does not authenticate visitors. Configure Vercel Deployment Protection or equivalent platform access control for the full application before production use; the repository does not configure or verify that protection. OAuth uses a short-lived signed state value and a separate PKCE verifier, each bound to an HttpOnly, SameSite=Lax browser cookie. The signed state is returned through Google's OAuth protocol and contains no credential secret; the PKCE verifier is never sent in the authorization URL. Neither is stored in SQLite. Google OAuth access/refresh tokens are read and refreshed from server-side SQLite and are not returned in OAuth callback HTML, JavaScript storage, or client-readable cookies. SQLite is not encrypted at rest by this application, and on Vercel its `/tmp` location is ephemeral; configure suitable durable protected storage before relying on credentials or editorial records in production.

Articles remain backward-compatible Markdown in the existing article/revision records. Startup adds article/revision option columns and affiliate/owned-product description, image, category/price, CTA, keyword, placement, and active-status columns when absent. The migration is additive and preserves article IDs, Blogger IDs, prior revisions, and Markdown. Owned products and affiliate records have separate vault forms; active state affects future choices and the public owned-product catalog, while linked records cannot be hard-deleted. Affiliate inline placement requires an exact configured keyword in an ordinary paragraph, skips linked/code paragraphs, and is omitted without a match; it is not semantic classification. Selected image metadata (alt text, caption, and provider/photographer attribution) and diagram step specifications remain represented in Markdown. Pollinations image URLs are provider-hosted and not durably mirrored; the UI validates the returned image and warns that availability in Blogger is not guaranteed. The shared renderer is authoritative for preview, saved HTML, and Blogger draft/update content. Blogger title, HTML, labels, status, and returned URL/ID are read back after create/update/publish where available; generated search descriptions are stored locally because the documented Blogger Posts API does not expose a search-description field. Navigation suggestions are read-only and use LIVE Blogger post URLs; selecting and ordering three-to-five related posts for each article is not implemented. Applying navigation changes remains a separate explicitly confirmed sync.

Quality reports include evidence and severity per finding, not an aggregate score. Similarity is a human-review signal, not a plagiarism determination. Citation reachability/relevance, factual accuracy, code execution, and AI authorship are explicitly not verified.

## Development and deployment commands

Install and run locally (PowerShell; activation is not required):

```powershell
& "C:\Users\anild\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn api.index:app --reload --port 8000
```

Run checks:

```powershell
.\.venv\Scripts\python.exe -m compileall -q api app.py core property_a_blog tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check static/js/app.js
node --check static/ebook/app.js
node --check static/ebook/service-worker.js
```

The documented local page URL is `http://localhost:8000`. Vercel deployment is configured by `vercel.json`; connect the repository to a Vercel project, set required environment variables in project settings, and deploy through the Vercel dashboard or the Vercel CLI. Deployment has not been verified from this workspace. See the root `README.md` for current setup notes.

## Where to make changes

- Browser screens and interactions: `static/index.html`, `static/js/app.js`, and `static/css/style.css`.
- API contracts and route wiring: `api/index.py`; update/add route tests in `tests/`.
- Generation, editorial review, rendering, persistence, or integration behavior: the focused module under `core/` or `property_a_blog/`.
- Quality heuristics and boundaries: `core/content_quality.py`; database migrations and report/revision/decision persistence: `core/database.py`.
- Test regressions with isolated SQLite files and mocked external APIs; never use production credentials or publish in routine tests.
- Check `vercel.json` whenever adding an asset directory or changing URL routing.
