"""Blogger and Search Console API wrappers with defensive errors."""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import date
from typing import Any
from core import database as db
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.env_config import get_google_redirect_uri, get_google_client_id, get_google_client_secret

BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"
SEARCH_CONSOLE_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
IDENTITY_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
SCOPES = IDENTITY_SCOPES + [BLOGGER_SCOPE, SEARCH_CONSOLE_SCOPE]
BLOG_URL = "https://aigen023.blogspot.com/"
REDIRECT_URI = "https://your-app.vercel.app/api/oauth/callback"

class CredentialLoadError(RuntimeError):
    def __init__(self, message: str, *, reconnect_required: bool = False) -> None:
        super().__init__(message)
        self.reconnect_required = reconnect_required


def get_redirect_uri() -> str:
    return os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "").strip() or get_google_redirect_uri() or REDIRECT_URI

def _oauth_state_signature(payload: str, client_secret: str) -> str:
    message = f"nextgen-oauth-state:{payload}".encode("ascii")
    return hmac.new(client_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

def _create_oauth_state(client_secret: str) -> str:
    payload = json.dumps(
        {
            "nonce": secrets.token_urlsafe(24),
            "issued_at": int(time.time()),
        },
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = _oauth_state_signature(encoded_payload, client_secret)
    return f"{encoded_payload}.{signature}"

def _read_oauth_state(state: str, client_secret: str) -> None:
    try:
        encoded_payload, supplied_signature = state.split(".", 1)
    except (AttributeError, ValueError) as exc:
        raise ValueError("Google OAuth state is invalid. Restart the connection.") from exc
    expected_signature = _oauth_state_signature(encoded_payload, client_secret)
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise ValueError("Google OAuth state could not be verified. Restart the connection.")
    try:
        padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload).decode("utf-8"))
        nonce = payload["nonce"]
        issued_at = int(payload["issued_at"])
        age = int(time.time()) - issued_at
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Google OAuth state is invalid. Restart the connection.") from exc
    if age < -60 or age > 900:
        raise ValueError("Google OAuth state expired. Restart the connection.")
    if not isinstance(nonce, str) or not nonce:
        raise ValueError("Google OAuth state is invalid. Restart the connection.")

def get_credentials(session_state: Any = None, token_override: Any = None) -> Credentials | None:
    token = None
    if token_override:
        if isinstance(token_override, str):
            try:
                token = json.loads(token_override)
            except Exception:
                token = None
        elif isinstance(token_override, dict):
            token = token_override
    if not token and session_state:
        token = session_state.get("google_api_token")
    if not token:
        stored = db.get_system_credential("google_api_token")
        if stored:
            try:
                token = json.loads(stored)
                if session_state:
                    session_state["google_api_token"] = token
            except json.JSONDecodeError as exc:
                raise CredentialLoadError(
                    "Saved Google credentials are unreadable. Disconnect and reconnect the Google account.",
                    reconnect_required=True,
                ) from exc
    if not token:
        return None
    try:
        creds = Credentials.from_authorized_user_info(token, SCOPES)
    except (TypeError, ValueError, KeyError) as exc:
        raise CredentialLoadError(
            "Saved Google credentials are incomplete. Disconnect and reconnect the Google account.",
            reconnect_required=True,
        ) from exc
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise CredentialLoadError(
                "Google rejected the saved refresh token. Reconnect the Google account; the stored credential was retained.",
                reconnect_required=True,
            ) from exc
        except Exception as exc:
            raise CredentialLoadError(
                "Google token refresh failed temporarily. Retry later; the stored credential was retained.",
            ) from exc
        new_token = json.loads(creds.to_json())
        if session_state:
            session_state["google_api_token"] = new_token
        try:
            db.save_system_credential("google_api_token", json.dumps(new_token))
        except Exception as exc:
            raise CredentialLoadError(
                "Google token refreshed, but the updated credential could not be saved. Check the configured database.",
            ) from exc
    return creds if creds.valid else None

def start_oauth(client_id: str, client_secret: str, session_state: Any, redirect_uri: str | None = None) -> str:
    client_id = client_id or get_google_client_id()
    client_secret = client_secret or get_google_client_secret()
    target_redirect = redirect_uri or get_redirect_uri()
    if not client_id or not client_secret: raise ValueError("Configure client_id and client_secret in .env or settings.")
    flow = Flow.from_client_config({"web":{"client_id":client_id,"client_secret":client_secret,
      "auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token",
      "redirect_uris":[target_redirect]}},scopes=SCOPES,redirect_uri=target_redirect)
    flow.code_verifier = secrets.token_urlsafe(64)
    state = _create_oauth_state(client_secret)
    url, _ = flow.authorization_url(
        state=state,
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge_method="S256",
    )
    session_state["oauth_state"] = state
    session_state["oauth_verifier"] = flow.code_verifier
    session_state["used_redirect_uri"] = target_redirect
    return url

