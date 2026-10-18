import html
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st
import markdown as md
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DRAFT_DIR = DATA_DIR / "drafts"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)
BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"
APP_URL = "https://aigen023-blog-manager.streamlit.app/"
BLOGGER_REDIRECT_URI = APP_URL

st.set_page_config(page_title="Aigen023 Blog Manager", page_icon="✍️", layout="wide")


def secret_section(name):
    try:
        return dict(st.secrets[name])
    except Exception:
        return {}


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


def save_local_draft(title, content, blog_id="", source_post_id=""):
    draft_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    draft = {
        "id": draft_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "title": title.strip(),
        "content": content,
        "blog_id": blog_id,
        "source_post_id": source_post_id,
        "status": "Local draft — not published",
    }
    (DRAFT_DIR / f"{draft_id}.json").write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return draft


def get_blogger_credentials():
    token_data = st.session_state.get("blogger_token")
    if not token_data:
        return None
    try:
        return Credentials.from_authorized_user_info(token_data, [BLOGGER_SCOPE])
    except Exception:
        st.session_state.pop("blogger_token", None)
        return None


def blogger_service():
    creds = get_blogger_credentials()
    if not creds or not creds.valid:
        return None
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def connect_blogger():
    google = secret_section("google")
    if not google.get("client_id") or not google.get("client_secret"):
        st.error("Missing [google] client_id/client_secret in Streamlit Secrets.")
        return
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": google["client_id"],
                "client_secret": google["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [BLOGGER_REDIRECT_URI],
            }
        },
        scopes=[BLOGGER_SCOPE],
        redirect_uri=BLOGGER_REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.session_state["blogger_oauth_state"] = state
    st.session_state["blogger_oauth_flow"] = {
        "state": state,
        "client_id": google["client_id"],
        "client_secret": google["client_secret"],
    }
    st.link_button("Continue to Google authorization", auth_url)


def handle_blogger_callback():
    code = st.query_params.get("code")
    state = st.query_params.get("state")
    if not code:
        return
    oauth_state = st.session_state.get("blogger_oauth_state")
    if not oauth_state or not state or state != oauth_state:
        st.error("OAuth state did not match. For safety, restart the Blogger connection.")
        st.query_params.clear()
        return
    cfg = st.session_state.get("blogger_oauth_flow", {})
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": cfg.get("client_id", ""),
                "client_secret": cfg.get("client_secret", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [BLOGGER_REDIRECT_URI],
            }
        },
        scopes=[BLOGGER_SCOPE],
        state=oauth_state,
        redirect_uri=BLOGGER_REDIRECT_URI,
    )
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state["blogger_token"] = json.loads(creds.to_json())
        st.session_state.pop("blogger_oauth_state", None)
        st.session_state.pop("blogger_oauth_flow", None)
        st.query_params.clear()
        st.success("Blogger connected for this browser session.")
        st.rerun()
    except Exception as exc:
        st.query_params.clear()
        st.error(f"Google authorization failed: {exc}")


def gate_app():
    auth = secret_section("auth")
    app_cfg = secret_section("app")
    required = ["redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"]
    missing = [key for key in required if not auth.get(key)]
    if missing:
        st.title("✍️ Aigen023 Blog Manager")
        st.error("App access is locked until authentication is configured.")
        st.markdown("In Streamlit **Manage app → Settings → Secrets**, add the [auth] settings and [app] allowed_email shown in the setup instructions.")
        st.stop()
    if not st.user.is_logged_in:
        st.title("✍️ Aigen023 Blog Manager")
        st.write("Private owner dashboard. Sign in with your Google account to continue.")
        st.button("Sign in with Google", on_click=st.login, type="primary")
        st.stop()
    signed_email = str(getattr(st.user, "email", "") or "").lower()
    allowed_email = str(app_cfg.get("allowed_email", "")).strip().lower()
    if not allowed_email or signed_email != allowed_email:
        st.error("This Google account is not authorized to use this dashboard.")
        st.button("Sign out", on_click=st.logout)
        st.stop()
    return signed_email


handle_blogger_callback()
owner_email = gate_app()

st.title("✍️ Aigen023 Agentic Blog Manager")
st.caption("NextGen Tech Notes · Blogger · SEO · AdSense · Affiliate planning")
with st.sidebar:
    st.success(f"Signed in: {owner_email}")
    if st.button("Sign out"):
        st.logout()
    st.divider()
    st.write("**Blogger connection**")
    if get_blogger_credentials():
        st.success("Connected for this browser session")
        if st.button("Disconnect Blogger"):
            st.session_state.pop("blogger_token", None)
            st.rerun()
    else:
        st.info("Not connected")
    st.caption("Credentials and tokens are not written to source files.")

