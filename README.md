# NextGen Tech Notes · Content Ops

A single-publication content workflow for [NextGen Tech Notes](https://aigen023.blogspot.com/), built with FastAPI, vanilla JavaScript, SQLite, and Vercel serverless functions. The owner selects the topic and AI provider, reviews and edits the saved article, then explicitly confirms any Blogger draft creation or live-post navigation update.

## Current capabilities

- User-selected article generation and optional curated topic ideas. Suggestions are not live trend or keyword metrics.
- Explicitly selected AI provider and model; no automatic provider fallback.
- Local article drafts, Markdown editing, HTML preview, SEO/schema warnings, and optional product/affiliate inserts.
- Monetization cards are added only when a specific saved product or affiliate link is selected; generation does not fall back to an unrelated first vault entry.
- Advisory content quality reports for overlap with saved drafts and reviewer-provided source excerpts, citation formatting, claim-support cues, writing, SEO, and technical examples. Similarity is a human-review signal, not proof of plagiarism.
- Persisted quality reports and article revisions, with content-bound human review decisions. Editing a reviewed draft marks the previous decision stale; approval does not publish an article.
- Optional Pexels or Unsplash search. Results are inserted only after selection and include photographer/provider attribution. Pollinations AI can generate a topic-specific featured illustration without an API key; its free endpoint is best-effort and rate-limited, and generated assets remain provider-hosted rather than mirrored to durable storage.
- On opening a newly generated draft in the editor, the app attempts one automatic Pollinations featured-image generation and inserts it only after the returned image loads. Provider errors leave the draft unchanged and are shown in Image Studio; the attempt is not a guarantee of a usable or Blogger-hosted image.
- One Markdown-to-Blogger rendering pipeline supports responsive tables, captioned/attributed images, safe HTML, and user-authored process diagrams rendered as portable SVG. Live-post internal-link and previous/next suggestions use verified Blogger URLs.
- Manual affiliate and owned-product libraries support editing, enable/disable, deletion when unreferenced, descriptions, optional image/price/category, CTA text, and relevant keywords. Affiliate inserts require a user-selected saved entry and include the configured disclosure; inline placement requires a configured keyword in a plain paragraph, skips headings and linked/code paragraphs, avoids duplicate affiliate URLs, and is omitted if there is no match. Owned-product settings remain separate from third-party affiliate records.
- Saved product and affiliate selections, TOC options, generated search descriptions, and server-rendered Blogger HTML persist with drafts and revisions. A generated search description is stored locally; Blogger's documented Posts API does not expose a search-description field.
- Confirmed Blogger draft creation with returned post ID/URL persistence and a follow-up read-back verification. Updating a linked draft or live post and publishing a draft are separate, explicitly confirmed actions; ordinary saving does not change Blogger content.
- Google OAuth can be explicitly disconnected. Temporary Google refresh failures retain saved credentials and report an actionable status rather than silently clearing them.
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

Local article data, revisions, quality reports, review decisions, and Google OAuth credentials are stored in `content_ops.db` by default. Set `CONTENT_OPS_DB` to select another SQLite path. Google OAuth binds its signed state and separate PKCE verifier to short-lived HttpOnly cookies; the verifier is never sent in the authorization URL. Saved credentials still require durable server-side storage. The application has no owner-password login; its APIs are accessible to anyone who can reach the deployment unless access is restricted outside the application.

## Article and Blogger workflow

The existing editor is the single authoring surface. Generate or write Markdown, choose an optional active saved product or affiliate entry, review the preview, and save locally. The affiliate library allows manual configuration only; it does not connect affiliate accounts or call partner APIs. The API renders Markdown itself when saving and again when creating a Blogger draft, so the client cannot submit arbitrary preview HTML in place of the saved Markdown. A successful Blogger draft action records the Blogger post ID and URL before fetching the new post to verify its title, HTML, labels, and draft status. If verification is incomplete, inspect Blogger and the linked local article before retrying.

Use **Create Blogger Draft** only after reviewing the saved article. **Update Blogger Post** asks separately before replacing the content of the linked existing post; **Publish Blogger Draft** requires its own confirmation and is only offered for linked drafts. These operations require the deployed UI and API to be protected by Vercel Deployment Protection or equivalent platform access controls. This repository does not configure or verify that deployment setting.

Products and affiliate links are selected from saved vault records; no arbitrary first item is inserted. Disabled products are omitted from future selection and from the public eBook catalog. A product/affiliate record referenced by a saved article or revision cannot be hard-deleted; disable it instead to preserve the article. Images and attribution inserted into Markdown remain with the article source. Affiliate inline placement is keyword-based rather than semantic and is a placement aid, not an endorsement or factual verification. The article schema stores TOC selection, product/affiliate IDs, and Blogger post URL in SQLite; new product/affiliate fields are added through backward-compatible startup migrations. SQLite on Vercel `/tmp` is still ephemeral, so these records and OAuth credentials are not durable across instances.

## Content review

In the editor, save the draft and choose **Save draft & run checks**. Optionally provide source excerpts as `URL | excerpt` (one per line). Review the evidence, revise, and recheck after editing. **Approve reviewed draft** records an explicit human decision but does not publish to Blogger. Revision history can restore an earlier saved version into the editor; saving it creates another revision.

The Image Studio sends the supplied article topic to Pollinations AI. Opening an autopilot draft in the editor triggers one best-effort featured-image attempt; a loaded result is inserted with alt text and provider attribution. The current classic endpoint returns a JPEG and documents a best-effort limit of one image request per IP at least 45 seconds apart; consult its current [API documentation](https://github.com/pollinations/pollinations/blob/master/APIDOCS.md) and [terms](https://pollinations.ai/terms) before use. The application validates the returned JPEG but does not store a durable copy or verify that Blogger will retain access to the provider-hosted URL. Use a selected Pexels/Unsplash result with source attribution or continue without an image if provider hosting is unsuitable.

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

In Google Cloud, enable the Blogger API and Search Console API, configure the OAuth consent screen, and add the exact callback URL shown in the Blogger connection panel (or `GOOGLE_OAUTH_REDIRECT_URI`) to the OAuth client's authorized redirect URIs. If a saved credential is incomplete or invalid, the panel reports that reconnection is required. Google identity is verified during OAuth, but this does not authorize the separate content-management API. OAuth credentials and provider keys must remain in deployment secrets.

## Important hosting limitation

Vercel function storage is temporary. This app's SQLite database defaults to `/tmp/content_ops.db` on Vercel, so articles, quality reports, revisions, review decisions, saved OAuth credentials, and settings may not persist across function instances or deployments. OAuth state itself is short-lived and browser-bound, not stored in SQLite. Do not rely on the temporary database as durable production storage. A durable database/storage service would add an external dependency and may have cost or quota limits; none is added here. Vercel serverless functions also do not create a continuously running queue worker. Generation and synchronization run only after user actions.

The eBook PWA is a storefront/catalog, not a protected eBook reader. It sends checkout to each product's configured seller URL. Offline mode caches the app and catalog only; purchased files are delivered by the seller. A PDF/EPUB reader, protected downloads, purchase verification, and cross-device accounts are not implemented.

Free hosting and provider quotas are subject to platform limits and can change. This repository cannot guarantee zero cost for every hosting account or third-party service.

## Access-control warning and persistence

The application does not authenticate visitors. If deployed to a public URL, its API exposes saved drafts and review history, permits article/product/affiliate changes and deletions, can trigger configured AI/image-provider usage, and allows Google-connected Blogger/Search Console operations (including explicitly confirmed Blogger draft creation and live navigation updates). Google OAuth connects those integrations; it does **not** authorize access to this application. Keep the deployment private using Vercel Deployment Protection or an equivalent platform-level access control before production use. Do not expose a public deployment with real integration credentials or private content. This repository does not configure or verify platform protection, so this change must not be deployed publicly as-is.

Google OAuth tokens remain server-side and are not sent to browser JavaScript. Vercel's SQLite `/tmp` storage remains ephemeral and cannot reliably preserve articles, revisions, reports, decisions, saved OAuth credentials, or settings across function instances and deployments. Select and configure an approved persistent store before depending on production records; no paid or external database has been added.

The automated commands above cover Python compilation, mocked unit tests, and JavaScript syntax. They do not prove that a live OAuth login, Blogger draft creation, Search Console report, AI provider request, Vercel deployment, or Pexels/Unsplash request succeeds. Those require credentials and a controlled live test. A saved token record that is missing Google authorized-user fields must be replaced by a fresh OAuth connection.

Project architecture and contribution guidance: [Project structure](docs/PROJECT_STRUCTURE.md), [development rules](docs/DEVELOPMENT_RULES.md), and [content quality review](docs/CONTENT_QUALITY.md).
