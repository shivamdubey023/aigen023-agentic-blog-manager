# NextGen Tech Notes · Content Ops

A single-publication content workflow for [NextGen Tech Notes](https://aigen023.blogspot.com/), built with FastAPI, vanilla JavaScript, SQLite, and Vercel serverless functions. The owner selects the topic and AI provider, reviews and edits the saved article, then explicitly confirms any Blogger draft creation or live-post navigation update.

## Current capabilities

- User-selected article generation and optional curated topic ideas. Suggestions are not live trend or keyword metrics.
- Explicitly selected AI provider and model; no automatic provider fallback.
- Local article drafts, Markdown editing, HTML preview, SEO/schema warnings, and optional product/affiliate inserts.
- Optional Pexels or Unsplash search. Results are inserted only after selection and include photographer/provider attribution; image generation is disabled.
- Confirmed Blogger draft creation. The app does not publish drafts automatically.
- Manually triggered previous/next navigation sync for LIVE Blogger posts. It changes live post HTML only after confirmation and reports partial failures.
- Google Search Console and Blogger API integrations when owner OAuth is configured.
- An installable eBook storefront/PWA at `/ebook/`, with a product catalog, search, device-local saved titles, install guidance for Android/iOS, and an offline-cached app shell/catalog.

Automated checks are advisory, not guarantees of article accuracy, search ranking, AdSense approval, or income. The application does not claim to have tested generated code or browsed sources unless that actually occurred.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

Open <http://localhost:8000>. Local article data is stored in `content_ops.db` by default. Set `CONTENT_OPS_DB` to select another SQLite path.

AI generation, image search, and Google integrations remain unavailable until their server-side credentials are configured. Manual editing and local draft storage do not require AI credentials.

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

In Google Cloud, enable the Blogger API and Search Console API, configure the OAuth consent screen, and add the exact `GOOGLE_OAUTH_REDIRECT_URI` value to the OAuth client's authorized redirect URIs. Owner identity is checked server-side. OAuth credentials and provider keys must remain in deployment secrets.

## Important hosting limitation

Vercel function storage is temporary. This app's SQLite database defaults to `/tmp/content_ops.db` on Vercel, so locally saved articles, OAuth state, and settings may not persist across function instances or deployments. Do not rely on it as durable production storage. A durable database/storage service would add an external dependency and may have cost or quota limits; none is added here. Vercel serverless functions also do not create a continuously running queue worker. Generation and synchronization run only after user actions.

The eBook PWA is a storefront/catalog, not a protected eBook reader. It sends checkout to each product's configured seller URL. Offline mode caches the app and catalog only; purchased files are delivered by the seller. A PDF/EPUB reader, protected downloads, purchase verification, and cross-device accounts are not implemented.

Free hosting and provider quotas are subject to platform limits and can change. This repository cannot guarantee zero cost for every hosting account or third-party service.

## Deployment access control

The current Vercel API does not enforce owner authentication on article generation and local article CRUD routes; Google OAuth is used for Google integrations, not as a global app login. Enable deployment access protection before configuring AI provider keys on a publicly reachable deployment. If your Vercel plan does not provide that protection, do not expose provider keys until an app-level owner login is implemented. A complete single-owner authentication gate is not implemented in this increment.

## Verification

Run the unit tests with:

```powershell
python -m unittest discover -s tests -v
```

Mocked tests validate local logic only. They do not prove that a live OAuth login, Blogger draft creation, Search Console report, AI provider request, Vercel deployment, or Pexels/Unsplash request succeeds. Those require credentials and a controlled live test.
