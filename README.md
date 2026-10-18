# Aigen023 Blog Manager

Hosted app for NextGen Tech Notes: Blogger drafts, AI-assisted article generation, image selection, SEO checklist, and reporting API integrations.

## Features in this build
- Google sign-in with an email allowlist.
- Google OAuth connection for Blogger, Search Console, GA4 Data API, and AdSense Management API.
- Lists accessible Blogger blogs and recent posts.
- AI-assisted Markdown article draft generation using Gemini API.
- Wikimedia Commons image search with source, author, and license metadata.
- Saves local drafts and creates Blogger drafts only after explicit confirmation.
- Search Console daily clicks/impressions/CTR/position rows.
- GA4 pageviews, sessions, and active users for a property the signed-in account can access.
- AdSense reports when the account is eligible and API access is enabled.

## Deploy
The Streamlit Community Cloud app is https://aigen023-blog-manager.streamlit.app/. Changes pushed to `main` trigger deployment; check Streamlit app logs if the build fails.

## Streamlit Secrets
Open Streamlit Community Cloud → app → **Manage app → Settings → Secrets**. Add the complete TOML below and replace every placeholder. Use a newly rotated OAuth secret; the previously shared secret must not be reused. Do not commit secrets to GitHub.

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

[gemini]
api_key = "YOUR_GEMINI_API_KEY"
```

The `[auth]` and `[google]` sections can use the same OAuth web client, provided the matching client ID and secret are used consistently. `[auth]` protects dashboard access; `[google]` authorizes the data APIs. Generate a unique random cookie secret. Never paste completed secrets into chat or commit them.

AI generation is optional: if you do not configure `[gemini]`, all non-AI dashboard features can still be used. Get a Gemini API key at https://aistudio.google.com/app/apikey; check your account's current free-tier limits before use.

## Google Cloud setup
1. Enable Blogger API v3, Google Search Console API, Google Analytics Data API, and AdSense Management API if you intend to use each report.
2. Under Google Auth Platform → Audience, add the account in `[app].allowed_email` as a test user while the OAuth app is in Testing.
3. Add both Authorized redirect URIs to the same OAuth Web client:
   - `https://aigen023-blog-manager.streamlit.app/oauth2callback` for Streamlit Google sign-in.
   - `https://aigen023-blog-manager.streamlit.app/` for the app's Google API consent flow.
4. Rotate the OAuth secret previously shared in chat. Store only the replacement in Streamlit Secrets.
5. The authorized Google account must have access to the Blogger blog, Search Console property, GA4 property, and AdSense account respectively.

## Important limitations
- The app creates Blogger drafts only; it does not automatically publish or overwrite live posts.
- Search Console, GA4, and AdSense reports only work when the relevant API is enabled and the Google account has permission. A missing AdSense account or unavailable API permission is reported as an error/no data, not fabricated earnings.
- Gemini output is a draft, not verified research. Fact-check instructions, code, claims, references, and links before publishing.
- Wikimedia Commons search results show source and license metadata, but you must check the source page's exact terms and attribution requirements.
- Drafts and affiliate ideas are stored as local files and may be lost on Streamlit Community Cloud restarts/redeploys. Download backups; persistent storage is not implemented.
- Do not bulk publish thin AI content, fabricate citations, or expect guaranteed AdSense approval or revenue.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```
