# Aigen023 Agentic Blog Manager

Zero-budget starter dashboard for [NextGen Tech Notes](https://aigen023.blogspot.com/).

## Current features
- Dashboard for local drafts and honest integration status.
- Markdown article draft editor and downloads.
- SVG cover image generation without an image API.
- SEO / AdSense quality checklist.
- Draft review workflow.
- Affiliate idea planner.
- Links to official Google integration documentation.

## Not implemented yet
This repository does **not** yet connect to Blogger, Search Console, GA4 or AdSense. It does not generate AI research or provide live views/earnings. Those features need Google OAuth/API setup and further development. Never assume expected income is guaranteed.

## Deploy free with Streamlit Community Cloud
1. Open https://share.streamlit.io/ and sign in with GitHub.
2. Choose **Create app**.
3. Select repository `shivamdubey023/aigen023-agentic-blog-manager`, branch `main`, and main file path `app.py`.
4. Deploy. The app URL will be shown by Streamlit.

GitHub stores the code; Streamlit Community Cloud runs the Python app. GitHub Pages alone cannot run a Streamlit/Python app.

## Local run on Windows
1. Install Python 3.11 or newer.
2. Open a terminal in this folder.
3. Run `py -m venv .venv`
4. Activate with `.venv\\Scripts\\activate`
5. Run `python -m pip install -r requirements.txt`
6. Run `streamlit run app.py`

## Data and privacy
Drafts are saved to local files in this starter. Files on Streamlit Community Cloud may not be durable across restarts/redeploys; download important drafts and add a persistent database/storage layer before using it as your only copy. Do not commit credentials, OAuth tokens or API keys.

## AdSense quality
Focus on original useful content, first-hand testing, verified references, working navigation and human review. Avoid thin bulk-generated content, copied text, fabricated citations or artificial traffic. No app can guarantee approval or revenue.
