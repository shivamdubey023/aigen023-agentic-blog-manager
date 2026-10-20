"""NextGen Tech Notes content operations dashboard."""
from __future__ import annotations
import html, json, re
from datetime import date, timedelta
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

from core import database as db
from property_a_blog.blogger_client import (
    BLOG_URL, get_redirect_uri, finish_oauth, get_credentials, list_blogs,
    oauth_error_hint, search_console_report, start_oauth, create_draft,
)
from property_a_blog.seo_optimizer import affiliate_box, content_quality_checks, render_article

st.set_page_config(page_title="NextGen Tech Notes · Content Ops", page_icon="🛠️", layout="wide")
db.init_db()

def secrets_section(name: str) -> dict:
    try: return dict(st.secrets[name])
    except Exception: return {}

# Process Google OAuth redirects before rendering the dashboard.
if st.query_params.get("code"):
    google_oauth = secrets_section("google")
    try:
        finish_oauth(
            st.query_params.get("code", ""),
            st.query_params.get("state", ""),
            st.session_state,
            client_id=google_oauth.get("client_id", ""),
            client_secret=google_oauth.get("client_secret", ""),
        )
        st.query_params.clear()
        st.rerun()
    except Exception as exc:
        st.error(f"Google login failed: {oauth_error_hint(exc)}")
        st.query_params.clear()

st.title("🛠️ NextGen Tech Notes")
st.caption("Content operations · human review required · Blogger drafts only")
creds = get_credentials(st.session_state)
creds = get_credentials(st.session_state)

with st.sidebar:
    st.divider()
    st.metric("Google API connection", "Connected" if creds else "Not connected")
    st.caption("The Google API token is held in the current browser session, not committed to source control.")

tabs = st.tabs(["Queue & Automation","Editor & Publisher","Content Repository","Search Console & AdSense","Settings & OAuth"])

with tabs[0]:
    st.subheader("Queue & automation")
    state = db.queue_state()
    st.write("Queue status:", "🟢 RUNNING" if state=="RUNNING" else "⏸️ PAUSED")
    c1,c2,c3 = st.columns(3)
    c1.metric("Saved articles",len(db.list_articles()))
    c2.metric("Queued",sum(1 for a in db.list_articles() if a["status"]=="QUEUED"))
    c3.metric("Queue items",len(db.queue_rows()))
    b1,b2,b3 = st.columns(3)
    if b1.button("Start queue", type="primary"):
        db.set_queue_state("RUNNING")
        st.rerun()
    if b2.button("Pause queue"):
        db.set_queue_state("PAUSED")
        st.rerun()
    if b3.button("Restart queue"):
        db.restart_queue()
        st.rerun()
    st.caption("No unattended publishing occurs. Queue execution is user-triggered so every article stays reviewable.")
    queue = db.queue_rows()
    if queue:
        st.dataframe(pd.DataFrame(queue)[[c for c in ["id","title","topic","state","retry_count","max_retries","updated_at"] if c in queue[0]]],use_container_width=True,hide_index=True)
        batch_size=st.number_input("Batch size (queued items to prepare for human review)",min_value=1,max_value=25,value=5,step=1)
        if st.button("Process batch → prepare drafts for review"):
            candidates=[x for x in queue if x.get("state")=="RUNNING" and x.get("article_id") and x.get("article_status")=="QUEUED"][:int(batch_size)]
            if not candidates:
                st.info("No RUNNING queue items linked to QUEUED articles. Start/restart the queue and add articles first.")
            else:
                processed=0
                for item in candidates:
                    article=db.get_article(item["article_id"])
                    if not article: 
                        db.log_queue_event(item["id"],"Skipped: article record missing",retry=True,state="PAUSED")
                        continue
                    try:
                        rendered,schema=render_article(article["markdown_body"],article["title"],article["primary_keyword"])
                        db.save_article(topic=article["topic"],primary_keyword=article["primary_keyword"],title=article["title"],
                          markdown_body=article["markdown_body"],rendered_html=rendered,schema_json=schema,status="DRAFT",
                          article_id=article["id"],blogger_post_id=article["blogger_post_id"],blogger_blog_id=article["blogger_blog_id"])
                        db.log_queue_event(item["id"],"Batch prepared article for human review",state="PAUSED")
                        processed+=1
                    except Exception as exc:
                        db.log_queue_event(item["id"],f"Batch processing error: {exc}",retry=True,state="PAUSED")
                st.success(f"Prepared {processed} draft(s) for review. Nothing was published.")
                st.rerun()
        choices = {f"#{x['id']} · {x.get('title') or x.get('topic') or 'Untitled'}":x for x in queue}
        chosen_label=st.selectbox("Queue item",list(choices),key="queue_selected")
        selected=choices[chosen_label]
        if st.button("Process next item (prepare for review)"):
            article = db.get_article(selected["article_id"]) if selected.get("article_id") else None
            if not article:
                db.log_queue_event(selected["id"],"Skipped: article record missing",retry=True,state="PAUSED")
                st.warning("Queue item has no linked article.")
            else:
                db.set_article_status(article["id"],"DRAFT")
                db.log_queue_event(selected["id"],"Prepared draft for human review",state="PAUSED")
                st.success("Article returned to DRAFT for review. No automatic publishing was performed.")
            st.rerun()
    else: st.info("Queue is empty. Save an article from the editor and choose Add to queue.")