def finish_oauth(
    code: str,
    state: str,
    session_state: Any,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str | None = None,
) -> Credentials:
    """Exchange OAuth callback code with backwards-compatible argument ordering."""
    client_id = client_id or get_google_client_id()
    client_secret = client_secret or get_google_client_secret()
    if not client_id or not client_secret:
        try:
            import streamlit as st
            google_config = dict(st.secrets.get("google", {}))
            client_id = client_id or str(google_config.get("client_id", ""))
            client_secret = client_secret or str(google_config.get("client_secret", ""))
        except Exception:
            pass
    if not client_id or not client_secret:
        raise ValueError("Configure client_id and client_secret in .env or settings.")
    expected_state = session_state.pop("oauth_state", "")
    code_verifier = session_state.pop("oauth_verifier", "")
    if not expected_state or not hmac.compare_digest(str(expected_state), state or ""):
        raise ValueError("Google OAuth state does not match this connection attempt. Restart the connection.")
    if not code:
        raise ValueError("Google did not return an authorization code. Restart the connection.")
    _read_oauth_state(state, client_secret)
    if not isinstance(code_verifier, str) or not re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", code_verifier):
        raise ValueError("Google OAuth PKCE verifier is missing. Restart the connection.")
    target_redirect = redirect_uri or session_state.get("used_redirect_uri") or get_redirect_uri()
    flow = Flow.from_client_config(
        {"web":{"client_id":client_id,"client_secret":client_secret,
          "auth_uri":"https://accounts.google.com/o/oauth2/auth",
          "token_uri":"https://oauth2.googleapis.com/token",
          "redirect_uris":[target_redirect]}},
        scopes=SCOPES, state=state, redirect_uri=target_redirect,
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
    db.save_system_credential("google_api_token", json.dumps(session_state["google_api_token"]))
    db.save_system_credential("google_user", json.dumps(session_state["google_user"]))
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

def get_post(creds: Credentials, blog_id: str, post_id: str) -> dict[str, Any]:
    try:
        return blogger_service(creds).posts().get(blogId=blog_id, postId=post_id).execute()
    except HttpError as exc:
        raise RuntimeError(f"Could not retrieve Blogger post ({exc.resp.status}).") from exc


def _normalized_html(content: str) -> str:
    return re.sub(r">\s+<", "><", content or "").strip()


def verify_post(
    post: dict[str, Any],
    *,
    title: str,
    rendered_html: str,
    status: str,
    labels: list[str] | None = None,
) -> dict[str, bool]:
    expected_labels = labels or []
    actual_labels = post.get("labels") or []
    return {
        "id": bool(post.get("id")),
        "title": post.get("title") == title,
        "content": _normalized_html(str(post.get("content") or "")) == _normalized_html(rendered_html),
        "status": str(post.get("status") or "").upper() == status.upper(),
        "labels": all(label in actual_labels for label in expected_labels),
    }


def create_draft(
    creds: Credentials,
    blog_id: str,
    title: str,
    rendered_html: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new draft only; never updates an existing post."""
    if not title.strip() or not rendered_html.strip(): raise ValueError("Title and rendered HTML are required.")
    try:
        body: dict[str, Any] = {
            "kind": "blogger#post",
            "title": title.strip(),
            "content": rendered_html,
        }
        if labels:
            body["labels"] = labels
        return blogger_service(creds).posts().insert(
            blogId=blog_id,
            body=body,
            isDraft=True,
        ).execute()
    except HttpError as exc: raise RuntimeError(f"Blogger draft creation failed ({exc.resp.status}): {exc}") from exc


def publish_draft(
    creds: Credentials,
    blog_id: str,
    post_id: str,
    *,
    explicit_confirmation: bool = False,
) -> dict[str, Any]:
    if not explicit_confirmation:
        raise PermissionError("Explicit confirmation is required to publish a Blogger post.")
    service = blogger_service(creds)
    try:
        post = service.posts().get(blogId=blog_id, postId=post_id).execute()
        if str(post.get("status") or "").upper() != "DRAFT":
            raise PermissionError("Only an unpublished Blogger draft can be published here.")
        result = service.posts().publish(blogId=blog_id, postId=post_id).execute()
        return result if isinstance(result, dict) else {}
    except HttpError as exc:
        raise RuntimeError(f"Blogger publish failed ({exc.resp.status}).") from exc

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

def update_live_post_navigation(creds: Credentials, blog_id: str, post_id: str, rendered_html: str,
                                *, explicit_confirmation: bool=False) -> dict[str,Any]:
    """Update only the content of a confirmed LIVE post for navigation synchronization."""
    if not explicit_confirmation:
        raise PermissionError("Explicit confirmation is required to update live post navigation.")
    service = blogger_service(creds)
    try:
        existing = service.posts().get(blogId=blog_id, postId=post_id).execute()
        if existing.get("status") != "LIVE":
            raise PermissionError("Refusing to update navigation on a post that is not LIVE.")
        existing["content"] = rendered_html
        return service.posts().update(blogId=blog_id, postId=post_id, body=existing).execute()
    except HttpError as exc:
        raise RuntimeError(f"Blogger live navigation update failed ({exc.resp.status}).") from exc


def update_live_post_content(
    creds: Credentials,
    blog_id: str,
    post_id: str,
    title: str,
    rendered_html: str,
    *,
    explicit_confirmation: bool = False,
) -> dict[str, Any]:
    if not explicit_confirmation:
        raise PermissionError("Explicit confirmation is required to update a live Blogger post.")
    service = blogger_service(creds)
    try:
        existing = service.posts().get(blogId=blog_id, postId=post_id).execute()
        if str(existing.get("status") or "").upper() != "LIVE":
            raise PermissionError("This update action is only for an already published Blogger post.")
        existing["title"] = title.strip()
        existing["content"] = rendered_html
        return service.posts().update(blogId=blog_id, postId=post_id, body=existing).execute()
    except HttpError as exc:
        raise RuntimeError(f"Blogger post update failed ({exc.resp.status}).") from exc

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
