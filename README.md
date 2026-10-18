# Aigen023 Agentic Blog Manager

Hosted starter for NextGen Tech Notes: Blogger draft management, SEO checklist, and affiliate planning.

## Current functionality
- Google sign-in gate with an email allowlist.
- Blogger OAuth connection using a separately stored client secret.
- Lists the blogs associated with the authorized Google account.
- Loads recent Blogger posts and drafts.
- Downloads existing post HTML.
- Saves local drafts and creates **Blogger drafts only**; it does not overwrite live posts.
- SEO / AdSense quality checklist and affiliate idea tracker.

## Deploy
The app is deployed on Streamlit Community Cloud at https://aigen023-blog-manager.streamlit.app/.

## Required Streamlit Secrets
Open the app in Streamlit Community Cloud, choose **Manage app → Settings → Secrets**, and add the following TOML. Replace all placeholders. Use a newly rotated Google OAuth client secret; the previous secret was exposed and must not be reused. Use the Google account email you want to allow into the dashboard.

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
```

Do not commit these values to GitHub. The `[auth]` client uses Google sign-in to gate the app; the `[google]` client values are used for Blogger API authorization. The same web client can be used if both redirect URIs are authorized in Google Cloud.

## Google Cloud configuration
1. Enable **Blogger API v3** in the project.
2. Configure Google Auth Platform branding and add your Google account as a test user.
3. Under the OAuth web client, add these exact Authorized redirect URIs:
   - `https://aigen023-blog-manager.streamlit.app/oauth2callback`
   - `https://aigen023-blog-manager.streamlit.app/`
4. Rotate the OAuth client secret that was shared in chat. Use the new secret only in Streamlit Secrets.
5. Set the Streamlit Secrets shown above, then restart/reboot the app.

## Security and data notes
- The app is gated by Google sign-in and the `allowed_email` allowlist. Leave this allowlist restricted to your own Google account.
- OAuth client secrets and tokens are not in source control.
- Blogger authorization tokens live in the current browser session; reconnect after the session ends.
- Local draft and affiliate files on Community Cloud are ephemeral and not a durable backup. Download important content.
- The app creates drafts only. Review content and references before publishing.
- Search Console, GA4, AdSense, and AI generation are not connected yet. No traffic or revenue is guaranteed.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```
