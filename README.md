# NextGen Tech Notes · Content Ops

A single-publication content workflow for [NextGen Tech Notes](https://aigen023.blogspot.com/), built with FastAPI, vanilla JavaScript, SQLite, and Vercel serverless functions. The owner selects the topic and AI provider, reviews and edits the saved article, then explicitly confirms any Blogger draft creation or live-post navigation update.

## Current capabilities

- User-selected article generation and optional curated topic ideas. Suggestions are not live trend or keyword metrics.
- Explicitly selected AI provider and model; no automatic provider fallback.
- Local article drafts, Markdown editing, HTML preview, SEO/schema warnings, and optional product/affiliate inserts.
- Advisory content quality reports for overlap with saved drafts and reviewer-provided source excerpts, citation formatting, claim-support cues, writing, SEO, and technical examples. Similarity is a human-review signal, not proof of plagiarism.
- Persisted quality reports and article revisions, with content-bound human review decisions. Editing a reviewed draft marks the previous decision stale; approval does not publish an article.
- Optional Pexels or Unsplash search. Results are inserted only after selection and include photographer/provider attribution; image generation is disabled.
- Confirmed Blogger draft creation. The app does not publish drafts automatically.
- Manually triggered previous/next navigation sync for LIVE Blogger posts. It changes live post HTML only after confirmation and reports partial failures.
- Google Search Console and Blogger API integrations when owner OAuth is configured.
- An installable eBook storefront/PWA at `/ebook/`, with a product catalog, search, device-local saved titles, install guidance for Android/iOS, and an offline-cached app shell/catalog.

Automated checks are advisory, not guarantees of article accuracy, search ranking, AdSense approval, or income. The application does not claim to have tested generated code or browsed sources unless that actually occurred.

## Run locally

Requirements: Python 3.11 or newer and Node.js 22 or newer for JavaScript syntax checks. Node.js is not needed to serve the app. PowerShell activation is optional; invoke the virtual environment executable directly:

```powershell
& "C:\Users\anild\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn api.index:app --reload --port 8000
```

If Python is installed elsewhere, use that `python.exe` in the first command. Keep Uvicorn running, then open **<http://localhost:8000>** to preview the web app. FastAPI's endpoint documentation is at <http://localhost:8000/docs>; check application status at <http://localhost:8000/api/health>. The frontend is plain static HTML/CSS/JavaScript and does not need a separate build or frontend server.

To exercise the local application without external credentials, open the editor, enter a title and Markdown, preview it, and save a draft. The article renderer and local database work without AI or Google credentials. AI generation, image search, OAuth, Blogger, and Search Console require their corresponding server-side environment variables. Do not put API keys in frontend files.

Local article data, revisions, quality reports, review decisions, and Google OAuth credentials are stored in `content_ops.db` by default. Set `CONTENT_OPS_DB` to select another SQLite path. The application has no owner-password login; its APIs are accessible to anyone who can reach the deployment unless access is restricted outside the application.

## Content review

In the editor, save the draft and choose **Save draft & run checks**. Optionally provide source excerpts as `URL | excerpt` (one per line). Review the evidence, revise, and recheck after editing. **Approve reviewed draft** records an explicit human decision but does not publish to Blogger. Revision history can restore an earlier saved version into the editor; saving it creates another revision.

The local review compares with up to 100 recent saved articles and reviewer-provided excerpts. It does not fetch or verify citations, independently establish facts, execute code, or assess AI authorship. See [content quality review](docs/CONTENT_QUALITY.md) for details and limitations.

## Test and responsive preview

With the development virtual environment activated, run:

```powershell
python -m compileall -q api app.py core property_a_blog tests
python -m unittest discover -s tests -v
node --check static/js/app.js
node --check static/ebook/app.js
node --check static/ebook/service-worker.js
```

To check the health endpoint from a second PowerShell window while Uvicorn is running:

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

Check responsive layouts in browser developer tools at widths of **320, 360, 390, 768, 1024, and 1440 pixels**. Verify all seven navigation destinations, forms, editor preview, image results, and notifications. Test at least one narrow phone width in portrait and landscape; the mobile navigation should expose Create, Rewrite, Generate, Editor, Images, Vault, and Blogger.

## Vercel configuration

The repository contains `vercel.json` for its FastAPI/static frontend deployment. Set environment variables in the Vercel project settings; do not put real credentials in source code, HTML, JavaScript, `.env.example`, or issue reports.

| Variable | Purpose |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth web client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | Exact deployed callback URL, ending in `/api/oauth/callback` |
| `GROQ_API_KEY` | Optional server-side Groq credential |
| `GEMINI_API_KEY` | Optional server-side Gemini credential |
| `COHERE_API_KEY` | Optional server-side Cohere credential |
| `OPENAI_API_KEY` | Optional server-side OpenAI credential |
| `ANTHROPIC_API_KEY` | Optional server-side Anthropic credential |
| `PEXELS_API_KEY` | Optional server-side Pexels search credential |
| `UNSPLASH_ACCESS_KEY` | Optional server-side Unsplash search credential |
Use only providers/models that are currently available to your account. Provider limits and pricing can change; check each provider's current terms before enabling it. Stock image APIs also have their own attribution rules and quotas. This app does not automatically switch providers or claim any provider is unlimited or permanently free.

In Google Cloud, enable the Blogger API and Search Console API, configure the OAuth consent screen, and add the exact `GOOGLE_OAUTH_REDIRECT_URI` value to the OAuth client's authorized redirect URIs. Google identity is verified during OAuth, but this does not authorize the separate content-management API. OAuth credentials and provider keys must remain in deployment secrets.

## Important hosting limitation

Vercel function storage is temporary. This app's SQLite database defaults to `/tmp/content_ops.db` on Vercel, so articles, quality reports, revisions, review decisions, OAuth state/credentials, and settings may not persist across function instances or deployments. Do not rely on it as durable production storage. A durable database/storage service would add an external dependency and may have cost or quota limits; none is added here. Vercel serverless functions also do not create a continuously running queue worker. Generation and synchronization run only after user actions.

The eBook PWA is a storefront/catalog, not a protected eBook reader. It sends checkout to each product's configured seller URL. Offline mode caches the app and catalog only; purchased files are delivered by the seller. A PDF/EPUB reader, protected downloads, purchase verification, and cross-device accounts are not implemented.

Free hosting and provider quotas are subject to platform limits and can change. This repository cannot guarantee zero cost for every hosting account or third-party service.

## Access-control warning and persistence

The application does not authenticate visitors. If deployed to a public URL, its API exposes saved drafts and review history, permits article/product/affiliate changes and deletions, can trigger configured AI/image-provider usage, and allows Google-connected Blogger/Search Console operations (including explicitly confirmed Blogger draft creation and live navigation updates). Google OAuth connects those integrations; it does **not** authorize access to this application. Keep the deployment private using Vercel Deployment Protection or an equivalent platform-level access control before production use. Do not expose a public deployment with real integration credentials or private content. This repository does not configure or verify platform protection, so this change must not be deployed publicly as-is.

Google OAuth tokens remain server-side and are not sent to browser JavaScript. Vercel's SQLite `/tmp` storage remains ephemeral and cannot reliably preserve articles, revisions, reports, decisions, OAuth state, or integration credentials across function instances and deployments. Select and configure an approved persistent store before depending on production records; no paid or external database has been added.

The automated commands above cover Python compilation, mocked unit tests, and JavaScript syntax. They do not prove that a live OAuth login, Blogger draft creation, Search Console report, AI provider request, Vercel deployment, or Pexels/Unsplash request succeeds. Those require credentials and a controlled live test.

Project architecture and contribution guidance: [Project structure](docs/PROJECT_STRUCTURE.md), [development rules](docs/DEVELOPMENT_RULES.md), and [content quality review](docs/CONTENT_QUALITY.md).