with tabs[1]:
    st.subheader("Technical article editor")
    with st.form("article_editor_form"):
        topic=st.text_input("Topic",placeholder="e.g. Debugging Django database connection errors")
        keyword=st.text_input("Primary keyword",placeholder="e.g. Django PostgreSQL connection error")
        title=st.text_input("Article title")
        audience=st.selectbox("Reader level",["Beginner","Student / fresher","Working developer","Senior engineer"])
        notes=st.text_area("First-hand notes, test results, environment and references (important)",height=100)
        use_ai=st.checkbox("Generate a draft with Gemini (requires [gemini].api_key)")
        make_article=st.form_submit_button("Create article draft",type="primary")
    if make_article:
        if not topic.strip(): st.error("Enter a topic.")
        else:
            try:
                if use_ai:
                    key=secrets_section("gemini").get("api_key","")
                    if not key: raise ValueError("Missing [gemini].api_key in Streamlit Secrets.")
                    prompt=f"""Write a deep, practical technical tutorial for NextGen Tech Notes.
Topic: {topic}
Primary keyword: {keyword}
Reader: {audience}
Author notes and evidence (use only as supplied; flag gaps): {notes or 'None supplied'}
Write at least 1,200 substantive words without padding or generic introductory filler. Explain prerequisites,
version assumptions, exact steps, reproducible code, commands and expected output, failure modes,
troubleshooting, security caveats, and relevant official documentation URLs only when confident.
Include a representative terminal traceback for a relevant failure when technically useful, label it as an example,
and never imply it was observed in a real run. Include a syntax-valid corrected example and verification steps.
Never claim you ran tests or have personal experience. Never invent real test results, metrics, citations, or URLs.
Use Markdown, one H1 followed by meaningful H2/H3 sections, and finish with a verification checklist and references to verify.
Mark unsupported facts [VERIFY]. Output article Markdown only."""
                    resp=requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                        params={"key":key},json={"contents":[{"parts":[{"text":prompt}]}],
                        "generationConfig":{"temperature":0.35,"maxOutputTokens":8000}},timeout=90)
                    if not resp.ok: raise RuntimeError(f"Gemini HTTP {resp.status_code}: {resp.text[:350]}")
                    draft=resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    title = title.strip() or next((x[2:].strip() for x in draft.splitlines() if x.startswith("# ")),topic)
                else:
                    draft=f"# {title.strip() or topic}\n\n## Prerequisites\n\nDescribe the tested environment and versions.\n\n## Steps\n\nAdd reproducible steps, code, expected output, and troubleshooting based on your own verification.\n\n## Verification\n\nRecord commands run and observed results.\n\n## References\n\nAdd official documentation links you have checked.\n"
                rendered,schema=render_article(draft,title or topic,keyword,description=f"Practical technical tutorial: {title or topic}.")
                article_id=db.save_article(topic=topic,primary_keyword=keyword,title=title or topic,markdown_body=draft,
                    rendered_html=rendered,schema_json=schema,status="DRAFT")
                st.session_state["active_article_id"]=article_id
                st.session_state["editor_markdown"]=draft
                st.session_state["editor_title"]=title or topic
                st.session_state["editor_topic"]=topic
                st.session_state["editor_keyword"]=keyword
                st.success(f"Saved article #{article_id} to SQLite. Continue reviewing below.")
            except Exception as exc: st.error(f"Could not create draft: {exc}")
    saved = db.get_article(st.session_state.get("active_article_id",0)) if st.session_state.get("active_article_id") else None
    default_md = st.session_state.get("editor_markdown",saved["markdown_body"] if saved else "")
    edited_title=st.text_input("Edit title",value=st.session_state.get("editor_title",saved["title"] if saved else ""),key="editor_title_field")
    edited_md=st.text_area("Markdown editor",value=default_md,height=380,key="editor_markdown_field")
    c1,c2,c3=st.columns(3)
    include_toc=c1.checkbox("Generate table of contents",value=True)
    affiliate_entries=db.list_affiliates()
    aff_labels=["No affiliate box"]+[f"{x['product_name']} (#{x['id']})" for x in affiliate_entries]
    selected_aff=c2.selectbox("Affiliate box",aff_labels)
    primary_keyword=st.session_state.get("editor_keyword","")
    if c3.button("Render preview"):
        st.session_state["preview_ready"]=True
    affiliate_html=""
    if selected_aff!="No affiliate box":
        af=affiliate_entries[aff_labels.index(selected_aff)-1]
        try: affiliate_html=affiliate_box(af["product_name"],af["tracking_url"],af["disclosure_snippet"])
        except ValueError as exc: st.error(str(exc))
    rendered,schema=render_article(edited_md,edited_title,primary_keyword,include_toc=include_toc,affiliate_html=affiliate_html)
    warnings=content_quality_checks(edited_title,edited_md)
    if warnings:
        with st.expander(f"Editorial review checklist ({len(warnings)} items)",expanded=True):
            for warning in warnings: st.warning(warning)
    if st.session_state.get("preview_ready",False):
        st.markdown("#### Preview")
        st.markdown(edited_md)
        st.caption("Preview shows Markdown; Blogger HTML includes generated heading IDs and structured data.")
    colsave,colqueue=st.columns(2)
    if colsave.button("Save edits to repository",type="primary"):
        try:
            article_id=db.save_article(topic=st.session_state.get("editor_topic",""),primary_keyword=primary_keyword,
                title=edited_title,markdown_body=edited_md,rendered_html=rendered,schema_json=schema,
                status="DRAFT",article_id=saved["id"] if saved else None)
            st.session_state["active_article_id"]=article_id
            st.success(f"Saved draft #{article_id}.")
        except Exception as exc: st.error(str(exc))
    if colqueue.button("Save and add to queue"):
        try:
            article_id=db.save_article(topic=st.session_state.get("editor_topic",""),primary_keyword=primary_keyword,
                title=edited_title,markdown_body=edited_md,rendered_html=rendered,schema_json=schema,status="QUEUED",
                article_id=saved["id"] if saved else None)
            db.queue_article(article_id)
            st.session_state["active_article_id"]=article_id
            st.success(f"Article #{article_id} added to the human-review queue.")
        except Exception as exc: st.error(str(exc))
    st.divider()
    st.subheader("Create a Blogger draft")
    if not creds:
        st.info("Connect Google API access in Settings & OAuth to upload drafts.")
    else:
        try: blogs=list_blogs(creds)
        except Exception as exc:
            blogs=[]; st.error(str(exc))
        target_options={f"{b.get('name','Untitled')} · {b.get('url','')}":b for b in blogs}
        if target_options:
            target_label=st.selectbox("Blogger target",list(target_options),key="publisher_blog")
            confirm=st.checkbox("I reviewed the article, code, links, schema, and image/affiliate disclosures.",key="publish_reviewed")
            if st.button("Upload as Blogger draft (not published)",disabled=not confirm):
                try:
                    rendered,schema=render_article(edited_md,edited_title,primary_keyword,include_toc=include_toc,affiliate_html=affiliate_html)
                    created=create_draft(creds,target_options[target_label]["id"],edited_title,rendered)
                    article_id=db.save_article(topic=st.session_state.get("editor_topic",""),primary_keyword=primary_keyword,
                      title=edited_title,markdown_body=edited_md,rendered_html=rendered,schema_json=schema,status="DRAFT",
                      article_id=saved["id"] if saved else None,blogger_post_id=created.get("id",""),
                      blogger_blog_id=target_options[target_label]["id"])
                    st.success(f"Created Blogger draft. Post ID: {created.get('id','(not returned)')}")
                    if created.get("url"): st.link_button("Open Blogger post",created["url"])
                except Exception as exc: st.error(f"Blogger upload failed: {exc}")
        else: st.info("No Blogger blogs returned for this account.")