try:
    handle_blogger_callback()
except Exception:
    pass

service = blogger_service()
blogs = []
blog_error = None
if service:
    try:
        blogs = service.blogs().listByUser(userId="self").execute().get("items", [])
    except HttpError as exc:
        blog_error = str(exc)

tab_dashboard, tab_posts, tab_editor, tab_seo, tab_affiliate, tab_setup = st.tabs(
    ["Dashboard", "Blogger posts", "Create / revise draft", "SEO & AdSense", "Affiliate planner", "Setup"]
)

with tab_dashboard:
    drafts = load_drafts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Local drafts", len(drafts))
    c2.metric("Blogger connection", "Connected" if service else "Not connected")
    c3.metric("Blogs found", len(blogs) if service else "—")
    c4.metric("Live analytics", "Not connected")
    st.info("Live views, Search Console clicks, and AdSense earnings are not connected yet. Do not interpret estimates as actual earnings.")
    st.subheader("Recent local drafts")
    if drafts:
        for draft in drafts[:8]:
            st.write(f"**{draft.get('title', 'Untitled')}** · {draft.get('created_at', '')} · {draft.get('status', '')}")
    else:
        st.write("No local drafts yet.")
    if blog_error:
        st.error(f"Blogger API error: {blog_error}")

with tab_posts:
    st.subheader("Your Blogger posts")
    if not service:
        st.info("Connect Blogger in the Setup tab first.")
    elif blog_error:
        st.error(blog_error)
    elif not blogs:
        st.warning("No Blogger blogs were returned for the authorized Google account.")
    else:
        blog_options = {f"{b.get('name', 'Untitled blog')} · {b.get('url', '')}": b for b in blogs}
        chosen_blog_label = st.selectbox("Choose a blog", list(blog_options))
        chosen_blog = blog_options[chosen_blog_label]
        try:
            post_response = service.posts().list(
                blogId=chosen_blog["id"], fetchBodies=True, maxResults=30, status=["LIVE", "DRAFT"]
            ).execute()
            posts = post_response.get("items", [])
            st.caption(f"Showing up to 30 posts from {chosen_blog.get('name', 'your blog')}.")
            if not posts:
                st.info("No posts returned.")
            for post in posts:
                status = "Draft" if post.get("status") == "DRAFT" else "Published"
                with st.expander(f"{post.get('title', 'Untitled')} · {status}"):
                    st.caption(f"Updated: {post.get('updated', 'unknown')} · Post ID: {post.get('id', '')}")
                    st.markdown(post.get("content", ""), unsafe_allow_html=True)
                    st.download_button(
                        "Download post HTML",
                        post.get("content", ""),
                        file_name=f"{slugify(post.get('title', 'post'))}.html",
                        mime="text/html",
                        key=f"download_{post.get('id')}",
                    )
                    if st.button("Load into revision editor", key=f"revise_{post.get('id')}"):
                        st.session_state["revision_title"] = f"Updated: {post.get('title', '')}"
                        st.session_state["revision_content"] = post.get("content", "")
                        st.session_state["revision_blog_id"] = chosen_blog["id"]
                        st.session_state["revision_source_post_id"] = post.get("id", "")
                        st.session_state["revision_blog_name"] = chosen_blog.get("name", "")
                        st.toast("Loaded into the draft editor. Original post remains unchanged.")
        except HttpError as exc:
            st.error(f"Could not load posts: {exc}")

