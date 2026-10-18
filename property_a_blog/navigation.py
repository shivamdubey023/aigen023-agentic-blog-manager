"""Idempotent previous/next navigation for live Blogger posts."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

NAV_START = "<!-- nextgen-content-nav:start -->"
NAV_END = "<!-- nextgen-content-nav:end -->"
NAV_BLOCK_RE = re.compile(
    re.escape(NAV_START) + r".*?" + re.escape(NAV_END),
    re.DOTALL,
)


def order_live_posts(posts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Return only LIVE posts with valid Blogger published timestamps, oldest first."""
    ordered: list[tuple[datetime, str, dict[str, Any]]] = []
    skipped: list[str] = []
    for post in posts:
        if post.get("status") != "LIVE":
            continue
        post_id = str(post.get("id") or "")
        try:
            published = datetime.fromisoformat(str(post["published"]).replace("Z", "+00:00"))
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            published = published.astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError):
            skipped.append(post_id or "unknown post")
            continue
        ordered.append((published, post_id, post))
    ordered.sort(key=lambda entry: (entry[0], entry[1]))
    return [entry[2] for entry in ordered], skipped


def navigation_content(
    content: str,
    previous: dict[str, Any] | None,
    next_post: dict[str, Any] | None,
) -> str:
    """Replace this app's navigation block without changing the article body."""
    body = NAV_BLOCK_RE.sub("", content or "").rstrip()
    links: list[str] = []
    if previous:
        link = _link("Previous post", previous)
        if link:
            links.append(link)
    if next_post:
        link = _link("Next post", next_post)
        if link:
            links.append(link)
    if not links:
        return body
    block = (
        f'{NAV_START}<nav aria-label="Article navigation"><p>'
        + " &nbsp; | &nbsp; ".join(links)
        + f"</p></nav>{NAV_END}"
    )
    return f"{body}\n\n{block}" if body else block


def _link(label: str, post: dict[str, Any]) -> str:
    title = _escape_html(str(post.get("title") or label))
    url = _escape_html(str(post.get("url") or ""))
    rel = "prev" if label == "Previous post" else "next"
    if not url.startswith("https://"):
        return ""
    return f'<a rel="{rel}" href="{url}">{label}: {title}</a>'


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