with tabs[2]:
    st.subheader("SQLite content repository")
    articles=db.list_articles()
    if articles:
        df=pd.DataFrame([{k:a.get(k) for k in ["id","topic","primary_keyword","title","status","blogger_post_id","created_at","updated_at"]} for a in articles])
        st.dataframe(df,use_container_width=True,hide_index=True)
        ids={f"#{a['id']} · {a['title'] or a['topic']}":a["id"] for a in articles}
        selected=st.selectbox("Load an article for editing",list(ids),key="repository_load")
        chosen_article=db.get_article(ids[selected])
        action1,action2=st.columns(2)
        if action1.button("Review / Edit selected article"):
            st.session_state["active_article_id"]=chosen_article["id"]
            st.session_state["editor_markdown"]=chosen_article["markdown_body"]
            st.session_state["editor_title"]=chosen_article["title"]
            st.session_state["editor_topic"]=chosen_article["topic"]
            st.session_state["editor_keyword"]=chosen_article["primary_keyword"]
            st.success("Loaded. Open Editor & Publisher tab.")
        if action2.button("Pause selected article"):
            db.set_article_status(chosen_article["id"],"PAUSED")
            st.success("Article paused.")
            st.rerun()
        if creds:
            try:
                repost_blogs=list_blogs(creds)
            except Exception as exc:
                repost_blogs=[]
                st.warning(f"Could not load Blogger blogs for reposting: {exc}")
            if repost_blogs:
                repost_options={f"{b.get('name','Untitled')} · {b.get('url','')}":b for b in repost_blogs}
                repost_target=st.selectbox("Repost destination (creates a new Blogger draft)",list(repost_options),key="repost_target")
                repost_confirm=st.checkbox("Confirm creating a separate new Blogger draft; do not replace the original.",key="repost_confirm")
                if st.button("Repost as new Blogger draft",disabled=not repost_confirm):
                    try:
                        rendered,_=render_article(chosen_article["markdown_body"],chosen_article["title"],chosen_article["primary_keyword"])
                        created=create_draft(creds,repost_options[repost_target]["id"],chosen_article["title"],rendered)
                        db.save_article(topic=chosen_article["topic"],primary_keyword=chosen_article["primary_keyword"],
                          title=chosen_article["title"],markdown_body=chosen_article["markdown_body"],rendered_html=rendered,
                          status="DRAFT",blogger_post_id=created.get("id",""),blogger_blog_id=repost_options[repost_target]["id"])
                        st.success(f"Created separate Blogger draft. Post ID: {created.get('id','not returned')}")
                    except Exception as exc: st.error(f"Repost failed: {exc}")
        export=st.download_button("Export repository CSV",df.to_csv(index=False),file_name="nextgen-tech-notes-articles.csv",mime="text/csv")
    else: st.info("No articles saved yet.")

