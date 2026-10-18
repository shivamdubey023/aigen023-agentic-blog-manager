# NextGen Tech Notes — AI Agentic Blog & Monetization Hub

A production-ready AI blogging engine and monetization platform built with **FastAPI**, **Modern Vanilla CSS/JS**, and **Vercel Serverless**. Designed specifically for [NextGen Tech Notes](https://aigen023.blogspot.com/) to automate high-ranking technical tutorials, rewrite existing content for **Google AdSense approval**, generate **free AI featured images**, and monetize via **Instamojo eBook sales** and **affiliates**.

---

## 🌟 Key Features

1. **Multi-Model LLM Engine**:
   - **Groq Cloud**: 100% free, ultra-fast generation (Llama 3.3 70B & DeepSeek R1).
   - **Google Gemini**: Free tier (Gemini 2.5 Flash & Pro).
   - **Cohere**: Free trial (Command R+).
   - **OpenAI & Claude**: Optional BYOK models (GPT-4o, Claude 3.5 Sonnet).

2. **AdSense Content Rewriter**:
   - Connects to your Blogger blog via Google API v3 to list previous posts.
   - Transforms thin or generic tutorials into comprehensive, 1,400–2,200+ word authority guides.
   - Injects reproducible code, realistic terminal tracebacks, prerequisites, and FAQ schemas.

3. **100% Free AI Blog Cover Studio**:
   - Powered by Pollinations.ai (Flux / SDXL).
   - Zero signup, zero API keys, instant 1200x630 featured images.

4. **Instamojo eBook & Affiliate Sales Engine**:
   - Integrates your active eBook: [Code to Career — The Python Fresher to Job-Ready Developer](https://codetocareer52.myinstamojo.com/product/code-to-career).
   - Injects high-converting, responsive eBook CTA banners with instant checkout buttons.
   - Built-in Affiliate Vault with `rel="sponsored nofollow noopener"` and required disclosure snippets.

5. **Blogger API v3 & Search Console**:
   - Uploads directly to Blogger as safe **drafts** (never overwrites live posts).
   - Inspects real organic search queries, clicks, and impressions.

---

## 🚀 Deploying to Vercel (Step-by-Step)

### Step 1: Push Code to GitHub
Ensure all your files are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Upgrade to Multi-Model AI Agentic Hub for Vercel"
git push origin main
```

### Step 2: Import Project in Vercel
1. Log in to [Vercel](https://vercel.com/).
2. Click **Add New...** → **Project**.
3. Select your GitHub repository (`aigen023-agentic-blog-manager` or your repository name).
4. Framework Preset: Leave as **Other** (Vercel automatically detects `vercel.json` and Python).

### Step 3: Add Environment Variables in Vercel
In the Vercel project configuration screen, open **Environment Variables** and add:

| Variable Name | Description | Where to get it |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Free LLM API Key (Llama 3.3 70B) | [console.groq.com](https://console.groq.com/) (100% Free) |
| `GEMINI_API_KEY` | Google Gemini API Key | [aistudio.google.com](https://aistudio.google.com/) (Free tier) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Google Cloud Console |

*(You can also configure API keys directly inside the web app settings in your browser).*

### Step 4: Configure Google OAuth Redirect URI
After deploying, Vercel gives you your live URL (e.g., `https://your-app-name.vercel.app`):
1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**.
2. Click your OAuth 2.0 Web Client.
3. Under **Authorized redirect URIs**, add:
   - `https://your-app-name.vercel.app/api/oauth/callback`
4. Click **Save**.

Now you can sign in to Google directly from your live Vercel app to fetch Blogger posts, upload drafts, and view Search Console metrics!

---

## 🛠️ Local Development (Optional)

If you ever want to run locally with Uvicorn:
```bash
pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.
