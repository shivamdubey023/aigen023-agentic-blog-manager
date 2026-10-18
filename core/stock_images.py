"""Search free stock-image APIs without exposing provider credentials to clients."""
from __future__ import annotations

from urllib.parse import urlparse

import requests

from core.env_config import get_pexels_key, get_unsplash_key

IMAGE_PROVIDERS = ("pexels", "unsplash")
PROVIDER_LINKS = {
    "pexels": "https://www.pexels.com/",
    "unsplash": "https://unsplash.com/",
}


def provider_status() -> dict[str, bool]:
    return {
        "pexels": bool(get_pexels_key()),
        "unsplash": bool(get_unsplash_key()),
    }


def search_stock_images(query: str, provider: str, *, limit: int = 12) -> list[dict[str, str]]:
    query = query.strip()
    provider = provider.strip().lower()
    if len(query) < 2 or len(query) > 120:
        raise ValueError("Image search query must be between 2 and 120 characters.")
    if provider not in IMAGE_PROVIDERS:
        raise ValueError("Choose Pexels or Unsplash.")

    limit = max(1, min(limit, 20))
    if provider == "pexels":
        return _search_pexels(query, limit)
    return _search_unsplash(query, limit)


def _search_pexels(query: str, limit: int) -> list[dict[str, str]]:
    api_key = get_pexels_key()
    if not api_key:
        raise ValueError("Pexels is not configured. Add PEXELS_API_KEY in Vercel environment variables.")
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": limit},
            timeout=12,
        )
    except requests.Timeout as exc:
        raise RuntimeError("Pexels image search timed out. Retry later.") from exc
    except requests.RequestException as exc:
        raise RuntimeError("Pexels image search failed due to a network error.") from exc
    _raise_api_error("Pexels", response.status_code, response.ok)
    photos = _response_list(response, "photos", "Pexels")
    results = []
    for photo in photos:
        src = photo.get("src") or {}
        results.append(_image_result(
            provider="pexels",
            image_url=src.get("large") or src.get("medium") or "",
            thumbnail_url=src.get("medium") or src.get("small") or "",
            alt_text=photo.get("alt") or query,
            photographer=photo.get("photographer") or "Pexels contributor",
            photographer_url=photo.get("photographer_url") or PROVIDER_LINKS["pexels"],
            source_url=photo.get("url") or PROVIDER_LINKS["pexels"],
        ))
    return [result for result in results if result]


def _search_unsplash(query: str, limit: int) -> list[dict[str, str]]:
    api_key = get_unsplash_key()
    if not api_key:
        raise ValueError("Unsplash is not configured. Add UNSPLASH_ACCESS_KEY in Vercel environment variables.")
    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {api_key}", "Accept-Version": "v1"},
            params={"query": query, "per_page": min(limit, 30), "content_filter": "high"},
            timeout=12,
        )
    except requests.Timeout as exc:
        raise RuntimeError("Unsplash image search timed out. Retry later.") from exc
    except requests.RequestException as exc:
        raise RuntimeError("Unsplash image search failed due to a network error.") from exc
    _raise_api_error("Unsplash", response.status_code, response.ok)
    photos = _response_list(response, "results", "Unsplash")
    results = []
    for photo in photos:
        urls = photo.get("urls") or {}
        user = photo.get("user") or {}
        links = photo.get("links") or {}
        results.append(_image_result(
            provider="unsplash",
            image_url=urls.get("regular") or urls.get("raw") or "",
            thumbnail_url=urls.get("small") or urls.get("thumb") or "",
            alt_text=photo.get("alt_description") or query,
            photographer=user.get("name") or "Unsplash contributor",
            photographer_url=user.get("links", {}).get("html") or PROVIDER_LINKS["unsplash"],
            source_url=links.get("html") or PROVIDER_LINKS["unsplash"],
        ))
    return [result for result in results if result]


def _image_result(
    *,
    provider: str,
    image_url: str,
    thumbnail_url: str,
    alt_text: str,
    photographer: str,
    photographer_url: str,
    source_url: str,
) -> dict[str, str] | None:
    allowed_hosts = {
        "pexels": {"images.pexels.com"},
        "unsplash": {"images.unsplash.com"},
    }
    if not _is_https_host(image_url, allowed_hosts[provider]):
        return None
    if not _is_https_host(thumbnail_url, allowed_hosts[provider]):
        thumbnail_url = image_url
    if not _is_https_url(photographer_url) or not _is_https_url(source_url):
        return None
    return {
        "provider": provider,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "alt_text": str(alt_text)[:300],
        "photographer": str(photographer)[:120],
        "photographer_url": photographer_url,
        "source_url": source_url,
    }


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)


def _is_https_host(value: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in allowed_hosts


def _raise_api_error(provider: str, status_code: int, ok: bool) -> None:
    if ok:
        return
    if status_code in {401, 403}:
        message = "check the API key and provider permissions"
    elif status_code == 429:
        message = "the API quota or rate limit was reached; retry later"
    elif status_code >= 500:
        message = "the provider is temporarily unavailable; retry later"
    else:
        message = "check the search request and provider configuration"
    raise RuntimeError(f"{provider} image search failed (HTTP {status_code}); {message}.")


def _response_list(response: requests.Response, key: str, provider: str) -> list[dict]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{provider} returned an invalid response; retry later.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise RuntimeError(f"{provider} returned an unexpected response; retry later.")
    return [photo for photo in payload[key] if isinstance(photo, dict)]