with tabs[3]:
    st.subheader("Search Console & AdSense status")
    st.caption("Only API-returned data is shown. No metrics are estimated or fabricated.")
    start=st.date_input("Start date",value=date.today()-timedelta(days=28),key="sc_start")
    end=st.date_input("End date",value=date.today()-timedelta(days=3),key="sc_end")
    if start>end: st.error("Start date must be on or before end date.")
    elif not creds: st.info("Connect Google API access in Settings & OAuth.")
    else:
        if st.button("Fetch Search Console metrics"):
            try:
                report=search_console_report(creds,start,end,site_url=BLOG_URL,dimensions=["date","query"],row_limit=1000)
                rows=report.get("rows",[])
                if rows:
                    frame=pd.DataFrame([{"date":r.get("keys",[""])[0],"query":r.get("keys",["",""])[1] if len(r.get("keys",[]))>1 else "",
                        "clicks":r.get("clicks",0),"impressions":r.get("impressions",0),"ctr":r.get("ctr",0),
                        "average_position":r.get("position",0)} for r in rows])
                    st.dataframe(frame,use_container_width=True,hide_index=True)
                    st.metric("Clicks",int(frame["clicks"].sum()))
                    st.metric("Impressions",int(frame["impressions"].sum()))
                    st.caption("Average position is a weighted aggregate only if recomputed using impressions; row values above are the API's query rows.")
                else: st.info("Search Console returned no rows for this period/property. Verify property ownership and date availability.")
            except Exception as exc: st.error(f"Search Console data unavailable: {exc}")
        st.divider()
        st.markdown("**AdSense**")
        st.info("AdSense metrics are not implemented in this build. No revenue figures are displayed. Add AdSense Management API reporting only after the account and API permissions are verified.")