with tab_editor:
    st.subheader("Create a new Blogger draft or prepare a revision")
    if not service:
        st.caption("You can create local drafts now; connect Blogger to save a draft directly to Blogger.")
    initial_title = st.session_state.get("revision_title", "")
    initial_content = st.session_state.get("revision_content", "")
    with st.form("draft_form", clear_on_submit=False):
        title = st.text_input("Post title", value=initial_title, key="editor_title")
        content = st.text_area(
            "Post content (HTML accepted; Markdown is converted)",
            value=initial_content,
            height=360,
            key="editor_content",
        )
        save_local = st.form_submit_button("Save local draft")
        publish_blogger_draft = st.form_submit_button("Save as Blogger draft", type="primary", disabled=not bool(service and blogs))
    if save_local:
        if not title.strip() or len(content.strip()) < 20:
            st.error("Enter a title and substantive content.")
        else:
            d = save_local_draft(title, content)
            st.success(f"Saved local draft {d['id']}.")
    if publish_blogger_draft:
        if not title.strip() or len(content.strip()) < 20:
            st.error("Enter a title and substantive content.")
        else:
            blog_choices = {f"{b.get('name', 'Untitled blog')} · {b.get('url', '')}": b for b in blogs}
            blog_label = st.selectbox("Select target blog for draft", list(blog_choices), key="target_blog")
            if st.button("Confirm create Blogger draft", key="confirm_blogger_draft"):
                try:
                    html_content = content if re.search(r"<[a-zA-Z][^>]*>", content) else md.markdown(content)
                    body = {"kind": "blogger#post", "title": title.strip(), "content": html_content}
                    created = service.posts().insert(
                        blogId=blog_choices[blog_label]["id"], body=body, isDraft=True
                    ).execute()
                    st.success(f"Blogger draft created: {created.get('title', title)}")
                    if created.get("url"):
                        st.link_button("Open draft post", created["url"])
                except HttpError as exc:
                    st.error(f"Could not create Blogger draft: {exc}")

with tab_seo:
    st.subheader("SEO and AdSense quality checklist")
    checks = [
        st.checkbox("Article solves a specific reader problem", key="seo1"),
        st.checkbox("Includes original examples, tests, or useful analysis", key="seo2"),
        st.checkbox("Every citation is real, relevant, and verified", key="seo3"),
        st.checkbox("Content is not copied or lightly rewritten", key="seo4"),
        st.checkbox("About, Contact, Privacy, and navigation pages are in place", key="seo5"),
        st.checkbox("Mobile layout, broken links, and spelling are checked", key="seo6"),
        st.checkbox("Relevant internal links and descriptive image alt text are added", key="seo7"),
    ]
    score = sum(checks)
    st.progress(score / len(checks))
    st.write(f"Self-check: {score}/{len(checks)}. This is not a Google approval score.")
    st.link_button("Google Search Console", "https://search.google.com/search-console/")
    st.link_button("Blogger", "https://www.blogger.com/")
    st.link_button("Google AdSense", "https://www.google.com/adsense/")

with tab_affiliate:
    st.subheader("Affiliate idea planner")
    st.write("Use affiliate links only when genuinely useful to readers, and clearly disclose them.")
    with st.form("affiliate_form"):
        product = st.text_input("Product or tool")
        problem = st.text_area("Reader problem it solves")
        experience = st.text_area("Your testing, experience, and downsides")
        affiliate_url = st.text_input("Affiliate URL (optional)")
        disclosed = st.checkbox("I will clearly disclose affiliate links")
        save_idea = st.form_submit_button("Save affiliate idea")
    if save_idea:
        if not product.strip() or not problem.strip():
            st.error("Enter a product and the reader problem.")
        else:
            path = DATA_DIR / "affiliate_ideas.json"
            try:
                ideas = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                ideas = []
            ideas.append({
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "product": product, "reader_problem": problem, "experience": experience,
                "affiliate_url": affiliate_url, "disclosure_confirmed": disclosed,
            })
            path.write_text(json.dumps(ideas, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success("Affiliate idea saved for this app instance.")

with tab_setup:
    st.subheader("Connect Blogger")
    st.write("This connection requests Blogger API access. You will authorize access on Google's page; the token stays in this browser session and is not committed to GitHub.")
    st.warning("The OAuth client secret you previously shared must be rotated before connecting. Use the replacement secret only in Streamlit Secrets.")
    st.write("1. Confirm Blogger API v3 is enabled in Google Cloud.")
    st.write("2. Add this exact URI to the OAuth client's **Authorized redirect URIs**:")
    st.code(BLOGGER_REDIRECT_URI)
    st.write("3. Ensure Streamlit Secrets contains [google] client_id and client_secret.")
    st.write("4. Click Connect Blogger below.")
    if st.button("Connect Blogger", type="primary"):
        connect_blogger()
    st.divider()
    st.subheader("What is not integrated yet")
    st.markdown("- Search Console clicks/impressions/CTR/position\n- GA4 pageviews and sessions\n- AdSense earnings API\n- AI article generation")
    st.caption("Blogger actions create drafts only. Existing published posts are not changed automatically.")
