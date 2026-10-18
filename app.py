import html
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DRAFT_DIR = DATA_DIR / "drafts"
for folder in (DATA_DIR, DRAFT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Aigen023 Blog Manager", page_icon="✍️", layout="wide")

def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value.lower())
    return re.sub(r"[\s-]+", "-", value).strip("-")[:80] or "blog-post"

def load_drafts():
    drafts = []
    for path in sorted(DRAFT_DIR.glob("*.json"), reverse=True):
        try:
            drafts.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return drafts

def make_cover_svg(title, subtitle):
    title = html.escape(title[:65])
    subtitle = html.escape(subtitle[:100])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#101a35"/><stop offset="1" stop-color="#126782"/></linearGradient></defs>
<rect width="1200" height="630" rx="24" fill="url(#bg)"/>
<circle cx="1030" cy="110" r="190" fill="#48d6c7" opacity=".12"/>
<circle cx="110" cy="590" r="220" fill="#8da7ff" opacity=".13"/>
<text x="75" y="100" fill="#72e7dc" font-size="25" font-family="Arial">AIGEN023 · NEXTGEN TECH NOTES</text>
<foreignObject x="75" y="155" width="1050" height="300"><div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial;color:white;font-size:52px;font-weight:bold;line-height:1.15">{title}</div></foreignObject>
<foreignObject x="78" y="485" width="1040" height="80"><div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Arial;color:#d6e8f3;font-size:25px">{subtitle}</div></foreignObject>
</svg>'''

def save_draft(title, topic, meta, keywords, article, references, notes):
    draft_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft = {
        "id": draft_id, "created_at": datetime.now().isoformat(timespec="seconds"),
        "title": title.strip(), "topic": topic.strip(), "meta_description": meta.strip(),
        "keywords": [x.strip() for x in keywords.split(",") if x.strip()],
        "article_markdown": article.strip(),
        "references": [x.strip() for x in references.splitlines() if x.strip()],
        "research_notes": notes.strip(), "status": "Draft — human review required",
        "checks": {"examples_tested": False, "references_verified": False, "proofread": False}
    }
    (DRAFT_DIR / f"{draft_id}.json").write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return draft

st.title("✍️ Aigen023 Agentic Blog Manager")
st.caption("Zero-budget starter for NextGen Tech Notes · Blogger · SEO · AdSense · Affiliate planning")
st.warning("Starter build: article drafts and checklists work. Live Blogger, Search Console, Analytics and AdSense data are NOT connected yet. Never treat estimated income as guaranteed.")

with st.sidebar:
    st.header("Your blog")
    blog_url = st.text_input("Blogger URL", "https://aigen023.blogspot.com/")
    st.markdown("**Connection status**")
    st.write("Blogger API: Not connected")
    st.write("Search Console: Not connected")
    st.write("GA4 Analytics: Not connected")
    st.write("AdSense API: Not connected")
    st.caption("No API keys or passwords should be committed to GitHub.")

tab_dashboard, tab_create, tab_review, tab_seo, tab_affiliate, tab_connect = st.tabs(
    ["Dashboard", "Create article", "Review drafts", "SEO & AdSense", "Affiliate planner", "Connect services"]
)

with tab_dashboard:
    drafts = load_drafts()
    a, b, c, d = st.columns(4)
    a.metric("Saved drafts", len(drafts))
    b.metric("Published posts", "Not connected")
    c.metric("Search clicks", "Not connected")
    d.metric("AdSense earnings", "Not connected")
    st.info("Pageviews, Search Console clicks and AdSense earnings are different metrics. Connect each official service before displaying live numbers.")
    st.subheader("Recent drafts")
    if drafts:
        for item in drafts[:8]:
            st.write(f"**{item.get('title', 'Untitled')}** · {item.get('created_at', '')} · {item.get('status', '')}")
    else:
        st.write("No drafts yet. Open Create article to start.")
    st.subheader("Recommended workflow")
    st.markdown("1. Choose a real reader problem.\n2. Add firsthand tests, examples and verified references.\n3. Proofread and check links.\n4. Publish manually in Blogger.\n5. Use Search Console to monitor indexing and clicks.")

with tab_create:
    st.subheader("Create an article draft")
    st.write("Write or paste your draft here. This starter does not yet generate factual research with AI.")
    with st.form("new_draft"):
        topic = st.text_input("Topic", placeholder="e.g. Fix a Django GraphQL error")
        title = st.text_input("SEO title")
        meta = st.text_area("Meta description", max_chars=160)
        keywords = st.text_input("Keywords, comma-separated")
        notes = st.text_area("Research notes / firsthand testing", height=100)
        article = st.text_area("Article in Markdown", height=340, placeholder="# Introduction\n## Problem\n## Step-by-step fix\n## Tested example\n## Common mistakes\n## References")
        references = st.text_area("References — one URL per line", height=100)
        submit = st.form_submit_button("Save draft", type="primary")
    if submit:
        if not topic.strip() or not title.strip() or len(article.strip()) < 250:
            st.error("Add a topic, title and substantive article of at least 250 characters.")
        else:
            draft = save_draft(title, topic, meta, keywords, article, references, notes)
            st.success(f"Saved draft {draft['id']}. Review it before publishing.")
            cover = make_cover_svg(title, "Practical guide · Examples · Troubleshooting")
            st.download_button("Download cover image (SVG)", cover, file_name=f"{slugify(title)}.svg", mime="image/svg+xml")
            st.download_button("Download Markdown article", article, file_name=f"{slugify(title)}.md", mime="text/markdown")
            st.download_button("Download draft metadata", json.dumps(draft, ensure_ascii=False, indent=2), file_name=f"{draft['id']}.json", mime="application/json")

with tab_review:
    st.subheader("Review and improve drafts")
    drafts = load_drafts()
    if not drafts:
        st.info("Create your first draft before using this section.")
    else:
        options = {f"{x['id']} · {x['title']}": x for x in drafts}
        selected = st.selectbox("Choose a draft", list(options))
        draft = options[selected]
        st.markdown(f"### {draft['title']}")
        st.caption(f"Created {draft['created_at']} · {draft['status']}")
        st.write("**Meta description:**", draft.get("meta_description") or "Not added")
        st.write("**Keywords:**", ", ".join(draft.get("keywords", [])) or "Not added")
        st.markdown(draft.get("article_markdown", ""))
        st.download_button("Download selected article", draft.get("article_markdown", ""), file_name=f"{slugify(draft['title'])}.md", mime="text/markdown")
        st.markdown("**Before publishing**")
        st.checkbox("I added original examples or firsthand experience", key=f"ex_{draft['id']}")
        st.checkbox("I verified every reference and factual claim", key=f"ref_{draft['id']}")
        st.checkbox("I proofread the article and checked links", key=f"proof_{draft['id']}")

with tab_seo:
    st.subheader("SEO and AdSense quality checklist")
    checks = [
        st.checkbox("The article solves a specific reader problem", key="seo1"),
        st.checkbox("It includes original examples, tests or useful analysis", key="seo2"),
        st.checkbox("Every citation is real, relevant and checked", key="seo3"),
        st.checkbox("The content is not copied or lightly rewritten", key="seo4"),
        st.checkbox("Navigation, About, Contact and Privacy pages are in place", key="seo5"),
        st.checkbox("Mobile layout, broken links and spelling are checked", key="seo6"),
        st.checkbox("Relevant internal links and descriptive image alt text are added", key="seo7"),
    ]
    score = sum(checks)
    st.progress(score / len(checks))
    st.write(f"Self-check: {score}/{len(checks)} — this is not a Google approval score.")
    st.markdown("**Useful links**")
    st.link_button("Google Search Console", "https://search.google.com/search-console/")
    st.link_button("Blogger", "https://www.blogger.com/")
    st.link_button("Google AdSense", "https://www.google.com/adsense/")
    st.caption("No tool can guarantee AdSense approval, traffic or income. Avoid bulk thin content, fake citations and artificial traffic.")

with tab_affiliate:
    st.subheader("Affiliate idea planner")
    st.write("Recommend products only when they genuinely help readers. Clearly disclose affiliate links and check current program terms.")
    with st.form("affiliate_idea"):
        product = st.text_input("Product or tool")
        problem = st.text_area("Reader problem it solves")
        experience = st.text_area("Your testing / experience and downsides")
        url = st.text_input("Affiliate URL (optional)")
        disclosure = st.checkbox("I will clearly disclose affiliate links")
        save_idea = st.form_submit_button("Save idea")
    if save_idea:
        if not product.strip() or not problem.strip():
            st.error("Enter a product and the reader problem.")
        else:
            path = DATA_DIR / "affiliate_ideas.json"
            try:
                ideas = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                ideas = []
            ideas.append({"created_at": datetime.now().isoformat(timespec="seconds"), "product": product, "reader_problem": problem, "experience": experience, "affiliate_url": url, "disclosure_confirmed": disclosure, "status": "Needs verification"})
            path.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success("Idea saved for this app instance.")
    st.caption("Note: Streamlit Community Cloud local files are not reliable permanent storage. Export important drafts and add persistent storage before depending on this for long-term use.")

with tab_connect:
    st.subheader("Integrations — next development phase")
    st.markdown("""
- **Blogger API:** import existing posts and save reviewed updates as Blogger drafts.
- **Search Console API:** clicks, impressions, CTR and average position.
- **Google Analytics 4 Data API:** pageviews and sessions, if GA4 is installed.
- **AdSense Management API:** earnings and ad metrics, if your account and API access permit it.
""")
    st.link_button("Blogger API documentation", "https://developers.google.com/blogger/docs/3.0/using")
    st.link_button("Search Console API authorization", "https://developers.google.com/webmaster-tools/v1/how-tos/authorizing")
    st.link_button("Google Analytics Data API", "https://developers.google.com/analytics/devguides/reporting/data/v1")
    st.link_button("AdSense Management API", "https://developers.google.com/adsense/management/getting_started")
    st.error("Do not place OAuth secrets, API keys, refresh tokens or passwords in source code or a public repository. Use Streamlit Secrets/environment variables when integrations are implemented.")