with tabs[4]:
    st.subheader("Settings & OAuth token lifecycle")
    st.write("Publication target:",BLOG_URL)
    st.write("OAuth callback:",get_redirect_uri())
    st.write("Required Google API scopes:")
    st.code("https://www.googleapis.com/auth/blogger\nhttps://www.googleapis.com/auth/webmasters.readonly")
    google=secrets_section("google")
    if creds:
        st.success("Google API OAuth token is valid for the current browser session.")
        if st.button("Disconnect Google APIs"):
            st.session_state.pop("google_api_token",None)
            st.session_state.pop("google_api_oauth_state",None)
            st.session_state.pop("google_api_oauth_client",None)
            st.rerun()
    else:
        st.warning("Google API access is not connected.")
        if st.button("Connect Blogger + Search Console",type="primary"):
            try:
                url=start_oauth(google.get("client_id",""),google.get("client_secret",""),st.session_state)
                st.link_button("Continue to Google authorization",url)
            except Exception as exc: st.error(oauth_error_hint(exc))
    st.divider()
    st.subheader("Affiliate vault")
    with st.form("affiliate_vault_form"):
        product=st.text_input("Product / service name")
        keywords=st.text_input("Trigger keywords (comma separated)")
        tracking_url=st.text_input("Tracking URL")
        disclosure=st.text_area("Disclosure text",value="This article may contain affiliate links. If you buy through these links, we may earn a commission at no additional cost to you.")
        save_aff=st.form_submit_button("Save affiliate entry")
    if save_aff:
        try:
            parsed=urlparse(tracking_url.strip())
            if parsed.scheme not in {"http","https"} or not parsed.netloc: raise ValueError("Enter a valid http(s) tracking URL.")
            if not product.strip() or not disclosure.strip(): raise ValueError("Product name and disclosure are required.")
            db.save_affiliate(product,[x.strip() for x in keywords.split(",") if x.strip()],tracking_url,disclosure)
            st.success("Affiliate entry saved."); st.rerun()
        except Exception as exc: st.error(str(exc))
    entries=db.list_affiliates()
    if entries: st.dataframe(pd.DataFrame([{k:x.get(k) for k in ["id","product_name","trigger_keywords","tracking_url","disclosure_snippet"]} for x in entries]),use_container_width=True,hide_index=True)
