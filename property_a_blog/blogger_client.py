"""Blogger and Search Console API wrappers with defensive errors."""
from __future__ import annotations
import json
from datetime import date
from typing import Any
from core import database as db
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"
SEARCH_CONSOLE_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
IDENTITY_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
SCOPES = IDENTITY_SCOPES + [BLOGGER_SCOPE, SEARCH_CONSOLE_SCOPE]
BLOG_URL = "https://aigen023.blogspot.com/"
REDIRECT_URI = "https://aigen023-blog-manager.streamlit.app/"

def get_credentials(session_state: Any) -> Credentials | None:
    token = session_state.get("google_api_token")
    if not token: return None
    try:
        creds = Credentials.from_authorized_user_info(token, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            session_state["google_api_token"] = json.loads(creds.to_json())
        return creds if creds.valid else None
    except Exception:
        session_state.pop("google_api_token", None)
        return None

def start_oauth(client_id: str, client_secret: str, session_state: Any) -> str:
    if not client_id or not client_secret: raise ValueError("Configure [google].client_id and [google].client_secret in Streamlit Secrets.")
    flow = Flow.from_client_config({"web":{"client_id":client_id,"client_secret":client_secret,
      "auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token",
      "redirect_uris":[REDIRECT_URI]}},scopes=SCOPES,redirect_uri=REDIRECT_URI)
    url,state=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent",
                                     code_challenge_method="S256")
    # PKCE verifier is required when exchanging the authorization code and must
    # survive Google's full-page redirect / Streamlit session reset.
    db.store_oauth_state(state, flow.code_verifier or "")
    return url

def finish_oauth(
    code: str,
    state: str,
    session_state: Any,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> Credentials:
    """Exchange OAuth callback code with backwards-compatible argument ordering."""
    if not client_id or not client_secret:
        try:
            import streamlit as st
            google_config = dict(st.secrets.get("google", {}))
        except Exception:
            google_config = {}
        client_id = client_id or str(google_config.get("client_id", ""))
        client_secret = client_secret or str(google_config.get("client_secret", ""))
    if not client_id or not client_secret:
        raise ValueError("Configure [google].client_id and [google].client_secret in Streamlit Secrets.")
    code_verifier = db.consume_oauth_state(state)
    if not code or not state or not code_verifier:
        raise ValueError("OAuth state or PKCE verifier is missing, expired, or already used. Restart Google login.")
    flow = Flow.from_client_config(
        {"web":{"client_id":client_id,"client_secret":client_secret,
          "auth_uri":"https://accounts.google.com/o/oauth2/auth",
          "token_uri":"https://oauth2.googleapis.com/token",
          "redirect_uris":[REDIRECT_URI]}},
        scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI,
        code_verifier=code_verifier,
    )
    # Google may return canonical OIDC scope URLs (userinfo.email/profile)
    # even when the request used the standard aliases (email/profile).
    # OAuthlib treats that equivalent representation as a scope change and
    # raises an error before credentials are available. We validate identity
    # below via the userinfo endpoint and use only the granted API scopes.
    flow.oauth2session._client.scope = None
    flow.fetch_token(code=code)
    creds=flow.credentials
    # Verify the Google identity using the access token; never trust browser-supplied email.
    import requests
    response=requests.get("https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization":f"Bearer {creds.token}"},timeout=15)
    response.raise_for_status()
    identity=response.json()
    if not identity.get("email") or identity.get("email_verified") is not True:
        raise ValueError("Google did not return a verified email address. Reconnect and approve the email scope.")
    session_state["google_api_token"]=json.loads(creds.to_json())
    session_state["google_user"]={"email":identity["email"],"name":identity.get("name","")}
    return creds
def blogger_service(creds: Credentials):
    if not creds or not creds.valid: raise ValueError("Google API account is not connected or token is invalid.")
    return build("blogger","v3",credentials=creds,cache_discovery=False)

def list_blogs(creds: Credentials) -> list[dict[str,Any]]:
    try: return blogger_service(creds).blogs().listByUser(userId="self").execute().get("items",[])
    except HttpError as exc: raise RuntimeError(f"Blogger API failed ({exc.resp.status}): {exc}") from exc

def list_posts(creds: Credentials, blog_id: str, limit: int=100) -> list[dict[str,Any]]:
    try:
        return blogger_service(creds).posts().list(blogId=blog_id,fetchBodies=True,maxResults=max(1,min(limit,500)),
          status=["LIVE","DRAFT"]).execute().get("items",[])
    except HttpError as exc: raise RuntimeError(f"Could not list Blogger posts ({exc.resp.status}): {exc}") from exc

def create_draft(creds: Credentials, blog_id: str, title: str, rendered_html: str) -> dict[str,Any]:
    """Create a new draft only; never updates an existing post."""
    if not title.strip() or not rendered_html.strip(): raise ValueError("Title and rendered HTML are required.")
    try:
        return blogger_service(creds).posts().insert(blogId=blog_id,
          body={"kind":"blogger#post","title":title.strip(),"content":rendered_html},isDraft=True).execute()
    except HttpError as exc: raise RuntimeError(f"Blogger draft creation failed ({exc.resp.status}): {exc}") from exc

def update_existing_draft(creds: Credentials, blog_id: str, post_id: str, title: str, rendered_html: str,
                          *, explicit_confirmation: bool=False) -> dict[str,Any]:
    if not explicit_confirmation: raise PermissionError("Explicit confirmation is required to update an existing post.")
    service=blogger_service(creds)
    try:
        existing=service.posts().get(blogId=blog_id,postId=post_id).execute()
        if existing.get("status")!="DRAFT": raise PermissionError("Refusing to overwrite a live/published Blogger post.")
        existing["title"],existing["content"]=title.strip(),rendered_html
        return service.posts().update(blogId=blog_id,postId=post_id,body=existing).execute()
    except HttpError as exc: raise RuntimeError(f"Blogger draft update failed ({exc.resp.status}): {exc}") from exc

def search_console_report(creds: Credentials, start: date, end: date, site_url: str=BLOG_URL,
                          dimensions: list[str]|None=None, row_limit: int=250) -> dict[str,Any]:
    try:
        api=build("searchconsole","v1",credentials=creds,cache_discovery=False)
        body={"startDate":start.isoformat(),"endDate":end.isoformat(),"dimensions":dimensions or ["date"],
              "rowLimit":max(1,min(row_limit,25000)),"dataState":"final"}
        return api.searchanalytics().query(siteUrl=site_url,body=body).execute()
    except HttpError as exc: raise RuntimeError(f"Search Console API failed ({exc.resp.status}): {exc}") from exc

def oauth_error_hint(exc: Exception) -> str:
    msg=str(exc)
    if "invalid_client" in msg.lower(): return "Google rejected the OAuth client. Verify the client ID and newly rotated secret match."
    if "access_denied" in msg.lower(): return "Access denied. Add this Google account as a test user if the OAuth app is in Testing."
    if "redirect_uri_mismatch" in msg.lower(): return "Add the exact callback URI to the OAuth client's Authorized redirect URIs."
    return msg[:600]
