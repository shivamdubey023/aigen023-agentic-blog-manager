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

Deploy the repository's `refactor/content-ops-hub` branch to test this refactor before switching production. In Streamlit Community Cloud, open **Manage app → Settings → Secrets** and add valid TOML. Never commit secrets or paste them into public issues.

```toml
[auth]
redirect_uri = "https://aigen023-blog-manager.streamlit.app/oauth2callback"
cookie_secret = "REPLACE_WITH_A_LONG_RANDOM_SECRET"
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_NEW_ROTATED_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[app]
allowed_email = "YOUR_GOOGLE_ACCOUNT_EMAIL"

[google]
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_NEW_ROTATED_CLIENT_SECRET"

# Optional; article generation is disabled without this key.
[gemini]
api_key = "YOUR_GEMINI_API_KEY"
```

Use a **newly rotated** OAuth client secret; do not reuse a secret previously exposed in chat. The same OAuth web client may be used in both `[auth]` and `[google]`, but the client ID and secret must match exactly. Generate a long random `cookie_secret`. Set `allowed_email` to the Google account allowed to use the private dashboard.

## Google OAuth configuration

1. In Google Cloud, enable **Blogger API v3** and **Google Search Console API**.
2. Configure an OAuth client of type **Web application**.
3. Add these exact **Authorized redirect URIs**:
   - `https://aigen023-blog-manager.streamlit.app/oauth2callback` — Streamlit's Google sign-in callback.
   - `https://aigen023-blog-manager.streamlit.app/` — Blogger/Search Console API authorization callback.
4. If the OAuth consent screen is in **Testing**, add the owner account under **Audience → Test users**.
5. Ensure the account has permission to manage the Blogger blog and access the Search Console property `https://aigen023.blogspot.com/`.
6. Required API OAuth scopes:
   - `https://www.googleapis.com/auth/blogger`
   - `https://www.googleapis.com/auth/webmasters.readonly`

If the Blogger API returns an error, check API enablement, test-user access, matching OAuth credentials, the exact redirect URI, and the account's property permissions. Analytics and AdSense reporting are intentionally not claimed as implemented in this refactor; no estimated earnings are fabricated.

## Run locally (Windows PowerShell)

Install Python 3.11 or newer. From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, or run `.venv\Scripts\python.exe -m streamlit run app.py` without activating the environment.

## Run locally (Linux/macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The OAuth redirect URI is currently configured for the hosted app. For local Google API OAuth, create a separate local OAuth configuration and set its redirect URI to `http://localhost:8501/` before starting the local flow.

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
