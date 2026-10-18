# NextGen Tech Notes — Content Operations Hub

A lean Streamlit dashboard for the technical publication [NextGen Tech Notes](https://aigen023.blogspot.com/). It stores article drafts and review queues in SQLite, renders Markdown as Blogger-ready HTML, generates editorial review warnings and JSON-LD, and connects to Blogger and Google Search Console.

**No YouTube/video/audio pipeline is included. No live posts are automatically published or overwritten.** AI-generated text is always a draft and must be checked by a human. This project does not guarantee search rankings, AdSense approval, or earnings.

## Features

- SQLite tables for articles, automation queue state/logs, and affiliate disclosures.
- Editor, Markdown preview, TOC generation, matching heading anchors, TechArticle JSON-LD, optional FAQPage JSON-LD helper, and affiliate boxes using `rel="sponsored nofollow noopener"`.
- Blogger API v3: list blogs/posts and create **drafts only**. Existing live posts are not overwritten.
- Search Console query/date rows for `https://aigen023.blogspot.com/`, using actual API results or an explicit no-data/error state.
- Optional Gemini article draft generation when a key is configured.
- Human review checklist for references, code, word count, reproducibility, and heading structure.
- CSV export of article metadata.

## Streamlit Community Cloud setup

Deploy the `refactor/content-ops-hub` branch to a separate test app first. In Streamlit Community Cloud, open **Manage app → Settings → Secrets** and add valid TOML. This build uses **one Google OAuth flow** for both owner verification and Blogger/Search Console access; it does not use Streamlit's built-in `st.login()` callback.

```toml
[app]
allowed_email = "YOUR_GOOGLE_ACCOUNT_EMAIL"

[google]
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_NEW_ROTATED_CLIENT_SECRET"

# Optional: article generation is disabled without this key.
[gemini]
api_key = "YOUR_GEMINI_API_KEY"
```

Use a **newly rotated** OAuth client secret; do not reuse a secret previously exposed in chat. The client ID and secret must match. Set `allowed_email` to the exact Google account permitted to access this dashboard. Never commit secrets to Git.

## Google OAuth configuration

1. In Google Cloud, enable **Blogger API v3** and **Google Search Console API**.
2. Configure an OAuth client of type **Web application**.
3. Add this exact **Authorized redirect URI**:
   - `https://aigen023-blog-manager.streamlit.app/`
4. If you deploy a separate Streamlit test app, add its exact root URL as another Authorized redirect URI, including the trailing slash.
5. If the OAuth consent screen is in **Testing**, add the owner account under **Audience → Test users**.
6. Ensure the owner account can manage the Blogger blog and access the Search Console property `https://aigen023.blogspot.com/`.
7. Required OAuth scopes:
   - `openid`, `email`, `profile` — verify the signed-in Google account.
   - `https://www.googleapis.com/auth/blogger` — create Blogger drafts.
   - `https://www.googleapis.com/auth/webmasters.readonly` — read Search Console reports.

The callback uses a short-lived, one-time OAuth state persisted in SQLite so the state check can survive a full browser redirect. If login still fails, open the Streamlit app logs and inspect the full traceback without sharing client secrets or authorization codes. For `invalid_client`, verify the matching client ID/rotated secret. For `redirect_uri_mismatch`, make the Google Cloud redirect URI match exactly. For `access_denied`, check test-user access and consent-screen settings.

Analytics and AdSense reporting are not claimed as implemented in this refactor; no estimated earnings are fabricated.

## Run locally (Windows PowerShell)

Install Python 3.11 or newer. From the repository root:

```powershell
New-Item -ItemType Directory -Force .streamlit
notepad .streamlit\secrets.toml
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8501/"
streamlit run app.py
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, or run `.venv\Scripts\python.exe -m streamlit run app.py` without activating the environment.

Add the following to `.streamlit\secrets.toml`, replacing the placeholders with your own values. Keep this file private; it is ignored by Git.

```toml
[app]
allowed_email = "YOUR_GOOGLE_ACCOUNT_EMAIL"

[google]
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"
```

For local sign-in, add `http://localhost:8501/` as an Authorized redirect URI on your Google OAuth Web application client. The environment variable above selects the callback for this local run; omit it in production to use the hosted callback.

## Run locally (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The OAuth redirect URI defaults to the hosted app. For local Google API OAuth, configure `GOOGLE_OAUTH_REDIRECT_URI` as shown above and add that exact URI to the OAuth client's authorized redirect URIs.

## Persistence and zero-cost limitations

- SQLite is stored at `content_ops.db` in the application directory by default. Set `CONTENT_OPS_DB` to choose another path. The database initializes automatically.
- Streamlit Community Cloud's local filesystem is not a durable database service; files may be reset on redeploy/restart. Export content and keep backups. For durable, always-on persistence on a zero-cost hosted tier, there is no guarantee—local Windows/Linux SQLite is the dependable option.
- The queue state and logs persist in SQLite, but this app does not run a hidden background scheduler. Processing is user-triggered and human review remains required.
- AI text is not automatically fact-checked. Do not publish invented tests, terminal output, personal experience, statistics, or citations. Verify all commands and links yourself.
- The 1,200-word check is a review hint, not a ranking rule. A longer article is not automatically useful or AdSense compliant.
- Schema markup must accurately describe visible content and the actual published article URL. Review generated JSON-LD and validate it before production publishing.
- Affiliate links must be disclosed clearly and use the correct relationship attributes. Confirm each program's disclosure and link requirements.

## Project structure

```text
app.py
core/
  database.py
property_a_blog/
  blogger_client.py
  seo_optimizer.py
requirements.txt
README.md
```
